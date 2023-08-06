"""Create a random animation."""

import random
from maya import cmds
import logging

from trigger.library import attribute

LOG = logging.getLogger(__name__)

animation_duration = 5000 # as frames

class Collector(object):
    """Collects controllers and attributes."""
    def __init__(self):
        self._controllers = []

    def add_morph_controllers(self, morph_hook):
        """Get morph controllers."""
        all_morphs = cmds.listAttr(morph_hook, userDefined=True)
        for morph_attr in all_morphs:
            remap_node = cmds.listConnections("{0}.{1}".format(morph_hook, morph_attr), source=True, destination=False,
                                              type="remapValue")
            if remap_node:
                cont = cmds.listConnections("{0}.inputValue".format(remap_node[0]), source=True, destination=False,
                                            type="transform")
                if cont:
                    if cont[0] not in self._controllers:
                        self._controllers.append(cont[0])
                        LOG.info("Added controller: {0}".format(cont[0]))

    def print_controllers(self):
        """Print controllers."""
        for controller in self._controllers:
            LOG.info(controller)

    def get_attribute_items(self):
        """Create and return attribute items."""
        attribute_items = []
        for controller in self._controllers:
            for attr in cmds.listAttr(controller, keyable=True):
                if cmds.getAttr("{0}.{1}".format(controller, attr), settable=True):
                    attribute_items.append(AttributeItem(controller, attr, cmds.getAttr("{0}.{1}".format(controller, attr))))
        return attribute_items


class FaceRomGenerator(object):
    def __init__(self):
        self._controllers = []
        self.morph_hook = "morph_hook"
        self._animation_duration = animation_duration

        self._attribute_items = []

    def collect_controllers(self):
        all_morphs = cmds.listAttr(self.morph_hook, userDefined=True)
        controllers = []
        for morph_attr in all_morphs:
            remap_node = cmds.listConnections("{0}.{1}".format(self.morph_hook, morph_attr), source=True, destination=False,
                                              type="remapValue")
            if remap_node:
                cont = cmds.listConnections("{0}.inputValue".format(remap_node[0]), source=True, destination=False,
                                            type="transform")
                if cont:
                    controllers.append(cont[0])

        return list(set(controllers))

    def collect_attributes(self):
        for controller in self._controllers:
            for attr in cmds.listAttr(controller, keyable=True):
                if cmds.getAttr("{0}.{1}".format(controller, attr), settable=True):
                    self._attribute_dictionary[controller][attr] = cmds.getAttr("{0}.{1}".format(controller, attr))

class AttributeItem(object):
    """Attribute item class."""
    default_translate_limits = [-100, 100]
    default_rotate_limits = [-90, 90]
    default_scale_limits = [0.5, 2]
    default_custom_limits = [-100, 100]
    default_limits = {
        "translateX": default_translate_limits,
        "translateY": default_translate_limits,
        "translateZ": default_translate_limits,
        "rotateX": default_rotate_limits,
        "rotateY": default_rotate_limits,
        "rotateZ": default_rotate_limits,
        "scaleX": default_scale_limits,
        "scaleY": default_scale_limits,
        "scaleZ": default_scale_limits,
        "tx": default_translate_limits,
        "ty": default_translate_limits,
        "tz": default_translate_limits,
        "rx": default_rotate_limits,
        "ry": default_rotate_limits,
        "rz": default_rotate_limits,
        "sx": default_scale_limits,
        "sy": default_scale_limits,
        "sz": default_scale_limits,
    }
    translate = ["translateX", "translateY", "translateZ", "tx", "ty", "tz"]
    rotate = ["rotateX", "rotateY", "rotateZ", "rx", "ry", "rz"]
    rotate = ["scaleX", "scaleY", "scaleZ", "sx", "sy", "sz"]
    def __init__(self, controller, attribute, value):
        self.default_translate_limits = [-100, 100]
        self.default_rotate_limits = [-90, 90]
        self.default_scale_limits = [0.5, 2]
        self.default_custom_limits = [-100, 100]

        self.controller = controller
        self.attribute = attribute
        self.attribute_path = "{0}.{1}".format(controller, attribute)
        if not cmds.listAttr(self.attribute_path, scalar=True):
            msg = "Only Scalar attributes are supported. {} is not a scalar attribute".format(self.attribute_path)
            LOG.error(msg)
            raise Exception(msg)

        self.value = value
        if cmds.listAttr("{0}.{1}".format(controller, attribute), userDefined=True):
            self.user_defined = True
        else:
            self.user_defined = False
        self._limits = self.get_limits()
        self._override_limits = []

    @property
    def limits(self):
        """Get limits."""
        return self._limits

    @property
    def override_limits(self):
        """Get override limits."""
        return self._override_limits

    @override_limits.setter
    def override_limits(self, value):
        """Set override limits."""
        if not isinstance(value, list):
            raise TypeError("Override limits must be a list")
        if len(value) != 2:
            raise ValueError("Override limits must have two values")
        self._override_limits = value

    def get_limits(self):
        """query the limits of the attribute FROM SCENE.
        If there are no limits, use the default limits defined
        """
        print("getting limits for {}".format(self.attribute_path))
        _state, _limits = attribute.query_limits(self.controller, self.attribute, only_hard_limits=False)
        if all(_state):
            return _limits
        # if one of the min or max values are not set, use the default for that one
        for idx, s in enumerate(_state):
            if s:
                continue
            if self.user_defined:
                _limits[idx] = self.default_custom_limits[idx]
            else:
                _limits[idx] = self.default_limits[self.attribute][idx]
        return _limits




