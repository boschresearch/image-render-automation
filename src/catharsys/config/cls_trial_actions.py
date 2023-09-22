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
    lTrialFileOptions: list[str]
    xLaunch: CConfigLaunch


# endclass


# ####################################################################################
# This class enables handling of actions per trial.
# In the launch file, actions are defined, and for each action a trial file is given.
# This class scans all actions of a launch file and collects the actions per trial file.
class CTrialActions:
    def __init__(self, _xLaunch: CConfigLaunch):
        self._xLaunch = copy.copy(_xLaunch)

        self._lActionPaths = self._xLaunch.GetActionPaths()
        self.UpdateResolvedActions()

    # enddef

    @property
    def dicLaunch(self) -> dict:
        return self._xLaunch.dicLaunch

    # enddef

    @property
    def dicGlobalArgs(self) -> dict:
        return self._xLaunch.dicGlobalArgs

    # enddef

    @property
    def lTrialFiles(self) -> list[str]:
        return list(self._dicTrialActionPaths.keys())

    # enddef

    def GetTrialActionPaths(self, _sTrial: str) -> list[str]:
        return self._dicTrialActionPaths.get(_sTrial)

    # enddef

    def GetResolvedAction(self, _sActionPath: str) -> CResolvedAction:
        return self._dicActionSet.get(_sActionPath)

    # enddef

    def GetTrialSelection(self) -> str:
        sTrial: str = self._xLaunch.dicGlobalArgs.get("sTrialFile")
        if sTrial is None:
            sTrial = self.lTrialFiles[0]
        # endif
        return sTrial

    # enddef

    # #####################################################################################################
    def SetActiveTrial(self, _sTrial: str):
        sGlobalTrialFile: str = self._xLaunch.dicGlobalArgs.get("sTrialFile")
        lGlobalTrialFileOptions: list[str] = self._xLaunch.dicGlobalArgs.get("lTrialFileOptions")

        if sGlobalTrialFile is not None and isinstance(lGlobalTrialFileOptions, list):
            if _sTrial in lGlobalTrialFileOptions:
                if sGlobalTrialFile not in lGlobalTrialFileOptions:
                    lGlobalTrialFileOptions.append(sGlobalTrialFile)
                # endif
                self._xLaunch.dicGlobalArgs["sTrialFile"] = _sTrial
            # endif
        # endif

        lActionPaths: list[str] = self._dicTrialActionPaths.get(_sTrial)
        if lActionPaths is not None:
            for sActionPath in lActionPaths:
                xResAct: CResolvedAction = self._dicActionSet[sActionPath]
                dicActCfg: dict = xResAct.xLaunch.GetActionConfig(xResAct.sBaseAction)
                lTrialFileOptions: list[str] = dicActCfg.get("lTrialFileOptions", lGlobalTrialFileOptions)
                if "sTrialFile" in dicActCfg and isinstance(lTrialFileOptions, list) and _sTrial in lTrialFileOptions:
                    sCurTrial = dicActCfg["sTrialFile"]
                    if sCurTrial not in lTrialFileOptions:
                        lCurTrialFileOptions: list[str] = dicActCfg.get("lTrialFileOptions")
                        if isinstance(lCurTrialFileOptions, list):
                            lCurTrialFileOptions.append(sCurTrial)
                        else:
                            dicActCfg["lTrialFileOptions"] = [sCurTrial] + lGlobalTrialFileOptions
                        # endif
                    # endif
                    dicActCfg["sTrialFile"] = _sTrial
                # endif
            # endfor
        # endif

    # enddef

    # #####################################################################################################
    def UpdateResolvedActions(self):
        sGlobalTrialFile: str = self._xLaunch.dicGlobalArgs.get("sTrialFile")
        lGlobalTrialFileOptions: list[str] = self._xLaunch.dicGlobalArgs.get("lTrialFileOptions")

        self._dicActionSet = {}
        self._dicTrialActionPaths = {}

        for sActionPath in self._lActionPaths:
            sBaseAction, xActLaunch = self._xLaunch.ResolveActionAlias(sActionPath)
            dicActCfg: dict = xActLaunch.GetActionConfig(sBaseAction)
            sTrialFile = dicActCfg.get("sTrialFile")
            if sTrialFile is None:
                sTrialFile = sGlobalTrialFile
            # endif
            lTrialFileOptions = dicActCfg.get("lTrialFileOptions")
            if lTrialFileOptions is None:
                lTrialFileOptions = lGlobalTrialFileOptions
            # endif

            if sTrialFile is None:
                raise RuntimeError(f"No trial file specified for action: {sActionPath}")
            # endif

            lActTrialFileOptions: list[str]
            if not isinstance(lTrialFileOptions, list):
                lActTrialFileOptions = [sTrialFile]
            else:
                lActTrialFileOptions = lTrialFileOptions.copy()
                if sTrialFile not in lActTrialFileOptions:
                    lActTrialFileOptions.append(sTrialFile)
                # endif
            # endif

            self._dicActionSet[sActionPath] = CResolvedAction(
                sActionPath=sActionPath,
                sBaseAction=sBaseAction,
                sTrialFile=sTrialFile,
                lTrialFileOptions=lActTrialFileOptions,
                xLaunch=xActLaunch,
            )

            for sActTrialFile in lActTrialFileOptions:
                lTrialAction = self._dicTrialActionPaths.get(sActTrialFile)
                if lTrialAction is None:
                    lTrialAction = self._dicTrialActionPaths[sActTrialFile] = []
                # endif
                lTrialAction.append(sActionPath)
            # endfor
        # endfor

    # enddef

    # #####################################################################################################
    def ApplyResolvedActions(self):
        sActPath: str = None
        for sActPath in self._dicActionSet:
            xResAct: CResolvedAction = self._dicActionSet[sActPath]
            dicResCfg: dict = xResAct.xLaunch.GetActionConfig(xResAct.sBaseAction)
            self._xLaunch.SetActionConfig(sActPath, dicResCfg)
        # endfor

    # enddef


# endclass
