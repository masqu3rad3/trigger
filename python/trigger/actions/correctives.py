"""Action Module for Pose space deformations"""

from maya import cmds

from trigger.library import functions
from trigger.library import connection
from trigger.library import attribute
from trigger.library import selection
from trigger.library import deformers
from trigger.library import naming

from trigger.core import io
from trigger.core import filelog
from trigger.core.decorators import tracktime

from trigger.ui.Qt import QtWidgets
from trigger.ui import custom_widgets
from trigger.ui import feedback

from PySide2 import QtWidgets

log = filelog.Filelog(logname=__name__, filename="trigger_log")

"""
example action data:
ACTION_DATA = {
                "definitions": [
                        {
                            "mode": 0, # 0 means Vector mode
                            "driver_transform": "some_joint"
                            "controller": "upper_arm_cont"
                            "target_rotation": "some_rotation"
                            "up_object": "some parent object of driver"
                            "driver_axis": "This is not used with angle mode"
                            "corrected_shape": "some_shape"
                            "skinned_mesh": "awesome skinned mesh"
                        },
                        {
                            "mode": 1, # 1 means Single Acis mode
                            "driver_transform": "some_joint"
                            "controller": "upper_arm_cont"
                            "target_rotation": "some_rotation"
                            "up_object": "This is not used with single axis mode"
                            "driver_axis": "X Y or Z axis"
                            "corrected_shape": "some_shape"
                            "skinned_mesh": "awesome skinned mesh"
                        }
                    ]
                }
"""

ACTION_DATA = {
    "definitions": [],
}

