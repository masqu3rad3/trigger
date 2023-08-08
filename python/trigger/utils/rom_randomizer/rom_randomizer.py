"""Create a random animation.

Sample usage:

from importlib import reload
from trigger.utils.rom_randomizer import rom_randomizer

collector = rom_randomizer.Collector()
collector.add_morph_controllers("morph_hook")
collector.excluded_attributes = ["activate", "lZip", "rZip", "stickyness", "rampEdges", "rampCenter"]


rom = rom_randomizer.FaceRomGenerator(collector)

# rom.random_pose(seed=1234)

# rom.generate_random_poses_rom(start_frame=1, duration=1000, interval=5, seed=None)
# rom.clear_keys()
rom.generate_random_combo_rom(start_frame=1, duration=100, minimum_combinations=1, maximum_combinations=5, interval=5, seed=None)

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

    def get_attribute_items(self, symmetry=False):
        """Create and return attribute items.

        Args:
            symmetry (bool): If True, will pair the Left and Right controllers
                            where available and create a symmetric attribute item.
        """
        controller_pairs = {}
        if symmetry:
            LOG.info("Symmetry is enabled")
            for controller in self._controllers:
                if controller.startswith("L_"):
                    pair = controller.replace("L_", "R_")
                    if cmds.objExists(pair):
                        controller_pairs[controller] = pair
            # remove right controllers from the list
            self._controllers = [x for x in self._controllers if not x in controller_pairs.values()]

        for controller in self._controllers:
            for attr in cmds.listAttr(controller, keyable=True):
                if attr in self._excluded_attributes:
                    continue
                if cmds.getAttr("{0}.{1}".format(controller, attr), settable=True):
                    symmetry_pair = controller_pairs.get(controller, None)
                    yield AttributeItem(
                        controller,
                        attr,
                        cmds.getAttr("{0}.{1}".format(controller, attr)),
                        symmetry_controller=symmetry_pair
                    )
                    # attribute_items.append(AttributeItem(controller, attr, cmds.getAttr("{0}.{1}".format(controller, attr))))
        # return attribute_items


class FaceRomGenerator(object):
    def __init__(self, collector_object, symmetry=False):
        self.collectors = [collector_object]
        self._animation_duration = animation_duration
        self._symmetry = symmetry

    @property
    def symmetry(self):
        """Return symmetry."""
        return self._symmetry

    @symmetry.setter
    def symmetry(self, value):
        """Set symmetry."""
        if not isinstance(value, bool):
            raise ValueError("symmetry must be a bool")
        self._symmetry = value

    def add_collector(self, collector_object):
        """Add collector."""
        self.collectors.append(collector_object)

    def clear_keys(self):
        """Clear all keys on all defined controllers."""
        for collector in self.collectors:
            attribute_items = collector.get_attribute_items(symmetry=self.symmetry)
            for attribute_item in attribute_items:
                attribute_item.clear_keys()

    def random_pose(self, seed=None):
        """Generate a random pose using all controllers in collectors."""
        random.seed(seed)
        for collector in self.collectors:
            attribute_items = collector.get_attribute_items(symmetry=self.symmetry)
            for attribute_item in attribute_items:
                attribute_item.set_random_value(seed=seed)

    def random_key(self, at_time, seed=None):
        random.seed(seed)
        for collector in self.collectors:
            attribute_items = collector.get_attribute_items(symmetry=self.symmetry)
            for attribute_item in attribute_items:
                attribute_item.key_random_value(at_time=at_time)

    def default_key(self, at_time):
        for collector in self.collectors:
            attribute_items = collector.get_attribute_items(symmetry=self.symmetry)
            for attribute_item in attribute_items:
                attribute_item.key_default(at_time=at_time)

    def _get_all_attributes(self):
        """Return all attributes."""
        all_attributes = []
        for collector in self.collectors:
            attribute_items = list(collector.get_attribute_items(symmetry=self.symmetry))
            for attribute_item in attribute_items:
                all_attributes.append(attribute_item)
        return all_attributes

    def generate_random_poses_rom(self, start_frame=1, duration=100, interval=5, seed=None):
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
            self.random_key(start_frame, seed=seed + start_frame)
            start_frame += interval
            duration -= interval

    def generate_random_combo_rom(self,
                                  start_frame=1,
                                  duration=100,
                                  minimum_combinations=1,
                                  maximum_combinations=5,
                                  interval=5,
                                  seed=None
                                  ):
        """Create a random rom using the combinations of n number of controllers."""
        all_attributes = self._get_all_attributes()
        seed = seed or int(time.time())
        # set an initial keyframe at start_frame
        self.default_key(start_frame)
        start_frame += interval
        while duration > start_frame:
            # random.seed(seed + start_frame)
            # generate a random number of combinations
            number_of_combinations = random.randint(
                minimum_combinations, maximum_combinations,
            )
            # pick the attributes to use randomly from the all_attributes list
            random.seed(seed + start_frame)
            random_attributes = random.sample(all_attributes, number_of_combinations)
            # attribute_start = int(start_frame)
            end_frame = start_frame
            end_frames = []
            for attribute_item in random_attributes:
                end_frames.append(attribute_item.key_min_to_max(start_frame, interval))
            start_frame = max(end_frames)

class AttributeItem(object):
    """Attribute item class."""

    default_translate_limits = [-5, 5]
    default_rotate_limits = [-15, 15]
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

    def __init__(self, controller, attribute, value, symmetry_controller=None):
        self.default_translate_limits = [-100, 100]
        self.default_rotate_limits = [-90, 90]
        self.default_scale_limits = [1.5, 2]
        self.default_custom_limits = [-100, 100]
        self.symmetry_controller = symmetry_controller
        self.controller = controller
        self.attribute = attribute
        self.attribute_path = "{0}.{1}".format(controller, attribute)
        if symmetry_controller:
            self.symmetry_attribute_path = "{0}.{1}".format(
                symmetry_controller, attribute
            )
        else:
            self.symmetry_attribute_path = None
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
        if self.symmetry_attribute_path:
            cmds.setAttr(self.symmetry_attribute_path, _value)

    def key_random_value(self, at_time, seed=None, in_tangent_type="linear", out_tangent_type="linear"):
        random.seed(seed)
        _limits = self.limits or self.override_limits
        _value = random.uniform(_limits[0], _limits[1])
        cmds.setKeyframe(self.controller, attribute=self.attribute, time=at_time, value=_value,
                         inTangentType=in_tangent_type, outTangentType=out_tangent_type)
        if self.symmetry_controller:
            cmds.setKeyframe(self.symmetry_controller, attribute=self.attribute, time=at_time, value=_value,
                             inTangentType=in_tangent_type, outTangentType=out_tangent_type)

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
        if self.symmetry_attribute_path:
            cmds.setAttr(self.symmetry_attribute_path, default_value)

    def key_default(self, at_time, in_tangent_type="linear", out_tangent_type="linear"):
        """Set the default for the attribute."""
        default_value = self._get_default_value()
        cmds.setKeyframe(self.controller, attribute=self.attribute, time=at_time, value=default_value,
                         inTangentType=in_tangent_type, outTangentType=out_tangent_type)
        if self.symmetry_controller:
            cmds.setKeyframe(self.symmetry_controller, attribute=self.attribute, time=at_time, value=default_value,
                             inTangentType=in_tangent_type, outTangentType=out_tangent_type)

    def clear_keys(self):
        """Clear all keys on the attribute."""
        cmds.cutKey(self.controller, attribute=self.attribute, clear=True)
        if self.symmetry_controller:
            cmds.cutKey(self.symmetry_controller, attribute=self.attribute, clear=True)
        self.set_default()

    def key_min_to_max(self, start_frame, interval_value):
        """Make a ROM animation between the limits of the attribute.

        Args:
            start_frame (int): start frame of the animation
            interval_value (int): interval between keys

        Returns:
            int: end frame of the animation
        """
        # put a key at the start frame
        end_frame = start_frame
        cmds.setKeyframe(self.controller, attribute=self.attribute, time=start_frame)
        # check the existing value of the attribute. If it is same a the minimum or maximum limit,
        # use only the different one
        original_value = cmds.getAttr(self.attribute_path)
        marker = start_frame
        key_dict = {start_frame: original_value}
        if not original_value == self.limits[0]:
            marker += interval_value
            key_dict[marker] = self.limits[0]
        if not original_value == self.limits[1]:
            if original_value == self.limits[0]:
                marker += interval_value
            else:
                marker += interval_value * 2
            key_dict[marker] = self.limits[1]
        end_frame = marker + interval_value
        key_dict[end_frame] = original_value

        for frame, value in key_dict.items():
            cmds.setKeyframe(self.controller, attribute=self.attribute, time=frame, value=value)
            if self.symmetry_controller:
                cmds.setKeyframe(self.symmetry_controller, attribute=self.attribute, time=frame, value=value)
        return end_frame