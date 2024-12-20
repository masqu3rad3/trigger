"""Look action saves and loads shaders"""

import os
from maya import cmds

from trigger.core import io
from trigger.core import filelog
from trigger.core.action import ActionCore

from trigger.ui.Qt import QtWidgets
from trigger.ui.layouts import save_box
from trigger.ui.widgets.browser import BrowserButton, FileLineEdit
from trigger.core.decorators import keepselection

log = filelog.Filelog(logname=__name__, filename="trigger_log")


ACTION_DATA = {
    "look_file_path": "",
}


# Name of the class MUST be the capitalized version of file name. eg. morph.py => Morph, split_shapes.py => Split_shapes
class Look(ActionCore):
    action_data = ACTION_DATA

    def __init__(self, **kwargs):
        super(Look, self).__init__(kwargs)
        self.io = io.IO(file_name="tmp_look.trl")
        # user defined variables
        self.lookFilePath = None

        # class variables

    def feed(self, action_data, *args, **kwargs):
        """Mandatory Method - Feeds the instance with the action data stored in actions session"""
        self.lookFilePath = action_data.get("look_file_path")

    def action(self):
        """Mandatory Method - Execute Action"""
        # everything in this method will be executed automatically.
        # This method does not accept any arguments. all the user variable must be defined to the instance before

        # delete ALL SG nodes to prevent clashing
        defaults = ["initialParticleSE", "initialShadingGroup"]
        all_engines = [x for x in cmds.ls(type="shadingEngine") if x not in defaults]
        cmds.delete(all_engines)

        look_data = self.io.read(self.lookFilePath)

        base_folder, file_name_and_ext = os.path.split(self.lookFilePath)
        file_name, ext = os.path.splitext(file_name_and_ext)
        look_folder = os.path.join(base_folder, file_name)

        apply_data = {}
        for sg_name, elements in look_data.items():
            sg_file_path = os.path.join(look_folder, "%s.ma" % sg_name)
            if not os.path.isfile(sg_file_path):
                log.warning("Shader file path not exist => %s. Skipping" % sg_file_path)
                continue

            sg_node_list = self.import_sgs(sg_file_path)
            if sg_node_list:
                sg_node = sg_node_list[0]
                apply_data[sg_node] = elements

        self.assign_sg_data(apply_data)

    def save_action(self, file_path=None, *args, **kwargs):
        """Mandatory Method - Save Action"""
        file_path = file_path or self.lookFilePath
        base_folder, file_name_and_ext = os.path.split(file_path)
        file_name, ext = os.path.splitext(file_name_and_ext)
        look_folder = os.path.join(base_folder, file_name)
        self.io.folder_check(look_folder)

        look_data = self.collect_sg_data()
        self.export_sgs(look_data.keys(), look_folder)
        self.io.write(look_data, file_path=file_path)

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

        file_path_lbl = QtWidgets.QLabel(text="Look File Path:")
        file_path_hLay = QtWidgets.QHBoxLayout()
        file_path_le = FileLineEdit()
        file_path_hLay.addWidget(file_path_le)
        browse_path_pb = BrowserButton(
            mode="openFile",
            update_widget=file_path_le,
            filterExtensions=["Trigger Look Files (*.trl)"],
            overwrite_check=False,
        )
        file_path_hLay.addWidget(browse_path_pb)
        layout.addRow(file_path_lbl, file_path_hLay)

        save_current_lbl = QtWidgets.QLabel(text="Save Current states")
        savebox_lay = save_box.SaveBoxLayout(
            alignment="horizontal",
            update_widget=file_path_le,
            filter_extensions=["Trigger Look Files (*.trl)"],
            overwrite_check=True,
            control_model=ctrl,
        )
        layout.addRow(save_current_lbl, savebox_lay)

        ctrl.connect(file_path_le, "look_file_path", str)
        ctrl.update_ui()

        ### Signals
        file_path_le.textChanged.connect(lambda x=0: ctrl.update_model())
        browse_path_pb.clicked.connect(lambda x=0: ctrl.update_model())
        savebox_lay.saved.connect(lambda file_path: self.save_action(file_path))

    @staticmethod
    def collect_sg_data():
        all_shading_engines = cmds.ls(type="shadingEngine")
        shading_dict = {}
        for sg in all_shading_engines:
            if cmds.sets(sg, q=True):
                sets = cmds.sets(sg, q=True)
                sets_full_path = [cmds.ls(x, l=True)[0] for x in sets]
                shading_dict[sg] = sets_full_path
        return shading_dict

    @staticmethod
    def assign_sg_data(sg_data):
        for sg, elements in sg_data.items():
            ## elements are faces or shapes
            if elements:
                for face_or_shape in elements:
                    instances = cmds.ls(face_or_shape.split("|")[-1], l=True)
                    for inst in instances:
                        try:
                            cmds.sets(inst, e=True, forceElement=sg)
                        except ValueError:
                            log.warning("Cannot find %s. Skipping" % inst)

    @staticmethod
    @keepselection
    def export_sgs(sg_list, root_folder):
        original_name = cmds.file(q=True, sn=True)
        for sg in sg_list:
            cmds.select(sg, allDagObjects=False, noExpand=True)
            if cmds.ls(sl=True):
                cmds.file(rename=os.path.join(root_folder, sg))
                cmds.file(op="v=0;", typ="mayaAscii", pr=True, es=True, force=True)
        cmds.file(rename=original_name)

    @staticmethod
    def import_sgs(file_path):
        all_imports = cmds.file(file_path, i=True, rnn=True)
        sg_nodes = cmds.ls(all_imports, type="shadingEngine")
        return sg_nodes
