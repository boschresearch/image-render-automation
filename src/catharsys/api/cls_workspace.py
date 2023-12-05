#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \cls_workspace.py
# Created Date: Friday, June 3rd 2022, 3:52:52 pm
# Author: Christian Perwass (CR/AEC5)
# <LICENSE id="Apache-2.0">
#
#   Image-Render Automation Functions module
#   Copyright 2022 Robert Bosch GmbH and its subsidiaries
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

from typing import Optional, Union
from pathlib import Path

from anybase import path as anypath
from anybase import config as anycfg

try:
    import catharsys.setup.version as cathversion
except Exception:
    import catharsys.util.version as cathversion
# endtry

from catharsys.config.cls_project import CProjectConfig

from .cls_project import CProject


#########################################################################
class CWorkspace:
    @property
    def pathStart(self):
        return self._pathStart

    @property
    def pathWorkspace(self):
        return self._pathWS

    @property
    def pathWorkspacePackageFile(self):
        return self._pathWsPkgFile

    @property
    def pathConfig(self):
        return self._pathConfig

    @property
    def dicPackage(self):
        return self._dicPkg

    @property
    def sCatharsysVersion(self):
        return self._sCathVersion

    @property
    def sRequiredCatharsysVersion(self):
        return self._sPkgCathVersion

    @property
    def sName(self):
        return self._sPkgName

    @property
    def sVersion(self):
        return self._sPkgVersion

    @property
    def dicProjects(self):
        return self._dicProjects

    @property
    def lProjectNames(self):
        return self._dicProjects.keys()

    #############################################################################
    def __init__(
        self,
        *,
        xWorkspace: Union[Path, str, list, tuple, None] = None,
        sFileBasenameLaunch: Optional[str] = None,
    ):
        self._pathStart: Path = None
        self._pathWS: Path = None
        self._pathWsPkgFile: Path = None
        self._pathConfig: Path = None

        self._dicPkg: dict = None
        self._sCathVersion: str = None
        self._sPkgCathVersion: str = None
        self._sPkgName: str = None
        self._sPkgVersion: str = None
        self._sFileBasenameLaunch: str = None

        self._dicProjects: dict[str, CProject] = None

        if xWorkspace is None:
            self._pathStart = Path.cwd()
        else:
            self._pathStart = anypath.MakeNormPath(xWorkspace)
        # endif

        if isinstance(sFileBasenameLaunch, str):
            self._sFileBasenameLaunch = sFileBasenameLaunch
        else:
            self._sFileBasenameLaunch = "launch"
        # endif

        self._pathWsPkgFile = self._FindWorkspaceFromPath(self._pathStart)
        if self._pathWsPkgFile is None:
            raise RuntimeError(
                "Cannot find valid Catharsys workspace starting from path: {}".format(self._pathStart.as_posix())
            )
        # endif

        self._dicPkg = anycfg.Load(self._pathWsPkgFile, sDTI="/package/catharsys/workspace:3")
        lCathVer = cathversion.AsIntList()
        self._sCathVersion = cathversion.AsString()

        sPkgCathVer = self._dicPkg.get("sCatharsysVersion")
        if sPkgCathVer is None:
            print(
                "WARNING: Workspace package file does not specify Catharsys version: {}".format(
                    self._pathWsPkgFile.as_posix()
                )
            )
        else:
            try:
                self._sPkgCathVersion = ""
                lPkgCathVer = [int(x) for x in sPkgCathVer.split(".")]
                if len(lPkgCathVer) == 0:
                    raise RuntimeError("Not enough digits in version")
                # endif
                self._sPkgCathVersion = sPkgCathVer

            except Exception as xEx:
                print(
                    "WARNING: Error parsing 'sCatharsysVersion' element in package file: {}\n>> {}\n".format(
                        self._pathWsPkgFile.as_posix()
                    ),
                    str(xEx),
                )
            # endtry

            bValidVer = True
            if lCathVer[0] != lPkgCathVer[0]:
                bValidVer = False
            elif len(lPkgCathVer) > 1 and lCathVer[1] != lPkgCathVer[1]:
                bValidVer = False
            # endif
            if bValidVer is False:
                print(
                    "WARNING: Workspace specifies Catharsys version '{}', but version '{}' is active".format(
                        sPkgCathVer, cathversion.AsString()
                    )
                )
            # endif
        # endif
        self._pathWS = self._pathWsPkgFile.parent

        self._sPkgName = self._dicPkg.get("sName", self._pathWS.name)
        self._sPkgVersion = self._dicPkg.get("sVersion", "n/a")

        self._InitConfigs()

    # enddef

    #############################################################################
    def PrintInfo(self) -> None:
        print("Workspace: {}, version {}".format(self._sPkgName, self._sPkgVersion))
        print("Path: {}".format(self._pathWS.as_posix()))
        print("Package: {}".format(self._pathWsPkgFile.relative_to(self._pathWS).as_posix()))
        print("Catharsys Version: Environment v{}, Required v{}".format(self._sCathVersion, self._sPkgCathVersion))
        print("Configurations:")
        for sPrjCfgId in self._dicProjects:
            print("    - '{}': {}".format(sPrjCfgId, self._dicProjects[sPrjCfgId].sInfo))
        # endfor

    # enddef

    #############################################################################
    def Project(self, _sPrjId: str) -> CProject:
        sPrjId = _sPrjId.replace("\\", "/")
        if sPrjId not in self._dicProjects:
            pathCfg = Path(sPrjId).absolute()
            sSelCfg: str = None
            if pathCfg.is_relative_to(self.pathConfig):
                sPathCfg = pathCfg.as_posix()
                sSelCfg = next((x for x in self.lProjectNames if sPathCfg.endswith(x)), None)
            # endif

            if sSelCfg is None:
                raise RuntimeError(f"Project '{sPrjId}' not available in workspace")
            # endif

            xProject = self._dicProjects[sSelCfg]
        else:
            xProject = self._dicProjects[sPrjId]
        # endif

        return xProject

    # enddef

    #############################################################################
    def _FindWorkspaceFromPath(self, pathStart: Path) -> Path:
        pathPkg = None
        pathTest = pathStart
        while True:
            pathPkg = pathTest / "package"
            pathPkg = anypath.ProvideReadFilepathExt(pathPkg, [".json", ".json5", ".ison"])
            if pathPkg is not None:
                dicRes = anycfg.Load(pathPkg, sDTI="/package/catharsys/workspace:3", bDoThrow=False)
                if dicRes["bOK"] is True:
                    break
                # endif
            # endif
            pathParent = pathTest.parent
            if pathParent == pathTest:
                break
            # endif
            pathTest = pathParent
        # endwhile

        return pathPkg

    # enddef

    #############################################################################
    def _InitConfigs(self) -> None:
        lProjects: list[CProject] = []

        pathConfig = self._pathWS / "config"
        if not pathConfig.exists():
            raise RuntimeError("Configuration folder 'config' not found in workspace: {}".format(pathConfig.as_posix()))
        # endif
        self._pathConfig = pathConfig

        ##############################################################################
        # Search for launch files
        lLaunchFiles = [
            x
            for x in pathConfig.rglob(f"{self._sFileBasenameLaunch}.*")
            if (x.is_file() and ".vscode" not in x.as_posix() and x.suffix in [".json", ".json5", ".ison"])
        ]

        lInvalidFiles = []
        # print(lLaunchFiles)
        for pathFile in lLaunchFiles:
            if any((x != pathFile and pathFile.parent.is_relative_to(x.parent) for x in lLaunchFiles)):
                lInvalidFiles.append(pathFile)
            # endif
        # endfor
        # print(lInvalidFiles)
        for pathFile in lInvalidFiles:
            lLaunchFiles.remove(pathFile)
        # endfor

        # Get list of valid project configurations in workspace
        for pathLaunchFile in lLaunchFiles:
            xPrjCfg = CProjectConfig()
            try:
                xPrjCfg.FromLaunchPath(pathLaunchFile)
            except Exception as xEx:
                print(
                    "WARNING: Invalid launch file for configuraton: {}\n{}\n".format(
                        pathLaunchFile.as_posix(), str(xEx)
                    )
                )
            # endtry
            lProjects.append(CProject(xPrjCfg, xWorkspace=self))
        # endfor

        self._dicProjects = {}
        for xProject in lProjects:
            self._dicProjects[xProject.sId] = xProject
        # endfor

    # enddef


# endclass
