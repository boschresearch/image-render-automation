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
from ..api.cls_workspace import CWorkspace
from .cls_variant_trial import CVariantTrial


# #####################################################################################
class CVariantLaunch:
    def __init__(self):
        self._pathGroup: Path = None
        self._pathVariant: Path = None

        self._xProject: CProject = None
        self._pathLaunchFile: Path = None

        self._iId: int = None
        self._sInfo: str = None

        self._iNextTrialVarId: int = 1
        self._dicTrialVariants: dict[int, CVariantTrial] = None

    # enddef

    # ############################################################################################
    def FromConfig(self, *, _pathGroup: Path, _prjX: CProject, _dicCfg: dict):
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
        sLaunchFilename = convert.DictElementToString(_dicCfg, "sLaunchFilename")
        self._pathLaunchFile = self._pathVariant / sLaunchFilename

        self._dicTrialVariants = {}
        dicCfgTrialVariants: dict = _dicCfg.get("mTrialVariants")
        if not isinstance(dicCfgTrialVariants, dict):
            raise RuntimeError("Element 'mTrialVariants' missing in launch variant configuration")
        # endif

        for iTrialVarId in dicCfgTrialVariants:
            xVarTrial = CVariantTrial()
            xVarTrial.FromConfig(
                _prjX=self._xProject, _pathGroup=self._pathVariant, _dicCfg=dicCfgTrialVariants[iTrialVarId]
            )
            self._dicTrialVariants[iTrialVarId] = xVarTrial
        # endfor

    # enddef

    # ############################################################################################
    def Create(self, *, _iId: int, _sInfo: str, _pathGroup: Path, _prjX: CProject):
        pathVariant: Path = _pathGroup / f"lv-{_iId}"
        if pathVariant.exists():
            raise RuntimeError(f"Launch variant path already exists: {(pathVariant.as_posix())}")
        # endif
        self._pathVariant = pathVariant
        self._pathVariant.mkdir(parents=True)

        self._iId = _iId
        self._sInfo = _sInfo
        self._pathGroup = _pathGroup
        self._xProject = _prjX
        pathSrcLaunchFile = self._xProject.xConfig.pathLaunchFile
        self._pathLaunchFile = self._pathVariant / f"{pathSrcLaunchFile.stem}.json"
        self._dicTrialVariants = {}

        # Load launch file and save as standard json
        dicLaunch = config.Load(pathSrcLaunchFile, sDTI="/catharsys/launch:*", bReplacePureVars=False)
        config.Save(self._pathLaunchFile, dicLaunch)

        # shutil.copyfile(pathSrcLaunchFile.as_posix(), self._pathLaunchFile.as_posix())

        self.AddTrialVariant()

    # enddef

    # ############################################################################################
    def AddTrialVariant(self, *, _sInfo: str = "") -> int:
        iId = self._iNextTrialVarId
        xVarTrial = CVariantTrial()
        xVarTrial.Create(_iId=iId, _sInfo=_sInfo, _pathGroup=self._pathVariant, _prjX=self._xProject)
        self._dicTrialVariants[iId] = xVarTrial
        self._iNextTrialVarId += 1

        return iId

    # enddef

    # ############################################################################################
    def GetTrialVariant(self, _iId: int) -> CVariantTrial:
        return self._dicTrialVariants.get(_iId)

    # enddef

    # ############################################################################################
    def UpdateFromSource(self, *, _bOverwrite: Optional[bool] = False):
        pathSrc: Path = self._xProject.xConfig.pathLaunch / self._pathLaunchFile.stem
        pathFullSrc = anypath.ProvideReadFilepathExt(pathSrc, [".json", ".json5", ".ison"])
        if pathFullSrc is None:
            raise RuntimeError(f"Source launch file not found at: {(pathFullSrc.as_posix())}[.json|.json5|.ison]")
        # endif
        pathSrc = pathFullSrc

        dicLaunch = config.Load(pathSrc, bReplacePureVars=False)
        if _bOverwrite is False:
            dicLaunchAct = config.Load(self._pathLaunchFile, bReplacePureVars=False)
            DictRecursiveUpdate(dicLaunch, dicLaunchAct, _lRegExExclude=["sTrialFile"], _bAddSrcKeysNotInTrg=False)
        # endif
        config.Save(self._pathLaunchFile, dicLaunch)

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
            "sDTI": "/catharsys/variants/launch:1.0",
            "iId": self._iId,
            "sInfo": self._sInfo,
            "iNextTrialVarId": self._iNextTrialVarId,
            "sLaunchFilename": self._pathLaunchFile.name,
            "mTrialVariants": dicTrialVars,
        }

        return dicData

    # enddef


# endclass
