#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \cls_anyexcept.py
# Created Date: Friday, March 19th 2021, 9:03:02 am
# Author: Christian Perwass (CR/AEC5)
# <LICENSE id="Apache-2.0">
#
#   Image-Render Base Functions module
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

from catharsys.util.cls_entrypoint_information import CEntrypointInformation
from catharsys.decs.decorator_log import logFunctionCall


def EntryPoint(
    f_entryPointType: CEntrypointInformation.EEntryType, *, clsInterfaceDoc=None
):
    """this decorator should be used to specify the type of entry point
    --- Usage:
    from catharsys.decs.decorator_ep import EntryPoint
    from catharsys.util.cls_entrypoint_information import CEntrypointInformation

    @paramclass
    class CDeltaRotationEulerParams:
        sDTI: str = (
            paramclass.HINT(sHint="entry point identification"),
            paramclass.REQUIRED("blender/modify/object/delta-rotation-euler:1"),
        )
        sType: str = None
        sMode: str = paramclass.OPTIONS(["INIT", "FRAME_UPDATE"], xDefault="INIT")
        sUnit: str = paramclass.OPTIONS(["deg", "rad"], xDefault="rad")
        sFrame: str = paramclass.OPTIONS(["world", "local"], xDefault="local")
        xValue: list = paramclass.REQUIRED([float, float, float])

    @EntryPoint(
        CEntrypointInformation.EEntryType.MODIFIER,
        CDeltaRotationEulerParams
        )

    def modObjectInSpecialWay( *args, **kwargs ):
        # do magic things
        pass | return values
    """

    def decorator(wrappedFunc):
        # called during import time (only once, even if imported by several modules in complex python applications)
        # print(f"decEntryPoint enters: {wrappedFunc.__name__} for {f_entryPointType.name}")
        CEntrypointInformation.AppendFuncion(
            f_entryPointType, wrappedFunc, clsInterfaceDoc=clsInterfaceDoc
        )
        return logFunctionCall(wrappedFunc)

    return decorator
