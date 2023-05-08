#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \cls_cfg_manifest_job.py
# Created Date: Tuesday, June 7th 2022, 2:03:20 pm
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
from pathlib import Path

import ison
from typing import Optional

from anybase import config
from anybase import file
from anybase import plugin
from catharsys.config.cls_job import CConfigJob
from catharsys.config.cls_project import CProjectConfig
from catharsys.api.cls_action_result_data import CActionResultData

##########################################################################################
class CConfigManifestJob(CConfigJob):
    @property
    def sAction(self):
        return config.GetDictValue(
            self._dicData, "sAction", str, sWhere="job configuration"
        )

    @property
    def sActionDti(self):
        return config.GetDictValue(
            self._dicData, "sActDti", str, sWhere="job configuration"
        )

    @property
    def lConfigs(self):
        return config.GetDictValue(
            self._dicData, "lConfigs", list, sWhere="job configuration"
        )

    @property
    def iConfigCount(self):
        return len(self.lConfigs)

    @property
    def dicPrjCfg(self):
        return config.GetDictValue(
            self._dicData, "mPrjCfg", dict, sWhere="job configuration"
        )

    @property
    def xPrjCfg(self):
        return self._xPrjCfg

    ######################################################################################
    def __init__(self, _dicData: Optional[dict] = None):

        self._xPrjCfg: CProjectConfig = None

        super().__init__(
            dicData=_dicData,
            sDTI="/catharsys/action-class/python/manifest-based/job-config:1",
        )
        self._InitData()

    # enddef

    ######################################################################################
    def _InitData(self):

        if self._dicData is None:
            return
        # endif

        self._xPrjCfg = CProjectConfig.Deserialize(self.dicPrjCfg)

    # enddef

    ##########################################################################
    def Save(self, sFilename: Optional[str] = None, bStripVars: bool = True) -> None:

        if sFilename is None:
            sFilename = "action-job-config_{0}.json".format(
                self.sAction.replace("/", "-")
            )
        # endif
        pathJsonFile = self.xPrjCfg.pathLaunch / sFilename

        try:
            file.SaveJson(pathJsonFile, self.ToDict(bStripVars=bStripVars), iIndent=4)
            print(
                "Action job config exported to: \n{0}".format(pathJsonFile.as_posix())
            )

        except ison.ParserError as xEx:
            print("Parser Error:")
            print(xEx.ToString())

        except Exception as xEx:
            print(str(xEx))
        # endtry

    # enddef

    ######################################################################################
    def ResultData(self, *, sActionDti: Optional[str] = None) -> CActionResultData:

        if sActionDti is None:
            sActionDti = self.sActionDti
        # endif

        epAction = plugin.SelectEntryPointFromDti(
            sGroup="catharsys.action",
            sTrgDti=sActionDti,
            sTypeDesc="catharsys action module",
        )

        modAction = epAction.load()

        if not hasattr(modAction, "ResultData"):
            raise RuntimeError(
                f"Function 'GetResultData()' not available for action '{sActionDti}'"
            )
        # endif

        return modAction.ResultData(self)

    # enddef

    ##########################################################################
    def _IndexOf(self, _xValue, _xCollection):
        return -1 if _xValue not in _xCollection else _xCollection.index(_xValue)

    # enddef

    ##########################################################################
    def _GetActionTrgPath(self, _lTrgActionDti, _dicCfg):

        sActionDti = None
        sActionName = None
        sPathTrgMain = None
        for sTrgActionDti in _lTrgActionDti:
            sTrgAction = config.GetDictValue(
                _dicCfg["dicActDtiToName"],
                sTrgActionDti,
                str,
                bOptional=True,
                bIsDtiKey=True,
            )
            if sTrgAction is None:
                continue
            # endif

            iActIdx = self._IndexOf(sTrgAction, _dicCfg["lActions"])
            if iActIdx >= 0:
                sPathTrgMain = _dicCfg["dicPathTrgAct"].get(sTrgAction)
                if sPathTrgMain is None:
                    raise Exception(
                        "Action configuration is corrupted: "
                        "No target path available for action '{0}'".format(sTrgAction)
                    )
                # endif
                sActionDti = sTrgActionDti
                sActionName = sTrgAction
                break
            # endif
        # endfor

        return sPathTrgMain, iActIdx, sActionDti, sActionName

    # enddef

    ###########################################################################
    def _GetActionRelPaths(self, _sAction, _dicCfg):

        pathBaseRender = self.xPrjCfg.pathActProd

        ############################################################
        # Get Relative Trial Path
        sPathLastAction = _dicCfg["sPathTrgMain"]
        lCfgIdFolders = _dicCfg["mConfig"]["lCfgIdFolders"]

        pathTrgBase = Path(sPathLastAction)
        for i in range(len(lCfgIdFolders)):
            pathTrgBase = pathTrgBase.parent
        # endfor

        # pathTrgMain = Path(sPathTrgMain)
        sRelPathTrial = pathTrgBase.relative_to(pathBaseRender).as_posix()
        ############################################################

        # Get Relativ configuration path
        pathRelTrgAct = Path(_dicCfg["mConfig"]["dicRelPathTrgAct"][_sAction])
        lRelPathTrgAct = pathRelTrgAct.parts
        lTrialFolder = sRelPathTrial.split("/")
        iIdx = len(lTrialFolder)
        if iIdx > 0:
            iIdx -= 1
        # endif

        sRelPathCfg = "/".join(lRelPathTrgAct[iIdx:])

        return {
            "sRelPathTrial": sRelPathTrial,
            "sRelPathCfg": sRelPathCfg,
            "lCfgIdFolders": lCfgIdFolders,
        }

    # enddef


# endclass
