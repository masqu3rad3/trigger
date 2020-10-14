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

# class Script(object):
#     def __init__(self):
#         super(Script, self).__init__()
#         self.filePath = None
#         self.moduleName = None
#         self.asName = None
#         self.commands = []
#
#     def dynamic_import(self, moduleName, as_name=None):
#         import_name = as_name if as_name else moduleName
#         exec("global %s" % import_name, globals())
#         cmd = "import {0} as {1}".format(moduleName, import_name)
#         exec(cmd, globals())
#
#     def feed(self, action_data):
#         self.filePath = action_data.get("script_file_path")
#         self.asName = action_data.get("import_as")
#         self.commands = action_data.get("commands")
#
#     def action(self):
#         directory, full_name = os.path.split(self.filePath)
#         self.moduleName = os.path.splitext(full_name)[0]
#
#         sys.path.insert(0, directory)
#         self.dynamic_import(self.moduleName, as_name=self.asName)
#         sys.path.pop(0)
# #
#
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

        try:
            isAsChanged = self.importAs.__name__
        except:
            isAsChanged = ""

        if module_name not in sys.modules or isAsChanged != module_name:
            import_name = self.importAs if self.importAs else module_name
            print("*"*30)
            print("import_name:", import_name)
            print("module_name:", module_name)
            print("*"*30)
            exec("global %s" % import_name, globals())
            cmd = "import {0} as {1}".format(module_name, import_name)
            exec(cmd, globals())
        else:
            reload_name = module_name if not self.importAs else self.importAs
            if sys.version_info.major > 2:
                FEEDBACK.warning("RELOADING PYTHON 3 => %s" % reload_name)
                cmd_reload = "importlib.reload({0})".format(reload_name)
            else:
                FEEDBACK.warning("RELOADING PYTHON 2 => %s" % reload_name)
                cmd_reload = "reload({0})".format(reload_name)
            exec(cmd_reload, globals())

        sys.path.pop(0)

        ## run the commands
        for command in self.commands:
            exec(command)
#
#     # @staticmethod
#     def dynamic_import(self, moduleName, as_name=None):
#         # sys.path.insert(0, path)
#         import_name = as_name if as_name else moduleName
#         exec("global %s" % import_name, globals())
#         cmd = "import {0} as {1}".format(moduleName, import_name)
#         exec(cmd, globals())
#         # sys.path.pop(0)
#

