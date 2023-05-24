.. _finger:

=========
Finger
=========

Finger module is a neighbour-aware module. The fingers who share the same hand-controller will have attributes created on the same area and will be considered as a group.

Guides
------

The minimum number of guide joints required for finger joint is 3
The last joint is the tip of the finger and won't have controller.
Essentially a 3 joint finger module has 2 segments.

Additional Properties:

- **Finger Type**: Will define the type of finger. 
- **Hand Controller**: The controller defined here will hold the bend and spread attribute for the finger.

.. image:: /_images/finger_guides.png

.. note::
    The spinner in the UI, next to the guide creation buttons are for segments, not joint count


Rig
---

.. image:: /_images/finger_rig.png
