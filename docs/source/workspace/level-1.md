
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
# Level 1 - "Just Render" Configuration

This workspace demonstrates the minimal setup to render anything with Catharsys. This is also the first step in a series of documents introducing the various aspects of Catharsys setup by step.

## Installation

To get started, let's install the workspace from a template,

:::{admonition} Shell
`cathy install template workspace-just-render`
:::

This command will ask you a couple of questions, as it allows you to create your own workspace, with your own names from a template. For this example, we will choose "level-1" as *module name* and "just-render" as *configuration name*. The output from the command should look something like this:

:::
    Creating template 'workspace-just-render'
    Enter new module name (press RETURN to abort): level-1
    New module path: [...]/level-1
    Create module folder [y]/n:
    Please enter values for the following template parameters:
    Using 'Configuration' = 'just-render'
    Using 'MODULE-NAME' = 'level-1'
    Do you want to use these values [y]/n/x:
    _cfg-name_ -> just-render
:::

To simplify working with the workspace, you can use VS-Code. To initialize the workspace for VS-Code, change to the workspace folder, ensure that you are in the conda environment you want to use and execute the command,

:::{admonition} Shell
`cathy code init`
:::

This generates a workspace file for VS-Code. You can open this workspace from VS-Code or run the following command,

:::{admonition} Shell
`cathy code show`
:::


## Initialization

Since we want to render something with Blender, we also need to initialize Blender for this workspace. If you havn't installed Blender, yet, go back to the Catharsys system installation documentation, and find the part for installing Blender. Note that this template workspace expects Blender version 3.3. 

Initialize Blender for all configurations of the newly created workspace with the command,

:::{admonition} Shell
`cathy blender init --all --addons`
:::

Note that there will be separate Blender installations, one for each combination of Conda workspace and Catharsys version. Since every configuration can specify a different Blender version, there is a Blender configuration folder for each configuration called `_Blender`. This folder contains the Blender user preferences and symbolic links to the installed addons for this configuration. How you specify this, will be discussed later, when we talk about the *execution file*.

To get an overview of the available configurations and actions in the workspace, run the command,

:::{admonition} Shell
`cathy ws info`
:::

To start our first render, let's *launch* an action,

:::{admonition} Shell
`cathy ws launch -c just-render -a run`
:::

If everything has been installed correctly, you should now find an image in the folder `_render/rq0004/just-render/Camera/Image`. 

Clearly, you could have rendered this image by just starting up Blender and rendering it. However, even this simple setup can be helpful, if you want to render many frames of an animation. In this case, Catharsys can split the rendering into a number of jobs that can be executed in parallel on a GPU cluster running the LSF job distribution system, or simply on a machine with a number of graphics cards.


## Configuration Files Overview

The configuration files of the workspace are located in the folder `config/just-render`. There you can find the following files:

- `launch.json5`: The launch file, specifying the available actions and defining action parameters. This file **must** be called `launch.json` or `launch.json5`.
- `manifest.json5`: The manifest file, which specifies the configuration *types* per action.
- `trial.json5`: The trial file gives a list of configurations per configuration *type* for each action, as specified by the manifest.
- `exec.json5`: The execution file defines how to execute the action. For Blender rendering it also defined which Blender version to use and which addons.

The Blender render action also needs these configuration files:

- `capture.json5`: The capture configuration specifies how to capture the images. For standard rendering this is simply the framerate. For rolling shutter rendering, this contains the rolling shutter parameters.
- `render.json5`: The render configuration configures the renderer and defines which render outputs to generate.
- `Test.blend`: This is Blender file that is used for rendering.

The file `Launch.ipynb` is a Jupyter notebook that allows to launch actions and view the results via the Catharsys API.

Now, let's now have a look at the various configuration files.

## The Launch File

The launch file must be called `launch.json` or `launch.json5` and is meant to simplify starting an action for a configuration. Instead of putting all the necessary parameters in a command line, they are contained in the launch file. The launch file in this example contains documentation for all the parameters. In the following, the most important parts are discussed here.

### Actions

:::json
{
    // The type identifier of this file
    sDTI: "/catharsys/launch:3.0",
    
    // The id of this launch parameter set
    sId: "$filebasename",
    
    // Some information what this configuration is for
    sInfo: "Minimal workspace for rendering with Blender file",

    // The map of all actions that can be launched
    mActions: {
        // An arbitrarily chosen name for an action.
        // In this case it makes sense to call it 'render', as it
        // executes the rendering action.
        run: {
            sDTI: "/catharsys/launch/action:1.0",
            // The id of the action
            sActionDTI: "/catharsys/action/std/blender/render/std:1.0",
            
            // The action configuration
            mConfig: {
                // ...
            }
            // ...
        }
    }
}
:::

For the naming convention and the meaning of the `sDTI` elements, see the {doc}`workspace basics <basics>` documentation. 

