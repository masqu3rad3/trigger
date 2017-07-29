import pymel.core as pm

import Qt
from Qt import QtWidgets, QtCore, QtGui
from maya import OpenMayaUI as omui

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

windowName = "TestUI"


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


class testUI(QtWidgets.QTabWidget):
    def __init__(self):
        # for entry in QtWidgets.QApplication.allWidgets():
        #     if entry.objectName() == windowName:
        #         entry.close()
        # parent = getMayaMainWindow()

        ## I use another QDialog as buffer since Tabs wont work when parented to the Maya Ui.
        self.buffer=bufferUI()
        super(testUI, self).__init__(parent=self.buffer)

        ## This will put the Tab Widget into the buffer layout
        self.buffer.superLayout.addWidget(self)

        ## This will zero out the margins caused by the bufferUI
        self.buffer.superLayout.setContentsMargins(0,0,0,0)

        self.setWindowTitle(windowName)
        self.setObjectName(windowName)

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
        self.tab2UI()

    def tab1UI(self):
        layout = QtWidgets.QFormLayout()
        layout.addRow("Name", QtWidgets.QLineEdit())
        layout.addRow("Address", QtWidgets.QLineEdit())
        self.setTabText(0, "Contact Details")
        self.initBonesTab.setLayout(layout)

    def tab2UI(self):
        layout = QtWidgets.QFormLayout()
        sex = QtWidgets.QHBoxLayout()
        sex.addWidget(QtWidgets.QRadioButton("Male"))
        sex.addWidget(QtWidgets.QRadioButton("Female"))
        layout.addRow(QtWidgets.QLabel("Sex"), sex)
        layout.addRow("Date of Birth", QtWidgets.QLineEdit())
        self.setTabText(1, "Personal Details")
        self.rigTab.setLayout(layout)

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
        spineCreate = QtWidgets.QPushButton("Create", minimumSize=(QtCore.QSize(wSize, hSize)), maximumSize=(QtCore.QSize(wSize, hSize)), parent=self)
        spineSegLb = QtWidgets.QLabel("Segments")
        spineSegInt = QtWidgets.QSpinBox(maximumSize=(QtCore.QSize(45, 50)))

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
        segmentsColumnSpine.addWidget(spineSegInt)
        firstRowSpine.addWidget(spineCreate)

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
        armCreate = QtWidgets.QPushButton("Create", minimumSize=(QtCore.QSize(wSize, hSize)), maximumSize=(QtCore.QSize(wSize, hSize)), parent=self)

        radioGrpArm = QtWidgets.QButtonGroup(layout)
        armSideLeft = QtWidgets.QRadioButton("Left", parent=self)
        armSideRight = QtWidgets.QRadioButton("Right", parent=self)
        armSideBoth = QtWidgets.QRadioButton("Both", parent=self)

        radioGrpArm.addButton(armSideLeft)
        radioGrpArm.addButton(armSideRight)
        radioGrpArm.addButton(armSideBoth)
        armSideLeft.setChecked(True)

        columnArm = QtWidgets.QVBoxLayout()
        layout.addLayout(columnArm)
        columnArm.addWidget(armLabel)

        firstRowArm = QtWidgets.QHBoxLayout()
        columnArm.addLayout(firstRowArm)

        radioColumnArm = QtWidgets.QVBoxLayout()
        radioColumnArm.setAlignment(QtCore.Qt.AlignLeft)
        firstRowArm.addLayout(radioColumnArm)

        radioColumnArm.addWidget(armSideLeft)
        radioColumnArm.addWidget(armSideRight)
        radioColumnArm.addWidget(armSideBoth)
        firstRowArm.addWidget(armCreate)


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
        fingerCreate = QtWidgets.QPushButton("Create", minimumSize=(QtCore.QSize(wSize, hSize)), maximumSize=(QtCore.QSize(wSize, hSize)), parent=self)

        radioGrpFinger = QtWidgets.QButtonGroup(layout)
        fingerSideLeft = QtWidgets.QRadioButton("Left", parent=self)
        fingerSideRight = QtWidgets.QRadioButton("Right", parent=self)
        fingerSideBoth = QtWidgets.QRadioButton("Both", parent=self)

        radioGrpFinger.addButton(fingerSideLeft)
        radioGrpFinger.addButton(fingerSideRight)
        radioGrpFinger.addButton(fingerSideBoth)
        fingerSideLeft.setChecked(True)

        fingerIsThumbChk = QtWidgets.QCheckBox("Thumb", parent=self)

        columnFinger = QtWidgets.QVBoxLayout()
        layout.addLayout(columnFinger)
        columnFinger.addWidget(fingerLabel)

        firstRowFinger = QtWidgets.QHBoxLayout()
        columnFinger.addLayout(firstRowFinger)

        radioColumnFinger = QtWidgets.QVBoxLayout()
        radioColumnFinger.setAlignment(QtCore.Qt.AlignLeft)
        firstRowFinger.addLayout(radioColumnFinger)

        radioColumnFinger.addWidget(fingerSideLeft)
        radioColumnFinger.addWidget(fingerSideRight)
        radioColumnFinger.addWidget(fingerSideBoth)
        radioColumnFinger.addWidget(fingerIsThumbChk)
        firstRowFinger.addWidget(fingerCreate)

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
        legCreate = QtWidgets.QPushButton("Create", minimumSize=(QtCore.QSize(wSize, hSize)), maximumSize=(QtCore.QSize(wSize, hSize)), parent=self)

        radioGrpLeg = QtWidgets.QButtonGroup(layout)
        legSideLeft = QtWidgets.QRadioButton("Left", parent=self)
        legSideRight = QtWidgets.QRadioButton("Right", parent=self)
        legSideBoth = QtWidgets.QRadioButton("Both", parent=self)
        radioGrpLeg.addButton(legSideLeft)
        radioGrpLeg.addButton(legSideRight)
        radioGrpLeg.addButton(legSideBoth)
        legSideLeft.setChecked(True)

        columnLeg = QtWidgets.QVBoxLayout()
        layout.addLayout(columnLeg)
        columnLeg.addWidget(legLabel)

        firstRowLeg = QtWidgets.QHBoxLayout()
        columnLeg.addLayout(firstRowLeg)

        radioColumnLeg = QtWidgets.QVBoxLayout()
        radioColumnLeg.setAlignment(QtCore.Qt.AlignLeft)
        firstRowLeg.addLayout(radioColumnLeg)

        radioColumnLeg.addWidget(legSideLeft)
        radioColumnLeg.addWidget(legSideRight)
        radioColumnLeg.addWidget(legSideBoth)
        firstRowLeg.addWidget(legCreate)


        #   ___      _  _
        #  |_ _|___ <_>| |
        #   | |<_> || || |
        #   |_|<___||_||_|
        #

        tailLabel = QtWidgets.QLabel("Tail", minimumSize=(QtCore.QSize(20, 18)), parent=self)
        tailLabel.setFont(QtGui.QFont("Arial", weight=QtGui.QFont.Bold))
        tailLabel.setAlignment(QtCore.Qt.AlignCenter)
        tailLabel.setFrameStyle(QtWidgets.QFrame.Panel)
        tailCreate = QtWidgets.QPushButton("Create", minimumSize=(QtCore.QSize(wSize, hSize)), maximumSize=(QtCore.QSize(wSize, hSize)), parent=self)
        tailSegLb = QtWidgets.QLabel("Segments")
        tailSegInt = QtWidgets.QSpinBox(maximumSize=(QtCore.QSize(45, 50)))

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
        segmentsColumntail.addWidget(tailSegInt)
        firstRowtail.addWidget(tailCreate)


        #   _ _            _     _    _ _              _
        #  | \ | ___  ___ | |__ < >  | | | ___  ___  _| |
        #  |   |/ ._>/ | '| / / /.\/ |   |/ ._><_> |/ . |
        #  |_\_|\___.\_|_.|_\_\ \_/\ |_|_|\___.<___|\___|
        #

        neckLabel = QtWidgets.QLabel("Neck And Head", minimumSize=(QtCore.QSize(20, 18)), parent=self)
        neckLabel.setFont(QtGui.QFont("Arial", weight=QtGui.QFont.Bold))
        neckLabel.setAlignment(QtCore.Qt.AlignCenter)
        neckLabel.setFrameStyle(QtWidgets.QFrame.Panel)
        neckCreate = QtWidgets.QPushButton("Create", minimumSize=(QtCore.QSize(wSize, hSize)), maximumSize=(QtCore.QSize(wSize, hSize)), parent=self)
        neckSegLb = QtWidgets.QLabel("Segments")
        neckSegInt = QtWidgets.QSpinBox(maximumSize=(QtCore.QSize(45, 50)))

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
        segmentsColumnneck.addWidget(neckSegInt)
        firstRowneck.addWidget(neckCreate)



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

