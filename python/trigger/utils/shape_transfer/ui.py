import logging

# from PySide2 import QtWidgets
from trigger.ui.Qt import QtWidgets, QtCore
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
            if data.type == "combo":
                label = QtWidgets.QLabel(text=property_name)
                combo = QtWidgets.QComboBox()
                combo.setObjectName(property_name)
                combo.addItems(data.items)
                combo.setCurrentIndex(data.default)
                self.formlayout.addRow(label, combo)
                combo.currentIndexChanged.connect(data.set_value)
            elif data.type == "integer":
                label = QtWidgets.QLabel(text=property_name)
                spinbox = QtWidgets.QSpinBox()
                spinbox.setObjectName(property_name)
                spinbox.setMinimum(data.minimum)
                spinbox.setMaximum(data.maximum)
                spinbox.setValue(data.default)
                self.formlayout.addRow(label, spinbox)
                spinbox.valueChanged.connect(data.set_value)
            elif data.type == "float":
                label = QtWidgets.QLabel(text=property_name)
                spinbox = QtWidgets.QDoubleSpinBox()
                spinbox.setObjectName(property_name)
                spinbox.setMinimum(data.minimum)
                spinbox.setMaximum(data.maximum)
                spinbox.setValue(data.default)
                self.formlayout.addRow(label, spinbox)
                spinbox.valueChanged.connect(data.set_value)
            elif data.type == "boolean":
                label = QtWidgets.QLabel(text=property_name)
                checkbox = QtWidgets.QCheckBox()
                checkbox.setObjectName(property_name)
                checkbox.setChecked(data.default)
                self.formlayout.addRow(label, checkbox)
                checkbox.stateChanged.connect(data.set_value)
            elif data.type == "slider":
                label = QtWidgets.QLabel(text=property_name)
                # slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
                slider = DoubleSlider(QtCore.Qt.Horizontal)
                # slider = QtWidgets.QDial()
                slider.setObjectName(property_name)
                slider.setMinimum(0)
                slider.setMaximum(100.0)
                slider.set_original_minimum(data.minimum)
                slider.set_original_maximum(data.maximum)
                slider.setValue(data.default)
                # adjust the slide step size according to the range
                self.formlayout.addRow(label, slider)
                slider.doubleValueChanged.connect(data.set_value)

    def setVisible(self, visible):
        """Override the setVisible method to set the layout visible and the protocol visible."""
        super(ProtocolWidget, self).setVisible(visible)
        self._protocol["visibility"].value = visible
        self.initialize_values()

    def initialize_values(self):
        """Get the values from the protocol object and update the widgets."""
        for property_name, data in self._protocol.items():
            if property_name in self.excluded_property_names:
                continue
            widget = self.findChild(QtWidgets.QWidget, property_name)
            if isinstance(widget, QtWidgets.QComboBox):
                widget.setCurrentIndex(data.value)
            elif isinstance(widget, QtWidgets.QSpinBox):
                widget.setValue(data.value)
            elif isinstance(widget, QtWidgets.QDoubleSpinBox):
                widget.setValue(data.value)
            elif isinstance(widget, QtWidgets.QCheckBox):
                widget.setChecked(data.value)
            elif isinstance(widget, QtWidgets.QSlider):
                widget.setValue(data.value)


