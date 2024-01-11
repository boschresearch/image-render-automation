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
#   Unless required by applicable law or agreed to in writing, software0
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# </LICENSE>
###

from collections.abc import Iterable
from typing import Optional, Callable, Union, Any

from .cls_view_dim import CViewDim, CViewDimGrp, CViewDimArtCommon, CViewDimArt, CViewDimArtType, TCatPathValue
from .cls_view_dim_node import CViewDimNode
from .cls_path_structure import CPathStructure, CPathVarHandlerResult, CPathVar, EPathVarType, ENodeType
from .cls_group import CArtefactType
from .cls_product_view import CProductView


class CViewDimNodePath:
    def __init__(self, _xData: Union[CViewDimNode, str], *, _iParent: int = 0) -> None:
        self._lGrpPath: list[str] = []
        self._lArtPath: list[str] = []
        self._sArtTypeId: Optional[str] = None
        self._sPath: str = ""

        if isinstance(_xData, str):
            self._FromString(_xData)
        elif isinstance(_xData, CViewDimNode):
            self._FromViewDimNode(_xData, _iParent=_iParent)
        else:
            raise TypeError(f"Invalid type for CViewDimNodePath: {type(_xData)}")
        # endif

    # enddef

    # ####################################################################################################################
    def __contains__(self, _xViewDimNodePath: "CViewDimNodePath") -> bool:
        """Checks if the given path is a sub-path of this path"""

        for sGrpPath, sGrpPath2 in zip(self._lGrpPath, _xViewDimNodePath._lGrpPath):
            if sGrpPath != "*" and sGrpPath != sGrpPath2:
                return False
            # endif
        # endfor

        if self._sArtTypeId is not None and self._sArtTypeId != _xViewDimNodePath._sArtTypeId:
            return False
        # endif

        for sArtPath, sArtPath2 in zip(self._lArtPath, _xViewDimNodePath._lArtPath):
            if sArtPath != "*" and sArtPath != sArtPath2:
                return False
            # endif
        # endfor

        return True

    # enddef

    # ####################################################################################################################
    def __str__(self) -> str:
        return self._sPath

    # enddef

    # ####################################################################################################################
    def __repr__(self) -> str:
        return self._sPath

    # enddef

    # ####################################################################################################################
    def __eq__(self, _xViewDimNodePath: "CViewDimNodePath") -> bool:
        return self._sPath == _xViewDimNodePath._sPath

    # enddef

    # ####################################################################################################################
    def __hash__(self) -> int:
        return hash(self._sPath)

    # enddef

    # ####################################################################################################################
    def ContainmentSpecificity(self, _xViewDimNodePath: "CViewDimNodePath") -> int:
        """Returns a value that is larger the higher the number of path elements that are contained in this path where this path is not "*".
        Each match is weighted by the position of the path element in the path.
        This is used to determine the specificity of a path containment. The more specific a path match is,
        the higher the number of non-wildcard path variables.
        If the given path is not a sub-path of this path, -1 is returned."""

        iPos = 1
        iSpecificity = 0
        for sGrpPath, sGrpPath2 in zip(self._lGrpPath, _xViewDimNodePath._lGrpPath):
            if sGrpPath != "*":
                if sGrpPath == sGrpPath2:
                    iSpecificity += iPos
                else:
                    return -1
                # endif
            # endif
            iPos <<= 1
        # endfor

        if self._sArtTypeId is not None:
            if self._sArtTypeId == _xViewDimNodePath._sArtTypeId:
                iSpecificity += iPos
                iPos <<= 1

                for sArtPath, sArtPath2 in zip(self._lArtPath, _xViewDimNodePath._lArtPath):
                    if sArtPath != "*":
                        if sArtPath == sArtPath2:
                            iSpecificity += iPos
                        else:
                            return -1
                        # endif
                    # endif
                    iPos <<= 1
                # endfor
            else:
                return -1
            # endif
        # endif

        return iSpecificity

    # enddef

    # ####################################################################################################################
    def _FromString(self, _sPath: str) -> None:
        self._sPath = _sPath
        lPath = _sPath.split("&")
        self._lGrpPath = lPath[0].split("|")
        if len(lPath) > 1:
            self._sArtTypeId = lPath[1]
            self._lArtPath = lPath[2].split("|")
        # endif

    # enddef

    # ####################################################################################################################
    def _FromViewDimNode(self, _xViewDimNode: CViewDimNode, *, _iParent: int = 0) -> None:
        xProdView: CProductView = _xViewDimNode.xProdView
        self._lGrpPath = ["*"] * xProdView.xGrpPathStruct.iPathVarCount
        self._lArtPath = []
        self._sArtTypeId = None

        if _xViewDimNode.sArtTypeId is None:
            iGrpDimCnt = max(0, _xViewDimNode.iDimIdx + 1 - _iParent)
        else:
            iGrpDimCnt = len(xProdView.lViewDims)
            iArtDimCnt = _xViewDimNode.iDimIdx + 1 - _iParent
            if iArtDimCnt < 0:
                iGrpDimCnt = max(0, iGrpDimCnt - iArtDimCnt)
                iArtDimCnt = 0
            else:
                self._sArtTypeId = _xViewDimNode.sArtTypeId
            # endif
        # endif

        for xViewDim in xProdView.lViewDims[0:iGrpDimCnt]:
            if isinstance(xViewDim, CViewDimGrp):
                xVg: CViewDimGrp = xViewDim
                self._lGrpPath[xVg.iVarIdx] = xVg.sValue
            # endif
        # endfor

        self._sPath = "|".join(self._lGrpPath)

        if self._sArtTypeId is not None:
            xArtPathStruct: CPathStructure = xProdView.dicArtTypes[self._sArtTypeId].xPathStruct
            self._lArtPath = ["*"] * xArtPathStruct.iPathVarCount

            for xViewDim in xProdView.dicArtViewDims[self._sArtTypeId][0:iArtDimCnt]:
                if isinstance(xViewDim, CViewDimArtCommon):
                    xVac: CViewDimArtCommon = xViewDim
                    iArtIdx = xVac.lArtTypeIds.index(self._sArtTypeId)
                    iVarIdx = xVac.lVarIdx[iArtIdx]
                    self._lArtPath[iVarIdx] = xVac.sValue
                elif isinstance(xViewDim, CViewDimArt):
                    xVa: CViewDimArt = xViewDim
                    self._lArtPath[xVa.iVarIdx] = xVa.sValue
                # endif
            # endfor
            self._sPath += f"&{self._sArtTypeId}&" + "|".join(self._lArtPath)
        # endif

    # enddef

    # ####################################################################################################################
    def GetFromPathDict(self, _dicPath: dict[str, Any], _xDefault: Optional[Any] = None) -> Optional[Any]:
        xResult: Optional[Any] = _xDefault
        iSpecMax: int = -1

        for sPath, xData in _dicPath.items():
            xPath = CViewDimNodePath(sPath)
            iSpec = xPath.ContainmentSpecificity(self)
            if iSpec > iSpecMax:
                xResult = xData
                iSpecMax = iSpec
            # endif
        # endfor

        return xResult

    # enddef

    # ####################################################################################################################
    def SetInPathDict(self, _dicPath: dict[str, Any], _xData: Any, *, _xDefault: Optional[Any] = None) -> None:
        """Adds this path to the dictionary with the given data as value if the path is not yet in the dictionary
        and there is no more general path that contains this path with the same data.
        If there is no more general path that contains this path with the same data, and the data is the default value,
        then the path is removed from the dictionary."""

        # Get matching paths in dictionary sorted by specificity, with highest specificity first
        lMatchingPaths = []
        for sPath, xData in _dicPath.items():
            xPath = CViewDimNodePath(sPath)
            iSpec = xPath.ContainmentSpecificity(self)
            if iSpec > -1:
                lMatchingPaths.append((xPath, iSpec, xData))
            # endif
        # endfor
        lMatchingPaths.sort(key=lambda x: x[1], reverse=True)

        # print("")
        # print(f"self: {(str(self))}")
        # print(f"dicPath: {_dicPath}")
        # print(f"lMatchingPaths: {lMatchingPaths}")
        # print(f"_xData: {_xData}")

        # Check if there are matching paths
        if len(lMatchingPaths) > 0:
            # Check if the most specific path is equal to this path
            if lMatchingPaths[0][0] == self:
                # If there is a more general path with the same data or no more general path but the data is the default value,
                # remove this path from the dictionary.
                # Otherwise, update the data of this path in the dictionary.
                if (len(lMatchingPaths) > 1 and lMatchingPaths[1][2] == _xData) or (
                    len(lMatchingPaths) == 1 and _xData == _xDefault
                ):
                    del _dicPath[str(self)]
                else:
                    _dicPath[str(self)] = _xData
                # endif
            else:
                # If the data for this path differs from the data of the most specific path, add this path to the dictionary.
                if lMatchingPaths[0][2] != _xData:
                    _dicPath[str(self)] = _xData
                # endif
            # endif

        else:
            # If the data is not the default value, add the path to the dictionary
            if _xData != _xDefault:
                _dicPath[str(self)] = _xData
            # endif
        # endif

    # enddef


# endclass
