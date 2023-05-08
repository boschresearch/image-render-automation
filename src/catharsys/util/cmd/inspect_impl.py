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

from anybase.cls_any_error import CAnyError_Message
from catharsys.util import CEntrypointInformation
from catharsys.util import CCatharsysCategories
from catharsys.decs.decorator_log import logFunctionCall

from importlib.metadata import entry_points as EntryPoints


# ###################################################################


# ###################################################################
# ###################################################################


def __CheckQualifier(_lDisplayPattern):
    if _lDisplayPattern is not None:
        for sPattern in _lDisplayPattern:
            if sPattern not in CEntrypointInformation.Names():
                raise CAnyError_Message(
                    sMsg=f"{sPattern} is not part of CEptInfo-Fields:{CEntrypointInformation.Names()}"
                )
    pass


# enddef

# ###################################################################
@logFunctionCall
def __PrintFindResult(_lSelectedCatagetories, _lDisplayPattern):

    if _lDisplayPattern is None:
        for idx, action in enumerate(_lSelectedCatagetories):
            print("v" * 100)
            print(f"[{idx}] {action}")
            print("^" * 100)
            print()
        # end for
    else:
        bOnlyID = len(_lDisplayPattern) == 1 and _lDisplayPattern[0] == "ID"
        if "ID" in _lDisplayPattern:
            _lDisplayPattern.remove("ID")
        if "entry" in _lDisplayPattern:
            _lDisplayPattern.remove("entry")

        for idx, action in enumerate(_lSelectedCatagetories):
            if bOnlyID:
                print(f"[{idx}] {action.entry.name} - {action.ID}")
            else:
                lSValues = [str(getattr(action, q)) for q in _lDisplayPattern]
                print(f"[{idx}:{action.entry.name}] {action.ID} : {', '.join(lSValues)}")
        # end for
    # end if


# enddef

# ###################################################################
@logFunctionCall
def _GroupHint(xCategories: CCatharsysCategories):
    lAllCategories = xCategories.Collect(None)
    groups = set()
    for action in lAllCategories:
        lElements = action.group.split(".")
        lElements.append(action.entry.name)
        for sGroupParts in lElements:
            groups.add(sGroupParts)
    # endfor action
    print(
        f"currently there is no result, do you think you gave a correct group-pattern?\navailable groups are: {groups}"
    )


# enddef


# ###################################################################
@logFunctionCall
def _Nav_findAll(_sGroupName: str = None, _lDisplayPattern=None, _bPrintResult=True):
    __CheckQualifier(_lDisplayPattern)

    xCategories = CCatharsysCategories()
    lGroupedCat = xCategories.Collect(_sGroupName)
    if _bPrintResult:
        __PrintFindResult(lGroupedCat, _lDisplayPattern)

        if len(lGroupedCat) == 0 and isinstance(_sGroupName, str) and len(_sGroupName) > 0:
            _GroupHint(xCategories)
        # endif

    return lGroupedCat


# enddef


# ###################################################################
@logFunctionCall
def _Nav_find(_sGroupName: str, _xslFindPattern, _lDisplayPattern):
    __CheckQualifier(_lDisplayPattern)

    xCategories = CCatharsysCategories()
    xCategoriesSubset = xCategories.Find(_xslFindPattern, _sGroupName)
    __PrintFindResult(xCategoriesSubset, _lDisplayPattern)

    if len(xCategoriesSubset) == 0 and isinstance(_sGroupName, str) and len(_sGroupName) > 0:
        _GroupHint(xCategories)
    # endif

    return xCategoriesSubset


# enddef


# ###################################################################
# ###################################################################
@logFunctionCall
def Run_Nav(*, _sGroupName, _xslFindPattern, _lDisplayPattern, _bFindAll: bool):

    lEpGroups_raw = [epPoint for sKey, epPoint in EntryPoints().items() if "catharsys.inspect" in sKey]
    # It seems that sometimes entry points are listed multiple times.
    # Maybe just a bug of pip or the metadata lib.
    # So, ensure here that each entry point is only scanned once.
    setCmdNames = set()
    lEntryPoints = []
    for lEntryPointsInGroup in lEpGroups_raw:
        for epPoint in lEntryPointsInGroup:
            if epPoint.name in setCmdNames:
                continue
            # endif
            setCmdNames.add(epPoint.name)
            lEntryPoints.append(epPoint)
        # end for
    # end for

    for epPoint in lEntryPoints:
        epCmd = epPoint.load()
        if hasattr(epCmd, "ExtendSysPath"):
            epCmd.ExtendSysPath()
        # endif
    # end for

    if _bFindAll:
        _Nav_findAll(
            _sGroupName=_sGroupName,
            _lDisplayPattern=_lDisplayPattern,
            _bPrintResult=True,
        )
    elif isinstance(_xslFindPattern, str) or isinstance(_xslFindPattern, list):
        _Nav_find(_sGroupName, _xslFindPattern, _lDisplayPattern)
    pass
