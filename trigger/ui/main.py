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

        # Splitter size hack
        # this must be done after the show()
        sizes = self.splitter.sizes()
        self.splitter.setSizes([sizes[0] * 0.7, sizes[1] * 1.3])

        self.populate_guides()


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
            segments_sample_sp = QtWidgets.QSpinBox(self.verticalLayoutWidget_2)
            segments_sample_sp.setMinimum(1)
            segments_sample_sp.setValue(3)
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(segments_sample_sp.sizePolicy().hasHeightForWidth())
            segments_sample_sp.setSizePolicy(sizePolicy)
            guide_button_hLay.addWidget(segments_sample_sp)
            if not self.guide.module_dict[module].get("multi_guide"):
                segments_sample_sp.setValue(3)
                segments_sample_sp.setEnabled(False)

            self.guide_buttons_vLay.addLayout(guide_button_hLay)

        ####### Module Buttons ########## [End]

        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.guide_buttons_vLay.addItem(spacerItem1)
        # self.guides_create_vLay.addLayout(self.guide_buttons_vLay)
        button_scrollArea_vLay.addLayout(self.guide_buttons_vLay)

        ####### SAMMPLE ########## [End]
        self.guides_list_listWidget = QtWidgets.QListWidget(self.module_create_splitter)
        # font = QtGui.QFont()
        # font.setPointSize(12)
        # font.setBold(False)
        # font.setWeight(50)
        # font.setStrikeOut(False)
        # self.guides_list_listWidget.setFont(font)
        self.guides_list_listWidget.setMouseTracking(False)
        self.guides_list_listWidget.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.guides_list_listWidget.setViewMode(QtWidgets.QListView.ListMode)

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

        R_guides_scrollArea = QtWidgets.QScrollArea(R_splitter_layoutWidget)
        R_guides_scrollArea.setFrameShape(QtWidgets.QFrame.NoFrame)
        R_guides_scrollArea.setFrameShadow(QtWidgets.QFrame.Sunken)
        R_guides_scrollArea.setWidgetResizable(True)

        R_guides_WidgetContents = QtWidgets.QWidget()
        R_guides_scrollArea_vLay = QtWidgets.QVBoxLayout(R_guides_WidgetContents)
        R_guides_scrollArea.setWidget(R_guides_WidgetContents)
        R_guides_vLay.addWidget(R_guides_scrollArea)


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

        guide_buttons_hLay = QtWidgets.QHBoxLayout()
        R_guides_scrollArea_vLay.addLayout(guide_buttons_hLay)

        define_selected_pb = QtWidgets.QPushButton(R_guides_WidgetContents)
        define_selected_pb.setText("Define Selected")
        guide_buttons_hLay.addWidget(define_selected_pb)

        create_guide_pb = QtWidgets.QPushButton(R_guides_WidgetContents)
        create_guide_pb.setText("Create Guide")
        guide_buttons_hLay.addWidget(create_guide_pb)

        # sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # sizePolicy.setHorizontalStretch(1)
        # sizePolicy.setVerticalStretch(1)
        # self.splitter.setSizePolicy(sizePolicy)

        # sizes = self.splitter.sizes()
        # print("3", sizes)
        # splitter.setSizes([sizes[0] * 1.6, sizes[1] * 0.4])
        # splitter.setStretchFactor(0, 0.2)
        # splitter.setStretchFactor(1, 8)

    def populate_guides(self):
        self.guides_list_listWidget.clear()
        guide_roots = self.guide.get_scene_roots()
        print("asn", guide_roots)
        self.guides_list_listWidget.addItems(guide_roots)








