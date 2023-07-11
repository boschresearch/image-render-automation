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
from anybase import config

from .cls_project import CProject
from .cls_workspace import CWorkspace
from ..config.cls_variant_group import CVariantGroup


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
class CVariants:
    c_sFolderVariants = "variants"
    c_sFileVariants = "variants.json"
    c_reFolderGrp = re.compile(r"g(?P<group>\d+)")

    def __init__(self, _prjX: CProject):
        self._xProject: CProject = _prjX
        self._dicGroupVariants: dict[str, CVariantGroup] = None

        dicVarCfg: dict = None
        if not self.pathVariantsConfig.exists():
            dicVarCfg = {"sDTI": "/catharsys/variants:1.0", "mGroups": {}}
            self.pathVariants.mkdir(parents=True, exist_ok=True)
            config.Save(self.pathVariantsConfig, dicVarCfg)
        else:
            dicVarCfg = config.Load(self.pathVariantsConfig, sDTI="/catharsys/variants:1")
            if "mGroups" not in dicVarCfg:
                raise RuntimeError("Element 'mGroups' missing in variants config")
            # endif
        # endif

        dicGroups: dict = dicVarCfg["mGroups"]
        self._dicGroupVariants = {}
        for sVarGrp in dicGroups:
            xVarGrp = CVariantGroup(self.pathVariants)
            xVarGrp.FromConfig(_prjX=self._xProject, _dicCfg=dicGroups[sVarGrp])
            self._dicGroupVariants[sVarGrp] = xVarGrp
        # endfor

    # enddef

    @property
    def xWorkspace(self) -> CWorkspace:
        return self._xProject.xWorkspace

    # enddef

    @property
    def pathWorkspace(self) -> Path:
        return self.xWorkspace.pathWorkspace

    # enddef

    @property
    def pathLaunch(self) -> Path:
        return self._xProject.xConfig.pathLaunch

    @property
    def pathVariants(self) -> Path:
        return self.pathLaunch / CVariants.c_sFolderVariants

    # enddef

    @property
    def pathVariantsConfig(self) -> Path:
        return self.pathVariants / CVariants.c_sFileVariants

    # enddef

    @property
    def lGroupNames(self) -> list[str]:
        return list(self._dicGroupVariants.keys())

    # enddef

    # ############################################################################################
    def HasGroup(self, _sGroup: str) -> bool:
        return _sGroup in self._dicGroupVariants

    # enddef

    # ############################################################################################
    def GetGroup(self, _sGroup: str) -> CVariantGroup:
        xGrp: CVariantGroup = self._dicGroupVariants.get(_sGroup)
        if not isinstance(xGrp, CVariantGroup):
            raise RuntimeError(f"Variant group '{_sGroup}' not available")
        # endif
        return xGrp

    # enddef

    # ############################################################################################
    def CreateGroup(self, _sGroup: str) -> CVariantGroup:
        if self.HasGroup(_sGroup):
            raise RuntimeError(f"Variant group '{_sGroup}' already exists")
        # endif

        xVarGrp: CVariantGroup = CVariantGroup(self.pathVariants)
        xVarGrp.Create(_prjX=self._xProject, _sGroup=_sGroup, _sInfo="n/a")

        self._dicGroupVariants[_sGroup] = xVarGrp

    # enddef

    # ############################################################################################
    # Updates all groups from the source launch and trial files
    def UpdateFromSource(self, *, _bOverwrite: Optional[bool] = False):
        self._xProject.Update()
        for sGroup in self._dicGroupVariants:
            self._dicGroupVariants[sGroup].UpdateFromSource(_bOverwrite=_bOverwrite)
        # endfor

    # enddef

    # ############################################################################################
    def Serialize(self, *, _bWriteToDisk: bool = True) -> dict:
        dicGroups = {}
        for sGroup in self._dicGroupVariants:
            dicGroups[sGroup] = self._dicGroupVariants[sGroup].Serialize()
        # endfor

        dicData = {
            "sDTI": "/catharsys/variants:1.0",
            "mGroups": dicGroups,
        }

        if _bWriteToDisk is True:
            config.Save(self.pathVariantsConfig, dicData)
        # endif

        return dicData

    # enddef


# endclass
