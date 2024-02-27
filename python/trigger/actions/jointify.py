"""Converts Blendshape nodes into joint deformations keeping rig controls"""
from maya import cmds
from trigger.utils import jointify

from trigger.core import filelog
from trigger.core.action import ActionCore

from trigger.library import selection, deformers

from trigger.ui.widgets.browser import BrowserButton, FileLineEdit
from trigger.ui import custom_widgets
from trigger.ui import feedback
from trigger.ui.Qt import QtWidgets, QtGui


log = filelog.Filelog(logname=__name__, filename="trigger_log")


ACTION_DATA = {
    "blendshape_node": "",
    "joint_count": 50,
    "auto_shape_duration": True,
    "shape_duration": 0.0,
    "joint_iterations": 30,
    "fbx_source": "",
    "root_nodes": [],
    "parent_to_roots": True,
    "correctives": False,
    "corrective_threshold": 0.01,
}

# Name of the class MUST be the capitalized version of file name. eg. morph.py => Morph, split_shapes.py => Split_shapes


class Jointify(ActionCore):
    action_data = ACTION_DATA

    def __init__(self, **kwargs):
        super(Jointify, self).__init__(kwargs)
        # user defined variables
        self.blendshape_node = None
        self.joint_count = None
        self.auto_shape_duration = None
        self.shape_duration = None
        self.joint_iterations = None
        self.fbx_source = None
        self.root_nodes = None
        self.parent_to_roots = None
        self.correctives = None
        self.corrective_threshold = None

        # class variables

    def feed(self, action_data, *args, **kwargs):
        """Mandatory Method - Feeds the instance with the action data stored in actions session"""
        self.blendshape_node = action_data.get("blendshape_node")
        self.joint_count = action_data.get("joint_count")
        self.auto_shape_duration = action_data.get("auto_shape_duration")
        self.shape_duration = action_data.get("shape_duration")
        self.joint_iterations = action_data.get("joint_iterations")
        self.fbx_source = action_data.get("fbx_source")
        self.root_nodes = action_data.get("root_nodes")
        self.parent_to_roots = action_data.get("parent_to_roots", True)
        self.correctives = action_data.get("correctives")
        self.corrective_threshold = action_data.get("corrective_threshold")

    def action(self):
        """Mandatory Method - Execute Action"""
        # everything in this method will be executed automatically.
        # This method does not accept any arguments. all the user variable must be defined to the instance before
        _shape_duration = 0 if self.auto_shape_duration else self.shape_duration
        j_hand = jointify.Jointify(
            blendshape_node=self.blendshape_node,
            joint_count=self.joint_count,
            shape_duration=_shape_duration,
            joint_iterations=self.joint_iterations,
            fbx_source=self.fbx_source,
            root_nodes=self.root_nodes,
            parent_to_roots=self.parent_to_roots,
            correctives=self.correctives,
            corrective_threshold=self.corrective_threshold,
        )

        j_hand.run()

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

        blendshape_node_lbl = QtWidgets.QLabel(text="Blendshape Node")
        blendshape_node_le_box = custom_widgets.LineEditBoxLayout(
            buttonsPosition="right"
        )
        blendshape_node_le_box.buttonGet.setText("<")
        blendshape_node_le_box.buttonGet.setMaximumWidth(30)
        blendshape_node_le_box.buttonGet.setToolTip("Gets the selected object")
        layout.addRow(blendshape_node_lbl, blendshape_node_le_box)

        joint_count_lbl = QtWidgets.QLabel(text="Joint Count")
        joint_count_sp = QtWidgets.QSpinBox()
        joint_count_sp.setMinimum(1)
        joint_count_sp.setMaximum(999999)
        layout.addRow(joint_count_lbl, joint_count_sp)

        auto_shape_duration_lbl = QtWidgets.QLabel(text="Auto Shape Duration")
        auto_shape_duration_cb = QtWidgets.QCheckBox()
        auto_shape_duration_cb.setToolTip(
            "If checked each shapes duration in the training set will be defined according"
            "to how many in-betweens each has"
        )
        layout.addRow(auto_shape_duration_lbl, auto_shape_duration_cb)

        shape_duration_lbl = QtWidgets.QLabel(text="Shape Duration")
        shape_duration_sp = QtWidgets.QDoubleSpinBox()
        shape_duration_sp.setToolTip(
            "Defines the duration of each shape in training set"
        )
        shape_duration_sp.setMinimum(0)
        shape_duration_sp.setMaximum(999999)
        layout.addRow(shape_duration_lbl, shape_duration_sp)

        joint_iterations_lbl = QtWidgets.QLabel(text="Joint Iterations")
        joint_iterations_sp = QtWidgets.QSpinBox()
        joint_iterations_sp.setToolTip(
            "Higher values mean more accurate training but takes more time"
        )
        joint_iterations_sp.setMinimum(1)
        joint_iterations_sp.setMaximum(999999)
        layout.addRow(joint_iterations_lbl, joint_iterations_sp)

        fbx_source_lbl = QtWidgets.QLabel(text="FBX Source")
        fbx_source_hlay = QtWidgets.QHBoxLayout()
        fbx_source_le = FileLineEdit()
        fbx_source_le.setToolTip(
            "FBX file of the same mesh with custom joints. Joints must be skinclustered to"
            "the mesh but weights doesnt have to be painted."
        )
        fbx_source_le.setPlaceholderText("(Optional)")
        fbx_source_hlay.addWidget(fbx_source_le)
        browse_path_pb = BrowserButton(
            mode="openFile",
            update_widget=fbx_source_le,
            filterExtensions=["FBX (*.fbx)"],
            overwrite_check=False,
        )
        fbx_source_hlay.addWidget(browse_path_pb)
        layout.addRow(fbx_source_lbl, fbx_source_hlay)

        root_nodes_lbl = QtWidgets.QLabel(text="Root Nodes")
        root_nodes_le_box = custom_widgets.LineEditBoxLayout(buttonsPosition="right")
        root_nodes_le_box.viewWidget.setToolTip(
            "Defines the one or multiple parent nodes scattered in the affected area. "
            "For each joint that will be created, closest one will be picked"
        )
        root_nodes_le_box.buttonGet.setText("<")
        root_nodes_le_box.buttonGet.setMaximumWidth(30)
        root_nodes_le_box.buttonGet.setToolTip("Gets the selected objects")
        layout.addRow(root_nodes_lbl, root_nodes_le_box)

        parent_to_roots_lbl = QtWidgets.QLabel(text="Parent To Roots")
        parent_to_roots_cb = QtWidgets.QCheckBox()
        parent_to_roots_cb.setToolTip(
            "If checked the defined roots will be used as parent for jointifed bones."
            "Otherwise, new joints on root locations will be created"
        )
        layout.addRow(parent_to_roots_lbl, parent_to_roots_cb)

        correctives_lbl = QtWidgets.QLabel(text="Extra Correctives")
        correctives_cb = QtWidgets.QCheckBox()
        correctives_cb.setToolTip(
            "If checked, the trained mesh will be compared against the original and an extra"
            "corrective blendshape will be created according to the threshold level"
        )
        layout.addRow(correctives_lbl, correctives_cb)

        corrective_threshold_lbl = QtWidgets.QLabel(text="Corrective Threshold")
        corrective_threshold_sp = QtWidgets.QDoubleSpinBox()
        corrective_threshold_sp.setToolTip(
            "If the standard deviation cannot stay below this threshold a corrective"
            "shape will be created"
        )
        corrective_threshold_sp.setMinimum(0)
        corrective_threshold_sp.setMaximum(999999)
        layout.addRow(corrective_threshold_lbl, corrective_threshold_sp)

        ctrl.connect(blendshape_node_le_box.viewWidget, "blendshape_node", str)
        ctrl.connect(joint_count_sp, "joint_count", int)
        ctrl.connect(auto_shape_duration_cb, "auto_shape_duration", bool)
        ctrl.connect(shape_duration_sp, "shape_duration", float)
        ctrl.connect(joint_iterations_sp, "joint_iterations", int)
        ctrl.connect(fbx_source_le, "fbx_source", str)
        ctrl.connect(root_nodes_le_box.viewWidget, "root_nodes", list)
        ctrl.connect(parent_to_roots_cb, "parent_to_roots", bool)
        ctrl.connect(correctives_cb, "correctives", bool)
        ctrl.connect(corrective_threshold_sp, "corrective_threshold", float)
        ctrl.update_ui()
        shape_duration_sp.setDisabled(auto_shape_duration_cb.isChecked())
        corrective_threshold_sp.setEnabled(correctives_cb.isChecked())

        def get_blendshape_node():
            """pops up a sub menu to select the blendshape node. If nothing is selected, lists only blendshape nodes
            applied to selected object. Otherwise lists all"""
            sel, msg = selection.validate(transforms=True)
            if sel:
                bs_nodes = []
                for x in sel:
                    bs_nodes.extend(deformers.get_deformers(x).get("blendShape", []))
                bs_nodes = list(set(bs_nodes))
            else:
                bs_nodes = cmds.ls(type="blendShape")
            if not bs_nodes:
                return
            zort_menu = QtWidgets.QMenu()
            menu_actions = [QtWidgets.QAction(str(bs)) for bs in bs_nodes]
            zort_menu.addActions(menu_actions)
            for defo, menu_action in zip(bs_nodes, menu_actions):
                menu_action.triggered.connect(
                    lambda ignore=defo, item=defo: blendshape_node_le_box.viewWidget.setText(
                        str(item)
                    )
                )
            zort_menu.exec_((QtGui.QCursor.pos()))

            ctrl.update_model()
            return

        def get_root_nodes():
            sel, msg = selection.validate(minimum=1, meshes_only=False, transforms=True)
            if sel:
                root_nodes_le_box.viewWidget.setText(ctrl.list_to_text(sel))
                ctrl.update_model()
                return
            else:
                feedback.Feedback().pop_info(
                    title="Selection Error", text=msg, critical=True
                )
                return

        # signals

        blendshape_node_le_box.buttonGet.pressed.connect(lambda: get_blendshape_node())
        blendshape_node_le_box.viewWidget.textChanged.connect(
            lambda: ctrl.update_model()
        )
        joint_count_sp.valueChanged.connect(lambda: ctrl.update_model())
        auto_shape_duration_cb.stateChanged.connect(lambda: ctrl.update_model())
        shape_duration_sp.valueChanged.connect(lambda: ctrl.update_model())
        joint_iterations_sp.valueChanged.connect(lambda: ctrl.update_model())
        fbx_source_le.textChanged.connect(lambda: ctrl.update_model())
        browse_path_pb.clicked.connect(lambda: ctrl.update_model())
        root_nodes_le_box.buttonGet.clicked.connect(lambda: get_root_nodes())
        root_nodes_le_box.viewWidget.textChanged.connect(lambda: ctrl.update_model())
        parent_to_roots_cb.stateChanged.connect(lambda: ctrl.update_model())
        correctives_cb.stateChanged.connect(lambda: ctrl.update_model())
        corrective_threshold_sp.valueChanged.connect(lambda: ctrl.update_model())
        auto_shape_duration_cb.stateChanged.connect(
            lambda state: shape_duration_sp.setDisabled(state)
        )
        correctives_cb.stateChanged.connect(
            lambda state: corrective_threshold_sp.setEnabled(state)
        )
