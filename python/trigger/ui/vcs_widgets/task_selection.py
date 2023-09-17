"""Custom version control widget for selecting tasks and versions"""

"""Custom shotgrid control widget for selecting trigger sessions and versions """

# from trigger.ui.Qt import QtWidgets, QtCore
from PySide2 import QtWidgets, QtCore
from trigger import version_control


class TaskSelection(QtWidgets.QVBoxLayout):
    task_changed_signal = QtCore.Signal(str)

    def __init__(self):
        super(TaskSelection, self).__init__()

        if not version_control:
            return
        else:
            self.sgh = version_control.controller.VersionControl()

        self.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        self.size_policy.setHorizontalStretch(0)
        self.size_policy.setVerticalStretch(0)

        self.first_line = QtWidgets.QHBoxLayout()
        self.addLayout(self.first_line)

        self.asset_type_combo = self._insert_single_combo(self.first_line, "Asset Type")
        self.asset_type_combo.setSizePolicy(self.size_policy)
        self.asset_combo = self._insert_single_combo(self.first_line, "Asset")
        self.asset_combo.setSizePolicy(self.size_policy)
        self.step_combo = self._insert_single_combo(self.first_line, "Step")
        self.step_combo.setSizePolicy(self.size_policy)
        self.task_combo = self._insert_single_combo(self.first_line, "Task")
        self.task_combo.setSizePolicy(self.size_policy)

        # self.populate_asset_types()

        # ####################
        # SIGNALS
        # ####################
        self.asset_type_combo.activated.connect(self.set_asset_type)
        self.asset_combo.activated.connect(self.set_asset)
        self.step_combo.activated.connect(self.set_step)
        self.task_combo.activated.connect(self.set_task)

        # self.first_line.addStretch(1)

    @staticmethod
    def _insert_single_combo(layout, label_text=""):
        """Adds a single combobox (label on top) to the layout widget"""
        _hold_vlay = QtWidgets.QVBoxLayout()
        _label = QtWidgets.QLabel(text=label_text)
        _label.setAlignment(QtCore.Qt.AlignCenter)
        _hold_vlay.addWidget(_label)
        combo = QtWidgets.QComboBox()
        combo.setMinimumHeight(25)
        _hold_vlay.addWidget(combo)
        layout.addLayout(_hold_vlay)
        return combo

    def populate_asset_types(self):
        self.asset_type_combo.clear()
        self.asset_type_combo.addItems(self.sgh.get_asset_types())
        if self.sgh.asset_type:
            self.asset_type_combo.setCurrentText(self.sgh.asset_type)
        else:
            self.asset_type_combo.setCurrentIndex(0)
        self.populate_assets()

    def populate_assets(self):
        self.asset_combo.clear()
        current_asset_type = self.sgh.asset_type or self.asset_type_combo.currentText()
        self.asset_combo.addItems(self.sgh.get_assets(current_asset_type))
        if self.sgh.asset:
            self.asset_combo.setCurrentText(self.sgh.asset)
        else:
            self.asset_combo.setCurrentIndex(0)
        self.populate_steps()

    def populate_steps(self):
        self.step_combo.clear()
        current_asset = self.sgh.asset or self.asset_combo.currentText()
        self.step_combo.addItems(self.sgh.get_steps(current_asset))
        if self.sgh.step:
            self.step_combo.setCurrentText(self.sgh.step)
        else:
            self.step_combo.setCurrentIndex(0)
        self.populate_tasks()

    def populate_tasks(self):
        self.task_combo.clear()
        current_asset = self.sgh.asset or self.asset_combo.currentText()
        current_step = self.sgh.step or self.step_combo.currentText()
        self.task_combo.addItems(self.sgh.get_tasks(current_asset, current_step))
        if self.sgh.task:
            self.task_combo.setCurrentText(str(self.sgh.task))
        else:
            self.task_combo.setCurrentIndex(0)
        # self.populate_sessions()

    def set_asset_type(self):
        self.sgh.asset_type = self.asset_type_combo.currentText()
        self.populate_assets()
        self.set_asset()

    def set_asset(self):
        self.sgh.asset = self.asset_combo.currentText()
        self.populate_steps()
        self.set_step()

    def set_step(self):
        self.sgh.step = self.step_combo.currentText()
        self.populate_tasks()
        self.set_task()

    def set_task(self):
        self.sgh.task = self.task_combo.currentText()
        # self.task_changed_signal.emit(self.sgh.)
