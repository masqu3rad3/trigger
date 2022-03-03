"""Responsible for creating visualization fillers for controllers"""
from maya import cmds
from trigger.core import io
from trigger.core import filelog
from trigger.core.decorators import tracktime

from trigger.library import selection
from trigger.utils import controller_filler

from trigger.ui.Qt import QtWidgets
from trigger.ui import custom_widgets
from trigger.ui.widgets.color_button import ColorButton
from trigger.ui import feedback

from PySide2 import QtWidgets  # temp

log = filelog.Filelog(logname=__name__, filename="trigger_log")

ACTION_DATA = {
    "controllers": [],
    "scaling": True,
    "normalize_scale": True,
    "coloring": True,
    "color_method": 0,  # 0 - object, 1 - shader, 2 - triswitch
    "color_match": False,
    "color_a": [0.0, 0.0, 1.0],
    "color_b": [1.0, 0.0, 0.0],
    "primary_channel": "",
    "visibility_controller": "",
    "id_tag": "fillers"
}


class Fillers(object):
    def __init__(self, *args, **kwargs):
        super(Fillers, self).__init__()

        # user defined variables
        self.controllers = None
        self.scaling = None
        self.normalize_scale = None
        self.coloring = None
        self.color_method = None
        self.color_match = None
        self.color_a = [0.0, 0.0, 1.0]
        self.color_b = [1.0, 0.0, 0.0]
        self.primary_channel = None
        self.visibility_controller = None
        self.id_tag = None

    def feed(self, action_data, *args, **kwargs):
        """Mandatory Method - Feeds the instance with the action data stored in actions session"""
        self.controllers = action_data.get("controllers")
        self.scaling = action_data.get("scaling")
        self.normalize_scale = action_data.get("normalize_scale")
        self.coloring = action_data.get("coloring")
        self.color_method = action_data.get("color_method")
        self.color_match = action_data.get("color_match")
        self.color_a = action_data.get("color_a")
        self.color_b = action_data.get("color_b")
        self.primary_channel = action_data.get("primary_channel")
        self.visibility_controller = action_data.get("visibility_controller")
        self.id_tag = action_data.get("id_tag")

    def action(self):
        """Mandatory Method - Execute Action"""
        # everything in this method will be executed automatically.
        # This method does not accept any arguments. all the user variable must be defined to the instance before

        methods = {0: "object",
                   1: "shader",
                   2: "triswitch"}
        primary_channel = self.primary_channel or "Auto"
        for controller in self.controllers:
            filler = controller_filler.Filler(controller=controller,
                                              scaling=self.scaling,
                                              normalize_scale=self.normalize_scale,
                                              coloring=self.coloring,
                                              color_method=methods[self.color_method],
                                              color_match=self.color_match,
                                              primary_channel=primary_channel,
                                              visibility_controller=self.visibility_controller
                                              )
            filler.colorA = self.color_a
            filler.colorB = self.color_b

            filler.create()


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

        controllers_lbl = QtWidgets.QLabel(text="Controllers")
        controllers_lbl.setToolTip("Defined controller curves will be 'filled'")
        controllers_listbox = custom_widgets.ListBoxLayout(alignment="start", buttonNew=False, buttonRename=False,
                                                           buttonUp=False, buttonDown=False)
        layout.addRow(controllers_lbl, controllers_listbox)

        scaling_lbl = QtWidgets.QLabel(text="Scaling Fillers")
        scaling_lbl.setToolTip("If checked, the fillers will have scaling animation driven with controllers")
        scaling_cb = QtWidgets.QCheckBox(checked=True)
        layout.addRow(scaling_lbl, scaling_cb)

        normalize_scale_lbl = QtWidgets.QLabel(text="Normalize Scales")
        normalize_scale_lbl.setToolTip("If checked, there wont be any negative scaling and '0' will be also 0 scale "
                                       "even it is between the start and end range")
        normalize_scale_cb = QtWidgets.QCheckBox()
        layout.addRow(normalize_scale_lbl, normalize_scale_cb)

        coloring_lbl = QtWidgets.QLabel(text="Colored Fillers")
        coloring_lbl.setToolTip("Whether fillers will have colors or not")
        coloring_cb = QtWidgets.QCheckBox(checked=True)
        layout.addRow(coloring_lbl, coloring_cb)

        color_method_lbl = QtWidgets.QLabel(text="Coloring Method")
        color_method_lbl.setToolTip("Defines the coloring method")
        color_method_combo = QtWidgets.QComboBox()
        color_method_combo.addItems(["Object", "Shader", "Switch"])
        color_method_combo.setToolTip("Object => Simple object coloring without shaders\n"
                                      "Shader => One shader per controller\n"
                                      "Switch = Single shader for all controllers with tripleShaderSwitches")
        layout.addRow(color_method_lbl, color_method_combo)

        colors_lbl = QtWidgets.QLabel(text="Colors")
        colors_lay = QtWidgets.QHBoxLayout()
        color_a_pb = ColorButton(text="Color A")
        color_b_pb = ColorButton(text="Color B")
        match_colors_cb = QtWidgets.QCheckBox(text="Match to Controller")
        match_colors_cb.setToolTip("Static colored filler matching to its controller")
        colors_lay.addWidget(color_a_pb)
        colors_lay.addWidget(color_b_pb)
        colors_lay.addWidget(match_colors_cb)
        layout.addRow(colors_lbl, colors_lay)

        primary_channel_lbl = QtWidgets.QLabel(text="Primary Channel")
        primary_channel_le = QtWidgets.QLineEdit()
        primary_channel_le.setToolTip("The channel which will drive filler animations. Leave empty for 'auto'")
        primary_channel_le.setPlaceholderText("Leave Empty for Auto")
        layout.addRow(primary_channel_lbl, primary_channel_le)

        visibility_controller_lbl = QtWidgets.QLabel(text="Visibility Controller")
        visibility_controller_lbl.setToolTip("Attribute to control visibilities of fillers")
        visibility_controller_le = QtWidgets.QLineEdit()
        visibility_controller_le.setPlaceholderText("i.e. pref_cont.Control_Visibility")
        layout.addRow(visibility_controller_lbl, visibility_controller_le)

        id_tag_lbl = QtWidgets.QLabel(text="ID tag")
        id_tag_lbl.setToolTip("Common nodes (Groups, Shaders, etc) will share the same nodes with the same id tags.")
        id_tag_le = QtWidgets.QLineEdit(text="fillers")
        layout.addRow(id_tag_lbl, id_tag_le)

        ctrl.connect(controllers_listbox.viewWidget, "controllers", list)
        ctrl.connect(scaling_cb, "scaling", bool)
        ctrl.connect(normalize_scale_cb, "normalize_scale", bool)
        ctrl.connect(coloring_cb, "coloring", bool)
        ctrl.connect(color_method_combo, "color_method", int)
        ctrl.connect(match_colors_cb, "color_match", bool)
        ctrl.connect(primary_channel_le, "primary_channel", str)
        ctrl.connect(visibility_controller_le, "visibility_controller", str)
        ctrl.connect(id_tag_le, "id_tag", str)

        ctrl.connect(color_a_pb, "color_a", list)
        ctrl.connect(color_b_pb, "color_b", list)
        ctrl.update_ui()

        def get_controllers():
            sel, msg = selection.validate(min=1, max=None, meshesOnly=False, transforms=False)
            if sel:
                # remove the items that is already in there
                existing_list = controllers_listbox.listItemNames()
                refined_sel = [x for x in sel if x not in existing_list]
                controllers_listbox.viewWidget.addItems(refined_sel)
                ctrl.update_model()
            else:
                feedback.Feedback().pop_info(title="Selection Error", text=msg, critical=True)


        # SIGNALS

        # model updates
        controllers_listbox.buttonGet.clicked.connect(get_controllers)
        controllers_listbox.buttonRemove.clicked.connect(lambda x: ctrl.update_model())
        controllers_listbox.buttonClear.clicked.connect(lambda x: ctrl.update_model())

        scaling_cb.stateChanged.connect(lambda x: ctrl.update_model())
        normalize_scale_cb.stateChanged.connect(lambda x: ctrl.update_model())
        coloring_cb.stateChanged.connect(lambda x: ctrl.update_model())
        color_method_combo.currentIndexChanged.connect(lambda x: ctrl.update_model())

        color_a_pb.clicked.connect(lambda x: ctrl.update_model())
        color_b_pb.clicked.connect(lambda x: ctrl.update_model())

        match_colors_cb.stateChanged.connect(lambda x: ctrl.update_model())
        primary_channel_le.textChanged.connect(lambda x: ctrl.update_model())
        visibility_controller_le.textChanged.connect(lambda x: ctrl.update_model())

        # enabling / disabling
        scaling_cb.stateChanged.connect(normalize_scale_lbl.setEnabled)
        scaling_cb.stateChanged.connect(normalize_scale_cb.setEnabled)
        coloring_cb.stateChanged.connect(color_method_lbl.setEnabled)
        coloring_cb.stateChanged.connect(color_method_combo.setEnabled)
        coloring_cb.stateChanged.connect(colors_lbl.setEnabled)

        coloring_cb.stateChanged.connect(match_colors_cb.setEnabled)
        match_colors_cb.stateChanged.connect(color_a_pb.setDisabled)
        match_colors_cb.stateChanged.connect(color_b_pb.setDisabled)

        coloring_cb.stateChanged.connect(
            lambda x: color_a_pb.setDisabled(x) if match_colors_cb.isChecked() and x else color_a_pb.setDisabled(not x))
        coloring_cb.stateChanged.connect(
            lambda x: color_b_pb.setDisabled(x) if match_colors_cb.isChecked() and x else color_b_pb.setDisabled(not x))

    @staticmethod
    def get_custom_color():
        """Opens maya color picker and gets the selected custom color"""
        cmds.colorEditor()
        if cmds.colorEditor(query=True, result=True):
            val = (cmds.colorEditor(query=True, rgb=True))
            return tuple(val)
        return
