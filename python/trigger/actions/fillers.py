"""Responsible for creating visualization fillers for controllers"""

from trigger.core import io
from trigger.core import filelog
from trigger.core.decorators import tracktime

from trigger.ui import custom_widgets
from trigger.ui import feedback

log = filelog.Filelog(logname=__name__, filename="trigger_log")


ACTION_DATA = {
    "controllers": [],
    "scaling": True,
    "scale_only_positive": True,
    "coloring": True,
    "color_a": (),
    "color_b": (),
    "color_method": "object",
    "primary_channel": "Auto",
    "visibility_controller": None
}

class Fillers(object):
    def __init__(self, *args, **kwargs):
        super(Fillers, self).__init__()

        # user defined variables
        self.controllers = None
        self.scaling = None
        self.scale_only_positive = None
        self.coloring = None
        self.color_a = None
        self.color_b = None
        self.color_method = None
        self.primary_channel = None
        self.visibility_controller = None

    def feed(self, action_data, *args, **kwargs):
        """Mandatory Method - Feeds the instance with the action data stored in actions session"""
        self.controllers = action_data.get("controllers")
        self.scaling = action_data.get("scaling")
        self.scale_only_positive = action_data.get("scale_only_positive")
        self.coloring = action_data.get("coloring")
        self.color_a = action_data.get("color_a")
        self.color_b = action_data.get("color_b")
        self.color_method = action_data.get("color_method")
        self.primary_channel = action_data.get("primary_channel")
        self.visibility_controller = action_data.get("visibility_controller")

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

        pass
