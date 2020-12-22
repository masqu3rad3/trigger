"""Look action saves and loads shaders"""

import os
from maya import cmds

from trigger.core import io
from trigger.core import logger

from trigger.ui.Qt import QtWidgets, QtGui
from trigger.ui import custom_widgets
from trigger.core.decorators import keepselection
from trigger.ui import feedback

LOG = logger.Logger(__name__)

ACTION_DATA = {
    "look_file_path": "",
}

# Name of the class MUST be the capitalized version of file name. eg. morph.py => Morph, split_shapes.py => Split_shapes
class Look(object):
    def __init__(self, *args, **kwargs):
        super(Look, self).__init__()
        self.io = io.IO(file_name = "tmp_look.trl")
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
        look_data = self.io.read(self.lookFilePath)

        base_folder, file_name_and_ext = os.path.split(self.lookFilePath)
        file_name, ext = os.path.splitext(file_name_and_ext)
        look_folder = os.path.join(base_folder, file_name)

        apply_data = {}
        for sg_name, elements in look_data.items():
            sg_file_path = os.path.join(look_folder, "%s.ma" %sg_name)
            if not os.path.isfile(sg_file_path):
                LOG.warning("Shader file path not exist => %s. Skipping" %sg_file_path)
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
        self.io._folderCheck(look_folder)

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
        # file_path_le = QtWidgets.QLineEdit()
        file_path_le = custom_widgets.FileLineEdit()
        file_path_hLay.addWidget(file_path_le)
        browse_path_pb = custom_widgets.BrowserButton(mode="saveFile", update_widget=file_path_le, filterExtensions=["Trigger Look Files (*.trl)"], overwrite_check=False)
        file_path_hLay.addWidget(browse_path_pb)
        layout.addRow(file_path_lbl, file_path_hLay)


        save_current_lbl = QtWidgets.QLabel(text="Save Current states")
        savebox_lay = custom_widgets.SaveBoxLayout(alignment="horizontal", update_widget=file_path_le, filter_extensions=["Trigger Look Files (*.trl)"], overwrite_check=True, control_model=ctrl)
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
        shading_dict = {sg: cmds.sets(sg, q=True) for sg in all_shading_engines if cmds.sets(sg, q=True)}
        return shading_dict

    @staticmethod
    def assign_sg_data(sg_data):
        for sg, elements in sg_data.items():
            ## elements are faces or shapes
            if elements:
                for face_or_shape in elements:
                    try:
                        cmds.sets(face_or_shape, e=True, forceElement=sg)
                    except ValueError:
                        pass

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