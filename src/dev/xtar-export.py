# ##################################################################
# Export catharsys production to xtar format
# ##################################################################

import xtar
import xtar_ml
import ison
from pathlib import Path

from catharsys.api.products.cls_products import CProducts, CGroup
from catharsys.api.cls_project import CProject
from catharsys.config.cls_project import CProjectConfig
# from catharsys.config.cls_launch import CConfigLaunch

def _scan_status(sText: str) -> None:
    print(sText)


def main():
    pathMain = Path.cwd()
    sConfigName = "crs-vehicle"
    sGrpId = "std"

    xConfig = CProjectConfig()
    xConfig.FromConfigName(xPathMain=pathMain, sConfigName=sConfigName)
    xProject = CProject(xConfig)
    xProducts = CProducts(_prjX=xProject)

    pathProdCfg = xConfig.pathLaunch / "production.json5"
    dicExceptions = xProducts.FromFile(pathProdCfg)
    xProducts.ScanArtefacts(_sGroupId=sGrpId, _funcStatus=_scan_status)

    print("Group names:")
    for sKey, sName in xProducts.dicGroupKeyNames.items():
        print(f"  {sKey}: {sName}")

    xGroup: CGroup = xProducts.dicGroups[sGrpId]

    print(f"dicArtTypes: {xGroup.dicArtTypes}")
    print(f"dicVarValues: {xGroup.dicVarValues}")
    print(f"lCommonArtVarIds: {xGroup.lCommonArtVarIds}")
    print(f"lPathVarIds: {xGroup.xPathStruct.lPathVarIds}")

    lGrpVarValues = xGroup.GetGroupVarValueLists()
    print(f"lGrpVarValues: {lGrpVarValues}")

    dicArtVarValueLists, dicArtVarsTypeList = xGroup.GetArtefactVarValues(lGrpVarValues)
    print(f"dicArtVarValueLists: {dicArtVarValueLists}")
    print(f"dicArtVarsTypeList: {dicArtVarsTypeList}")

    dicArtVarLabelLists = xGroup.GetArtefactVarLabels(dicArtVarValueLists)
    print(f"dicArtVarLabelLists: {dicArtVarLabelLists}")

    lNodes = xGroup.GetGroupVarNodeList(lGrpVarValues)
    print(f"Nodes count: {len(lNodes)}")
    xNode = lNodes[100]
    print(f"Node lPathNames: {xNode.lPathNames}")
    print(f"Node: {xNode}")

    xArtNode = xGroup.GetArtVarNode(_xNode=xNode, _sArtType="image", _lArtPath=["Image", "1"])
    print(f"Artefact node: {xArtNode}")
    print(f"Artefact node path: {xArtNode.pathFS}")

    print(f"Image artefact vars: {xGroup.dicArtTypes['image'].xPathStruct.lPathVarIds}")

    #########################

    lExportVarIdxs: list[int] = [iIdx for iIdx, sId in enumerate(xGroup.xPathStruct.lPathVarIds) if sId != "production"]
    print(f"lExportVarIdxs: {lExportVarIdxs}")
    lExportVarIds: list[str] = [xGroup.xPathStruct.lPathVarIds[iIdx] for iIdx in lExportVarIdxs]
    print(f"lExportVarIds: {lExportVarIds}")
    lExportVarNames: list[str] = [xGroup.xPathStruct.dicVars[sId].sName for sId in lExportVarIds]
    print(f"lExportVarNames: {lExportVarNames}")
    
    lConfigs = []
    for iIdx, sId, sName in zip(lExportVarIdxs, lExportVarIds, lExportVarNames, strict=True):
        lConfigs.append({
            "sId": sId,
            "sName": sName,
            "lValues": lGrpVarValues[iIdx],
        })
    # endfor
    # print(f"lConfigs: {lConfigs}")

    # Generate set of data types from artefact variables, by ignoring the last element, unless there is only one.
    # This assumes that the last element is typically the filename (frame).
    # Create a flat list of these types, with the corresponding path information and number of elements.
    
if __name__ == "__main__":
    main()
