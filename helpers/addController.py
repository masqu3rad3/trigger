## Adds a direct controller to the selected joint (or any other object)
import sys
# import pymel.core as pm

from trigger.library import functions
from trigger.library.controllers import Icon
from trigger.core.undo_dec import undo
import inspect

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

# TODO: temp
from PySide2 import QtWidgets, QtCore, QtGui

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
            name = functions.uniqueName(name)
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

    # @undo
    # def add_controller(self, icon_type, icon_name=None, scale=(1,1,1)):
    #     selection = cmds.ls(sl=True)
    #     if not selection:
    #         cont, _ = self.createIcon()
    #     pass
    #
    #     with pm.UndoChunk():
    #
    #         if self.suffix_lineEdit.text() == "":
    #             suffix = self.controllerType_comboBox.currentText()
    #         else:
    #             suffix = self.suffix_lineEdit.text()
    #
    #         scale = (self.controllerScale_doubleSpinBox.value(), self.controllerScale_doubleSpinBox.value(), self.controllerScale_doubleSpinBox.value())
    #         if not pm.ls(sl=True):
    #             self.all_iconFunctions[self.controllerType_comboBox.currentIndex()][1](name="cont_{0}".format(suffix), scale=scale)
    #
    #         else:
    #             counter = 1
    #             for i in pm.ls(sl=True):
    #                 cont = self.all_iconFunctions[self.controllerType_comboBox.currentIndex()][1](name="cont_{0}{1}".format(suffix, counter), scale=scale)
    #                 functions.alignToAlter(cont, i, mode=2)
    #                 functions.createUpGrp(cont, "ORE")
    #
    #                 if self.parentCon_radioButton.isChecked():
    #                     pm.parentConstraint(cont, i, mo=False)
    #                 elif self.orientCon_radioButton.isChecked():
    #                     pm.orientConstraint(cont, i, mo=False)
    #                 elif self.pointCon_radioButton.isChecked():
    #                     pm.pointConstraint(cont, i, mo=False)
    #                 if self.scaleCon_checkBox.isChecked():
    #                     pm.scaleConstraint(cont, i, mo=False)
    #
    #             counter += 1



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











    def old_buildUI(self):

        self.setObjectName(WINDOW_NAME)
        self.resize(300, 270)
        self.setWindowTitle(WINDOW_NAME)



        self.controllerType_label = QtWidgets.QLabel(self)
        self.controllerType_label.setGeometry(QtCore.QRect(20, 60, 101, 21))
        self.controllerType_label.setFrameShape(QtWidgets.QFrame.Box)
        self.controllerType_label.setText(("Controller Type:"))

        self.controllerType_comboBox = QtWidgets.QComboBox(self)
        self.controllerType_comboBox.setGeometry(QtCore.QRect(130, 60, 151, 22))

        self.controllerScale_doubleSpinBox = QtWidgets.QDoubleSpinBox(self, value=1, minimum=0, singleStep=0.1)
        self.controllerScale_doubleSpinBox.setGeometry(QtCore.QRect(210, 100, 71, 21))
        self.controllerScale_doubleSpinBox.setPrefix((""))
        self.controllerScale_doubleSpinBox.setSuffix((""))

        self.controllerScale_label = QtWidgets.QLabel(self)
        self.controllerScale_label.setGeometry(QtCore.QRect(20, 100, 101, 21))
        self.controllerScale_label.setFrameShape(QtWidgets.QFrame.Box)
        self.controllerScale_label.setText(("Controller Scale:"))

        self.constraintMethod_groupBox = QtWidgets.QGroupBox(self)
        self.constraintMethod_groupBox.setGeometry(QtCore.QRect(20, 130, 261, 51))
        self.constraintMethod_groupBox.setTitle(("Constraint Method"))
        self.constraintMethod_groupBox.setFlat(False)
        self.constraintMethod_groupBox.setCheckable(False)

        self.pointCon_radioButton = QtWidgets.QRadioButton(self.constraintMethod_groupBox)
        self.pointCon_radioButton.setGeometry(QtCore.QRect(10, 20, 61, 18))
        self.pointCon_radioButton.setText(("Point"))

        self.orientCon_radioButton = QtWidgets.QRadioButton(self.constraintMethod_groupBox)
        self.orientCon_radioButton.setGeometry(QtCore.QRect(70, 20, 61, 18))
        self.orientCon_radioButton.setText(("Orient"))

        self.parentCon_radioButton = QtWidgets.QRadioButton(self.constraintMethod_groupBox)
        self.parentCon_radioButton.setGeometry(QtCore.QRect(130, 20, 61, 18))
        self.parentCon_radioButton.setText(("Parent"))
        self.parentCon_radioButton.setChecked(True)

        self.none_radioButton = QtWidgets.QRadioButton(self.constraintMethod_groupBox)
        self.none_radioButton.setGeometry(QtCore.QRect(190, 20, 61, 18))
        self.none_radioButton.setText(("None"))

        self.scaleCon_checkBox = QtWidgets.QCheckBox(self)
        self.scaleCon_checkBox.setGeometry(QtCore.QRect(180, 190, 101, 20))
        self.scaleCon_checkBox.setText(("Scale Constraint"))

        self.suffix_label = QtWidgets.QLabel(self)
        self.suffix_label.setGeometry(QtCore.QRect(20, 20, 51, 21))
        self.suffix_label.setFrameShape(QtWidgets.QFrame.Box)
        self.suffix_label.setText(("Suffix:"))

        self.suffix_lineEdit = QtWidgets.QLineEdit(self)
        self.suffix_lineEdit.setGeometry(QtCore.QRect(80, 20, 201, 20))
        self.suffix_lineEdit.setText((""))
        self.suffix_lineEdit.setAlignment(QtCore.Qt.AlignCenter)
        self.suffix_lineEdit.setPlaceholderText(("choose an unique name"))

        self.create_pushButton = QtWidgets.QPushButton(self)
        self.create_pushButton.setGeometry(QtCore.QRect(20, 220, 261, 31))
        self.create_pushButton.setText(("Create Controller(s)"))

        # iconNames = [i[0] for i in self.all_iconFunctions]
        # self.controllerType_comboBox.addItems(iconNames)

        # self.create_pushButton.clicked.connect(self.createController)


