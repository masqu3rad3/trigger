"""
RollerMatic - Python Script
Title: RiggerMatic UI script
AUTHOR:	Arda Kutlu
e-mail: ardakutlu@gmail.com
Web: http://www.ardakutlu.com
VERSION:1.0(Initial)
CREATION DATE: 01.10.2019
LAST MODIFIED DATE: 01.10.2019

DESCRIPTION: Python UI and Setup script
Requires rollerMatic.py plugin installed

INSTALL:
Copy rollerMaticUI to user/maya/scripts folder
Run these commands in python tab (or put them in a shelf):
import rollerMaticUI
rollerMaticUI.MainUI().show()
"""

import maya.cmds as cmds
from trigger.ui.Qt import QtWidgets, QtCore
from trigger.ui.qtmaya import get_main_maya_window
from maya import OpenMayaUI as omui


windowName = "RollerMatic v1.0"


def reloadPlugin():
    loaded = cmds.pluginInfo("rollerMatic", loaded=True, query=True)
    if not loaded:
        try:
            cmds.loadPlugin("rollerMatic.py")
            return True
        except:
            return False
    return True

def checkMayaVersion():
    currentVersion = cmds.about(api=True)
    if currentVersion < 201700:
        return False
    else:
        return True

def createRig(object, ground=None):
    objectShape = cmds.listRelatives(object, shapes=True)[0] #get shape
    # -------------------
    # Prepare controllers
    # -------------------

    # get dimensions
    selObjCenter = cmds.objectCenter(object)  # center location in world coordinates

    # get the radius from the maximum edge of the bounding box
    objBB = cmds.exactWorldBoundingBox(object)
    dimensionList = [objBB[3] - objBB[0], objBB[4] - objBB[1],
                     objBB[5] - objBB[2]]  # [x, y, z] dimensions in world space
    objRadius = max(dimensionList)

    controllerRadius = max((dimensionList[0], dimensionList[2]))

    # create a circle controller
    contMaster = cmds.circle(name="cont_%s" % object, nr=[0, 1, 0], radius=controllerRadius / 1.35)[0]
    cmds.setAttr("%s.tx" % contMaster, (selObjCenter[0]))
    cmds.setAttr("%s.ty" % contMaster, (selObjCenter[1]))
    cmds.setAttr("%s.tz" % contMaster, (selObjCenter[2]))
    cmds.makeIdentity(contMaster, a=True)

    # create master locator
    locatorMaster = cmds.spaceLocator(name="masterLocator")[0]
    cmds.setAttr("%s.tx" % locatorMaster, (selObjCenter[0]))
    cmds.setAttr("%s.ty" % locatorMaster, (selObjCenter[1]))
    cmds.setAttr("%s.tz" % locatorMaster, (selObjCenter[2]))
    locatorMasterShape = cmds.listRelatives(locatorMaster, shapes=True)[0]  # get shape

    # create an upper group for the obj
    objUpGrp = cmds.group(name="%s_upGrp" % object, em=True)
    cmds.setAttr("%s.tx" % objUpGrp, (selObjCenter[0]))
    cmds.setAttr("%s.ty" % objUpGrp, (selObjCenter[1]))
    cmds.setAttr("%s.tz" % objUpGrp, (selObjCenter[2]))
    cmds.makeIdentity(objUpGrp, a=True)

    # create an upper Y for the obj
    objUpGrpY = cmds.group(name="%s_upY" % object, em=True)

    cmds.setAttr("%s.tx" % objUpGrpY, (selObjCenter[0]))
    cmds.setAttr("%s.ty" % objUpGrpY, (selObjCenter[1]))
    cmds.setAttr("%s.tz" % objUpGrpY, (selObjCenter[2]))
    cmds.makeIdentity(objUpGrpY, a=True)

    cmds.parent(objUpGrpY, objUpGrp)

    cmds.parent(object, objUpGrpY)

    # ------------------
    # Create rollermatic
    # ------------------

    rollerMatic = cmds.createNode("rollerMatic")
    # connect inMesh
    cmds.connectAttr("%s.worldMesh[0]" % objectShape, "%s.inMesh" % rollerMatic)
    # connect in positions
    cmds.connectAttr("%s.worldPosition" % locatorMasterShape, "%s.inPosition" % rollerMatic)
    # cmds.connectAttr("%s.translate" % contMaster, "%s.inPosition" % rollerMatic)
    cmds.connectAttr("%s.rotate" % contMaster, "%s.startRotation" % rollerMatic)
    # connect out rotation
    cmds.connectAttr("%s.outRotation" % rollerMatic, "%s.rotate" % object)
    cmds.connectAttr("%s.outPosition" % rollerMatic, "%s.translate" % objUpGrpY)
    # connect time
    cmds.connectAttr("time1.outTime", "%s.time" % rollerMatic)

    # connect masterLocator to the controller
    cmds.parentConstraint(contMaster, locatorMaster, mo=False)

    if ground:
        groundShape = cmds.listRelatives(ground, shapes=True)[0]  # get shape

        cpomLocator = cmds.spaceLocator()
        cpomLocatorShape = cmds.listRelatives(cpomLocator, shapes=True)[0]  # get shape

        cmds.pointConstraint(contMaster, cpomLocator, sk="y")

        cmds.geometryConstraint(ground, cpomLocator)

        cmds.connectAttr("%s.worldPosition.worldPositionY" % cpomLocatorShape, "%s.groundHeight" % rollerMatic)



