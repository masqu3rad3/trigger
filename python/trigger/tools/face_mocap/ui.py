"""UI for Face Mocap."""

import dataclasses
from trigger.ui.Qt import QtWidgets, QtCore
from trigger.ui.qtmaya import get_main_maya_window
from trigger.ui.widgets.browser import FolderBrowserBoxLayout
from trigger.tools.face_mocap import main as focap
from trigger.ui import feedback
from trigger.ui.widgets.information_bar import InformationBar

_version = "1.0.0"
WINDOW_NAME = "Face Mocap v{}".format(_version)


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

@dataclasses.dataclass
class FaceMocapSettings:
    live_link_folder: str = ""
    import_livelink: bool = True
    import_a2f: bool = True
    start_frame: int = 1
    bake_on_controllers: bool = False
    controller: str = "C_all_1_cont"
    a2f_mocap_layer: str = "A2F_mocap_layer"
    livelink_mocap_layer: str = "LiveLink_mocap_layer"

@dataclasses.dataclass
class FaceMocapWidgets:
    live_link_folder: FolderBrowserBoxLayout = None
    import_livelink: QtWidgets.QCheckBox = None
    import_a2f: QtWidgets.QCheckBox = None
    start_frame: QtWidgets.QSpinBox = None
    bake_on_controllers: QtWidgets.QCheckBox = None
    controller: QtWidgets.QLineEdit = None
    a2f_mocap_layer: QtWidgets.QLineEdit = None
    livelink_mocap_layer: QtWidgets.QLineEdit = None
    # loading_progressbar: LoadingProgressBar = None
    information_bar: QtWidgets.QWidget = None
    button_box: QtWidgets.QDialogButtonBox = None

