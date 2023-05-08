#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /py
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


# Make all symbols of anybase.config available as cathy.config symbols.
# This enables a later overwriting of function or addition of new functions.
# It's like class derivation.
from anybase.file import *

#######################################################################
# Load JSON file from relative path to script path
def LoadJsonFromRelPath(_xPrjCfg, _xRelPath):

    sFilePath = _xPrjCfg.GetAbsPath(_xRelPath).as_posix()
    return LoadJson(sFilePath)


# enddef

#######################################################################
# save JSON file from relative path to script path
def SaveJsonToRelPath(_xPrjCfg, _xRelPath, _dicData, **kwargs):

    iIndent = kwargs.pop("iIndent", 0)

    sFilePath = _xPrjCfg.GetAbsPath(_xRelPath).as_posix()
    SaveJson(sFilePath, _dicData, iIndent=iIndent)


# enddef

#######################################################################
# Save Python object as Pickle file in relative path to script path
def SavePickleToRelPath(_xPrjCfg, _xRelPath, _dicData):
    import pickle

    sFilePath = _xPrjCfg.GetAbsPath(_xRelPath).as_posix()
    SavePickle(sFilePath, _dicData)


# enddef

#######################################################################
# Load Pickel file from relative path to script path
def LoadPickleFromRelPath(_xPrjCfg, _xRelPath):
    import pickle

    sFilePath = _xPrjCfg.GetAbsPath(_xRelPath).as_posix()
    return LoadPickle(sFilePath)


# enddef

#######################################################################
# Save text file from relative path to script path
def LoadTextFromRelPath(_xPrjCfg, _xRelPath):

    sFilePath = _xPrjCfg.GetAbsPath(_xRelPath).as_posix()
    return LoadText(sFilePath)


# enddef

#######################################################################
# Save text file from relative path to script path
def SaveTextToRelPath(_xPrjCfg, _xRelPath, _sText):

    sFilePath = _xPrjCfg.GetAbsPath(_xRelPath).as_posix()
    SaveText(sFilePath, _sText)


# enddef
