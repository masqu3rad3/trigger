# This Module is intended to gather all mirror-related tools, utilities and commands into a single class
import sys

import pymel.core as pm
import pymel.core.datatypes as dt

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
    if sys.version_info.major == 3:
        ptr = wrapInstance(int(win), QtWidgets.QMainWindow)
    else:
        ptr = wrapInstance(long(win), QtWidgets.QMainWindow)
    return ptr


class MirrorTools(object):
    def __init__(self):
        super(MirrorTools, self).__init__()
        self.lookAxis = "+z"
        self.upAxis = "+y"

    def getSide(self, node):
        nodePos = pm.xform(node, q=1, ws=1, rp=1)

        # Keys are lookAxis / Up Axis, result is the left Controller alignment
        lefties = {
            "+z+y": ["x", 1, 0],
            "+z-y": ["x", -1, 0],
            "+z+x": ["y", -1, 1],
            "+z-x": ["y", 1, 1],

            "-z+y": ["x", -1, 0],
            "-z-y": ["x", 1, 0],
            "-z+x": ["y", 1, 1],
            "-z-x": ["y", -1, 1],

            "+x+y": ["z", -1, 2],
            "+x-y": ["z", 1, 2],
            "+x+z": ["y", -1, 1],
            "+x-z": ["y", 1, 1],

            "-x+y": ["z", 1, 2],
            "-x-y": ["z", -1, 2],
            "-x+z": ["y", -1, 1],
            "-x-z": ["y", 1, 1],
        }
        key = "%s%s" %(self.lookAxis, self.upAxis)

        # nodeMirrorAxis = pm.getAttr("%s.t%s" %(node, lefties[key][0]))

        # Extract the corresponding axis value from the world space coordination of nodes pivot.
        # Multiply it with the second value of the key. This is the left alignment
        val = nodePos[lefties[key][2]] * lefties[key][1]
        # val = (nodeMirrorAxis * lefties[key][1])
        if val > 0:
            return lefties[key][0], "LEFT"
        elif val == 0:
            return None
        else:
            return lefties[key][0], "RIGHT"
        # if

    def mirrorSelect(self):
        # aka mirrorControllers
        selection = pm.ls(sl=True)

        validAlignments = [("RIGHT", "LEFT"), ("right", "left"), ("Right", "Left"), ("_R", "_L"), ("_r", "_l")]

        targetSelectionList = []
        for node in selection:
            nodeName = node.name()
            for a in validAlignments:
                if a[0] in nodeName:
                    oppositeNode = nodeName.replace(a[0], a[1])
                    if pm.objExists(oppositeNode):
                        targetSelectionList.append(pm.PyNode(oppositeNode))
                if a[1] in nodeName:
                    oppositeNode = nodeName.replace(a[1], a[0])
                    if pm.objExists(oppositeNode):
                        targetSelectionList.append(pm.PyNode(oppositeNode))

        pm.select(targetSelectionList)



    def mirrorPose(self, type=0):

        def setMirrorData(sourceNode, targetNode, type=3):

            if type == 0:
                tNorm = dt.Vector(1, 1, -1)
                rNorm = dt.Vector(-1, -1, 1)

            if type == 1:
                tNorm = dt.Vector(-1, 1, 1)
                rNorm = dt.Vector(1, -1, -1)

            if type == 2:
                tNorm = dt.Vector(-1, -1, -1)
                rNorm = dt.Vector(1, 1, 1)

            if type == 3:
                tNorm = dt.Vector(1, 1, 1)
                rNorm = dt.Vector(1, 1, 1)

            ## // TODO add the auto function


            if pm.Attribute(sourceNode.translateX).isKeyable():
                tx = pm.getAttr(sourceNode.translateX)
                mtx = tx * tNorm[0]
                pm.setAttr(targetNode.translateX, mtx)

            if pm.Attribute(sourceNode.translateY).isKeyable():
                ty = pm.getAttr(sourceNode.translateY)
                mty = ty * tNorm[1]
                pm.setAttr(targetNode.translateY, mty)

            if pm.Attribute(sourceNode.translateZ).isKeyable():
                tz = pm.getAttr(sourceNode.translateZ)
                mtz = tz * tNorm[2]
                pm.setAttr(targetNode.translateZ, mtz)

            if pm.Attribute(sourceNode.rotateX).isKeyable():
                rx = pm.getAttr(sourceNode.rotateX)
                mrx = rx * rNorm[0]
                pm.setAttr(targetNode.rotateX, mrx)

            if pm.Attribute(sourceNode.rotateY).isKeyable():
                ry = pm.getAttr(sourceNode.rotateY)
                mry = ry * rNorm[1]
                pm.setAttr(targetNode.rotateY, mry)

            if pm.Attribute(sourceNode.rotateZ).isKeyable():
                rz = pm.getAttr(sourceNode.rotateZ)
                mrz = rz * rNorm[2]
                pm.setAttr(targetNode.rotateZ, mrz)

        # type1NodeList = ["_IK_hand", "_Pole", "_FK_UpLeg", "_FK_LowLeg", "_FK_Foot", "_FK_Ball"]
        # type2NodeList = ["_Shoulder", "_FK_UpArm", "_FK_LowArm", "_FK_Hand", "_Thumb", "_Index", "_Middle", "_Ring",
        #                  "_Pinky", "_Toe", "_Lip"]
        selection = pm.ls(sl=True)
        if not selection:
            pm.warning("select at least one controller")
        for x in selection:
            ## find the opposite
            if "_R" in x.name():
                mirrorName = x.name().replace("_R", "_L")
            elif "_L" in x.name():
                mirrorName = x.name().replace("_L", "_R")

            else:
                pm.warning("No mirror name found")
                return
            try:
                mirrorNode = pm.PyNode(mirrorName)
            except pm.MayaNodeError:
                pm.warning("No mirror found")
                return

            setMirrorData(x, mirrorNode, type=type)

            # for idTag in type1NodeList:
            #     if idTag in x.name():
            #         print idTag
            #         setMirrorData(x, mirrorNode, type=1)
            #         continue
            #
            # for idTag in type2NodeList:
            #     if idTag in x.name():
            #         print idTag
            #         setMirrorData(x, mirrorNode, type=2)
            #         continue

    def mirrorCopy(self):
        """
        Args:
            asdf:
        Returns:
        """
        # aka mirrorControllers
        selection = pm.ls(sl=True)
        for node in selection:
            # dupNode = pm.duplicate(node)
            ## rename if applicable

            axis = self.getSide(node)[0]
            # try to rename the new duplicate
            if not axis:
                pm.warning("Selected objects pivot is exactly in the middle of the defined axis")
                return

            orName = node.name()

            validAlignments = [("RIGHT", "LEFT"), ("right", "left"), ("Right", "Left"), ("_R", "_L"), ("_r", "_l")]
            alignedFlag = 0
            for a in validAlignments:
                if a[0] in orName:
                    dupNode = pm.duplicate(node)
                    newName = orName.replace(a[0], a[1])
                    pm.rename(dupNode[0], newName)
                    alignedFlag = 1
                if a[1] in orName:
                    dupNode = pm.duplicate(node)
                    newName = orName.replace(a[1], a[0])
                    pm.rename(dupNode[0], newName)
                    alignedFlag = 1
                if alignedFlag == 1:
                    break

            if alignedFlag == 0:
                dupNode = pm.duplicate(node)

            ## create a group for the selected controller
            nodeGrp = pm.group(name="tmpGrp", em=True)
            pm.parent(dupNode, nodeGrp)
            # ## mirror it on the given axis
            pm.setAttr("%s.s%s" % (nodeGrp, axis), -1)
            ## ungroup it
            pm.ungroup(nodeGrp)
            ## freeze scale
            pm.makeIdentity(dupNode, a=True, t=False, r=False, s=True)
        pm.select(selection)

    def mirrorRename(self, auto=True, *args, **kwargs):
        """
        adds "_LEFT" and "_RIGHT" words to the selections
        Args:
            auto: (Bool) If True, alignment tag is automated using the class coordinates. Default True.
            addToName(an): (Bool) If True Adds the Alignment label to the end of the current name. If False 'baseName'
                flag is used to rename the object. In this case, a 'baseName' must be provided. Default True
            baseName(bn): (String) This option is valid if only the addToName set to False. Provided string value
                is going to be used for renaming the object.
            sameSideSelection(sss): (Bool) If set True, it assumes that all the selected objects are at the same side.
                All selections will be tagged with the same side value. If set False, it is going to be assumed that two
                objects are selected from opposite sides. Discarded if "auto" flag set True
            side(s): (String) Side tag suffix. Default is "LEFT". Valid values are "LEFT" and "RIGHT".
                Discarded if "auto" flag set True.
            firstSelection(fs): (String) Indicates whether the first selection is left or right. Valid values are "left"
                and "right"
        Returns:
        """

        #default key values
        newName = ""
        addToName = True
        # completeRename = None
        baseName = None

        sameSideSelection = False
        side = "LEFT"
        # mirroredSelection = None
        firstSelection = "left"

        namingTemplate = '"{0}_{1}".format(sel.name(), side)'

        ## get the key arguments
        for key in kwargs:
            if key == "addToName" or key == "an":
                addToName = kwargs[key]
            if key == "sameSideSelection" or key == "sss":
                sameSideSelection = kwargs[key]
            if key == "firstSelection" or key == "fs":
                firstSelection = kwargs[key]
            if key == "side" or key == "s":
                side = kwargs[key].upper()
            if key == "baseName" or key == "bn":
                baseName = kwargs[key]

        if addToName:
            namingTemplate = '"{0}_{1}".format(sel.name(), side)'
        else:
            namingTemplate = '"{0}_{1}".format(baseName, side)'

        selection = pm.ls(sl=True)
        if auto:
            for sel in selection:
                side = self.getSide(sel)[1]
                if side:
                    newName = eval(namingTemplate)
                    pm.rename(sel, newName)
                else:
                    pm.warning("%s is at the center along the mirror axis. Skipping") %sel

            return


        if not addToName and not baseName:
            pm.error("You must provide a 'baseName' with 'completeRename' flag")
            return

        selection = pm.ls(sl=True)

        if not sameSideSelection:
            if len(selection) != 2:
                pm.error("Selection count must be 2 with 'mirroredSelection' flag")
                return
            if firstSelection.lower() == "left":
                secondSelection = "right"
            elif firstSelection.lower() == "right":
                secondSelection = "left"
            else:
                pm.error("firstSelection flag is not valid. Valid options are 'left' and 'right'")
                return

            ## original side
            side = firstSelection.upper()
            sel = selection[0]
            newName = selection[0]
            # exec "newName=%s" % (namingTemplate)
            newName = eval (namingTemplate)
            pm.rename(selection[0], newName)

            ## mirrored side
            side = secondSelection.upper()
            sel = selection[1]
            newName = selection[1]
            # exec "newName=%s" % (namingTemplate)
            newName = eval(namingTemplate)
            pm.rename(selection[1], newName)

        else:
            for sel in selection:
                # exec "newName=%s" %(namingTemplate)
                newName = eval(namingTemplate)
                pm.rename(sel, newName)

