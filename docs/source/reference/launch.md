# Launch Configuration

The launch configuration defines and parametrizes the actions you can execute in a workspace. See also the launch file documentation [here](launch-file-info). A full, simple example can be found [here
](https://github.com/boschresearch/image-render-templates/blob/main/workspace-just-render/config/_cfg-name_/launch.json5). A more complex example is [here](https://github.com/boschresearch/image-render-workspace-examples/blob/main/config/usecase/rolling-shutter/launch.json5).


| Tag         | Type   | Description                                         | Value Constraints              | Example         |
| ----------- | ------ | --------------------------------------------------- | ------------------------------ | --------------- |
| sDTI        | string | DTI of launch file. Must be this value.             | `/catharsys/launch:3.0`        |                 |
| sId         | string | Id of launch file.                                  | Any string.                    | `$filebasename` |
| sInfo       | string | Information string shown by command `cathy ws info` | Any string.                    |                 |
| mGlobalArgs | dict   | Default arguments used by all actions.              | See [below](#launch-arguments) |                 |
| mActions    | dict   | Definition of actions that can be executed.         | See [below](#action-arguments)                      |                 |

## Action Arguments

The top level elements of the `mActions` dictionary are user defined names of the actions. These names are used in the `-a` argument of the command `cathy ws launch -c [config] -a [action]`, to determine which action is to be executed for a configuration. Each action block must either contain an action definition or an action alias definition. Note that action blocks can also be nested. 

### Action Definition

An action definition uses the DTI `/catharsys/launch/action:1.0`.
Here is an example of a standard action definition:

```json
"mActions": {
    "my_render": {
        "sDTI": "/catharsys/launch/action:1.0",
        "sActionDTI": "/catharsys/action/std/blender/render/std:1.0",
        "mConfig": {
            // Launch arguments for action
        }
    }
}
```

This action would be executed via `cathy ws launch -c trial-01 -a my_render`. 

Here is an example of nested action names:

```json
"mActions": {
    "my_render": {
        "std": {
            "sDTI": "/catharsys/launch/action:1.0",
            "sActionDTI": "/catharsys/action/std/blender/render/std:1.0",
            "mConfig": {
                // Launch arguments for action
            }
        },
        "rs": {
            "sDTI": "/catharsys/launch/action:1.0",
            "sActionDTI": "/catharsys/action/std/blender/render/rs:1.0",
            "mConfig": {
                // Launch arguments for action
            }           
        }
    }
}
```
These actions would be executed via `cathy ws launch -c trial-01 -a my_render/std` and `cathy ws launch -c trial-01 -a my_render/rs`. 

The action definition dictionary must have these elements:

| Tag        | Type   | Description                                                                                            | Value Constraints                       | Example |
| ---------- | ------ | ------------------------------------------------------------------------------------------------------ | --------------------------------------- | ------- |
| sDTI       | string | DTI of action arguments. Must be this value.                                                           | `/catharsys/launch/action:1.0`          |         |
| sActionDTI | string | DTI of action to use. See {external+image-render-actions-std:doc}`actions overview <actions-overview>` | DTI of any action installed in environment |         |
| mConfig    | dict   | Dictionary of [launch arguments](#launch-arguments).                                                   |                                         |         |


### Action Alias

It is also possible to define action aliases, that refer to other actions, but overwrite some launch arguments. In this way, you can, for example, have an action that generates a Blender file for debugging but does not render the actual scene as an alias of the actual render action.

An action alias uses the DTI `/catharsys/launch/action-alias:1.0`. Here is an example,

```json
"mActions": {
    "my_render": {
        "image": {
            "sDTI": "/catharsys/launch/action:1.0",
            "sActionDTI": "/catharsys/action/std/blender/render/std:1.0",
            "mConfig": {
                // Launch arguments for render action
                "bDoProcess": true,
                "bDoStoreProcessData": false,
            }
        },
        "blend": {
            "sDTI": "/catharsys/launch/action-alias:1.0",
            "sActionName": "my_render/image",
            "mConfig": {
                // Overwrite launch arguments of action "my_render/image"
                "bDoProcess": false,
                "bDoStoreProcessData": true,
            }           
        }
    }
}
```
These actions would be executed via `cathy ws launch -c trial-01 -a my_render/image` and `cathy ws launch -c trial-01 -a my_render/blend`. 

The action alias definition must have these elements:

| Tag         | Type   | Description                                          | Value Constraints                     | Example |
| ----------- | ------ | ---------------------------------------------------- | ------------------------------------- | ------- |
| sDTI        | string | DTI of action arguments. Must be this value.         | `/catharsys/launch/action:1.0`        |         |
| sActionName | string | The name of the action in this launch file to use.   | Any action name defined in this file. |         |
| mConfig     | dict   | Dictionary of [launch arguments](#launch-arguments). |                                       |         |


## Launch Arguments

The launch arguments listed here can be used in the `mGlobalArgs` block as well as in the `mConfig` block of the actions. 

```{Note}
The `mGlobalArgs` dictionary defines default values that are used by all actions.The elements defined here are **not** global variabels. 
This dictionary should probably be called `mDefaultArgs` instead. This may be changed in a future version.
```

| Tag                 | Type   | Description                                                           | Value Constraints                            | Example   |
| ------------------- | ------ | --------------------------------------------------------------------- | -------------------------------------------- | --------- |
| sDTI                | string | DTI of launch arguments structure. Must be this value.                | `/catharsys/launch/args:1.1`                 |           |
| sTrialFile          | string | Name of the trial configuration file to be used.                      | Relative path to file. Extension not needed. | `"trial"` |
| sExecFile           | string | Name of the execution configuration file to be used.                  | Relative path to file. Extension not needed. | `"exec"`  |
| iFrameFirst         | int    | Index of first frame to render.                                       | `>= 0`                                       | 1         |
| iFrameLast          | int    | Index of last frame to render.                                        | `>= iFrameFirst`                             | 1         |
| iFrameStep          | int    | Frame increment                                                       | `>= 1`                                       | 1         |
| iRenderQuality      | int    | Render quality. For Blender the number of rays per pixel.             | `>= 1`                                       | 256       |
| sTopFolder          | string | (opt) If given, defines the name of the top production folder.        | Any string that can be used as folder name.  | `"blend"` |
| bDoProcess          | bool   | Flag whether to perform action (true) or just generate config.        | true, false                                  | true      |
| bDoOverwrite        | bool   | Flag whether to overwrite files (true) or not.                        | true, false                                  | false     |
| bDoStoreProcessData | bool   | For Blender render action stores the generated/modified Blender file. | true, false                                  | false     |

```{Note}
Apart from the elements given in the table, you can add any other element to the launch arguement dictionary block in the JSON file. All launch arguments are available to all other configurations via the dictionary `${action:args}`. 
For example, to access the `iFrameFirst` element of the current action, use `${action:args:iFrameFirst}`. If you add some other element `foo` to the launch arguments, then it is accessible via `${action:args:foo}`. See also [](var-action).
```
