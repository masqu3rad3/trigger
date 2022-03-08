"""Widget to be used to select published assets. Derived from task_selection"""

from trigger import version_control
from trigger.ui.vcs_widgets.task_selection import TaskSelection

from trigger.ui.Qt import QtWidgets, QtCore
# from PySide2 import QtWidgets, QtCore

class PublishSelection(TaskSelection):
    selectionChanged = QtCore.Signal(str)
    def __init__(self):
        super(PublishSelection, self).__init__()

        # _publish_path = None

        self.second_line = QtWidgets.QHBoxLayout()
        self.addLayout(self.second_line)
        self.published_versions_combo = TaskSelection._insert_single_combo(self.second_line, "Publish Version")
        self.published_types_combo = TaskSelection._insert_single_combo(self.second_line, "Publish Type")
        self.published_types_combo.setSizePolicy(self.size_policy)

        # SUGNAL
        self.published_versions_combo.activated.connect(self.set_publish_version())
        self.published_types_combo.activated.connect(self.set_publish_type)

        self.populate_asset_types()

    # @property
    def get_path(self):
        return self.sgh.get_publish_path()

    # @path.setter
    # def path(self, path):
    #     # set the model
    #     self.sgh.set_publish_fields_from_path(path)
    #     # refresh the combos
    #     self.populate_asset_types()

    def set_path(self, path):
        # set the model
        state = self.sgh.set_publish_fields_from_path(path)
        # refresh the combos
        if state:
            self.populate_asset_types()
        return state

    def populate_tasks(self):
        super(PublishSelection, self).populate_tasks()
        self.populate_publish_versions()

    # def populate_tasks(self):
    #     self.task_combo.clear()
    #     current_asset = self.sgh.asset or self.asset_combo.currentText()
    #     current_step = self.sgh.step or self.step_combo.currentText()
    #     self.task_combo.addItems(self.sgh.get_tasks(current_asset, current_step))
    #     if self.sgh.task:
    #         self.task_combo.setCurrentText(str(self.sgh.task))
    #     else:
    #         self.task_combo.setCurrentIndex(0)
    #     self.populate_publish_versions()

    def set_task(self):
        # self.sgh.task = self.task_combo.currentText()
        super(PublishSelection, self).set_task()
        self.populate_publish_versions()
        self.set_publish_version()

    def populate_publish_versions(self):
        """Lists all versions for selected publish element"""
        self.published_versions_combo.clear()
        current_task = self.sgh.task or self.task_combo.currentText()
        _int_version_list = sorted(self.sgh.get_publish_versions(current_task))
        _str_version_list = ([str(x) for x in _int_version_list])
        print("DEBUG___")
        print(current_task)
        print(_int_version_list)
        print(_str_version_list)
        self.published_versions_combo.addItems(_str_version_list)
        last_version = self.published_versions_combo.count()-1
        self.published_versions_combo.setCurrentIndex(last_version)
        # if self.sgh.publish_version:
        #     self.published_versions_combo.setCurrentText(self.sgh.publish_version)
        # else:
        #     self.published_versions_combo.setCurrentIndex(0)
        # self.populate_publish_types()
        self.set_publish_version()

    def populate_publish_types(self):
        """Lists available published types which belongs to the parent task"""
        self.published_types_combo.clear()
        current_version = self.sgh.publish_version or self.published_versions_combo.currentText()
        if not current_version:
            return
        self.published_types_combo.addItems(self.sgh.get_publish_types(current_version))
        if self.sgh.publish_type:
            self.published_types_combo.setCurrentText(self.sgh.publish_type)
        else:
            self.published_types_combo.setCurrentIndex(0)


        print(self.sgh.get_publish_path())

    def set_publish_version(self):
        """Sets the selected publish version"""
        _version = self.published_versions_combo.currentText()
        if _version:
            self.sgh.publish_version = int(_version)
        else:
            self.sgh.publish_version = None
        self.populate_publish_types()
        self.set_publish_type()

    def set_publish_type(self):
        """sets the selected publish on model"""
        self.sgh.publish_type = self.published_types_combo.currentText()
        self.selectionChanged.emit(self.sgh.get_publish_path())

    # def set_from_path(self, path):
    #     """Sets the dropdown lists from the path"""
    #     # set the model
    #     self.sgh.set_publish_fields_from_path(path)
    #     # refresh the combos
    #     self.populate_asset_types()
