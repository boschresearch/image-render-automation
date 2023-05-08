#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \dev_api_ison.py
# Created Date: Friday, June 3rd 2022, 3:38:06 pm
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


import ison

dicData = {"__locals__": {"Hello": "World"}, "result": "Hello ${Hello}"}
xResult = ison.run.Run(xData=dicData, sResultKey="result")

print(xResult)
