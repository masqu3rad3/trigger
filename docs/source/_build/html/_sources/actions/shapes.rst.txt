.. _shapes:
.. |shapes| image:: ../../../python/trigger/ui/icons/shapes.png

=====================================
Shapes |shapes|
=====================================

Shapes Action stores and loads the edits on controller curves.

When the action runs, it only replaces the curves already existing in the scene, ignoring the rest. Similar to Look Action, it collects the current maya scene information during save. Therefore it is advised to be careful when hitting save button since it will replace the already existing Trigger Shapes file (.trs) with whatever the scene contains.

Common usage of shapes action is to edit default controller shapes created with Kinematics Action.

1. Simply drop a Shapes action after the kinematics.
2. Run the session until Shapes action.
3. Edit the controller shapes to match the rig better
4. save the Shapes file.

With the next build, these shapes will be replaced with the default Kinematics shapes.

   - **File Path**: The absolute path where the Trigger Shapes file (.trs) will be stored AND saved with 'Save' button
   - **Save Button**: Saves all shaders and shader-mesh pair information in the CURRENT scene to the file defined in File Path. Think twice before hitting that. Use Save as or increment if you have doubts.
   - **Save As**: Brings up the file browser to specify a save as location and saves it
   - **Increment**: Versions up the file defined in File Path.

.. warning:: 
    Be careful when hitting the save button. The current scene will be used to overwrite the file.