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
import enum
from collections.abc import Iterable
from pathlib import Path
from typing import Optional, Callable, Union

from catharsys.api.products.cls_products import CProducts
from catharsys.api.products.cls_group import CGroup, CArtefactType
from catharsys.api.products.cls_path_structure import CPathStructure
from catharsys.api.products.cls_node import CNode

from .cls_view_dim import CViewDim, CViewDimArtCommon, CViewDimArt, CViewDimArtType, CViewDimGrp, EViewDimType


# ##################################################################################################################
# ##################################################################################################################
class CViewDimNode:
    def __init__(self, *, _xProdView: "CProductView", _iDimIdx: int, _sArtTypeId: Optional[str] = None):
        self._xProdView: "CProductView" = _xProdView
        self._iDimIdx: int = _iDimIdx
        self._sArtTypeId: str = _sArtTypeId
        self._xViewDim: CViewDim = None
        if self._sArtTypeId is None:
            self._xViewDim = self._xProdView.lViewDims[self._iDimIdx]
        else:
            self._xViewDim = self._xProdView.dicArtViewDims[self._sArtTypeId][self._iDimIdx]
        # endif

    # enddef

    @property
    def xViewDim(self) -> CViewDim:
        return self._xViewDim

    # enddef

    @property
    def sLabel(self) -> str:
        return self._xProdView.GetViewDimLabel(self._xViewDim)

    # enddef

    @property
    def sDimLabel(self) -> str:
        return self._xViewDim.sDimLabel

    # enddef

    @property
    def sValue(self) -> str:
        return self._xProdView.GetViewDimValue(self._xViewDim)

    # enddef

    @property
    def iRange(self) -> int:
        return self._xViewDim.iRange

    # enddef

    @property
    def iDimIdx(self) -> int:
        return self._iDimIdx

    # enddef

    @property
    def sArtTypeId(self) -> str:
        return self._sArtTypeId

    # enddef

    @property
    def bIsUniqueArtVar(self) -> bool:
        return self._sArtTypeId is not None

    # enddef

    @property
    def bIsUniqueArtVarStartNode(self) -> bool:
        return self._sArtTypeId is not None and self._iDimIdx == 0

    # enddef

    @property
    def lLabels(self) -> Iterable[str]:
        self._xViewDim.Reset()
        while True:
            yield self.sLabel
            if self._xViewDim.Next() is False:
                break
            # endif
        # endwhile

    # enddef

    @property
    def lValues(self) -> Iterable[str]:
        self._xViewDim.Reset()
        while True:
            yield self.sValue
            if self._xViewDim.Next() is False:
                break
            # endif
        # endwhile

    # enddef

    def Reset(self):
        self._xViewDim.Reset()

    # enddef

    def Next(self):
        return self._xViewDim.Next()

    # enddef

    def NextDim(self) -> Optional["CViewDimNode"]:
        iNextDim = self._iDimIdx + 1
        if self._sArtTypeId is None:
            if iNextDim < len(self._xProdView.lViewDims):
                return CViewDimNode(_xProdView=self._xProdView, _iDimIdx=iNextDim)
            # endif

            sViewArtTypeId = self._xProdView.GetViewArtTypeId(_bDoRaise=False)
            if sViewArtTypeId is None:
                return None
            # endif

            lViewDims = self._xProdView.dicArtViewDims.get(sViewArtTypeId)
            if lViewDims is None or len(lViewDims) == 0:
                return None
            # endif

            return CViewDimNode(_xProdView=self._xProdView, _iDimIdx=0, _sArtTypeId=sViewArtTypeId)
        # endif

        lViewDims = self._xProdView.dicArtViewDims[self._sArtTypeId]
        if iNextDim < len(lViewDims):
            return CViewDimNode(_xProdView=self._xProdView, _iDimIdx=iNextDim, _sArtTypeId=self._sArtTypeId)
        # endif

        return None

    # enddef


# endclass


