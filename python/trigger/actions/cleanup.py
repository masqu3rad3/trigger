"""Cleanup"""
from maya import cmds
from maya import mel

from trigger.core import filelog
from trigger.library import functions, connection, shading

from trigger.ui.Qt import QtWidgets, QtGui # for progressbar

# from PySide2 import QtWidgets

log = filelog.Filelog(logname=__name__, filename="trigger_log")

ACTION_DATA = {
    "delete_unknown_nodes": True,
    "delete_blind_data": True,
    "delete_unused_nodes": True,
    "delete_display_layers": True,
    "delete_animation_layers": True,
    "merge_similar_file_nodes": True,
    "merge_similar_shaders": True,
}

class Cleanup(object):
    def __init__(self, *args, **kwargs):
        super(Cleanup, self).__init__()

        # user defined variables
        self.deleteUnknownNodes = True
        self.deleteBlindData = True
        self.deleteUnusedNodes = True
        self.deleteDisplayLayers = True
        self.deleteAnimationLayers = True
        self.mergeSimilarFileNodes = True
        self.mergeSimilarShaders = True

        # class variables

    def feed(self, action_data, *args, **kwargs):
        """Mandatory Method - Feeds the instance with the action data stored in actions session"""
        self.deleteUnknownNodes = action_data.get("delete_unknown_nodes")
        self.deleteBlindData = action_data.get("delete_blind_data")
        self.deleteUnusedNodes = action_data.get("delete_unused_nodes")
        self.deleteDisplayLayers = action_data.get("delete_display_layers")
        self.deleteAnimationLayers = action_data.get("delete_animation_layers")
        self.mergeSimilarFileNodes = action_data.get("merge_similar_file_nodes")
        self.mergeSimilarShaders = action_data.get("merge_similar_shaders")

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
        if self.mergeSimilarFileNodes:
            self.merge_similar_file_nodes()
        if self.mergeSimilarShaders:
            self.merge_similar_shaders()

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
        # Delete Section
        clear_lbl = QtWidgets.QLabel(text="Delete from scene: ")

        clear_vlay = QtWidgets.QVBoxLayout()
        unknown_nodes_cb = QtWidgets.QCheckBox(text="Unknown Nodes")
        blind_data_cb = QtWidgets.QCheckBox(text="Blind Data")
        delete_unusued_nodes_cb = QtWidgets.QCheckBox(text="Unused Shading Nodes")
        display_layers_cb = QtWidgets.QCheckBox(text="Display Layers")
        animation_layers_cb = QtWidgets.QCheckBox(text="Animation Layers")
        clear_vlay.addWidget(unknown_nodes_cb)
        clear_vlay.addWidget(blind_data_cb)
        clear_vlay.addWidget(delete_unusued_nodes_cb)
        clear_vlay.addWidget(display_layers_cb)
        clear_vlay.addWidget(animation_layers_cb)

        layout.addRow(clear_lbl, clear_vlay)

        # optimize section
        optimize_lbl = QtWidgets.QLabel(text="Optimize: ")
        optimize_vlay = QtWidgets.QVBoxLayout()
        merge_similar_file_nodes_cb = QtWidgets.QCheckBox(text="Merge Similar File Nodes")
        merge_similar_shaders_cb = QtWidgets.QCheckBox(text="Merge Similar Shaders")
        optimize_vlay.addWidget(merge_similar_file_nodes_cb)
        optimize_vlay.addWidget(merge_similar_shaders_cb)

        layout.addRow(optimize_lbl, optimize_vlay)

        ctrl.connect(unknown_nodes_cb, "delete_unknown_nodes", bool)
        ctrl.connect(blind_data_cb, "delete_blind_data", bool)
        ctrl.connect(delete_unusued_nodes_cb, "delete_unused_nodes", bool)
        ctrl.connect(display_layers_cb, "delete_display_layers", bool)
        ctrl.connect(animation_layers_cb, "delete_animation_layers", bool)
        ctrl.connect(merge_similar_file_nodes_cb, "merge_similar_file_nodes", bool)
        ctrl.connect(merge_similar_shaders_cb, "merge_similar_shaders", bool)

        ctrl.update_ui()

        #Signals
        unknown_nodes_cb.stateChanged.connect(lambda x=0: ctrl.update_model())
        blind_data_cb.stateChanged.connect(lambda x=0: ctrl.update_model())
        delete_unusued_nodes_cb.stateChanged.connect(lambda x=0: ctrl.update_model())
        display_layers_cb.stateChanged.connect(lambda x=0: ctrl.update_model())
        animation_layers_cb.stateChanged.connect(lambda x=0: ctrl.update_model())
        merge_similar_file_nodes_cb.stateChanged.connect(lambda x=0: ctrl.update_model())
        merge_similar_shaders_cb.stateChanged.connect(lambda x=0: ctrl.update_model())

    def delete_unknown_nodes(self):
        unknown_nodes = cmds.ls(type="unknown")
        functions.deleteObject(unknown_nodes)
        log.info("%i unknown nodes deleted" %len(unknown_nodes))

    def delete_blind_data(self):
        blind_types = ["polyBlindData", "blindDataTemplate"]
        blind_nodes = cmds.ls(type=blind_types)
        functions.deleteObject(blind_nodes)
        log.info("%i blind data nodes deleted" %len(blind_nodes))

    def delete_unused_nodes(self):
        mel.eval('hyperShadePanelMenuCommand("hyperShadePanel1", "deleteUnusedNodes");')

    def delete_display_layers(self):
        layers = cmds.ls(type="displayLayer")
        layers.remove("defaultLayer")
        functions.deleteObject(layers)
        log.info("%i display layers deleted" %len(layers))

    def delete_animation_layers(self):
        layers = cmds.ls(type="animLayer")
        functions.deleteObject(layers)
        log.info("%i animation layers deleted" %len(layers))

    @staticmethod
    def merge_similar_file_nodes():
        """Makes sure that there are no file nodes sharing the same file path"""

        all_file_nodes = cmds.ls(type="file")
        # create dictionary of paths:
        path_dict = {}
        for file_node in all_file_nodes:
            file_path = cmds.getAttr("%s.fileTextureName" % file_node)
            if not file_path:
                functions.deleteObject(file_node)
            else:
                path_dict.setdefault(file_path, []).append(file_node)

        history = []
        for file_path, node_list in path_dict.items():
            if len(node_list) > 1:
                # replace the outgoing connections with first node for the rest
                for node in node_list[1:]:
                    connection.replace_connections(node, node_list[0], incoming=False, outgoing=True)
                    history.append(node)
                    functions.deleteObject(node)

        log.info("%s duplicate file nodes has been deleted" % len(history))
        return path_dict

    @staticmethod
    def merge_similar_shaders():
        all_materials = shading.get_all_materials()

        dict_list = []
        for mat in all_materials:
            mat_dict = {"name": mat}
            connections = cmds.listConnections(mat, source=True, destination=False, plugs=True, connections=True)
            if connections:
                active_plugs = connections[::2]
            else:
                continue
            file_dict = {}
            for plug in active_plugs:
                file_node = shading.find_file_node(plug)
                if file_node:
                    texture_name = cmds.getAttr("%s.fileTextureName" % file_node)
                file_dict[plug.split(".")[-1]] = texture_name
                mat_dict["filedata"] = file_dict
            dict_list.append(mat_dict)

        ## group the shaders sharing the same filedata

        out = {}
        for d in dict_list:
            out.setdefault(tuple(d['filedata'].items()), []).append(d['name'])
        same_shaders_list = [v for v in out.values() if len(v) > 1]

        for same in same_shaders_list:
            selection_list = []
            shading_engines = cmds.listConnections(same, source=False, destination=True, type="shadingEngine")
            for sha in shading_engines:
                selection_list.extend(cmds.sets(shading_engines, q=True))
            cmds.sets(selection_list, e=True, forceElement=shading_engines[0])

        total_shader_count = 0
        for same in same_shaders_list:
            total_shader_count += len(same)
        mel.eval('hyperShadePanelMenuCommand("hyperShadePanel1", "deleteUnusedNodes");')
        log.info("%s shaders merged into %s shaders" % (total_shader_count, len(same_shaders_list)))