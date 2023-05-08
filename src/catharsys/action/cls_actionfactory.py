#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \cls_actions.py
# Created Date: Monday, April 25th 2022, 3:47:55 pm
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

from typing import Optional

from anybase import config, plugin
from anybase.cls_any_error import CAnyError_Message, CAnyError_TaskMessage

import sys

from catharsys.config.cls_project import CProjectConfig

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib import metadata
# endif

from catharsys.config.cls_launch import CConfigLaunch
from catharsys.action.cls_actionclass_executor import CActionClassExecutor

from catharsys.decs.decorator_log import logFunctionCall


class CActionFactory:
    """
    This class creates actions launcher.
    """

    ########################################################################################
    def __init__(self, *, xPrjCfg, dicLaunchArgs=None):
        self._xPrjCfg: CProjectConfig = None
        self._xCfgLaunch: CConfigLaunch = None

        self._xPrjCfg = xPrjCfg

        # Intantiate launch config class with action config
        self._xCfgLaunch = CConfigLaunch()

        if dicLaunchArgs is None:
            # Load launch config file form project defaults
            self._xCfgLaunch.LoadFile(self._xPrjCfg)
        else:
            # Set launch config from given dictionary
            self._xCfgLaunch.SetLaunchArgs(self._xPrjCfg, dicLaunchArgs)
        # endif

    # enddef

    ########################################################################################
    def GetActionPaths(self) -> list[str]:
        return self._xCfgLaunch.GetActionPaths()

    # enddef

    ########################################################################################
    @logFunctionCall
    def CreateAction(
        self, *, sAction: str, dicConfigOverride: Optional[dict] = None
    ) -> CActionClassExecutor:

        try:
            # Resolve potential action aliases
            sActionName, xActCfgLaunch = self._xCfgLaunch.ResolveActionAlias(sAction)

            # Get action launch configuration data
            dicActData = xActCfgLaunch.GetActionData(
                sActionName, dicConfigOverride=dicConfigOverride
            )

            try:
                # Get the action DTI, which is used to load the actual action plugin
                sActDti = dicActData["sActionDTI"]
                dicActArgs = dicActData["mConfig"]

            except KeyError as xEx:
                raise CAnyError_Message(
                    sMsg="Element '{}' not specified in launch configuration".format(
                        str(xEx)
                    )
                )
            # endtry

            # Look for action module
            epAction = plugin.SelectEntryPointFromDti(
                sGroup="catharsys.action",
                sTrgDti=sActDti,
                sTypeDesc="catharsys action module",
            )

            modAction = epAction.load()
            dicActCfg = modAction.GetDefinition()
            sActClsDti = dicActCfg.get("sDTI")
            sPrjDti = dicActCfg.get("sProjectClassDTI")

            # Append "/join" to DTI of action class config
            sActClsDti = config.JoinDti(sActClsDti, "class")

            # Load the action class declaration.
            # The action class prepares the data and launches the actual action.
            epActCls = plugin.SelectEntryPointFromDti(
                sGroup="catharsys.actionclass",
                sTrgDti=sActClsDti,
                sTypeDesc="catharsys action class",
            )

            # Create project class instance specified by action
            xActPrjCfg = CProjectConfig.Create(sDTI=sPrjDti)
            # Initialize action project config class with given project config
            xActPrjCfg.FromProject(self._xPrjCfg)

            # Loads action class declaration
            clsActionClass = epActCls.load()

            # Update project configuration with launch arguments
            xActPrjCfg.ApplyConfig(dicActArgs)

            xAction: CActionClassExecutor = clsActionClass(
                xPrjCfg=xActPrjCfg,
                sAction=sActionName,
                dicActArgsOverride=dicConfigOverride,
                dicActCfg=dicActCfg,
                xCfgLaunch=xActCfgLaunch,
            )

            return xAction

        except Exception as xEx:
            raise CAnyError_TaskMessage(
                sTask="Create Action",
                sMsg="Error creating action '{}'".format(sAction),
                xChildEx=xEx,
            )
        # endtry

    # enddef


# endclass
