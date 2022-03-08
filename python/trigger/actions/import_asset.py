"""This module is responsible for importing/exporting external files (mostly geometries)"""

import os
from maya import cmds
from maya import mel
import platform

from trigger.library import attribute

from trigger.core import filelog
# from trigger.ui.Qt import QtWidgets, QtGui # for progressbar
from PySide2 import QtWidgets, QtGui  # for progressbar
from trigger.ui import custom_widgets
from trigger.ui.widgets.browser_button import BrowserButton

from trigger import version_control
from trigger.ui.vcs_widgets.publish_selection import PublishSelection

log = filelog.Filelog(logname=__name__, filename="trigger_log")

ACTION_DATA = {
    "import_file_path": "",
    "scale": 1.0,
    "root_suffix": "",
    "parent_under": "",
}


class Import_asset(object):
    def __init__(self, *args, **kwargs):
        super(Import_asset, self).__init__()
        self.filePath = None
        self.scale = None
        self.rootSuffix = None
        self.parentUnder = None

    def feed(self, action_data):
        self.filePath = action_data.get("import_file_path")
        self.scale = action_data.get("scale", 1.0)
        self.rootSuffix = action_data.get("root_suffix", "")
        self.parentUnder = action_data.get("parent_under", "")

    def action(self):
        """Mandatory method for all action maya_modules"""
        if not self.filePath:
            log.warning("import path not defined")
            return
        ext = os.path.splitext(self.filePath)[1]
        if ext == ".abc":
            new_nodes = self.import_alembic(self.filePath)
        elif ext == ".obj":
            new_nodes = self.import_obj(self.filePath)
        elif ext == ".fbx":
            new_nodes = self.import_fbx(self.filePath)
        elif ext == ".ma" or ext == ".mb":
            new_nodes = self.import_scene(self.filePath)
        elif ext == ".usd":
            new_nodes = self.import_usd(self.filePath)
        else:
            log.warning("Unrecognized file format => %s" % ext)
            return

        self.post_process(new_nodes, scale=self.scale, suffix=self.rootSuffix, parent_under=self.parentUnder)

    def save_action(self):
        """Mandatory method for all action modules"""
        pass

    def ui(self, ctrl, layout, handler, *args, **kwargs):

        vcs_lay = None
        override_vcs_cb = None
        path_available_in_vcs = None
        if version_control.controller:
            vcs_lbl = QtWidgets.QLabel(text="Version Control")
            # _hold_lay = QtWidgets.QVBoxLayout()
            vcs_lay = PublishSelection()
            vcs_lay.addStretch(1)
            # _hold_lay.addLayout(vcs_lay)
            # _hold_lay.addStretch(1)
            layout.addRow(vcs_lbl, vcs_lay)

            path_available_in_vcs = vcs_lay.set_path(ctrl.model.query_action(ctrl.action_name, "import_file_path"))
            # vcs_lay.path = ctrl.model.query_action(ctrl.action_name, "import_file_path")

            override_vcs_lbl = QtWidgets.QLabel(text="Override Version Control")
            override_vcs_cb = QtWidgets.QCheckBox(checked=not path_available_in_vcs)
            layout.addRow(override_vcs_lbl, override_vcs_cb)






        file_path_lbl = QtWidgets.QLabel(text="File Path")
        file_path_hLay = QtWidgets.QHBoxLayout()
        file_path_le = custom_widgets.FileLineEdit()
        file_path_hLay.addWidget(file_path_le)
        browse_path_pb = BrowserButton(mode="openFile", update_widget=file_path_le,
                                                      filterExtensions=["All Supported (*.ma *.mb *.usd *.abc *.obj)",
                                                                        "Maya ASCII (*.ma)", "Maya Binary (*.mb)",
                                                                        "USD (*.usd)", "Alembic (*.abc)", "FBX (*.fbx)",
                                                                        "OBJ (*.obj)",
                                                                        ], overwrite_check=False)
        file_path_hLay.addWidget(browse_path_pb)
        layout.addRow(file_path_lbl, file_path_hLay)

        scale_lbl = QtWidgets.QLabel(text="Scale:")
        scale_sp = QtWidgets.QDoubleSpinBox(buttonSymbols=QtWidgets.QAbstractSpinBox.NoButtons, maximum=999999.9)
        layout.addRow(scale_lbl, scale_sp)

        root_suffix_lbl = QtWidgets.QLabel(text="Root Suffix:")
        root_suffix_le = QtWidgets.QLineEdit(maximumWidth=50)
        layout.addRow(root_suffix_lbl, root_suffix_le)

        parent_under_lbl = QtWidgets.QLabel(text="Parent Under:")
        parent_under_suffix_le = QtWidgets.QLineEdit(maximumWidth=75)
        layout.addRow(parent_under_lbl, parent_under_suffix_le)

        ctrl.connect(file_path_le, "import_file_path", str)
        ctrl.connect(scale_sp, "scale", float)
        ctrl.connect(root_suffix_le, "root_suffix", str)
        ctrl.connect(parent_under_suffix_le, "parent_under", str)

        ctrl.update_ui()

        # version control override logic
        file_path_le.setDisabled(path_available_in_vcs)
        browse_path_pb.setDisabled(path_available_in_vcs)
        #     pass

        # SIGNALS
        if version_control.controller:
            vcs_lay.selectionChanged.connect(lambda path: file_path_le.setText(path))
            override_vcs_cb.stateChanged.connect(file_path_le.setEnabled)
            override_vcs_cb.stateChanged.connect(browse_path_pb.setEnabled)
        file_path_le.textChanged.connect(lambda x=0: ctrl.update_model())
        browse_path_pb.clicked.connect(lambda x=0: ctrl.update_model())
        browse_path_pb.clicked.connect(file_path_le.validate)  # to validate on initial browse result
        scale_sp.valueChanged.connect(lambda x=0: ctrl.update_model())
        root_suffix_le.textChanged.connect(lambda x=0: ctrl.update_model())
        parent_under_suffix_le.textChanged.connect(lambda x=0: ctrl.update_model())

    def import_scene(self, file_path, *args, **kwargs):
        return cmds.file(file_path, i=True, returnNewNodes=True)

    def import_obj(self, file_path, *args, **kwargs):
        opFlag = "lo=0 mo=1"
        new_nodes = cmds.file(file_path, i=True, op=opFlag, returnNewNodes=True)
        return new_nodes

    def import_alembic(self, file_path, update_only=False, *args, **kwargs):
        self._load_alembic_plugin()
        pre = cmds.ls(long=True)
        if not update_only:
            cmds.AbcImport(file_path, ftr=False, sts=False)
        else:
            cmds.AbcImport(file_path, connect="/", createIfNotFound=True, ftr=False, sts=False)
        after = cmds.ls(long=True)
        new_nodes = [x for x in after if x not in pre]
        return new_nodes

    def import_usd(self, file_path, *args, **kwargs):
        self._load_usd_plugin()
        new_nodes = cmds.file(file_path, i=True, type="USD Import", ignoreVersion=True, mergeNamespacesOnClash=False,
                              rpr=True, returnNewNodes=True)
        return new_nodes

    def import_fbx(self, file_path, *args, **kwargs):
        self._load_fbx_plugin()
        pre = cmds.ls(long=True)

        fbx_import_settings = {
            "FBXImportMergeBackNullPivots": "-v true",
            "FBXImportMode": "-v add",
            "FBXImportSetLockedAttribute": "-v false",
            "FBXImportUnlockNormals": "-v false",
            "FBXImportScaleFactor": "1.0",
            "FBXImportProtectDrivenKeys": "-v true",
            "FBXImportShapes": "-v true",
            "FBXImportQuaternion": "-v euler",
            "FBXImportCameras": "-v true",
            "FBXImportSetMayaFrameRate": "-v false",
            "FBXImportResamplingRateSource": "-v Scene",
            "FBXImportGenerateLog": "-v false",
            "FBXImportConstraints": "-v true",
            "FBXImportLights": "-v true",
            "FBXImportConvertDeformingNullsToJoint": "-v true",
            "FBXImportFillTimeline": "-v false",
            "FBXImportMergeAnimationLayers": "-v true",
            "FBXImportHardEdges": "-v true",
            "FBXImportAxisConversionEnable": "-v true",
            "FBXImportCacheFile": "-v true",
            "FBXImportUpAxis": "y",
            "FBXImportSkins": "-v true",
            "FBXImportConvertUnitString": "-v true",
            "FBXImportForcedFileAxis": "-v disabled"
        }

        for item in fbx_import_settings.items():
            mel.eval('%s %s' % (item[0], item[1]))

        try:
            compFilePath = file_path.replace("\\", "//")  ## for compatibility with mel syntax.
            cmd = ('FBXImport -f "{0}";'.format(compFilePath))
            mel.eval(cmd)
            after = cmds.ls(long=True)
            new_nodes = [x for x in after if x not in pre]
            return new_nodes
        except:
            msg = "Cannot import FBX for unknown reason. Skipping"
            log.error(msg)
            raise Exception(msg)

    @staticmethod
    def post_process(new_nodes, scale=1.0, suffix="", parent_under="", *args, **kwargs):
        """Scaling and renaming post process"""
        if suffix != "" or scale != 1.0 or parent_under != "":
            # get the root node(s)
            root_nodes = cmds.ls(new_nodes, assemblies=True, l=True)
            # make sure all scales are unlocked
            for node in new_nodes:
                if cmds.objectType(node) == "transform":
                    attribute.unlock(node, attr_list=["sx", "sy", "sz"])

            # _ = [attribute.unlock(node, attr_list=["sx", "sy", "sz"]) for node in new_nodes]
            # scale it (them) and add the suffix
            for node in root_nodes:
                temp_grp = cmds.group(name="trigger_temp_grp", em=True)
                cmds.parent(node, temp_grp)
                cmds.xform(temp_grp, s=(scale, scale, scale), piv=(0, 0, 0), ztp=True, p=True)
                cmds.makeIdentity(temp_grp, a=True, t=False, r=False, s=True)
                cmds.parent(temp_grp + node, world=True)
                cmds.delete(temp_grp)

                if suffix:
                    node = cmds.rename(node, "%s_%s" % (node, suffix))

                if parent_under:
                    cmds.parent(node, parent_under)
        else:
            # nothing to do
            return

    def _load_alembic_plugin(self):
        """Makes sure the alembic plugin is loaded"""
        if not cmds.pluginInfo("AbcExport", l=True, q=True):
            try:
                cmds.loadPlugin("AbcExport")
            except:
                log.error("Alembic Export Plugin cannot be loaded")
        if not cmds.pluginInfo("AbcImport", l=True, q=True):
            try:
                cmds.loadPlugin("AbcImport")
            except:
                log.error("Alembic Import Plugin cannot be loaded")

    def _load_fbx_plugin(self):
        """Makes sure the FBX plugin is loaded"""
        if not cmds.pluginInfo('fbxmaya', l=True, q=True):
            try:
                cmds.loadPlugin("fbxmaya")
            except:
                log.error("FBX Plugin cannot be loaded")

    def _load_usd_plugin(self):
        """Makes sure the usd plugin loaded"""
        if not cmds.pluginInfo('mayaUsdPlugin', l=True, q=True):
            try:
                cmds.loadPlugin("mayaUsdPlugin")
            except:
                log.error("USD Plugin cannot be loaded")
