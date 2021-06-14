"""Module for converting blendshape deformations joint based deformations"""
import subprocess
import os
import platform

from maya import cmds
from maya import mel

from trigger.library import deformers, attribute, functions
from trigger.core.decorators import keepselection, tracktime
from trigger.library import connection

class Jointify(object):
    def __init__(self, blendshape_node=None, joint_count=30, head_joint=None, shape_duration=10, joint_iterations=30, fbx_source=None, *args, **kwargs):
        super(Jointify, self).__init__()

        self._check_plugins()

        # user variables
        self.blendshapeNode = blendshape_node
        self.jointCount = joint_count
        self.headJoint = head_joint
        self.shapeDuration = shape_duration
        self.jointIterations = joint_iterations
        self.fbxSource = fbx_source


        # class variables
        self.dem_exec = self._get_dem_bones()
        self.originalData = {}
        self.trainingData = {}
        self.demData = {}

    def start(self):
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
        self.trainingData["animationRange"] = [0, (len(self.originalData.items())*self.shapeDuration)]
        self.trainingData["mesh"] = cmds.listConnections("{0}.outputGeometry".format(self.blendshapeNode))[0]

        for nmb, (attr, data) in enumerate(self.originalData.items()):
            # print("nmb", nmb)
            # print("attr", attr)
            # print("data", data)


            # disconnect inputs
            if data["connected"]:
                cmds.disconnectAttr(data["in"], data["out"])
            start_frame = (self.shapeDuration * (nmb+1)) - self.shapeDuration
            end_frame = start_frame + (self.shapeDuration-1)
            cmds.setKeyframe(self.blendshapeNode, at=attr, t=start_frame - 1, value=0)
            cmds.setKeyframe(self.blendshapeNode, at=attr, t=start_frame, value=0)
            cmds.setKeyframe(self.blendshapeNode, at=attr, t=end_frame, value=1)
            cmds.setKeyframe(self.blendshapeNode, at=attr, t=end_frame + 1, value=0)
            data["timeGap"] = [start_frame, end_frame]

        # # update the training data
        # self.trainingData["startFrame"] = shape_duration
        # self.trainingData["endFrame"] = (shape_duration * (len(self.originalData.items())+1)) + (shape_duration-1)
        # self.trainingData["shapeDuration"] = shape_duration

    @tracktime
    @keepselection
    def create_dem_bones(self):
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

        if not self.fbxSource:
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
                "FBXExportBakeComplexEnd": "-v 0",
                "FBXExportBakeComplexStart": "-v 0",
                "FBXExportAnimationOnly": "-v false",
                "FBXExportSkeletonDefinitions": "-v true",
                "FBXExportUpAxis": "y",
                "FBXExportQuaternion": "-v resample",
                "FBXExportInstances": "-v false",
                "FBXExportBakeComplexStep": "-v 1",
                "FBXExportCameras": "-v false",
                "FBXExportTangents": "-v false",
                "FBXExportInAscii": "-v false",
                "FBXExportLights": "-v true",
                "FBXExportReferencedAssetsContent": "-v true",
                "FBXExportConstraints": "-v false",
                "FBXExportSmoothMesh": "-v true",
                "FBXExportHardEdges": "-v false",
                "FBXExportInputConnections": "-v false",
                "FBXExportEmbeddedTextures": "-v false",
                "FBXExportBakeComplexAnimation": "-v false",
                "FBXExportCacheFile": "-v true",
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

        else:
            fbx_source = self.fbxSource

        # do the DEM magic
        process = subprocess.Popen([self.dem_exec.replace("\\", "/"),
                          '-a=%s' %abc_source.replace("\\", "/"),
                          '-i=%s' %fbx_source.replace("\\", "/"),
                          '-o=%s' %fbx_output.replace("\\", "/"),
                          '-b=%i' %self.jointCount,
                                    # '--bindUpdate=1',
                                    # '--patience=3',
                                    # '--transAffine=10',
                                    '--nInitIters=%i' %self.jointIterations,
                                    # '-n=400',
                                    # '--transAffineNorm=10'
                                    ])
        process.communicate()


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
            "FBXImportHardEdges": "-v false",
            "FBXImportAxisConversionEnable": "-v true",
            "FBXImportCacheFile": "-v true",
            "FBXImportUpAxis": "y",
            "FBXImportSkins": "-v true",
            "FBXImportConvertUnitString": "-v true",
            "FBXImportForcedFileAxis": "-v disabled"
        }
        for item in fbx_import_settings.items():
            mel.eval('%s %s' % (item[0], item[1]))

        compFilePath = fbx_output.replace("\\", "//")  ## for compatibility with mel syntax.
        cmd = ('FBXImport -f "{0}";'.format(compFilePath))

        # get the difference of nodes before and after the import
        pre = cmds.ls(long=True)
        mel.eval(cmd)
        after = cmds.ls(long=True)

        # build dem-data dictionary
        self.demData["demNodes"] = [x for x in after if x not in pre]
        self.demData["joints"] = cmds.ls(self.demData["demNodes"], type="joint")
        self.demData["meshes"] = cmds.ls(self.demData["demNodes"], type="mesh")
        self.demData["meshTransform"] = functions.getParent(self.demData["meshes"][0])
        self.demData["skinCluster"] = deformers.get_deformers(self.demData["meshTransform"]).get('skinCluster')[0]


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

        multMatrix_db = {}
        for shape, data in self.originalData.items():
            # find the active joints in the time gap
            active_joints = [jnt for jnt in self.demData["joints"] if self._is_moving(jnt, data["timeGap"])]

            for jnt in active_joints:
                if multMatrix_db.get(jnt):
                    translate_mult = multMatrix_db[jnt][0]
                    translate_mult_index = attribute.getNextIndex("%s.matrixIn" %translate_mult)
                    rotate_mult = multMatrix_db[jnt][1]
                    rotate_mult_index = attribute.getNextIndex("%s.matrixIn" %rotate_mult)
                else:
                    translate_mult = cmds.createNode("multMatrix")
                    translate_mult_index = 0
                    rotate_mult = cmds.createNode("multMatrix")
                    rotate_mult_index = 0
                    multMatrix_db[jnt] = (translate_mult, rotate_mult)
                driver_loc = cmds.spaceLocator(name="%s_%s_loc" %(shape, jnt))
            # for each active joint:
                # create an upper group, apply the same time gap animation to the group

                # create the corresponding attribute on the jointify hook
                # drive the group animation with that attribute

        return multMatrix_db
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

    @staticmethod
    def _is_moving(obj, time_gap, translate_threshold=0.01, rotate_threshold=0.5, decimal=3):
        """Checks if the object is moving between the given time gap"""

        def get_std_deviation(value_list):
            avg = sum(value_list) / len(value_list)
            var = sum((x - avg) ** 2 for x in value_list) / len(value_list)
            std = var ** 0.5
            return std

        for attr in "xyz":
            val_list = cmds.keyframe("%s.t%s" % (obj, attr), q=True, valueChange=True, t=tuple(time_gap))
            deviation = round(get_std_deviation(val_list), decimal)
            # print("t%s" %attr, deviation)
            if deviation > translate_threshold:
                return True
        for attr in "xyz":
            val_list = cmds.keyframe("%s.r%s" % (obj, attr), q=True, valueChange=True, t=tuple(time_gap))
            deviation = round(get_std_deviation(val_list), decimal)
            # print("r%s" %attr, deviation, val_list)
            if deviation > rotate_threshold:
                return True
        return False