class MainUI(QtWidgets.QDialog):
    def __init__(self):
        for entry in QtWidgets.QApplication.allWidgets():
            try:
                if entry.objectName() == windowName:
                    entry.close()
            except AttributeError:
                pass
        parent = get_main_maya_window()
        super(MainUI, self).__init__(parent=parent)

        if not reloadPlugin():
            cmds.confirmDialog(title="Plugin Error", message="rollerMatic Plugin cannot be loaded", button=['Ok'])
            self.close()
            self.deleteLater()
            return
            pass

        # store
        self.object = []
        self.ground = None

        self.setWindowTitle(windowName)
        self.setObjectName(windowName)
        self.buildUI()

    def buildUI(self):
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self)
        self.verticalLayout_2.setObjectName(("verticalLayout_2"))

        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName(("verticalLayout"))

        self.rollObject_horizontalLayout = QtWidgets.QHBoxLayout()
        self.rollObject_horizontalLayout.setObjectName(("rollObject_horizontalLayout"))

        self.rollObject_lineEdit = QtWidgets.QLineEdit(self)
        self.rollObject_lineEdit.setFocusPolicy(QtCore.Qt.NoFocus)
        self.rollObject_lineEdit.setAlignment(QtCore.Qt.AlignCenter)
        self.rollObject_lineEdit.setReadOnly(True)
        self.rollObject_lineEdit.setPlaceholderText(("Roll Object"))
        self.rollObject_lineEdit.setObjectName(("rollObject_lineEdit"))
        self.rollObject_lineEdit.setMinimumSize(200,20)

        self.rollObject_horizontalLayout.addWidget(self.rollObject_lineEdit)

        self.rollObject_pushButton = QtWidgets.QPushButton(self)
        self.rollObject_pushButton.setText(("<< GET Object(s)"))
        self.rollObject_pushButton.setMinimumSize(100,20)
        self.rollObject_pushButton.setObjectName(("rollObject_pushButton"))

        self.rollObject_horizontalLayout.addWidget(self.rollObject_pushButton)

        self.verticalLayout.addLayout(self.rollObject_horizontalLayout)

        self.ground_horizontalLayout = QtWidgets.QHBoxLayout()
        self.ground_horizontalLayout.setObjectName(("ground_horizontalLayout"))

        self.ground_lineEdit = QtWidgets.QLineEdit(self)
        self.ground_lineEdit.setFocusPolicy(QtCore.Qt.NoFocus)
        self.ground_lineEdit.setAlignment(QtCore.Qt.AlignCenter)
        self.ground_lineEdit.setReadOnly(True)
        self.ground_lineEdit.setPlaceholderText(("Ground Object (Optional)"))
        self.ground_lineEdit.setObjectName(("ground_lineEdit"))
        self.ground_lineEdit.setMinimumSize(200,20)

        self.ground_horizontalLayout.addWidget(self.ground_lineEdit)

        self.groundget_pushButton = QtWidgets.QPushButton(self)
        self.groundget_pushButton.setText(("<< GET Ground"))
        self.groundget_pushButton.setMinimumSize(100,20)
        self.groundget_pushButton.setObjectName(("groundget_pushButton"))
        self.ground_horizontalLayout.addWidget(self.groundget_pushButton)

        self.verticalLayout.addLayout(self.ground_horizontalLayout)

        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)

        self.verticalLayout.addItem(spacerItem)

        self.rig_pushButton = QtWidgets.QPushButton(self)
        self.rig_pushButton.setText(("Create Rig"))
        self.rig_pushButton.setObjectName(("rig_pushButton"))
        self.verticalLayout.addWidget(self.rig_pushButton)
        self.verticalLayout_2.addLayout(self.verticalLayout)

        self.rollObject_pushButton.clicked.connect(self.onGetObject)
        self.groundget_pushButton.clicked.connect(self.onGetGround)

        self.rig_pushButton.clicked.connect(self.onRig)

    def onGetGround(self):
        selection = cmds.ls(sl=True)
        if len(selection) != 1:
            msg = "A single object must be selected"
            self.infoPop(textTitle="Warning", textHeader=msg, type="C")
            return
        for x in self.object:
            if x == self.ground:
                msg = "Rolling Object and Ground cannot be the same node"
                self.infoPop(textTitle="Warning", textHeader=msg, type="C")
                return

        if selection[0] == self.object:
            msg = "Rolling Object and Ground cannot be the same node"
            self.infoPop(textTitle="Warning", textHeader=msg, type="C")
            return
        else:
            self.ground = selection[0]
            self.ground_lineEdit.setText(self.ground)
            return


    def onGetObject(self):
        selection = cmds.ls(sl=True)
        if len(selection) == 0:
            msg = "Select at least one polygon object"
            self.infoPop(textTitle="Warning", textHeader=msg, type="C")
            return
        for x in selection:
            if x == self.ground:
                msg = "Rolling Object and Ground cannot be the same node"
                self.infoPop(textTitle="Warning", textHeader=msg, type="C")
                return

        self.object = selection
        self.rollObject_lineEdit.setText(",".join(self.object))
        return

    def onRig(self):
        if not self.object:
            msg = "An object to roll must be defined"
            self.infoPop(textTitle="Warning", textHeader=msg, type="C")
            return

        cmds.undoInfo(openChunk=True)
        for obj in self.object:
            createRig(obj, self.ground)
        cmds.undoInfo(closeChunk=True)



    def infoPop(self, textTitle="info", textHeader="", textInfo="", type="I"):
        self.msg = QtWidgets.QMessageBox(parent=self)
        if type == "I":
            self.msg.setIcon(QtWidgets.QMessageBox.Information)
        if type == "C":
            self.msg.setIcon(QtWidgets.QMessageBox.Critical)

        self.msg.setText(textHeader)
        self.msg.setInformativeText(textInfo)
        self.msg.setWindowTitle(textTitle)
        self.msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        self.msg.button(QtWidgets.QMessageBox.Ok).setFixedHeight(30)
        self.msg.button(QtWidgets.QMessageBox.Ok).setFixedWidth(100)
        self.msg.show()