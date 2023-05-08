#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /exception.py
# Created Date: Thursday, October 22nd 2020, 3:11:51 pm
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


#######################################################################
# Print Exception
def Print(_xEx, bPrintTrace=True):

    import traceback

    print("")
    print("===================================================================")
    print("EXCEPTION ({0})".format(type(_xEx)))
    print(_xEx)
    if bPrintTrace is True:
        print("")
        traceback.print_exception(type(_xEx), _xEx, _xEx.__traceback__)
    # endif
    print("===================================================================")
    print("")


# enddef
