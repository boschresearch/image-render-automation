# ##################################################################
# Export catharsys production to xtar format
# ##################################################################
import os
import numpy as np
from tqdm import tqdm
import shutil
import xtar
import xtar_ml
import ison
import math
from pathlib import Path
from dataclasses import dataclass
from catharsys.api.products.cls_node import CNode
from catharsys.api.products.cls_products import CProducts, CGroup
from catharsys.api.cls_project import CProject
from catharsys.config.cls_project import CProjectConfig
# from catharsys.config.cls_launch import CConfigLaunch
from anybase import convert
# need to enable OpenExr explicitly
os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"
import cv2


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


@dataclass
class CMissingArtefact:
    sArtType: str
    lGrpPath: list[str]
    lArtPath: list[str]
    sExportName: str

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



def _scan_status(sText: str) -> None:
    print(sText)


def main():
    pathMain = Path.cwd()
    sConfigName = "crs-vehicle"
    sGrpId = "export_xtar"

    xConfig = CProjectConfig()
    xConfig.FromConfigName(xPathMain=pathMain, sConfigName=sConfigName)
    xProject = CProject(xConfig)
    xProducts = CProducts(_prjX=xProject)

    pathProdCfg = xConfig.pathLaunch / "production.json5"
    dicExceptions = xProducts.FromFile(pathProdCfg)
    xProducts.ScanArtefacts(_sGroupId=sGrpId, _funcStatus=_scan_status)

    # print("Group names:")
    # for sKey, sName in xProducts.dicGroupKeyNames.items():
    #     print(f"  {sKey}: {sName}")

    xGroup: CGroup = xProducts.dicGroups[sGrpId]

    # print(f"dicArtTypes: {xGroup.dicArtTypes}")
    # print(f"dicVarValues: {xGroup.dicVarValues}")
    # print(f"lCommonArtVarIds: {xGroup.lCommonArtVarIds}")
    # print(f"lPathVarIds: {xGroup.xPathStruct.lPathVarIds}")

    lGrpVarValues = xGroup.GetGroupVarValueLists()
    # print(f"lGrpVarValues: {lGrpVarValues}")

    dicArtVarValueLists, dicArtVarsTypeList = xGroup.GetArtefactVarValues(lGrpVarValues)
    # print(f"dicArtVarValueLists: {dicArtVarValueLists}")
    # print(f"dicArtVarsTypeList: {dicArtVarsTypeList}")

    dicArtVarLabelLists = xGroup.GetArtefactVarLabels(dicArtVarValueLists)
    # print(f"dicArtVarLabelLists: {dicArtVarLabelLists}")

    lNodes = xGroup.GetGroupVarNodeList(lGrpVarValues)
    # print(f"Nodes count: {len(lNodes)}")
    xNode = lNodes[100]
    # print(f"Node lPathNames: {xNode.lPathNames}")
    # print(f"Node: {xNode}")

    xArtNode = xGroup.GetArtVarNode(_xNode=xNode, _sArtType="image", _lArtPath=["Image", "1"])
    # print(f"Artefact node: {xArtNode}")
    # print(f"Artefact node path: {xArtNode.pathFS}")

    # print(f"Image artefact vars: {xGroup.dicArtTypes['image'].xPathStruct.lPathVarIds}")
    #########################

    if "production" in xGroup.xPathStruct.lPathVarIds:
        iProductionIndex = xGroup.xPathStruct.lPathVarIds.index("production")
        sProductionValue = lGrpVarValues[iProductionIndex][0]
    else:
        iProductionIndex = -1
        sProductionValue = ""
    # endif

    # print(f"iProductionIndex: {iProductionIndex}")
    # print(f"sProductionValue: {sProductionValue}")

    lExportVarIdxs: list[int] = [iIdx for iIdx, sId in enumerate(xGroup.xPathStruct.lPathVarIds) if sId != "production"]
    # print(f"lExportVarIdxs: {lExportVarIdxs}")
    lExportVarIds: list[str] = [xGroup.xPathStruct.lPathVarIds[iIdx] for iIdx in lExportVarIdxs]
    # print(f"lExportVarIds: {lExportVarIds}")
    lExportVarNames: list[str] = [xGroup.xPathStruct.dicVars[sId].sName for sId in lExportVarIds]
    # print(f"lExportVarNames: {lExportVarNames}")
    lExportVarValues: list[list[str]] = [lGrpVarValues[iIdx] for iIdx in lExportVarIdxs]
    # print(f"lExportVarValues: {lExportVarValues}")
    lGroupDimConfigs: list[CGroupConfig] = []
    for iIdx, sId, sName in zip(lExportVarIdxs, lExportVarIds, lExportVarNames, strict=True):
        lGroupDimConfigs.append(CGroupConfig(sId, sName, lGrpVarValues[iIdx]))
    # endfor
    # print(f"lConfigs: {lConfigs}")

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
        # print(f"lNameValueMod: {lNameValueMod}")

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
            # print(f"sArtVarId: {sArtVarId}, iIdx: {iIdx}, lNameValues: {lNameValues}")
            # print(f"  sExportName: {sExportName}")
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
                sExportName=sExportName))
        # endfor all names
    # endfor sArtVarId

    # print("lGroupConfigs: ")
    # for xGroupConfig in lGroupDimConfigs:
    #     print(f"  {xGroupConfig}")

    # print("lArterfactConfigs: ")
    # for xArtefactConfig in lArterfactConfigs:
    #     print(f"  {xArtefactConfig}")

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

    iExportCount = 0
    lMissing = []
    dicExport: dict[str, CArtefactExport] = {}
    for xArtCfg in lArtefactConfigs:
        dicExport[xArtCfg.sExportName] = CArtefactExport(
            sName=xArtCfg.sExportName,
            lVarIds=lExportVarIds + [xArtCfg.sArtIterVarId],
            lVarNames=lExportVarNames + [xArtCfg.sArtIterVarName],
            lVarValues=lExportVarValues + [xArtCfg.lArtIterPath],
            lDataType=xArtCfg.lDataType,
            lArtFilePaths=[],
            lArtIdxLists=[],
            lArtMissing=[],
        )

    for iIdx in range(iCfgTotalCount):
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
            raise TypeError(f"Element 'lExclude' in 'mFilters' of production group '{sGrpId}' is not a list: {type(lExcFilters)}")
        # endif 
        if not isinstance(lIncFilters, list):
            raise TypeError(f"Element 'lInclude' in 'mFilters' of production group '{sGrpId}' is not a list: {type(lIncFilters)}")
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

        # print("\n")
        # print(f"iIdx: {iIdx}, lCfgValues: {lCfgValues}")
        # print(f"  dicProcFilters: {dicProcFilters}")

        if iProductionIndex >= 0:
            lCfgValues.insert(iProductionIndex, sProductionValue)
        # endif

        xNode = xGroup.GetGroupVarNode(lCfgValues)
        # print(f"  lCfgValues: {lCfgValues}")
        # print(f"  Node: {xNode}")
        for xArtCfg in lArtefactConfigs:
            sArtType = xArtCfg.sArtType
            xExport = dicExport[xArtCfg.sExportName]

            for sArtIterIdx, sArtIterValue in enumerate(xArtCfg.lArtIterPath):
                lArtPath: list[str] = xArtCfg.lArtMainPath + [sArtIterValue]
                # print(f"  sArtType: {sArtType}, lArtPath: {lArtPath}")
                xArtNode = xGroup.GetArtVarNode(_xNode=xNode, _sArtType=sArtType, _lArtPath=lArtPath)
                if xArtNode is None:
                    xExport.lArtMissing.append(lCfgIndices + [sArtIterIdx])
                    continue
                # endif

                # print(f"  lCfgIndices: {lCfgIndices}, sArtIterIdx: {sArtIterIdx}")
                xExport.lArtIdxLists.append(lCfgIndices + [sArtIterIdx])
                xExport.lArtFilePaths.append(xArtNode.pathFS)

            # endfor artefact elements
        # endfor artefact types
        iExportCount += 1

        # if iExportCount > 10:
        #     break
    # endfor group configs

    # print(f"missing count: {len(lMissing)}")
    print(f"export count: {iExportCount}")
    # print(f"\n dicExport: {dicExport}")
    # print(f"lMissing: {lMissing}")

    # ##################################################################
    # xtar export
    # ##################################################################
    lTypes: list[xtar.IOType] = []
    lMetaTypes: list[xtar.IOType] = []

    iElementCount = 0
    for xExport in dicExport.values():
        print(f"\nArtefact export: {xExport.sName}")
        print(f"  Element Count: {len(xExport.lArtFilePaths)}")
        print(f"  Missing Count: {len(xExport.lArtMissing)}")
        if iElementCount == 0:
            iElementCount = len(xExport.lArtFilePaths)
        elif iElementCount != len(xExport.lArtFilePaths):
            print(f"  WARNING: Artefact export element count mismatch: {iElementCount} != {len(xExport.lArtFilePaths)}")
            print(f"  Ignoring artefact: {xExport.sName}")
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
                print(f"  WARNING: Unsupported image format: {sImgFormat}")
                print(f"  Ignoring artefact: {xExport.sName}")
                continue
            # endif

        elif xExport.lDataType[0] == "data":
            if xExport.lDataType[1] == "json":
                lTypes.append(xtar.IOType(xtar.EDataType.JSON, xExport.sName, xtar.JsonWriterParams()))
                lMetaTypes.append(xtar.IOType(xtar.EDataType.JSON, xExport.sName, xtar.JsonWriterParams()))
            else:
                print(f"  WARNING: Unsupported data format: {xExport.lDataType[1]}")
                print(f"  Ignoring artefact: {xExport.sName}")
                continue
            # endif
        else:
            print(f"  WARNING: Unsupported format: {xExport.lDataType[0]}")
            print(f"  Ignoring artefact: {xExport.sName}")
            continue

        # endif
    # endfor


    print(f"\nlTypes: {lTypes}\n")

    pathXtar = xProject.xConfig.pathOutput / "xtar" / xProject.xConfig.sLaunchFolderName
    if pathXtar.exists():
        shutil.rmtree(pathXtar)
    # endif
    pathXtar.mkdir(parents=True, exist_ok=True)

    xWriter = xtar.ContiguousDatasetWriter(pathXtar, lTypes, samples_per_group=1000, meta_writer_types=lMetaTypes)

    dicMeta = {}
    for xType in lMetaTypes:
        xExport = dicExport[xType.content_id]
        dicMeta.update({
            xType.content_id: {
                "name": xExport.sName,
                "var_ids": xExport.lVarIds,
                "var_names": xExport.lVarNames,
                "var_values": xExport.lVarValues,
                "indexes": xExport.lArtIdxLists,
            }
        })
    # endfor meta
    xWriter.add_meta(0, **dicMeta)

    print(f"iElementCount: {iElementCount}")

    iMaxCount = 10
    if iMaxCount > 0 and iElementCount > iMaxCount:
        iElementCount = iMaxCount

    print(f"Number of elements to write: {iElementCount}")
    for iIdx in tqdm(range(iElementCount), desc="Writing artefacts", unit="configuration"):
        dicData = {}
        for xType in lTypes:
            xExport = dicExport[xType.content_id]
            if iIdx < len(xExport.lArtFilePaths):
                # Export OpenEXR images as numpy arrays
                if xExport.lDataType[0] == "image" and xExport.lDataType[1] == "exr":
                    sFilepath = str(xExport.lArtFilePaths[iIdx])
                    imgData = cv2.imread(sFilepath, cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH | cv2.IMREAD_UNCHANGED)
                    if imgData is None:
                        print(f"  WARNING: Failed to read image: {sFilepath}")
                        continue
                    # endif
                    if len(imgData.shape) > 2:
                        # Flip order of color channel elements, as cv2 stores images as BGR and not RGB.
                        if imgData.shape[2] == 4:
                            imgData = imgData[:, :, [2, 1, 0, 3]]
                        else:
                            imgData = imgData[:, :, ::-1]
                        # endif
                    # endif
                    dicData[xType.content_id] = imgData
                else:
                    dicData[xType.content_id] = xExport.lArtFilePaths[iIdx]
                # endif
            else:
                print(f"  WARNING: Missing artefact: {xType.content_id}")
            # endif
        # endfor
        xWriter.add(**dicData)
    # endfor data
    xWriter.flush()

if __name__ == "__main__":
    main()
