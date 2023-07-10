###
# Author: Christian Perwass (CR/AEC5)
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
import copy
from dataclasses import dataclass
from typing import Optional

from pathlib import Path
from anybase import config

from .cls_workspace import CWorkspace


# #####################################################################################
class CTrialGroup:
    def __init__(self, *, _iId: int = None, _sName: str = None, _sInfo: str = None, _sSourceFile: str = None):
        self.iId: int = _iId
        self.sSrcFile: str = _sSourceFile
        self.dicVarFiles: dict[int, str] = None

    # enddef


# endclass


# #####################################################################################
class CLaunchGroup:
    def __init__(self):
        self.pathSrc: Path = None
        self.pathGrp: Path = None

        self.iId: int = None
        self.iNextTrialGroupId: int = None
        self.sInfo: str = None
        self.sSrcFile: str = None
        self.sVarFile: str = None
        self.dicTrialGroups: dict[str, CTrialGroup] = None

    # enddef

    def FromConfig(self, _dicCfg: dict):
        pass

    # enddef

    def Create(self, *, _iId: int, _sInfo: str, _pathSrc: Path, _pathGrp: Path, _sSrcFile: str):
        pass

    # enddef


# endclass


# #####################################################################################
# This class handles workspace variants.
# In particular, variants of the launch and trial files are handled.
# The organizational structure of variants is:
#   - group 1
#       - launch variant 1
#           - launch file
#           - trial group 1
#               - source trial file
#               - list of variant trial files
#           - trial group 2
#               - source trial file
#               - list of variant trial files
#       - launch variant 2
#           [...]
#   [...]
#
# All variants are stored in a workspace.
# For each variant an appropriate instance of CWorkspace can be returned,
#   which contains the active name of the launch file for the current variant.
#   The launch file variant contains the same trial file names of the currently
#   active trial group variant.
#
class CVariantGroup:
    c_reFileGrpLaunch = re.compile(r"g(?P<group>\d+)-l(?P<launch>\d+).json")
    c_reFileGrpTrial = re.compile(r"g(?P<group>\d+)-l(?P<launch>\d+)-t(?P<trial>\d+).json")

    def __init__(
        self,
    ):
        self._wsMain: CWorkspace = None
        self._sGroup: str = None

        self._sInfo: str = None
        self._iNextLaunchGroupId: int = None
        self._dicLaunchGroups: dict[int, CLaunchGroup] = None

    # enddef

    # ############################################################################################
    def FromConfig(self, *, _wsX: CWorkspace, _sGroup: str, _dicCfg: dict):
        pass

    # enddef

    # ############################################################################################
    def Create(self, *, _wsX: CWorkspace, _sGroup: str, _sInfo: str):
        self._wsMain = _wsX
        self._sGroup = _sGroup
        self._sInfo = _sInfo
        self._iNextLaunchGroupId = 1

    # enddef

    # ############################################################################################
    def CreateGroup(self, _sGroup: str) -> CVariantGroup:
        dicGrp: dict = self._dicVarCfg["mGroups"].get(_sGroup)
        if isinstance(dicGrp, dict):
            raise RuntimeError(f"Variant group '{_sGroup}' already exists")
        # endif

        dicGrp = self._dicVarCfg["mGroups"][_sGroup] = {
            "sDTI": "/catharsys/variants/group:1.0",
            "sInfo": "n/a",
            "mLaunch": {},
        }
