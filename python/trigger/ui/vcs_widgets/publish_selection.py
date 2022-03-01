"""Widget to be used to select published assets. Derived from task_selection"""

from trigger import version_control
from trigger.ui.vcs_widgets.task_selection import TaskSelection

# from trigger.ui.Qt import QtWidgets, QtCore
from PySide2 import QtWidgets, QtCore

class PublishSelection(TaskSelection):
    def __init__(self):
        super(PublishSelection, self).__init__()

        self.second_line = QtWidgets.QHBoxLayout()
        self.addLayout(self.second_line)
        self.publishes_combo = TaskSelection._insert_single_combo(self.second_line, "Publish Type")
        self.publishes_combo.setSizePolicy(self.size_policy)
        self.publish_versions_combo = TaskSelection._insert_single_combo(self.second_line, "Publish Version")

        # SUGNAL
        self.publishes_combo.activated.connect(self.set_publish_type)

        self.populate_asset_types()

    def populate_tasks(self):
        super(PublishSelection, self).populate_tasks()
        self.populate_publish_types()

    def populate_publish_types(self):
        """Lists available published types which belongs to the parent task"""
        self.publishes_combo.clear()
        # TODO - get the information from rbl_shotgrid
        test_items = ["TEST.abc", "test.usd", "test.ma"]
        self.publishes_combo.addItems(test_items)

    def populate_publish_versions(self):
        """Lists all versions for selected publish element"""
        self.publish_versions_combo.clear()
        # TODO - get the infrotmation from rbl_shotgrid

    def set_publish_type(self):
        """sets the selected publish on model"""
        print("test set pub")
        # TODO - set the information to rbl_shotgrid model

    def set_publish_version(self):
        """Sets the selected publish version"""
        # TODO - set the information to rbl_shotgrid model
