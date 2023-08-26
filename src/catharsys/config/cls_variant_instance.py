###
# Author: Christian Perwass (CR/AEC5)
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
import uuid
from typing import Optional
from pathlib import Path
from catharsys.api.cls_project import CProject
from catharsys.config.cls_project import CProjectConfig


class CVariantInstance:
    c_reFolderInstance = re.compile(r"(?P<group>[a-zA-Z0-9\-_]+)-(?P<lid>\d+)-(?P<tid>\d+)@(?P<uid>[A-Fa-f0-9\-]+)")

    def __init__(self, *, _pathInstances: Path):
        self._pathMain: Path = _pathInstances
        self._pathInst: Path = None
        self._sPrjId: str = None
        self._sGroup: str = None
        self._iLaunchId: int = None
        self._iTrialId: int = None
        self._uidInst: uuid.UUID = None

    # enddef

    @property
    def sGroup(self) -> str:
        return self._sGroup

    # enddef

    @property
    def iLaunchId(self) -> int:
        return self._iLaunchId

    # enddef

    @property
    def iTrialId(self) -> int:
        return self._iTrialId

    # enddef

    @property
    def uidInstance(self) -> uuid.UUID:
        return self._uidInst

    # enddef

    @property
    def pathInstance(self) -> Path:
        return self._pathInst

    # enddef

    @property
    def sName(self) -> str:
        return f"{self._sGroup}-{self._iLaunchId}-{self._iTrialId}"

    # enddef

    @property
    def sInstanceFolderName(self) -> str:
        return f"{self.sName}@{self._uidInst}"

    # enddef

    @property
    def sProjectId(self) -> str:
        return self._sPrjId

    # enddef

    # ############################################################################################
    @classmethod
    def IsInstanceFolder(cls, _sFolderName: str) -> bool:
        return cls.c_reFolderInstance.fullmatch(_sFolderName) is not None

    # enddef

    # ############################################################################################
    @classmethod
    def IsInstancePath(cls, _pathInst: Path) -> bool:
        return cls.IsInstanceFolder(_pathInst.name)

    # enddef

    # ############################################################################################
    def _CreatePrjId(self):
        tParts = self._pathInst.parts
        try:
            iStart = tParts.index("config") + 1
            iEnd = tParts.index(".variants")
            self._sPrjId = "/".join(tParts[iStart:iEnd])
        except Exception:
            self._sPrjId = self.sName
        # endtry

    # enddef

    # ############################################################################################
    def FromPath(self, _pathInst: Path) -> "CVariantInstance":
        xMatch: re.Pattern = CVariantInstance.c_reFolderInstance.fullmatch(_pathInst.name)
        if xMatch is None:
            raise RuntimeError(f"Path is not a variant instance path: {(_pathInst.as_posix())}")
        # endif

        self._sGroup = xMatch.group("group")
        self._iLaunchId = int(xMatch.group("lid"))
        self._iTrialId = int(xMatch.group("tid"))
        self._uidInst = uuid.UUID(xMatch.group("uid"))
        self._pathInst = self._pathMain / self.sInstanceFolderName

        self._CreatePrjId()

        return self

    # enddef

    # ############################################################################################
    def Create(
        self, *, _sGroup: str, _iLaunchId: int, _iTrialId: int, _sUUID: Optional[str] = None
    ) -> "CVariantInstance":
        self._sGroup = _sGroup
        self._iLaunchId = _iLaunchId
        self._iTrialId = _iTrialId
        self._uidInst = None

        if not isinstance(_sUUID, str):
            self._uidInst = uuid.uuid4()
        else:
            self._uidInst = uuid.UUID(hex=_sUUID)
        # endif

        self._pathInst = self._pathMain / self.sInstanceFolderName
        self._CreatePrjId()

        self._pathInst.mkdir(parents=True, exist_ok=True)
        return self

    # enddef

    # ############################################################################################
    def GetProjectConfig(self) -> CProjectConfig:
        xPrjCfg = CProjectConfig()
        xPrjCfg.FromLaunchPath(self._pathInst)

        return xPrjCfg

    # enddef

    # ############################################################################################
    def GetProject(self) -> CProject:
        return CProject(self.GetProjectConfig())

    # enddef


# endclass
