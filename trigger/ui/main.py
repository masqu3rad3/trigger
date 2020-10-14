"""Main UI for TRigger"""
import subprocess
import platform
import sys, os
import importlib
from functools import wraps
from trigger.ui import Qt
from trigger.ui.Qt import QtWidgets, QtCore, QtGui
from trigger.ui import model_ctrl

# from trigger.base import initials
from trigger.core import compatibility as compat
from trigger.base import session
from trigger.base import actions_session


from maya import OpenMayaUI as omui

if Qt.__binding__ == "PySide":
    from shiboken import wrapInstance
elif Qt.__binding__.startswith('PyQt'):
    from sip import wrapinstance as wrapInstance
else:
    from shiboken2 import wrapInstance

from trigger.core import feedback

FEEDBACK = feedback.Feedback(logger_name=__name__)

WINDOW_NAME = "TRigger"

# TODO: TEMPORARY
from PySide2 import QtCore, QtGui, QtWidgets

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


class MainUI(QtWidgets.QMainWindow):

    # create guide and rig objects
    # guide = initials.Initials()
    actions_handler = actions_session.ActionsSession()
    guides_handler = session.Session()

    def __init__(self):
        for entry in QtWidgets.QApplication.allWidgets():
            try:
                if entry.objectName() == WINDOW_NAME:
                    entry.close()
            except (AttributeError, TypeError):
                pass
        parent = getMayaMainWindow()
        super(MainUI, self).__init__(parent=parent)
        # self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.installEventFilter(self)
        self.force = False
        # core ui
        self.setWindowTitle(WINDOW_NAME)
        self.setObjectName(WINDOW_NAME)
        self.resize(1000, 600)
        self.centralwidget = QtWidgets.QWidget(self)
        self.centralwidget.setObjectName("centralwidget")
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setCentralWidget(self.centralwidget)


        # Build the UI elements
        self.buildTabsUI()
        self.buildBarsUI()
        self.buildRiggingUI()
        self.buildGuidesUI()


        self.populate_guides()


        # Create a QTimer
        self.timer = QtCore.QTimer()
        # Connect it to f
        self.timer.timeout.connect(self.force_update)
        # Call f() every 5 seconds
        self.timer.start(1000)

        self.splitter.setStretchFactor(0, 10)
        self.splitter.setStretchFactor(1, 40)
        self.splitter.setStretchFactor(1, 50)

        self.rig_LR_splitter.setStretchFactor(0, 10)
        self.rig_LR_splitter.setStretchFactor(1, 90)

        self.show()


    def buildBarsUI(self):
        self.menubar = QtWidgets.QMenuBar(self)
        # self.menubar.setGeometry(QtCore.QRect(0, 0, 570, 21))
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setTitle("File")
        self.setMenuBar(self.menubar)

        self.statusbar = QtWidgets.QStatusBar(self)
        self.setStatusBar(self.statusbar)

        self.new_trigger_action = QtWidgets.QAction(self, text="New Trigger Session")
        self.open_trigger_action = QtWidgets.QAction(self, text="Open Trigger Session")
        self.save_trigger_action = QtWidgets.QAction(self, text="Save Trigger Session")
        self.save_as_trigger_action = QtWidgets.QAction(self, text="Save As Trigger Session")
        self.import_guides_action = QtWidgets.QAction(self, text="Import Guides")
        self.export_guides_action = QtWidgets.QAction(self, text="Export Guides")
        self.settings_action = QtWidgets.QAction(self, text="Settings")
        self.reset_scene_action = QtWidgets.QAction(self, text="Reset Scene")

        self.menuFile.addAction(self.new_trigger_action)
        self.menuFile.addAction(self.open_trigger_action)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.save_trigger_action)
        self.menuFile.addAction(self.save_as_trigger_action)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.import_guides_action)
        self.menuFile.addAction(self.export_guides_action)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.settings_action)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.reset_scene_action)

        self.menubar.addAction(self.menuFile.menuAction())

    def buildTabsUI(self):
        self.centralWidget_vLay = QtWidgets.QVBoxLayout(self.centralwidget)  # this is only to fit the tab widget
        self.centralWidget_vLay.setSpacing(0)
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)

        self.rigging_tab = QtWidgets.QWidget()
        self.tabWidget.addTab(self.rigging_tab, "Actions")

        self.guides_tab = QtWidgets.QWidget()
        self.tabWidget.addTab(self.guides_tab, "Guides")

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
        self.guides_sides_hLay.setSpacing(3)

        self.guides_sides_C_rb = QtWidgets.QRadioButton()
        self.guides_sides_C_rb.setText("C")
        self.guides_sides_hLay.addWidget(self.guides_sides_C_rb)

        self.guides_sides_L_rb = QtWidgets.QRadioButton()
        self.guides_sides_L_rb.setText("L")
        self.guides_sides_hLay.addWidget(self.guides_sides_L_rb)

        self.guides_sides_R_rb = QtWidgets.QRadioButton()
        self.guides_sides_R_rb.setText("R")
        self.guides_sides_hLay.addWidget(self.guides_sides_R_rb)

        self.guides_sides_Both_rb = QtWidgets.QRadioButton()
        self.guides_sides_Both_rb.setText("Both")
        self.guides_sides_hLay.addWidget(self.guides_sides_Both_rb)
        self.guides_sides_Both_rb.setChecked(True)

        self.guides_sides_Auto_rb = QtWidgets.QRadioButton()
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

        self.module_settings_formLayout = QtWidgets.QFormLayout()
        button_scrollArea_vLay.addLayout(self.module_settings_formLayout)

        self.guide_buttons_vLay = QtWidgets.QVBoxLayout()
        self.guide_buttons_vLay.setSpacing(2)

        ####### Module Buttons ########## [START]

        for module in sorted(self.guides_handler.init.valid_limbs):
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
            if not self.guides_handler.init.module_dict[module].get("multi_guide"):
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

        humanoid_button_pb.clicked.connect(lambda: self.on_create_guide("humanoid"))

        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.guide_buttons_vLay.addItem(spacerItem1)
        # self.guides_create_vLay.addLayout(self.guide_buttons_vLay)
        button_scrollArea_vLay.addLayout(self.guide_buttons_vLay)

        self.guides_list_treeWidget = QtWidgets.QTreeWidget(self.splitter, sortingEnabled=True, rootIsDecorated=False)
        self.guides_list_treeWidget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.guides_list_treeWidget.sizePolicy().hasHeightForWidth())
        self.guides_list_treeWidget.setSizePolicy(sizePolicy)

        # columng for guides list
        colums = ["Name", "Side", "Root Joint", "Module"]
        header = QtWidgets.QTreeWidgetItem(colums)
        self.guides_list_treeWidget.setHeaderItem(header)
        self.guides_list_treeWidget.setColumnWidth(0, 80)
        self.guides_list_treeWidget.setColumnWidth(1, 20)

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

        self.R_guides_WidgetContents = QtWidgets.QWidget()

        self.R_guides_scrollArea_vLay = QtWidgets.QVBoxLayout(self.R_guides_WidgetContents)
        R_guides_scrollArea.setWidget(self.R_guides_WidgetContents)
        R_guides_vLay.addWidget(R_guides_scrollArea)


        self.module_settings_formLayout = QtWidgets.QFormLayout()
        self.module_extras_formLayout = QtWidgets.QFormLayout()
        self.R_guides_scrollArea_vLay.addLayout(self.module_settings_formLayout)
        self.R_guides_scrollArea_vLay.addLayout(self.module_extras_formLayout)

        ## PROPERTIES -General [Start]
        #name
        module_name_lbl = QtWidgets.QLabel(self.R_guides_WidgetContents, text="Module Name")
        self.module_name_le = QtWidgets.QLineEdit(self.R_guides_WidgetContents)
        self.module_settings_formLayout.addRow(module_name_lbl, self.module_name_le)

        #up axis
        up_axis_lbl = QtWidgets.QLabel(self.R_guides_WidgetContents, text="Up Axis")
        up_axis_hLay = QtWidgets.QHBoxLayout(spacing=3)

        self.up_axis_sp_list = [QtWidgets.QDoubleSpinBox(self.R_guides_WidgetContents, minimumWidth=40, buttonSymbols=QtWidgets.QAbstractSpinBox.NoButtons) for axis in "XYZ"]
        _ = [up_axis_hLay.addWidget(sp) for sp in self.up_axis_sp_list]
        self.module_settings_formLayout.addRow(up_axis_lbl, up_axis_hLay)
        
        #mirror axis
        mirror_axis_lbl = QtWidgets.QLabel(self.R_guides_WidgetContents, text="Mirror Axis")
        mirror_axis_hLay = QtWidgets.QHBoxLayout(spacing=3)
        self.mirror_axis_sp_list = [QtWidgets.QDoubleSpinBox(self.R_guides_WidgetContents, minimumWidth=40, buttonSymbols=QtWidgets.QAbstractSpinBox.NoButtons) for axis in "XYZ"]
        _ = [mirror_axis_hLay.addWidget(sp) for sp in self.mirror_axis_sp_list]
        self.module_settings_formLayout.addRow(mirror_axis_lbl, mirror_axis_hLay)

        #look axis
        look_axis_lbl = QtWidgets.QLabel(self.R_guides_WidgetContents, text="Look Axis")
        look_axis_hLay = QtWidgets.QHBoxLayout(spacing=3)
        self.look_axis_sp_list = [QtWidgets.QDoubleSpinBox(self.R_guides_WidgetContents, minimumWidth=40, buttonSymbols=QtWidgets.QAbstractSpinBox.NoButtons) for axis in "XYZ"]
        _ = [look_axis_hLay.addWidget(sp) for sp in self.look_axis_sp_list]
        self.module_settings_formLayout.addRow(look_axis_lbl, look_axis_hLay)

        #inherit orientation
        inherit_orientation_lbl = QtWidgets.QLabel(self.R_guides_WidgetContents, text="Inherit Orientation")
        self.inherit_orientation_cb = QtWidgets.QCheckBox(self.R_guides_WidgetContents, text="", checked=True)
        self.module_settings_formLayout.addRow(inherit_orientation_lbl, self.inherit_orientation_cb)

        ## PROPERTIES - General [End]

        self.guide_test_pb = QtWidgets.QPushButton()
        self.guide_test_pb.setText("Test Build Selected Branch")
        guides_tab_vlay.addWidget(self.guide_test_pb)

        ## SIGNALS
        self.guides_list_treeWidget.currentItemChanged.connect(self.on_guide_change)
        # self.module_name_le.textChanged.connect(lambda text=self.module_name_le.text(): self.update_properties("moduleName", text))
        self.module_name_le.textEdited.connect(lambda text=self.module_name_le.text(): self.update_properties("moduleName", text))
        self.module_name_le.editingFinished.connect(self.populate_guides)

        self.up_axis_sp_list[0].valueChanged.connect(lambda num: self.update_properties("upAxisX", num))
        self.up_axis_sp_list[1].valueChanged.connect(lambda num: self.update_properties("upAxisY", num))
        self.up_axis_sp_list[2].valueChanged.connect(lambda num: self.update_properties("upAxisZ", num))
        self.mirror_axis_sp_list[0].valueChanged.connect(lambda num: self.update_properties("mirrorAxisX", num))
        self.mirror_axis_sp_list[1].valueChanged.connect(lambda num: self.update_properties("mirrorAxisY", num))
        self.mirror_axis_sp_list[2].valueChanged.connect(lambda num: self.update_properties("mirrorAxisZ", num))
        self.look_axis_sp_list[0].valueChanged.connect(lambda num: self.update_properties("lookAxisX", num))
        self.look_axis_sp_list[1].valueChanged.connect(lambda num: self.update_properties("lookAxisY", num))
        self.look_axis_sp_list[2].valueChanged.connect(lambda num: self.update_properties("lookAxisZ", num))

        self.inherit_orientation_cb.toggled.connect(lambda state=self.inherit_orientation_cb.isChecked(): self.update_properties("useRefOri", state))

        self.guide_test_pb.clicked.connect(self.build_test_guides)

        # menu items
        self.open_trigger_action.triggered.connect(self.open_trigger)
        self.save_trigger_action.triggered.connect(self.save_trigger)
        self.save_as_trigger_action.triggered.connect(self.save_as_trigger)

        self.export_guides_action.triggered.connect(self.export_guides)
        self.import_guides_action.triggered.connect(self.import_guides)

        self.reset_scene_action.triggered.connect(self.guides_handler.reset_scene)
        self.reset_scene_action.triggered.connect(self.populate_guides)


    def buildRiggingUI(self):
        self.rigging_tab_vLay = QtWidgets.QVBoxLayout(self.rigging_tab)

        self.rig_LR_splitter = QtWidgets.QSplitter(self.rigging_tab)
        self.rig_LR_splitter.setOrientation(QtCore.Qt.Horizontal)


        self.layoutWidget_2 = QtWidgets.QWidget(self.rig_LR_splitter)

        self.rig_actions_vLay = QtWidgets.QVBoxLayout(self.layoutWidget_2)
        self.rig_actions_vLay.setContentsMargins(0, 0, 0, 0)

        self.actions_lbl = QtWidgets.QLabel(self.layoutWidget_2)
        self.actions_lbl.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.actions_lbl.setFrameShadow(QtWidgets.QFrame.Plain)
        self.actions_lbl.setText("Actions")
        self.actions_lbl.setAlignment(QtCore.Qt.AlignCenter)
        self.rig_actions_vLay.addWidget(self.actions_lbl)

        self.rig_action_addremove_hLay = QtWidgets.QHBoxLayout()
        self.rig_actions_vLay.addLayout(self.rig_action_addremove_hLay)
        self.add_action_pb = QtWidgets.QPushButton(self.layoutWidget_2)
        self.add_action_pb.setText("Add")
        self.rig_action_addremove_hLay.addWidget(self.add_action_pb)

        self.delete_action_pb = QtWidgets.QPushButton(self.layoutWidget_2)
        self.delete_action_pb.setText("Delete")
        self.rig_action_addremove_hLay.addWidget(self.delete_action_pb)

        self.move_action_up_pb = QtWidgets.QPushButton(self.layoutWidget_2)
        self.move_action_up_pb.setMaximumSize(QtCore.QSize(50, 16777215))
        self.move_action_up_pb.setText("up")
        self.rig_action_addremove_hLay.addWidget(self.move_action_up_pb)

        self.move_action_down_pb = QtWidgets.QPushButton(self.layoutWidget_2)
        self.move_action_down_pb.setMaximumSize(QtCore.QSize(50, 16777215))
        self.move_action_down_pb.setText("down")
        self.rig_action_addremove_hLay.addWidget(self.move_action_down_pb)

        self.rig_actions_listwidget = QtWidgets.QListWidget(self.layoutWidget_2)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        font.setStrikeOut(False)
        self.rig_actions_listwidget.setFont(font)
        self.rig_actions_listwidget.setMouseTracking(False)
        self.rig_actions_listwidget.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.rig_actions_listwidget.setViewMode(QtWidgets.QListView.ListMode)
        self.rig_actions_vLay.addWidget(self.rig_actions_listwidget)

        self.verticalLayoutWidget_3 = QtWidgets.QWidget(self.rig_LR_splitter)
        self.action_settings_vLay = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_3)
        self.action_settings_vLay.setContentsMargins(0, 0, 0, 0)

        self.action_settings_lbl = QtWidgets.QLabel(self.verticalLayoutWidget_3)
        self.action_settings_lbl.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.action_settings_lbl.setFrameShadow(QtWidgets.QFrame.Plain)
        self.action_settings_lbl.setText("Settings")
        self.action_settings_lbl.setAlignment(QtCore.Qt.AlignCenter)
        self.action_settings_vLay.addWidget(self.action_settings_lbl)

        self.action_settings_scrollArea = QtWidgets.QScrollArea(self.verticalLayoutWidget_3)
        self.action_settings_scrollArea.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.action_settings_scrollArea.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.action_settings_scrollArea.setLineWidth(1)
        self.action_settings_scrollArea.setWidgetResizable(True)

        self.action_settings_WidgetContents = QtWidgets.QWidget()
        self.action_settings_WidgetContents.setGeometry(QtCore.QRect(0, 0, 346, 223))

        self.action_settings_scrollArea_vLay = QtWidgets.QVBoxLayout(self.action_settings_WidgetContents)

        self.action_settings_formLayout = QtWidgets.QFormLayout()
        self.action_settings_formLayout.setHorizontalSpacing(6)
        self.action_settings_scrollArea_vLay.addLayout(self.action_settings_formLayout)

        self.action_settings_scrollArea.setWidget(self.action_settings_WidgetContents)
        self.action_settings_vLay.addWidget(self.action_settings_scrollArea)
        self.rigging_tab_vLay.addWidget(self.rig_LR_splitter)
        self.rig_buttons_hLay = QtWidgets.QHBoxLayout()

        self.build_pb = QtWidgets.QPushButton(self.rigging_tab, text="Build Rig")
        self.rig_buttons_hLay.addWidget(self.build_pb)

        self.build_and_publish_pb = QtWidgets.QPushButton(self.rigging_tab, text="Build && Publish")
        self.rig_buttons_hLay.addWidget(self.build_and_publish_pb)
        self.rigging_tab_vLay.addLayout(self.rig_buttons_hLay)

        ### SIGNALS ####

        self.add_action_pb.clicked.connect(self.add_actions_menu)
        self.move_action_up_pb.clicked.connect(self.move_action_up)
        self.move_action_down_pb.clicked.connect(self.move_action_down)
        self.delete_action_pb.clicked.connect(self.delete_action)
        self.rig_actions_listwidget.currentItemChanged.connect(self.action_settings_menu)

        self.build_pb.clicked.connect(lambda x=0: self.actions_handler.run_all_actions())

    def open_trigger(self):
        dlg = QtWidgets.QFileDialog.getOpenFileName(self, str("Open Trigger Session"), "", str("Trigger Session (*.tr)"))
        if dlg[0]:
            self.actions_handler.load_session(os.path.normpath(dlg[0]))
            self.populate_actions()

    def save_as_trigger(self):
        dlg = QtWidgets.QFileDialog.getSaveFileName(self, str("Save Trigger Session"), "", str("Trigger Session (*.tr)"))
        if dlg[0]:
            self.actions_handler.save_session(os.path.normpath(dlg[0]))

    def save_trigger(self):
        if self.actions_handler.currentFile:
            self.actions_handler.save_session(self.actions_handler.currentFile)
        else:
            self.save_as_trigger()


    def action_settings_menu(self):
        """Builds the action settings depending on action type"""
        # get the action type
        row = self.rig_actions_listwidget.currentRow()
        if row == -1:
            return
        action_name = self.rig_actions_listwidget.currentItem().text()
        action_type = self.actions_handler.get_action_type(action_name)
        self.clearLayout(self.action_settings_formLayout)

        if action_type == "kinematics":
            self.kinematics_settings_layout()

        if action_type == "weights":
            self.weights_settings_layout()

        if action_type == "script":
            self.script_settings_layout()

    def kinematics_settings_layout(self):
        row = self.rig_actions_listwidget.currentRow()
        if row == -1:
            return
        action_name = self.rig_actions_listwidget.currentItem().text()
        # feed the controller
        ctrl = model_ctrl.Controller()
        ctrl.model = self.actions_handler
        ctrl.action_name = action_name

        file_path_lbl = QtWidgets.QLabel(text="File Path:")
        file_path_hLay = QtWidgets.QHBoxLayout()
        file_path_le = QtWidgets.QLineEdit()
        file_path_hLay.addWidget(file_path_le)
        browse_path_pb = BrowserButton(update_widget=file_path_le, mode="openFile", filterExtensions=["Trigger Guide Files (*.trg)"])
        file_path_hLay.addWidget(browse_path_pb)
        self.action_settings_formLayout.addRow(file_path_lbl, file_path_hLay)

        guide_roots_lbl = QtWidgets.QLabel(text="Guide Roots:")
        guide_roots_hLay = QtWidgets.QHBoxLayout()
        guide_roots_le = QtWidgets.QLineEdit()
        guide_roots_hLay.addWidget(guide_roots_le)
        get_guide_roots_pb = QtWidgets.QPushButton(text="Get")
        guide_roots_hLay.addWidget(get_guide_roots_pb)
        self.action_settings_formLayout.addRow(guide_roots_lbl, guide_roots_hLay)

        create_auto_sw_lbl = QtWidgets.QLabel(text="Create Auto Switchers:")
        create_auto_sw_cb = QtWidgets.QCheckBox()
        self.action_settings_formLayout.addRow(create_auto_sw_lbl, create_auto_sw_cb)

        after_action_lbl = QtWidgets.QLabel(text="After Action:")
        after_action_combo = QtWidgets.QComboBox()
        after_action_combo.addItems(["Do Nothing", "Hide Guides", "Delete Guides"])
        self.action_settings_formLayout.addRow(after_action_lbl, after_action_combo)

        multi_selectionSets_lbl = QtWidgets.QLabel(text = "Selection Sets")
        multi_selectionSets_cb = QtWidgets.QCheckBox()
        self.action_settings_formLayout.addRow(multi_selectionSets_lbl, multi_selectionSets_cb)

        # make connections with the controller object
        ctrl.connect(file_path_le, "guides_file_path", str)
        ctrl.connect(guide_roots_le, "guide_roots", list)
        ctrl.connect(create_auto_sw_cb, "auto_switchers", bool)
        ctrl.connect(after_action_combo, "after_creation", int)
        ctrl.connect(multi_selectionSets_cb, "multi_selectionSets", bool)

        ctrl.update_ui()


        def get_roots_menu():
            # recentList = reversed(self.manager.loadRecentProjects())
            # list_of_actions = sorted(self.rig.action_dict.keys())
            if file_path_le.text():
                if not os.path.isfile(file_path_le.text()):
                    FEEDBACK.throw_error("Guide file does not exist")

                list_of_roots = list(self.guides_handler.get_roots_from_file(file_path=file_path_le.text()))

                zortMenu = QtWidgets.QMenu()
                for root in list_of_roots:
                    tempAction = QtWidgets.QAction(str(root), self)
                    zortMenu.addAction(tempAction)
                    tempAction.triggered.connect(lambda ignore=root, item=root: add_root(str(root)))
                    # tempAction.triggered.connect(self.populate_actions)


                # self.populate_actions()

                zortMenu.exec_((QtGui.QCursor.pos()))

        def add_root(root):
            current_roots = guide_roots_le.text()
            if root in current_roots:
                FEEDBACK.warning("%s is already in the list" %root)
                return
            new_roots = root if not current_roots else "{0}  {1}".format(current_roots, root)
            guide_roots_le.setText(new_roots)
            ctrl.update_model()

        ### Signals
        # file_path_le.textEdited.connect(lambda x=0: ctrl.update_model())
        file_path_le.editingFinished.connect(lambda x=0: ctrl.update_model())
        browse_path_pb.clicked.connect(lambda x=0: ctrl.update_model())
        guide_roots_le.editingFinished.connect(lambda x=0: ctrl.update_model())
        get_guide_roots_pb.clicked.connect(get_roots_menu)
        create_auto_sw_cb.stateChanged.connect(lambda x=0: ctrl.update_model())
        after_action_combo.currentIndexChanged.connect(lambda x=0: ctrl.update_model())
        multi_selectionSets_cb.stateChanged.connect(lambda x=0: ctrl.update_model())

    def weights_settings_layout(self):
        row = self.rig_actions_listwidget.currentRow()
        if row == -1:
            return
        deformers = importlib.import_module("trigger.library.deformers")
        action_name = self.rig_actions_listwidget.currentItem().text()
        # feed the controller
        ctrl = model_ctrl.Controller()
        ctrl.model = self.actions_handler
        ctrl.action_name = action_name

        file_path_lbl = QtWidgets.QLabel(text="File Path:")
        file_path_hLay = QtWidgets.QHBoxLayout()
        file_path_le = QtWidgets.QLineEdit()
        file_path_hLay.addWidget(file_path_le)
        browse_path_pb = BrowserButton(mode="saveFile", update_widget=file_path_le, filterExtensions=["Trigger Weight Files (*.trw)"], overwrite_check=False)
        file_path_hLay.addWidget(browse_path_pb)
        self.action_settings_formLayout.addRow(file_path_lbl, file_path_hLay)

        deformers_lbl = QtWidgets.QLabel(text="Deformers")
        deformers_hLay = QtWidgets.QHBoxLayout()
        deformers_le = QtWidgets.QLineEdit()
        deformers_hLay.addWidget(deformers_le)
        get_deformers_pb = QtWidgets.QPushButton(text="Get")
        deformers_hLay.addWidget(get_deformers_pb)
        self.action_settings_formLayout.addRow(deformers_lbl, deformers_hLay)

        save_current_lbl = QtWidgets.QLabel(text="Save Current states")
        save_current_hlay = QtWidgets.QHBoxLayout()
        save_current_pb = QtWidgets.QPushButton(text="Save")
        increment_current_pb = QtWidgets.QPushButton(text="Increment and Save")
        save_current_hlay.addWidget(save_current_pb)
        save_current_hlay.addWidget(increment_current_pb)
        self.action_settings_formLayout.addRow(save_current_lbl, save_current_hlay)

        # make connections with the controller object
        ctrl.connect(file_path_le, "weights_file_path", str)
        ctrl.connect(deformers_le, "deformers", list)

        ctrl.update_ui()

        def get_deformers_menu():
            list_of_deformers = list(deformers.get_deformers(namesOnly=True))

            zortMenu = QtWidgets.QMenu()
            for deformer in list_of_deformers:
                tempAction = QtWidgets.QAction(str(deformer), self)
                zortMenu.addAction(tempAction)
                tempAction.triggered.connect(lambda ignore=deformer, item=deformer: add_deformer(str(deformer)))
            zortMenu.exec_((QtGui.QCursor.pos()))

        def add_deformer(deformer):
            current_deformers = deformers_le.text()
            if deformer in current_deformers:
                FEEDBACK.warning("%s is already in the list" %deformer)
                return
            new_deformers = deformer if not current_deformers else "{0}  {1}".format(current_deformers, deformer)
            deformers_le.setText(new_deformers)
            ctrl.update_model()

        def save_deformers(increment=False):
            if increment:
                ctrl.update_model()
                FEEDBACK.warning("NOT YET IMPLEMENTED")
                # TODO make an external incrementer
            else:
                ctrl.update_model()
                if os.path.isfile(file_path_le.text()):
                    state = self.queryPop(type="okCancel", textTitle="Overwrite", textHeader="The file %s already exists.\nDo you want to OVERWRITE?" %file_path_le.text())
                    if state == "cancel":
                        return
                self.actions_handler.run_save_action(action_name)

        ### Signals
        file_path_le.editingFinished.connect(lambda x=0: ctrl.update_model())
        browse_path_pb.clicked.connect(lambda x=0: ctrl.update_model())
        deformers_le.editingFinished.connect(lambda x=0: ctrl.update_model())
        get_deformers_pb.clicked.connect(get_deformers_menu)
        get_deformers_pb.clicked.connect(lambda x=0: ctrl.update_model())

        save_current_pb.clicked.connect(lambda x=0: save_deformers())
        increment_current_pb.clicked.connect(lambda x=0: save_deformers(increment=True))

    def script_settings_layout(self):
        row = self.rig_actions_listwidget.currentRow()
        if row == -1:
            return

        action_name = self.rig_actions_listwidget.currentItem().text()
        # feed the controller
        ctrl = model_ctrl.Controller()
        ctrl.model = self.actions_handler
        ctrl.action_name = action_name

        file_path_lbl = QtWidgets.QLabel(text="File Path:")
        file_path_hLay = QtWidgets.QHBoxLayout()
        file_path_le = QtWidgets.QLineEdit()
        file_path_hLay.addWidget(file_path_le)
        edit_file_pb = QtWidgets.QPushButton(text="Edit")
        file_path_hLay.addWidget(edit_file_pb)
        browse_path_pb = BrowserButton(mode="saveFile", update_widget=file_path_le, filterExtensions=["Python Files (*.py)"], overwrite_check=False)
        file_path_hLay.addWidget(browse_path_pb)
        self.action_settings_formLayout.addRow(file_path_lbl, file_path_hLay)

        import_as_lbl = QtWidgets.QLabel(text="Import as:")
        import_as_le = QtWidgets.QLineEdit()
        self.action_settings_formLayout.addRow(import_as_lbl, import_as_le)

        commands_lbl = QtWidgets.QLabel(text="Commands")
        commands_le = QtWidgets.QLineEdit()
        self.action_settings_formLayout.addRow(commands_lbl, commands_le)

        ctrl.connect(file_path_le, "script_file_path", str)
        ctrl.connect(import_as_le, "import_as", str)
        ctrl.connect(commands_le, "commands", list)
        ctrl.update_ui()

        def edit_file():
            file_path = file_path_le.text()
            system = platform.system()
            if system == "Windows":
                os.startfile(file_path)
            elif system == "Linux":
                subprocess.Popen(["xdg-open", file_path])
                pass
            else:
                subprocess.Popen(["open", file_path])
                pass

        ### Signals
        file_path_le.textEdited.connect(lambda x=0: ctrl.update_model())
        import_as_le.textEdited.connect(lambda x=0: ctrl.update_model())
        edit_file_pb.clicked.connect(edit_file)
        browse_path_pb.clicked.connect(lambda x=0: ctrl.update_model())
        commands_le.textEdited.connect(lambda x=0: ctrl.update_model())

    def add_actions_menu(self):
        # recentList = reversed(self.manager.loadRecentProjects())
        # list_of_actions = sorted(self.rig.action_dict.keys())
        list_of_actions = sorted(self.actions_handler.action_data_dict.keys())

        zortMenu = QtWidgets.QMenu()
        for action_item in list_of_actions:
            tempAction = QtWidgets.QAction(action_item, self)
            zortMenu.addAction(tempAction)
            tempAction.triggered.connect(lambda ignore=action_item, item=action_item: self.actions_handler.add_action(action_type=item))
            tempAction.triggered.connect(self.populate_actions)
            ## Take note about the usage of lambda "item=z" makes it possible using the loop, ignore -> for discarding emitted value
            # tempAction.triggered.connect(lambda ignore=p, item=p: setAndClose(custompath=(item)))
            # tempAction.triggered.connect(lambda item=z: manager.playPreview(str(item)))

        self.populate_actions()

        zortMenu.exec_((QtGui.QCursor.pos()))

    def populate_actions(self):
        self.rig_actions_listwidget.clear()
        self.rig_actions_listwidget.addItems(self.actions_handler.list_action_names())

    def move_action_up(self):
        self.block_all_signals(True)
        row = self.rig_actions_listwidget.currentRow()
        if row == -1:
            return
        action_name = self.rig_actions_listwidget.currentItem().text()
        self.actions_handler.move_up(action_name=action_name)
        self.populate_actions()

        # select the original selected item again
        original_selection = self.rig_actions_listwidget.findItems(action_name, QtCore.Qt.MatchExactly)[0]
        original_row = self.rig_actions_listwidget.row(original_selection)
        self.rig_actions_listwidget.setCurrentRow(original_row)
        self.block_all_signals(False)

    def move_action_down(self):
        self.block_all_signals(True)
        row = self.rig_actions_listwidget.currentRow()
        if row == -1:
            return
        action_name = self.rig_actions_listwidget.currentItem().text()
        self.actions_handler.move_down(action_name=action_name)
        self.populate_actions()

        # select the original selected item again
        original_selection = self.rig_actions_listwidget.findItems(action_name, QtCore.Qt.MatchExactly)[0]
        original_row = self.rig_actions_listwidget.row(original_selection)
        self.rig_actions_listwidget.setCurrentRow(original_row)
        self.block_all_signals(False)

    def delete_action(self):
        self.block_all_signals(True)
        row = self.rig_actions_listwidget.currentRow()
        if row == -1:
            return
        action_name = self.rig_actions_listwidget.currentItem().text()
        self.actions_handler.delete_action(action_name=action_name)
        self.populate_actions()
        self.block_all_signals(False)


