import os
from copy import deepcopy

from maya import cmds
# import maya.api.OpenMaya as om
# from trigger.library import functions as extra

from trigger.core import io
from trigger.core import logger
from trigger import actions
from trigger.core import compatibility as compat

LOG = logger.Logger(logger_name=__name__)

class ActionsSession(dict):
    def __init__(self):
        super(ActionsSession, self).__init__()

        # at least a file name is necessary while instancing the IO
        self.io = io.IO(file_name="tmp_actions_session.tr")
        self.currentFile = None
        self.action_data_dict = {}
        for mod in actions.__all__:
            self.action_data_dict[mod]=eval('actions.{0}.ACTION_DATA'.format(mod))

        """
        Structure:
        {
        actions:[
                    {
                    "name": "body_kinetics",
                    "type": "kinematics",
                    "data": {ACTION_DATA}
                    },
                    {
                    "name": "Weights_Main_Body",
                    "type": "weights",
                    "data": {ACTION_DATA}
                    },
                    {
                    "name": "Final_Cleanup",
                    "type": "cleanup",
                    "data": {ACTION_DATA}
                    }
                    {
                    "name": "Add_Extras",
                    "type": "python",
                    "data": {ACTION_DATA}
                    }       
                ]
        }
        """


        self["actions"] = []
        self.compareActions = deepcopy(self["actions"])

    def new_session(self):
        """Clears the data"""
        self.__init__()

    def save_session(self, file_path):
        """Saves the session to the given file path"""
        if not os.path.splitext(file_path)[1]:
            file_path = "%s.tr" %file_path
        self.io.file_path = file_path
        self.io.write(self)
        self.currentFile = file_path
        self.compareActions = deepcopy(self["actions"])
        LOG.info("Session Saved Successfully...")

    def load_session(self, file_path):
        """Loads the session from the file"""
        self.io.file_path = file_path
        actions_data = self.io.read()
        if actions_data:
            self.clear()
            self.update(actions_data)
            self.currentFile = file_path
            self.compareActions = deepcopy(self["actions"])
            LOG.info("Action Session Loaded Successfully...")
        else:
            LOG.throw_error("The specified file doesn't exists")

    def is_modified(self):
        """Checks if the current file is different than the saved file"""
        if self.compareActions == self["actions"]:
            return False
        else:
            return True
        # if not self.currentFile:
        #     if self["actions"]:
        #         return True
        #     else:
        #         return False
        # actions_data = self.io.read()
        # if actions_data != self:
        #     return True
        # else:
        #     return False

    def list_valid_actions(self):
        """Returns all available actions"""
        return sorted(self.action_data_dict.keys())

    def reset_actions(self):
        self["actions"] = []
        self.compareActions = deepcopy(self["actions"])

    def add_action(self, action_name=None, action_type=None):
        """
        Adds an action to the session database
        Args:
            action_name: (String) Nice name for the action
            action_type: (String) Type of the action. Must be one of the valid types

        Returns:

        """
        # if not action_name:
        #     FEEDBACK.throw_error("Action Name cannot is empty or contains illegal chars")
        if not action_name:
            action_name = action_type + "1"
            idcounter = 0
            while action_name in self.list_action_names():
                action_name = "%s%s" % (action_type, str(idcounter + 1))
                idcounter = idcounter + 1

        if action_name in self.list_action_names():
            LOG.throw_error("Action Name already exists in the Session")
        if not action_type in self.list_valid_actions():
            LOG.throw_error("Defined Action type is not valid")
        # action_item = eval("actions.%s.%s()" % (action_name, action_name.capitalize()))
        action = {
            "name": action_name,
            "type": action_type,
            "data": deepcopy(self.action_data_dict.get(action_type))
        }
        self["actions"].append(action)
        pass

    def get_action(self, action_name):
        """Returns the action dictionary item by name"""
        for action in self["actions"]:
            if action["name"] == action_name:
                return action
        return None

    def rename_action(self, action_name, new_name):
        if action_name == new_name:
            return
        if self.get_action(new_name):
            LOG.throw_error("Action name %s already exists" % new_name)
        action = self.get_action(action_name)
        action["name"] = new_name

    def get_action_type(self, action_name):
        action = self.get_action(action_name)
        return action["type"]

    def delete_action(self, action_name):
        """Deletes the action by name from the dictionary"""
        action = self.get_action(action_name)
        if action:
            self["actions"].remove(action)
        else:
            LOG.warning("%s cannot be found in the action list")

    def edit_action(self, action_name, property, new_value):
        """
        Edits the property values
        Args:
            action_name: (String) Action by name
            property: (String) Data Property
            new_value: (Multi) The new value. If its not match to the value data of the property, will throw error

        Returns: True if success, None or False if not

        """
        action = self.get_action(action_name)
        if action:
            current_value = action["data"].get(property)
            if current_value == None:
                LOG.throw_error("The property '%s' does not exist in %s ACTION_DATA" % (property, action["type"]))
            if compat.is_string(current_value):
                # new_value = compat.decode(new_value)
                new_value = str(new_value)
            if type(current_value) != type(new_value):
                LOG.throw_error("%s property only accepts %s values" % (property, str(type(current_value))))

            action["data"][property] = new_value
            LOG.info("%s @ %s => %s" % (property, action["name"], new_value))
            return True
        else:
            LOG.warning("%s cannot be found in the action list")
            return False

    def query_action(self, action_name, property):
        action = self.get_action(action_name)
        if action:
            current_value = action["data"].get(property)
            if current_value == None:
                LOG.throw_error("The property '%s' does not exist in %s ACTION_DATA" % (property, action["type"]))
            else:
                return current_value
        else:
            LOG.warning("%s cannot be found in the action list")
            return None

    def get_all_actions(self):
        """Returns all available actions"""
        return self["actions"]

    def list_action_names(self):
        """Returns all available action names"""
        return [action["name"] for action in self["actions"]]

    def move_up(self, action_name):
        """Moves the action one index up"""
        action = self.get_action(action_name)
        index = self["actions"].index(action)
        if not index == 0:
            self["actions"].insert(index-1, self["actions"].pop(index))
        LOG.info("%s index => %s" % (action_name, index - 1))

    def move_down(self, action_name):
        """Moves the action one index down"""
        action = self.get_action(action_name)
        index = self["actions"].index(action)
        if not index == len(self["actions"]):
            self["actions"].insert(index+1, self["actions"].pop(index))
        LOG.info("%s index => %s" % (action_name, index + 1))

    def move(self, action_name, new_index):
        """Moves the action to the given index nmb"""
        action = self.get_action(action_name)
        old_index = self["actions"].index(action)
        if old_index != new_index:
            self["actions"].insert(new_index, self["actions"].pop(old_index))
        LOG.info("%s index => %s" % (action_name, new_index))

    def run_all_actions(self):
        """runs all actions in the actions list"""
        # reset scene
        cmds.file(new=True, force=True)
        for action in self["actions"]:
            action_cmd = "actions.{0}.{1}()".format(action["type"], action["type"].capitalize())
            a_hand = eval(action_cmd)
            a_hand.feed(action["data"])
            a_hand.action()

    def run_action(self, action_name):
        action = self.get_action(action_name)
        action_cmd = "actions.{0}.{1}()".format(action["type"], action["type"].capitalize())
        a_hand = eval(action_cmd)
        a_hand.feed(action["data"])
        a_hand.action()

    def run_save_action(self, action_name):
        action = self.get_action(action_name)
        action_cmd = "actions.{0}.{1}()".format(action["type"], action["type"].capitalize())
        a_hand = eval(action_cmd)
        a_hand.feed(action["data"])
        a_hand.save_action()

    def get_layout_ui(self, action_name, ctrl, layout):
        action = self.get_action(action_name)
        action_cmd = "actions.{0}.{1}()".format(action["type"], action["type"].capitalize())
        a_hand = eval(action_cmd)
        a_hand.ui(ctrl, layout, self)

