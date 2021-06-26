"""Module for converting blendshape deformations joint based deformations"""
import subprocess
import os
import platform

from maya import cmds
from maya import mel

from trigger.library import deformers, attribute, functions, api, arithmetic, naming
from trigger.core.decorators import keepselection, tracktime
from trigger.library import connection


class Bone(object):
    def __init__(self, joint):
        self._name = joint
        self._translateMult_node = cmds.createNode("multMatrix", name="%s_MM_translate" % self._name)
        self._rotateMult_node = cmds.createNode("multMatrix", name="%s_MM_rotate" % self._name)
        self._positionCompensate_node = cmds.createNode("pointMatrixMult", name="%s_pointMatrixMult" % self._name)
        self._rotationDecompose_node = cmds.createNode("decomposeMatrix", name="%s_decomposeMatrix" % self._name)

        cmds.connectAttr("%s.matrixSum" % self._translateMult_node, "%s.inMatrix" % self._positionCompensate_node)
        cmds.connectAttr("%s.matrixSum" % self._rotateMult_node, "%s.inputMatrix" % self._rotationDecompose_node)

        # set initial compensation value
        self._default_distance = cmds.getAttr("%s.translate" % self._name, time=0)[0]
        # cmds.currentTime(0)
        # self._default_distance = api.getWorldTranslation()
        cmds.setAttr("%s.inPoint" % self._positionCompensate_node, *self._default_distance)

        self._isClean = False

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        cmds.rename(self._name, name)
        self._name = name

    # @property
    # def translate_mult(self):
    #     return self._translateMult_node
    #
    # @property
    # def rotate_mult(self):
    #     return self._rotateMult_node

    def add_driver(self, t_matrix_plug, r_matrix_plug, position_offset=(0,0,0)):
        # connect the driver into nex available attrs
        t_id = attribute.getNextIndex("%s.matrixIn" % self._translateMult_node)
        cmds.connectAttr(t_matrix_plug, "%s.matrixIn[%i]" %(self._translateMult_node, t_id))

        r_id = attribute.getNextIndex("%s.matrixIn" % self._rotateMult_node)
        cmds.connectAttr(r_matrix_plug, "%s.matrixIn[%i]" %(self._rotateMult_node, t_id))

        # compensate the offset value
        offset = tuple(x - y for x, y in zip(self._default_distance, position_offset)) # subtract tuples
        cmds.setAttr("%s.inPoint" % self._positionCompensate_node, *offset)
        self._default_distance = offset

    # @property
    # def decompose_matrix(self):
    #     return self._decomposeMatrix

    def is_clean(self):
        return self._isClean

    def clear_keys(self):
        t_keys = cmds.listConnections(self._name, type="animCurveTU") or []
        r_keys = cmds.listConnections(self._name, type="animCurveTA") or []
        s_keys = cmds.listConnections(self._name, type="animCurveTL") or []
        all_keys = t_keys + r_keys + s_keys
        if all_keys:
            cmds.delete(all_keys)

        cmds.connectAttr("%s.output" % self._positionCompensate_node, "%s.translate" % self._name, f=True)
        cmds.connectAttr("%s.outputRotate" % self._rotationDecompose_node, "%s.rotate" % self._name, f=True)
        self._isClean = True

    def is_active(self, time_gap, translate_threshold=0.01, rotate_threshold=0.5, decimal=3):
        """Checks if the object is moving between the given time gap"""

        def get_std_deviation(value_list):
            avg = sum(value_list) / len(value_list)
            var = sum((x - avg) ** 2 for x in value_list) / len(value_list)
            std = var ** 0.5
            return std

        for attr in "xyz":
            val_list = cmds.keyframe("%s.t%s" % (self._name, attr), q=True, valueChange=True, t=tuple(time_gap))
            deviation = round(get_std_deviation(val_list), decimal)
            # print("t%s" %attr, deviation)
            if deviation > translate_threshold:
                return True
        for attr in "xyz":
            val_list = cmds.keyframe("%s.r%s" % (self._name, attr), q=True, valueChange=True, t=tuple(time_gap))
            deviation = round(get_std_deviation(val_list), decimal)
            if deviation > rotate_threshold:
                return True
        return False