#######################
### GUIDE FUNCTIONS ###
#######################

    def import_guides(self):
        dlg = QtWidgets.QFileDialog.getOpenFileName(self, str("Import Guides"), "", str("Trigger Guides (*.trg)"))
        if dlg[0]:
            self.guides_handler.load_session(os.path.normpath(dlg[0]), reset_scene=False)

    def export_guides(self):
        dlg = QtWidgets.QFileDialog.getSaveFileName(self, str("Export Guides"), "", str("Trigger Guides (*.trg)"))
        if dlg[0]:
            self.guides_handler.save_session(os.path.normpath(dlg[0]))

    def build_test_guides(self):
        self.progressBar()
        self.guides_handler.init.test_build(progress_bar=self.progress_progressBar)
        self.progress_Dialog.close()

    def populate_guides(self):
        self.block_all_signals(True)

        if self.guides_list_treeWidget.currentItem():
            selected_root_jnt = self.guides_list_treeWidget.currentItem().text(2)
        else:
            selected_root_jnt = None

        self.guides_list_treeWidget.clear()
        roots_dict_list = self.guides_handler.init.get_scene_roots()
        for item in roots_dict_list:
            if item["side"] == "C":
                color = QtGui.QColor(255, 255, 0, 255)
            elif item["side"] == "L":
                color = QtGui.QColor(0, 100, 255, 255)
            else:
                color = QtGui.QColor(255, 100, 0, 255)
            tree_item = QtWidgets.QTreeWidgetItem(self.guides_list_treeWidget, [item["module_name"], item["side"], item["root_joint"], item["module_type"]])
            if item["root_joint"] == selected_root_jnt:
                self.guides_list_treeWidget.setCurrentItem(tree_item)
            tree_item.setForeground(0, color)

        self.populate_properties()

        self.block_all_signals(False)

    def populate_properties(self):
        self.block_all_signals(True)

        # general properties
        if self.guides_list_treeWidget.currentIndex().row() == -1:
            self.R_guides_WidgetContents.setHidden(True)
            return

        root_jnt = self.guides_list_treeWidget.currentItem().text(2)
        module_type = self.guides_list_treeWidget.currentItem().text(3)
        self.module_name_le.setText(self.guides_handler.init.get_property(root_jnt, "moduleName"))
        for num, axis in enumerate("XYZ"):
            self.up_axis_sp_list[num].setValue(self.guides_handler.init.get_property(root_jnt, "upAxis%s" % axis))
            self.mirror_axis_sp_list[num].setValue(self.guides_handler.init.get_property(root_jnt, "mirrorAxis%s" % axis))
            self.look_axis_sp_list[num].setValue(self.guides_handler.init.get_property(root_jnt, "lookAxis%s" % axis))

        self.inherit_orientation_cb.setChecked(self.guides_handler.init.get_property(root_jnt, "useRefOri"))

        self.R_guides_WidgetContents.setHidden(False)

        # extra properties
        extra_properties = self.guides_handler.init.get_extra_properties(module_type)
        self.clearLayout(self.module_extras_formLayout)
        if extra_properties:
            for property_dict in extra_properties:
                self.draw_extra_property(property_dict, self.module_extras_formLayout, root_jnt)

        self.block_all_signals(False)
        pass

    def draw_extra_property(self, property_dict, parent_form_layout, root_jnt):

        p_name = property_dict["attr_name"]
        p_nice_name = property_dict.get("nice_name").replace("_", " ")
        p_lbl = QtWidgets.QLabel(self.R_guides_WidgetContents, text=p_nice_name)
        p_type = property_dict.get("attr_type")
        p_value = self.guides_handler.init.get_property(root_jnt, p_name)

        if p_type == "long" or p_type == "short":
            p_widget = QtWidgets.QSpinBox()
            min_val = property_dict.get("min_value") if property_dict.get("min_value") else -99999
            max_val = property_dict.get("max_value") if property_dict.get("max_value") else 99999
            p_widget.setRange(min_val, max_val)
            p_widget.setValue(p_value)
            p_widget.valueChanged.connect(lambda num: self.update_properties(p_name, num))
        elif p_type == "bool":
            p_widget = QtWidgets.QCheckBox()
            p_widget.setChecked(p_value)
            p_widget.toggled.connect(lambda state=p_widget.isChecked(): self.update_properties(p_name, state))
        elif p_type == "enum":
            p_widget = QtWidgets.QComboBox()
            enum_list_raw = property_dict.get("enum_list")
            if not enum_list_raw:
                FEEDBACK.throw_error("Missing 'enum_list'")
            enum_list = enum_list_raw.split(":")
            p_widget.addItems(enum_list)
            p_widget.setCurrentIndex(p_value)
            p_widget.currentIndexChanged.connect(lambda index: self.update_properties(p_name, index))
        elif p_type == "float" or p_type == "double":
            p_widget = QtWidgets.QDoubleSpinBox()
            min_val = property_dict.get("min_value") if property_dict.get("min_value") else -99999
            max_val = property_dict.get("max_value") if property_dict.get("max_value") else 99999
            p_widget.setRange(min_val, max_val)
            p_widget.setValue(p_value)
            p_widget.valueChanged.connect(lambda num: self.update_properties(p_name, num))
        elif p_type == "string":
            p_widget = QtWidgets.QLineEdit()
            p_widget.setText(p_value)
            p_widget.textChanged.connect(lambda text: self.update_properties(p_name, text))
        else:
            p_widget = None
            FEEDBACK.throw_error("Cannot find a proper equivalent for this attribute type %s" % p_type)

        parent_form_layout.addRow(p_lbl, p_widget)

    def update_properties(self, property, value):
        root_jnt = self.guides_list_treeWidget.currentItem().text(2)
        self.guides_handler.init.set_property(root_jnt, property, value)
        # if property == "moduleName":
        #     self.populate_guides()

    def on_create_guide(self, limb_name, *args, **kwargs):
        if limb_name == "humanoid":
            self.guides_handler.init.initHumanoid()
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
            self.guides_handler.init.initLimb(limb_name, whichSide= side, **kwargs)
        self.populate_guides()

    def on_guide_change(self, currentItem, previousItem):
        row = self.guides_list_treeWidget.currentIndex().row()
        if row == -1:
            return
        self.guides_handler.init.select_root(str(currentItem.text(2)))
        self.populate_properties()

    def force_update(self):
        if self.force and self.tabWidget.currentIndex() == 0:
            self.populate_guides()

    def eventFilter(self, object, event):
        if event.type() == QtCore.QEvent.WindowActivate:
            self.force = False
        elif event.type()== QtCore.QEvent.WindowDeactivate:
            self.force = True
        # elif event.type()== QtCore.QEvent.FocusIn:
        #     self.force = False
        # elif event.type()== QtCore.QEvent.FocusOut:
        #     self.force = True
        return False

    def clearLayout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self.clearLayout(child.layout())


    ##############
    ### COMMON ###
    ##############

    # def block_all_signals(self, state):
    #     self.guides_list_treeWidget.blockSignals(state)
    #     self.rig_actions_listwidget.blockSignals(state)
    #     for sp_up in self.up_axis_sp_list:
    #         sp_up.blockSignals(state)
    #     for sp_mirror in self.mirror_axis_sp_list:
    #         sp_mirror.blockSignals(state)
    #     for sp_look in self.look_axis_sp_list:
    #         sp_look.blockSignals(state)
    #     self.inherit_orientation_cb.blockSignals(state)
    @staticmethod
    def list_to_text(list_item):
        return " ".join(list_item)

    @staticmethod
    def text_to_list(text_item):
        return text_item.split(" ")

    def block_all_signals(self, state):
        """Blocks and Unblocks all signals for defined widgets inside function"""
        widgets_affected = [self.guides_list_treeWidget, self.rig_actions_listwidget, self.inherit_orientation_cb]
        widgets_affected.extend(self.up_axis_sp_list)
        widgets_affected.extend(self.mirror_axis_sp_list)
        widgets_affected.extend(self.look_axis_sp_list)
        for widget in widgets_affected:
            widget.blockSignals(state)


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
        self.msg.button(QtWidgets.QMessageBox.Ok).setFixedHeight(30)
        self.msg.button(QtWidgets.QMessageBox.Ok).setFixedWidth(100)
        self.msg.show()

    def queryPop(self, type, textTitle="Question", textHeader="", textInfo=""):
        """
        Pops a query window

        Args:
            type: (String) Valid types are: 'yesNoCancel', 'okCancel', 'yesNo'
            textTitle: (String) Title of the text
            textHeader: (String) Message header
            textInfo: (String) Message details

        Returns: (String) 'yes', 'no', 'ok' or 'cancel' depending on the type

        """

        if type == "yesNoCancel":

            q = QtWidgets.QMessageBox(parent=self)
            q.setIcon(QtWidgets.QMessageBox.Question)
            q.setText(textHeader)
            q.setInformativeText(textInfo)
            q.setWindowTitle(textTitle)
            q.setStandardButtons(
                QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel)

            q.button(QtWidgets.QMessageBox.Save).setFixedHeight(30)
            q.button(QtWidgets.QMessageBox.Save).setFixedWidth(100)
            q.button(QtWidgets.QMessageBox.No).setFixedHeight(30)
            q.button(QtWidgets.QMessageBox.No).setFixedWidth(100)
            q.button(QtWidgets.QMessageBox.Cancel).setFixedHeight(30)
            q.button(QtWidgets.QMessageBox.Cancel).setFixedWidth(100)
            ret = q.exec_()
            if ret == QtWidgets.QMessageBox.Save:
                return "yes"
            elif ret == QtWidgets.QMessageBox.No:
                return "no"
            elif ret == QtWidgets.QMessageBox.Cancel:
                return "cancel"

        if type == "okCancel":
            q = QtWidgets.QMessageBox(parent=self)
            q.setIcon(QtWidgets.QMessageBox.Question)
            q.setText(textHeader)
            q.setInformativeText(textInfo)
            q.setWindowTitle(textTitle)
            q.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
            q.button(QtWidgets.QMessageBox.Ok).setFixedHeight(30)
            q.button(QtWidgets.QMessageBox.Ok).setFixedWidth(100)
            q.button(QtWidgets.QMessageBox.Cancel).setFixedHeight(30)
            q.button(QtWidgets.QMessageBox.Cancel).setFixedWidth(100)
            ret = q.exec_()
            if ret == QtWidgets.QMessageBox.Ok:
                return "ok"
            elif ret == QtWidgets.QMessageBox.Cancel:
                return "cancel"

        if type == "yesNo":
            q = QtWidgets.QMessageBox(parent=self)
            q.setIcon(QtWidgets.QMessageBox.Question)
            q.setText(textHeader)
            q.setInformativeText(textInfo)
            q.setWindowTitle(textTitle)
            q.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            q.button(QtWidgets.QMessageBox.Yes).setFixedHeight(30)
            q.button(QtWidgets.QMessageBox.Yes).setFixedWidth(100)
            q.button(QtWidgets.QMessageBox.No).setFixedHeight(30)
            q.button(QtWidgets.QMessageBox.No).setFixedWidth(100)
            ret = q.exec_()
            if ret == QtWidgets.QMessageBox.Yes:
                return "yes"
            elif ret == QtWidgets.QMessageBox.No:
                return "no"

