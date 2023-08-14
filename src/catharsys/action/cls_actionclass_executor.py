#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \cls_actionclass.py
# Created Date: Monday, June 13th 2022, 11:33:45 am
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

from typing import Optional

from catharsys.config.cls_project import CProjectConfig
from catharsys.config.cls_launch import CConfigLaunch
from catharsys.config.cls_job import CConfigJob
from catharsys.config.cls_exec_job import CConfigExecJob


##########################################################################################
class CActionClassExecutor:
    @property
    def xPrjCfg(self):
        return self._xPrjCfg

    @property
    def sAction(self):
        return self._sAction

    @property
    def dicActCfg(self):
        return self._dicActCfg

    @property
    def xCfgLaunch(self):
        return self._xCfgLaunch

    @property
    def dicActions(self):
        return self._dicActions

    @property
    def sActClsDti(self):
        return self._sActClsDti

    ######################################################################################
    def __init__(
        self,
        *,
        xPrjCfg: CProjectConfig,
        sAction: str,
        dicActCfg: dict,
        xCfgLaunch: CConfigLaunch,
        dicActArgsOverride: Optional[dict] = None
    ):
        self._xPrjCfg: CProjectConfig = xPrjCfg
        self._sAction: str = sAction
        self._dicActCfg: dict = dicActCfg
        self._xCfgLaunch: CConfigLaunch = xCfgLaunch
        self._dicActions: dict = xCfgLaunch.GetActionDict(dicConfigOverride=dicActArgsOverride)

        self._sActClsDti: str = self._dicActCfg.get("sDTI")

        ### DEBUG ###
        # print(self._dicActions)

    # enddef

    ######################################################################################
    def GetJobConfig(self) -> CConfigJob:
        return None

    # enddef

    ######################################################################################
    def GetExecJobConfigList(self, _xJob: CConfigJob) -> list[CConfigExecJob]:
        return None

    # enddef

    ######################################################################################
    def ExecuteJobList(self, _lExecJobs: list[CConfigExecJob]):
        return None

    # enddef

    ######################################################################################
    def Execute(self, *, bDoProcess: bool = True, dicDebug: bool = None) -> CConfigJob:
        return CConfigJob(sDTI="none")

    # enddef


# endclass