class MirrorToolsUI(QtWidgets.QDialog):


    def __init__(self):
        for entry in QtWidgets.QApplication.allWidgets():
            try:
                if entry.objectName() == "addController":
                    entry.close()
            except (AttributeError, TypeError):
                pass
        parent = getMayaMainWindow()
        super(MirrorToolsUI, self).__init__(parent=parent)
        self.setWindowTitle(("MirrorTools"))


        self.wSize = 400
        self.hSize = 20
        self.setFixedSize(300, 270)

        self.mtool = MirrorTools()

        self.buildUI()


    def buildUI(self):

        axisList = ["+x", "+y", "+z", "-x", "-y", "-z"]

        # This function prevents two comboboxes take the same index value
        def fixClash(currentAxis, otherAxis):
            # list number 1 is for skipping the (-) or (+)
            if currentAxis.currentText()[1] == otherAxis.currentText()[1]:
                otherAxis.setCurrentIndex(divmod(otherAxis.currentIndex()+1, otherAxis.count())[1])

        self.setObjectName(("mirrortools_Dialog"))
        self.resize(190, 460)
        self.setMinimumSize(QtCore.QSize(190, 460))
        self.setMaximumSize(QtCore.QSize(190, 460))

        self.lookaxis_label = QtWidgets.QLabel(self)
        self.lookaxis_label.setGeometry(QtCore.QRect(30, 10, 51, 21))
        self.lookaxis_label.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.lookaxis_label.setText(("Look Axis"))
        self.lookaxis_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.lookaxis_label.setObjectName(("lookaxis_label"))

        self.upaxis_label = QtWidgets.QLabel(self)
        self.upaxis_label.setGeometry(QtCore.QRect(30, 40, 51, 20))
        self.upaxis_label.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.upaxis_label.setAutoFillBackground(False)
        self.upaxis_label.setText(("Up Axis"))
        self.upaxis_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.upaxis_label.setObjectName(("upaxis_label"))

        self.lookaxis_comboBox = QtWidgets.QComboBox(self)
        self.lookaxis_comboBox.setGeometry(QtCore.QRect(90, 10, 69, 22))
        self.lookaxis_comboBox.setToolTip((""))
        self.lookaxis_comboBox.setObjectName(("lookaxis_comboBox"))
        self.lookaxis_comboBox.addItems(axisList)
        self.lookaxis_comboBox.setCurrentIndex(2)

        self.upaxis_comboBox = QtWidgets.QComboBox(self)
        self.upaxis_comboBox.setGeometry(QtCore.QRect(90, 40, 71, 22))
        self.upaxis_comboBox.setToolTip((""))
        self.upaxis_comboBox.setObjectName(("upaxis_comboBox"))
        self.upaxis_comboBox.addItems(axisList)
        self.upaxis_comboBox.setCurrentIndex(1)

        self.lookaxis_comboBox.currentIndexChanged.connect(lambda: fixClash(self.lookaxis_comboBox, self.upaxis_comboBox))
        self.upaxis_comboBox.currentIndexChanged.connect(lambda: fixClash(self.upaxis_comboBox, self.lookaxis_comboBox))

        self.mirrorpose_groupBox = QtWidgets.QGroupBox(self)
        self.mirrorpose_groupBox.setGeometry(QtCore.QRect(10, 70, 171, 111))
        self.mirrorpose_groupBox.setToolTip((""))
        self.mirrorpose_groupBox.setTitle(("Mirror Pose"))
        self.mirrorpose_groupBox.setObjectName(("mirrorpose_groupBox"))

        self.mirrorpose_pushButton = QtWidgets.QPushButton(self.mirrorpose_groupBox)
        self.mirrorpose_pushButton.setGeometry(QtCore.QRect(10, 80, 151, 23))
        self.mirrorpose_pushButton.setToolTip((""))
        self.mirrorpose_pushButton.setText(("Mirror Pose"))
        self.mirrorpose_pushButton.setObjectName(("mirrorpose_pushButton"))

        self.typea_radioButton = QtWidgets.QRadioButton(self.mirrorpose_groupBox)
        self.typea_radioButton.setGeometry(QtCore.QRect(10, 50, 31, 17))
        self.typea_radioButton.setToolTip((""))
        self.typea_radioButton.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.typea_radioButton.setText(("A"))
        self.typea_radioButton.setChecked(True)
        self.typea_radioButton.setObjectName(("typea_radioButton"))

        self.typeb_radioButton = QtWidgets.QRadioButton(self.mirrorpose_groupBox)
        self.typeb_radioButton.setGeometry(QtCore.QRect(50, 50, 31, 17))
        self.typeb_radioButton.setToolTip((""))
        self.typeb_radioButton.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.typeb_radioButton.setText(("B"))
        self.typeb_radioButton.setChecked(False)
        self.typeb_radioButton.setObjectName(("typeb_radioButton"))

        self.typec_radioButton = QtWidgets.QRadioButton(self.mirrorpose_groupBox)
        self.typec_radioButton.setGeometry(QtCore.QRect(90, 50, 31, 17))
        self.typec_radioButton.setToolTip((""))
        self.typec_radioButton.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.typec_radioButton.setText(("C"))
        self.typec_radioButton.setChecked(False)
        self.typec_radioButton.setObjectName(("typec_radioButton"))

        self.typed_radioButton = QtWidgets.QRadioButton(self.mirrorpose_groupBox)
        self.typed_radioButton.setGeometry(QtCore.QRect(130, 50, 31, 17))
        self.typed_radioButton.setToolTip((""))
        self.typed_radioButton.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.typed_radioButton.setText(("D"))
        self.typed_radioButton.setChecked(False)
        self.typed_radioButton.setObjectName(("typed_radioButton"))

        self.controllertype_label = QtWidgets.QLabel(self.mirrorpose_groupBox)
        self.controllertype_label.setGeometry(QtCore.QRect(10, 20, 31, 21))
        self.controllertype_label.setToolTip((""))
        self.controllertype_label.setText(("Type:"))
        self.controllertype_label.setObjectName(("controllertype_label"))

        self.triggerauto_checkBox = QtWidgets.QCheckBox(self.mirrorpose_groupBox)
        self.triggerauto_checkBox.setGeometry(QtCore.QRect(70, 22, 91, 20))
        self.triggerauto_checkBox.setToolTip((""))
        self.triggerauto_checkBox.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.triggerauto_checkBox.setText(("T-Rigger Auto"))
        self.triggerauto_checkBox.setObjectName(("triggerauto_checkBox"))
        # TODO: Remove this when auto is ready
        self.triggerauto_checkBox.setDisabled(True)

        self.mirrorcopy_groupBox = QtWidgets.QGroupBox(self)
        self.mirrorcopy_groupBox.setGeometry(QtCore.QRect(10, 190, 171, 61))
        self.mirrorcopy_groupBox.setToolTip((""))
        self.mirrorcopy_groupBox.setTitle(("Mirror Copy"))
        self.mirrorcopy_groupBox.setObjectName(("mirrorcopy_groupBox"))

        self.mirrorcopy_pushButton = QtWidgets.QPushButton(self.mirrorcopy_groupBox)
        self.mirrorcopy_pushButton.setGeometry(QtCore.QRect(10, 30, 151, 23))
        self.mirrorcopy_pushButton.setToolTip((""))
        self.mirrorcopy_pushButton.setText(("Mirror Copy"))
        self.mirrorcopy_pushButton.setObjectName(("mirrorcopy_pushButton"))

        self.mirrorrename_groupBox = QtWidgets.QGroupBox(self)
        self.mirrorrename_groupBox.setGeometry(QtCore.QRect(10, 260, 171, 121))
        self.mirrorrename_groupBox.setToolTip((""))
        self.mirrorrename_groupBox.setTitle(("Mirror Rename"))
        self.mirrorrename_groupBox.setObjectName(("mirrorrename_groupBox"))

        self.mirrorrename_pushButton = QtWidgets.QPushButton(self.mirrorrename_groupBox)
        self.mirrorrename_pushButton.setGeometry(QtCore.QRect(10, 90, 151, 23))
        self.mirrorrename_pushButton.setToolTip((""))
        self.mirrorrename_pushButton.setText(("Mirror Rename"))
        self.mirrorrename_pushButton.setObjectName(("mirrorrename_pushButton"))

        self.addassuffix_checkBox = QtWidgets.QCheckBox(self.mirrorrename_groupBox)
        self.addassuffix_checkBox.setGeometry(QtCore.QRect(10, 30, 91, 17))
        self.addassuffix_checkBox.setToolTip((""))
        self.addassuffix_checkBox.setText(("Add as suffix"))
        self.addassuffix_checkBox.setChecked(True)
        self.addassuffix_checkBox.setObjectName(("addassuffix_checkBox"))

        self.basename_lineEdit = QtWidgets.QLineEdit(self.mirrorrename_groupBox)
        self.basename_lineEdit.setEnabled(False)
        self.basename_lineEdit.setGeometry(QtCore.QRect(12, 60, 151, 20))
        self.basename_lineEdit.setToolTip((""))
        self.basename_lineEdit.setText((""))
        self.basename_lineEdit.setPlaceholderText(("Enter Base Name"))
        self.basename_lineEdit.setObjectName(("basename_lineEdit"))

        self.mirrorselect_groupBox = QtWidgets.QGroupBox(self)
        self.mirrorselect_groupBox.setGeometry(QtCore.QRect(10, 390, 171, 121))
        self.mirrorselect_groupBox.setToolTip((""))
        self.mirrorselect_groupBox.setTitle(("Mirror Select"))
        self.mirrorselect_groupBox.setObjectName(("mirrorselect_groupBox"))

        self.mirrorselect_pushButton = QtWidgets.QPushButton(self.mirrorselect_groupBox)
        self.mirrorselect_pushButton.setGeometry(QtCore.QRect(10, 30, 151, 23))
        self.mirrorselect_pushButton.setToolTip((""))
        self.mirrorselect_pushButton.setText(("Mirror Select"))
        self.mirrorselect_pushButton.setObjectName(("mirrorselect_pushButton"))

        # QtCore.QObject.connect(self.addassuffix_checkBox, QtCore.SIGNAL(("toggled(bool)")),
        #                        self.basename_lineEdit.setDisabled)
        # QtCore.QObject.connect(self.triggerauto_checkBox, QtCore.SIGNAL(("toggled(bool)")),
        #                        self.typea_radioButton.setDisabled)
        # QtCore.QObject.connect(self.triggerauto_checkBox, QtCore.SIGNAL(("toggled(bool)")),
        #                        self.typeb_radioButton.setDisabled)
        # QtCore.QObject.connect(self.triggerauto_checkBox, QtCore.SIGNAL(("toggled(bool)")),
        #                        self.typec_radioButton.setDisabled)
        # QtCore.QObject.connect(self.triggerauto_checkBox, QtCore.SIGNAL(("toggled(bool)")),
        #                        self.typed_radioButton.setDisabled)
        # QtCore.QMetaObject.connectSlotsByName(self)

        self.addassuffix_checkBox.toggled.connect(self.basename_lineEdit.setDisabled)
        # self.triggerauto_checkBox.toggled

        self.mirrorpose_pushButton.clicked.connect(self.onMirrorPose)
        self.mirrorcopy_pushButton.clicked.connect(self.onMirrorCopy)
        self.mirrorrename_pushButton.clicked.connect(self.onMirrorRename)
        self.mirrorselect_pushButton.clicked.connect(self.mtool.mirrorSelect)

    def onMirrorPose(self):

        # self.mtool.upAxis = self.upaxis_comboBox.cu
        self.mtool.upAxis = self.upaxis_comboBox.currentText()
        self.mtool.lookAxis = self.lookaxis_comboBox.currentText()
        if self.triggerauto_checkBox.isChecked():
            type=4
        if self.typea_radioButton.isChecked():
            type=0
        if self.typeb_radioButton.isChecked():
            type = 1
        if self.typec_radioButton.isChecked():
            type = 2
        if self.typed_radioButton.isChecked():
            type = 3

        pm.undoInfo(openChunk=True)
        self.mtool.mirrorPose(type=type)
        pm.undoInfo(closeChunk=True)

    def onMirrorCopy(self):
        pm.undoInfo(openChunk=True)
        self.mtool.upAxis = self.upaxis_comboBox.currentText()
        self.mtool.lookAxis = self.lookaxis_comboBox.currentText()

        self.mtool.mirrorCopy()
        pm.undoInfo(closeChunk=True)

    def onMirrorRename(self):
        pm.undoInfo(openChunk=True)
        if self.addassuffix_checkBox.isChecked():
            addAsSuffix = True
        else:
            if self.basename_lineEdit.text() == "":
                self.infoPop(textTitle="Missing Field", textHeader="Enter a Base Name", textInfo="Please enter an unique base name", type="I")
                return
            addAsSuffix = False
        self.mtool.mirrorRename(auto=True, addToName=addAsSuffix, baseName=self.basename_lineEdit.text())
        pm.undoInfo(closeChunk=True)

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
        self.msg.show()

