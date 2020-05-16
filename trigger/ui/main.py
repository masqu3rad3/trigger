"""Main UI for TRigger"""
from trigger.ui import Qt
from trigger.ui.Qt import QtWidgets, QtCore, QtGui

from trigger.guides import initials
from trigger.rig import builder

from maya import OpenMayaUI as omui

if Qt.__binding__ == "PySide":
    from shiboken import wrapInstance
    from Qt.QtCore import Signal
elif Qt.__binding__.startswith('PyQt'):
    from sip import wrapinstance as wrapInstance
    from Qt.Core import pyqtSignal as Signal
else:
    from shiboken2 import wrapInstance
    from Qt.QtCore import Signal

WINDOW_NAME = "TRigger"


def getMayaMainWindow():
    """
    Gets the memory adress of the main window to connect Qt dialog to it.
    Returns:
        (long) Memory Adress
    """
    win = omui.MQtUtil_mainWindow()
    ptr = wrapInstance(long(win), QtWidgets.QMainWindow)
    return ptr


class MainUI(QtWidgets.QMainWindow):
    def __init__(self):
        for entry in QtWidgets.QApplication.allWidgets():
            try:
                if entry.objectName() == WINDOW_NAME:
                    entry.close()
            except (AttributeError, TypeError):
                pass
        parent = getMayaMainWindow()
        super(MainUI, self).__init__(parent=parent)

        # core ui
        self.setWindowTitle(WINDOW_NAME)
        self.setObjectName(WINDOW_NAME)
        self.resize(650, 400)
        self.centralwidget = QtWidgets.QWidget(self)
        self.centralwidget.setObjectName("centralwidget")
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setCentralWidget(self.centralwidget)

        # create guide and rig objects
        self.guide = initials.Initials()
        self.rig = builder.Builder()

        # Build the UI elements
        self.buildTabsUI()
        self.buildBarsUI()
        self.buildGuidesUI()
        self.show()

        self.populate_guides()


        # Create a QTimer
        self.timer = QtCore.QTimer()
        # Connect it to f
        self.timer.timeout.connect(self.force_update)
        # Call f() every 5 seconds
        self.timer.start(1000)


        # Splitter size hack
        # this must be done after the show()
        sizes = self.splitter.sizes()
        # print sizes
        # self.splitter.setSizes([sizes[0] * 0.3, sizes[1] * 1.0])
        self.splitter.setSizes([sizes[0] * 0.3, sizes[1] * 1.0, sizes[2] * 1.5])



    def buildBarsUI(self):
        self.menubar = QtWidgets.QMenuBar(self)
        # self.menubar.setGeometry(QtCore.QRect(0, 0, 570, 21))
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setTitle("File")
        self.setMenuBar(self.menubar)

        self.statusbar = QtWidgets.QStatusBar(self)
        self.setStatusBar(self.statusbar)

        self.Import_Guides_action = QtWidgets.QAction(self, text="Import Guides")
        self.Export_Guides_action = QtWidgets.QAction(self, text="Export Guides")
        self.Save_Session_action = QtWidgets.QAction(self, text="Save Session")
        self.Load_Session_action = QtWidgets.QAction(self, text="Load Session")
        self.New_Session_action = QtWidgets.QAction(self, text="New Session")
        self.Settings_action = QtWidgets.QAction(self, text="Settings")

        self.menuFile.addAction(self.New_Session_action)
        self.menuFile.addAction(self.Save_Session_action)
        self.menuFile.addAction(self.Load_Session_action)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.Import_Guides_action)
        self.menuFile.addAction(self.Export_Guides_action)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.Settings_action)
        self.menubar.addAction(self.menuFile.menuAction())


    def  buildTabsUI(self):
        self.centralWidget_vLay = QtWidgets.QVBoxLayout(self.centralwidget)  # this is only to fit the tab widget
        self.centralWidget_vLay.setSpacing(0)
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.guides_tab = QtWidgets.QWidget()
        self.tabWidget.addTab(self.guides_tab, "Guides")

        self.rigging_tab = QtWidgets.QWidget()
        self.tabWidget.addTab(self.rigging_tab, "Rigging")
        self.centralWidget_vLay.addWidget(self.tabWidget)

    def buildGuidesUI(self):
        guides_tab_vlay = QtWidgets.QVBoxLayout(self.guides_tab)
        self.splitter = QtWidgets.QSplitter(self.guides_tab)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        guides_tab_vlay.addWidget(self.splitter)

        L_splitter_layoutWidget = QtWidgets.QWidget(self.splitter)
        L_guides_vLay = QtWidgets.QVBoxLayout(L_splitter_layoutWidget)
        L_guides_vLay.setContentsMargins(0, 0, 0, 0)


        module_guides_lbl = QtWidgets.QLabel(L_splitter_layoutWidget)
        module_guides_lbl.setFrameShape(QtWidgets.QFrame.StyledPanel)
        module_guides_lbl.setFrameShadow(QtWidgets.QFrame.Plain)
        module_guides_lbl.setText("Module Guides")
        module_guides_lbl.setAlignment(QtCore.Qt.AlignCenter)
        L_guides_vLay.addWidget(module_guides_lbl)

        ########################################################################



        self.module_create_splitter = QtWidgets.QSplitter(L_splitter_layoutWidget)
        L_guides_vLay.addWidget(self.module_create_splitter)
        # self.module_create_splitter.setGeometry(QtCore.QRect(30, 30, 473, 192))
        self.module_create_splitter.setOrientation(QtCore.Qt.Horizontal)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.module_create_splitter.sizePolicy().hasHeightForWidth())
        self.module_create_splitter.setSizePolicy(sizePolicy)

        self.verticalLayoutWidget_2 = QtWidgets.QWidget(self.module_create_splitter)

        self.guides_create_vLay = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_2)
        self.guides_create_vLay.setContentsMargins(0, 0, 0, 0)

        self.guides_sides_hLay = QtWidgets.QHBoxLayout()

        self.guides_sides_L_rb = QtWidgets.QRadioButton(self.verticalLayoutWidget_2)
        self.guides_sides_L_rb.setText("L")
        self.guides_sides_hLay.addWidget(self.guides_sides_L_rb)

        self.guides_sides_R_rb = QtWidgets.QRadioButton(self.verticalLayoutWidget_2)
        self.guides_sides_R_rb.setText("R")
        self.guides_sides_hLay.addWidget(self.guides_sides_R_rb)

        self.guides_sides_Both_rb = QtWidgets.QRadioButton(self.verticalLayoutWidget_2)
        self.guides_sides_Both_rb.setText("Both")
        self.guides_sides_hLay.addWidget(self.guides_sides_Both_rb)
        self.guides_sides_Both_rb.setChecked(True)

        self.guides_sides_Auto_rb = QtWidgets.QRadioButton(self.verticalLayoutWidget_2)
        self.guides_sides_Auto_rb.setText("Auto")
        self.guides_sides_hLay.addWidget(self.guides_sides_Auto_rb)

        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.guides_sides_hLay.addItem(spacerItem)
        self.guides_create_vLay.addLayout(self.guides_sides_hLay)
        
        button_scrollArea = QtWidgets.QScrollArea()
        button_scrollArea.setFrameShape(QtWidgets.QFrame.NoFrame)
        button_scrollArea.setFrameShadow(QtWidgets.QFrame.Sunken)
        button_scrollArea.setWidgetResizable(True)

        button_scrollArea_WidgetContents = QtWidgets.QWidget()
        button_scrollArea_vLay = QtWidgets.QVBoxLayout(button_scrollArea_WidgetContents)
        button_scrollArea.setWidget(button_scrollArea_WidgetContents)
        self.guides_create_vLay.addWidget(button_scrollArea)

        module_settings_formLayout = QtWidgets.QFormLayout()
        button_scrollArea_vLay.addLayout(module_settings_formLayout)

        self.guide_buttons_vLay = QtWidgets.QVBoxLayout()
        self.guide_buttons_vLay.setSpacing(2)

        ####### Module Buttons ########## [START]

        for module in sorted(self.guide.valid_limbs):
            guide_button_hLay = QtWidgets.QHBoxLayout()
            guide_button_hLay.setSpacing(2)
            guide_button_pb = QtWidgets.QPushButton(self.verticalLayoutWidget_2)
            guide_button_pb.setText(module.capitalize())
            guide_button_hLay.addWidget(guide_button_pb)
            segments_sp = QtWidgets.QSpinBox(self.verticalLayoutWidget_2)
            segments_sp.setObjectName("sp_%s" %module)
            segments_sp.setMinimum(1)
            segments_sp.setValue(3)
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(segments_sp.sizePolicy().hasHeightForWidth())
            segments_sp.setSizePolicy(sizePolicy)
            guide_button_hLay.addWidget(segments_sp)
            if not self.guide.module_dict[module].get("multi_guide"):
                segments_sp.setValue(3)
                segments_sp.setEnabled(False)

            self.guide_buttons_vLay.addLayout(guide_button_hLay)

            ############ SIGNALS ############### [Start]
            # following signal connection finds the related spinbox using the object name
            guide_button_pb.clicked.connect(lambda ignore=module, limb=module: self.on_create_guide(limb, segments=self.verticalLayoutWidget_2.findChild(QtWidgets.QSpinBox, "sp_%s" %limb).value()))
            ############ SIGNALS ############### [End]

        ####### Module Buttons ########## [End]

        ####### Preset Buttons ########## [Start]
        preset_spacer = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.guide_buttons_vLay.addItem(preset_spacer)

        preset_lbl = QtWidgets.QLabel()
        preset_lbl.setFrameShape(QtWidgets.QFrame.StyledPanel)
        preset_lbl.setFrameShadow(QtWidgets.QFrame.Plain)
        preset_lbl.setText("Presets")
        preset_lbl.setAlignment(QtCore.Qt.AlignCenter)
        self.guide_buttons_vLay.addWidget(preset_lbl)

        humanoid_button_pb = QtWidgets.QPushButton(self.verticalLayoutWidget_2, text="Humanoid")
        self.guide_buttons_vLay.addWidget(humanoid_button_pb)

        humanoid_button_pb.clicked.connect(lambda: self.guide.initHumanoid())



        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.guide_buttons_vLay.addItem(spacerItem1)
        # self.guides_create_vLay.addLayout(self.guide_buttons_vLay)
        button_scrollArea_vLay.addLayout(self.guide_buttons_vLay)


        # self.guides_list_listWidget = QtWidgets.QListWidget(self.module_create_splitter)
        # self.guides_list_treeWidget = QtWidgets.QTreeWidget(self.module_create_splitter, sortingEnabled=True, rootIsDecorated=False)
        self.guides_list_treeWidget = QtWidgets.QTreeWidget(self.splitter, sortingEnabled=True, rootIsDecorated=False)
        self.guides_list_treeWidget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.guides_list_treeWidget.sizePolicy().hasHeightForWidth())
        self.guides_list_treeWidget.setSizePolicy(sizePolicy)

        # columng for guides list
        colums = ["Type", "Side", "Root Joint"]
        header = QtWidgets.QTreeWidgetItem(colums)
        self.guides_list_treeWidget.setHeaderItem(header)
        self.guides_list_treeWidget.setColumnWidth(0, 80)
        self.guides_list_treeWidget.setColumnWidth(1, 20)

        # font = QtGui.QFont()
        # font.setPointSize(12)
        # font.setBold(False)
        # font.setWeight(50)
        # font.setStrikeOut(False)
        # self.guides_list_listWidget.setFont(font)

        # self.guides_list_treeWidget.setMouseTracking(False)
        # self.guides_list_treeWidget.setFrameShape(QtWidgets.QFrame.StyledPanel)
        # self.guides_list_treeWidget.setViewMode(QtWidgets.QListView.ListMode)

        ############# SAMPLE #################### [START]

        # item = QtWidgets.QListWidgetItem()
        # item.setText("Arm")
        # item.setTextAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignVCenter)
        # self.guides_list_listWidget.addItem(item)
        # item = QtWidgets.QListWidgetItem()
        # item.setText("Leg")
        # item.setTextAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignVCenter)
        # self.guides_list_listWidget.addItem(item)
        # item = QtWidgets.QListWidgetItem()
        # item.setText("Tentacle")
        # item.setTextAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignVCenter)
        # self.guides_list_listWidget.addItem(item)


        ############# SAMPLE #################### [End]

        # Guides Right Side
        R_splitter_layoutWidget = QtWidgets.QWidget(self.splitter)
        R_guides_vLay = QtWidgets.QVBoxLayout(R_splitter_layoutWidget)
        R_guides_vLay.setContentsMargins(0, 0, 0, 0)

        guide_properties_lbl = QtWidgets.QLabel(R_splitter_layoutWidget)
        guide_properties_lbl.setFrameShape(QtWidgets.QFrame.StyledPanel)
        guide_properties_lbl.setFrameShadow(QtWidgets.QFrame.Plain)
        guide_properties_lbl.setText("Guide Properties")
        guide_properties_lbl.setAlignment(QtCore.Qt.AlignCenter)
        R_guides_vLay.addWidget(guide_properties_lbl)

        self.R_guides_scrollArea = QtWidgets.QScrollArea(R_splitter_layoutWidget)
        self.R_guides_scrollArea.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.R_guides_scrollArea.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.R_guides_scrollArea.setWidgetResizable(True)

        R_guides_WidgetContents = QtWidgets.QWidget()

        R_guides_scrollArea_vLay = QtWidgets.QVBoxLayout(R_guides_WidgetContents)
        self.R_guides_scrollArea.setWidget(R_guides_WidgetContents)
        R_guides_vLay.addWidget(self.R_guides_scrollArea)


        module_settings_formLayout = QtWidgets.QFormLayout()
        R_guides_scrollArea_vLay.addLayout(module_settings_formLayout)


        ## SAMPLE [Start]

        setting1_lbl = QtWidgets.QLabel(R_guides_WidgetContents, text="Setting1")
        setting1_le = QtWidgets.QLineEdit(R_guides_WidgetContents)
        module_settings_formLayout.addRow(setting1_lbl, setting1_le)

        setting2_lbl = QtWidgets.QLabel(R_guides_WidgetContents, text="Setting2")
        setting2_combo = QtWidgets.QComboBox(R_guides_WidgetContents)
        module_settings_formLayout.addRow(setting2_lbl, setting2_combo)

        setting3_lbl = QtWidgets.QLabel(R_guides_WidgetContents, text="Setting3")
        setting3_chk = QtWidgets.QCheckBox(R_guides_WidgetContents)
        module_settings_formLayout.addRow(setting3_lbl, setting3_chk)

        ## SAMPLE [End]

        # ## Discarded buttons [Start]
        # guide_buttons_hLay = QtWidgets.QHBoxLayout()
        # R_guides_scrollArea_vLay.addLayout(guide_buttons_hLay)
        #
        # define_selected_pb = QtWidgets.QPushButton(R_guides_WidgetContents)
        # define_selected_pb.setText("Define Selected")
        # guide_buttons_hLay.addWidget(define_selected_pb)
        #
        # create_guide_pb = QtWidgets.QPushButton(R_guides_WidgetContents)
        # create_guide_pb.setText("Create Guide")
        # guide_buttons_hLay.addWidget(create_guide_pb)
        # ## Discarded buttons [End]

        # sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # sizePolicy.setHorizontalStretch(1)
        # sizePolicy.setVerticalStretch(1)
        # self.splitter.setSizePolicy(sizePolicy)

        # sizes = self.splitter.sizes()
        # print("3", sizes)
        # splitter.setSizes([sizes[0] * 1.6, sizes[1] * 0.4])
        # splitter.setStretchFactor(0, 0.2)
        # splitter.setStretchFactor(1, 8)

        ## SIGNALS
        self.guides_list_treeWidget.currentItemChanged.connect(self.on_guide_change)

    def populate_guides(self):

        self.guides_list_treeWidget.blockSignals(True)
        if self.guides_list_treeWidget.currentItem():
            selected_root_jnt = self.guides_list_treeWidget.currentItem().text(2)
        else:
            selected_root_jnt = None

        self.guides_list_treeWidget.clear()
        roots_dict_list = self.guide.get_scene_roots()
        for item in roots_dict_list:
            if item["side"] == "C":
                color = QtGui.QColor(255, 255, 0, 255)
            elif item["side"] == "L":
                color = QtGui.QColor(0, 100, 255, 255)
            else:
                color = QtGui.QColor(255, 100, 0, 255)
            tree_item = QtWidgets.QTreeWidgetItem(self.guides_list_treeWidget, [item["module_name"], item["side"], item["root_joint"]])
            if item["root_joint"] == selected_root_jnt:
                self.guides_list_treeWidget.setCurrentItem(tree_item)
            tree_item.setForeground(0, color)

        # print(selected_root_jnt)
        # if selected_root_jnt:


        # self.guides_list_treeWidget.setCurrentItem(currentItem)
        self.guides_list_treeWidget.blockSignals(False)

    def on_create_guide(self, limb_name, *args, **kwargs):
        # print(limb_name)
        # print(kwargs)
        if limb_name == "humanoid":
            self.guide.initHumanoid()
        else:
            # get side
            if self.guides_sides_L_rb.isChecked():
                side="left"
            elif self.guides_sides_R_rb.isChecked():
                side="right"
            elif self.guides_sides_Both_rb.isChecked():
                side="both"
            elif self.guides_sides_Auto_rb.isChecked():
                side="auto"
            else:
                side="center"
            self.guide.initLimb(limb_name, whichSide= side, **kwargs)

        self.populate_guides()


    def on_guide_change(self):

        row = self.guides_list_treeWidget.currentIndex().row()
        if row == -1:
            return
        self.guide.select_root(str(self.guides_list_treeWidget.currentItem().text(2)))
        self.populate_properties()

    def populate_properties(self):
        pass

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

    def force_update(self):
        # print(self.centralwidget.hasFocus())
        if self.R_guides_scrollArea.hasFocus() or self.guides_list_treeWidget.hasFocus():
            return
        self.populate_guides()