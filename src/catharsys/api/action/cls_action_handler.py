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
    """This class creates and manages a set of execution jobs for an action.
    This works following a polling paradigm: you can check what the state of a job is
    and whether it has new output and then call a function to get that updated output.
    """

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
        """Returns the action object this instance was created with

        Returns
        -------
        CAction
            The action object
        """
        return self._xAction

    # enddef

    @property
    def iJobCount(self) -> int:
        """The number of jobs created.

        Returns
        -------
        int
            The number of jobs.
        """
        return len(self._lExecJobs)

    # enddef

    @property
    def sExecType(self) -> str:
        """This is the last part of the DTI string for the action executor.
            For example, if the DTI is '/catharsys/exec/python/lsf:2.0', this
            property returns 'lsf'.

        Returns
        -------
        str
            The execution type
        """
        return self._sExecType

    # enddef

    # ##################################################################################################
    def GetJobConfig(self, iIdx: int) -> CConfigExecJob:
        """Get a job configuration

        Parameters
        ----------
        iIdx : int
            Index of the job

        Returns
        -------
        CConfigExecJob
            The job execution configuration instance. See CConfigExecJob for more information.
        """
        return self._lExecJobs[iIdx]

    # enddef

    # ##################################################################################################
    def TerminateAll(self):
        """Terminate all running jobs."""
        self._xActExec.TerminateAll()

    # enddef

    # ##################################################################################################
    def TerminateJob(self, iJobId: int):
        """Terminate a specific job.

        Parameters
        ----------
        iJobId : int
            The job indes.
        """
        self._xActExec.TerminateJob(iJobId)

    # enddef

    # ##################################################################################################
    def GetJobInfo(self, iIdx: int) -> dict[str, Any]:
        """Get info for a specific job. The type of output depends on the executor.
            See modules 'cls_action_executor_lsf.py' and 'cls_action_executor_std.py' for more details.

        Parameters
        ----------
        iIdx : int
            The job id.

        Returns
        -------
        dict[str, Any]
            Job information
        """
        if self._xActExec is None:
            return dict(Status="n/a")
        # endif
        return self._xActExec.GetJobInfo(iIdx)

    # enddef

    # ##################################################################################################
    def UpdateJobOutput(self, *, _iMaxTime_ms: int = 100):
        """Updates job outputs for all jobs that have new output.

        Parameters
        ----------
        _iMaxTime_ms : int, optional
            Maximal time in milliseconds for which to poll job output before returning, by default 100
        """
        self._xActExec.UpdateJobOutput(_iMaxTime_ms=_iMaxTime_ms)

    # enddef

    # ##################################################################################################
    def GetJobOutputTypes(self) -> list[str]:
        """Get the types of output a job can generate. This depends on the specific executor. For example,
        the LSF executor can return output types 'Standard' and 'Error', which are the outputs of the pipes
        'stdout' and 'stderr'. You can then explicitly load the output from one of these types with the
        function GetJobOutput().

        Returns
        -------
        list[str]
            A list of job output type id strings.
        """
        return self._xActExec.GetJobOutputTypes()

    # enddef

    # ##################################################################################################
    def GetJobOutput(self, iIdx: int, *, _sType: str = None) -> CProcessOutput:
        """Get the output for a specific job and output type. The returned value is of type 'CProcessOutput'
        which is also an iterator that will only iterate over the lines that have been added since the last
        time it was used.

        Parameters
        ----------
        iIdx : int
            The job id.
        _sType : str, optional
            The job output type (see GetJobOutputTypes()), by default None, in which case the executor chooses
            a default type.

        Returns
        -------
        CProcessOutput
            Iterator class over newly added output.
        """
        return self._xActExec.GetJobOutput(iIdx, _sType=_sType)

    # enddef

    # ##################################################################################################
    def GetJobStatus(self, iIdx: int) -> EJobStatus:
        """Get the status of a job.

        Parameters
        ----------
        iIdx : int
            The job id.

        Returns
        -------
        EJobStatus
            The job status.
        """
        return self._xActExec.GetJobStatus(iIdx)

    # enddef

    # ##################################################################################################
    def GetJobEndMessage(self, iIdx: int) -> str:
        """Get the job end message. If a job was run locally and an error occured, this contains the
        error message. For an LSF job this contains only errors that occured in the job generation process.
        Errors the LSF job itself generated have to be read from the 'Error' output of the job.

        Parameters
        ----------
        iIdx : int
            The job id.

        Returns
        -------
        str
            The end message.
        """
        return self._xActExec.GetJobEndMessage(iIdx)

    # enddef

    # ##################################################################################################
    def GetJobStatusChanged(self, *, _bClear: bool = True) -> set[int]:
        """A set of job ids, whose status has changed.

        Parameters
        ----------
        _bClear : bool, optional
            If true clears the status changed flag for all jobs after this call, by default True

        Returns
        -------
        set[int]
            A set of job ids.
        """
        return self._xActExec.GetJobStatusChanged(_bClear=_bClear)

    # enddef

    # ##################################################################################################
    def GetJobOutputChanged(self, *, _bClear: bool = True) -> set[int]:
        """A set of job ids, that have generated new output.

        Parameters
        ----------
        _bClear : bool, optional
            If true clears the output changed flag for all jobs after this call, by default True

        Returns
        -------
        set[int]
            A set of job ids.
        """
        return self._xActExec.GetJobOutputChanged(_bClear=_bClear)

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
        """Create all job configurations. This can be quite time consuming.
        This function is also called from the Launch() function.

        Parameters
        ----------
        _funcStatus : Optional[Callable[[int, int], None]], optional
            A callback function that is called when the creation status changes, by default None

        Returns
        -------
        CConfigJob
            The complete job configuration.
        """
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
        """This function launches the action that was passed in with the class constructor.
        The output and status of the jobs is handled via the GetJobOutput() and GetJobStatus() functions,
        as this will happen in separate processes.
        The creation of all job configurations and the launching and ending of all jobs, is handled in this thread,
        and feedback is available via callback functions.

        Parameters
        ----------
        _funcCreateJobsStatus : Optional[Callable[[int, int], None]], optional
            Returns the status of the configuration creation. The first argument is the current configuration
            index and the second argument the total number of configuration that are generated, by default None
        _funcJobExecStart : Optional[Callable[[None], None]], optional
            Callback function, called after all configurations have been generated and before the jobs are launched, by default None
        _funcJobExecEnd : Optional[Callable[[None], None]], optional
            Callback function, called after all jobs have finished, by default None

        Raises
        ------
        RuntimeError
            For errors during configuration generation
        CAnyError_Message
            For exceptions thrown by the executor function.
        """
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
