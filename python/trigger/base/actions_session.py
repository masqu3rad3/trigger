import os
from copy import deepcopy

from maya import cmds

from trigger.core import io
from trigger.core import filelog
from trigger.library import scene
from trigger import actions
from trigger.core.decorators import tracktime, windowsOff
from trigger.core import compatibility as compat
from trigger.ui.Qt import QtWidgets

LOG = filelog.Filelog(logname=__name__, filename="trigger_log")


class ActionsSession(dict):
    def __init__(self, progress_listwidget=None, *args, **kwargs):
        super(ActionsSession, self).__init__(*args, **kwargs)
        self.progressListwidget = progress_listwidget
        # at least a file name is necessary while instancing the IO
        self.io = io.IO(file_name="tmp_actions_session.tr")
        self.currentFile = None
        self.action_data_dict =  {module_name: class_obj.action_data for module_name, class_obj in actions.class_data.items()}

        # self.action_data_dict = {}
        # for mod in actions.__all__:
        #     self.action_data_dict[mod] = eval("actions.{0}.ACTION_DATA".format(mod))

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
        LOG.header("New Session")
        self.__init__()

    def save_session(self, file_path):
        """Saves the session to the given file path"""
        if not os.path.splitext(file_path)[1] == ".tr":
            file_path = "%s.tr" % file_path
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
            LOG.header("New Session")
            LOG.info("Action Session Loaded Successfully...")
        else:
            LOG.error("Cannot Open. File doesn't exist or unreadable => %s" % file_path)
            raise Exception

    def import_session(self, file_path, insert_index=None):
        """Imports the session from the file"""
        self.io.file_path = file_path
        actions_data = self.io.read()
        imported_actions = actions_data["actions"]
        ## Make sure new action names are not clashing
        for act in imported_actions:
            action_name = act["name"]
            idcounter = 0
            while action_name in self.list_action_names():
                action_name = "%s%s" % (action_name, str(idcounter + 1))
                idcounter = idcounter + 1
            act["name"] = action_name

        if insert_index == None:
            self["actions"].extend(imported_actions)
        else:
            # slice it
            self["actions"][insert_index:insert_index] = imported_actions

    def is_modified(self):
        """Checks if the current file is different than the saved file"""
        if self.compareActions == self["actions"]:
            return False
        else:
            return True

    def list_valid_actions(self):
        """Returns all available actions"""
        return sorted(self.action_data_dict.keys())

    def reset_actions(self):
        self["actions"] = []
        self.compareActions = deepcopy(self["actions"])

    def add_action(self, action_name=None, action_type=None, insert_index=None):
        """
        Adds an action to the session database
        Args:
            action_name: (String) Nice name for the action
            action_type: (String) Type of the action. Must be one of the valid types

        Returns:

        """
        if not action_name:
            action_name = action_type + "1"
            idcounter = 0
            while action_name in self.list_action_names():
                action_name = "%s%s" % (action_type, str(idcounter + 1))
                idcounter = idcounter + 1

        if action_name in self.list_action_names():
            LOG.error("Action Name already exists in the Session")
        if not action_type in self.list_valid_actions():
            LOG.error("Defined Action type is not valid")
        action = {
            "name": action_name,
            "type": action_type,
            "data": deepcopy(self.action_data_dict.get(action_type)),
            "enabled": True,
        }
        if insert_index == None:
            self["actions"].append(action)
        else:
            self["actions"].insert(insert_index, action)

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
            LOG.error("Action name %s already exists" % new_name)
        action = self.get_action(action_name)
        action["name"] = new_name

    def get_action_type(self, action_name):
        action = self.get_action(action_name)
        return action["type"]

    def duplicate_action(self, action_name):
        """Duplicates the given action"""
        action = self.get_action(action_name)
        if not action:
            LOG.warning("%s is not in the list of actions" % action_name)
            return
        id = self["actions"].index(action)
        dup_action = deepcopy(action)
        idcounter = 0
        action_name = dup_action["name"] + "1"
        while action_name in self.list_action_names():
            action_name = "%s%s" % (dup_action["name"], str(idcounter + 1))
            idcounter = idcounter + 1

        dup_action["name"] = action_name
        self["actions"].insert(id + 1, dup_action)

    def delete_action(self, action_name):
        """Deletes the action by name from the dictionary"""
        action = self.get_action(action_name)
        if action:
            self["actions"].remove(action)
        else:
            LOG.warning("%s is not in the list of actions" % action_name)

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
            defaults = self.action_data_dict[action["type"]]
            current_value = action["data"].get(property, defaults.get(property))
            if current_value == None:
                msg = "The property '%s' does not exist in %s ACTION_DATA" % (
                    property,
                    action["type"],
                )
                LOG.error(msg)
                raise Exception(msg)
            if compat.is_string(new_value):
                new_value = str(new_value)
            if compat.is_string(current_value):
                current_value = str(current_value)
            if type(current_value) != type(new_value):
                msg = "%s property only accepts %s values" % (
                    property,
                    str(type(current_value)),
                )
                LOG.error(msg)
                raise Exception(msg)

            action["data"][property] = new_value
            # log.info("%s @ %s => %s" % (property, action["name"], new_value))
            return True
        else:
            LOG.warning("%s cannot be found in the action list")
            return False

    def query_action(self, action_name, property):
        action = self.get_action(action_name)
        if action:
            defaults = self.action_data_dict[action["type"]]
            current_value = action["data"].get(property, defaults.get(property))
            if current_value == None:
                LOG.error(
                    "The property '%s' does not exist in %s ACTION_DATA"
                    % (property, action["type"])
                )
            else:
                return current_value
        else:
            LOG.warning("%s cannot be found in the action list")
            return None

    def enable_action(self, action_name):
        action = self.get_action(action_name)
        action["enabled"] = True

    def disable_action(self, action_name):
        action = self.get_action(action_name)
        action["enabled"] = False

    def is_enabled(self, action_name):
        action = self.get_action(action_name)
        try:
            return action["enabled"]
        except KeyError:  ## this is for backward compatibility
            return True

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
            self["actions"].insert(index - 1, self["actions"].pop(index))

    def move_down(self, action_name):
        """Moves the action one index down"""
        action = self.get_action(action_name)
        index = self["actions"].index(action)
        if not index == len(self["actions"]):
            self["actions"].insert(index + 1, self["actions"].pop(index))

    def move(self, action_name, new_index):
        """Moves the action to the given index nmb"""
        action = self.get_action(action_name)
        old_index = self["actions"].index(action)
        if old_index != new_index:
            self["actions"].insert(new_index, self["actions"].pop(old_index))

    def get_info(self, action_name):
        action = self.get_action(action_name)
        action_cmd = "actions.{0}.{1}()".format(
            action["type"], action["type"].capitalize()
        )
        a_hand = eval(action_cmd)
        # backward compatibility for v2.0.0
        try:
            return a_hand.info()
        except AttributeError:
            return ""

    @tracktime
    def _action(self, action):
        LOG.header("%s" % action["name"])

        # action_cmd = "actions.{0}.{1}()".format(
        #     action["type"], action["type"].capitalize()
        # )
        # a_hand = eval(action_cmd)

        a_hand = actions.class_data[action["type"]]()

        a_hand.feed(action["data"])
        a_hand.action()
        LOG.info("success...")

    @windowsOff
    @tracktime
    def run_all_actions(self, reset_scene=True, until=None):
        """runs all actions in the actions list"""
        # reset scene
        LOG.seperator()
        LOG.header("BUILDING...")
        if reset_scene:
            scene.reset()
        for row, action in enumerate(self["actions"]):
            if action["name"] == until:
                return
            if self.is_enabled(action["name"]):
                if self.progressListwidget:
                    self.progressListwidget.setCurrentRow(-1)
                    self.progressListwidget.activateItem(row)

                    self.progressListwidget.scrollToItem(
                        self.progressListwidget.item(row),
                        QtWidgets.QAbstractItemView.EnsureVisible,
                    )
                    QtWidgets.QApplication.processEvents()
                try:
                    self._action(action)
                    if self.progressListwidget:
                        self.progressListwidget.successItem(row)
                except Exception as e:
                    if self.progressListwidget:
                        self.progressListwidget.errorItem(row)
                    LOG.error("Cannot complete action => %s\n%s" % (action["name"], e))
                    raise
        LOG.header("Total BUILDING TIME:")

    # @windowsOff
    def run_action(self, action_name):
        LOG.info("Running action => %s" % action_name)
        action = self.get_action(action_name)
        try:
            self._action(action)
            if self.progressListwidget:
                self.progressListwidget.successItem(
                    self.progressListwidget.currentRow()
                )
        except Exception as e:
            if self.progressListwidget:
                self.progressListwidget.errorItem(self.progressListwidget.currentRow())
            LOG.error("Cannot complete action => %s\n%s" % (action["name"], e))
            raise

    @tracktime
    def run_save_action(self, action_name):
        LOG.info("saving Action Data")
        action = self.get_action(action_name)


        # action_cmd = "actions.{0}.{1}()".format(
        #     action["type"], action["type"].capitalize()
        # )
        # a_hand = eval(action_cmd)

        a_hand = actions.class_data[action["type"]]()
        a_hand.feed(action["data"])
        a_hand.save_action()
        LOG.info("success")
        return True

    def get_layout_ui(self, action_name, ctrl, layout):
        action = self.get_action(action_name)
        # action_cmd = "actions.{0}.{1}()".format(
        #     action["type"], action["type"].capitalize()
        # )
        # a_hand = eval(action_cmd)

        a_hand = actions.class_data[action["type"]]()
        a_hand.ui(ctrl, layout, self)
