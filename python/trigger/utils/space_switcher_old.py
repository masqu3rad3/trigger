import pymel.core as pm
import trigger.library.functions as extra
from trigger.ui import Qt
from trigger.ui.Qt import QtWidgets, QtCore
from maya import OpenMayaUI as omui




if Qt.__binding__ == "PySide":
    from shiboken import wrapInstance
elif Qt.__binding__.startswith('PyQt'):
    from sip import wrapinstance as wrapInstance
else:
    from shiboken2 import wrapInstance

windowName = "AnchorMaker"

def getMayaMainWindow():
    """
    Gets the memory adress of the main window to connect Qt dialog to it.
    Returns:
        (long) Memory Adress
    """
    win = omui.MQtUtil_mainWindow()
    ptr = wrapInstance(long(win), QtWidgets.QMainWindow)
    return ptr

def spaceSwitcher(node, targetList, overrideExisting=False, mode="parent", defaultVal=1, listException=None):

    """
    Creates the space switch attributes between selected node (controller) and targets.
    Args:
        node: (single object) Object which anchor space will be switched. Mostly a controller curve.
        targetList: (list of objects) The node will be anchored between these targets.
        overrideExisting: (bool) If True, the existing attributes on the node with the same name will be deleted and recreated. Default False
        mode: (String) The type of the constrain that will be applied to the node. Valid options are "parent", "point and "orient". Default "parent"
        defaultVal: (integer) Default value for the new Switch attribute. If it is out of range, 1 will be used. default: 1.
        listException: (List) If this argument is not none, the given elements in the list will be removed from the targetList, in case it is in the list of course.
    Returns: None

    """

    anchorPoses = list(targetList)
    if anchorPoses.__contains__(node):
        # if targetList contains the node itself, remove it
        anchorPoses.remove(node)
    if anchorPoses == []:
        pm.error("target list is empty or no valid targets")
    if listException != None:
        for x in listException:
            if anchorPoses.__contains__(x):
                anchorPoses.remove(x)
    if len(anchorPoses) > defaultVal:
        defaultVal = 1
    modeList = ("parent", "point", "orient")
    if not modeList.__contains__(mode):
        pm.error("unknown mode flag. Valid mode flags are 'parent', 'point' and 'orient' ")
    # create the enumerator list
    enumFlag = "worldSpace:"
    for enum in range(0, len(anchorPoses)):
        cur = str(anchorPoses[enum])
        cur = cur.replace("cont_", "")
        enumFlag += "%s:" % cur

    # # check if the attribute exists
    if pm.attributeQuery(mode + "Switch", node=node, exists=True):
        if overrideExisting:
            pm.deleteAttr("{0}.{1}Switch".format(node, mode))
        else:
            pm.error("Switch Attribute already exists. Use overrideExisting=True to delete the old")
    pm.addAttr(node, at="enum", k=True, shortName=mode + "Switch", longName=mode + "_Switch", en=enumFlag, defaultValue=defaultVal)
    driver = "%s.%sSwitch" % (node, mode)

    switchGrp = extra.createUpGrp(node, "{0}SW".format(mode))

    # # Upgrp
    # grpName = (node.name() + "_" + mode + "SW")
    # switchGrp = pm.group(em=True, name=grpName)
    #
    # # align the new created empty group to the selected object
    # pointCon = pm.parentConstraint(node, switchGrp, mo=False)
    # pm.delete(pointCon)
    #
    # # check if the target object has a parent
    # originalParent = pm.listRelatives(node, p=True)
    # if (len(originalParent) > 0):
    #     pm.parent(switchGrp, originalParent[0])
    #
    # pm.parent(node, switchGrp)

    # switchGrp=createUpGrp(node, (mode+"SW"))
    if mode == "parent":
        con = pm.parentConstraint(anchorPoses, switchGrp, mo=True)
    elif mode == "point":
        con = pm.parentConstraint(anchorPoses, switchGrp, sr=("x", "y", "z"), mo=True)
    elif mode == "orient":
        con = pm.parentConstraint(anchorPoses, switchGrp, st=("x", "y", "z"), mo=True)

    ## make worldSpace driven key (all zero)
    for i in range(0, len(anchorPoses)):
        attr = "{0}W{1}".format(anchorPoses[i], i)
        pm.setDrivenKeyframe(con, cd=driver, at=attr, dv=0.0, v=0.0)

    # # loop for each DRIVER POSITION
    for dPos in range(0, len(anchorPoses)):
        # # loop for each target at parent constraint
        for t in range(0, len(anchorPoses)):
            attr = "{0}W{1}".format(anchorPoses[t], t)
            # # if driver value matches the attribute, make the value 1, else 0
            if t == (dPos):
                value = 1
            else:
                value = 0
            pm.setDrivenKeyframe(con, cd=driver, at=attr, dv=float(dPos + 1), v=float(value))

