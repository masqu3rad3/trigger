#
# Renamer version 1.1

import re

import maya.cmds as cmds

from trigger.ui.qtmaya import getMayaMainWindow
from trigger.ui.Qt import QtWidgets

from trigger.core.decorators import undo
from trigger.core import logger

log = logger.Logger(__name__)
WINDOW_NAME = "Tik_Renamer"

class Renamer(object):
    def __init__(self):
        super(Renamer, self).__init__()
        self.objectList = []

    def getObjects(self, method):
        """returns objects according to the method"""
        if method == 0: # selected objects
            self.objectList = cmds.ls(sl=True, long=True)
        if method == 1: # Hierarchy
            self.objectList = cmds.listRelatives(cmds.ls(sl=True), c=True, ad=True, f=True) + cmds.ls(sl=True)
        if method == 2: # Everything
            # self.objectList = cmds.ls(long=True)
            self.objectList = cmds.ls()

        # sort the list to iterate transforms first
        # self.objectList = sorted(object_list, key=lambda x: cmds.objectType(x) == "transform")

    def removePasted(self, selectMethod):
        """Removes pasted_ from the object name"""
        self.getObjects(selectMethod) # initialize the objectList
        for obj in self.objectList:
            try:
                if "pasted__" in obj:
                    pasted = "pasted__"
                elif "pasted_" in obj:
                    pasted = "pasted_"
                elif "pasted" in obj:
                    pasted = "pasted"
                else:
                    continue
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

    def rename(self, selectMethod, new_name):
        self.getObjects(selectMethod)  # initialize the objectList

        # get the hashtags from the name
        pat = r'[#]'
        pat_iters = list(re.finditer(pat, new_name))
        padding = len(pat_iters) or 0

        if pat_iters:
            pre = new_name[0:pat_iters[0].start()]
            post = new_name[pat_iters[-1].end():-1]
        else:
            pre = new_name
            post = ""

        count = 1
        for obj in self.objectList:
            instance = str(count).zfill(padding) if padding else ""
            # try:
            print(obj, pre, instance, post)
            renamed = cmds.rename(obj, "{0}{1}{2}".format(pre, instance, post), ignoreShape=True)
            self._rename_children(renamed)
            count += 1
            # except RuntimeError:
            #     continue

    def _rename_children(self, obj):
        children = cmds.listRelatives(obj, children=True, fullPath=True, type="shape")
        if children:
            for c in children:
                cmds.rename(c, "%sShape" %obj)


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
        self.remove_pasted_pb.setText("Remove pasted tag")
        master_vlay.addWidget(self.remove_pasted_pb)

        self.remove_namespace_pb = QtWidgets.QPushButton(self)
        self.remove_namespace_pb.setText("Remove namespace")
        master_vlay.addWidget(self.remove_namespace_pb)

        left_right_hlay = QtWidgets.QHBoxLayout()
        master_vlay.addLayout(left_right_hlay)

        self.add_r_pb = QtWidgets.QPushButton(self, text="Add")
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
            log.throw_error("Method cannot defined")
            return

        if command == "removePasted":
            self.renamer.removePasted(method)
        elif command == "removeSemi":
            self.renamer.removeNamespace(method)
        elif command == "addRight":
            self.renamer.addPrefix(method, "R_")
        elif command == "addLeft":
            self.renamer.addPrefix(method, "L_")
        elif command == "addSuffix":
            self.renamer.addSuffix(method, str(self.add_suffix_le.text()))
        elif command == "addPrefix":
            self.renamer.addPrefix(method, str(self.add_prefix_le.text()))
        elif command == "rename":
            self.renamer.rename(method, str(self.rename_le.text()))
        elif command == "replace":
            self.renamer.replace(method, str(self.replace_A_le.text()), str(self.replace_B_le.text()))

class Node(object):
    dag_path = ""
    def __init__(self, node=None):
        super(Node, self).__init__()
        if node:
            self.update_dag(node)

    @classmethod
    def update_dag(cls, new_path):
        node_list = cmds.ls(new_path, l=True)
        if not node_list:
            raise Exception("Node does not exist")
        cls.dag_path = node_list[0]

    @classmethod
    def get_dag(cls):
        return cls.dag_path

    @classmethod
    def rename(cls, new_name):
        cls.update_dag(cmds.rename(cls.dag_path, new_name, ignoreShape=True))
        cls._rename_children(new_name)

    @staticmethod
    def _rename_children(obj):
        shapes = cmds.listRelatives(obj, children=True, fullPath=True, type="shape")
        if shapes:
            for c in shapes:
                cmds.rename(c, "%sShape" %obj)

    def __str__(self):
        return self.get_dag()

    def __repr__(self):
        return self.get_dag()
