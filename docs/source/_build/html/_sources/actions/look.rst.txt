.. _look:
.. |look| image:: ../../../python/trigger/ui/icons/look.png

===========================
Look |look|
===========================

Look action stores shaders and their matching geometry information and allows it to be loaded back at any time.

The usage of this action is very simple but requires attention because it directly uses scene information. A file can easily be overwritten with wrong information.

To prevent that, always make sure that the maya outliner hiearchy matches the same state to the look action is going to run.

Essentially, the most fool-proof way is to put and keep the Look action right after the import Asset or assemble action where we bring in the geometries.

    - **File Path**: The absolute path where the trigger look file (.trl) will be stored AND saved with 'Save' button
    - **Save Button**: Saves all shaders and shader-mesh pair information in the CURRENT scene to the file defined in File Path. Think twice before hitting that. Use Save as or increment if you have doubts.
    - **Save As**: Brings up the file browser to specify a save as location and saves it
    - **Increment**: Versions up the file defined in File Path.

.. warning:: 
    Be careful when hitting the save button. The current scene will be used to overwrite the file.