.. _arm:

========
Arm
========

Guides
------

Arm Module guides needs to have exactly **4 joints**:
  
    - Collar
    - Shoulder
    - Elbow
    - Hand

Additional Guide Properties:

- **Local Joints**: If checked, the deformation joints wont follow the plug, keeping the rig localized. This function is useful where you want to move the controllers with the character but deform a separate geometry locally.


.. image:: /_images/arm_guides.png




Rig
---

The rigged module contains 13 deformation joints (10 x ribbon joints, Hand, Collar, Elbow)
It has the following features:

  - IK/FK switch
  - Stretchy (and squashy) IK with volume preservation option
  - Soft IK
  - Switchable between Rotate Plane Solver and Single Chain Solvers (Pole Vector Attribute on hand controller)
  - Elbow pinning
  - Upper and Lower arm can be independently scaleable
  - Auto Shoulder movement
  - Animateable shoulder alignment
  - Auto/Manual Twists for Hand and Shoulder
  - Extra Tweak Controls

.. image:: /_images/arm_rig.png
