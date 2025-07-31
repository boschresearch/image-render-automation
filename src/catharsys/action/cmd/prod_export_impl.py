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

import re
from pathlib import Path
from tqdm import tqdm

# from anybase import file as anyfile
from anybase import path as anypath

from typing import Optional

from ison.util import data as isondata
from anybase import assertion, convert
from anybase.cls_any_error import CAnyError, CAnyError_Message

from catharsys.config.cls_project import CProjectConfig
from catharsys.action.cls_actionfactory import CActionFactory
from catharsys.action.cls_actionclass_executor import CActionClassExecutor
from catharsys.config.cls_job import CConfigJob

from catharsys.api.cls_workspace import CWorkspace
from catharsys.api.products.cls_products import CProducts
from catharsys.api.cls_project import CProject
from catharsys.api.products.cls_product_export import CProductExport

xIterBar: tqdm = None

def _Status(sText: str):
    print(sText, flush=True)


# enddef

def _IterInit(sText: str, iCount: int):
    global xIterBar
    xIterBar = tqdm(total=int(iCount), desc=sText, leave=True)


# enddef

def _IterUpdate(iIncrement: int, bEnd: bool = False):
    global xIterBar
    if bEnd is True:
        xIterBar.close()
    else:
        xIterBar.update(int(iIncrement))
    # endif


# enddef


def RunExport(
    *,
    _sConfigName: str,
    _sOutputPath: str,
    _sGroupName: str,
    _sProdCfgFile: str | None = None,
    _sScanFile: str | None = None,
    _iSamplesPerGroup: int = 1000,
    _bOverwrite: bool = False,
    _iMaxSamples: int = -1,
) -> None:
    """
    Run the export process for the given configuration and product configuration.

    Args:
        _sConfig (str): The configuration folder.
        _sProdCfg (str): The product configuration file.
        _sOutput (str): The output file.
        _sGroup (str): The group name.
        _sScanFile (str, optional): The scan file. Defaults to None.
        _iSamplesPerGroup (int, optional): The number of samples per group. Defaults to 1000.
        _bOverwrite (bool, optional): Whether to overwrite existing files. Defaults to False.
        _iMaxSamples (int, optional): The maximum number of samples. Defaults to -1.

    Raises:
        RuntimeError: If an error occurs during the export process.
    """
    # Initialize variables
    try:
        xExport = CProductExport(
            _sConfigName=_sConfigName,
            _sGroupName=_sGroupName,
            _sProdCfgFile=_sProdCfgFile,
            _funcStatus=_Status,
            _funcIterInit=_IterInit,
            _funcIterUpdate=_IterUpdate,
            )

        xExport.ProvideProductScan(_sScanFile=_sScanFile)
        xExport.PrepareExport()
        if xExport.bHasMissingArtefacts:
            response = input("There are missing artefacts. Do you want to continue the export? (y/N): ").strip().lower()
            if response != "y":
                print("Export cancelled by user due to missing artefacts.")
                return
            # endif
        # endif

        xExport.ExportArtefacts(_sOutputPath=_sOutputPath, _iSamplesPerGroup=_iSamplesPerGroup, _bOverwrite=_bOverwrite, _iMaxSamples=_iMaxSamples)

    except Exception as xEx:
        xFinalEx = CAnyError_Message(sMsg="Error exporting products", xChildEx=xEx)
        raise RuntimeError(xFinalEx.ToString())
    # endtry
# enddef


