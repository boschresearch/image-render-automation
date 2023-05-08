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

####################################################################
def Info(
    *,
    sPathWorkspace: Optional[str] = None,
    sFileBasenameLaunch: Optional[str] = None,
):

    try:
        pathWS = None
        if sPathWorkspace is not None:
            # A project path has been specified
            pathWS = Path(sPathWorkspace)
            if not pathWS.exists():
                raise CAnyError_Message(
                    sMsg="Project path does not exist: {}".format(pathWS.as_posix())
                )
            # endif
        # endif

        wsX = capi.CWorkspace(
            xWorkspace=pathWS, sFileBasenameLaunch=sFileBasenameLaunch
        )
        print("Workspace: {}, version {}".format(wsX.sName, wsX.sVersion))
        print("Path: {}".format(wsX.pathWorkspace.as_posix()))
        print("Required Catharsys Version: {}".format(wsX.sRequiredCatharsysVersion))
        print("Active Catharsys Version: {}".format(wsX.sCatharsysVersion))
        print("Configurations:")
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

    except Exception as xEx:
        xFinalEx = CAnyError_Message(
            sMsg="Error obtaining info on workspace", xChildEx=xEx
        )
        raise RuntimeError(xFinalEx.ToString())
    # endtry


# enddef
