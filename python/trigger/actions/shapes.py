"""This module is for saving / loading custom shapes"""
import os

from maya import cmds
import platform
from trigger.core import logger
from trigger.library import functions as extra

from trigger.ui.Qt import QtWidgets, QtGui
from trigger.ui import custom_widgets
from trigger.ui import feedback

LOG = logger.Logger(__name__, logging_level="info")

ACTION_DATA = {
                "shapes_file_path": "",
}

class Shapes(object):
    def __init__(self, *args, **kwargs):
        super(Shapes, self).__init__()
        self.shapes_file_path = ""

    def feed(self, action_data, *args, **kwargs):
        """Mandatory method for all action maya_modules"""
        self.shapes_file_path = action_data.get("shapes_file_path")

    def action(self):
        """Mandatory method for all action maya_modules"""
        self.import_shapes(self.shapes_file_path)

    def save_action(self, file_path=None, *args, **kwargs):
        """Mandatory method for all action maya_modules"""
        file_path = file_path or self.shapes_file_path
        if file_path:
            self.export_shapes(file_path)

    def ui(self, ctrl, layout, handler, *args, **kwargs):
        """Mandatory method for all action maya_modules"""

        file_path_lbl = QtWidgets.QLabel(text="Shapes File Path:")
        file_path_hLay = QtWidgets.QHBoxLayout()
        # file_path_le = QtWidgets.QLineEdit()
        file_path_le = custom_widgets.FileLineEdit()
        file_path_hLay.addWidget(file_path_le)
        browse_path_pb = custom_widgets.BrowserButton(mode="saveFile", update_widget=file_path_le, filterExtensions=["Alembic Files (*.abc)"], overwrite_check=False)
        file_path_hLay.addWidget(browse_path_pb)
        layout.addRow(file_path_lbl, file_path_hLay)


        save_current_lbl = QtWidgets.QLabel(text="Save Current states")
        savebox_lay = custom_widgets.SaveBoxLayout(alignment="horizontal", update_widget=file_path_le, filter_extensions=["Alembic Files (*.abc)"], overwrite_check=True, control_model=ctrl)
        layout.addRow(save_current_lbl, savebox_lay)

        ctrl.connect(file_path_le, "shapes_file_path", str)
        ctrl.update_ui()

        ### Signals
        file_path_le.editingFinished.connect(lambda x=0: ctrl.update_model())
        browse_path_pb.clicked.connect(lambda x=0: ctrl.update_model())
        savebox_lay.saved.connect(lambda file_path: self.save_action(file_path))



    def gather_scene_shapes(self, key="*_cont"):
        """
        Duplicates all controllers and gathers them under the 'replaceShapes_grp'
        Args:
            key: (string) Optional key string with wildcards to search shapes.

        Returns: replaceShapes_grp

        """
        all_ctrl = cmds.ls(key, type="transform")
        # EXCLUDE FK/IK icons always
        all_ctrl = filter(lambda x: "FK_IK" not in x, all_ctrl)
        export_grp = cmds.group(name="replaceShapes_grp", em=True)
        for ctrl in all_ctrl:
            dup_ctrl = cmds.duplicate(ctrl, name="%s_REPLACE" % ctrl, renameChildren=True)[0]
            # #delete everything below
            garbage = cmds.listRelatives(dup_ctrl, c=True, typ="transform")
            # print garbage
            cmds.delete(garbage)
            for attr in ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz", "v"]:
                cmds.setAttr("%s.%s" % (dup_ctrl, attr), e=True, k=True, l=False)
            cmds.setAttr("%s.v" % dup_ctrl, 1)
            cmds.parent(dup_ctrl, export_grp)
        return export_grp
    
    def export_shapes(self, alembic_file_path):
        """Exports the shapes to the file location as .abc"""
        self.load_alembic_plugin()

        export_grp = self.gather_scene_shapes()

        export_command = "-file " \
                         "{0} " \
                         "-writeFaceSets 0 " \
                         "-writeUVsets 0 " \
                         "-noNormals 0 " \
                         "-autoSubd 0 " \
                         "-stripNamespaces 1 " \
                         "-wholeFrameGeo 0 " \
                         "-renderableOnly 0 " \
                         "-step 1.0 " \
                         "-dataFormat 'Ogawa' " \
                         "-worldSpace 0 " \
                         "-writeVisibility 0 " \
                         "-frameRange 1 1 " \
                         "-eulerFilter 0 " \
                         "-writeColorSets 0 " \
                         "-uvWrite 0 " \
                         "-root {1}".format(alembic_file_path, export_grp)

        LOG.info("COMMAND", export_command)
        cmds.AbcExport(j=export_command)
        cmds.delete(export_grp)
        LOG.info("Exporting shapes successfull...")

    # TODO: INCLUDE import_export action module and use that import functions
    def import_shapes(self, alembic_file_path):
        """Imports shapes from the alembic file and replaces them with the existing ones"""
        self.load_alembic_plugin()

        cmds.AbcImport(alembic_file_path, ftr=False, sts=False)
        # get all the shapes in the group
        all_ctrl = cmds.listRelatives("replaceShapes_grp", children=True)

        for ctrl in all_ctrl:
            # get the shape
            shapes = extra.getShapes(ctrl)
            for shape in shapes:
                rig_shape = shape.replace("_REPLACE", "")
                if not cmds.objExists(rig_shape):
                    continue
                # Alex trick
                cmds.connectAttr("%s.worldSpace" % shape, "%s.create" % rig_shape, f=True)

        # oddly, it requires a viewport refresh before disconnecting (or deleting) the replacement shapes
        cmds.refresh()
        cmds.delete("replaceShapes_grp")

    def load_alembic_plugin(self):
        """Makes sure the alembic plugin is loaded"""
        currentPlatform = platform.system()
        ext = ".mll" if currentPlatform == "Windows" else ".so"
        try: cmds.loadPlugin("AbcExport%s" % ext)
        except: LOG.throw_error("Alembic Plugin cannot be loaded")