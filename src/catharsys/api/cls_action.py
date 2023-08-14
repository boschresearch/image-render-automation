#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \cls_action.py
# Created Date: Friday, April 22nd 2022, 2:46:48 pm
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

import sys
import copy

from typing import Optional, Union, ForwardRef
from pathlib import Path

import ison
from anybase import file as anyfile
from catharsys.action.cls_actionfactory import CActionFactory
from catharsys.action.cls_actionclass_executor import CActionClassExecutor
from catharsys.config.cls_job import CConfigJob
from catharsys.config.cls_exec_job import CConfigExecJob
from catharsys.config.cls_project import CProjectConfig

TProject = ForwardRef("Project")


########################################################################################
class CAction:
    @property
    def sAction(self):
        return self._sAction

    @property
    def xProject(self):
        return self._xProject

    ####################################################################################
    def __init__(self, _sAction: str, _xProject: TProject, *, dicConfigOverride: Optional[dict] = None):
        self._sAction: str = None
        self._dicConfigOverride: dict = None
        self._xActFact: CActionFactory = None
        self._xProject: TProject = None
        self._xPrjCfg: CProjectConfig = None
        self._xAction: CActionClassExecutor = None

        self._sAction = _sAction
        self._dicConfigOverride = copy.deepcopy(dicConfigOverride)
        self._xProject = _xProject
        self._xPrjCfg = self._xProject.xConfig

        self._xActFact = CActionFactory(xPrjCfg=self._xPrjCfg)
        self._xAction = self._xActFact.CreateAction(sAction=self._sAction, dicConfigOverride=self._dicConfigOverride)
        self._xAction.Init()

    # enddef

    ####################################################################################
    def Launch(self, bPrintOutput=False) -> CConfigJob:
        if self._xAction is None:
            raise Exception("No action created")
        # endif

        xOrigStdOut = sys.stdout

        if not bPrintOutput:
            sFilename = "stdout_{0}.txt".format(self.sAction.replace("/", "_"))
            pathStdOutFile = self._xPrjCfg.pathLaunch / sFilename
            sys.stdout = pathStdOutFile.open("w")
        # endif

        xCfgJob = None

        try:
            xCfgJob = self._xAction.Execute()

        except Exception as xEx:
            print("Exception in running action:\n{0}".format(str(xEx)))
        finally:
            if not bPrintOutput:
                sys.stdout.close()
                sys.stdout = xOrigStdOut
                print("Action output written to: (use CTRL+LMB to open)\n{0}".format(pathStdOutFile.as_posix()))
            # endif
        # endexcept

        return xCfgJob

    # enddef

    ##########################################################################
    def GetJobConfig(self) -> CConfigJob:
        if self._xAction is None:
            raise Exception("No action created")
        # endif

        return self._xAction.GetJobConfig()

    # enddef

    ##########################################################################
    def GetExecJobConfigList(self, _xJobCfg: CConfigJob) -> list[CConfigExecJob]:
        if self._xAction is None:
            raise Exception("No action created")
        # endif

        return self._xAction.GetExecJobConfigList(_xJobCfg)

    # enddef

    ##########################################################################
    def ExecuteJobList(self, _lExecJobs: list[CConfigExecJob], bPrintOutput: bool = False):
        if self._xAction is None:
            raise Exception("No action created")
        # endif

        xOrigStdOut = sys.stdout

        if not bPrintOutput:
            sFilename = "stdout_{0}.txt".format(self.sAction.replace("/", "_"))
            pathStdOutFile = self._xPrjCfg.pathLaunch / sFilename
            sys.stdout = pathStdOutFile.open("w")
        # endif

        xCfgJob = None

        try:
            xCfgJob = self._xAction.ExecuteJobList(_lExecJobs)

        except Exception as xEx:
            print("Exception in running action:\n{0}".format(str(xEx)))
        finally:
            if not bPrintOutput:
                sys.stdout.close()
                sys.stdout = xOrigStdOut
                print("Action output written to: (use CTRL+LMB to open)\n{0}".format(pathStdOutFile.as_posix()))
            # endif
        # endexcept

        return xCfgJob

    # enddef


# endclass
