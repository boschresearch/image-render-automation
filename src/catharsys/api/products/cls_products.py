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

import re
import copy
from pathlib import Path
from typing import Iterator, Optional, Union, Callable

from catharsys.api.cls_project import CProject

from anybase import config
from anybase import file as anyfile
from anybase.cls_any_error import CAnyError_Message

from .cls_path_structure import CPathVar, EPathVarType, CPathVarHandlerResult
from .cls_group import CGroup
from .cls_node import ENodeType


class CProducts:
    c_reFrame: re.Pattern = re.compile(r"Frame_(\d+)\.(.+)")

    def __init__(
        self,
        *,
        _prjX: CProject,
    ):
        self._xProject: CProject = _prjX

        self._dicGroups: dict[str, CGroup] = dict()

        self._dicSystemVars: dict[str, CPathVar] = {
            "production": CPathVar(
                sId="production",
                sName="Production",
                eType=EPathVarType.SYSTEM,
                eNodeType=ENodeType.PATH,
                funcHandler=self._OnVarProduction,
            ),
            "top": CPathVar(
                sId="top",
                sName="Top Folder",
                eType=EPathVarType.SYSTEM,
                eNodeType=ENodeType.PATH,
                funcHandler=self._OnVarTop,
            ),
            "rq": CPathVar(
                sId="rq",
                sName="Render Quality",
                eType=EPathVarType.SYSTEM,
                eNodeType=ENodeType.PATH,
                funcHandler=self._OnVarRq,
                sReParseValue=r"rq[0]*(\d+)",
                sReReplaceValue=r"\1",
            ),
            "project": CPathVar(
                sId="project",
                sName="Configuration",
                eType=EPathVarType.SYSTEM,
                eNodeType=ENodeType.PATH,
                funcHandler=self._OnVarProject,
            ),
            "frame": CPathVar(
                sId="frame",
                sName="Frame",
                eType=EPathVarType.SYSTEM,
                eNodeType=ENodeType.ARTEFACT,
                funcHandler=self._OnVarFrame,
                sReParseValue=r"Frame_[0]*(\d+)\..+",
                sReReplaceValue=r"\1",
            ),
        }

    # enddef

    @property
    def dicGroups(self) -> dict[str, CGroup]:
        return self._dicGroups

    # enddef

    @property
    def lGroups(self) -> list[str]:
        return list(self._dicGroups.keys())

    # enddef

    @property
    def lGroupNames(self) -> list[str]:
        return [xGrp.sName for xGrp in self._dicGroups.values()]

    # enddef

    @property
    def dicGroupKeyNames(self) -> dict[str, str]:
        return {k: v.sName for k, v in self._dicGroups.items()}

    # enddef

    @property
    def iGroupCount(self) -> int:
        return len(self._dicGroups)

    # enddef

    # #####################################################################################################
    def FromFile(self, _pathConfig: Path, *, _bIgnoreGroupExceptions: bool = False):
        dicExceptions: dict[str, str] = dict()
        self._dicCfg = config.Load(_pathConfig, sDTI="/catharsys/production:1")
        dicGroups = self._dicCfg["mGroups"]
        for sGroup in dicGroups:
            try:
                self._dicGroups[sGroup] = CGroup(
                    _sId=sGroup, _prjX=self._xProject, _dicPathSystemVars=self._dicSystemVars
                )
                self._dicGroups[sGroup].FromConfig(dicGroups[sGroup])
            except Exception as xEx:
                if _bIgnoreGroupExceptions is True:
                    dicExceptions[sGroup] = str(xEx)
                    del self._dicGroups[sGroup]
                else:
                    raise CAnyError_Message(sMsg=f"Error parsing group '{sGroup}'", xChildEx=xEx)
                # endif
            # endtry
        # endfor

        return dicExceptions

    # enddef

    # #####################################################################################################
    def ScanArtefacts(
        self,
        *,
        _sGroupId: Optional[str] = None,
        _funcStatus: Optional[Callable[[str], None]] = None,
        _funcIterInit: Optional[Callable[[str, int], None]] = None,
        _funcIterUpdate: Optional[Callable[[int], None]] = None,
    ):
        if _sGroupId is None:
            for sGroup in self._dicGroups:
                if _funcStatus is not None:
                    _funcStatus(f"Scanning for production group '{sGroup}'...")
                # endif

                self._dicGroups[sGroup].ScanArtefacts(
                    _funcStatus=_funcStatus,
                    _funcIterInit=_funcIterInit,
                    _funcIterUpdate=_funcIterUpdate,
                )
            # endfor
        else:
            xGrp = self._dicGroups.get(_sGroupId)
            if xGrp is None:
                raise RuntimeError(f"Group '{_sGroupId}' not available")
            # endif
            if _funcStatus is not None:
                _funcStatus(f"Scanning for production group '{_sGroupId}'...")
            # endif

            xGrp.ScanArtefacts(
                _funcStatus=_funcStatus,
                _funcIterInit=_funcIterInit,
                _funcIterUpdate=_funcIterUpdate,
            )
        # endif

    # enddef

    # ######################################################################################################
    def SerializeScan(self, _xFilePath: Union[str, list, tuple, Path]):
        dicGroups: dict[str, list[tuple]] = dict()
        for sGroup in self._dicGroups:
            dicGroups[sGroup] = self._dicGroups[sGroup].SerializeScan()
        # endfor

        dicData = {
            "sDTI": "/catharsys/production/scan:1.0",
            "sProjectId": self._xProject.sId,
            "mGroups": dicGroups,
        }

        anyfile.SavePickle(_xFilePath, dicData)

    # enddef

    # ######################################################################################################
    def DeserializeScan(self, _xFilePath: Union[str, list, tuple, Path]):
        dicData = anyfile.LoadPickle(_xFilePath)
        if not config.IsConfigType(dicData, "/catharsys/production/scan:1"):
            raise RuntimeError("Invalid file type")
        # endif

        sProjectId = dicData.get("sProjectId")
        if sProjectId is None:
            raise RuntimeError("No project id specified in file")
        # endif

        if sProjectId != self._xProject.sId:
            raise RecursionError(
                f"File contains product scan for project '{sProjectId}'. Expected project '{self._xProject.sId}'"
            )
        # endif

        dicGroups = dicData.get("mGroups")
        if dicGroups is None:
            raise RuntimeError("No group data given in product scan file")
        # endif

        for sGroup in dicGroups:
            if sGroup not in self._dicGroups:
                print(f"WARNING: Group '{sGroup}' given in scan not found in current configuration")
            # endif

            self._dicGroups[sGroup].DeserializeScan(dicGroups[sGroup])
        # endfor

    # enddef

    # ######################################################################################################
    def RegisterSystemVar(self, xPathVar: CPathVar):
        self._dicSystemVars[xPathVar.sId] = copy.copy(xPathVar)

    # enddef

    # ######################################################################################################
    def _OnVarProduction(self, _pathScan: Path) -> Iterator[CPathVarHandlerResult]:
        if _pathScan is not None:
            raise RuntimeError("Path variable 'production' must be the first element in a path structure")
        # endif

        pathScan = self._xProject.xConfig.pathProduction
        if not pathScan.exists():
            pathTest = pathScan.parent / "_render"
            if not pathTest.exists():
                raise RuntimeError(f"Production path does not exist: {(pathTest.as_posix())}")
            # endif
            pathScan = pathTest
        # endif

        yield CPathVarHandlerResult(pathScan, pathScan.as_posix())

    # enddef

    # ######################################################################################################
    def _OnVarTop(self, _pathScan: Path) -> Iterator[CPathVarHandlerResult]:
        if _pathScan is None:
            raise RuntimeError("Path variable 'top' must not be the first element of a path structure")
        # endif

        for pathItem in _pathScan.iterdir():
            if not pathItem.is_dir() or pathItem.name.startswith("rq"):
                continue
            # endif

            yield CPathVarHandlerResult(pathItem, pathItem.name)
        # endfor

    # enddef

    # ######################################################################################################
    def _OnVarRq(self, _pathScan: Path) -> Iterator[CPathVarHandlerResult]:
        if _pathScan is None:
            raise RuntimeError("Path variable 'rq' must not be the first element of a path structure")
        # endif
        for pathItem in _pathScan.iterdir():
            if not pathItem.is_dir() or not pathItem.name.startswith("rq"):
                continue
            # endif

            yield CPathVarHandlerResult(pathItem, pathItem.name, int(pathItem.name[2:]))
        # endfor

    # enddef

    # ######################################################################################################
    def _OnVarProject(self, _pathScan: Path) -> Iterator[CPathVarHandlerResult]:
        if _pathScan is None:
            raise RuntimeError("Path variable 'project' must not be the first element of a path structure")
        # endif
        pathItem: Path = _pathScan / self._xProject.sId
        if not pathItem.exists():
            yield CPathVarHandlerResult(None, None)
        else:
            yield CPathVarHandlerResult(pathItem, self._xProject.sId)
        # endif

    # enddef

    # ######################################################################################################
    def _OnVarFrame(self, _pathScan: Path) -> Iterator[CPathVarHandlerResult]:
        if _pathScan is None:
            raise RuntimeError("Path variable 'frame' must not be the first element of a path structure")
        # endif
        for pathItem in _pathScan.iterdir():
            xMatch = CProducts.c_reFrame.fullmatch(pathItem.name)
            if not pathItem.is_file() or xMatch is None:
                continue
            # endif
            yield CPathVarHandlerResult(pathItem, pathItem.stem, (int(xMatch.group(1)), xMatch.group(2)), pathItem.name)
        # endfor

    # enddef


# endclass
