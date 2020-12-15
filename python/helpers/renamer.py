#
# Renamer version 1.1

import sys
import maya.cmds as cmds

from trigger.ui import Qt
from trigger.ui.Qt import QtWidgets, QtCore, QtGui
from maya import OpenMayaUI as omui

if Qt.__binding__ == "PySide":
    from shiboken import wrapInstance
elif Qt.__binding__.startswith('PyQt'):
    from sip import wrapinstance as wrapInstance
else:
    from shiboken2 import wrapInstance

from trigger.library import functions
from trigger.core.decorators import undo
from trigger.core import logger

FEEDBACK = logger.Logger(__name__)


WINDOW_NAME = "Tik_Renamer"

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


class Renamer(object):
    def __init__(self):
        super(Renamer, self).__init__()
        self.objectList = []

    def getObjects(self, method):
        """returns objects according to the method"""
        if method == 0: # selected objects
            self.objectList = cmds.ls(sl=True, long=True)
        if method == 1: # Hierarchy
            self.objectList = cmds.listRelatives(cmds.ls(sl=True), c=True, ad=True, f=True)
        if method == 2: # Everything
            self.objectList = cmds.ls(long=True)


    def removePasted(self, selectMethod):
        """Removes pasted_ from the object name"""
        self.getObjects(selectMethod) # initialize the objectList
        print(self.objectList)
        for obj in self.objectList:
            try:
                if "pasted__" in obj:
                    pasted = "pasted__"
                elif "pasted_" in obj:
                    pasted = "pasted_"
                elif "pasted" in obj:
                    pasted = "pasted"
                else:
                    return
                cmds.rename(obj, obj.split("|")[-1].replace(pasted, ""))
            except RuntimeError:
                pass

    def removeNamespace(self, selectMethod):
        """Removes the namespace from selection"""
        self.getObjects(selectMethod)  # initialize the objectList
        for i in self.objectList:
            try:
                cmds.rename(i, i.split(":")[-1])
            except IndexError and RuntimeError:
                pass

    def addSuffix(self, selectMethod, suffix):
        self.getObjects(selectMethod)  # initialize the objectList
        for obj in self.objectList:
            try:
                # name = obj if not "|" in obj else obj.split("|")[-1]
                name = obj.split("|")[-1]
                cmds.rename(obj, "{0}{1}".format(name, suffix))
            except RuntimeError:
                pass

    def addPrefix(self, selectMethod, prefix):
        self.getObjects(selectMethod)  # initialize the objectList
        for obj in self.objectList:
            try:
                # name = obj if not "|" in obj else obj.split("|")[-1]
                name = obj.split("|")[-1]
                cmds.rename(obj, "{0}{1}".format(prefix, name))
            except RuntimeError:
                pass

    def rename(self, selectMethod, newName):
        self.getObjects(selectMethod)  # initialize the objectList

        # get the hashtags from the name
        split = newName.split("#")
        newName = split[0]
        padding = abs(len(split)-1)

        counter = 1
        for i in self.objectList:
            try:
                cmds.rename(i, "{0}{1}".format(newName, str(counter).zfill(padding)))
                counter += 1
            except RuntimeError:
                pass

    def replace(self, selectMethod, A, B):
        self.getObjects(selectMethod)  # initialize the objectList

        for obj in self.objectList:
            try:
                # name = obj if not "|" in obj else obj.split("|")[-1]
                name = obj.split("|")[-1]
                cmds.rename(obj, name.replace(A, B))
            except RuntimeError:
                pass

