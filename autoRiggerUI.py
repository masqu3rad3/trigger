import pymel.core as pm

import Qt
from Qt import QtWidgets, QtCore, QtGui
from maya import OpenMayaUI as omui
import initials as init

reload(init)
import scratch

reload(scratch)

import contIcons as icon
reload(icon)

import mrCubic
reload(mrCubic)

import math

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


# class mainUI(MayaQWidgetDockableMixin, QtWidgets.QMainWindow):
class mainUI(QtWidgets.QMainWindow):
    def __init__(self):
        for entry in QtWidgets.QApplication.allWidgets():
            if entry.objectName() == windowName:
                entry.close()
        parent = getMayaMainWindow()
        # parent = None
        super(mainUI, self).__init__(parent=parent)

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
        file = bar.addMenu("Settings")
        ### file actions
        generalSettings = QtWidgets.QAction("&General Settings", self)
        # generalSettings.triggered.connect(self.generalSettingsUI)
        initialSettings = QtWidgets.QAction("&Initial Joint Settings", self)
        # initialSettings.triggered.connect(self.initialSettingsUI)
        rigSettings = QtWidgets.QAction("&Rig Settings", self)
        # rigSettings.triggered.connect(self.rigSettingsUI)

        file.addAction(generalSettings)
        file.addAction(initialSettings)
        file.addAction(rigSettings)

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

        self.initSkeleton = init.initialJoints()
        self.rigger = scratch.LimbBuilder()

        self.layout.setContentsMargins(0, 0, 0, 0)

        self.setMinimumSize(250, 100)
        self.resize(250, 500)

        self.buildUI()


        ### new ###
        # self.show(dockable=True, floating=False, area='left')

    def dock_ui(self):
        if pm.dockControl('T-RiggerDock', q=1, ex=1):
            pm.deleteUI('T-RiggerDock')
        allowedAreas = ['right', 'left']
        try:
            floatingLayout = pm.paneLayout(configuration='single', width=250, height=400)
        except RuntimeError:
            self.m_logger.warning("Skipping docking. Restart to dock.")
            self.show()
            return False
        pm.dockControl('T-RiggerDock', area='left', allowedArea=allowedAreas,
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

        self.tabWidget.addTab(self.initBonesTab, "Init Bones")
        self.tabWidget.addTab(self.rigTab, "Rigging")

        self.initBonesUI()
        self.rigUI()
        # layout = QtWidgets.QVBoxLayout(self)


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
    # def replaceControllerUI(self):
    #     self.RCDialog = QtWidgets.QDialog(parent=self)
    #     self.RCDialog.setWindowTitle("Replace Controller")
    #
    #     RCLayout = QtWidgets.QVBoxLayout(self)
    #
    #     iconNames = [i[0] for i in self.all_iconFunctions]
    #     self.typeDropDown = QtWidgets.QComboBox(minimumSize = (QtCore.QSize(self.wSize / 3, self.hSize)), maximumSize = (QtCore.QSize(self.wSize / 3, self.hSize)))
    #
    #     layout.addWidget(self.typeDropDown)
    #
    #     self.typeDropDown.addItems(iconNames)


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
        label = QtWidgets.QLabel("Select a Root Joint -> hit Rig Button")
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
        addToRigBtn = QtWidgets.QPushButton("Add To Rig")

        # ## Add widgets to the group layout
        addGrpLayout.addWidget(addlabel)
        addGrpLayout.addWidget(addToRigBtn)
        #
        # ## Connect the button signal to the rig creation
        addToRigBtn.clicked.connect(self.addRig)
        ## Add groupbox under the tabs main layout
        self.riglayout.addWidget(addLimbGrpBox)

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
        self.tailSegInt = QtWidgets.QSpinBox(maximumSize=(QtCore.QSize(40, 20)), value=3, minimum=1)

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
        self.rigger.__init__()
        self.rigger.startBuilding(createAnchors=self.isCreateAnchorsChk.isChecked())
        pm.undoInfo(closeChunk=True)

    def addRig(self):
        pm.undoInfo(openChunk=True)
        # self.rigger.__init__()
        self.rigger.createLimbs(addLimb=True)
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

# testUI().show()

