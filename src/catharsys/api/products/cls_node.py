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

import enum
import anytree
from pathlib import Path
from typing import Optional, Any


class ENodeType(int, enum.Enum):
    ROOT = enum.auto()
    GROUP = enum.auto()
    ARTGROUP = enum.auto()
    ARTEFACT = enum.auto()
    PATH = enum.auto()


# endif


class CNode(anytree.NodeMixin):
    def __init__(
        self,
        name: str,
        parent: Optional["CNode"] = None,
        children: Optional[list["CNode"]] = None,
        *,
        _iLevel: int,
        _eType: ENodeType,
        _xData: Optional[Any] = None,
        _sPathName: Optional[str] = None,
    ):
        super().__init__()
        self.name = name
        if _sPathName is not None:
            self._sPathName = _sPathName
        else:
            self._sPathName = name
        # endif

        self._iLevel: int = _iLevel
        self._eType: ENodeType = _eType
        self._xData: Any = _xData

        self.parent = parent
        if children:
            self.children = children
        # endif

    # enddef

    def __repr__(self) -> str:
        sPath: str = ""
        lNames: list[str] = [
            str(node.name) for node in self.path if node._eType in [ENodeType.PATH, ENodeType.ARTEFACT]
        ]
        if len(lNames) > 0:
            sPath = "/".join(lNames)
        # endif
        sData: str = ""
        if self._xData is not None:
            sData = f"<{self._xData}>"
        # endif
        sGroup = self.sGroup
        if sGroup is None:
            sGroup = ""
        # endif
        sArtGroup = self.sArtefactGroup
        if sArtGroup is None:
            sArtGroup = ""
        # endif

        return f"{sGroup}:{sArtGroup}:{self._iLevel}> {self._eType} {sData} [{sPath}]"

    # enddef

    @property
    def iLevel(self) -> int:
        return self._iLevel

    # enddef

    @property
    def eType(self) -> ENodeType:
        return self._eType

    # enddef

    @property
    def xGroupNode(self) -> "CNode":
        return next((node for node in self.path if node._eType == ENodeType.GROUP), None)

    # enddef

    @property
    def sGroup(self) -> str:
        xNode = self.xGroupNode
        if xNode is None:
            return None
        # endif
        return str(xNode.name)

    # enddef

    @property
    def xArtefactGroupNode(self) -> "CNode":
        return next((node for node in self.path if node._eType == ENodeType.ARTGROUP), None)

    # enddef

    @property
    def sArtefactGroup(self) -> str:
        xNode = self.xArtefactGroupNode
        if xNode is None:
            return None
        # endif
        return str(xNode.name)

    # enddef

    @property
    def bIsArtefact(self) -> bool:
        return self._eType == ENodeType.ARTEFACT

    # enddef

    @property
    def lPathNames(self) -> list[str]:
        lNames: list[str] = [
            str(node._sPathName) for node in self.path if node._eType in [ENodeType.PATH, ENodeType.ARTEFACT]
        ]
        return lNames

    # enddef

    @property
    def pathFS(self) -> Path:
        sName: str = ""
        lNames = self.lPathNames
        if len(lNames) > 0:
            sName = "/".join(lNames)
            if ":" not in lNames[0]:
                sName = "/" + sName
            # endif
        # endif
        return Path(sName)

    # enddef


# endclass