class Driver(object):
    def __init__(self, name="drv", bone=None, time_gap=None, parent_node=None):
        # self._name = cmds.spaceLocator(name=naming.uniqueName(name))[0]
        self._name = cmds.group(em=True, name=naming.uniqueName(name))
        if parent_node:
            cmds.parent(self._name, parent_node)
        self._bone = bone
        self._timeGap = tuple(time_gap)


    @property
    def bone(self):
        return self._bone

    @bone.setter
    def bone(self, bone_object):
        self._bone = bone_object

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        cmds.rename(self._name, name)
        self._name = name

    @property
    def time_gap(self):
        return self._timeGap

    @time_gap.setter
    def time_gap(self, time_gap):
        self._timeGap = time_gap

    def get_animcurves(self):
        connections = cmds.listConnections(self._name)
        anim_curves = cmds.ls(connections, type=['animCurveTA', 'animCurveTL', 'animCurveTT', 'animCurveTU'])
        return anim_curves

    def copy_keys(self):
        """ copies the keys from the joint """
        assert self._bone, "bone to drive is not defined"
        assert self._timeGap, "time gap is not defined"
        time_offset = (self._timeGap[0] * -1)
        cmds.copyKey(self._bone.name, time=self._timeGap)
        cmds.pasteKey(self._name, timeOffset=time_offset)
        # set the handles and pre/post infinity
        cmds.keyTangent(self._name, inTangentType="spline", outTangentType="spline")
        cmds.setInfinity(self._name, pri='linear', poi='linear')

    def drive(self):
        assert self._bone, "bone to drive is not defined"
        if not self._bone.is_clean():
            self._bone.clear_keys()

        pick_translate = cmds.createNode("pickMatrix", name="pick_translate")
        cmds.setAttr("%s.useTranslate" % pick_translate, 1)
        cmds.setAttr("%s.useRotate" % pick_translate, 0)
        cmds.setAttr("%s.useShear" % pick_translate, 0)
        cmds.setAttr("%s.useScale" % pick_translate, 0)
        cmds.connectAttr("%s.worldMatrix[0]" % self._name, "%s.inputMatrix" % pick_translate)
        # cmds.connectAttr("%s.xformMatrix" % self._name, "%s.inputMatrix" % pick_translate)

        pick_rotate = cmds.createNode("pickMatrix", name="pick_rotate")
        cmds.setAttr("%s.useTranslate" % pick_rotate, 0)
        cmds.setAttr("%s.useRotate" % pick_rotate, 1)
        cmds.setAttr("%s.useShear" % pick_rotate, 0)
        cmds.setAttr("%s.useScale" % pick_rotate, 0)
        cmds.connectAttr("%s.worldMatrix[0]" % self._name, "%s.inputMatrix" % pick_rotate)
        # cmds.connectAttr("%s.xformMatrix" % self._name, "%s.inputMatrix" % pick_rotate)

        offset = cmds.getAttr("%s.translate" % self._name, time=0)[0]
        self._bone.add_driver(t_matrix_plug="%s.outputMatrix" % pick_translate, r_matrix_plug="%s.outputMatrix" % pick_rotate, position_offset=offset)


