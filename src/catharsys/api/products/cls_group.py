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

from pathlib import Path
from dataclasses import dataclass
import anytree

from catharsys.api.cls_project import CProject

from anybase import config

from .cls_node import CNode, ENodeType
from .cls_path_structure import CPathStructure, CPathVar


@dataclass
class CArtefactType:
    sId: str
    sName: str = None
    lType: list[str] = None
    xPathStruct: CPathStructure = None


# endclass


class CGroup:
    def __init__(self, *, _sId: str, _prjX: CProject, _dicPathSystemVars: dict[str, CPathVar] = None):
        self._xProject: CProject = _prjX
        self._sId: str = _sId
        self._sName: str = None
        self._xPathStruct: CPathStructure = None
        self._dicArtTypes: dict[str, CArtefactType] = None
        self._xTree: CNode = None

        if _dicPathSystemVars is not None:
            self._dicPathSystemVars = _dicPathSystemVars
        else:
            self._dicPathSystemVars = {}
        # endf

    # enddef

    @property
    def xTree(self) -> CNode:
        return self._xTree

    # enddef

    # ######################################################################################################
    def FromConfig(self, _dicCfg: dict):
        self._sName = _dicCfg.get("sName", self._sId)
        self._xPathStruct = CPathStructure(
            _dicCfg["sPathStructure"],
            _dicUserVars=_dicCfg.get("mVars"),
            _eLastElementNodeType=ENodeType.PATH,
            _dicSystemVars=self._dicPathSystemVars,
        )

        self._dicArtTypes = dict()
        dicArtefacts = _dicCfg.get("mArtefacts")
        if not isinstance(dicArtefacts, dict):
            raise RuntimeError(f"Production group '{self._sId}' configuration has no 'mArtefacts' element")
        # endif

        for sArtId in dicArtefacts:
            dicArt: dict = dicArtefacts[sArtId]
            dicDti: dict = config.CheckConfigType(dicArt, "/catharsys/production/artefact/*:*")
            if dicDti["bOK"] is False:
                raise RuntimeError(f"Invalid artefact type for artefact '{sArtId}'")
            # endif

            lArtSubType: list[str] = dicDti["lCfgType"][3:]

            xArtType: CArtefactType = CArtefactType(sId=sArtId)
            xArtType.sName = dicArt.get("sName", sArtId)
            xArtType.lType = lArtSubType.copy()
            xArtType.xPathStruct = CPathStructure(
                dicArt["sPathStructure"],
                _dicUserVars=dicArt.get("mVars"),
                _eLastElementNodeType=ENodeType.ARTEFACT,
                _dicSystemVars=self._dicPathSystemVars,
            )
            self._dicArtTypes[sArtId] = xArtType
        # endfor

    # enddef

    # ######################################################################################################
    def ScanArtefacts(self):
        # Scan group path structure
        pathScan: Path = None
        self._xTree = CNode(self._sId, _iLevel=0, _eType=ENodeType.GROUP, _xData=self)
        self._xPathStruct.ScanFileSystem(
            _pathScan=pathScan,
            _nodeParent=self._xTree,
            _iLevel=0,
        )

        iMaxGroupLevel: int = self._xPathStruct.iMaxLevel

        # Scan all artefact types
        sArtTypeId: str = ""
        for sArtTypeId in self._dicArtTypes:
            xArtType: CArtefactType = self._dicArtTypes[sArtTypeId]
            xNode: CNode = None
            tNodes: tuple[CNode] = tuple(
                anytree.PreOrderIter(self._xTree, filter_=lambda node: node.is_leaf and node._iLevel == iMaxGroupLevel)
            )
            for xNode in tNodes:
                xArtTypeNode = CNode(sArtTypeId, parent=xNode, _iLevel=0, _eType=ENodeType.ARTGROUP, _xData=xArtType)
                xArtType.xPathStruct.ScanFileSystem(
                    _pathScan=xNode.pathFS,
                    _nodeParent=xArtTypeNode,
                    _iLevel=0,
                )
            # endfor

        # endfor

    # enddef

    # ######################################################################################################
    def GetVarValueLists(self) -> list[list[str]]:
        return [[node.name for node in group] for group in anytree.LevelGroupOrderIter(self._xTree)]

    # enddef


# endclass
