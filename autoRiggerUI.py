import pymel.core as pm

import Qt
from Qt import QtWidgets, QtCore, QtGui
from maya import OpenMayaUI as omui
import initials as init
import inspect
reload(init)
import scratch

reload(scratch)

import contIcons as icon
reload(icon)

import mrCubic
reload(mrCubic)

import extraProcedures as extra
reload(extra)

import os
import json
import re
# import math

# from maya.app.general.mayaMixin import MayaQWidgetDockableMixin


# from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

if Qt.__binding__ == "PySide":
    from shiboken import wrapInstance
    from Qt.QtCore import Signal
elif Qt.__binding__.startswith('PyQt'):
    from sip import wrapinstance as wrapInstance
    from Qt.Core import pyqtSignal as Signal
else:
    from shiboken2 import wrapInstance
    from Qt.QtCore import Signal

windowName = "T-Rigger"


def getMayaMainWindow():
    """
    Gets the memory adress of the main window to connect Qt dialog to it.
    Returns:
        (long) Memory Adress
    """
    win = omui.MQtUtil_mainWindow()
    ptr = wrapInstance(long(win), QtWidgets.QMainWindow)
    return ptr

def loadJson(file):
    if os.path.isfile(file):
        with open(file, 'r') as f:
            # The JSON module will read our file, and convert it to a python dictionary
            data = json.load(f)
            return data
    else:
        return None

def dumpJson(data, file):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

def nameCheck(text):

    if re.match("^[A-Za-z0-9_-]*$", text):
        if text == "":
            return -1
        text = text.replace(" ", "_")
        return text
    else:
        return -1

