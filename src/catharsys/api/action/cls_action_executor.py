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

from typing import Optional, Callable, Any

from anybase.cls_process_output import CProcessOutput

from catharsys.api.cls_action import CAction
from catharsys.config.cls_exec_job import CConfigExecJob

from .cls_job_status import EJobStatus


class CActionExecutor:
    def __init__(self, *, _xAction: CAction, _lExecJobs: list[CConfigExecJob]):
        self._lExecJobs: list[CConfigExecJob] = _lExecJobs
        self._xAction: CAction = _xAction

    # enddef

    # ##################################################################################################
    def GetJobInfo(self, iIdx: int) -> dict[str, Any]:
        pass

    # enddef

    # ##################################################################################################
    def UpdateJobOutput(self, *, _iMaxTime_ms: int = 100):
        pass

    # enddef

    # ##################################################################################################
    def TerminateAll(self):
        pass

    # enddef

    # ##################################################################################################
    def TerminateJob(self, iJobId: int):
        pass

    # enddef

    # ##################################################################################################
    def GetJobOutputTypes(self) -> list[str]:
        pass

    # enddef

    # ##################################################################################################
    def GetJobOutput(self, iIdx: int, *, _sType: str = None) -> CProcessOutput:
        pass

    # enddef

    # ##################################################################################################
    def GetJobStatus(self, iIdx: int) -> EJobStatus:
        pass

    # enddef

    # ##################################################################################################
    def GetJobStatusChanged(self, *, _bClear: bool = True) -> set[int]:
        pass

    # enddef

    # ##################################################################################################
    def GetJobEndMessage(self, iIdx: int) -> str:
        pass

    # enddef

    # ##################################################################################################
    def GetJobOutputChanged(self, *, _bClear: bool = True) -> set[int]:
        pass

    # enddef

    # ##################################################################################################
    async def Execute(
        self,
        *,
        _funcJobExecStart: Optional[Callable[[None], None]] = None,
        _funcJobExecEnd: Optional[Callable[[None], None]] = None,
    ):
        pass

    # enddef


# endclass
