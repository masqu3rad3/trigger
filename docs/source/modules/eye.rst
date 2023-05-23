.. _eye:

=========
Eye
=========

Eye module is a neighbour-aware module. This means, in rigging time, the module will look for sibling eye modules sharing the same group id and will
create a single master controller for all of them in addition to individual controllers.

This means, as long as the guides parented to the same limb-end any number of eyes or eye-like rigs can be created

Guides
------

Eye Modules must contain exactly 2 guide joints. First joint defines the position of the eye and the second one defines the initial aim orientation.

Additional properties:

- **Local Joints**: If checked, the deformation joints wont follow the plug, keeping the rig localized. This function is useful where you want to move the controllers with the character but deform a separate geometry locally.
- **Group ID**: When there are multiple eyes in the rig, the ones have the same Group ID, will share the same outer controller.

.. image:: /_images/eye_guides.png




Rig
---

Each rigged eye module contains a single deformation joint

.. image:: /_images/eye_rig.png


