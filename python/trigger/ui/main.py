#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Main UI for trigger"""
import sys, os
from maya import cmds

from trigger.core import database

# from trigger.ui import Qt
from trigger.ui.Qt import QtWidgets, QtCore, QtGui
from trigger.ui.qtmaya import getMayaMainWindow
from trigger.ui import model_ctrl
from trigger.ui import custom_widgets
from trigger.ui import feedback

from trigger.base import session
from trigger.base import actions_session

from trigger.library import naming


from trigger.core import filelog

log = filelog.Filelog(logname=__name__, filename="trigger_log")
db = database.Database()

WINDOW_NAME = "Trigger v2.0.1"

def _createCallbacks(function, parent=None, event=None):
    callbackIDList = []
    if parent:
        job = cmds.scriptJob(e=[event, function], replacePrevious=True, parent=parent)
    else:
        job = cmds.scriptJob(e=[event, function])
    callbackIDList.append(job)
    return callbackIDList


def _killCallbacks(callbackIDList):
    for ID in callbackIDList:
        if cmds.scriptJob(ex=ID):
            cmds.scriptJob(kill=ID)

def launch(force=False):
    for entry in QtWidgets.QApplication.allWidgets():
        try:
            if entry.objectName() == WINDOW_NAME:
                if force:
                    entry.close()
                    entry.deleteLater()
                else:
                    log.warning("Only one session of Trigger can be opened per Maya instance")
                    return
        except (AttributeError, TypeError):
            pass
    MainUI().show()

