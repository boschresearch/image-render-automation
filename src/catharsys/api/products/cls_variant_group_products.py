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

from .cls_products import CProducts
from .cls_path_structure import CPathVar, EPathVarType, CPathVarHandlerResult
from .cls_node import ENodeType


class CVariantGroupProducts(CProducts):
    def __init__(self, *, _xVariantGroup: CVariantGroup):
        super().__init__(_prjX=_xVariantGroup.xProject)
        self._xVarGrp: CVariantGroup = _xVariantGroup

        self.RegisterSystemVar(
            CPathVar(
                sId="variant",
                sName="Configuration Variant",
                eType=EPathVarType.SYSTEM,
                eNodeType=ENodeType.PATH,
                funcHandler=self._OnVarVariant,
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
        reGroup: re.Pattern = re.compile(f"{self._xVarGrp.sGroup}-(\\d+)-(\\d+)")

        for pathItem in _pathScan.iterdir():
            xMatch = reGroup.fullmatch(pathItem.name)
            if not pathItem.is_dir() or xMatch is None:
                continue
            # endif
            yield CPathVarHandlerResult(
                pathItem, pathItem.name, (self._xVarGrp.sGroup, xMatch.group(1), xMatch.group(2))
            )
        # endfor

    # enddef


# endclass
