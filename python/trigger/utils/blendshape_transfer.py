from maya import cmds
from trigger.library import deformers, functions, selection
from trigger.ui.qtmaya import getMayaMainWindow
from trigger.ui.Qt import QtWidgets
from trigger.ui import custom_widgets
from trigger.ui import feedback

from PySide2 import QtWidgets # temp

windowName = "Blendshape Transfer v0.0.1"

class BlendshapeTransfer(object):
    def __init__(self, source_mesh=None, target_mesh=None, source_blendshape_grp=None):
        super(BlendshapeTransfer, self).__init__()

        # user defined
        self._sourceMesh = source_mesh
        self._targetMesh = target_mesh
        self._sourceBlendShapeGrp = source_blendshape_grp

        # wrap settings
        self.wrapMode = "surface"
        self.maxDrivers = 1
        self.falloffScale = 1.0
        self.smoothInfluences = 7
        self.smoothNormals = 1
        self.softNormalization = 0
        self.spanSamples = 2

        # class var
        self.wrap_node = None
        self.transferShapesGrp = "tr_transferShapes_grp"
        self.tmpSource = None
        self.tmpTarget = None
        self.blendshapeNode = None

    @property
    def source_mesh(self):
        return self._sourceMesh

    @source_mesh.setter
    def source_mesh(self, new_value):
        self._sourceMesh = new_value

    @property
    def target_mesh(self):
        return self._targetMesh

    @target_mesh.setter
    def target_mesh(self, new_value):
        self._targetMesh = new_value

    @property
    def source_blendshape_grp(self):
        return self._sourceBlendShapeGrp

    @source_blendshape_grp.setter
    def source_blendshape_grp(self, new_value):
        self._sourceBlendShapeGrp = new_value

    def _prepare_meshes(self):
        """adds blendshape and wrap nodes to prepare the transfer"""
        if not cmds.objExists(self.transferShapesGrp):
            cmds.group(name=self.transferShapesGrp, em=True)

        self.tmpSource = cmds.duplicate(self.source_mesh, name="trTMP_blndtrans__source_mesh")[0]
        self.tmpTarget = cmds.duplicate(self.target_mesh, name="trTMP_blndtrans__target_mesh")[0]
        cmds.parent(self.tmpSource, self.transferShapesGrp)
        cmds.hide(self.tmpSource)
        cmds.parent(self.tmpTarget, self.transferShapesGrp)
        source_blendshape_list = functions.getMeshes(self.source_blendshape_grp)

        self.blendshapeNode = cmds.blendShape(source_blendshape_list, self.tmpSource, w=[0, 0], name="trTMP_blndtrans_")
        self.wrap_node = deformers.create_proximity_wrap(self.tmpSource, self.tmpTarget,
                                                    wrap_mode=self.wrapMode,
                                                    falloff_scale=self.falloffScale,
                                                    max_drivers=self.maxDrivers,
                                                    smooth_influences=self.smoothInfluences,
                                                    smooth_normals=self.smoothNormals,
                                                    soft_normalization=self.softNormalization,
                                                    span_samples=self.spanSamples)

    def tweak_wrap(self, property, value):
        if not self.wrap_node:
            return
        cmds.setAttr("%s.%s" %(self.wrap_node, property), value)

    def preview_mode_on(self, offset = (0, 40, 0)):
        self.preview_mode_off() # reset first
        self._prepare_meshes()

        self.qc_blendshapes(self.blendshapeNode)

        # offset the mesh for visibility
        if offset:
            #TODO: get dimensions of the mesh and move accordingly
            offset_cluster = cmds.cluster(self.tmpTarget, name="trTMP_blndtrans__offsetCluster")
            cmds.setAttr("%s.t" % offset_cluster[1], *offset)
            cmds.parent(offset_cluster, self.transferShapesGrp)

    def preview_mode_off(self):
        functions.deleteObject("trTMP_blndtrans_*")
        functions.deleteObject(self.transferShapesGrp)

    @staticmethod
    def qc_blendshapes(blendshape_node, separation=5):
        blend_attributes = cmds.aliasAttr(blendshape_node, q=True)[::2]
        for nmb, attr in enumerate(blend_attributes):
            start_frame = separation * (nmb + 1)
            end_frame = start_frame + (separation - 1)
            cmds.setKeyframe(blendshape_node, at=attr, t=start_frame - 1, value=0)
            cmds.setKeyframe(blendshape_node, at=attr, t=start_frame, value=1)
            cmds.setKeyframe(blendshape_node, at=attr, t=end_frame, value=1)
            cmds.setKeyframe(blendshape_node, at=attr, t=end_frame + 1, value=0)

    def transfer(self):
        self.preview_mode_off()
        self._prepare_meshes()
        blend_attributes = cmds.aliasAttr(self.blendshapeNode, q=True)[::2]
        for attr in blend_attributes:
            cmds.setAttr("%s.%s" %(self.blendshapeNode[0], attr), 1)
            new_blendshape = cmds.duplicate(self.tmpTarget)[0]
            # cmds.parent(new_blendshape, self.transferShapesGrp)
            cmds.rename(new_blendshape, attr)
            cmds.setAttr("%s.%s" %(self.blendshapeNode[0], attr), 0)
        functions.deleteObject("trTMP_blndtrans_*")

