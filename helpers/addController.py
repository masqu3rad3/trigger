## Adds a direct controller to the selected joint (or any other object)
import sys

from trigger.library import functions
from trigger.library import naming
from trigger.library import api
from trigger.library.controllers import Icon
from trigger.core.decorators import undo

from trigger.ui import Qt
from trigger.ui.Qt import QtWidgets, QtCore, QtGui

from maya import OpenMayaUI as omui
from maya import cmds

if Qt.__binding__ == "PySide":
    from shiboken import wrapInstance
    from trigger.ui.Qt.QtCore import Signal
elif Qt.__binding__.startswith('PyQt'):
    from sip import wrapinstance as wrapInstance
    from trigger.ui.Qt.QtCore import pyqtSignal as Signal
else:
    from shiboken2 import wrapInstance
    from trigger.ui.Qt.QtCore import Signal

VERSION = "0.0.2"
WINDOW_NAME = "Add_Controller %s" % VERSION

def getMayaMainWindow():
    """
    Gets the memory adress of the main window to connect Qt dialog to it.
    Returns:
        (long) Memory Adress
    """
    win = omui.MQtUtil_mainWindow()
    if sys.version_info.major == 3:
        ptr = wrapInstance(int(win), QtWidgets.QMainWindow)
    else:
        ptr = wrapInstance(long(win), QtWidgets.QMainWindow)
    return ptr

class AddController(Icon):
    """Inherits Trigger's controller library"""
    def __init__(self):
        super(AddController, self).__init__()

    @undo
    def add_controller(self, name="", icon="", scale=1.0, constraint="None", add_scale_constraint=False, normal=(0,1,0)):
        """Adds controllers for each selected object"""
        selection = cmds.ls(sl=True)
        if not selection:
            cont, _ = self.createIcon(icon, iconName=name, scale=(scale, scale, scale), normal=normal)
            return
        for sel in selection:
            if not name:
                name = "%s_cont" % sel
            # make sure the name is unique
            name = naming.uniqueName(name)
            cont, _ = self.createIcon(icon, iconName=name, scale=(scale, scale, scale), normal=normal)
            cont_offset = functions.createUpGrp(cont, "offset")
            functions.alignTo(cont_offset, sel, position=True, rotation=True)
            if constraint == "Point":
                cmds.pointConstraint(cont, sel, mo=False)
            elif constraint == "Orient":
                cmds.orientConstraint(cont, sel, mo=False)
            elif constraint == "Parent":
                cmds.parentConstraint(cont, sel, mo=False)

            if add_scale_constraint:
                cmds.scaleConstraint(cont, sel, mo=False)


class MainUI(QtWidgets.QDialog):
    def __init__(self):
        for entry in QtWidgets.QApplication.allWidgets():
            try:
                if entry.objectName() == WINDOW_NAME:
                    entry.close()
            except (AttributeError, IndexError):
                pass
        parent = getMayaMainWindow()
        super(MainUI, self).__init__(parent=parent)

        self.controller_handler = AddController()
        # self.all_iconFunctions = inspect.getmembers(icon, inspect.isfunction)
        self.wSize = 400
        self.hSize = 20
        # self.setFixedSize(300, 270)
        self.setObjectName(WINDOW_NAME)
        self.setWindowTitle(WINDOW_NAME)
        self.resize(360, 270)
        self.buildUI()

    def buildUI(self):
        master_layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(master_layout)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)

        form_layout = QtWidgets.QFormLayout(spacing=10, labelAlignment=(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter))
        name_lbl = QtWidgets.QLabel()
        name_lbl.setText("Name:")
        self.name_le = QtWidgets.QLineEdit()
        self.name_le.setPlaceholderText("(Optional)")
        form_layout.addRow(name_lbl, self.name_le)

        icon_lbl = QtWidgets.QLabel()
        icon_lbl.setText("Icon:")
        self.icon_combo = QtWidgets.QComboBox()
        form_layout.addRow(icon_lbl, self.icon_combo)
        self.icon_combo.setSizePolicy(sizePolicy)
        self.icon_combo.addItems(self.controller_handler.getIconsList())

        icon_scale_lbl = QtWidgets.QLabel()
        icon_scale_lbl.setText("Scale:")
        self.icon_scale_spin = QtWidgets.QDoubleSpinBox()
        self.icon_scale_spin.setValue(1.0)
        form_layout.addRow(icon_scale_lbl, self.icon_scale_spin)

        constraint_lbl = QtWidgets.QLabel()
        constraint_lbl.setText("Constraint:")
        self.constraint_combo = QtWidgets.QComboBox()
        self.constraint_combo.addItems(["Point", "Orient", "Parent", "None"])
        form_layout.addRow(constraint_lbl, self.constraint_combo)

        scale_constraint_lbl = QtWidgets.QLabel()
        scale_constraint_lbl.setText("Scale Constraint")
        self.scale_constraint_cb = QtWidgets.QCheckBox()
        # scale_constraint_cb.
        form_layout.addRow(scale_constraint_lbl, self.scale_constraint_cb)

        normal_lbl = QtWidgets.QLabel()
        normal_lbl.setText("Normal")
        normal_hlay = QtWidgets.QHBoxLayout()
        self.normal_x_spinner = QtWidgets.QDoubleSpinBox(buttonSymbols=QtWidgets.QAbstractSpinBox.NoButtons, value=0.0, decimals=1)
        self.normal_y_spinner = QtWidgets.QDoubleSpinBox(buttonSymbols=QtWidgets.QAbstractSpinBox.NoButtons, value=1.0, decimals=1)
        self.normal_z_spinner = QtWidgets.QDoubleSpinBox(buttonSymbols=QtWidgets.QAbstractSpinBox.NoButtons, value=0.0, decimals=1)
        normal_hlay.addWidget(self.normal_x_spinner)
        normal_hlay.addWidget(self.normal_y_spinner)
        normal_hlay.addWidget(self.normal_z_spinner)
        form_layout.addRow(normal_lbl, normal_hlay)

        master_layout.addLayout(form_layout)

        create_controllers_pb = QtWidgets.QPushButton()
        create_controllers_pb.setText("Create Controller(s)")
        master_layout.addWidget(create_controllers_pb)

        ## SIGNALS
        create_controllers_pb.clicked.connect(self.on_create_controllers)

    def on_create_controllers(self):
        # gather the arguments
        name = self.name_le.text()
        icon = self.icon_combo.currentText()
        scale = self.icon_scale_spin.value()
        constraint_type = self.constraint_combo.currentText()
        is_scale_constraint = self.scale_constraint_cb.isChecked()
        normal = (self.normal_x_spinner.value(), self.normal_y_spinner.value(), self.normal_z_spinner.value())

        self.controller_handler.add_controller(name=name, icon=icon, scale=scale, constraint=constraint_type, add_scale_constraint=is_scale_constraint, normal=normal)
