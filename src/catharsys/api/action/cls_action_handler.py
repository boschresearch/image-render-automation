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

import asyncio
import concurrent.futures

from anybase import config, plugin
from anybase.cls_any_error import CAnyError_Message
from typing import Optional, Callable, Any

from catharsys.api.cls_action import CAction
from catharsys.config.cls_job import CConfigJob
from catharsys.config.cls_exec_job import CConfigExecJob

from anybase.cls_process_output import CProcessOutput

from .cls_job_status import EJobStatus
from .cls_action_executor import CActionExecutor


class CActionHandler:
    # ##################################################################################################
    def __init__(self, *, _xAction: CAction):
        self._xAction: CAction = _xAction
        self._dicExec: dict = None
        self._sExecType: str = None
        self._xLoop: asyncio.AbstractEventLoop = None

        self._funcCreateJobsStatus: Callable[[int, int], None] = None

        self._lExecJobs: list[CConfigExecJob] = []
        self._xActExec: CActionExecutor = None

    # enddef

    @property
    def xAction(self) -> CAction:
        return self._xAction

    # enddef

    @property
    def iJobCount(self) -> int:
        return len(self._lExecJobs)

    # enddef

    @property
    def sExecType(self) -> str:
        return self._sExecType

    # enddef

    # ##################################################################################################
    def GetJobConfig(self, iIdx: int) -> CConfigExecJob:
        return self._lExecJobs[iIdx]

    # enddef

    # ##################################################################################################
    def TerminateAll(self):
        self._xActExec.TerminateAll()

    # enddef

    # ##################################################################################################
    def TerminateJob(self, iJobId: int):
        self._xActExec.TerminateJob(iJobId)

    # enddef

    # ##################################################################################################
    def GetJobInfo(self, iIdx: int) -> dict[str, Any]:
        if self._xActExec is None:
            return dict(Status="n/a")
        # endif
        return self._xActExec.GetJobInfo(iIdx)

    # enddef

    # ##################################################################################################
    def UpdateJobOutput(self, *, _iMaxTime_ms: int = 100):
        self._xActExec.UpdateJobOutput(_iMaxTime_ms=_iMaxTime_ms)

    # enddef

    # ##################################################################################################
    def GetJobOutputTypes(self) -> list[str]:
        return self._xActExec.GetJobOutputTypes()

    # enddef

    # ##################################################################################################
    def GetJobOutput(self, iIdx: int, *, _sType: str = None) -> CProcessOutput:
        return self._xActExec.GetJobOutput(iIdx, _sType=_sType)

    # enddef

    # ##################################################################################################
    def GetJobStatus(self, iIdx: int) -> EJobStatus:
        return self._xActExec.GetJobStatus(iIdx)

    # enddef

    # ##################################################################################################
    def GetJobEndMessage(self, iIdx: int) -> str:
        return self._xActExec.GetJobEndMessage(iIdx)

    # enddef

    # ##################################################################################################
    def GetJobStatusChanged(self, *, _bClear: bool = True) -> set[int]:
        return self._xActExec.GetJobStatusChanged()

    # enddef

    # ##################################################################################################
    def GetJobOutputChanged(self, *, _bClear: bool = True) -> set[int]:
        return self._xActExec.GetJobOutputChanged()

    # enddef

    # ##################################################################################################
    def _Callback_DoCreateJobsStatus(self, iIdx: int, iCnt: int):
        # print(f"DoCreateJob: Status Update: {iIdx}, {iCnt}")
        if self._funcCreateJobsStatus is not None:
            self._xLoop.call_soon_threadsafe(lambda iIdx, iCnt: self._funcCreateJobsStatus(iIdx, iCnt), iIdx, iCnt)
        # endif

    # enddef

    # ##################################################################################################
    def _DoCreateJobs(self) -> CConfigJob:
        # print("DoCreateJobs: START")
        xCfgJob: CConfigJob = self._xAction.GetJobConfig(
            _funcStatus=lambda iIdx, iCnt: self._Callback_DoCreateJobsStatus(iIdx, iCnt)
        )

        # print("DoCreateJobs: END")
        return xCfgJob

    # enddef

    # ##################################################################################################
    async def CreateJobs(self, *, _funcStatus: Optional[Callable[[int, int], None]] = None) -> CConfigJob:
        self._xLoop = asyncio.get_running_loop()
        self._funcCreateJobsStatus = _funcStatus

        xCfgJob: CConfigJob = None
        with concurrent.futures.ThreadPoolExecutor() as xPool:
            xCfgJob = await self._xLoop.run_in_executor(xPool, lambda: self._DoCreateJobs())
        # endwith

        self._funcCreateJobsStatus = None
        self._xLoop = None

        return xCfgJob

    # enddef

    # ##################################################################################################
    async def Launch(
        self,
        *,
        _funcCreateJobsStatus: Optional[Callable[[int, int], None]] = None,
        _funcJobExecStart: Optional[Callable[[None], None]] = None,
        _funcJobExecEnd: Optional[Callable[[None], None]] = None,
    ):
        xCfgJob = await self.CreateJobs(_funcStatus=_funcCreateJobsStatus)

        self._lExecJobs = self._xAction.GetExecJobConfigList(xCfgJob)

        self._dicExec = xCfgJob.dicData["mExec"]
        dicDti: dict = config.CheckConfigType(self._dicExec, "/catharsys/exec/*:*")
        if dicDti["bOK"] is False:
            raise RuntimeError("Invalid execution configuration for action")
        # endif

        self._xLoop = asyncio.get_running_loop()

        try:
            self._sExecType = "/".join(dicDti["lCfgType"][3:])
            sActExecDti: str = f"/catharsys/action-handler/executor/{self._sExecType}:1"
            epActExec = plugin.SelectEntryPointFromDti(
                sGroup="catharsys.action_handler.executors", sTrgDti=sActExecDti, sTypeDesc="Action Executor"
            )
            clsActionExecutor: type[CActionExecutor] = epActExec.load()
            self._xActExec: CActionExecutor = clsActionExecutor(_xAction=self._xAction, _lExecJobs=self._lExecJobs)
            await self._xActExec.Execute(_funcJobExecStart=_funcJobExecStart, _funcJobExecEnd=_funcJobExecEnd)
        except Exception as xEx:
            raise CAnyError_Message(sMsg="Error launching jobs", xChildEx=xEx)
        finally:
            self._xLoop = None
        # endtry

    # enddef


# endclass
