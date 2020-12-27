"""Reference another Trigger session"""

import os
from trigger.core import filelog

# from trigger.base.actions_session import ActionsSession

import importlib
from trigger.ui.Qt import QtWidgets
from trigger.ui import custom_widgets

log = filelog.Filelog(logname=__name__, filename="trigger_log")


ACTION_DATA = {
    "trigger_file_path": ""
}

# Name of the class MUST be the capitalized version of file name. eg. morph.py => Morph, split_shapes.py => Split_shapes
class Reference_session(object):
    def __init__(self, *args, **kwargs):
        super(Reference_session, self).__init__()
        # user defined variables
        self.triggerFilePath = None

        # class variables

    def feed(self, action_data, *args, **kwargs):
        """Mandatory Method - Feeds the instance with the action data stored in actions session"""
        self.triggerFilePath = action_data.get("trigger_file_path")

    def action(self):
        """Mandatory Method - Execute Action"""
        # everything in this method will be executed automatically.
        # This method does not accept any arguments. all the user variable must be defined to the instance before
        if not self.triggerFilePath:
            log.warning("Reference Trigger Session path not defined. Skipping")
            return
        if not os.path.isfile(self.triggerFilePath):
            log.error("Trigger File does not exists => %s" % self.triggerFilePath)

        actions_session = importlib.import_module("trigger.base.actions_session")
        referenced_session = actions_session.ActionsSession()
        referenced_session.load_session(self.triggerFilePath)
        referenced_session.run_all_actions()


    def save_action(self):
        """Mandatory Method - Save Action"""
        # This method will be called automatically and accepts no arguments.
        # If the action has an option to save files, this method will be used by the UI.
        # Else, this method can stay empty
        pass

    def ui(self, ctrl, layout, handler, *args, **kwargs):
        """
        Mandatory Method - UI setting definitions

        Args:
            ctrl: (model_ctrl) ctrl object instance of /ui/model_ctrl. Updates UI and Model
            layout: (QLayout) The layout object from the main ui. All setting widgets should be added to this layout
            handler: (actions_session) An instance of the actions_session. TRY NOT TO USE HANDLER UNLESS ABSOLUTELY NECESSARY
            *args:
            **kwargs:

        Returns: None

        """

        trigger_file_path_lbl = QtWidgets.QLabel(text="Trigger Session:")
        trigger_file_path_hLay = QtWidgets.QHBoxLayout()
        # trigger_file_path_le = QtWidgets.QLineEdit()
        trigger_file_path_le = custom_widgets.FileLineEdit()
        trigger_file_path_hLay.addWidget(trigger_file_path_le)
        browse_path_pb = custom_widgets.BrowserButton(mode="openFile", update_widget=trigger_file_path_le, filterExtensions=["Trigger Session (*.tr)"], overwrite_check=False)
        trigger_file_path_hLay.addWidget(browse_path_pb)
        layout.addRow(trigger_file_path_lbl, trigger_file_path_hLay)

        ctrl.connect(trigger_file_path_le, "trigger_file_path", str)
        ctrl.update_ui()

        trigger_file_path_le.textChanged.connect(lambda x=0: ctrl.update_model())
        browse_path_pb.clicked.connect(lambda x=0: ctrl.update_model())
        # to validate on initial browse result
        browse_path_pb.clicked.connect(trigger_file_path_le.validate)


