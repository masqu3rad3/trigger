"""This module is for saving / loading custom scripts"""

import os
from maya import cmds

from trigger.core import feedback
from trigger.core import dynamic_import as dyn

FEEDBACK = feedback.Feedback(__name__)

ACTION_DATA = {
    "script_file_path": "",
    "import_as": "",
    "commands": [],
}

class Script(object):
    def __init__(self):
        super(Script, self).__init__()
        self.filePath = None
        self.importAs = None
        self.commands = []

    def feed(self, action_data):
        self.filePath = action_data.get("script_file_path")
        self.importAs = action_data.get("import_as")
        self.commands = action_data.get("commands")

    def action(self):
        # workaround for stupid windows paths to work in nested strings
        self.filePath = self.filePath.replace("\\", "\\\\")

        # if import as not defined, use file name instead
        if not self.importAs:
            self.importAs = os.path.splitext(os.path.basename(self.filePath))[0]
        exec("%s=dyn.dynamic_import('%s')" %(self.importAs, self.filePath))

        ## run the commands
        for command in self.commands:
            exec(command)