class MainUI(QtWidgets.QDialog):
    def __init__(self):
        for entry in QtWidgets.QApplication.allWidgets():
            try:
                if entry.objectName() == WINDOW_NAME:
                    entry.close()
            except (AttributeError, TypeError):
                pass
        parent = getMayaMainWindow()
        super(MainUI, self).__init__(parent=parent)

        self.setWindowTitle(WINDOW_NAME)
        self.setObjectName(WINDOW_NAME)
        self.resize(228, 251)
        self.buildUI()
        self.renamer = Renamer()


    def buildUI(self):
        master_vlay = QtWidgets.QVBoxLayout(self)

        radibuttons_hlay = QtWidgets.QHBoxLayout()
        master_vlay.addLayout(radibuttons_hlay)

        self.hierarchy_rb = QtWidgets.QRadioButton(self)
        self.hierarchy_rb.setText("Hierarcy")
        radibuttons_hlay.addWidget(self.hierarchy_rb)

        self.selection_rb = QtWidgets.QRadioButton(self)
        self.selection_rb.setText("Selection")
        radibuttons_hlay.addWidget(self.selection_rb)
        self.selection_rb.setChecked(True)

        self.all_rb = QtWidgets.QRadioButton(self)
        self.all_rb.setText("All")
        radibuttons_hlay.addWidget(self.all_rb)

        self.remove_pasted_pb = QtWidgets.QPushButton(self)
        self.remove_pasted_pb.setText("Remove _pasted")
        master_vlay.addWidget(self.remove_pasted_pb)

        self.remove_namespace_pb = QtWidgets.QPushButton(self)
        self.remove_namespace_pb.setText("Remove namespace")
        master_vlay.addWidget(self.remove_namespace_pb)

        left_right_hlay = QtWidgets.QHBoxLayout()
        master_vlay.addLayout(left_right_hlay)

        self.add_r_pb = QtWidgets.QPushButton(self)
        self.add_r_pb.setText("Add \'R\'")
        left_right_hlay.addWidget(self.add_r_pb)

        self.add_l_pb = QtWidgets.QPushButton(self)
        self.add_l_pb.setText("Add \'L\'")
        left_right_hlay.addWidget(self.add_l_pb)

        add_suffix_hlay = QtWidgets.QHBoxLayout()
        master_vlay.addLayout(add_suffix_hlay)

        self.add_suffix_pb = QtWidgets.QPushButton(self)
        self.add_suffix_pb.setText("Add Suffix")
        add_suffix_hlay.addWidget(self.add_suffix_pb)

        self.add_suffix_le = QtWidgets.QLineEdit(self)
        add_suffix_hlay.addWidget(self.add_suffix_le)

        add_prefix_hlay = QtWidgets.QHBoxLayout()
        master_vlay.addLayout(add_prefix_hlay)

        self.add_prefix_le = QtWidgets.QLineEdit(self)
        add_prefix_hlay.addWidget(self.add_prefix_le)

        self.add_prefix_pb = QtWidgets.QPushButton(self)
        self.add_prefix_pb.setText("Add Prefix")
        add_prefix_hlay.addWidget(self.add_prefix_pb)

        rename_hlay = QtWidgets.QHBoxLayout()
        master_vlay.addLayout(rename_hlay)

        self.rename_pb = QtWidgets.QPushButton(self)
        self.rename_pb.setText("Rename")
        rename_hlay.addWidget(self.rename_pb)

        self.rename_le = QtWidgets.QLineEdit(self)
        self.rename_le.setPlaceholderText("use \'#\' for numeration")
        rename_hlay.addWidget(self.rename_le)

        replace_hlay = QtWidgets.QHBoxLayout()
        master_vlay.addLayout(replace_hlay)

        self.replace_pb = QtWidgets.QPushButton(self)
        self.replace_pb.setText("Replace")
        replace_hlay.addWidget(self.replace_pb)

        self.replace_A_le = QtWidgets.QLineEdit(self)
        self.replace_A_le.setPlaceholderText("A")
        replace_hlay.addWidget(self.replace_A_le)

        self.replace_B_le = QtWidgets.QLineEdit(self)
        self.replace_B_le.setPlaceholderText("B")
        replace_hlay.addWidget(self.replace_B_le)

        #################
        #### SIGNALS ####
        #################

        self.remove_pasted_pb.clicked.connect(lambda: self.buttonPressed("removePasted"))
        self.remove_namespace_pb.clicked.connect(lambda: self.buttonPressed("removeSemi"))
        self.add_l_pb.clicked.connect(lambda: self.buttonPressed("addLeft"))
        self.add_r_pb.clicked.connect(lambda: self.buttonPressed("addRight"))
        self.add_suffix_pb.clicked.connect(lambda: self.buttonPressed("addSuffix"))
        self.add_prefix_pb.clicked.connect(lambda: self.buttonPressed("addPrefix"))
        self.rename_pb.clicked.connect(lambda: self.buttonPressed("rename"))
        self.replace_pb.clicked.connect(lambda: self.buttonPressed("replace"))

    @undo
    def buttonPressed(self, command):
        if self.selection_rb.isChecked():
            method=0
        elif self.hierarchy_rb.isChecked():
            method=1
        elif self.all_rb.isChecked():
            method=2
        else:
            FEEDBACK.throw_error("Method cannot defined")
            return

        if command == "removePasted":
            self.renamer.removePasted(method)
        elif command == "removeSemi":
            self.renamer.removeNamespace(method)
        elif command == "addRight":
            self.renamer.addSuffix(method, "_R")
        elif command == "addLeft":
            self.renamer.addSuffix(method, "_L")
        elif command == "addSuffix":
            self.renamer.addSuffix(method, str(self.add_suffix_le.text()))
        elif command == "addPrefix":
            self.renamer.addPrefix(method, str(self.add_prefix_le.text()))
        elif command == "rename":
            self.renamer.rename(method, str(self.rename_le.text()))
        elif command == "replace":
            self.renamer.replace(method, str(self.replace_A_le.text()), str(self.replace_B_le.text()))

