#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \actions\launch.py
# Created Date: Tuesday, August 10th 2021, 9:31:09 am
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

import re
from pathlib import Path

from typing import Optional

from ison.util import data as isondata
from anybase import assertion, convert
from anybase import file as anyfile
from anybase.cls_any_error import CAnyError, CAnyError_Message

from catharsys.config.cls_project import CProjectConfig
from catharsys.action.cls_actionfactory import CActionFactory
from catharsys.action.cls_actionclass_executor import CActionClassExecutor
from catharsys.config.cls_job import CConfigJob

from catharsys.decs.decorator_log import logFunctionCall

from . import ws_impl
from .ws_launch import NsKeys


#####################################################################
@logFunctionCall
def Launch(
    *,
    xPrjCfg: CProjectConfig,
    sAction: str,
    dicConfigOverride: Optional[dict] = None,
    dicLaunchArgs: Optional[dict] = None,
    bDoProcess: bool = True,
    dicDebug: dict = {},
) -> CConfigJob:
    assertion.FuncArgTypes()

    # Create action factory for given action
    xActFac = CActionFactory(xPrjCfg=xPrjCfg, dicLaunchArgs=dicLaunchArgs)

    # Create the action
    xAction = xActFac.CreateAction(sAction=sAction, dicConfigOverride=dicConfigOverride)

    # Initialize action
    xAction.Init()

    # Executes the action and returns the configuration dictionaries
    return xAction.Execute(bDoProcess=bDoProcess, dicDebug=dicDebug)


# enddef


#####################################################################
def ListActions(*, xPrjCfg: CProjectConfig, dicLaunchArgs: Optional[dict] = None):
    assertion.FuncArgTypes()

    xActFac = CActionFactory(xPrjCfg=xPrjCfg, dicLaunchArgs=dicLaunchArgs)
    lActions = xActFac.GetActionPaths()

    print("Available actions:")
    for sAction in lActions:
        print("  - {}".format(sAction))
    # endfor
    print(" ")


# enddef

#####################################################################
# Get arguments for launch script


def GetScriptArgDict(_lScriptArgs: list[str]) -> dict:

    reEveryLetter = "[\\d\\w_-]+"
    reOnlySingleEqual = "[={1}]"
    reAssignMatch = reEveryLetter + reOnlySingleEqual + reEveryLetter

    def FindExact(_sEpxression, _sValue):
        tExactSpan = (0, len(_sValue))
        xReResult = re.search(_sEpxression, _sValue)
        bParseOK = xReResult and xReResult.span() == tExactSpan
        return bParseOK

    # enddef

    dicScript = dict()
    for sItem in _lScriptArgs:
        if FindExact(reAssignMatch, sItem):
            sKey, sValue = sItem.split("=")
            dicScript[sKey.strip()] = sValue.strip()
        elif FindExact(reEveryLetter, sItem):
            dicScript[sItem.strip()] = None
        else:
            raise CAnyError_Message(
                sMsg=(
                    f"parse error in '{sItem}', make sure vars and value (if any) consists of "
                    f"{reEveryLetter} for assignment use single '='"
                )
            )
        # endif
    # endfor

    return dicScript


# enddef


####################################################################


