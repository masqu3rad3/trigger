#
# Renamer version 1.0

# import pymel.core as pm
import sys
import maya.cmds as cmds

from trigger.ui import Qt
from trigger.ui.Qt import QtWidgets, QtCore, QtGui
from maya import OpenMayaUI as omui

if Qt.__binding__ == "PySide":
    from shiboken import wrapInstance
    from trigger.ui.Qt.QtCore import Signal
elif Qt.__binding__.startswith('PyQt'):
    from sip import wrapinstance as wrapInstance
    from trigger.ui.Qt.QtCore import pyqtSignal as Signal
else:
    from shiboken2 import wrapInstance
    from trigger.ui.Qt.QtCore import Signal

from trigger.library import functions
from trigger.core.undo_dec import undo
from trigger.core import feedback

FEEDBACK = feedback.Feedback(__name__)


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

# def uniqueList(seq, idfun=None):
#    # order preserving
#    if idfun is None:
#        def idfun(x): return x
#    seen = {}
#    result = []
#    for item in seq:
#        marker = idfun(item)
#        # in old Python versions:
#        # if seen.has_key(marker)
#        # but in new ones:
#        if marker in seen: continue
#        seen[marker] = 1
#        result.append(item)
#    return result

# def uniqueList(seq): # Dave Kirby
#     # Order preserving
#     seen = set()
#     return [x for x in seq if x not in seen and not seen.add(x)]

