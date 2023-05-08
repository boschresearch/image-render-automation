#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \start.py
# Created Date: Thursday, May 5th 2022, 11:51:37 am
# Author: Christian Perwass (CR/AEC5)
# <LICENSE id="Apache-2.0">
#
#   Image-Render Setup module
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

from catharsys.decs.decorator_log import logFunctionCall

g_sCmdDesc: str = "Runs Code Inspection related Catharsys commands"

# do not define this variable, it is the 'implicit interface' or hint,
# the command tree is not at the end
# no declaration of: g_parseArgs = None

####################################################################
@logFunctionCall
def AddArgParseArguments(_parseArgs):
    """parameter for cathy gui will be added into the parser"""

    _parseArgs.add_argument(
        "-f",
        "--find",
        dest="xslFindPattern",
        nargs="+",
        required=False,
        help="when using that interface for navigating, use find, the params builds an and, printing only a \
            subset on information use '-d, --display' option",
    )

    _parseArgs.add_argument(
        "-d",
        "--display",
        dest="lDisplayPattern",
        nargs="+",
        required=False,
        help="when using that interface for navigating, print only a \
            subset on information can be given: ID,FILE",
    )

    _parseArgs.add_argument(
        "-g",
        "--group",
        dest="lGroupnames",
        nargs=1,
        required=False,
        help="when navigating inside the entry points, restrict the results on entry point groups",
    )

    _parseArgs.add_argument(
        "-all",
        "--all",
        dest="bAllEntryPoints",
        action="store_true",
        default=False,
        help="when using that interface for navigating, use find and additionally --all option",
    )


# enddef


####################################################################
@logFunctionCall
def RunCmd(_argsCmd, _lArgs):
    from catharsys.util.cmd import inspect_impl as impl
    from catharsys.setup import args

    argsSubCmd = args.ParseCmdArgs(_argsCmd=_argsCmd, _lArgs=_lArgs, _funcAddArgs=AddArgParseArguments)

    sGroupName = None
    if argsSubCmd.lGroupnames is not None:
        sGroupName = argsSubCmd.lGroupnames[0]

    lDisplayPattern = None
    if argsSubCmd.lDisplayPattern is not None:
        lDisplayPattern = argsSubCmd.lDisplayPattern

    xslFindPattern = ""
    bFindAll = False
    if argsSubCmd.xslFindPattern is not None:
        xslFindPattern = argsSubCmd.xslFindPattern
    elif argsSubCmd.bAllEntryPoints is not None:
        bFindAll = True

    impl.Run_Nav(
        _bFindAll=bFindAll,
        _sGroupName=sGroupName,
        _lDisplayPattern=lDisplayPattern,
        _xslFindPattern=xslFindPattern,
    )


# enddef
