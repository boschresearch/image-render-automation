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
from typing import Optional


########################################################################
# Recursively update target dictionary with source dictionary
def DictRecursiveUpdate(
    _dicTrg: dict,
    _dicSrc: dict,
    *,
    _lRegExExclude: Optional[list[str]] = None,
    _lReExclude: Optional[list[re.Pattern]] = None,
    _bRemoveTrgKeysNotInSrc: bool = False,
    _bAddSrcKeysNotInTrg: bool = True,
):
    if not isinstance(_dicTrg, dict) or not isinstance(_dicSrc, dict):
        raise RuntimeError("Invalid arguments: expect dictionaries")
    # endif

    lReExclude: list[re.Pattern] = _lReExclude

    if lReExclude is None and _lRegExExclude is not None:
        lReExclude = []
        for sRegEx in _lRegExExclude:
            lReExclude.append(re.compile(sRegEx))
        # endfor
    # endif

    if _bRemoveTrgKeysNotInSrc is True:
        lRemoveKeys: list[str] = []
        for sTrgKey in _dicTrg:
            if sTrgKey not in _dicSrc:
                lRemoveKeys.append(sTrgKey)
            # endif
        # endfor

        for sKey in lRemoveKeys:
            del _dicTrg[sKey]
        # endfor
    # endif

    for sSrcKey in _dicSrc:
        if lReExclude is not None and any((x.fullmatch(sSrcKey) is not None for x in lReExclude)):
            continue
        # endif

        if sSrcKey in _dicTrg and isinstance(_dicTrg[sSrcKey], dict) and isinstance(_dicSrc[sSrcKey], dict):
            DictRecursiveUpdate(_dicTrg[sSrcKey], _dicSrc[sSrcKey], _lReExclude=lReExclude)
        elif sSrcKey in _dicTrg:
            _dicTrg[sSrcKey] = _dicSrc[sSrcKey]
        elif _bAddSrcKeysNotInTrg is True:
            _dicTrg[sSrcKey] = _dicSrc[sSrcKey]
        # endif
    # endfor


# enddef