@logFunctionCall
def RunLaunch(
    *,
    sAction: str,
    sFileBasenameLaunch: Optional[str] = None,
    sTrialFile: Optional[str] = None,
    sExecFile: Optional[str] = None,
    sPathWorkspace: Optional[str] = None,
    sPathLaunch: Optional[str] = None,
    sFolderConfig: Optional[str] = None,
    lActArgs: Optional[list] = None,
    lScriptArgs: Optional[list] = None,
    sDebugPort: Optional[str] = None,
    sDebugTimeout: Optional[str] = None,
    bDebugSkipAction: bool = False,
    bShowActionGui: bool = False,
    bConfigOnly: bool = False,
    bIncludeConfigVars: bool = False,
):

    xPrjCfg = None
    if sAction is None:
        raise RuntimeError("No action specified")
    # endif

    try:
        xPrjCfg = CProjectConfig(sFileBasenameLaunch=sFileBasenameLaunch)
        pathMain = None

        if sPathWorkspace is not None:
            # A project path has been specified
            pathMain = Path(sPathWorkspace)
            if not pathMain.exists():
                raise CAnyError_Message(sMsg="Project path does not exist: {}".format(pathMain.as_posix()))
            # endif
        # endif

        if sFolderConfig is not None:
            # A config folder has been specified.
            # If the main path has not been specified explicitly,
            # the project config class assumes that the CWD is the project directory.
            if sPathLaunch is not None:
                print("Ignoring given launch path to use workspace path and config folder")
            # endif

            xPrjCfg.FromConfigName(xPathMain=pathMain, sConfigName=sFolderConfig)

        else:
            # No config folder specified.
            # Assume that the CWD is the launch path
            if pathMain is not None:
                print("Ignoring given workspace path to use launch path")
            # endif

            xPrjCfg.FromLaunchPath(sPathLaunch)
        # endif

        dicDebug = dict()

        if lScriptArgs is not None:
            dicDebug[NsKeys.script_args] = GetScriptArgDict(lScriptArgs)
        # endif

        if sDebugPort is not None:
            iDebugPort = convert.ToInt(sDebugPort, bDoRaise=False)
            if iDebugPort is not None:
                dicDebug[NsKeys.iDebugPort] = iDebugPort
            else:
                raise RuntimeError(f"The specified debug port must be an integer not '{sDebugPort}'")
            # endif
        # endif

        if sDebugTimeout is not None:
            fDebugTimeout = convert.ToFloat(sDebugTimeout, bDoRaise=False)
            if fDebugTimeout is not None:
                dicDebug[NsKeys.fDebugTimeout] = fDebugTimeout
            else:
                raise RuntimeError(f"The specified timeout must be a float value not '{sDebugPort}'")
            # endif
        # endif

        dicDebug[NsKeys.bSkipAction] = bDebugSkipAction
        dicDebug[NsKeys.bShowGui] = bShowActionGui

        dicConfigOverride = ws_impl.GetConfigOverride(sTrialFile=sTrialFile, sExecFile=sExecFile, lActArgs=lActArgs)

        bDoProcess = not bConfigOnly

        xProcConfig = Launch(
            xPrjCfg=xPrjCfg,
            sAction=sAction,
            dicConfigOverride=dicConfigOverride,
            bDoProcess=bDoProcess,
            dicDebug=dicDebug,
        )

        if bConfigOnly is True:
            dicProcConfig = xProcConfig.dicData
            sConfigName = xPrjCfg.sLaunchFolderName.replace("/", "+").replace(" ", "-").replace(".", "_")
            sActionFilename = sAction.replace("/", "+").replace(" ", "-").replace(".", "_")
            pathCfgFile = xPrjCfg.pathOutput / f"job-config_[{sConfigName}]_[{sActionFilename}].json"
            pathCfgFile.parent.mkdir(parents=True, exist_ok=True)

            if bIncludeConfigVars is False:
                dicProcConfig = isondata.StripVarsFromData(dicProcConfig)
            # endif

            # print(dicProcConfig)
            anyfile.SaveJson(pathCfgFile, dicProcConfig, iIndent=4)
            print("Processed configuration saved in file:\n> {}\n".format(pathCfgFile.as_posix()))
        # endif

    except Exception as xEx:
        if xPrjCfg is None:
            xFinalEx = CAnyError_Message(sMsg="Error launching action '{}'".format(sAction), xChildEx=xEx)
        else:
            xFinalEx = CAnyError_Message(
                sMsg="Error launching action '{}' from path: {}".format(sAction, xPrjCfg.sLaunchPath),
                xChildEx=xEx,
            )
        # endif
        raise RuntimeError(xFinalEx.ToString())
    # endtry


# enddef
