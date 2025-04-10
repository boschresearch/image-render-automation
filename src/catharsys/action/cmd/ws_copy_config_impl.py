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

from typing import Optional
from pathlib import Path

from anybase.cls_any_error import CAnyError_Message

import catharsys.api as capi
from catharsys.setup import util


#################################################################################
def _PrintConfigs(wsX: capi.CWorkspace):

    for sPrjId in wsX.lProjectNames:
        xPrj = wsX.Project(sPrjId)
        sInfo = xPrj.sInfo
        if len(sInfo) > 0:
            print("  - {}: {}".format(sPrjId, sInfo))
        else:
            print("  - {}".format(sPrjId))
        # endif

        for sAction in xPrj.lActions:
            sInfo = xPrj.GetActionInfo(sAction)
            if len(sInfo) > 0:
                print("      * {}: {}".format(sAction, sInfo))
            else:
                print("      * {}".format(sAction))
            # endif
        # endfor
        print(" ")
    # endfor
    print("\n")


# enddef

#################################################################################
def Copy(*, sCfgNameSource: str, sCfgNameTarget: str, sPathWorkspace: str):

    try:
        pathWS = None
        if sPathWorkspace is not None:
            # A project path has been specified
            pathWS = Path(sPathWorkspace)
            if not pathWS.exists():
                raise CAnyError_Message(sMsg="Project path does not exist: {}".format(pathWS.as_posix()))
            # endif
        # endif

        wsX = capi.CWorkspace(xWorkspace=pathWS)
        # print("Workspace: {}, version {}".format(wsX.sName, wsX.sVersion))
        print("Path: {}".format(wsX.pathWorkspace.as_posix()))

        if sCfgNameSource not in wsX.lProjectNames:
            raise RuntimeError(f"Source configuration '{sCfgNameSource}' not found in workspace")
        # endif

        if sCfgNameTarget in wsX.lProjectNames:
            raise RuntimeError(f"Target configuration '{sCfgNameTarget}' already available in workspace")
        # endif

        prjSrc = wsX.Project(sCfgNameSource)
        pathCfgSrc: Path = prjSrc.xConfig.pathLaunch
        pathCfgTrg: Path = wsX.pathConfig / sCfgNameTarget

        try:
            pathCfgTrg.mkdir(parents=True, exist_ok=False)
        except Exception as xEx:
            raise RuntimeError(f"Error creation configuration folder:\n{(str(xEx))}\n")
        # endtry

        lReExcludeDirs = [
            r"\.git",
            r"\.vscode",
            r"__pycache__",
            r".+\.egg-info",
            r"_blender",
            r"\.variants.*",
        ]

        lReExcludeFiles = [
            # r"\.git.+",
            r"\.vscode.+",
            r"stdout_.+\.txt",
            r"action-config-list_.+\.json",
            r"cml-vars_.+\.json",
            r"\.env",
            r".+\.egg-info",
        ]

        util.CopyFiles(
            pathCfgSrc,
            pathCfgTrg,
            pathSrcTop=pathCfgSrc,
            pathTrgTop=pathCfgTrg,
            lReExcludeDirs=lReExcludeDirs,
            lReExcludeFiles=lReExcludeFiles,
        )

    except Exception as xEx:
        xFinalEx = CAnyError_Message(sMsg="Error copying configuration", xChildEx=xEx)
        raise RuntimeError(xFinalEx.ToString())
    # endtry


# enddef
