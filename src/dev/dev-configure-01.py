# develop python functions to generate a catharsys configuration

import enum
# import StrEnum


class EConfigForm(str, enum.Enum):
    Value = "value"
    FileJSON = "file/json"
# endclass

class EConfigType(str, enum.Enum):
    BlenderRenderOutputList1 = "/catharsys/blender/render/output-list:1"
# endclass


class EBlenderActionType(str, enum.Enum):
    RenderStandard1 = "/catharsys/action/std/blender/render/std:1.0"
    ProcessDepth1 = "/catharsys/action/std/blender/post-render/proc-depth:1.0"
# endclass


class CConfigDefinition:
    c_lConfigIds: set[str] = set()

    def __init__(self, eType: EConfigType | str, bAddToPath: bool = True, sId: str = None):
        self._sType: str = str(eType)
        self._sForm: str = None
        self._bAddToPath: bool = bAddToPath

        if isinstance(sId, str):
            self._sId: str = sId
        else:
            sBaseId: str = self._sType.replace("/", "_")
            sId = f"{sBaseId}_1"
            iIdx = 2
            while sId in CConfigDefinition.c_lConfigIds:
                sId = f"{sBaseId}_{iIdx}"
                iIdx += 1
            # endwhile
            CConfigDefinition.c_lConfigIds.add(sId)
            self._sId = sId
        # endif

    # enddef

    @property
    def sId(self) -> str:
        return self._sId
    # enddef

# endclass


class CActionDefinition:
    def __init__(self, sName: str, eType: enum.Enum | str, lConfigs: list[CConfigDefinition] = None, lDependencies: list["CActionDefinition"] = None):
        self._sName: str = sName
        self._sType: str = str(eType)

        if isinstance(lConfigs, list):
            self._lConfigs: list[CConfigDefinition] = lConfigs
        else:
            self._lConfigs: list[CConfigDefinition] = []
        # endif

        if isinstance(lDependencies, list):
            self._lDeps: list[CActionDefinition] = lDependencies
        else:
            self._lDeps: list[CActionDefinition] = []
        # endif

      
    # enddef

    @property
    def sName(self) -> str:
        return self._sName
    # enddef

# endclass


class CActionGroup:
    def __init__(self, sName: str, lElements: list["CActionGroup" | CActionDefinition] = None):
        self._sName = sName
        if isinstance(lElements, list):
            self._lElements: list["CActionGroup" | CActionDefinition] = lElements
        else:
            self._lElements: list["CActionGroup" | CActionDefinition] = []
        # endif
    # enddef
# endclass

class CActionManifest:
    def __init__(self, lActions: list[CActionDefinition | CActionGroup] = None, sId: str = None):
        if isinstance(sId, str):
            self._sId = sId
        else:
            self._sId = "${filebasename}"
        # enddef

        if isinstance(lActions, list):
            self._lActions: list[CActionDefinition | CActionGroup] = lActions
        else:
            self._lActions: list[CActionDefinition | CActionGroup] = []
        # endif
    # enddef
# endclass

class CTrialDefinition: 
    def __init__(self, sId: str, )

if __name__ == "__main__":
    
    cfgRender = CConfigDefinition(EConfigType.BlenderRenderOutputList1, False)
    
    actRender = CActionDefinition("render", EBlenderActionType.RenderStandard1, 
                                  lConfigs=[cfgRender],)
    
    xManifest = CActionManifest([
        
    ])