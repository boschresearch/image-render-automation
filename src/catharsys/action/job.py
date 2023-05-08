#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \job.py
# Created Date: Friday, May 6th 2022, 2:17:14 pm
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

from importlib import metadata

from anybase import plugin
from catharsys.util import config
from anybase.cls_any_error import CAnyError, CAnyError_Message, CAnyError_TaskMessage

from catharsys.decs.decorator_log import logFunctionCall

###############################################################################
# Start a job based on a configuration file
@logFunctionCall
def Start(*, xPrjCfg, dicExec, dicArgs):
    """Start a job

    Parameters
    ----------
    xPrjCfg : _type_
        _description_
    dicExec : _type_
        _description_
    dicArgs : _type_
        _description_

    Raises
    ------
    CAnyError_Message
        _description_
    """
    try:
        sExecFile = "?"
        if isinstance(dicExec, dict):
            sExecFile = config.GetDictValue(dicExec, "__locals__/filepath", str, bOptional=True, bAllowKeyPath=True)
        else:
            raise RuntimeError("Argument 'dicExec' of invalid type")
        # endif

        sTrgDti = dicExec.get("sDTI")
        if not isinstance(sTrgDti, str):
            raise CAnyError_Message(sMsg=f"Execution configuration has no element 'sDTI' in file: {sExecFile}")
        # endif

        try:
            epExec = plugin.SelectEntryPointFromDti(
                sGroup="catharsys.execute",
                sTrgDti=sTrgDti,
                sTypeDesc="catharsys execution function",
            )
            modExec = epExec.load()
        except Exception as xEx:
            raise CAnyError_Message(
                sMsg=f"Error loading executor for execution configuration: {sExecFile}", xChildEx=xEx
            )
        # endtry

        if not hasattr(modExec, "StartJob"):
            raise CAnyError_Message(sMsg="Execution module has no function 'StartJob()': {}".format(modExec.__file__))
        # endif

        try:
            modExec.StartJob(xPrjCfg=xPrjCfg, dicExec=dicExec, dicArgs=dicArgs)
        except Exception as xEx:
            raise CAnyError_Message(
                sMsg="Error running job executor in module: {}".format(modExec.__file__),
                xChildEx=xEx,
            )
        # endif
    except Exception as xEx:
        raise CAnyError_TaskMessage(
            sTask="Job execution",
            sMsg="Error starting job of type '{}'".format(sTrgDti),
            xChildEx=xEx,
        )
    # endtry


# enddef


# if __name__ == "__main__":
#     dicExec = {
#         "sDTI": "/catharsys/exec/blender/std:2.1"
#     }

#     try:
#         Start(dicExec=dicExec)
#     except Exception as xEx:
#         CAnyError.Print(xEx, bTraceback=False)
#     # endtry
# # endif
