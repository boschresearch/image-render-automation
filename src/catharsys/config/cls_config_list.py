#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \actions\lib\util.py
# Created Date: Friday, August 20th 2021, 7:45:30 am
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

import os

from anybase import assertion
from catharsys.util import config, path
from catharsys.config.cls_project import CProjectConfig
from anybase.cls_any_error import CAnyError, CAnyError_Message

from catharsys.decs.decorator_log import logFunctionCall


class CConfigList:
    @property
    def dicGroup(self):
        return self._dicGrpCfg

    @property
    def sAction(self):
        return self._dicGrpCfg["sAction"]

    @property
    def sActionDti(self):
        return self._dicGrpCfg["sActDti"]

    @property
    def lConfigs(self):
        if self._dicGrpCfg is None:
            return None
        # endif
        return self._dicGrpCfg.get("lConfigs")

    # enddef

    @property
    def iCount(self):
        if self.lConfigs is None:
            return None
        # endif
        return len(self.lConfigs)

    # enddef

    @property
    def xPrjCfg(self):
        return self._xPrjCfg

    # enddef

    @property
    def dicArgv(self):
        return self._dicArgv

    # enddef

    def GetArg(self, sArgKey):
        return self._dicArgv.get(sArgKey)

    # enddef

    ################################################################################
    def __init__(self, lArgv: list = None):
        self._xPrjCfg: CProjectConfig = None
        self._dicGrpCfg: dict = None
        self._dicArgv = dict()

        if isinstance(lArgv, list):
            # parse all cmd line args into a dict '-key': list of following args until next '-xxx" or end of cmd-line
            setArgKeys = set()
            sKey: str

            for sKey in lArgv:
                if sKey.startswith("-") and sKey != "---":
                    setArgKeys.add(sKey)
                # endif
            # end for

            for sKey in setArgKeys:
                bAppend = False
                lsArgs = list()
                sArg: str
                for sArg in lArgv:
                    if sArg.startswith("-"):
                        bAppend = False
                    # endif
                    if bAppend:
                        lsArgs.append(sArg)
                    # endif

                    if sArg == sKey:
                        bAppend = True
                    # endif
                # end for all args

                self._dicArgv[sKey] = lsArgs
            # end for all keys
        # endif parse cmd line

    # enddef

    ################################################################################
    @logFunctionCall
    def LoadFile(self, _xFilepath):
        """Load the configuration list from given absolute file path.

        Args:
            _sPath (string): Absolute filepath to config json file. This can be either
                             the path where the file '_sFile' lies, or the

        Raises:
            Exception: if file cannot be loaded

        Returns:
            dict: Configuration list dictionary of type '/catharsys/action/config-list:*'.
        """

        pathFile = path.MakeNormPath(_xFilepath)
        bFound = pathFile.exists()
        print(
            "Config file: {0} -> {1}".format(
                pathFile.as_posix(), "found" if bFound else "not found"
            )
        )
        if not bFound:
            raise CAnyError_Message(
                sMsg="Config file not found: {}".format(pathFile.as_posix)
            )
        # endif

        # Load script configuration parameters
        dicLoadCfg = config.Load(
            pathFile,
            sDTI="/catharsys/action/config-list:1.1",
            bReplacePureVars=False,
            bAddPathVars=False,
            bDoThrow=False,
        )
        if dicLoadCfg["bOK"] is False:
            raise CAnyError_Message(
                sMsg="Error loading std/render action configuration file: {0}".format(
                    dicLoadCfg["sMsg"]
                )
            )
        # endif
        self._dicGrpCfg = dicLoadCfg["dicCfg"]

        # Get Project Config instance
        dicPrjCfg = self._dicGrpCfg.get("mPrjCfg")
        if dicPrjCfg is None:
            raise CAnyError_Message(
                sMsg="Element 'mPrjCfg' missing in configuration list"
            )
        # endif

        # Create appropriate project configuration class and initialize it
        self._xPrjCfg = CProjectConfig.Deserialize(dicPrjCfg)
        # print(self._xPrjCfg)

    # enddef

    ################################################################################
    # Run Config Loop
    @logFunctionCall
    def ForEachConfig(self, _funcProcess):

        iCfgCnt = self.iCount
        for iCfgIdx, dicCfg in enumerate(self.lConfigs):

            try:
                _funcProcess(self.xPrjCfg, dicCfg, iCfgIdx=iCfgIdx, iCfgCnt=iCfgCnt)

            except Exception as xEx:
                sMsg = (
                    "Exception during rendering of configuration '{0}' "
                    "in config group '{1}', frame group '{2}':".format(
                        iCfgIdx,
                        self.dicGroup["iConfigGroupIdx"],
                        self.dicGroup["iFrameGroupIdx"],
                    )
                )
                raise CAnyError_Message(sMsg=sMsg, xChildEx=xEx)
            # endtry
        # endfor

    # enddef


# endclass
