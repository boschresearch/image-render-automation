###
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
import re
import shutil
from typing import Optional
from pathlib import Path


###############################################################################################
def RemoveTree(pathDir: Path, *, bIgnoreErrors: bool = False):
    if not pathDir.exists():
        if bIgnoreErrors is False:
            raise RuntimeError(f"Path does not exist: {(pathDir.as_posix())}")
        # endif
        return
    # endif

    shutil.rmtree(path=pathDir.as_posix(), ignore_errors=bIgnoreErrors)


# enddef


###############################################################################################
def CopyFile(pathSrcFile: Path, pathTrgFile: Path):
    shutil.copyfile(pathSrcFile.as_posix(), pathTrgFile.as_posix())


# enddef


###############################################################################################
def CopyFileToDir(pathSrcFile: Path, pathTrgDir: Path):
    if not pathSrcFile.exists():
        raise RuntimeError(f"Source file does not exist: {(pathSrcFile.as_posix())}")
    # endif

    if not pathSrcFile.is_file():
        raise RuntimeError(f"Source path is not a file: {(pathSrcFile.as_posix())}")
    # endif

    if not pathTrgDir.exists():
        raise RuntimeError(f"Target directory does not exist: {(pathTrgDir.as_posix())}")
    # endif

    if not pathTrgDir.is_dir():
        raise RuntimeError(f"Target path is not a directory: {(pathTrgDir.as_posix())}")
    # endif

    pathTrgFile = pathTrgDir / pathSrcFile.name
    shutil.copyfile(pathSrcFile.as_posix(), pathTrgFile.as_posix())


# enddef


###############################################################################################
def CopyFilesInDir(
    pathSrc: Path,
    pathTrg: Path,
    *,
    bRecursive: bool = True,
    bDoPrint: bool = False,
    lReExcludeDirs: list[str] = [],
    lReExcludeFiles: list[str] = [],
    _lReCmpExclDirs: list[re.Pattern] = [],
    _lReCmpExclFiles: list[re.Pattern] = [],
    pathSrcTop: Optional[Path] = None,
    pathTrgTop: Optional[Path] = None,
):
    if len(_lReCmpExclDirs) > 0:
        lReExclDirs = _lReCmpExclDirs
    else:
        lReExclDirs = [re.compile(x) for x in lReExcludeDirs]
    # endif

    if len(_lReCmpExclFiles) > 0:
        lReExclFiles = _lReCmpExclFiles
    else:
        lReExclFiles = [re.compile(x) for x in lReExcludeFiles]
    # endif

    if pathSrcTop is None:
        pathSrcTop = pathSrc
    # endif

    if pathTrgTop is None:
        pathTrgTop = pathTrg
    # endif

    for pathSrcX in pathSrc.glob("*"):
        if pathSrcX.is_file():
            sName = pathSrcX.name

            if len(lReExclFiles) > 0 and any(test.match(sName) for test in lReExclFiles) is True:
                if bDoPrint is True:
                    print("Exclude file: {}".format(pathSrcX.relative_to(pathSrcTop).as_posix()))
                # endif
            else:
                pathTrgX = pathTrg / sName
                # print("Copy file: {}".format(pathSrcX.relative_to(pathSrcTop).as_posix()))
                shutil.copy(pathSrcX, pathTrgX)
            # endif

        elif pathSrcX.is_dir():
            if bRecursive is True:
                sName = pathSrcX.name

                if len(lReExclDirs) > 0 and any(test.match(sName) for test in lReExclDirs) is True:
                    if bDoPrint is True:
                        print("Exclude folder: {}".format(pathSrcX.relative_to(pathSrcTop).as_posix()))
                    # endif
                else:
                    pathTrgX = pathTrg / sName
                    pathTrgX.mkdir(exist_ok=True)
                    # print("Copy folder: {}".format(pathSrcX.relative_to(pathSrcTop).as_posix()))
                    CopyFilesInDir(
                        pathSrcX,
                        pathTrgX,
                        pathSrcTop=pathSrcTop,
                        pathTrgTop=pathTrgTop,
                        _lReCmpExclDirs=lReExclDirs,
                        _lReCmpExclFiles=lReExclFiles,
                    )
                # endif
            # endif recursive
        # endif file | dir
    # endfor


# enddef
