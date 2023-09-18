#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /path.py
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

import os
from pathlib import Path

# Make all symbols of anybase.config available as cathy.config symbols.
# This enables a later overwriting of function or addition of new functions.
# It's like class derivation.
from anybase.path import *
from . import version


#################################################################################################################
# This functions copies the creation of the cath user path from catharsys.setup.util, as that module
# is not available in a Blender context.
def GetCathUserPath(*, _bCheckExists: bool = False) -> Path:
    sCondaEnvName = os.environ.get("CONDA_DEFAULT_ENV")
    if sCondaEnvName is None:
        raise RuntimeError("Conda environment name system environment variable not set")
    # endif

    pathUser = Path.home() / ".catharsys" / sCondaEnvName / version.MajorMinorAsString()
    if _bCheckExists is True and not pathUser.exists():
        raise RuntimeError(f"Catharsys user path does not exist: {(pathUser.as_posix())}")
    # endif

    return pathUser


# enddef


