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
from .cls_category import ECategoryType, CCategory, CCategoryTypeBool, CCategoryTypeBoolGroup


class CCategoryCollection:
    def __init__(self):
        self._dicCat: dict[str, CCategory] = dict()

    # enddef

    def __contains__(self, _sKey: str) -> bool:
        return _sKey in self._dicCat

    # enddef

    # ##################################################################################################
    # test two instances for equality
    # tests only category ids and types
    def __eq__(self, _xOther: Any) -> bool:
        """Test two instances for equality. Tests only category ids, types and default value."""

        if not isinstance(_xOther, CCategoryCollection):
            return False
        # endif

        for sKey, xCat in self._dicCat.items():
            if sKey not in _xOther._dicCat:
                return False
            # endif
            xCatOther = _xOther._dicCat[sKey]
            if xCat.eType != xCatOther.eType:
                return False
            # endif

            if xCat.GetDefaultValue() != xCatOther.GetDefaultValue():
                return False
            # endif
        # endfor

        return True

    # enddef

    # ##################################################################################################
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

            if lType[0] == "boolean":
                self._dicCat[sKey] = CCategoryTypeBool(_sKey=sKey, _dicData=dicData)
            elif lType[0] == "boolean-group":
                self._dicCat[sKey] = CCategoryTypeBoolGroup(_sKey=sKey, _dicData=dicData)
            else:
                raise RuntimeError(
                    f"Unsupported specific category type '{(lType[0])}' for category definition '{sKey}'"
                )
            # endif

        # endfor

    # enddef

    def ToDict(self) -> dict:
        dicData: dict = dict()

        for sKey, xCat in self._dicCat.items():
            dicData[sKey] = xCat.ToDict()
        # endfor
        return dicData

    # enddef

    def Get(self, _sKey: str) -> Union[CCategory, None]:
        return self._dicCat.get(_sKey)

    # enddef


# endclass
