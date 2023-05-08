#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /cls_loopconfigs.py
# Created Date: Thursday, October 22nd 2020, 4:26:28 pm
# Author: Christian Perwass
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

#####################################################################
# Class that implements nested configuration loops based on a scheme
import os
import copy
from pathlib import Path
from anybase import path
from catharsys.util import config
from catharsys.util.cls_configcml import CConfigCML
from catharsys.decs.decorator_log import logFunctionCall
from catharsys.config.cls_project import CProjectConfig
import ison

# from timeit import default_timer as timer


class CLoopConfigs:

    xPrjCfg: CProjectConfig = None
    pathCfgFile: Path = None

    lScheme: list = None
    dicCfgCache: dict = None

    sId: str = None
    sCfgPath: str = None
    sCfgFilename: str = None

    #################################################################
    # Constructor
    def __init__(self, *, xPrjCfg, sId, sCfgFilePath, lScheme):

        self.sId = sId

        self.xPrjCfg = xPrjCfg
        self.pathCfgFile = path.MakeNormPath(sCfgFilePath)
        self.sCfgPath = self.pathCfgFile.parent.as_posix()
        self.sCfgFilename = self.pathCfgFile.name

        self.lScheme = copy.deepcopy(lScheme)

        # Initialize loop
        self.Init()

    # enddef

    #################################################################
    # Getter/Setter

    def GetId(self):
        return self.sId

    # enddef

    def GetTotalStepCount(self):
        return self.iTotalCnt

    # enddef

    def GetTotalStepIdx(self):
        return self.iTotalIdx

    # enddef

    #################################################################
    # Get current value of level config
    def _GetLevelValue(self, _dicLevel):

        iIdx = _dicLevel.get("iIdx")
        lValues = _dicLevel.get("lValues")
        return lValues[iIdx]

    # enddef

    #################################################################
    # Check whether given level is filtered
    def IsFiltered(self, _dicLevel, _xCfgVars):

        sId = _dicLevel.get("sId")
        self._SetCfgVarsCurrentId(_xCfgVars, sId)

        sFilter = _dicLevel.get("sFilter")

        sCfgFilter = None
        dicId = _xCfgVars.GetVarData().get("id")
        dicCfg = dicId.get(sId)
        xCfgValue = dicCfg.get("value")
        # xCfgValue = _xCfgVars.GetVarData().get("value")
        if xCfgValue is not None and isinstance(xCfgValue, dict):
            sCfgFilter = xCfgValue.get("sFilter")
        # endif

        sEval = None
        sCfgEval = None

        try:
            if sFilter is not None:
                sEval = _xCfgVars.Process(sFilter)
            # endif

            if sCfgFilter is not None:
                sCfgEval = _xCfgVars.Process(sCfgFilter)
            # endif
        except Exception as xEx:
            raise Exception("Error in filter for config with id '{0}':\n{1}".format(sId, str(xEx)))
        # endtrty

        try:
            bTest = True
            bCfgTest = True

            if sEval is not None:
                bTest = eval(sEval)
            # endif

            if sCfgEval is not None:
                bCfgTest = eval(sCfgEval)
            # endif

        except Exception as xEx:
            raise Exception(
                "Error in filter for config with id '{0}': " "cannot execute filter expression\n{1}".format(sId, xEx)
            )
        # endtry

        return not (bTest and bCfgTest)

    # enddef

    #################################################################
    def _SetCfgVarsCurrentId(self, _xCfgVars, _sId):

        dicVar = _xCfgVars.GetVarData()
        dicVarCfgId = dicVar.get("id")
        dicVarCfgMeta = dicVarCfgId.get(_sId)
        dicVarCfgId["@this"] = _xCfgVars.GetVarDataRef(["id", _sId], bLiteral=True)
        dicVarCfgId["@parent"] = dicVarCfgMeta.get("parent")
        dicVarCfgId["@child"] = dicVarCfgMeta.get("child")
        dicVar["value"] = _xCfgVars.GetVarDataRef(["id", _sId, "value"], bLiteral=True)

    # enddef

    #################################################################
    # Get config data for current loop step
    @logFunctionCall
    def GetData(self, dicCfgVars={}, *, dicRuntimeVars=None, setRuntimeVarsEval=None):

        if self.iTotalIdx < 0 or self.iTotalIdx >= self.iTotalCnt:
            raise Exception("Loop index ({0}) out of range.".format(self.iTotalIdx))
        # endif

        dicVars = copy.deepcopy(dicCfgVars)

        lCfgIds = []
        lCfgIdFolders = []
        dicCfgIdMeta = {}
        dicActCfgIdFolders = {}
        lAct = []
        lIds = []
        dicData = {}
        xConfigCML = CConfigCML(
            xPrjCfg=self.xPrjCfg, dicConstVars=dicCfgVars, dicRtVars=dicRuntimeVars, setRtVarsEval=setRuntimeVarsEval
        )

        # dTimeStart = timer()

        for dicLevel in self.lScheme:

            xConfigCML.Clear()

            iIdx = dicLevel.get("iIdx")
            sDti = dicLevel.get("sDTI")
            sForm = dicLevel.get("sForm")
            sId = dicLevel.get("sId")
            sAct = dicLevel.get("sAction")
            if sAct not in lAct:
                lAct.append(sAct)
            # endif
            sFolderFormat = dicLevel.get("sFolderFormat", "")
            sFolderPrefix = dicLevel.get("sFolderPrefix", "")
            lFolderPrefix = sFolderPrefix.split("/")
            bAddToPath = dicLevel.get("bAddToPath", True) and dicLevel.get("iAddToPath", 1) != 0
            lValues = dicLevel.get("lValues")

            lIds.append(sId)

            lData = dicData.get(sDti)
            if lData is None:
                lData = dicData[sDti] = []
            # endif

            dicCfg = None
            if sForm == "file/json":
                pathCfgFile = config.ProvideReadFilepathExt((self.sCfgPath, lValues[iIdx]))
                sFpCfg = pathCfgFile.as_posix()
                dicCfgData = self.dicCfgCache.get(sFpCfg)
                if dicCfgData is None:
                    # print(f"adding to cache: {sFpCfg}")
                    dicPathVars = self.xPrjCfg.GetFilepathVarDict(sFpCfg)
                    dicCfg = config.Load(
                        (self.sCfgPath, lValues[iIdx]),
                        sDTI=sDti,
                        dicCustomVars=dicPathVars,
                        bAddPathVars=True,
                    )

                    if "sId" in dicCfg:
                        lId = xConfigCML.Process(
                            dicCfg,
                            lProcessPaths=["sId"],
                            sImportPath=dicCfg["__locals__"]["path"],
                        )
                        sCfgId = lId[0]["sId"]
                    else:
                        sCfgId = "_"
                    # endif

                    if len(sFolderFormat) > 0:
                        sCfgId = sFolderFormat.format(sCfgId)
                    # endif

                    dicCfgData = self.dicCfgCache[sFpCfg] = {}
                    dicCfgData["dicCfg"] = dicCfg
                    dicCfgData["sCfgId"] = sCfgId

                else:
                    # print(f"loading from cache: {sFpCfg}")
                    dicCfg = dicCfgData["dicCfg"]
                    sCfgId = dicCfgData["sCfgId"]
                # endif

                lData.append(dicCfg)

            elif sForm == "value" or sForm == "const-value":
                xValue = lValues[iIdx]
                lData.append(xValue)
                if isinstance(xValue, dict):
                    sCfgId = xValue.get("sId", "_")
                    if len(sFolderFormat) > 0:
                        sCfgId = sFolderFormat.format(sCfgId)
                    # endif
                else:
                    if len(sFolderFormat) > 0:
                        sCfgId = sFolderFormat.format(xValue)
                    else:
                        sCfgId = str(xValue)
                    # endif
                # endif
            else:
                raise Exception("Unsupported config data form '{0}'.".format(sForm))
            # endif

            lCfgIds.append(sCfgId)
            if bAddToPath:
                # Construct list of folders per actions
                if sAct not in dicActCfgIdFolders:
                    dicActCfgIdFolders[sAct] = []
                # endif
                lActCfgIdFolders = dicActCfgIdFolders.get(sAct)

                if len(lFolderPrefix) > 1:
                    lCfgIdFolders.extend(lFolderPrefix[0:-1])
                    lActCfgIdFolders.extend(lFolderPrefix[0:-1])
                # endif

                # HACK to support relative paths within values and ids
                if sCfgId == "." or sCfgId == "..":
                    sCfgIdFolder = sCfgId
                else:
                    sCfgIdFolder = lFolderPrefix[-1] + sCfgId.replace(".", "_").replace(" ", "_")
                # endif
                # Due to the "sFolderFormat" option, sCfgId may also include '/'.
                # So, here we need to split the resultant config folder again by '/'
                # and add potentiel subfolders to the folder list.
                lFolder = sCfgIdFolder.split("/")
                if len(lFolder) > 1:
                    lCfgIdFolders.extend(lFolder[0:-1])
                    lActCfgIdFolders.extend(lFolder[0:-1])
                    sCfgIdFolder = lFolder[-1]
                # endif

                lCfgIdFolders.append(sCfgIdFolder)
                lActCfgIdFolders.append(sCfgIdFolder)
            # endif

            # Dictionary per config, containing for example the relative path
            dicCfgIdMeta[sId] = {
                "sDTI": sDti,
                "iDataListIdx": len(lData) - 1,
                "sFolder": sCfgIdFolder if bAddToPath else None,
                "sRelPathCfg": os.path.normpath(os.path.sep.join(lCfgIdFolders)),
                "iCfgIdx": len(lCfgIds) - 1,
                "sCfgId": sCfgId,
            }
        # endfor
        # dTimeEnd = timer()
        # print("Load configs: {}s".format(dTimeEnd - dTimeStart))

        sRelPathTrgMain = path.MakeNormPath((self.sId, lCfgIdFolders)).as_posix()

        dicRelPathTrgAct = {}
        sRelPath = self.sId
        for sAct in lAct:
            if sAct in dicActCfgIdFolders:
                sRelPath = "/".join([sRelPath, "/".join(dicActCfgIdFolders.get(sAct))])
            # endif
            dicRelPathTrgAct[sAct] = sRelPath
        # endfor

        ####################################################
        # Create variables for replacement in config files.
        dicVars["trial-id"] = self.sId
        dicVars["rel-path-trg"] = sRelPathTrgMain
        dicVars["path-trg"] = os.path.join(self.xPrjCfg.pathActProd, sRelPathTrgMain)

        ###################################
        # Create variables for key 'action'
        dicVarAct = {}
        for sAct in lAct:
            dicVarAct[sAct] = {"rel-path-trg": dicRelPathTrgAct.get(sAct)}
        # endfor
        dicVars["actions"] = dicVarAct

        ###################################
        # Variables for the 'id' key:
        dicVarCfgId = {}
        for sId, dicCfgMeta in dicCfgIdMeta.items():
            sDti = dicCfgMeta.get("sDTI")
            iDataListIdx = dicCfgMeta.get("iDataListIdx")

            dicVarCfgId[sId] = {
                "cfg-id": dicCfgMeta.get("sCfgId"),
                "rel-path-cfg": dicCfgMeta.get("sRelPathCfg"),
                "folder": dicCfgMeta.get("sFolder"),
                "dti": sDti,
                "value": copy.deepcopy(dicData.get(sDti)[iDataListIdx]),
            }
        # endfor
        dicVars["id"] = dicVarCfgId

        # Create config vars instance
        xCfgVars = CConfigCML(
            xPrjCfg=self.xPrjCfg,
            dicConstVars=dicVars,
            sImportPath=self.sCfgPath,
            dicRtVars=dicRuntimeVars,
            setRtVarsEval=setRuntimeVarsEval,
        )

        # Create parent/child references
        dicVarCfgId = xCfgVars.GetVarData().get("id")
        for sId, dicCfgMeta in dicCfgIdMeta.items():
            iCfgIdx = dicCfgMeta.get("iCfgIdx")
            sParentId = None if iCfgIdx <= 0 else lIds[iCfgIdx - 1]
            sChildId = None if iCfgIdx >= len(lIds) - 1 else lIds[iCfgIdx + 1]

            # dicVarCfgId.get(sId).update({
            #     "parent": "" if sParentId is None else sParentId,
            #     "child": "" if sChildId is None else sChildId,
            # })
            dicVarCfgId.get(sId).update(
                {
                    "parent": {"dti": ""}
                    if sParentId is None
                    else xCfgVars.GetVarDataRef(["id", sParentId], bLiteral=True),
                    "child": {"dti": ""}
                    if sChildId is None
                    else xCfgVars.GetVarDataRef(["id", sChildId], bLiteral=True),
                }
            )
        # endfor

        ######################################################################
        # Process all config variables

        # dTimeStart = timer()

        # Pre-process all configs first and then parse them normally.
        for iProcPass in range(2):
            bPreProcessOnly = iProcPass == 0

            for sId, dicCfgMeta in dicCfgIdMeta.items():
                self._SetCfgVarsCurrentId(xCfgVars, sId)

                sDti = dicCfgMeta.get("sDTI")
                iDataListIdx = dicCfgMeta.get("iDataListIdx")
                lCfgData = dicData.get(sDti)
                xCfg = lCfgData[iDataListIdx]
                if isinstance(xCfg, dict):
                    sImportPath = config.GetDictValue(
                        xCfg,
                        "__locals__/path",
                        str,
                        bAllowKeyPath=True,
                        sWhere="configuration data",
                    )
                    # sImportPath = config.GetElementAtPath(xCfg, "__locals__/path")
                    # sFpCmlVars = os.path.join(sImportPath, "cml-vars_{0}.json".format(sId.replace("/", "_")))
                    # file.SaveJson(sFpCmlVars, xCfgVars.GetVarData(), iIndent=4)
                else:
                    sImportPath = None
                # endif

                try:
                    lCfgData[iDataListIdx] = xCfgVars.Process(
                        xCfg, sImportPath=sImportPath, bPreProcessOnly=bPreProcessOnly
                    )
                except ison.ParserError as xEx:
                    sFpConfig = config.GetDictValue(
                        xCfg,
                        "__locals__/filepath",
                        str,
                        bAllowKeyPath=True,
                        sWhere="configuration data",
                    )
                    sFilename = config.GetDictValue(
                        xCfg,
                        "__locals__/filename",
                        str,
                        bAllowKeyPath=True,
                        sWhere="configuration data",
                    )

                    # sFpConfig = config.GetElementAtPath(xCfg, "__locals__/filepath")
                    # sFilename = config.GetElementAtPath(xCfg, "__locals__/filename")

                    sMsg = (
                        "Error parsing configuration:\n"
                        "> Trial ID: {}\n"
                        "> Trial data list index: {}\n"
                        "> DTI: {}\n"
                        "> File: {}\n"
                        "> Import Path: {}\n"
                        "> File Path: {}\n"
                        "> PreProc only: {}\n"
                        "Parsing trace:\n"
                        "{}\n".format(
                            sId,
                            iDataListIdx,
                            sDti,
                            sFilename,
                            sImportPath,
                            sFpConfig,
                            bPreProcessOnly,
                            xEx.ToString(),
                        )
                    )
                    raise Exception(sMsg)
                # endtry
            # endfor
        # endfor processing pass

        # dTimeEnd = timer()
        # print("Process configs: {}s".format(dTimeEnd - dTimeStart))

        ######################################################################
        # Update dicVarData with processed configs
        dicVarCfgId = xCfgVars.GetVarData().get("id")
        for sId, dicCfgMeta in dicCfgIdMeta.items():
            sDti = dicCfgMeta.get("sDTI")
            iDataListIdx = dicCfgMeta.get("iDataListIdx")
            xCfgData = dicData.get(sDti)[iDataListIdx]

            # If the processed dictionary contains a reference to an
            # id dictionary, need make sure that this is not replaced
            # by the processed dictionary. So here is a roundabout way
            # to make a copy into a new dictionary.
            dicId = dicVarCfgId[sId]
            dicNewId = dicVarCfgId[sId] = {}
            for sKey in dicId:
                if sKey != "value":
                    dicNewId[sKey] = dicId[sKey]
                # endif
            # endfor
            dicNewId["value"] = copy.deepcopy(xCfgData)
            # dicVarCfgId.get(sId)["value"] = copy.deepcopy(xCfgData)
        # endfor

        ######################################################################
        # Process and test all manifest and config filters
        for dicLevel in self.lScheme:
            if self.IsFiltered(dicLevel, xCfgVars):
                return None
            # endif
        # endfor

        return {
            "mData": dicData,
            "lIds": lIds,
            "lCfgIdFolders": lCfgIdFolders,
            "lCfgIds": lCfgIds,
            "mCfgIdMeta": dicCfgIdMeta,
            "sRelPathTrgMain": sRelPathTrgMain,
            "dicRelPathTrgAct": dicRelPathTrgAct,
            "lActions": lAct,
        }

    # enddef

    #################################################################
    # Initialize loop
    def Init(self):

        if len(self.lScheme) == 0:
            self.iTotalCnt = 0
        else:
            self.iTotalCnt = 1

            for dicLevel in self.lScheme:
                dicLevel["iIdx"] = 0
                iCnt = len(dicLevel["lValues"])
                self.iTotalCnt *= iCnt
                dicLevel["iCnt"] = iCnt
            # endfor
        # endif

        # Need to call Next() once to make first step active
        self.iTotalIdx = -1

        # Reset configuration file cache
        self.dicCfgCache = {}

    # enddef

    #################################################################
    # Step the loop
    def Next(self):

        bOK = True
        iLevelCnt = len(self.lScheme)

        if iLevelCnt == 0:
            self.iTotalIdx = -1
            return False
        # endif

        if self.iTotalIdx < 0:
            self.iTotalIdx = 0
            return True
        # endif

        self.iTotalIdx += 1

        for iLevelIdx in range(iLevelCnt - 1, -1, -1):
            dicLevel = self.lScheme[iLevelIdx]

            iIdx = dicLevel.get("iIdx") + 1
            if iIdx < dicLevel.get("iCnt"):
                dicLevel["iIdx"] = iIdx
                break
            else:
                dicLevel["iIdx"] = 0
                if iLevelIdx == 0:
                    bOK = False
                # endif
            # endif
        # endfor

        return bOK

    # enddef


# endclass
