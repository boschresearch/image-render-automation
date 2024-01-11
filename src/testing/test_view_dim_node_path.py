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

from catharsys.api.products.cls_view_dim_node_path import CViewDimNodePath

# from catharsys.api.products.cls_view_dim_node import CViewDimNode
# from catharsys.api.products.cls_product_view import CProductView


class TestClass:
    def _PrintPath(self, xPath: CViewDimNodePath):
        print(f"lGrpPath: {xPath._lGrpPath}")
        print(f"lArtPath: {xPath._lArtPath}")
        print(f"sArtTypeId: {xPath._sArtTypeId}")

    # enddef

    ################################################################################
    def test_parse_path_01(self):
        sPath1 = "hello|world|*"
        sPath2 = "hello|*|*"

        xPath1 = CViewDimNodePath(sPath1)
        xPath2 = CViewDimNodePath(sPath2)

        print("")
        self._PrintPath(xPath1)
        self._PrintPath(xPath2)

        assert xPath1 in xPath2
        assert xPath2 not in xPath1

    # enddef

    ################################################################################
    def test_parse_path_02(self):
        sPath1 = "hello|world|*&image&a|*"
        sPath2 = "hello|*|*"

        xPath1 = CViewDimNodePath(sPath1)
        xPath2 = CViewDimNodePath(sPath2)

        print("")
        self._PrintPath(xPath1)
        self._PrintPath(xPath2)

        assert xPath1 in xPath2
        assert xPath2 not in xPath1

    # enddef

    ################################################################################
    def test_parse_path_03(self):
        sPath1 = "hello|world|*&image&a|b"
        sPath2 = "hello|world|*&image&a|*"

        xPath1 = CViewDimNodePath(sPath1)
        xPath2 = CViewDimNodePath(sPath2)

        print("")
        self._PrintPath(xPath1)
        self._PrintPath(xPath2)

        assert xPath1 in xPath2
        assert xPath2 not in xPath1

    # enddef

    ################################################################################
    def test_set_path_dict_01(self):
        dicPath = {}
        iDefault = 0

        sPath1 = "hello|*|*"
        sPath2 = "hello|world|*"

        xPath1 = CViewDimNodePath(sPath1)
        xPath2 = CViewDimNodePath(sPath2)

        print("")

        xPath1.SetInPathDict(dicPath, 0, _xDefault=iDefault)
        print(f"dicPath: {dicPath}")
        assert len(dicPath) == 0

        xPath1.SetInPathDict(dicPath, 1, _xDefault=iDefault)
        print(f"dicPath: {dicPath}")
        assert len(dicPath) == 1

        xPath2.SetInPathDict(dicPath, 1, _xDefault=iDefault)
        print(f"dicPath: {dicPath}")
        assert len(dicPath) == 1

        xPath2.SetInPathDict(dicPath, 2, _xDefault=iDefault)
        print(f"dicPath: {dicPath}")
        assert len(dicPath) == 2

        xPath2.SetInPathDict(dicPath, 1, _xDefault=iDefault)
        print(f"dicPath: {dicPath}")
        assert len(dicPath) == 1

        xPath1.SetInPathDict(dicPath, 0, _xDefault=iDefault)
        print(f"dicPath: {dicPath}")
        assert len(dicPath) == 0

    # enddef

    ################################################################################
    def test_get_path_dict_01(self):
        dicPath = {}
        iDefault = 0

        sPath1 = "hello|*|*"
        sPath2 = "hello|world|*"
        sPath3 = "hello|world|b"

        xPath1 = CViewDimNodePath(sPath1)
        xPath2 = CViewDimNodePath(sPath2)
        xPath3 = CViewDimNodePath(sPath3)

        print("")

        xPath1.SetInPathDict(dicPath, 1, _xDefault=iDefault)
        xPath2.SetInPathDict(dicPath, 2, _xDefault=iDefault)
        xPath3.SetInPathDict(dicPath, 3, _xDefault=iDefault)
        print(f"dicPath: {dicPath}")
        assert len(dicPath) == 3

        xPath = CViewDimNodePath("hello|moon|*")
        assert xPath.GetFromPathDict(dicPath, iDefault) == 1

        xPath = CViewDimNodePath("hello|world|a")
        assert xPath.GetFromPathDict(dicPath, iDefault) == 2

        xPath = CViewDimNodePath("hello|world|b")
        assert xPath.GetFromPathDict(dicPath, iDefault) == 3

        xPath = CViewDimNodePath("hero|world|a")
        assert xPath.GetFromPathDict(dicPath, iDefault) == iDefault

    # enddef


# endclass
