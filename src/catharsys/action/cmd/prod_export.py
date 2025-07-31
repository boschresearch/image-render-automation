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
g_sCmdDesc = "Catharsys Products Export"


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
        default=[None],
        help="The production configuration file",
        required=False,
    )

    _parseArgs.add_argument(
        "-o",
        "--output",
        nargs=1,
        dest="output_path",
        default=[None],
        help="Give the output path for the xtar dataset",
        required=True,
    )

    _parseArgs.add_argument(
        "-g",
        "--group",
        nargs=1,
        dest="group",
        default=[None],
        help="Specify production group from production configuration to scan",
    )

    _parseArgs.add_argument(
        "-s",
        "--scan-file",
        nargs=1,
        dest="scan_file",
        default=[None],
        help="Specify the file system scan file to use. ",
    )

    _parseArgs.add_argument(
        "-n",
        "--samples-per-group",
        nargs=1,
        dest="samples_per_group",
        default=[1000],
        help="Specify the number of samples per group used by xtar. ",
    )

    _parseArgs.add_argument(
        "-x",
        "--overwrite",
        action="store_true",
        dest="overwrite",
        default=False,
        help="Overwrite existing xtar dataset.",
    )

    _parseArgs.add_argument(
        "--max-samples",
        nargs=1,
        dest="max_samples",
        default=[-1],
        help="Specify the maximum number of samples to export. ",
    )

# enddef


####################################################################
def RunCmd(_argsCmd, _lArgs):
    from catharsys.action.cmd import prod_export_impl as impl
    from catharsys.setup import args

    argsSubCmd = args.ParseCmdArgs(_argsCmd=_argsCmd, _lArgs=_lArgs, _funcAddArgs=AddArgParseArguments)

    impl.RunExport(
        _sConfigName=argsSubCmd.config_folder[0],
        _sOutputPath=argsSubCmd.output_path[0],
        _sGroupName=argsSubCmd.group[0],
        _sProdCfgFile=argsSubCmd.prod_config[0],
        _sScanFile=argsSubCmd.scan_file[0],
        _iSamplesPerGroup=int(argsSubCmd.samples_per_group[0]),
        _bOverwrite=argsSubCmd.overwrite,
        _iMaxSamples=int(argsSubCmd.max_samples[0]),
    )


# enddef
