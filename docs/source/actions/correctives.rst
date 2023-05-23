.. _correctives:
.. |correctives| image:: ../../../python/trigger/ui/icons/correctives.png

=========================
Correctives |correctives|
=========================

Correctives Actions creates deltas from sculpted corrective blendshapes and implements them into the rig.

It can contain as much as definitions as you require in a single Action item.
Hitting the Add New Definition button creates a new definition.

Each definition contains a set of properties:

    - **Mode:** Switches between Vector and Single axis modes. Vector is useful for multi axis moving joints like shoulders. Single Axis is less resource consuming and suitable for joints moving on a single axis.
    - **Driver Transform:** This is usually the bone object that we put the PSD (pose space deformer) on
    - **Controller:** object which is getting used to acquire the pose that we want to put corrective shape. This must be the currently active controller. For example if there are switchable IK and FK controllers for the defined Driver Transform and the default mode is IK, then the IK controller needsto be selected. Since the PSD is getting the angle information from the joint, the same corrective will be triggered with both IK and FK once created. This is only for initial creation of PSDs and delta shapes
    - **Target Transform:** Holds and displays the captured values of Controller.
    - **CAPTURE button:** captures the current transform values of Controller. Move and/or rotate the controller object to the pose that you want to activate the corrective 100% and hit this button to capture the pose to be used later during rig creation Up O ject: Only available in Vector mode. Defines the up vector to align the PSD. Usually any parent node of the Driver Transform works.
    - **Corrected Shape:** The sculpted shape of the corrected pose. This mesh MUST be sculpted from the captured state of target transform. This line can be left empty. In that case only the PSD will be created.
    - **Skinned Mesh:** the mesh that has the skincluster applied.

.. warning:: 
    This Action requires the extractDeltas.py plugin to work


Sample workflow where we are putting a corrective on shoulder area:

1. Run the trigger actions until this action. Most of the rig should be functional before adding correctives. Click 'Add Definition' button for the first corrective
2. Select the upper arm joint and click the "<" icon next to the 'Driver Transform' section
3. Select the currently active controller that moves the upper arm. It should be the hand controller if the default mode is IK and upper Arm controller if FK.
4. Hit "<" next to the Controller section.
5. Pose the shoulder area into the pose that you want to apply correctives. and Hit "CAPTURE" button.
6. Select the skinned mesh. First click "<" next to the skinned Mesh section then go to the RigHelpers shelf and click the copy() item from next to the External section. This will duplicate the skinned mesh, unlock the transforms and delete the excess intermediate objects.
7. sculpt & export the mesh to an alembic cache.
8. We need to make sure the sculpted mesh is getting imported on the next run. So add an import asset or assemble action above the correctives action and define the mesh you just exported in here.
9. Lastly while the mesh you exported is selected, hit '<' in Corrected Shape row to add it into correctives definition
10. To add more correctives, hit 'Add New Definition' and repeat steps 2-9

The next time Build Rig command executed, the PSD and corrective deltas will be created on the fly.

To-do's
--------

- implement jointify to convert corrective blendshapes into joint based deformations
- A helper tool to manage & prepare corrective shape stages for sculptors which uses the correctives defined here (Will use the *.tr file)