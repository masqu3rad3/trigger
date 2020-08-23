"""This module is responsible for importing/exporting external files (mostly geometries)"""

from maya import cmds
from maya import mel
import platform

from trigger.core import feedback
from trigger.library import functions as extra
from trigger.library import controllers as ic

FEEDBACK = feedback.Feedback(__name__)


ACTION_DATA = {}

class ImportExport(object):
    def __init__(self, *args, **kwargs):
        super(ImportExport, self).__init__()
        # self.rigName = "trigger"

    def action(self):
        """Mandatory method for all action maya_modules"""
        pass


    def import_scene(self, file_path, *args, **kwargs):
        return cmds.file(file_path, i=True)


    def import_obj(self, file_path, *args, **kwargs):
        opFlag = "lo=0 mo=1"
        cmds.file(file_path, i=True, op=opFlag)

    def import_alembic(self, file_path, *args, **kwargs):
        self._load_alembic_plugin()
        cmds.AbcImport(file_path, ftr=False, sts=False)

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
        except: FEEDBACK.throw_error("Alembic Plugin cannot be loaded")

    def _load_fbx_plugin(self):
        """Makes sure the FBX plugin is loaded"""
        try: cmds.loadPlugin("fbxmaya")
        except: FEEDBACK.throw_error("FBX Plugin cannot be loaded")

    # TODO: EXPORT FUNCTIONS