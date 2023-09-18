#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \start.py
# Created Date: Thursday, May 5th 2022, 11:51:37 am
# Author: Christian Perwass (CR/AEC5)
# <LICENSE id="Apache-2.0">
#
#   Image-Render Setup module
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

import warnings

from collections import defaultdict

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    # pkg_resources is DEPRECATED and should be replaced at some point.
    import pkg_resources
# endwith

import importlib
import inspect
import os

from catharsys.decs.decorator_log import logFunctionCall

from catharsys.util import CEntrypointInformation


# ###################################################################
def _GetCatharsysGroups():
    """get all distributions"""
    listofdists = [list(pkg_resources.find_distributions(d)) for d in pkg_resources.working_set.entries]
    lAllDists = [xDist for lDist in listofdists for xDist in lDist]

    # get all entry point groups associated with catharsys
    setCatharsysGroups = set(
        [
            sKey
            for lKeys in [pkg_resources.get_entry_map(d).keys() for d in lAllDists]
            for sKey in lKeys
            if "catharsys" in sKey
        ]
    )
    return setCatharsysGroups


# enddef


# ###################################################################
# ###################################################################
class CCatharsysCategories:
    """walk through the pkg list and extracts the catharsys specific pkgs.
    Afterwards, it analyses the entry points and sort them in different categories"""

    def __init__(self) -> None:
        # protected class attributes
        self.__ENTRY_POINT_DICTS = defaultdict(lambda: dict(), dict())

        xCatGroups = _GetCatharsysGroups()

        for sGroup in xCatGroups:
            for ep in pkg_resources.iter_entry_points(sGroup, name=None):
                # print(f"#{d}")
                sIdentifier, sPathExtension = str(ep).split(" = ")

                if ":" in sPathExtension:
                    sPath, sObjectName = sPathExtension.split(":")
                    self._DetermineCatPackage_bySubModuleName(
                        _sGroupName=sGroup,
                        _sIdentifier=sIdentifier,
                        _sModuleName=sPath,
                        _sObjectName=sObjectName,
                    )

                else:
                    self._DetermineCatPackage_byModuleName(
                        _sGroupName=sGroup,
                        _sIdentifier=sIdentifier,
                        _sModuleName=sPathExtension,
                    )
                # endif
            # end for entry points
        # end for all groups
        pass

    # -------------------------------------------------------------------------------------------
    def Collect(self, _sGroupName: str = None):
        lReturnActions = list()
        for xEntryTypeKey, dictAction in self.__ENTRY_POINT_DICTS.items():
            if xEntryTypeKey not in (
                CEntrypointInformation.EEntryType.UNDEFINED,
                CEntrypointInformation.EEntryType.UNKNOWN,
            ):
                for _, xIdAction in dictAction.items():
                    lReturnActions.append(xIdAction)
                # endfor all items
            # endif not unknown
        # endfor all entries

        # select groupname, if wanted
        if _sGroupName is not None:
            lReturnActions = [
                xIdAction
                for xIdAction in lReturnActions
                if _sGroupName in xIdAction.group or _sGroupName == xIdAction.entry.name
            ]

        return lReturnActions

    # enddef

    # -------------------------------------------------------------------------------------------
    def Find(self, _xslIdentifier, _sGroupName: str = None):
        xActionTemp = self.Collect(_sGroupName)
        lReturnActions = None

        # select only those actions, that matches the identifier(s)
        if isinstance(_xslIdentifier, str):
            lReturnActions = [xAction for xAction in xActionTemp if xAction.IsPatternInside(_xslIdentifier)]
        elif isinstance(_xslIdentifier, list):
            lReturnActions = xActionTemp
            for fStr in _xslIdentifier:
                lReturnActions = [xAction for xAction in lReturnActions if xAction.IsPatternInside(fStr)]
        # endif identifier

        return lReturnActions

    # enddef

    # -------------------------------------------------------------------------------------------
    def _DetermineCatPackage_bySubModuleName(
        self, _sGroupName: str, _sIdentifier: str, _sModuleName: str, _sObjectName: str
    ):
        """tries to im port the command and determine the different pkg entry point alternatives"""
        try:
            xCatPackage = importlib.import_module(_sModuleName)
            sFilename = xCatPackage.__file__

            xEntryType = CEntrypointInformation.EEntryType.UNKNOWN
            xEpInfo = CEntrypointInformation(
                entry=xEntryType,
                group=_sGroupName,
                ID=_sIdentifier,
                module_name=_sModuleName,
                definition=_sModuleName,
                filename=sFilename,
                objname=_sObjectName,
            )
            if _sObjectName in dir(xCatPackage):
                xPackageObject = vars(xCatPackage)[_sObjectName]
                xEpInfo.module_name = xPackageObject.__module__
                xEpInfo.definition = (
                    xPackageObject.__doc__ if xPackageObject.__doc__ is not None else "object DocString n/a"
                )
                # if callable(obj):
                if inspect.isfunction(xPackageObject):
                    xEntryType = CEntrypointInformation.EEntryType.FUNCTION
                    xEpInfo.filename = f'"{sFilename}", line {xPackageObject.__code__.co_firstlineno}'
                elif inspect.isclass(xPackageObject):
                    xEntryType = CEntrypointInformation.EEntryType.CLASSES
                else:
                    # now look in entry point decorators
                    if hasattr(xPackageObject, "wrappedFunc"):
                        xEntryType = CEntrypointInformation.GetEntryType(xPackageObject.wrappedFunc)
                        xEpDescriptionDict = CEntrypointInformation.GetEntryInterfaceDoc(xPackageObject.wrappedFunc)
                        if xEpDescriptionDict is not None:
                            xEpInfo.definition = CEntrypointInformation.CDetailedDefinition(
                                xEpInfo.definition, xEpDescriptionDict
                            )
                        xEpInfo.filename = f'"{sFilename}", line {xPackageObject.wrappedFunc.__code__.co_firstlineno}'
                    else:
                        print(
                            f" ?????? {_sModuleName} wie geht's weiter mit {_sObjectName}"
                            " not in (isfunction, isclass, wrappedFunc)"
                        )
                    # endif wrappedFunc
                # endif obj matching
            else:
                print(f" ?????? {_sModuleName} wie geht's weiter mit {_sObjectName} not in dir(cat_package)")
            # end if

            xEpInfo.entry = xEntryType
            self.__ENTRY_POINT_DICTS[xEntryType].update({_sIdentifier: xEpInfo})

        except ImportError:
            print(f" {_sModuleName} doesn't exist")
            self.__ENTRY_POINT_DICTS[CEntrypointInformation.EEntryType.UNDEFINED].update(
                {
                    _sIdentifier: CEntrypointInformation(
                        CEntrypointInformation.EEntryType.UNDEFINED,
                        _sGroupName,
                        _sIdentifier,
                        _sModuleName,
                    )
                }
            )
        # endtry import

    # enddef

    # -------------------------------------------------------------------------------------------
    def _DetermineCatPackage_byModuleName(self, _sGroupName: str, _sIdentifier: str, _sModuleName: str):
        """tries to im port the command and determine the different pkg entry point alternatives"""

        try:
            lStrGroups = _sGroupName.split(".")[2:]
            if len(lStrGroups) > 0:
                lStrGroups.append(_sIdentifier)
                _sIdentifier = ".".join(lStrGroups)
            # endif grouphandling

            xCatPackage = importlib.import_module(_sModuleName)
            sFilename = xCatPackage.__file__

            xEntryType = CEntrypointInformation.EEntryType.UNKNOWN
            xEpInfo = CEntrypointInformation(
                entry=xEntryType,
                group=_sGroupName,
                ID=_sIdentifier,
                module_name=_sModuleName,
                filename=sFilename,
                definition="not documented so far",
                objname=_sModuleName.split(".")[-1],
            )
            if "g_sCmdDesc" in vars(xCatPackage):
                if "g_xArgParser" not in vars(xCatPackage):
                    xEntryType = CEntrypointInformation.EEntryType.COMMAND
                    xEpInfo.definition = xCatPackage.g_sCmdDesc
                # end if
            elif all(func in dir(xCatPackage) for func in ["GetDefinition", "ResultData", "Run"]):
                xEntryType = CEntrypointInformation.EEntryType.ACTION
                xEpInfo.definition = xCatPackage.GetDefinition()
            elif "StartJob" in dir(xCatPackage):
                xEntryType = CEntrypointInformation.EEntryType.EXE_PLUGIN
                xEpInfo.definition = (
                    xCatPackage.StartJob.__doc__ if xCatPackage.StartJob.__doc__ is not None else "job DocString n/a"
                )
            else:
                print(f" ?????? {_sModuleName} wie geht's weiter")
            # endif cat_package matching

            xEpInfo.entry = xEntryType
            self.__ENTRY_POINT_DICTS[xEntryType].update({_sIdentifier: xEpInfo})

        except ImportError:
            print(f"{_sModuleName} doesn't exist")
            self.__ENTRY_POINT_DICTS[CEntrypointInformation.EEntryType.UNDEFINED].update(
                {
                    _sIdentifier: CEntrypointInformation(
                        CEntrypointInformation.EEntryType.UNDEFINED,
                        _sGroupName,
                        _sIdentifier,
                        _sModuleName,
                    )
                }
            )
        # endtry import

    # enddef

    # -------------------------------------------------------------------------------------------


# ###################################################################
# ###################################################################
