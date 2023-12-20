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
from pathlib import Path
from typing import Union, Any
from anybase import config
from .cls_category import CCategoryCollection


class CCategoryData:
    def __init__(self):
        self._dicVarValCat: dict[str, dict[str, dict[str, Any]]] = dict()
        self._pathFile: Path = None
        self._dicConfig: dict = None

    # enddef

    @property
    def dicVarValCat(self) -> dict[str, dict[str, dict[str, Any]]]:
        return self._dicVarValCat

    # enddef

    def FromFile(self, _pathFile: Path):
        if not _pathFile.exists():
            self._dicVarValCat.clear()
            self._pathFile = _pathFile
            self._dicConfig = {"sDTI": "/catharsys/production/category-data:1.0", "mData": self._dicVarValCat}
        else:
            self._pathFile = _pathFile
            self._dicConfig: dict = config.Load(_pathFile, sDTI="/catharsys/production/category-data:1.0")
            dicData = self._dicConfig.get("mData")
            if not isinstance(dicData, dict):
                self._dicVarValCat.clear()
            else:
                self._dicVarValCat = dicData
            # endif
        # endif

    # endif

    def SetValue(
        self,
        *,
        _sVarId: str,
        _sVarValue: str,
        _sCatId: str,
        _xCatValue: Any,
        _xCatCln: CCategoryCollection,
        _bDoSave: bool = True,
    ):
        xCat = _xCatCln.Get(_sCatId)
        if xCat is None:
            raise RuntimeError(
                f"Category '{_sCatId}' not defined. "
                "Trying to set variable '{_sVarId}' for value '{_sVarValue}' with value '{_xCatValue}'"
            )
        # endif

        # If the default value for the categorie is to be set, then do not enter
        # it into the database. Also, remove an already present element, if it
        # is set to the default value.
        bIsDefaultValue: bool = _xCatValue == xCat.GetDefaultValue()

        dicValCat = self._dicVarValCat.get(_sVarId)
        if dicValCat is None:
            if bIsDefaultValue is True:
                return
            # endif
            self._dicVarValCat[_sVarId] = dict()
            dicValCat = self._dicVarValCat[_sVarId]
        # endif

        dicCat = dicValCat.get(_sVarValue)
        if dicCat is None:
            if bIsDefaultValue is True:
                return
            # endif
            dicValCat[_sVarValue] = dict()
            dicCat = dicValCat[_sVarValue]
        # endif

        if _sCatId not in dicCat and bIsDefaultValue is True:
            return
        # endif

        if _sCatId in dicCat and bIsDefaultValue is True:
            del dicCat[_sCatId]
        else:
            dicCat[_sCatId] = _xCatValue
        # endif

        if len(dicCat) == 0:
            del dicValCat[_sVarValue]
            if len(dicValCat) == 0:
                del self._dicVarValCat[_sVarId]
            # endif
        # endif

        if "mData" not in self._dicConfig:
            self._dicConfig["mData"] = self._dicVarValCat
        # endif

        if _bDoSave is True:
            config.Save(self._pathFile, self._dicConfig)
        # endif

    # enddef


# endclass
