#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \ws_impl.py
# Created Date: Monday, June 13th 2022, 9:33:30 am
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

import re
from typing import Optional

from anybase import convert
from anybase.cls_any_error import CAnyError_Message


#########################################################################################################
def GetConfigOverride(
    sTrialFile: Optional[str] = None,
    sExecFile: Optional[str] = None,
    lActArgs: Optional[list[str]] = None,
) -> dict:

    dicConfigOverride: dict = {}

    if sTrialFile is not None:
        dicConfigOverride["sTrialFile"] = sTrialFile
    # endif

    if sExecFile is not None:
        dicConfigOverride["sExecFile"] = sExecFile
    # endif

    reActArg = re.compile(r"([a-zA-Z0-9.\-_\/]+)\s*=\s*([a-zA-Z0-9.\-_$%{}\/:]+)")

    if lActArgs is not None:
        for sArg in lActArgs:
            xMatch = reActArg.match(sArg)
            if xMatch is None:
                raise CAnyError_Message(
                    sMsg="Invalid action argument override: {}".format(sArg)
                )
            # endif
            sKey = xMatch.group(1)
            sValue = xMatch.group(2)
            if (
                sKey[0] == "i"
                and len(sKey) > 1
                and sKey[1].isupper()
                and "$" not in sValue
            ):
                xValue = convert.ToInt(sValue, bDoRaise=False)
                if xValue is None:
                    raise CAnyError_Message(
                        sMsg=f"Error converting value '{sValue}' for argument '{sKey}' to integer"
                    )
                # endif
            elif (
                sKey[0] == "b"
                and len(sKey) > 1
                and sKey[1].isupper()
                and "$" not in sValue
            ):
                xValue = convert.ToBool(sValue, bDoRaise=False)
                if xValue is None:
                    raise CAnyError_Message(
                        sMsg=f"Error converting value '{sValue}' for argument '{sKey}' to bool"
                    )
                # endif
            elif (
                sKey[0] == "f"
                and len(sKey) > 1
                and sKey[1].isupper()
                and "$" not in sValue
            ):
                xValue = convert.ToFloat(sValue, bDoRaise=False)
                if xValue is None:
                    raise CAnyError_Message(
                        sMsg=f"Error converting value '{sValue}' for argument '{sKey}' to float"
                    )
                # endif
            else:
                xValue = sValue
            # endif

            dicConfigOverride[sKey] = xValue
        # endfor
    # endif

    return dicConfigOverride


# enddef