# ##################################################################################################################
# ##################################################################################################################
class CProductView:
    def __init__(self, _xProducts: CProducts):
        self._xProdData: CProducts = _xProducts
        self._xProdGrp: CGroup = None

        self._lGrpVarValueLists: list[list[str]] = None
        self._lGrpVarLabelLists: list[list[str]] = None

        self._lSelGrpVarValueLists: list[list[str]] = None
        self._lSelGrpVarLabelLists: list[list[str]] = None

        self._dicArtVarValueLists: dict[str, list[list[str]]] = None
        self._dicArtVarTypeLists: dict[str, list[str]] = None

        # dictionary of variable ids of selected artefact types
        self._dicSelArtTypeVarIds: dict[str, list[str]] = None
        # dictionary of variables ids that are common over all selected artefact types
        self._dicSelCommonArtVarTypes: dict[str, list[str]] = None

        # ### Glossary
        # - Active Variables: are those where more than one value is selected.
        #       These are the variables that are iterated over.
        # ###

        # dictionary of selected artefact variables per type that are active and
        # used by more than one artefact types.
        # Maps variable ids to list of types, where this variable is used.
        self._dicSelActCommonArtVarTypes: dict[str, list[str]] = dict()
        # names of selected active common artefact variables
        self._dicSelActCommonArtVarNames: dict[str, str] = dict()

        # dictionary of selected artefact variables per type that are active and
        # only used by a single artefact types.
        # Maps arterfact types to list of variable ids
        self._dicSelActSpecialArtTypeVarIds: dict[str, list[str]] = dict()
        # names of special variables
        self._dicSelActSpecialArtTypeVarNames: dict[str, dict[str, str]] = dict()

        self._lSelActGrpVarIds: list[str] = None
        self._lSelActGrpVarNames: list[str] = None

        self._dicSelArtVarValueLists: dict[str, list[list[str]]] = dict()
        self._dicSelArtVarLabelLists: dict[str, list[list[str]]] = dict()

        self._dicSelActArtVarIds: dict[str, list[str]] = dict()
        self._dicSelActArtVarNames: dict[str, list[str]] = dict()

        self._lSelActArtTypeIds: list[str] = []

        self._dicViewDimNames: dict[str, str] = dict()
        self._dicArtViewDimNames: dict[str, dict[str, str]] = dict()

        self._lViewDims: list[CViewDim] = []
        self._dicArtViewDims: dict[str, list[CViewDim]] = dict()

    # enddef

    @property
    def lGroups(self) -> list[str]:
        return self._xProdData.lGroups

    # enddef

    @property
    def dicGroupKeyNames(self) -> dict[str, str]:
        return self._xProdData.dicGroupKeyNames

    # enddef

    @property
    def iGroupCount(self) -> int:
        return self._xProdData.iGroupCount

    # enddef

    @property
    def bHasGroupData(self) -> bool:
        if self._xProdGrp is None:
            return False
        # endif
        return self._xProdGrp.bHasData

    # enddef

    @property
    def xGrpPathStruct(self) -> CPathStructure:
        return self._xProdGrp.xPathStruct

    # enddef

    @property
    def lGrpPathVarIds(self) -> list[str]:
        return self.xGrpPathStruct.lPathVarIds

    # enddef

    @property
    def lGrpVarValueLists(self) -> list[list[str]]:
        return self._lGrpVarValueLists

    # enddef

    @property
    def lGrpVarLabelLists(self) -> list[list[str]]:
        return self._lGrpVarLabelLists

    # enddef

    @property
    def lSelGrpVarValueLists(self) -> list[list[str]]:
        return self._lSelGrpVarValueLists

    # enddef

    @property
    def lSelGrpVarLabelLists(self) -> list[list[str]]:
        return self._lSelGrpVarLabelLists

    # enddef

    @property
    def dicArtVarValueLists(self) -> dict[str, list[list[str]]]:
        return self._dicArtVarValueLists

    # enddef

    @property
    def dicArtVarLabelLists(self) -> dict[str, list[list[str]]]:
        return self._dicArtVarLabelLists

    # enddef

    @property
    def dicSelActCommonArtVarNames(self) -> dict[str, str]:
        return self._dicSelActCommonArtVarNames

    # enddef

    @property
    def dicSelActSpecialArtTypeVarNames(self) -> dict[str, dict[str, str]]:
        return self._dicSelActSpecialArtTypeVarNames

    # enddef

    @property
    def lSelActArtTypeIds(self) -> list[str]:
        return self._lSelActArtTypeIds

    # enddef

    @property
    def bHasSelectedActiveArtefactVariables(self) -> bool:
        return len(self._lSelActArtTypeIds) > 0

    # enddef

    @property
    def dicViewDimNames(self) -> dict[str, str]:
        return self._dicViewDimNames

    # enddef

    @property
    def dicArtViewDimNames(self) -> dict[str, dict[str, str]]:
        return self._dicArtViewDimNames

    # enddef

    @property
    def bHasSelectedArtefactVarValues(self) -> bool:
        return len(self._dicSelArtVarValueLists) > 0

    # enddef

    @property
    def lViewDims(self) -> list[CViewDim]:
        return self._lViewDims

    # enddef

    @property
    def dicArtViewDims(self) -> dict[str, list[CViewDim]]:
        return self._dicArtViewDims

    # enddef

    @property
    def dicVarValues(self) -> dict[str, str]:
        return self._xProdGrp.dicVarValues

    # enddef

    @property
    def lMessages(self) -> list[str]:
        return self._xProdData.lMessages

    # enddef

    # ####################################################################################################################
    def GetMessages(self, _bDoClear: bool = True) -> list[str]:
        return self._xProdData.GetMessages(_bDoClear)
    # enddef

    # ####################################################################################################################
    def GetSelectedGroupVarValueCount(self, _sGrpVarId: str) -> int:
        iGrpVarIdx: int = self.lGrpPathVarIds.index(_sGrpVarId)
        return len(self._lSelGrpVarValueLists[iGrpVarIdx])

    # enddef

    # ####################################################################################################################
    def GetSelectedArtefactVarValueCount(self, _sArtTypeId: str, _sArtVarId: str) -> int:
        xArtType: CArtefactType = self._xProdGrp.dicArtTypes[_sArtTypeId]
        lArtVarIds = xArtType.xPathStruct.lPathVarIds
        iArtVarIdx = lArtVarIds.index(_sArtVarId)
        lArtVarValues = self._dicSelArtVarValueLists[_sArtTypeId][iArtVarIdx]
        return len(lArtVarValues)

    # enddef

    # ####################################################################################################################
    def GetSelectedActiveCommonArtefactVarValueCount(self, _sArtVarId: str) -> int:
        lArtTypeIds = self._dicSelActCommonArtVarTypes[_sArtVarId]
        sArtTypeId = lArtTypeIds[0]
        return self.GetSelectedArtefactVarValueCount(sArtTypeId, _sArtVarId)

    # enddef

    # ####################################################################################################################
    def ArtefactVarListsItems(self) -> Iterable[tuple[CArtefactType, list[list[str]], list[list[str]]]]:
        for sArtType, lVarValueLists in self._dicArtVarValueLists.items():
            yield self._xProdGrp.dicArtTypes[sArtType], lVarValueLists, self._dicArtVarLabelLists[sArtType]
        # endfor

    # enddef

    # ####################################################################################################################
    def ActiveSelectedGroupVarItems(self) -> Iterable[tuple[str, str]]:
        for sId, sName in zip(self._lSelActGrpVarIds, self._lSelActGrpVarNames):
            yield sId, sName
        # endfor

    # enddef

    # ####################################################################################################################
    def GetArtefactVarLabelLists(self, _sType: str) -> list[list[str]]:
        return self._dicArtVarLabelLists[_sType]

    # enddef

    # ####################################################################################################################
    def GetArtefactType(self, _sType: str) -> CArtefactType:
        return self._xProdGrp.dicArtTypes[_sType]

    # enddef

    # ####################################################################################################################
    def GetArtefactTypeName(self, _sType: str) -> CArtefactType:
        return self._xProdGrp.dicArtTypes[_sType].sName

    # enddef

    # ####################################################################################################################
    def GetArtefactPathVarIds(self, _sType: str) -> list[str]:
        return self._xProdGrp.dicArtTypes[_sType].xPathStruct.lPathVarIds

    # enddef

    # ####################################################################################################################
    def GetArtefactPathStruct(self, _sType: str) -> CPathStructure:
        return self._xProdGrp.dicArtTypes[_sType].xPathStruct

    # enddef

    # ####################################################################################################################
    def DoesScanMatchProdFile(self) -> bool:
        return self._xProdData.DoesScanMatchProdFile()

    # enddef

    # ####################################################################################################################
    def FromFile(self, _pathProduction: Path):
        self._xProdData.FromFile(_pathProduction)

    # enddef

    # ####################################################################################################################
    def ScanArtefacts(
        self,
        *,
        _sGroupId: Optional[str] = None,
        _funcStatus: Optional[Callable[[str], None]] = None,
        _funcIterInit: Optional[Callable[[str, int], None]] = None,
        _funcIterUpdate: Optional[Callable[[int], None]] = None,
    ):
        self._xProdData.ScanArtefacts(_sGroupId=_sGroupId)

    # enddef

    # ######################################################################################################
    def SerializeScan(self, _xFilePath: Union[str, list, tuple, Path]):
        self._xProdData.SerializeScan(_xFilePath)

    # enddef

    # ######################################################################################################
    def DeserializeScan(self, _xFilePath: Union[str, list, tuple, Path], *, _bDoPrint=True):
        self._xProdData.DeserializeScan(_xFilePath, _bDoPrint=_bDoPrint)

    # enddef

    # ####################################################################################################################
    def SelectGroup(self, _sGroup: str, *, _bDoRaise: bool = True) -> bool:
        if _sGroup not in self._xProdData.dicGroups:
            if _bDoRaise is True:
                raise RuntimeError(f"Group '{_sGroup}' not available")
            else:
                return False
            # endif
        # endif

        self._xProdGrp = self._xProdData.dicGroups[_sGroup]
        if self._xProdGrp.bHasData is True:
            self._lGrpVarValueLists = self._xProdGrp.GetGroupVarValueLists()
            self._lGrpVarLabelLists = self._xProdGrp.GetGroupVarLabelLists(self._lGrpVarValueLists)
        # endif

        return True

    # enddef

    # ####################################################################################################################
    def _GetLabelsForSelValues(
        self, _lSelVarValueLists: list[list[str]], _lVarValueLists: list[list[str]], _lVarLabelLists: [list[list[str]]]
    ):
        # Get list of labels for selected group values
        lSelVarLabelLists: list[list[str]] = []

        for lSelVarValues, lVarValues, lVarLabels in zip(_lSelVarValueLists, _lVarValueLists, _lVarLabelLists):
            lSelVarLabels: list[str] = []
            for sSelValue in lSelVarValues:
                try:
                    iIdx = lVarValues.index(sSelValue)
                except Exception:
                    raise RuntimeError(
                        f"Selection value '{sSelValue}' not in available group variable values: {lVarValues}"
                    )
                # endtry
                lSelVarLabels.append(lVarLabels[iIdx])
            # endfor
            lSelVarLabelLists.append(lSelVarLabels)
        # endfor
        return lSelVarLabelLists

    # enddef

    # ####################################################################################################################
    def SetSelectedGroupVarValueLists(self, _lSelGrpVarValueLists: list[list[str]]):
        if self._xProdGrp is None:
            raise RuntimeError("No group selected")
        # endif

        if len(_lSelGrpVarValueLists) != len(self._lGrpVarValueLists):
            raise RuntimeError("The selection list must have the same length as the group value list")
        # endif

        self._lSelGrpVarValueLists = _lSelGrpVarValueLists
        self._lSelGrpVarLabelLists = self._GetLabelsForSelValues(
            _lSelGrpVarValueLists, self._lGrpVarValueLists, self._lGrpVarLabelLists
        )

        # Get artefact values for selected group values
        self._dicArtVarValueLists, self._dicArtVarTypeLists = self._xProdGrp.GetArtefactVarValues(_lSelGrpVarValueLists)
        self._dicArtVarLabelLists = self._xProdGrp.GetArtefactVarLabels(self._dicArtVarValueLists)

        # List of group variable ids where more than one value is selected.
        # These are the variables that we can iterate over.
        self._lSelActGrpVarIds = [
            sVarId for sVarId, lVarValues in zip(self.lGrpPathVarIds, self._lSelGrpVarValueLists) if len(lVarValues) > 1
        ]
        self._lSelActGrpVarNames = [self.xGrpPathStruct.dicVars[sVarId].sName for sVarId in self._lSelActGrpVarIds]

    # enddef

    # ####################################################################################################################
    # Set the list of variable ids per artefact type used
    def SetSelectedArtefactVariableIds(self, _dicSelArtTypeVarIds: dict[str, list[str]]):
        self._dicSelArtTypeVarIds = copy.deepcopy(_dicSelArtTypeVarIds)

        # Create a dictionary of common artefact variables
        self._dicSelCommonArtVarTypes = dict()

        for sArtTypeId, lArtVarIds in self._dicSelArtTypeVarIds.items():
            for sVarId in lArtVarIds:
                if sVarId in self._dicSelCommonArtVarTypes:
                    self._dicSelCommonArtVarTypes[sVarId].append(sArtTypeId)
                else:
                    self._dicSelCommonArtVarTypes[sVarId] = [sArtTypeId]
                # endif
            # endfor
        # endfor

        # Remove elements from common artefact variable to type dictionary,
        # that only appear in a single artefact type.
        lRemove: list[str] = [
            sArtVarId for sArtVarId, lArtTypes in self._dicSelCommonArtVarTypes.items() if len(lArtTypes) <= 1
        ]
        for sArtVarId in lRemove:
            del self._dicSelCommonArtVarTypes[sArtVarId]
        # endfor

    # enddef

    # ####################################################################################################################
    def ClearArtefactVarSelection(self):
        self._dicSelArtVarValueLists = dict()
        self._dicSelArtVarLabelLists = dict()
        self._dicSelActArtVarIds = dict()
        self._dicSelActArtVarNames = dict()
        self._lSelActArtTypeIds = []

        self._dicSelActCommonArtVarTypes = dict()
        self._dicSelActCommonArtVarNames = dict()

        self._dicSelActSpecialArtTypeVarIds = dict()
        self._dicSelActSpecialArtTypeVarNames = dict()

    # enddef

    # ####################################################################################################################
    def SetSelectedArtefactVarValueListsForType(self, _sArtTypeId: str, _lSelArtVarValueLists: list[list[str]]):
        self._dicSelArtVarValueLists[_sArtTypeId] = _lSelArtVarValueLists
        self._dicSelArtVarLabelLists[_sArtTypeId] = self._GetLabelsForSelValues(
            _lSelArtVarValueLists, self._dicArtVarValueLists[_sArtTypeId], self._dicArtVarLabelLists[_sArtTypeId]
        )

        # List of artefact variable ids where more than one value is selected.
        # These are the variables that we can iterate over.
        lSelActArtVarIds = [
            sVarId
            for sVarId, lVarValues in zip(self.GetArtefactPathVarIds(_sArtTypeId), _lSelArtVarValueLists)
            if len(lVarValues) > 1
        ]
        self._dicSelActArtVarIds[_sArtTypeId] = lSelActArtVarIds
        self._dicSelActArtVarNames[_sArtTypeId] = [
            self.GetArtefactPathStruct(_sArtTypeId).dicVars[sVarId].sName for sVarId in lSelActArtVarIds
        ]

        self._lSelActArtTypeIds.append(_sArtTypeId)

        for sVarId in lSelActArtVarIds:
            if sVarId in self._dicSelActCommonArtVarTypes:
                self._dicSelActCommonArtVarTypes[sVarId].append(_sArtTypeId)
            else:
                self._dicSelActCommonArtVarTypes[sVarId] = [_sArtTypeId]
            # endif
        # endfor

    # enddef

    # ####################################################################################################################
    def UpdateArtefactVarSelection(self):
        # Remove elements from common artefact variable to type dictionary,
        # that only appear in a single artefact type.
        if len(self._lSelActArtTypeIds) > 1:
            lRemove: list[str] = [
                sArtVarId for sArtVarId, lArtTypes in self._dicSelActCommonArtVarTypes.items() if len(lArtTypes) <= 1
            ]
            for sArtVarId in lRemove:
                sArtTypeId = self._dicSelActCommonArtVarTypes[sArtVarId][0]

                # Create dictionary of lists of var ids per artefact type,
                # for variables that are unique to an artefact type.
                lArtVarIds: list[str] = self._dicSelActSpecialArtTypeVarIds.get(sArtTypeId)
                if lArtVarIds is None:
                    self._dicSelActSpecialArtTypeVarIds[sArtTypeId] = [sArtVarId]
                else:
                    lArtVarIds.append(sArtVarId)
                # endif
                del self._dicSelActCommonArtVarTypes[sArtVarId]
            # endfor
        # endif

        for sSelArtVarId, lSelArtTypeIds in self._dicSelActCommonArtVarTypes.items():
            xArtType: CArtefactType = self._xProdGrp.dicArtTypes[lSelArtTypeIds[0]]
            self._dicSelActCommonArtVarNames[sSelArtVarId] = xArtType.xPathStruct.dicVars[sSelArtVarId].sName
        # endfor

        # View dimension names for variables that are unique to artefacts
        for sSelArtTypeId, lSelArtVarIds in self._dicSelActSpecialArtTypeVarIds.items():
            xArtType: CArtefactType = self._xProdGrp.dicArtTypes[sSelArtTypeId]
            dicSpecialViewDimNames: dict[str, str] = dict()
            for sSelArtVarId in lSelArtVarIds:
                dicSpecialViewDimNames[sSelArtVarId] = xArtType.xPathStruct.dicVars[sSelArtVarId].sName
            # endfor
            self._dicSelActSpecialArtTypeVarNames[sSelArtTypeId] = dicSpecialViewDimNames
        # endfor

    # enddef

    # ####################################################################################################################
    def CreateDimIdGroup(self, _sName: str) -> str:
        return f"g:{_sName}"

    # enddef

    # ####################################################################################################################
    def CreateDimIdCommonArtefact(self, _sName: str) -> str:
        return f"ac:{_sName}"

    # enddef

    # ####################################################################################################################
    def CreateDimIdArtefact(self, _sName: str) -> str:
        return f"a:{_sName}"

    # enddef

    # ####################################################################################################################
    def GetDimIdType(self, _sKey: str) -> tuple[str, EViewDimType]:
        sName: str = None
        eType: EViewDimType = None

        if _sKey.startswith("g:"):
            sName = _sKey[2:]
            eType = EViewDimType.GROUP

        elif _sKey.startswith("ac:"):
            sName = _sKey[3:]
            eType = EViewDimType.ARTCOMVAR

        elif _sKey.startswith("a:"):
            sName = _sKey[2:]
            eType = EViewDimType.ARTVAR

        elif _sKey == "!art-type":
            sName = _sKey
            eType = EViewDimType.ARTTYPE

        else:
            raise RuntimeError(f"Invalid view dimension key '{_sKey}'")
        # endif

        return sName, eType

    # enddef

    # ####################################################################################################################
    def UpdateViewDimNames(self):
        self._dicViewDimNames = dict()
        self._dicArtViewDimNames = dict()

        self._dicViewDimNames.update({self.CreateDimIdGroup(k): v for k, v in self.ActiveSelectedGroupVarItems()})

        # if  there is at least one artefact type with at least one variable
        # with more than one value, then make the common variables selectable.
        if self.bHasSelectedActiveArtefactVariables:
            for sSelArtVarId, sSelArtVarName in self._dicSelActCommonArtVarNames.items():
                self._dicViewDimNames[self.CreateDimIdCommonArtefact(sSelArtVarId)] = sSelArtVarName
            # endfor
        # endif

        self._dicViewDimNames["!art-type"] = "Artefact Type"

        for sArtTypeId, dicArtVarNames in self._dicSelActSpecialArtTypeVarNames.items():
            self._dicArtViewDimNames[sArtTypeId] = {
                self.CreateDimIdArtefact(sVarId): sVarName for sVarId, sVarName in dicArtVarNames.items()
            }
        # endfor

    # enddef

    # ####################################################################################################################
    def ClearViewDims(self):
        self._lViewDims = []
        self._dicArtViewDims = dict()

    # enddef

    # ####################################################################################################################
    def AddViewDim(
        self,
        *,
        _sDimKey: str,
        _iRangeMin: Optional[int] = None,
        _iRangeMax: Optional[int] = None,
        _sArtTypeId: Optional[str] = None,
    ):
        sDimId, eDimType = self.GetDimIdType(_sDimKey)
        sDimLabel = self._dicViewDimNames.get(_sDimKey, "")

        bRangeValid: bool = _iRangeMin is not None and _iRangeMax is not None
        iMin: int = _iRangeMin
        iMax: int = _iRangeMax
        xViewDim: CViewDim = None

        if eDimType == EViewDimType.GROUP:
            sGrpVarId: str = sDimId
            iGrpVarIdx = self.lGrpPathVarIds.index(sGrpVarId)
            lGrpVarValues = self._lSelGrpVarValueLists[iGrpVarIdx]
            lGrpVarLabels = self._lSelGrpVarLabelLists[iGrpVarIdx]
            if bRangeValid is False:
                iMin = 0
                iMax = len(lGrpVarValues) - 1
            # endif
            xViewDim = CViewDimGrp(
                _sVarId=sGrpVarId,
                _iVarIdx=iGrpVarIdx,
                _lValues=lGrpVarValues,
                _lLabels=lGrpVarLabels,
                _iMin=iMin,
                _iMax=iMax,
                _sDimLabel=sDimLabel,
            )

        elif eDimType == EViewDimType.ARTCOMVAR:
            sArtVarId: str = sDimId
            lArtTypeIds = self._dicSelActCommonArtVarTypes[sArtVarId]

            lArtVarIdx: list[int] = []
            lArtVarValues: list[str] = None
            lArtVarLabels: list[str] = None
            for sArtTypeId in lArtTypeIds:
                xArtType: CArtefactType = self._xProdGrp.dicArtTypes[sArtTypeId]
                lArtVarIds = xArtType.xPathStruct.lPathVarIds
                iArtVarIdx = lArtVarIds.index(sArtVarId)
                lArtVarIdx.append(iArtVarIdx)
                if lArtVarValues is None:
                    lArtVarValues = self._dicSelArtVarValueLists[sArtTypeId][iArtVarIdx]
                    lArtVarLabels = self._dicSelArtVarLabelLists[sArtTypeId][iArtVarIdx]
                # endif
            # endfor
            if bRangeValid is False:
                iMin = 0
                iMax = len(lArtVarValues) - 1
            # endif
            xViewDim = CViewDimArtCommon(
                _sVarId=sArtVarId,
                _lValues=lArtVarValues,
                _lLabels=lArtVarLabels,
                _lArtTypeIds=lArtTypeIds,
                _lVarIdx=lArtVarIdx,
                _iMin=iMin,
                _iMax=iMax,
                _sDimLabel=sDimLabel,
            )

        elif eDimType == EViewDimType.ARTTYPE:
            xViewDim = CViewDimArtType(_lArtTypes=self._lSelActArtTypeIds, _sDimLabel=sDimLabel)

        elif eDimType == EViewDimType.ARTVAR:
            if _sArtTypeId is None:
                raise RuntimeError(f"No artefact type id specified for the artefact variable key '{_sDimKey}'")
            # endif
            sArtVarId = sDimId
            lArtVarIds = self.GetArtefactPathVarIds(_sArtTypeId)
            iArtVarIdx = lArtVarIds.index(sArtVarId)
            lArtVarValues = self._dicSelArtVarValueLists[_sArtTypeId][iArtVarIdx]
            lArtVarLabels = self._dicSelArtVarLabelLists[_sArtTypeId][iArtVarIdx]
            if bRangeValid is False:
                iMin = 0
                iMax = len(lArtVarValues) - 1
            # endif

            xViewDim = CViewDimArt(
                _sVarId=sArtVarId,
                _sArtTypeId=_sArtTypeId,
                _iVarIdx=iArtVarIdx,
                _lValues=lArtVarValues,
                _lLabels=lArtVarLabels,
                _iMin=iMin,
                _iMax=iMax,
                _sDimLabel=sDimLabel,
            )

        else:
            raise RecursionError(f"Invalid view dimension key '{_sDimKey}'")
        # endif

        xViewDim.Reset()

        if eDimType == EViewDimType.ARTVAR:
            if _sArtTypeId in self._dicArtViewDims:
                self._dicArtViewDims[_sArtTypeId].append(xViewDim)
            else:
                self._dicArtViewDims[_sArtTypeId] = [xViewDim]
            # endif
        else:
            self._lViewDims.append(xViewDim)
        # endif

    # enddef

    # ####################################################################################################################
    def ResetViewDimIndices(self):
        for xViewDim in self._lViewDims:
            xViewDim.Reset()
        # endfor

        for lViewDims in self._dicArtViewDims.values():
            for xViewDim in lViewDims:
                xViewDim.Reset()
            # endfor
        # endfor

    # enddef

    # ####################################################################################################################
    def StartViewDimNodeIteration(self) -> CViewDimNode:
        if self.bHasSelectedArtefactVarValues is False:
            return None
        # endif

        self.ResetViewDimIndices()
        self._lViewGrpPath = [x[0] for x in self._lSelGrpVarValueLists]
        self._sViewArtTypeId = next((x for x in self._dicSelArtVarValueLists), None)

        # for xViewDim in self._lViewDims:
        #     print(self.GetViewDimLabel(xViewDim))
        # # endfor

        return CViewDimNode(_xProdView=self, _iDimIdx=0)

    # enddef

    # ####################################################################################################################
    def GetViewDimNodeIterationValue(self) -> tuple[CNode, CArtefactType]:
        xViewDim: CViewDim = None
        lViewDimArtCom: list[CViewDimArtCommon] = []

        # Set first all group path elements and the artefact type
        for xViewDim in self._lViewDims:
            if isinstance(xViewDim, CViewDimGrp):
                xVdg: CViewDimGrp = xViewDim
                self._lViewGrpPath[xVdg.iVarIdx] = xVdg.sValue

            elif isinstance(xViewDim, CViewDimArtType):
                xVdat: CViewDimArtType = xViewDim
                self._sViewArtTypeId = xVdat.sValue

            elif isinstance(xViewDim, CViewDimArtCommon):
                lViewDimArtCom.append(xViewDim)

            else:
                raise RuntimeError(f"Invalid view dimension object type: {xViewDim._eType}")
            # endif
        # endfor

        lViewArtPath = [x[0] for x in self._dicSelArtVarValueLists[self._sViewArtTypeId]]

        for xArtCom in lViewDimArtCom:
            if self._sViewArtTypeId in xArtCom.lArtTypeIds:
                iTypeIdx = xArtCom.lArtTypeIds.index(self._sViewArtTypeId)
                iVarIdx = xArtCom.lVarIdx[iTypeIdx]
                lViewArtPath[iVarIdx] = xArtCom.sValue
            # endif
        # endfor

        # Set unique artefact variables
        lArtViewDims = self._dicArtViewDims.get(self._sViewArtTypeId)
        if lArtViewDims is not None:
            for xViewDim in lArtViewDims:
                if isinstance(xViewDim, CViewDimArt):
                    xVda: CViewDimArt = xViewDim
                    lViewArtPath[xVda.iVarIdx] = xVda.sValue
                # endif
            # endfor
        # endif

        # Set Variable values
        dicVarValues = self._xProdGrp.dicVarValues

        for sGrpVarId, sVarValue in zip(self._xProdGrp.xPathStruct.lPathVarIds, self._lViewGrpPath):
            if sGrpVarId in dicVarValues:
                dicVarValues[sGrpVarId] = sVarValue
            # endif
        # endfor

        dicVarValues["art-type"] = self._sViewArtTypeId

        lArtVarIds = self.GetArtefactPathVarIds(self._sViewArtTypeId)
        for sArtVarId, sVarValue in zip(lArtVarIds, lViewArtPath):
            if sArtVarId in dicVarValues:
                dicVarValues[sArtVarId] = sVarValue
            # endif
        # endfor

        # Get node
        xArtType: CArtefactType = None
        ndArt: CNode = None
        ndGrp: CNode = self._xProdGrp.GetGroupVarNode(self._lViewGrpPath)
        if ndGrp is not None:
            ndArt = self._xProdGrp.GetArtVarNode(_xNode=ndGrp, _sArtType=self._sViewArtTypeId, _lArtPath=lViewArtPath)
            if ndArt is not None:
                xArtType = self.GetArtefactType(self._sViewArtTypeId)
            # endif
        # endif

        return ndArt, xArtType

    # enddef

    # ####################################################################################################################
    def GetViewArtTypeId(self, *, _bDoRaise: bool = True) -> str:
        xViewDim: CViewDimArtType = next((x for x in self._lViewDims if isinstance(x, CViewDimArtType)), None)
        if xViewDim is None:
            if _bDoRaise is True:
                raise RuntimeError("No artefact type in view dimension list")
            else:
                return None
            # endif
        # endif

        return xViewDim.sValue

    # enddef

    # ##########################################################################################################
    def GetViewDimValue(self, _xViewDim: CViewDim) -> str:
        sValue: str = None

        if isinstance(_xViewDim, CViewDimGrp):
            xVdg: CViewDimGrp = _xViewDim
            sValue = xVdg.sValue

        elif isinstance(_xViewDim, CViewDimArtType):
            xVdat: CViewDimArtType = _xViewDim
            sValue = xVdat.sValue

        elif isinstance(_xViewDim, CViewDimArtCommon):
            xVdac: CViewDimArtCommon = _xViewDim
            sValue = xVdac.sValue

        elif isinstance(_xViewDim, CViewDimArt):
            xVda: CViewDimArt = _xViewDim
            sValue = xVda.sValue

        else:
            raise RuntimeError(f"Invalid view dimension object type: {_xViewDim._eType}")
        # endif
        return sValue

    # enddef

    # ##########################################################################################################
    def GetViewDimLabel(self, _xViewDim: CViewDim) -> str:
        sValue: str = None

        if isinstance(_xViewDim, CViewDimGrp):
            xVdg: CViewDimGrp = _xViewDim
            sValue = xVdg.sLabel

        elif isinstance(_xViewDim, CViewDimArtType):
            xVdat: CViewDimArtType = _xViewDim
            xArtType: CArtefactType = self._xProdGrp.dicArtTypes[xVdat.sValue]
            sValue = xArtType.sName

        elif isinstance(_xViewDim, CViewDimArtCommon):
            xVdac: CViewDimArtCommon = _xViewDim
            sValue = xVdac.sLabel

        elif isinstance(_xViewDim, CViewDimArt):
            xVda: CViewDimArt = _xViewDim
            sValue = xVda.sLabel

        else:
            raise RuntimeError(f"Invalid view dimension object type: {_xViewDim._eType}")
        # endif
        return sValue

    # enddef


# endclass
