#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \cathy\cls_cfg_exec.py
# Created Date: Monday, April 26th 2021, 10:05:56 am
# Author: Christian Perwass (CR/AEC5)
# <LICENSE id="Apache-2.0">
#
#   Image-Render Standard Actions module
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

import catharsys.util.config as cathcfg


class CConfigExecLsf:
    def __init__(self, _dicExec):
        self._lModules: list[str] = None
        self._iJobGpuCores: int = None
        self._iJobMaxTime: int = None
        self._sJobQueue: str = None
        self._iLsbGpuNewSyntax: int = None
        self._iJobMemReqGb: int = None
        self._lJobExcludeHosts: list[str] = None
        self._lJobHosts: list[str] = None

        cathcfg.StoreDictValuesInObject(
            self,
            _dicExec,
            [
                ("lModules", list, []),
                ("iJobGpuCores", int, 1),
                ("iJobMaxTime", int, 0),
                ("sJobQueue", str, None, True),
                ("iLsbGpuNewSyntax", int, 0),
                ("iJobMemReqGb", int, 0),
                ("lJobExcludeHosts", list, []),
                ("lJobHosts", list, []),
            ],
            sTrgAttributePrefix="_",
            sWhere="LSF configuration",
        )

    # enddef

    @property
    def lModules(self) -> list[str]:
        return self._lModules

    @property
    def iJobGpuCores(self) -> int:
        return self._iJobGpuCores

    @property
    def iJobMaxTime(self) -> int:
        return self._iJobMaxTime

    @property
    def sJobQueue(self) -> str:
        return self._sJobQueue

    @property
    def bIsLsbGpuNewSyntax(self) -> bool:
        return self._iLsbGpuNewSyntax != 0

    @property
    def iJobMemReqGb(self) -> int:
        return self._iJobMemReqGb

    @property
    def lJobExcludeHosts(self) -> list[str]:
        return self._lJobExcludeHosts

    @property
    def lJobHosts(self) -> list[str]:
        return self._lJobHosts


# endclass