def removeAnchor(node):
    """
    Removes the anchors created with the spaceswitcher method
    Args:
        node: (PyNode Object) A Single object (mostly a controller curve) which the anchors will be removed

    Returns:

    """
    userAtts = pm.listAttr(node, ud=True)
    switchAtts = [att for att in userAtts if "_Switch" in att]
    switchDir = {"point": "pointSW", "orient": "orientSW", "parent": "parentSW"}

    for switch in switchAtts:

        for type in (switchDir.keys()):
            if type in switch:
                switchNode = pm.PyNode("{0}_{1}".format(node, switchDir[type]))
                # r = switchNode.getChildren()
                constraint = pm.listRelatives(switchNode, c=True,
                                              type=["parentConstraint", "orientConstraint", "pointConstraint"])
                pm.delete(constraint)
                child = pm.listRelatives(switchNode, c=True, type="transform")[0]
                try:
                    parent = pm.listRelatives(switchNode, p=True, type="transform")[0]
                except IndexError:
                    parent = None
                if parent:
                    pm.parent(child, parent)
                else:
                    pm.parent(child, w=True)
                pm.delete(switchNode)
                pm.deleteAttr("{0}.{1}".format(node, switch))

class anchorMaker(QtWidgets.QDialog):
    def __init__(self):
        for entry in QtWidgets.QApplication.allWidgets():
            try:
                if entry.objectName() == windowName:
                    entry.close()
            except AttributeError:
                pass
        parent = getMayaMainWindow()
        super(anchorMaker, self).__init__(parent=parent)

        self.setWindowTitle(windowName)
        self.setObjectName(windowName)
        self.UI()
        self.anchorObject = None
        self.anchorLocations = []

    def UI(self):
        self.setObjectName(("anchormaker_Dialog"))
        self.resize(288, 197)
        self.setWindowTitle(("Anchor Maker"))

        self.anchortype_comboBox = QtWidgets.QComboBox(self)
        self.anchortype_comboBox.setGeometry(QtCore.QRect(110, 20, 101, 22))
        self.anchortype_comboBox.setObjectName(("anchortype_comboBox"))
        self.anchortype_comboBox.addItem((""))
        self.anchortype_comboBox.setItemText(0, ("parent"))
        self.anchortype_comboBox.addItem((""))
        self.anchortype_comboBox.setItemText(1, ("point"))
        self.anchortype_comboBox.addItem((""))
        self.anchortype_comboBox.setItemText(2, ("orient"))

        self.anchortype_label = QtWidgets.QLabel(self)
        self.anchortype_label.setGeometry(QtCore.QRect(20, 20, 81, 21))
        self.anchortype_label.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.anchortype_label.setText(("Anchor Type:"))
        self.anchortype_label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.anchortype_label.setObjectName(("anchortype_label"))

        self.anchorobject_lineEdit = QtWidgets.QLineEdit(self)
        self.anchorobject_lineEdit.setGeometry(QtCore.QRect(110, 50, 101, 21))
        self.anchorobject_lineEdit.setToolTip(("This is the object that will be anchored to different locations"))
        self.anchorobject_lineEdit.setPlaceholderText(("select and hit \'get\'"))
        self.anchorobject_lineEdit.setObjectName(("anchorobject_lineEdit"))
        self.anchorobject_lineEdit.setReadOnly(True)

        self.anchorobject_label = QtWidgets.QLabel(self)
        self.anchorobject_label.setGeometry(QtCore.QRect(20, 50, 81, 21))
        self.anchorobject_label.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.anchorobject_label.setText(("Anchor Object:"))
        self.anchorobject_label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.anchorobject_label.setObjectName(("anchorobject_label"))

        self.locationobjects_lineEdit = QtWidgets.QLineEdit(self)
        self.locationobjects_lineEdit.setGeometry(QtCore.QRect(110, 80, 101, 21))
        self.locationobjects_lineEdit.setToolTip(("This is the object that will be anchored to different locations"))
        self.locationobjects_lineEdit.setPlaceholderText(("select and hit \'get\'"))
        self.locationobjects_lineEdit.setObjectName(("locationobjects_lineEdit"))
        self.locationobjects_lineEdit.setReadOnly(True)

        self.locationobjects_label = QtWidgets.QLabel(self)
        self.locationobjects_label.setGeometry(QtCore.QRect(10, 80, 91, 21))
        self.locationobjects_label.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.locationobjects_label.setText(("Anchor Locations:"))
        self.locationobjects_label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.locationobjects_label.setObjectName(("locationobjects_label"))

        self.getanchor_pushButton = QtWidgets.QPushButton(self)
        self.getanchor_pushButton.setGeometry(QtCore.QRect(220, 50, 51, 21))
        self.getanchor_pushButton.setText(("<- Get"))
        self.getanchor_pushButton.setObjectName(("getanchor_pushButton"))

        self.getlocations_pushButton = QtWidgets.QPushButton(self)
        self.getlocations_pushButton.setGeometry(QtCore.QRect(220, 80, 51, 21))
        self.getlocations_pushButton.setText(("<- Get"))
        self.getlocations_pushButton.setObjectName(("getlocations_pushButton"))

        self.deleteanchor_pushButton = QtWidgets.QPushButton(self)
        self.deleteanchor_pushButton.setGeometry(QtCore.QRect(20, 120, 71, 61))
        self.deleteanchor_pushButton.setText(("Delete\nAnchors"))
        self.deleteanchor_pushButton.setObjectName(("deleteanchor_pushButton"))

        self.createanchor_pushButton = QtWidgets.QPushButton(self)
        self.createanchor_pushButton.setGeometry(QtCore.QRect(120, 120, 151, 61))
        self.createanchor_pushButton.setText(("Create\nAnchor"))
        self.createanchor_pushButton.setObjectName(("createanchor_pushButton"))
        self.createanchor_pushButton.setEnabled(False)

        self.getanchor_pushButton.clicked.connect(self.onGetAnchor)
        self.getlocations_pushButton.clicked.connect(self.onGetAnchorLocations)
        self.createanchor_pushButton.clicked.connect(lambda: spaceSwitcher(self.anchorObject, self.anchorLocations, mode=self.anchortype_comboBox.currentText()))
        self.deleteanchor_pushButton.clicked.connect(self.onDeleteAnchor)

    def onGetAnchor(self):
        selection = pm.ls(sl=True)
        if not len(selection) == 1:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Warning)
            msg.setInformativeText("Select a single Anchor. It can be any type of object")
            msg.setWindowTitle("Selection Error")
            retval = msg.exec_()
            return
        self.anchorobject_lineEdit.setText(selection[0].name())
        self.anchorobject_lineEdit.setStyleSheet("background-color: yellow; color: black")
        self.anchorObject = selection[0]
        if not self.anchorLocations == []:
            self.createanchor_pushButton.setEnabled(True)
            self.createanchor_pushButton.setStyleSheet("background-color: green; color: black")

    def onGetAnchorLocations(self):
        selection = pm.ls(sl=True)
        if not len(selection) > 0:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Warning)
            msg.setInformativeText("Select at least one docking point. It can be any type of object")
            msg.setWindowTitle("Selection Error")
            retval = msg.exec_()
            return
        self.locationobjects_lineEdit.setText("%s items" %len(selection))
        self.locationobjects_lineEdit.setStyleSheet("background-color: yellow; color: black")
        self.anchorLocations = selection
        if self.anchorObject:
            self.createanchor_pushButton.setEnabled(True)
            self.createanchor_pushButton.setStyleSheet("background-color: green; color: black")

    def onDeleteAnchor(self):
        selection = pm.ls(sl=True)
        for i in selection:
            removeAnchor(i)
