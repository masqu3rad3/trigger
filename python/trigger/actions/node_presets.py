"""Saves and Loads node presets from arbitrary locations"""

import os
import shutil

from maya import cmds
from trigger.core import io
from trigger.core import filelog
from trigger.library import selection
from trigger.core.decorators import tracktime

from trigger.ui import custom_widgets
from trigger.ui.Qt import QtWidgets, QtGui # for progressbar
from trigger.ui import feedback

log = filelog.Filelog(logname=__name__, filename="trigger_log")


ACTION_DATA = {
    "nodes": [],
    "nodes_file_path": "",
    "skip_non_existing": True
}

# Name of the class MUST be the capitalized version of file name. eg. morph.py => Morph, split_shapes.py => Split_shapes
class Node_presets(object):
    def __init__(self, *args, **kwargs):
        super(Node_presets, self).__init__()

        self.io = io.IO(file_name="tmp_presets.trp")
        # user defined variables
        self.nodes = None
        self.nodes_file_path = ""
        self.skip_non_existing = True

        # class variables

    def feed(self, action_data, *args, **kwargs):
        """Mandatory Method - Feeds the instance with the action data stored in actions session"""
        self.nodes = action_data.get("nodes")
        self.nodes_file_path = action_data.get("nodes_file_path")
        self.skip_non_existing = action_data.get("skip_non_existing", True)

    def action(self):
        """Mandatory Method - Execute Action"""
        self.io.file_path = self.nodes_file_path
        data_list = self.io.read()

        base_folder, file_name_and_ext = os.path.split(self.nodes_file_path)
        file_name, ext = os.path.splitext(file_name_and_ext)
        remote_presets_folder = os.path.join(base_folder, file_name)

        for node_data in data_list:
            node = node_data.get("name", None)
            if not node_data.get("name", None) in self.nodes:
                continue # if the node is not exist in trigger action list , skip that
            node_preset = os.path.join(remote_presets_folder, "%s.mel" %node)
            if not os.path.exists(node_preset) and not self.skip_non_existing:
                log.error("The node preset cannot be found => %s" %node_preset, proceed=False)
            else:
                log.warning("The node preset cannot be found => %s" %node_preset)
            self.load_preset(node, remote_presets_folder)
            self.set_user_defined_attributes(node, node_data.get("user_defined", []))

    def save_action(self, file_path=None, *args, **kwargs):
        """Mandatory Method - Save Action"""
        # This method will be called automatically and accepts no arguments.
        file_path = file_path or self.nodes_file_path
        base_folder, file_name_and_ext = os.path.split(file_path)
        file_name, ext = os.path.splitext(file_name_and_ext)
        remote_presets_folder = os.path.join(base_folder, file_name)
        self.io._folderCheck(remote_presets_folder)

        # build .trp data
        data_list = []
        for node in self.nodes:
            data = {}
            # preset_path = os.path.join(remote_presets_folder, "%s.mel" % node)
            node_type = cmds.objectType(node)
            data["name"] = node
            data["type"] = node_type
            data["user_defined"] = self.collect_user_defined_attributes(node)
            data_list.append(data)
            self.save_preset(node, remote_presets_folder)

        self.io.file_path = file_path
        self.io.write(data_list)


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

        file_path_lbl = QtWidgets.QLabel(text="File Path:")
        file_path_hLay = QtWidgets.QHBoxLayout()
        file_path_le = custom_widgets.FileLineEdit()
        file_path_hLay.addWidget(file_path_le)
        browse_path_pb = custom_widgets.BrowserButton(mode="openFile", update_widget=file_path_le, filterExtensions=["Trigger Preset Files (*.trp)"], overwrite_check=False)
        file_path_hLay.addWidget(browse_path_pb)
        layout.addRow(file_path_lbl, file_path_hLay)

        nodes_lbl = QtWidgets.QLabel(text="Nodes")
        nodes_listbox = custom_widgets.ListBoxLayout(alignment="start", buttonUp=False, buttonNew=False, buttonDown=False)
        layout.addRow(nodes_lbl, nodes_listbox)

        ctrl.connect(file_path_le, "nodes_file_path", str)
        ctrl.connect(nodes_listbox.viewWidget, "nodes", list)

        ctrl.update_ui()

        save_current_lbl = QtWidgets.QLabel(text="Save Current states")
        savebox_lay = custom_widgets.SaveBoxLayout(alignment="horizontal", update_widget=file_path_le, filter_extensions=["Trigger Weight Files (*.trp)"], overwrite_check=True, control_model=ctrl)
        layout.addRow(save_current_lbl, savebox_lay)

        def get_nodes():
            sel, msg = selection.validate(min=1, max=None, meshesOnly=False, transforms=False)
            if sel:
                nodes_listbox.viewWidget.addItems(sel)
                ctrl.update_model()
            else:
                feedback.Feedback().pop_info(title="Selection Error", text=msg, critical=True)

        def update_nodes():
            self.nodes = nodes_listbox.listItemNames()

        ### Signals
        file_path_le.textChanged.connect(lambda x=0: ctrl.update_model())
        browse_path_pb.clicked.connect(lambda x=0: ctrl.update_model())
        browse_path_pb.clicked.connect(file_path_le.validate)  # to validate on initial browse result
        nodes_listbox.buttonGet.clicked.connect(get_nodes)
        nodes_listbox.buttonRemove.clicked.connect(lambda x: ctrl.update_model())

        savebox_lay.saved.connect(lambda file_path: update_nodes())
        savebox_lay.saved.connect(lambda file_path: self.save_action(file_path))

        pass

    @staticmethod
    def save_preset(node, target_folder):
        """saves the preset to a specific folder. The file will be saved with the node name"""
        presets_folder = os.path.join(cmds.about(preferences=True), "presets")
        cmds.nodePreset(save=(node, "trigger_tmp_preset"))
        preset_name = "{0}Preset_{1}.mel".format(cmds.objectType(node), "trigger_tmp_preset")
        source_path = os.path.join(presets_folder, preset_name)
        print(source_path, os.path.isfile(source_path))
        target_path = os.path.join(target_folder, "%s.mel" % node)
        shutil.copy(source_path, target_path)
        os.remove(source_path)
        return target_path

    @staticmethod
    def load_preset(node, source_folder):
        """loads the preset from a source folder. File name must match the node name"""
        source_file = os.path.join(source_folder, "%s.mel" % node)
        if not os.path.isfile(source_file):
            log.error("The source file doesn't exist => %s" %source_file, proceed=False)
        presets_folder = os.path.join(cmds.about(preferences=True), "presets")
        if not os.path.isdir(presets_folder):
            os.mkdir(presets_folder)
        preset_name = "{0}Preset_{1}.mel".format(cmds.objectType(node), "trigger_tmp_preset")
        target_path = os.path.join(presets_folder, preset_name)
        shutil.copy(source_file, target_path)
        cmds.nodePreset(load=(node, "trigger_tmp_preset"))
        os.remove(target_path)

    @staticmethod
    def collect_user_defined_attributes(node):
        """
        Returns the user attribute dictionary list for defined node

        [
            {
            "name": "foot_roll",
            "type": "float",
            "value": 0.0
            }
        ]
        """
        ud_attrs = cmds.listAttr(node, ud=True) or []
        ud_list = []
        for attr in ud_attrs:
            attr_data = {
                "name": attr,
                "type": cmds.attributeQuery(attr, node=node, at=True),
                "value": cmds.getAttr("{0}.{1}".format(node, attr))
            }
            ud_list.append(attr_data)
        return ud_list

    @staticmethod
    def set_user_defined_attributes(node, data_list):
        """Sets the user attributes back from the json data"""
        for data in data_list:
            attr = "{0}.{1}".format(node, data["name"])
            try:
                cmds.setAttr(attr, data["value"])
            except RuntimeError:
                if cmds.listConnections(attr, source=True, destination=False):
                    continue
                elif cmds.getAttr(attr, l=True):
                    continue
                cmds.setAttr("{0}.{1}".format(node, data["name"]), data["value"], type=data["type"])
        return

