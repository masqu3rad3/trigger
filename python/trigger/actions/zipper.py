"""Zipper Action which wraps around lipzip from face utils"""
from maya import cmds

from trigger.core import filelog

from trigger.library import selection
from trigger.utils.face import lip_zipper

from trigger.ui.Qt import QtWidgets
from trigger.ui import custom_widgets
from trigger.ui import feedback

# from PySide2 import QtWidgets  # temp

log = filelog.Filelog(logname=__name__, filename="trigger_log")

ACTION_DATA = {
    "upper_edges": [],
    "lower_edges": [],
    "morph_mesh": "",
    "final_mesh": "",
    "pair_count": 30,
    "controller": "",
}


# Name of the class MUST be the capitalized version of file name. eg. morph.py => Morph, split_shapes.py => Split_shapes


class Zipper(object):
    def __init__(self, *args, **kwargs):
        super(Zipper, self).__init__()

        # user defined variables
        self.upper_edges = None
        self.lower_edges = None
        self.morph_mesh = None
        self.final_mesh = None
        self.pair_count = None
        self.controller = None

        # class variables

    def feed(self, action_data, *args, **kwargs):
        """Mandatory Method - Feeds the instance with the action data stored in actions session"""
        self.upper_edges = action_data.get("upper_edges")
        self.lower_edges = action_data.get("lower_edges")
        self.morph_mesh = action_data.get("morph_mesh")
        self.final_mesh = action_data.get("final_mesh")
        self.pair_count = action_data.get("pair_count")
        self.controller = action_data.get("controller")

    def action(self):
        """Mandatory Method - Execute Action"""
        # everything in this method will be executed automatically.
        # This method does not accept any arguments. all the user variable must be defined to the instance before
        lip_zipper(self.upper_edges, self.lower_edges, self.morph_mesh, self.final_mesh, self.pair_count, self.controller)

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

        upper_edges_lbl = QtWidgets.QLabel(text="Upper Edges")
        upper_edges_le_box = custom_widgets.LineEditBoxLayout(buttonsPosition="right")
        upper_edges_le_box.buttonGet.setText("<")
        upper_edges_le_box.buttonGet.setMaximumWidth(30)
        upper_edges_le_box.buttonGet.setToolTip("Gets the selected edges from a polygon object")
        layout.addRow(upper_edges_lbl, upper_edges_le_box)

        lower_edges_lbl = QtWidgets.QLabel(text="Lower Edges")
        lower_edges_le_box = custom_widgets.LineEditBoxLayout(buttonsPosition="right")
        lower_edges_le_box.buttonGet.setText("<")
        lower_edges_le_box.buttonGet.setMaximumWidth(30)
        lower_edges_le_box.buttonGet.setToolTip("Gets the selected edges from a polygon object")
        layout.addRow(lower_edges_lbl, lower_edges_le_box)

        morph_mesh_lbl = QtWidgets.QLabel(text="Morph Mesh")
        morph_mesh_le_box = custom_widgets.LineEditBoxLayout(buttonsPosition="right")
        morph_mesh_le_box.buttonGet.setText("<")
        morph_mesh_le_box.buttonGet.setMaximumWidth(30)
        morph_mesh_le_box.buttonGet.setToolTip("Gets the selected object as local mesh")
        layout.addRow(morph_mesh_lbl, morph_mesh_le_box)

        final_mesh_lbl = QtWidgets.QLabel(text="Final Mesh")
        final_mesh_le_box = custom_widgets.LineEditBoxLayout(buttonsPosition="right")
        final_mesh_le_box.buttonGet.setText("<")
        final_mesh_le_box.buttonGet.setMaximumWidth(30)
        morph_mesh_le_box.buttonGet.setToolTip("Gets the selected object as final mesh")
        layout.addRow(final_mesh_lbl, final_mesh_le_box)

        pair_count_lbl = QtWidgets.QLabel(text="Pair Count")
        pair_count_sp = QtWidgets.QSpinBox()
        pair_count_sp.setMinimum(2)
        pair_count_sp.setMaximum(999999)
        layout.addRow(pair_count_lbl, pair_count_sp)

        controller_lbl = QtWidgets.QLabel(text="Controller")
        controller_le_box = custom_widgets.LineEditBoxLayout(buttonsPosition="right")
        controller_le_box.buttonGet.setText("<")
        controller_le_box.buttonGet.setMaximumWidth(30)
        controller_le_box.buttonGet.setToolTip("Gets the selected object as controller")
        layout.addRow(controller_lbl, controller_le_box)

        ctrl.connect(upper_edges_le_box.viewWidget, "upper_edges", list)
        ctrl.connect(lower_edges_le_box.viewWidget, "lower_edges", list)
        ctrl.connect(morph_mesh_le_box.viewWidget, "morph_mesh", str)
        ctrl.connect(final_mesh_le_box.viewWidget, "final_mesh", str)
        ctrl.connect(pair_count_sp, "pair_count", int)
        ctrl.connect(controller_le_box.viewWidget, "controller", str)
        ctrl.update_ui()

        def get_selected_edges(widget):
            if selection.get_selection_type() != "edge":
                feedback.Feedback().pop_info(title="Selection Error", text="Edges from the same object must be selected", critical=True)
                return
            all_object_selection = cmds.ls(sl=True, o=True)
            if len(all_object_selection) > 1:
                feedback.Feedback().pop_info(title="Selection Error", text="Edges from the same object must be selected", critical=True)
                return
            sel = cmds.ls(sl=True)
            widget.setText(ctrl.list_to_text(sel))
            ctrl.update_model()
            return

        def get_selected_mesh(widget):
            sel, msg = selection.validate(minimum=1, maximum=1, meshes_only=True, transforms=True)
            if sel:
                widget.setText(sel[0])
                ctrl.update_model()
                return
            else:
                feedback.Feedback().pop_info(title="Selection Error", text=msg, critical=True)
                return

        # SIGNALS

        upper_edges_le_box.buttonGet.pressed.connect(lambda: get_selected_edges(upper_edges_le_box.viewWidget))
        lower_edges_le_box.buttonGet.pressed.connect(lambda: get_selected_edges(lower_edges_le_box.viewWidget))
        morph_mesh_le_box.buttonGet.pressed.connect(lambda: get_selected_mesh(morph_mesh_le_box.viewWidget))
        final_mesh_le_box.buttonGet.pressed.connect(lambda: get_selected_mesh(final_mesh_le_box.viewWidget))
        pair_count_sp.valueChanged.connect(lambda: ctrl.update_model())
        controller_le_box.buttonGet.pressed.connect(lambda: get_selected_mesh(controller_le_box.viewWidget))

        upper_edges_le_box.viewWidget.textChanged.connect(lambda: ctrl.update_model())
        lower_edges_le_box.viewWidget.textChanged.connect(lambda: ctrl.update_model())
        morph_mesh_le_box.viewWidget.textChanged.connect(lambda: ctrl.update_model())
        final_mesh_le_box.viewWidget.textChanged.connect(lambda: ctrl.update_model())
        controller_le_box.viewWidget.textChanged.connect(lambda: ctrl.update_model())