The file's id is defined via a variable, using the syntax `$[variable name]`. See the {external+functional-json:doc}`ison language <language>` documentation for more information on using variables and functions in JSON files. For a list of available variables see the {doc}`configuration variables <../config_proc>` documentation.

The main Block in the launch file is the `mActions` block. Here, a set of actions is defined. The elements in the `mActions` block are freely choosable names of actions. Each action is again a dictionary specifying the action type and its configuration. In the example above, the action is called `run`. This is the action name you use when launching an action from the command line. The actual action that is started, is referenced by the `sActionDTI` element. In this case, we want to execute the standard Blender rendering action version 1.0.

:::{note}
You can find an overview of the available standard actions {external+image-render-actions-std:doc}`here <actions-overview>`.
:::

:::{note}
When an action is installed in the Conda environment, it registers its' name (the action DTI) as an entry point. The Catharsys system uses the name specfied in the `sActionDTI` element, to search for an action in the current environment. It's fairly straight forward to write your on action and register it in the system using the standard action template. This template can be installed with the command `cathy install template std-action-python`.
:::

### Action Configuration

The action configuration parameters are contained in the `mConfig` block. In this example,

:::json
mConfig: {
    sDTI: "/catharsys/launch/args:1.1",
    sInfo: "Render blender file",

    // IMPORTANT: All files of type '.json', '.json5' and '.ison' can be
    //            referenced by their basename alone, without the extension.
    //            The appropriate extension is added automatically.

    // The name of the trial file to use.
    sTrialFile: "trial",

    // The execution configuraion file.
    // IMPORTANT: All file paths are regarded as relative 
    //            to the path of the current file.
    sExecFile: "exec",

    // [...]
}
:::

The `sInfo` element gives a short info about the action, which is displayed by the command `cathy ws info`.

The `sTrialFile` and `sExecFile` reference the trial and execution configuration used for this action. The trial file specified which (partial) configurations to use for this action and the execution file specifies how to execute the action. For this Blender render action, the execution file specifies the Blender version to use, which Blender addons to install and whether Blender is executed locally or on a job distribution system. 

:::{note}
The Blender initialization command `cathy blender init` uses the execution file of a configuration to know which Blender addons to install and how to configure them.
:::

The trial and execution files are discussed in more detail below.

### Render Action Parameters

The render action expects a number of additional parameters in the `mConfig` block:

- `iFrameFirst`: The index of the first frame to render
- `iFrameLast`: The index of the last frame to render
- `iFrameStep`: The step increment for the frame index
- `iRenderQuality`: The render quality in samples per pixel. This value will be used in the name of the top render folder. For example, if the render quality is set to 4, the top render folder is called `rq0004`. You can overwrite this behaviour by specifying the element `sTopFolder`.
- `sTopFolder`: If this parameter is specified, it defines the name of the top folder, instead of using the render quality. This is useful for actions that do not render, or if the render action just generates a new Blender file. This is discussed in the render output list configuration.
- `bDoProcess`: Boolean flag, wether to actually process the action or not. If this is set to `false`, the configurations are processed but the actual action is not executed. For the render action, also the Blender file is modified, if so specified, but the rendering itself is not executed. This can be used in combination with the parameter `bDoStoreProcessData` to not render the Blender file but just to save it for debugging.
- `bDoOverwrite`: When this is `true` all output files that will be generated by this action will be deleted beforehand if they are already present. 
- `bDoStoreProcessData`: When this is set to `true`, the modified Blender file is stored after all modifications have been applied but before it is rendered. For other actions, this paramter may have no effect or store some other data.


## The `__platform__` Element

Before we discuss the execution file, a short aside explaining the `__platform__` element, that can be used as part of any dictionary. Before a dictionary is parsed by the configuration parser ({external+functional-json:doc}`ISON parser <language>`), it looks for a `__platform__` element. This can be part of any dictionary not just at the top level of a JSON file. The `__platform__` block is replaced by a `__data__` block depending on the operating system and node (machine name). This is best seen in an example,

:::json
{
    sDTI: "/catharsys/exec/blender/std:2.1",
    sId: "${filebasename}",

    __platform__: {
        Windows: {
            __data__: {
                sDTI: "/catharsys/exec/blender/std:2.1"
            }
        },
        Linux: {
            "hi-025l": {
                __data__: {
                    // Use the LSF job distribution system (must be installed on system)
                    sDTI: "/catharsys/exec/blender/lsf:2.1",

                    // [...]
                },
            },
        },
    },
}
:::

The whole `__platform__` block is replaced by the *contents* of the corresponding `__data__` block, depending on the operating system, `Windows` or `Linux`, and for Linux only if the current node is called `hi-025l`. The contents of the `__data__` block overwrites any elements of the same name defined outside the `__platform__` block. In this case, the `sDTI` element at the top will be overwritten by the platform specific `sDTI` element.

The `__platform__` is also helpful to specify absolute paths of addons or assets depending on the machine the configuration is executed on.

## The Execution File


## The Manifest File


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


## The Trial File


## The Render Action Configurations


