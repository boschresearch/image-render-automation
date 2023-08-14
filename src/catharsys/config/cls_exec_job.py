#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Author: Christian Perwass (CR/ADI2.1)
# <LICENSE id="Apache-2.0">
#
#   Image-Render Automation Functions module
#   Copyright 2023 Robert Bosch GmbH and its subsidiaries
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

from pathlib import Path
import copy
from typing import Optional
from anybase.cls_process_handler import CProcessHandler


##########################################################################################
# Base class for job configurations for different action classes
class CConfigExecJob:
    ######################################################################################
    def __init__(self, *, _iIdx: int, _sName: str, _sLabel: str, _pathConfig: Path, _dicConfig: dict):
        self._iIdx: int = _iIdx
        self._sName: str = _sName
        self._sLabel: str = _sLabel
        self._pathConfig: Path = _pathConfig
        self._dicConfig: dict = copy.deepcopy(_dicConfig)
        self._xProcHandler: CProcessHandler = CProcessHandler()

    # enddef

    @property
    def iIdx(self) -> int:
        return self._iIdx

    # enddef

    @property
    def sName(self) -> str:
        return self._sName

    # enddef

    @property
    def sLabel(self) -> str:
        return self._sLabel

    # enddef

    @property
    def pathConfig(self) -> Path:
        return self._pathConfig

    # enddef

    @property
    def dicConfig(self) -> dict:
        return self._dicConfig

    # enddef

    @property
    def xProcHandler(self) -> CProcessHandler:
        return self._xProcHandler

    # enddef


# endclass
