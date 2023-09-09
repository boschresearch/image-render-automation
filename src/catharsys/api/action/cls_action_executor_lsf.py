###
# Author: Christian Perwass (CR/ADI2.1)
# <LICENSE id="Apache-2.0">
#
#   Image-Render Automation Functions module
#   Copyright 2023 Robert Bosch GmbH and its subsidiaries
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# </LICENSE>
###

import re
import sys
import enum
import time
import asyncio
import platform
import concurrent.futures
import threading
import queue
from dataclasses import dataclass
from datetime import datetime
from importlib import resources as res
from pathlib import Path

from anybase import config
from anybase.cls_any_error import CAnyError_Message
from typing import Optional, Callable, Any

import catharsys.gui.web
from catharsys.api.cls_action import CAction
from catharsys.config.cls_job import CConfigJob
from catharsys.config.cls_exec_job import CConfigExecJob

from anybase import shell
from anybase.cls_process_group_handler import CProcessGroupHandler, EProcessStatus
from anybase.cls_process_handler import CProcessHandler
from anybase.cls_process_output import CProcessOutput

from .cls_action_executor import CActionExecutor
from .cls_job_status import EJobStatus

from catharsys.api.cls_project import CProject
from catharsys.api.cls_workspace import CWorkspace


class ELsfJobStatus(enum.Enum):
    NONE = enum.auto()
    SUBMITTED = enum.auto()
    PENDING = enum.auto()
    RUNNING = enum.auto()
    ENDED = enum.auto()
    TERMINATED = enum.auto()


# endclass


@dataclass
class CLsfJobInfo:
    iLsfId: int = None
    iJobIdx: int = None
    sUser: str = None
    eStatus: ELsfJobStatus = ELsfJobStatus.NONE
    sQueue: str = None
    sFromHost: str = None
    sExecHost: str = None
    sJobName: str = None
    dtLaunch: datetime = None


# endclass


class EOutputType(str, enum.Enum):
    STD = "Standard"
    ERR = "Error"


# endclass


