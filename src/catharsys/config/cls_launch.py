#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /launch.py
# Created Date: Thursday, October 22nd 2020, 4:26:28 pm
# Author: Christian Perwass
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

# Handle launch files and execute
import copy
from typing import Tuple, Optional

from anybase.cls_any_error import CAnyError_Message
from catharsys.util import config
from catharsys.util.cls_configcml import CConfigCML
import ison


class CConfigLaunch:
    @property
    def dicLaunch(self):
        return self._dicLaunch

    # enddef

    @property
    def sInfo(self):
        return self._dicLaunch.get("sInfo", "")

    @property
    def dicRuntimeVars(self):
        return self._dicRtv

    # enddef

    @property
    def setRuntimeVarsEval(self):
        return self._setRtvEval

    # enddef

    @property
    def dicGlobalArgs(self) -> dict:
        return self.dicLaunch.get("mGlobalArgs", {})

    # enddef

    ######################################################################################
    def __init__(
        self, _dicData: Optional[dict] = None, _dicRtv: Optional[dict] = None, _setRtvEval: Optional[set] = None
    ):
        self._dicLaunch: dict = None
        self._dicRtv: dict = None
        self._setRtvEval: set = None

        if isinstance(_dicData, dict):
            config.AssertConfigType(_dicData, "/catharsys/launch:3")
            self._dicLaunch = copy.deepcopy(_dicData)
        # endif

        if isinstance(_dicRtv, dict):
            self._dicRtv = copy.deepcopy(_dicRtv)
        # endif

        if isinstance(_setRtvEval, set):
            self._setRtvEval = copy.deepcopy(_setRtvEval)
        # endif

    # enddef

    ######################################################################################
    def __copy__(self) -> "CConfigLaunch":
        return CConfigLaunch(self._dicLaunch, self._dicRtv, self._setRtvEval)

    # enddef

    ######################################################################################
    # Load Launch from file
    def LoadFile(self, _xPrjCfg):
        pathFile = _xPrjCfg.pathLaunchFile
        if pathFile is None:
            raise CAnyError_Message(sMsg="No launch file defined in project configuration")
        # endif

        pathFile = config.ProvideReadFilepathExt(pathFile)
        dicPathVars = _xPrjCfg.GetFilepathVarDict(pathFile)
        self._dicLaunch = config.Load(pathFile, sDTI="launch:*", dicCustomVars=dicPathVars, bAddPathVars=True)
        xCML = CConfigCML(
            xPrjCfg=_xPrjCfg,
            dicConstVars=_xPrjCfg.GetFilepathVarDict(pathFile),
            sImportPath=pathFile.parent,
        )

        self._dicLaunch = xCML.Process(self._dicLaunch)
        self._dicRtv = xCML.GetRuntimeVars(_bCopy=False)
        self._setRtvEval = xCML.GetRuntimeVarEvalSet(_bCopy=False)

        dicDti = config.SplitDti(self.dicLaunch.get("sDTI"))
        lVer = dicDti.get("lVersion")
        if lVer[0] < 3 or lVer[0] > 3:
            raise Exception("Launch configuration version is not supported.")
        # endif

    # enddef

    ######################################################################################
    # Set launch argument from dictionary
    def SetLaunchArgs(self, _xPrjCfg, _dicArgs):
        dicCfg = config.AssertConfigType(_dicArgs, "launch:*")
        lVer = dicCfg.get("lCfgVer")
        if lVer[0] < 1 or lVer[0] > 2:
            raise Exception("Launch configuration version is not supported.")
        # endif

        self._dicLaunch = copy.deepcopy(_dicArgs)
        dicPathVars = _xPrjCfg.GetFilepathVarDict(_xPrjCfg.pathLaunch)
        # Add path variables to launch args, so that CreateAction() can find them
        ison.util.data.AddVarsToData(self._dicLaunch, dicLocals=dicPathVars)

        xConfigCML = CConfigCML(xPrjCfg=_xPrjCfg, sImportPath=_xPrjCfg.pathLaunch.as_posix())
        self._dicLaunch = xConfigCML.Process(self._dicLaunch)
        self._dicRtv = xConfigCML.GetRuntimeVars(_bCopy=False)
        self._setRtvEval = xConfigCML.GetRuntimeVarEvalSet(_bCopy=False)

    # enddef

    ######################################################################################
    def GetActionPaths(self) -> list[str]:
        dicActionArgs = config.GetDictValue(self._dicLaunch, "mActions", dict, sWhere="launch arguments")

        # Available actions
        lActPaths = config.GetDictPaths(dicActionArgs, sDTI="/catharsys/launch/action:*")
        # Avilable action aliases
        lActPaths.extend(config.GetDictPaths(dicActionArgs, sDTI="/catharsys/launch/action-alias:*"))

        lActPaths.sort()
        return lActPaths

    # enddef

    ######################################################################################
    # Apply an action alias and return a new launch config instance,
    # together with the final action name.
    # if the given action name is not an alias, returns a copy of this instance.
    def ResolveActionAlias(self, _sActionAlias: str) -> Tuple[str, "CConfigLaunch"]:
        dicActionArgs = config.GetDictValue(self._dicLaunch, "mActions", dict, sWhere="launch arguments")

        # Available actions
        lActPaths = config.GetDictPaths(dicActionArgs, sDTI="/catharsys/launch/action:*")
        # Avilable action aliases
        lActAliPaths = config.GetDictPaths(dicActionArgs, sDTI="/catharsys/launch/action-alias:*")

        # if given action name is not an alias, the return a copy of this instance
        if _sActionAlias in lActPaths:
            return _sActionAlias, CConfigLaunch(self._dicLaunch, self._dicRtv, self._setRtvEval)
        # endif

        # if given action name is also not an alias, then this is an error
        if _sActionAlias not in lActAliPaths:
            raise CAnyError_Message(sMsg=f"Action '{_sActionAlias}' not found in launch arguments")
        # endif

        # Resolve potential chain of aliases
        sActionName = _sActionAlias
        lAliCfg = []
        while sActionName in lActAliPaths:
            sInActAlias = f"action alias '{sActionName}'"
            dicAlias = config.GetDictValue(
                dicActionArgs,
                sActionName,
                dict,
                bAllowKeyPath=True,
                sWhere="launch actions",
            )
            sActionName = config.GetDictValue(dicAlias, "sActionName", str, sWhere=sInActAlias)
            lAliCfg.insert(
                0,
                config.GetDictValue(dicAlias, "mConfig", dict, xDefault={}, sWhere=sInActAlias),
            )
        # endwhile

        if sActionName not in lActPaths:
            raise CAnyError_Message(
                sMsg=f"Action '{sActionName}' referenced in {sInActAlias} not found in launch configuration"
            )
        # endif

        # Create copy of launch args and apply alias overrides
        dicNewLaunch = copy.deepcopy(self._dicLaunch)
        dicNewActArgs = config.GetDictValue(dicNewLaunch, "mActions", dict, sWhere="launch arguments")
        dicNewAct = config.GetDictValue(
            dicNewActArgs,
            sActionName,
            dict,
            bAllowKeyPath=True,
            sWhere="launch actions",
        )
        dicNewActCfg = config.GetDictValue(dicNewAct, "mConfig", dict, sWhere=f"action '{sActionName}' arguments")

        for dicAliCfg in lAliCfg:
            dicNewActCfg.update(dicAliCfg)
        # endfor

        return sActionName, CConfigLaunch(dicNewLaunch, self._dicRtv, self._setRtvEval)

    # enddef

    ######################################################################################
    def GetResolvedActionData(self, _sAction):
        sAction, xLaunchCfg = self.ResolveActionAlias(_sAction)
        return xLaunchCfg.GetActionData(sAction)

    # enddef

    ######################################################################################
    def GetActionInfo(self, _sAction):
        dicAction = self.GetResolvedActionData(_sAction)
        dicConfig = config.GetDictValue(dicAction, "mConfig", dict, sWhere=f"action '{_sAction}' arguments")
        return dicConfig.get("sInfo", "")

    # enddef

    ######################################################################################
    def GetActionConfig(self, _sAction) -> dict:
        try:
            dicActions = self.dicLaunch.get("mActions")
            if dicActions is None:
                raise CAnyError_Message(sMsg="Launch configuration does not contain element 'mActions'.")
            # endif

            dicAction: dict = config.GetDictValue(
                dicActions,
                _sAction,
                dict,
                bAllowKeyPath=True,
                sWhere="launch configuration actions",
            )

            dicCfg = dicAction.get("mConfig")
            if dicCfg is None:
                dicCfg = dicAction["mConfig"] = {}
            # endif

        except Exception as xEx:
            raise CAnyError_Message(sMsg="Error obtaining action data", xChildEx=xEx)
        # endtry

        return dicCfg

    # enddef

    ######################################################################################
    # Get dictionary of all execution files per action
    def GetActionData(self, _sAction, *, dicConfigOverride: Optional[dict] = None):
        try:
            dicNewConfig = copy.deepcopy(self.dicGlobalArgs)
            dicActions = self.dicLaunch.get("mActions")
            if dicActions is None:
                raise CAnyError_Message(sMsg="Launch configuration does not contain element 'mActions'.")
            # endif

            dicAction: dict = config.GetDictValue(
                dicActions,
                _sAction,
                dict,
                bAllowKeyPath=True,
                sWhere="launch configuration actions",
            )
            dicAction: dict = copy.deepcopy(dicAction)

            dicConfig = dicAction.get("mConfig")
            if dicConfig is None:
                # only global arguments are used
                dicConfig = dicAction["mConfig"] = {}
                # raise CAnyError_Message(sMsg="Element 'mConfig' missing in launch configuration of action '{}'"
                #                         .format(_sAction))
            # endif

            # update global arguments with config and replace config with combined dictionary
            dicNewConfig.update(dicConfig)
            if isinstance(dicConfigOverride, dict):
                dicNewConfig.update(dicConfigOverride)
            # endif
            dicAction["mConfig"] = dicNewConfig
        except Exception as xEx:
            raise CAnyError_Message(sMsg="Error obtaining action data", xChildEx=xEx)
        # endtry

        ison.util.data.AddLocalGlobalVars(dicAction, self.dicLaunch)
        return dicAction

    # enddef

    ######################################################################################
    # Get dictionary of all execution files per action
    def GetActionDict(self, *, dicConfigOverride: Optional[dict] = None):
        try:
            dicAllAct = {}
            dicGlobalArgs = self.dicLaunch.get("mGlobalArgs", {})
            dicActions = self.dicLaunch.get("mActions")
            if dicActions is None:
                raise CAnyError_Message(sMsg="Launch configuration does not contain element 'mActions'.")
            # endif

            lActPaths = config.GetDictPaths(dicActions, sDTI="/catharsys/launch/action:*")

            if len(lActPaths) == 0:
                raise CAnyError_Message(sMsg="No action definitions found of type '/catharsys/launch/action:*'")
            # endif

            for sActPath in lActPaths:
                dicAction: dict = config.GetDictValue(
                    dicActions,
                    sActPath,
                    dict,
                    bAllowKeyPath=True,
                    sWhere="launch configuration actions",
                )
                dicAction: dict = copy.deepcopy(dicAction)

                dicConfig = dicAction.get("mConfig")
                if dicConfig is None:
                    # only global arguments are used
                    dicConfig = dicAction["mConfig"] = {}
                # endif

                dicNewConfig = copy.deepcopy(dicGlobalArgs)
                # update config with global arguments
                dicNewConfig.update(dicConfig)
                if isinstance(dicConfigOverride, dict):
                    dicNewConfig.update(dicConfigOverride)
                # endif
                dicAction["mConfig"] = dicNewConfig
                ison.util.data.AddLocalGlobalVars(dicAction, self.dicLaunch)

                dicAllAct[sActPath] = dicAction
            # endfor
        except Exception as xEx:
            raise CAnyError_Message(sMsg="Error obtaining action data", xChildEx=xEx)
        # endtry

        return dicAllAct

    # enddef

    ######################################################################################
    # Get dictionary of all actions per trial
    def GetTrialActionDict(self, *, dicConfigOverride: Optional[dict] = None):
        dicTrialAct = {}
        dicActAll: dict = self.GetActionDict(dicConfigOverride=dicConfigOverride)
        sActPath: str = None
        for sActPath in dicActAll:
            dicAct: dict = dicActAll[sActPath]
            sTrialFile = dicAct["mConfig"].get("sTrialFile")
            if sTrialFile is None:
                continue
            # endif

            lTrialActs: list = dicTrialAct.get(sTrialFile)
            if lTrialActs is None:
                lTrialActs = dicTrialAct[sTrialFile] = []
            # endif
            lTrialActs.append(sActPath)
        # endfor

        return dicTrialAct

    # enddef


# endclass
