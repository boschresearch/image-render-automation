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
from typing import Optional

from pathlib import Path
from anybase import config, convert

from ..api.cls_project import CProject
from .cls_variant_launch import CVariantLaunch
from .cls_variant_trial import CVariantTrial


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
# For each variant an appropriate instance of CProject can be returned,
#   which contains the active name of the launch file for the current variant.
#   The launch file variant contains the same trial file names of the currently
#   active trial group variant.
#
class CVariantGroup:
    c_reFileGrpLaunch = re.compile(r"g(?P<group>\d+)-l(?P<launch>\d+).json")
    c_reFileGrpTrial = re.compile(r"g(?P<group>\d+)-l(?P<launch>\d+)-t(?P<trial>\d+).json")

    def __init__(self, _pathVariants: Path):
        self._pathVariants: Path = _pathVariants
        self._pathGroup: Path = None

        self._xProject: CProject = None
        self._sGroup: str = None

        self._sInfo: str = None
        self._iNextLaunchVarId: int = None
        self._dicLaunchVariants: dict[int, CVariantLaunch] = None

        self._pathVariants.mkdir(parents=True, exist_ok=True)

    # enddef

    @property
    def lLaunchVariantIds(self) -> list[int]:
        return list(self._dicLaunchVariants.keys())

    # enddef

    # ############################################################################################
    def FromConfig(self, *, _prjX: CProject, _dicCfg: dict):
        _sGroup: str = _dicCfg.get("sName")
        if _sGroup is None:
            raise RuntimeError("Element 'sGroup' missing in configuration")
        # endif

        pathGroup: Path = self._pathVariants / _sGroup
        if not pathGroup.exists():
            raise RuntimeError(f"Group folder '{_sGroup}' does not exists at: {(pathGroup.as_posix())}")
        # endif
        self._pathGroup = pathGroup

        self._xProject = _prjX
        self._sGroup = _sGroup
        self._sInfo = convert.DictElementToString(_dicCfg, "sInfo", sDefault="")
        self._iNextLaunchVarId = convert.DictElementToInt(_dicCfg, "iNextLaunchVarId")

        self._dicLaunchVariants = {}
        dicCfgLaunchVars = _dicCfg.get("mLaunchVariants")
        if not isinstance(dicCfgLaunchVars, dict):
            raise RuntimeError("Element 'mLaunchVariants' missing in variants group configuration")
        # endif

        sLaunchVarId: str = None
        for sLaunchVarId in dicCfgLaunchVars:
            iLaunchVarId: int = int(sLaunchVarId)
            xVarLaunch = CVariantLaunch()
            xVarLaunch.FromConfig(
                _pathGroup=self._pathGroup, _prjX=self._xProject, _dicCfg=dicCfgLaunchVars[sLaunchVarId]
            )
            self._dicLaunchVariants[iLaunchVarId] = xVarLaunch
        # endfor

    # enddef

    # ############################################################################################
    def Create(self, *, _prjX: CProject, _sGroup: str, _sInfo: str):
        pathGroup: Path = self._pathVariants / _sGroup
        if pathGroup.exists():
            raise RuntimeError(f"Variant group folder already exists: {(pathGroup.as_posix())}")
        # endif
        self._pathGroup = pathGroup
        self._pathGroup.mkdir(parents=True)

        self._xProject = _prjX
        self._sGroup = _sGroup
        self._sInfo = _sInfo
        self._iNextLaunchVarId = 1
        self._dicLaunchVariants = {}

        self.AddLaunchVariant()

    # enddef

    # ############################################################################################
    def AddLaunchVariant(self, *, _sInfo: str = "") -> int:
        iId = self._iNextLaunchVarId
        xVarLaunch = CVariantLaunch()
        xVarLaunch.Create(_iId=iId, _sInfo=_sInfo, _pathGroup=self._pathGroup, _prjX=self._xProject)
        self._dicLaunchVariants[iId] = xVarLaunch
        self._iNextLaunchVarId += 1

        return iId

    # enddef

    # ############################################################################################
    def GetLaunchVariant(self, _iId: int):
        return self._dicLaunchVariants.get(_iId)

    # enddef

    # ############################################################################################
    def UpdateFromSource(self, *, _bOverwrite: Optional[bool] = False):
        for iLaunchVarId in self._dicLaunchVariants:
            self._dicLaunchVariants[iLaunchVarId].UpdateFromSource(_bOverwrite=_bOverwrite)
        # endfor

    # enddef

    # ############################################################################################
    def Serialize(self) -> dict:
        dicLaunchVars = {}
        for iLaunchVarId in self._dicLaunchVariants:
            dicLaunchVars[iLaunchVarId] = self._dicLaunchVariants[iLaunchVarId].Serialize()
        # endfor

        dicData = {
            "sDTI": "/catharsys/variants/group:1.0",
            "sName": self._sGroup,
            "sInfo": self._sInfo,
            "iNextLaunchVarId": self._iNextLaunchVarId,
            "mLaunchVariants": dicLaunchVars,
        }

        return dicData

    # enddef
