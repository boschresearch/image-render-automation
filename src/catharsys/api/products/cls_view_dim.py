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


class EViewDimType(enum.Enum):
    GROUP = enum.auto()
    ARTTYPE = enum.auto()
    ARTCOMVAR = enum.auto()
    ARTVAR = enum.auto()


# endclass


class CViewDim:
    def __init__(self, *, _eType: EViewDimType, _sDimLabel: str = ""):
        self._eType: EViewDimType = _eType
        self._sDimLabel: str = _sDimLabel
        self._iIdx: int = 0
        self._iCnt: int = 0
        self._iMin: int = 0
        self._iMax: int = 0

    # enddef

    @property
    def iIdx(self) -> int:
        return self._iIdx

    # enddef

    @property
    def iCnt(self) -> int:
        return self._iCnt

    # enddef

    @property
    def iRange(self) -> int:
        return self._iMax - self._iMin + 1

    # enddef

    @property
    def iMin(self) -> int:
        return self._iMin

    # enddef

    @property
    def iMax(self) -> int:
        return self._iMax

    # enddef

    @property
    def sDimLabel(self) -> str:
        return self._sDimLabel

    # enddef

    def Next(self) -> bool:
        if self._iIdx + 1 > self._iMax:
            self._iIdx = self._iMin
            return False
        # endif
        self._iIdx += 1
        return True

    # enddef

    def Reset(self):
        self._iIdx = self._iMin

    # enddef


# endclass


class CViewDimGrp(CViewDim):
    def __init__(
        self,
        *,
        _sVarId: str,
        _iVarIdx: int,
        _lValues: list[str],
        _lLabels: list[str],
        _iMin: int,
        _iMax: int,
        _sDimLabel: str = "",
    ):
        super().__init__(_eType=EViewDimType.GROUP, _sDimLabel=_sDimLabel)
        self._sVarId: str = _sVarId
        self._iVarIdx: int = _iVarIdx
        self._lValues: list[str] = _lValues
        self._lLabels: list[str] = _lLabels
        self._iCnt = len(self._lValues)
        self._iMin = _iMin
        self._iMax = _iMax

    # enddef

    @property
    def sVarId(self) -> str:
        return self._sVarId

    # enddef

    @property
    def iVarIdx(self) -> int:
        return self._iVarIdx

    # enddef

    @property
    def sValue(self) -> str:
        return self._lValues[self._iIdx]

    # enddef

    @property
    def sLabel(self) -> str:
        return self._lLabels[self._iIdx]

    # enddef


# endclass


class CViewDimArtCommon(CViewDim):
    def __init__(
        self,
        *,
        _sVarId: str,
        _lArtTypeIds: list[str],
        _lVarIdx: list[int],
        _lValues: list[str],
        _lLabels: list[str],
        _iMin: int,
        _iMax: int,
        _sDimLabel: str = "",
    ):
        super().__init__(_eType=EViewDimType.ARTCOMVAR, _sDimLabel=_sDimLabel)
        self._lArtTypeIds: list[str] = _lArtTypeIds
        self._lVarIdx: list[int] = _lVarIdx
        self._sVarId: str = _sVarId
        self._lValues: list[str] = _lValues
        self._lLabels: list[str] = _lLabels
        self._iCnt = len(self._lValues)
        self._iMin = _iMin
        self._iMax = _iMax

    # enddef

    @property
    def sVarId(self) -> str:
        return self._sVarId

    # enddef

    @property
    def lVarIdx(self) -> list[int]:
        return self._lVarIdx

    # enddef

    @property
    def lArtTypeIds(self) -> list[str]:
        return self._lArtTypeIds

    # enddef

    @property
    def sValue(self) -> str:
        return self._lValues[self._iIdx]

    # enddef

    @property
    def sLabel(self) -> str:
        return self._lLabels[self._iIdx]

    # enddef


# endclass


class CViewDimArtType(CViewDim):
    def __init__(self, *, _lArtTypes: list[str], _sDimLabel: str = ""):
        super().__init__(_eType=EViewDimType.ARTTYPE, _sDimLabel=_sDimLabel)
        self._lArtTypes: list[str] = _lArtTypes
        self._iCnt = len(self._lArtTypes)
        self._iMin = 0
        self._iMax = self._iCnt - 1

    # enddef

    @property
    def sValue(self) -> str:
        return self._lArtTypes[self._iIdx]

    # enddef


# endclass


class CViewDimArt(CViewDim):
    def __init__(
        self,
        *,
        _sVarId: str,
        _sArtTypeId: str,
        _iVarIdx: int,
        _lValues: list[str],
        _lLabels: list[str],
        _iMin: int,
        _iMax: int,
        _sDimLabel: str = "",
    ):
        super().__init__(_eType=EViewDimType.ARTVAR, _sDimLabel=_sDimLabel)
        self._sArtTypeId: str = _sArtTypeId
        self._iVarIdx: int = _iVarIdx
        self._sVarId: str = _sVarId
        self._lValues: list[str] = _lValues
        self._lLabels: list[str] = _lLabels
        self._iCnt = len(self._lValues)
        self._iMin = _iMin
        self._iMax = _iMax

    # enddef

    @property
    def sVarId(self) -> str:
        return self._sVarId

    # enddef

    @property
    def iVarIdx(self) -> int:
        return self._iVarIdx

    # enddef

    @property
    def sArtTypeId(self) -> str:
        return self._sArtTypeId

    # enddef

    @property
    def sValue(self) -> str:
        return self._lValues[self._iIdx]

    # enddef

    @property
    def sLabel(self) -> str:
        return self._lLabels[self._iIdx]

    # enddef


# endclass
