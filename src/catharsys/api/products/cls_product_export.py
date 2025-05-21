###
# Author: Christian Perwass (CR/ADI2.1)
# <LICENSE id="Apache-2.0">
#
#   Image-Render Automation Functions module
#   Copyright 2023 Robert Bosch GmbH and its subsidiaries
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

import os
import math
import shutil
import anybase
import anybase.file
import ison
from pathlib import Path
from dataclasses import dataclass

import numpy as np
import xtar
from xtar_ml import BBox3D, BBox3dClnDecoder, BBox3dClnEncoder, BBox3DCollection

# from anybase import file as anyfile
from anybase import path as anypath

from typing import Any, Callable

# from ison.util import data as isondata
from anybase import convert
# from anybase.cls_any_error import CAnyError, CAnyError_Message

# from catharsys.config.cls_project import CProjectConfig
# from catharsys.action.cls_actionfactory import CActionFactory
# from catharsys.action.cls_actionclass_executor import CActionClassExecutor
# from catharsys.config.cls_job import CConfigJob

from catharsys.api.cls_workspace import CWorkspace
from catharsys.api.products.cls_products import CProducts, CGroup
from catharsys.api.cls_project import CProject

os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"
import cv2

def _Status(sText: str):
    pass

def _IterInit(sText: str, iCount: int):
    pass

def _IterUpdate(iCount: int, bDone: bool):
    pass

@dataclass
class CGroupConfig:
    sId: str
    sName: str
    lValues: list[str]

# endclass

@dataclass
class CArtefactConfig:
    sArtType: str
    lDataType: list[str]
    lArtMainPath: list[str]
    lArtIterPath: list[str]
    sArtIterVarId: str
    sArtIterVarName: str
    sExportName: str
    dicMeta: dict[str, Any]

@dataclass
class CArtefactExport:
    sName: str
    lVarIds: list[str]
    lVarNames: list[str]
    lVarValues: list[list[str]]
    lDataType: list[str]
    lArtFilePaths: list[Path]
    lArtIdxLists: list[list[int]]
    lArtMissing: list[list[int]]
    dicMeta: dict[str, Any]

@dataclass
class CLabelExport:
    sName: str
    xBox3dCln: BBox3dClnEncoder