class MainUI(QtWidgets.QMainWindow):
    iconsPath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "icons")

    def __init__(self):

        # for entry in QtWidgets.QApplication.allWidgets():
        #     try:
        #         if entry.objectName() == WINDOW_NAME:
        #             # self.closeEvent()
        #             # sys.stderr = lambda: 1
        #             # return
        #             raise Exception("Only one session of Trigger can be opened per Maya instance")
        #             # entry.close()
        #             # entry.deleteLater()
        #
        #     except (AttributeError, TypeError):
        #         pass
        parent = getMayaMainWindow()
        super(MainUI, self).__init__(parent=parent)

        log.clear()
        # create guide and rig objects
        self.actions_handler = actions_session.ActionsSession()
        self.guides_handler = session.Session()

        self.actions_handler.reset_actions()

        self.feedback = feedback.Feedback()
        self.feedback.parent = self
        self.installEventFilter(self)
        # self.force = False
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

        # define the listwidget to the actions handler to update it during build
        self.actions_handler.progressListwidget = self.rig_actions_listwidget

        self.populate_guides()

        self.splitter.setStretchFactor(0, 10)
        self.splitter.setStretchFactor(1, 40)
        self.splitter.setStretchFactor(1, 50)

        self.rig_LR_splitter.setStretchFactor(0, 10)
        self.rig_LR_splitter.setStretchFactor(1, 90)

        self.show()
        self.update_title()

        # self.callbackIDList = _createCallbacks(self.force_update, WINDOW_NAME, "SelectionChanged")
        self.callbackIDList = _createCallbacks(self.force_update, parent=None, event="SelectionChanged")

        log.info("Interface Loaded Successfully")

    def update_title(self):
        file_name = self.actions_handler.currentFile if self.actions_handler.currentFile else "untitled"
        asteriks = "*" if self.actions_handler.is_modified() else ""
        self.setWindowTitle("{0} - {1}{2}".format(WINDOW_NAME, file_name, asteriks))

    def closeEvent(self, event):
        if self.actions_handler.is_modified():
            r = self.feedback.pop_question(title="Scene not saved", text="Current Trigger session is not saved\n Do you want to save before quit?", buttons=["yes", "no", "cancel"])
            if r == "yes":
                self.save_trigger()
                _killCallbacks(self.callbackIDList)
                event.accept()
            elif r == "no":
                _killCallbacks(self.callbackIDList)
                event.accept()
            else:
                event.ignore()
        else:
            _killCallbacks(self.callbackIDList)
            event.accept()



    def buildBarsUI(self):
        self.menubar = QtWidgets.QMenuBar(self)
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setTitle("File")
        self.setMenuBar(self.menubar)

        self.statusbar = QtWidgets.QStatusBar(self)
        self.setStatusBar(self.statusbar)

        self.new_trigger_action = QtWidgets.QAction(self, text="New Trigger Session")
        self.open_trigger_action = QtWidgets.QAction(self, text="Open Trigger Session")
        self.import_trigger_action = QtWidgets.QAction(self, text="Import Trigger Session")
        self.save_trigger_action = QtWidgets.QAction(self, text="Save Trigger Session")
        self.save_as_trigger_action = QtWidgets.QAction(self, text="Save As Trigger Session")
        self.increment_trigger_action = QtWidgets.QAction(self, text="Increment Save Trigger Session")
        self.import_guides_action = QtWidgets.QAction(self, text="Import Guides")
        self.export_guides_action = QtWidgets.QAction(self, text="Export Guides")
        self.settings_action = QtWidgets.QAction(self, text="Settings")
        self.reset_scene_action = QtWidgets.QAction(self, text="Reset Scene")
        self.exit_action = QtWidgets.QAction(self, text="Exit")

        self.menuFile.addAction(self.new_trigger_action)
        self.menuFile.addAction(self.open_trigger_action)
        self.menuFile.addAction(self.import_trigger_action)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.save_trigger_action)
        self.menuFile.addAction(self.save_as_trigger_action)
        self.menuFile.addAction(self.increment_trigger_action)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.import_guides_action)
        self.menuFile.addAction(self.export_guides_action)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.settings_action)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.reset_scene_action)
        self.menuFile.addSeparator()


        self.recents_menu = QtWidgets.QMenu("Recent Sessions")
        self.menuFile.addMenu(self.recents_menu)
        # self.recents_menu = self.menuFile.addMenu("Recent Sessions")
        self.menuFile.addAction(self.exit_action)

        self.menubar.addAction(self.menuFile.menuAction())

        self.populate_recents()

        # SIGNALS
        # menu items
        self.new_trigger_action.triggered.connect(self.new_trigger)
        self.open_trigger_action.triggered.connect(self.open_trigger)
        self.import_trigger_action.triggered.connect(self.import_trigger)
        self.save_trigger_action.triggered.connect(self.save_trigger)
        self.save_as_trigger_action.triggered.connect(self.save_as_trigger)
        self.increment_trigger_action.triggered.connect(self.increment_trigger)

        self.export_guides_action.triggered.connect(self.export_guides)
        self.import_guides_action.triggered.connect(self.import_guides)

        self.reset_scene_action.triggered.connect(self.guides_handler.reset_scene)
        self.reset_scene_action.triggered.connect(self.populate_guides)

        self.exit_action.triggered.connect(self.close)

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

        self.up_axis_sp_list = [QtWidgets.QDoubleSpinBox(self.R_guides_WidgetContents, minimum=-1, maximum=1, minimumWidth=40, buttonSymbols=QtWidgets.QAbstractSpinBox.NoButtons) for axis in "XYZ"]
        _ = [up_axis_hLay.addWidget(sp) for sp in self.up_axis_sp_list]
        self.module_settings_formLayout.addRow(up_axis_lbl, up_axis_hLay)
        
        #mirror axis
        mirror_axis_lbl = QtWidgets.QLabel(self.R_guides_WidgetContents, text="Mirror Axis")
        mirror_axis_hLay = QtWidgets.QHBoxLayout(spacing=3)
        self.mirror_axis_sp_list = [QtWidgets.QDoubleSpinBox(self.R_guides_WidgetContents,  minimum=-1, maximum=1, minimumWidth=40, buttonSymbols=QtWidgets.QAbstractSpinBox.NoButtons) for axis in "XYZ"]
        _ = [mirror_axis_hLay.addWidget(sp) for sp in self.mirror_axis_sp_list]
        self.module_settings_formLayout.addRow(mirror_axis_lbl, mirror_axis_hLay)

        #look axis
        look_axis_lbl = QtWidgets.QLabel(self.R_guides_WidgetContents, text="Look Axis")
        look_axis_hLay = QtWidgets.QHBoxLayout(spacing=3)
        self.look_axis_sp_list = [QtWidgets.QDoubleSpinBox(self.R_guides_WidgetContents,  minimum=-1, maximum=1, minimumWidth=40, buttonSymbols=QtWidgets.QAbstractSpinBox.NoButtons) for axis in "XYZ"]
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

        ### SHORTCUTS ###
        shortcutForceUpdate = QtWidgets.QShortcut(QtGui.QKeySequence("F5"), self, self.force_update)

        ## SIGNALS
        self.guides_list_treeWidget.currentItemChanged.connect(self.on_guide_change)
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

        self.rig_actions_listwidget = custom_widgets.ProgressListWidget()

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

        # info button is standard for all actions
        self.action_info_pb = QtWidgets.QPushButton(text="?")
        self.action_info_pb.setMaximumWidth(15)
        self.action_settings_scrollArea_vLay.addWidget(self.action_info_pb)


        self.action_settings_formLayout = QtWidgets.QFormLayout()
        self.action_settings_formLayout.setHorizontalSpacing(6)
        self.action_settings_scrollArea_vLay.addLayout(self.action_settings_formLayout)

        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.action_settings_scrollArea_vLay.addItem(spacerItem)

        self.action_settings_scrollArea.setWidget(self.action_settings_WidgetContents)
        self.action_settings_vLay.addWidget(self.action_settings_scrollArea)
        self.rigging_tab_vLay.addWidget(self.rig_LR_splitter)
        self.rig_buttons_hLay = QtWidgets.QHBoxLayout()

        self.build_pb = QtWidgets.QPushButton(self.rigging_tab, text="Build Rig")
        self.rig_buttons_hLay.addWidget(self.build_pb)

        self.build_and_publish_pb = QtWidgets.QPushButton(self.rigging_tab, text="Build && Publish")
        self.build_and_publish_pb.setIcon(QtGui.QIcon(os.path.join(self.iconsPath, "cab.png")))

        self.rig_buttons_hLay.addWidget(self.build_and_publish_pb)
        self.rigging_tab_vLay.addLayout(self.rig_buttons_hLay)

        ### RIGHT CLICK MENUS ###
        # List Widget Right Click Menu

        def on_context_menu_rig_actions(point):
            popMenu_rig_action.exec_(self.rig_actions_listwidget.mapToGlobal(point))

        # for some reason, if the popMenu_rig_action is a class variable, it causes random crashes
        popMenu_rig_action = QtWidgets.QMenu()
        self.rig_actions_listwidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.rig_actions_listwidget.customContextMenuRequested.connect(on_context_menu_rig_actions)

        self.action_rc_rename = QtWidgets.QAction('Rename', self)
        popMenu_rig_action.addAction(self.action_rc_rename)

        self.action_rc_dup = QtWidgets.QAction('Duplicate', self)
        popMenu_rig_action.addAction(self.action_rc_dup)

        popMenu_rig_action.addSeparator()
        self.action_rc_run = QtWidgets.QAction('Run', self)
        popMenu_rig_action.addAction(self.action_rc_run)

        self.action_rc_toggle = QtWidgets.QAction('Toggle Disable/Enable', self)
        popMenu_rig_action.addAction(self.action_rc_toggle)

        ### SHORTCUTS ###
        shortcutRefresh = QtWidgets.QShortcut(QtGui.QKeySequence("F5"), self, self.refresh)

        ### SIGNALS ####

        self.action_rc_rename.triggered.connect(self.on_action_rename)
        self.action_rc_dup.triggered.connect(self.on_action_duplicate)
        self.action_rc_toggle.triggered.connect(self.on_action_toggle)
        # TODO: ADD signals for rc run

        self.add_action_pb.clicked.connect(self.add_actions_menu)
        self.move_action_up_pb.clicked.connect(self.move_action_up)
        self.move_action_down_pb.clicked.connect(self.move_action_down)
        self.delete_action_pb.clicked.connect(self.delete_action)
        self.rig_actions_listwidget.currentItemChanged.connect(self.action_settings_menu)

        self.action_info_pb.clicked.connect(self.on_action_info)

        self.build_pb.clicked.connect(lambda x=0: self.actions_handler.run_all_actions())
        self.rig_actions_listwidget.doubleClicked.connect(lambda x: self.actions_handler.run_action(x.data()))
        # TODO: Make a seperate method for running run actions wih progressbar


    def refresh(self):
        row = self.rig_actions_listwidget.currentRow()
        self.populate_actions()
        self.rig_actions_listwidget.setCurrentRow(row)
        self.populate_properties()

    def populate_recents(self):
        self.recents_menu.clear()
        for recent in db.recentSessions:
            recent_action = QtWidgets.QAction(self.menuFile, text=recent)
            self.recents_menu.addAction(recent_action)
            recent_action.triggered.connect(lambda _=0, x=recent: self.open_trigger(file_path=x))

    def on_action_info(self):
        row = self.rig_actions_listwidget.currentRow()
        if row == -1:
            return
        action_name = self.rig_actions_listwidget.currentItem().text()
        info = self.actions_handler.get_info(action_name)

        self.message_dialog = QtWidgets.QDialog(self)
        self.message_dialog.setWindowTitle("%s Action Information" %(action_name.capitalize().replace("_", " ")))
        # self.message_dialog.resize(800, 700)
        message_layout = QtWidgets.QVBoxLayout(self.message_dialog)
        message_layout.setContentsMargins(0, 0, 0, 0)
        info_te = QtWidgets.QTextEdit()
        info_te.setFont(QtGui.QFont("Courier New", 12, QtGui.QFont.Bold))
        info_te.setReadOnly(True)
        info_te.setText(info)
        message_layout.addWidget(info_te)
        self.message_dialog.show()


    def on_action_rename(self):
        action_name = self.rig_actions_listwidget.currentItem().text()
        rename_dialog = QtWidgets.QDialog()
        rename_dialog.setWindowTitle("Rename Action")
        rename_masterLay = QtWidgets.QVBoxLayout()
        rename_dialog.setLayout(rename_masterLay)
        rename_le = custom_widgets.ValidatedLineEdit(text=action_name)
        rename_masterLay.addWidget(rename_le)
        rename_hlay = QtWidgets.QHBoxLayout()
        rename_masterLay.addLayout(rename_hlay)
        rename_cancel_pb = QtWidgets.QPushButton(text="Cancel")
        rename_ok_pb = QtWidgets.QPushButton(text="Ok")
        rename_le.setConnectedWidgets(rename_ok_pb)
        rename_hlay.addWidget(rename_cancel_pb)
        rename_hlay.addWidget(rename_ok_pb)
        rename_cancel_pb.clicked.connect(rename_dialog.close)
        rename_ok_pb.clicked.connect(rename_dialog.accept)
        r = rename_dialog.exec_()
        if not r:
            return
        #TODO : FOOLPROOF IT _ NON-UNIQUE ACTION NAMES AND ILLEGAL CHARS
        if self.actions_handler.get_action(rename_le.text()) and rename_le.text() != action_name:
            self.feedback.pop_info(title="Existing Action", text="This action name exists. Action names must be unique", critical=True)
            self.on_action_rename()
        self.actions_handler.rename_action(action_name, str(rename_le.text()))
        self.populate_actions()

    def on_action_duplicate(self):
        action_name = self.rig_actions_listwidget.currentItem().text()
        self.actions_handler.duplicate_action(action_name)
        self.populate_actions()

    def on_action_toggle(self):
        action_name = self.rig_actions_listwidget.currentItem().text()
        is_enabled = self.actions_handler.is_enabled(action_name)
        if is_enabled:
            self.actions_handler.disable_action(action_name)
        else:
            self.actions_handler.enable_action(action_name)
        self.populate_actions()

    def new_trigger(self):
        if self.actions_handler.is_modified():
            if self.actions_handler.currentFile:
                file_name = os.path.basename(self.actions_handler.currentFile)
            else:
                file_name = "untitled"
            state = self.feedback.pop_question(title="Save Changes?", text="Save changes to %s?" %file_name, buttons=["yes", "no", "cancel"])
            if state == "yes":
                self.save_trigger()
            elif state == "no":
                pass
            else:
                return

        self.actions_handler.new_session()
        self.populate_actions()
        self.update_title()

    def open_trigger(self, file_path=None):
        if self.actions_handler.is_modified():
            if self.actions_handler.currentFile:
                file_name = os.path.basename(self.actions_handler.currentFile)
            else:
                file_name = "untitled"
            state = self.feedback.pop_question(title="Save Changes?", text="Save changes to %s?" %file_name, buttons=["yes", "no", "cancel"])
            if state == "yes":
                self.save_trigger()
            elif state == "no":
                pass
            else:
                return
        if not file_path:
            dlg = QtWidgets.QFileDialog.getOpenFileName(self, str("Open Trigger Session"), self.actions_handler.currentFile, str("Trigger Session (*.tr)"))
            if dlg[0]:
                file_path = os.path.normpath(dlg[0])
            else:
                return

        self.actions_handler.load_session(file_path)
        db.recentSessions.add(file_path)
        self.populate_actions()
        self.update_title()
        self.populate_recents()
        # self.buildBarsUI()

    def import_trigger(self, file_path=None):
        row = self.rig_actions_listwidget.currentRow()
        index = None if row == -1 else row+1

        if not file_path:
            dlg = QtWidgets.QFileDialog.getOpenFileName(self, str("Open Trigger Session"), self.actions_handler.currentFile, str("Trigger Session (*.tr)"))
            if dlg[0]:
                file_path = os.path.normpath(dlg[0])
            else:
                return

        self.actions_handler.import_session(file_path, insert_index=index)
        self.populate_actions()

    def increment_trigger(self):
        if self.actions_handler.currentFile:
            new_file = naming.increment(self.actions_handler.currentFile)
            self.actions_handler.save_session(new_file)
            db.recentSessions.add(new_file)
            self.update_title()
            self.populate_recents()
        else:
            self.feedback.pop_info(title="Cannot Complete", text="Trigger Session needs to be saved first to increment it\nAborting...", critical=True)

    def save_as_trigger(self):
        dlg = QtWidgets.QFileDialog.getSaveFileName(self, str("Save Trigger Session"), self.actions_handler.currentFile, str("Trigger Session (*.tr)"))
        if dlg[0]:
            self.actions_handler.save_session(os.path.normpath(dlg[0]))
            db.recentSessions.add(os.path.normpath(dlg[0]))
            self.update_title()
            self.populate_recents()

    def save_trigger(self):
        if self.actions_handler.currentFile:
            self.actions_handler.save_session(self.actions_handler.currentFile)
            db.recentSessions.add(self.actions_handler.currentFile)
            self.update_title()
            self.populate_recents()
        else:
            self.save_as_trigger()

    def action_settings_menu(self):
        """Builds the action settings depending on action type"""
        # get the action type
        self.clearLayout(self.action_settings_formLayout)
        row = self.rig_actions_listwidget.currentRow()
        if row == -1:
            return
        action_name = self.rig_actions_listwidget.currentItem().text()
        action_type = self.actions_handler.get_action_type(action_name)
        ctrl = model_ctrl.Controller()
        ctrl.model = self.actions_handler
        ctrl.action_name = action_name

        self.actions_handler.get_layout_ui(action_name, ctrl, self.action_settings_formLayout)

    def add_actions_menu(self):
        list_of_actions = sorted(self.actions_handler.action_data_dict.keys())
        row = self.rig_actions_listwidget.currentRow()
        index = None if row == -1 else row+1

        zortMenu = QtWidgets.QMenu()
        for action_item in list_of_actions:
            icon_path = os.path.join(self.iconsPath, "%s.png" %action_item)
            tempAction = QtWidgets.QAction(QtGui.QIcon(icon_path), action_item, self)
            zortMenu.addAction(tempAction)
            tempAction.triggered.connect(lambda ignore=action_item, item=action_item: self.actions_handler.add_action(action_type=item, insert_index=index))
            tempAction.triggered.connect(self.populate_actions)
            tempAction.triggered.connect(lambda: self.rig_actions_listwidget.setCurrentRow(row+1))
            ## Take note about the usage of lambda "item=z" makes it possible using the loop, ignore -> for discarding emitted value

        self.populate_actions()
        self.rig_actions_listwidget.setCurrentRow(row)
        zortMenu.exec_((QtGui.QCursor.pos()))
    def actions_rc(self):
        pass

    def populate_actions(self):
        self.rig_actions_listwidget.clear()
        self.rig_actions_listwidget.addItems(self.actions_handler.list_action_names())

        for row, action_name in enumerate(self.actions_handler.list_action_names()):
            action_type = self.actions_handler.get_action_type(action_name)
            icon_path = os.path.join(self.iconsPath, "%s.png" % action_type)
            self.rig_actions_listwidget.setIcon(row, icon_path)
            if self.actions_handler.is_enabled(action_name):
                self.rig_actions_listwidget.enableItem(row)
            else:
                self.rig_actions_listwidget.disableItem(row)

        self.update_title()

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
        self.block_all_signals(False)
        self.populate_actions()

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
        self.update_title()

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
                log.error("Missing 'enum_list'")
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
            log.error("Cannot find a proper equivalent for this attribute type %s" % p_type)

        parent_form_layout.addRow(p_lbl, p_widget)

    def update_properties(self, property, value):
        root_jnt = self.guides_list_treeWidget.currentItem().text(2)
        self.guides_handler.init.set_property(root_jnt, property, value)

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
        self.populate_guides()

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