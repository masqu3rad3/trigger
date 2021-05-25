"""Module for converting blendshape deformations joint based deformations"""
import subprocess
import os
import platform

from maya import cmds
from maya import mel

from trigger.library import deformers, attribute
from trigger.core.decorators import keepselection
from trigger.library import connection

class Jointify(object):
    def __init__(self, blendshape_node=None, *args, **kwargs):
        super(Jointify, self).__init__()

        self._check_plugins()

        # class variables
        self.dem_exec = self._get_dem_bones()
        self.blendshapeNode = blendshape_node
        self.originalData = {}
        self.trainingData = {}

    def start(self, blendshape_node=None):
        """Main function"""
        self.blendshapeNode = self.blendshapeNode or blendshape_node
        if not self.blendshapeNode:
            raise Exception("Blendshape node is not defined")

        self.collect_original_data()
        self.prepare_training_set()
        self.create_dem_bones()
        self.jointify()

    def collect_original_data(self):
        """Collects all target and hook plug data

        Sample:
        {
        'blink': {
                'connected': True,
                'in': 'morph_hook.blink',
                'out': 'trigger_morph_blendshape.blink',
                'type': 'base'},
        'browLowerer': {
                'connected': True,
                'in': 'morph_hook.browLowerer',
                'out': 'trigger_morph_blendshape.browLowerer',
                'type': 'base'}
        }

        """
        print("Collecting Original Data")
        self.originalData.clear()
        targetshapes = deformers.get_influencers(self.blendshapeNode)
        for shape in targetshapes:
            self.originalData[shape] = {}
            incoming = cmds.listConnections("{0}.{1}".format(self.blendshapeNode, shape), s=True, d=False)
            if incoming:
                cnx = connection.connections("{0}.{1}".format(self.blendshapeNode, shape), return_mode="incoming")[0]
                self.originalData[shape]["connected"] = True
                if cmds.objectType(incoming) == "combinationShape":
                    self.originalData[shape]["type"] = "combination"
                    # get the base attributes forming the combination
                    plugs = cmds.listConnections(incoming, plugs=True, source=True, destination=False)
                    self.originalData[shape]["combinations"] = [x.split(".")[1] for x in plugs]
                else:
                    self.originalData[shape]["type"] = "base"
                    self.originalData[shape]["combinations"] = []
                self.originalData[shape]["in"] = cnx["plug_in"]
                self.originalData[shape]["out"] = cnx["plug_out"]

            else:
                self.originalData[shape]["connected"] = False
                self.originalData[shape]["type"] = "base"
                self.originalData[shape]["in"] = ""
                self.originalData[shape]["out"] = ""
        return self.originalData

    def prepare_training_set(self):
        """Creates a ROM from blendshape targets"""

        print("Preparing Training Set")
        shape_duration = 10
        self.trainingData["animationRange"] = [0, (len(self.originalData.items())*shape_duration)]
        self.trainingData["mesh"] = cmds.listConnections("{0}.outputGeometry".format(self.blendshapeNode))[0]

        for nmb, (attr, data) in enumerate(self.originalData.items()):
            # print("nmb", nmb)
            # print("attr", attr)
            # print("data", data)


            # disconnect inputs
            if data["connected"]:
                cmds.disconnectAttr(data["in"], data["out"])
            start_frame = (shape_duration * (nmb+1)) - shape_duration
            end_frame = start_frame + (shape_duration-1)
            cmds.setKeyframe(self.blendshapeNode, at=attr, t=start_frame - 1, value=0)
            cmds.setKeyframe(self.blendshapeNode, at=attr, t=start_frame, value=0)
            cmds.setKeyframe(self.blendshapeNode, at=attr, t=end_frame, value=1)
            cmds.setKeyframe(self.blendshapeNode, at=attr, t=end_frame + 1, value=0)
            data["timeGap"] = [start_frame, end_frame]

        # # update the training data
        # self.trainingData["startFrame"] = shape_duration
        # self.trainingData["endFrame"] = (shape_duration * (len(self.originalData.items())+1)) + (shape_duration-1)
        # self.trainingData["shapeDuration"] = shape_duration

    @keepselection
    def create_dem_bones(self, joint_count=10):
        """Exports the training set to DEM bones. does the training and get back the FBX"""

        print("Training Dem Bones")
        # temporary file paths for alembic and FBX files
        abc_source = os.path.normpath(os.path.join(os.path.expanduser("~"), "jointify_source_abc.abc"))
        fbx_source = os.path.normpath(os.path.join(os.path.expanduser("~"), "jointify_source_fbx.fbx"))
        fbx_output = os.path.normpath(os.path.join(os.path.expanduser("~"), "jointify_output_fbx.fbx"))

        # export Alembic animation
        abc_exp_command = "-framerange {0} {1} -uvWrite -dataFormat ogawa -noNormals -root {2} -file {3}".format(
            self.trainingData["animationRange"][0],
            self.trainingData["animationRange"][1],
            self.trainingData["mesh"],
            abc_source
        )
        cmds.AbcExport(j= abc_exp_command)

        # export static FBX
        ### file -force -options "" -typ "FBX export" -pr -es "C:/Users/arda.kutlu/Documents/jointify_source_fbx.fbx";
        cmds.currentTime(0)
        copy_mesh = cmds.duplicate(self.trainingData["mesh"])[0]
        cmds.select(copy_mesh)
        fbx_export_settings = {
            "FBXExportApplyConstantKeyReducer": "-v false",
            "FBXExportShapes": "-v true",
            "FBXExportUseSceneName": "-v false",
            "FBXExportAxisConversionMethod": "convertAnimation",
            "FBXExportBakeComplexEnd": "-v 10",
            "FBXExportBakeComplexStart": "-v 1",
            "FBXExportAnimationOnly": "-v false",
            "FBXExportSkeletonDefinitions": "-v false",
            "FBXExportUpAxis": "y",
            "FBXExportQuaternion": "-v resample",
            "FBXExportInstances": "-v false",
            "FBXExportBakeComplexStep": "-v 1",
            "FBXExportCameras": "-v true",
            "FBXExportTangents": "-v false",
            "FBXExportInAscii": "-v false",
            "FBXExportLights": "-v true",
            "FBXExportReferencedAssetsContent": "-v true",
            "FBXExportConstraints": "-v true",
            "FBXExportSmoothMesh": "-v true",
            "FBXExportHardEdges": "-v false",
            "FBXExportInputConnections": "-v true",
            "FBXExportEmbeddedTextures": "-v true",
            "FBXExportBakeComplexAnimation": "-v false",
            "FBXExportCacheFile": "-v true",
            "FBXExportConvertUnitString": "In",
            "FBXExportSmoothingGroups": "-v true",
            "FBXExportBakeResampleAnimation": "-v true",
            "FBXExportTriangulate": "-v false",
            "FBXExportSkins": "-v true",
            "FBXExportFileVersion": "-v FBX202000",
            "FBXExportScaleFactor": "1.0"
        }
        for item in fbx_export_settings.items():
            mel.eval('%s %s'%(item[0], item[1]))

        compFilePath = fbx_source.replace("\\", "//")  ## for compatibility with mel syntax.
        cmd = ('FBXExport -f "{0}" -s;'.format(compFilePath))
        mel.eval(cmd)

        cmds.delete(copy_mesh)

        # do the DEM magic
        print("DEBUG")
        print(self.dem_exec)
        print(abc_source)
        print(fbx_source)
        print(fbx_output)
        print(joint_count)

        subprocess.Popen([self.dem_exec.replace("\\", "/"),
                          '-a=%s' %abc_source.replace("\\", "/"),
                          '-i=%s' %fbx_source.replace("\\", "/"),
                          '-o=%s' %fbx_output.replace("\\", "/"),
                          '-b=%i' %joint_count])

            ## requires joint count

        # import back the output fbx
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
        for item in mayaImp_fbx.items():
            # TODO : Test with more versions of Maya
            mel.eval('%s %s' % (item[0], item[1]))

        try:
            compFilePath = filePath.replace("\\", "//")  ## for compatibility with mel syntax.
            cmd = ('FBXImport -f "{0}";'.format(compFilePath))
            mel.eval(cmd)


        # return imported joints and mesh

        pass

    def jointify(self):
        """Creates a joint version of the blendshape deformations using the dem bones data as guidance"""

        print("Jointifying the blendshape node")
        # create a hook node to replace the blendshape deformer
        jointify_hook = cmds.group(em=True, name="jointify_hook")

        # TODO prepare the incoming database according to the requirements:
        # All imported animated joints
        # imported mesh which is skinclustered to the animated joints
        # Names of all shapes
        # Time Gaps for all shapes
        # combinationShape info for all shapes


        # requires imported animated joints and mesh

        # for each shape:
            ## requires TIME GAP for that shape
            # find the active joints in the time gap

            # for each active joint:
                # create an upper group, apply the same time gap animation to the group

                # create the corresponding attribute on the jointify hook
                # drive the group animation with that attribute


        # do a separate loop for connecting combination shapes and end-hook connections:
        # for each shape:
            # if the shape IS a combination shape:
                # create a combination node to drive that attribute with related base attributes
                ## requires all combination shapes
            # else (NOT a combination shape)
                # if original shape is driven with some other attr, drive this with the same one

        pass

    @staticmethod
    def _check_plugins():
        if not cmds.pluginInfo('AbcExport', l=True, q=True):
            try:
                cmds.loadPlugin('AbcExport')
            except:
                msg = "Alembic Export Plugin cannot be initialized."
                cmds.confirmDialog(title='Plugin Error', message=msg)
                raise Exception(msg)

        if not cmds.pluginInfo('AbcImport', l=True, q=True):
            try:
                cmds.loadPlugin('AbcImport')
            except:
                msg = "Alembic Import Plugin cannot be initialized."
                cmds.confirmDialog(title='Plugin Error', message=msg)
                raise Exception(msg)

        if not cmds.pluginInfo('fbxmaya', l=True, q=True):
            try:
                cmds.loadPlugin('fbxmaya')
            except:
                msg = "FBX Plugin cannot be initialized."
                cmds.confirmDialog(title='Plugin Error', message=msg)
                raise Exception(msg)

    @staticmethod
    def _get_dem_bones():
        """Checks the dem bones executables"""
        folder = os.path.split(os.path.realpath(__file__))[0]
        current_os = platform.system()

        if current_os == "Windows":
            executable = os.path.join(folder, "dembones", current_os, "DemBones.exe")
        elif current_os == "Linux" or os == "MacOs":
            executable = os.path.join(folder, "dembones", current_os, "DemBones")
        else:
            msg = "Unknown Operating System"
            cmds.confirmDialog(title='OS Error', message=msg)
            raise Exception(msg)

        if not os.path.isfile(executable):
            msg = "Dem-Bones executable cannot be found (%s)" %executable
            cmds.confirmDialog(title='Executable Error', message=msg)
            raise Exception(msg)

        return executable


