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
import json

from pathlib import Path
from dataclasses import dataclass
import anytree
from typing import Union, Optional, Callable
from anytree.exporter import DictExporter

from catharsys.api.cls_project import CProject

from anybase import config
from anybase import file as anyfile

from .cls_node import CNode, ENodeType
from .cls_path_structure import CPathStructure, CPathVar, EPathVarType


@dataclass
class CArtefactType:
    sId: str
    sName: str = None
    lType: list[str] = None
    xPathStruct: CPathStructure = None
    dicMeta: dict = None


# endclass


class CJsonNodeEncoder(json.JSONEncoder):
    def default(self, _objX):
        if isinstance(_objX, CArtefactType):
            return f"CArtefactType({_objX.sId})"
        # endif
        return super().default(_objX)

    # enddef


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

        self._dicVarValues: dict[str, str] = dict()

    # enddef

    @property
    def xTree(self) -> CNode:
        return self._xTree

    # enddef

    @property
    def sName(self) -> str:
        return self._sName

    # enddef

    @property
    def bHasData(self) -> bool:
        if self._xTree is None:
            return False
        # endif
        return len(self._xTree.children) > 0

    # enddef

    @property
    def xProject(self) -> CProject:
        return self._xProject

    # enddef

    @property
    def xPathStruct(self) -> CPathStructure:
        return self._xPathStruct

    # enddef

    @property
    def dicArtTypes(self) -> dict[str, CArtefactType]:
        return self._dicArtTypes

    # enddef

    @property
    def dicVarValues(self) -> dict[str, str]:
        return self._dicVarValues

    # enddef

    # ######################################################################################################
    def FromConfig(self, _dicCfg: dict):
        self._dicVarValues = dict()

        self._sName = _dicCfg.get("sName", self._sId)
        self._xPathStruct = CPathStructure(
            _dicCfg["sPathStructure"],
            _dicUserVars=_dicCfg.get("mVars"),
            _eLastElementNodeType=ENodeType.PATH,
            _dicSystemVars=self._dicPathSystemVars,
        )

        for sVarId, xPathVar in self._xPathStruct.dicVars.items():
            if xPathVar.eType != EPathVarType.FIXED:
                self._dicVarValues[sVarId] = ""
            # endif
        # endfor

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
            xArtType.dicMeta = dicArt.get("mMeta")
            self._dicArtTypes[sArtId] = xArtType

            for sVarId, xPathVar in xArtType.xPathStruct.dicVars.items():
                if xPathVar.eType != EPathVarType.FIXED:
                    self._dicVarValues[sVarId] = ""
                # endif
            # endfor

        # endfor

    # enddef

    # ######################################################################################################
    def _DoSerializeNode(self, _xNode: CNode) -> tuple:
        lChildren: list[tuple] = []
        for xChild in _xNode.children:
            lChildren.append(self._DoSerializeNode(xChild))
        # endfor

        xData = None
        if isinstance(_xNode._xData, CArtefactType):
            xData = f"CArtefactType({_xNode._xData.sId})"
        else:
            xData = _xNode._xData
        # endif

        if _xNode.name == _xNode._sPathName:
            sPathName = None
        else:
            sPathName = _xNode._sPathName
        # endif

        return (_xNode.name, sPathName, _xNode._iLevel, int(_xNode._eType), xData, lChildren)

    # enddef

    # ######################################################################################################
    def SerializeScan(self) -> list[tuple]:
        lChildren = []
        for xChild in self._xTree.children:
            lChildren.append(self._DoSerializeNode(xChild))
        # endfor

        return lChildren

    # enddef

    # ######################################################################################################
    def _DoDeserializeNode(self, _xParent: CNode, _tData: tuple):
        sName: str = _tData[0]
        sPathName: str = _tData[1]
        iLevel: int = _tData[2]
        iType: int = _tData[3]
        xData = _tData[4]
        lChildren: list[tuple] = _tData[5]

        if sPathName is None:
            sPathName = sName
        # endif

        xNode: CNode
        if isinstance(xData, str) and xData.startswith("CArtefactType("):
            xArtType = self._dicArtTypes.get(sName)
            if xArtType is None:
                raise RuntimeError("Invalid artefact type '{sName}'")
            # endif
            xNode = CNode(sName, parent=_xParent, _iLevel=0, _eType=ENodeType.ARTGROUP, _xData=xArtType)
        else:
            xNode = CNode(sName, parent=_xParent, _iLevel=iLevel, _eType=iType, _sPathName=sPathName, _xData=xData)
        # endif

        for tChild in lChildren:
            self._DoDeserializeNode(xNode, tChild)
        # endfor

    # enddef

    # ######################################################################################################
    def DeserializeScan(self, _lChildren: list[tuple]):
        self._xTree = CNode(self._sId, _iLevel=0, _eType=ENodeType.GROUP, _xData=self)
        for tChild in _lChildren:
            self._DoDeserializeNode(self._xTree, tChild)
        # endfor

    # enddef

    # ######################################################################################################
    def ScanArtefacts(
        self,
        *,
        _funcStatus: Optional[Callable[[str], None]] = None,
        _funcIterInit: Optional[Callable[[str, int], None]] = None,
        _funcIterUpdate: Optional[Callable[[int], None]] = None,
    ):
        if _funcStatus is not None:
            _funcStatus("Scanning group paths...")
        # endif

        # Scan group path structure
        pathScan: Path = None
        self._xTree = CNode(self._sId, _iLevel=0, _eType=ENodeType.GROUP, _xData=self)
        self._xPathStruct.ScanFileSystem(
            _pathScan=pathScan,
            _nodeParent=self._xTree,
            _iLevel=0,
        )
        iMaxGroupLevel: int = self._xPathStruct.iMaxLevel

        # Prune nodes that are leaves but not at max group level
        tGroupLeafNodes: tuple[CNode] = tuple()
        xNode: CNode = None
        while True:
            tGroupLeafNodes: tuple[CNode] = tuple(
                anytree.PreOrderIter(
                    self._xTree, filter_=lambda xNode: xNode.is_leaf and xNode._iLevel < iMaxGroupLevel
                )
            )

            if len(tGroupLeafNodes) == 0 or len(self._xTree.children) == 0:
                break
            # endif

            for xNode in tGroupLeafNodes:
                xNode.parent = None
            # endfor
        # endwhile
        del tGroupLeafNodes
        del xNode

        if len(self._xTree.children) == 0:
            return
        # endif

        tGroupLeafNodes: tuple[CNode] = tuple(anytree.PreOrderIter(self._xTree, filter_=lambda node: node.is_leaf))

        iGrpPathCnt: int = 0
        if _funcStatus is not None:
            iGrpPathCnt = len(tGroupLeafNodes)
            _funcStatus(f"Scanning artefacts for {iGrpPathCnt} group paths...")
        # endif

        bHasFuncIter: bool = _funcIterInit is not None and _funcIterUpdate is not None

        # Scan all artefact types
        sArtTypeId: str = ""
        for sArtTypeId in self._dicArtTypes:
            xArtType: CArtefactType = self._dicArtTypes[sArtTypeId]

            if bHasFuncIter is not None:
                _funcIterInit(f"Artefact '{xArtType.sName}'", iGrpPathCnt)
            # endif

            xNode: CNode = None
            for iIdx, xNode in enumerate(tGroupLeafNodes):
                if bHasFuncIter:
                    _funcIterUpdate(iIdx)
                # endif

                xArtTypeNode = CNode(sArtTypeId, parent=xNode, _iLevel=0, _eType=ENodeType.ARTGROUP, _xData=xArtType)
                xArtType.xPathStruct.ScanFileSystem(
                    _pathScan=xNode.pathFS,
                    _nodeParent=xArtTypeNode,
                    _iLevel=0,
                )
            # endfor
            if bHasFuncIter:
                _funcIterUpdate(iGrpPathCnt)
            # endif
        # endfor

    # enddef

    # ######################################################################################################
    def _GetVarValueSets(self, *, _xNode: CNode, _iMaxLevel: int) -> list[list[str]]:
        node: CNode
        lVarValueSets: list[set[str]] = [
            set([node.name for node in group]) for group in anytree.LevelGroupOrderIter(_xNode, maxlevel=_iMaxLevel)
        ]
        return lVarValueSets

    # enddef

    # ######################################################################################################
    def _RepresentsInt(self, _sValue: str):
        try:
            int(_sValue)
        except Exception:
            return False
        # endtry
        return True

    # enddef

    # ######################################################################################################
    def _ToInt(self, _sValue: str):
        return int(_sValue)

    # enddef

    # ######################################################################################################
    def _GetVarValueLists(self, *, _xNode: CNode, _iMaxLevel: int) -> list[list[str]]:
        lVarValueSets = self._GetVarValueSets(_xNode=_xNode, _iMaxLevel=_iMaxLevel)

        lVarValues = [list(x) for x in lVarValueSets[1:]]
        for lX in lVarValues:
            if len(lX) > 0:
                if self._RepresentsInt(lX[0]) is True:
                    lX.sort(key=self._ToInt)
                else:
                    lX.sort()
                # endif
            # endif
        # endfor

        return lVarValues

    # enddef

    # ######################################################################################################
    def _GetVarLabelLists(self, *, _lVarValueLists: list[list[str]], _xPathStruct: CPathStructure) -> list[list[str]]:
        lVarLabelLists: list[list[str]] = []
        for sVarId, lVarValues in zip(_xPathStruct.lPathVarIds, _lVarValueLists):
            lVarLabel: list[str] = []
            xVar: CPathVar = _xPathStruct.dicVars[sVarId]
            if xVar.funcLabel is not None:
                for sVarValue in lVarValues:
                    lVarLabel.append(xVar.funcLabel(xVar, sVarValue))
                # endfor
            elif xVar.sReParseValue is None or xVar.sReReplaceValue is None:
                lVarLabel = lVarValues
            else:
                for sVarValue in lVarValues:
                    sLabel = re.sub(xVar.sReParseValue, xVar.sReReplaceValue, sVarValue)
                    lVarLabel.append(sLabel)
                # endfor
            # endif
            lVarLabelLists.append(lVarLabel)
        # endfor

        return lVarLabelLists

    # enddef

    # ######################################################################################################
    def GetGroupVarValueLists(self) -> list[list[str]]:
        iGroupVarCnt: int = self._xPathStruct.iPathVarCount
        return self._GetVarValueLists(_xNode=self._xTree, _iMaxLevel=iGroupVarCnt + 1)

    # enddef

    # ######################################################################################################
    def GetGroupVarLabelLists(self, _lGrpVarValueLists: list[list[str]]) -> list[list[str]]:
        return self._GetVarLabelLists(_lVarValueLists=_lGrpVarValueLists, _xPathStruct=self._xPathStruct)

    # enddef

    # ######################################################################################################
    def GetGroupVarNodeList(self, _lGroupVarValueSelLists: list[list[str]]) -> list[CNode]:
        iGroupVarCnt: int = self._xPathStruct.iPathVarCount
        if len(_lGroupVarValueSelLists) != iGroupVarCnt:
            raise RuntimeError(f"The group variable value selection list must have {iGroupVarCnt} elements")
        # endif

        # Find those group leaf nodes whose path satisfies the group variable value selections
        lValues: list[str] = None
        lNodes: list[CNode] = [self._xTree]
        for lValues in _lGroupVarValueSelLists:
            lChildNodes: list[CNode] = []
            if len(lValues) == 1 and lValues[0] == "*":
                for xNode in lNodes:
                    lChildNodes.extend(list(xNode.children))
                # endfor
            else:
                setValues = set(lValues)
                for xNode in lNodes:
                    lChildNodes.extend([xChild for xChild in xNode.children if xChild.name in setValues])
                # endfor
            # endfor
            lNodes = lChildNodes
        # endfor

        return lNodes

    # enddef

    # ######################################################################################################
    def GetArtefactVarValues(
        self, _lGroupVarValueSelLists: list[list[str]], *, _bSameVarValueUnion: bool = True
    ) -> tuple[dict[str, list[list[str]]], dict[str, list[str]]]:
        lNodes = self.GetGroupVarNodeList(_lGroupVarValueSelLists)

        # Create a union over all artefact values of the same type,
        # for different groups paths, e.g. different cameras.
        dicArtVarValueSets: dict[str, list[set[str]]] = dict()
        for xNode in lNodes:
            for xChild in xNode.children:
                sArtType: str = str(xChild.name)
                iPathVarCount: int = self._dicArtTypes[sArtType].xPathStruct.iPathVarCount
                lValueSets = self._GetVarValueSets(_xNode=xChild, _iMaxLevel=iPathVarCount + 1)[1:]
                # if there are no artefacts for a child, then ignore the whole path var list
                if len(lValueSets) < iPathVarCount:
                    continue
                # endif

                lArtVarValues: list[set[str]] = dicArtVarValueSets.get(sArtType)
                # print(f"sArtType, lArtVarValues: {sArtType}, {lArtVarValues}")
                # print(f"lValueSets: {lValueSets}")

                if lArtVarValues is None:
                    dicArtVarValueSets[sArtType] = lValueSets
                else:
                    for iIdx, setValues in enumerate(lArtVarValues):
                        setValues.update(lValueSets[iIdx])
                    # endfor
                # endif
            # endfor children
        # endfor nodes

        # print(f"dicArtVarValueSets: {dicArtVarValueSets}")

        # Create dictionary of list of artefact types per variable
        dicArtVarsTypeList: dict[str, list[str]] = dict()
        for sArtType, xArtType in self._dicArtTypes.items():
            if sArtType not in dicArtVarValueSets:
                continue
            # endif

            for sArtVarId in xArtType.xPathStruct.lPathVarIds:
                lArtTypes: list[str] = dicArtVarsTypeList.get(sArtVarId)
                if lArtTypes is None:
                    dicArtVarsTypeList[sArtVarId] = [sArtType]
                else:
                    lArtTypes.append(sArtType)
                # endif
            # endfor
        # endfor

        # Create union of values for same variables in different artefact types, e.g. frames
        if _bSameVarValueUnion is True:
            # Make union of common variables from different types
            dicArtVarValueLists: dict[str, list[list[str]]] = dict()
            sArtType: str = None
            lValueSets: list[set[str]] = None
            for sArtVarId, lArtTypes in dicArtVarsTypeList.items():
                # if a variable appears in only one artefact type,
                # we do not need to create a union of all values.
                if len(lArtTypes) <= 1:
                    continue
                # endif

                # Create union of value sets for variable over all artefact types
                setValues = set()
                for sArtType in lArtTypes:
                    lArtVarIds = self._dicArtTypes[sArtType].xPathStruct.lPathVarIds
                    lValueSets = dicArtVarValueSets[sArtType]
                    iArtVarIdx = lArtVarIds.index(sArtVarId)
                    setValues = setValues.union(lValueSets[iArtVarIdx])
                # endfor

                # Set union of values
                for sArtType in lArtTypes:
                    lArtVarIds = self._dicArtTypes[sArtType].xPathStruct.lPathVarIds
                    lValueSets = dicArtVarValueSets[sArtType]
                    iArtVarIdx = lArtVarIds.index(sArtVarId)
                    lValueSets[iArtVarIdx] = setValues
                # endfor
            # endfor
        # endif

        # Make values sets to sorted lists
        dicArtVarValueLists: dict[str, list[list[str]]] = dict()
        sArtType: str = None
        lValueSets: list[set[str]] = None
        for sArtType, lValueSets in dicArtVarValueSets.items():
            lValueLists = [list(x) for x in lValueSets]
            for lValues in lValueLists:
                lValues.sort()
            # endfor
            dicArtVarValueLists[sArtType] = lValueLists
        # endfor

        return dicArtVarValueLists, dicArtVarsTypeList

    # enddef

    # ######################################################################################################
    def GetArtefactVarLabels(self, _dicArtVarValueLists: dict[str, list[list[str]]]) -> dict[str, list[list[str]]]:
        dicArtVarLabelLists: dict[str, list[list[str]]] = dict()
        for sArtTypeId, lArtValueLists in _dicArtVarValueLists.items():
            xArtType: CArtefactType = self._dicArtTypes[sArtTypeId]
            dicArtVarLabelLists[sArtTypeId] = self._GetVarLabelLists(
                _lVarValueLists=lArtValueLists, _xPathStruct=xArtType.xPathStruct
            )
        # endfor
        return dicArtVarLabelLists

    # enddef

    # ######################################################################################################
    def GetGroupVarNode(self, _lGrpPath: list[str]) -> CNode:
        xNode: CNode = self._xTree
        for sName in _lGrpPath:
            xNode = next((xChild for xChild in xNode.children if xChild.name == sName), None)
            if xNode is None:
                return None
            # endif
        # endfor
        return xNode

    # enddef

    # ######################################################################################################
    def GetArtVarNode(self, *, _xNode: CNode, _sArtType: str, _lArtPath: list[str]) -> CNode:
        xNode = next((xChild for xChild in _xNode.children if xChild.name == _sArtType), None)
        if xNode is None:
            return None
        # endif

        for sName in _lArtPath:
            xNode = next((xChild for xChild in xNode.children if xChild.name == sName), None)
            if xNode is None:
                return None
            # endif
        # endfor
        return xNode

    # enddef

    # enddef


# endclass
