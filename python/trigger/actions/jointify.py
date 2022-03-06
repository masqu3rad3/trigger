"""Converts Blendshape nodes into joint deformations keeping rig controls"""
from trigger.utils import jointify


from trigger.core import io
from trigger.core import filelog
from trigger.core.decorators import tracktime

from trigger.ui.widgets.browser_button import BrowserButton
from trigger.ui import custom_widgets
from trigger.ui import feedback

from PySide2 import QtWidgets  # temp

log = filelog.Filelog(logname=__name__, filename="trigger_log")


ACTION_DATA = {
    "blendshape_node": "",
    "joint_count": 30,
    "auto_shape_duration": True,
    "shape_duration": 0,
    "joint_iterations": 30,
    "fbx_source": "",
    "root_nodes": [],
    "correctives": False,
    "corrective_threshold": 0.01,
}

# Name of the class MUST be the capitalized version of file name. eg. morph.py => Morph, split_shapes.py => Split_shapes


class Jointify(object):
    def __init__(self, *args, **kwargs):
        super(Jointify, self).__init__()

        # user defined variables
        self.blendshape_node = None
        self.joint_count = None
        self.shape_duration = None
        self.joint_iterations = None
        self.fbx_source = None
        self.root_nodes = None
        self.correctives = None
        self.corrective_threshold = None

        # class variables

    def feed(self, action_data, *args, **kwargs):
        """Mandatory Method - Feeds the instance with the action data stored in actions session"""
        self.blendshape_node = action_data.get("blendshape_node")
        self.joint_count = action_data.get("joint_count")
        self.shape_duration = action_data.get("shape_duration")
        self.joint_iterations = action_data.get("joint_iterations")
        self.fbx_source = action_data.get("fbx_source")
        self.root_nodes = action_data.get("root_nodes")
        self.correctives = action_data.get("correctives")
        self.corrective_threshold = action_data.get("corrective_threshold")

    def action(self):
        """Mandatory Method - Execute Action"""
        # everything in this method will be executed automatically.
        # This method does not accept any arguments. all the user variable must be defined to the instance before
        pass

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
        blendshape_node_le_box = custom_widgets.LineEditBoxLayout(buttonsPosition="right")
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
        auto_shape_duration_cb.setToolTip("If checked each shapes duration in the training set will be defined according"
                                       "to how many in-betweens each has")
        layout.addRow(auto_shape_duration_lbl, auto_shape_duration_cb)

        shape_duration_lbl = QtWidgets.QLabel(text="Shape Duration")
        shape_duration_sp = QtWidgets.QDoubleSpinBox()
        shape_duration_sp.setToolTip("Defines the duration of each shape in training set")
        shape_duration_sp.setMinimum(0)
        shape_duration_sp.setMaximum(999999)
        layout.addRow(shape_duration_lbl, shape_duration_sp)
        
        joint_iterations_lbl = QtWidgets.QLabel(text="Joint Iterations")
        joint_iterations_sp = QtWidgets.QSpinBox()
        joint_iterations_sp.setToolTip("Higher values mean more accurate training but takes more time")
        joint_iterations_sp.setMinimum(1)
        joint_iterations_sp.setMaximum(999999)
        layout.addRow(joint_iterations_lbl, joint_iterations_sp)

        fbx_source_lbl = QtWidgets.QLabel(text="FBX Source")
        fbx_source_hlay = QtWidgets.QHBoxLayout()
        fbx_source_le = custom_widgets.FileLineEdit()
        fbx_source_le.setToolTip("FBX file of the same mesh with custom joints. Joints must be skinclustered to"
                                 "the mesh but weights doesnt have to be painted.")
        fbx_source_le.setPlaceholderText("(Optional)")
        fbx_source_hlay.addWidget(fbx_source_le)
        browse_path_pb = BrowserButton(mode="openFile", update_widget=fbx_source_le, 
                                       filterExtensions=["FBX (*.fbx)"], overwrite_check=False)
        fbx_source_hlay.addWidget(browse_path_pb)
        layout.addRow(fbx_source_lbl, fbx_source_hlay)

        root_nodes_lbl = QtWidgets.QLabel(text="Upper Edges")
        root_nodes_le_box = custom_widgets.LineEditBoxLayout(buttonsPosition="right")
        root_nodes_le_box.buttonGet.setText("<")
        root_nodes_le_box.buttonGet.setMaximumWidth(30)
        root_nodes_le_box.buttonGet.setToolTip("Gets the selected objects")
        layout.addRow(root_nodes_lbl, root_nodes_le_box)
        
        correctives_lbl = QtWidgets.QLabel(text="Extra Correctives")
        correctives_cb = QtWidgets.QCheckBox()
        correctives_cb.setToolTip("If checked, the trained mesh will be compared against the original and an extra"
                               "corrective blendshape will be created according to the threshold level")
        layout.addRow(correctives_lbl, correctives_cb)
        
        corrective_threshold_lbl = QtWidgets.QLabel(text="Corrective Threshold")
        corrective_threshold_sp = QtWidgets.QDoubleSpinBox()
        corrective_threshold_sp.setToolTip("If the standard deviation cannot stay below this threshold a corrective"
                                           "shape will be created")
        corrective_threshold_sp.setMinimum(0)
        corrective_threshold_sp.setMaximum(999999)
        layout.addRow(corrective_threshold_lbl, corrective_threshold_sp)
        