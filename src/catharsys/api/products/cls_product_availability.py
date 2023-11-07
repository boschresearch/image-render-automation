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

from pathlib import Path
from typing import Optional

from anybase import file as anyfile

# from catharsys.api.products.cls_products import CProducts
from catharsys.api.products.cls_group import CGroup
from catharsys.api.products.cls_node import CNode
from catharsys.api.products.cls_path_structure import CPathVar

from dataclasses import dataclass


@dataclass
class CMissing:
    xNode: CNode
    iLevel: int
    lNames: list[str]


# endclass


class CProductAvailability:
    def __init__(
        self,
        *,
        _xGroup: CGroup,
        _lSelGrpVarValLists: list[list[str]],
        _dicSelArtVarValLists: Optional[dict[list[list[str]]]] = None,
    ):
        self._xGrp: CGroup = _xGroup
        self._lSelGrpVarValLists: list[list[str]] = _lSelGrpVarValLists
        self._dicSelArtVarValLists: dict[list[list[str]]] = _dicSelArtVarValLists
        self._dicMissing: dict[str, list[CMissing]] = dict()
        self.Clear()

    # enddef

    @property
    def dicMissing(self):
        return self._dicMissing

    # enddef

    @property
    def lGroupMissing(self):
        return self._dicMissing["__group__"]

    # enddef

    def Clear(self):
        self._dicMissing = dict()
        self._dicMissing["__group__"] = []

    # enddef

    def _DoTestGrpAvailability(self, _xRoot: CNode, _iLevel: int):
        lSelGrpVarVal = self._lSelGrpVarValLists[_iLevel]
        xMissing = CMissing(_xRoot, _iLevel, [])
        for xGrpVarVal in lSelGrpVarVal:
            sGrpVarVal: str = str(xGrpVarVal)
            xNode: CNode = next((node for node in _xRoot.children if node.name == sGrpVarVal), None)
            if xNode is None:
                xMissing.lNames.append(sGrpVarVal)
            elif _iLevel + 1 < len(self._lSelGrpVarValLists):
                self._DoTestGrpAvailability(xNode, _iLevel + 1)
            elif self._dicSelArtVarValLists is not None:
                self._DoTestAllArtAvailability(xNode)
            # endif
        # endfor
        if len(xMissing.lNames) > 0:
            self.lGroupMissing.append(xMissing)
        # endif

    # enddef

    def _DoTestAllArtAvailability(self, _xGrpRoot: CNode):
        for sArtTypeId, lArtVarValLists in self._dicSelArtVarValLists.items():
            if sArtTypeId not in self._dicMissing:
                self._dicMissing[sArtTypeId] = []
            # endif

            xNode: CNode = next((node for node in _xGrpRoot.children if node.name == sArtTypeId), None)
            if xNode is None:
                self._dicMissing[sArtTypeId].append(CMissing(_xGrpRoot, 0, lArtVarValLists[0]))
            else:
                self._DoTestArtAvailability(xNode, 0, sArtTypeId)
            # endif

        # endfor

    # enddef

    def _DoTestArtAvailability(self, _xRoot: CNode, _iLevel: int, _sArtTypeId: str):
        lSelArtVarValLists = self._dicSelArtVarValLists[_sArtTypeId]
        lSelArtVarVal = lSelArtVarValLists[_iLevel]
        xMissing = CMissing(_xRoot, _iLevel, [])
        for xArtVarVal in lSelArtVarVal:
            sArtVarVal = str(xArtVarVal)
            xNode: CNode = next((node for node in _xRoot.children if node.name == sArtVarVal), None)
            if xNode is None:
                xMissing.lNames.append(sArtVarVal)
            elif _iLevel + 1 < len(lSelArtVarValLists):
                self._DoTestArtAvailability(xNode, _iLevel + 1, _sArtTypeId)
            # endif
        # endfor

        if len(xMissing.lNames) > 0:
            self._dicMissing[_sArtTypeId].append(xMissing)
        # endif

    # enddef

    def Analyze(self):
        self.Clear()
        self._DoTestGrpAvailability(self._xGrp.xTree, 0)

    # enddef

    def GetMissingArtefactsGroupVarValues(self, _sVarId: str, _lArtTypeIds: Optional[list[str]] = None):
        if _sVarId not in self._xGrp.xPathStruct.lPathVarIds:
            raise RuntimeError(f"Group variable '{_sVarId}' does not exist")
        # endif
        iVarLevel = self._xGrp.xPathStruct.lPathVarIds.index(_sVarId)
        # lVarValues = self._lSelGrpVarValLists[iVarLevel]
        dicVarValMissing: dict[str, set[str]] = dict()

        if _lArtTypeIds is None:
            lArtTypeIds = list(self._dicSelArtVarValLists.keys())
        else:
            lArtTypeIds = _lArtTypeIds
        # endif

        for xMissing in self.lGroupMissing:
            if xMissing.xNode.iLevel == iVarLevel - 1:
                sPath = xMissing.xNode.pathFS.as_posix()
                if sPath not in dicVarValMissing:
                    dicVarValMissing[sPath] = set()
                # endif
                dicVarValMissing[sPath].update(xMissing.lNames)

            elif xMissing.xNode.iLevel > iVarLevel:
                xVarNode: CNode = xMissing.xNode.ancestors[iVarLevel + 1]
                # print(f"xVarNode: {xVarNode}")
                xPathNode: CNode = xVarNode.parent
                # print(f"xPathNode: {xPathNode}")

                sPath = xPathNode.pathFS.as_posix()
                if sPath not in dicVarValMissing:
                    dicVarValMissing[sPath] = set()
                # endif
                dicVarValMissing[sPath].add(xVarNode.name)

            else:
                pathMain = xMissing.xNode.pathFS
                for sName in xMissing.lNames:
                    sPath = (pathMain / sName).as_posix()
                    if sPath not in dicVarValMissing:
                        dicVarValMissing[sPath] = set()
                    # endif
                # endfor
            # endif
        # endfor

        for sArtTypeId in lArtTypeIds:
            lMissing = self._dicMissing.get(sArtTypeId)
            if lMissing is None:
                raise RuntimeError(f"Artefact type id '{sArtTypeId}' not available")
            # endif
            for xMissing in lMissing:
                xVarNode: CNode = xMissing.xNode.ancestors[iVarLevel + 1]
                # print(f"xVarNode: {xVarNode}")
                xPathNode: CNode = xVarNode.parent
                # print(f"xPathNode: {xPathNode}")

                sPath = xPathNode.pathFS.as_posix()
                if sPath not in dicVarValMissing:
                    dicVarValMissing[sPath] = set()
                # endif
                dicVarValMissing[sPath].add(xVarNode.name)
            # endfor
        # endfor

        dicMissing: dict[str, list] = {}
        for sPath, setVals in dicVarValMissing.items():
            if len(setVals) > 0 and next((self._IsInt(x) for x in setVals), None) is True:
                lVals = [int(x) for x in setVals]
            else:
                lVals = list(setVals)
            # endif
            lVals.sort()
            dicMissing[sPath] = lVals
        # endfor

        return dicMissing

    # enddef

    def _IsInt(self, _sVal: str) -> bool:
        try:
            iVal = int(_sVal)
        except Exception:
            return False
        # endtry
        return True

    # enddef

    def PrintMissingArtefactsGroupVarValues(
        self,
        *,
        _sVarId: str,
        _lArtTypeIds: Optional[list[str]] = None,
        _bConcise: bool = False,
        _dicMissing: Optional[dict] = None,
    ):
        if _dicMissing is None:
            dicMissing = self.GetMissingArtefactsGroupVarValues(_sVarId, _lArtTypeIds)
        else:
            dicMissing = _dicMissing
        # endif

        sVarName = self._xGrp.xPathStruct.dicVars[_sVarId].sName

        if len(dicMissing) == 0:
            print("All artefacts available")
            return
        # endif

        if isinstance(_lArtTypeIds, list) and len(_lArtTypeIds) > 0:
            sArtNames = ", ".join(_lArtTypeIds)
            print(
                f"Artefact type(s) '{sArtNames}' missing for the following values of path variable '{sVarName}' [{_sVarId}]:"
            )
        else:
            print(f"Any artefact types missing for the following values '{sVarName}' [{_sVarId}]:")
        # endif
        print("")

        for sPath, lVals in dicMissing.items():
            print(f"  Path: {sPath}")

            if _bConcise is True and isinstance(lVals[0], int):
                lCluster: list[str] = []
                iStartVal = lVals[0]
                iPrevVal = iStartVal
                for iVal in lVals[1:]:
                    if iVal > iPrevVal + 1:
                        if iStartVal == iPrevVal:
                            lCluster.append(f"{iStartVal}")
                        elif iStartVal + 1 == iPrevVal:
                            lCluster.extend([iStartVal, iPrevVal])
                        else:
                            lCluster.append([iStartVal, iPrevVal])
                        # endif
                        iStartVal = iVal
                    # endif
                    iPrevVal = iVal
                # endfor
                if iStartVal == iPrevVal:
                    lCluster.append(f"{iStartVal}")
                elif iStartVal + 1 == iPrevVal:
                    lCluster.extend([iStartVal, iPrevVal])
                else:
                    lCluster.append([iStartVal, iPrevVal])
                # endif

                print(f"  Values:\n{lCluster}\n")
            else:
                print(f"  Values:\n{lVals}\n")
            # endif

        # endfor

    # enddef

    def SaveMissingArtefactsGroupVarValues(
        self,
        *,
        _pathFile: Path,
        _sVarId: str,
        _lArtTypeIds: Optional[list[str]] = None,
        _iIndent: int = -1,
        _dicMissing: Optional[dict] = None,
    ):
        if _dicMissing is None:
            dicMissing = self.GetMissingArtefactsGroupVarValues(_sVarId, _lArtTypeIds)
        else:
            dicMissing = _dicMissing
        # endif

        dicData = {
            "sDTI": "/catharsys/production/missing/single-var:1.0",
            "sProjectId": self._xGrp.xProject.sId,
            "sProdVarId": _sVarId,
            "lArtefactTypeIds": _lArtTypeIds,
            "mMissing": dicMissing,
        }

        anyfile.SaveJson(_pathFile, dicData, iIndent=_iIndent)

    # enddef

    def PrintMissing(self):
        print("Missing main paths:")
        for xMissing in self.lGroupMissing:
            print("")
            print(f"  {(xMissing.xNode.pathFS.as_posix())}")
            sVarId = self._xGrp.xPathStruct.lPathVarIds[xMissing.iLevel]
            sVarName = self._xGrp.xPathStruct.dicVars[sVarId].sName
            print(f"  {sVarName}: {xMissing.lNames}")
        # endfor

        for sArtTypeId, lMissing in self.dicMissing.items():
            if sArtTypeId == "__group__" or len(lMissing) == 0:
                continue
            # endif

            xArtType = self._xGrp.dicArtTypes[sArtTypeId]
            print(f"\nMissing Artefacts '{xArtType.sName}':")
            for xMissing in lMissing:
                print("")
                print(f"  {(xMissing.xNode.pathFS.as_posix())}")
                sVarId = xArtType.xPathStruct.lPathVarIds[xMissing.iLevel]
                sVarName = xArtType.xPathStruct.dicVars[sVarId].sName
                print(f"  {sVarName}: {xMissing.lNames}")
            # endfor
        # endfor artefact types

    # enddef


# endclass
