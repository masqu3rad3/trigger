"""Create a random animation.

Sample usage:

from importlib import reload
from trigger.utils import rom_generator
reload(rom_generator)
from trigger.library import attribute
reload(attribute)

collector = rom_generator.Collector()
collector.add_morph_controllers("morph_hook")
collector.excluded_attributes = ["activate", "lZip", "rZip", "stickyness", "rampEdges", "rampCenter"]


rom = rom_generator.FaceRomGenerator(collector)

# rom.random_pose(seed=1234)

rom.generate_random_rom(start_frame=1, duration=1000, interval=5, seed=None)
# rom.clear_keys()


"""



import random
from maya import cmds
import logging
import time

from trigger.library import attribute

LOG = logging.getLogger(__name__)

animation_duration = 5000  # as frames


class Collector(object):
    """Collects controllers and attributes."""

    def __init__(self):
        self._controllers = []
        self._excluded_attributes = []

    @property
    def controllers(self):
        """Return controllers."""
        return self._controllers

    @property
    def excluded_attributes(self):
        """Return excluded attributes."""
        return self._excluded_attributes

    @excluded_attributes.setter
    def excluded_attributes(self, value):
        """Set excluded attributes."""
        if not isinstance(value, list):
            raise ValueError("excluded_attributes must be a list")
        self._excluded_attributes = value

    def add_controller(self, controller):
        """Add controller."""
        if controller not in self._controllers:
            self._controllers.append(controller)

    def remove_controller(self, controller):
        """Remove controller."""
        if controller in self._controllers:
            self._controllers.remove(controller)

    def clear(self):
        """Clear controllers."""
        self._controllers = []

    def add_morph_controllers(self, morph_hook):
        """Get morph controllers."""
        all_morphs = cmds.listAttr(morph_hook, userDefined=True)
        for morph_attr in all_morphs:
            remap_node = cmds.listConnections(
                "{0}.{1}".format(morph_hook, morph_attr),
                source=True,
                destination=False,
                type="remapValue",
            )
            if remap_node:
                cont = cmds.listConnections(
                    "{0}.inputValue".format(remap_node[0]),
                    source=True,
                    destination=False,
                    type="transform",
                )
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
        # attribute_items = []
        for controller in self._controllers:
            for attr in cmds.listAttr(controller, keyable=True):
                if attr in self._excluded_attributes:
                    continue
                if cmds.getAttr("{0}.{1}".format(controller, attr), settable=True):
                    yield AttributeItem(
                        controller,
                        attr,
                        cmds.getAttr("{0}.{1}".format(controller, attr)),
                    )
                    # attribute_items.append(AttributeItem(controller, attr, cmds.getAttr("{0}.{1}".format(controller, attr))))
        # return attribute_items


class FaceRomGenerator(object):
    def __init__(self, collector_object):
        self.collectors = [collector_object]
        self._animation_duration = animation_duration

    def add_collector(self, collector_object):
        """Add collector."""
        self.collectors.append(collector_object)

    def clear_keys(self):
        """Clear all keys on all defined controllers."""
        for collector in self.collectors:
            attribute_items = collector.get_attribute_items()
            for attribute_item in attribute_items:
                attribute_item.clear_keys()

    def random_pose(self, seed=None):
        """Generate a random pose using all controllers in collectors."""
        random.seed(seed)
        for collector in self.collectors:
            attribute_items = collector.get_attribute_items()
            for attribute_item in attribute_items:
                attribute_item.set_random_value(seed=seed)

    def random_key(self, at_time, seed=None):
        random.seed(seed)
        for collector in self.collectors:
            attribute_items = collector.get_attribute_items()
            for attribute_item in attribute_items:
                attribute_item.key_random_value(at_time=at_time)

    def default_key(self, at_time):
        for collector in self.collectors:
            attribute_items = collector.get_attribute_items()
            for attribute_item in attribute_items:
                attribute_item.key_default(at_time=at_time)

    def generate_random_rom(self, start_frame=1, duration=100, interval=5, seed=None):
        """
        Generate a random rom.
        Args:
            duration (int): Duration of the animation in frames.
            interval (int): Interval between keyframes in frames.
            seed (int): Seed for randomization. None will use system time.

        Returns:

        """
        seed = seed or int(time.time())
        # set an initial keyframe at start_frame
        self.default_key(start_frame)
        start_frame += interval
        while duration > 0:
            self.random_key(start_frame, seed=seed+start_frame)
            start_frame += interval
            duration -= interval




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

    def __init__(self, controller, attribute, value):
        self.default_translate_limits = [-100, 100]
        self.default_rotate_limits = [-90, 90]
        self.default_scale_limits = [1.5, 2]
        self.default_custom_limits = [-100, 100]

        self.controller = controller
        self.attribute = attribute
        self.attribute_path = "{0}.{1}".format(controller, attribute)
        if not cmds.listAttr(self.attribute_path, scalar=True):
            msg = "Only Scalar attributes are supported. {} is not a scalar attribute".format(
                self.attribute_path
            )
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
        _state, _limits = attribute.query_limits(
            self.controller, self.attribute, only_hard_limits=False
        )
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

    def set_random_value(self, seed=None):
        """Set a random value within the resolved or overriden limits."""
        random.seed(seed)
        _limits = self.limits or self.override_limits
        _value = random.uniform(_limits[0], _limits[1])
        cmds.setAttr(self.attribute_path, _value)

    def key_random_value(self, at_time, seed=None, in_tangent_type="linear", out_tangent_type="linear"):
        random.seed(seed)
        _limits = self.limits or self.override_limits
        _value = random.uniform(_limits[0], _limits[1])
        cmds.setKeyframe(self.controller, attribute=self.attribute, time=at_time, value=_value, inTangentType=in_tangent_type, outTangentType=out_tangent_type)

    def _get_default_value(self):
        """Intermediary method to get the default value of the attribute."""
        if self.user_defined:
            default_value = cmds.addAttr(self.attribute_path, query=True, defaultValue=True)
        else:
            # try to get it from the custom trigger attributes.
            default_attr = "default{0}".format(self.attribute)
            if cmds.attributeQuery(default_attr, node=self.controller, exists=True):
                default_value = cmds.getAttr("{0}.{1}".format(self.controller, default_attr))
            else:
                # get the average of default limits
                default_value = sum(self.default_limits[self.attribute]) * 0.5
        return default_value


    def set_default(self):
        """Set the default for the attribute."""
        default_value = self._get_default_value()
        cmds.setAttr(self.attribute_path, default_value)

    def key_default(self, at_time, in_tangent_type="linear", out_tangent_type="linear"):
        """Set the default for the attribute."""
        default_value = self._get_default_value()
        cmds.setKeyframe(self.controller, attribute=self.attribute, time=at_time, value=default_value, inTangentType=in_tangent_type, outTangentType=out_tangent_type)

    def clear_keys(self):
        """Clear all keys on the attribute."""
        cmds.cutKey(self.controller, attribute=self.attribute, clear=True)
        self.set_default()