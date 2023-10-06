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
from typing import Optional, Callable
from timeit import default_timer as timer

import ison
from ison.util.data import AddLocalGlobalVars
from ison.core.cls_parser_error import CParserError

from anybase.cls_any_error import CAnyError_Message, CAnyError_TaskMessage
from anybase import convert
from anybase.cls_process_handler import CProcessHandler

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
from catharsys.plugins.std.action_class.manifest import utils

from catharsys.config.cls_project import CProjectConfig
from catharsys.config.cls_launch import CConfigLaunch
from catharsys.config.cls_exec_job import CConfigExecJob
from catharsys.config.cls_job import CConfigJob
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
        self.dicActionDti: dict = None
        self.dicTrial: dict = None
        self.dicExec: dict = None
        self.dicDebug: dict = None
        self.dicCfgVars: dict = None
        self.pathTrialFile: Path = None
        self.pathExecFile: Path = None
        self.pathManifestFile: Path = None
        self.lTrialCfgs: list = None
        self.lJobDistTypes: list = ["single;all", "frames;configs", "per-frame;configs"]
        self.sJobDistType: str = None
        self.sPathTrialConfig: str = None

        self.xCML: CConfigCML = None

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

        ######################################################################################
        # Create Parser
        self.xCML = CConfigCML(
            xPrjCfg=self.xPrjCfg,
            dicConstVars=self.dicCfgVars,
            dicRtVars=self.xCfgLaunch.dicRuntimeVars,
            setRtVarsEval=self.xCfgLaunch.setRuntimeVarsEval,
        )

        # adds globals of launch file to parser instance
        dicGlobals = {}
        ison.util.data.AddLocalGlobalVars(dicGlobals, self.dicActions[self.sAction], bLocalVars=False)
        dicGlobals = self.xCML.Process(dicGlobals)

        ######################################################################################
        # Load & process TRIAL configuration
        sTrialFile = self.dicActArgs.get("sTrialFile")
        if sTrialFile is None:
            raise CAnyError_Message(sMsg="No trial file specified in launch arguments. ('sTrialFile' element missing)")
        # endif

        self.pathTrialFile = config.ProvideReadFilepathExt((self.sPathTrialConfig, sTrialFile))

        self.dicTrial = config.Load(self.pathTrialFile, sDTI="trial:1", bAddPathVars=True, dicCustomVars=dicVars)
        try:
            self.dicTrial = self.xCML.Process(self.dicTrial, sImportPath=self.pathTrialFile.parent.as_posix())

        except CParserError as xEx:
            raise CAnyError_TaskMessage(sTask="Processing trial configuration", sMsg=xEx.ToString())
        # endtry

        # add the processed trial data to the variables, so that
        # they can be used when processing the execution config
        self.dicCfgVars["trial"] = copy.deepcopy(self.dicTrial)
        self.xCML.UpdateConstVars(self.dicCfgVars, _bAllowOverwrite=True, _bPrintWarnings=False)

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
        # xCML = CConfigCML(
        #     xPrjCfg=self.xPrjCfg,
        #     sImportPath=self.pathExecFile,
        #     dicRtVars=self.xCfgLaunch.dicRuntimeVars,
        #     setRtVarsEval=self.xCfgLaunch.setRuntimeVarsEval,
        # )
        self.dicExec = config.Load(self.pathExecFile, sDTI=sExecDti, dicCustomVars=dicVars, bAddPathVars=True)
        try:
            self.dicExec = self.xCML.Process(self.dicExec, sImportPath=self.pathExecFile.parent.as_posix())
        except CParserError as xEx:
            raise CAnyError_TaskMessage(sTask="Processing execution configuration", sMsg=xEx.ToString())
        # endtry

        self.dicCfgVars["exec"] = copy.deepcopy(self.dicExec)
        self.xCML.UpdateConstVars(self.dicCfgVars, _bAllowOverwrite=True, _bPrintWarnings=False)

        ######################################################################################
        # Load & process MANIFEST specified in trial
        self.xManifest = CConfigManifest(xPrjCfg=self.xPrjCfg, _xCML=self.xCML)

        sFileManifest = self.dicTrial.get("sManifestFile")
        if sFileManifest is None:
            raise Exception("No manifest file given in trial file '{0}'".format(self.dicActArgs.get("sTrialFile")))
        # endif
        self.pathManifestFile = config.ProvideReadFilepathExt((self.sPathTrialConfig, sFileManifest))
        self.xManifest.LoadFile(self.pathManifestFile)
        # Get trial configurations according to manifest
        self.lTrialCfgs = self.xManifest.GetTrialConfigs(self.sAction, self.dicTrial)  # , dicCfgVars=self.dicCfgVars)

    # enddef

    @property
    def sId(self) -> str:
        return self.dicTrial.get("sId")

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
    # Get Manifest Job Config
    def GetJobConfig(self, *, _funcStatus: Optional[Callable[[int, int], None]] = None) -> CConfigManifestJob:
        sDT = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Get the configuration loops
        sFpTrial = config.GetDictValue(
            self.dicTrial, "__locals__/filepath", str, bAllowKeyPath=True, sWhere="trial file"
        )

        # Get random seed for random values in configs
        utils.ApplyConfigRandomSeed(self.dicTrial, _bApplyToConfig=True, _sConfigFilename=sFpTrial)

        # Get the configuration loops
        # sFpTrial = config.GetDictValue(self.dicTrial, "__locals__/filepath", str,
        #                                bAllowKeyPath=True,
        #                                sWhere="trial file")

        # sFpTrial = config.GetElementAtPath(self.dicTrial, "__locals__/filepath")

        # dTimeStart = time.perf_counter()
        xLoopConfigs = CLoopConfigs(
            xPrjCfg=self.xPrjCfg,
            sId=self.dicTrial.get("sId"),
            sCfgFilePath=self.pathTrialFile,
            lScheme=self.lTrialCfgs,
        )
        iCfgCnt = xLoopConfigs.GetTotalStepCount()
        # dTimeEnd = time.perf_counter()
        # print("Init Job config and count total number: {:5.2f}s".format(dTimeEnd - dTimeStart))

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
                if _funcStatus is not None:
                    _funcStatus(iCfgIdx, iCfgCnt)
                else:
                    logFunctionCall.PrintLog("Creating configs {}-{} of {}".format(iCfgIdx, iCfgIdx + 9, iCfgCnt))
                    sys.stdout.write("Creating configs {}-{} of {}           \r".format(iCfgIdx, iCfgIdx + 9, iCfgCnt))
                    sys.stdout.flush()
                # endif
            # endif

            # print(f"Create config {iCfgIdx} of {iCfgCnt}")

            # dTimeStart = timer()
            # The GetData() function copies the state of self.xCML into a new parser instance,
            # which is then used to parse the configs for one config set.
            dicData = xLoopConfigs.GetData(self.xCML)

            # dTimeEnd = timer()
            # print("GetData: {:5.3f}s       ".format(dTimeEnd - dTimeStart))

            # If returned data is none, then this config is filtered.
            # So we can continue with the next one.
            if dicData is None:
                continue
            # endif

            # # Add the action globals to the config dictionary
            # ison.util.data.AddLocalGlobalVars(
            #     dicData["mData"],
            #     {
            #         "__globals__": self.xCML.dicVarGlo,
            #         "__func_globals__": self.xCML.dicVarFuncGlo,
            #     },
            #     "globals",
            # )

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

            # dTimeStart = time.perf_counter()
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
            # dTimeEnd = time.perf_counter()
            # print("Creating config dict: {:5.2f}s".format(dTimeEnd - dTimeStart))

            lJobConfigs.append(dicProcConfig)
            # print("...finished")
        # endwhile configs

        if _funcStatus is not None:
            _funcStatus(iCfgCnt, iCfgCnt)
        else:
            sys.stdout.write("                                             \r")
            sys.stdout.flush()
        # endif

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
            "mExec": self.dicExec,
            "lConfigs": lJobConfigs,
        }

        return CConfigManifestJob(dicJob)

    # enddef

    ######################################################################################
    # Split full job into list of executable jobs
    def GetExecJobConfigList(self, _xJob: CConfigManifestJob) -> list[CConfigExecJob]:
        lExecJobs: list[CConfigExecJob] = []

        if _xJob.iConfigCount == 0:
            print("WARNING: No configuration available to execute action '{0}'".format(self.sAction))
            return lExecJobs
        # endif

        if self.sJobDistType == "single;all":
            lExecJobs = self._GetJobs_SingleAll(sId=self.sId, dicJob=_xJob.dicData)

        elif self.sJobDistType == "frames;configs":
            lExecJobs = self._GetJobs_FramesConfigs(sId=self.sId, dicJob=_xJob.dicData)

        elif self.sJobDistType == "per-frame;configs":
            lExecJobs = self._GetJobs_PerFrameConfigs(sId=self.sId, dicJob=_xJob.dicData)
        else:
            raise CAnyError_Message(sMsg=f"Unsupported job distribution type '{self.sJobDistType}'")
        # endif

        return lExecJobs

    # enddef

    ######################################################################################
    # Execute Job List
    def ExecuteJobList(self, _lExecJobs: list[CConfigExecJob]):
        iMaxLocalWorkers: int = convert.DictElementToInt(self.dicActArgs, "iMaxLocalWorkers", iDefault=1)
        self._ExecJobsParallel(_lJobs=_lExecJobs, _iMaxLocalWorkers=iMaxLocalWorkers)

    # enddef

    ######################################################################################
    # Execute action
    @logFunctionCall
    def Execute(self, *, bDoProcess: bool = True, dicDebug: bool = None) -> CConfigManifestJob:
        self.dicDebug = dicDebug

        xJob: CConfigManifestJob = self.GetJobConfig()

        if bDoProcess is True:
            lExecJobs = self.GetExecJobConfigList(xJob)
            self.ExecuteJobList(lExecJobs)
        # endif

        return xJob

    # enddef

    ######################################################################################
    # Execute single job
    @logFunctionCall
    def _GetJobs_SingleAll(self, *, sId, dicJob) -> list[CConfigExecJob]:
        # This job distribution scheme simply enforces
        # iFrameGroups = 1 and iConfigGroups = 0.
        # In this way, there is one job per config that processes all frames.
        dicJob["iFrameGroups"] = 1
        dicJob["iConfigGroups"] = 0

        return self._GetJobs_FramesConfigs(sId=sId, dicJob=dicJob)

    # enddef

    ######################################################################################
    # Execute jobs with distribution over frames
    @logFunctionCall
    def _GetJobs_FramesConfigs(self, *, sId, dicJob) -> list[CConfigExecJob]:
        iFrameFirst = convert.DictElementToInt(self.dicActArgs, "iFrameFirst", iDefault=0)
        iFrameLast = convert.DictElementToInt(self.dicActArgs, "iFrameLast", iDefault=0)
        iFrameStep = convert.DictElementToInt(self.dicActArgs, "iFrameStep", iDefault=1)

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

        # iMaxLocalWorkers = dicJob["iMaxLocalWorkers"]
        lJobs: list[CConfigExecJob] = []
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
                    "mExec": dicJob["mExec"],
                    "lConfigs": lJobConfigs,
                }

                lJobs.append(
                    CConfigExecJob(
                        _iIdx=iJobIdx,
                        _sName=sJobName,
                        _sLabel=sFileJobConfig,
                        _pathConfig=pathJobConfig,
                        _dicConfig=dicJobConfig,
                    )
                )
                iJobIdx += 1
            # endfor frame groups
        # endfor config groups

        return lJobs

    # enddef

    ######################################################################################
    # Execute jobs with distribution over frames
    @logFunctionCall
    def _GetJobs_PerFrameConfigs(self, *, sId, dicJob) -> list[CConfigExecJob]:
        iFrameFirst = convert.DictElementToInt(self.dicActArgs, "iFrameFirst", iDefault=0)
        iFrameLast = convert.DictElementToInt(self.dicActArgs, "iFrameLast", iDefault=0)
        iFrameStep = convert.DictElementToInt(self.dicActArgs, "iFrameStep", iDefault=1)
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

        lJobs: list[CConfigExecJob] = []
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
                        "mExec": dicJob["mExec"],
                        "lConfigs": lJobConfigs,
                    }

                    lJobs.append(
                        CConfigExecJob(
                            _iIdx=iJobIdx,
                            _sName=sJobName,
                            _sLabel=sFileJobConfig,
                            _pathConfig=pathJobConfig,
                            _dicConfig=dicJobConfig,
                        )
                    )
                    iJobIdx += 1
                # endfor sub-frames
            # endfor configs
        # endfor frames

        return lJobs

    # enddef

    ######################################################################################
    def _ExecJobsParallel(self, *, _lJobs: list[CConfigExecJob], _iMaxLocalWorkers: int):
        if len(_lJobs) == 0:
            return
        # endif

        with concurrent.futures.ThreadPoolExecutor(max_workers=_iMaxLocalWorkers) as xExecutor:
            xExecJob: CConfigExecJob = None
            for xExecJob in _lJobs:
                if xExecJob.xProcHandler.bPollTerminateAvailable and xExecJob.xProcHandler.PollTerminate() is True:
                    continue
                # endif

                sPathJobConfigMain: str = xExecJob.dicConfig["sPathJobConfigMain"]
                path.CreateDir(sPathJobConfigMain)

                # Start the actual job
                # Save the render config to a file
                file.SaveJson(xExecJob.pathConfig, xExecJob.dicConfig, iIndent=4)
                logFunctionCall.PrintLog(f"save and start [job](file:\\\\{str(xExecJob.pathConfig)})")
                self.StartJobParallel(
                    pathJobConfig=xExecJob.pathConfig,
                    sJobName=xExecJob.sName,
                    sJobNameLong=xExecJob.sLabel,
                    xProcHandler=xExecJob.xProcHandler,
                    xExecutor=xExecutor,
                )
            # endfor job

            for futJob in concurrent.futures.as_completed(self.dicJobFutures):
                dicArgs = self.dicJobFutures[futJob]
                try:
                    sName = dicArgs["sJobNameLong"]
                    # print(f"Finished job: {sName}")
                    futJob.result()
                except Exception as xEx:
                    sMsg = f"Exception running job:\n{(str(xEx))}"
                    xProcHander: CProcessHandler = dicArgs["xProcessHandler"]
                    if xProcHander is not None and xProcHander.bEndedAvailable is True:
                        xProcHander.Ended(1, sMsg)
                    # endif
                    print(sMsg)
                # endtry
            # endfor

        # end with thread pool

    # enddef

    ###############################################################################
    @logFunctionCall
    def StartJob(
        self,
        *,
        pathJobConfig: Path,
        sJobName: str,
        sJobNameLong: str,
        xProcHandler: CProcessHandler,
    ):
        dicArgs = {
            "pathJobConfig": pathJobConfig,
            "sJobName": sJobName,
            "sJobNameLong": sJobNameLong,
            "dicTrial": self.dicTrial,
            "dicDebug": self.dicDebug,
            "xProcessHandler": xProcHandler,
        }

        job.Start(xPrjCfg=self.xPrjCfg, dicExec=self.dicExec, dicArgs=dicArgs)

    # enddef

    ###############################################################################
    @logFunctionCall
    def StartJobParallel(
        self,
        *,
        pathJobConfig: Path,
        sJobName: str,
        sJobNameLong: str,
        xProcHandler: CProcessHandler,
        xExecutor: concurrent.futures.ThreadPoolExecutor,
    ):
        dicArgs = {
            "pathJobConfig": pathJobConfig,
            "sJobName": sJobName,
            "sJobNameLong": sJobNameLong,
            "dicTrial": self.dicTrial,
            "dicDebug": self.dicDebug,
            "xProcessHandler": xProcHandler,
        }

        futJob = xExecutor.submit(job.Start, xPrjCfg=self.xPrjCfg, dicExec=self.dicExec, dicArgs=dicArgs)
        self.dicJobFutures[futJob] = dicArgs

    # enddef


# endclass
