"""This module is for saving / loading custom scripts"""

import os, sys
from maya import cmds
import platform

import importlib
# from trigger.core import io
from trigger.core import feedback
from trigger.library import functions as extra
from trigger.library import controllers as ic

FEEDBACK = feedback.Feedback(__name__)

ACTION_DATA = {
    "script_file_path": "",
    "import_as": "",
    "commands": [],
}

class Script(object):
    def __init__(self, file_path=None, import_as=None, commands=None):
        super(Script, self).__init__()

        self.file_path = file_path
        self.importAs = None if not import_as else import_as
        self.commands = [] if not commands else commands

    def feed(self, action_data):
        self.file_path = action_data.get("script_file_path")
        self.importAs = action_data.get("import_as")
        self.commands = action_data.get("commands")

    def action(self):
        # abort if no file path
        if not self.file_path:
            FEEDBACK.throw_error("No File Path defined")

        if not os.path.isfile(self.file_path):
            FEEDBACK.throw_error("The defined File does not exist")

        ## add the path to the system path
        directory, full_name = os.path.split(self.file_path)
        module_name = os.path.splitext(full_name)[0]
        sys.path.insert(0, directory)

        ## import the module
        if module_name not in sys.modules:
            importlib.import_module(module_name)
            cmd = "import %s as %s" %(module_name, self.importAs) if self.import_as else "import %s" %(module_name)
            exec(cmd)
        else:
            if sys.version_info.major > 2:
                importlib.reload(module_name)
            else:
                reload(module_name)

        # remove the added path
        sys.path.pop(0)
        pass

        ## run the commands
        for command in self.commands:
            exec(command)



