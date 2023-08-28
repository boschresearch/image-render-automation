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
import json
import copy
import hashlib
from datetime import datetime
from typing import Optional, Any
from pathlib import Path

from anybase import config
from anybase.cls_any_error import CAnyError_Message
from catharsys.api.cls_project import CProject
from catharsys.config.cls_project import CProjectConfig


class CVariantInstance:
    c_reFolderInstance = re.compile(r"^(?P<group>[a-zA-Z0-9\-_]+)-(?P<lid>\d+)-(?P<tid>\d+)")

    def __init__(self, *, _pathInstances: Path):
        self._pathMain: Path = _pathInstances
        self._pathInst: Path = None
        self._sPrjId: str = None
        self._sGroup: str = None
        self._iLaunchId: int = None
        self._iTrialId: int = None
        self._sHash: str = None
        self._sTypeHash: str = None
        self._dtCreated: datetime = None
        self._dicMeta: dict[str, Any] = None

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
    def sId(self) -> str:
        return self._sHash

    # enddef

    @property
    def sTypeId(self) -> str:
        return self._sTypeHash

    # enddef

    @property
    def dtCreated(self) -> datetime:
        return self._dtCreated

    # enddef

    @property
    def sTimeCreated(self) -> str:
        return self._dtCreated.strftime("%d %b %Y, %H:%M:%S.%f")

    # enddef

    @property
    def pathInstance(self) -> Path:
        return self._pathInst

    # enddef

    @property
    def pathInstanceConfig(self) -> Path:
        return self.pathInstance / ".instance.json"

    # enddef

    @property
    def sName(self) -> str:
        return f"{self._sGroup}-{self._iLaunchId}-{self._iTrialId}"

    # enddef

    @property
    def dicMeta(self) -> dict[str, Any]:
        return self._dicMeta

    # enddef

    @property
    def sProjectId(self) -> str:
        return self._sPrjId

    # enddef

    # ############################################################################################
    @classmethod
    def IsInstanceFolder(cls, _sFolderName: str) -> bool:
        return cls.c_reFolderInstance.match(_sFolderName) is not None

    # enddef

    # ############################################################################################
    @classmethod
    def IsInstancePath(cls, _pathInst: Path) -> bool:
        return cls.IsInstanceFolder(_pathInst.name)

    # enddef

    # ############################################################################################
    def IsEqual(self, _xClass: "CVariantInstance") -> bool:
        if isinstance(_xClass, self.__class__):
            return self.sId == _xClass.sId
        # endif
        return False

    # enddef

    # ############################################################################################
    def IsEqualType(self, _xClass: "CVariantInstance") -> bool:
        if isinstance(_xClass, self.__class__):
            return self.sTypeId == _xClass.sTypeId
        # endif
        return False

    # enddef

    # ############################################################################################
    def FromPath(self, _pathInst: Path) -> "CVariantInstance":
        xMatch: re.Pattern = CVariantInstance.c_reFolderInstance.match(_pathInst.name)
        if xMatch is None:
            raise RuntimeError(f"Path is not a variant instance path: {(_pathInst.as_posix())}")
        # endif
        self._pathInst = _pathInst
        try:
            dicData = config.Load(self.pathInstanceConfig, sDTI="/catharsys/variant/instance:1", bReplacePureVars=False)
            self._sHash = dicData["sHash"]
            self._sTypeHash = dicData["sTypeHash"]
            self._sGroup = dicData["sGroup"]
            self._iLaunchId = dicData["iLaunchId"]
            self._iTrialId = dicData["iTrialId"]
            self._sPrjId = dicData["sPrjId"]
            self._dtCreated = datetime.strptime(dicData["sTimeCreated"], "%d %b %Y, %H:%M:%S.%f")
            self._dicMeta = dicData["mMeta"]
        except Exception as xEx:
            raise CAnyError_Message(
                sMsg=f"Error initializing variant instance from configuration file: {self.pathInstanceConfig}",
                xChildEx=xEx,
            )
        # endtry

        return self

    # enddef

    # ############################################################################################
    def Create(
        self, *, _sPrjId: str, _sGroup: str, _iLaunchId: int, _iTrialId: int, _dicMeta: Optional[dict[str, Any]] = None
    ) -> "CVariantInstance":
        self._sGroup = _sGroup
        self._iLaunchId = _iLaunchId
        self._iTrialId = _iTrialId
        self._sPrjId = _sPrjId
        self._dtCreated = datetime.now()

        if isinstance(_dicMeta, dict):
            self._dicMeta = copy.deepcopy(_dicMeta)
        else:
            self._dicMeta = dict()
        # endif

        try:
            sMeta = json.dumps(self._dicMeta)
        except Exception as xEx:
            raise CAnyError_Message(sMsg="Variant instance meta data must be json serializable", xChildEx=xEx)
        # endtry

        sData = f"{self._sGroup}-{self._sPrjId}-{self._iLaunchId}-{self._iTrialId}:{sMeta}"
        self._sTypeHash = hashlib.md5(sData.encode("utf-8")).hexdigest()

        sData = f"{self._sTypeHash}:{self.sTimeCreated}"
        self._sHash = hashlib.md5(sData.encode("utf-8")).hexdigest()

        # Ensure that the main instance path exists
        self._pathMain.mkdir(parents=True, exist_ok=True)

        # Find available folder name
        iHashDigits: int = 1
        sFolderName: str = self.sName
        while True:
            self._pathInst = self._pathMain / sFolderName
            if not self._pathInst.exists():
                break
            # endif
            sHash = self._sHash[0:iHashDigits]
            sFolderName = f"{self.sName}@{sHash}"
            iHashDigits += 1
        # endwhile

        self._pathInst.mkdir(parents=True)
        self._Serialize()

        return self

    # enddef

    # ############################################################################################
    def _Serialize(self):
        try:
            dicData = {
                "sHash": self._sHash,
                "sTypeHash": self._sTypeHash,
                "sGroup": self._sGroup,
                "iLaunchId": self._iLaunchId,
                "iTrialId": self._iTrialId,
                "sPrjId": self._sPrjId,
                "sTimeCreated": self.sTimeCreated,
                "mMeta": self._dicMeta,
            }
            config.Save(self.pathInstanceConfig, dicData, sDTI="/catharsys/variant/instance:1.0")
        except Exception as xEx:
            raise CAnyError_Message(
                sMsg=f"Error serializing variant instance: {self._sGroup}, {self._iLaunchId}, {self._iTrialId}",
                xChildEx=xEx,
            )
        # endtry

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
