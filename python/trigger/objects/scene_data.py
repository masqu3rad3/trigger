"""Generic module to hold, edit and query data to/from a Maya Node's attribute.

It inherits Python's dict class and overrides the __setitem__ and __getitem__ methods to
store and retrieve data from a Maya node's attribute.
"""

import ast
import logging

from maya import cmds

LOG = logging.getLogger(__name__)

# USE PYTHON3 VERSION (below) WHEN PY3 BECOMES AVAILABLE
class SceneDictionary(dict):
    """Python 2 version of SceneDictionary."""
    def __init__(self, node, attribute="sceneData"):
        """Initialize."""
        super(SceneDictionary, self).__init__()
        self.node = node
        self.attribute = attribute

    def __setitem__(self, key, value):
        """Set the data on the node."""
        if not self._check_node():
            LOG.error("Node %s doesn't exist", self.node)
            return False

        super(SceneDictionary, self).__setitem__(key, value)

        self.validate_attribute()
        cmds.setAttr("{}.{}".format(self.node, self.attribute), str(self), type="string")

    def __getitem__(self, key):
        """Retrieve the data from the scene node."""
        if not self._check_node():
            _data = None
        else:
            self.validate_attribute()
            _all_data = cmds.getAttr("{}.{}".format(self.node, self.attribute)) or "{}"
            _data = ast.literal_eval(_all_data).get(key, None)
        # first ingest the data to the dict
        if _data:
            super(SceneDictionary, self).__setitem__(key, _data)
        # now run the original function with the new data
        return super(SceneDictionary, self).__getitem__(key)

    def update(self, *args, **kwargs):
        """Update the dictionary."""
        for k, var in dict(*args, **kwargs).items():
            self[k] = var

    def get(self, key, default=None):
        """Get the value from the dictionary."""
        try:
            return self.__getitem__(key)
        except KeyError:
            return default

    def _check_node(self):
        """Check if the node exists."""
        if not cmds.objExists(self.node):
            return False
        return True

    def validate_attribute(self):
        """Create the attribute on the node."""
        if not cmds.attributeQuery(self.attribute, node=self.node, exists=True):
            cmds.addAttr(self.node, longName=self.attribute, dataType="string")


#
# import ast
# import logging
# from collections import UserDict
# from maya import cmds
#
# LOG = logging.getLogger(__name__)
#
# class SceneDictionary(UserDict):
#     def __init__(self, node, attribute="sceneData"):
#         super(SceneDictionary, self).__init__()
#         self.node = node
#         self.attribute = attribute
#
#     def __setitem__(self, key, value):
#         """Set the data on the node."""
#         if not self._check_node():
#             LOG.error("Node {} doesn't exist".format(self.node))
#             return False
#
#         super(SceneDictionary, self).__setitem__(key, value)
#
#         self.validate_attribute()
#         cmds.setAttr("{}.{}".format(self.node, self.attribute), str(self), type="string")
#
#     def __getitem__(self, key):
#         """Retrieve the data from the scene node."""
#         if not self._check_node():
#             _data = None
#         else:
#             self.validate_attribute()
#             _all_data = cmds.getAttr("{}.{}".format(self.node, self.attribute)) or "{}"
#             _data = ast.literal_eval(_all_data).get(key, None)
#         # first ingest the data to the dict
#         if _data:
#             super(SceneDictionary, self).__setitem__(key, _data)
#         # now run the original function with the new data
#         return super(SceneDictionary, self).__getitem__(key)\
#
#     def _check_node(self):
#         """Check if the node exists."""
#         if not cmds.objExists(self.node):
#             return False
#         return True
#
#     def validate_attribute(self):
#         """Create the attribute on the node."""
#         if not cmds.attributeQuery(self.attribute, node=self.node, exists=True):
#             cmds.addAttr(self.node, longName=self.attribute, dataType="string")
#
