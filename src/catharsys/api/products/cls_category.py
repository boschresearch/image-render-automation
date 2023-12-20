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
from anybase import config


class ECategoryType(enum.Enum):
    NONE = enum.auto()
    BOOL = enum.auto()


# endclass


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


class CCategoryTypeBool(CCategory):
    def __init__(self, *, _sName: str, _sId: str, _sIconTrue: str = "", _sIconFalse: str = "", _sIconColor: str = ""):
        super().__init__(_eType=ECategoryType.BOOL, _sName=_sName, _sId=_sId)
        self._sIconTrue: str = _sIconTrue
        self._sIconFalse: str = _sIconFalse
        self._sIconColor: str = _sIconColor

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
        return False

    # enddef


# endclass


class CCategoryCollection:
    def __init__(self):
        self._dicCat: dict[str, CCategory] = dict()

    # enddef

    def __contains__(self, _sKey: str) -> bool:
        return _sKey in self._dicCat

    # enddef

    def FromConfigDict(self, _dicCfg: dict[str, dict]):
        for sKey, dicData in _dicCfg.items():
            if sKey.startswith("__"):
                continue
            # endif

            if not isinstance(dicData, dict):
                raise RuntimeError(f"Category '{sKey}' definition element has to be a dictionary")
            # endif

            xDtiInfo = config.CDtiInfo(config.CheckConfigType(dicData, "/catharsys/production/category/*:*"))
            if xDtiInfo.bOk is False:
                raise RuntimeError(f"Invalid DTI type for category definition '{sKey}': {xDtiInfo.sConfigDti}")
            # endif
            lType = xDtiInfo.lConfigType[3:]
            if len(lType) == 0:
                raise RuntimeError(
                    f"No specific category type given for category definition '{sKey}': {xDtiInfo.sConfigDti}"
                )
            # endif
            # lVer = xDtiInfo.lConfigVersion

            sName = dicData.get("sName", sKey)

            if lType[0] == "boolean":
                sIconTrue = dicData.get("sIconTrue", "")
                sIconFalse = dicData.get("sIconFalse", "")
                sIconColor = dicData.get("sIconColor", "")
                self._dicCat[sKey] = CCategoryTypeBool(
                    _sName=sName,
                    _sId=sKey,
                    _sIconTrue=sIconTrue,
                    _sIconFalse=sIconFalse,
                    _sIconColor=sIconColor,
                )
            else:
                raise RuntimeError(
                    f"Unsupported specific category type '{(lType[0])}' for category definition '{sKey}'"
                )
            # endif

        # endfor

    # enddef

    def Get(self, _sKey: str) -> Union[CCategory, None]:
        return self._dicCat.get(_sKey)

    # enddef


# endclass
