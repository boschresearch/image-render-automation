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

from collections.abc import Iterable
from typing import Optional, Callable, Union, Any

from .cls_view_dim import CViewDim, CViewDimGrp, CViewDimArtCommon, CViewDimArt, CViewDimArtType, TCatPathValue
from .cls_path_structure import CPathStructure, CPathVarHandlerResult, CPathVar, EPathVarType, ENodeType
from .cls_group import CArtefactType


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
    def xProdView(self) -> "CProductView":
        return self._xProdView

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
    def sVarId(self) -> str:
        return self._xProdView.GetViewDimVarId(self._xViewDim)

    # enddef

    @property
    def dicCategories(self) -> TCatPathValue:
        return self._xProdView.GetViewDimCategories(self._xViewDim)

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

    @property
    def lCategories(self) -> Iterable[TCatPathValue]:
        self._xViewDim.Reset()
        while True:
            yield self.dicCategories
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
