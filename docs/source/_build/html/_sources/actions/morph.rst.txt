.. _morph:
.. |morph| image:: ../../../python/trigger/ui/icons/morph.png

===========================
Morph |morph|
===========================

Morph Action can be used in a broad range from creating a couple of simple blendshapes to creating a complex FACS based facial rig with dozens of inbetweens and combinations.

The action strictly depends on naming conventions descriped in Blendshapes Naming Conventions. 

Morph Action creates all blendshapes, inbetweens and combinations (even combinations of combinations) based on this naming convention rules.

    - **Blendshapes Group**: The root group for all the involving shapes. Morph action will automatically figure out how to use which shape under this group based on their naming convention tags.
    - **Neutral Mesh**: The neutral state of the mesh. This will be used to calculate deltas and a duplicate of this will be created during the process if the morph mesh is not defined.
    - **Hook Node**: The controller node that will hold the connections. If the object is not exists in the scene, one group with the same name will be created.
    - **Morph Mesh**: If defined, the blendshape deformer will be applied to this mesh. Must share the same topology with Neutral Mesh.