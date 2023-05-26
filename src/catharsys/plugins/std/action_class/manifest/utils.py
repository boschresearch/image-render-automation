#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \utils.py
# Created Date: Thursday, May 25th 2023, 3:44:17 pm
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

import random
import numpy as np
from anybase import convert
from catharsys.util.cls_configcml import CConfigCML
import hashlib
from pathlib import Path


def ApplyConfigRandomSeed(
    _dicCfg: dict, *, _bApplyToConfig: bool = False, _sConfigFilename: str = None
):
    # if isinstance(_xParser, CConfigCML):
    #     lResult = _xParser.Process(_dicCfg, lProcessPaths=["iRandomSeed", "xRandomSeed"])
    #     if lResult[0] is not None:
    #         _dicCfg["iRandomSeed"] = lResult[0]["iRandomSeed"]
    #     # endif

    #     if lResult[1] is not None:
    #         _dicCfg["xRandomSeed"] = lResult[1]["xRandomSeed"]
    #     # endif
    # # endif

    xRandomSeed = convert.DictElementToInt(_dicCfg, "iRandomSeed", bDoRaise=False)
    if xRandomSeed is None:
        xRandomSeed = _dicCfg.get("xRandomSeed")
        if (
            xRandomSeed is not None
            and not isinstance(xRandomSeed, int)
            and not isinstance(xRandomSeed, float)
            and not isinstance(xRandomSeed, str)
        ):
            if _sConfigFilename is not None:
                raise RuntimeError(
                    f"Element 'xRandomSeed' in configuration '{_sConfigFilename}' must be integer, float or string but is: {xRandomSeed}"
                )
            else:
                raise RuntimeError(
                    f"Element 'xRandomSeed' in configuration must be integer, float or string but is: {xRandomSeed}"
                )
            # endif
        # endif
    # endif

    if xRandomSeed is not None:
        if isinstance(xRandomSeed, str):
            xRandomSeed = int.from_bytes(hashlib.sha256(bytes(xRandomSeed, "utf-8")).digest()[:4], "little")
            # xRandomSeed = hash(xRandomSeed)
        # endif

        if _bApplyToConfig is True:
            _dicCfg["xRandomSeed"] = xRandomSeed
        # endif

        # sName = Path(_sConfigFilename).name
        # sId = _dicCfg.get("sId")
        # print(f"{sName}: {sId}, {xRandomSeed}")

        # dicGlobals = _dicCfg.get("__globals__")
        # fY = dicGlobals.get("fY")
        # if fY is not None:
        #     print(f">> fY: {fY}")
        # # endif

        random.seed(xRandomSeed)
        np.random.seed(xRandomSeed)

        # if _xParser is not None:
        #     tResult = _xParser.ExecFunc("rand.seed", xRandomSeed)
        #     print(f">>> tResult: {tResult}")
        # # endif

        # fVal = random.uniform(-1, 1)
        # print(f">>> fVal: {fVal}\n")
    # endif

    return xRandomSeed


# enddef
