#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /compositor.py
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


from anybase.cls_anycml import CAnyCML
from . import configcml_func_std


class CConfigCML(CAnyCML):
    def __init__(
        self,
        *,
        xPrjCfg,
        dicConstVars={},
        dicRefVars=None,
        sImportPath=None,
        dicRtVars=None,
        setRtVarsEval=None,
        xParser: "CConfigCML" = None
    ):
        super().__init__(
            dicConstVars,
            dicRefVars=dicRefVars,
            sImportPath=sImportPath,
            dicRtVars=dicRtVars,
            setRtVarsEval=setRtVarsEval,
            xParser=xParser,
        )

        configcml_func_std.SetProjectConfig(xPrjCfg)
        self.RegisterFunctionModule(configcml_func_std)

    # enddef


# endclass
