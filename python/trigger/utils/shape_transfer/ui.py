import logging

# from PySide2 import QtWidgets
from trigger.ui.Qt import QtWidgets
from trigger.ui import qtmaya

# import dnmayalib

from trigger.utils.shape_transfer.main import ShapeTransfer
from trigger.ui.feedback import Feedback
from trigger.ui.layouts.scene_select import SceneSelectLayout

# from utils import validate
# from widgets import Feedback, LineEditBoxLayout

# from Qt import QtWidgets


LOG = logging.getLogger(__name__)

WINDOWNAME = "Shape Transfer v1.0.0"


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
    # parent = dnmayalib.interface.main_window()
    parent = qtmaya.get_main_maya_window()
    MainUI(parent).show()


class ProtocolWidget(QtWidgets.QWidget):
    """Custom Layout for protocol properties."""

    # TODO: Instead of exclusion list, add a new key to the property to define the widgets exclusion
    excluded_property_names = ["visibility", "source_visibility", "target_visibility"]

    def __init__(self, protocol_object):
        super(ProtocolWidget, self).__init__()
        self._protocol = protocol_object

        self.master_vlay = QtWidgets.QVBoxLayout(self)
        self.formlayout = QtWidgets.QFormLayout()
        self.master_vlay.addLayout(self.formlayout)

        self.build_layout()

    def build_layout(self):
        """Build the layout."""

        # build the protocol properties
        for property_name, data in self._protocol.items():
            if property_name in self.excluded_property_names:
                continue
            print(property_name)
            print(data)
            if data.type == "combo":
                label = QtWidgets.QLabel(text=property_name)
                combo = QtWidgets.QComboBox()
                combo.addItems(data.items)
                combo.setCurrentIndex(data.default)
                self.formlayout.addRow(label, combo)
                combo.currentIndexChanged.connect(data.set_value)
            elif data.type == "integer":
                label = QtWidgets.QLabel(text=property_name)
                spinbox = QtWidgets.QSpinBox()
                spinbox.setMinimum(data.minimum)
                spinbox.setMaximum(data.maximum)
                spinbox.setValue(data.default)
                self.formlayout.addRow(label, spinbox)
                spinbox.valueChanged.connect(data.set_value)
            elif data.type == "float":
                label = QtWidgets.QLabel(text=property_name)
                spinbox = QtWidgets.QDoubleSpinBox()
                spinbox.setMinimum(data.minimum)
                spinbox.setMaximum(data.maximum)
                spinbox.setValue(data.default)
                self.formlayout.addRow(label, spinbox)
                spinbox.valueChanged.connect(data.set_value)
            elif data.type == "boolean":
                label = QtWidgets.QLabel(text=property_name)
                checkbox = QtWidgets.QCheckBox()
                checkbox.setChecked(data.default)
                self.formlayout.addRow(label, checkbox)
                checkbox.stateChanged.connect(data.set_value)

    def setVisible(self, visible):
        """Override the setVisible method to set the layout visible and the protocol visible."""
        super(ProtocolWidget, self).setVisible(visible)
        print("setVisible -- dbg")
        print(self._protocol.name)
        print("setVisible -- dbg")

        self._protocol["visibility"].value = visible


