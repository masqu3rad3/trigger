import os
from trigger.library import naming
# from trigger.ui.Qt import QtWidgets, QtCore, QtGui
from trigger.ui import feedback
from trigger.core import foolproof

from PySide2 import QtWidgets, QtCore

try:
    from trigger.base import rbl_shotgrid as shotgrid
except ImportError:
    shotgrid = None


class AssetSelection(QtWidgets.QHBoxLayout):
    def __init__(self, *args, **kwargs):
        super(AssetSelection, self).__init__(*args, **kwargs)

        if not shotgrid:
            return
        else:
            self.sgh = shotgrid.ShotTrigger()

        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        size_policy.setHorizontalStretch(1)
        size_policy.setVerticalStretch(0)

        _asset_type_lay = QtWidgets.QVBoxLayout()
        _asset_type_lb = QtWidgets.QLabel(text="Asset Type")
        _asset_type_lb.setAlignment(QtCore.Qt.AlignCenter)
        _asset_type_lay.addWidget(_asset_type_lb)
        self.asset_type_combo = QtWidgets.QComboBox()
        _asset_type_lay.addWidget(self.asset_type_combo)
        self.addLayout(_asset_type_lay)

        _asset_lay = QtWidgets.QVBoxLayout()
        _asset_lb = QtWidgets.QLabel(text="Asset")
        _asset_lb.setAlignment(QtCore.Qt.AlignCenter)
        _asset_lay.addWidget(_asset_lb)
        self.asset_combo = QtWidgets.QComboBox()
        _asset_lay.addWidget(self.asset_combo)
        self.addLayout(_asset_lay)

        _step_lay = QtWidgets.QVBoxLayout()
        _step_lb = QtWidgets.QLabel(text="Step")
        _step_lb.setAlignment(QtCore.Qt.AlignCenter)
        _step_lay.addWidget(_step_lb)
        self.step_combo = QtWidgets.QComboBox()
        _step_lay.addWidget(self.step_combo)
        self.addLayout(_step_lay)

        _task_lay = QtWidgets.QVBoxLayout()
        _task_lb = QtWidgets.QLabel(text="Task")
        _task_lb.setAlignment(QtCore.Qt.AlignCenter)
        _task_lay.addWidget(_task_lb)
        self.task_combo = QtWidgets.QComboBox()
        self.task_combo.setContentsMargins(0,0,0,0)
        _task_lay.addWidget(self.task_combo)
        self.addLayout(_task_lay)

        _session_lay = QtWidgets.QVBoxLayout()
        _session_lb = QtWidgets.QLabel(text="Session")
        _session_lb.setAlignment(QtCore.Qt.AlignCenter)
        _session_lay.addWidget(_session_lb)
        _session_h_lay = QtWidgets.QHBoxLayout()
        _session_h_lay.setMargin(0)
        _session_h_lay.setSpacing(0)
        _session_h_lay.setContentsMargins(0,0,0,0)

        _session_lay.setMargin(0)
        _session_lay.setSpacing(0)
        _session_lay.setContentsMargins(0,0,0,0)


        self.session_combo = QtWidgets.QComboBox()
        self.session_combo.setMinimumHeight(30)
        # self.session_combo.setSizePolicy(size_policy)
        self.new_session_pb = QtWidgets.QPushButton(text="+")
        self.new_session_pb.setMinimumHeight(30)
        # self.new_session_pb.setFixedWidth(30)
        _session_h_lay.addWidget(self.session_combo)
        _session_h_lay.addWidget(self.new_session_pb)
        _session_lay.addLayout(_session_h_lay)
        self.addLayout(_session_lay)

        _version_lay = QtWidgets.QVBoxLayout()
        _version_lb = QtWidgets.QLabel(text="Version")
        _version_lb.setAlignment(QtCore.Qt.AlignCenter)
        _version_lay.addWidget(_version_lb)
        _version_h_lay = QtWidgets.QHBoxLayout()
        self.version_combo = QtWidgets.QComboBox()
        self.new_version_pb = QtWidgets.QPushButton(text="+")
        self.new_version_pb.setFixedWidth(30)
        _version_h_lay.addWidget(self.version_combo)
        _version_h_lay.addWidget(self.new_version_pb)
        _version_lay.addLayout(_version_h_lay)
        self.addLayout(_version_lay)

        # # add new session button
        # self._add_session_lay = QtWidgets.QVBoxLayout()
        # self._add_session_lb = QtWidgets.QLabel(text="")
        # self._add_session_lb.setAlignment(QtCore.Qt.AlignCenter)
        # self._add_session_lay.addWidget(self._add_session_lb)
        # self.add_session_pb = QtWidgets.QPushButton(text="+")
        # self.add_session_pb.setFixedWidth(40)
        # self._add_session_lay.addWidget(self.add_session_pb)
        # self.addLayout(self._add_session_lay)

        self.populate_asset_types()

        self.asset_type_combo.activated.connect(self.set_asset_type)
        self.asset_combo.activated.connect(self.set_asset)
        self.step_combo.activated.connect(self.set_step)
        self.task_combo.activated.connect(self.set_task)
        self.session_combo.activated.connect(self.set_session)
        self.version_combo.activated.connect(self.set_version)

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
            self.task_combo.setCurrentText(self.sgh.task)
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

    def populate_versions(self):
        self.version_combo.clear()
        asset = self.sgh.asset or self.asset_combo.currentText()
        step = self.sgh.step or self.step_combo.currentText()
        variant = self.sgh.variant or self.sgh._variant_from_task(self.task_combo.currentText())
        session = self.sgh.session or self.session_combo.currentText()
        _str_version_list = sorted([str(x) for x in self.sgh.get_versions(asset, step, variant, session)])
        self.version_combo.addItems(_str_version_list)
        if self.sgh.session_version:
            self.version_combo.addItems(self.sgh.get_versions(asset, step, variant, session))
        else:
            self.version_combo.setCurrentIndex(self.version_combo.count()-1)

    def set_asset_type(self):
        self.sgh.asset_type = self.asset_type_combo.currentText()
        self.populate_assets()

    def set_asset(self):
        self.sgh.asset = self.asset_combo.currentText()
        self.populate_steps()

    def set_step(self):
        self.sgh.step = self.step_combo.currentText()
        self.populate_tasks()

    def set_task(self):
        self.sgh.task = self.task_combo.currentText()
        self.populate_sessions()

    def set_session(self):
        self.sgh.session = self.session_combo.currentText()
        self.populate_versions()

    def set_version(self):
        self.sgh.session_version = int(self.version_combo.currentText())




