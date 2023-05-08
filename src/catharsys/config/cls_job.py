#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \cls_job.py
# Created Date: Tuesday, June 7th 2022, 1:57:27 pm
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

import copy
from typing import Optional

from ison.util.data import StripVarsFromData

from anybase import config

##########################################################################################
# Base class for job configurations for different action classes
class CConfigJob:
    @property
    def sDti(self) -> str:
        return self._sDti

    @property
    def dicData(self) -> dict:
        return self._dicData

    ######################################################################################
    def __init__(self, *, sDTI: str, dicData: Optional[dict] = None):

        self._sDti: str = None
        self._dicData: dict = None

        self._sDti = sDTI

        if dicData is not None:
            config.AssertConfigType(dicData, sDTI)
            self._dicData = dicData
        # endif

    # enddef

    ######################################################################################
    def GetResultData(self, **kwargs):
        pass

    # enddef

    ######################################################################################
    def ToDict(self, bStripVars: bool = True):

        if bStripVars is True:
            dicCfg = StripVarsFromData(self._dicData)
        else:
            dicCfg = copy.deepcopy(self._dicData)
        # endif

        return dicCfg

    # enddef


# endclass
