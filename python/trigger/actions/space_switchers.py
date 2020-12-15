"""Creates extra space switchers"""

"""
example action data:
ACTION_DATA = {
                "switcher_definitions": [
                        {
                            "anchor": "IK_L_Hand_cont",
                            "locations": ["pelvis_cont", "master_cont", "chest_cont"]
                        },
                        {
                            "anchor": "head_cont",
                            "locations": ["pelvis_cont", "neck_cont", "master_cont"]
                        }
                    ]
                }
"""

from trigger.core import io
from trigger.core import logger

from trigger.ui.Qt import QtWidgets, QtGui, QtCore
from trigger.ui import custom_widgets
from trigger.ui import feedback

from trigger.utils import space_switcher

LOG = logger.Logger(__name__)

ACTION_DATA = {
    "switcher_definitions": [],
}


# Name of the class MUST be the capitalized version of file name. eg. morph.py => Morph, split_shapes.py => Split_shapes
class Space_switchers(object):
    def __init__(self, *args, **kwargs):
        super(Space_switchers, self).__init__()

        # user defined variables
        self.swithcerDefinitions = None

        # class variables

    def feed(self, action_data, *args, **kwargs):
        """Mandatory Method - Feeds the instance with the action data stored in actions session"""
        self.swithcerDefinitions = action_data.get("switcher_definitions")

    def action(self):
        """Mandatory Method - Execute Action"""
        # everything in this method will be executed automatically.
        # This method does not accept any arguments. all the user variable must be defined to the instance before
        for sw_data in self.swithcerDefinitions:
            space_switcher.create_space_switch(sw_data[0], sw_data[1], overrideExisting=True, mode=sw_data[2])

    def save_action(self):
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
            handler: (actions_session) An instance of the actions_session.
                                    TRY NOT TO USE HANDLER UNLESS ABSOLUTELY NECESSARY
            *args:
            **kwargs:

        Returns: None

        """
        switcher_definitions_lbl = QtWidgets.QLabel(text="Definitions")
        switcher_definitions_lay = QtWidgets.QVBoxLayout()
        layout.addRow(switcher_definitions_lbl, switcher_definitions_lay)

        add_new_definition_btn = QtWidgets.QPushButton(text= "Add New Definition")
        switcher_definitions_lay.addWidget(add_new_definition_btn)

        self.id = 0
        self.definition_widgets = []

        def add_new_definition(anchor_val="", locations_val="", mode_val="parent"):
            self.id += 1

            def_formlayout = QtWidgets.QFormLayout()
            def_anchor_lbl = QtWidgets.QLabel(text="Anchor")
            def_anchor_le = QtWidgets.QLineEdit()
            def_formlayout.addRow(def_anchor_lbl, def_anchor_le)
            def_targets_lbl = QtWidgets.QLabel(text="Locations")
            def_targets_le = QtWidgets.QLineEdit()
            def_targets_le.setPlaceholderText("(;) separated")
            def_formlayout.addRow(def_targets_lbl, def_targets_le)
            def_modes_lbl = QtWidgets.QLabel(text="Mode")
            def_modes_combo = QtWidgets.QComboBox()
            def_modes_combo.addItems(["parent", "point", "orient"])
            def_formlayout.addRow(def_modes_lbl, def_modes_combo)
            def_remove_lbl = QtWidgets.QLabel(text="")
            def_remove_pb = QtWidgets.QPushButton(text="Remove")
            def_formlayout.addRow(def_remove_lbl, def_remove_pb)
            switcher_definitions_lay.addLayout(def_formlayout)

            tmp_dict = {
                "id": self.id,
                "anchor_le": def_anchor_le,
                "targets_le": def_targets_le,
                "modes_combo": def_modes_combo,
            }
            self.definition_widgets.append(tmp_dict)

            # initial values
            def_anchor_le.setText(anchor_val)
            def_targets_le.setText(locations_val)
            index = def_modes_combo.findText(mode_val, QtCore.Qt.MatchFixedString)
            if index >= 0:
                def_modes_combo.setCurrentIndex(index)

            # signals
            def_anchor_le.editingFinished.connect(update_model)
            def_targets_le.editingFinished.connect(update_model)
            def_modes_combo.currentIndexChanged.connect(update_model)
            def_remove_pb.clicked.connect(lambda _=0, lay=def_formlayout, id=self.id: delete_definition(lay, id))
            def_remove_pb.clicked.connect(update_model)

        # custom model/ui updates

        def update_model():
            # collect definition data
            print("updating Model")
            switcher_definitions = []
            for widget_dict in self.definition_widgets:
                tmp_list = []
                tmp_list.append(widget_dict["anchor_le"].text())
                tmp_list.append(ctrl.text_to_list(widget_dict["targets_le"].text()))
                tmp_list.append(widget_dict["modes_combo"].currentText())
                switcher_definitions.append(tmp_list)
            # feed the model with the definitions
            ctrl.model.edit_action(ctrl.action_name, "switcher_definitions", switcher_definitions)
            print(switcher_definitions)
            pass

        def update_ui():
            print("updating UI")
            data = ctrl.model.query_action(ctrl.action_name, "switcher_definitions")
            for definition in data:
                add_new_definition(anchor_val=definition[0], locations_val=ctrl.list_to_text(definition[1]), mode_val=definition[2])
            pass

        def delete_definition(layout, id):
            print("ID", id)
            for item in self.definition_widgets:
                if item["id"] == id:
                    self.definition_widgets.pop(item)
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

        # signals
        add_new_definition_btn.clicked.connect(add_new_definition)

        pass