# class MainUI(QtWidgets.QDialog):
class MainUI(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(MainUI, self).__init__(parent=parent)
        self.transfer_handler = ShapeTransfer()

        self.setWindowTitle(WINDOWNAME)
        self.setObjectName(WINDOWNAME)
        self.feed = Feedback()

        self.centralwidget = QtWidgets.QWidget(self)
        self.centralwidget.setObjectName("centralwidget")
        self.setCentralWidget(self.centralwidget)

        self.master_vlay = QtWidgets.QVBoxLayout(self.centralwidget)
        # self.setLayout(self.master_vlay)

        # STaTUS BAR
        self.statusbar = QtWidgets.QStatusBar(self)
        self.setStatusBar(self.statusbar)

        self.progress_bar = None

        self.build_ui()
        self.setMinimumSize(290, 600)

    def build_bars(self):
        """Build the menu and status bars."""
        menu_bar = QtWidgets.QMenuBar(self, geometry=QtCore.QRect(0, 0, 1680, 18))
        self.setMenuBar(menu_bar)

        file_menu = menu_bar.addMenu("File")
        tools_menu = menu_bar.addMenu("Tools")
        help_menu = menu_bar.addMenu("Help")

        # File Menu
        export_active_shape = QtWidgets.QAction("&Export Active Shape", self)
        file_menu.addAction(export_active_shape)
        export_active_sequence = QtWidgets.QAction("&Export Active Sequence", self)
        file_menu.addAction(export_active_sequence)
        file_menu.addSeparator()
        ingest_shape = QtWidgets.QAction("&Ingest Shape", self)
        file_menu.addAction(ingest_shape)
        ingest_sequence = QtWidgets.QAction("&Ingest Sequence", self)
        file_menu.addAction(ingest_sequence)

        # Tools Menu
        replace_shape = QtWidgets.QAction("&Replace Shape", self)
        replace_shape.setToolTip("Replace the selected shape with the active shape")
        tools_menu.addAction(replace_shape)
        replace_sequence = QtWidgets.QAction("&Replace Sequence", self)
        replace_sequence.setToolTip(
            "Replace the selected animated shape with the active preview sequence"
        )
        tools_menu.addAction(replace_sequence)

        # Create a progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        # self.progress_bar.setRange(0, 2000)
        # self.progress_bar.setValue(25)
        # self.progress_bar.reset()
        # self.progress_bar.setTextVisible(True)
        # self.progress_bar.setFormat("%p%")
        self.master_vlay.addWidget(self.progress_bar)

        # SIGNALS
        # TODO: Add signals for the menu actions

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

        # set the initial visibility values to the transfer_handler
        self.on_source_visibility(source_visible_cb.isChecked())
        self.on_target_visibility(target_visible_cb.isChecked())

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

    def build_buttons(self):
        """Build command buttons."""

        buttons_hlay = QtWidgets.QHBoxLayout()
        self.master_vlay.addLayout(buttons_hlay)

        self.preview_pb = QtWidgets.QPushButton(text="Preview")
        self.preview_pb.setCheckable(True)
        buttons_hlay.addWidget(self.preview_pb)

        refresh_pb = QtWidgets.QPushButton(text="R")
        refresh_pb.setMaximumWidth(15)
        buttons_hlay.addWidget(refresh_pb)

        transfer_pb = QtWidgets.QPushButton(text="Transfer")
        buttons_hlay.addWidget(transfer_pb)

        # SIGNALS
        # when the preview button is clicked
        self.preview_pb.clicked.connect(self.on_preview)

        transfer_pb.clicked.connect(self.on_transfer)

    def build_ui(self):
        """Build the UI."""

        self.build_commons()
        self.build_general_settings()
        self.build_transfer_tabs()
        self.build_bars()
        self.build_buttons()

    def set_protocol(self, *args, **kwargs):
        """Set the active protocol on shape_transfer object according to the active tab and protocol combo box."""

        # get the active tab
        active_tab = self.tab_widget.currentWidget()

        # if the active tab is the shape transfer tab
        if active_tab == self.shape_transfer_tab:
            # get the protocol id from the combo box
            protocol_id = self.shape_transfer_type_combo.currentIndex()
            _protocol = self.transfer_handler.shape_protocols[protocol_id]
            self.transfer_handler.set_active_protocol(_protocol)
            # find the protocol widget using the id and set it visible and the rest invisible
            for protocol_widget in self.shape_widgets:

                protocol_widget.setVisible(protocol_widget._protocol == _protocol)
            # hide all the topology widgets
            _ = [
                protocol_widget.setVisible(False)
                for protocol_widget in self.topology_widgets
            ]

        elif active_tab == self.topology_transfer_tab:
            # get the protocol id from the combo box
            protocol_id = self.topology_transfer_type_combo.currentIndex()
            _protocol = self.transfer_handler.topology_protocols[protocol_id]
            self.transfer_handler.set_active_protocol(_protocol)
            for protocol_widget in self.topology_widgets:
                protocol_widget.setVisible(protocol_widget._protocol == _protocol)
            # hide all the shape widgets
            _ = [
                protocol_widget.setVisible(False)
                for protocol_widget in self.shape_widgets
            ]
        else:
            pass

    def on_preview(self, state):
        """Set the preview mode on the transfer handler."""

        state, message = self.transfer_handler.preview_mode(turn_on=state)
        if not state:
            self.feed.pop_info(title="Preview Error", text=message, critical=True)
            self.preview_pb.setChecked(False)
            return
        # update the active widget values
        active_tab = self.tab_widget.currentWidget()

        if active_tab == self.shape_transfer_tab:
            for protocol_widget in self.shape_widgets:
                protocol_widget.initialize_values()
        elif active_tab == self.topology_transfer_tab:
            for protocol_widget in self.topology_widgets:
                protocol_widget.initialize_values()

        self.statusbar.showMessage(message, 5000)

    def on_transfer(self):
        """Run the transfer and inform the user about the progress and result."""
        state, message = self.transfer_handler.transfer(q_progressbar=self.progress_bar)
        if not state:
            self.feed.pop_info(title="Transfer Error", text=message, critical=True)
            return
        # uncheck the preview button and emit its signal
        self.preview_pb.setChecked(False)
        self.preview_pb.clicked.emit()
        # TODO: Add a feedback message

        self.statusbar.showMessage(message, 5000)

    def on_source_visibility(self, value):
        """Set visibility of all sources on all protocols."""
        for protocol in self.transfer_handler.all_protocols:
            protocol["source_visibility"].value = bool(value)

    def on_target_visibility(self, value):
        """Set visibility of all sources on all protocols."""
        for protocol in self.transfer_handler.all_protocols:
            protocol["target_visibility"].value = bool(value)


class DoubleSlider(QtWidgets.QSlider):

    # create our our signal that we can connect to if necessary
    doubleValueChanged = QtCore.Signal(float)

    def __init__(self, *args, **kargs):
        super(DoubleSlider, self).__init__( *args, **kargs)
        # self._multi = 10 ** decimals
        self._multi = 10 ** 3.0

        self._original_minimum = 0.0
        self._original_maximum = 1.0


        self.valueChanged.connect(self.emitDoubleValueChanged)

    def set_original_minimum(self, value):
        self._original_minimum =  round(value, 2)

    def set_original_maximum(self, value):
        self._original_maximum = round(value, 2)

    def map_to_slider(self, value):
        """map the value from original range to the slider range (0-100)"""
        return int(( round(value, 2) - self._original_minimum) / (self._original_maximum - self._original_minimum) * 100.0)

    def map_to_original(self, value):
        """map the value from slider range (0-100) to the original range"""
        return  round((value / 100.0), 2) * (self._original_maximum - self._original_minimum) + self._original_minimum

    def emitDoubleValueChanged(self):
        _raw_value = float(super(DoubleSlider, self).value())
        value = round((_raw_value / self._multi), 2)
        self.doubleValueChanged.emit(self.map_to_original(value))

    def value(self):
        _raw_value = float(super(DoubleSlider, self).value())
        value = round((_raw_value / self._multi), 2)
        return (self.map_to_original(value))

    def setMinimum(self, value):
        return super(DoubleSlider, self).setMinimum(value * self._multi)

    def setMaximum(self, value):
        return super(DoubleSlider, self).setMaximum(value * self._multi)

    def setSingleStep(self, value):
        return super(DoubleSlider, self).setSingleStep(value * self._multi)

    def singleStep(self):
        return float(super(DoubleSlider, self).singleStep()) / self._multi

    def setValue(self, value):
        mapped_value = round(self.map_to_slider(value),2)
        super(DoubleSlider, self).setValue(int(mapped_value * self._multi))
