#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \cls_display.py
# Created Date: Wednesday, June 8th 2022, 9:02:00 am
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

from typing import Optional, Union, ForwardRef
from anybase import assertion, plugin
from catharsys.api import CResultData
from .cls_htmlpage import CHtmlPage

THtmlRender = ForwardRef("HtmlRender")


########################################################################################
def RenderActionResultData(_xData: CResultData, *, sRenderLib: str):
    assertion.FuncArgTypes()

    epRenderer = plugin.SelectEntryPointFromDti(
        sGroup=f"catharsys.html.render.{sRenderLib}",
        sTrgDti=_xData.sDti,
        sTypeDesc=f"catharsys '{sRenderLib}' html render class",
    )

    classRenderer = epRenderer.load()
    return classRenderer(_xData)


# enddef


########################################################################################
class CHtmlRender(CHtmlPage):
    @property
    def sRenderLib(self):
        return self._sRenderLib

    ####################################################################################
    def __init__(
        self,
        *,
        xHtmlPage: Union[CHtmlPage, THtmlRender, None] = None,
        sRenderLib: str = "std",
    ):

        super().__init__(xHtmlPage)

        if isinstance(xHtmlPage, CHtmlRender):
            self._sRenderLib = xHtmlPage.sRenderLib
        else:
            self._sRenderLib: str = sRenderLib
        # endif

    # enddef

    ####################################################################################
    def ActionResultData(self, _xData: CResultData):
        return RenderActionResultData(_xData, sRenderLib=self._sRenderLib)

    # enddef

    ####################################################################################
    def Data(self, _xData, **kwargs):

        if isinstance(_xData, CResultData):
            xDisp = self.ActionResultData(_xData)
            # xDisp.Draw(**kwargs)
            # self.Markdown(xDisp)

        else:
            self.Text(
                "WARNING: Cannot display data objects of type '{}'".format(
                    str(type(_xData))
                )
            )
        # endif

    # enddef


# endclass
