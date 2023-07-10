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
from pathlib import Path
from anybase import config

from .cls_workspace import CWorkspace
from .cls_variant_group import CVariantGroup


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
class CVariants:
    c_sFolderVariants = "variants"
    c_sFileVariants = "variants.json"
    c_reFolderGrp = re.compile(r"g(?P<group>\d+)")

    def __init__(self, _wsX: CWorkspace):
        self._wsMain: CWorkspace = _wsX
        self._dicVarCfg: dict = None
        self._dicVarGrp: dict[str, CVariantGroup] = None
        self._InitFromWorkspace()

    # enddef

    @property
    def pathWorkspace(self) -> Path:
        return self._wsMain.pathWorkspace

    # enddef

    @property
    def pathVariants(self) -> Path:
        return self.pathWorkspace / CVariants.c_sFolderVariants

    # enddef

    @property
    def pathVariantsConfig(self) -> Path:
        return self.pathVariants / CVariants.c_sFileVariants

    # enddef

    @property
    def lGroupNames(self) -> list[str]:
        return list(self._dicVarCfg["mGroups"].keys())

    # enddef

    # ############################################################################################
    def _InitFromWorkspace(self):
        if not self.pathVariantsConfig.exists():
            self._dicVarCfg = {"sDTI": "/catharsys/variants:1.0", "mGroups": {}}
            self.pathVariants.mkdir(parents=True, exist_ok=True)
            config.Save(self.pathVariantsConfig, self._dicVarCfg)
        else:
            self._dicVarCfg = config.Load(self.pathVariantsConfig, sDTI="/catharsys/variants:1")
            if "mGroups" not in self._dicVarCfg:
                raise RuntimeError("Element 'mGroups' missing in variants config")
            # endif
        # endif

        dicGroups: dict = self._dicVarCfg["mGroups"]
        self._dicVarGrp = {}
        for sVarGrp in dicGroups:
            self._dicVarGrp[sVarGrp] = CVariantGroup(self._wsMain, sVarGrp, dicGroups[sVarGrp])
        # endfor

        # dicFilesVarCfg = { "mGroups": {} }
        # dicGroups: dict = dicFilesVarCfg["mGroups"]
        # pathItem: Path = None
        # for pathItem in self.pathVariants.iterdir():
        #     if pathItem.is_dir():
        #         xMatch = CVariants.c_reFolderGrp.fullmatch(pathItem.name)
        #         if xMatch is not None:
        #             iGrpId = int(xMatch.group("group"))
        #             dicGrp: dict = dicGroups[iGrpId] = {}
        # # endfor

    # enddef

    # ############################################################################################
    def HasGroup(self, _sGroup: str) -> bool:
        return _sGroup in self._dicVarCfg["mGroups"]

    # enddef

    # ############################################################################################
    def GetGroup(self, _sGroup: str) -> CVariantGroup:
        xGrp: CVariantGroup = self._dicVarGrp.get(_sGroup)
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

        self._dicVarGrp[_sGroup] = CVariantGroup(self._wsMain, _sGroup)
    # enddef

# endclass
