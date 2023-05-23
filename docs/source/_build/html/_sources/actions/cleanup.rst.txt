.. _cleanup:
.. |cleanup| image:: ../../../python/trigger/ui/icons/cleanup.png

=================
Cleanup |cleanup|
=================

Cleanup action is an action to help keep the rig file as clean as possible. It validates the current state of the scene with checked items and tries to fix
those issues automatically.

    - **Unknown nodes:** Deletes any unknown nodes in the scene, usually caused by missing plugins
    - **Blind Data:** Deletes the blind data nodes which is frequently comes from the game assets
    - **Unused Shading Nodes:** Prunes the scene from unused shaders
    - **Display Layers:** Deletes all display layers
    - **Animation Layers:** Deletes all animation layers
    - **Merge Similar File Nodes:** If two or more file nodes share the same file input, it keeps only the first one and makes re-connections.
    - **Merge Similar Shaders:** If two or more shaders are identical, uses only first one and makes re-connections.