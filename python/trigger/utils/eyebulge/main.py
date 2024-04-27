# pylint: disable=consider-using-f-string
"""Core Module for Eye-Bulge."""

import logging

from maya import cmds

from trigger.library import attribute
from trigger.utils.eyebulge import methodology

LOG = logging.getLogger(__name__)


class EyeBulge(object):
    """Main Eye Bulge Handler object."""

    valid_methods = list(methodology.classes.keys())

    def __init__(
        self,
        method="shrinkWrap",
        face_mesh=None,
        eye_joint=None,
        pupil_joint=None,
        eye_geo=None,
        controller=None,
        name="eye_bulge",
        module_group="eye_bulge_grp",
    ):
        """Initialize the eye bulge core.

        Args:
            method (str, optional): Eye bulge methodology.
            Valid values are shrinkWrap and dnSculpt. Defaults to shrinkWrap.
            face_mesh (str): Mesh that the bulge will interact with.
            eye_joint (str): Eye Joint.
            pupil_joint (str): Pupil Joint.
            eye_geo (str): Eye Ball mesh.
            controller (str, optional): Controller that will hold the exposed
            attributes. Defaults to None.
            name (str): name of the module. Defaults to "eye_bulge". This is
            actually not mandatory but we need to define unique names per eye
            for creatures that have more than one eye.
            module_group (str, optional): the group to hold the created
            elements. Defaults to "eye_bulge_grp".
            dev_mode (bool): If true, cleanup methods will be skipped.
            Good for debugging / developing.
        """

        self._method = None
        self._face_mesh = None
        self._eye_joint = None
        self._pupil_joint = None
        self._eye_geo = None
        self._controller = None
        self._name = None
        self._module_group = None

        self.method = method
        self.face_mesh = face_mesh
        self.eye_joint = eye_joint
        self.pupil_joint = pupil_joint
        self.eye_geo = eye_geo
        self.controller = controller
        self.name = name
        self.module_group = module_group

        self.dev_mode = False

    @property
    def method(self):
        """Return the defined methodology."""
        return self._method

    @method.setter
    def method(self, value):
        """Set the Eye Bulge methodologyy."""
        if value not in self.valid_methods:
            raise ValueError(
                "{0} is not in valid methods. Valid methods are {1}".format(
                    value, self.valid_methods
                )
            )
        self._method = value

    @property
    def face_mesh(self):
        """Return the defined face mesh."""
        return self._face_mesh

    @face_mesh.setter
    def face_mesh(self, value):
        """Set the face mesh."""
        self._face_mesh = self.validate_transform(value)

    @property
    def eye_joint(self):
        """Return the defined eye joint."""
        return self._eye_joint

    @eye_joint.setter
    def eye_joint(self, value):
        """Set the eye joint."""
        self._eye_joint = self.validate_joint(value)

    @property
    def pupil_joint(self):
        """Return the defined pupil joint."""
        return self._pupil_joint

    @pupil_joint.setter
    def pupil_joint(self, value):
        """Set the pupil joint."""
        self._pupil_joint = self.validate_joint(value)

    @property
    def eye_geo(self):
        """Return the defined eye geometry."""
        return self._eye_geo

    @eye_geo.setter
    def eye_geo(self, value):
        """Set the eye geometry."""
        self._eye_geo = self.validate_transform(value)

    @property
    def controller(self):
        """Return the defined controller."""
        return self._controller

    @controller.setter
    def controller(self, value):
        """Set the controller."""
        self._controller = self.validate_transform(value)

    @property
    def name(self):
        """Return the defined name."""
        return self._name

    @name.setter
    def name(self, value):
        """Set the name of the eye bulge."""
        if not isinstance(value, str):
            raise ValueError(
                "Name must be a string value. Got {}".format(value)
            )
        self._name = value

    @property
    def module_group(self):
        """Return the defined module group."""
        return self._module_group

    @module_group.setter
    def module_group(self, value):
        """Set the name of the module group."""
        if not isinstance(value, str):
            raise ValueError(
                "Module group must be a string value. Got {}".format(value)
            )
        self._module_group = value

    def validate_transform(self, transform):
        """Make sure the transform exists in the scene."""
        if not transform:
            return None
        _scene_transform = cmds.ls(transform, type="transform")
        if not _scene_transform:
            raise ValueError(
                "{} does not exist in the scene, or it is not a transform node".format(
                    transform
                )
            )
        return transform

    def validate_joint(self, joint):
        """Make sure the joint exists in the scene."""
        if not joint:
            return None
        _scene_joint = cmds.ls(joint, type="joint")
        if not _scene_joint:
            raise ValueError(
                "{} does not exist in the scene, or it is not a joint object".format(
                    joint
                )
            )
        return joint

    def set_property(self, key, value):
        """Set the property value on active method."""

        if not self._method:
            raise ValueError(
                "Method is not defined. Method needs to be defined first to set its attributes."
            )

        _active_method = methodology.classes[self._method]

        _available_properties = list(_active_method.properties.keys())
        if key not in _available_properties:
            raise ValueError(
                "{0} is not an available property on {1}".format(
                    key, self._method
                )
            )

        _active_method.properties[key] = value

    def create(self):
        """Create the Eye-bulge."""

        # instanciate the methodologt
        _method_obj = methodology.classes[self._method]

        # make sure the module group exists before passing it to object.
        if not cmds.objExists(self._module_group):
            cmds.group(name=self._module_group, empty=True)
            if not self.dev_mode:
                attribute.lock_and_hide(self._module_group)
                if cmds.objExists("modules"):
                    cmds.parent(self._module_group, "modules")

        # feed the common input information
        _method_obj.inputs["name"] = self._name
        _method_obj.inputs["face_mesh"] = self._face_mesh
        _method_obj.inputs["eye_mesh"] = self._eye_geo
        _method_obj.inputs["eye_joint"] = self._eye_joint
        _method_obj.inputs["pupil_joint"] = self._pupil_joint
        _method_obj.inputs["controller"] = self._controller
        _method_obj.inputs["module_group"] = self._module_group
        _method_obj.dev_mode = self.dev_mode

        _method_obj.run()

        _preference_nodes = _method_obj.pref_nodes
