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
        meshes_formlayout.addRow(source_mesh_lbl, source_mesh_ssl)

        source_blpack_lbl = QtWidgets.QLabel(text="Blendshapes Group")
        source_blpack_lbl.setToolTip(
            "blendshape group includes all the shapes compatible with the source mesh"
        )
        source_blpack_ssl = SceneSelectLayout(
            selection_type="object", single_selection=True
        )
        meshes_formlayout.addRow(source_blpack_lbl, source_blpack_ssl)

        target_mesh_lbl = QtWidgets.QLabel(text="Target Neutral Mesh")
        target_mesh_lbl.setToolTip(
            "The target mesh which does not have a blendshape pack"
        )
        target_mesh_ssl = SceneSelectLayout(
            selection_type="object", single_selection=True
        )
        meshes_formlayout.addRow(target_mesh_lbl, target_mesh_ssl)

    def build_general_settings(self):
        """Build generic settings."""

        gen_settings_group = QtWidgets.QGroupBox()
        gen_settings_group.setTitle("General Settings")
        self.master_vlay.addWidget(gen_settings_group)

        gen_settings_formlayout = QtWidgets.QFormLayout(gen_settings_group)

        offset_preview_mesh_lbl = QtWidgets.QLabel(text="Offset Preview Mesh")
        offset_preview_mesh_hlay = QtWidgets.QHBoxLayout()
        self.offset_x_sp = QtWidgets.QDoubleSpinBox(minimum=-99999, maximum=99999)
        self.offset_y_sp = QtWidgets.QDoubleSpinBox(minimum=-99999, maximum=99999)
        self.offset_z_sp = QtWidgets.QDoubleSpinBox(minimum=-99999, maximum=99999)
        offset_preview_mesh_hlay.addWidget(self.offset_x_sp)
        offset_preview_mesh_hlay.addWidget(self.offset_y_sp)
        offset_preview_mesh_hlay.addWidget(self.offset_z_sp)
        gen_settings_formlayout.addRow(
            offset_preview_mesh_lbl, offset_preview_mesh_hlay
        )
        mesh_visibility_hlay = QtWidgets.QHBoxLayout()
        mesh_visibility_lbl = QtWidgets.QLabel(text="Mesh Visibilities")

        # source_visible_lbl = QtWidgets.QLabel(text="Source Visible")
        self.source_visible_cb = QtWidgets.QCheckBox()
        self.source_visible_cb.setText("Source")
        mesh_visibility_hlay.addWidget(self.source_visible_cb)

        self.target_visible_cb = QtWidgets.QCheckBox()
        self.target_visible_cb.setText("Target")
        self.target_visible_cb.setChecked(True)
        mesh_visibility_hlay.addWidget(self.target_visible_cb)

        switch_btn = QtWidgets.QPushButton()
        switch_btn.setText("Switch")
        mesh_visibility_hlay.addWidget(switch_btn)

        gen_settings_formlayout.addRow(mesh_visibility_lbl, mesh_visibility_hlay)

    def build_transfer_tabs(self):
        """Create a tabbed layout for the transfer protocols."""

        tab_widget = QtWidgets.QTabWidget()
        self.master_vlay.addWidget(tab_widget)

        shape_transfer_tab = QtWidgets.QWidget()
        tab_widget.addTab(shape_transfer_tab, "Shape Transfer")
        topology_transfer_tab = QtWidgets.QWidget()
        tab_widget.addTab(topology_transfer_tab, "Topology Transfer")

        # Shape Transfer
        shape_transfer_formlayout = QtWidgets.QFormLayout(shape_transfer_tab)
        shape_transfer_protocol_names = [
            protocol.display_name for protocol in self.transfer_handler.shape_protocols
        ]
        shape_transfer_type_lbl = QtWidgets.QLabel(text="Transfer Type")
        shape_transfer_type_combo = QtWidgets.QComboBox()
        shape_transfer_type_combo.addItems(shape_transfer_protocol_names)
        shape_transfer_formlayout.addRow(shape_transfer_type_lbl, shape_transfer_type_combo)


        # Topology Transfer
        topology_transfer_formlayout = QtWidgets.QFormLayout(topology_transfer_tab)
        topology_transfer_protocol_names = [
            protocol.display_name for protocol in self.transfer_handler.topology_protocols
        ]
        topology_transfer_type_lbl = QtWidgets.QLabel(text="Transfer Type")
        topology_transfer_type_combo = QtWidgets.QComboBox()
        topology_transfer_type_combo.addItems(topology_transfer_protocol_names)
        topology_transfer_formlayout.addRow(topology_transfer_type_lbl, topology_transfer_type_combo)


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

    def build_ui(self):
        """Build the UI."""

        self.build_commons()
        self.build_general_settings()
        self.build_transfer_tabs()
        self.build_buttons()

        return

        # meshes_group = QtWidgets.QGroupBox()
        # meshes_group.setTitle("Meshes")
        # master_vlay.addWidget(meshes_group)
        #
        # meshes_formlayout = QtWidgets.QFormLayout(meshes_group)
        #
        # source_mesh_lbl = QtWidgets.QLabel(text="Source Neutral Mesh")
        # source_mesh_lbl.setToolTip(
        #     "The source mesh which has the blendshape pack"
        # )
        # self.source_mesh_leBox = LineEditBoxLayout(
        #     buttonsPosition="right"
        # )
        # self.source_mesh_leBox.buttonGet.setText("<")
        # self.source_mesh_leBox.buttonGet.setMaximumWidth(30)
        # meshes_formlayout.addRow(source_mesh_lbl, self.source_mesh_leBox)
        #
        # source_blpack_lbl = QtWidgets.QLabel(text="Blendshapes Group")
        # source_blpack_lbl.setToolTip(
        #     "blendshape group includes all the shapes compatible with the source mesh"
        # )
        # self.source_blpack_leBox = LineEditBoxLayout(
        #     buttonsPosition="right"
        # )
        # self.source_blpack_leBox.buttonGet.setText("<")
        # self.source_blpack_leBox.buttonGet.setMaximumWidth(30)
        # meshes_formlayout.addRow(source_blpack_lbl, self.source_blpack_leBox)
        #
        # target_mesh_lbl = QtWidgets.QLabel(text="Target Neutral Mesh")
        # target_mesh_lbl.setToolTip(
        #     "The target mesh which does not have a blendshape pack"
        # )
        # self.target_mesh_leBox = LineEditBoxLayout(
        #     buttonsPosition="right"
        # )
        # self.target_mesh_leBox.buttonGet.setText("<")
        # self.target_mesh_leBox.buttonGet.setMaximumWidth(30)
        # meshes_formlayout.addRow(target_mesh_lbl, self.target_mesh_leBox)

        # gen_settings_group = QtWidgets.QGroupBox()
        # gen_settings_group.setTitle("General Settings")
        # master_vlay.addWidget(gen_settings_group)
        #
        # gen_settings_formlayout = QtWidgets.QFormLayout(gen_settings_group)
        #
        # offset_preview_mesh_lbl = QtWidgets.QLabel(text="Offset Preview Mesh")
        # offset_preview_mesh_hlay = QtWidgets.QHBoxLayout()
        # self.offset_x_sp = QtWidgets.QDoubleSpinBox(
        #     minimum=-99999, maximum=99999
        # )
        # self.offset_y_sp = QtWidgets.QDoubleSpinBox(
        #     minimum=-99999, maximum=99999
        # )
        # self.offset_z_sp = QtWidgets.QDoubleSpinBox(
        #     minimum=-99999, maximum=99999
        # )
        # offset_preview_mesh_hlay.addWidget(self.offset_x_sp)
        # offset_preview_mesh_hlay.addWidget(self.offset_y_sp)
        # offset_preview_mesh_hlay.addWidget(self.offset_z_sp)
        # gen_settings_formlayout.addRow(
        #     offset_preview_mesh_lbl, offset_preview_mesh_hlay
        # )
        # mesh_visibility_hlay = QtWidgets.QHBoxLayout()
        # mesh_visibility_lbl = QtWidgets.QLabel(text="Mesh Visibilities")
        #
        # # source_visible_lbl = QtWidgets.QLabel(text="Source Visible")
        # self.source_visible_cb = QtWidgets.QCheckBox()
        # self.source_visible_cb.setText("Source")
        # mesh_visibility_hlay.addWidget(self.source_visible_cb)
        #
        # self.target_visible_cb = QtWidgets.QCheckBox()
        # self.target_visible_cb.setText("Target")
        # self.target_visible_cb.setChecked(True)
        # mesh_visibility_hlay.addWidget(self.target_visible_cb)
        #
        # switch_btn = QtWidgets.QPushButton()
        # switch_btn.setText("Switch")
        # mesh_visibility_hlay.addWidget(switch_btn)
        #
        # gen_settings_formlayout.addRow(
        #     mesh_visibility_lbl, mesh_visibility_hlay
        # )

        # shape transfer group
        shape_transfer_group = QtWidgets.QGroupBox()
        shape_transfer_group.setTitle("Shape Transfer Group")
        master_vlay.addWidget(shape_transfer_group)
        transfer_select_formlayout = QtWidgets.QFormLayout(shape_transfer_group)
        transfer_type_lbl = QtWidgets.QLabel(text="Transfer Type")
        self.transfer_type_combo = QtWidgets.QComboBox()
        self.transfer_type_combo.addItems(self.transfer.available_transfer_modes)
        transfer_select_formlayout.addRow(transfer_type_lbl, self.transfer_type_combo)

        # deformer group
        deformer_select_group = QtWidgets.QGroupBox()
        deformer_select_group.setTitle("Topology Transfer Group")
        master_vlay.addWidget(deformer_select_group)
        deformer_select_formlayout = QtWidgets.QFormLayout(deformer_select_group)
        deformer_type_lbl = QtWidgets.QLabel(text="Deformer")
        self.deformer_type_combo = QtWidgets.QComboBox()
        self.deformer_type_combo.addItems(self.transfer.available_wrap_modes)
        deformer_select_formlayout.addRow(deformer_type_lbl, self.deformer_type_combo)

        # proximity wrap settings
        self.prx_wrap_settings_group = QtWidgets.QGroupBox()
        self.prx_wrap_settings_group.setTitle("Proximity Wrap Settings")
        master_vlay.addWidget(self.prx_wrap_settings_group)

        prx_wrap_settings_formlayout = QtWidgets.QFormLayout(
            self.prx_wrap_settings_group
        )

        wrap_mode_lbl = QtWidgets.QLabel(text="Wrap Mode")
        self.wrap_mode_combo = QtWidgets.QComboBox()
        self.wrap_mode_combo.addItems(["offset", "surface", "snap", "rigid", "cluster"])
        prx_wrap_settings_formlayout.addRow(wrap_mode_lbl, self.wrap_mode_combo)

        falloff_scale_lbl = QtWidgets.QLabel(text="Falloff Scale")
        self.falloff_scale_sp = QtWidgets.QDoubleSpinBox()
        self.falloff_scale_sp.setMinimum(0.01)
        prx_wrap_settings_formlayout.addRow(falloff_scale_lbl, self.falloff_scale_sp)

        smooth_influences_lbl = QtWidgets.QLabel(text="Smooth Influences")
        self.smooth_influences_sp = QtWidgets.QSpinBox()
        self.smooth_influences_sp.setMinimum(0)
        prx_wrap_settings_formlayout.addRow(
            smooth_influences_lbl, self.smooth_influences_sp
        )

        soft_normalization_lbl = QtWidgets.QLabel(text="Soft Normalization")
        self.soft_normalization_cb = QtWidgets.QCheckBox()
        prx_wrap_settings_formlayout.addRow(
            soft_normalization_lbl, self.soft_normalization_cb
        )

        span_samples_lbl = QtWidgets.QLabel(text="Span Samples")
        self.span_samples_sp = QtWidgets.QSpinBox()
        self.span_samples_sp.setMinimum(0)
        prx_wrap_settings_formlayout.addRow(span_samples_lbl, self.span_samples_sp)

        # dnWrap settings
        self.dn_wrap_settings_group = QtWidgets.QGroupBox()
        self.dn_wrap_settings_group.setVisible(False)
        self.dn_wrap_settings_group.setTitle("dnWrap Settings")
        master_vlay.addWidget(self.dn_wrap_settings_group)

        dn_settings_formlayout = QtWidgets.QFormLayout(self.dn_wrap_settings_group)

        dn_quality_lbl = QtWidgets.QLabel(text="Quality")
        self.dn_quality_sp = QtWidgets.QSpinBox()
        self.dn_quality_sp.setMinimum(1)
        dn_settings_formlayout.addRow(dn_quality_lbl, self.dn_quality_sp)

        dn_shrink_lbl = QtWidgets.QLabel(text="Shrink")
        self.dn_shrink_cb = QtWidgets.QCheckBox()
        dn_settings_formlayout.addRow(dn_shrink_lbl, self.dn_shrink_cb)

        dn_falloff_lbl = QtWidgets.QLabel(text="Falloff")
        self.dn_falloff_cb = QtWidgets.QCheckBox()
        dn_settings_formlayout.addRow(dn_falloff_lbl, self.dn_falloff_cb)

        dn_max_distance_lbl = QtWidgets.QLabel(text="Max Distance")
        self.dn_max_distance_sp = QtWidgets.QDoubleSpinBox()
        self.dn_max_distance_sp.setMinimum(0.0)
        dn_settings_formlayout.addRow(dn_max_distance_lbl, self.dn_max_distance_sp)

        dn_falloff_width_lbl = QtWidgets.QLabel(text="Falloff Width")
        self.dn_falloff_width_sp = QtWidgets.QDoubleSpinBox()
        self.dn_falloff_width_sp.setMinimum(0.0)
        dn_settings_formlayout.addRow(dn_falloff_width_lbl, self.dn_falloff_width_sp)

        dn_use_normals_lbl = QtWidgets.QLabel(text="Use Normals")
        self.dn_use_normals_cb = QtWidgets.QCheckBox()
        dn_settings_formlayout.addRow(dn_use_normals_lbl, self.dn_use_normals_cb)

        dn_normal_tolerance_angle_lbl = QtWidgets.QLabel(text="Normal Tolerance Angle")
        self.dn_normal_tolerance_angle_sp = QtWidgets.QDoubleSpinBox()
        self.dn_normal_tolerance_angle_sp.setMinimum(0.0)
        dn_settings_formlayout.addRow(
            dn_normal_tolerance_angle_lbl, self.dn_normal_tolerance_angle_sp
        )

        dn_use_uvs_lbl = QtWidgets.QLabel(text="Use UVs")
        self.dn_use_uvs_cb = QtWidgets.QCheckBox()
        dn_settings_formlayout.addRow(dn_use_uvs_lbl, self.dn_use_uvs_cb)

        buttons_hlay = QtWidgets.QHBoxLayout()
        master_vlay.addLayout(buttons_hlay)
        preview_pb = QtWidgets.QPushButton(text="Preview")
        preview_pb.setCheckable(True)
        buttons_hlay.addWidget(preview_pb)

        refresh_pb = QtWidgets.QPushButton(text="R")
        refresh_pb.setMaximumWidth(15)
        buttons_hlay.addWidget(refresh_pb)

        transfer_pb = QtWidgets.QPushButton(text="Transfer")
        buttons_hlay.addWidget(transfer_pb)

        self.update_ui()

        def on_toggle_preview():
            self.update_model()
            if preview_pb.isChecked():
                if self.transfer.is_same_topology(
                    self.transfer.source_mesh, self.transfer.target_mesh
                ):
                    self.prx_wrap_settings_group.setEnabled(False)
                else:
                    self.prx_wrap_settings_group.setEnabled(True)
                self.transfer.preview_mode_on()
            else:
                self.prx_wrap_settings_group.setEnabled(True)
                self.transfer.preview_mode_off()

        def on_transfer():
            self.update_model()
            preview_pb.blockSignals(True)
            self.transfer.transfer()
            preview_pb.setChecked(False)
            preview_pb.blockSignals(False)

        def set_wrap_mode(index_value):
            """Make only selected deformers settings visible"""
            self.transfer.wrap_mode = index_value
            if preview_pb.isChecked():
                self.transfer.preview_mode_on()  # this will restart the preview
            if index_value == 0:  # proximity
                self.prx_wrap_settings_group.setVisible(True)
                self.dn_wrap_settings_group.setVisible(False)
            elif index_value == 1:  # dn
                self.prx_wrap_settings_group.setVisible(False)
                self.dn_wrap_settings_group.setVisible(True)
            else:
                return

        def set_transfer_mode(index_value):
            """Set the transfer mode both in UI elements and transfer obj."""
            if index_value == 1:  # zTransfer
                if not self.transfer.validate_plugin("zMayaToolkit"):
                    self.feed.pop_info(
                        title="Plugin Error",
                        text="zMayaToolkit cannot be initialized. zDeformationTransfer requires zMayaToolkit.",
                        critical=True,
                    )
                    self.transfer_type_combo.setCurrentIndex(0)
                    return
            self.transfer.transfer_mode = index_value
            if preview_pb.isChecked():
                self.transfer.preview_mode_on()  # this will restart the preview
            # TODO anything else?

        def on_source_visibility(value):
            self.transfer.source_visible = bool(value)

        def on_target_visibility(value):
            self.transfer.target_visible = bool(value)

        def on_switch_visibility():
            """Toggle visibility between the source and target meshes."""
            _source = self.transfer.source_visible
            _target = self.transfer.target_visible
            if _source != _target:  # Check if a and b have different states
                self.source_visible_cb.setChecked(_target)
                self.target_visible_cb.setChecked(_source)

        # #######
        # SIGNALS
        # #######

        self.source_mesh_leBox.buttonGet.clicked.connect(
            lambda x=0: self.get_selected(self.source_mesh_leBox.viewWidget)
        )
        self.source_blpack_leBox.buttonGet.clicked.connect(
            lambda x=0: self.get_selected(
                self.source_blpack_leBox.viewWidget, group=True
            )
        )
        self.target_mesh_leBox.buttonGet.clicked.connect(
            lambda x=0: self.get_selected(self.target_mesh_leBox.viewWidget)
        )

        self.offset_x_sp.valueChanged.connect(self.on_tweak_offset)
        self.offset_y_sp.valueChanged.connect(self.on_tweak_offset)
        self.offset_z_sp.valueChanged.connect(self.on_tweak_offset)
        self.source_visible_cb.stateChanged.connect(on_source_visibility)
        self.target_visible_cb.stateChanged.connect(on_target_visibility)
        switch_btn.clicked.connect(on_switch_visibility)

        self.deformer_type_combo.currentIndexChanged.connect(set_wrap_mode)
        self.transfer_type_combo.currentIndexChanged.connect(set_transfer_mode)

        self.wrap_mode_combo.currentIndexChanged.connect(
            lambda v, p="wrapMode": self.transfer.tweak_wrap(property=p, value=v)
        )
        self.falloff_scale_sp.editingFinished.connect(
            lambda p="falloffScale": self.transfer.tweak_wrap(
                property=p,
                value=self.falloff_scale_sp.value(),
            )
        )
        self.smooth_influences_sp.valueChanged.connect(
            lambda _, p="smoothInfluences": self.transfer.tweak_wrap(
                property=p, value=self.smooth_influences_sp.value()
            )
        )
        self.soft_normalization_cb.stateChanged.connect(
            lambda v, p="softNormalization": self.transfer.tweak_wrap(
                property=p, value=bool(v)
            )
        )
        self.span_samples_sp.valueChanged.connect(
            lambda _, p="spanSamples": self.transfer.tweak_wrap(
                property=p, value=self.span_samples_sp.value()
            )
        )

        self.dn_quality_sp.editingFinished.connect(
            lambda p="quality": self.transfer.tweak_wrap(
                property=p, value=int(self.dn_quality_sp.value())
            )
        )
        self.dn_shrink_cb.stateChanged.connect(
            lambda v, p="shrink": self.transfer.tweak_wrap(property=p, value=bool(v))
        )
        self.dn_falloff_cb.stateChanged.connect(
            lambda v, p="falloff": self.transfer.tweak_wrap(property=p, value=bool(v))
        )
        self.dn_max_distance_sp.editingFinished.connect(
            lambda p="maxDistance": self.transfer.tweak_wrap(
                property=p, value=self.dn_max_distance_sp.value()
            )
        )
        self.dn_falloff_width_sp.editingFinished.connect(
            lambda p="falloffWidth": self.transfer.tweak_wrap(
                property=p, value=self.dn_falloff_width_sp.value()
            )
        )
        self.dn_use_normals_cb.stateChanged.connect(
            lambda v, p="useNormals": self.transfer.tweak_wrap(
                property=p, value=bool(v)
            )
        )
        self.dn_normal_tolerance_angle_sp.editingFinished.connect(
            lambda p="normalToleranceAngle": self.transfer.tweak_wrap(
                property=p, value=self.dn_normal_tolerance_angle_sp.value()
            )
        )
        self.dn_use_uvs_cb.stateChanged.connect(
            lambda v, p="useUvs": self.transfer.tweak_wrap(property=p, value=bool(v))
        )

        preview_pb.toggled.connect(on_toggle_preview)
        refresh_pb.clicked.connect(self.transfer.refresh)
        transfer_pb.clicked.connect(on_transfer)

    def on_tweak_offset(self):
        offset_value = (
            self.offset_x_sp.value(),
            self.offset_y_sp.value(),
            self.offset_z_sp.value(),
        )
        self.transfer.tweak_offset(offset_value)

    def update_ui(self):
        # mesh
        self.source_mesh_leBox.viewWidget.setText(self.transfer.source_mesh)
        self.source_blpack_leBox.viewWidget.setText(self.transfer.source_blendshape_grp)
        self.target_mesh_leBox.viewWidget.setText(self.transfer.target_mesh)
        # general
        self.offset_x_sp.setValue(self.transfer.offsetValue[0])
        self.offset_y_sp.setValue(self.transfer.offsetValue[1])
        self.offset_z_sp.setValue(self.transfer.offsetValue[2])
        self.source_visible_cb.setChecked(self.transfer.source_visible)
        # shape transfer
        self.transfer_type_combo.setCurrentIndex(self.transfer.transfer_mode)

        # proxymity wrap
        self.wrap_mode_combo.setCurrentText(self.transfer.prx_wrap_type)
        self.falloff_scale_sp.setValue(self.transfer.falloffScale)
        self.smooth_influences_sp.setValue(self.transfer.smoothInfluences)
        self.soft_normalization_cb.setChecked(self.transfer.softNormalization)
        self.span_samples_sp.setValue(self.transfer.spanSamples)
        # dnWrap
        self.dn_quality_sp.setValue(self.transfer.dn_quality)
        self.dn_shrink_cb.setChecked(self.transfer.dn_shrink)
        self.dn_falloff_cb.setChecked(self.transfer.dn_falloff)
        self.dn_max_distance_sp.setValue(self.transfer.dn_max_distance)
        self.dn_falloff_width_sp.setValue(self.transfer.dn_faloff_width)
        self.dn_use_normals_cb.setChecked(self.transfer.dn_use_normals)
        self.dn_normal_tolerance_angle_sp.setValue(
            self.transfer.dn_normal_tolerance_angle
        )
        self.dn_use_uvs_cb.setChecked(self.transfer.dn_use_uvs)

    def update_model(self):
        # mesh
        self.transfer.source_mesh = self.source_mesh_leBox.viewWidget.text()
        self.transfer.source_blendshape_grp = self.source_blpack_leBox.viewWidget.text()
        self.transfer.target_mesh = self.target_mesh_leBox.viewWidget.text()
        # general
        self.transfer.offsetValue[0] = self.offset_x_sp.value()
        self.transfer.offsetValue[1] = self.offset_y_sp.value()
        self.transfer.offsetValue[2] = self.offset_z_sp.value()
        self.transfer.source_visible = self.source_visible_cb.isChecked()
        # shape transfer
        self.transfer.transfer_mode = self.transfer_type_combo.currentIndex()

        # wrap
        self.transfer.prx_wrap_type = self.wrap_mode_combo.currentText()
        self.transfer.falloffScale = self.falloff_scale_sp.value()
        self.transfer.smoothInfluences = self.smooth_influences_sp.value()
        self.transfer.softNormalization = self.soft_normalization_cb.isChecked()
        self.transfer.spanSamples = self.span_samples_sp.value()

    def get_selected(self, line_edit, group=False):
        meshes_only = False if group else True
        selected, msg = validate(
            minimum=1,
            maximum=1,
            meshes_only=meshes_only,
            groups_only=group,
            transforms=True,
            full_path=False,
        )
        if not selected:
            self.feed.pop_info(title="Selection Error", text=msg)
            return
        else:
            line_edit.setText(selected[0])
