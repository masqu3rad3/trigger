"""Boiler Plate template for actions"""

from trigger.core import io
from trigger.core import filelog
from trigger.core.decorators import tracktime

from trigger.library import selection

from trigger.ui.Qt import QtWidgets
from trigger.ui import custom_widgets
from trigger.ui import feedback

log = filelog.Filelog(logname=__name__, filename="trigger_log")

"""
example action data:
ACTION_DATA = {
                "definitions": [
                        {
                            "name": "renderGeo_set",
                            "members": ["faceAvA, bodyAvA]
                        },
                        {
                            "name": "controllers_set",
                            "members": [Arm_cont, Leg_cont]
                        }
                    ]
                }
"""


ACTION_DATA = {
    "definitions": [],
}

# Name of the class MUST be the capitalized version of file name. eg. morph.py => Morph, split_shapes.py => Split_shapes
class Selection_sets(object):
    def __init__(self, *args, **kwargs):
        super(Selection_sets, self).__init__()

        # user defined variables
        self.setDefinitions = None

        # class variables
        self.definition_widgets = None
        self.id = 0

    def feed(self, action_data, *args, **kwargs):
        """Mandatory Method - Feeds the instance with the action data stored in actions session"""
        self.setDefinitions = action_data.get("definitions")

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

        definitions_lbl = QtWidgets.QLabel(text="Definitions")
        definitions_lay = QtWidgets.QVBoxLayout()
        layout.addRow(definitions_lbl, definitions_lay)

        add_new_definition_btn = QtWidgets.QPushButton(text= "Add New Set")
        definitions_lay.addWidget(add_new_definition_btn)

        self.id = 0
        self.definition_widgets = []

        def add_new_definition(set_name=None, members=None):
            if not set_name:
                # collect existing set names
                all_set_names = [x["name"] for x in self.setDefinitions]
                uid_count = 1
                set_name = "triggerSet1"
                while set_name in all_set_names:
                    set_name = "triggerSet%i" % uid_count
                    uid_count += 1
            members = members or []

            self.id += 1

            def_formlayout = QtWidgets.QFormLayout()

            def_name_lbl = QtWidgets.QLabel(text="Name")
            def_name_le = QtWidgets.QLineEdit()
            def_formlayout.addRow(def_name_lbl, def_name_le)

            def_members_lbl = QtWidgets.QLabel(text="Members")
            def_members_listBox = custom_widgets.ListBoxLayout(buttonAdd=True, buttonGet=True, buttonRename=True, buttonRemove=True)
            def_formlayout.addRow(def_members_lbl, def_members_listBox)

            tmp_dict = {
                "id": self.id,
                "def_name_le": def_name_le,
                "def_members_listBox": def_members_listBox,
            }
            self.definition_widgets.append(tmp_dict)

            # initial values
            def_members_listBox.viewWidget.addItems(members)
            def_name_le.setText(set_name)

        def get_selected(update_widget, mesh_only=True):
            sel, msg = selection.validate(min=1, max=None, meshesOnly=False, transforms=False)
            if sel:
                update_widget.setText(sel[0])
                update_model()
            else:
                feedback.Feedback().pop_info(title="Selection Error", text=msg, critical=True)

        def update_model():
            definitions = []
            for widget_dict in self.definition_widgets:
                tmp_dict = {}
                tmp_dict["name"] = widget_dict["def_name_le"].text()
                tmp_dict["members"] = widget_dict["def_members_listBox"].listItemNames()
                definitions.append(tmp_dict)

            # feed the model with the definitions
            ctrl.model.edit_action(ctrl.action_name, "definitions", definitions)


        def update_ui():
            data = ctrl.model.query_action(ctrl.action_name, "definitions")
            for definition in data:
                add_new_definition(set_name=definition["name"],
                                   members=definition["members"],
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
