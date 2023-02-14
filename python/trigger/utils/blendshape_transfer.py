from maya import cmds
import maya.api.OpenMaya as om
from trigger.core.decorators import viewportOff, keepselection

from trigger.library import deformers, functions, selection, interface, api

from trigger.ui.qtmaya import getMayaMainWindow
from trigger.ui.Qt import QtWidgets
from trigger.ui import custom_widgets
from trigger.ui import feedback

from PySide2 import QtWidgets # temp

windowName = "Blendshape Transfer v0.0.2"

class BlendshapeTransfer(object):
    def __init__(self, source_mesh=None, target_mesh=None, source_blendshape_grp=None):
        super(BlendshapeTransfer, self).__init__()

        # user defined
        self._sourceMesh = source_mesh
        self._targetMesh = target_mesh
        self._sourceBlendShapeGrp = source_blendshape_grp

        # general settings
        self.offsetValue = [0,40,0]
        self.offsetCluster = None
        self.annotationsGrp = None

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

    @staticmethod
    @keepselection
    def _unlock_normals(mesh):
        cmds.select(mesh)
        cmds.UnlockNormals()

    def _prepare_meshes(self):
        """adds blendshape and wrap nodes to prepare the transfer"""
        if not cmds.objExists(self.transferShapesGrp):
            cmds.group(name=self.transferShapesGrp, em=True)

        self.tmpSource = cmds.duplicate(self.source_mesh, name="trTMP_blndtrans__source_mesh")[0]
        self.tmpTarget = cmds.duplicate(self.target_mesh, name="trTMP_blndtrans__target_mesh")[0]
        self._unlock_normals(self.tmpSource)
        self._unlock_normals(self.tmpTarget)
        cmds.parent(self.tmpSource, self.transferShapesGrp)
        cmds.hide(self.tmpSource)
        cmds.parent(self.tmpTarget, self.transferShapesGrp)
        source_blendshape_list = functions.get_meshes(self.source_blendshape_grp)

        if self.is_same_topology(self.tmpSource, self.tmpTarget):
            self.blendshapeNode = cmds.blendShape(source_blendshape_list, self.tmpTarget, w=[0, 0], name="trTMP_blndtrans_blendshape")
            next_index = cmds.blendShape(self.blendshapeNode, q=True, wc=True)
            cmds.blendShape(self.blendshapeNode, edit=True, t=(self.tmpTarget, next_index, self.source_mesh, 1.0), w=[next_index, -1.0])
            # rename is something obvious to treat differently in QC
            cmds.aliasAttr("negateSource", "%s.w[%i]" %(self.blendshapeNode[0], next_index))
        else:
            self.blendshapeNode = cmds.blendShape(source_blendshape_list, self.tmpSource, w=[0, 0], name="trTMP_blndtrans_blendshape")
            self.wrap_node = deformers.create_proximity_wrap(self.tmpSource, self.tmpTarget,
                                                        wrap_mode=self.wrapMode,
                                                        falloff_scale=self.falloffScale,
                                                        max_drivers=self.maxDrivers,
                                                        smooth_influences=self.smoothInfluences,
                                                        smooth_normals=self.smoothNormals,
                                                        soft_normalization=self.softNormalization,
                                                        span_samples=self.spanSamples)

    def tweak_wrap(self, property, value):
        if self.wrap_node and cmds.objExists(self.wrap_node):
            cmds.setAttr("%s.%s" %(self.wrap_node, property), value)
        return

    def tweak_offset(self, values):
        if self.offsetCluster and cmds.objExists(self.offsetCluster[1]):
            cmds.setAttr("%s.t" % self.offsetCluster[1], *values)
        return

    def preview_mode_on(self):
        # cmds.currentTime(300)

        self.preview_mode_off() # reset first
        self._prepare_meshes()

        self.qc_blendshapes(self.blendshapeNode)

        self.offsetCluster = cmds.cluster(self.tmpTarget, name="trTMP_blndtrans__offsetCluster")
        cmds.parent(self.annotationsGrp, self.offsetCluster[1])
        cmds.setAttr("%s.t" % self.offsetCluster[1], *self.offsetValue)
        cmds.parent(self.offsetCluster[1], self.transferShapesGrp)
        cmds.hide(functions.get_shapes(self.offsetCluster[1])) # hide only shape

    def preview_mode_off(self):
        functions.delete_object("trTMP_blndtrans_*")
        functions.delete_object(self.transferShapesGrp)

    def qc_blendshapes(self, blendshape_node, separation=5):
        blend_attributes = deformers.get_influencers(blendshape_node)
        if "negateSource" in blend_attributes:
            blend_attributes.remove("negateSource")
            same_topo = True
        else:
            same_topo = False

        self.annotationsGrp = cmds.group(name="trTMP_blndtrans_Annotations", em=True)
        cmds.parent(self.annotationsGrp, self.transferShapesGrp)

        for nmb, attr in enumerate(blend_attributes):
            start_frame = separation * (nmb + 1)
            end_frame = start_frame + (separation - 1)
            cmds.setKeyframe(blendshape_node, at=attr, t=start_frame - 1, value=0)
            cmds.setKeyframe(blendshape_node, at=attr, t=start_frame, value=1)
            cmds.setKeyframe(blendshape_node, at=attr, t=end_frame, value=1)
            cmds.setKeyframe(blendshape_node, at=attr, t=end_frame + 1, value=0)
            # annotations
            center = cmds.objectCenter(self.tmpTarget, gl=True)
            raw = cmds.xform(self.tmpTarget, q=1, bb=1)
            offset = (0, (raw[4] - center[1])*1.1, 0)
            # offset = om.MVector(0, (raw[4] - center[1])*1.1, 0) + om.MVector(self.offsetValue)


            annotation = interface.annotate(self.tmpTarget, attr, offset=offset,
                               name="trTMP_blndtrans_%s" %attr,
                               visibility_range=[start_frame, end_frame])
            cmds.parent(annotation, self.annotationsGrp)


        if same_topo:
            # if the same topo animate the delta shape at the beginning and end of range
            cmds.setKeyframe(blendshape_node, at="negateSource", t=separation-1, value=0)
            cmds.setKeyframe(blendshape_node, at="negateSource", t=separation, value=-1)
            cmds.setKeyframe(blendshape_node, at="negateSource", t=separation*len(blend_attributes)+separation-1, value=-1)
            cmds.setKeyframe(blendshape_node, at="negateSource", t=separation*len(blend_attributes)+separation, value=0)

        # extend the timeline range to fit the qc
        cmds.playbackOptions(min=1, max=separation*len(blend_attributes)+separation)


    def refresh(self):
        """To fix weird maya bug with blendshape node which is not triggering the next target after the cursor
        for some reason"""
        cmds.setAttr("%s.nodeState" % self.blendshapeNode[0], 1)
        cmds.setAttr("%s.nodeState" % self.blendshapeNode[0], 0)


    def transfer(self):
        self.preview_mode_off()
        self._prepare_meshes()
        blend_attributes = deformers.get_influencers(self.blendshapeNode)
        if "negateSource" in blend_attributes:
            blend_attributes.remove("negateSource")
        for attr in blend_attributes:
            cmds.setAttr("%s.%s" %(self.blendshapeNode[0], attr), 1)
            new_blendshape = cmds.duplicate(self.tmpTarget)[0]
            # cmds.parent(new_blendshape, self.transferShapesGrp)
            # get rid of the intermediates
            functions.delete_intermediates(new_blendshape)
            cmds.rename(new_blendshape, attr)
            cmds.setAttr("%s.%s" %(self.blendshapeNode[0], attr), 0)
        functions.delete_object("trTMP_blndtrans_*")

    @staticmethod
    def is_same_topology(source, target):
        """checks if the source and target shares the same topology"""
        # state = cmds.polyCompare([source, target], fd=True) # 0 means they are matching
        # if state == 0:
        #     return True
        # else:
        #     return False
        source_count = len(api.get_all_vertices(source))
        target_count = len(api.get_all_vertices(target))

        if source_count == target_count:
            return True
        else:
            return False


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

        gen_settings_group = QtWidgets.QGroupBox()
        gen_settings_group.setTitle("General Settings")
        master_vlay.addWidget(gen_settings_group)

        gen_settings_formlayout = QtWidgets.QFormLayout(gen_settings_group)

        offset_preview_mesh_lbl = QtWidgets.QLabel(text="Offset Preview Mesh")
        offset_preview_mesh_hlay = QtWidgets.QHBoxLayout()
        self.offset_x_sp = QtWidgets.QDoubleSpinBox(minimum=-99999, maximum=99999)
        self.offset_y_sp = QtWidgets.QDoubleSpinBox(minimum=-99999, maximum=99999)
        self.offset_z_sp = QtWidgets.QDoubleSpinBox(minimum=-99999, maximum=99999)
        offset_preview_mesh_hlay.addWidget(self.offset_x_sp)
        offset_preview_mesh_hlay.addWidget(self.offset_y_sp)
        offset_preview_mesh_hlay.addWidget(self.offset_z_sp)
        gen_settings_formlayout.addRow(offset_preview_mesh_lbl, offset_preview_mesh_hlay)

        wrap_settings_group = QtWidgets.QGroupBox()
        wrap_settings_group.setTitle("Wrap Settings")
        master_vlay.addWidget(wrap_settings_group)

        wrap_settings_formlayout = QtWidgets.QFormLayout(wrap_settings_group)

        wrap_mode_lbl = QtWidgets.QLabel(text="Wrap Mode")
        self.wrap_mode_combo = QtWidgets.QComboBox()
        self.wrap_mode_combo.addItems(["offset", "surface", "snap", "rigid", "cluster"])
        wrap_settings_formlayout.addRow(wrap_mode_lbl, self.wrap_mode_combo)

        falloff_scale_lbl = QtWidgets.QLabel(text="Falloff Scale")
        self.falloff_scale_sp = QtWidgets.QDoubleSpinBox()
        self.falloff_scale_sp.setMinimum(0.01)
        wrap_settings_formlayout.addRow(falloff_scale_lbl, self.falloff_scale_sp)

        smooth_influences_lbl = QtWidgets.QLabel(text="Smooth Influences")
        self.smooth_influences_sp = QtWidgets.QSpinBox()
        self.smooth_influences_sp.setMinimum(0)
        wrap_settings_formlayout.addRow(smooth_influences_lbl, self.smooth_influences_sp)

        soft_normalization_lbl = QtWidgets.QLabel(text="Soft Normalization")
        self.soft_normalization_cb = QtWidgets.QCheckBox()
        wrap_settings_formlayout.addRow(soft_normalization_lbl, self.soft_normalization_cb)

        span_samples_lbl = QtWidgets.QLabel(text="Span Samples")
        self.span_samples_sp = QtWidgets.QSpinBox()
        self.span_samples_sp.setMinimum(0)
        wrap_settings_formlayout.addRow(span_samples_lbl, self.span_samples_sp)

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
                if self.transfer.is_same_topology(self.transfer.source_mesh, self.transfer.target_mesh):
                    wrap_settings_group.setEnabled(False)
                else:
                    wrap_settings_group.setEnabled(True)
                self.transfer.preview_mode_on()
            else:
                wrap_settings_group.setEnabled(True)
                self.transfer.preview_mode_off()

        def on_transfer():
            self.update_model()
            preview_pb.blockSignals(True)
            self.transfer.transfer()
            preview_pb.setChecked(False)
            preview_pb.blockSignals(False)



        # SIGNALS
        self.source_mesh_leBox.buttonGet.clicked.connect(lambda x=0: self.get_selected(self.source_mesh_leBox.viewWidget))
        self.source_blpack_leBox.buttonGet.clicked.connect(lambda x=0: self.get_selected(self.source_blpack_leBox.viewWidget, group=True))
        self.target_mesh_leBox.buttonGet.clicked.connect(lambda x=0: self.get_selected(self.target_mesh_leBox.viewWidget))

        self.offset_x_sp.valueChanged.connect(self.on_tweak_offset)
        self.offset_y_sp.valueChanged.connect(self.on_tweak_offset)
        self.offset_z_sp.valueChanged.connect(self.on_tweak_offset)

        self.wrap_mode_combo.currentIndexChanged.connect(lambda v, p="wrapMode": self.transfer.tweak_wrap(property=p, value=v))
        self.falloff_scale_sp.valueChanged.connect(lambda v, p="falloffScale": self.transfer.tweak_wrap(property=p, value=v))
        self.smooth_influences_sp.valueChanged.connect(lambda v, p="smoothInfluences": self.transfer.tweak_wrap(property=p, value=v))
        self.soft_normalization_cb.stateChanged.connect(lambda v, p="softNormalization": self.transfer.tweak_wrap(property=p, value=v))
        self.span_samples_sp.valueChanged.connect(lambda v, p="spanSamples": self.transfer.tweak_wrap(property=p, value=v))



        preview_pb.toggled.connect(on_toggle_preview)
        refresh_pb.clicked.connect(self.transfer.refresh)
        transfer_pb.clicked.connect(on_transfer)

    def on_tweak_offset(self):
        offset_value = (self.offset_x_sp.value(), self.offset_y_sp.value(), self.offset_z_sp.value())
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
        # wrap
        self.wrap_mode_combo.setCurrentText(self.transfer.wrapMode)
        self.falloff_scale_sp.setValue(self.transfer.falloffScale)
        self.smooth_influences_sp.setValue(self.transfer.smoothInfluences)
        self.soft_normalization_cb.setChecked(self.transfer.softNormalization)
        self.span_samples_sp.setValue(self.transfer.spanSamples)

    def update_model(self):
        # mesh
        self.transfer.source_mesh = self.source_mesh_leBox.viewWidget.text()
        self.transfer.source_blendshape_grp = self.source_blpack_leBox.viewWidget.text()
        self.transfer.target_mesh = self.target_mesh_leBox.viewWidget.text()
        # general
        self.transfer.offsetValue[0] = self.offset_x_sp.value()
        self.transfer.offsetValue[1] = self.offset_y_sp.value()
        self.transfer.offsetValue[2] = self.offset_z_sp.value()
        # wrap
        self.transfer.wrapMode = self.wrap_mode_combo.currentText()
        self.transfer.falloffScale = self.falloff_scale_sp.value()
        self.transfer.smoothInfluences = self.smooth_influences_sp.value()
        self.transfer.softNormalization = self.soft_normalization_cb.isChecked()
        self.transfer.spanSamples = self.span_samples_sp.value()

    def get_selected(self, line_edit, group=False):
        meshes_only=False if group else True
        selected, msg = selection.validate(minimum=1, maximum=1, meshes_only=meshes_only, groups_only=group, transforms=True, full_path=False)
        if not selected:
            self.feed.pop_info(title="Selection Error", text=msg)
            return
        else:
            line_edit.setText(selected[0])






