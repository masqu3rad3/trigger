"""This module is for saving / loading custom shapes"""

from maya import cmds
import platform
from trigger.core import filelog
from trigger.core.action import ActionCore

from trigger.core.decorators import keepselection

from trigger.ui.Qt import QtWidgets
from trigger.ui.layouts.save_box import SaveBoxLayout
from trigger.ui.widgets.browser import BrowserButton, FileLineEdit

log = filelog.Filelog(logname=__name__, filename="trigger_log")


ACTION_DATA = {
    "search_key": "*_cont",
    "exclude_key": "",
    "shapes_file_path": "",
}


class Shapes(ActionCore):
    def __init__(self, *args, **kwargs):
        super(Shapes, self).__init__()
        self.shapes_file_path = ""
        self.search_key = ""
        self.exclude_key = ""

    def feed(self, action_data, *args, **kwargs):
        """Mandatory method for all action maya_modules"""
        self.shapes_file_path = action_data.get("shapes_file_path")
        self.search_key = action_data.get("search_key", "*_cont")
        self.exclude_key = action_data.get("exclude_key", "")
        print(self.shapes_file_path)
        print(self.search_key)
        print(self.exclude_key)

    def action(self):
        """Mandatory method for all action maya_modules"""
        self.import_shapes(self.shapes_file_path)

    def save_action(
        self, file_path=None, search_key=None, exclude_key=None, *args, **kwargs
    ):
        """Mandatory method for all action maya_modules"""
        file_path = file_path or self.shapes_file_path
        search_key = search_key or self.search_key
        exclude_key = exclude_key or self.exclude_key
        if file_path:
            self.export_shapes(file_path, key=search_key, exclude_key=exclude_key)

    def ui(self, ctrl, layout, handler, *args, **kwargs):
        """Mandatory method for all action maya_modules"""

        search_key_lbl = QtWidgets.QLabel(text="Search Key")
        search_key_hlay = QtWidgets.QHBoxLayout()
        search_key_le = QtWidgets.QLineEdit()
        search_key_le.setToolTip("Wildcard to get controller shapes from scene")
        search_key_preview_pb = QtWidgets.QPushButton(text="Preview Selection")
        search_key_hlay.addWidget(search_key_le)
        search_key_hlay.addWidget(search_key_preview_pb)
        layout.addRow(search_key_lbl, search_key_hlay)

        exclude_key_lbl = QtWidgets.QLabel(text="Exclude Key")
        exclude_key_hlay = QtWidgets.QHBoxLayout()
        exclude_key_le = QtWidgets.QLineEdit()
        exclude_key_le.setToolTip("Wildcard to exclude shapes")
        exclude_key_le.setPlaceholderText("(Optional) Keywords to exclude")
        exclude_key_hlay.addWidget(exclude_key_le)
        layout.addRow(exclude_key_lbl, exclude_key_hlay)

        file_path_lbl = QtWidgets.QLabel(text="Shapes File Path")
        file_path_hLay = QtWidgets.QHBoxLayout()
        file_path_le = FileLineEdit()
        file_path_hLay.addWidget(file_path_le)
        browse_path_pb = BrowserButton(
            mode="openFile",
            update_widget=file_path_le,
            filterExtensions=["Maya ASCII Files (*.ma)"],
            overwrite_check=False,
        )
        file_path_hLay.addWidget(browse_path_pb)
        layout.addRow(file_path_lbl, file_path_hLay)

        save_current_lbl = QtWidgets.QLabel(text="Save Current states")
        savebox_lay = SaveBoxLayout(
            alignment="horizontal",
            update_widget=file_path_le,
            filter_extensions=["Maya ASCII Files (*.ma)"],
            overwrite_check=True,
            control_model=ctrl,
        )
        layout.addRow(save_current_lbl, savebox_lay)

        ctrl.connect(search_key_le, "search_key", str)
        ctrl.connect(exclude_key_le, "exclude_key", str)
        ctrl.connect(file_path_le, "shapes_file_path", str)
        ctrl.update_ui()

        ### Signals
        search_key_le.textChanged.connect(lambda: ctrl.update_model())
        search_key_preview_pb.clicked.connect(
            lambda: cmds.select(
                self.get_controllers(
                    selection_key=search_key_le.text(),
                    exclude_key=exclude_key_le.text(),
                )
            )
        )
        exclude_key_le.textChanged.connect(lambda: ctrl.update_model())
        file_path_le.textChanged.connect(lambda x=0: ctrl.update_model())
        browse_path_pb.clicked.connect(lambda x=0: ctrl.update_model())
        browse_path_pb.clicked.connect(
            file_path_le.validate
        )  # to validate on initial browse result
        savebox_lay.saved.connect(
            lambda file_path: self.save_action(
                file_path, search_key_le.text(), exclude_key_le.text()
            )
        )

    @staticmethod
    def get_controllers(selection_key, exclude_key):
        all_conts = cmds.ls(selection_key, type="transform")
        if exclude_key:
            exclude_conts = cmds.ls(exclude_key, type="transform")
            all_conts = [x for x in all_conts if x not in exclude_conts]
        # EXCLUDE FK/IK icons always
        all_conts = filter(lambda x: "FK_IK" not in x, all_conts)
        return all_conts

    def gather_scene_shapes(self, key, exclude_key):
        """
        Duplicates all controllers and gathers them under the 'replaceShapes_grp'
        Args:
            key: (string) key string with wildcards to search shapes.
            exclude_key: (string) key string to exclude certain shapes

        Returns: replaceShapes_grp

        """
        all_conts = self.get_controllers(key, exclude_key)
        export_grp = cmds.group(name="replaceShapes_grp", em=True)
        for ctrl in all_conts:
            dup_ctrl = cmds.duplicate(
                ctrl, name="%s_REPLACE" % ctrl, renameChildren=True
            )[0]
            # #delete everything below
            garbage = cmds.listRelatives(dup_ctrl, c=True, typ="transform")
            # print garbage
            cmds.delete(garbage)
            for attr in ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz", "v"]:
                cmds.setAttr("%s.%s" % (dup_ctrl, attr), e=True, k=True, l=False)
            cmds.setAttr("%s.v" % dup_ctrl, 1)
            cmds.parent(dup_ctrl, export_grp)
        return export_grp

    @keepselection
    def export_shapes(self, file_path, key="*_cont", exclude_key=None):
        export_grp = self.gather_scene_shapes(key, exclude_key)
        # import pdb
        # pdb.set_trace()
        cmds.select(export_grp)
        cmds.file(
            file_path,
            force=True,
            options="v=0;",
            typ="mayaAscii",
            preserveReferences=False,
            exportSelected=True,
        )
        cmds.delete(export_grp)
        log.info("Controller Shapes Exported successfully...")

    ### ALEMBIC CURVE EXPORT HAS A BUG - ITs DEPRECATED UNTIL FURTHER FIXes
    # def export_shapes(self, alembic_file_path):
    #     """Exports the shapes to the file location as .abc"""
    #     self.load_alembic_plugin()
    #
    #     export_grp = self.gather_scene_shapes()
    #
    #     export_command = "-file " \
    #                      "{0} " \
    #                      "-writeFaceSets 0 " \
    #                      "-writeUVsets 0 " \
    #                      "-noNormals 0 " \
    #                      "-autoSubd 0 " \
    #                      "-stripNamespaces 1 " \
    #                      "-wholeFrameGeo 0 " \
    #                      "-renderableOnly 0 " \
    #                      "-step 1.0 " \
    #                      "-dataFormat 'Ogawa' " \
    #                      "-worldSpace 0 " \
    #                      "-writeVisibility 0 " \
    #                      "-frameRange 1 1 " \
    #                      "-eulerFilter 0 " \
    #                      "-writeColorSets 0 " \
    #                      "-uvWrite 0 " \
    #                      "-root {1}".format(alembic_file_path, export_grp)
    #
    #     log.info("COMMAND: %s" %export_command)
    #     cmds.AbcExport(j=export_command)
    #     cmds.delete(export_grp)
    #     log.info("Exporting shapes successfull...")

    def import_shapes(self, file_path):
        all_nodes = cmds.file(
            file_path, i=True, ignoreVersion=True, returnNewNodes=True
        )
        all_ctrl_curves = cmds.ls(all_nodes, type="nurbsCurve")
        for curve_shape in all_ctrl_curves:
            rig_shape = curve_shape.replace("_REPLACE", "")
            if not cmds.objExists(rig_shape):
                continue
            # Alex trick
            cmds.connectAttr(
                "%s.worldSpace" % curve_shape, "%s.create" % rig_shape, f=True
            )
            cmds.dgeval("%s.worldSpace" % rig_shape)

        # oddly, it requires a viewport refresh before disconnecting (or deleting) the replacement shapes
        cmds.refresh()
        cmds.delete("replaceShapes_grp")

    # def import_shapes(self, alembic_file_path):
    #     """Imports shapes from the alembic file and replaces them with the existing ones"""
    #     self.load_alembic_plugin()
    #
    #     cmds.AbcImport(alembic_file_path, ftr=False, sts=False)
    #     # get all the shapes in the group
    #     all_ctrl = cmds.listRelatives("replaceShapes_grp", children=True)
    #
    #     for ctrl in all_ctrl:
    #         # get the shape
    #         shapes = extra.getShapes(ctrl)
    #         for shape in shapes:
    #             rig_shape = shape.replace("_REPLACE", "")
    #             if not cmds.objExists(rig_shape):
    #                 continue
    #             # Alex trick
    #             cmds.connectAttr("%s.worldSpace" % shape, "%s.create" % rig_shape, f=True)
    #
    #     # oddly, it requires a viewport refresh before disconnecting (or deleting) the replacement shapes
    #     cmds.refresh()
    #     cmds.delete("replaceShapes_grp")

    def load_alembic_plugin(self):
        """Makes sure the alembic plugin is loaded"""
        currentPlatform = platform.system()
        ext = ".mll" if currentPlatform == "Windows" else ".so"
        try:
            cmds.loadPlugin("AbcExport%s" % ext)
        except:
            log.error("Alembic Plugin cannot be loaded")
