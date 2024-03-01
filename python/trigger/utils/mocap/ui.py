"""UI for mocap mapper."""

from trigger.ui.Qt import QtWidgets
from trigger.ui.qtmaya import get_main_maya_window
from trigger.ui.widgets.browser import FileBrowserBoxLayout
from trigger.utils.mocap import mapper

_version = "0.1.0"
WINDOW_NAME = "Mocap Mapper v{}".format(_version)


def launch(force=True):
    for entry in QtWidgets.QApplication.allWidgets():
        try:
            if entry.objectName() == WINDOW_NAME:
                if force:
                    entry.close()
                    entry.deleteLater()
                else:
                    return
        except (AttributeError, TypeError):
            pass
    MainUI().show()


class MainUI(QtWidgets.QDialog):
    def __init__(self):
        parent = get_main_maya_window()
        super(MainUI, self).__init__(parent=parent)
        self._mocap_mapper = mapper.MocapMapper()

        self.setWindowTitle(WINDOW_NAME)
        self.setObjectName(WINDOW_NAME)

        self.setMinimumSize(800, 200)

        self.build_ui()

    def build_ui(self):
        """Create UI for mocap mapper."""

        # create a master vertical layout
        master_layout = QtWidgets.QVBoxLayout()
        self.setLayout(master_layout)

        # create a form layout to hold the options and settings
        form_layout = QtWidgets.QFormLayout()
        master_layout.addLayout(form_layout)

        # create a combo box to select the mapping
        mapping_lbl = QtWidgets.QLabel("Mapping Template:")
        mapping_combo = QtWidgets.QComboBox()
        mapping_combo.addItems(self._mocap_mapper.list_mappings())
        form_layout.addRow(mapping_lbl, mapping_combo)

        # create a line edit box layout for bind pose fbx file
        bind_pose_fbx_lbl = QtWidgets.QLabel("Bind Pose FBX File:")
        bind_pose_fbx_fbox = FileBrowserBoxLayout()
        bind_pose_fbx_fbox.line_edit.setPlaceholderText(
            "Set the bind pose FBX (optional)"
        )

        form_layout.addRow(bind_pose_fbx_lbl, bind_pose_fbx_fbox)

        # create a line edit box layout for animation fbx file
        anim_fbx_lbl = QtWidgets.QLabel("Animation FBX File:")
        anim_fbx_fbox = FileBrowserBoxLayout()
        anim_fbx_fbox.line_edit.setPlaceholderText("Set the animation FBX")
        form_layout.addRow(anim_fbx_lbl, anim_fbx_fbox)

        # create a checkbox to keep the fbx file
        keep_fbx_lbl = QtWidgets.QLabel("Keep FBX File:")
        keep_fbx_chk = QtWidgets.QCheckBox()
        keep_fbx_chk.setChecked(self._mocap_mapper.keep_fbx)
        form_layout.addRow(keep_fbx_lbl, keep_fbx_chk)

        # create a checkbox to bake the animation
        bake_lbl = QtWidgets.QLabel("Bake Animation:")
        bake_chk = QtWidgets.QCheckBox()
        bake_chk.setChecked(self._mocap_mapper.bake)
        form_layout.addRow(bake_lbl, bake_chk)

        # create a button box
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        master_layout.addWidget(button_box)

        # change the label of the OK button to "Import"
        button_box.button(QtWidgets.QDialogButtonBox.Ok).setText("Apply Animation")

        # SIGNALS
        mapping_combo.currentTextChanged.connect(self._mocap_mapper.set_mapping)
        bind_pose_fbx_fbox.line_edit.textChanged.connect(
            self._mocap_mapper.set_bind_pose_fbx
        )
        anim_fbx_fbox.line_edit.textChanged.connect(self._mocap_mapper.set_anim_fbx)
        keep_fbx_chk.stateChanged.connect(self._mocap_mapper.set_keep_fbx)
        bake_chk.stateChanged.connect(self._mocap_mapper.set_bake)
        button_box.accepted.connect(self._mocap_mapper.apply_animation)
        button_box.rejected.connect(self.close)
