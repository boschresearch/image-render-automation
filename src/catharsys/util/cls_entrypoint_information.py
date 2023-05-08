#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \cls_anyexcept.py
# Created Date: Friday, March 19th 2021, 9:03:02 am
# Author: Christian Perwass (CR/AEC5)
# <LICENSE id="Apache-2.0">
#
#   Image-Render Base Functions module
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

from collections import defaultdict
from dataclasses import dataclass, fields
from typing import ClassVar
from enum import Enum, auto
import os


# ###################################################################


@dataclass(repr=False)
class CEntrypointInformation:
    # -------------------------------------------------------------------
    class EEntryType(Enum):
        ACTION = auto()
        EXE_PLUGIN = auto()
        FUNCTION = auto()
        MODIFIER = auto()
        ANIMATION = auto()
        GENERATOR = auto()
        CLASSES = auto()
        UNKNOWN = auto()
        UNDEFINED = auto()
        COMMAND = auto()

    # end class
    # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    # -------------------------------------------------------------------
    @dataclass(frozen=True)
    class CDetailedDefinition:
        # definition given in doc strings
        definition: str
        # dictionary for detailed json syntax and node decrisption
        templateDict: dict

        def __str__(self) -> str:
            return self.definition

    # end class
    # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    # type classification (see above enum declaration)
    entry: EEntryType
    # group of setup:
    # e.g.: 'catharsys.blender.generate'
    group: str
    # sDTI string:
    # e.g.: '/catharsys/blender/generate/collection/load:1.0'
    ID: str
    # module name to which the entry points belong to
    # e.g.: 'catharsys.plugins.std.blender.generate.func.collection_std'
    module_name: str
    # implementation file
    # e.g.: '...../repos/image-render-actions-std-blender/src/catharsys/plugins/std/blender/generate/func/collection_std.py'
    filename: str = ""
    # definition of description or doc_string
    definition: str = ""
    # when callable the function name
    # e.g.: LoadCollections
    objname: str = ""

    @classmethod
    def AppendFuncion(cls, f_entryPtType: EEntryType, f_func, clsInterfaceDoc=None):
        """during import time, the decorators appends their wrapped functions
        into the class-list for further inspection purposes"""
        cls.__CLASSIFIED_ENTRY_POINTS[f_entryPtType].append(f_func)

        if clsInterfaceDoc is not None:
            cls.__ENTRY_INTERFACE_DOCS[f_func] = clsInterfaceDoc
        pass

    @classmethod
    def GetEntryType(cls, f_funcWrapped):
        for xEpType, lEntryPoints in cls.__CLASSIFIED_ENTRY_POINTS.items():
            if f_funcWrapped in lEntryPoints:
                return xEpType
        return CEntrypointInformation.EEntryType.UNKNOWN

    @classmethod
    def GetEntryInterfaceDoc(cls, f_funcWrapped):
        if f_funcWrapped in cls.__ENTRY_INTERFACE_DOCS:
            return cls.__ENTRY_INTERFACE_DOCS[f_funcWrapped]
        return None

    @classmethod
    def Functions(cls, f_entryPtType: EEntryType):
        """when entry points are inspected, the function collection that
        refers to on eyntry point type can be accessed"""
        return cls.__CLASSIFIED_ENTRY_POINTS[f_entryPtType]
        pass

    def IsPatternInside(self, f_sFindPattern: str):
        return (
            (f_sFindPattern in self.ID)
            or (f_sFindPattern in self.module_name)
            or (f_sFindPattern in self.objname)
        )

    def __str__(self) -> str:
        if self.entry in (self.EEntryType.UNDEFINED, self.EEntryType.UNKNOWN):
            return f"{self._Header()}: ???? name='{self.module_name}'"

        sStart = str(self.definition)[:70]
        sEnd = str(self.definition)[-30:]

        sFilenamePath = self.filename.replace("\\", "/").split("/")
        sFilename_wo_extension = sFilenamePath[-1]
        if len(self.objname) > 0:
            sFilename_wo_extension += f" - {self.objname}"
        return f"{self._Header()}: name='{self.module_name}'\nfile_object='{sFilename_wo_extension}'\ndescription='{sStart}....{sEnd}'"

    def __repr__(self) -> str:
        return self.__str__()

    def _Header(self) -> str:
        return f"<CEptInfo[{self.entry.name}:{self.ID}]>"

    def Open(self):
        if self.entry in (self.EEntryType.UNDEFINED, self.EEntryType.UNKNOWN):
            print(f"Can't open the entry point: {self}")
        else:
            os.system(f"code -g {self.filename} -r")

    @staticmethod
    def Names():
        """wegen des zusaetzlichen Properties reicht das normale fields() nicht aus"""
        n = [f.name for f in fields(CEntrypointInformation)]
        n += [
            key
            for key, value in CEntrypointInformation.__dict__.items()
            if isinstance(value, property)
        ]
        return n

    # as abbreviation the merged filename (wo path) and object
    # e.g.: 'collection_std.py - LoadCollections'
    @property
    def file_object(self):
        sFilenamePath = self.filename.replace("\\", "/").split("/")
        sFilename_wo_extension = sFilenamePath[-1]
        if len(self.objname) > 0:
            sFilename_wo_extension += f" - {self.objname}"
        return sFilename_wo_extension

    # as special hint the header and the definition
    # e.g.: <CEptInfo[FUNCTION:/catharsys/blender/generate/collection/load:1.0]>
    #       some description
    @property
    def help(self) -> str:
        if (
            self.entry == self.EEntryType.UNDEFINED
            or self.entry == self.EEntryType.UNKNOWN
        ):
            return f"\nCan't help in case of that entry point: {self}"

        return f"{self._Header()}\n{self.definition}"

    # protected class attributes
    __CLASSIFIED_ENTRY_POINTS: ClassVar[defaultdict] = defaultdict(
        lambda: list(), dict()
    )
    __ENTRY_INTERFACE_DOCS: ClassVar[dict] = dict()


# endclass
