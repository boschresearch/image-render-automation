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


####################################################################

xIterBar: tqdm = None


def _ScanStatus(sText: str):
    print(sText, flush=True)


# enddef


def _ScanIterInit(sText: str, iCount: int):
    global xIterBar
    xIterBar = tqdm(total=int(iCount), desc=sText, leave=True)


# enddef


def _ScanIterUpdate(iIncrement: int, bEnd: bool = False):
    global xIterBar
    if bEnd is True:
        xIterBar.close()
    else:
        xIterBar.update(int(iIncrement))
    # endif


# enddef


def RunScan(
    *,
    _sConfig: str,
    _sProdCfgFile: str,
    _sOutFile: Optional[str] = None,
    _sGroup: Optional[str] = None,
):
    try:
        xWs = CWorkspace()
        xPrj = xWs.Project(_sConfig)
        xProds = CProducts(_prjX=xPrj)

        pathProdCfg = anypath.MakeNormPath(_sProdCfgFile)
        if not pathProdCfg.is_absolute():
            pathProdCfg = xPrj.xConfig.pathLaunch / pathProdCfg
        # endif
        pathProdCfg = anypath.ProvideReadFilepathExt(pathProdCfg, [".ison", ".json", ".json5"])

        dicEx = xProds.FromFile(pathProdCfg, _bIgnoreGroupExceptions=True)
        if len(dicEx) > 0:
            print(f"There were errors while loading production configuration: {pathProdCfg}")
            print(dicEx)
        # endif

        print("Scanning for artefacts...")
        xProds.ScanArtefacts(
            _sGroupId=_sGroup,
            _funcStatus=_ScanStatus,
            _funcIterInit=_ScanIterInit,
            _funcIterUpdate=_ScanIterUpdate,
        )

        if _sOutFile is None:
            sFileId: str = xPrj.sId.replace("/", "_")
            if _sGroup is None:
                pathScan = xPrj.xConfig.pathOutput / f"file-scan-{sFileId}.pickle"
            else:
                pathScan = xPrj.xConfig.pathOutput / f"file-scan-{sFileId}-{_sGroup}.pickle"
            # endif
        else:
            pathScan = anypath.MakeNormPath(_sOutFile).absolute()
        # endif

        print("Storing file scan...")
        xProds.SerializeScan(pathScan)
        print(f"Artefact scan stored in file: {pathScan}")

    except Exception as xEx:
        xFinalEx = CAnyError_Message(sMsg="Error scanning products", xChildEx=xEx)
        raise RuntimeError(xFinalEx.ToString())
    # endtry


# enddef
