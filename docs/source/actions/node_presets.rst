.. _node_presets:
.. |node_presets| image:: ../../../python/trigger/ui/icons/node_presets.png

===========================
Node Presets |node_presets|
===========================

Node Presets Action can store and load any property of any node in maya.

Similar to the other save-enabled nodes (e.g look, weights) Node Presets action interacts with the currently open maya scene to store the information into files.

Press the 'Get' button to add the selected nodes into the list. When saved or incremented, all possible values of the nodes listed in there will be stored in a file.

    - **File Path**: The absolute path where the trigger presets file (.trp) will be stored.
    - **Nodes List**: All properties of the nodes listed here will be stored
    - **Rename**: Pops up an edit line to rename the selected node in the list
    - **Get**: Gets the selected nodes and puts them into list. The selection type can either be a DAG or non-DAG node.
    - **Remove**: Removes selected node from the list
    - **Clear**: Removes everything from the list.
    - **Save**: Saves the current states of the nodes to the file
    - **Save As**: Pops up a file browser to define the save as location
    - **Increment**: Versions up the file and save it.