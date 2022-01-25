import os
from trigger.library import naming
from trigger.ui.Qt import QtWidgets, QtCore, QtGui
from trigger.ui import feedback
from trigger.core import foolproof

from PySide2 import QtWidgets, QtCore

try:
    from trigger.base import rbl_shotgrid as shotgrid
except:
    shotgrid = None

class AssetSelection(QtWidgets.QHBoxLayout):
    def __init__(self, *args, **kwargs):
        super(AssetSelection, self).__init__(*args, **kwargs)

        if not shotgrid:
            return
        else:
            self.sgh = shotgrid.ShotTrigger()

        self._asset_type_lay = QtWidgets.QVBoxLayout()
        self._asset_lay = QtWidgets.QVBoxLayout()
        self._step_lay = QtWidgets.QVBoxLayout()
        self._task_lay = QtWidgets.QVBoxLayout()

        self._asset_type_lb = QtWidgets.QLabel(text="Asset Type")
        self._asset_type_lb.setAlignment(QtCore.Qt.AlignCenter)
        self._asset_type_lay.addWidget(self._asset_type_lb)

        self._asset_lb = QtWidgets.QLabel(text="Asset")
        self._asset_lb.setAlignment(QtCore.Qt.AlignCenter)
        self._asset_lay.addWidget(self._asset_lb)

        self._step_lb = QtWidgets.QLabel(text="Step")
        self._step_lb.setAlignment(QtCore.Qt.AlignCenter)
        self._step_lay.addWidget(self._step_lb)

        self._task_lb = QtWidgets.QLabel(text="Task")
        self._task_lb.setAlignment(QtCore.Qt.AlignCenter)
        self._task_lay.addWidget(self._task_lb)

        self.asset_type_combo = QtWidgets.QComboBox()
        self._asset_type_lay.addWidget(self.asset_type_combo)
        self.asset_combo = QtWidgets.QComboBox()
        self._asset_lay.addWidget(self.asset_combo)
        self.step_combo = QtWidgets.QComboBox()
        self._step_lay.addWidget(self.step_combo)
        self.task_combo = QtWidgets.QComboBox()
        self._task_lay.addWidget(self.task_combo)

        self.addLayout(self._asset_type_lay)
        self.addLayout(self._asset_lay)
        self.addLayout(self._step_lay)
        self.addLayout(self._task_lay)

        self.populate_asset_types()
        self.populate_assets()
        self.populate_steps()
        self.populate_tasks()

        self.asset_type_combo.activated.connect(self.set_asset_type)

    def populate_asset_types(self):
        self.asset_type_combo.clear()
        self.asset_type_combo.addItems(self.sgh.get_asset_types())
        if self.sgh.asset_type:
            self.asset_type_combo.setCurrentText(self.sgh.asset_type)
        else:
            self.asset_type_combo.setCurrentIndex(0)

    def populate_assets(self):
        self.asset_combo.clear()
        current_asset_type = self.sgh.asset_type or self.asset_type_combo.currentText()
        self.asset_combo.addItems(self.sgh.get_assets(current_asset_type))
        if self.sgh.asset:
            self.asset_combo.setCurrentText(self.sgh.asset)
        else:
            self.asset_combo.setCurrentIndex(0)

    def populate_steps(self):
        self.step_combo.clear()
        current_asset = self.sgh.asset or self.asset_combo.currentText()
        self.step_combo.addItems(self.sgh.get_steps(current_asset))
        if self.sgh.step:
            self.step_combo.setCurrentText(self.sgh.step)
        else:
            self.step_combo.setCurrentIndex(0)

    def populate_tasks(self):
        self.task_combo.clear()
        current_asset = self.sgh.asset or self.asset_combo.currentText()
        current_step = self.sgh.step or self.step_combo.currentText()
        self.task_combo.addItems(self.sgh.get_tasks(current_asset, current_step))
        if self.sgh.task:
            self.task_combo.setCurrentText(self.sgh.task)
        else:
            self.task_combo.setCurrentIndex(0)

    def set_asset_type(self, val):
        print(self.asset_type_combo.currentText())
        pass

    def set_asset(self, val):
        pass

    def set_step(self, val):
        pass

    def set_task(self, val):
        pass



