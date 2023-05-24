.. _script:
.. |script| image:: ../../../python/trigger/ui/icons/script.png

=====================================
Script |script|
=====================================

Script action is for running custom python scripts and commands inside Trigger context.

The modules imported and variables defined (even the global
ones) are not accessible other than the individual action module itself.

    - **File Path**: The python module or python script file (.py) which will be loaded. This can be left empty for the non-dependant simple cmds commands.
    - **Edit**: This button either opens the default code editor assigned for .py files by os or pops a browser windows to select a save location for a new .py file if nothing defined in file path section.
    - **Import As**: If the file defined in file path is a module, it will be imported as the word defined here
    - **Commands**: multiple commands can be entered separated with ';'

.. tip:: 
    simple commands may not require a file path defined. Cmds module can be imported and the command can run in commands section without 
    the need of any external file like this::
    from maya import cmds; cmds.delete("trigger_refGuides")
