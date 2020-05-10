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
        self.resize(570, 400)
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
        self.splitter.setSizes([sizes[0] * 0.4, sizes[1] * 1.6])


    def buildBarsUI(self):
        self.menubar = QtWidgets.QMenuBar(self)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 570, 21))
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

        self.L_guides_listWidget = QtWidgets.QListWidget(L_splitter_layoutWidget)
        guides_font = QtGui.QFont()
        guides_font.setPointSize(12)
        guides_font.setBold(True)
        self.L_guides_listWidget.setFont(guides_font)

        ## SAMPLE [Start]
        self.L_guides_listWidget.addItems(self.guide.valid_limbs)

        ## SAMPLE [End]

        L_guides_vLay.addWidget(self.L_guides_listWidget)

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
        R_guides_WidgetContents.setGeometry(QtCore.QRect(0, 0, 243, 310))
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











