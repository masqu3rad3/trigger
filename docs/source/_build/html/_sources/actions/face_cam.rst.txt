.. _face_cam:
.. |face_cam| image:: ../../../python/trigger/ui/icons/face_cam.png

=========================
Face Cam |face_cam|
=========================

Face Cam action creates a camera fixed on a part of the rig. It can be rotated freely but the translation is limited within the boundaries of given mesh.
Since faces are the most common use, it is named after that but can be used for any part of the rig.

Face Cam action has following properties:

    - **Camera Name**: Nothing fancy, just a name for the camera. Default 'faceCam'
    - **Face Mesh**: The mesh object that the camera will be focused on.
    - **Parent Node**: Parent object that the camera will be constrained
    - **Focal Length**: Focal length of the camera. Default 50
    - **Initial Distance**: The distance between camera and mesh
    - **Limit Multiplier**: The multiplier value which will define the extra transformation boundaries. For example if this set 2, the translation boundaries limits the camera will be doubled

.. tip:: 
    The boundary limits of face cam is calculated by defined face mesh * limit multiplier value