class Shape(object):
    def __init__(self, name, jointify_node, duration, combination_of=None, hook_attrs=None):
        self._drivers = []
        if not cmds.objExists(jointify_node):
            cmds.group(em=True, name=jointify_node)
        self._jointifyNode = jointify_node
        self._name = name
        self._duration = duration
        self._hookAttrs = hook_attrs
        if combination_of:
            self._baseShapes = combination_of
        else:
            self._baseShapes = []

    def add_driver(self, driver):
        self._drivers.append(driver)

    def get_driver_names(self):
        return [drv.name for drv in self._drivers]

    # def make_connections(self):
    #     # validate the hook attribute
    #     if self._baseShapes: # in case this is a combination shape
    #         base_attrs = []
    #         for base in self._baseShapes:
    #             base_attr = attribute.validate_attr("{0}.{1}".format(self._jointifyNode, base), attr_range=[0.0, self._duration],
    #                                                 attr_type="float", default_value=0, keyable=True, display=True)
    #             base_attrs.append(base_attr)
    #
    #         # out_attr = "locator3.tx"
    #         combo_node = cmds.createNode("combinationShape", name="%s_combo" % ("_".join(self._baseShapes)))
    #         # TODO Here is the place to adjust combinationShape Node if necessary
    #
    #         for nmb, attr in enumerate(base_attrs):
    #             cmds.connectAttr(attr, "{0}.inputWeight[{1}]".format(combo_node, nmb))
    #
    #         jointify_attr = "%s.outputWeight" % combo_node
    #         # cmds.connectAttr("%s.outputWeight" % combo_node, out_attr)
    #
    #     else:
    #         jointify_attr = attribute.validate_attr("{0}.{1}".format(self._jointifyNode, self._name), attr_range=[0.0, self._duration],
    #                                             attr_type="float", default_value=0, keyable=True, display=True)
    #     for driver in self._drivers:
    #         driver.drive()
    #         anim_curves = driver.get_animcurves()
    #         if anim_curves:
    #             input_attrs = ["%s.input" % x for x in anim_curves]
    #             curve_duration = driver.time_gap[1] - driver.time_gap[0]
    #             # attribute.drive_attrs(jointify_attr, input_attrs, driver_range=[0, 1], driven_range=[0,curve_duration], force=True)
    #             # use multiplier in order to make out-of-range animation available
    #             # self._multiply_connect(jointify_attr, input_attrs, self._duration)
    #             # make a direct connection to jointify node
    #             _ = [cmds.connectAttr(jointify_attr, x) for x in input_attrs]
    #
    #     # drive the attribute with the scene hook if there is one
    #     if self._hookNode:
    #         hook_attr = attribute.validate_attr("{0}.{1}".format(self._hookNode, self._name),
    #                                                 attr_range=[0.0, 1.0],
    #                                                 attr_type="float", default_value=0, keyable=True, display=True)
    #
    #         # TODO maybe the _multiply connect node can be optimized if needed
    #         self._multiply_connect(hook_attr, [jointify_attr], self._duration)

    def make_connections(self):


        jointify_attr = attribute.validate_attr("{0}.{1}".format(self._jointifyNode, self._name), attr_range=[0.0, self._duration],
                                                attr_type="float", default_value=0, keyable=True, display=True)
        for driver in self._drivers:
            driver.drive()
            anim_curves = driver.get_animcurves()
            if anim_curves:
                input_attrs = ["%s.input" % x for x in anim_curves]
                curve_duration = driver.time_gap[1] - driver.time_gap[0]
                # attribute.drive_attrs(jointify_attr, input_attrs, driver_range=[0, 1], driven_range=[0,curve_duration], force=True)
                # use multiplier in order to make out-of-range animation available
                # self._multiply_connect(jointify_attr, input_attrs, self._duration)
                # make a direct connection to jointify node
                _ = [cmds.connectAttr(jointify_attr, x) for x in input_attrs]

        # drive the attribute with the scene hook if there is one

        # if self._hookAttrs:
        #     hook_attr = attribute.validate_attr("{0}.{1}".format(self._hookAttrs, self._name),
        #                                         attr_range=[0.0, 1.0],
        #                                         attr_type="float", default_value=0, keyable=True, display=True)



        # validate the hook attribute
        if self._baseShapes:  # in case this is a combination shape
            # print("Debug")
            # print(self._name, self._baseShapes)
            # base_attrs = []
            # for base in self._baseShapes:
            #     base_attr = attribute.validate_attr("{0}.{1}".format(self._hookAttrs, base),
            #                                         attr_range=[0.0, 1.0],
            #                                         attr_type="float", default_value=0, keyable=True, display=True)
            #     base_attrs.append(base_attr)

            # out_attr = "locator3.tx"
            combo_node = cmds.createNode("combinationShape", name="%s_combo" % ("_".join(self._baseShapes)))
            # TODO Here is the place to adjust combinationShape Node if necessary

            for nmb, attr in enumerate(self._hookAttrs):
                cmds.connectAttr(attr, "{0}.inputWeight[{1}]".format(combo_node, nmb))

            self._multiply_connect("%s.outputWeight" % combo_node, jointify_attr, self._duration)

        else:
            # TODO maybe the _multiply connect node can be optimized if needed
            self._multiply_connect(self._hookAttrs[0], jointify_attr, self._duration)


    def _multiply_connect(self, driver_attr, driven_attr, mult_value):
        if mult_value != 1:
            mult_node = cmds.createNode("multDoubleLinear", name="%s_mult" %driven_attr)
            cmds.setAttr("%s.isHistoricallyInteresting" %mult_node, 0)
            cmds.connectAttr(driver_attr, "%s.input1" %mult_node)
            cmds.setAttr("%s.input2" %mult_node, mult_value)
            # output_plug = arithmetic.multiply(driver_attr, mult_value)
            cmds.connectAttr("%s.output" %mult_node, driven_attr)
        else:
            cmds.connectAttr(driver_attr, driven_attr)



