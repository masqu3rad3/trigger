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
            # self.objectList = cmds.ls(sl=True, long=True)
            self.objectList = [Node(node=x) for x in cmds.ls(sl=True, long=True)]
        if method == 1: # Hierarchy
            relatives = cmds.listRelatives(cmds.ls(sl=True), c=True, ad=True, f=True) or []
            self.objectList = [Node(node=x) for x in relatives + cmds.ls(sl=True)]
        if method == 2: # Everything
            # self.objectList = cmds.ls(long=True)
            # self.objectList = cmds.ls()
            self.objectList = [Node(node=x) for x in cmds.ls()]

        # sort the list to iterate transforms first
        # self.objectList = sorted(object_list, key=lambda x: cmds.objectType(x) == "transform")

    def removePasted(self, selectMethod):
        """Removes pasted_ from the object name"""
        self.getObjects(selectMethod) # initialize the objectList
        for obj in self.objectList:
            if "pasted__" in obj:
                pasted = "pasted__"
            elif "pasted_" in obj:
                pasted = "pasted_"
            elif "pasted" in obj:
                pasted = "pasted"
            else:
                continue
            new_name = obj.get_base().replace(pasted, "")
            obj.set_new_name(new_name)
            # cmds.rename(obj, obj.split("|")[-1].replace(pasted, ""))

        for obj in reversed((sorted(self.objectList))):
            obj.execute_new_name()

    def removeNamespace(self, selectMethod):
        """Removes the namespace from selection"""
        self.getObjects(selectMethod)  # initialize the objectList
        for obj in self.objectList:
            obj.remove_namespace()

    def addSuffix(self, selectMethod, suffix):
        self.getObjects(selectMethod)  # initialize the objectList
        for obj in self.objectList:
            name = obj.get_base()
            obj.set_new_name("{0}{1}".format(name, suffix))

        for obj in reversed((sorted(self.objectList))):
            obj.execute_new_name()

    def addPrefix(self, selectMethod, prefix):
        self.getObjects(selectMethod)  # initialize the objectList

        for obj in self.objectList:
            name = obj.get_base()
            obj.set_new_name("{0}{1}".format(prefix, name))

        for obj in reversed((sorted(self.objectList))):
            obj.execute_new_name()

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

        for nmb, obj in enumerate(self.objectList):
            instance = str(nmb+1).zfill(padding) if padding else ""
            # print(instance, obj)
            obj.set_new_name("{0}{1}{2}".format(pre, instance, post))
            # obj.rename("{0}{1}{2}".format(pre, instance, post))

        for obj in list(reversed((sorted(self.objectList)))):
            obj.execute_new_name()


    def replace(self, selectMethod, A, B):
        self.getObjects(selectMethod)  # initialize the objectList

        for obj in self.objectList:
            name = obj.get_base()
            obj.rename(name.replace(A, B))

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
    def __init__(self, node=None):
        super(Node, self).__init__()
        self._dag_path = ""
        self._new_name = ""
        if node:
            self.update_dag(node)

    def update_dag(self, new_path):
        node_list = cmds.ls(new_path, l=True)
        if not node_list:
            raise Exception("Node does not exist")
        self._dag_path = node_list[0]

    def get_base(self):
        return self._dag_path.split("|")[-1]

    def get_dag(self):
        return self._dag_path

    def set_new_name(self, new_name):
        self._new_name = new_name

    def execute_new_name(self):
        if self._new_name:
            self.rename(self._new_name)

    def rename(self, new_name):
        try:
            self.update_dag(cmds.rename(self._dag_path, self.unique(new_name), ignoreShape=True))
        except RuntimeError:
            cmds.warning("%s cannot renamed" % new_name)
            self._rename_children(new_name)


    def _rename_children(self, obj):
        if not cmds.objExists(obj):
            return
        shapes = cmds.listRelatives(obj, children=True, fullPath=True, type="shape")
        if shapes:
            for c in shapes:
                try:
                    cmds.rename(c, self.unique("%sShape" %obj))
                except RuntimeError:
                    cmds.warning("%s cannot renamed" % obj)

    def remove_namespace(self):
        if ':' in self._dag_path:
            ns = self._dag_path.rsplit(':')[0]
            ns = ns.split("|")[-1]
        else:
            return
        cmds.namespace(rm=ns, mnr=True, f=True)

    def __str__(self):
        return self.get_dag()

    def __repr__(self):
        return self.get_dag()

    @staticmethod
    def unique(name):
        """Searches the scene for match and returns a unique name for given name"""

        baseName = name
        idcounter = 0
        while cmds.objExists(name):
            is_digits = re.search('.*?([0-9]+)$', baseName.split(".")[0])
            if not is_digits:
                name = "%s%s" % (baseName, str(idcounter + 1))
            else:
                digit = is_digits.groups()[0] # as str
                padding = len(digit)
                stripped_name = baseName.replace(digit, "")
                name = "%s%s" % (stripped_name, str(idcounter+int(digit)).zfill(padding))
            # name = "%s%s" % (baseName, str(idcounter + 1))
            idcounter += 1
        return name

    # this is for python 2.x
    def __cmp__(self, other):
        print(self._dag_path, other._dag_path)
        if self._dag_path < other._dag_path:
            return -1  # <--------- yay!
        elif self._dag_path > other._dag_path:
            return 1
        else:
            return 0

    # these are for python 3.x
    def __lt__(self, other):
        return self._dag_path < other._dag_path

    def __gt__(self, other):
        return self._dag_path > other._dag_path

    def __eq__(self, other):
        return self._dag_path == other._dag_path



