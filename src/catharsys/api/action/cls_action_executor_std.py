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

from anybase.cls_any_error import CAnyError_Message
from typing import Optional, Callable, Any

from catharsys.api.cls_action import CAction
from catharsys.config.cls_exec_job import CConfigExecJob

from anybase.cls_process_group_handler import CProcessGroupHandler, EProcessStatus
from anybase.cls_process_output import CProcessOutput

from .cls_action_executor import CActionExecutor
from .cls_job_status import EJobStatus


class CActionExecutorStd(CActionExecutor):
    def __init__(self, *, _xAction: CAction, _lExecJobs: list[CConfigExecJob]):
        super().__init__(_xAction=_xAction, _lExecJobs=_lExecJobs)

        self._xLoop: asyncio.AbstractEventLoop = None
        self._xJobGrp: CProcessGroupHandler = CProcessGroupHandler()

        self._lJobState: list[EJobStatus] = []
        self._setJobStateChanged: set[int] = set()

        self._dicProcToJobStatus: dict[EProcessStatus, EJobStatus] = {
            EProcessStatus.NOT_STARTED: EJobStatus.NOT_STARTED,
            EProcessStatus.STARTING: EJobStatus.STARTING,
            EProcessStatus.RUNNING: EJobStatus.RUNNING,
            EProcessStatus.ENDED: EJobStatus.ENDED,
            EProcessStatus.TERMINATED: EJobStatus.TERMINATED,
        }

        self._dicJobStatusToText: dict[EJobStatus, str] = {
            EJobStatus.NOT_STARTED: "not started",
            EJobStatus.STARTING: "starting",
            EJobStatus.RUNNING: "running",
            EJobStatus.ENDED: "ended",
            EJobStatus.TERMINATED: "terminated",
        }

        self._lJobOutputTypes = ["Standard"]

    # enddef

    # ##################################################################################################
    def TerminateAll(self):
        self._xJobGrp.TerminateAll()

    # enddef

    # ##################################################################################################
    def TerminateJob(self, iJobId: int):
        self._xJobGrp.TerminateProc(iJobId)

    # enddef

    # ##################################################################################################
    def GetJobInfo(self, iIdx: int) -> dict[str, Any]:
        return dict(Status=self._dicJobStatusToText.get(self.GetJobStatus(iIdx)))

    # enddef

    # ##################################################################################################
    def UpdateJobOutput(self, *, _iMaxTime_ms: int = 100):
        self._xJobGrp.UpdateProcOutput(_iMaxTime_ms=_iMaxTime_ms)

    # enddef

    # ##################################################################################################
    def GetJobOutputTypes(self) -> list[str]:
        return self._lJobOutputTypes.copy()

    # enddef

    # ##################################################################################################
    def GetJobOutput(self, iIdx: int, *, _sType: str = None) -> CProcessOutput:
        return self._xJobGrp.GetProcOutput(iIdx)

    # enddef

    # ##################################################################################################
    def GetJobStatus(self, iIdx: int) -> EJobStatus:
        eJobStatus: EJobStatus = self._dicProcToJobStatus.get(self._xJobGrp.GetProcStatus(iIdx))
        return eJobStatus

    # enddef

    # ##################################################################################################
    def GetJobEndMessage(self, iIdx: int) -> str:
        return self._xJobGrp.GetProcEndMessage(iIdx)

    # enddef

    # ##################################################################################################
    def GetJobStatusChanged(self, *, _bClear: bool = True) -> set[int]:
        return self._xJobGrp.GetProcStatusChanged()

    # enddef

    # ##################################################################################################
    def GetJobOutputChanged(self, *, _bClear: bool = True) -> set[int]:
        return self._xJobGrp.GetProcOutputChanged()

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
        # print("Launch Local: START")
        # print(f"> Job Count: {(len(self._lExecJobs))}")

        self._xLoop = asyncio.get_running_loop()

        try:
            self._xJobGrp.Clear()
            self._lJobState = []
            self._setJobStateChanged = set()

            xJob: CConfigExecJob = None
            for iJobIdx, xJob in enumerate(self._lExecJobs):
                self._xJobGrp.AddProcessHandler(_iJobId=iJobIdx, _xProcHandler=xJob.xProcHandler)
                self._lJobState.append(EJobStatus.NOT_STARTED)
            # endfor

            if _funcJobExecStart is not None:
                _funcJobExecStart()
            # endif

            # print("> Starting thread")
            with concurrent.futures.ThreadPoolExecutor() as xPool:
                await self._xLoop.run_in_executor(xPool, lambda: self._DoExecuteJobs())
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


# endclass