# Name of the class MUST be the capitalized version of file name. eg. morph.py => Morph, split_shapes.py => Split_shapes
class Correctives(object):
    def __init__(self, *args, **kwargs):
        super(Correctives, self).__init__()

        # user defined variables
        self.correctiveDefinitions = None

        # class variables

    def feed(self, action_data, *args, **kwargs):
        """Mandatory Method - Feeds the instance with the action data stored in actions session"""
        self.correctiveDefinitions = action_data.get("definitions")

    def action(self):
        """Mandatory Method - Execute Action"""
        # everything in this method will be executed automatically.
        # This method does not accept any arguments. all the user variable must be defined to the instance before
        for definition in self.correctiveDefinitions:
            mode = definition.get("mode")
            driver_transform = definition.get("driver_transform")
            controller = definition.get("controller")
            target_rotation = definition.get("target_rotation")
            up_object = definition.get("up_object")
            driver_axis = definition.get("driver_axis")
            corrected_shape = definition.get("corrected_shape")
            skinned_mesh = definition.get("skinned_mesh")
            if not driver_transform:
                log.error("Driver Transform not defined")
                raise
            if mode == 0: # vector mode
                rig_grp = functions.validateGroup("rig_grp")
                psd_grp = functions.validateGroup("psd_grp")
                if functions.getParent(psd_grp) != rig_grp:
                    cmds.parent(psd_grp, rig_grp)
                angle_extractor_root = self.vector_psd(driver_transform, controller, target_rotation, up_object, prefix=driver_transform)
                cmds.parent(angle_extractor_root, psd_grp)
                psd_attr = "%s.angleBetween" % angle_extractor_root

            elif mode == 1: # single axis mode
                psd_attr = "{0}.rotate{1}".format(driver_transform, driver_axis.upper())
            else:
                log.error("This mode (index=>%i) is not yet implemented" %mode)
                continue

            if corrected_shape:
                if not skinned_mesh:
                    log.error("If corrected shape defined, skinned mesh must defined as well. skipping connecting correctives...")
                    continue
                else:
                    self.load_extract_deltas()
                    self.connect_correctives(corrected_shape, skinned_mesh, controller, target_rotation, psd_attr)

    def save_action(self, file_path=None, *args, **kwargs):
        """Mandatory Method - Save Action"""
        # This method will be called automatically and accepts no arguments.
        # If the action has an option to save files, this method will be used by the UI.
        # Else, this method can stay empty
        pass

    def ui(self, ctrl, layout, handler, *args, **kwargs):
        """
        Mandatory Method - UI setting definitions

        Args:
            ctrl: (model_ctrl) ctrl object instance of /ui/model_ctrl. Updates UI and Model
            layout: (QLayout) The layout object from the main ui. All setting widgets should be added to this layout
            handler: (actions_session) An instance of the actions_session. TRY NOT TO USE HANDLER UNLESS ABSOLUTELY NECESSARY
            *args:
            **kwargs:

        Returns: None

        """

        definitions_lbl = QtWidgets.QLabel(text="Definitions")
        definitions_lay = QtWidgets.QVBoxLayout()
        layout.addRow(definitions_lbl, definitions_lay)

        add_new_definition_btn = QtWidgets.QPushButton(text= "Add New Definition")
        definitions_lay.addWidget(add_new_definition_btn)

        self.id = 0
        self.definition_widgets = []

        def add_new_definition(mode_val=0,
                               driver_transform_val="",
                               controller_val="",
                               target_rotation_val=[0,0,0],
                               up_object_val="",
                               driver_axis_val="",
                               corrected_shape_val="",
                               skinned_mesh_val=""
                               ):
            self.id += 1

            def_formlayout = QtWidgets.QFormLayout()

            def_mode_lbl = QtWidgets.QLabel(text="Mode")
            def_mode_combo = QtWidgets.QComboBox()
            def_mode_combo.addItems(["Vector", "Single Axis"])
            def_formlayout.addRow(def_mode_lbl, def_mode_combo)

            def_driver_transform_lbl = QtWidgets.QLabel(text="Driver Transform")
            def_driver_transform_leBox = custom_widgets.LineEditBoxLayout(buttonsPosition="right")
            def_driver_transform_leBox.buttonGet.setText("<")
            def_driver_transform_leBox.buttonGet.setMaximumWidth(30)
            def_formlayout.addRow(def_driver_transform_lbl, def_driver_transform_leBox)

            def_controller_lbl = QtWidgets.QLabel(text="Controller")
            def_controller_leBox = custom_widgets.LineEditBoxLayout(buttonsPosition="right")
            def_controller_leBox.buttonGet.setText("<")
            def_controller_leBox.buttonGet.setMaximumWidth(30)
            def_formlayout.addRow(def_controller_lbl, def_controller_leBox)

            def_target_rotation_lbl = QtWidgets.QLabel(text="Target Rotation")
            rotations_hlay = QtWidgets.QHBoxLayout()
            x_rot_sp = QtWidgets.QDoubleSpinBox(minimum=-999999, maximum=999999)
            y_rot_sp = QtWidgets.QDoubleSpinBox(minimum=-999999, maximum=999999)
            z_rot_sp = QtWidgets.QDoubleSpinBox(minimum=-999999, maximum=999999)
            rotations_hlay.addWidget(x_rot_sp)
            rotations_hlay.addWidget(y_rot_sp)
            rotations_hlay.addWidget(z_rot_sp)
            get_rotation_pb = QtWidgets.QPushButton(text="<")
            get_rotation_pb.setMaximumWidth(30)
            rotations_hlay.addWidget(get_rotation_pb)
            def_formlayout.addRow(def_target_rotation_lbl, rotations_hlay)

            def_up_object_lbl = QtWidgets.QLabel(text="Up Object")
            def_up_object_leBox = custom_widgets.LineEditBoxLayout(buttonsPosition="right")
            def_up_object_leBox.buttonGet.setText("<")
            def_up_object_leBox.buttonGet.setMaximumWidth(30)
            def_formlayout.addRow(def_up_object_lbl, def_up_object_leBox)

            def_driver_axis_lbl = QtWidgets.QLabel("Driver Axis")
            def_driver_axis_combo = QtWidgets.QComboBox()
            def_driver_axis_combo.addItems(["X", "Y", "Z"])
            def_formlayout.addRow(def_driver_axis_lbl, def_driver_axis_combo)

            def_corrected_shape_lbl = QtWidgets.QLabel(text="Corrected Shape")
            def_corrected_shape_leBox = custom_widgets.LineEditBoxLayout(buttonsPosition="right")
            def_corrected_shape_leBox.buttonGet.setText("<")
            def_corrected_shape_leBox.buttonGet.setMaximumWidth(30)
            def_formlayout.addRow(def_corrected_shape_lbl, def_corrected_shape_leBox)

            def_skinned_mesh_lbl = QtWidgets.QLabel(text="Skinned Mesh")
            def_skinned_mesh_leBox = custom_widgets.LineEditBoxLayout(buttonsPosition="right")
            def_skinned_mesh_leBox.buttonGet.setText("<")
            def_skinned_mesh_leBox.buttonGet.setMaximumWidth(30)
            def_formlayout.addRow(def_skinned_mesh_lbl, def_skinned_mesh_leBox)

            def_remove_lbl = QtWidgets.QLabel(text="")
            def_remove_pb = QtWidgets.QPushButton(text="Remove")
            def_formlayout.addRow(def_remove_lbl, def_remove_pb)

            id_lbl = QtWidgets.QLabel("")
            id_separator_lbl = QtWidgets.QLabel("-"*100)
            def_formlayout.addRow(id_lbl, id_separator_lbl)

            definitions_lay.insertLayout(definitions_lay.count()-1, def_formlayout)

            tmp_dict = {
                "id": self.id,
                "def_mode_combo": def_mode_combo,
                "def_driver_transform_leBox": def_driver_transform_leBox,
                "def_controller_leBox": def_controller_leBox,
                "x_rot_sp": x_rot_sp,
                "y_rot_sp": y_rot_sp,
                "z_rot_sp": z_rot_sp,
                "def_up_object_leBox": def_up_object_leBox,
                "def_driver_axis_combo": def_driver_axis_combo,
                "def_corrected_shape_leBox": def_corrected_shape_leBox,
                "def_skinned_mesh_leBox": def_skinned_mesh_leBox,
                "def_driver_axis_lbl": def_driver_axis_lbl,
                "def_up_object_lbl": def_up_object_lbl
            }
            self.definition_widgets.append(tmp_dict)

            # initial values
            def_mode_combo.setCurrentIndex(mode_val)
            def_driver_transform_leBox.viewWidget.setText(driver_transform_val)
            def_controller_leBox.viewWidget.setText(controller_val)
            x_rot_sp.setValue(target_rotation_val[0])
            y_rot_sp.setValue(target_rotation_val[1])
            z_rot_sp.setValue(target_rotation_val[2])
            def_up_object_leBox.viewWidget.setText(up_object_val)
            def_driver_axis_combo.setCurrentText(driver_axis_val)
            def_corrected_shape_leBox.viewWidget.setText(corrected_shape_val)
            def_skinned_mesh_leBox.viewWidget.setText(skinned_mesh_val)

            update_widget_visibility(def_mode_combo.currentIndex(), tmp_dict)

            # signals
            def_mode_combo.currentIndexChanged.connect(lambda val, w_dict=tmp_dict: update_widget_visibility(val, w_dict))
            def_mode_combo.currentIndexChanged.connect(update_model)
            def_driver_transform_leBox.viewWidget.textChanged.connect(update_model)
            def_driver_transform_leBox.buttonGet.clicked.connect(lambda _=0, widget=def_driver_transform_leBox.viewWidget: get_selected(widget, mesh_only=False))
            def_controller_leBox.viewWidget.textChanged.connect(update_model)
            def_controller_leBox.buttonGet.clicked.connect(lambda _=0, widget=def_controller_leBox.viewWidget: get_selected(widget, mesh_only=False))
            x_rot_sp.valueChanged.connect(update_model)
            y_rot_sp.valueChanged.connect(update_model)
            z_rot_sp.valueChanged.connect(update_model)
            get_rotation_pb.clicked.connect(lambda _=0, x=x_rot_sp, y=y_rot_sp, z=z_rot_sp: get_rotation(x, y, z))
            def_up_object_leBox.viewWidget.textChanged.connect(update_model)
            def_up_object_leBox.buttonGet.clicked.connect(lambda _=0, widget=def_up_object_leBox.viewWidget: get_selected(widget, mesh_only=False))
            def_driver_axis_combo.currentIndexChanged.connect(update_model)
            def_corrected_shape_leBox.viewWidget.textChanged.connect(update_model)
            def_corrected_shape_leBox.buttonGet.clicked.connect(lambda _=0, widget=def_corrected_shape_leBox.viewWidget: get_selected(widget))
            def_skinned_mesh_leBox.viewWidget.textChanged.connect(update_model)
            def_skinned_mesh_leBox.buttonGet.clicked.connect(lambda _=0, widget=def_skinned_mesh_leBox.viewWidget: get_selected(widget))
            def_remove_pb.clicked.connect(lambda _=0, lay=def_formlayout, id=self.id: delete_definition(lay, id))
            def_remove_pb.clicked.connect(update_model)

        def get_rotation(x_widget, y_widget, z_widget):
            sel, msg = selection.validate(min=1, max=1, meshesOnly=False, transforms=True)
            if sel:
                rotations = cmds.getAttr("%s.r" %sel[0])[0]
                x_widget.setValue(rotations[0])
                y_widget.setValue(rotations[1])
                z_widget.setValue(rotations[2])
                update_model()
            else:
                feedback.Feedback().pop_info(title="Selection Error", text=msg, critical=True)

        def get_selected(update_widget, mesh_only=True):
            sel, msg = selection.validate(min=1, max=1, meshesOnly=mesh_only, transforms=True)
            if sel:
                update_widget.setText(sel[0])
                update_model()
            else:
                feedback.Feedback().pop_info(title="Selection Error", text=msg, critical=True)


        def update_widget_visibility(val, w_dict):
            if val == 0: # vector mode
                w_dict["def_driver_axis_combo"].setVisible(False)
                w_dict["def_up_object_leBox"].viewWidget.setVisible(True)
                w_dict["def_up_object_leBox"].buttonGet.setVisible(True)
                w_dict["def_up_object_lbl"].setVisible(True)
                w_dict["def_driver_axis_lbl"].setVisible(False)

            else:
                w_dict["def_driver_axis_combo"].setVisible(True)
                w_dict["def_up_object_leBox"].viewWidget.setVisible(False)
                w_dict["def_up_object_leBox"].buttonGet.setVisible(False)
                w_dict["def_up_object_lbl"].setVisible(False)
                w_dict["def_driver_axis_lbl"].setVisible(True)

        # custom model/ui updates

        def update_model():
            # collect definition data
            print("devbug")
            definitions = []
            for widget_dict in self.definition_widgets:
                tmp_dict = {}
                tmp_dict["mode"] = widget_dict["def_mode_combo"].currentIndex()
                tmp_dict["driver_transform"] = widget_dict["def_driver_transform_leBox"].viewWidget.text()
                tmp_dict["controller"] = widget_dict["def_controller_leBox"].viewWidget.text()
                tmp_dict["target_rotation"] = [widget_dict["x_rot_sp"].value(),
                                               widget_dict["y_rot_sp"].value(),
                                               widget_dict["z_rot_sp"].value()]
                tmp_dict["up_object"] = widget_dict["def_up_object_leBox"].viewWidget.text()
                tmp_dict["driver_axis"] = widget_dict["def_driver_axis_combo"].currentText()
                tmp_dict["corrected_shape"] = widget_dict["def_corrected_shape_leBox"].viewWidget.text()
                tmp_dict["skinned_mesh"] = widget_dict["def_skinned_mesh_leBox"].viewWidget.text()

                definitions.append(tmp_dict)
            # feed the model with the definitions
            ctrl.model.edit_action(ctrl.action_name, "definitions", definitions)

        def update_ui():
            data = ctrl.model.query_action(ctrl.action_name, "definitions")
            for definition in data:
                add_new_definition(mode_val=definition["mode"],
                                   driver_transform_val=definition["driver_transform"],
                                   controller_val=definition["controller"],
                                   target_rotation_val=definition["target_rotation"],
                                   up_object_val=definition["up_object"],
                                   driver_axis_val=definition["driver_axis"],
                                   corrected_shape_val=definition["corrected_shape"],
                                   skinned_mesh_val=definition["skinned_mesh"],
                                   )

        def delete_definition(layout, id):
            for item in self.definition_widgets:
                if item["id"] == id:
                    self.definition_widgets.remove(item)
                    break
            del_layout(layout)

        def del_layout(layout):
            if layout is not None:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.setParent(None)
                    else:
                        del_layout(item.layout())

        update_ui()

        add_new_definition_btn.clicked.connect(add_new_definition)

    @staticmethod
    def vector_psd(driver_transform, controller, target_rotation, up_object, return_angle_attr=False, prefix=""):
        root_loc = cmds.spaceLocator(name=naming.uniqueName("%s_angleExt_root" %prefix))[0]
        point_a = cmds.spaceLocator(name=naming.uniqueName("%s_angleExt_pointA" %prefix))[0]
        cmds.setAttr("%s.tx" % point_a, 5)
        point_b = cmds.spaceLocator(name=naming.uniqueName("%s_angleExt_pointB" %prefix))[0]
        point_b_offset = functions.createUpGrp(point_b, "offset")
        cmds.setAttr("%s.tx" % point_b, 5)
        cmds.parent(point_a, root_loc)
        cmds.parent(point_b_offset, root_loc)
        functions.alignTo(root_loc, driver_transform, position=True, rotation=True)
        cmds.pointConstraint(driver_transform, root_loc, mo=False)
        cmds.parentConstraint(driver_transform, point_a, mo=True)
        connection.matrixConstraint(up_object, point_b_offset, st="xyz", mo=True)

        # store controllers initial rotation
        initial_rotation = cmds.getAttr("%s.r" % controller)[0]
        # temporarily parent b to the controller and move it to its target position
        cmds.parent(point_b, controller)
        cmds.setAttr("%s.r" % controller, *target_rotation)
        cmds.parent(point_b, point_b_offset)
        cmds.setAttr("%s.r" % controller, *initial_rotation)

        # # create a temporary group hierarchy to match the locator to the target rotation
        # tmp_grp = cmds.group(em=True, name="vector_psd_TEMP_GRP")
        # functions.alignTo(tmp_grp, driver_transform, position=True, rotation=True)
        # trans_parent = functions.getParent(driver_transform)
        # if trans_parent:
        #     cmds.parent(tmp_grp, trans_parent)
        #
        # # temporarily parent point_b to the transform to move it to the goal rotation
        # cmds.parent(point_b, tmp_grp)
        # cmds.setAttr("%s.r" % tmp_grp, *target_rotation)
        # cmds.parent(point_b, point_b_offset)
        # cmds.delete(tmp_grp)

        angle_between = cmds.createNode("angleBetween", name=naming.uniqueName("%s_angleExt_angleBetween" % prefix))
        cmds.connectAttr("%s.t" % point_a, "%s.vector1" % angle_between)
        cmds.connectAttr("%s.t" % point_b, "%s.vector2" % angle_between)

        angle_attr = attribute.create_attribute(root_loc, attr_name="angleBetween", attr_type="float", keyable=False,
                                                display=True)
        cmds.connectAttr("%s.angle" % angle_between, angle_attr)
        if return_angle_attr:
            return angle_attr
        else:
            return root_loc

    @staticmethod
    def load_extract_deltas():
        is_loaded = cmds.pluginInfo("extractDeltas", q=True, loaded=True)
        if is_loaded:
            return
        else:
            try:
                cmds.loadPlugin("extractDeltas")
                return
            except:
                log.error("extractDeltas plug-in cannot loaded. Check if the plugin exists in your environment")
                raise

    @staticmethod
    def connect_correctives(corrected_mesh, skinned_mesh, controller, target_rotation, psd_attr, discard_delta=True):
        """
        Extracts the deltas of the corrected mesh and connects it to the psd attribute

        Args:
            corrected_mesh: (String) Sculpted mesh
            skinned_mesh: (String) The mesh with the skinCluster
            controller: (String) Controller object which used to get into the sculpted position
            target_rotation: (tuple or list) target rotations of the the controller object
            psd_attr: (String) pose space deformer attribute which will initiall drive the corrected shape
                                        e.g. L_thumb.rotateX, angleExtract_loc.angleBetween
            discard_delta: (bool) if True, the delta shape which will be extracted by extractDeltas plugin will be deleted

        Returns: None

        """

        # get range of statr
        r_start = cmds.getAttr(psd_attr)

        # store controllers initial rotation
        initial_rotation = cmds.getAttr("%s.r" % controller)[0]

        cmds.setAttr("%s.r" % controller, *target_rotation)
        # get range end
        r_end = cmds.getAttr(psd_attr)

        extracted_delta_shape = cmds.extractDeltas(s=skinned_mesh, c=corrected_mesh)

        # get existing blendshapes on skinned mesh and re-use the one front of chain (if any)
        foc_blendshapes = deformers.get_pre_blendshapes(skinned_mesh)
        if foc_blendshapes:
            bs_node = foc_blendshapes[0]
        else:
            bs_node = naming.uniqueName("corrective_blendshapes")

        deformers.connect_bs_targets(
            psd_attr,
            {skinned_mesh: extracted_delta_shape},
            driver_range=[r_start, r_end],
            force_new=False,
            front_of_chain=True,
            bs_node_name=bs_node
        )

        # back to original state
        cmds.setAttr("%s.r" % controller, *initial_rotation)

        if discard_delta:
            functions.deleteObject(extracted_delta_shape)


