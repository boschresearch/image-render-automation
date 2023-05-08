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
#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /lsf.py
# Created Date: Tuesday, June 28th 2022, 8:42:05 am
# Created by: Christian Perwass (CR/AEC5)
# -----
# Copyright (c) 2022 Robert Bosch GmbH and its subsidiaries
#
# All rights reserved.
# -----
###

from pathlib import Path
import tempfile
import platform

from typing import Union
from anybase import assertion, shell
from anybase.cls_any_error import CAnyError_Message
import catharsys.plugins.std

################################################################################################
def ExecBSub(
    *, sCommands: str, bDoPrint: bool = False, bDoPrintOnError: bool = False
) -> Union[bool, list[str]]:

    # Only supported on Linux platforms
    if platform.system() != "Linux":
        raise CAnyError_Message(
            sMsg="Unsupported system '{}' for LSF job creation".format(
                platform.system()
            )
        )
    # endif

    ##################################################################################
    # Create a temporary file for the bsub commands
    pathFileBsub = None
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".bsub") as xFile:
        pathFileBsub = Path(xFile.name)
        xFile.write(sCommands)
    # endwith

    ##################################################################################
    # In the current VSCode version, the path is destroyed when running in a Jupyter notebook.
    # We need to recreate it here.
    # This also shouldn't do any harm when running from the command line (I hope).
    lCmds = [
        "export PATH=$PATH:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin",
        "source ~/.bashrc",
        'bsub < "{}"'.format(pathFileBsub.as_posix()),
    ]

    bOk, lStdOut = shell.ExecBashCmds(
        lCmds=lCmds,
        bDoPrintOnError=bDoPrintOnError,
        bDoPrint=bDoPrint,
        bReturnStdOut=True,
        sPrintPrefix=">> ",
    )

    # Delete temporary file with BSUB commands
    pathFileBsub.unlink()

    return bOk, lStdOut


# enddef
