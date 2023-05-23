.. _split_shapes:
.. |split_shapes| image:: ../../../python/trigger/ui/icons/split_shapes.png

=====================================
Split Shapes |split_shapes|
=====================================

Split Shapes is a blendshape action which splits the given shapes into different parts with customizable masks.

Split Shapes Action usually prepares the scene for Morph Actions. The most common usage is to gather symmetrically sculpted shapes and split them into vertical and horizontal splits to provide localized and asymmetrical controls.


Sample Workflow:

1. Import the sculpted blendshapes pack with an Import Asset Action or Assemble Action
2. Select the neutral mesh from the Maya outliner and hit **prepare** button in the Split Shapes action. A temporary blendshape will be created on neutral mesh with 3 preset split maps. Vertical Sharp, Vertical Smooth and Horizontal Sharp.
3. Using Maya's paint blendshape weights tool, paint each target separately. 

    In vertical maps, Left side of the character is represented by white. In horizontal maps upper sides of the character should be white. 
    The results for Vertical Sharp, Vertical Smooth and Horizontal Sharp maps should be similar to these:

    .. image:: /_images/split_shapes_ss1.png
4. If more split maps are required, duplicate the Neutral mesh, rename it as the extra split map that you want (e.g horizontal_smooth) and add it as an additional blendshape target to splitMaps_blendshape node and paint it as you like.
5. Hit **Save** button and browse a filepath to save the split maps. Next time you want to edit a map, selecting the neutral mesh and hitting prepare button will bring your painted maps from this file instead of just the blank template
6. Fill the **Blendshapes Root Group** section with the name of the group which holds all the blendshapes.
7. Fill the **Neutral Mesh** section with the name of the neutral mesh in the scene. As a convention, neutral mesh is part of the blendshape pack. Even though it is in the Blendshapes root group, the neutral must be specified here.
8. For each shape in the pack, we need to make a definition. Hit **New** button and a new pop up dialog should appear.
9. In the new menu, write down the shape name that is going to be splitted into the **Mesh** section. Then from the right hand side, select the split maps that you want to apply to this shape.

    .. image:: /_images/split_shapes_ss2.png
    *In this case, we are instructiong the lipPuckerer shape to be split into 4 parts using two split maps.*
10. Hit **Ok** and repeat the same step for each shape.

Use the preset split map names (vertical_smooth, vertical_sharp, horizontal_sharp, horizontal_smooth) as it is as long as they serve the purpose and do no substitute them with custom named split maps unless you know what you are doing. The reason for that is, these will always split the shapes with the correct naming convention in a way that the Morph Action Action will understand.

For example, if we are splitting the lipPuckerer both horizontally and vertically, when the preset names are used, it will split the shape as

- *ULlipPuckerer (upper left)*
- *URlipPuckerer (upper right)*
- *DLlipPuckerer (lower left)*
- *LRlipPuckerer (lower right)*

After Split Shapes Actions execution complete during building, the splitted shapes will be gathered in a new group called SPLITTES_SHAPES_grp and the unsplit version will be deleted. Any shape not defined in the Split Definitions will stay untouched where it was.