class Jointify(object):
    def __init__(self,
                 blendshape_node=None,
                 joint_count=30,
                 shape_duration=10,
                 joint_iterations=30,
                 fbx_source=None,
                 head_joint=None,
                 head_position=None,
                 *args, **kwargs):
        super(Jointify, self).__init__()

        self._check_plugins()

        # user variables
        self.blendshapeNode = blendshape_node
        self.jointCount = joint_count
        self.headJoint = head_joint
        self.shapeDuration = shape_duration
        self.jointIterations = joint_iterations
        self.fbxSource = fbx_source

        self.headJoint = head_joint

        if head_joint and not head_position:
            self.headPosition = api.getWorldTranslation(head_joint)
        else:
            self.headPosition = head_position or [0, 0, 0]

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
            cmds.setKeyframe(self.blendshapeNode, at=attr, t=start_frame - 1, value=0, itt="linear", ott="linear")
            cmds.setKeyframe(self.blendshapeNode, at=attr, t=start_frame, value=0, itt="linear", ott="linear")
            cmds.setKeyframe(self.blendshapeNode, at=attr, t=end_frame, value=1, itt="linear", ott="linear")
            cmds.setKeyframe(self.blendshapeNode, at=attr, t=end_frame + 1, value=0, itt="linear", ott="linear")
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

        # create the root joint:
        cmds.select(d=True)
        root_jnt = cmds.joint(name="jointifyRoot_jnt")
        cmds.setAttr("%s.t" % root_jnt, *self.headPosition)
        # parent the demJoints to the root bone and offset the key values accordingly
        cmds.parent(self.demData["joints"], root_jnt)
        for jnt in self.demData["joints"]:
            cmds.keyframe("%s.tx" % jnt, vc=self.headPosition[0]*-1, relative=True)
            cmds.keyframe("%s.ty" % jnt, vc=self.headPosition[1]*-1, relative=True)
            cmds.keyframe("%s.tz" % jnt, vc=self.headPosition[2]*-1, relative=True)

    # def jointify(self):
    #     """Creates a joint version of the blendshape deformations using the dem bones data as guidance"""
    #
    #     print("Jointifying the blendshape node")
    #     # create a hook node to replace the blendshape deformer
    #     jointify_hook = cmds.group(em=True, name="jointify_hook")
    #
    #     # TODO prepare the incoming database according to the requirements:
    #     # All imported animated joints
    #     # imported mesh which is skinclustered to the animated joints
    #     # Names of all shapes
    #     # Time Gaps for all shapes
    #     # combinationShape info for all shapes
    #
    #
    #     # requires imported animated joints and mesh
    #
    #     multMatrix_db = {}
    #     for shape, data in self.originalData.items():
    #         # find the active joints in the time gap
    #         active_joints = [jnt for jnt in self.demData["joints"] if self._is_moving(jnt, data["timeGap"])]
    #
    #         for jnt in active_joints:
    #             if multMatrix_db.get(jnt):
    #                 translate_mult = multMatrix_db[jnt][0]
    #                 translate_mult_index = attribute.getNextIndex("%s.matrixIn" %translate_mult)
    #                 rotate_mult = multMatrix_db[jnt][1]
    #                 rotate_mult_index = attribute.getNextIndex("%s.matrixIn" %rotate_mult)
    #             else:
    #                 translate_mult = cmds.createNode("multMatrix")
    #                 translate_mult_index = 0
    #                 rotate_mult = cmds.createNode("multMatrix")
    #                 rotate_mult_index = 0
    #                 multMatrix_db[jnt] = (translate_mult, rotate_mult)
    #             driver_loc = cmds.spaceLocator(name="%s_%s_loc" %(shape, jnt))
    #             self.copy_keys(jnt, driver_loc, time_range=data["timeGap"], start_frame=0)
    #         # for each active joint:
    #             # create an upper group, apply the same time gap animation to the group
    #
    #             # create the corresponding attribute on the jointify hook
    #             # drive the group animation with that attribute
    #
    #     return multMatrix_db
    #     # do a separate loop for connecting combination shapes and end-hook connections:
    #     # for each shape:
    #         # if the shape IS a combination shape:
    #             # create a combination node to drive that attribute with related base attributes
    #             ## requires all combination shapes
    #         # else (NOT a combination shape)
    #             # if original shape is driven with some other attr, drive this with the same one
    #
    #     pass

    def jointify(self):
        """Creates a joint version of the blendshape deformations using the dem bones data as guidance"""

        print("Jointifying the blendshape node")

        # tidy up the scene with groups
        drivers_grp = functions.validateGroup("jointifyDrv_grp")

        bone_objects = [Bone(x) for x in self.demData["joints"] if x is not "jointifyRoot_jnt"]

        jointify_node = functions.validateGroup("jointify")

        # before making connections (which clears joint keys), get all the transform data from joints since they are re-used
        shape_objects = []
        for shape, data in self.originalData.items():
            # TODO Get the hook nood procedurally from the blendshapes input connections
            scene_hook = data["in"].split(".")[0] if data["in"] else None
            if data["type"] == "combination":
                scene_hooks = [self.originalData[x]["in"] for x in data["combinations"] if self.originalData[x]["connected"]]
            else:
                scene_hooks = [data["in"]] if data["connected"] else []

            shape_obj = Shape(name=shape, jointify_node=jointify_node, duration=data["timeGap"][1] - data["timeGap"][0], combination_of=data["combinations"], hook_attrs=scene_hooks)
            # create a driver for each active bone object
            for bone_obj in bone_objects:
                if bone_obj.is_active(time_gap=data["timeGap"]):
                    drv_obj = Driver(name="drv", bone=bone_obj, time_gap=data["timeGap"], parent_node=drivers_grp)
                    drv_obj.copy_keys()
                    shape_obj.add_driver(drv_obj)
            shape_objects.append(shape_obj)

        for shape_obj in shape_objects:
            shape_obj.make_connections()
            # cmds.parent(shape_obj.get_driver_names(), drivers_grp)

        # # create driver objects
        # for shape in all_shapes:
        #     shape_obj = Shape()
        #     # add active bones
        #     active_bones = [x for x in bone_objects if x.is_active(time_gap=time_gap)]

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

    @staticmethod
    def copy_keys(source, target, time_range=None, start_frame=None):
        if start_frame != None:
            time_offset = (time_range[0] * -1) + start_frame
        else:
            time_offset = 0
        cmds.copyKey(source, time=time_range)
        cmds.pasteKey(target, timeOffset=time_offset)