class Renamer(object):
    def __init__(self):
        super(Renamer, self).__init__()
        self.objectList = []

    def getObjects(self, method):
        if method == 0: # selected objects
            # self.objectList = pm.ls(sl=True)
            self.objectList = cmds.ls(sl=True)
        if method == 1: # Hierarchy
            self.objectList = []
            for obj in cmds.ls(sl=True):
                self.objectList.append(obj)
                self.objectList += (cmds.listRelatives(obj, ad=True, c=True))
            self.objectList = functions.uniqueList(self.objectList)
        if method == 2: # Everything
            self.objectList = cmds.ls()


    def removePasted(self, selectMethod):
        self.getObjects(selectMethod) # initialize the objectList
        for i in self.objectList:
            try:
                cmds.rename(i, i.replace("pasted", ""))
                # i.rename(i.name().replace("pasted__", ""))
            except RuntimeError:
                pass

    def removeSemi(self, selectMethod):
        self.getObjects(selectMethod)  # initialize the objectList
        for i in self.objectList:
            try:
                cmds.rename(i, i.split(":")[-1])
                # i.rename(i.name().split(":")[-1])
            except IndexError and RuntimeError:
                pass

    def addRight(self, selectMethod):
        self.getObjects(selectMethod)  # initialize the objectList
        for i in self.objectList:
            try:
                cmds.rename(i, "{0}_RIGHT".format(i))
                # i.rename("{0}_RIGHT".format(i.name()))
            except RuntimeError:
                pass

    def addLeft(self, selectMethod):
        self.getObjects(selectMethod)  # initialize the objectList
        for i in self.objectList:
            try:
                cmds.rename(i, "{0}_LEFT".format(i))
            except RuntimeError:
                pass

    def addSuffix(self, selectMethod, suffix):
        self.getObjects(selectMethod)  # initialize the objectList
        for i in self.objectList:
            try:
                cmds.rename(i, "{0}{1}".format(i,suffix))
                # i.rename("{0}{1}".format(i.name(),suffix))
            except RuntimeError:
                pass

    def addPrefix(self, selectMethod, prefix):
        self.getObjects(selectMethod)  # initialize the objectList
        for i in self.objectList:
            try:
                cmds.rename(i, "{0}{1}".format(prefix, i))
                # i.rename("{0}{1}".format(prefix, i.name()))
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
                # i.rename("{0}{1}".format(newName, str(counter).zfill(padding)))
                counter += 1
            except RuntimeError:
                pass

    def replace(self, selectMethod, A, B):
        self.getObjects(selectMethod)  # initialize the objectList

        for i in self.objectList:
            try:
                cmds.rename(i, i.replace(A, B))
                # i.name().replace(A, B)
                # i.rename(i.name().replace(A, B))
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

    def old_buildUI(self):

        self.setObjectName((WINDOW_NAME))
        self.resize(270, 341)
        self.setToolTip((""))
        self.setStatusTip((""))
        self.setWhatsThis((""))
        self.setAccessibleName((""))
        self.setAccessibleDescription((""))
        self.setWindowFilePath((""))

        self.selected_radioButton = QtWidgets.QRadioButton(self)
        self.selected_radioButton.setGeometry(QtCore.QRect(20, 20, 71, 20))
        self.selected_radioButton.setToolTip((""))
        self.selected_radioButton.setStatusTip((""))
        self.selected_radioButton.setWhatsThis((""))
        self.selected_radioButton.setAccessibleName((""))
        self.selected_radioButton.setAccessibleDescription((""))
        self.selected_radioButton.setText(("Selected"))
        self.selected_radioButton.setChecked(True)
        self.selected_radioButton.setObjectName(("selected_radioButton"))

        self.selected_radioButton_2 = QtWidgets.QRadioButton(self)
        self.selected_radioButton_2.setGeometry(QtCore.QRect(110, 20, 71, 20))
        self.selected_radioButton_2.setToolTip((""))
        self.selected_radioButton_2.setStatusTip((""))
        self.selected_radioButton_2.setWhatsThis((""))
        self.selected_radioButton_2.setAccessibleName((""))
        self.selected_radioButton_2.setAccessibleDescription((""))
        self.selected_radioButton_2.setText(("Hierarchy"))
        self.selected_radioButton_2.setObjectName(("selected_radioButton_2"))

        self.selected_radioButton_3 = QtWidgets.QRadioButton(self)
        self.selected_radioButton_3.setGeometry(QtCore.QRect(210, 20, 41, 20))
        self.selected_radioButton_3.setToolTip((""))
        self.selected_radioButton_3.setStatusTip((""))
        self.selected_radioButton_3.setWhatsThis((""))
        self.selected_radioButton_3.setAccessibleName((""))
        self.selected_radioButton_3.setAccessibleDescription((""))
        self.selected_radioButton_3.setText(("All"))
        self.selected_radioButton_3.setObjectName(("selected_radioButton_3"))

        self.removepasted_pushButton = QtWidgets.QPushButton(self)
        self.removepasted_pushButton.setGeometry(QtCore.QRect(20, 50, 231, 31))
        self.removepasted_pushButton.setToolTip((""))
        self.removepasted_pushButton.setStatusTip((""))
        self.removepasted_pushButton.setWhatsThis((""))
        self.removepasted_pushButton.setAccessibleName((""))
        self.removepasted_pushButton.setAccessibleDescription((""))
        self.removepasted_pushButton.setText(("Remove \"_pasted\""))
        self.removepasted_pushButton.setObjectName(("removepasted_pushButton"))
        self.removepasted_pushButton.setFocus()

        self.removesemi_pushButton = QtWidgets.QPushButton(self)
        self.removesemi_pushButton.setGeometry(QtCore.QRect(20, 90, 231, 31))
        self.removesemi_pushButton.setToolTip((""))
        self.removesemi_pushButton.setStatusTip((""))
        self.removesemi_pushButton.setWhatsThis((""))
        self.removesemi_pushButton.setAccessibleName((""))
        self.removesemi_pushButton.setAccessibleDescription((""))
        self.removesemi_pushButton.setText(("Remove \":\""))
        self.removesemi_pushButton.setObjectName(("removesemi_pushButton"))

        self.addright_pushButton = QtWidgets.QPushButton(self)
        self.addright_pushButton.setGeometry(QtCore.QRect(20, 130, 91, 31))
        self.addright_pushButton.setToolTip((""))
        self.addright_pushButton.setStatusTip((""))
        self.addright_pushButton.setWhatsThis((""))
        self.addright_pushButton.setAccessibleName((""))
        self.addright_pushButton.setAccessibleDescription((""))
        self.addright_pushButton.setText(("Add \"RIGHT\""))
        self.addright_pushButton.setObjectName(("addright_pushButton"))

        self.addleft_pushButton = QtWidgets.QPushButton(self)
        self.addleft_pushButton.setGeometry(QtCore.QRect(160, 130, 91, 31))
        self.addleft_pushButton.setToolTip((""))
        self.addleft_pushButton.setStatusTip((""))
        self.addleft_pushButton.setWhatsThis((""))
        self.addleft_pushButton.setAccessibleName((""))
        self.addleft_pushButton.setAccessibleDescription((""))
        self.addleft_pushButton.setText(("Add \"LEFT\""))
        self.addleft_pushButton.setObjectName(("addleft_pushButton"))

        self.addsuffix_pushButton = QtWidgets.QPushButton(self)
        self.addsuffix_pushButton.setGeometry(QtCore.QRect(180, 170, 71, 31))
        self.addsuffix_pushButton.setToolTip((""))
        self.addsuffix_pushButton.setStatusTip((""))
        self.addsuffix_pushButton.setWhatsThis((""))
        self.addsuffix_pushButton.setAccessibleName((""))
        self.addsuffix_pushButton.setAccessibleDescription((""))
        self.addsuffix_pushButton.setText(("Add Suffix"))
        self.addsuffix_pushButton.setObjectName(("addsuffix_pushButton"))

        self.addsuffix_lineEdit = QtWidgets.QLineEdit(self)
        self.addsuffix_lineEdit.setGeometry(QtCore.QRect(20, 170, 151, 31))
        self.addsuffix_lineEdit.setToolTip((""))
        self.addsuffix_lineEdit.setStatusTip((""))
        self.addsuffix_lineEdit.setWhatsThis((""))
        self.addsuffix_lineEdit.setAccessibleName((""))
        self.addsuffix_lineEdit.setAccessibleDescription((""))
        self.addsuffix_lineEdit.setText((""))
        self.addsuffix_lineEdit.setAlignment(QtCore.Qt.AlignCenter)
        self.addsuffix_lineEdit.setPlaceholderText(("Object_Name_<suffix>"))
        self.addsuffix_lineEdit.setObjectName(("addsuffix_lineEdit"))

        self.addprefix_pushButton = QtWidgets.QPushButton(self)
        self.addprefix_pushButton.setGeometry(QtCore.QRect(20, 210, 71, 31))
        self.addprefix_pushButton.setToolTip((""))
        self.addprefix_pushButton.setStatusTip((""))
        self.addprefix_pushButton.setWhatsThis((""))
        self.addprefix_pushButton.setAccessibleName((""))
        self.addprefix_pushButton.setAccessibleDescription((""))
        self.addprefix_pushButton.setText(("Add Prefix"))
        self.addprefix_pushButton.setObjectName(("addprefix_pushButton"))

        self.addprefix_lineEdit = QtWidgets.QLineEdit(self)
        self.addprefix_lineEdit.setGeometry(QtCore.QRect(100, 210, 151, 31))
        self.addprefix_lineEdit.setToolTip((""))
        self.addprefix_lineEdit.setStatusTip((""))
        self.addprefix_lineEdit.setWhatsThis((""))
        self.addprefix_lineEdit.setAccessibleName((""))
        self.addprefix_lineEdit.setAccessibleDescription((""))
        self.addprefix_lineEdit.setText((""))
        self.addprefix_lineEdit.setAlignment(QtCore.Qt.AlignCenter)
        self.addprefix_lineEdit.setPlaceholderText(("<prefix>_Object_Name"))
        self.addprefix_lineEdit.setObjectName(("addprefix_lineEdit"))

        self.rename_pushButton = QtWidgets.QPushButton(self)
        self.rename_pushButton.setGeometry(QtCore.QRect(20, 250, 71, 31))
        self.rename_pushButton.setToolTip((""))
        self.rename_pushButton.setStatusTip((""))
        self.rename_pushButton.setWhatsThis((""))
        self.rename_pushButton.setAccessibleName((""))
        self.rename_pushButton.setAccessibleDescription((""))
        self.rename_pushButton.setText(("Rename"))
        self.rename_pushButton.setObjectName(("rename_pushButton"))

        self.rename_lineEdit = QtWidgets.QLineEdit(self)
        self.rename_lineEdit.setGeometry(QtCore.QRect(100, 250, 151, 31))
        self.rename_lineEdit.setToolTip((""))
        self.rename_lineEdit.setStatusTip((""))
        self.rename_lineEdit.setWhatsThis((""))
        self.rename_lineEdit.setAccessibleName((""))
        self.rename_lineEdit.setAccessibleDescription((""))
        self.rename_lineEdit.setText((""))
        self.rename_lineEdit.setAlignment(QtCore.Qt.AlignCenter)
        self.rename_lineEdit.setPlaceholderText(("new_object_name_####"))
        self.rename_lineEdit.setObjectName(("rename_lineEdit"))

        self.replace_pushButton = QtWidgets.QPushButton(self)
        self.replace_pushButton.setGeometry(QtCore.QRect(20, 290, 71, 31))
        self.replace_pushButton.setToolTip((""))
        self.replace_pushButton.setStatusTip((""))
        self.replace_pushButton.setWhatsThis((""))
        self.replace_pushButton.setAccessibleName((""))
        self.replace_pushButton.setAccessibleDescription((""))
        self.replace_pushButton.setText(("Replace"))
        self.replace_pushButton.setObjectName(("replace_pushButton"))

        self.replace_a_lineEdit = QtWidgets.QLineEdit(self)
        self.replace_a_lineEdit.setGeometry(QtCore.QRect(100, 290, 71, 31))
        self.replace_a_lineEdit.setToolTip((""))
        self.replace_a_lineEdit.setStatusTip((""))
        self.replace_a_lineEdit.setWhatsThis((""))
        self.replace_a_lineEdit.setAccessibleName((""))
        self.replace_a_lineEdit.setAccessibleDescription((""))
        self.replace_a_lineEdit.setText((""))
        self.replace_a_lineEdit.setAlignment(QtCore.Qt.AlignCenter)
        self.replace_a_lineEdit.setPlaceholderText(("A"))
        self.replace_a_lineEdit.setObjectName(("replace_a_lineEdit"))

        self.replace_b_lineEdit = QtWidgets.QLineEdit(self)
        self.replace_b_lineEdit.setGeometry(QtCore.QRect(180, 290, 71, 31))
        self.replace_b_lineEdit.setToolTip((""))
        self.replace_b_lineEdit.setStatusTip((""))
        self.replace_b_lineEdit.setWhatsThis((""))
        self.replace_b_lineEdit.setAccessibleName((""))
        self.replace_b_lineEdit.setAccessibleDescription((""))
        self.replace_b_lineEdit.setText((""))
        self.replace_b_lineEdit.setAlignment(QtCore.Qt.AlignCenter)
        self.replace_b_lineEdit.setPlaceholderText(("B"))
        self.replace_b_lineEdit.setObjectName(("replace_b_lineEdit"))

        self.removepasted_pushButton.clicked.connect(lambda: self.buttonPressed("removePasted"))
        self.removesemi_pushButton.clicked.connect(lambda: self.buttonPressed("removeSemi"))
        self.addleft_pushButton.clicked.connect(lambda: self.buttonPressed("addLeft"))
        self.addright_pushButton.clicked.connect(lambda: self.buttonPressed("addRight"))
        self.addsuffix_pushButton.clicked.connect(lambda: self.buttonPressed("addSuffix"))
        self.addprefix_pushButton.clicked.connect(lambda: self.buttonPressed("addPrefix"))
        self.rename_pushButton.clicked.connect(lambda: self.buttonPressed("rename"))
        self.replace_pushButton.clicked.connect(lambda: self.buttonPressed("replace"))

        # QtCore.QMetaObject.connectSlotsByName(namingtools_Dialog)
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
            self.renamer.removeSemi(method)
        elif command == "addRight":
            self.renamer.addRight(method)
        elif command == "addLeft":
            self.renamer.addLeft(method)
        elif command == "addSuffix":
            self.renamer.addSuffix(method, str(self.add_suffix_le.text()))
        elif command == "addPrefix":
            self.renamer.addPrefix(method, str(self.add_prefix_le.text()))
        elif command == "rename":
            self.renamer.rename(method, str(self.rename_le.text()))
        elif command == "replace":
            self.renamer.replace(method, str(self.replace_A_le.text()), str(self.replace_B_le.text()))

    # def testPop(self):
    #     exportWindow, ok = QtWidgets.QInputDialog.getItem(self, 'Text Input Dialog',
    #                                                       'SAVE BEFORE PROCEED\n\nANY UNSAVED WORK WILL BE LOST\n\nEnter Asset Name:')
    #     if ok:
    #         print "popped"
    #
    # def setColor(self):
    #     color = QtWidgets.QColorDialog.getColor(QtCore.Qt.green, self)
    #     if color.isValid():
    #         print(color.name())
    #         print(QtGui.QPalette(color))
    #         print color
    #
    # def wheelEvent(self, event):
    #     # print event.delta()
    #     t =(math.pow(1.2, event.delta() / 120.0))
    #     if event.modifiers() == QtCore.Qt.ControlModifier:
    #         print t


# testUI().show()
