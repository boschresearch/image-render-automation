
<!---
<LICENSE id="CC BY-SA 4.0">
    
    Image-Render Automation Functions module documentation
    Copyright 2022 Robert Bosch GmbH and its subsidiaries
    
    This work is licensed under the 
    
        Creative Commons Attribution-ShareAlike 4.0 International License.
    
    To view a copy of this license, visit 
        http://creativecommons.org/licenses/by-sa/4.0/ 
    or send a letter to 
        Creative Commons, PO Box 1866, Mountain View, CA 94042, USA.
    
</LICENSE>
--->
# Action Configuration

All configuration files apart from the `launch` file depend on the type of action that is executed. Every action can define an *action class* it belongs to, which results in a specific processing of the configuration files. So far, all actions belong to the *manifest-based* action class, which will be discussed in the following.

:::{note}
You can find an overview of the available standard actions {external+image-render-actions-std:doc}`here <actions-overview>`.
:::


## Manifest-based

As an example, we will use the most basic workspace that is included with the `image-render-setup` package, called `simple`. You can install it with the command:

:::{admonition} Shell
`cathy install workspace simple`
:::

Manifest-based actions demand two additional configurations files:

1. A *manifest* file, that defines the configuration types that are expected per action.
2. A *trial* file, that defines the actual configurations used per configuration type.

The manifest file in the `simple` example looks like this:

:::{code-block} json
{
    sDTI: "/catharsys/manifest:1.1",
    sId: "${filebasename}",

    mActions: {
        render: {
            sDTI: "manifest/action:1",
            lConfigs: [
                { sId: "render", sDTI: "blender/render/output-list:1", sForm: "file/json", bAddToPath: false },
                { sId: "cap", sDTI: "capture/std:1", sForm: "file/json", bAddToPath: false },
                { sId: "cam", sDTI: "camera-name:1", sForm: "value" },
                { sId: "mod", sDTI: "blender/modify:1", sForm: "file/json" },
                { sId: "anim", sDTI: "blender/animate:1", sForm: "file/json" },
            ],
            lDeps: []
        }
    }
}
:::

:::{note}
Note the use of the variable `${filebasename}` in the configuration. When processed this string is replaced by the file's basename, i.e. `manifest` in this case. For a description of all available variables see {doc}`config_proc`.
:::

