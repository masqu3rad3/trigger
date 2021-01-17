"""Cleanup"""
from maya import cmds

from trigger.core import io
from trigger.core import filelog
from trigger.core.decorators import tracktime

from trigger.library import functions

from trigger.ui import custom_widgets

from trigger.ui.Qt import QtWidgets, QtGui # for progressbar
from trigger.ui import feedback

from PySide2 import QtWidgets

log = filelog.Filelog(logname=__name__, filename="trigger_log")

ACTION_DATA = {
    "unknown_nodes": True,
    "blind_data": True,
    "display_layers": True,
    "animation_layers": True,
}

class Cleanup(object):
    def __init__(self, *args, **kwargs):
        super(Cleanup, self).__init__()

        # user defined variables
        self.deleteUnknownNodes = True
        self.deleteBlindData = True
        self.deleteDisplayLayers = True
        self.deleteAnimationLayers = True

        # class variables

    def feed(self, action_data, *args, **kwargs):
        """Mandatory Method - Feeds the instance with the action data stored in actions session"""
        self.deleteUnknownNodes = action_data.get("unknown_nodes")
        self.deleteBlindData = action_data.get("blind_data")
        self.deleteDisplayLayers = action_data.get("display_layers")
        self.deleteAnimationLayers = action_data.get("animation_layers")

    def action(self):
        """Mandatory Method - Execute Action"""
        # everything in this method will be executed automatically.
        # This method does not accept any arguments. all the user variable must be defined to the instance before
        if self.deleteUnknownNodes:
            self.delete_unknown_nodes()
        if self.deleteBlindData:
            self.delete_blind_data()
        if self.deleteDisplayLayers:
            self.delete_display_layers()
        if self.deleteAnimationLayers:
            self.delete_animation_layers()

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

        clear_lbl = QtWidgets.QLabel(text="Delete from scene: ")

        clear_vlay = QtWidgets.QVBoxLayout()
        unknown_nodes_cb = QtWidgets.QCheckBox(text="Unknown Nodes")
        blind_data_cb = QtWidgets.QCheckBox(text="Blind Data")
        display_layers_cb = QtWidgets.QCheckBox(text="Display Layers")
        animation_layers_cb = QtWidgets.QCheckBox(text="Animation Layers")
        clear_vlay.addWidget(unknown_nodes_cb)
        clear_vlay.addWidget(blind_data_cb)
        clear_vlay.addWidget(display_layers_cb)
        clear_vlay.addWidget(animation_layers_cb)

        layout.addRow(clear_lbl, clear_vlay)

        ctrl.connect(unknown_nodes_cb, "unknown_nodes", bool)
        ctrl.connect(blind_data_cb, "blind_data", bool)
        ctrl.connect(display_layers_cb, "display_layers", bool)
        ctrl.connect(animation_layers_cb, "animation_layers", bool)

        ctrl.update_ui()

        #Signals
        unknown_nodes_cb.stateChanged.connect(lambda x=0: ctrl.update_model())
        blind_data_cb.stateChanged.connect(lambda x=0: ctrl.update_model())
        display_layers_cb.stateChanged.connect(lambda x=0: ctrl.update_model())
        animation_layers_cb.stateChanged.connect(lambda x=0: ctrl.update_model())

    def delete_unknown_nodes(self):
        unknown_nodes = cmds.ls(type="unknown")
        functions.deleteObject(unknown_nodes)
        log.info("%i unknown nodes deleted" %len(unknown_nodes))

    def delete_blind_data(self):
        blind_types = ["polyBlindData", "blindDataTemplate"]
        blind_nodes = cmds.ls(type=blind_types)
        functions.deleteObject(blind_nodes)
        log.info("%i blind data nodes deleted" %len(blind_nodes))

    def delete_display_layers(self):
        layers = cmds.ls(type="displayLayer")
        layers.remove("defaultLayer")
        functions.deleteObject(layers)
        log.info("%i display layers deleted" %len(layers))


    def delete_animation_layers(self):
        layers = cmds.ls(type="animLayer")
        functions.deleteObject(layers)
        log.info("%i animation layers deleted" %len(layers))
