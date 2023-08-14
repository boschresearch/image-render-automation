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

from typing import Union, Tuple, Optional
from anybase import assertion, shell
from anybase.cls_process_handler import CProcessHandler
from anybase.cls_any_error import CAnyError_Message
import catharsys.plugins.std
from catharsys.config.cls_exec_lsf import CConfigExecLsf


################################################################################################
def ExecBSub(
    *,
    sCommands: str,
    bDoPrint: bool = False,
    bDoPrintOnError: bool = False,
    xProcHandler: Optional[CProcessHandler] = None,
) -> Tuple[bool, list[str]]:
    # Only supported on Linux platforms
    if platform.system() != "Linux":
        raise CAnyError_Message(sMsg="Unsupported system '{}' for LSF job creation".format(platform.system()))
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
        xProcHandler=xProcHandler,
    )

    # Delete temporary file with BSUB commands
    pathFileBsub.unlink()

    return bOk, lStdOut


# enddef


# #################################################################################################
def Execute(
    *,
    _sJobName: str,
    _xCfgExecLsf: CConfigExecLsf,
    _sScript: str,
    _bDoPrint: bool = True,
    _bDoPrintOnError: bool = True,
    _xProcHandler: Optional[CProcessHandler] = None,
) -> Tuple[bool, list[str]]:
    if len(_xCfgExecLsf.lModules) > 0:
        sSetLoadModules = "module load {0}".format(" ".join(_xCfgExecLsf.lModules))
    else:
        sSetLoadModules = ""
    # endif

    if _xCfgExecLsf.iJobMemReqGb == 0:
        sSetMemReq = ""
    else:
        sSetMemReq = f"#BSUB -M {_xCfgExecLsf.iJobMemReqGb}G"
    # endif

    if _xCfgExecLsf.iJobMaxTime == 0:
        sSetJobMaxTime = ""
    else:
        sSetJobMaxTime = f"#BSUB -W {_xCfgExecLsf.iJobMaxTime}"
    # endif

    if _xCfgExecLsf.iJobGpuCores > 0:
        if _xCfgExecLsf.bIsLsbGpuNewSyntax is False:
            sSetGpuCount = f'#BSUB -R "rusage[ngpus_excl_p={_xCfgExecLsf.iJobGpuCores}]"'
        else:
            sSetGpuCount = f'#BSUB -gpu "num={_xCfgExecLsf.iJobGpuCores}/task:mode=exclusive_process"'
        # endif
    else:
        sSetGpuCount = ""
    # endif

    if _xCfgExecLsf.sJobQueue is None:
        sSetJobQueue = ""
    else:
        sSetJobQueue = f"#BSUB -q {_xCfgExecLsf.sJobQueue}"
    # endif

    if len(_xCfgExecLsf.lJobHosts) == 0:
        sSetJobHosts = ""
    else:
        sHostList = " ".join(_xCfgExecLsf.lJobHosts)
        sSetJobHosts = f"#BSUB -m {sHostList}"
    # endif

    if len(_xCfgExecLsf.lJobExcludeHosts) == 0:
        sSetJobExcludeHosts = ""
    else:
        lCommands = [f"hname!='{x}'" for x in _xCfgExecLsf.lJobExcludeHosts]
        sCommand = " && ".join(lCommands)
        sSetJobExcludeHosts = f'#BSUB -R"{sCommand}"'
    # endif

    sBsubScript = f"""
        # ####################################
        # #BSUB Settings

        #BSUB -J {_sJobName}
        #BSUB -o lsf/%J/stdout.txt
        #BSUB -e lsf/%J/stderr.txt
        {sSetJobMaxTime}
        {sSetJobQueue}
        {sSetGpuCount}
        {sSetMemReq}
        {sSetJobHosts}
        {sSetJobExcludeHosts}

        module purge
        {sSetLoadModules}

        # ####################################
        # Script to execute
        {_sScript}
    """

    return ExecBSub(
        sCommands=sBsubScript, bDoPrint=_bDoPrint, bDoPrintOnError=_bDoPrintOnError, xProcHandler=_xProcHandler
    )


# enddef
