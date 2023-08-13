"""UI for Rom Randomizer"""

from maya import cmds

import logging

from trigger.ui.Qt import QtWidgets, QtCore
from trigger.ui.qtmaya import get_main_maya_window
from trigger.ui.layouts.scene_select import SceneSelectLayout
from trigger.utils.rom_randomizer import rom_randomizer

LOG = logging.getLogger(__name__)

WINDOWNAME = "Rom Randomizer v{}".format(rom_randomizer.__version__)


def launch(force=True):
    for entry in QtWidgets.QApplication.allWidgets():
        try:
            if entry.objectName() == WINDOWNAME:
                if force:
                    entry.close()
                    entry.deleteLater()
                else:
                    return
        except (AttributeError, TypeError):
            pass
    MainUI().show()


class MainUI(QtWidgets.QDialog):
    """Main UI for Rom Randomizer"""

    def __init__(self, parent=get_main_maya_window()):
        super(MainUI, self).__init__(parent=parent)

        self.setWindowTitle(WINDOWNAME)
        self.setObjectName(WINDOWNAME)

        self.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        self.size_policy.setHorizontalStretch(1)
        self.size_policy.setVerticalStretch(0)

        self.rom_generator = rom_randomizer.RomGenerator()

        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setFocus()

        # widgets
        self.hook_node_select_layout = SceneSelectLayout(
            selection_type="object", single_selection=True
        )
        self.additional_controllers_select_layout = SceneSelectLayout(
            selection_type="object", add_button=True, single_selection=False
        )
        self.exclude_attributes_select_layout = SceneSelectLayout(
            selection_type="attribute", add_button=True, single_selection=False
        )

        self.time_slider_rb = QtWidgets.QRadioButton("Time Slider")
        self.custom_range_rb = QtWidgets.QRadioButton("Custom Range")
        self.start_spinbox = QtWidgets.QSpinBox()
        self.start_spinbox.setRange(-999999999, 999999999)
        self.end_spinbox = QtWidgets.QSpinBox()
        self.end_spinbox.setRange(-999999999, 999999999)
        self.method_combobox = QtWidgets.QComboBox()
        self.interval_spinbox = QtWidgets.QSpinBox()
        self.interval_spinbox.setRange(1, 999999999)
        self.min_combinations_spinbox = QtWidgets.QSpinBox()
        self.min_combinations_spinbox.setRange(1, 999999999)
        self.max_combinations_spinbox = QtWidgets.QSpinBox()
        self.max_combinations_spinbox.setRange(1, 999999999)
        self.symmetry_cb = QtWidgets.QCheckBox()
        self.seed_sp = QtWidgets.QSpinBox()
        self.seed_sp.setRange(1, 999999999)

        self.build_ui()

    def build_ui(self):
        """Build ui."""
        master_vlay = QtWidgets.QVBoxLayout()
        self.setLayout(master_vlay)

        # Collection
        # ---------------------------------------------------------------------
        collection_group = QtWidgets.QGroupBox(title="Collection")
        master_vlay.addWidget(collection_group)
        collection_formlayout = QtWidgets.QFormLayout(collection_group)

        # collection_formlayout.setAlignment(QtCore.Qt.AlignCenter)

        hook_node_lbl = QtWidgets.QLabel("Hook Node")
        hook_node_lbl.setToolTip(
            "When defined, the controllers that connected to this node will be collected."
        )
        # self.hook_node_select_layout = SceneSelectLayout(selection_type="object", single_selection=True)
        collection_formlayout.addRow(hook_node_lbl, self.hook_node_select_layout)

        additional_controllers_lbl = QtWidgets.QLabel("Additional Controllers")
        additional_controllers_lbl.setToolTip(
            "Add any controller(s). Semi-colon separated. Wildcards are supported."
        )
        # self.additional_controllers_select_layout = SceneSelectLayout(selection_type="object", add_button=True, single_selection=False)
        collection_formlayout.addRow(
            additional_controllers_lbl, self.additional_controllers_select_layout
        )

        exclude_attributes_lbl = QtWidgets.QLabel("Exclude Attributes")
        exclude_attributes_lbl.setToolTip(
            "Any attributes defined in here (semi-colon separated) will be excluded from the rom. This affects to all collected controllers."
        )
        # self.exclude_attributes_select_layout = SceneSelectLayout(selection_type="attribute", add_button=True, single_selection=False)
        collection_formlayout.addRow(
            exclude_attributes_lbl, self.exclude_attributes_select_layout
        )

        # Options
        # ---------------------------------------------------------------------
        options_group = QtWidgets.QGroupBox(title="Options")
        master_vlay.addWidget(options_group)
        options_formlayout = QtWidgets.QFormLayout(options_group)

        # options_formlayout.setAlignment(QtCore.Qt.AlignCenter)

        time_range_lbl = QtWidgets.QLabel("Time Range")

        time_range_layout = QtWidgets.QVBoxLayout(margin=0)
        time_range_selection_layout = QtWidgets.QHBoxLayout(margin=0)
        time_range_layout.addLayout(time_range_selection_layout)
        # make a radio button selection to choose between time slider or custom range
        # time_slider_rb = QtWidgets.QRadioButton("Time Slider")
        time_range_selection_layout.addWidget(self.time_slider_rb)
        # custom_range_rb = QtWidgets.QRadioButton("Custom Range")
        time_range_selection_layout.addWidget(self.custom_range_rb)

        # make two spinboxes for the custom range
        time_range_spinbox_layout = QtWidgets.QHBoxLayout(margin=0)
        time_range_layout.addLayout(time_range_spinbox_layout)
        # start_spinbox = QtWidgets.QSpinBox(range=(-999999999, 999999999)
        # end_spinbox = QtWidgets.QSpinBox(range=(-999999999, 999999999)

        # make the default range 0-100
        self.start_spinbox.setValue(0)
        self.end_spinbox.setValue(100)

        time_range_spinbox_layout.addWidget(self.start_spinbox)
        time_range_spinbox_layout.addWidget(self.end_spinbox)

        options_formlayout.addRow(time_range_lbl, time_range_layout)

        # disable the custom range spinboxes if the time slider is selected
        def disable_spinboxes():
            # if the time slider is selected, disable the spinboxes
            if self.time_slider_rb.isChecked():
                self.start_spinbox.setEnabled(False)
                self.end_spinbox.setEnabled(False)
            else:
                self.start_spinbox.setEnabled(True)
                self.end_spinbox.setEnabled(True)

        self.time_slider_rb.toggled.connect(disable_spinboxes)
        self.custom_range_rb.toggled.connect(disable_spinboxes)
        self.time_slider_rb.setChecked(True)

        method_lbl = QtWidgets.QLabel("Method")
        # method_combobox = QtWidgets.QComboBox()
        self.method_combobox.addItems(self.rom_generator.methods.keys())

        options_formlayout.addRow(method_lbl, self.method_combobox)

        interval_lbl = QtWidgets.QLabel("Interval Between Poses")

        # interval_spinbox.setRange(1, 999999999)
        self.interval_spinbox.setValue(5)

        options_formlayout.addRow(interval_lbl, self.interval_spinbox)

        min_max_combinations_lbl = QtWidgets.QLabel("Min/Max Combinations")
        min_max_combinations_spinbox_layout = QtWidgets.QHBoxLayout(margin=0)

        # min_combinations_spinbox = QtWidgets.QSpinBox(range=(1, 999999999))
        self.min_combinations_spinbox.setValue(2)
        min_max_combinations_spinbox_layout.addWidget(self.min_combinations_spinbox)

        # max_combinations_spinbox = QtWidgets.QSpinBox(range=(1, 999999999))
        # max_combinations_spinbox.setRange(1, 999999999)
        self.max_combinations_spinbox.setValue(4)
        min_max_combinations_spinbox_layout.addWidget(self.max_combinations_spinbox)

        options_formlayout.addRow(
            min_max_combinations_lbl, min_max_combinations_spinbox_layout
        )

        # disable the interval spinbox if the method is random combinations
        def method_toggle():
            state = self.method_combobox.currentText() != "Random Poses"
            self.min_combinations_spinbox.setEnabled(state)
            self.max_combinations_spinbox.setEnabled(state)

        self.method_combobox.currentTextChanged.connect(method_toggle)
        method_toggle()

        symmetry_lbl = QtWidgets.QLabel("Symmetry")
        options_formlayout.addRow(symmetry_lbl, self.symmetry_cb)

        seed_lbl = QtWidgets.QLabel("Seed")
        seed_spinbox_layout = QtWidgets.QHBoxLayout(margin=0)
        seed_enable_cb = QtWidgets.QCheckBox()
        seed_spinbox_layout.addWidget(seed_enable_cb)
        # seed_sp = QtWidgets.QSpinBox(range=(1, 9999999999))
        seed_spinbox_layout.addWidget(self.seed_sp)
        options_formlayout.addRow(seed_lbl, seed_spinbox_layout)

        # disable the spinbox if the checkbox is not checked
        def seed_toggle():
            self.seed_sp.setEnabled(seed_enable_cb.isChecked())

        seed_enable_cb.toggled.connect(seed_toggle)
        seed_toggle()

        # Buttons
        # ---------------------------------------------------------------------
        button_hlay = QtWidgets.QHBoxLayout()
        master_vlay.addLayout(button_hlay)

        # create the buttons
        clear_animation_btn = QtWidgets.QPushButton("Clear Animation")
        random_pose_btn = QtWidgets.QPushButton("Random Pose")
        generate_rom_btn = QtWidgets.QPushButton("Generate ROM")

        # add the buttons to the layout
        button_hlay.addWidget(clear_animation_btn)
        button_hlay.addWidget(random_pose_btn)
        button_hlay.addWidget(generate_rom_btn)

        # SIGNALS

        clear_animation_btn.clicked.connect(self.on_clear_animation)
        random_pose_btn.clicked.connect(self.on_random_pose)
        generate_rom_btn.clicked.connect(self.on_generate_rom)

    def _get_collector(self):
        """Get the collector object from the scene."""
        collector = rom_randomizer.Collector()
        if self.hook_node_select_layout.selection:
            collector.add_hooked_controllers(self.hook_node_select_layout.selection[0])
        if self.additional_controllers_select_layout.selection:
            for controller in self.additional_controllers_select_layout.selection:
                # list them again to resolve wildcards
                _scene_controllers = cmds.ls(controller, type="transform")
                _ = [collector.add_controller(c) for c in _scene_controllers]
        if self.exclude_attributes_select_layout.selection:
            collector.excluded_attributes = (
                self.exclude_attributes_select_layout.selection
            )

        return collector

    def on_clear_animation(self):
        """Clear animation callback."""
        rom = rom_randomizer.RomGenerator(self._get_collector())
        rom.clear_keys()

    def on_random_pose(self):
        """Random pose callback."""
        rom = rom_randomizer.RomGenerator(self._get_collector())
        seed = self.seed_spinbox.value() if self.seed_sp.isEnabled() else None
        rom.random_pose(seed=seed)

    def on_generate_rom(self):
        """Generate ROM callback."""
        # rom = rom_randomizer.RomGenerator(self._get_collector())
        self.rom_generator.set_collector(self._get_collector())
        # collect the options
        if self.time_slider_rb.isChecked():
            # get the range from the maya time slider
            start = cmds.playbackOptions(query=True, animationStartTime=True)
            end = cmds.playbackOptions(query=True, animationEndTime=True)
        else:
            start = self.start_spinbox.value()
            end = self.end_spinbox.value()
        # method = self.method_combobox.currentIndex() # 0 = random poses, 1 = random combinations
        method = (
            self.method_combobox.currentText()
        )  # 0 = random poses, 1 = random combinations
        interval = self.interval_spinbox.value()
        min_combinations = self.min_combinations_spinbox.value()
        max_combinations = self.max_combinations_spinbox.value()
        symmetry = self.symmetry_cb.isChecked()
        seed = self.seed_spinbox.value() if self.seed_sp.isEnabled() else None
        self.rom_generator.symmetry = symmetry
        generate_function = self.rom_generator.methods[method]
        generate_function(
            start_frame=start,
            duration=end - start,
            interval=interval,
            minimum_combinations=min_combinations,
            maximum_combinations=max_combinations,
            seed=seed,
        )
        # if method == 0:
        #     rom.generate_random_poses_rom(start_frame=start, duration=end-start, interval=interval, seed=seed)
        # elif method == 1:
        # else:
        #     LOG.warning("Unknown method: {}".format(method))
