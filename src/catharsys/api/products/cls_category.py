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
from typing import Union, Any
from dataclasses import dataclass

from anybase import config, convert


class ECategoryType(enum.Enum):
    NONE = enum.auto()
    BOOL = enum.auto()
    BOOL_GROUP = enum.auto()


# endclass


# ##################################################################################################
class CCategory:
    def __init__(self, *, _eType: ECategoryType, _sName: str, _sId: str):
        self._eType: ECategoryType = _eType
        self._sId: str = _sId
        self._sName: str = _sName

    # enddef

    @property
    def eType(self) -> ECategoryType:
        return self._eType

    # enddef

    @property
    def sName(self) -> str:
        return self._sName

    # enddef

    @property
    def sId(self) -> str:
        return self._sId

    # enddef

    def GetDefaultValue(self) -> Any:
        return None

    # endef


# endclass


# ##################################################################################################
class CCategoryTypeBool(CCategory):
    def __init__(self, *, _dicData: dict[str, Any], _sKey: str):
        sName = convert.DictElementToString(_dicData, "sName", sDefault=_sKey)

        super().__init__(_eType=ECategoryType.BOOL, _sName=sName, _sId=_sKey)
        self._bDefaultValue: bool = convert.DictElementToBool(_dicData, "bDefaultValue", bDefault=False)
        self._sIconTrue: str = convert.DictElementToString(_dicData, "sIconTrue", sDefault="")
        self._sIconFalse: str = convert.DictElementToString(_dicData, "sIconFalse", sDefault="")
        self._sIconColor: str = convert.DictElementToString(_dicData, "sIconColor", sDefault="")

    # enddef

    @property
    def sIconTrue(self) -> str:
        return self._sIconTrue

    # enddef

    @property
    def sIconFalse(self) -> str:
        return self._sIconFalse

    # enddef

    @property
    def sIconColor(self) -> str:
        return self._sIconColor

    # enddef

    def GetDefaultValue(self) -> Any:
        return self._bDefaultValue

    # enddef

    def ToDict(self) -> dict:
        return {
            "sDTI": "/catharsys/production/category/boolean:1.0",
            "sName": self.sName,
            "bDefaultValue": self._bDefaultValue,
            "sIconTrue": self.sIconTrue,
            "sIconFalse": self.sIconFalse,
            "sIconColor": self.sIconColor,
        }

    # enddef


# endclass


# ##################################################################################################
@dataclass
class CBoolGroupChoice:
    sDescription: str = ""
    sIcon: str = ""
    sColor: str = ""


# endclass


# ##################################################################################################
class CCategoryTypeBoolGroup(CCategory):
    def __init__(self, *, _dicData: dict[str, Any], _sKey: str):
        sName = convert.DictElementToString(_dicData, "sName", sDefault=_sKey)
        super().__init__(_eType=ECategoryType.BOOL_GROUP, _sName=sName, _sId=_sKey)

        self._iDefaultValue = convert.DictElementToInt(_dicData, "iDefaultValue", iDefault=0)

        self._lChoices: list[CBoolGroupChoice] = list()

        lGroup: list[dict[str]] = _dicData.get("lGroup")
        if lGroup is None:
            raise RuntimeError(f"Category '{_sKey}' has no 'lGroup' element")
        # endif
        if not isinstance(lGroup, list):
            raise RuntimeError(f"Category '{_sKey}' 'lGroup' element is not a list")
        # endif
        if len(lGroup) == 0:
            raise RuntimeError(f"Category '{_sKey}' 'lGroup' element is empty")
        # endif
        for dicChoice in lGroup:
            if not isinstance(dicChoice, dict):
                raise RuntimeError(f"Category '{_sKey}' 'lGroup' element contains non-dictionary elements")
            # endif

            sDescription = convert.DictElementToString(dicChoice, "sDescription", sDefault="")
            sIcon = convert.DictElementToString(dicChoice, "sIcon", sDefault="done")
            sColor = convert.DictElementToString(dicChoice, "sColor", sDefault="")
            self._lChoices.append(CBoolGroupChoice(sDescription=sDescription, sIcon=sIcon, sColor=sColor))
        # endfor

    # enddef

    @property
    def lChoices(self) -> list[CBoolGroupChoice]:
        return self._lChoices

    # enddef

    def GetDefaultValue(self) -> Any:
        return self._iDefaultValue

    # enddef

    def ToDict(self) -> dict:
        lGroup: list[dict[str, Any]] = list()
        for xChoice in self._lChoices:
            lGroup.append(
                {
                    "sDescription": xChoice.sDescription,
                    "sIcon": xChoice.sIcon,
                    "sColor": xChoice.sColor,
                }
            )
        # endfor

        return {
            "sDTI": "/catharsys/production/category/boolean-group:1.0",
            "sName": self.sName,
            "iDefaultValue": self._iDefaultValue,
            "lGroup": lGroup,
        }

    # enddef


# endclass
