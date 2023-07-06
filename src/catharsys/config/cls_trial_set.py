###
# Author: Christian Perwass (CR/ADI2.1)
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

import copy
from dataclasses import dataclass
from typing import Tuple, Optional
from anybase.cls_any_error import CAnyError_Message

from .cls_launch import CConfigLaunch


@dataclass
class CResolvedAction:
    sActionPath: str
    sBaseAction: str
    sTrialFile: str
    xLaunch: CConfigLaunch


# endclass


class CTrialSet:
    def __init__(self, _xLaunch: CConfigLaunch):
        self._xLaunch = copy.copy(_xLaunch)

        self._lActionPaths = self._xLaunch.GetActionPaths()

        sGlobalTrialFile: str = self._xLaunch.dicGlobalArgs.get("sTrialFile")

        self._dicActionSet = {}
        self._dicTrialActions = {}

        for sActionPath in self._lActionPaths:
            sBaseAction, xActLaunch = self._xLaunch.ResolveActionAlias(sActionPath)
            sTrialFile = xActLaunch.GetActionConfig(sBaseAction).get("sTrialFile")
            if sTrialFile is None:
                sTrialFile = sGlobalTrialFile
            # endif

            self._dicActionSet[sActionPath] = CResolvedAction(
                sActionPath=sActionPath, sBaseAction=sBaseAction, sTrialFile=sTrialFile, xLaunch=xActLaunch
            )

            lTrialAction = self._dicTrialActions.get(sTrialFile)
            if lTrialAction is None:
                lTrialAction = self._dicTrialActions[sTrialFile] = []
            # endif
            lTrialAction.append(sActionPath)
        # endfor

    # enddef

    @property
    def dicGlobalArgs(self) -> dict:
        return self._xLaunch.dicGlobalArgs

    # enddef

    @property
    def lTrialFiles(self) -> list[str]:
        return list(self._dicTrialActions.keys())

    # enddef

    def GetTrialActionPaths(self, _sTrial: str) -> list[str]:
        return self._dicTrialActions.get(_sTrial)

    # enddef


# endclass