class MainUI(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(MainUI, self).__init__(parent=parent)
        self.transfer_handler = ShapeTransfer()

        self.setWindowTitle(WINDOWNAME)
        self.setObjectName(WINDOWNAME)
        self.feed = Feedback()

        self.master_vlay = QtWidgets.QVBoxLayout()
        self.setLayout(self.master_vlay)

        self.build_ui()
        self.setMinimumSize(290, 600)

    def build_commons(self):
        """Build the commons section."""

        meshes_group = QtWidgets.QGroupBox()
        meshes_group.setTitle("Meshes")
        self.master_vlay.addWidget(meshes_group)

        meshes_formlayout = QtWidgets.QFormLayout(meshes_group)

        source_mesh_lbl = QtWidgets.QLabel(text="Source Neutral Mesh")
        source_mesh_lbl.setToolTip("The source mesh which has the blendshape pack")
        source_mesh_ssl = SceneSelectLayout(
            selection_type="object", single_selection=True
        )
        source_mesh_ssl.select_textbox.setText(self.transfer_handler._source_mesh)
        meshes_formlayout.addRow(source_mesh_lbl, source_mesh_ssl)

        source_blpack_lbl = QtWidgets.QLabel(text="Blendshapes Group")
        source_blpack_lbl.setToolTip(
            "blendshape group includes all the shapes compatible with the source mesh"
        )
        source_blpack_ssl = SceneSelectLayout(
            selection_type="object", single_selection=True
        )
        source_blpack_ssl.select_textbox.setText(
            self.transfer_handler._source_blendshape_grp
        )
        meshes_formlayout.addRow(source_blpack_lbl, source_blpack_ssl)

        target_mesh_lbl = QtWidgets.QLabel(text="Target Neutral Mesh")
        target_mesh_lbl.setToolTip(
            "The target mesh which does not have a blendshape pack"
        )
        target_mesh_ssl = SceneSelectLayout(
            selection_type="object", single_selection=True
        )
        target_mesh_ssl.select_textbox.setText(self.transfer_handler._target_mesh)
        meshes_formlayout.addRow(target_mesh_lbl, target_mesh_ssl)

        # SIGNALS
        source_mesh_ssl.select_textbox.textChanged.connect(
            self.transfer_handler.set_source_mesh
        )
        source_blpack_ssl.select_textbox.textChanged.connect(
            self.transfer_handler.set_source_blendshape_grp
        )
        target_mesh_ssl.select_textbox.textChanged.connect(
            self.transfer_handler.set_target_mesh
        )

    def build_general_settings(self):
        """Build generic settings."""

        gen_settings_group = QtWidgets.QGroupBox()
        gen_settings_group.setTitle("General Settings")
        self.master_vlay.addWidget(gen_settings_group)

        gen_settings_formlayout = QtWidgets.QFormLayout(gen_settings_group)

        offset_preview_mesh_lbl = QtWidgets.QLabel(text="Offset Preview Mesh")
        offset_preview_mesh_hlay = QtWidgets.QHBoxLayout()
        offset_x_sp = QtWidgets.QDoubleSpinBox(minimum=-99999, maximum=99999)
        offset_y_sp = QtWidgets.QDoubleSpinBox(minimum=-99999, maximum=99999)
        offset_z_sp = QtWidgets.QDoubleSpinBox(minimum=-99999, maximum=99999)

        # get the initial transform values from the scene transform node
        offset_x_sp.setValue(self.transfer_handler.get_offset_x())
        offset_y_sp.setValue(self.transfer_handler.get_offset_y())
        offset_z_sp.setValue(self.transfer_handler.get_offset_z())

        offset_preview_mesh_hlay.addWidget(offset_x_sp)
        offset_preview_mesh_hlay.addWidget(offset_y_sp)
        offset_preview_mesh_hlay.addWidget(offset_z_sp)
        gen_settings_formlayout.addRow(
            offset_preview_mesh_lbl, offset_preview_mesh_hlay
        )
        mesh_visibility_hlay = QtWidgets.QHBoxLayout()
        mesh_visibility_lbl = QtWidgets.QLabel(text="Mesh Visibilities")

        # source_visible_lbl = QtWidgets.QLabel(text="Source Visible")
        source_visible_cb = QtWidgets.QCheckBox()
        source_visible_cb.setText("Source")
        mesh_visibility_hlay.addWidget(source_visible_cb)

        target_visible_cb = QtWidgets.QCheckBox()
        target_visible_cb.setText("Target")
        target_visible_cb.setChecked(True)
        mesh_visibility_hlay.addWidget(target_visible_cb)

        switch_btn = QtWidgets.QPushButton()
        switch_btn.setText("Switch")
        mesh_visibility_hlay.addWidget(switch_btn)

        gen_settings_formlayout.addRow(mesh_visibility_lbl, mesh_visibility_hlay)

        def on_switch_visibility():
            """Switch the checked status between source and target checkboxes."""
            _source = source_visible_cb.isChecked()
            _target = target_visible_cb.isChecked()
            if _source != _target:  # Check if a and b have different states
                source_visible_cb.setChecked(_target)
                target_visible_cb.setChecked(_source)

        # SIGNALS
        offset_x_sp.valueChanged.connect(self.transfer_handler.set_offset_x)
        offset_y_sp.valueChanged.connect(self.transfer_handler.set_offset_y)
        offset_z_sp.valueChanged.connect(self.transfer_handler.set_offset_z)

        switch_btn.clicked.connect(on_switch_visibility)
        source_visible_cb.stateChanged.connect(self.on_source_visibility)
        target_visible_cb.stateChanged.connect(self.on_target_visibility)

    def build_transfer_tabs(self):
        """Create a tabbed layout for the transfer protocols."""

        self.tab_widget = QtWidgets.QTabWidget()
        self.master_vlay.addWidget(self.tab_widget)

        self.shape_transfer_tab = QtWidgets.QWidget()
        self.tab_widget.addTab(self.shape_transfer_tab, "Shape Transfer")

        self.topology_transfer_tab = QtWidgets.QWidget()
        self.tab_widget.addTab(self.topology_transfer_tab, "Topology Transfer")

        # Shape Transfer
        shape_transfer_formlayout = QtWidgets.QFormLayout(self.shape_transfer_tab)
        shape_transfer_protocol_names = [
            protocol.display_name for protocol in self.transfer_handler.shape_protocols
        ]
        shape_transfer_type_lbl = QtWidgets.QLabel(text="Transfer Type")
        self.shape_transfer_type_combo = QtWidgets.QComboBox()
        self.shape_transfer_type_combo.addItems(shape_transfer_protocol_names)
        shape_transfer_formlayout.addRow(
            shape_transfer_type_lbl, self.shape_transfer_type_combo
        )

        shape_transfer_protocol_settings_vlay = QtWidgets.QVBoxLayout()
        shape_transfer_formlayout.addRow(shape_transfer_protocol_settings_vlay)
        self.shape_widgets = []
        for protocol in self.transfer_handler.shape_protocols:
            protocol_widget = ProtocolWidget(protocol)
            shape_transfer_protocol_settings_vlay.addWidget(protocol_widget)
            self.shape_widgets.append(protocol_widget)

        # Topology Transfer
        topology_transfer_formlayout = QtWidgets.QFormLayout(self.topology_transfer_tab)
        topology_transfer_protocol_names = [
            protocol.display_name
            for protocol in self.transfer_handler.topology_protocols
        ]
        topology_transfer_type_lbl = QtWidgets.QLabel(text="Transfer Type")
        self.topology_transfer_type_combo = QtWidgets.QComboBox()
        self.topology_transfer_type_combo.addItems(topology_transfer_protocol_names)
        topology_transfer_formlayout.addRow(
            topology_transfer_type_lbl, self.topology_transfer_type_combo
        )

        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll_area.setFrameShadow(QtWidgets.QFrame.Sunken)
        scroll_area.setWidgetResizable(True)
        contents = QtWidgets.QWidget()
        scroll_area.setWidget(contents)

        topology_transfer_protocol_settings_vlay = QtWidgets.QVBoxLayout(contents)
        topology_transfer_formlayout.addRow(scroll_area)

        self.topology_widgets = []
        for protocol in self.transfer_handler.topology_protocols:
            protocol_widget = ProtocolWidget(protocol)
            topology_transfer_protocol_settings_vlay.addWidget(protocol_widget)
            self.topology_widgets.append(protocol_widget)

        # run the set_protocol method to set the active protocol
        self.set_protocol()

        # SIGNALS
        # when tab is changed update the active protocol by calling the set_protocol
        self.tab_widget.currentChanged.connect(self.set_protocol)
        self.shape_transfer_type_combo.currentIndexChanged.connect(self.set_protocol)
        self.topology_transfer_type_combo.currentIndexChanged.connect(self.set_protocol)

    def set_protocol(self, *args, **kwargs):
        """Set the active protocol on shape_transfer object according to the active tab and protocol combo box."""

        print("set_protocol -- dbg")
        # get the active tab
        active_tab = self.tab_widget.currentWidget()

        # if the active tab is the shape transfer tab
        if active_tab == self.shape_transfer_tab:
            print("shape transfer tab")
            # get the protocol id from the combo box
            protocol_id = self.shape_transfer_type_combo.currentIndex()
            _protocol = self.transfer_handler.shape_protocols[protocol_id]
            self.transfer_handler.set_active_protocol(_protocol)
            # find the protocol widget using the id and set it visible and the rest invisible
            for protocol_widget in self.shape_widgets:
                if protocol_widget._protocol == _protocol:
                    protocol_widget.setVisible(True)
                else:
                    protocol_widget.setVisible(False)

        elif active_tab == self.topology_transfer_tab:
            print("topology transfer tab")
            # get the protocol id from the combo box
            protocol_id = self.topology_transfer_type_combo.currentIndex()
            _protocol = self.transfer_handler.topology_protocols[protocol_id]
            self.transfer_handler.set_active_protocol(_protocol)
            for protocol_widget in self.topology_widgets:
                if protocol_widget._protocol == _protocol:
                    protocol_widget.setVisible(True)
                else:
                    protocol_widget.setVisible(False)
        else:
            pass

        print(self.transfer_handler.active_protocol.name)
        print(self.transfer_handler.active_protocol.display_name)

    def build_buttons(self):
        """Build command buttons."""

        buttons_hlay = QtWidgets.QHBoxLayout()
        self.master_vlay.addLayout(buttons_hlay)

        preview_pb = QtWidgets.QPushButton(text="Preview")
        preview_pb.setCheckable(True)
        buttons_hlay.addWidget(preview_pb)

        refresh_pb = QtWidgets.QPushButton(text="R")
        refresh_pb.setMaximumWidth(15)
        buttons_hlay.addWidget(refresh_pb)

        transfer_pb = QtWidgets.QPushButton(text="Transfer")
        buttons_hlay.addWidget(transfer_pb)

        # SIGNALS
        # when the preview button is clicked
        preview_pb.clicked.connect(self.transfer_handler.preview_mode)

    def build_ui(self):
        """Build the UI."""

        self.build_commons()
        self.build_general_settings()
        self.build_transfer_tabs()
        self.build_buttons()

        return

    def on_source_visibility(self, value):
        """Set visibility of all sources on all protocols."""
        for protocol in self.transfer_handler.all_protocols:
            protocol["source_visibility"].value = bool(value)

    def on_target_visibility(self, value):
        """Set visibility of all sources on all protocols."""
        for protocol in self.transfer_handler.all_protocols:
            protocol["target_visibility"].value = bool(value)

    # def on_switch_visibility(self):
    #     """Toggle visibility between the source and target meshes."""
    #     _source = self.transfer.source_visible
    #     _target = self.transfer.target_visible
    #     if _source != _target:  # Check if a and b have different states
    #         self.source_visible_cb.setChecked(_target)
    #         self.target_visible_cb.setChecked(_source)

    # def on_source_visibility(value):
    #     self.transfer.source_visible = bool(value)
    #
    # def on_target_visibility(value):
    #     self.transfer.target_visible = bool(value)
    #
    # def on_switch_visibility():
    #     """Toggle visibility between the source and target meshes."""
    #     _source = self.transfer.source_visible
    #     _target = self.transfer.target_visible
    #     if _source != _target:  # Check if a and b have different states
    #         self.source_visible_cb.setChecked(_target)
    #         self.target_visible_cb.setChecked(_source)