class BrowserButton(QtWidgets.QPushButton):
    def __init__(self, text="Browse", update_widget=None, mode="openFile", filterExtensions=None, title=None, overwrite_check=True):
        super(BrowserButton, self).__init__()
        self._updateWidget = update_widget
        if text:
            self.setText(text)
        self._validModes = ["openFile", "saveFile", "directory"]
        if mode in self._validModes:
            self._mode = mode
        else:
            raise Exception("Mode is not valid. Valid modes are %s" % (", ".join(self._validModes)))
        self._filterExtensions = self._listToFilter(filterExtensions) if filterExtensions else ""
        self._title = title if title else ""
        self._selectedPath = ""
        self._overwriteCheck=overwrite_check

    def setUpdateWidget(self, widget):
        self._updateWidget = widget

    def updateWidget(self):
        return self._updateWidget

    def setMode(self, mode):
        if mode not in self._validModes:
            raise Exception("Mode is not valid. Valid modes are %s" % (", ".join(self._validModes)))
        self._mode = mode

    def mode(self):
        return self._mode

    def setFilterExtensions(self, extensionlist):
        self._filterExtensions = self._listToFilter(extensionlist)

    def selectedPath(self):
        return self._selectedPath

    def setSelectedPath(self, new_path):
        self._selectedPath = new_path

    def setTitle(self, title):
        self._title = title

    def title(self):
        return self._title

    def _listToFilter(self, filter_list):
        return ";;".join(filter_list)

    def mouseReleaseEvent(self, *args, **kwargs):
        super(BrowserButton, self).mouseReleaseEvent(*args, **kwargs)
        if self._mode == "openFile":
            dlg = QtWidgets.QFileDialog.getOpenFileName(self, self._title, self._selectedPath, self._filterExtensions)
            new_path = dlg[0] if dlg else None
        elif self._mode == "saveFile":
            if not self._overwriteCheck:
                dlg = QtWidgets.QFileDialog.getSaveFileName(self, self._title, self._selectedPath, self._filterExtensions, options=(QtWidgets.QFileDialog.DontConfirmOverwrite))
            else:
                dlg = QtWidgets.QFileDialog.getSaveFileName(self, self._title, self._selectedPath, self._filterExtensions)
            new_path = dlg[0] if dlg else None
        elif self._mode == "directory":
            dlg = QtWidgets.QFileDialog.getExistingDirectory(self, self._title, self._selectedPath, options=(QtWidgets.QFileDialog.ShowDirsOnly))
            new_path = dlg if dlg else None
        else:
            new_path = None

        if new_path:
            self._selectedPath = os.path.normpath(new_path)
            if self._updateWidget:
                self._updateWidget.setText(self._selectedPath)
            self.click()

