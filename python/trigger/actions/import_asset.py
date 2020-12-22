"""This module is responsible for importing/exporting external files (mostly geometries)"""

import os
from maya import cmds
from maya import mel
import platform

from trigger.core import logger

from trigger.ui.Qt import QtWidgets, QtGui # for progressbar
from trigger.ui import custom_widgets

LOG = logger.Logger(__name__)


ACTION_DATA = {
    "import_file_path": ""
}

class Import_asset(object):
    def __init__(self, *args, **kwargs):
        super(Import_asset, self).__init__()
        # self.rigName = "trigger"
        self.filePath = None

    def feed(self, action_data):
        self.filePath = action_data.get("import_file_path")

    def action(self):
        """Mandatory method for all action maya_modules"""
        if not self.filePath:
            LOG.warning("import path not defined")
            return
        ext = os.path.splitext(self.filePath)[1]
        if ext == ".abc":
            self.import_alembic(self.filePath)
        elif ext == ".obj":
            self.import_obj(self.filePath)
        elif ext == ".fbx":
            self.import_fbx(self.filePath)
        elif ext == ".ma" or ext == ".mb":
            self.import_scene(self.filePath)
        else:
            LOG.warning("Unrecognized file format => %s" % ext)

    def save_action(self):
        """Mandatory method for all action modules"""
        pass

    def ui(self, ctrl, layout, *args, **kwargs):

        file_path_lbl = QtWidgets.QLabel(text="File Path:")
        file_path_hLay = QtWidgets.QHBoxLayout()
        # file_path_le = QtWidgets.QLineEdit()
        file_path_le = custom_widgets.FileLineEdit()
        file_path_hLay.addWidget(file_path_le)
        browse_path_pb = custom_widgets.BrowserButton(mode="openFile", update_widget=file_path_le, filterExtensions=["Maya ASCII (*.ma)", "Maya Binary (*.mb)", "Alembic (*.abc)", "FBX (*.fbx)", "OBJ (*.obj)"], overwrite_check=False)
        file_path_hLay.addWidget(browse_path_pb)
        layout.addRow(file_path_lbl, file_path_hLay)

        ctrl.connect(file_path_le, "import_file_path", str)
        ctrl.update_ui()

        file_path_le.textChanged.connect(lambda x=0: ctrl.update_model())
        browse_path_pb.clicked.connect(lambda x=0: ctrl.update_model())
        browse_path_pb.clicked.connect(file_path_le.validate)  # to validate on initial browse result

    def import_scene(self, file_path, *args, **kwargs):
        return cmds.file(file_path, i=True)

    def import_obj(self, file_path, *args, **kwargs):
        opFlag = "lo=0 mo=1"
        cmds.file(file_path, i=True, op=opFlag)

    def import_alembic(self, file_path, update_only=False, *args, **kwargs):
        self._load_alembic_plugin()
        if not update_only:
            cmds.AbcImport(file_path, ftr=False, sts=False)
        else:
            cmds.AbcImport(file_path, connect="/", createIfNotFound=True, ftr=False, sts=False)

    def import_fbx(self, file_path, *args, **kwargs):
        self._load_fbx_plugin()

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
            # TODO : Test with more versions of Maya
            mel.eval('%s %s' % (item[0], item[1]))

        try:
            compFilePath = file_path.replace("\\", "//")  ## for compatibility with mel syntax.
            cmd = ('FBXImport -f "{0}";'.format(compFilePath))
            mel.eval(cmd)
            return True
        except:
            msg = "Cannot import FBX for unknown reason. Skipping"
            cmds.confirmDialog(title='Unknown Error', message=msg)
            return False


    def _load_alembic_plugin(self):
        """Makes sure the alembic plugin is loaded"""
        currentPlatform = platform.system()
        ext = ".mll" if currentPlatform == "Windows" else ".so"
        try: cmds.loadPlugin("AbcExport%s" % ext)
        except: LOG.throw_error("Alembic Plugin cannot be loaded")

    def _load_fbx_plugin(self):
        """Makes sure the FBX plugin is loaded"""
        try: cmds.loadPlugin("fbxmaya")
        except: LOG.throw_error("FBX Plugin cannot be loaded")

    # TODO: EXPORT FUNCTIONS