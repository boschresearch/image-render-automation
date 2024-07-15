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

import re
from pathlib import Path
from typing import Iterator

from catharsys.config.cls_variant_group import CVariantGroup
from catharsys.config.cls_variant_project import CVariantProject
from catharsys.config.cls_variant_trial import CVariantTrial

from .cls_products import CProducts
from .cls_path_structure import CPathVar, EPathVarType, CPathVarHandlerResult
from .cls_node import ENodeType


class CVariantGroupProducts(CProducts):
    def __init__(self, *, _xVariantGroup: CVariantGroup):
        pathVariantOutput: Path = _xVariantGroup.xProject.xConfig.pathOutput / _xVariantGroup.sGroup
        pathVariantOutput.mkdir(parents=True, exist_ok=True)
        super().__init__(_prjX=_xVariantGroup.xProject, _pathOutput=pathVariantOutput)
        self._xVarGrp: CVariantGroup = _xVariantGroup
        self._reGroup: re.Pattern = re.compile(f"{self._xVarGrp.sGroup}-(\\d+)-(\\d+)")
        self.RegisterSystemVar(
            CPathVar(
                sId="variant",
                sName="Configuration Variant",
                eType=EPathVarType.SYSTEM,
                eNodeType=ENodeType.PATH,
                funcHandler=self._OnVarVariant,
            )
        )

        self.RegisterSystemVar(
            CPathVar(
                sId="my-variant",
                sName="Configuration Variant",
                eType=EPathVarType.SYSTEM,
                eNodeType=ENodeType.PATH,
                funcHandler=self._OnVarMyVariant,
                funcLabel=self._OnVarMyVariantLabel,
            )
        )

    # enddef

    @property
    def xVariantGroup(self) -> CVariantGroup:
        return self._xVarGrp

    # enddef

    # ######################################################################################################
    def _OnVarVariant(self, _pathScan: Path) -> Iterator[CPathVarHandlerResult]:
        if _pathScan is None:
            raise RuntimeError("Path variable 'variant' must not be the first element of a path structure")
        # endif
        reGroup: re.Pattern = re.compile("(\\w+)-(\\d+)-(\\d+)")
        # reGroup: re.Pattern = re.compile(f"{self._xVarGrp.sGroup}-(\\d+)-(\\d+)")

        for pathItem in _pathScan.iterdir():
            xMatch = reGroup.fullmatch(pathItem.name)
            if not pathItem.is_dir() or xMatch is None:
                continue
            # endif
            yield CPathVarHandlerResult(pathItem, pathItem.name, (xMatch.group(1), xMatch.group(2), xMatch.group(3)))
        # endfor

    # enddef

    # ######################################################################################################
    def _OnVarMyVariant(self, _pathScan: Path) -> Iterator[CPathVarHandlerResult]:
        if _pathScan is None:
            raise RuntimeError("Path variable 'variant' must not be the first element of a path structure")
        # endif

        for pathItem in _pathScan.iterdir():
            xMatch = self._reGroup.fullmatch(pathItem.name)
            if not pathItem.is_dir() or xMatch is None:
                continue
            # endif
            yield CPathVarHandlerResult(
                pathItem, pathItem.name, (self._xVarGrp.sGroup, xMatch.group(1), xMatch.group(2))
            )
        # endfor

    # enddef

    # ######################################################################################################
    def _GetShortInfo(self, _sInfo: str, _iId: int) -> str:
        sInfo = _sInfo
        if ":" in sInfo:
            sInfo = sInfo[0 : sInfo.index(":")]
        elif "." in sInfo:
            sInfo = sInfo[0 : sInfo.index(".")]
        # endif
        if len(sInfo) == 0:
            sInfo = f"{_iId}"
        # endif
        return sInfo

    # endif

    # ######################################################################################################
    def _OnVarMyVariantLabel(self, _xPathVar: CPathVar, _sValue: str) -> str:
        xMatch = self._reGroup.fullmatch(_sValue)
        if xMatch is None:
            return
        # endif

        iPrjVarId: int = int(xMatch.group(1))
        iTrialVarId: int = int(xMatch.group(2))

        xPrjVar: CVariantProject = self._xVarGrp.GetProjectVariant(iPrjVarId)
        xTrialVar: CVariantTrial = xPrjVar.GetTrialVariant(iTrialVarId)

        sPrjInfo: str = self._GetShortInfo(xPrjVar.sInfo, iPrjVarId)
        sTrialInfo: str = self._GetShortInfo(xTrialVar.sInfo, iTrialVarId)

        return f"{sPrjInfo}: {sTrialInfo}"

    # enddef


# endclass
