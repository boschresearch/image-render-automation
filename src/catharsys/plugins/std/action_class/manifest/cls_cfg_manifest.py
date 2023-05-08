#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /manifest.py
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

# Class to handle manifest files
import os
import copy
from anybase.cls_any_error import CAnyError_Message
from catharsys.util import config
from catharsys.util.cls_configcml import CConfigCML
from anybase import convert, path
import ison
from pathlib import Path

from catharsys.decs.decorator_log import logFunctionCall


class CConfigManifest:
    def __init__(self, *, xPrjCfg):
        self.dicM = {}
        self.dicCfgGrps = {}
        self.xPrjCfg = xPrjCfg

    # enddef

    ######################################################################################
    # Load Manifest from file
    def LoadFile(self, _xFilepath):

        pathFile = config.ProvideReadFilepathExt(_xFilepath)
        dicVars = self.xPrjCfg.GetFilepathVarDict(pathFile)
        self.dicM = config.Load(pathFile, sDTI="manifest:1.0", dicCustomVars=dicVars, bAddPathVars=True)
        xCML = CConfigCML(xPrjCfg=self.xPrjCfg, sImportPath=pathFile.parent)
        self.dicM = xCML.Process(self.dicM)

        self.dicCfgGrps = {}

        dicCGs = self.dicM.get("mConfigGroups", {})
        lPaths = config.GetDictPaths(dicCGs)
        for sCG in lPaths:
            self.dicCfgGrps[sCG] = self._ConstructConfigGroup(sCG, dicCGs, [])
        # endfor

    # enddef

    ######################################################################################
    # Recursive function to construct config groups which may include other
    # config groups.
    def _ConstructConfigGroup(self, _sCfgGrp, _dicCfgGrps, _lCfgGrpIdList):

        if _sCfgGrp in _lCfgGrpIdList:
            raise Exception("Dependency loop detected at config group '{0}'.".format(_sCfgGrp))
        # endif

        lCfgs = config.GetDictValue(
            _dicCfgGrps,
            _sCfgGrp,
            list,
            bAllowKeyPath=True,
            sWhere="manifest",
            sMsgNotFound="Configuration group '{sKey}' not defined in {sWhere}",
        )
        # lCfgs = config.GetElementAtPath(_dicCfgGrps, _sCfgGrp, sTypename="Config group")
        # if lCfgs is None:
        #     raise Exception("Configuration group '{0}' not defined in manifest".format(_sCfgGrp))
        # # endif

        lCfgGrpIdList = copy.deepcopy(_lCfgGrpIdList)
        lCfgGrpIdList.append(_sCfgGrp)

        lCombCfg = []
        for dicCfg in lCfgs:
            sSubCfgGrp = dicCfg.get("sConfigGroup")
            if sSubCfgGrp is not None:
                lCombCfg.extend(self._ConstructConfigGroup(sSubCfgGrp, _dicCfgGrps, lCfgGrpIdList))
            else:
                lCombCfg.append(dicCfg)
            # endif
        # endfor

        return lCombCfg

    # enddef

    ######################################################################################
    # Recursive function to construct config list from actions with dependencies
    def _ConstructConfigList(self, _sAction, _dicActions, _lActList):

        if _sAction in _lActList:
            raise Exception("Dependency loop detected at action '{0}'.".format(_sAction))
        # endif

        dicAct = config.GetDictValue(
            _dicActions,
            _sAction,
            dict,
            bAllowKeyPath=True,
            sWhere="manifest",
            sMsgNotFound="Action '{sKey}' not defined in {sWhere}",
        )
        # try:
        #     dicAct = config.GetElementAtPath(_dicActions, _sAction, bRaiseException=True)
        # except Exception as xEx:
        #     raise CAnyError_Message(sMsg="Action '{0}' not defined in manifest".format(_sAction),
        #                             xChildEx=xEx)
        # # endif

        lActList = copy.deepcopy(_lActList)
        lActList.append(_sAction)

        lDeps = dicAct.get("lDeps", [])
        lTrgCfg = []
        for sDep in lDeps:
            lTrgCfg.extend(self._ConstructConfigList(sDep, _dicActions, lActList))
        # endfor

        lSrcCfg = dicAct.get("lConfigs", [])
        for dicCfg in lSrcCfg:
            sCfgGrp = dicCfg.get("sConfigGroup")
            if sCfgGrp is not None:
                lCfgGrp = self.dicCfgGrps.get(sCfgGrp)
                if lCfgGrp is None:
                    raise Exception("Configuration group '{0}' not found in manifest.".format(sCfgGrp))
                # endif
                lCfgGrp = copy.deepcopy(lCfgGrp)
                for dicX in lCfgGrp:
                    dicX["sAction"] = _sAction
                # endfor
                lTrgCfg.extend(lCfgGrp)
            else:
                dicX = copy.deepcopy(dicCfg)
                dicX["sAction"] = _sAction
                lTrgCfg.append(dicX)
            # endif
        # endfor

        return lTrgCfg

    # enddef

    ######################################################################################
    def _GetControlLoopIterCfg(
        self, *, _iIdx: int, _dicIterCfg: dict, _dicCtrl: dict, _xCML: CConfigCML, _sImportPath: str
    ) -> dict:

        dicCtrlIter = {}
        if _dicIterCfg is not None:
            dicCtrlIter = copy.deepcopy(_dicIterCfg)
        # endif

        # Execute lambda function call on dicCtrlIter with parameter str(iIdx)
        dicCtrlIter = ison.lambda_parser.Parse(dicCtrlIter, [str(_iIdx)])

        # Add locally defined variables from loop config
        for sVarType in [
            "__locals__",
            "__globals__",
            "__eval_locals__",
            "__eval_globals__",
            "__func_locals__",
            "__func_globals__",
            "__runtime_vars__",
        ]:
            if sVarType not in _dicCtrl:
                continue
            # endif

            if sVarType in dicCtrlIter:
                dicCtrlIter[sVarType].update(_dicCtrl[sVarType])
            else:
                dicCtrlIter[sVarType] = copy.deepcopy(_dicCtrl[sVarType])
            # endif
        # endfor

        # Store 'sId' in 'sCtrlId'
        dicCtrlIter["sCtrlId"] = _dicCtrl.get("sId", "_")

        # Replace 'sId' with the processed 'dIterId' if it exists
        if "sId" not in dicCtrlIter:
            dicCtrlIter["sId"] = str(_iIdx)
        else:
            # process 'sId' in case it contains functions/variables
            lProcId = _xCML.Process(
                dicCtrlIter,
                sImportPath=_sImportPath,
                lProcessPaths=["sId"],
            )
            dicCtrlIter["sId"] = convert.DictElementToString(lProcId[0], "sId")
        # endif

        # add element 'idx' to config
        dicCtrlIter["idx"] = _iIdx

        # set iteration DTI
        dicCtrlIter["sDTI"] = "/catharsys/manifest/control/loop/iter:1.0"

        return dicCtrlIter

    # endif

    ######################################################################################
    def _ProcessControlLoopRange(self, *, _dicCfgVars: dict, _pathCfgFile: Path, _dicCtrl: dict) -> list:

        xCML = CConfigCML(xPrjCfg=self.xPrjCfg, dicConstVars=_dicCfgVars)

        sImportPath = _pathCfgFile.as_posix()
        lRange = xCML.Process(
            _dicCtrl,
            sImportPath=sImportPath,
            lProcessPaths=["iMin", "iMax", "iStep", "lActiveIndices"],
        )
        logFunctionCall.PrintLog(f"range{lRange}")

        if lRange[0] is None:
            raise Exception(f"No minimal value given for loop in config file '{_pathCfgFile.name}'")
        # endif
        iMin = convert.DictElementToInt(lRange[0], "iMin")

        if lRange[1] is None:
            raise Exception(f"No maximal value given for loop in config file '{_pathCfgFile.name}'")
        # endif
        iMax = convert.DictElementToInt(lRange[1], "iMax")

        iStep = convert.DictElementToInt(lRange[2], "iStep", iDefault=1)

        if lRange[3] is not None:
            lActiveIndices = convert.DictElementToIntList(lRange[3], "lActiveIndices")
            if len(lActiveIndices) == 0:
                raise RuntimeError(f"Active index list is empty in loop config file '{_pathCfgFile.name}'")
            # endif
        else:
            lActiveIndices: list = None
        # endif

        dicIterCfg = _dicCtrl.get("mIterationConfig")
        lCtrlValues: list = []

        for iIdx in range(iMin, iMax + 1, iStep):

            if lActiveIndices is not None and iIdx not in lActiveIndices:
                continue
            # endif

            dicCtrlIter = self._GetControlLoopIterCfg(
                _iIdx=iIdx, _dicIterCfg=dicIterCfg, _dicCtrl=_dicCtrl, _xCML=xCML, _sImportPath=sImportPath
            )
            dicCtrlIter["iMin"] = iMin
            dicCtrlIter["iMax"] = iMax
            dicCtrlIter["iStep"] = iStep

            # add iter config to value list
            lCtrlValues.append(dicCtrlIter)
        # endfor

        return lCtrlValues

    # enddef

    ######################################################################################
    def _ProcessControlLoopList(self, *, _dicCfgVars: dict, _pathCfgFile: Path, _dicCtrl: dict) -> list:

        xCML = CConfigCML(xPrjCfg=self.xPrjCfg, dicConstVars=_dicCfgVars)

        sImportPath = _pathCfgFile.as_posix()
        lRange = xCML.Process(
            _dicCtrl,
            sImportPath=sImportPath,
            lProcessPaths=["lIndices", "iMin", "iMax", "iStep"],
        )
        logFunctionCall.PrintLog(f"range{lRange}")

        if lRange[0] is None:
            raise Exception(f"No index list given in element 'lIndices' for loop in config file '{_pathCfgFile.name}'")
        # endif
        lIndices = convert.DictElementToIntList(lRange[0], "lIndices")

        if len(lIndices) == 0:
            raise RuntimeError(f"Index list has no elements in loop config file '{_pathCfgFile.name}'")
        # endif

        if lRange[1] is not None:
            iMin = convert.DictElementToInt(lRange[1], "iMin")
            if iMin < 0 or iMin >= len(lIndices):
                raise RuntimeError(
                    f"Minimum index '{iMin}' is out of bounds for index list of length '{(len(lIndices))}'"
                )
            # endif

        else:
            iMin = 0
        # endif

        if lRange[2] is not None:
            iMax = convert.DictElementToInt(lRange[2], "iMax")
            if iMax < 0:
                iMax = len(lIndices) - 1
            elif iMax >= len(lIndices):
                raise RuntimeError(
                    f"Maximum index '{iMax}' is out of bounds for index list of length '{(len(lIndices))}'"
                )
            # endif

            if iMax < iMin:
                raise RuntimeError(
                    f"Maximum index '{iMax}' is smaller that minimum index '{iMin}' "
                    f"in loop config file '{_pathCfgFile.name}'"
                )
            # endif
        else:
            iMax = len(lIndices) - 1
        # endif

        iStep = convert.DictElementToInt(lRange[3], "iStep", iDefault=1)

        dicIterCfg = _dicCtrl.get("mIterationConfig")
        lCtrlValues: list = []

        for iListIdx in range(iMin, iMax + 1, iStep):

            # The actual index to use
            iIdx: int = lIndices[iListIdx]

            dicCtrlIter = self._GetControlLoopIterCfg(
                _iIdx=iIdx, _dicIterCfg=dicIterCfg, _dicCtrl=_dicCtrl, _xCML=xCML, _sImportPath=sImportPath
            )

            # add iter config to value list
            lCtrlValues.append(dicCtrlIter)
        # endfor

        return lCtrlValues

    # enddef

    ######################################################################################
    # Get list of configs from trial dictionary for given action
    @logFunctionCall
    def GetTrialConfigs(self, _sAction, _dicTrial, *, dicCfgVars):

        dicActions = self.dicM.get("mActions")
        if dicActions is None:
            raise Exception("Manifest does not contain any action definitions")
        # endif

        dicTrialCfg = _dicTrial.get("mConfigs")
        if dicTrialCfg is None:
            raise Exception("Trial data does not contain configurations")
        # endif

        # Get hierarchy of config types from manifest for selected action
        lConfigs = self._ConstructConfigList(_sAction, dicActions, [])

        # Add list of configs from trial to config list
        for dicCfg in lConfigs:
            sCfgId = dicCfg["sId"]
            sCfgForm = dicCfg["sForm"]
            sCfgDti = dicCfg["sDTI"]
            logFunctionCall.PrintLog(f"trial[{sCfgId}] : {sCfgDti}")

            if sCfgForm == "const-value":
                lValues = dicCfg.get("lValues")
                if lValues is None:
                    raise Exception(
                        "Configuration with id '{0}' "
                        "in manifest is of type 'const-value' "
                        "but has no values specified.".format(sCfgId)
                    )
                # endif
            else:
                lValues = config.GetDictValue(
                    dicTrialCfg,
                    sCfgId,
                    list,
                    bAllowKeyPath=True,
                    sWhere="trial file",
                    sMsgNotFound="Configurations with id '{sKey}' not found in {sWhere}",
                )

                # lValues = config.GetElementAtPath(dicTrialCfg, sCfgId)
                # if lValues is None:
                #     raise Exception("Configurations with id '{0}' not present in trial file"
                #                     .format(sCfgId))
                # # endif

                # Process manifest control configs
                dicRes = config.CheckDti(sCfgDti, "/catharsys/manifest/control/*:*")
                if dicRes["bOK"] is True and sCfgForm.startswith("file/"):
                    lCtrlValues = []
                    sTrialPath = config.GetDictValue(
                        _dicTrial,
                        "__locals__/path",
                        str,
                        bAllowKeyPath=True,
                        sWhere="trial file",
                    )
                    # sTrialPath = config.GetElementAtPath(_dicTrial, "__locals__/path")

                    for sFileCtrlCfg in lValues:

                        pathCfgFile = config.ProvideReadFilepathExt((sTrialPath, sFileCtrlCfg))
                        dicVars = self.xPrjCfg.GetFilepathVarDict(pathCfgFile)
                        dicCtrlLoad = config.Load(
                            pathCfgFile,
                            sDTI=sCfgDti,
                            dicCustomVars=dicVars,
                            bDoThrow=False,
                            bAddPathVars=True,
                        )
                        if dicCtrlLoad["bOK"] is False:
                            raise Exception(
                                "Error loading manifest loop configuration file "
                                "'{0}' at path '{1}':\n{2}".format(sFileCtrlCfg, sTrialPath, dicCtrlLoad["sMsg"])
                            )
                        # endif
                        dicCtrl = dicCtrlLoad["dicCfg"]
                        dicCtrlDti = config.SplitDti(dicCtrl["sDTI"])

                        lCtrlType = dicCtrlDti["lType"][3:]
                        lCtrlVer = dicCtrlDti["lVersion"]

                        if lCtrlType[0] == "loop" and lCtrlType[1] == "range" and lCtrlVer[0] == 1:
                            lCtrlValues.extend(
                                self._ProcessControlLoopRange(
                                    _dicCfgVars=dicCfgVars, _pathCfgFile=pathCfgFile, _dicCtrl=dicCtrl
                                )
                            )

                        elif lCtrlType[0] == "loop" and lCtrlType[1] == "list" and lCtrlVer[0] == 1:
                            lCtrlValues.extend(
                                self._ProcessControlLoopList(
                                    _dicCfgVars=dicCfgVars, _pathCfgFile=pathCfgFile, _dicCtrl=dicCtrl
                                )
                            )

                        else:
                            raise Exception(
                                "Unsupported manifest control configuration "
                                "for id '{0}' with DTI '{1}'.".format(sCfgId, sCfgDti)
                            )
                        # endif

                    # endfor loop config

                    # store loop indices as values in trial configuration
                    dicCfg["lValues"] = copy.deepcopy(lCtrlValues)
                    dicCfg["sForm"] = "value"

                else:
                    # no manifest control structure
                    dicCfg["lValues"] = copy.deepcopy(lValues)
                # endif config is manifest control structure
            # endif
        # endfor

        return lConfigs

    # enddef


# endclass
