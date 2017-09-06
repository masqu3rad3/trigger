import pymel.core as pm

import Qt
from Qt import QtWidgets, QtCore, QtGui
from maya import OpenMayaUI as omui
import initials as init
reload(init)
import scratch
reload(scratch)
import math


if Qt.__binding__ == "PySide":
    from shiboken import wrapInstance
    from Qt.QtCore import Signal
elif Qt.__binding__.startswith('PyQt'):
    from sip import wrapinstance as wrapInstance
    from Qt.Core import pyqtSignal as Signal
else:
    from shiboken2 import wrapInstance
    from Qt.QtCore import Signal

windowName = "Tik_AutoRigger"


def getMayaMainWindow():
    """
    Gets the memory adress of the main window to connect Qt dialog to it.
    Returns:
        (long) Memory Adress
    """
    win = omui.MQtUtil_mainWindow()
    ptr = wrapInstance(long(win), QtWidgets.QMainWindow)
    return ptr

class bufferUI(QtWidgets.QDialog):
    def __init__(self):
        # for entry in QtWidgets.QApplication.allWidgets():
        #     if entry.objectName() == windowName:
        #         entry.close()
        parent = getMayaMainWindow()
        super(bufferUI, self).__init__(parent=parent)
        self.superLayout = QtWidgets.QVBoxLayout(self)
        self.setWindowTitle(windowName)
        self.setObjectName(windowName)
        self.show()


