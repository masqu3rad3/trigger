"""Create a random animation."""

import random
from maya import cmds
import logging

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
    def __init__(self, controller, attribute, value):
        self.controller = controller
        self.attribute = attribute
        self.value = value
        self.limits = [0, 0]