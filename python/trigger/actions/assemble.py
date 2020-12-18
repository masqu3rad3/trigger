"""Assembles the scene geo with alembic caches"""

from trigger.core import io
from trigger.core import logger
from trigger.actions import import_asset
from trigger.library import naming

from trigger.ui.Qt import QtWidgets, QtGui # for progressbar
from trigger.ui import custom_widgets
from trigger.ui import feedback

LOG = logger.Logger(__name__)

ACTION_DATA = {
    "alembic_path_list": [],
}

# Name of the class MUST be the capitalized version of file name. eg. morph.py => Morph, split_shapes.py => Split_shapes
class Assemble(import_asset.Import_asset):
    def __init__(self, *args, **kwargs):
        super(Assemble, self).__init__()

        # user defined variables
        self.alembicPathList = []

        # class variables

    def feed(self, action_data, *args, **kwargs):
        """Mandatory Method - Feeds the instance with the action data stored in actions session"""
        self.alembicPathList = action_data.get("alembic_path_list")

    def action(self):
        """Mandatory Method - Execute Action"""
        # everything in this method will be executed automatically.
        # This method does not accept any arguments. all the user variable must be defined to the instance before
        for file_path in self.alembicPathList:
            self.import_alembic(file_path, update_only=True)

    def save_action(self, file_path=None, *args, **kwargs):
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
        alembic_paths_lbl = QtWidgets.QLabel(text="Alembic Paths")
        alembic_paths_listbox = custom_widgets.ListBoxLayout(alignment="start", buttonAdd=False, buttonNew=False, buttonGet=False, buttonRename=False, buttonUp=False, buttonDown=False)
        browse_pb = custom_widgets.BrowserButton(text="Add", filterExtensions=["Alembic (*.abc)"], title="Choose Alembic Asset Cache")
        alembic_paths_listbox.addNewButton(browse_pb, insert=0)
        increment_pb = QtWidgets.QPushButton(text="Increment Version")
        alembic_paths_listbox.addNewButton(increment_pb, insert=1)
        layout.addRow(alembic_paths_lbl, alembic_paths_listbox)

        ctrl.connect(alembic_paths_listbox.viewWidget, "alembic_path_list", list)

        ctrl.update_ui()

        def add_path_to_list():
            file_path = browse_pb.selectedPath()
            if file_path:
                alembic_paths_listbox.viewWidget.addItem(file_path)
            ctrl.update_model()

        def increment():
            row = alembic_paths_listbox.viewWidget.row()
            if row == -1:
                return
            current_text = alembic_paths_listbox.viewWidget.currentItem().text()
            naming.increment(current_text, force_version=False)
            ctrl.update_model()

        alembic_paths_listbox.buttonRemove.clicked.connect(lambda x: ctrl.update_model())
        browse_pb.clicked.connect(add_path_to_list)
