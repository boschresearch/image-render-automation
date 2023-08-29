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
from .cls_trial_actions import CTrialActions
from .cls_launch import CConfigLaunch


# #####################################################################################
class CVariantTrial:
    def __init__(self):
        self._iId: int = None
        self._sInfo: str = None
        self._pathGroup: Path = None
        self._pathVariant: Path = None
        self._xProject: CProject = None
        self._xTrialAct: CTrialActions = None

        self._lRelPathFiles: list[str] = None

    # enddef

    @property
    def xTrialActions(self) -> CTrialActions:
        return self._xTrialAct

    # enddef


    # ##################################c##########################################################
    def UpdateLaunchConfig(self, _xLaunch: CConfigLaunch):
        self._xTrialAct = CTrialActions(_xLaunch)
    # enddef

    # ##################################c##########################################################
    def FromConfig(self, *, _pathGroup: Path, _prjX: CProject, _xLaunch: CConfigLaunch, _dicCfg: dict):
        self._iId = convert.DictElementToInt(_dicCfg, "iId")

        pathVariant: Path = _pathGroup / f"tv-{self._iId}"
        if not pathVariant.exists():
            raise RuntimeError(
                f"Trial variant folder '{pathVariant.name}' does not exists at: {(pathVariant.as_posix())}"
            )
        # endif
        self._pathVariant = pathVariant
        self._pathGroup = _pathGroup
        self._xProject = _prjX
        self._xTrialAct = CTrialActions(_xLaunch)

        self._sInfo = convert.DictElementToString(_dicCfg, "sInfo", sDefault="")
        self._lRelPathFiles = convert.DictElementToStringList(_dicCfg, "lRelPathFiles")

        for sRelPathFile in self._lRelPathFiles:
            pathFile: Path = self._pathVariant / sRelPathFile
            if not pathFile.exists():
                raise RuntimeError(f"Trial variant file missing: {(pathFile.as_posix())}")
            # endif
        # endfor

    # enddef

    # ############################################################################################
    def Create(self, *, _iId: int, _sInfo: str, _pathGroup: Path, _prjX: CProject, _xLaunch: CConfigLaunch):
        pathVariant: Path = _pathGroup / f"tv-{_iId}"
        if pathVariant.exists():
            raise RuntimeError(f"Trial variant path already exists: {(pathVariant.as_posix())}")
        # endif
        self._pathVariant = pathVariant
        self._pathVariant.mkdir(parents=True)

        self._iId = _iId
        self._sInfo = _sInfo
        self._pathGroup = _pathGroup
        self._xProject = _prjX
        self._xTrialAct = CTrialActions(_xLaunch)

        self._lRelPathFiles = []

        for sTrialFile in self._xTrialAct.lTrialFiles:
            self.AddFileConfig(sTrialFile)
        # endfor

    # enddef

    # ############################################################################################
    def AddFileConfig(self, _sRelPathFile: str):
        pathSrc = self.GetConfigSourceAbsPath(_sRelPathFile)
        if pathSrc is None:
            raise RuntimeError(f"Source file does not exist: {(pathSrc.as_posix())}[.json|.json5|.ison]")
        # endif

        sSrcRel = self.GetConfigVariantRelPathFromSourceAbsPath(pathSrc)

        pathTrg: Path = self._pathVariant / sSrcRel
        if pathTrg.exists():
            raise RuntimeError(f"Target file already exists: {(pathTrg.as_posix())}")
        # endif

        # Load config file and save as standard json
        dicCfg = config.Load(pathSrc, bReplacePureVars=False)
        config.Save(pathTrg, dicCfg)

        # shutil.copyfile(pathSrc, pathTrg)

        self._lRelPathFiles.append(sSrcRel)

    # enddef

    # ############################################################################################
    def GetVariantAbsPath(self, _sRelPathFile: str) -> Path:
        return self._pathVariant / _sRelPathFile

    # enddef

    # ############################################################################################
    def GetConfigVariantRelPathFromSourceAbsPath(self, _pathSrc: Path) -> str:
        pathSrcRel: Path = _pathSrc.relative_to(self._xProject.xConfig.pathLaunch)
        pathSrcRel = pathSrcRel.parent / f"{pathSrcRel.stem}.json"
        return pathSrcRel.as_posix()

    # enddef

    # ############################################################################################
    def GetConfigSourceAbsPath(self, _sRelPathFile: str) -> Path:
        pathRelFile = Path(_sRelPathFile)
        pathSrc: Path = self._xProject.xConfig.pathLaunch / pathRelFile.parent / f"{pathRelFile.stem}"
        return anypath.ProvideReadFilepathExt(pathSrc, [".json", ".json5", ".ison"], bDoRaise=False)

    # enddef

    # ############################################################################################
    def CreateVariantSourceTargetPaths(self, _pathTrg: Path) -> list[tuple[Path, Path]]:
        lPathMap: list[tuple[Path, Path]] = []

        for sRelPathFile in self._lRelPathFiles:
            pathSrcFile = self.GetVariantAbsPath(sRelPathFile)
            pathTrgFile = _pathTrg / sRelPathFile
            lPathMap.append((pathSrcFile, pathTrgFile))
        # endfor

        return lPathMap

    # enddef

    # ############################################################################################
    def UpdateFromSource(self, *, _bOverwrite: Optional[bool] = False):
        lRemoveFiles: list[int] = []
        # Rescan the launch file for the current set of trial files and their actions
        self._xTrialAct = CTrialActions(self._xProject.xLaunch)

        lSrcFilePaths: list[str] = []
        lVarRelFilePaths: list[str] = []
        for sTrialFile in self._xTrialAct.lTrialFiles:
            pathSrc = self.GetConfigSourceAbsPath(sTrialFile)
            if pathSrc is None:
                continue
            # endif
            lSrcFilePaths.append(pathSrc.as_posix())

            sRelPathFile = self.GetConfigVariantRelPathFromSourceAbsPath(pathSrc)
            lVarRelFilePaths.append(sRelPathFile)
        # endfor

        sRelPathFile: str = None
        for iIdx, sRelPathFile in enumerate(self._lRelPathFiles):
            pathVar = self.GetVariantAbsPath(sRelPathFile)
            pathSrc = self.GetConfigSourceAbsPath(sRelPathFile)
            if not pathVar.exists() or not pathSrc.exists():
                lRemoveFiles.append(iIdx)
            elif pathSrc.as_posix() not in lSrcFilePaths:
                lRemoveFiles.append(iIdx)
            else:
                dicCfg = config.Load(pathSrc, bReplacePureVars=False)
                if _bOverwrite is False:
                    dicCfgVar = config.Load(pathVar, bReplacePureVars=False)
                    DictRecursiveUpdate(dicCfg, dicCfgVar, _bAddSrcKeysNotInTrg=False)
                # endif
                config.Save(pathVar, dicCfg)
            # endif
        # endfor

        for iIdx in lRemoveFiles:
            sRelPathFile = self._lRelPathFiles[iIdx]
            pathVar = self.GetVariantAbsPath(sRelPathFile)
            pathVar.unlink(missing_ok=True)
            del self._lRelPathFiles[iIdx]
        # endfor

        for sRelPathFile in lVarRelFilePaths:
            if sRelPathFile not in self._lRelPathFiles:
                self.AddFileConfig(sRelPathFile)
            # endif
        # endfor

    # enddef

    # ############################################################################################
    def Serialize(self) -> dict:
        dicData = {
            "sDTI": "/catharsys/variants/trial:1.0",
            "iId": self._iId,
            "lRelPathFiles": self._lRelPathFiles,
        }
        return dicData

    # enddef


# endclass
