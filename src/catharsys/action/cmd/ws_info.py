#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \actions\launch.py
# Created Date: Tuesday, August 10th 2021, 9:31:09 am
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


g_sCmdDesc = "Catharsys Workspace Info"


####################################################################
def AddArgParseArguments(_parseArgs):

    _parseArgs.add_argument(
        "-l", "--launch", nargs=1, dest="launch_file", default=[None]
    )
    _parseArgs.add_argument("--path", nargs=1, dest="workspace_path", default=[None])


# enddef


#####################################################################
def RunCmd(_argsCmd, _lArgs):

    from . import ws_info_impl as impl
    from catharsys.setup import args

    argsSubCmd = args.ParseCmdArgs(_argsCmd=_argsCmd, _lArgs=_lArgs, _funcAddArgs=AddArgParseArguments)

    impl.Info(
        sPathWorkspace=argsSubCmd.workspace_path[0],
        sFileBasenameLaunch=argsSubCmd.launch_file[0],
    )


# enddef
