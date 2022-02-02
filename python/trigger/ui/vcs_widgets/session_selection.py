"""Custom shotgrid control widget for selecting trigger sessions and versions """

from trigger.ui.Qt import QtWidgets, QtCore
# from PySide2 import QtWidgets, QtCore
from trigger import version_control

class SessionSelection(QtWidgets.QHBoxLayout):
    new_session_signal = QtCore.Signal(str)
    increment_version_signal = QtCore.Signal(str)
    session_changed_signal = QtCore.Signal(str)
    def __init__(self):
        super(SessionSelection, self).__init__()

        if not version_control:
            return
        else:
            self.sgh = version_control.controller.VersionControl()

        self.asset_type_combo = self.__insert_single_combo(self, "Asset Type")
        self.asset_combo = self.__insert_single_combo(self, "Asset")
        self.step_combo = self.__insert_single_combo(self, "Step")
        self.task_combo = self.__insert_single_combo(self, "Task")
        self.session_combo, self.new_session_pb = self.__insert_combo_with_add_button(self, "Session")
        self.version_combo, self.new_version_pb = self.__insert_combo_with_add_button(self, "Version")

        # self.parent_widget = QtWidgets.QWidget()
        # self.addWidget(self.parent_widget)

        self.populate_asset_types()

        # ####################
        # SIGNALS
        # ####################
        self.asset_type_combo.activated.connect(self.set_asset_type)
        self.asset_combo.activated.connect(self.set_asset)
        self.step_combo.activated.connect(self.set_step)
        self.task_combo.activated.connect(self.set_task)
        self.session_combo.activated.connect(self.set_session)
        self.version_combo.activated.connect(self.set_version)
        # self.asset_type_combo.currentTextChanged.connect(self.set_asset_type)
        # self.asset_combo.currentTextChanged.connect(self.set_asset)
        # self.step_combo.currentTextChanged.connect(self.set_step)
        # self.task_combo.currentTextChanged.connect(self.set_task)
        # self.session_combo.currentTextChanged.connect(self.set_session)
        # self.version_combo.currentTextChanged.connect(self.set_version)

        self.new_session_pb.clicked.connect(self.new_session_dialog)
        self.new_version_pb.clicked.connect(self.increment_version)

    def __validate_button_states(self):
        """Disables the new session and/or new version buttons depending on the task/session availability"""
        task_state = bool(self.task_combo.count())
        self.new_session_pb.setEnabled(task_state)
        session_state = bool(self.session_combo.count())
        self.new_version_pb.setEnabled(session_state)

    def new_session_dialog(self):
        # w = QtWidgets.QWidget()
        # self.addWidget(w)
        new_session_name, ok = QtWidgets.QInputDialog.getText(self.asset_type_combo, "New Session", "Enter new session name:")
        # new_session_name, ok = QtWidgets.QInputDialog.getText(self.parent_widget, "New Session", "Enter new session name:")
        # new_session_name, ok = QtWidgets.QInputDialog.getText(w, "New Session", "Enter new session name:")
        if ok:
            new_session_path = self.sgh.request_new_session_path(new_session_name)
            self.new_session_signal.emit(new_session_path)
            print("emitted")

    def increment_version(self):
        # self.set_session()
        # self.set_version()
        new_version_path = self.sgh.request_new_version_path()
        self.increment_version_signal.emit(new_version_path)
        # self.populate_versions(set_last=True)

    @staticmethod
    def __insert_single_combo(layout, label_text=""):
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

    @staticmethod
    def __insert_combo_with_add_button(layout, label_text="", button_text="+"):
        """Adds a combobox (label on top) with button to the layout widget"""
        _hold_vlay = QtWidgets.QVBoxLayout()
        _label = QtWidgets.QLabel(text=label_text)
        _label.setAlignment(QtCore.Qt.AlignCenter)
        _hold_vlay.addWidget(_label)
        _hold_hlay = QtWidgets.QHBoxLayout()
        _hold_hlay.setSpacing(1)
        combo = QtWidgets.QComboBox()
        combo.setMinimumHeight(25)
        button = QtWidgets.QPushButton(text=button_text)
        button.setMinimumHeight(24)
        button.setFixedWidth(25)
        _hold_hlay.addWidget(combo)
        _hold_hlay.addWidget(button)
        _hold_hlay.setContentsMargins(0, 0, 0, 0)
        _hold_vlay.addLayout(_hold_hlay)
        layout.addLayout(_hold_vlay)
        return combo, button

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
        self.populate_sessions()

    def populate_sessions(self):
        self.session_combo.clear()
        asset = self.sgh.asset or self.asset_combo.currentText()
        step = self.sgh.step or self.step_combo.currentText()
        variant = self.sgh.variant or self.sgh._variant_from_task(self.task_combo.currentText())
        self.session_combo.addItems(self.sgh.get_sessions(asset, step, variant))
        if self.sgh.session:
            self.session_combo.setCurrentText(self.sgh.session)
        else:
            self.session_combo.setCurrentIndex(0)
        self.populate_versions()
        self.__validate_button_states()

    # def populate_versions(self, set_last=False):
    #     self.version_combo.clear()
    #     asset = self.sgh.asset or self.asset_combo.currentText()
    #     step = self.sgh.step or self.step_combo.currentText()
    #     variant = self.sgh.variant or self.sgh._variant_from_task(self.task_combo.currentText())
    #     session = self.sgh.session or self.session_combo.currentText()
    #     _int_version_list = sorted(self.sgh.get_versions(asset, step, variant, session))
    #     _str_version_list = ([str(x) for x in _int_version_list])
    #     self.version_combo.addItems(_str_version_list)
    #     if self.sgh.session_version and not set_last:
    #         self.version_combo.setCurrentText(str(self.sgh.session_version))
    #     else:
    #         last_version = self.version_combo.count()-1
    #         self.version_combo.setCurrentIndex(last_version)
    #         self.sgh.session_version = last_version
    #     self.__validate_button_states()

    def populate_versions(self):
        self.version_combo.clear()
        asset = self.sgh.asset or self.asset_combo.currentText()
        step = self.sgh.step or self.step_combo.currentText()
        variant = self.sgh.variant or self.sgh._variant_from_task(self.task_combo.currentText())
        session = self.sgh.session or self.session_combo.currentText()
        _int_version_list = sorted(self.sgh.get_versions(asset, step, variant, session))
        _str_version_list = ([str(x) for x in _int_version_list])
        self.version_combo.addItems(_str_version_list)
        last_version = self.version_combo.count()-1
        self.version_combo.setCurrentIndex(last_version)
        # self.sgh.session_version = last_version
        self.__validate_button_states()

    def set_asset_type(self):
        print("debug")
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
        self.populate_sessions()
        self.set_session()

    def set_session(self):
        self.sgh.session = self.session_combo.currentText()
        # self.sgh.session_version = None # makes sure when switching back, it will pick up the latest
        self.populate_versions()
        self.set_version()

    def set_version(self):
        if self.version_combo.currentText():
            print("pre", self.sgh.session_version)
            self.sgh.session_version = int(self.version_combo.currentText())
            print("after", self.sgh.session_version)
            self.session_changed_signal.emit(self.sgh.get_session_path())