# class mainUI(MayaQWidgetDockableMixin, QtWidgets.QMainWindow):
class mainUI(QtWidgets.QMainWindow):
    def __init__(self):
        for entry in QtWidgets.QApplication.allWidgets():
            if entry.objectName() == windowName:
                entry.close()
                # entry.deleteLater()
        parent = getMayaMainWindow()
        # parent = None
        super(mainUI, self).__init__(parent=parent)

        # settings
        # self.rigName = "triggerAutoRig"
        # self.majorLeftColor = 6
        # self.minorLeftColor = 18
        # self.majorRightColor = 13
        # self.minorRightColor = 9
        # self.majorCenterColor = 17
        # self.minorCenterColor = 20
        # self.lookAxis = "+z"
        # self.upAxis = "+y"
        # self.afterCreation = 0
        # self.seperateSelectionSets = True
        self.settingsDefaults={
            "rigName": "triggerAutoRig",
            "majorLeftColor": 6,
            "minorLeftColor": 18,
            "majorRightColor": 13,
            "minorRightColor": 9,
            "majorCenterColor": 17,
            "minorCenterColor": 20,
            "lookAxis": "+z",
            "upAxis": "+y",
            "afterCreation": 0,
            "seperateSelectionSets": True
            }
        self.loadSettings()


        self.colorCodeDict={}
        self.colorCodes = (
            (120, 120, 120),
            (0, 0, 0),
            (64, 64, 64),
            (128, 128, 128),
            (155, 0, 40),
            (0, 4, 95),
            (0, 0, 255),
            (0, 70, 24),
            (37, 0, 67),
            (199, 0, 199),
            (137, 71, 51),
            (62, 34, 31),
            (153, 37, 0),
            (255, 0, 0),
            (0, 255, 0),
            (0, 65, 153),
            (255, 255, 255),
            (255, 255, 0),
            (99, 220, 255),
            (67, 255, 162),
            (255, 175, 175),
            (227, 172, 121),
            (255, 255, 98),
            (0, 153, 83),
            (160, 105, 47),
            (159, 160, 47),
            (104, 160, 47),
            (47, 160, 93),
            (47, 160, 160),
            (47, 103, 160),
            (110, 47, 160),
            (160, 47, 105)
        )

        self.anchorController = None
        self.anchorLocations = None

        self.wSize = 60
        self.hSize = 50

        self.setWindowTitle(windowName)
        self.setObjectName(windowName)

        self.mainDialog = QtWidgets.QDialog(self)

        # setup the central widget
        self.centralWidget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.centralWidget)
        self.defineAs = False

        bar = self.menuBar()
        file = bar.addMenu("File")
        ### file actions
        generalSettings = QtWidgets.QAction("&Settings", self)
        generalSettings.triggered.connect(self.settingsUI)
        test = QtWidgets.QAction("&Test", self)
        test.triggered.connect(self.progressBar)
        # initialSettings = QtWidgets.QAction("&Initial Joint Settings", self)
        # # initialSettings.triggered.connect(self.initialSettingsUI)
        # rigSettings = QtWidgets.QAction("&Rig Settings", self)
        # # rigSettings.triggered.connect(self.rigSettingsUI)

        file.addAction(generalSettings)
        file.addAction(test)
        # file.addAction(initialSettings)
        # file.addAction(rigSettings)

        ### Tools actions
        tools = bar.addMenu("Tools")
        anchorMaker = QtWidgets.QAction("&Anchor Maker", self)
        anchorMaker.triggered.connect(self.anchorMakerUI)
        mirrorPose = QtWidgets.QAction("&Mirror Pose", self)
        mirrorPose.triggered.connect(self.mirrorPoseUI)
        replaceController = QtWidgets.QAction("&Replace Controller", self)
        # replaceController.triggered.connect(self.replaceControllerUI)

        selectJDef = QtWidgets.QAction("&Select Deformer Joints", self)
        selectJDef.triggered.connect(lambda: pm.select(pm.ls("jDef*")))

        MrCubic = QtWidgets.QAction("&Mr Cubic", self)
        MrCubic.triggered.connect(lambda: mrCubic.mrCube(pm.ls(sl=True)))

        tools.addAction(anchorMaker)
        tools.addAction(mirrorPose)
        tools.addAction(replaceController)
        tools.addAction(selectJDef)
        tools.addAction(MrCubic)

        help = bar.addMenu("Help")
        help.addAction("Getting Started")
        help.addAction("Help")
        help.addAction("About")

        self.layout = QtWidgets.QVBoxLayout(self.mainDialog)
        self.centralWidget.setLayout(self.layout)

        self.initSkeleton = init.initialJoints(self.settingsData)
        self.rigger = scratch.LimbBuilder(self.settingsData)

        self.layout.setContentsMargins(0, 0, 0, 0)

        self.setMinimumSize(250, 100)
        self.resize(250, 500)
        self.buildUI()


        ### new ###
        # self.show(dockable=True, floating=False, area='left')

    def dock_ui(self):
        for entry in QtWidgets.QApplication.allWidgets():
            if entry.objectName() == windowName:
                entry.close()
                # entry.deleteLater()
        if pm.dockControl('triggerDock', q=1, ex=1):
            pm.deleteUI('triggerDock')
        allowedAreas = ['right', 'left']
        try:
            floatingLayout = pm.paneLayout(configuration='single', width=250, height=400)
        except RuntimeError:
            pm.warning("Skipping docking. Restart to dock.")
            self.show()
            return False
        pm.dockControl('triggerDock', area='left', allowedArea=allowedAreas,
                               content=floatingLayout, label='T-Rigger')
        pm.control(windowName, e=True, p=floatingLayout)

        return True

    def buildUI(self):

        self.tabWidget = QtWidgets.QTabWidget()
        self.layout.addWidget(self.tabWidget)

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

        self.extra_tab = QtWidgets.QScrollArea()
        self.extra_tab.setWidget(QtWidgets.QWidget())

        self.extra_layout = QtWidgets.QVBoxLayout(self.extra_tab.widget())
        self.extra_layout.setAlignment(QtCore.Qt.AlignTop)
        self.extra_tab.setWidgetResizable(True)

        self.tabWidget.addTab(self.initBonesTab, "Init Bones")
        self.tabWidget.addTab(self.rigTab, "Rigging")
        self.tabWidget.addTab(self.extra_tab, "Extra")

        self.initBonesUI()
        self.rigUI()
        self.extraUI()
        # layout = QtWidgets.QVBoxLayout(self)

    def progressBar(self):

        self.progress_Dialog = QtWidgets.QDialog(parent=self)
        self.progress_Dialog.setObjectName(("progress_Dialog"))
        self.progress_Dialog.setEnabled(True)
        self.progress_Dialog.resize(290, 40)
        self.progress_Dialog.setMinimumSize(QtCore.QSize(290, 40))
        self.progress_Dialog.setMaximumSize(QtCore.QSize(290, 40))
        self.progress_Dialog.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)
        self.progress_Dialog.setWindowTitle(("Progress"))
        self.progress_Dialog.setWindowOpacity(1.0)

        self.progress_Dialog.setWindowFilePath((""))
        self.progress_Dialog.setInputMethodHints(QtCore.Qt.ImhNone)
        self.progress_Dialog.setSizeGripEnabled(False)
        self.progress_Dialog.setModal(True)
        self.progress_label = QtWidgets.QLabel(self.progress_Dialog)
        self.progress_label.setGeometry(QtCore.QRect(10, 10, 51, 21))

        self.progress_label.setText(("Progress:"))
        self.progress_label.setObjectName(("progress_label"))
        self.progress_progressBar = QtWidgets.QProgressBar(self.progress_Dialog)
        self.progress_progressBar.setGeometry(QtCore.QRect(70, 10, 211, 21))
        self.progress_progressBar.setInputMethodHints(QtCore.Qt.ImhNone)
        self.progress_progressBar.setProperty("value", 24)
        self.progress_progressBar.setFormat(("%p%"))
        self.progress_progressBar.setObjectName(("progress_progressBar"))

        ret = self.progress_Dialog.show()

    def colorPickUI(self):



        edgeSize = 20

        self.colorPick_Dialog = QtWidgets.QDialog(parent=self)
        self.colorPick_Dialog.setObjectName(("colorPick"))
        self.colorPick_Dialog.resize(edgeSize*8, edgeSize*4)
        self.colorPick_Dialog.setWindowTitle(("Color Pick"))
        self.colorPick_Dialog.setModal(True)

        self.returnvalue = 0

        def buttonAction(dialog, value):
            dialog.done(1)
            print value
            self.returnvalue = value

        for i in range (len(self.colorCodes)):
            button = QtWidgets.QPushButton(self.colorPick_Dialog)

            r=divmod(edgeSize*(i), edgeSize*8)
            x = r[1]
            y = (r[0])*edgeSize
            button.setGeometry(QtCore.QRect(x, y, edgeSize, edgeSize))
            button.setText("")
            # cnv_rgb = str((int(self.colorCodes[i][0]*255), int(self.colorCodes[i][1]*255), int(self.colorCodes[i][2]*255)))
            button.setStyleSheet("background-color:rgb%s" %(str(self.colorCodes[i])))
            button.setObjectName("button%s" %i)
            button.clicked.connect(lambda item=(i, self.colorCodes[i]): buttonAction(self.colorPick_Dialog, item))

        # self.majorleft_pushButton.setFocus()

        # self.colorPick_Dialog.show()
        ret = self.colorPick_Dialog.exec_()
        if ret == QtWidgets.QDialog.Accepted:
            # self.close()
            # self.deleteLater()
            return self.returnvalue


 ##############################################################
        # for labelName in labels:
        #     label = QtWidgets.QLabel(labelName, parent=self)
        #     label.setFixedSize(QtCore.QSize(220, 18))
        #     label.setFont(QtGui.QFont("Arial", weight=QtGui.QFont.Bold))
        #     label.setAlignment(QtCore.Qt.AlignCenter)
        #     label.setFrameStyle(QtWidgets.QFrame.Panel)
        #     column = QtWidgets.QVBoxLayout()
        #     self.initBoneslayout.addLayout(column)
        #     column.addWidget(label)
        #     eval("self.init{0}UI()".format(labelName))
        #     pressEvents.append(label)

    ##############################################################

    def saveSettings(self):

        self.rigName = self.rigname_lineEdit.text()
        if self.rigName == "":
            self.rigName = "triggerAutoRig"
        if nameCheck(self.rigName) == -1:
            self.infoPop(textHeader="Invalid Characters", textTitle="Naming Error", textInfo="Use Latin Characters without any spaces.")
            return
        # self.majorLeftColor = self.colorCodeDict["majorleft_pushButton"]
        # self.minorLeftColor = self.colorCodeDict["minorleft_pushButton"]
        # self.majorRightColor = self.colorCodeDict["majorright_pushButton"]
        # self.minorRightColor = self.colorCodeDict["minorright_pushButton"]
        # self.majorCenterColor = self.colorCodeDict["majorcenter_pushButton"]
        # self.minorCenterColor = self.colorCodeDict["minorcenter_pushButton"]
        self.settingsData["rigName"] = self.rigName
        self.settingsData["majorLeftColor"] = self.colorCodeDict["majorleft_pushButton"]
        self.settingsData["minorLeftColor"] = self.colorCodeDict["minorleft_pushButton"]
        self.settingsData["majorRightColor"] = self.colorCodeDict["majorright_pushButton"]
        self.settingsData["minorRightColor"] = self.colorCodeDict["minorright_pushButton"]
        self.settingsData["majorCenterColor"] = self.colorCodeDict["majorcenter_pushButton"]
        self.settingsData["minorCenterColor"] = self.colorCodeDict["minorcenter_pushButton"]


        # self.lookAxis = self.lookaxis_comboBox.currentText()
        # self.upAxis = self.upaxis_comboBox.currentText()
        # self.afterCreation = self.aftercreation_comboBox.currentIndex()
        # self.seperateSelectionSets = self.jointselectionsets_comboBox.currentIndex() == 0

        self.settingsData["lookAxis"] = self.lookaxis_comboBox.currentText()
        self.settingsData["upAxis"] = self.upaxis_comboBox.currentText()
        self.settingsData["afterCreation"] = self.aftercreation_comboBox.currentIndex()
        self.settingsData["seperateSelectionSets"] = self.jointselectionsets_comboBox.currentIndex() == 0

        # settingsData = {
        #     "rigName": self.rigName,
        #     "majorLeftColor": self.majorLeftColor,
        #     "minorLeftColor": self.minorLeftColor,
        #     "majorRightColor": self.majorRightColor,
        #     "minorRightColor": self.minorRightColor,
        #     "majorCenterColor": self.majorCenterColor,
        #     "minorCenterColor": self.minorCenterColor,
        #     "lookAxis": self.lookAxis,
        #     "upAxis": self.upAxis,
        #     "afterCreation": self.afterCreation,
        #     "seperateSelectionSets": self.seperateSelectionSets
        #     }

        homedir = os.path.expanduser("~")
        settingsFilePath = os.path.join(homedir, "triggerSettings.json")
        dumpJson(self.settingsData, settingsFilePath)
        self.initSkeleton.__init__(settingsData=self.settingsData)
        self.rigger.__init__(settingsData=self.settingsData)


    def loadSettings(self, loadDefaults=False):
        if loadDefaults:
            self.settingsData=self.settingsDefaults
            return
        homedir = os.path.expanduser("~")
        settingsFilePath = os.path.join(homedir, "triggerSettings.json")

        # settingsData = loadJson(settingsFilePath)

        if os.path.isfile(settingsFilePath):
            self.settingsData = loadJson(settingsFilePath)
            return
        else:
            self.settingsData = self.settingsDefaults
            dumpJson(self.settingsData, settingsFilePath)

        # If the file is not yet created or deleted/corrupted
        # if not settingsData or loadDefaults:
        #     self.settingsData = {"rigName": "triggerAutoRig",
        #                     "majorLeftColor": 6,
        #                     "minorLeftColor": 18,
        #                     "majorRightColor": 13,
        #                     "minorRightColor": 9,
        #                     "majorCenterColor": 17,
        #                     "minorCenterColor": 20,
        #                     "lookAxis": "+z",
        #                     "upAxis": "+y",
        #                     "afterCreation": 0,
        #                     "seperateSelectionSets": True
        #                     }

        # self.rigName = settingsData["rigName"]
        # self.majorLeftColor = settingsData["majorLeftColor"]
        # self.minorLeftColor = settingsData["minorLeftColor"]
        # self.majorRightColor = settingsData["majorRightColor"]
        # self.minorRightColor = settingsData["minorRightColor"]
        # self.majorCenterColor = settingsData["majorCenterColor"]
        # self.minorCenterColor = settingsData["minorCenterColor"]
        # self.lookAxis = settingsData["lookAxis"]
        # self.upAxis = settingsData["upAxis"]
        # self.afterCreation = settingsData["afterCreation"]
        # self.seperateSelectionSets = settingsData["seperateSelectionSets"]


        #dumpJson(settingsData, settingsFilePath)

    def settingsUI(self):

        axisList=["+x", "+y", "+z", "-x", "-y", "-z"]

        self.colorCodeDict = {
            "majorleft_pushButton": self.settingsData["majorLeftColor"],
            "minorleft_pushButton": self.settingsData["minorLeftColor"],
            "majorright_pushButton": self.settingsData["majorRightColor"],
            "minorright_pushButton": self.settingsData["minorRightColor"],
            "majorcenter_pushButton": self.settingsData["majorCenterColor"],
            "minorcenter_pushButton": self.settingsData["minorCenterColor"]
        }


        self.trigger_settings_Dialog = QtWidgets.QDialog(parent=self)
        self.trigger_settings_Dialog.setObjectName(("trigger_settings_Dialog"))
        self.trigger_settings_Dialog.resize(341, 494)
        self.trigger_settings_Dialog.setWindowTitle(("T-Rigger Settings"))
        self.trigger_settings_Dialog.setModal(False)

        self.general_settings_groupBox = QtWidgets.QGroupBox(self.trigger_settings_Dialog)

        self.general_settings_groupBox.setGeometry(QtCore.QRect(20, 20, 301, 191))
        self.general_settings_groupBox.setTitle(("General Settings"))
        self.general_settings_groupBox.setObjectName(("general_settings_groupBox"))

        self.rigname_label = QtWidgets.QLabel(self.general_settings_groupBox)
        self.rigname_label.setGeometry(QtCore.QRect(0, 25, 101, 20))
        self.rigname_label.setText(("Name"))
        self.rigname_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.rigname_label.setObjectName(("rigname_label"))

        self.rigname_lineEdit = QtWidgets.QLineEdit(self.general_settings_groupBox)
        self.rigname_lineEdit.setGeometry(QtCore.QRect(110, 25, 155, 20))
        self.rigname_lineEdit.setToolTip((""))
        self.rigname_lineEdit.setStatusTip((""))
        self.rigname_lineEdit.setWhatsThis((""))
        self.rigname_lineEdit.setAccessibleName((""))
        self.rigname_lineEdit.setAccessibleDescription((""))
        self.rigname_lineEdit.setCursorPosition(0)
        self.rigname_lineEdit.setPlaceholderText(("Give a name for the rig"))
        self.rigname_lineEdit.setObjectName(("rigname_lineEdit"))

        self.colorcoding_label = QtWidgets.QLabel(self.general_settings_groupBox)
        self.colorcoding_label.setGeometry(QtCore.QRect(0, 60, 101, 20))
        self.colorcoding_label.setText(("Color Coding"))
        self.colorcoding_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.colorcoding_label.setObjectName(("colorcoding_label"))

        self.majorleft_pushButton = QtWidgets.QPushButton(self.general_settings_groupBox)
        self.majorleft_pushButton.setGeometry(QtCore.QRect(20, 90, 81, 31))
        self.majorleft_pushButton.setAcceptDrops(False)
        self.majorleft_pushButton.setToolTip((""))
        self.majorleft_pushButton.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.majorleft_pushButton.setText(("Major Left"))
        self.majorleft_pushButton.setAutoDefault(True)
        self.majorleft_pushButton.setDefault(False)
        self.majorleft_pushButton.setFlat(False)
        self.majorleft_pushButton.setObjectName(("majorleft_pushButton"))
        self.majorleft_pushButton.setFocus()

        self.minorleft_pushButton = QtWidgets.QPushButton(self.general_settings_groupBox)
        self.minorleft_pushButton.setGeometry(QtCore.QRect(20, 130, 81, 31))
        self.minorleft_pushButton.setAcceptDrops(False)
        self.minorleft_pushButton.setToolTip((""))
        self.minorleft_pushButton.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.minorleft_pushButton.setText(("Minor Left"))
        self.minorleft_pushButton.setAutoDefault(True)
        self.minorleft_pushButton.setDefault(False)
        self.minorleft_pushButton.setFlat(False)
        self.minorleft_pushButton.setObjectName(("minorleft_pushButton"))

        self.minorright_pushButton = QtWidgets.QPushButton(self.general_settings_groupBox)
        self.minorright_pushButton.setGeometry(QtCore.QRect(200, 130, 81, 31))
        self.minorright_pushButton.setAcceptDrops(False)
        self.minorright_pushButton.setToolTip((""))
        self.minorright_pushButton.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.minorright_pushButton.setText(("Minor Right"))
        self.minorright_pushButton.setAutoDefault(True)
        self.minorright_pushButton.setDefault(False)
        self.minorright_pushButton.setFlat(False)
        self.minorright_pushButton.setObjectName(("minorright_pushButton"))

        self.majorright_pushButton = QtWidgets.QPushButton(self.general_settings_groupBox)
        self.majorright_pushButton.setGeometry(QtCore.QRect(200, 90, 81, 31))
        self.majorright_pushButton.setAcceptDrops(False)
        self.majorright_pushButton.setToolTip((""))
        self.majorright_pushButton.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.majorright_pushButton.setText(("Major Right"))
        self.majorright_pushButton.setAutoDefault(True)
        self.majorright_pushButton.setDefault(False)
        self.majorright_pushButton.setFlat(False)
        self.majorright_pushButton.setObjectName(("majorright_pushButton"))

        self.minorcenter_pushButton = QtWidgets.QPushButton(self.general_settings_groupBox)
        self.minorcenter_pushButton.setGeometry(QtCore.QRect(110, 130, 81, 31))
        self.minorcenter_pushButton.setAcceptDrops(False)
        self.minorcenter_pushButton.setToolTip((""))
        self.minorcenter_pushButton.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.minorcenter_pushButton.setText(("Minor Center"))
        self.minorcenter_pushButton.setAutoDefault(True)
        self.minorcenter_pushButton.setDefault(False)
        self.minorcenter_pushButton.setFlat(False)
        self.minorcenter_pushButton.setObjectName(("minorcenter_pushButton"))

        self.majorcenter_pushButton = QtWidgets.QPushButton(self.general_settings_groupBox)
        self.majorcenter_pushButton.setGeometry(QtCore.QRect(110, 90, 81, 31))
        self.majorcenter_pushButton.setAcceptDrops(False)
        self.majorcenter_pushButton.setToolTip((""))
        self.majorcenter_pushButton.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.majorcenter_pushButton.setText(("Major Center"))
        self.majorcenter_pushButton.setAutoDefault(True)
        self.majorcenter_pushButton.setDefault(False)
        self.majorcenter_pushButton.setFlat(False)
        self.majorcenter_pushButton.setObjectName(("majorcenter_pushButton"))

        self.initjoint_settings_groupBox = QtWidgets.QGroupBox(self.trigger_settings_Dialog)
        self.initjoint_settings_groupBox.setGeometry(QtCore.QRect(20, 230, 301, 91))
        self.initjoint_settings_groupBox.setTitle(("Initial Joint Settings"))
        self.initjoint_settings_groupBox.setObjectName(("initjoint_settings_groupBox"))

        # This function prevents two comboboxes take the same index value
        def fixClash(currentAxis, otherAxis):
            # list number 1 is for skipping the (-) or (+)
            if currentAxis.currentText()[1] == otherAxis.currentText()[1]:
                otherAxis.setCurrentIndex(divmod(otherAxis.currentIndex()+1, otherAxis.count())[1])

        self.lookaxis_label = QtWidgets.QLabel(self.initjoint_settings_groupBox)
        self.lookaxis_label.setGeometry(QtCore.QRect(0, 20, 101, 20))
        self.lookaxis_label.setText(("Look Axis"))
        self.lookaxis_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.lookaxis_label.setObjectName(("lookaxis_label"))

        self.lookaxis_comboBox = QtWidgets.QComboBox(self.initjoint_settings_groupBox)
        self.lookaxis_comboBox.setGeometry(QtCore.QRect(120, 20, 74, 22))
        self.lookaxis_comboBox.setToolTip((""))
        self.lookaxis_comboBox.setObjectName(("lookaxis_comboBox"))
        self.lookaxis_comboBox.addItems(axisList)

        self.upaxis_label = QtWidgets.QLabel(self.initjoint_settings_groupBox)
        self.upaxis_label.setGeometry(QtCore.QRect(0, 50, 101, 20))
        self.upaxis_label.setText(("Up Axis"))
        self.upaxis_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.upaxis_label.setObjectName(("upaxis_label"))

        self.upaxis_comboBox = QtWidgets.QComboBox(self.initjoint_settings_groupBox)
        self.upaxis_comboBox.setGeometry(QtCore.QRect(120, 50, 74, 22))
        self.upaxis_comboBox.setToolTip((""))
        self.upaxis_comboBox.setObjectName(("upaxis_comboBox"))
        self.upaxis_comboBox.addItems(axisList)

        self.lookaxis_comboBox.currentIndexChanged.connect(lambda: fixClash(self.lookaxis_comboBox, self.upaxis_comboBox))
        self.upaxis_comboBox.currentIndexChanged.connect(lambda: fixClash(self.upaxis_comboBox, self.lookaxis_comboBox))


        self.rig_settings_groupBox = QtWidgets.QGroupBox(self.trigger_settings_Dialog)
        self.rig_settings_groupBox.setGeometry(QtCore.QRect(20, 340, 301, 90))
        self.rig_settings_groupBox.setTitle(("Rig Settings"))
        self.rig_settings_groupBox.setObjectName(("rig_settings_groupBox"))

        self.aftercreation_label = QtWidgets.QLabel(self.rig_settings_groupBox)
        self.aftercreation_label.setGeometry(QtCore.QRect(0, 20, 101, 20))
        self.aftercreation_label.setText(("After Creation"))
        self.aftercreation_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.aftercreation_label.setObjectName(("aftercreation_label"))

        self.aftercreation_comboBox = QtWidgets.QComboBox(self.rig_settings_groupBox)
        self.aftercreation_comboBox.setGeometry(QtCore.QRect(120, 20, 141, 22))
        self.aftercreation_comboBox.setToolTip((""))
        self.aftercreation_comboBox.setObjectName(("aftercreation_comboBox"))
        self.aftercreation_comboBox.addItems(["Do Nothing", "Hide Initial Joints", "Delete Initial Joints"])

        self.selectionsets_label = QtWidgets.QLabel(self.rig_settings_groupBox)
        self.selectionsets_label.setGeometry(QtCore.QRect(0, 50, 101, 20))
        self.selectionsets_label.setText(("Joint Selection Sets"))
        self.selectionsets_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.selectionsets_label.setObjectName(("selectionsets_label"))

        self.jointselectionsets_comboBox = QtWidgets.QComboBox(self.rig_settings_groupBox)
        self.jointselectionsets_comboBox.setGeometry(QtCore.QRect(120, 50, 141, 22))
        self.jointselectionsets_comboBox.addItems(["Seperate for each limb", "One set for everything"])

        def initDialog(loadDefaults=False):
            self.loadSettings(loadDefaults=loadDefaults)
            self.rigname_lineEdit.setText(self.settingsData["rigName"])
            self.colorCodeDict = {
                "majorleft_pushButton": self.settingsData["majorLeftColor"],
                "minorleft_pushButton": self.settingsData["minorLeftColor"],
                "majorright_pushButton": self.settingsData["majorRightColor"],
                "minorright_pushButton": self.settingsData["minorRightColor"],
                "majorcenter_pushButton": self.settingsData["majorCenterColor"],
                "minorcenter_pushButton": self.settingsData["minorCenterColor"]
            }
            cbuttons = [self.majorleft_pushButton, self.minorleft_pushButton, self.majorright_pushButton, self.minorright_pushButton, self.majorcenter_pushButton, self.minorcenter_pushButton]
            for button in cbuttons:
                buttoncolor = self.colorCodes[self.colorCodeDict[button.objectName()]]
                textcolor = (255 - buttoncolor[0], 255 - buttoncolor[1], 255 - buttoncolor[2])
                button.setStyleSheet("background-color:rgb{}; color:rgb{}".format(buttoncolor, textcolor))

            index = self.lookaxis_comboBox.findText(self.settingsData["lookAxis"], QtCore.Qt.MatchFixedString)
            if index >= 0:
                self.lookaxis_comboBox.setCurrentIndex(index)

            index = self.upaxis_comboBox.findText(self.settingsData["upAxis"], QtCore.Qt.MatchFixedString)
            if index >= 0:
                self.upaxis_comboBox.setCurrentIndex(index)

            fixClash(self.lookaxis_comboBox, self.upaxis_comboBox)
            self.aftercreation_comboBox.setCurrentIndex(self.settingsData["afterCreation"])
            self.jointselectionsets_comboBox.setCurrentIndex(not self.settingsData["seperateSelectionSets"])

        self.trigger_buttonBox = QtWidgets.QDialogButtonBox(self.trigger_settings_Dialog)
        self.trigger_buttonBox.setGeometry(QtCore.QRect(20, 450, 301, 30))
        self.trigger_buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.trigger_buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.RestoreDefaults | QtWidgets.QDialogButtonBox.Save)
        self.trigger_buttonBox.setObjectName(("trigger_buttonBox"))

        self.trigger_buttonBox.accepted.connect(self.trigger_settings_Dialog.accept)
        self.trigger_buttonBox.accepted.connect(self.saveSettings)
        self.trigger_buttonBox.rejected.connect(self.trigger_settings_Dialog.reject)
        # self.trigger_buttonBox.button(QtWidgets.QDialogButtonBox.RestoreDefaults).clicked.connect(self.colorPickUI)
        self.trigger_buttonBox.button(QtWidgets.QDialogButtonBox.RestoreDefaults).clicked.connect(lambda: (initDialog(loadDefaults=True)))

        def colorButtons(button):
            colorCode = self.colorPickUI()
            # text color is the complimentary color
            textcolor = str((255-colorCode[1][0], 255-colorCode[1][1], 255-colorCode[1][2]))
            buttoncolor = str(colorCode[1])
            button.setStyleSheet("background-color:rgb{0}; color:rgb{1}".format(buttoncolor, textcolor))
            self.colorCodeDict[button.objectName()]=colorCode[0]

        self.majorcenter_pushButton.clicked.connect(lambda: colorButtons(self.majorcenter_pushButton))
        self.minorcenter_pushButton.clicked.connect(lambda: colorButtons(self.minorcenter_pushButton))
        self.majorleft_pushButton.clicked.connect(lambda: colorButtons(self.majorleft_pushButton))
        self.minorleft_pushButton.clicked.connect(lambda: colorButtons(self.minorleft_pushButton))
        self.majorright_pushButton.clicked.connect(lambda: colorButtons(self.majorright_pushButton))
        self.minorright_pushButton.clicked.connect(lambda: colorButtons(self.minorright_pushButton))

        initDialog()
        self.trigger_settings_Dialog.show()

    def mirrorPoseUI(self):
        parent = getMayaMainWindow()
        self.MPDialog = QtWidgets.QDialog(parent=parent)
        self.MPDialog.setWindowTitle("Mirror Pose")

        MPLayout = QtWidgets.QVBoxLayout(self.MPDialog)

        MPradioGrp = QtWidgets.QButtonGroup(MPLayout)
        self.MPLeftToRight= QtWidgets.QRadioButton("Left => Right", parent=self)
        self.MPRightToLeft= QtWidgets.QRadioButton("Right => Left", parent=self)

        MPradioGrp.addButton(self.MPLeftToRight)
        MPradioGrp.addButton(self.MPRightToLeft)
        self.MPLeftToRight.setChecked(True)

        # MPradioColumn = QtWidgets.QVBoxLayout()
        # MPradioColumn.setAlignment(QtCore.Qt.AlignLeft)
        # MPLayout.addLayout(MPradioColumn)

        MPLayout.addWidget(self.MPLeftToRight)
        MPLayout.addWidget(self.MPRightToLeft)

        MPcheckbox = QtWidgets.QCheckBox("Selection Only", parent=self)
        MPLayout.addWidget(MPcheckbox)

        def enDis(self, state):
            self.MPRightToLeft.setEnabled(state)
            self.MPLeftToRight.setEnabled(state)

        # MPcheckbox.toggled.connect(lambda:MPradioGrp.setEnabled(not MPcheckbox.isChecked()))
        MPcheckbox.toggled.connect(lambda:enDis(self, not MPcheckbox.isChecked()))

        MPmirrorBtn = QtWidgets.QPushButton("Mirror Pose", parent=self)
        MPLayout.addWidget(MPmirrorBtn)

        self.MPDialog.show()

    def anchorMakerUI(self):
        import anchorMaker
        reload(anchorMaker)
        anchorMaker.anchorMaker().show()

    def extraUI(self):
        pass

    def initBonesUI(self):

        labels = ["Spine", "Neck", "Arm", "Finger", "Leg", "Tail", "Tentacle", "Root", "Biped"]
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
        pressEvents[7].mousePressEvent = lambda x: self.hideToggle(self.rootGroupBox)
        pressEvents[8].mousePressEvent = lambda x: self.hideToggle(self.bipedGroupBox)

    def rigUI(self):

        ## Create a groupbox
        rigGrpBox = QtWidgets.QGroupBox("Rig From Roots")
        ## Create a Layout for the groupbox
        rigGrpLayout = QtWidgets.QVBoxLayout()
        # ## set layout for the groupbox
        rigGrpBox.setLayout(rigGrpLayout)

        ## Create widgets
        label = QtWidgets.QLabel("Select Initial Root Joint -> hit Rig Button")
        rigBtn = QtWidgets.QPushButton("RIG from Root")

        self.isCreateAnchorsChk = QtWidgets.QCheckBox("Create Anchors Automatically", parent=self)
        # self.isCreateAnchorsChk.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.isCreateAnchorsChk.setChecked(True)

        ## Add widgets to the group layout
        rigGrpLayout.addWidget(label)
        rigGrpLayout.addWidget(self.isCreateAnchorsChk)

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
        sl_parent_j_button = QtWidgets.QPushButton("Select")
        addToRigBtn = QtWidgets.QPushButton("Add To Rig")

        # ## Add widgets to the group layout
        addGrpLayout.addWidget(addlabel)
        addGrpLayout.addWidget(addToRigBtn)
        #
        # ## Connect the button signal to the rig creation
        addToRigBtn.clicked.connect(self.addRig)
        ## Add groupbox under the tabs main layout
        self.riglayout.addWidget(addLimbGrpBox)

        # create 'EDIT CONTROLLER CURVES' Group

        edit_controllers_grpbox = QtWidgets.QGroupBox("Create / Replace Controller Curves")
        edit_controllers_layout = QtWidgets.QVBoxLayout()
        edit_controllers_grpbox.setLayout(edit_controllers_layout)

        controllers_layout = QtWidgets.QHBoxLayout()
        self.controllers_combobox = QtWidgets.QComboBox()
        self.all_icon_functions = inspect.getmembers(icon, inspect.isfunction)
        iconNames = [i[0] for i in self.all_icon_functions]
        self.controllers_combobox.addItems(iconNames)

        self.controllers_checkbox = QtWidgets.QCheckBox("Align To Center", parent=self)

        controllers_layout.addWidget(self.controllers_combobox)
        controllers_layout.addWidget(self.controllers_checkbox)
        edit_controllers_layout.addLayout(controllers_layout)

        edit_controllers_buttons_layout = QtWidgets.QHBoxLayout()
        edit_controllers_layout.addLayout(edit_controllers_buttons_layout)

        add_controller_pushbutton = QtWidgets.QPushButton("Create")
        add_controller_pushbutton.setToolTip(("Creates the defined controller shape at <0,0,0>"))

        replace_controller_pushbutton = QtWidgets.QPushButton("Replace")
        replace_controller_pushbutton.setToolTip(("Replaces the selected Controller Curves with the defined controller shape"))

        mirror_controller_pushbutton = QtWidgets.QPushButton("Mirror")
        mirror_controller_pushbutton.setToolTip(("Replaces other side of the rig with the selected controller"))

        edit_controllers_buttons_layout.addWidget(add_controller_pushbutton)
        edit_controllers_buttons_layout.addWidget(replace_controller_pushbutton)
        edit_controllers_buttons_layout.addWidget(mirror_controller_pushbutton)

        add_controller_pushbutton.clicked.connect(self.onAddController)
        replace_controller_pushbutton.clicked.connect(self.onReplaceController)
        mirror_controller_pushbutton.clicked.connect(self.onMirrorController)

        self.riglayout.addWidget(edit_controllers_grpbox)

        # # create 'ANCHOR CREATION' Group
        #
        # anchor_conts_grpbox = QtWidgets.QGroupBox("Create Anchors for Controllers")
        # anchor_conts_layout = QtWidgets.QVBoxLayout()
        # anchor_conts_grpbox.setLayout(anchor_conts_layout)
        #
        # # First Row
        # anchor_conts_first_row = QtWidgets.QHBoxLayout()
        # anchor_conts_type_combobox = QtWidgets.QComboBox()
        # anchor_conts_type_combobox.addItems(["parent", "point", "orient"])
        # anchor_conts_first_row.addWidget(anchor_conts_type_combobox)
        # anchor_conts_layout.addLayout(anchor_conts_first_row)
        #
        # # Second Row
        # anchor_conts_second_row = QtWidgets.QHBoxLayout()
        # anchor_conts_label1 = QtWidgets.QLabel("Control Curve")
        # self.anchor_conts_lineedit1 = QtWidgets.QLineEdit()
        # self.anchor_conts_lineedit1.setReadOnly(True)
        # anchor_conts_get_pb1 = QtWidgets.QPushButton("Get")
        #
        # anchor_conts_second_row.addWidget(anchor_conts_label1)
        # anchor_conts_second_row.addWidget(self.anchor_conts_lineedit1)
        # anchor_conts_second_row.addWidget(anchor_conts_get_pb1)
        #
        # anchor_conts_layout.addLayout(anchor_conts_second_row)
        #
        # # Third Row
        # anchor_conts_third_row = QtWidgets.QHBoxLayout()
        # anchor_conts_label2 = QtWidgets.QLabel("Anchor Locations")
        # self.anchor_conts_lineedit2 = QtWidgets.QLineEdit()
        # self.anchor_conts_lineedit2.setReadOnly(True)
        # anchor_conts_get_pb2 = QtWidgets.QPushButton("Get")
        #
        # anchor_conts_third_row.addWidget(anchor_conts_label2)
        # anchor_conts_third_row.addWidget(self.anchor_conts_lineedit2)
        # anchor_conts_third_row.addWidget(anchor_conts_get_pb2)
        #
        # anchor_conts_layout.addLayout(anchor_conts_third_row)
        #
        # # Fourth Row
        # anchor_conts_fourth_row = QtWidgets.QHBoxLayout()
        # create_anchors_pb = QtWidgets.QPushButton("Create Anchors")
        # anchor_conts_fourth_row.addWidget(create_anchors_pb )
        # anchor_conts_layout.addLayout(anchor_conts_fourth_row)
        #
        #
        # anchor_conts_get_pb1.clicked.connect(self.onGetControlCurve)
        # anchor_conts_get_pb2.clicked.connect(self.onGetAnchorLocations)
        # create_anchors_pb.clicked.connect(lambda: extra.spaceSwitcher(self.anchorController, self.anchorLocations, mode=anchor_conts_type_combobox.currentText()))
        #
        # self.riglayout.addWidget(anchor_conts_grpbox)

    def onGetControlCurve(self):
        selection = pm.ls(sl=True)
        if len(selection) > 1:
            self.infoPop(textTitle="Selection Error", textHeader="Select only one object", textInfo="")
        else:
            self.anchorController = selection[0]
            self.anchor_conts_lineedit1.setText(selection[0].name())
        pass

    def onGetAnchorLocations(self):
        self.anchorLocations = pm.ls(sl=True)
        self.anchor_conts_lineedit2.setText("{0} Docks".format (len(self.anchorLocations)))
        pass

    def onAddController(self):
        pm.undoInfo(openChunk=True)
        objName=extra.uniqueName("cont_{0}".format(self.controllers_combobox.currentText()))
        self.all_icon_functions[self.controllers_combobox.currentIndex()][1](name=objName, scale=(1,1,1))
        pm.undoInfo(closeChunk=True)
    def onReplaceController(self):
        pm.undoInfo(openChunk=True)
        selection = pm.ls(sl=True)
        if not selection:
            self.infoPop(textTitle="Skipping action", textHeader="Selection needed", textInfo="You need to select at least one controller node. (transform node)")
            return
        import extraTools as tools
        reload(tools)
        for i in selection:
            oldController = str(i.name())
            objName=extra.uniqueName("cont_{0}".format(self.controllers_combobox.currentText()))
            newController = self.all_icon_functions[self.controllers_combobox.currentIndex()][1](name=objName, scale=(1,1,1))
            tools.replaceController(mirrorAxis=self.initSkeleton.mirrorAxis, mirror=False, oldController=oldController,
                                    newController= newController, alignToCenter=self.controllers_checkbox.isChecked())
            pm.select(oldController)
        pm.undoInfo(closeChunk=True)

    def onMirrorController(self):
        pm.undoInfo(openChunk=True)
        import extraTools as tools
        reload(tools)
        selection = pm.ls(sl=True)
        if not selection:
            self.infoPop(textTitle="Skipping action", textHeader="Selection needed", textInfo="You need to select at least one controller node. (transform node)")
            return
        for sel in selection:
            oldController = extra.getMirror(sel)

            if oldController:
                tryChannels = ["tx", "ty", "tz", "rx", "ry", "rz"]
                transformDict = {}
                for i in tryChannels:
                    keptdata = pm.getAttr("%s.%s" % (oldController, i))
                    transformDict[i] = keptdata
                    try:
                        pm.setAttr("%s.%s" % (oldController, i), 0)
                    except RuntimeError:
                        pass

                # newController = pm.duplicate(pm.ls(sl=True))[0]
                newController = pm.duplicate(sel)[0]


                pm.setAttr(newController.tx, e=True, k=True, l=False)
                pm.setAttr(newController.ty, e=True, k=True, l=False)
                pm.setAttr(newController.tz, e=True, k=True, l=False)
                pm.setAttr(newController.rx, e=True, k=True, l=False)
                pm.setAttr(newController.ry, e=True, k=True, l=False)
                pm.setAttr(newController.rz, e=True, k=True, l=False)
                pm.setAttr(newController.sx, e=True, k=True, l=False)
                pm.setAttr(newController.sy, e=True, k=True, l=False)
                pm.setAttr(newController.sz, e=True, k=True, l=False)

                pm.delete(newController.getChildren(type="transform"))
                tempGrp = pm.group(em=True)
                pm.parent(newController, tempGrp)

                pm.setAttr(tempGrp.scaleX, -1)
                pm.makeIdentity(tempGrp, a=True)
                pm.parent(newController, world=True)
                pm.delete(tempGrp)

                # pm.makeIdentity(newController, a=True)
                pm.parent(newController, oldController)
                tools.replaceController(mirrorAxis=self.initSkeleton.mirrorAxis, mirror=False, oldController=oldController, newController=newController, alignToCenter=self.controllers_checkbox.isChecked())
                for i in tryChannels:
                    try:
                        pm.setAttr("%s.%s" % (oldController, i), transformDict[i])
                    except RuntimeError:
                        pass

        pm.undoInfo(closeChunk=True)


    def initSpineUI(self):
        self.spineGroupBox = QtWidgets.QGroupBox()
        self.spineGroupBox.setFixedSize(210, 80)

        layout = QtWidgets.QHBoxLayout()
        # layout.setContentsMargins(0,0,0,0)
        # layout.setSpacing(2)


        buttonLay = QtWidgets.QHBoxLayout()
        buttonLay.setSpacing(0)
        buttonLay.setAlignment(QtCore.Qt.AlignRight)
        self.spineCreateBtn = QtWidgets.QPushButton("Create", minimumSize=(QtCore.QSize(self.wSize, self.hSize)), maximumSize=(QtCore.QSize(self.wSize, self.hSize)), parent=self)
        self.spineHelpBtn = QtWidgets.QPushButton("?", minimumSize=(QtCore.QSize(self.wSize / 3, self.hSize)), maximumSize=(QtCore.QSize(self.wSize / 3, self.hSize)), parent=self)
        buttonLay.addWidget(self.spineCreateBtn)
        buttonLay.addWidget(self.spineHelpBtn)

        spineSegLb = QtWidgets.QLabel("Segments")
        self.spineSegInt = QtWidgets.QSpinBox(maximumSize=(QtCore.QSize(40, 20)), value=3, minimum=1)

        layout.addWidget(spineSegLb)
        layout.addWidget(self.spineSegInt)
        layout.addLayout(buttonLay)

        self.spineCreateBtn.clicked.connect(self.createSpine)
        self.spineHelpBtn.clicked.connect(lambda x="Spine": self.help(x))

        self.spineGroupBox.setLayout(layout)
        self.spineGroupBox.setHidden(True)
        self.initBoneslayout.addWidget(self.spineGroupBox)

    def initNeckUI(self):
        self.neckGroupBox = QtWidgets.QGroupBox()
        self.neckGroupBox.setFixedSize(210, 80)
        layout = QtWidgets.QHBoxLayout()

        buttonLay = QtWidgets.QHBoxLayout()
        buttonLay.setSpacing(0)
        buttonLay.setAlignment(QtCore.Qt.AlignRight)
        self.neckCreateBtn = QtWidgets.QPushButton("Create", minimumSize=(QtCore.QSize(self.wSize, self.hSize)), maximumSize=(QtCore.QSize(self.wSize, self.hSize)), parent=self)
        self.neckHelpBtn = QtWidgets.QPushButton("?", minimumSize=(QtCore.QSize(self.wSize / 3, self.hSize)), maximumSize=(QtCore.QSize(self.wSize / 3, self.hSize)), parent=self)
        buttonLay.addWidget(self.neckCreateBtn)
        buttonLay.addWidget(self.neckHelpBtn)

        neckSegLb = QtWidgets.QLabel("Segments")
        self.neckSegInt = QtWidgets.QSpinBox(maximumSize=(QtCore.QSize(40, 20)), value=3, minimum=1)

        layout.addWidget(neckSegLb)
        layout.addWidget(self.neckSegInt)
        layout.addLayout(buttonLay)

        self.neckCreateBtn.clicked.connect(self.createNeck)

        self.neckGroupBox.setLayout(layout)
        self.neckGroupBox.setHidden(True)
        self.initBoneslayout.addWidget(self.neckGroupBox)

    def help(self, item):

        self.messageDialog = QtWidgets.QDialog()
        self.messageDialog.setWindowTitle("Initial Spine Help")

        self.messageDialog.resize(500, 700)
        self.messageDialog.show()
        messageLayout = QtWidgets.QVBoxLayout(self.messageDialog)
        messageLayout.setContentsMargins(0, 0, 0, 0)
        helpText = QtWidgets.QTextEdit()
        helpText.setReadOnly(True)
        helpText.setStyleSheet("background-color: rgb(255, 255, 255);")
        helpText.setStyleSheet(""
                               "border: 20px solid black;"
                               "background-color: black"
                               "")
        # testLabel = QtWidgets.QLabel("TESTING")
        helpText.textCursor().insertHtml("""
<h1><span style="color: #ff6600;">Creating Initial Spine Joints</span></h1>
<p><span style="font-weight: 400;">This section is for creating or defining </span><em><span style="font-weight: 400;">Spine Initialization Joints.</span></em></p>
<p><span style="font-weight: 400;">These joints will inform the rigging module about the locations of spine joints and pass various options through extra attributes.</span></p>
<h3><strong><span style="color: #ff6600;">How To use?</span></strong></h3>
<p><span style="font-weight: 400;">Pressing the <em>Create</em>&nbsp;button will create number of joints defined by the </span><span style="font-weight: 400; color: #800080;"><strong>Segments</strong> </span><span style="font-weight: 400;">value.</span></p>
<p><span style="font-weight: 400;">Pressing the CTRL will change the mode to define mode which allows defining pre-existing joints as spine.</span></p>
<p><span style="font-weight: 400;">To define existing joints, first select all the joints that you wish to define with the correct order (starting from the root of spine), then CTRL+click <em>Create</em>&nbsp;button.</span></p>
<p><strong><span style="color: #800080;">Segments</span></strong><span style="font-weight: 400;"> value is </span><strong>not </strong><span style="font-weight: 400;">the final resolution of the spine rig. <strong><span style="color: #800080;">Segments</span> </strong>are used to tell the rig module, where and how many controllers will be on the spine rig.</span></p>
<h3><span style="color: #ff6600;">What next?</span></h3>
<p><span style="font-weight: 400;">After creating (or defining) the initial spine joints, various options can be reached through the Spine Root. These options are stored in extra attributes. During the rigging process, these options will be derived by the rigging module.</span></p>
<p><span style="font-weight: 400;">These extra attributes are:</span></p>
<p><span style="font-weight: 400;"><span style="color: #3366ff;"><strong>Resolution:</strong></span>&nbsp;</span><span style="font-weight: 400;">This is the actual final joint resolution for the spine deformation joints.</span></p>
<p><span style="font-weight: 400;"><span style="color: #3366ff;"><strong>DropOff:</strong></span>&nbsp;</span><span style="font-weight: 400;">This value will change the way the controllers are affecting the spline IK chain. Usually the default value is ok. If the rig have too many segments (This means more controllers will be created) then tweaking this value may be necessary.</span></p>

        """)
        messageLayout.addWidget(helpText)



        # msg = QtWidgets.QMessageBox()
        # # msg.setIcon(QtWidgets.QMessageBox.Help)
        #
        # title = ""
        # message = ""
        # details = ""
        #
        # if item == "Spine":
        #     message = """
        #     Spine initial:
        #     Create button will place a set of initial joints defined as 'Spine'
        #
        #     The count of the initial joints are defined by 'Segments' value. These 'segments' are not the resolution of the spine. This will simply tell the rig module where the controller curves will be.
        #     In short, 'segments' value will define how many controllers will be along the spine.
        #
        #     """
        #     title = "Spine Initial"
        #
        #     # print message
        #
        # else:
        #     return
        #
        # msg.setWindowTitle(title)
        # msg.setInformativeText(message)
        # # msg.setDetailedText(details)
        # retval = msg.exec_()

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
        self.tailGroupBox.setFixedSize(210, 130)

        layout = QtWidgets.QHBoxLayout()
        sgmSubLayout = QtWidgets.QHBoxLayout()

        self.tailCreateBtn = QtWidgets.QPushButton("Create", minimumSize=(QtCore.QSize(self.wSize, self.hSize)), maximumSize=(QtCore.QSize(self.wSize, self.hSize)), parent=self)
        tailSegLb = QtWidgets.QLabel("Segments")
        self.tailSegInt = QtWidgets.QSpinBox(maximumSize=(QtCore.QSize(40, 20)), value=3, minimum=0)

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
        self.tentacleGroupBox.setFixedSize(210, 130)

        layout = QtWidgets.QHBoxLayout()
        sgmSubLayout = QtWidgets.QHBoxLayout()
        self.tentacleCreateBtn = QtWidgets.QPushButton("Create", minimumSize=(QtCore.QSize(self.wSize, self.hSize)), maximumSize=(QtCore.QSize(self.wSize, self.hSize)), parent=self)
        tentacleSegLb = QtWidgets.QLabel("Seg.")
        self.tentacleSegInt = QtWidgets.QSpinBox(maximumSize=(QtCore.QSize(40, 20)), value=3, minimum=1)

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
        self.bipedGroupBox.setFixedSize(210, 100)

        layout = QtWidgets.QHBoxLayout()

        self.bipedCreateBtn = QtWidgets.QPushButton("Create", minimumSize=(QtCore.QSize(self.wSize, self.hSize)), maximumSize=(QtCore.QSize(self.wSize, self.hSize)), parent=self)

        bipedFingerLb = QtWidgets.QLabel("Fingers")
        self.fingerSegInt = QtWidgets.QSpinBox(maximumSize=(QtCore.QSize(40, 20)), value=5, minimum=1, maximum=5)
        bipedSpineLb = QtWidgets.QLabel("Spine Segs")
        self.bipedSpineSegsInt = QtWidgets.QSpinBox(maximumSize=(QtCore.QSize(40, 20)), value=3, minimum=1)
        bipedNeckLb = QtWidgets.QLabel("Neck Segs")
        self.bipedNeckSegsInt = QtWidgets.QSpinBox(maximumSize=(QtCore.QSize(40, 20)), value=1, minimum=1)

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

    def initRootUI(self):
        self.rootGroupBox = QtWidgets.QGroupBox()
        self.rootGroupBox.setFixedSize(210, 100)
        self.rootGroupBox.setAlignment(QtCore.Qt.AlignRight)
        layout = QtWidgets.QHBoxLayout()
        self.rootCreateBtn = QtWidgets.QPushButton("Create", minimumSize=(QtCore.QSize(self.wSize, self.hSize)), maximumSize=(QtCore.QSize(self.wSize, self.hSize)), parent=self)

        layout.addWidget(self.rootCreateBtn)
        layout.setAlignment(QtCore.Qt.AlignRight)
        self.rootCreateBtn.clicked.connect(self.createRoot)

        self.rootGroupBox.setLayout(layout)
        self.rootGroupBox.setHidden(True)
        self.initBoneslayout.addWidget(self.rootGroupBox)

    def createBiped(self):
        pm.undoInfo(openChunk=True)
        self.initSkeleton.initHumanoid(fingers=self.fingerSegInt.value(), spineSegments=self.bipedSpineSegsInt.value(), neckSegments=self.bipedNeckSegsInt.value())
        pm.undoInfo(closeChunk=True)

    def createArm(self):
        pm.undoInfo(openChunk=True)
        side = ""
        if self.armSideLeft.isChecked():
            side = "left"
        elif self.armSideRight.isChecked():
            side = "right"
        elif self.armSideCenter.isChecked():
            side = "center"
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
        elif self.legSideCenter.isChecked():
            side = "center"
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

    def createRoot(self):
        pm.undoInfo(openChunk=True)
        self.initSkeleton.initLimb("root", defineAs=self.defineAs)
        pm.undoInfo(closeChunk=True)

    def rig(self):
        pm.undoInfo(openChunk=True)
        self.progressBar()
        # self.progress_Dialog.show()
        self.rigger.__init__(settingsData=self.settingsData, progressBar=self.progress_progressBar)
        self.rigger.startBuilding(createAnchors=self.isCreateAnchorsChk.isChecked())
        self.progress_Dialog.close()
        pm.undoInfo(closeChunk=True)

    def addRig(self):
        pm.undoInfo(openChunk=True)
        # self.rigger.__init__()
        self.progressBar()
        self.rigger.__init__(settingsData=self.settingsData, progressBar=self.progress_progressBar)
        self.rigger.createlimbs(addLimb=True)
        self.progress_Dialog.close()
        pm.undoInfo(closeChunk=True)

    def keyPressEvent(self, event):
        ## If Ctrl is pressed, change the button labels
        if event.key() == 16777249:
            self.defineAs = True
            text = "Define As"
            self.spineCreateBtn.setText(text)
            self.neckCreateBtn.setText(text)
            self.armCreateBtn.setText(text)
            self.fingerCreateBtn.setText(text)
            self.legCreateBtn.setText(text)
            self.tailCreateBtn.setText(text)
            self.tentacleCreateBtn.setText(text)

    def keyReleaseEvent(self, event):
        if event.key() == 16777249:
            text = "Create"
            self.defineAs = False
            self.spineCreateBtn.setText(text)
            self.neckCreateBtn.setText(text)
            self.armCreateBtn.setText(text)
            self.fingerCreateBtn.setText(text)
            self.legCreateBtn.setText(text)
            self.tailCreateBtn.setText(text)
            self.tentacleCreateBtn.setText(text)

    def hideToggle(self, UI):
        # print UI
        if UI.isVisible():
            UI.setHidden(True)
        else:
            UI.setHidden(False)

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

# testUI().show()

