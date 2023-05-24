.. _weights:
.. |weights| image:: ../../../python/trigger/ui/icons/weights.png

=====================================
Weights |weights|
=====================================

Weights Action stores and restores weight values to any deformer that is defined in its list of deformers.

In case the deformer does not exist, it will create it.

Usage of Weights action is similar to other actions that works with Maya scene directly. Remember that all influences that will affect the deformer must be
already present in the scene when this action run.
For example, you cannot add weights to a character before the kinematics action because at the time the Weights Action runs, there won't be any joints to
affect the skinclusters.

Ideally, the session should be executed until the Weights Action. Then you can regularly skin cluster the objects to the joints and paint the weights.
Then you can define the deformers on the Weights Action and save it into a file.

The easiest way to do that is to select the mesh and hit **Get** button from the right side menu. This will drop down all valid modifiers applied on the mesh.

Multiple meshes can be selected and **Add All Items** command can be used from the end of the list to define multiple deformers at the same time

.. image:: /_images/weights_ss.png

- **File Path**: The absolute path where the trigger weight file (.trw) will be stored AND saved with 'Save' button
- **Deformers**: The list of deformers currently defined in the action
- **New**: Pops up an input window which you can enter the name of the new deformer manually.
- **Rename**: Lets you edit the name of the currently selected deformer from the list
- **Remove**: Removes the selected deformer from the action definition list
- **Clear**: Removes everything from the action definition list
- **Save Button**: Saves all shaders and shader-mesh pair information in the CURRENT scene to the file defined in File Path. Think twice before hitting that. Use Save as or increment if you have doubts.
- **Save As**: Brings up the file browser to specify a save as location and saves it
- **Increment**: Versions up the file defined in File Path

.. tip:: 
    Deformers are not limited with skin clusters. Currently skincluster, shrinkwrap, deltamush and blendshape deformers are supported.