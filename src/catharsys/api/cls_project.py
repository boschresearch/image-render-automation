#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \cls_project.py
# Created Date: Tuesday, June 7th 2022, 7:47:54 am
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


from typing import Optional, Union, ForwardRef
from pathlib import Path

from anybase import path as anypath
from anybase import config as anycfg

import catharsys.util.version
from catharsys.config.cls_project import CProjectConfig
from catharsys.config.cls_launch import CConfigLaunch

from .cls_action import CAction

TWorkspace = ForwardRef("Workspace")


#########################################################################
class CProject:
    @property
    def xConfig(self) -> CProjectConfig:
        return self._xPrjCfg

    @property
    def sId(self) -> str:
        return self._xPrjCfg.sLaunchFolderName

    @property
    def sInfo(self) -> str:
        return self._xLaunch.sInfo

    @property
    def lActions(self) -> list[str]:
        return self._lActionPaths

    @property
    def xWorkspace(self) -> TWorkspace:
        return self._xWorkspace

    @property
    def xConfig(self) -> CProjectConfig:
        return self._xPrjCfg

    @property
    def xLaunch(self) -> CConfigLaunch:
        return self._xLaunch

    #####################################################################
    def __init__(self, _xPrjCfg: CProjectConfig, *, xWorkspace: Optional[TWorkspace] = None):
        self._xWorkspace = xWorkspace
        self._xPrjCfg = _xPrjCfg
        self._xLaunch = CConfigLaunch()
        self._xLaunch.LoadFile(_xPrjCfg)
        self._lActionPaths = self._xLaunch.GetActionPaths()

    # enddef

    #####################################################################
    def GetActionInfo(self, _sAction: str):
        if not _sAction in self._lActionPaths:
            raise RuntimeError(f"Action '{_sAction}' not available in project '{self.sId}'")
        # endif
        return self._xLaunch.GetActionInfo(_sAction)

    # enddef

    #####################################################################
    def PrintActions(self):
        print(f"Actions of project '{self.sId}':")
        for sAction in self._lActionPaths:
            print("  - '{}': {}".format(sAction, self.GetActionInfo(sAction)))
        # endfor

    # enddef

    #####################################################################
    def Action(self, _sAction: str, *, _dicConfigOverride: dict = None) -> CAction:
        if not _sAction in self._lActionPaths:
            raise RuntimeError(f"Action '{_sAction}' not available in project '{self.sId}'")
        # endif

        return CAction(_sAction, self, dicConfigOverride=_dicConfigOverride)

    # enddef


# endclass
