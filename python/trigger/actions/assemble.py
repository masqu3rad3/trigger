"""Assembles the scene geo with alembic caches"""
import os
from trigger.core import filelog
from trigger.actions import import_asset
from trigger.library import naming

from trigger.ui.Qt import QtWidgets, QtGui # for progressbar
from trigger.ui.widgets.browser import BrowserButton
from trigger.ui import custom_widgets

log = filelog.Filelog(logname=__name__, filename="trigger_log")

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
            handler: (actions_session) An instance of the actions_session.
            TRY NOT TO USE HANDLER UNLESS ABSOLUTELY NECESSARY
            *args:
            **kwargs:

        Returns: None

        """
        alembic_paths_lbl = QtWidgets.QLabel(text="Alembic Paths")
        alembic_paths_listbox = custom_widgets.ListBoxLayout(alignment="start", buttonAdd=False, buttonNew=False,
                                                             buttonGet=False, buttonRename=False, buttonUp=False,
                                                             buttonDown=False)
        font = QtGui.QFont()
        font.setPointSize(8)
        alembic_paths_listbox.viewWidget.setFont(font)
        alembic_paths_listbox.viewWidget.setViewMode(QtWidgets.QListView.ListMode)
        alembic_paths_listbox.viewWidget.setAlternatingRowColors(True)

        browse_pb = BrowserButton(text="Add", filterExtensions=["Alembic (*.abc)"],
                                                 title="Choose Alembic Asset Cache")
        alembic_paths_listbox.addNewButton(browse_pb, insert=0)
        next_version_pb = QtWidgets.QPushButton(text="Next Version")
        previous_version_pb = QtWidgets.QPushButton(text="Previous Version")
        alembic_paths_listbox.addNewButton(next_version_pb, insert=1)
        alembic_paths_listbox.addNewButton(previous_version_pb, insert=2)
        layout.addRow(alembic_paths_lbl, alembic_paths_listbox)

        ctrl.connect(alembic_paths_listbox.viewWidget, "alembic_path_list", list)

        ctrl.update_ui()

        def color_update(item):
            file_path = os.path.normpath(str(item.text()))
            if not os.path.isfile(file_path):
                item.setForeground(QtGui.QColor(255, 0, 0, 255))
            elif naming.is_latest_version(file_path):
                item.setForeground(QtGui.QColor(0, 255, 0, 255))
            else:
                item.setForeground(QtGui.QColor(255, 255, 0, 255))

        def update_all():
            row_count = alembic_paths_listbox.viewWidget.count()
            for row_nmb in range(row_count):
                item = alembic_paths_listbox.viewWidget.item(row_nmb)
                color_update(item)

        update_all()

        def add_path_to_list():
            file_path = browse_pb.selectedPath()
            if file_path:
                item = QtWidgets.QListWidgetItem(file_path)
                alembic_paths_listbox.viewWidget.addItem(item)
                color_update(item)
                # alembic_paths_listbox.viewWidget.addItem(file_path)
            ctrl.update_model()

        def version_up():
            row = alembic_paths_listbox.viewWidget.currentRow()
            if row == -1:
                return
            current_item = alembic_paths_listbox.viewWidget.currentItem()
            current_text = current_item.text()
            current_item.setText(naming.get_next_version(current_text))
            color_update(current_item)

            ctrl.update_model()

        def version_down():
            row = alembic_paths_listbox.viewWidget.currentRow()
            if row == -1:
                return
            current_item = alembic_paths_listbox.viewWidget.currentItem()
            current_text = current_item.text()
            current_item.setText(naming.get_previous_version(current_text))
            color_update(current_item)
            ctrl.update_model()

        alembic_paths_listbox.buttonRemove.clicked.connect(lambda x: ctrl.update_model())
        browse_pb.clicked.connect(add_path_to_list)
        next_version_pb.clicked.connect(version_up)
        previous_version_pb.clicked.connect(version_down)

    @staticmethod
    def info():
        description_text = """
This action is for assembling set of Alembic files into the scene. The imported alembic caches updates the scene 
hierarchy. That means, only the non-existing nodes will be imported. The existing groups/meshes won't be duplicated.
"""
        return description_text
