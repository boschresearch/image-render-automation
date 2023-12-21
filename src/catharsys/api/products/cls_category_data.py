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
from .cls_category_collection import CCategoryCollection


class CCategoryData:
    def __init__(self):
        self._dicVarValCat: dict[str, dict[str, dict[str, Any]]] = dict()
        self._xCatCln: CCategoryCollection = CCategoryCollection()
        self._pathFile: Path = None
        self._dicConfig: dict = None

    # enddef

    @property
    def dicVarValCat(self) -> dict[str, dict[str, dict[str, Any]]]:
        return self._dicVarValCat

    # enddef

    @property
    def xCatCln(self) -> CCategoryCollection:
        return self._xCatCln

    # enddef

    # ##################################################################################################
    def Create(self, *, _pathFile: Path, _xCatCln: CCategoryCollection, _bReplace: bool = False):
        """Create a new category data file. The file must not exist. If it exists, it can be replaced
        by setting the _bReplace parameter to True.

        Parameters
        ----------
        _pathFile : Path
            The path to the category data file.
        _xCatCln : CCategoryCollection
            The category collection object.
        _bReplace : bool, optional
            If True, an existing category data file will be replaced. The default is False.
        """
        if _pathFile.exists() and _bReplace is False:
            raise RuntimeError(f"Category data file already exists: {(_pathFile.as_posix())}")
        elif _bReplace is True:
            _pathFile.unlink()
        # endif

        self._dicVarValCat.clear()
        self._pathFile = _pathFile
        self._xCatCln = _xCatCln
        self._dicConfig = {
            "sDTI": "/catharsys/production/category-data:1.0",
            "mCategories": self._xCatCln.ToDict(),
            "mData": self._dicVarValCat,
        }

    # endif

    # ##################################################################################################
    def CopyCompatibleCategoryDataFrom(self, _xCatData: "CCategoryData", _bDoSave: bool = True):
        """Copy the compatible category data from another category data object. Only those categories
        are copied, which are compatible with the categories of this object.

        Parameters
        ----------
        _xCatData : CCategoryData
            The category data object to copy from.
        """

        # find compatible categories
        lCompatibleCatIds: list[str] = list()
        for sCatId, xCat in _xCatData._xCatCln._dicCat.items():
            if sCatId in self._xCatCln and xCat.eType == self._xCatCln.Get(sCatId).eType:
                lCompatibleCatIds.append(sCatId)
            # endif
        # endfor

        # copy the compatible categories
        for sVarId, dicValCat in _xCatData._dicVarValCat.items():
            for sValName, dicCat in dicValCat.items():
                for sCatId in lCompatibleCatIds:
                    if sCatId in dicCat:
                        self.SetValue(
                            _sVarId=sVarId,
                            _sVarValue=sValName,
                            _sCatId=sCatId,
                            _xCatValue=dicCat[sCatId],
                            _bDoSave=False,
                        )
                    # endif
                # endfor
            # endfor
        # endfor

        if _bDoSave is True:
            self.SaveToFile()
        # endif

    # enddef

    # ##################################################################################################
    def FromFile(self, _pathFile: Path):
        """Load the category data from a file. The file must exist and must be a valid category data.
        Parameters
        ----------
        _pathFile : Path
            The path to the category data file.
        """
        if not _pathFile.exists():
            raise RuntimeError(f"Category data file does not exists: {(_pathFile.as_posix())}")
        # endif

        self._pathFile = _pathFile
        self._dicConfig: dict = config.Load(_pathFile, sDTI="/catharsys/production/category-data:1.0")

        dicData = self._dicConfig.get("mData")
        if not isinstance(dicData, dict):
            self._dicVarValCat.clear()
        else:
            self._dicVarValCat = dicData
        # endif

        dicCats: dict = self._dicConfig.get("mCategories")
        if isinstance(dicCats, dict):
            self._xCatCln.FromConfigDict(dicCats)
        else:
            raise RuntimeError("Category data is missing category definition block 'mCategories'")
        # endif

    # endif

    # ##################################################################################################
    def SetValue(
        self,
        *,
        _sVarId: str,
        _sVarValue: str,
        _sCatId: str,
        _xCatValue: Any,
        _bDoSave: bool = True,
    ):
        xCat = self._xCatCln.Get(_sCatId)
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

        if _bDoSave is True:
            self.SaveToFile()
        # endif

    # enddef

    # ##################################################################################################
    def SaveToFile(self, _pathFile: Union[Path, None] = None):
        if _pathFile is not None:
            self._pathFile = _pathFile
        # endif

        if "mData" not in self._dicConfig:
            self._dicConfig["mData"] = self._dicVarValCat
        # endif

        config.Save(self._pathFile, self._dicConfig)

    # enddef

    # ##################################################################################################
    def RenameFile(self, _pathFile: Path):
        if self._pathFile is not None:
            self._pathFile.rename(_pathFile)
            self._pathFile = _pathFile
        # endif

    # enddef


# endclass
