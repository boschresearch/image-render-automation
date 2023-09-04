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
from typing import Iterator

from catharsys.api.cls_project import CProject

from anybase import config

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
            ),
        }

    # enddef

    @property
    def dicGroups(self) -> dict[str, CGroup]:
        return self._dicGroups

    # enddef

    # #####################################################################################################
    def FromFile(self, _pathConfig: Path):
        self._dicCfg = config.Load(_pathConfig, sDTI="/catharsys/production:1")
        dicGroups = self._dicCfg["mGroups"]
        for sGroup in dicGroups:
            self._dicGroups[sGroup] = CGroup(_sId=sGroup, _prjX=self._xProject, _dicPathSystemVars=self._dicSystemVars)
            self._dicGroups[sGroup].FromConfig(dicGroups[sGroup])
        # endfor

    # enddef

    # #####################################################################################################
    def ScanArtefacts(self):
        for sGroup in self._dicGroups:
            self._dicGroups[sGroup].ScanArtefacts()
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
            yield CPathVarHandlerResult(pathItem, pathItem.name, (int(xMatch.group(1)), xMatch.group(2)))
        # endfor

    # enddef


# endclass
