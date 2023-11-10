#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \dev_api_ison.py
# Created Date: Friday, June 3rd 2022, 3:38:06 pm
# Author: Christian Perwass (CR/AEC5)
# <LICENSE id="Apache-2.0">
#
#   Image-Render Automation Functions module
#   Copyright 2022 Robert Bosch GmbH and its subsidiaries
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
import catharsys.api as capi
from catharsys.api.action.cls_action_handler import CActionHandler, EJobStatus, CProcessOutput

bJobsStarted = False


def HandleCreateJobsStatus(iIdx: int, iCnt: int):
    print(f"Creating config {iIdx} of {iCnt}")


# enddef


def CreateHandleStartExec(evStarted: asyncio.Event):
    def HandleStartExec():
        print("Starting execution...")
        evStarted.set()

    # enddef

    return HandleStartExec


# enddef


def HandleEndExec():
    print("Ended execution")


# enddef


async def MainLoop():
    global bJobsStarted
    xWs = capi.CWorkspace()
    xWs.PrintInfo()

    xPrj = xWs.Project("anytruth/test-01")
    xPrj.PrintActions()

    xAction = xPrj.Action("render/std")

    xActHandler = CActionHandler(_xAction=xAction)

    # We will use this event to signal that all configurations have been generated
    evStarted = asyncio.Event()

    print("Starting Launch Task")
    xExecTask = asyncio.create_task(
        xActHandler.Launch(
            _funcCreateJobsStatus=HandleCreateJobsStatus,
            _funcJobExecStart=CreateHandleStartExec(evStarted),
            _funcJobExecEnd=HandleEndExec,
        )
    )

    # wait for the actual render jobs to be launched
    await evStarted.wait()

    print("Starting loop")
    while True:
        # print("Testing job status...")
        xActHandler.UpdateJobOutput(_iMaxTime_ms=100)
        setJobStatusChanged = xActHandler.GetJobStatusChanged()
        setJobOutputChanged = xActHandler.GetJobOutputChanged()
        # print("...done")

        for iJobId in setJobStatusChanged:
            eJobStatus = xActHandler.GetJobStatus(iJobId)
            print(f">>> Job {iJobId}: {eJobStatus.name}")
        # endfor

        for iJobId in setJobOutputChanged:
            xProcOut = xActHandler.GetJobOutput(iJobId)
            for sLine in xProcOut:
                print(f"[{iJobId}]> {sLine}", end="")
            # endfor
        # endfor

        setDone, setPending = await asyncio.wait((xExecTask,), timeout=1)
        if len(setDone) > 0:
            break
        # endif
    # endif

    if xExecTask.exception() is not None:
        print("EXCEPTION:")
        print(str(xExecTask.exception()))
    # endif

    print("Finished")


# enddef

asyncio.run(MainLoop())