class MainUI(QtWidgets.QDialog):
    def __init__(self):
        parent = get_main_maya_window()
        super(MainUI, self).__init__(parent=parent)
        self.handler = focap.FaceMocap()
        self.data = FaceMocapSettings()
        self.widgets = FaceMocapWidgets()

        self.feedback = feedback.Feedback()

        self.setWindowTitle(WINDOW_NAME)
        self.setObjectName(WINDOW_NAME)

        self.setMinimumSize(300, 200)

        self.build_ui()
        self.connect_signals()

    def build_ui(self):
        """Create the UI for facial mocap."""

        master_layout = QtWidgets.QVBoxLayout()
        self.setLayout(master_layout)

        form_layout = QtWidgets.QFormLayout()
        master_layout.addLayout(form_layout)

        # create a line edit box layout for the Live Link folder
        live_link_folder_lbl = QtWidgets.QLabel("Live Link Folder:")
        self.widgets.live_link_folder = FolderBrowserBoxLayout()
        self.widgets.live_link_folder.line_edit.setPlaceholderText(
            "Set the Live Link folder"
        )
        form_layout.addRow(live_link_folder_lbl, self.widgets.live_link_folder)

        self.widgets.import_livelink = QtWidgets.QCheckBox("Import Live Link")
        self.widgets.import_livelink.setChecked(self.data.import_livelink)
        form_layout.addRow(self.widgets.import_livelink)

        self.widgets.import_a2f = QtWidgets.QCheckBox("Generate Audio to Face")
        self.widgets.import_a2f.setChecked(self.data.import_a2f)
        form_layout.addRow(self.widgets.import_a2f)

        start_frame_lbl = QtWidgets.QLabel("Start Frame:")
        self.widgets.start_frame = QtWidgets.QSpinBox()
        # make the width larger
        self.widgets.start_frame.setFixedWidth(50)
        self.widgets.start_frame.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)

        self.widgets.start_frame.setValue(self.data.start_frame)
        form_layout.addRow(start_frame_lbl, self.widgets.start_frame)

        self.widgets.bake_on_controllers = QtWidgets.QCheckBox("Bake on Controllers")
        self.widgets.bake_on_controllers.setChecked(self.data.bake_on_controllers)
        form_layout.addRow(self.widgets.bake_on_controllers)

        controller_lbl = QtWidgets.QLabel("Master Controller:")
        self.widgets.controller = QtWidgets.QLineEdit()
        self.widgets.controller.setPlaceholderText("Set the controller")
        self.widgets.controller.setText(self.data.controller)
        self.widgets.controller.setEnabled(self.data.bake_on_controllers)
        form_layout.addRow(controller_lbl, self.widgets.controller)

        a2f_mocap_layer_lbl = QtWidgets.QLabel("A2F Mocap Layer:")
        self.widgets.a2f_mocap_layer = QtWidgets.QLineEdit()
        self.widgets.a2f_mocap_layer.setPlaceholderText("Set the A2F mocap layer")
        self.widgets.a2f_mocap_layer.setText(self.data.a2f_mocap_layer)
        self.widgets.a2f_mocap_layer.setDisabled(
            self.data.bake_on_controllers)
        form_layout.addRow(a2f_mocap_layer_lbl, self.widgets.a2f_mocap_layer)

        livelink_mocap_layer_lbl = QtWidgets.QLabel("LiveLink Mocap Layer:")
        self.widgets.livelink_mocap_layer = QtWidgets.QLineEdit()
        self.widgets.livelink_mocap_layer.setPlaceholderText("Set the LiveLink mocap layer")
        self.widgets.livelink_mocap_layer.setText(self.data.livelink_mocap_layer)
        self.widgets.livelink_mocap_layer.setDisabled(self.data.bake_on_controllers)
        form_layout.addRow(livelink_mocap_layer_lbl, self.widgets.livelink_mocap_layer)

        self.widgets.information_bar = InformationBar()
        self.widgets.information_bar.set_text("Ready")
        self.widgets.information_bar.set_border_color("#A9A9A9")
        # set the height of the information bar
        self.widgets.information_bar.setFixedHeight(25)
        master_layout.addWidget(self.widgets.information_bar)

        # create a button box
        self.widgets.button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        master_layout.addWidget(self.widgets.button_box)

        # change the label of the OK button to "Import"
        self.widgets.button_box.button(QtWidgets.QDialogButtonBox.Ok).setText("Apply Animation")


    def connect_signals(self):
        """Connect the signals for the UI."""

        # if the bake on controllers is checked, the controller should be enabled
        self.widgets.bake_on_controllers.stateChanged.connect(self.widgets.controller.setEnabled)

        # and if its unchecked, the a2f mocap layer should be enabled
        self.widgets.bake_on_controllers.stateChanged.connect(self.widgets.a2f_mocap_layer.setDisabled)
        self.widgets.bake_on_controllers.stateChanged.connect(self.widgets.livelink_mocap_layer.setDisabled)

        self.widgets.button_box.accepted.connect(self.apply_animation)
        self.widgets.button_box.rejected.connect(self.close)

    def apply_animation(self):
        """Apply the animation based on the current widget settings."""

        self.widgets.information_bar.set_text("Processing...")
        self.widgets.information_bar.set_border_color("yellow")

        livelink_folder = self.widgets.live_link_folder.line_edit.text()
        if not livelink_folder:
            self.feedback.pop_info(title="Missing information", text="Please set the Live Link folder\n\nThe Live Link folder is required to import the animation.", critical=True)
            self.widgets.loading_progressbar.stop()
            return

        import_livelink = self.widgets.import_livelink.isChecked()
        import_a2f = self.widgets.import_a2f.isChecked()
        start_frame = self.widgets.start_frame.value()
        bake_on_controllers = self.widgets.bake_on_controllers.isChecked()
        controller = self.widgets.controller.text()
        a2f_mocap_layer = self.widgets.a2f_mocap_layer.text()
        livelink_mocap_layer = self.widgets.livelink_mocap_layer.text()

        self.handler.set_controller(controller)
        self.handler.set_a2f_mocap_layer(a2f_mocap_layer)
        self.handler.set_livelink_mocap_layer(livelink_mocap_layer)
        self.handler.set_start_frame(start_frame)

        #################

        QtWidgets.QApplication.processEvents()

        self.handler.import_livelinkface_package(livelink_folder, import_livelink=import_livelink, import_a2f=import_a2f, bake_a2f=bake_on_controllers, bake_livelink=bake_on_controllers)

        self.widgets.information_bar.set_text("Facial Animation Applied")
        self.widgets.information_bar.set_border_color("green")
        #################