class mainUI(QtWidgets.QTabWidget):
    wSize = 60
    hSize = 50
    def __init__(self):
        for entry in QtWidgets.QApplication.allWidgets():
            if entry.objectName() == windowName:
                # print entry
                entry.close()

        ## I use another QDialog as buffer since Tabs wont work when parented to the Maya Ui.
        self.buffer=bufferUI()
        super(mainUI, self).__init__(parent=self.buffer)

        ## This will put the Tab Widget into the buffer layout
        self.buffer.superLayout.addWidget(self)

        ## This will zero out the margins caused by the bufferUI
        self.buffer.superLayout.setContentsMargins(0,0,0,0)

        self.setWindowTitle(windowName)
        self.setObjectName(windowName)
        self.buffer.setMinimumSize(220, 100)
        self.buffer.resize(240, 300)

        self.initSkeleton = init.initialJoints()
        # self.rigger = scratch.LimbBuilder()


        self.tabDialog()


    def tabDialog(self):


        self.initBonesTab = QtWidgets.QScrollArea()
        self.initBonesTab.setWidget(QtWidgets.QWidget())

        self.initBoneslayout = QtWidgets.QVBoxLayout(self.initBonesTab.widget())
        self.initBoneslayout.setAlignment(QtCore.Qt.AlignTop)
        self.initBonesTab.setWidgetResizable(True)

        self.rigTab = QtWidgets.QScrollArea()
        self.rigTab.setWidget(QtWidgets.QWidget())

        self.riglayout = QtWidgets.QVBoxLayout(self.rigTab.widget())
        self.riglayout.setAlignment(QtCore.Qt.AlignTop)
        self.rigTab.setWidgetResizable(True)

        self.addTab(self.initBonesTab, "Init Bones")
        self.addTab(self.rigTab, "Rigging")

        self.initBonesUI()
        self.rigUI()

    def rigUI(self):

        ## Create a groupbox
        rigGrpBox = QtWidgets.QGroupBox("Rig From Roots")
        ## Create a Layout for the groupbox
        rigGrpLayout = QtWidgets.QVBoxLayout()
        ## Put the layout under groupbox
        rigGrpBox.setLayout(rigGrpLayout)

        ## Create widgets
        label = QtWidgets.QLabel("Select a Root Joint -> hit Rig Button")
        rigBtn = QtWidgets.QPushButton("RIG from Root")
        self.isCreateAnchorsChk = QtWidgets.QCheckBox("Create Anchors Automatically", parent=self)
        self.isCreateAnchorsChk.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.isCreateAnchorsChk.setChecked(True)
        spineResLayout = QtWidgets.QHBoxLayout()
        spineResLayout.setAlignment(QtCore.Qt.AlignRight)
        spineResLbl = QtWidgets.QLabel("Spine Res./Dropoff")
        self.spineResInt = QtWidgets.QSpinBox(maximumSize=(QtCore.QSize(40, 20)), value=3, minimum=1)
        self.spineDropoff = QtWidgets.QDoubleSpinBox(maximumSize=(QtCore.QSize(50, 20)), value=2.0, minimum=0.1, maximum=10 )

        neckResLayout = QtWidgets.QHBoxLayout()
        neckResLayout.setAlignment(QtCore.Qt.AlignRight)
        neckResLbl = QtWidgets.QLabel("Neck Res./Dropoff")
        self.neckResInt = QtWidgets.QSpinBox(maximumSize=(QtCore.QSize(40, 20)), value=3, minimum=1)
        self.neckDropoff = QtWidgets.QDoubleSpinBox(maximumSize=(QtCore.QSize(50, 20)), value=2.0, minimum=0.1, maximum=10)


        ## Add widgets to the group layout
        rigGrpLayout.addWidget(label)
        rigGrpLayout.addWidget(self.isCreateAnchorsChk)
        rigGrpLayout.addLayout(spineResLayout)
        rigGrpLayout.addLayout(neckResLayout)
        spineResLayout.addWidget(spineResLbl)
        spineResLayout.addWidget(self.spineResInt)
        spineResLayout.addWidget(self.spineDropoff)
        neckResLayout.addWidget(neckResLbl)
        neckResLayout.addWidget(self.neckResInt)
        neckResLayout.addWidget(self.neckDropoff)
        rigGrpLayout.addWidget(rigBtn)

        ## Connect the button signal to the rig creation
        rigBtn.clicked.connect(self.rig)
        ## Add groupbox under the tabs main layout
        self.riglayout.addWidget(rigGrpBox)


        # ## Create a groupbox
        # anchorGrpBox = QtWidgets.QGroupBox("Rig From Roots")
        # ## Create a Layout for the groupbox
        # rigGrpLayout = QtWidgets.QVBoxLayout()
        # ## Put the layout under groupbox
        # rigGrpBox.setLayout(rigGrpLayout)
        #
        # ## Create widgets
        # label = QtWidgets.QLabel("Select a Root Joint -> hit Rig Button")
        # rigBtn = QtWidgets.QPushButton("RIG from Root")
        # self.isCreateAnchorsChk = QtWidgets.QCheckBox("Create Anchors Automatically", parent=self)
        # self.isCreateAnchorsChk.setChecked(True)
        # ## Add widgets to the group layout
        # rigGrpLayout.addWidget(label)
        # rigGrpLayout.addWidget(self.isCreateAnchorsChk)
        # rigGrpLayout.addWidget(rigBtn)
        #
        # ## Connect the button signal to the rig creation
        # rigBtn.clicked.connect(self.rig)
        # ## Add groupbox under the tabs main layout
        # self.riglayout.addWidget(rigGrpBox)


    def initBonesUI(self):

        labels = ["Spine", "Neck", "Arm", "Finger", "Leg", "Tail", "Biped"]
        pressEvents = []
        for labelName in labels:
            label = QtWidgets.QLabel(labelName, parent=self)
            label.setFixedSize(QtCore.QSize(185, 18))
            label.setFont(QtGui.QFont("Arial", weight=QtGui.QFont.Bold))
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setFrameStyle(QtWidgets.QFrame.Panel)
            column = QtWidgets.QVBoxLayout()
            self.initBoneslayout.addLayout(column)
            column.addWidget(label)
            eval("self.init{0}UI()".format(labelName))
            pressEvents.append(label)


        pressEvents[0].mousePressEvent = lambda x: self.hideToggle(self.spineGroupBox)
        pressEvents[1].mousePressEvent = lambda x: self.hideToggle(self.neckGroupBox)
        pressEvents[2].mousePressEvent = lambda x: self.hideToggle(self.armGroupBox)
        pressEvents[3].mousePressEvent = lambda x: self.hideToggle(self.fingerGroupBox)
        pressEvents[4].mousePressEvent = lambda x: self.hideToggle(self.legGroupBox)
        pressEvents[5].mousePressEvent = lambda x: self.hideToggle(self.tailGroupBox)
        pressEvents[6].mousePressEvent = lambda x: self.hideToggle(self.bipedGroupBox)

    def initSpineUI(self):
        self.spineGroupBox = QtWidgets.QGroupBox()
        self.spineGroupBox.setFixedSize(185, 80)
        layout = QtWidgets.QHBoxLayout()

        self.spineCreateBtn = QtWidgets.QPushButton("Create", minimumSize=(QtCore.QSize(self.wSize, self.hSize)), maximumSize=(QtCore.QSize(self.wSize, self.hSize)), parent=self)
        spineSegLb = QtWidgets.QLabel("Spine Resolution")
        self.spineSegInt = QtWidgets.QSpinBox(maximumSize=(QtCore.QSize(40, 20)),value=3, minimum=1)


        layout.addWidget(spineSegLb)
        layout.addWidget(self.spineSegInt)
        layout.addWidget(self.spineCreateBtn)

        self.spineCreateBtn.clicked.connect(self.createSpine)

        self.spineGroupBox.setLayout(layout)
        self.spineGroupBox.setHidden(True)
        self.initBoneslayout.addWidget(self.spineGroupBox)
        
    def initNeckUI(self):
        self.neckGroupBox = QtWidgets.QGroupBox()
        self.neckGroupBox.setFixedSize(185, 80)
        layout = QtWidgets.QHBoxLayout()

        self.neckCreateBtn = QtWidgets.QPushButton("Create", minimumSize=(QtCore.QSize(self.wSize, self.hSize)), maximumSize=(QtCore.QSize(self.wSize, self.hSize)), parent=self)
        neckSegLb = QtWidgets.QLabel("Segments")
        self.neckSegInt = QtWidgets.QSpinBox(maximumSize=(QtCore.QSize(40, 20)),value=3, minimum=1)

        layout.addWidget(neckSegLb)
        layout.addWidget(self.neckSegInt)
        layout.addWidget(self.neckCreateBtn)

        self.neckCreateBtn.clicked.connect(self.createNeck)

        self.neckGroupBox.setLayout(layout)
        self.neckGroupBox.setHidden(True)
        self.initBoneslayout.addWidget(self.neckGroupBox)

    def initArmUI(self):
        self.armGroupBox = QtWidgets.QGroupBox()
        self.armGroupBox.setFixedSize(185, 80)
        layout = QtWidgets.QHBoxLayout()

        self.armCreateBtn = QtWidgets.QPushButton("Create", minimumSize=(QtCore.QSize(self.wSize, self.hSize)), maximumSize=(QtCore.QSize(self.wSize, self.hSize)), parent=self)

        radioGrpArm = QtWidgets.QButtonGroup(layout)
        self.armSideLeft = QtWidgets.QRadioButton("Left", parent=self)
        self.armSideRight = QtWidgets.QRadioButton("Right", parent=self)
        self.armSideBoth = QtWidgets.QRadioButton("Both", parent=self)
        self.armSideAuto = QtWidgets.QRadioButton("Auto", parent=self)

        radioGrpArm.addButton(self.armSideLeft)
        radioGrpArm.addButton(self.armSideRight)
        radioGrpArm.addButton(self.armSideBoth)
        radioGrpArm.addButton(self.armSideAuto)
        self.armSideAuto.setChecked(True)

        radioColumnArm = QtWidgets.QVBoxLayout()
        radioColumnArm.setAlignment(QtCore.Qt.AlignLeft)
        layout.addLayout(radioColumnArm)

        radioColumnArm.addWidget(self.armSideLeft)
        radioColumnArm.addWidget(self.armSideRight)
        radioColumnArm.addWidget(self.armSideBoth)
        radioColumnArm.addWidget(self.armSideAuto)

        layout.addWidget(self.armCreateBtn)

        self.armCreateBtn.clicked.connect(self.createArm)

        self.armGroupBox.setLayout(layout)
        self.armGroupBox.setHidden(True)

        self.initBoneslayout.addWidget(self.armGroupBox)
        
    def initLegUI(self):
        self.legGroupBox = QtWidgets.QGroupBox()
        self.legGroupBox.setFixedSize(185, 80)
        layout = QtWidgets.QHBoxLayout()

        self.legCreateBtn = QtWidgets.QPushButton("Create", minimumSize=(QtCore.QSize(self.wSize, self.hSize)), maximumSize=(QtCore.QSize(self.wSize, self.hSize)), parent=self)

        radioGrpLeg = QtWidgets.QButtonGroup(layout)
        self.legSideLeft = QtWidgets.QRadioButton("Left", parent=self)
        self.legSideRight = QtWidgets.QRadioButton("Right", parent=self)
        self.legSideBoth = QtWidgets.QRadioButton("Both", parent=self)
        self.legSideAuto = QtWidgets.QRadioButton("Auto", parent=self)

        radioGrpLeg.addButton(self.legSideLeft)
        radioGrpLeg.addButton(self.legSideRight)
        radioGrpLeg.addButton(self.legSideBoth)
        radioGrpLeg.addButton(self.legSideAuto)
        self.legSideAuto.setChecked(True)

        radioColumnLeg = QtWidgets.QVBoxLayout()
        radioColumnLeg.setAlignment(QtCore.Qt.AlignLeft)
        layout.addLayout(radioColumnLeg)

        radioColumnLeg.addWidget(self.legSideLeft)
        radioColumnLeg.addWidget(self.legSideRight)
        radioColumnLeg.addWidget(self.legSideBoth)
        radioColumnLeg.addWidget(self.legSideAuto)

        layout.addWidget(self.legCreateBtn)

        self.legCreateBtn.clicked.connect(self.createLeg)

        self.legGroupBox.setLayout(layout)
        self.legGroupBox.setHidden(True)

        self.initBoneslayout.addWidget(self.legGroupBox)

    def initFingerUI(self):
        self.fingerGroupBox = QtWidgets.QGroupBox()
        self.fingerGroupBox.setFixedSize(185, 100)
        layout = QtWidgets.QHBoxLayout()

        self.fingerCreateBtn = QtWidgets.QPushButton("Create", minimumSize=(QtCore.QSize(self.wSize, self.hSize)), maximumSize=(QtCore.QSize(self.wSize, self.hSize)), parent=self)

        radioGrpFinger = QtWidgets.QButtonGroup(layout)
        self.fingerSideLeft = QtWidgets.QRadioButton("Left", parent=self)
        self.fingerSideRight = QtWidgets.QRadioButton("Right", parent=self)
        self.fingerSideBoth = QtWidgets.QRadioButton("Both", parent=self)
        self.fingerSideAuto = QtWidgets.QRadioButton("Auto", parent=self)

        radioGrpFinger.addButton(self.fingerSideLeft)
        radioGrpFinger.addButton(self.fingerSideRight)
        radioGrpFinger.addButton(self.fingerSideBoth)
        radioGrpFinger.addButton(self.fingerSideAuto)
        self.fingerSideLeft.setChecked(True)

        self.fingerIsThumbChk = QtWidgets.QCheckBox("Thumb", parent=self)

        radioColumnFinger = QtWidgets.QVBoxLayout()
        radioColumnFinger.setAlignment(QtCore.Qt.AlignLeft)
        layout.addLayout(radioColumnFinger)

        radioColumnFinger.addWidget(self.fingerSideLeft)
        radioColumnFinger.addWidget(self.fingerSideRight)
        radioColumnFinger.addWidget(self.fingerSideBoth)
        radioColumnFinger.addWidget(self.fingerSideAuto)
        radioColumnFinger.addWidget(self.fingerIsThumbChk)
        layout.addWidget(self.fingerCreateBtn)

        self.fingerCreateBtn.clicked.connect(self.createFinger)

        self.fingerGroupBox.setLayout(layout)
        self.fingerGroupBox.setHidden(True)
        self.initBoneslayout.addWidget(self.fingerGroupBox)

    def initTailUI(self):
        self.tailGroupBox = QtWidgets.QGroupBox()
        self.tailGroupBox.setFixedSize(185,80)

        layout = QtWidgets.QHBoxLayout()

        self.tailCreateBtn = QtWidgets.QPushButton("Create", minimumSize=(QtCore.QSize(self.wSize, self.hSize)), maximumSize=(QtCore.QSize(self.wSize, self.hSize)), parent=self)
        tailSegLb = QtWidgets.QLabel("Segments")
        self.tailSegInt = QtWidgets.QSpinBox(maximumSize=(QtCore.QSize(40, 20)),value=3, minimum=1)

        layout.addWidget(tailSegLb)
        layout.addWidget(self.tailSegInt)
        layout.addWidget(self.tailCreateBtn)

        self.tailCreateBtn.clicked.connect(self.createTail)

        self.tailGroupBox.setLayout(layout)
        self.tailGroupBox.setHidden(True)
        self.initBoneslayout.addWidget(self.tailGroupBox)
        
    def initBipedUI(self):
        self.bipedGroupBox = QtWidgets.QGroupBox()
        self.bipedGroupBox.setFixedSize(185,80)

        layout = QtWidgets.QHBoxLayout()

        self.bipedCreateBtn = QtWidgets.QPushButton("Create", minimumSize=(QtCore.QSize(self.wSize, self.hSize)), maximumSize=(QtCore.QSize(self.wSize, self.hSize)), parent=self)
        bipedSegLb = QtWidgets.QLabel("Fingers")
        self.fingerSegInt = QtWidgets.QSpinBox(maximumSize=(QtCore.QSize(40, 20)),value=5, minimum=1, maximum=5)

        layout.addWidget(bipedSegLb)
        layout.addWidget(self.fingerSegInt)
        layout.addWidget(self.bipedCreateBtn)

        self.bipedCreateBtn.clicked.connect(self.createBiped)

        self.bipedGroupBox.setLayout(layout)
        self.initBoneslayout.addWidget(self.bipedGroupBox)

    def hideToggle(self, UI):
        # print UI

        if UI.isVisible():
            UI.setHidden(True)
        else:
            UI.setHidden(False)

    def rig(self):
        pm.undoInfo(openChunk=True)
        rigger = scratch.LimbBuilder()
        # self.rigger.__init__()
        rigger.startBuilding(createAnchors=self.isCreateAnchorsChk.isChecked(), spineRes=self.spineResInt.value(), neckRes=self.neckResInt.value())
        pm.undoInfo(closeChunk=True)

    def createBiped(self):
        pm.undoInfo(openChunk=True)
        self.initSkeleton.initHumanoid(fingers=self.fingerSegInt.value())
        pm.undoInfo(closeChunk=True)

    def createArm(self):
        pm.undoInfo(openChunk=True)
        side=""
        if self.armSideLeft.isChecked():
            side = "left"
        elif self.armSideRight.isChecked():
            side = "right"
        elif self.armSideBoth.isChecked():
            side = "both"
        elif self.armSideAuto.isChecked():
            side = "auto"
        self.initSkeleton.initLimb("arm", whichSide=side)
        pm.undoInfo(closeChunk=True)

    def createSpine(self):
        pm.undoInfo(openChunk=True)
        self.initSkeleton.initLimb("spine", segments=self.spineSegInt.value())
        pm.undoInfo(closeChunk=True)

    def createFinger(self):
        pm.undoInfo(openChunk=True)

        side = ""
        if self.fingerSideLeft.isChecked():
            side = "left"
        elif self.fingerSideRight.isChecked():
            side = "right"
        elif self.fingerSideBoth.isChecked():
            side = "both"
        elif self.fingerSideAuto.isChecked():
            side = "auto"

        self.initSkeleton.initLimb("finger", whichSide=side, thumb=self.fingerIsThumbChk.isChecked())
        pm.undoInfo(closeChunk=True)

    def createLeg(self):
        pm.undoInfo(openChunk=True)

        side = ""
        if self.legSideLeft.isChecked():
            side = "left"
        elif self.legSideRight.isChecked():
            side = "right"
        elif self.legSideBoth.isChecked():
            side = "both"
        elif self.legSideAuto.isChecked():
            side = "auto"

        self.initSkeleton.initLimb("leg", whichSide=side)
        pm.undoInfo(closeChunk=True)

    def createTail(self):
        pm.undoInfo(openChunk=True)
        self.initSkeleton.initLimb("tail", segments=self.tailSegInt.value())
        pm.undoInfo(closeChunk=True)

    def createNeck(self):
        pm.undoInfo(openChunk=True)
        self.initSkeleton.initLimb("neck", segments=self.neckSegInt.value())
        pm.undoInfo(closeChunk=True)

    def testPop(self):
        exportWindow, ok = QtWidgets.QInputDialog.getItem(self, 'Text Input Dialog',
                                                          'SAVE BEFORE PROCEED\n\nANY UNSAVED WORK WILL BE LOST\n\nEnter Asset Name:')
        if ok:
            print "popped"

    def setColor(self):
        color = QtWidgets.QColorDialog.getColor(QtCore.Qt.green, self)
        if color.isValid():
            print(color.name())
            print(QtGui.QPalette(color))
            print color

    def wheelEvent(self, event):
        # print event.delta()
        t = (math.pow(1.2, event.delta() / 120.0))
        if event.modifiers() == QtCore.Qt.ControlModifier:
            print t

# testUI().show()

