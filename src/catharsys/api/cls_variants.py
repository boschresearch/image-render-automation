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

from typing import Optional
from pathlib import Path
from anybase import config
from anybase import path as anypath
from anybase import link as anylink

from .cls_project import CProject
from .cls_workspace import CWorkspace
from ..config.cls_variant_group import CVariantGroup
from ..config.cls_variant_launch import CVariantLaunch
from ..config.cls_variant_trial import CVariantTrial
from ..config.cls_variant_instance import CVariantInstance
from ..util import fsops


# This class handles workspace variants.
# In particular, variants of the launch and trial files are handled.
# The organizational structure of variants is:
#   - group 1
#       - launch variant 1
#           - launch file
#           - trial group 1
#               - source trial file
#               - list of variant trial files
#           - trial group 2
#               - source trial file
#               - list of variant trial files
#       - launch variant 2
#           [...]
#   [...]
#
# All variants are stored in a workspace.
# For each variant an appropriate instance of CProject can be returned,
#   which contains the active name of the launch file for the current variant.
#   The launch file variant contains the same trial file names of the currently
#   active trial group variant.
#
class CVariants:
    c_sFolderVariants = ".variants"
    c_sFolderInstances = "_instances"
    c_sFileVariants = "variants.json"
    c_lConfigSuffix = [".json", ".json5", ".ison"]
    # c_reFolderGrp = re.compile(r"g(?P<group>\d+)")

    def __init__(self, _prjX: CProject):
        self._xProject: CProject = _prjX
        self._dicGroupVariants: dict[str, CVariantGroup] = None

        dicVarCfg: dict = None
        if not self.pathVariantsConfigFile.exists():
            dicVarCfg = {"sDTI": "/catharsys/variants:1.0", "mGroups": {}}
            self.pathVariants.mkdir(parents=True, exist_ok=True)
            config.Save(self.pathVariantsConfigFile, dicVarCfg)
            pathGitIgnore = self.pathVariants / ".gitignore"
            pathGitIgnore.write_text(f"{CVariants.c_sFolderInstances}\n")
        else:
            dicVarCfg = config.Load(self.pathVariantsConfigFile, sDTI="/catharsys/variants:1")
            if "mGroups" not in dicVarCfg:
                raise RuntimeError("Element 'mGroups' missing in variants config")
            # endif
        # endif

        dicGroups: dict = dicVarCfg["mGroups"]
        self._dicGroupVariants = {}
        for sVarGrp in dicGroups:
            xVarGrp = CVariantGroup(self.pathVariants)
            xVarGrp.FromConfig(_prjX=self._xProject, _dicCfg=dicGroups[sVarGrp])
            self._dicGroupVariants[sVarGrp] = xVarGrp
        # endfor

    # enddef

    @property
    def xWorkspace(self) -> CWorkspace:
        return self._xProject.xWorkspace

    # enddef

    @property
    def xProject(self) -> CProject:
        return self._xProject

    # enddef

    @property
    def pathWorkspace(self) -> Path:
        return self.xWorkspace.pathWorkspace

    # enddef

    @property
    def pathLaunch(self) -> Path:
        return self._xProject.xConfig.pathLaunch

    @property
    def pathVariants(self) -> Path:
        return self.pathLaunch / CVariants.c_sFolderVariants

    # enddef

    @property
    def pathVariantsConfigFile(self) -> Path:
        return self.pathVariants / CVariants.c_sFileVariants

    # enddef

    @property
    def pathInstances(self) -> Path:
        return self.pathVariants / CVariants.c_sFolderInstances

    # enddef

    @property
    def lGroupNames(self) -> list[str]:
        return list(self._dicGroupVariants.keys())

    # enddef

    # ############################################################################################
    def HasGroup(self, _sGroup: str) -> bool:
        return _sGroup in self._dicGroupVariants

    # enddef

    # ############################################################################################
    def GetGroup(self, _sGroup: str, *, _bDoRaise: bool = True) -> CVariantGroup:
        xGrp: CVariantGroup = self._dicGroupVariants.get(_sGroup)
        if not isinstance(xGrp, CVariantGroup):
            if _bDoRaise is True:
                raise RuntimeError(f"Variant group '{_sGroup}' not available")
            # endif
            return None
        # endif
        return xGrp

    # enddef

    # ############################################################################################
    def CreateGroup(self, _sGroup: str) -> CVariantGroup:
        if self.HasGroup(_sGroup):
            raise RuntimeError(f"Variant group '{_sGroup}' already exists")
        # endif

        xVarGrp: CVariantGroup = CVariantGroup(self.pathVariants)
        xVarGrp.Create(_prjX=self._xProject, _sGroup=_sGroup, _sInfo="n/a")

        self._dicGroupVariants[_sGroup] = xVarGrp

    # enddef

    # ############################################################################################
    # Updates all groups from the source launch and trial files
    def UpdateFromSource(self, *, _bOverwrite: Optional[bool] = False):
        self._xProject.Update()
        for sGroup in self._dicGroupVariants:
            self._dicGroupVariants[sGroup].UpdateFromSource(_bOverwrite=_bOverwrite)
        # endfor

    # enddef

    # ############################################################################################
    def Serialize(self, *, _bWriteToDisk: bool = True) -> dict:
        dicGroups = {}
        for sGroup in self._dicGroupVariants:
            dicGroups[sGroup] = self._dicGroupVariants[sGroup].Serialize()
        # endfor

        dicData = {
            "sDTI": "/catharsys/variants:1.0",
            "mGroups": dicGroups,
        }

        if _bWriteToDisk is True:
            config.Save(self.pathVariantsConfigFile, dicData)
        # endif

        return dicData

    # enddef

    ############################################################################################
    def GetInstances(self) -> list[CVariantInstance]:
        pathInstances = self.pathInstances
        pathInstances.mkdir(parents=True, exist_ok=True)
        lInst: list[CVariantInstance] = []

        for pathInst in pathInstances.iterdir():
            if not pathInst.is_dir():
                continue
            # endif
            if not CVariantInstance.IsInstancePath(pathInst):
                continue
            # endif

            lInst.append(CVariantInstance(_pathInstances=self.pathInstances).FromPath(pathInst))
        # endfor

        return lInst

    # enddef

    # ############################################################################################
    def CreateInstance(self, *, _sGroup: str, _iLaunchId: int, _iTrialId: int) -> CVariantInstance:
        xGroup: CVariantGroup = self.GetGroup(_sGroup)
        xLaunch: CVariantLaunch = xGroup.GetLaunchVariant(_iLaunchId)
        xTrial: CVariantTrial = xLaunch.GetTrialVariant(_iTrialId)

        xInst = CVariantInstance(_pathInstances=self.pathInstances)
        xInst.Create(_sGroup=_sGroup, _iLaunchId=_iLaunchId, _iTrialId=_iTrialId)

        lReExcludeDirs: list[str] = [r"^(\.|_).+"]
        lReExcludeFiles: list[str] = [r".+\.ipynb$"]

        # Copy source configurations
        fsops.CopyFilesInDir(
            self.pathLaunch, xInst.pathInstance, lReExcludeDirs=lReExcludeDirs, lReExcludeFiles=lReExcludeFiles
        )

        # Copy folders that start with "_" as symbolic links
        pathSrc: Path = None
        for pathSrc in self.pathLaunch.iterdir():
            if pathSrc.is_dir() and pathSrc.name.startswith("_"):
                pathTrg = xInst.pathInstance / pathSrc.name
                anylink.symlink(pathSrc.as_posix(), pathTrg.as_posix())
            # endif
        # endfor

        # Check whether launch file exists with one of the possible extensions
        pathTrgFile = anypath.ProvideReadFilepathExt(
            xInst.pathInstance / xLaunch.pathLaunchFile.stem, CVariants.c_lConfigSuffix, bDoRaise=False
        )
        if pathTrgFile is not None:
            pathTrgFile.unlink()
        # endif

        # Copy Variant launch file
        fsops.CopyFileToDir(xLaunch.pathLaunchFile, xInst.pathInstance)

        # Copy variant trial files
        lSrcTrgPaths = xTrial.CreateVariantSourceTargetPaths(xInst.pathInstance)
        sTrialBaseId = f"{self._xProject.xConfig.sLaunchFolderName}/{xInst.sName}"
        pathSrc: Path = None
        pathTrg: Path = None
        bIsConfigFile: bool = False
        for pathSrc, pathTrg in lSrcTrgPaths:
            # Remove target files if they exist under the same name but with possibly different configuration suffix
            if pathTrg.suffix in CVariants.c_lConfigSuffix:
                bIsConfigFile = True
                pathTest = pathTrg.parent / pathTrg.stem
                pathTest = anypath.ProvideReadFilepathExt(pathTest, CVariants.c_lConfigSuffix, bDoRaise=False)
                if pathTest is not None:
                    pathTest.unlink()
                # endif
            else:
                bIsConfigFile = False
            # endif
            fsops.CopyFile(pathSrc, pathTrg)

            # Adapt the trial ids
            if bIsConfigFile is True:
                dicCfg = config.Load(pathTrg, bReplacePureVars=False)
                if config.IsConfigType(dicCfg, "/catharsys/trial:*"):
                    bChanged: bool = False
                    sId: str = dicCfg.get("sId", "")
                    if "${rel-path-config}" in sId:
                        sId = sId.replace("${rel-path-config}", sTrialBaseId)
                        bChanged = True
                    # endif

                    if "${filebasename}" in sId or "$filebasename" in sId:
                        sFilebasename = f"{sTrialBaseId}/{pathTrg.stem}"
                        sId = sId.replace("${filebasename}", sFilebasename)
                        sId = sId.replace("$filebasename", sFilebasename)
                        bChanged = True
                    # endif

                    if bChanged is False:
                        sId = f"{sTrialBaseId}/{sId}"
                    # endif

                    dicCfg["sId"] = sId
                    config.Save(pathTrg, dicCfg)
                # endif
            # endif
        # endfor

        return xInst

    # enddef

    # ############################################################################################
    def RemoveAllInstances(self):
        fsops.RemoveTree(self.pathInstances, bIgnoreErrors=True)

    # enddef

    # ############################################################################################
    def RemoveInstance(self, _xInstance: CVariantInstance, *, _bIgnoreErrors: bool = False):
        fsops.RemoveTree(_xInstance.pathInstance, bIgnoreErrors=_bIgnoreErrors)

    # enddef


# endclass
