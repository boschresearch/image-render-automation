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

import ison

# from anybase import file as anyfile
from anybase import path as anypath

from typing import Optional

from ison.util import data as isondata
from anybase import assertion, convert, config
from anybase.cls_any_error import CAnyError, CAnyError_Message

from catharsys.config.cls_project import CProjectConfig
from catharsys.action.cls_actionfactory import CActionFactory
from catharsys.action.cls_actionclass_executor import CActionClassExecutor
from catharsys.config.cls_job import CConfigJob

from catharsys.api.cls_workspace import CWorkspace
from catharsys.api.products.cls_products import CProducts
from catharsys.api.products.cls_product_availability import CProductAvailability


####################################################################


def RunAnalysis(
    *,
    _sConfig: str,
    _sProdAnaCfgFile: str,
    _sScanFile: Optional[str] = None,
    _lProdAnaNames: Optional[list[str]] = None,
):
    try:
        xWs = CWorkspace()
        xPrj = xWs.Project(_sConfig)

        # #####################################################################
        # Load analysis configuration
        pathProdAnaCfg = anypath.MakeNormPath(_sProdAnaCfgFile)

        if not pathProdAnaCfg.is_absolute():
            pathProdAnaCfg = xPrj.xConfig.pathLaunch / pathProdAnaCfg
        # endif

        pathProdAnaCfgExt = anypath.ProvideReadFilepathExt(pathProdAnaCfg, [".ison", ".json", ".json5"])
        if pathProdAnaCfgExt is None:
            if len(pathProdAnaCfg.suffix) > 0:
                raise RuntimeError(f"Production analysis file not found: {(pathProdAnaCfg.as_posix())}")
            else:
                raise RuntimeError(
                    f"Production analysis file not found: {(pathProdAnaCfg.as_posix())}[.ison | .json | .json5]"
                )
            # endif

        else:
            pathProdAnaCfg = pathProdAnaCfgExt
        # endif

        dicFpVars = xPrj.xConfig.GetFilepathVarDict(pathProdAnaCfg)
        dicAnaCfg = config.Load(pathProdAnaCfg, sDTI="/catharsys/production/analyze:1.*")
        xParser = ison.Parser(dicFpVars)
        dicAnaCfg = xParser.Process(dicAnaCfg, sImportPath=pathProdAnaCfg.parent.as_posix())

        # #####################################################################
        # Load corresponding product configuration file
        sPathProdConfig = convert.DictElementToString(dicAnaCfg, "sPathProdConfig")

        xProds = CProducts(_prjX=xPrj)

        pathProdCfg = anypath.MakeNormPath(sPathProdConfig)
        if not pathProdCfg.is_absolute():
            pathProdCfg = xPrj.xConfig.pathLaunch / pathProdCfg
        # endif
        pathProdCfg = anypath.ProvideReadFilepathExt(pathProdCfg, [".ison", ".json", ".json5"])
        if not pathProdCfg.exists():
            raise RuntimeError(
                f"Production configuration not found as specified in analysis configuration: {(pathProdCfg.as_posix())}"
            )
        # endif

        dicEx = xProds.FromFile(pathProdCfg, _bIgnoreGroupExceptions=True)
        if len(dicEx) > 0:
            print(f"There were errors while loading production configuration: {pathProdCfg}")
            print(dicEx)
        # endif

        # #####################################################################
        # Load scan file
        if _sScanFile is None:
            pathScan = xPrj.xConfig.pathOutput / f"file-scan-{xPrj.sId}.pickle"
        else:
            pathScan = anypath.MakeNormPath(_sScanFile)
            if not pathScan.is_absolute():
                pathScan = xPrj.xConfig.pathLaunch / pathScan
            # endif
            pathScan = anypath.ProvideReadFilepathExt(pathScan, [".pickle"])
        # endif

        if not pathScan.exists() or not pathScan.is_file():
            raise RuntimeError(
                f"Scan file not found at: {(pathScan.as_posix())}\n"
                "You may want to run a file system scan with: \n"
                f"    cathy prod scan -c {_sConfig} -p {sPathProdConfig}\n"
            )
        # endif

        print(f"Loading artefacts scan from: {(pathScan.as_posix())}\n")
        xProds.DeserializeScan(pathScan)

        # #####################################################################
        # Run analysis
        lAnaMissing: list[dict] = dicAnaCfg.get("lAnalyzeMissing")
        if lAnaMissing is None:
            raise RuntimeError("Element 'lAnalyzeMissing' not found in production analysis configuration")
        # endif

        lAnaNames: list[str] = None
        if isinstance(_lProdAnaNames, list) and len(_lProdAnaNames) > 0:
            lAnaNames = _lProdAnaNames
        # endif

        for dicAna in lAnaMissing:
            sName: str = convert.DictElementToString(dicAna, "sName")
            if lAnaNames is not None and sName not in lAnaNames:
                continue
            # endif

            sGroupId: str = convert.DictElementToString(dicAna, "sGroupId")
            sGroupVarId: str = convert.DictElementToString(dicAna, "sGroupVarId")
            lArtTypeIds: list[str] = convert.DictElementToStringList(dicAna, "lArtTypeIds", lDefault=[])
            if len(lArtTypeIds) == 0:
                lArtTypeIds = None
            # endif

            sTitle = f"\nRunning analysis '{sName}':"
            print(sTitle)
            print("=" * len(sTitle))

            xGrp = xProds.dicGroups.get(sGroupId)
            if xGrp is None:
                raise RuntimeError(f"Group '{sGroupId}' not found in: {(pathProdCfg.as_posix())}")
            # endif

            lGrpVarValLists = xGrp.GetGroupVarValueLists()
            dicArtVarValLists, dicArtVarsTypeList = xGrp.GetArtefactVarValues(lGrpVarValLists)

            lExpGrpVarVals: list = dicAna.get("lGroupVarValues")
            if not isinstance(lExpGrpVarVals, list):
                raise RuntimeError("Element 'lGroupVarValues' must be a list")
            # endif

            lEffExpGrpVarVals: list = []
            for xVal in lExpGrpVarVals:
                if isinstance(xVal, list):
                    if len(xVal) == 2:
                        iFirst, iLast = xVal
                        if not isinstance(iFirst, int) or not isinstance(iLast, int):
                            raise RuntimeError(f"Expect both elements in range to be integers: {xVal}")
                        # endif
                        lEffExpGrpVarVals.extend(list(range(iFirst, iLast + 1)))
                    elif len(xVal) == 3:
                        iFirst, iLast, iStep = xVal
                        if not isinstance(iFirst, int) or not isinstance(iLast, int) or not isinstance(iStep, int):
                            raise RuntimeError(f"Expect all elements in range with step size to be integers: {xVal}")
                        # endif
                        lEffExpGrpVarVals.extend(list(range(iFirst, iLast + 1, iStep)))
                    else:
                        raise RuntimeError(f"Expect range element to have 2 or 3 integer elements: {xVal}")
                    # endif
                else:
                    lEffExpGrpVarVals.append(xVal)
                # endif
            # endfor

            if sGroupVarId not in xGrp.xPathStruct.lPathVarIds:
                raise RuntimeError(
                    f"Group variable '{sGroupVarId}' not found production configuration group '{sGroupId}'"
                )
            # endif

            iVarIdx = xGrp.xPathStruct.lPathVarIds.index(sGroupVarId)
            lGrpVarValLists[iVarIdx] = lEffExpGrpVarVals

            xProdAvail = CProductAvailability(
                _xGroup=xGrp, _lSelGrpVarValLists=lGrpVarValLists, _dicSelArtVarValLists=dicArtVarValLists
            )
            xProdAvail.Analyze()
            dicVarValMissing = xProdAvail.GetMissingArtefactsGroupVarValues(sGroupVarId, lArtTypeIds)

            dicPrint: dict = dicAna.get("mPrint")
            bPrintConcise: bool = False
            if isinstance(dicPrint, dict):
                bPrintConcise = convert.DictElementToBool(dicPrint, "bConcise", bDefault=False)

                xProdAvail.PrintMissingArtefactsGroupVarValues(
                    _sVarId=sGroupVarId,
                    _lArtTypeIds=lArtTypeIds,
                    _bConcise=bPrintConcise,
                    _dicMissing=dicVarValMissing,
                )
            # endif

            dicSave: dict = dicAna.get("mSave")
            if isinstance(dicSave, dict):
                sArtTypeName = "-".join(lArtTypeIds)
                pathMissing: Path = (
                    xPrj.xConfig.pathOutput / f"file-scan-missing-{xPrj.sId}-{sGroupVarId}-{sArtTypeName}.json"
                )
                sSavePath: str = convert.DictElementToString(dicSave, "sPath", sDefault=None, bDoRaise=False)
                if sSavePath is not None:
                    pathMissing = anypath.MakeNormPath(sSavePath).absolute()
                # endif

                iIndent: int = convert.DictElementToInt(dicSave, "iIndent", iDefault=-1)
                xProdAvail.SaveMissingArtefactsGroupVarValues(
                    _pathFile=pathMissing,
                    _sVarId=sGroupVarId,
                    _lArtTypeIds=lArtTypeIds,
                    _dicMissing=dicVarValMissing,
                    _iIndent=iIndent,
                )

                print(f"\nAnalysis saved to file: {(pathMissing.as_posix())}")
            # endif
        # endfor analysis dicts
    except Exception as xEx:
        xFinalEx = CAnyError_Message(sMsg="Error scanning products", xChildEx=xEx)
        raise RuntimeError(xFinalEx.ToString())
    # endtry


# enddef
