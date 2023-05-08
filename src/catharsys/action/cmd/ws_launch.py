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

from anybase.dec.cls_const_keyword_namespace import constKeywordNamespace


@constKeywordNamespace
class NsKeys:
    script_args: str
    iDebugPort: str
    fDebugTimeout: str
    bSkipAction: str
    bShowGui: str


# endclass


# end class
g_sCmdDesc = "Launch Catharsys Action"


####################################################################
def AddArgParseArguments(_parseArgs):

    _parseArgs.add_argument(
        "-c",
        "--config",
        nargs=1,
        dest="config_folder",
        default=[None],
        help=(
            "The config folder where the launch file is located. "
            "Assumes that './config/[config folder]/launch[.json, .json5, .ison]' exists."
        ),
    )

    _parseArgs.add_argument(
        "-a",
        "--action",
        nargs=1,
        dest="action",
        default=[None],
        help="The action to execute",
    )

    _parseArgs.add_argument(
        "-l",
        "--launch",
        nargs=1,
        dest="launch_file",
        default=[None],
        help="Overrides the default launch file basename 'launch' (no extension)",
    )

    _parseArgs.add_argument(
        "-t",
        "--trial",
        nargs=1,
        dest="trial_file",
        default=[None],
        help="Overrides the trial file basename (no extension) from what is specified in launch file",
    )

    _parseArgs.add_argument(
        "-e",
        "--exec",
        nargs=1,
        dest="exec_file",
        default=[None],
        help="Overrides the execution file basename (no extension) from what is specified in launch file",
    )

    _parseArgs.add_argument(
        "-v",
        "--vars",
        nargs="*",
        dest="actargs",
        default=None,
        help="""\
             Overrides/sets arbitrary parameters specified in the launch file.
             Each element must be of the form '[parameter name]=[value]'.
             The value elements can also contain variable references in the form '${[variable name]}'
            """,
    )

    # calling cathy with e.g:  --script-vars dbg-port=portNumder option2=val2
    # every argument after --script-vars wil be split up and creates an
    # arg-pair '-option val' afterwards for the following script
    _parseArgs.add_argument(
        "-s",
        "--script-vars",
        nargs="*",
        dest=NsKeys.script_args,
        default=None,
        help="""\
             defines the arguments that will be passed to the script
             Each element must be of the form '[parameter_name/cmd_name]=[value]'.
             The value elements will be given to the script as '-cmd_name value'
            """,
    )

    _parseArgs.add_argument(
        "-p",
        "--path",
        nargs=1,
        dest="workspace_path",
        default=[None],
        help="The path to the workspace. Defaults to the current working directory.",
    )

    _parseArgs.add_argument(
        "--launch-file-path",
        nargs=1,
        dest="launch_path",
        default=[None],
        help="The path to the launch file to use. When this is specified, the arguments '--path' and '--config' are ignored.",
    )

    _parseArgs.add_argument(
        "--config-only",
        dest="config_only",
        action="store_true",
        default=False,
        help="Only create the action job configuration.",
    )

    _parseArgs.add_argument(
        "--config-vars",
        dest="include_config_vars",
        action="store_true",
        default=False,
        help="When '--config-only' is selected, adds also the local variables of the job config to the output.",
    )

    _parseArgs.add_argument(
        "--debug-port",
        nargs=1,
        dest="debug_port",
        default=[None],
        help="If a debug port is specified, the action breaks and waits for a debugger to attach at the given port.",
    )

    _parseArgs.add_argument(
        "--debug-timeout",
        nargs=1,
        dest="debug_timeout",
        default=[None],
        help="The time in seconds for how long to wait for the debug port to be available.",
    )

    _parseArgs.add_argument(
        "--debug-skip-action",
        dest="debug_skip_action",
        action="store_true",
        default=False,
        help=(
            "If debugging, skip the action. This can be useful when starting Blender with GUI (--action-gui), "
            "which is equivalent to using the 'cathy blender debug' command."
        ),
    )

    _parseArgs.add_argument(
        "--action-gui",
        dest="action_gui",
        action="store_true",
        default=False,
        help="If the action has a GUI, then show it. By default no GUI is shown.",
    )


# enddef


####################################################################
def RunCmd(_argsCmd, _lArgs):
    from catharsys.action.cmd import ws_launch_impl as impl
    from catharsys.setup import args

    argsSubCmd = args.ParseCmdArgs(_argsCmd=_argsCmd, _lArgs=_lArgs, _funcAddArgs=AddArgParseArguments)

    impl.RunLaunch(
        sAction=argsSubCmd.action[0],
        sFileBasenameLaunch=argsSubCmd.launch_file[0],
        sTrialFile=argsSubCmd.trial_file[0],
        sExecFile=argsSubCmd.exec_file[0],
        lActArgs=argsSubCmd.actargs,
        lScriptArgs=argsSubCmd.script_args,
        sFolderConfig=argsSubCmd.config_folder[0],
        sPathWorkspace=argsSubCmd.workspace_path[0],
        sPathLaunch=argsSubCmd.launch_path[0],
        sDebugPort=argsSubCmd.debug_port[0],
        sDebugTimeout=argsSubCmd.debug_timeout[0],
        bDebugSkipAction=argsSubCmd.debug_skip_action,
        bShowActionGui=argsSubCmd.action_gui,
        bConfigOnly=argsSubCmd.config_only,
        bIncludeConfigVars=argsSubCmd.include_config_vars,
    )


# enddef
