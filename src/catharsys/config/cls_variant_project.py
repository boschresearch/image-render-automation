###
# Author: Christian Perwass (CR/AEC5)
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
import copy
import shutil
from dataclasses import dataclass
from typing import Optional

from pathlib import Path
from anybase import config, convert
from anybase import path as anypath
from ..util.data import DictRecursiveUpdate

from ..api.cls_project import CProject

# from ..api.cls_workspace import CWorkspace
# from ..config.cls_launch import CConfigLaunch
from .cls_variant_trial import CVariantTrial
from .cls_launch import CConfigLaunch
from ..util import fsops


# #####################################################################################
class CVariantProject:
    def __init__(self):
        self._Clear()

    # enddef

    def _Clear(self):
        self._pathGroup: Path = None
        self._pathVariant: Path = None

        self._xProject: CProject = None
        # self._pathLaunchFile: Path = None
        self._xLaunch: CConfigLaunch = None
        self._sSrcLaunchFilename: str = None
        self._sLaunchFileStem: str = None
        self._setLaunchFileIds: set[int] = None
        self._iSelectedLaunchFileId: int = None
        self._iNextLaunchFileId: int = None
        self._dicLaunchFileInfo: dict[int, str] = None

        self._iId: int = None
        self._sInfo: str = None

        self._iNextTrialVarId: int = 1
        self._dicTrialVariants: dict[int, CVariantTrial] = None

    # enddef

    @property
    def pathLaunchFile(self) -> Path:
        return self.GetPathLaunchFile(self._iSelectedLaunchFileId)

    # enddef

    @property
    def xLaunch(self) -> CConfigLaunch:
        return self._xLaunch

    # enddef

    @property
    def lTrialVariantIds(self) -> list[int]:
        return list(self._dicTrialVariants.keys())

    # enddef

    @property
    def setLaunchFileIds(self) -> set[int]:
        return self._setLaunchFileIds.copy()

    # enddef

    @property
    def dicLaunchFileInfo(self) -> dict[int, str]:
        return self._dicLaunchFileInfo

    # enddef

    @property
    def iSelectedLaunchFileId(self) -> int:
        return self._iSelectedLaunchFileId

    # enddef

    @property
    def iLaunchFileVariantCount(self) -> int:
        return len(self._setLaunchFileIds)

    # enddef

    @property
    def sSrcLaunchFilename(self) -> str:
        return self._sSrcLaunchFilename

    # enddef

    # ############################################################################################
    def GetLaunchFilename(self, _iId: int) -> str:
        return f"{self._sLaunchFileStem}-{_iId}.json"

    # enddef

    # ############################################################################################
    def GetPathLaunchFile(self, _iId: int) -> Path:
        return self._pathVariant / self.GetLaunchFilename(_iId)

    # enddef

    # ############################################################################################
    def GetPathSourceLaunchFile(self) -> Path:
        return self._xProject.xConfig.pathLaunch / self._sSrcLaunchFilename

    # enddef

    # ############################################################################################
    def FromConfig(self, *, _pathGroup: Path, _prjX: CProject, _dicCfg: dict):
        dicDti = config.CheckConfigType(_dicCfg, "/catharsys/variants/project:1")
        if dicDti["bOK"] is False:
            raise RuntimeError("Variant configuration type not supported")
        # endif

        self._iId = convert.DictElementToInt(_dicCfg, "iId")

        pathVariant: Path = _pathGroup / f"lv-{self._iId}"
        if not pathVariant.exists():
            raise RuntimeError(
                f"Launch variant folder '{pathVariant.name}' already exists at: {(pathVariant.as_posix())}"
            )
        # endif
        self._pathVariant = pathVariant
        self._pathGroup = _pathGroup
        self._xProject = _prjX

        self._sInfo = convert.DictElementToString(_dicCfg, "sInfo", sDefault="")
        self._iNextTrialVarId = convert.DictElementToInt(_dicCfg, "iNextTrialVarId")
        self._sSrcLaunchFilename = convert.DictElementToString(_dicCfg, "sSrcLaunchFilename")
        self._sLaunchFileStem = convert.DictElementToString(_dicCfg, "sLaunchFileStem")
        self._setLaunchFileIds = set(convert.DictElementToIntList(_dicCfg, "lLaunchFileIds"))
        self._iSelectedLaunchFileId = convert.DictElementToInt(_dicCfg, "iSelectedLaunchFileId")
        self._iNextLaunchFileId = convert.DictElementToInt(_dicCfg, "iNextLaunchFileId")

        self._xLaunch = CConfigLaunch(config.Load(self.pathLaunchFile, bReplacePureVars=False))

        self._dicTrialVariants = {}
        dicCfgTrialVariants: dict = _dicCfg.get("mTrialVariants")
        if not isinstance(dicCfgTrialVariants, dict):
            raise RuntimeError("Element 'mTrialVariants' missing in launch variant configuration")
        # endif

        sTrialVarId: str = None
        for sTrialVarId in dicCfgTrialVariants:
            iTrialVarId: int = int(sTrialVarId)
            xVarTrial = CVariantTrial()
            xVarTrial.FromConfig(
                _prjX=self._xProject,
                _pathGroup=self._pathVariant,
                _xLaunch=self._xLaunch,
                _dicCfg=dicCfgTrialVariants[sTrialVarId],
            )
            self._dicTrialVariants[iTrialVarId] = xVarTrial
        # endfor

    # enddef

    # ############################################################################################
    def Create(self, *, _iId: int, _sInfo: str, _pathGroup: Path, _prjX: CProject):
        pathVariant: Path = _pathGroup / f"lv-{_iId}"
        if pathVariant.exists():
            raise RuntimeError(f"Project variant path already exists: {(pathVariant.as_posix())}")
        # endif
        self._pathVariant = pathVariant
        self._pathVariant.mkdir(parents=True)

        self._iId = _iId
        self._sInfo = _sInfo
        self._pathGroup = _pathGroup
        self._xProject = _prjX

        self._iNextLaunchFileId = 1
        pathSrcLaunchFile = self._xProject.xConfig.pathLaunchFile
        self._sSrcLaunchFilename = pathSrcLaunchFile.name
        self._sLaunchFileStem = pathSrcLaunchFile.stem
        self._setLaunchFileIds = set([self._iNextLaunchFileId])

        self._iSelectedLaunchFileId = self._iNextLaunchFileId
        self._iNextLaunchFileId += 1
        self._dicTrialVariants = {}

        # Load launch file and save as standard json
        dicLaunch = config.Load(pathSrcLaunchFile, sDTI="/catharsys/launch:*", bReplacePureVars=False)
        config.Save(self.pathLaunchFile, dicLaunch)
        self._xLaunch = CConfigLaunch(dicLaunch)

        # shutil.copyfile(pathSrcLaunchFile.as_posix(), self._pathLaunchFile.as_posix())

        self.AddTrialVariant()

    # enddef

    # ############################################################################################
    def Destroy(self):
        if isinstance(self._pathVariant, Path) and self._pathVariant.exists():
            fsops.RemoveTree(self._pathVariant, bIgnoreErrors=True)
        # endif
        self._Clear()

    # enddef

    # ############################################################################################
    def AddLaunchFileVariant(self, *, _bSelect: bool = False, _bCopyCurrent: bool = True, _sInfo: str = "") -> int:
        self._setLaunchFileIds.add(self._iNextLaunchFileId)
        iNewId: int = self._iNextLaunchFileId
        self._iNextLaunchFileId += 1

        if _bCopyCurrent is True:
            dicLaunch = config.Load(self.pathLaunchFile, sDTI="/catharsys/launch:*", bReplacePureVars=False)
        else:
            dicLaunch = config.Load(self.GetPathSourceLaunchFile(), sDTI="/catharsys/launch:*", bReplacePureVars=False)
        # endif

        pathNewLaunch = self.GetPathLaunchFile(iNewId)
        config.Save(pathNewLaunch, dicLaunch)

        self._dicLaunchFileInfo[iNewId] = _sInfo

        if _bSelect is True:
            self.SelectLaunchFileVariant(iNewId)
        # endif

        return iNewId

    # enddef

    # ############################################################################################
    def RemoveLaunchFileVariant(self, _iId: int):
        if _iId not in self._setLaunchFileIds:
            raise RuntimeError(f"Launch file variant with id '{_iId}' not available")
        # endif

        if len(self._setLaunchFileIds) <= 1:
            raise RuntimeError("Cannot remove last launch file variant")
        # endif

        pathLaunchFile = self.GetPathLaunchFile(_iId)
        pathLaunchFile.unlink(missing_ok=True)
        self._setLaunchFileIds.discard(_iId)
        del self._dicLaunchFileInfo[_iId]

        if self._iSelectedLaunchFileId == _iId:
            iNewId = next((x for x in self._setLaunchFileIds))
            self.SelectLaunchFileVariant(iNewId)
        # endif

    # enddef

    # ############################################################################################
    def SelectLaunchFileVariant(self, _iId: int):
        if _iId not in self._setLaunchFileIds:
            raise RuntimeError(f"Launch file variant id '{_iId}' not available")
        # endif
        self._iSelectedLaunchFileId = _iId

        self._xLaunch = CConfigLaunch(config.Load(self.pathLaunchFile, bReplacePureVars=False))

        xVarTrial: CVariantTrial = None
        for xVarTrial in self._dicTrialVariants.values():
            xVarTrial.UpdateLaunchConfig(self._xLaunch)
        # endfor

    # enddef

    # ############################################################################################
    def AddTrialVariant(self, *, _sInfo: str = "") -> int:
        iId = self._iNextTrialVarId
        xVarTrial = CVariantTrial()
        xVarTrial.Create(
            _iId=iId, _sInfo=_sInfo, _pathGroup=self._pathVariant, _prjX=self._xProject, _xLaunch=self._xLaunch
        )
        self._dicTrialVariants[iId] = xVarTrial
        self._iNextTrialVarId += 1

        return iId

    # enddef

    # ############################################################################################
    def RemoveTrialVariant(self, _iId: int):
        if _iId not in self._dicTrialVariants:
            raise RuntimeError(f"Trial variant id '{_iId}' not found")
        # endif

        self._dicTrialVariants[_iId].Destroy()
        del self._dicTrialVariants[_iId]

    # enddef

    # ############################################################################################
    def GetTrialVariant(self, _iId: int) -> CVariantTrial:
        return self._dicTrialVariants.get(_iId)

    # enddef

    # ############################################################################################
    def UpdateFromSource(self, *, _bOverwrite: Optional[bool] = False):
        pathSrc: Path = self.GetPathSourceLaunchFile()
        # pathFullSrc = anypath.ProvideReadFilepathExt(pathSrc, [".json", ".json5", ".ison"])
        if not pathSrc.exists():
            raise RuntimeError(f"Source launch file not found at: {(pathSrc.as_posix())}")
        # endif
        # pathSrc = pathFullSrc

        dicLaunch = config.Load(pathSrc, bReplacePureVars=False)
        for iId in self._setLaunchFileIds:
            pathLaunchFile: Path = self.GetPathLaunchFile(iId)
            if _bOverwrite is False:
                dicLaunchAct = config.Load(pathLaunchFile, bReplacePureVars=False)
                DictRecursiveUpdate(dicLaunch, dicLaunchAct, _lRegExExclude=["sTrialFile"], _bAddSrcKeysNotInTrg=False)
            # endif
            config.Save(pathLaunchFile, dicLaunch)
        # endfor

        for iTrialVarId in self._dicTrialVariants:
            self._dicTrialVariants[iTrialVarId].UpdateFromSource(_bOverwrite=_bOverwrite)
        # endfor

    # enddef

    # ############################################################################################
    def Serialize(self) -> dict:
        dicTrialVars = {}
        for iTrialVarId in self._dicTrialVariants:
            dicTrialVars[iTrialVarId] = self._dicTrialVariants[iTrialVarId].Serialize()
        # endfor

        dicData = {
            "sDTI": "/catharsys/variants/project:1.0",
            "iId": self._iId,
            "sInfo": self._sInfo,
            "iNextTrialVarId": self._iNextTrialVarId,
            "sSrcLaunchFilename": self._sSrcLaunchFilename,
            "sLaunchFileStem": self._sLaunchFileStem,
            "lLaunchFileIds": list(self._setLaunchFileIds),
            "iSelectedLaunchFileId": self._iSelectedLaunchFileId,
            "iNextLaunchFileId": self._iNextLaunchFileId,
            "mTrialVariants": dicTrialVars,
        }

        return dicData

    # enddef


# endclass
