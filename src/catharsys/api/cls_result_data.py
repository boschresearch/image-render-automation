#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \cls_result_data.py
# Created Date: Tuesday, June 7th 2022, 4:37:55 pm
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

########################################################################################
# Base class for action result data
class CResultData:
    @property
    def sDti(self):
        return self._sDataDti

    @property
    def lWarnings(self):
        return self._lWarnings

    ####################################################################################
    def __init__(self, *, sDataDti: str):

        self._sDataDti: str = sDataDti
        self._lWarnings: list = []

    # enddef

    ##########################################################################
    def Process(self, **kwargs):
        pass

    # enddef


# endclass
