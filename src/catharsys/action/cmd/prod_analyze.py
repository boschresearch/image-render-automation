#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \actions\launch.py
# Author: Christian Perwass (CR/ADI2.1)
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


# end class
g_sCmdDesc = "Catharsys Products Analysis"


####################################################################
def AddArgParseArguments(_parseArgs):
    _parseArgs.add_argument(
        "-c",
        "--config",
        nargs=1,
        dest="config_folder",
        # default=[None],
        help=(
            "The config folder where the launch file is located. "
            "Assumes that './config/[config folder]/launch[.json, .json5, .ison]' exists."
        ),
        required=True,
    )

    _parseArgs.add_argument(
        "-p",
        "--prod-ana",
        nargs=1,
        dest="prod_ana_config",
        help="The production analysis configuration file",
        required=True,
    )

    _parseArgs.add_argument(
        "-s",
        "--scan-file",
        nargs=1,
        dest="scan_file",
        default=[None],
        help="Specify the file system scan file to use",
    )

    _parseArgs.add_argument(
        "-n",
        "--names",
        nargs="*",
        dest="ana_names",
        default=[],
        help="Analysis names to process. By default, all analysis configurations are processed.",
    )


# enddef


####################################################################
def RunCmd(_argsCmd, _lArgs):
    from catharsys.action.cmd import prod_analyze_impl as impl
    from catharsys.setup import args

    argsSubCmd = args.ParseCmdArgs(_argsCmd=_argsCmd, _lArgs=_lArgs, _funcAddArgs=AddArgParseArguments)

    impl.RunAnalysis(
        _sConfig=argsSubCmd.config_folder[0],
        _sProdAnaCfgFile=argsSubCmd.prod_ana_config[0],
        _sScanFile=argsSubCmd.scan_file[0],
        _lProdAnaNames=argsSubCmd.ana_names,
    )


# enddef
