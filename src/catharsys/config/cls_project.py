#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \vars.py
# Created Date: Friday, April 22nd 2022, 2:43:25 pm
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
# Basic project structure:
# [main_project_folder]
# |- config
#    |- [config name 1]
#       | - launch[.json, .json5, .ison]
#    |- [config name 2]
#       | - launch[.json, .json5, .ison]
# |- package.json
#
# launch.json:
#   - fundamental parameters for launching actions
#   - parameter set per action
#
# package.json:
#   - version of project
#   - Catharsys version needed
###

import os
from pathlib import Path
from typing import Optional

from anybase import config, plugin
from anybase import filepathvars as anyfpv
from anybase.cls_any_error import CAnyError_Message, CAnyError_TaskMessage
from catharsys.util import path


# Project paths for a given configuration
class CProjectConfig:

    #######################################################################
    # getter functions
    @property
    def sLaunchPath(self):
        return self._pathLaunch.as_posix() if self._pathLaunch is not None else None

    @property
    def sLaunchFilePath(self):
        return self._pathLaunchFile.as_posix() if self._pathLaunchFile is not None else None

    @property
    def sMainPath(self):
        return self._pathMain.as_posix() if self._pathMain is not None else None

    @property
    def sConfigPath(self):
        return self._pathConfig.as_posix() if self._pathConfig is not None else None

    @property
    def sOutputPath(self):
        return self._pathOutput.as_posix() if self._pathOutput is not None else None

    @property
    def sProductionPath(self):
        return self._pathProduction.as_posix() if self._pathProduction is not None else None

    @property
    def sActProdPath(self):
        return self._pathActProd.as_posix() if self._pathActProd is not None else None

    @property
    def pathLaunch(self):
        return self._pathLaunch

    @property
    def pathLaunchFile(self):
        return self._pathLaunchFile

    @property
    def pathMain(self):
        return self._pathMain

    @property
    def pathConfig(self):
        return self._pathConfig

    @property
    def pathOutput(self):
        return self._pathOutput

    @property
    def pathActProd(self):
        return self._pathActProd

    @property
    def sConfigFolderName(self):
        return self._sFolderConfig

    @property
    def sOutputFolderName(self):
        return self._sFolderOutput

    @property
    def sProductionFolderName(self):
        return self._sFolderProduction

    @property
    def sActProdFolderName(self):
        return self._sFolderActProd

    @property
    def sLaunchFileBasename(self):
        return self._sFileBasenameLaunch

    @property
    def sLaunchFolderName(self):
        return self._pathLaunch.relative_to(self._pathConfig).as_posix()

    #############################################################################
    # Constructor
    def __init__(self, *, sFileBasenameLaunch: Optional[str] = None):

        self._pathLaunch: Path = None
        self._pathLaunchFile: Path = None
        self._pathMain: Path = None
        self._pathConfig: Path = None
        self._pathOutput: Path = None
        self._pathProduction: Path = None
        self._pathActProd: Path = None

        self._sFolderConfig: str = "config"
        self._sFolderOutput: str = "_output"
        self._sFolderProduction: str = "_product"
        self._sFolderActProd: str = "."

        if isinstance(sFileBasenameLaunch, str):
            self._sFileBasenameLaunch = sFileBasenameLaunch
        else:
            self._sFileBasenameLaunch: str = "launch"
        # endif

    # enddef

    #############################################################################
    def IsLaunchFileValid(self) -> bool:

        if not self.pathLaunchFile.exists():
            return False, "Launch file does not exist at path: {}".format(self.sLaunchFilePath)
        # endif

        try:
            config.Load(self.pathLaunchFile, sDTI="/catharsys/launch:3")
        except Exception as xEx:
            return False, "Invalid launch file at path: {}".format(self.sLaunchFilePath)
        # endtry

        return True, ""

    # enddef

    #############################################################################
    def AssertLaunchFileValid(self) -> bool:

        if not self.pathLaunchFile.exists():
            raise CAnyError_Message(sMsg=f"Launch file does not exist at path: {self.sLaunchFilePath}")
        # endif

        try:
            config.Load(self.pathLaunchFile, sDTI="/catharsys/launch:3")
        except Exception as xEx:
            raise CAnyError_Message(
                sMsg=f"Invalid launch file at path: {self.sLaunchFilePath}",
                xChildEx=xEx,
            )
        # endtry

    # enddef

    #############################################################################
    def FromLaunchPath(self, _xPathLaunch):
        pathLaunch = None

        if _xPathLaunch is not None:
            if isinstance(_xPathLaunch, str):
                pathLaunch = Path(_xPathLaunch)
            elif isinstance(_xPathLaunch, Path):
                pathLaunch = _xPathLaunch
            else:
                raise CAnyError_Message(sMsg="Launch path argument of invalid type")
            # endif

            if not pathLaunch.exists():
                raise CAnyError_Message(sMsg="Launch file path '{}' does not exist".format(pathLaunch.as_posix()))
            # endif

        else:
            pathLaunch = Path.cwd()
        # endif

        if pathLaunch.is_file():
            self._pathLaunchFile = pathLaunch
            self._pathLaunch = pathLaunch.parent

        else:
            self._pathLaunch = pathLaunch
            self._pathLaunchFile = config.ProvideReadFilepathExt((self._pathLaunch, self.sLaunchFileBasename))
            # sLaunchFilename = self._FindLaunchFilename()
            # if sLaunchFilename is None:
            #     self._pathLaunchFile = self._pathLaunch / (self.sLaunchFileBasename + ".json5")
            # else:
            #     self._pathLaunchFile = self._pathLaunch / sLaunchFilename
            # # endif
        # endif

        if self._sFolderConfig not in self._pathLaunch.parts:
            raise CAnyError_Message(
                sMsg="Folder 'config' not in launch file path: {}".format(self._pathLaunch.as_posix())
            )
        # endif

        # Find main path as parent path of config folder path
        self._pathMain = self._pathLaunch
        while self._pathMain.name != self._sFolderConfig:
            self._pathMain = self._pathMain.parent
        # endwhile
        self._pathMain = self._pathMain.parent

        self._pathConfig = self._pathMain / self._sFolderConfig
        self._pathOutput = self._pathMain / self._sFolderOutput
        self._pathProduction = self._pathMain / self._sFolderProduction
        self._pathActProd = self._pathProduction / self._sFolderActProd

        self.AssertLaunchFileValid()

    # enddef

    #############################################################################
    def FromConfigName(self, *, xPathMain, sConfigName):

        pathMain = None

        if not isinstance(sConfigName, str):
            raise CAnyError_Message(sMsg="Argument 'sConfigName' must be a string")
        # endif

        if xPathMain is not None:
            if isinstance(xPathMain, str):
                pathMain = Path(xPathMain)
            elif isinstance(xPathMain, Path):
                pathMain = xPathMain
            else:
                raise CAnyError_Message(sMsg="Main path argument of invalid type")
            # endif

            if not pathMain.exists():
                raise CAnyError_Message(sMsg="Main path '{}' does not exist".format(pathMain.as_posix()))
            # endif

        else:
            pathMain = Path.cwd()
        # endif

        pathConfigName = Path(sConfigName)
        if len(pathConfigName.parts) > 1 and pathConfigName.parts[0] == self._sFolderConfig:
            pathConfigName = Path().joinpath(*pathConfigName.parts[1:])
        # endif

        self._pathMain = pathMain
        self._pathConfig = self._pathMain / self._sFolderConfig
        self._pathLaunch = self._pathConfig / pathConfigName
        self._pathOutput = self._pathMain / self._sFolderOutput
        self._pathProduction = self._pathMain / self._sFolderProduction
        self._pathActProd = self._pathProduction / self._sFolderActProd

        self._pathLaunchFile = config.ProvideReadFilepathExt((self._pathLaunch, self.sLaunchFileBasename))

        # sLaunchFilename = self._FindLaunchFilename()
        # if sLaunchFilename is None:
        #     self._pathLaunchFile = self._pathLaunch / (self.sLaunchFileBasename + ".json5")
        # else:
        #     self._pathLaunchFile = self._pathLaunch / sLaunchFilename
        # # endif

        self.AssertLaunchFileValid()

    # enddef

    #############################################################################
    def FromProject(self, _xPrjCfg):

        if not isinstance(_xPrjCfg, CProjectConfig):
            raise CAnyError_Message(sMsg="Invalid project class type")
        # endif

        self._sFolderConfig = _xPrjCfg.sConfigFolderName
        self._sFolderOutput = _xPrjCfg._sFolderOutput
        self._sFolderProduction = _xPrjCfg._sFolderProduction
        self._sFolderActProd = _xPrjCfg._sFolderActProd

        self._sFileBasenameLaunch = _xPrjCfg.sLaunchFileBasename

        self._pathMain = Path(_xPrjCfg.sMainPath)
        self._pathLaunch = Path(_xPrjCfg.sLaunchPath)
        self._pathLaunchFile = Path(_xPrjCfg.sLaunchFilePath)
        self._pathConfig = Path(_xPrjCfg.sConfigPath)
        self._pathOutput = Path(_xPrjCfg.sOutputPath)
        self._pathProduction = Path(_xPrjCfg.sProductionPath)
        self._pathActProd = Path(_xPrjCfg.sActProdPath)

    # enddef __init__

    #######################################################################
    # This function can be overwritten by derived classes to
    # modify the project parameters
    def ApplyConfig(self, _dicCfg):
        pass

    # enddef

    #######################################################################
    def GetAbsPath(self, _xRelPath):

        """
        Create an absolute path from the given relative path
        using the script path as base path.
        """
        pathAbs = self._pathLaunch

        if isinstance(_xRelPath, list):
            for sFolder in _xRelPath:
                pathAbs /= sFolder
            # endfor

        elif isinstance(_xRelPath, str):
            pathRel = Path(_xRelPath)
            pathAbs /= pathRel

        elif isinstance(_xRelPath, Path):
            pathAbs /= _xRelPath

        else:
            raise Exception("Invalid relative path variable type")
        # endif

        return pathAbs

    # enddef

    # #####################################################################
    # # Find launch args file
    # def _FindLaunchFilename(self):

    #     sFilename = None

    #     for sExt in [".json", ".json5", ".ison"]:
    #         sFilename = "{}{}".format(self._sFileBasenameLaunch, sExt)
    #         pathLAF = self._pathLaunch / sFilename
    #         if pathLAF.exists():
    #             break
    #         # endif
    #         sFilename = None
    #     # endfor

    #     return sFilename
    # # enddef

    #######################################################################
    def Serialize(self):
        return {
            "sDTI": "/catharsys/project-class/std/base:1.0",
            "sLaunchPath": self.sLaunchPath,
            "sLaunchFilePath": self.sLaunchFilePath,
            "sMainPath": self.sMainPath,
            "sConfigPath": self.sConfigPath,
            "sOutputPath": self.sOutputPath,
            "sProductionPath": self.sProductionPath,
            "sActProdPath": self.sActProdPath,
            "sConfigFolderName": self.sConfigFolderName,
            "sOutputFolderName": self.sOutputFolderName,
            "sProductionFolderName": self.sProductionFolderName,
            "sActProdFolderName": self.sActProdFolderName,
            "sLaunchFileBasename": self.sLaunchFileBasename,
        }

    # enddef

    #######################################################################
    def FromData(self, _dicSerialized):
        try:
            self._sFolderConfig = _dicSerialized["sConfigFolderName"]
            self._sFolderOutput = _dicSerialized["sOutputFolderName"]
            self._sFolderProduction = _dicSerialized["sProductionFolderName"]
            self._sFolderActProd = _dicSerialized["sActProdFolderName"]

            self._sLaunchFileBasename = _dicSerialized["sLaunchFileBasename"]

            self._pathMain = Path(_dicSerialized["sMainPath"])
            self._pathLaunch = Path(_dicSerialized["sLaunchPath"])
            self._pathLaunchFile = Path(_dicSerialized["sLaunchFilePath"])
            self._pathConfig = Path(_dicSerialized["sConfigPath"])
            self._pathOutput = Path(_dicSerialized["sOutputPath"])
            self._pathProduction = Path(_dicSerialized["sProductionPath"])
            self._pathActProd = Path(_dicSerialized["sActProdPath"])

        except KeyError as xEx:
            raise CAnyError_Message(
                sMsg="Missing element '{}' in serialized project configuration".format(str(xEx)),
                xChildEx=xEx,
            )
        # endif

    # enddef

    #######################################################################
    @staticmethod
    def Create(*, sDTI):
        try:
            epPrjCls = plugin.SelectEntryPointFromDti(
                sGroup="catharsys.projectclass",
                sTrgDti=sDTI,
                sTypeDesc="action project class",
            )

            # Load project class declaration
            clsProjectClass = epPrjCls.load()
            # Create project class
            xPrjCfg = clsProjectClass()

        except Exception as xEx:
            raise CAnyError_TaskMessage(
                sTask="Create project configuration from type",
                sMsg="Error",
                xChildEx=xEx,
            )
        # endtry

        return xPrjCfg

    # enddef

    #######################################################################
    @staticmethod
    def Deserialize(_dicData):
        try:
            config.AssertConfigType(_dicData, "/catharsys/project-class/*:*")

            xPrjCfg = CProjectConfig.Create(sDTI=_dicData["sDTI"])

            # Initialize action project config class with given project config
            xPrjCfg.FromData(_dicData)

        except Exception as xEx:
            raise CAnyError_TaskMessage(sTask="Deserialize project configuration", sMsg="Error", xChildEx=xEx)
        # endtry

        return xPrjCfg

    # enddef

    ################################################################
    def GetFilepathVarDict(self, _xFilepath):

        pathFile = path.MakeNormPath(_xFilepath)
        if pathFile.is_file():
            pathRelCfg = Path(os.path.relpath(pathFile.as_posix(), self.sConfigPath))
        else:
            pathRelCfg = pathFile.relative_to(self.sConfigPath)
        # endif

        sCfgFolder = pathRelCfg.parts[0]
        sRelCfgFolderPath = "/".join(pathRelCfg.parts[1:])

        dicVar = anyfpv.GetVarDict(_xFilepath)
        dicVar.update(
            {
                "path-cath-user": path.GetCathUserPath(_bCheckExists=False).as_posix(),
                "path-workspace": self.sMainPath,  # old: "workspacepath"
                "path-all-configs": self.sConfigPath,  # old: "configpath"
                "path-config": (self.pathConfig / sCfgFolder).as_posix(),  # old: "configpathfolder"
                "path-output": self.sOutputPath,
                "path-production": self.sProductionPath,
                "path-actprod": self.sActProdPath,
                "folder-config": sCfgFolder,  # old: "configfolder"
                "folder-actprod": self._sFolderActProd,
                "rel-path-config": pathRelCfg.as_posix(),  # old: "relconfigpath"
                "rel-path-config-child": sRelCfgFolderPath,  # old: "relconfigchildpath"
            }
        )

        return dicVar

    # enddef


# endclass
