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
g_sCmdDesc = "Catharsys Products Scan"


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
        "--prod-cfg",
        nargs=1,
        dest="prod_config",
        # default=[None],
        help="The production configuration file",
        required=True,
    )

    _parseArgs.add_argument(
        "-o",
        "--output",
        nargs=1,
        dest="output_file",
        default=[None],
        help="Overrides the automatically created output filename",
    )

    _parseArgs.add_argument(
        "-g",
        "--group",
        nargs=1,
        dest="group",
        default=[None],
        help="Specify production group from production configuration to scan",
    )


# enddef


####################################################################
def RunCmd(_argsCmd, _lArgs):
    from catharsys.action.cmd import prod_scan_impl as impl
    from catharsys.setup import args

    argsSubCmd = args.ParseCmdArgs(_argsCmd=_argsCmd, _lArgs=_lArgs, _funcAddArgs=AddArgParseArguments)

    impl.RunScan(
        _sConfig=argsSubCmd.config_folder[0],
        _sProdCfgFile=argsSubCmd.prod_config[0],
        _sOutFile=argsSubCmd.output_file[0],
        _sGroup=argsSubCmd.group[0],
    )


# enddef