class CProductExport:

    def __init__(
        self, 
        _sConfigName: str, 
        _sGroupName: str,
        *,
        _sProdCfgFile: str | None = None,
        _funcStatus: Callable[[str], None] | None = None,
        _funcIterInit: Callable[[str, int], None] | None = None,
        _funcIterUpdate: Callable[[int, bool], None] | None = None,
    ) -> None:
        self._sConfigName: str = _sConfigName
        self._sGroupName: str = _sGroupName
        self._funcStatus: Callable[[str], None] = _funcStatus if _funcStatus is not None else _Status
        self._funcIterInit: Callable[[str, int], None] = _funcIterInit if _funcIterInit is not None else _IterInit
        self._funcIterUpdate: Callable[[int, bool], None] = _funcIterUpdate if _funcIterUpdate is not None else _IterUpdate
        self._bHasScan: bool = False
        self._pathScan: Path = Path("")
        self._dicExport: dict[str, CArtefactExport] = {}
        self._iExportItemCount: int = 0
        self._bHasMissingArtefacts: bool = False
        self._dicLabelExport: dict[str, CLabelExport] = {}

        self._xWs: CWorkspace = CWorkspace()
        self._xPrj: CProject = self._xWs.Project(_sConfigName)

        self._xProds = CProducts(_prjX=self._xPrj)

        self._pathProdCfg: Path
        if _sProdCfgFile is not None:
            self._pathProdCfg = anypath.MakeNormPath(_sProdCfgFile)
            if not self._pathProdCfg.is_absolute():
                self._pathProdCfg = self._xPrj.xConfig.pathLaunch / self._pathProdCfg
            # endif
            self._pathProdCfg = anypath.ProvideReadFilepathExt(self._pathProdCfg, [".ison", ".json", ".json5"])
        else:
            self._pathProdCfg = self._xPrj.xConfig.pathLaunch / "production.json5"
        # endif

        if not self._pathProdCfg.exists():
            raise RuntimeError(
                f"Production configuration not found at: {(self._pathProdCfg.as_posix())}"
            )
        # endif
    
        self._dicGrpEx: dict[str, str] = self._xProds.FromFile(self._pathProdCfg, _bIgnoreGroupExceptions=True)

        if self._sGroupName not in self._xProds.dicGroups:
            raise ValueError(
                f"Group '{self._sGroupName}' not found in production configuration: {self._pathProdCfg.as_posix()}"
            )
        # endif


    # enddef

    @property
    def dicGrpExceptions(self) -> dict[str, str]:
        return self._dicGrpEx
    # enddef

    @property
    def pathScan(self) -> Path:
        return self._pathScan
    # enddef

    @property
    def iExportItemCount(self) -> int:
        return self._iExportItemCount
    
    @property
    def bHasMissingArtefacts(self) -> bool:
        return self._bHasMissingArtefacts


    def ProvideProductScan(self, _sScanFile: str | Path | None = None) -> None:
        
        self._bHasScan = False

        if _sScanFile is None:
            self._funcStatus("Scanning for artefacts...")
            self._xProds.ScanArtefacts(
                _sGroupId=self._sGroupName,
                _funcStatus=self._funcStatus,
                _funcIterInit=self._funcIterInit,
                _funcIterUpdate=self._funcIterUpdate,
            )

            sFileId: str = self._xPrj.sId.replace("/", "_")
            self._pathScan = self._xPrj.xConfig.pathOutput / f"file-scan-{sFileId}-{self._sGroupName}.pickle"
            self._xProds.SerializeScan(self._pathScan)
            self._funcStatus(f"Scan file written to: {self._pathScan.as_posix()}")

        else:
            pathScan: Path = anypath.MakeNormPath(_sScanFile)
            if not pathScan.is_absolute():
                pathScan = self._xPrj.xConfig.pathLaunch / pathScan
            # endif
            pathScan = anypath.ProvideReadFilepathExt(pathScan, [".pickle"])
            if not pathScan.exists():
                raise RuntimeError(
                    f"Scan file not found at: {(pathScan.as_posix())}"
                )
            # endif
            self._pathScan = pathScan
            self._funcStatus(f"Loading scan file: {self._pathScan.as_posix()}")
            self._xProds.DeserializeScan(self._pathScan)
        # endif
        self._bHasScan = True
    # enddef


    def PrepareExport(self) -> None:
        
        if not self._bHasScan:
            raise RuntimeError("Artefact scan not available.")
        # endif

        self._dicExport = {}
        self._iExportItemCount = 0

        xGroup: CGroup = self._xProds.dicGroups[self._sGroupName]
        lGrpVarValues = xGroup.GetGroupVarValueLists()
        dicArtVarValueLists, dicArtVarsTypeList = xGroup.GetArtefactVarValues(lGrpVarValues)
        # dicArtVarLabelLists = xGroup.GetArtefactVarLabels(dicArtVarValueLists)

        if "production" in xGroup.xPathStruct.lPathVarIds:
            iProductionIndex = xGroup.xPathStruct.lPathVarIds.index("production")
            sProductionValue = lGrpVarValues[iProductionIndex][0]
        else:
            iProductionIndex = -1
            sProductionValue = ""
        # endif

        lGroupDimConfigs: list[CGroupConfig] = []
        for iIdx, sId in enumerate(xGroup.xPathStruct.lPathVarIds):
            if sId == "production":
                continue
            # endif
            sName: str = xGroup.xPathStruct.dicVars[sId].sName
            lGroupDimConfigs.append(CGroupConfig(sId, sName, lGrpVarValues[iIdx]))
        # endfor

        # Generate set of data types from artefact variables, by ignoring the last element, unless there is only one.
        # This assumes that the last element is typically the filename (frame).
        # Create a flat list of these types, with the corresponding path information and number of elements.
        lArtefactConfigs: list[CArtefactConfig] = []
        for sArtVarId, lArtVarValues in dicArtVarValueLists.items():
            lNameValueLists = lArtVarValues[:-1]
            lNameValueCounts = [len(lNameValueList) for lNameValueList in lNameValueLists]
            iValueListCount = len(lNameValueLists)
            lNameValueMod = [0] * iValueListCount
            for iIdx in range(iValueListCount):
                if iIdx < iValueListCount - 1:
                    lNameValueMod[iIdx] = math.prod(lNameValueCounts[iIdx + 1:])
                else:
                    lNameValueMod[iIdx] = 1
            # endfor

            iNameTotalCount = math.prod(lNameValueCounts)
            for iIdx in range(iNameTotalCount):
                lNameValues = []
                iValueRemIdx = iIdx
                for iValueListIdx, lNameValueList in enumerate(lNameValueLists):
                    iValueIdx = iValueRemIdx // lNameValueMod[iValueListIdx]
                    iValueRemIdx = iValueRemIdx % lNameValueMod[iValueListIdx]
                    lNameValues.append(lNameValueList[iValueIdx])
                # endfor
                sExportName = "-".join(lNameValues)
                xArtType = xGroup.dicArtTypes[sArtVarId]
                sArtIterVarId = xArtType.xPathStruct.lPathVarIds[-1]
                sArtIterVarName = xArtType.xPathStruct.dicVars[sArtIterVarId].sName
                
                lArtefactConfigs.append(CArtefactConfig(
                    sArtType=sArtVarId, 
                    lDataType=xArtType.lType,
                    lArtMainPath=lNameValues, 
                    lArtIterPath=lArtVarValues[-1], 
                    sArtIterVarId=sArtIterVarId,
                    sArtIterVarName=sArtIterVarName,
                    sExportName=sExportName,
                    dicMeta=xArtType.dicMeta if xArtType.dicMeta is not None else {},
                ))
            # endfor all names
        # endfor sArtVarId

        lCfgValueCounts = [len(xGroupConfig.lValues) for xGroupConfig in lGroupDimConfigs]
        iCfgValListCount = len(lCfgValueCounts)
        iCfgTotalCount = math.prod(lCfgValueCounts)
        lCfgValueMod = [0] * iCfgValListCount
        for iIdx in range(iCfgValListCount):
            if iIdx < iCfgValListCount - 1:
                lCfgValueMod[iIdx] = math.prod(lCfgValueCounts[iIdx + 1:])
            else:
                lCfgValueMod[iIdx] = 1
        # endfor

        lExportVarIds = [x.sId for x in lGroupDimConfigs]
        lExportVarNames = [x.sName for x in lGroupDimConfigs]
        lExportVarValues = [x.lValues for x in lGroupDimConfigs]
        for xArtCfg in lArtefactConfigs:
            self._dicExport[xArtCfg.sExportName] = CArtefactExport(
                sName=xArtCfg.sExportName,
                lVarIds=lExportVarIds + [xArtCfg.sArtIterVarId],
                lVarNames=lExportVarNames + [xArtCfg.sArtIterVarName],
                lVarValues=lExportVarValues + [xArtCfg.lArtIterPath],
                lDataType=xArtCfg.lDataType,
                lArtFilePaths=[],
                lArtIdxLists=[],
                lArtMissing=[],
                dicMeta=xArtCfg.dicMeta,
            )

        self._funcStatus(f"Found {len(lArtefactConfigs)} artefact types for {iCfgTotalCount} configurations.")
        self._funcIterInit("Collecting artefacts...", iCfgTotalCount)
        self._bHasMissingArtefacts = False
        for iIdx in range(iCfgTotalCount):
            self._funcIterUpdate(1, False)
            lCfgValues = []
            lCfgIndices = []
            iValueRemIdx = iIdx
            for iValueListIdx, iValueCount in enumerate(lCfgValueCounts):
                iValueIdx = iValueRemIdx // lCfgValueMod[iValueListIdx]
                iValueRemIdx = iValueRemIdx % lCfgValueMod[iValueListIdx]
                lCfgValues.append(lGroupDimConfigs[iValueListIdx].lValues[iValueIdx])
                lCfgIndices.append(iValueIdx)
            # endfor
            dicVars = {k.sId: v for k, v in zip(lGroupDimConfigs, lCfgValues)}
            
            dicProcFilters: dict = ison.Parser(dicVars).Process(xGroup.dicFilters)

            lExcFilters: list[list[str] | str | int | float | bool] = dicProcFilters.get("lExclude", [])
            lIncFilters: list[list[str] | str | int | float | bool] = dicProcFilters.get("lInclude", [])
            if not isinstance(lExcFilters, list):
                raise TypeError(f"Element 'lExclude' in 'mFilters' of production group '{self._sGroupName}' is not a list: {type(lExcFilters)}")
            # endif 
            if not isinstance(lIncFilters, list):
                raise TypeError(f"Element 'lInclude' in 'mFilters' of production group '{self._sGroupName}' is not a list: {type(lIncFilters)}")
            # endif
            bDoInclude = False
            if len(lIncFilters) == 0:
                bDoInclude = True
            else:
                for xIncFilter in lIncFilters:
                    if not isinstance(xIncFilter, list):
                        if convert.ToBool(xIncFilter):
                            bDoInclude = True
                            break
                        # endif
                    else:
                        if all((convert.ToBool(x) for x in xIncFilter)):
                            bDoInclude = True
                            break
                        # endif
                    # endif
                # endfor
            # endif

            if not bDoInclude:
                continue
            # endif
            bDoExclude = False
            if len(lExcFilters) == 0:
                bDoExclude = False
            else:
                for xExcFilter in lExcFilters:
                    if not isinstance(xExcFilter, list):
                        if convert.ToBool(xExcFilter):
                            bDoExclude = True
                            break
                        # endif
                    else:
                        if all((convert.ToBool(x) for x in xExcFilter)):
                            bDoExclude = True
                            break
                        # endif
                    # endif
                # endfor
            # endif 
            if bDoExclude:
                continue
            # endif

            if iProductionIndex >= 0:
                lCfgValues.insert(iProductionIndex, sProductionValue)
            # endif

            xNode = xGroup.GetGroupVarNode(lCfgValues)
            for xArtCfg in lArtefactConfigs:
                sArtType = xArtCfg.sArtType
                xExport = self._dicExport[xArtCfg.sExportName]

                for sArtIterIdx, sArtIterValue in enumerate(xArtCfg.lArtIterPath):
                    lArtPath: list[str] = xArtCfg.lArtMainPath + [sArtIterValue]
                    xArtNode = xGroup.GetArtVarNode(_xNode=xNode, _sArtType=sArtType, _lArtPath=lArtPath)
                    if xArtNode is None:
                        xExport.lArtMissing.append(lCfgIndices + [sArtIterIdx])
                        self._bHasMissingArtefacts = True
                        continue
                    # endif

                    xExport.lArtIdxLists.append(lCfgIndices + [sArtIterIdx])
                    xExport.lArtFilePaths.append(xArtNode.pathFS)
                # endfor artefact elements
            # endfor artefact types
            self._iExportItemCount += 1
        # endfor group configs
        self._funcIterUpdate(0, True)

        self._StoreMissingArtefacts()
    # enddef

    def _StoreMissingArtefacts(self, _sFilePath: str | Path | None = None) -> None:
        if _sFilePath is None:
            pathFile = self._xPrj.xConfig.pathOutput / f"export-missing-artefacts-{self._sConfigName}-{self._sGroupName}.json"
        else:
            pathFile = anypath.MakeNormPath(_sFilePath)
            if not pathFile.is_absolute():
                pathFile = self._xPrj.xConfig.pathOutput / pathFile
            # endif
        # endif

        if not self._bHasMissingArtefacts:
            if pathFile.exists():
                pathFile.unlink()
            # endif
            return
        # endif

        dicData: dict[str, Any] = {
            "iExportItemCount": self._iExportItemCount,
        }
        for xExport in self._dicExport.values():
            if len(xExport.lArtMissing) > 0:
                lValLists = []
                for lIdxList in xExport.lArtMissing:
                    lValues = [xExport.lVarValues[iIdx] for iIdx in lIdxList]
                    lValLists.append(lValues)
                # endfor

                dicData[xExport.sName] = {
                    "lVarIds": xExport.lVarIds,
                    "lVarNames": xExport.lVarNames,
                    "lMissing": lValLists,
                }
            # endif
        # endfor
        anybase.file.SaveJson(pathFile, dicData)
        self._funcStatus(f"The list of missing artefacts was written to: {pathFile.as_posix()}")
    # enddef

    def ExportArtefacts(
            self, 
            _sOutputPath: str | Path, 
            _iSamplesPerGroup: int = 1000, 
            _bOverwrite: bool = False, 
            _iMaxSamples: int = -1) -> None:
        if not self._bHasScan:
            raise RuntimeError("Artefact scan not available.")
        # endif

        pathXtar: Path = anypath.MakeNormPath(_sOutputPath)
        if not pathXtar.is_absolute():
            pathXtar = self._xPrj.xConfig.pathMain / pathXtar
        # endif
        if pathXtar.exists():
            if not pathXtar.is_dir():
                raise RuntimeError(f"Output path is not a directory: {pathXtar.as_posix()}")
            # endif
            if _bOverwrite:
                shutil.rmtree(pathXtar)
            else:
                raise RuntimeError(f"Output path already exists: {pathXtar.as_posix()}")
            # endif
        # endif
        pathXtar.mkdir(parents=True, exist_ok=True)

        lTypes: list[xtar.IOType] = []
        lMetaTypes: list[xtar.IOType] = []
        self._dicLabelExport = {}

        iElementCount = 0
        for xExport in self._dicExport.values():
            self._funcStatus(f"Prepare artefact export: {xExport.sName}")
            self._funcStatus(f"  Element Count: {len(xExport.lArtFilePaths)}")
            if len(xExport.lArtMissing) > 0:
                self._funcStatus(f"  Missing Count: {len(xExport.lArtMissing)}")

            if iElementCount == 0:
                iElementCount = len(xExport.lArtFilePaths)
            elif iElementCount != len(xExport.lArtFilePaths):
                self._funcStatus(f"  WARNING: Artefact export element count mismatch: {iElementCount} != {len(xExport.lArtFilePaths)}")
                self._funcStatus(f"  Ignoring artefact: {xExport.sName}")
                continue
            # endif

            if xExport.lDataType[0] == "image":
                sImgFormat = xExport.lDataType[1]
                if sImgFormat in ["png", "jpg", "jpeg", "bmp"]:
                    eImgFormat: xtar.EImageFormat | None = None
                    if sImgFormat == "png":
                        eImgFormat = xtar.EImageFormat.PNG
                    elif sImgFormat == "jpg" or sImgFormat == "jpeg":
                        eImgFormat = xtar.EImageFormat.JPEG
                    elif sImgFormat == "bmp":
                        eImgFormat = xtar.EImageFormat.BMP
                    # endif
                    lTypes.append(xtar.IOType(xtar.EDataType.IMAGE, xExport.sName, xtar.ImageWriterParams(eImgFormat)))
                    lMetaTypes.append(xtar.IOType(xtar.EDataType.JSON, xExport.sName, xtar.JsonWriterParams()))
                elif sImgFormat == "exr":
                    lTypes.append(xtar.IOType(xtar.EDataType.ARRAY, xExport.sName, xtar.ArrayWriterParams(zip_compression=True)))
                    lMetaTypes.append(xtar.IOType(xtar.EDataType.JSON, xExport.sName, xtar.JsonWriterParams()))
                else:
                    self._funcStatus(f"  WARNING: Unsupported image format: {sImgFormat}")
                    self._funcStatus(f"  Ignoring artefact: {xExport.sName}")
                    continue
                # endif

            elif xExport.lDataType[0] == "data":
                if xExport.lDataType[1] == "json":
                    lTypes.append(xtar.IOType(xtar.EDataType.JSON, xExport.sName, xtar.JsonWriterParams()))
                    lMetaTypes.append(xtar.IOType(xtar.EDataType.JSON, xExport.sName, xtar.JsonWriterParams()))
                else:
                    self._funcStatus(f"  WARNING: Unsupported data format: {xExport.lDataType[1]}")
                    self._funcStatus(f"  Ignoring artefact: {xExport.sName}")
                    continue
                # endif

            elif xExport.lDataType[0] == "label":
                if xExport.lDataType[1] != "json":
                    self._funcStatus(f"  WARNING: Unsupported label format: {xExport.lDataType[1]}")
                    self._funcStatus(f"  Ignoring artefact: {xExport.sName}")
                    continue
                # endif

                if "export" in xExport.dicMeta:
                    dicMetaExport: dict[str, Any] = xExport.dicMeta["export"]
                    if not isinstance(dicMetaExport, dict):
                        raise TypeError(f"Element 'export' in 'mMeta' of artefact '{xExport.sName}' is not a dictionary: {type(dicMetaExport)}")
                    
                    bBox3d: bool = convert.DictElementToBool(dicMetaExport, "bBox3d", False)
                    bBox2d: bool = convert.DictElementToBool(dicMetaExport, "bBox2d", False)
                    bIdealBox2d: bool = convert.DictElementToBool(dicMetaExport, "bIdealBox2d", False)
                    bCamera: bool = convert.DictElementToBool(dicMetaExport, "bCamera", False)
                    xBox3dCln: BBox3dClnEncoder | None = None
                    if bBox3d:
                        xBox3dCln = BBox3dClnEncoder(
                            content_id="label",
                            meta_data={},
                            has_props=True)
                        lTypes.extend(xBox3dCln.io_types)
                    # endif


                    
                    self._dicLabelExport

                       

            else:
                self._funcStatus(f"  WARNING: Unsupported format: {xExport.lDataType[0]}")
                self._funcStatus(f"  Ignoring artefact: {xExport.sName}")
                continue

            # endif
        # endfor

        for sExportName in self._lLabelExportNames:
            xExport = self._dicExport[sExportName]
            self._funcIterInit(f"Parsing label artefacts for '{sExportName}'...", len(xExport.lArtFilePaths))
            for iIdx, pathFile in enumerate(xExport.lArtFilePaths):
                if not pathFile.exists():
                    self._funcStatus(f"  WARNING: Missing artefact: {pathFile.as_posix()}")
                    continue
                # endif
                
            # endfor

        self._funcStatus(f"Exporting artefacts to: {pathXtar.as_posix()}")
        xWriter = xtar.ContiguousDatasetWriter(pathXtar, lTypes, samples_per_group=_iSamplesPerGroup, meta_writer_types=lMetaTypes)

        self._funcStatus("Writing meta data...")
        dicMeta = {}
        for xType in lMetaTypes:
            xExport = self._dicExport[xType.content_id]
            dicMeta.update({
                xType.content_id: {
                    "name": xExport.sName,
                    "var_ids": xExport.lVarIds,
                    "var_names": xExport.lVarNames,
                    "var_values": xExport.lVarValues,
                    "value_indices_per_sample": xExport.lArtIdxLists,
                }
            })
        # endfor meta
        xWriter.add_meta(0, **dicMeta)

        if _iMaxSamples > 0:
            iElementCount = min(iElementCount, _iMaxSamples)
        
        # self._funcStatus("Writing artefacts...")
        self._funcIterInit("Writing artefacts...", iElementCount)
        for iIdx in range(iElementCount):
            self._funcIterUpdate(1, False)
            dicData: dict[str, Any] = {}
            for xType in lTypes:
                xExport = self._dicExport[xType.content_id]
                if iIdx < len(xExport.lArtFilePaths):
                    # Export OpenEXR images as numpy arrays
                    if xExport.lDataType[0] == "image" and xExport.lDataType[1] == "exr":
                        dicData[xType.content_id] = self._Process_OpenExr(xExport.lArtFilePaths[iIdx])
                    else:
                        dicData[xType.content_id] = xExport.lArtFilePaths[iIdx]
                    # endif
                else:
                    print(f"  WARNING: Missing artefact: {xType.content_id}")
                # endif
            # endfor
            xWriter.add(**dicData)
        # endfor data
        self._funcIterUpdate(0, True)

        xWriter.flush()
        self._funcStatus(f"Exported {iElementCount} artefacts to: {pathXtar.as_posix()}")
    # enddef

    def _Process_OpenExr(self, _sFilePath: str | Path) -> np.ndarray:
        sFilepath = str(_sFilePath)
        imgData = cv2.imread(sFilepath, cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH | cv2.IMREAD_UNCHANGED)
        if imgData is None:
            self._funcStatus(f"  WARNING: Failed to read image: {sFilepath}")
            return np.array([])
        # endif

        if len(imgData.shape) > 2:
            # Flip order of color channel elements, as cv2 stores images as BGR and not RGB.
            if imgData.shape[2] == 4:
                imgData = imgData[:, :, [2, 1, 0, 3]]
            else:
                imgData = imgData[:, :, ::-1]
            # endif
        # endif
        return imgData
    # enddef

# endclass

