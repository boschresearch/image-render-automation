# catharsys configure ideas

from catharsys.plugins.std.blender import define as blend

xComp = blend.compositor.CDefine([
    blend.compositor.CFileOutput(
        _sOutput="Image", 
        _sFolder="Image", 
        _eContentType=blend.compositor.EFileOutputContentType.IMAGE,
        _xFormat=blend.compositor.CFileFormatPng(
            blend.compositor.EPixelType.RGB,
            blend.compositor.EColorDepth.BITS8,
            15,
        )
    )
])

xOutImg = blend.render.output.CImage(xComp)




# if __name__ == "__main__":
#     xFileOutPng8 = CConfigBlenderCompositorFileOutput()
#     # xComp = CConfigBlenderCompositor([xFileOutPng8])
#     xRenderOutImg = CConfigBlenderRenderOutputImage(lFileOut=[xFileOutPng8])
#     xRenderListAll = CConfigBlenderRenderOutputList([xRenderOutImg])
#     CActionBlenderRenderStd("render", [])