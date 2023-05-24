"""Boiler Plate template for actions"""
from maya import cmds

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
        self.setDefinitions = []

        # class variables
        self.definition_widgets = None
        self.id = 0

    def feed(self, action_data, *args, **kwargs):
        """Mandatory Method - Feeds the instance with the action data stored in actions session"""
        self.setDefinitions = action_data.get("definitions", [])

    def action(self):
        """Mandatory Method - Execute Action"""

        for definition in self.setDefinitions:
            # if the set exists use it
            selection.add_to_set(definition["members"], definition["name"], force=True)

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
            def_members_listBox = custom_widgets.ListBoxLayout(buttonAdd=False, buttonGet=True, buttonRename=False, buttonRemove=True)
            def_formlayout.addRow(def_members_lbl, def_members_listBox)

            def_remove_lbl = QtWidgets.QLabel(text="")
            def_remove_pb = QtWidgets.QPushButton(text="Remove Selection Set")
            def_formlayout.addRow(def_remove_lbl, def_remove_pb)

            id_lbl = QtWidgets.QLabel("")
            id_separator_lbl = QtWidgets.QLabel("-"*100)
            def_formlayout.addRow(id_lbl, id_separator_lbl)

            definitions_lay.insertLayout(0, def_formlayout)

            tmp_dict = {
                "id": self.id,
                "def_name_le": def_name_le,
                "def_members_listBox": def_members_listBox,
            }
            self.definition_widgets.append(tmp_dict)

            # initial values
            def_members_listBox.viewWidget.addItems(members)
            def_name_le.setText(set_name)

            # signals
            def_name_le.editingFinished.connect(update_model)
            def_members_listBox.viewWidget.model().rowsInserted.connect(update_model) # catch the signal from the list
            def_members_listBox.viewWidget.model().rowsRemoved.connect(update_model) # catch the signal from the list
            def_members_listBox.buttonClear.clicked.connect(update_model) # catch the signal from the list
            # def_members_listBox.viewWidget.model().modelReset.connect(update_model) # catch the signal from the list
            def_members_listBox.buttonGet.clicked.connect(
                lambda _=0, widget=def_members_listBox: get_selected(widget, mesh_only=False)
            )
            def_remove_pb.clicked.connect(lambda _=0, lay=def_formlayout, uid=self.id: delete_definition(lay, uid))

            update_model()

        def get_selected(list_box_layout, mesh_only=True):
            sel, msg = selection.validate(minimum=1, maximum=None, meshes_only=False, transforms=False)
            if sel:
                # remove the items that is already in there
                existing_list = list_box_layout.listItemNames()
                refined_sel = [x for x in sel if x not in existing_list]
                list_box_layout.viewWidget.addItems(refined_sel)
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

        def delete_definition(layout_item, uid):
            for item in self.definition_widgets:
                if item["id"] == uid:
                    self.definition_widgets.remove(item)
                    break
            del_layout(layout_item)
            update_model()

        def del_layout(layout_item):
            if layout is not None:
                while layout_item.count():
                    item = layout_item.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.setParent(None)
                    else:
                        del_layout(item.layout())

        update_ui()

        add_new_definition_btn.clicked.connect(add_new_definition)
