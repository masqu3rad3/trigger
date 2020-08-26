import os

from maya import cmds
import maya.api.OpenMaya as om
from trigger.library import functions as extra

from trigger.core import io
from trigger.core import feedback
from trigger import actions

FEEDBACK = feedback.Feedback(logger_name=__name__)

class ActionsSession(dict):
    def __init__(self):
        super(ActionsSession, self).__init__()

        # at least a file name is necessary while instancing the IO
        self.io = io.IO(file_name="tmp_actions_session.json")
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

    def save_session(self, file_path):
        """Saves the session to the given file path"""

        self.io.file_path = file_path
        self.io.write(self)
        FEEDBACK.info("Session Saved Successfully...")

    def load_session(self, file_path, reset_scene=True):
        """Loads the session from the file"""

        if reset_scene:
            cmds.file(new=True, force=True)
        self.io.file_path = file_path
        actions_data = self.io.read()
        if actions_data:
            self.clear()
            self.update(actions_data)
            FEEDBACK.info("Action Session Loaded Successfully...")
        else:
            FEEDBACK.throw_error("The specified file doesn't exists")

    def get_valid_actions(self):
        return sorted(self.action_data_dict.keys())

    def add_action(self, action_name, action_type):
        """
        Adds an action to the session database
        Args:
            action_name: (String) Nice name for the action
            action_type: (String) Type of the action. Must be one of the valid types

        Returns:

        """
        if not action_name:
            FEEDBACK.throw_error("Action Name cannot is empty or contains illegal chars")
        if action_name in self.get_action_names():
            FEEDBACK.throw_error("Action Name already exists in the Session")
        if not action_type in self.get_valid_actions():
            FEEDBACK.throw_error("Defined Action type is not valid")
        # action_item = eval("actions.%s.%s()" % (action_name, action_name.capitalize()))
        action = {
            "name": action_name,
            "type": action_type,
            "data": self.action_data_dict.get(action_type)
        }
        self["actions"].append(action)
        pass

    def delete_action(self, action_name):
        for action in self["actions"]:
            if action["name"] == action_name:
                self["actions"].remove(action)
                return
        else:
            FEEDBACK.warning("%s cannot be found in the action list")

    def edit_action(self, action_name, property):
        pass

    def get_actions(self):
        return self["actions"]

    def get_action_names(self):
        return [action["name"] for action in self["actions"]]

    def move_up(self, action):
        pass

    def move_down(self, action):
        pass



