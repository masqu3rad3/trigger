"""This module is for saving / loading custom scripts"""

import os
from maya import cmds  # NEVER REMOVE THIS LINE!!!
import platform
import subprocess

from trigger.core import filelog
from trigger.core import dynamic_import as dyn  # NEVER REMOVE THIS LINE!!!

from trigger.ui.Qt import QtWidgets, QtGui  # for progressbar
from trigger.ui import custom_widgets
from trigger.ui.widgets.browser_button import BrowserButton

log = filelog.Filelog(logname=__name__, filename="trigger_log")


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
        if self.filePath:
            # workaround for stupid windows paths to work in nested strings
            self.filePath = self.filePath.replace("\\", "\\\\")

            # if import as not defined, use file name instead
            if not self.importAs:
                self.importAs = os.path.splitext(os.path.basename(self.filePath))[0]
            exec("%s=dyn.dynamic_import('%s')" %(self.importAs, self.filePath))

        ## run the commands
        log.warning(self.commands)
        for command in self.commands:
            if "\\n" in command:
                command = command.replace("\\n", "\n")
            log.info("Executing command: %s" %command)
            exec(command)

    def save_action(self):
        """Mandatory method for all action modules"""
        pass

    def ui(self, ctrl, layout, *args, **kwargs):

        file_path_lbl = QtWidgets.QLabel(text="File Path:")
        file_path_hLay = QtWidgets.QHBoxLayout()
        # file_path_le = QtWidgets.QLineEdit()
        file_path_le = custom_widgets.FileLineEdit()
        file_path_hLay.addWidget(file_path_le)
        edit_file_pb = QtWidgets.QPushButton(text="Edit")
        file_path_hLay.addWidget(edit_file_pb)
        browse_path_pb = BrowserButton(mode="openFile", update_widget=file_path_le, filterExtensions=["Python Files (*.py)"], overwrite_check=False)
        save_path_pb = BrowserButton(mode="saveFile", update_widget=file_path_le, filterExtensions=["Python Files (*.py)"], overwrite_check=False)
        file_path_hLay.addWidget(browse_path_pb)
        layout.addRow(file_path_lbl, file_path_hLay)

        import_as_lbl = QtWidgets.QLabel(text="Import as:")
        import_as_le = QtWidgets.QLineEdit()
        layout.addRow(import_as_lbl, import_as_le)

        commands_lbl = QtWidgets.QLabel(text="Commands")
        commands_le = QtWidgets.QLineEdit()
        layout.addRow(commands_lbl, commands_le)

        ctrl.connect(file_path_le, "script_file_path", str)
        ctrl.connect(import_as_le, "import_as", str)
        ctrl.connect(commands_le, "commands", list)
        ctrl.update_ui()

        def edit_file():
            file_path = file_path_le.text()
            if not file_path:
                result = save_path_pb.browserEvent()
                if result:
                    if not os.path.isfile(result):
                        f = open(result, "w+")
                        f.close()
                    file_path = result
                else:
                    return

            system = platform.system()
            if system == "Windows":
                os.startfile(file_path)
            elif system == "Linux":
                subprocess.Popen(["xdg-open", file_path])
                pass
            else:
                subprocess.Popen(["open", file_path])
                pass

        ### Signals
        file_path_le.textChanged.connect(lambda x=0: ctrl.update_model())
        import_as_le.textChanged.connect(lambda x=0: ctrl.update_model())
        edit_file_pb.clicked.connect(edit_file)
        browse_path_pb.clicked.connect(lambda x=0: ctrl.update_model())
        browse_path_pb.clicked.connect(file_path_le.validate)  # to validate on initial browse result
        save_path_pb.clicked.connect(lambda x=0: ctrl.update_model())
        commands_le.textEdited.connect(lambda x=0: ctrl.update_model())


