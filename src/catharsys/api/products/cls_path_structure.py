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

import copy
from pathlib import Path
from typing import Callable, Optional, Iterator, Any
from dataclasses import dataclass
import enum

from .cls_node import CNode, ENodeType


class EPathVarType(enum.Enum):
    FIXED = enum.auto()
    USER = enum.auto()
    SYSTEM = enum.auto()


# endclass


@dataclass
class CPathVarHandlerResult:
    pathScan: Path
    sName: str
    xData: Optional[Any] = None


# endclass


@dataclass
class CPathVar:
    sId: str
    sName: str
    eType: EPathVarType
    eNodeType: ENodeType
    funcHandler: Callable[[Path], Iterator[CPathVarHandlerResult]] = None


# endclass


class CPathStructure:
    def __init__(
        self,
        _sPathStruct: str,
        _eLastElementNodeType: ENodeType,
        *,
        _dicUserVars: Optional[dict] = None,
        _dicSystemVars: Optional[dict[str, CPathVar]] = None,
    ):
        self._sPathStruct: str = _sPathStruct
        self._eLastElementNodeType: ENodeType = _eLastElementNodeType
        self._lPathVars: list[str] = []
        self._dicVars: dict[str, CPathVar] = dict()
        self._dicSystemVars: dict[str, CPathVar] = None
        if _dicSystemVars is not None:
            self._dicSystemVars = copy.deepcopy(_dicSystemVars)
        # endif

        self._ParsePathStruct(_dicUserVars)

    # enddef

    @property
    def lPathVarIds(self) -> list[str]:
        return self._lPathVars

    # enddef

    @property
    def iPathVarCount(self) -> int:
        return len(self._lPathVars)

    # enddef

    @property
    def iMaxLevel(self) -> int:
        return len(self._lPathVars) - 1

    # enddef

    @property
    def dicVars(self) -> dict[str, CPathVar]:
        return self._dicVars

    # enddef

    def _ParsePathStruct(self, _dicUserVars: Optional[dict] = None):
        lItems: list[str] = self._sPathStruct.split("/")
        for iIdx, sItem in enumerate(lItems):
            bIsLastElement: bool = iIdx == len(lItems) - 1
            eNodeType: ENodeType = self._eLastElementNodeType if bIsLastElement else ENodeType.PATH

            sVarId: str = sItem
            if sItem.startswith("!"):
                sVarId = sItem[1:]
                if sVarId not in self._dicSystemVars:
                    raise RuntimeError(f"Unknown pre-defined path structure variable '{sVarId}'")
                # endif
                self._dicVars[sVarId] = self._dicSystemVars[sVarId]

            elif sItem.startswith("?"):
                sVarId = sItem[1:-1]
                if isinstance(_dicUserVars, dict) and sVarId in _dicUserVars:
                    self._dicVars[sVarId] = CPathVar(
                        sId=sVarId,
                        sName=_dicUserVars[sVarId].get("sName", sVarId),
                        eType=EPathVarType.USER,
                        eNodeType=eNodeType,
                    )
                else:
                    self._dicVars[sVarId] = CPathVar(
                        sId=sVarId, sName=sVarId, eType=EPathVarType.USER, eNodeType=eNodeType
                    )
                # endif

            else:
                self._dicVars[sItem] = CPathVar(sId=sItem, sName=sItem, eType=EPathVarType.FIXED, eNodeType=eNodeType)
            # endif

            self._lPathVars.append(sVarId)
        # endif

    # enddef

    # #######################################################################################################################
    def ScanFileSystem(self, *, _pathScan: Path, _nodeParent: CNode, _iLevel: int):
        nodeX: CNode = None
        lPathVarIds = self.lPathVarIds
        sPathVarId: str = lPathVarIds[_iLevel]
        xPathVar: CPathVar = self.dicVars[sPathVarId]

        if xPathVar.eType == EPathVarType.SYSTEM:
            if xPathVar.funcHandler is not None:
                xResult: CPathVarHandlerResult = None
                for xResult in xPathVar.funcHandler(_pathScan):
                    if xResult.sName is None:
                        continue
                    # endif
                    nodeX = CNode(
                        xResult.sName,
                        parent=_nodeParent,
                        _iLevel=_iLevel,
                        _eType=xPathVar.eNodeType,
                        _xData=xResult.xData,
                    )
                    if xResult.pathScan is not None and len(lPathVarIds) > _iLevel + 1:
                        self.ScanFileSystem(
                            _pathScan=xResult.pathScan,
                            _nodeParent=nodeX,
                            _iLevel=_iLevel + 1,
                        )
                    # enddef
                # endfor
            # endif

        elif xPathVar.eType == EPathVarType.USER:
            if _pathScan is None:
                raise RuntimeError("User path variable must not be the first element of a path structure")
            # endif
            for pathItem in _pathScan.iterdir():
                if (xPathVar.eNodeType == ENodeType.PATH and not pathItem.is_dir()) or (
                    xPathVar.eNodeType == ENodeType.ARTEFACT and not pathItem.is_file()
                ):
                    continue
                # endif
                nodeX = CNode(pathItem.name, parent=_nodeParent, _iLevel=_iLevel, _eType=xPathVar.eNodeType)
                if xPathVar.eNodeType == ENodeType.PATH and len(lPathVarIds) > _iLevel + 1:
                    self.ScanFileSystem(
                        _pathScan=pathItem,
                        _nodeParent=nodeX,
                        _iLevel=_iLevel + 1,
                    )
                # enddef
            # endfor

        elif xPathVar.eType == EPathVarType.FIXED:
            if _pathScan is None:
                pathItem = Path(xPathVar.sId)
            else:
                pathItem = _pathScan / xPathVar.sId
            # endif
            if pathItem.exists():
                nodeX = CNode(pathItem.name, parent=_nodeParent, _iLevel=_iLevel, _eType=xPathVar.eNodeType)
                if xPathVar.eNodeType == ENodeType.PATH and len(lPathVarIds) > _iLevel + 1:
                    self.ScanFileSystem(
                        _pathScan=pathItem,
                        _nodeParent=nodeX,
                        _iLevel=_iLevel + 1,
                    )
                # enddef
            # endif

        else:
            raise RuntimeError(f"Unsupported path variable type: {xPathVar.eType}")
        # endif

    # enddef


# endclass