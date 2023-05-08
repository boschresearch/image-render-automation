#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /actionmanifest.py
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

# Handle actions and execute
import os
import sys
import math
import copy
import random
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Optional

import ison
from ison.core.cls_parser_error import CParserError

from anybase.cls_any_error import CAnyError_Message, CAnyError_TaskMessage
from anybase import convert

from catharsys.util import config
from catharsys.util import path
from catharsys.util import file
from catharsys.decs.decorator_log import logFunctionCall
from catharsys.util.cls_configcml import CConfigCML
from catharsys.action import job
from catharsys.plugins.std.action_class.manifest.cls_cfg_manifest import CConfigManifest
from catharsys.plugins.std.action_class.manifest.cls_cfg_manifest_job import (
    CConfigManifestJob,
)
from catharsys.config.cls_project import CProjectConfig
from catharsys.config.cls_launch import CConfigLaunch
from catharsys.action.cls_actionclass_executor import CActionClassExecutor
from .cls_loopconfigs import CLoopConfigs

import concurrent.futures


class CActionClassManifestExecutor(CActionClassExecutor):

    ######################################################################################
    def __init__(
        self,
        *,
        xPrjCfg: CProjectConfig,
        sAction: str,
        dicActCfg: dict,
        xCfgLaunch: CConfigLaunch,
        dicActArgsOverride: Optional[dict] = None,
    ):

        self.xManifest: CConfigManifest = None
        self.dicActArgs: dict = None
        self.dicActGlobals: dict = None
        self.dicActionDti: dict = None
        self.dicTrial: dict = None
        self.dicExec: dict = None
        self.dicDebug: dict = None
        self.dicActGlobals: dict = None
        self.dicCfgVars: dict = None
        self.pathTrialFile: Path = None
        self.pathExecFile: Path = None
        self.pathManifestFile: Path = None
        self.lTrialCfgs: list = None
        self.lJobDistTypes: list = ["single;all", "frames;configs", "per-frame;configs"]
        self.sJobDistType: str = None
        self.sPathTrialConfig: str = None

        self.dicJobFutures: dict = {}

        super().__init__(
            xPrjCfg=xPrjCfg,
            sAction=sAction,
            dicActCfg=dicActCfg,
            xCfgLaunch=xCfgLaunch,
            dicActArgsOverride=dicActArgsOverride,
        )

        self.dicActArgs = config.GetDictValue(self.dicActions[sAction], "mConfig", dict, sWhere="action configuration")

        if not config.CheckDti(self.sActClsDti, "action/python/manifest-based:2.0"):
            raise Exception("Incompatible action configuration of type '{0}'.".format(self.sActClsDti))
        # endif

        self.sActDti = config.GetDictValue(self.dicActCfg, "sActionDTI", str, sWhere="action definition")

    # enddef

    ######################################################################################
    # Init Action
    @logFunctionCall
    def Init(self):

        # initialize configuration variables that are passed as constant variables,
        # when parsing the various configuration scripts
        self.dicCfgVars = self.xPrjCfg.GetFilepathVarDict(self.xPrjCfg.pathLaunchFile)

        # the action name
        self.dicCfgVars["action-name"] = self.sAction
        self.dicCfgVars["action-dti"] = self.sActDti

        # action configuration
        self.dicCfgVars["actcfg"] = copy.deepcopy(self.dicActCfg)
        # add the launch args to the variable dictionary, so that these
        # values can already be used when processing the trial configuration
        self.dicCfgVars["actargs"] = self.dicActArgs.copy()

        # Additional variable access
        self.dicCfgVars["action"] = {
            "name": self.sAction,
            "dti": self.sActDti,
            "config": self.dicCfgVars["actcfg"],
            "args": self.dicCfgVars["actargs"],
        }

        sJobDistType = self.dicActCfg.get("sJobDistType")
        if sJobDistType not in self.lJobDistTypes:
            raise Exception("Unsupported job distribution type '{0}'.".format(sJobDistType))
        # endif
        self.sJobDistType = sJobDistType

        self.sPathTrialConfig = self.xPrjCfg.sLaunchPath  # self.dicActArgs.get("sConfigPath")
        dicVars = self.xPrjCfg.GetFilepathVarDict(self.sPathTrialConfig)

        self.dicActGlobals = self.dicActions[self.sAction].get("__globals__")
        dicActEvalGlobals = self.dicActions[self.sAction].get("__eval_globals__")
        if isinstance(self.dicActGlobals, dict) and isinstance(dicActEvalGlobals, dict):
            ison.util.data.UpdateDict(self.dicActGlobals, dicActEvalGlobals, "launch", bAllowOverwrite=True)
        # endif
        if isinstance(self.dicActGlobals, dict):
            ison.util.data.UpdateDict(self.dicCfgVars, self.dicActGlobals, "launch")
        # endif

        # raise RuntimeError("DEBUG")
        ######################################################################################
        # Load & process TRIAL configuration
        sTrialFile = self.dicActArgs.get("sTrialFile")
        if sTrialFile is None:
            raise CAnyError_Message(sMsg="No trial file specified in launch arguments. ('sTrialFile' element missing)")
        # endif

        self.pathTrialFile = config.ProvideReadFilepathExt((self.sPathTrialConfig, sTrialFile))
        xCML = CConfigCML(
            xPrjCfg=self.xPrjCfg,
            dicConstVars=self.dicCfgVars,
            sImportPath=self.pathTrialFile.as_posix(),
            dicRtVars=self.xCfgLaunch.dicRuntimeVars,
            setRtVarsEval=self.xCfgLaunch.setRuntimeVarsEval,
        )

        self.dicTrial = config.Load(self.pathTrialFile, sDTI="trial:1", bAddPathVars=True, dicCustomVars=dicVars)
        try:
            self.dicTrial = xCML.Process(self.dicTrial)
        except CParserError as xEx:
            raise CAnyError_TaskMessage(sTask="Processing trial configuration", sMsg=xEx.ToString())
        # endtry

        # add the processed trial data to the variables, so that
        # they can be used when processing the execution config
        self.dicCfgVars["trial"] = copy.deepcopy(self.dicTrial)

        ######################################################################################
        # Load & process EXECUTION configuration
        sExecDti = self.dicActCfg.get("sExecuteDTI", "exec/*:1")

        sExecFile = self.dicActArgs.get("sExecFile")
        if sExecFile is None:
            raise CAnyError_Message(
                sMsg="No execution file specified in launch arguments. ('sExecFile' element missing)"
            )
        # endif

        self.pathExecFile = config.ProvideReadFilepathExt((self.sPathTrialConfig, sExecFile))
        xCML = CConfigCML(
            xPrjCfg=self.xPrjCfg,
            sImportPath=self.pathExecFile,
            dicRtVars=self.xCfgLaunch.dicRuntimeVars,
            setRtVarsEval=self.xCfgLaunch.setRuntimeVarsEval,
        )
        self.dicExec = config.Load(self.pathExecFile, sDTI=sExecDti, dicCustomVars=dicVars, bAddPathVars=True)
        self.dicExec = xCML.Process(self.dicExec)

        self.dicCfgVars["exec"] = copy.deepcopy(self.dicExec)

        ######################################################################################
        # Load & process MANIFEST specified in trial
        self.xManifest = CConfigManifest(xPrjCfg=self.xPrjCfg)

        sFileManifest = self.dicTrial.get("sManifestFile")
        if sFileManifest is None:
            raise Exception("No manifest file given in trial file '{0}'".format(self.dicActArgs.get("sTrialFile")))
        # endif
        self.pathManifestFile = config.ProvideReadFilepathExt((self.sPathTrialConfig, sFileManifest))
        self.xManifest.LoadFile(self.pathManifestFile)
        # Get trial configurations according to manifest
        self.lTrialCfgs = self.xManifest.GetTrialConfigs(self.sAction, self.dicTrial, dicCfgVars=self.dicCfgVars)

    # enddef

    ######################################################################################
    def GetAction(self):
        return self.sAction

    # enddef

    ######################################################################################
    def GetTrialConfigPath(self):
        return self.sPathTrialConfig

    # enddef

    ######################################################################################
    def _ToIdName(self, _sId):
        return _sId.replace("/", "_").replace("\\", "_").replace(".", "-")

    # enddef

    ######################################################################################
    # Execute action
    @logFunctionCall
    def Execute(self, bDoProcess: bool = True, dicDebug: bool = None) -> CConfigManifestJob:

        self.dicDebug = dicDebug

        sDT = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Get random seed for random values in configs
        iRandomSeed = self.dicTrial.get("iRandomSeed")
        if iRandomSeed is None:
            iRandomSeed = self.dicTrial["iRandomSeed"] = 0
        # endif
        random.seed(iRandomSeed)
        np.random.seed(iRandomSeed)

        # Get the configuration loops
        # sFpTrial = config.GetDictValue(self.dicTrial, "__locals__/filepath", str,
        #                                bAllowKeyPath=True,
        #                                sWhere="trial file")

        # sFpTrial = config.GetElementAtPath(self.dicTrial, "__locals__/filepath")

        xLoopConfigs = CLoopConfigs(
            xPrjCfg=self.xPrjCfg,
            sId=self.dicTrial.get("sId"),
            sCfgFilePath=self.pathTrialFile,
            lScheme=self.lTrialCfgs,
        )
        iCfgCnt = xLoopConfigs.GetTotalStepCount()

        # Add the starting time of the action
        self.dicCfgVars["now"] = sDT

        sActName = self.sAction.replace("/", "-").replace(".", "_")
        sPathJobConfigMain = os.path.join(self.xPrjCfg.sActProdPath, "_temp", "actions", sActName, sDT)
        lJobConfigs = []

        # dTimeStart = timer()

        # Loop over all configs
        while xLoopConfigs.Next():
            iCfgIdx = xLoopConfigs.GetTotalStepIdx()

            if iCfgIdx % 10 == 0:
                logFunctionCall.PrintLog("Creating configs {}-{} of {}".format(iCfgIdx, iCfgIdx + 9, iCfgCnt))
                sys.stdout.write("Creating configs {}-{} of {}           \r".format(iCfgIdx, iCfgIdx + 9, iCfgCnt))
                sys.stdout.flush()
            # endif

            # print(f"Create config {iCfgIdx} of {iCfgCnt}")

            # dTimeStart = timer()
            dicData = xLoopConfigs.GetData(
                dicCfgVars=self.dicCfgVars,
                dicRuntimeVars=self.xCfgLaunch.dicRuntimeVars,
                setRuntimeVarsEval=self.xCfgLaunch.setRuntimeVarsEval,
            )
            # dTimeEnd = timer()
            # print("GetData: {:5.2f}s".format(dTimeEnd - dTimeStart))

            # If returned data is none, then this config is filtered.
            # So we can continue with the next one.
            if dicData is None:
                continue
            # endif

            # Add the action globals to the config dictionary
            if isinstance(self.dicActGlobals, dict):
                ison.util.data.AddLocalGlobalVars(
                    dicData["mData"],
                    {"__globals__": self.dicActGlobals},
                    "launch globals",
                )
            # endif

            # print("Configuration index: {0}".format(iCfgIdx))

            dicRelPathTrgAct = dicData["dicRelPathTrgAct"]
            dicPathTrgAct = {}
            dicActDtiToName = {}

            for sAct in dicRelPathTrgAct:
                # Construct absolute target paths from relative paths
                dicPathTrgAct[sAct] = os.path.join(self.xPrjCfg.sActProdPath, dicRelPathTrgAct[sAct])
                # Create Action DTI to Action Name dictionary
                sDti = self.dicActions[sAct].get("sActionDTI")
                dicActDtiToName[sDti] = sAct
            # endfor

            sPathTrgMain = os.path.join(self.xPrjCfg.sActProdPath, dicData.get("sRelPathTrgMain"))

            dicProcConfig = copy.deepcopy(self.dicActArgs)

            dicProcConfig.update(
                {
                    "sDTI": "/catharsys/action/config:1.0",
                    "iCfgIdx": iCfgIdx,
                    "iCfgCnt": iCfgCnt,
                    "mConfig": dicData,
                    "sPathTrgMain": sPathTrgMain,
                    "dicPathTrgAct": dicPathTrgAct,
                    "dicActDtiToName": dicActDtiToName,
                    "lActions": copy.deepcopy(dicData.get("lActions")),
                    "sJobGroupId": sDT,
                }
            )

            lJobConfigs.append(dicProcConfig)
            # print("...finished")
        # endwhile configs

        sys.stdout.write("                                             \r")
        sys.stdout.flush()

        # dTimeEnd = timer()
        # dTimeDelta = dTimeEnd - dTimeStart
        # print("Loop Configs: {:5.2f}s, mean per config: {:5.2f}".format(dTimeDelta, dTimeDelta/iCfgCnt))

        dicRes = config.CheckConfigType(self.dicActArgs, "/catharsys/launch/args:1")
        if dicRes["bOK"] is False:
            raise Exception("Launch arguments type error: {0}".format(dicRes["sMsg"]))
        # endif

        iConfigsPerGroup: int = None
        iFramesPerGroup: int = None

        if dicRes["lCfgVer"][1] == 0:
            # Number of groups all frames are split in
            iFrameGroups = convert.DictElementToInt(self.dicActArgs, "iJobsPerConfig", iDefault=1)
            # Each config triggers a new job
            iConfigGroups = 0
            iMaxLocalWorkers = 1

        elif dicRes["lCfgVer"][1] >= 1:
            iFrameGroups = convert.DictElementToInt(self.dicActArgs, "iFrameGroups", iDefault=1)
            iConfigGroups = convert.DictElementToInt(self.dicActArgs, "iConfigGroups", iDefault=0)
            iMaxLocalWorkers = convert.DictElementToInt(self.dicActArgs, "iMaxLocalWorkers", iDefault=1)
            iConfigsPerGroup = convert.DictElementToInt(self.dicActArgs, "iConfigsPerGroup", bDoRaise=False)
            iFramesPerGroup = convert.DictElementToInt(self.dicActArgs, "iFramesPerGroup", bDoRaise=False)
        # endif

        dicJob = {
            "sDTI": "/catharsys/action-class/python/manifest-based/job-config:1.0",
            "sAction": self.sAction,
            "sActDti": self.sActDti,
            "mPrjCfg": self.xPrjCfg.Serialize(),
            "iFrameGroups": iFrameGroups,
            "iConfigGroups": iConfigGroups,
            "iConfigsPerGroup": iConfigsPerGroup,
            "iFramesPerGroup": iFramesPerGroup,
            "iMaxLocalWorkers": iMaxLocalWorkers,
            "sPathJobConfigMain": sPathJobConfigMain,
            "lConfigs": lJobConfigs,
        }

        if len(lJobConfigs) == 0:
            print("WARNING: No configuration available to execute action '{0}'".format(self.sAction))

        elif bDoProcess is True:
            path.CreateDir(sPathJobConfigMain)

            if self.sJobDistType == "single;all":
                self._ExecJobs_SingleAll(sId=xLoopConfigs.GetId(), dicJob=dicJob, bDoProcess=bDoProcess)

            elif self.sJobDistType == "frames;configs":
                self._ExecJobs_FramesConfigs(sId=xLoopConfigs.GetId(), dicJob=dicJob, bDoProcess=bDoProcess)

            elif self.sJobDistType == "per-frame;configs":
                self._ExecJobs_PerFrameConfigs(sId=xLoopConfigs.GetId(), dicJob=dicJob, bDoProcess=bDoProcess)
            else:
                raise CAnyError_Message(sMsg=f"Unsupported job distribution type '{self.sJobDistType}'")
            # endif
        # endif

        return CConfigManifestJob(dicJob)

    # enddef

    ######################################################################################
    # Execute single job
    @logFunctionCall
    def _ExecJobs_SingleAll(self, *, sId, dicJob, bDoProcess=True):

        # This job distribution scheme simply enforces
        # iFrameGroups = 1 and iConfigGroups = 0.
        # In this way, there is one job per config that processes all frames.
        dicJob["iFrameGroups"] = 1
        dicJob["iConfigGroups"] = 0

        self._ExecJobs_FramesConfigs(sId=sId, dicJob=dicJob, bDoProcess=bDoProcess)

    # enddef

    ######################################################################################
    # Execute jobs with distribution over frames
    @logFunctionCall
    def _ExecJobs_FramesConfigs(self, *, sId, dicJob, bDoProcess=True):

        iFrameFirst = self.dicActArgs.get("iFrameFirst", 0)
        iFrameLast = self.dicActArgs.get("iFrameLast", 0)
        iFrameStep = self.dicActArgs.get("iFrameStep", 1)

        iFrameCnt = int(math.floor((iFrameLast - iFrameFirst) / iFrameStep)) + 1
        iFrameGroups = dicJob["iFrameGroups"]
        iFramesPerGroup: int = dicJob["iFramesPerGroup"]
        if iFramesPerGroup is None:
            iFrameGroups = iFrameCnt if iFrameGroups <= 0 else min(iFrameCnt, iFrameGroups)
        else:
            if iFramesPerGroup < 1:
                raise RuntimeError(f"Value of 'iFramesPerGroup' must be greater than zero but is '{iFramesPerGroup}'")
            # endif
            iFramesPerGroup = min(iFrameCnt, iFramesPerGroup)
            iFrameGroups = int(math.floor(iFrameCnt / iFramesPerGroup)) + (1 if iFrameCnt % iFramesPerGroup > 0 else 0)
        # endif

        iConfigCnt = len(dicJob["lConfigs"])
        iConfigGroups = dicJob["iConfigGroups"]
        iConfigsPerGroup: int = dicJob["iConfigsPerGroup"]

        if iConfigsPerGroup is None:
            iConfigGroups = iConfigCnt if iConfigGroups <= 0 else min(iConfigCnt, iConfigGroups)
            iConfigsPerGroup = int(math.floor(iConfigCnt / iConfigGroups)) + (
                1 if iConfigCnt % iConfigGroups > 0 else 0
            )

        else:
            if iConfigsPerGroup < 1:
                raise RuntimeError(f"Value of 'iConfigsPerGroup' must be greater than zero but is '{iConfigsPerGroup}'")
            # endif
            iConfigsPerGroup = min(iConfigCnt, iConfigsPerGroup)
            iConfigGroups = int(math.floor(iConfigCnt / iConfigsPerGroup)) + (
                1 if iConfigCnt % iConfigsPerGroup > 0 else 0
            )
        # endif

        logFunctionCall.PrintLog(
            f"FrameConfigs: 'iConfigGroups':{iConfigGroups} 'iConfigCnt':{iConfigCnt}"
            f"\n              'iFrameGroups':{iFrameGroups} 'iFrameCnt':{iFrameCnt}"
        )

        # print(
        #     f"FrameConfigs: 'iConfigGroups':{iConfigGroups} 'iConfigCnt':{iConfigCnt}"
        #     f"\n              'iFrameGroups':{iFrameGroups} 'iFrameCnt':{iFrameCnt}"
        # )

        iJobCnt = iConfigGroups * iFrameGroups
        sIdName = self._ToIdName(sId)

        iMaxLocalWorkers = dicJob["iMaxLocalWorkers"]
        with concurrent.futures.ThreadPoolExecutor(max_workers=iMaxLocalWorkers) as xExecutor:
            iJobIdx = 0
            for iConfigGrpIdx in range(iConfigGroups):
                iCfgStart = iConfigGrpIdx * iConfigsPerGroup
                iCfgEnd = iCfgStart + iConfigsPerGroup
                iCfgEnd = min(iCfgEnd, iConfigCnt)
                lJobConfigs = dicJob["lConfigs"][iCfgStart:iCfgEnd]

                for iFrameGrpIdx in range(iFrameGroups):

                    sFileJobConfig = "{0}_job{1:02d}.json".format(sIdName, iJobIdx + 1)
                    pathJobConfig = Path(dicJob["sPathJobConfigMain"]) / sFileJobConfig
                    sJobName = "{0}:{1:02d}/{2:02d}".format(sIdName, iJobIdx + 1, iJobCnt)

                    for dicConfig in lJobConfigs:
                        # Update the render config for this job
                        dicConfig.update(
                            {
                                "iFrameFirst": iFrameGrpIdx * iFrameStep + iFrameFirst,
                                "iFrameLast": iFrameLast,
                                "iFrameStep": iFrameGroups * iFrameStep,
                            }
                        )
                    # endfor

                    dicJobConfig = {
                        "sDTI": "/catharsys/action/config-list:1.1",
                        "sAction": dicJob["sAction"],
                        "sActDti": dicJob["sActDti"],
                        "mPrjCfg": dicJob["mPrjCfg"],
                        "iConfigGroupIdx": iConfigGrpIdx,
                        "iConfigGroups": iConfigGroups,
                        "iFrameGroupIdx": iFrameGrpIdx,
                        "iFrameGroups": iFrameGroups,
                        "sPathJobConfigMain": dicJob["sPathJobConfigMain"],
                        "lConfigs": lJobConfigs,
                    }

                    # Start the actual job
                    if bDoProcess:
                        # Save the render config to a file
                        file.SaveJson(pathJobConfig, dicJobConfig, iIndent=4)
                        logFunctionCall.PrintLog(f"save and start [job](file:\\\\{str(pathJobConfig)})")
                        self.StartJobParallel(
                            pathJobConfig=pathJobConfig,
                            sJobName=sJobName,
                            sJobNameLong=sFileJobConfig,
                            xExecutor=xExecutor,
                        )
                    # endif

                    iJobIdx += 1
                # endfor frame groups
            # endfor config groups

            for futJob in concurrent.futures.as_completed(self.dicJobFutures):
                dicArgs = self.dicJobFutures[futJob]
                try:
                    sName = dicArgs["sJobNameLong"]
                    print(f"Finished job: {sName}")
                    futJob.result()
                except Exception as xEx:
                    print(f"Exception running job:\n{(str(xEx))}")
                # endtry
            # endfor

        # end with thread pool

    # enddef

    ######################################################################################
    # Execute jobs with distribution over frames
    @logFunctionCall
    def _ExecJobs_PerFrameConfigs(self, *, sId, dicJob, bDoProcess=True):

        iFrameFirst = self.dicActArgs.get("iFrameFirst", 0)
        iFrameLast = self.dicActArgs.get("iFrameLast", 0)
        iFrameStep = self.dicActArgs.get("iFrameStep", 1)
        iFrameCnt = int(math.floor((iFrameLast - iFrameFirst) / iFrameStep)) + 1

        iSubFrameGroups = dicJob["iFrameGroups"]
        iSubFramesPerGroup: int = dicJob["iFramesPerGroup"]

        if iSubFrameGroups <= 0:
            raise Exception(
                "For actions of job distribution type 'per-frame', "
                "the frame groups count (iFrameGroups) has to be "
                "given explicitly, i.e. greater than zero."
            )
        # endif
        if iSubFramesPerGroup is not None:
            if iSubFramesPerGroup < 1:
                raise RuntimeError(
                    f"Value of 'iFramesPerGroup' must be greater than zero but is '{iSubFramesPerGroup}'"
                )
            # endif
            iSubFramesPerGroup = min(iFrameCnt, iSubFramesPerGroup)
            iSubFrameGroups = int(math.floor(iFrameCnt / iSubFramesPerGroup)) + (
                1 if iFrameCnt % iSubFramesPerGroup > 0 else 0
            )
        # endif

        iConfigCnt = len(dicJob["lConfigs"])
        iConfigGroups = dicJob["iConfigGroups"]
        iConfigsPerGroup: int = dicJob["iConfigsPerGroup"]

        if iConfigsPerGroup is None:
            iConfigGroups = iConfigCnt if iConfigGroups <= 0 else min(iConfigCnt, iConfigGroups)
            iConfigsPerGroup = int(math.floor(iConfigCnt / iConfigGroups)) + (
                1 if iConfigCnt % iConfigGroups > 0 else 0
            )

        else:
            if iConfigsPerGroup < 1:
                raise RuntimeError(f"Value of 'iConfigsPerGroup' must be greater than zero but is '{iConfigsPerGroup}'")
            # endif
            iConfigsPerGroup = min(iConfigCnt, iConfigsPerGroup)
            iConfigGroups = int(math.floor(iConfigCnt / iConfigsPerGroup)) + (
                1 if iConfigCnt % iConfigsPerGroup > 0 else 0
            )
        # endif

        logFunctionCall.PrintLog(
            f"PerFrameConfigs: 'iConfigGroups':{iConfigGroups} 'iConfigCnt':{iConfigCnt}"
            f"\n                'iConfigsPerGroup':{iConfigsPerGroup} 'iFrameCnt':{iFrameCnt}"
        )

        iJobCnt = iFrameCnt * iConfigGroups * iSubFrameGroups
        sIdName = self._ToIdName(sId)

        iMaxLocalWorkers = dicJob["iMaxLocalWorkers"]
        with concurrent.futures.ThreadPoolExecutor(max_workers=iMaxLocalWorkers) as xExecutor:
            iJobIdx = 0
            # Loop over frames
            for iFrameIdx in range(iFrameFirst, iFrameLast + 1, iFrameStep):

                # Loop over configs
                for iConfigGrpIdx in range(iConfigGroups):
                    iCfgStart = iConfigGrpIdx * iConfigsPerGroup
                    iCfgEnd = iCfgStart + iConfigsPerGroup
                    iCfgEnd = min(iCfgEnd, iConfigCnt)
                    lJobConfigs = dicJob["lConfigs"][iCfgStart:iCfgEnd]

                    # Loop over jobs per frame
                    for iSubFrameIdx in range(iSubFrameGroups):

                        sFileJobConfig = "{0}_frm{1:02d}_job{2:02d}.json".format(sIdName, iFrameIdx, iJobIdx + 1)
                        pathJobConfig = Path(dicJob["sPathJobConfigMain"]) / sFileJobConfig
                        sJobName = "{0}:{1}/{2}>{3}.{4}.{5}".format(
                            sIdName,
                            iJobIdx + 1,
                            iJobCnt,
                            iFrameIdx,
                            iConfigGrpIdx,
                            iSubFrameIdx,
                        )

                        for dicConfig in lJobConfigs:
                            # Update the render config for this job
                            dicConfig.update(
                                {
                                    "iFrameFirst": iFrameIdx,
                                    "iFrameLast": iFrameIdx,
                                    "iFrameStep": 1,
                                    "iSubFrameOffset": iSubFrameIdx,
                                    "iSubFrameStep": iSubFrameGroups,
                                }
                            )
                        # endfor

                        dicJobConfig = {
                            "sDTI": "/catharsys/action/config-list:1.1",
                            "sAction": dicJob["sAction"],
                            "sActDti": dicJob["sActDti"],
                            "mPrjCfg": dicJob["mPrjCfg"],
                            "iConfigGroupIdx": iConfigGrpIdx,
                            "iConfigGroups": iConfigGroups,
                            "iFrameGroupIdx": iSubFrameIdx,
                            "iFrameGroups": iSubFrameGroups,
                            "sPathJobConfigMain": dicJob["sPathJobConfigMain"],
                            "lConfigs": lJobConfigs,
                        }

                        # Start the actual job
                        if bDoProcess:
                            # Save the render config to a file
                            file.SaveJson(pathJobConfig, dicJobConfig, iIndent=4)

                            self.StartJobParallel(
                                pathJobConfig=pathJobConfig,
                                sJobName=sJobName,
                                sJobNameLong=sFileJobConfig,
                                xExecutor=xExecutor,
                            )
                        # endif

                        iJobIdx += 1
                    # endfor sub-frames
                # endfor configs
            # endfor frames

            for futJob in concurrent.futures.as_completed(self.dicJobFutures):
                dicArgs = self.dicJobFutures[futJob]
                try:
                    sName = dicArgs["sJobNameLong"]
                    print(f"Finished job: {sName}")
                    futJob.result()
                except Exception as xEx:
                    print(f"Exception running job:\n{(str(xEx))}")
                # endtry
            # endfor

        # endwith thread pool

    # enddef

    ###############################################################################
    @logFunctionCall
    def StartJob(self, *, pathJobConfig, sJobName, sJobNameLong):

        dicArgs = {
            "pathJobConfig": pathJobConfig,
            "sJobName": sJobName,
            "sJobNameLong": sJobNameLong,
            "dicTrial": self.dicTrial,
            "dicDebug": self.dicDebug,
        }

        job.Start(xPrjCfg=self.xPrjCfg, dicExec=self.dicExec, dicArgs=dicArgs)

    # enddef

    ###############################################################################
    @logFunctionCall
    def StartJobParallel(
        self, *, pathJobConfig: Path, sJobName: str, sJobNameLong: str, xExecutor: concurrent.futures.ThreadPoolExecutor
    ):

        dicArgs = {
            "pathJobConfig": pathJobConfig,
            "sJobName": sJobName,
            "sJobNameLong": sJobNameLong,
            "dicTrial": self.dicTrial,
            "dicDebug": self.dicDebug,
        }

        futJob = xExecutor.submit(job.Start, xPrjCfg=self.xPrjCfg, dicExec=self.dicExec, dicArgs=dicArgs)
        self.dicJobFutures[futJob] = dicArgs

    # enddef


# endclass
