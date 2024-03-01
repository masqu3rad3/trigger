"""Layout for selecting objects or nodes from the scene"""

from maya import cmds

import trigger.library.selection
from trigger.library import functions
from trigger.ui.Qt import QtWidgets, QtCore
from trigger.ui import feedback


class SceneSelectLayout(QtWidgets.QHBoxLayout):
    """Layout for selecting objects or nodes from the scene"""

    selection_types = ["object", "vertex", "edge", "face", "attribute"]

    def __init__(
        self,
        selection_type="object",
        single_selection=False,
        select_button=True,
        add_button=False,
        read_only=False,
        unique=True,
        *args,
        **kwargs
    ):
        super(SceneSelectLayout, self).__init__(*args, **kwargs)
        self.single_selection = single_selection
        self.selection_type = "object"
        self.set_selection_type(selection_type)  # object, vertex, edge, face

        self.feedback = feedback.Feedback(parent=self)
        self._is_select_button = select_button
        self._is_add_button = (
            not single_selection or add_button
        )  # if its single selection, then there is no add button

        self.select_button = None
        self.add_button = None
        self.select_textbox = None

        self.read_only = read_only
        self.unique = unique

        self.setMargin(0)

        self.build()

    @property
    def selection(self):
        """Return the selection."""
        return self.text_to_list(self.select_textbox.text())

    def set_selection_type(self, selection_type):
        """Set the selection type."""
        if selection_type not in self.selection_types:
            raise ValueError(
                "Invalid selection type: {0}. Valid values are {1}".format(
                    selection_type, self.selection_types
                )
            )
        self.selection_type = selection_type

    def build(self):
        """Build layout."""
        self.select_textbox = QtWidgets.QLineEdit()
        self.select_textbox.setReadOnly(self.read_only)
        self.addWidget(self.select_textbox)

        if self._is_add_button:
            self.add_button = QtWidgets.QPushButton(text="+")
            self.add_button.setFixedWidth(20)
            self.add_button.clicked.connect(self.add)
            self.addWidget(self.add_button)

        if self._is_select_button:
            self.select_button = QtWidgets.QPushButton(text="<")
            self.select_button.setFixedWidth(20)
            self.select_button.clicked.connect(self.select)
            self.addWidget(self.select_button)

    def _get_selection(self):
        """Validate the selection."""
        selection_type = trigger.library.selection.get_selection_type()
        if selection_type != self.selection_type and self.selection_type != "attribute":
            self.feedback.pop_info(
                title="Selection Error",
                text="Please select a {0}".format(self.selection_type),
                critical=True,
            )
            return None
        if self.selection_type == "attribute":
            selection = cmds.channelBox(
                "mainChannelBox", query=True, selectedMainAttributes=True
            )
        else:
            selection = cmds.ls(selection=True)
        return selection

    def select(self):
        """Select objects or nodes from the scene."""

        selection = self._get_selection()
        if selection:
            if self.single_selection:
                self.select_textbox.setText(selection[0])
            else:
                self.select_textbox.setText(self.list_to_text(selection))

    def add(self):
        """Add the selection to the current selection."""
        selection = self._get_selection()
        if not selection:
            return
        # append the selection to the textbox
        current_selection = self.text_to_list(self.select_textbox.text())
        current_selection.extend(selection)
        if self.unique:
            current_selection = functions.unique_list(current_selection)
        self.select_textbox.setText(self.list_to_text(current_selection))

    @staticmethod
    def list_to_text(list_item):
        return "; ".join(list_item)

    @staticmethod
    def text_to_list(text_item):
        if text_item:
            return str(text_item).split("; ")
        else:
            return []
