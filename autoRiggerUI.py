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
        self.buffer.setMinimumSize(250, 100)
        self.buffer.resize(250, 500)
        self.defineAs=False

        self.initSkeleton = init.initialJoints()
        self.rigger = scratch.LimbBuilder()


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
        # ## set layout for the groupbox
        rigGrpBox.setLayout(rigGrpLayout)

        ## Create widgets
        label = QtWidgets.QLabel("Select a Root Joint -> hit Rig Button")
        rigBtn = QtWidgets.QPushButton("RIG from Root")
        self.isCreateAnchorsChk = QtWidgets.QCheckBox("Create Anchors Automatically", parent=self)
        # self.isCreateAnchorsChk.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.isCreateAnchorsChk.setChecked(True)
        # spineResLayout = QtWidgets.QHBoxLayout()
        # spineResLayout.setAlignment(QtCore.Qt.AlignRight)
        # spineResLbl = QtWidgets.QLabel("Spine Res./Dropoff")
        # self.spineResInt = QtWidgets.QSpinBox(maximumSize=(QtCore.QSize(40, 20)), value=3, minimum=1)
        # self.spineDropoff = QtWidgets.QDoubleSpinBox(maximumSize=(QtCore.QSize(50, 20)), value=2.0, minimum=0.1, maximum=10 )

        # neckResLayout = QtWidgets.QHBoxLayout()
        # neckResLayout.setAlignment(QtCore.Qt.AlignRight)
        # neckResLbl = QtWidgets.QLabel("Neck Res./Dropoff")
        # self.neckResInt = QtWidgets.QSpinBox(maximumSize=(QtCore.QSize(40, 20)), value=3, minimum=1)
        # self.neckDropoff = QtWidgets.QDoubleSpinBox(maximumSize=(QtCore.QSize(50, 20)), value=2.0, minimum=0.1, maximum=10)


        ## Add widgets to the group layout
        rigGrpLayout.addWidget(label)
        rigGrpLayout.addWidget(self.isCreateAnchorsChk)
        # rigGrpLayout.addLayout(spineResLayout)
        # rigGrpLayout.addLayout(neckResLayout)
        # spineResLayout.addWidget(spineResLbl)
        # spineResLayout.addWidget(self.spineResInt)
        # spineResLayout.addWidget(self.spineDropoff)
        # neckResLayout.addWidget(neckResLbl)
        # neckResLayout.addWidget(self.neckResInt)
        # neckResLayout.addWidget(self.neckDropoff)
        rigGrpLayout.addWidget(rigBtn)

        ## Connect the button signal to the rig creation
        rigBtn.clicked.connect(self.rig)
        ## Add groupbox under the tabs main layout
        self.riglayout.addWidget(rigGrpBox)


        # ## Create a groupbox
        addLimbGrpBox = QtWidgets.QGroupBox("Add Limb to the Rig")
        ## Create a Layout for the groupbox
        addGrpLayout = QtWidgets.QVBoxLayout()
        # ## set layout for the groupbox
        addLimbGrpBox.setLayout(addGrpLayout)
        #
        # ## Create widgets
        addlabel = QtWidgets.QLabel("Select in order:\n <Root Reference> - <Parent Node> \n <Master Controller>")
        addToRigBtn = QtWidgets.QPushButton("Add To Rig")
        # self.isCreateAnchorsChk = QtWidgets.QCheckBox("Create Anchors Automatically", parent=self)
        # self.isCreateAnchorsChk.setChecked(True)
        # ## Add widgets to the group layout
        addGrpLayout.addWidget(addlabel)
        addGrpLayout.addWidget(addToRigBtn)

        #
        # ## Connect the button signal to the rig creation
        addToRigBtn.clicked.connect(self.addRig)
        ## Add groupbox under the tabs main layout
        self.riglayout.addWidget(addLimbGrpBox)

    def initBonesUI(self):

        labels = ["Spine", "Neck", "Arm", "Finger", "Leg", "Tail", "Tentacle", "Biped"]
        pressEvents = []
        for labelName in labels:
            label = QtWidgets.QLabel(labelName, parent=self)
            label.setFixedSize(QtCore.QSize(220, 18))
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
        pressEvents[6].mousePressEvent = lambda x: self.hideToggle(self.tentacleGroupBox)
        pressEvents[7].mousePressEvent = lambda x: self.hideToggle(self.bipedGroupBox)

    def initSpineUI(self):
        self.spineGroupBox = QtWidgets.QGroupBox()
        self.spineGroupBox.setFixedSize(210, 80)

        layout = QtWidgets.QHBoxLayout()

        self.spineCreateBtn = QtWidgets.QPushButton("Create", minimumSize=(QtCore.QSize(self.wSize, self.hSize)), maximumSize=(QtCore.QSize(self.wSize, self.hSize)), parent=self)
        spineSegLb = QtWidgets.QLabel("Segments")
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
        self.neckGroupBox.setFixedSize(210, 80)
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
        self.armGroupBox.setFixedSize(210, 100)
        layout = QtWidgets.QHBoxLayout()

        self.armCreateBtn = QtWidgets.QPushButton("Create", minimumSize=(QtCore.QSize(self.wSize, self.hSize)), maximumSize=(QtCore.QSize(self.wSize, self.hSize)), parent=self)

        radioGrpArm = QtWidgets.QButtonGroup(layout)
        self.armSideLeft = QtWidgets.QRadioButton("Left", parent=self)
        self.armSideRight = QtWidgets.QRadioButton("Right", parent=self)
        self.armSideCenter = QtWidgets.QRadioButton("Center", parent=self)
        self.armSideBoth = QtWidgets.QRadioButton("Both", parent=self)
        self.armSideAuto = QtWidgets.QRadioButton("Auto", parent=self)

        radioGrpArm.addButton(self.armSideLeft)
        radioGrpArm.addButton(self.armSideRight)
        radioGrpArm.addButton(self.armSideCenter)
        radioGrpArm.addButton(self.armSideBoth)
        radioGrpArm.addButton(self.armSideAuto)
        self.armSideAuto.setChecked(True)

        radioColumnArm = QtWidgets.QVBoxLayout()
        radioColumnArm.setAlignment(QtCore.Qt.AlignLeft)
        layout.addLayout(radioColumnArm)

        radioColumnArm.addWidget(self.armSideLeft)
        radioColumnArm.addWidget(self.armSideRight)
        radioColumnArm.addWidget(self.armSideCenter)
        radioColumnArm.addWidget(self.armSideBoth)
        radioColumnArm.addWidget(self.armSideAuto)

        layout.addWidget(self.armCreateBtn)

        self.armCreateBtn.clicked.connect(self.createArm)

        self.armGroupBox.setLayout(layout)
        self.armGroupBox.setHidden(True)

        self.initBoneslayout.addWidget(self.armGroupBox)
        
    def initLegUI(self):
        self.legGroupBox = QtWidgets.QGroupBox()
        self.legGroupBox.setFixedSize(210, 100)
        layout = QtWidgets.QHBoxLayout()

        self.legCreateBtn = QtWidgets.QPushButton("Create", minimumSize=(QtCore.QSize(self.wSize, self.hSize)), maximumSize=(QtCore.QSize(self.wSize, self.hSize)), parent=self)

        radioGrpLeg = QtWidgets.QButtonGroup(layout)
        self.legSideLeft = QtWidgets.QRadioButton("Left", parent=self)
        self.legSideRight = QtWidgets.QRadioButton("Right", parent=self)
        self.legSideCenter = QtWidgets.QRadioButton("Center", parent=self)
        self.legSideBoth = QtWidgets.QRadioButton("Both", parent=self)
        self.legSideAuto = QtWidgets.QRadioButton("Auto", parent=self)

        radioGrpLeg.addButton(self.legSideLeft)
        radioGrpLeg.addButton(self.legSideRight)
        radioGrpLeg.addButton(self.legSideCenter)
        radioGrpLeg.addButton(self.legSideBoth)
        radioGrpLeg.addButton(self.legSideAuto)
        self.legSideAuto.setChecked(True)

        radioColumnLeg = QtWidgets.QVBoxLayout()
        radioColumnLeg.setAlignment(QtCore.Qt.AlignLeft)
        layout.addLayout(radioColumnLeg)

        radioColumnLeg.addWidget(self.legSideLeft)
        radioColumnLeg.addWidget(self.legSideRight)
        radioColumnLeg.addWidget(self.legSideCenter)
        radioColumnLeg.addWidget(self.legSideBoth)
        radioColumnLeg.addWidget(self.legSideAuto)

        layout.addWidget(self.legCreateBtn)

        self.legCreateBtn.clicked.connect(self.createLeg)

        self.legGroupBox.setLayout(layout)
        self.legGroupBox.setHidden(True)

        self.initBoneslayout.addWidget(self.legGroupBox)

    def initFingerUI(self):
        self.fingerGroupBox = QtWidgets.QGroupBox()
        self.fingerGroupBox.setFixedSize(210, 100)
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
        self.tailGroupBox.setFixedSize(210,130)

        layout = QtWidgets.QHBoxLayout()
        sgmSubLayout = QtWidgets.QHBoxLayout()

        self.tailCreateBtn = QtWidgets.QPushButton("Create", minimumSize=(QtCore.QSize(self.wSize, self.hSize)), maximumSize=(QtCore.QSize(self.wSize, self.hSize)), parent=self)
        tailSegLb = QtWidgets.QLabel("Segments")
        self.tailSegInt = QtWidgets.QSpinBox(maximumSize=(QtCore.QSize(40, 20)),value=3, minimum=1)

        radioGrpTail = QtWidgets.QButtonGroup(layout)
        self.tailSideLeft = QtWidgets.QRadioButton("Left", parent=self)
        self.tailSideRight = QtWidgets.QRadioButton("Right", parent=self)
        self.tailSideCenter = QtWidgets.QRadioButton("Center", parent=self)
        self.tailSideBoth = QtWidgets.QRadioButton("Both", parent=self)
        self.tailSideAuto = QtWidgets.QRadioButton("Auto", parent=self)

        radioGrpTail.addButton(self.tailSideLeft)
        radioGrpTail.addButton(self.tailSideRight)
        radioGrpTail.addButton(self.tailSideCenter)
        radioGrpTail.addButton(self.tailSideBoth)
        radioGrpTail.addButton(self.tailSideAuto)
        self.tailSideAuto.setChecked(True)

        radioColumnTail = QtWidgets.QVBoxLayout()
        radioColumnTail.setAlignment(QtCore.Qt.AlignLeft)
        layout.addLayout(radioColumnTail)

        radioColumnTail.addWidget(self.tailSideLeft)
        radioColumnTail.addWidget(self.tailSideRight)
        radioColumnTail.addWidget(self.tailSideCenter)
        radioColumnTail.addWidget(self.tailSideBoth)
        radioColumnTail.addWidget(self.tailSideAuto)

        sgmSubLayout.addWidget(tailSegLb)
        sgmSubLayout.addWidget(self.tailSegInt)
        radioColumnTail.addLayout(sgmSubLayout)
        layout.addWidget(self.tailCreateBtn)

        self.tailCreateBtn.clicked.connect(self.createTail)

        self.tailGroupBox.setLayout(layout)
        self.tailGroupBox.setHidden(True)
        self.initBoneslayout.addWidget(self.tailGroupBox)


    def initTentacleUI(self):
        self.tentacleGroupBox = QtWidgets.QGroupBox()
        self.tentacleGroupBox.setFixedSize(210,130)

        layout = QtWidgets.QHBoxLayout()
        sgmSubLayout = QtWidgets.QHBoxLayout()
        self.tentacleCreateBtn = QtWidgets.QPushButton("Create", minimumSize=(QtCore.QSize(self.wSize, self.hSize)), maximumSize=(QtCore.QSize(self.wSize, self.hSize)), parent=self)
        tentacleSegLb = QtWidgets.QLabel("Seg.")
        self.tentacleSegInt = QtWidgets.QSpinBox(maximumSize=(QtCore.QSize(40, 20)),value=3, minimum=1)

        radioGrpTentacle = QtWidgets.QButtonGroup(layout)
        self.tentacleSideLeft = QtWidgets.QRadioButton("Left", parent=self)
        self.tentacleSideRight = QtWidgets.QRadioButton("Right", parent=self)
        self.tentacleSideCenter = QtWidgets.QRadioButton("Center", parent=self)
        self.tentacleSideBoth = QtWidgets.QRadioButton("Both", parent=self)
        self.tentacleSideAuto = QtWidgets.QRadioButton("Auto", parent=self)

        radioGrpTentacle.addButton(self.tentacleSideLeft)
        radioGrpTentacle.addButton(self.tentacleSideRight)
        radioGrpTentacle.addButton(self.tentacleSideCenter)
        radioGrpTentacle.addButton(self.tentacleSideBoth)
        radioGrpTentacle.addButton(self.tentacleSideAuto)
        self.tentacleSideAuto.setChecked(True)

        radioColumnTentacle = QtWidgets.QVBoxLayout()
        radioColumnTentacle.setAlignment(QtCore.Qt.AlignLeft)
        layout.addLayout(radioColumnTentacle)

        radioColumnTentacle.addWidget(self.tentacleSideLeft)
        radioColumnTentacle.addWidget(self.tentacleSideRight)
        radioColumnTentacle.addWidget(self.tentacleSideCenter)
        radioColumnTentacle.addWidget(self.tentacleSideBoth)
        radioColumnTentacle.addWidget(self.tentacleSideAuto)

        sgmSubLayout.addWidget(tentacleSegLb)
        sgmSubLayout.addWidget(self.tentacleSegInt)
        radioColumnTentacle.addLayout(sgmSubLayout)
        layout.addWidget(self.tentacleCreateBtn)

        self.tentacleCreateBtn.clicked.connect(self.createTentacle)

        self.tentacleGroupBox.setLayout(layout)
        self.tentacleGroupBox.setHidden(True)
        self.initBoneslayout.addWidget(self.tentacleGroupBox)
        
    def initBipedUI(self):
        self.bipedGroupBox = QtWidgets.QGroupBox()
        self.bipedGroupBox.setFixedSize(210,100)

        layout = QtWidgets.QHBoxLayout()

        self.bipedCreateBtn = QtWidgets.QPushButton("Create", minimumSize=(QtCore.QSize(self.wSize, self.hSize)), maximumSize=(QtCore.QSize(self.wSize, self.hSize)), parent=self)

        bipedFingerLb = QtWidgets.QLabel("Fingers")
        self.fingerSegInt = QtWidgets.QSpinBox(maximumSize=(QtCore.QSize(40, 20)),value=5, minimum=1, maximum=5)
        bipedSpineLb = QtWidgets.QLabel("Spine Segs")
        self.bipedSpineSegsInt = QtWidgets.QSpinBox(maximumSize=(QtCore.QSize(40, 20)),value=3, minimum=1)
        bipedNeckLb = QtWidgets.QLabel("Neck Segs")
        self.bipedNeckSegsInt = QtWidgets.QSpinBox(maximumSize=(QtCore.QSize(40, 20)),value=1, minimum=1)

        spinLayout = QtWidgets.QVBoxLayout()
        spinLayout.setAlignment(QtCore.Qt.AlignLeft)
        layout.addLayout(spinLayout)

        spinSubA = QtWidgets.QHBoxLayout()
        spinLayout.addLayout(spinSubA)

        spinSubB = QtWidgets.QHBoxLayout()
        spinLayout.addLayout(spinSubB)

        spinSubC = QtWidgets.QHBoxLayout()
        spinLayout.addLayout(spinSubC)

        spinSubA.addWidget(bipedFingerLb)
        spinSubA.addWidget(self.fingerSegInt)
        spinSubB.addWidget(bipedSpineLb)
        spinSubB.addWidget(self.bipedSpineSegsInt)
        spinSubC.addWidget(bipedNeckLb)
        spinSubC.addWidget(self.bipedNeckSegsInt)

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
        self.rigger.__init__()
        self.rigger.startBuilding(createAnchors=self.isCreateAnchorsChk.isChecked())
        pm.undoInfo(closeChunk=True)

    def addRig(self):
        pm.undoInfo(openChunk=True)
        # self.rigger.__init__()
        self.rigger.addLimb()
        pm.undoInfo(closeChunk=True)

    def createBiped(self):
        pm.undoInfo(openChunk=True)
        self.initSkeleton.initHumanoid(fingers=self.fingerSegInt.value(), spineSegments=self.bipedSpineSegsInt.value(), neckSegments=self.bipedNeckSegsInt.value())
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
        self.initSkeleton.initLimb("arm", whichSide=side, defineAs=self.defineAs)
        pm.undoInfo(closeChunk=True)

    def createSpine(self):
        pm.undoInfo(openChunk=True)
        self.initSkeleton.initLimb("spine", segments=self.spineSegInt.value(), defineAs=self.defineAs)
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

        self.initSkeleton.initLimb("finger", whichSide=side, thumb=self.fingerIsThumbChk.isChecked(), defineAs=self.defineAs)
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

        self.initSkeleton.initLimb("leg", whichSide=side, defineAs=self.defineAs)
        pm.undoInfo(closeChunk=True)

    def createTail(self):
        pm.undoInfo(openChunk=True)

        side = ""
        if self.tailSideLeft.isChecked():
            side = "left"
        elif self.tailSideRight.isChecked():
            side = "right"
        elif self.tailSideCenter.isChecked():
            side = "center"
        elif self.tailSideBoth.isChecked():
            side = "both"
        elif self.tailSideAuto.isChecked():
            side = "auto"
        print "side", side
        self.initSkeleton.initLimb("tail", whichSide=side, segments=self.tailSegInt.value(), defineAs=self.defineAs)
        pm.undoInfo(closeChunk=True)

    def createNeck(self):
        pm.undoInfo(openChunk=True)
        self.initSkeleton.initLimb("neck", segments=self.neckSegInt.value(), defineAs=self.defineAs)
        pm.undoInfo(closeChunk=True)

    def createTentacle(self):
        pm.undoInfo(openChunk=True)

        side = ""
        if self.tentacleSideLeft.isChecked():
            side = "left"
        elif self.tentacleSideRight.isChecked():
            side = "right"
        elif self.tentacleSideCenter.isChecked():
            side = "center"
        elif self.tentacleSideBoth.isChecked():
            side = "both"
        elif self.tentacleSideAuto.isChecked():
            side = "auto"

        self.initSkeleton.initLimb("tentacle", whichSide=side, segments=self.tentacleSegInt.value(), defineAs=self.defineAs)
        pm.undoInfo(closeChunk=True)

    # def updateRigAttr(self):
    #     self.rigger.__init__()
    #     self.rigger.createAnchors = self.isCreateAnchorsChk.isChecked()
    #     self.rigger.spineRes = self.spineResInt.value()
    #     self.rigger.spineDropoff = self.spineDropoff.value()
    #     self.rigger.neckRes = self.neckResInt.value()
    #     self.rigger.neckDropoff = self.neckDropoff.value()

    def keyPressEvent(self, event):
        ## If Ctrl is pressed, change the button labels
        if event.key() == 16777249:
            self.defineAs=True
            text="Define As"
            self.spineCreateBtn.setText(text)
            self.neckCreateBtn.setText(text)
            self.armCreateBtn.setText(text)
            self.fingerCreateBtn.setText(text)
            self.legCreateBtn.setText(text)
            self.tailCreateBtn.setText(text)
            self.tentacleCreateBtn.setText(text)


    def keyReleaseEvent(self, event):
        if event.key() == 16777249:
            text="Create"
            self.defineAs=False
            self.spineCreateBtn.setText(text)
            self.neckCreateBtn.setText(text)
            self.armCreateBtn.setText(text)
            self.fingerCreateBtn.setText(text)
            self.legCreateBtn.setText(text)
            self.tailCreateBtn.setText(text)
            self.tentacleCreateBtn.setText(text)


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

