"""Action Module for Pose space deformations"""

from maya import cmds

from trigger.core import validate
from trigger.library import functions
from trigger.library import connection
from trigger.library import attribute
from trigger.library import selection
from trigger.library import deformers
from trigger.library import naming

from trigger.core import filelog
from trigger.core.action import ActionCore

from trigger.ui.Qt import QtWidgets
from trigger.ui import custom_widgets
from trigger.ui import feedback

LOG = filelog.Filelog(logname=__name__, filename="trigger_log")

"""
example action data:
ACTION_DATA = {
                "definitions": [
                        {
                            "mode": 0, # 0 means Vector mode
                            "driver_transform": "some_joint"
                            "controller": "upper_arm_cont"
                            "target_matrix": "some_rotation"
                            "up_object": "some parent object of driver"
                            "driver_axis": "This is not used with angle mode"
                            "corrected_shape": "some_shape"
                            "skinned_mesh": "awesome skinned mesh"
                        },
                        {
                            "mode": 1, # 1 means Single Acis mode
                            "driver_transform": "some_joint"
                            "controller": "upper_arm_cont"
                            "target_matrix": "some_rotation"
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


class Correctives(ActionCore):
    action_data = ACTION_DATA

    def __init__(self, **kwargs):
        super(Correctives, self).__init__(kwargs)
        # user defined variables
        self.correctiveDefinitions = None

        # class variables
        self.definition_widgets = None
        self.uid = 0

    def feed(self, action_data):
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
            target_rotation = definition.get("target_matrix")
            up_object = definition.get("up_object")
            driver_axis = definition.get("driver_axis")
            corrected_shape = definition.get("corrected_shape")
            skinned_mesh = definition.get("skinned_mesh")
            if not driver_transform:
                LOG.error("Driver Transform not defined")
                raise
            if mode == 0:  # vector mode
                rig_grp = functions.validate_group("rig_grp")
                psd_grp = functions.validate_group("psd_grp")
                if functions.get_parent(psd_grp) != rig_grp:
                    cmds.parent(psd_grp, rig_grp)
                angle_extractor_root = self.vector_psd(
                    driver_transform,
                    controller,
                    target_rotation,
                    up_object,
                    prefix=driver_transform,
                )
                cmds.parent(angle_extractor_root, psd_grp)
                psd_attr = "%s.angleBetween" % angle_extractor_root

            elif mode == 1:  # single axis mode
                psd_attr = "{0}.rotate{1}".format(driver_transform, driver_axis.upper())
            else:
                LOG.error("This mode (index=>%i) is not yet implemented" % mode)
                continue

            if corrected_shape:
                if not skinned_mesh:
                    LOG.error(
                        "If corrected shape defined, skinned mesh must defined as well. "
                        "skipping connecting correctives..."
                    )
                    continue
                else:
                    # self.load_extract_deltas()
                    validate.plugin("extractDeltas")
                    self.connect_correctives(
                        corrected_shape,
                        skinned_mesh,
                        controller,
                        target_rotation,
                        psd_attr,
                    )

    def save_action(self, file_path=None, *args, **kwargs):
        """Mandatory Method - Save Action"""
        # This method will be called automatically and accepts no arguments.
        # If the action has an option to save files, this method will be used by the UI.
        # Else, this method can stay empty
        pass

    def ui(self, ctrl, layout, handler):
        """
        Mandatory Method - UI setting definitions

        Args:
            ctrl: (model_ctrl) ctrl object instance of /ui/model_ctrl. Updates UI and Model
            layout: (QLayout) The layout object from the main ui. All setting widgets should be added to this layout
            handler: (actions_session) An instance of the actions_session.
            TRY NOT TO USE HANDLER UNLESS ABSOLUTELY NECESSARY

        Returns: None

        """

        definitions_lbl = QtWidgets.QLabel(text="Definitions")
        definitions_lay = QtWidgets.QVBoxLayout()
        layout.addRow(definitions_lbl, definitions_lay)

        add_new_definition_btn = QtWidgets.QPushButton(text="Add New Definition")
        definitions_lay.addWidget(add_new_definition_btn)

        self.uid = 0
        self.definition_widgets = []

        def add_new_definition(
            mode_val=0,
            driver_transform_val="",
            controller_val="",
            target_matrix_val=None,
            up_object_val="",
            driver_axis_val="",
            corrected_shape_val="",
            skinned_mesh_val="",
        ):
            target_matrix_val = target_matrix_val or []
            self.uid += 1

            def_formlayout = QtWidgets.QFormLayout()

            def_mode_lbl = QtWidgets.QLabel(text="Mode")
            def_mode_combo = QtWidgets.QComboBox()
            def_mode_combo.addItems(["Vector", "Single Axis"])
            def_formlayout.addRow(def_mode_lbl, def_mode_combo)

            def_driver_transform_lbl = QtWidgets.QLabel(text="Driver Transform")
            def_driver_transform_lebox = custom_widgets.LineEditBoxLayout(
                buttonsPosition="right"
            )
            def_driver_transform_lebox.buttonGet.setText("<")
            def_driver_transform_lebox.buttonGet.setMaximumWidth(30)
            def_formlayout.addRow(def_driver_transform_lbl, def_driver_transform_lebox)

            def_controller_lbl = QtWidgets.QLabel(text="Controller")
            def_controller_lebox = custom_widgets.LineEditBoxLayout(
                buttonsPosition="right"
            )
            def_controller_lebox.buttonGet.setText("<")
            def_controller_lebox.buttonGet.setMaximumWidth(30)
            def_formlayout.addRow(def_controller_lbl, def_controller_lebox)

            def_target_matrix_lbl = QtWidgets.QLabel(text="Target Transform")
            def_target_matrix_lbl.setToolTip(
                "The ultimate position which will be the corrective 100% activated"
            )
            matrix_hlay = QtWidgets.QHBoxLayout()
            target_matrix_list = QtWidgets.QListWidget()

            matrix_hlay.addWidget(target_matrix_list)

            matrix_vlay = QtWidgets.QVBoxLayout()
            matrix_hlay.addLayout(matrix_vlay)
            capture_matrix_pb = QtWidgets.QPushButton(text="CAPTURE")
            capture_matrix_pb.setToolTip(
                "Adjust the controller to the angle and position where the corrective "
                "will be active and press this button to set the values"
            )
            capture_matrix_pb.setMaximumWidth(200)
            capture_matrix_pb.setFixedHeight(100)
            matrix_vlay.addWidget(capture_matrix_pb)
            edit_matrix_pb = QtWidgets.QPushButton(text="Edit")
            edit_matrix_pb.setToolTip(
                "sets the current controller to the defined target transform"
            )
            edit_matrix_pb.setMaximumWidth(200)
            edit_matrix_pb.setFixedHeight(20)
            matrix_vlay.addWidget(edit_matrix_pb)
            def_formlayout.addRow(def_target_matrix_lbl, matrix_hlay)

            def_up_object_lbl = QtWidgets.QLabel(text="Up Object")
            def_up_object_lebox = custom_widgets.LineEditBoxLayout(
                buttonsPosition="right"
            )
            def_up_object_lebox.buttonGet.setText("<")
            def_up_object_lebox.buttonGet.setMaximumWidth(30)
            def_formlayout.addRow(def_up_object_lbl, def_up_object_lebox)

            def_driver_axis_lbl = QtWidgets.QLabel("Driver Axis")
            def_driver_axis_combo = QtWidgets.QComboBox()
            def_driver_axis_combo.addItems(["X", "Y", "Z"])
            def_formlayout.addRow(def_driver_axis_lbl, def_driver_axis_combo)

            def_corrected_shape_lbl = QtWidgets.QLabel(text="Corrected Shape")
            def_corrected_shape_lebox = custom_widgets.LineEditBoxLayout(
                buttonsPosition="right"
            )
            def_corrected_shape_lebox.buttonGet.setText("<")
            def_corrected_shape_lebox.buttonGet.setMaximumWidth(30)
            def_formlayout.addRow(def_corrected_shape_lbl, def_corrected_shape_lebox)

            def_skinned_mesh_lbl = QtWidgets.QLabel(text="Skinned Mesh")
            def_skinned_mesh_lebox = custom_widgets.LineEditBoxLayout(
                buttonsPosition="right"
            )
            def_skinned_mesh_lebox.buttonGet.setText("<")
            def_skinned_mesh_lebox.buttonGet.setMaximumWidth(30)
            def_formlayout.addRow(def_skinned_mesh_lbl, def_skinned_mesh_lebox)

            def_remove_lbl = QtWidgets.QLabel(text="")
            def_remove_pb = QtWidgets.QPushButton(text="Remove")
            def_formlayout.addRow(def_remove_lbl, def_remove_pb)

            id_lbl = QtWidgets.QLabel("")
            id_separator_lbl = QtWidgets.QLabel("-" * 100)
            def_formlayout.addRow(id_lbl, id_separator_lbl)

            definitions_lay.insertLayout(definitions_lay.count() - 1, def_formlayout)

            tmp_dict = {
                "id": self.uid,
                "def_mode_combo": def_mode_combo,
                "def_driver_transform_lebox": def_driver_transform_lebox,
                "def_controller_lebox": def_controller_lebox,
                "target_matrix_list": target_matrix_list,
                "def_up_object_lebox": def_up_object_lebox,
                "def_driver_axis_combo": def_driver_axis_combo,
                "def_corrected_shape_lebox": def_corrected_shape_lebox,
                "def_skinned_mesh_lebox": def_skinned_mesh_lebox,
                "def_driver_axis_lbl": def_driver_axis_lbl,
                "def_up_object_lbl": def_up_object_lbl,
            }
            self.definition_widgets.append(tmp_dict)

            # initial values
            def_mode_combo.setCurrentIndex(mode_val)
            def_driver_transform_lebox.viewWidget.setText(driver_transform_val)
            def_controller_lebox.viewWidget.setText(controller_val)
            str_target_matrix_val = [str(x) for x in target_matrix_val]
            target_matrix_list.addItems(str_target_matrix_val)
            def_up_object_lebox.viewWidget.setText(up_object_val)
            def_driver_axis_combo.setCurrentText(driver_axis_val)
            def_corrected_shape_lebox.viewWidget.setText(corrected_shape_val)
            def_skinned_mesh_lebox.viewWidget.setText(skinned_mesh_val)

            update_widget_visibility(def_mode_combo.currentIndex(), tmp_dict)

            def capture_matrix():
                cont = cmds.ls(def_controller_lebox.viewWidget.text())
                if cont:
                    target_matrix_list.clear()
                    tm_matrix = cmds.xform(cont[0], matrix=True, query=True)
                    str_tm_matrix = [str(x) for x in tm_matrix]
                    target_matrix_list.addItems(str_tm_matrix)
                    update_model()
                else:
                    feedback.Feedback().pop_info(
                        title="Selection Error",
                        text="Controller not defined or does not exist in the scene",
                        critical=True,
                    )

            def edit_matrix():
                cont = cmds.ls(def_controller_lebox.viewWidget.text())
                if cont:
                    _matrix = [
                        float(target_matrix_list.item(x).text())
                        for x in range(target_matrix_list.count())
                    ]
                    cmds.xform(cont[0], matrix=_matrix)
                else:
                    feedback.Feedback().pop_info(
                        title="Selection Error",
                        text="Controller not defined or does not exist in the scene",
                        critical=True,
                    )

            # signals
            def_mode_combo.currentIndexChanged.connect(
                lambda val, w_dict=tmp_dict: update_widget_visibility(val, w_dict)
            )
            def_mode_combo.currentIndexChanged.connect(update_model)
            def_driver_transform_lebox.viewWidget.textChanged.connect(update_model)
            def_driver_transform_lebox.buttonGet.clicked.connect(
                lambda _=0, widget=def_driver_transform_lebox.viewWidget: get_selected(
                    widget, mesh_only=False
                )
            )
            def_controller_lebox.viewWidget.textChanged.connect(update_model)
            def_controller_lebox.buttonGet.clicked.connect(
                lambda _=0, widget=def_controller_lebox.viewWidget: get_selected(
                    widget, mesh_only=False
                )
            )
            capture_matrix_pb.clicked.connect(capture_matrix)
            edit_matrix_pb.clicked.connect(edit_matrix)
            def_up_object_lebox.viewWidget.textChanged.connect(update_model)
            def_up_object_lebox.buttonGet.clicked.connect(
                lambda _=0, widget=def_up_object_lebox.viewWidget: get_selected(
                    widget, mesh_only=False
                )
            )
            def_driver_axis_combo.currentIndexChanged.connect(update_model)
            def_corrected_shape_lebox.viewWidget.textChanged.connect(update_model)
            def_corrected_shape_lebox.buttonGet.clicked.connect(
                lambda _=0, widget=def_corrected_shape_lebox.viewWidget: get_selected(
                    widget
                )
            )
            def_skinned_mesh_lebox.viewWidget.textChanged.connect(update_model)
            def_skinned_mesh_lebox.buttonGet.clicked.connect(
                lambda _=0, widget=def_skinned_mesh_lebox.viewWidget: get_selected(
                    widget
                )
            )
            def_remove_pb.clicked.connect(
                lambda _=0, lay=def_formlayout, uid=self.uid: delete_definition(
                    lay, uid
                )
            )
            def_remove_pb.clicked.connect(update_model)

            update_model()

        def _get_rotation(x_widget, y_widget, z_widget):
            sel, msg = selection.validate(
                minimum=1, maximum=1, meshes_only=False, transforms=True
            )
            if sel:
                rotations = cmds.getAttr("%s.r" % sel[0])[0]
                x_widget.setValue(rotations[0])
                y_widget.setValue(rotations[1])
                z_widget.setValue(rotations[2])
                update_model()
            else:
                feedback.Feedback().pop_info(
                    title="Selection Error", text=msg, critical=True
                )

        def get_selected(update_widget, mesh_only=True):
            sel, msg = selection.validate(
                minimum=1, maximum=1, meshes_only=mesh_only, transforms=True
            )
            if sel:
                update_widget.setText(sel[0])
                update_model()
            else:
                feedback.Feedback().pop_info(
                    title="Selection Error", text=msg, critical=True
                )

        def update_widget_visibility(val, w_dict):
            if val == 0:  # vector mode
                w_dict["def_driver_axis_combo"].setVisible(False)
                w_dict["def_up_object_lebox"].viewWidget.setVisible(True)
                w_dict["def_up_object_lebox"].buttonGet.setVisible(True)
                w_dict["def_up_object_lbl"].setVisible(True)
                w_dict["def_driver_axis_lbl"].setVisible(False)

            else:
                w_dict["def_driver_axis_combo"].setVisible(True)
                w_dict["def_up_object_lebox"].viewWidget.setVisible(False)
                w_dict["def_up_object_lebox"].buttonGet.setVisible(False)
                w_dict["def_up_object_lbl"].setVisible(False)
                w_dict["def_driver_axis_lbl"].setVisible(True)

        # custom model/ui updates

        def update_model():
            # collect definition data
            definitions = []
            for widget_dict in self.definition_widgets:
                tm_widget = widget_dict["target_matrix_list"]
                tmp_dict = {
                    "mode": widget_dict["def_mode_combo"].currentIndex(),
                    "driver_transform": widget_dict[
                        "def_driver_transform_lebox"
                    ].viewWidget.text(),
                    "controller": widget_dict["def_controller_lebox"].viewWidget.text(),
                    "target_matrix": [
                        float(tm_widget.item(x).text())
                        for x in range(tm_widget.count())
                    ],
                    "up_object": widget_dict["def_up_object_lebox"].viewWidget.text(),
                    "driver_axis": widget_dict["def_driver_axis_combo"].currentText(),
                    "corrected_shape": widget_dict[
                        "def_corrected_shape_lebox"
                    ].viewWidget.text(),
                    "skinned_mesh": widget_dict[
                        "def_skinned_mesh_lebox"
                    ].viewWidget.text(),
                }
                definitions.append(tmp_dict)
            # feed the model with the definitions
            ctrl.model.edit_action(ctrl.action_name, "definitions", definitions)

        def update_ui():
            data = ctrl.model.query_action(ctrl.action_name, "definitions")
            for definition in data:
                add_new_definition(
                    mode_val=definition["mode"],
                    driver_transform_val=definition["driver_transform"],
                    controller_val=definition["controller"],
                    target_matrix_val=definition["target_matrix"],
                    up_object_val=definition["up_object"],
                    driver_axis_val=definition["driver_axis"],
                    corrected_shape_val=definition["corrected_shape"],
                    skinned_mesh_val=definition["skinned_mesh"],
                )

        def delete_definition(layout_widget, item_id):
            for item in self.definition_widgets:
                if item["id"] == item_id:
                    self.definition_widgets.remove(item)
                    break
            del_layout(layout_widget)

        def del_layout(layout_widget):
            if layout_widget is not None:
                while layout_widget.count():
                    item = layout_widget.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.setParent(None)
                    else:
                        del_layout(item.layout())

        update_ui()

        add_new_definition_btn.clicked.connect(add_new_definition)

    @staticmethod
    def vector_psd(
        driver_transform,
        controller,
        target_matrix,
        up_object,
        return_angle_attr=False,
        prefix="",
    ):
        root_loc = cmds.spaceLocator(
            name=naming.unique_name("%s_angleExt_root" % prefix)
        )[0]
        point_a = cmds.spaceLocator(
            name=naming.unique_name("%s_angleExt_pointA" % prefix)
        )[0]
        cmds.setAttr("%s.tx" % point_a, 5)
        point_b = cmds.spaceLocator(
            name=naming.unique_name("%s_angleExt_pointB" % prefix)
        )[0]
        point_b_offset = functions.create_offset_group(point_b, "offset")
        cmds.setAttr("%s.tx" % point_b, 5)
        cmds.parent(point_a, root_loc)
        cmds.parent(point_b_offset, root_loc)
        functions.align_to(root_loc, driver_transform, position=True, rotation=True)
        cmds.pointConstraint(driver_transform, root_loc, maintainOffset=False)
        cmds.parentConstraint(driver_transform, point_a, maintainOffset=True)
        connection.matrixConstraint(
            up_object, point_b_offset, skipTranslate="xyz", maintainOffset=True
        )

        # store controllers initial rotation
        # initial_rotation = cmds.getAttr("%s.r" % controller)[0]
        initial_matrix = cmds.xform(controller, matrix=True, query=True)
        # temporarily parent b to the controller and move it to its target position
        cmds.parent(point_b, controller)
        cmds.xform(controller, matrix=target_matrix)
        cmds.parent(point_b, point_b_offset)
        functions.align_to(point_b, point_a, position=True, rotation=True)

        cmds.xform(controller, matrix=initial_matrix)

        angle_between = cmds.createNode(
            "angleBetween", name=naming.unique_name("%s_angleExt_angleBetween" % prefix)
        )
        cmds.connectAttr("%s.t" % point_a, "%s.vector1" % angle_between)
        cmds.connectAttr("%s.t" % point_b, "%s.vector2" % angle_between)

        angle_attr = attribute.create_attribute(
            root_loc,
            attr_name="angleBetween",
            attr_type="float",
            keyable=False,
            display=True,
        )
        cmds.connectAttr("%s.angle" % angle_between, angle_attr)
        if return_angle_attr:
            return angle_attr
        else:
            return root_loc

    # @staticmethod
    # def load_extract_deltas():
    #     validate.plugin("extractDeltas")
    # is_loaded = cmds.pluginInfo("extractDeltas", query=True, loaded=True)
    # if is_loaded:
    #     return
    # else:
    #     try:
    #         cmds.loadPlugin("extractDeltas")
    #         return
    #     except:
    #         LOG.error("extractDeltas plug-in cannot loaded. Check if the plugin exists in your environment")
    #         raise

    @staticmethod
    def connect_correctives(
        corrected_mesh,
        skinned_mesh,
        controller,
        target_matrix,
        psd_attr,
        discard_delta=True,
    ):
        """
        Extracts the deltas of the corrected mesh and connects it to the psd attribute

        Args:
            corrected_mesh: (String) Sculpted mesh
            skinned_mesh: (String) The mesh with the skinCluster
            controller: (String) Controller object which used to get into the sculpted position
            target_matrix: (tuple or list) target rotations of the the controller object
            psd_attr: (String) pose space deformer attribute which will initiall drive the corrected shape
                                        e.g. L_thumb.rotateX, angleExtract_loc.angleBetween
            discard_delta: (bool) if True, the delta shape which will be extracted by extractDeltas plugin will be deleted

        Returns: None

        """

        # get range of statr
        r_start = cmds.getAttr(psd_attr)

        # store controllers initial rotation
        initial_matrix = cmds.xform(controller, matrix=True, query=True)

        cmds.xform(controller, matrix=target_matrix)

        # get range end
        r_end = cmds.getAttr(psd_attr)

        extracted_delta_shape = cmds.extractDeltas(s=skinned_mesh, c=corrected_mesh)

        # get existing blendshapes on skinned mesh and re-use the one front of chain (if any)
        foc_blendshapes = deformers.get_pre_blendshapes(skinned_mesh)
        if foc_blendshapes:
            bs_node = foc_blendshapes[0]
        else:
            bs_node = naming.unique_name("corrective_blendshapes")

        print("bs_node", bs_node)
        print("psd_attr", psd_attr)
        print("skinned_mesh", skinned_mesh)
        print("extracted_delta_shape", extracted_delta_shape)
        deformers.connect_bs_targets(
            psd_attr,
            {skinned_mesh: extracted_delta_shape},
            driver_range=[r_start, r_end],
            force_new=False,
            front_of_chain=True,
            bs_node_name=bs_node,
        )

        # back to original state
        cmds.xform(controller, matrix=initial_matrix)

        if discard_delta:
            functions.delete_object(extracted_delta_shape)
