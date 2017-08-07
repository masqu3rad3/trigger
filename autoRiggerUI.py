import pymel.core as pm

import Qt
from Qt import QtWidgets, QtCore, QtGui
from maya import OpenMayaUI as omui
import initials as init
reload(init)
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
        self.buffer.setMinimumSize(200, 600)
        self.buffer.resize(150, 500)

        self.initSkeleton = init.initialJoints()

        self.tabDialog()


    def tabDialog(self):
        # width = self.buffer.frameGeometry().width()
        # height = self.buffer.frameGeometry().height()
        # self.resize(width, height)
        # self.tabWidget = QtWidgets.QTabWidget(self)
        # mainLayout = QtWidgets.QVBoxLayout()
        # mainLayout.addWidget(self.tabWidget)
        self.initBonesTab = QtWidgets.QWidget()
        self.rigTab = QtWidgets.QWidget()
        self.addTab(self.initBonesTab, "Init Bones")
        self.addTab(self.rigTab, "Rigging")
        self.initBonesUI()
        self.rigUI()

    def rigUI(self):
        pass


    def initBonesUI(self):

        wSize = 60
        hSize = 50
        ## This is the main layout
        layout = QtWidgets.QVBoxLayout()
        self.setTabText(0, "Init Bones")
        self.initBonesTab.setLayout(layout)

        #   ___       _
        #  / __> ___ <_>._ _  ___
        #  \__ \| . \| || ' |/ ._>
        #  <___/|  _/|_||_|_|\___.
        #       |_|

        spineLabel = QtWidgets.QLabel("Spine", minimumSize=(QtCore.QSize(20, 18)), parent=self)
        spineLabel.setFont(QtGui.QFont("Arial", weight=QtGui.QFont.Bold))
        spineLabel.setAlignment(QtCore.Qt.AlignCenter)
        spineLabel.setFrameStyle(QtWidgets.QFrame.Panel)
        self.spineCreateBtn = QtWidgets.QPushButton("Create", minimumSize=(QtCore.QSize(wSize, hSize)), maximumSize=(QtCore.QSize(wSize, hSize)), parent=self)
        spineSegLb = QtWidgets.QLabel("Segments")
        self.spineSegInt = QtWidgets.QSpinBox(maximumSize=(QtCore.QSize(45, 50)),value=3, minimum=1)

        columnSpine = QtWidgets.QVBoxLayout()
        layout.addLayout(columnSpine)
        columnSpine.addWidget(spineLabel)

        firstRowSpine = QtWidgets.QHBoxLayout()
        columnSpine.addLayout(firstRowSpine)

        segmentsColumnSpine = QtWidgets.QVBoxLayout()
        segmentsColumnSpine.setAlignment(QtCore.Qt.AlignLeft)
        firstRowSpine.addLayout(segmentsColumnSpine)

        ## Add Widgets

        segmentsColumnSpine.addWidget(spineSegLb)
        segmentsColumnSpine.addWidget(self.spineSegInt)
        firstRowSpine.addWidget(self.spineCreateBtn)
        self.spineCreateBtn.clicked.connect(self.createSpine)

        # self.spineCreateBtn.clicked.connect(lambda segs=self.spineSegInt.value : self.initSkeleton.initLimb("spine", whichSide="auto", segments=12))

        #   ___
        #  | . | _ _ ._ _ _
        #  |   || '_>| ' ' |
        #  |_|_||_|  |_|_|_|
        #

        # ## These are the all Widgets in the Dialog
        armLabel = QtWidgets.QLabel("Arm", minimumSize=(QtCore.QSize(20, 18)), parent=self)
        armLabel.setFont(QtGui.QFont("Arial", weight=QtGui.QFont.Bold))
        armLabel.setAlignment(QtCore.Qt.AlignCenter)
        armLabel.setFrameStyle(QtWidgets.QFrame.Panel)
        self.armCreateBtn = QtWidgets.QPushButton("Create", minimumSize=(QtCore.QSize(wSize, hSize)), maximumSize=(QtCore.QSize(wSize, hSize)), parent=self)

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

        columnArm = QtWidgets.QVBoxLayout()
        layout.addLayout(columnArm)
        columnArm.addWidget(armLabel)

        firstRowArm = QtWidgets.QHBoxLayout()
        columnArm.addLayout(firstRowArm)

        radioColumnArm = QtWidgets.QVBoxLayout()
        radioColumnArm.setAlignment(QtCore.Qt.AlignLeft)
        firstRowArm.addLayout(radioColumnArm)

        radioColumnArm.addWidget(self.armSideLeft)
        radioColumnArm.addWidget(self.armSideRight)
        radioColumnArm.addWidget(self.armSideBoth)
        radioColumnArm.addWidget(self.armSideAuto)

        firstRowArm.addWidget(self.armCreateBtn)

        self.armCreateBtn.clicked.connect(self.createArm)



        #   ___  _
        #  | __><_>._ _  ___  ___  _ _
        #  | _> | || ' |/ . |/ ._>| '_>
        #  |_|  |_||_|_|\_. |\___.|_|
        #               <___'

        ## These are the all Widgets in the Dialog
        fingerLabel = QtWidgets.QLabel("Finger", minimumSize=(QtCore.QSize(20, 18)), parent=self)
        fingerLabel.setFont(QtGui.QFont("Arial", weight=QtGui.QFont.Bold))
        fingerLabel.setAlignment(QtCore.Qt.AlignCenter)
        fingerLabel.setFrameStyle(QtWidgets.QFrame.Panel)
        self.fingerCreateBtn = QtWidgets.QPushButton("Create", minimumSize=(QtCore.QSize(wSize, hSize)), maximumSize=(QtCore.QSize(wSize, hSize)), parent=self)

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

        columnFinger = QtWidgets.QVBoxLayout()
        layout.addLayout(columnFinger)
        columnFinger.addWidget(fingerLabel)

        firstRowFinger = QtWidgets.QHBoxLayout()
        columnFinger.addLayout(firstRowFinger)

        radioColumnFinger = QtWidgets.QVBoxLayout()
        radioColumnFinger.setAlignment(QtCore.Qt.AlignLeft)
        firstRowFinger.addLayout(radioColumnFinger)

        radioColumnFinger.addWidget(self.fingerSideLeft)
        radioColumnFinger.addWidget(self.fingerSideRight)
        radioColumnFinger.addWidget(self.fingerSideBoth)
        radioColumnFinger.addWidget(self.fingerSideAuto)
        radioColumnFinger.addWidget(self.fingerIsThumbChk)
        firstRowFinger.addWidget(self.fingerCreateBtn)

        self.fingerCreateBtn.clicked.connect(self.createFinger)

        #   _
        #  | |   ___  ___
        #  | |_ / ._>/ . |
        #  |___|\___.\_. |
        #            <___'

        ## These are the all Widgets in the Dialog
        legLabel = QtWidgets.QLabel("Leg", minimumSize=(QtCore.QSize(20, 18)), parent=self)
        legLabel.setFont(QtGui.QFont("Arial", weight=QtGui.QFont.Bold))
        legLabel.setAlignment(QtCore.Qt.AlignCenter)
        legLabel.setFrameStyle(QtWidgets.QFrame.Panel)
        self.legCreateBtn = QtWidgets.QPushButton("Create", minimumSize=(QtCore.QSize(wSize, hSize)), maximumSize=(QtCore.QSize(wSize, hSize)), parent=self)

        radioGrpLeg = QtWidgets.QButtonGroup(layout)
        self.legSideLeft = QtWidgets.QRadioButton("Left", parent=self)
        self.legSideRight = QtWidgets.QRadioButton("Right", parent=self)
        self.legSideBoth = QtWidgets.QRadioButton("Both", parent=self)
        self.legSideAuto = QtWidgets.QRadioButton("Auto", parent=self)
        radioGrpLeg.addButton(self.legSideLeft)
        radioGrpLeg.addButton(self.legSideRight)
        radioGrpLeg.addButton(self.legSideBoth)
        radioGrpLeg.addButton(self.legSideAuto)
        self.legSideLeft.setChecked(True)

        columnLeg = QtWidgets.QVBoxLayout()
        layout.addLayout(columnLeg)
        columnLeg.addWidget(legLabel)

        firstRowLeg = QtWidgets.QHBoxLayout()
        columnLeg.addLayout(firstRowLeg)

        radioColumnLeg = QtWidgets.QVBoxLayout()
        radioColumnLeg.setAlignment(QtCore.Qt.AlignLeft)
        firstRowLeg.addLayout(radioColumnLeg)

        radioColumnLeg.addWidget(self.legSideLeft)
        radioColumnLeg.addWidget(self.legSideRight)
        radioColumnLeg.addWidget(self.legSideBoth)
        radioColumnLeg.addWidget(self.legSideAuto)
        firstRowLeg.addWidget(self.legCreateBtn)

        self.legCreateBtn.clicked.connect(self.createLeg)


        #   ___      _  _
        #  |_ _|___ <_>| |
        #   | |<_> || || |
        #   |_|<___||_||_|
        #

        tailLabel = QtWidgets.QLabel("Tail", minimumSize=(QtCore.QSize(20, 18)), parent=self)
        tailLabel.setFont(QtGui.QFont("Arial", weight=QtGui.QFont.Bold))
        tailLabel.setAlignment(QtCore.Qt.AlignCenter)
        tailLabel.setFrameStyle(QtWidgets.QFrame.Panel)
        self.tailCreateBtn = QtWidgets.QPushButton("Create", minimumSize=(QtCore.QSize(wSize, hSize)), maximumSize=(QtCore.QSize(wSize, hSize)), parent=self)
        tailSegLb = QtWidgets.QLabel("Segments")
        self.tailSegInt = QtWidgets.QSpinBox(maximumSize=(QtCore.QSize(45, 50)),value=8, minimum=2)

        columntail = QtWidgets.QVBoxLayout()
        layout.addLayout(columntail)
        columntail.addWidget(tailLabel)

        firstRowtail = QtWidgets.QHBoxLayout()
        columntail.addLayout(firstRowtail)

        segmentsColumntail = QtWidgets.QVBoxLayout()
        segmentsColumntail.setAlignment(QtCore.Qt.AlignLeft)
        firstRowtail.addLayout(segmentsColumntail)

        ## Add Widgets

        segmentsColumntail.addWidget(tailSegLb)
        segmentsColumntail.addWidget(self.tailSegInt)
        firstRowtail.addWidget(self.tailCreateBtn)

        self.tailCreateBtn.clicked.connect(self.createTail)


        #   _ _            _     _    _ _              _
        #  | \ | ___  ___ | |__ < >  | | | ___  ___  _| |
        #  |   |/ ._>/ | '| / / /.\/ |   |/ ._><_> |/ . |
        #  |_\_|\___.\_|_.|_\_\ \_/\ |_|_|\___.<___|\___|
        #

        neckLabel = QtWidgets.QLabel("Neck And Head", minimumSize=(QtCore.QSize(20, 18)), parent=self)
        neckLabel.setFont(QtGui.QFont("Arial", weight=QtGui.QFont.Bold))
        neckLabel.setAlignment(QtCore.Qt.AlignCenter)
        neckLabel.setFrameStyle(QtWidgets.QFrame.Panel)
        self.neckCreateBtn = QtWidgets.QPushButton("Create", minimumSize=(QtCore.QSize(wSize, hSize)), maximumSize=(QtCore.QSize(wSize, hSize)), parent=self)
        neckSegLb = QtWidgets.QLabel("Segments")
        self.neckSegInt = QtWidgets.QSpinBox(maximumSize=(QtCore.QSize(45, 50)), value=3, minimum=1)

        columnneck = QtWidgets.QVBoxLayout()
        layout.addLayout(columnneck)
        columnneck.addWidget(neckLabel)

        firstRowneck = QtWidgets.QHBoxLayout()
        columnneck.addLayout(firstRowneck)

        segmentsColumnneck = QtWidgets.QVBoxLayout()
        segmentsColumnneck.setAlignment(QtCore.Qt.AlignLeft)
        firstRowneck.addLayout(segmentsColumnneck)

        ## Add Widgets

        segmentsColumnneck.addWidget(neckSegLb)
        segmentsColumnneck.addWidget(self.neckSegInt)
        firstRowneck.addWidget(self.neckCreateBtn)

        self.neckCreateBtn.clicked.connect(self.createNeckAndHead)



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

    def createNeckAndHead(self):
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