class CActionExecutorLsf(CActionExecutor):
    def __init__(self, *, _xAction: CAction, _lExecJobs: list[CConfigExecJob]):
        super().__init__(_xAction=_xAction, _lExecJobs=_lExecJobs)

        self._xLoop: asyncio.AbstractEventLoop = None

        self._xJobGrp: CProcessGroupHandler = CProcessGroupHandler()
        self._xLsfJobGrp: CProcessGroupHandler = CProcessGroupHandler()
        self._lJobProcHandler: list[CProcessHandler] = []
        self._lLsfJobStatus: list[ELsfJobStatus] = []

        self._reBpeekJobNotStarted: re.Pattern = re.compile(r"Job\s<(?P<id>\d+)> : Not yet started")
        self._reBpeekJobNotFound: re.Pattern = re.compile(r"Job\s<(?P<id>\d+)> is not found")

        self._lockJobData: threading.Lock = threading.Lock()
        self._evTerminateAll: threading.Event = threading.Event()
        self._lJobStatus: list[EJobStatus] = []
        self._setJobStatusChanged: set[int] = set()

        self._dicLsfJobInfo: dict[int, CLsfJobInfo] = dict()
        self._dicJobIdxToLsfId: dict[int, int] = dict()

        self._dicLsfJobStatusText: dict[ELsfJobStatus, str] = {
            ELsfJobStatus.NONE: "n/a",
            ELsfJobStatus.SUBMITTED: "submitted",
            ELsfJobStatus.PENDING: "pending",
            ELsfJobStatus.RUNNING: "running",
            ELsfJobStatus.ENDED: "ended",
            ELsfJobStatus.TERMINATED: "terminated",
        }

        self._lJobOutputTypes: list[str] = [EOutputType.STD, EOutputType.ERR]
        self._dicJobOutput: dict[str, list[CProcessOutput]] = {
            EOutputType.STD: [],
            EOutputType.ERR: [],
        }
        self._lActJobOutputType: list[EOutputType] = []
        self._setJobOutputChanged: set[int] = set()

    # enddef

    # ##################################################################################################
    def TerminateAll(self):
        self._evTerminateAll.set()
        # self._xJobGrp.TerminateAll()
        # self._xLsfJobGrp.TerminateAll()

    # enddef

    # ##################################################################################################
    def TerminateJob(self, iJobId: int):
        self._xJobGrp.TerminateProc(iJobId)

    # enddef

    # ##################################################################################################
    def GetJobInfo(self, iIdx: int) -> dict[str, Any]:
        dicInfo = dict()

        with self._lockJobData:
            iLsfIdx: int = self._dicJobIdxToLsfId.get(iIdx)

            if iLsfIdx is None:
                dicInfo["Status"] = "n/a"
                return dicInfo
            # endif

            xLsfJobInfo = self._dicLsfJobInfo.get(iLsfIdx)
            if xLsfJobInfo is None:
                dicInfo["Status"] = "n/a"
                return dicInfo
            # endif

            dicInfo["Status"] = self._dicLsfJobStatusText.get(xLsfJobInfo.eStatus, "n/a")
            dicInfo["Job Id"] = str(xLsfJobInfo.iLsfId)

            if isinstance(xLsfJobInfo.sUser, str):
                dicInfo["User"] = xLsfJobInfo.sUser
                dicInfo["Queue"] = xLsfJobInfo.sQueue
                if isinstance(xLsfJobInfo.sExecHost, str):
                    dicInfo["Host"] = xLsfJobInfo.sExecHost
                # endif
                dicInfo["Submitted"] = xLsfJobInfo.dtLaunch.strftime("%b %d %H:%M")
            # endif
        # endwith lock
        return dicInfo

    # enddef

    # ##################################################################################################
    def UpdateJobOutput(self, *, _iMaxTime_ms: int = 100):
        self._xJobGrp.UpdateProcOutput(_iMaxTime_ms=_iMaxTime_ms)
        self._setJobOutputChanged = self._xJobGrp.GetProcOutputChanged()

        iJobIdx: int = None
        for iJobIdx in self._setJobOutputChanged:
            xProcOut: CProcessOutput = self._xJobGrp.GetProcOutput(iJobIdx)
            eActOutType = self._lActJobOutputType[iJobIdx]
            xTrgOut = self._dicJobOutput[eActOutType][iJobIdx]
            sLine: str = None
            for sLine in xProcOut:
                if sLine.startswith("<< output from stdout >>"):
                    if eActOutType != EOutputType.STD:
                        eActOutType = EOutputType.STD
                        xTrgOut = self._dicJobOutput[eActOutType][iJobIdx]
                    # endif
                elif sLine.startswith("<< output from stderr >>"):
                    if eActOutType != EOutputType.ERR:
                        eActOutType = EOutputType.ERR
                        xTrgOut = self._dicJobOutput[eActOutType][iJobIdx]
                    # endif
                else:
                    xTrgOut.AddLine(sLine)
                # endif
            # endfor
        # endfor changed job outputs

    # enddef

    # ##################################################################################################
    def GetJobOutputTypes(self) -> list[str]:
        return self._lJobOutputTypes.copy()

    # enddef

    # ##################################################################################################
    def GetJobOutput(self, iIdx: int, *, _sType: str = None) -> CProcessOutput:
        # return self._xJobGrp.GetProcOutput(iIdx)
        if _sType is None:
            return self._dicJobOutput[EOutputType.STD][iIdx]
        # endif

        lJobOut = self._dicJobOutput.get(_sType)
        if lJobOut is None:
            raise RuntimeError(f"Invalid job output type '{_sType}'")
        # endif

        return lJobOut[iIdx]

    # enddef

    # ##################################################################################################
    def GetJobEndMessage(self, iIdx: int) -> str:
        return ""

    # enddef

    # ##################################################################################################
    def GetJobStatus(self, iIdx: int) -> EJobStatus:
        with self._lockJobData:
            if iIdx < 0 or iIdx >= len(self._lJobStatus):
                return None
            else:
                return self._lJobStatus[iIdx]
            # endif
        # endwith

    # enddef

    # ##################################################################################################
    def GetJobStatusChanged(self, *, _bClear: bool = True) -> set[int]:
        with self._lockJobData:
            setChanged: set[int] = self._setJobStatusChanged.copy()
            if _bClear is True:
                self._setJobStatusChanged.clear()
            # endif
        # endwith

        return setChanged

    # enddef

    # ##################################################################################################
    def GetJobOutputChanged(self, *, _bClear: bool = True) -> set[int]:
        # return self._xJobGrp.GetProcOutputChanged()
        setChanged = self._setJobOutputChanged.copy()
        if _bClear is True:
            self._setJobOutputChanged.clear()
        # endif
        return setChanged

    # enddef

    # ##################################################################################################
    def _DoExecuteJobs(self):
        self._xAction.ExecuteJobList(self._lExecJobs, bPrintOutput=True)

    # enddef

    # ##################################################################################################
    async def Execute(
        self,
        *,
        _funcJobExecStart: Optional[Callable[[None], None]] = None,
        _funcJobExecEnd: Optional[Callable[[None], None]] = None,
    ):
        self._xJobGrp.Clear()
        self._xLsfJobGrp.Clear()
        self._lLsfJobStatus.clear()
        self._lJobProcHandler.clear()
        self._lJobStatus = []
        self._setJobStatusChanged = set()
        self._dicJobOutput[EOutputType.STD].clear()
        self._dicJobOutput[EOutputType.ERR].clear()
        self._lActJobOutputType.clear()
        self._setJobOutputChanged.clear()

        self._xLoop = asyncio.get_running_loop()

        try:
            # Create handler to return the LSF job numbers for each job configuration
            xJob: CConfigExecJob = None
            for iJobIdx, xJob in enumerate(self._lExecJobs):
                self._xLsfJobGrp.AddProcessHandler(_iJobId=iJobIdx, _xProcHandler=xJob.xProcHandler)

                xProcHandler = CProcessHandler()
                self._xJobGrp.AddProcessHandler(_iJobId=iJobIdx, _xProcHandler=xProcHandler)
                self._lJobProcHandler.append(xProcHandler)
                self._lLsfJobStatus.append(ELsfJobStatus.NONE)

                self._lJobStatus.append(EJobStatus.NOT_STARTED)

                self._dicJobOutput[EOutputType.STD].append(CProcessOutput())
                self._dicJobOutput[EOutputType.ERR].append(CProcessOutput())
                self._lActJobOutputType.append(EOutputType.STD)
            # endfor

            if _funcJobExecStart is not None:
                _funcJobExecStart()
            # endif

            # print("> Starting thread")
            with concurrent.futures.ThreadPoolExecutor() as xPool:
                await self._xLoop.run_in_executor(xPool, lambda: self._DoExecuteLsfJobs())
            # endwith
            # print("Launch Local: END")

            # Empty queue before exiting function
            self.UpdateJobOutput(_iMaxTime_ms=0)

            if _funcJobExecEnd is not None:
                _funcJobExecEnd()
            # endif
        except Exception as xEx:
            raise CAnyError_Message(sMsg="Error executing standard jobs", xChildEx=xEx)
        finally:
            self._xLoop = None
        # endtry

    # enddef

    # ##################################################################################################
    def _DoExecuteBjobs(self, *, _fInterval_s: float, _xProcHandler: CProcessHandler):
        sSystem: str = platform.system()
        if sSystem == "Linux":
            xScript = res.files(catharsys.gui.web).joinpath("scripts").joinpath("show_bjobs.sh")
            sScript: str = None
            sPathScript: str = None
            with res.as_file(xScript) as pathScript:
                sScript = pathScript.read_text()
                sPathScript = pathScript.parent.as_posix()
            # endwith
            sScript = sScript.replace("$TIME", str(_fInterval_s))
            lScript: list[str] = sScript.splitlines()
            shell.ExecBashCmds(lCmds=lScript, sCwd=sPathScript, xProcHandler=_xProcHandler)
        else:
            raise RuntimeError(f"Launching LSF jobs not supported on system type '{sSystem}")
        # endif

    # enddef

    # ##################################################################################################
    def _DoExecuteSingleBjobs(self) -> list[str]:
        sSystem: str = platform.system()
        if sSystem == "Linux":
            lLines: list[str] = []
            bOk: bool = False
            bOK, lLines = shell.ExecBashCmds(lCmds=["bjobs"], bReturnStdOut=True)
        else:
            raise RuntimeError(f"Launching LSF jobs not supported on system type '{sSystem}")
        # endif

        return lLines

    # enddef

    def _BpeekStdOut(self, sLine: str):
        if "ls_rstat: File operation failed:" in sLine:
            # print("BPEEK: Terminate")
            self._bBpeekTerminate = True
        elif self._bBpeekTerminate is False:
            self._lBpeekLines.append(sLine)
        # endif

    # enddef

    def _BpeekPollTerminate(self) -> bool:
        return self._bBpeekTerminate

    # enddef

    # ##################################################################################################
    def _DoExecuteSingleBpeek(self, *, _iLsfJobId: int, _xProcHandler: CProcessHandler):
        sSystem: str = platform.system()
        if sSystem == "Linux":
            self._lBpeekLines: list[str] = []
            self._bBpeekTerminate: bool = False

            xProcH: CProcessHandler = CProcessHandler()
            xProcH.AddHandlerStdOut(lambda sLine: self._BpeekStdOut(sLine))
            xProcH.AddHandlerPollTerminate(lambda: self._BpeekPollTerminate())
            if _xProcHandler.bStdOutAvailable is True:
                shell.ExecBashCmds(lCmds=[f"bpeek {_iLsfJobId}"], xProcHandler=xProcH)
                # bOk, lLines = shell.ExecCmd(sCmd=[f"bpeek {_iLsfJobId}"], bDoPrint=True, bReturnStdOut=True, sPrintPrefix=">> ")
                # print(self._lBpeekLines)
                for sLine in self._lBpeekLines:
                    xMatch: re.Match = self._reBpeekJobNotStarted.match(sLine)
                    if xMatch is not None:
                        # print(f"[{_iLsfJobId}] bpeek: NOT STARTED")
                        break
                    # endif

                    xMatch = self._reBpeekJobNotFound.match(sLine)
                    if xMatch is not None:
                        # print(f"[{_iLsfJobId}] bpeek: NOT FOUND")
                        break
                    # endif

                    _xProcHandler.StdOut(sLine)
                # endfor
            # endif
        else:
            raise RuntimeError(f"Launching LSF jobs not supported on system type '{sSystem}")
        # endif

    # enddef

    # ##################################################################################################
    def _DoExecuteBpeek(self, *, _iLsfJobId: int, _xProcHandler: CProcessHandler):
        sSystem: str = platform.system()
        if sSystem == "Linux":
            bRestart: bool = False
            bExit: bool = False
            lLines: list[str] = []

            while True:
                bRestart = False
                bOk: bool = False
                bOk, lLines = shell.ExecBashCmds(lCmds=[f"bpeek {_iLsfJobId}"], bReturnStdOut=True)
                print(f"[{_iLsfJobId}] bpeek: {(len(lLines))}")
                for sLine in lLines:
                    xMatch: re.Match = self._reBpeekJobNotStarted.match(sLine)
                    if xMatch is not None:
                        print(f"[{_iLsfJobId}] bpeek: RESTART")
                        bRestart = True
                        break
                    # endif

                    xMatch = self._reBpeekJobNotFound.match(sLine)
                    if xMatch is not None:
                        print(f"[{_iLsfJobId}] bpeek: EXIT")
                        bExit = True
                        break
                    # endif
                # endfor
                if bExit is True or bRestart is False:
                    break
                # endif

                time.sleep(0.1)
            # endwhile
            if bExit is False:
                print(f"[{_iLsfJobId}] bpeek: START")
                if _xProcHandler.bStdOutAvailable is True:
                    for sLine in lLines:
                        _xProcHandler.StdOut(sLine)
                    # endfor
                # endif
                shell.ExecBashCmds(lCmds=[f"bpeek -f {_iLsfJobId}"], xProcHandler=_xProcHandler)
                print(f"[{_iLsfJobId}] bpeek: END")
            # endif
        else:
            raise RuntimeError(f"Launching LSF jobs not supported on system type '{sSystem}")
        # endif

    # enddef

    # ##################################################################################################
    def _DoTerminateLsfJob(self, *, _iLsfJobId: int):
        sSystem: str = platform.system()
        if sSystem == "Linux":
            shell.ExecBashCmds(lCmds=[f"bkill {_iLsfJobId}"])
        else:
            raise RuntimeError(f"Launching LSF jobs not supported on system type '{sSystem}")
        # endif

    # ##################################################################################################
    def _DoExecuteLsfJobs(self):
        # self._xAction.ExecuteJobList(self._lExecJobs, bPrintOutput=True)

        reJobSubmitted: re.Pattern = re.compile(r"Job\s<(?P<id>\d+)> is submitted")
        reBjobLine: re.Pattern = re.compile(
            r"^(?P<id>\d+)\s+(?P<user>[^\s]+)\s+(?P<state>[^\s]+)\s+"
            r"(?P<queue>[^\s]+)\s+(?P<from_host>[^\s]+)\s+"
            r"((?P<exec_host>[\w\-]+)|(?P<no_exec_host>\s{9}))\s+"
            r"(?P<job_name>[^\s]+)\s+(?P<month>\w+)\s+"
            r"(?P<day>\d+)\s+(?P<hour>\d+):(?P<minute>\d+)"
        )

        with self._lockJobData:
            self._dicLsfJobInfo: dict[int, CLsfJobInfo] = dict()
            self._dicJobIdxToLsfId: dict[int, int] = dict()
        # endwith

        # #######################################################################
        # Start submitting LSF jobs in separate thread.
        # This is the actual Catharsys launch call, which will only submit
        # the jobs to LSF. We still need to monitor the jobs' progress and
        # capture their output.
        threadSubmit = threading.Thread(target=lambda: self._DoExecuteJobs())
        threadSubmit.start()

        # #######################################################################
        # Run main loop
        # In this loop we:
        # - capture the output of the lsf job submission jobs and capture the
        #   LSF job ids to associate them with the job indices.
        # - capture the output of the bjobs parallel thread
        # - if a full bjobs output has been received, analyze whether new jobs
        #   are added, whether they are running or were removed.

        lBjobsText: list[str] = []
        setBpeekStartLsfJobId: set[int] = set()
        setBjobsFound: set[int] = set()
        setTerminatingLsfJob: set[int] = set()
        dicLoadLsfOutputTexts: dict[int, Path] = dict()

        bTestJobSubmisson: bool = True
        bTerminating: bool = False
        iEmptyBjobsOutputCount: int = 0

        while True:
            if self._evTerminateAll.is_set() and bTerminating is False:
                bTerminating = True
                if bTestJobSubmisson is True:
                    self._xLsfJobGrp.TerminateAll()
                    iTestCnt: int = 0
                    while not self._xLsfJobGrp.AllEnded() and iTestCnt < 50:
                        time.sleep(0.1)
                        iTestCnt += 1
                    # endwhile
                # endif
                self._xJobGrp.TerminateAll()
            # endif

            # while jobs are still being submitted capture their respective job ids
            if bTestJobSubmisson is True:
                self._xLsfJobGrp.UpdateProcOutput()
                setLsfOutputChanged: set[int] = self._xLsfJobGrp.GetProcOutputChanged()
                with self._lockJobData:
                    iJobIdx: int = None
                    for iJobIdx in setLsfOutputChanged:
                        xOut: CProcessOutput = self._xLsfJobGrp.GetProcOutput(iJobIdx)
                        sLine: str = None
                        for sLine in xOut:
                            # Look for lsf job id in job output
                            xMatch: re.Match = reJobSubmitted.match(sLine)
                            if xMatch is not None:
                                self._lLsfJobStatus[iJobIdx] = ELsfJobStatus.SUBMITTED
                                iLsfId: int = int(xMatch.group("id"))
                                self._dicLsfJobInfo[iLsfId] = CLsfJobInfo(
                                    iLsfId=iLsfId, iJobIdx=iJobIdx, eStatus=ELsfJobStatus.SUBMITTED
                                )
                                self._dicJobIdxToLsfId[iJobIdx] = iLsfId
                                # print(f"Submitted job {iJobIdx} with LSF index {iLsfId}")
                                xProcHandler = self._lJobProcHandler[iJobIdx]
                                if xProcHandler.bStdOutAvailable:
                                    xProcHandler.StdOut(f"--- Job {iJobIdx} submitted with id {iLsfId} ---\n")
                                    xProcHandler.StdOut("--- Full output available when job ended ---\n")
                                    xProcHandler.StdOut("------\n")
                                # endif
                                break
                            # endif
                        # endfor stdout lines
                    # endfor jobs with output
                # endwith lock
                if len(setLsfOutputChanged) == 0 and not threadSubmit.is_alive():
                    bTestJobSubmisson = False
                    # print("! Job Submission finished")
                # endif
            # endif

            lBjobsText = self._DoExecuteSingleBjobs()
            setBjobsFound.clear()

            # if bBjobsStartFound is True and bBjobsEndFound is True:
            for sLine in lBjobsText:
                # print(f"BJOB: {sLine}")
                xMatch = reBjobLine.match(sLine)
                if xMatch is None:
                    # print("> no job info line")
                    continue
                # endif
                iLsfId = int(xMatch.group("id"))
                if iLsfId not in self._dicLsfJobInfo:
                    # print(f"> LSF Job id {iLsfId} not in list of submitted jobs")
                    continue
                # endif

                setBjobsFound.add(iLsfId)
                # print(f"Found bjob {iLsfId}")

                xLsfJobInfo: CLsfJobInfo = self._dicLsfJobInfo[iLsfId]
                sState = xMatch.group("state")
                if sState == "PEND" and xLsfJobInfo.eStatus != ELsfJobStatus.PENDING:
                    # print("State PENDING")
                    with self._lockJobData:
                        xLsfJobInfo.eStatus = ELsfJobStatus.PENDING
                        self._lJobStatus[xLsfJobInfo.iJobIdx] = EJobStatus.STARTING
                        self._setJobStatusChanged.add(xLsfJobInfo.iJobIdx)
                    # endwith lock
                elif sState == "RUN" and xLsfJobInfo.eStatus in [
                    ELsfJobStatus.PENDING,
                    ELsfJobStatus.SUBMITTED,
                ]:
                    # print("State change to RUNNING")
                    setBpeekStartLsfJobId.add(iLsfId)
                    with self._lockJobData:
                        xLsfJobInfo.eStatus = ELsfJobStatus.RUNNING
                        xLsfJobInfo.sExecHost = xMatch.group("exec_host")
                        self._lJobStatus[xLsfJobInfo.iJobIdx] = EJobStatus.RUNNING
                        self._setJobStatusChanged.add(xLsfJobInfo.iJobIdx)
                    # endwith lock
                # endif

                self._lLsfJobStatus[xLsfJobInfo.iJobIdx] = xLsfJobInfo.eStatus

                if not isinstance(xLsfJobInfo.sUser, str):
                    with self._lockJobData:
                        xLsfJobInfo.sUser = xMatch.group("user")
                        xLsfJobInfo.sFromHost = xMatch.group("from_host")
                        xLsfJobInfo.sQueue = xMatch.group("queue")
                        xLsfJobInfo.sJobName = xMatch.group("job_name")

                        sMonth: str = xMatch.group("month")
                        sDay: str = xMatch.group("day")
                        sHour: str = xMatch.group("hour")
                        sMinute: str = xMatch.group("minute")

                        sDate: str = f"{sMonth} {sDay} {sHour}:{sMinute}"
                        xLsfJobInfo.dtLaunch = datetime.strptime(sDate, "%b %d %H:%M")
                    # endwith lock
                # endif

                # print(f"{iLsfId} [{xLsfJobInfo.iJobIdx}]: {xLsfJobInfo.eStatus} ({sState})")
            # endfor bjob lines
            # bBjobsStartFound = False
            # bBjobsEndFound = False
            lBjobsText.clear()

            # Check whether jobs that were previously started are no longer in bjobs output
            for iLsfId in self._dicLsfJobInfo:
                xLsfJobInfo = self._dicLsfJobInfo[iLsfId]
                if iLsfId not in setBjobsFound and xLsfJobInfo.eStatus in [
                    ELsfJobStatus.PENDING,
                    ELsfJobStatus.RUNNING,
                ]:
                    if xLsfJobInfo.eStatus == ELsfJobStatus.PENDING or iLsfId in setTerminatingLsfJob:
                        xLsfJobInfo.eStatus = ELsfJobStatus.TERMINATED
                    else:
                        xLsfJobInfo.eStatus = ELsfJobStatus.ENDED
                    # endif

                    self._lLsfJobStatus[xLsfJobInfo.iJobIdx] = xLsfJobInfo.eStatus

                    with self._lockJobData:
                        if xLsfJobInfo.eStatus == ELsfJobStatus.TERMINATED:
                            self._lJobStatus[xLsfJobInfo.iJobIdx] = EJobStatus.TERMINATED
                        else:
                            self._lJobStatus[xLsfJobInfo.iJobIdx] = EJobStatus.ENDED
                        # endif
                        self._setJobStatusChanged.add(xLsfJobInfo.iJobIdx)

                        xPrj: CProject = self._xAction.xProject
                        xWorkspace: CWorkspace = xPrj.xWorkspace
                        pathLsf: Path = xWorkspace.pathWorkspace / "lsf" / f"{iLsfId}"
                        dicLoadLsfOutputTexts[xLsfJobInfo.iJobIdx] = pathLsf
                    # endwith

                    # print(f"Job {xLsfJobInfo.iJobIdx} with LSF id {iLsfId} ENDED with state {xLsfJobInfo.eStatus}")
                # endif
            # endfor

            self.UpdateLsfTextFiles(dicLoadLsfOutputTexts)

            # This is a fail-safe, to end this thread, if the bjobs call
            # does not return output for any jobs that we have submitted
            # but the jos themselves are not triggered to end- for some
            # reason. In this case, the main loop ends if this happens
            # 10 times in a row.
            if len(setBjobsFound) == 0 and len(self._dicLsfJobInfo) > 0:
                iEmptyBjobsOutputCount += 1
            else:
                iEmptyBjobsOutputCount = 0
            # endif

            # Test whether all jobs have ended
            if (
                all((x == ELsfJobStatus.ENDED or x == ELsfJobStatus.TERMINATED) for x in self._lLsfJobStatus)
                or iEmptyBjobsOutputCount >= 10
            ):
                # print("All jobs ENDED")
                break
            # endif

            # Check whether any of the jobs was triggered to terminate
            # from external (e.g. the user). In this case, we also need to
            # kill the corresponding LSF job .
            xProcHandler: CProcessHandler = None
            for iJobIdx, xProcHandler in enumerate(self._lJobProcHandler):
                if xProcHandler.PollTerminate() is True:
                    iLsfId = self._dicJobIdxToLsfId.get(iJobIdx)
                    if iLsfId is not None and iLsfId not in setTerminatingLsfJob:
                        # print(f"Terminating LSF Job {iLsfId} [{iJobIdx}]")
                        setTerminatingLsfJob.add(iLsfId)
                        self._DoTerminateLsfJob(_iLsfJobId=iLsfId)
                    # endif
                # endif
            # endfor

            time.sleep(1)

        # endwhile main loop

        time.sleep(1)
        self.UpdateLsfTextFiles(dicLoadLsfOutputTexts)

        if iEmptyBjobsOutputCount >= 10:
            print("ERROR: bjobs shows no jobs but job management threads still running. Cleaning up...")
        # endif

    # enddef

    def UpdateLsfTextFiles(self, _dicLoadLsfOutputTexts: dict[int, Path]):
        lRemove: list[int] = []
        for iJobIdx, pathLsf in _dicLoadLsfOutputTexts.items():
            bOk = self.LoadLsfTextFiles(iJobIdx, pathLsf)
            if bOk is True:
                lRemove.append(iJobIdx)
            # endif
        # endfor
        for iJobIdx in lRemove:
            del _dicLoadLsfOutputTexts[iJobIdx]
        # endfor

    # enddef

    def LoadLsfTextFiles(self, _iJobIdx: int, _pathLsf: Path) -> bool:
        bOk = True
        if _pathLsf.exists():
            # print(f"LSF path exists: {pathLsf}")
            xProcHandler = self._lJobProcHandler[_iJobIdx]
            if xProcHandler.bStdOutAvailable:
                pathStdOut = _pathLsf / "stdout.txt"
                if pathStdOut.exists():
                    # print(">> stdout.txt exists")
                    sText = pathStdOut.read_text()
                    lLines = sText.splitlines(keepends=True)
                    xProcHandler.StdOut("<< output from stdout >>")
                    for sLine in lLines:
                        xProcHandler.StdOut(sLine)
                    # endfor
                else:
                    bOk = False
                # endif

                pathStdErr = _pathLsf / "stderr.txt"
                if pathStdErr.exists():
                    # print(">> stderr.txt exists")
                    sText = pathStdErr.read_text()
                    lLines = sText.splitlines(keepends=True)
                    xProcHandler.StdOut("<< output from stderr >>")
                    for sLine in lLines:
                        xProcHandler.StdOut(sLine)
                    # endfor
                else:
                    bOk = False
                # endif

            # endif
        else:
            bOk = False
        # endif

        return bOk

    # enddef


# endclass