class MainUI(QtWidgets.QDialog):
    def __init__(self):
        for entry in QtWidgets.QApplication.allWidgets():
            try:
                if entry.objectName() == windowName:
                    entry.close()
            except (AttributeError, TypeError):
                pass
        parent = getMayaMainWindow()
        super(MainUI, self).__init__(parent=parent)

        self.transfer = BlendshapeTransfer()

        self.setWindowTitle(windowName)
        self.setObjectName(windowName)
        self.feed = feedback.Feedback()
        self.setMinimumSize(250,50)


        self.build_ui()

    def build_ui(self):
        master_vlay = QtWidgets.QVBoxLayout()
        self.setLayout(master_vlay)

        meshes_group = QtWidgets.QGroupBox()
        meshes_group.setTitle("Meshes")
        master_vlay.addWidget(meshes_group)

        meshes_formlayout = QtWidgets.QFormLayout(meshes_group)

        source_mesh_lbl = QtWidgets.QLabel(text="Source Neutral Mesh")
        source_mesh_lbl.setToolTip("The source mesh which has the blendshape pack")
        self.source_mesh_leBox = custom_widgets.LineEditBoxLayout(buttonsPosition="right")
        self.source_mesh_leBox.buttonGet.setText("<")
        self.source_mesh_leBox.buttonGet.setMaximumWidth(30)
        meshes_formlayout.addRow(source_mesh_lbl, self.source_mesh_leBox)

        source_blpack_lbl = QtWidgets.QLabel(text="Blendshapes Group")
        source_blpack_lbl.setToolTip("blendshape group includes all the shapes compatible with the source mesh")
        self.source_blpack_leBox = custom_widgets.LineEditBoxLayout(buttonsPosition="right")
        self.source_blpack_leBox.buttonGet.setText("<")
        self.source_blpack_leBox.buttonGet.setMaximumWidth(30)
        meshes_formlayout.addRow(source_blpack_lbl, self.source_blpack_leBox)
        
        target_mesh_lbl = QtWidgets.QLabel(text="Target Neutral Mesh")
        target_mesh_lbl.setToolTip("The target mesh which does not have a blendshape pack")
        self.target_mesh_leBox = custom_widgets.LineEditBoxLayout(buttonsPosition="right")
        self.target_mesh_leBox.buttonGet.setText("<")
        self.target_mesh_leBox.buttonGet.setMaximumWidth(30)
        meshes_formlayout.addRow(target_mesh_lbl, self.target_mesh_leBox)

        settings_group = QtWidgets.QGroupBox()
        settings_group.setTitle("Settings")
        master_vlay.addWidget(settings_group)

        settings_formlayout = QtWidgets.QFormLayout(settings_group)

        wrap_mode_lbl = QtWidgets.QLabel(text="Wrap Mode")
        self.wrap_mode_combo = QtWidgets.QComboBox()
        self.wrap_mode_combo.addItems(["offset", "surface", "snap", "rigid", "cluster"])
        settings_formlayout.addRow(wrap_mode_lbl, self.wrap_mode_combo)

        falloff_scale_lbl = QtWidgets.QLabel(text="Falloff Scale")
        self.falloff_scale_sp = QtWidgets.QDoubleSpinBox()
        self.falloff_scale_sp.setMinimum(0.01)
        settings_formlayout.addRow(falloff_scale_lbl, self.falloff_scale_sp)

        smooth_influences_lbl = QtWidgets.QLabel(text="Smooth Influences")
        self.smooth_influences_sp = QtWidgets.QSpinBox()
        self.smooth_influences_sp.setMinimum(0)
        settings_formlayout.addRow(smooth_influences_lbl, self.smooth_influences_sp)

        soft_normalization_lbl = QtWidgets.QLabel(text="Soft Normalization")
        self.soft_normalization_cb = QtWidgets.QCheckBox()
        settings_formlayout.addRow(soft_normalization_lbl, self.soft_normalization_cb)

        span_samples_lbl = QtWidgets.QLabel(text="Span Samples")
        self.span_samples_sp = QtWidgets.QSpinBox()
        self.span_samples_sp.setMinimum(0)
        settings_formlayout.addRow(span_samples_lbl, self.span_samples_sp)

        buttons_hlay = QtWidgets.QHBoxLayout()
        master_vlay.addLayout(buttons_hlay)
        preview_pb = QtWidgets.QPushButton(text="Preview")
        preview_pb.setCheckable(True)
        buttons_hlay.addWidget(preview_pb)

        transfer_pb = QtWidgets.QPushButton(text="Transfer")
        buttons_hlay.addWidget(transfer_pb)

        self.update_ui()

        def on_toggle_preview():
            self.update_model()
            if preview_pb.isChecked():
                self.transfer.preview_mode_on()
            else:
                self.transfer.preview_mode_off()

        def on_transfer():
            preview_pb.blockSignals(True)
            self.transfer.transfer()
            preview_pb.setChecked(False)
            preview_pb.blockSignals(False)
        # SIGNALS
        self.source_mesh_leBox.buttonGet.clicked.connect(lambda x=0: self.get_selected(self.source_mesh_leBox.viewWidget))
        self.source_blpack_leBox.buttonGet.clicked.connect(lambda x=0: self.get_selected(self.source_blpack_leBox.viewWidget, group=True))
        self.target_mesh_leBox.buttonGet.clicked.connect(lambda x=0: self.get_selected(self.target_mesh_leBox.viewWidget))

        self.wrap_mode_combo.currentIndexChanged.connect(lambda v, p="wrapMode": self.transfer.tweak_wrap(property=p, value=v))
        self.falloff_scale_sp.valueChanged.connect(lambda v, p="falloffScale": self.transfer.tweak_wrap(property=p, value=v))
        self.smooth_influences_sp.valueChanged.connect(lambda v, p="smoothInfluences": self.transfer.tweak_wrap(property=p, value=v))
        self.soft_normalization_cb.stateChanged.connect(lambda v, p="softNormalization": self.transfer.tweak_wrap(property=p, value=v))
        self.span_samples_sp.valueChanged.connect(lambda v, p="spanSamples": self.transfer.tweak_wrap(property=p, value=v))

        preview_pb.toggled.connect(on_toggle_preview)
        transfer_pb.clicked.connect(on_transfer)

    def update_ui(self):
        self.source_mesh_leBox.viewWidget.setText(self.transfer.source_mesh)
        self.source_blpack_leBox.viewWidget.setText(self.transfer.source_blendshape_grp)
        self.target_mesh_leBox.viewWidget.setText(self.transfer.target_mesh)
        self.wrap_mode_combo.setCurrentText(self.transfer.wrapMode)
        self.falloff_scale_sp.setValue(self.transfer.falloffScale)
        self.smooth_influences_sp.setValue(self.transfer.smoothInfluences)
        self.soft_normalization_cb.setChecked(self.transfer.softNormalization)
        self.span_samples_sp.setValue(self.transfer.spanSamples)

    def update_model(self):
        self.transfer.source_mesh = self.source_mesh_leBox.viewWidget.text()
        self.transfer.source_blendshape_grp = self.source_blpack_leBox.viewWidget.text()
        self.transfer.target_mesh = self.target_mesh_leBox.viewWidget.text()
        self.transfer.wrapMode = self.wrap_mode_combo.currentText()
        self.transfer.falloffScale = self.falloff_scale_sp.value()
        self.transfer.smoothInfluences = self.smooth_influences_sp.value()
        self.transfer.softNormalization = self.soft_normalization_cb.isChecked()
        self.transfer.spanSamples = self.span_samples_sp.value()

    def get_selected(self, line_edit, group=False):
        meshes_only=False if group else True
        selected, msg = selection.validate(min=1, max=1, meshesOnly=meshes_only, groupsOnly=group, transforms=True, fullPath=False)
        if not selected:
            self.feed.pop_info(title="Selection Error", text=msg)
            return
        else:
            line_edit.setText(selected[0])






