"""Module for converting blendshape deformations joint based deformations"""

import sys
import subprocess
import os
import platform

from trigger.core import compatibility as compat

if sys.version_info.major == 3:
    from math import gcd
else:
    from fractions import gcd
# import fractions
import functools
import time

from maya import cmds
from maya import mel

# unfortunatalely only ol api has the MFnBlendShapeDeformer
import maya.OpenMaya as om
import maya.OpenMayaAnim as oma

from trigger.library import (
    deformers,
    attribute,
    functions,
    api,
    arithmetic,
    naming,
    transform,
)
from trigger.core.decorators import keepselection
from trigger.library import connection
from trigger.objects import skin
from trigger.utils import skin_transfer
from trigger.core import filelog


def get_std_deviation(value_list):
    if not value_list:
        return 0
    avg = sum(value_list) / len(value_list)
    var = sum((x - avg) ** 2 for x in value_list) / len(value_list)
    std = var**0.5
    return std


class Bone(object):
    def __init__(self, joint):
        self._name = joint
        self._translateMult_node = cmds.createNode(
            "multMatrix", name="%s_MM_translate" % self._name
        )
        self._rotateMult_node = cmds.createNode(
            "multMatrix", name="%s_MM_rotate" % self._name
        )
        self._positionCompensate_node = cmds.createNode(
            "pointMatrixMult", name="%s_pointMatrixMult" % self._name
        )
        self._rotationDecompose_node = cmds.createNode(
            "decomposeMatrix", name="%s_decomposeMatrix" % self._name
        )

        cmds.connectAttr(
            "%s.matrixSum" % self._translateMult_node,
            "%s.inMatrix" % self._positionCompensate_node,
        )
        cmds.connectAttr(
            "%s.matrixSum" % self._rotateMult_node,
            "%s.inputMatrix" % self._rotationDecompose_node,
        )

        # set initial compensation value
        self._default_distance = cmds.getAttr("%s.translate" % self._name, time=0)[0]
        cmds.setAttr(
            "%s.inPoint" % self._positionCompensate_node, *self._default_distance
        )

        self._isClean = False

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        cmds.rename(self._name, name)
        self._name = name

    def add_driver(self, t_matrix_plug, r_matrix_plug, position_offset=(0, 0, 0)):
        # connect the driver into nex available attrs
        t_id = attribute.get_next_index("%s.matrixIn" % self._translateMult_node)
        cmds.connectAttr(
            t_matrix_plug, "%s.matrixIn[%i]" % (self._translateMult_node, t_id)
        )

        r_id = attribute.get_next_index("%s.matrixIn" % self._rotateMult_node)
        cmds.connectAttr(
            r_matrix_plug, "%s.matrixIn[%i]" % (self._rotateMult_node, t_id)
        )

        # compensate the offset value
        offset = tuple(
            x - y for x, y in zip(self._default_distance, position_offset)
        )  # subtract tuples
        cmds.setAttr("%s.inPoint" % self._positionCompensate_node, *offset)
        self._default_distance = offset

    def is_clean(self):
        return self._isClean

    def clear_keys(self):
        t_keys = cmds.listConnections(self._name, type="animCurveTU") or []
        r_keys = cmds.listConnections(self._name, type="animCurveTA") or []
        s_keys = cmds.listConnections(self._name, type="animCurveTL") or []
        all_keys = t_keys + r_keys + s_keys
        if all_keys:
            cmds.delete(all_keys)

        cmds.connectAttr(
            "%s.output" % self._positionCompensate_node,
            "%s.translate" % self._name,
            f=True,
        )
        cmds.connectAttr(
            "%s.outputRotate" % self._rotationDecompose_node,
            "%s.rotate" % self._name,
            f=True,
        )
        self._isClean = True

    def is_active(
        self, time_gap, translate_threshold=0.01, rotate_threshold=0.5, decimal=3
    ):
        """Checks if the object is moving between the given time gap"""

        for attr in "xyz":
            val_list = cmds.keyframe(
                "%s.t%s" % (self._name, attr),
                q=True,
                valueChange=True,
                t=tuple(time_gap),
            )
            deviation = round(get_std_deviation(val_list), decimal)
            # print("t%s" %attr, deviation)
            if deviation > translate_threshold:
                return True
        for attr in "xyz":
            val_list = cmds.keyframe(
                "%s.r%s" % (self._name, attr),
                q=True,
                valueChange=True,
                t=tuple(time_gap),
            )
            deviation = round(get_std_deviation(val_list), decimal)
            if deviation > rotate_threshold:
                return True
        return False


class Driver(object):
    def __init__(self, name="drv", bone=None, time_gap=None, parent_node=None):
        # self._name = cmds.spaceLocator(name=naming.uniqueName(name))[0]
        self._name = cmds.group(em=True, name=naming.unique_name(name))
        if parent_node:
            cmds.parent(self._name, parent_node)
        self._bone = bone
        self._timeGap = tuple(time_gap)
        self._composeTranslate = cmds.createNode(
            "composeMatrix", name="composeTranslate"
        )
        self._composeRotate = cmds.createNode("composeMatrix", name="composeRotate")

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
        anim_curves = cmds.ls(
            connections,
            type=["animCurveTA", "animCurveTL", "animCurveTT", "animCurveTU"],
        )
        return anim_curves

    def copy_keys(self):
        """copies the keys from the joint"""
        assert self._bone, "bone to drive is not defined"
        assert self._timeGap, "time gap is not defined"
        time_offset = self._timeGap[0] * -1
        cmds.copyKey(self._bone.name, time=self._timeGap)
        cmds.pasteKey(self._name, timeOffset=time_offset)
        # set the handles and pre/post infinity
        cmds.keyTangent(self._name, inTangentType="spline", outTangentType="spline")
        cmds.setInfinity(self._name, pri="linear", poi="linear")

    def drive(self):
        assert self._bone, "bone to drive is not defined"
        if not self._bone.is_clean():
            self._bone.clear_keys()

        for attr in "XYZ":
            translate_out_plug = cmds.listConnections(
                "{0}.translate{1}".format(self._name, attr),
                source=True,
                destination=False,
                p=True,
            )[0]
            cmds.connectAttr(
                translate_out_plug,
                "{0}.inputTranslate{1}".format(self._composeTranslate, attr),
                f=True,
            )

            rotate_out_plug = cmds.listConnections(
                "{0}.rotate{1}".format(self._name, attr),
                source=True,
                destination=False,
                p=True,
            )[0]
            cmds.connectAttr(
                rotate_out_plug,
                "{0}.inputRotate{1}".format(self._composeRotate, attr),
                f=True,
            )

        offset = cmds.getAttr("%s.translate" % self._name, time=0)[0]
        # self._bone.add_driver(t_matrix_plug="%s.outputMatrix" % pick_translate, r_matrix_plug="%s.outputMatrix" % pick_rotate, position_offset=offset)
        self._bone.add_driver(
            t_matrix_plug="%s.outputMatrix" % self._composeTranslate,
            r_matrix_plug="%s.outputMatrix" % self._composeRotate,
            position_offset=offset,
        )

    def clear_node(self):
        functions.delete_object(self._name)


class Shape(object):
    def __init__(
        self,
        name,
        jointify_node,
        duration,
        combination_of=None,
        hook_attrs=None,
        delta_shape=None,
        corrective_bs=None,
    ):
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
        self.deltaShape = delta_shape
        self.correctiveBs = corrective_bs

    def add_driver(self, driver):
        self._drivers.append(driver)

    def get_driver_names(self):
        return [drv.name for drv in self._drivers]

    def make_connections(self):
        jointify_attr = attribute.validate_attr(
            "{0}.{1}".format(self._jointifyNode, self._name),
            attr_range=[0.0, self._duration],
            attr_type="float",
            default_value=0,
            keyable=True,
            display=True,
        )
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

            driver.clear_node()

        if self.deltaShape:
            deformers.add_target_blendshape(
                self.correctiveBs, self.deltaShape, weight=1.0
            )
            self._multiply_connect(
                jointify_attr,
                "{0}.{1}".format(self.correctiveBs, self.deltaShape),
                1.0 / self._duration,
            )

        # validate the hook attribute
        if self._baseShapes:  # in case this is a combination shape
            name = "%s_combo" % ("_".join(self._baseShapes))
            combo_node = cmds.createNode("combinationShape", name=name)
            # TODO Here is the place to adjust combinationShape Node if necessary

            for nmb, attr in enumerate(self._hookAttrs):
                cmds.connectAttr(attr, "{0}.inputWeight[{1}]".format(combo_node, nmb))

            self._multiply_connect(
                "%s.outputWeight" % combo_node, jointify_attr, self._duration
            )

        else:
            # TODO maybe the _multiply connect node can be optimized if needed
            if self._hookAttrs:
                self._multiply_connect(
                    self._hookAttrs[0], jointify_attr, self._duration
                )

    def _multiply_connect(self, driver_attr, driven_attr, mult_value):
        if mult_value != 1:
            name = "%s_mult" % driven_attr.split(".")[-1]
            mult_node = cmds.createNode(compat.MULT_NODE_NAME, name=name)
            cmds.setAttr("%s.isHistoricallyInteresting" % mult_node, 0)
            cmds.connectAttr(driver_attr, "%s.input1" % mult_node)
            cmds.setAttr("%s.input2" % mult_node, mult_value)
            cmds.connectAttr("%s.output" % mult_node, driven_attr)
        else:
            cmds.connectAttr(driver_attr, driven_attr)


class Jointify(object):
    def __init__(
        self,
        blendshape_node=None,
        joint_count=30,
        shape_duration=0,
        joint_iterations=30,
        fbx_source=None,
        root_nodes=None,
        parent_to_roots=True,
        correctives=False,
        corrective_threshold=0.01,
        *args,
        **kwargs
    ):
        super(Jointify, self).__init__()

        self.log = filelog.Filelog(logname=__name__, filename="jointify_report")
        self.log.title("Jointify Report")

        self._check_plugins()

        # user variables
        self.blendshapeNode = blendshape_node
        self.jointCount = joint_count
        # self.headJoint = head_joint
        self.shapeDuration = shape_duration
        self.jointIterations = joint_iterations
        self.fbxSource = fbx_source
        self.correctives = correctives
        self.correctiveThreshold = corrective_threshold

        if root_nodes:
            if type(root_nodes) != list:
                self.rootNodes = [root_nodes]
            else:
                self.rootNodes = root_nodes
        else:
            self.rootNodes = [cmds.spaceLocator(name="jointify_rootLoc")[0]]

        self.parent_to_roots = parent_to_roots

        # class variables
        self.dem_exec = self._get_dem_bones()
        if not self.dem_exec:
            msg = "DemBones executable cannot be found"
            self.log.error(msg)
            raise

        self.originalData = {}
        self.trainingData = {}
        self.demData = {}
        self.correctiveBs = None

        self.log.header("Initialization")
        self.log.info("Blendshape Node: %s" % self.blendshapeNode)
        self.log.info("Joint count: %s" % self.jointCount)
        self.log.info("Shape duration: %s" % self.shapeDuration or "Auto")
        self.log.info("Joint Iterations: %s" % self.jointIterations)
        self.log.info("FBX Source: %s" % self.fbxSource)
        self.log.info("Correctives: %s" % str(bool(correctives)))
        self.log.info("Corrective Threshold: %s" % self.correctiveThreshold)

    def run(self):
        self.log.header("Starting Jointify process")
        start_time = time.time()
        self.collect_original_data()
        self.prepare_training_set()
        self.create_dem_bones()
        self.jointify()
        end_time = time.time()

        self.log.seperator()
        self.log.info("Jointified in total %s seconds" % (end_time - start_time))

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
        self.log.header("Collecting Original Data")
        self.originalData.clear()
        targetshapes = deformers.get_influencers(self.blendshapeNode)
        for shape in targetshapes:
            self.originalData[shape] = {}
            incoming = cmds.listConnections(
                "{0}.{1}".format(self.blendshapeNode, shape), s=True, d=False
            )
            if incoming:
                cnx = connection.connections(
                    "{0}.{1}".format(self.blendshapeNode, shape), return_mode="incoming"
                )[0]
                self.originalData[shape]["connected"] = True
                if cmds.objectType(incoming) == "combinationShape":
                    self.originalData[shape]["type"] = "combination"
                    # get the base attributes forming the combination
                    plugs = cmds.listConnections(
                        incoming, plugs=True, source=True, destination=False
                    )
                    _combinations = []
                    for plug in plugs:
                        _node, _attr = plug.split(".")
                        if _node == self.blendshapeNode:
                            _combinations.append(_attr)
                        # if it is not the self.blendshapeNode, try to find it from the incoming connections
                        else:
                            # TODO: This is a hotfix for the combination shapes which includes inbetweens.
                            # FIXME This is not a good solution. It should be fixed in the future
                            # print("This is a hotfix for the combination shapes which includes inbetweens.")
                            # print(plug)
                            _node_input_plug = cmds.listConnections(
                                _node, plugs=True, source=True, destination=False
                            )[0]
                            _node_parent_node, _node_parent_attr = _node_input_plug.split(".")
                            if _node_parent_node == self.blendshapeNode:
                                _combinations.append(_node_parent_attr)
                    self.originalData[shape]["combinations"] = _combinations

                    # self.originalData[shape]["combinations"] = [
                    #     x.split(".")[1] for x in plugs
                    # ]
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
                self.originalData[shape]["combinations"] = []
        self.log.info("Original data collected successfully")
        return self.originalData

    def prepare_training_set(self, smooth=False):
        """Creates a ROM from blendshape targets"""

        self.log.header("Preparing Training Set")

        # self.trainingData["mesh"] = cmds.listConnections("{0}.outputGeometry".format(self.blendshapeNode))[0]
        _history = cmds.listHistory(
            self.blendshapeNode,
            allFuture=True,
            future=True,
            pruneDagObjects=False,
            bf=False,
        )
        _shape_node = cmds.ls(_history, type="mesh")[0]
        self.trainingData["mesh"] = functions.get_parent(_shape_node)

        start_frame = 0
        end_frame = 0
        for nmb, (attr, data) in enumerate(self.originalData.items()):
            duration = self.shapeDuration or self._get_shape_duration(
                self.blendshapeNode, attr
            )
            end_delay = 1 if not smooth else duration
            end_frame = start_frame + duration
            # disconnect inputs
            if data["connected"]:
                cmds.disconnectAttr(data["in"], data["out"])

            cmds.setKeyframe(
                self.blendshapeNode,
                at=attr,
                t=start_frame,
                value=0,
                itt="linear",
                ott="linear",
            )
            cmds.setKeyframe(
                self.blendshapeNode,
                at=attr,
                t=end_frame,
                value=1,
                itt="linear",
                ott="linear",
            )
            cmds.setKeyframe(
                self.blendshapeNode,
                at=attr,
                t=end_frame + end_delay,
                value=0,
                itt="linear",
                ott="linear",
            )
            data["timeGap"] = [start_frame, end_frame]
            start_frame = end_frame + end_delay

        self.trainingData["animationRange"] = [0, end_frame]
        self.log.info("Training data prepared")

    @keepselection
    def create_dem_bones(self):
        """Exports the training set to DEM bones. does the training and get back the FBX"""

        start_time = time.time()
        self.log.header("Training Dem Bones")
        # temporary file paths for alembic and FBX files
        abc_source = os.path.normpath(
            os.path.join(os.path.expanduser("~"), "jointify_source_abc.abc")
        )
        fbx_source = os.path.normpath(
            os.path.join(os.path.expanduser("~"), "jointify_source_fbx.fbx")
        )
        fbx_output = os.path.normpath(
            os.path.join(os.path.expanduser("~"), "jointify_output_fbx.fbx")
        )

        self.log.info("Exporting Alembic Animation...")
        # export Alembic animation
        abc_exp_command = "-framerange {0} {1} -uvWrite -dataFormat ogawa -noNormals -root {2} -file {3}".format(
            self.trainingData["animationRange"][0],
            self.trainingData["animationRange"][1],
            self.trainingData["mesh"],
            abc_source,
        )
        cmds.AbcExport(j=abc_exp_command)

        if not self.fbxSource:
            self.log.info("Exporting FBX...")
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
                "FBXExportScaleFactor": "1.0",
            }
            for item in fbx_export_settings.items():
                mel.eval("%s %s" % (item[0], item[1]))

            compFilePath = fbx_source.replace(
                "\\", "//"
            )  ## for compatibility with mel syntax.
            cmd = 'FBXExport -f "{0}" -s;'.format(compFilePath)
            mel.eval(cmd)

            cmds.delete(copy_mesh)

        else:
            self.log.info("Using %s as FBX source..." % self.fbxSource)
            fbx_source = self.fbxSource

        # do the DEM magic
        self.log.info("DemBones are getting created with following flags:")
        self.log.info(self.dem_exec.replace("\\", "/"))
        self.log.info("-a=%s" % abc_source.replace("\\", "/"))
        self.log.info("-i=%s" % fbx_source.replace("\\", "/"))
        self.log.info("-o=%s" % fbx_output.replace("\\", "/"))
        self.log.info("-b=%i" % self.jointCount)
        self.log.info("--nInitIters=%i" % self.jointIterations)
        process = subprocess.Popen(
            [
                self.dem_exec.replace("\\", "/"),
                "-a=%s" % abc_source.replace("\\", "/"),
                "-i=%s" % fbx_source.replace("\\", "/"),
                "-o=%s" % fbx_output.replace("\\", "/"),
                "-b=%i" % self.jointCount,
                # '--bindUpdate=1',
                # '--patience=3',
                # '--transAffine=10',
                "--nInitIters=%i" % self.jointIterations,
                # '-n=400',
                # '--transAffineNorm=10'
            ]
        )
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
            "FBXImportForcedFileAxis": "-v disabled",
        }
        for item in fbx_import_settings.items():
            mel.eval("%s %s" % (item[0], item[1]))

        compFilePath = fbx_output.replace(
            "\\", "//"
        )  ## for compatibility with mel syntax.
        cmd = 'FBXImport -f "{0}";'.format(compFilePath)

        # get the difference of nodes before and after the import
        pre = cmds.ls(long=True)
        mel.eval(cmd)
        after = cmds.ls(long=True)

        # build dem-data dictionary
        self.demData["demNodes"] = [x for x in after if x not in pre]

        self.demData["joints"] = cmds.ls(self.demData["demNodes"], type="joint")
        self.demData["meshes"] = cmds.ls(self.demData["demNodes"], type="mesh")
        self.demData["meshTransform"] = functions.get_parent(self.demData["meshes"][0])
        self.demData["skinCluster"] = deformers.get_deformers(
            self.demData["meshTransform"]
        ).get("skinCluster")[0]

        # # create the root joint:
        # cmds.select(d=True)
        # root_jnt = cmds.joint(name="jointifyRoot_jnt")
        # cmds.setAttr("%s.t" % root_jnt, *self.headPosition)
        # # parent the demJoints to the root bone and offset the key values accordingly
        # cmds.parent(self.demData["joints"], root_jnt)
        # for jnt in self.demData["joints"]:
        #     cmds.keyframe("%s.tx" % jnt, vc=self.headPosition[0]*-1, relative=True)
        #     cmds.keyframe("%s.ty" % jnt, vc=self.headPosition[1]*-1, relative=True)
        #     cmds.keyframe("%s.tz" % jnt, vc=self.headPosition[2]*-1, relative=True)

        # # delete the temp files from disk
        # os.remove(abc_source)
        # os.remove(fbx_source)
        # os.remove(fbx_output)

        end_time = time.time()
        self.log.info("DemBones are created in %s seconds" % (end_time - start_time))

    def jointify(self):
        """Creates a joint version of the blendshape deformations using the dem bones data as guidance"""

        temp_grp = cmds.group(em=True, name="garbage_grp")

        start_time = time.time()

        self.log.header("Replacing the blendshape node with joints...")

        if self.correctives:
            neutral_shape = transform.duplicate(
                self.trainingData["mesh"], name="jointify_neutral", at_time=0
            )
            self.correctiveBs = cmds.blendShape(
                self.trainingData["mesh"], name="jointify_correctives"
            )[0]
            cmds.parent(neutral_shape, temp_grp)

        # transfer the skin weights, but dont activate the skincluster yet
        cmds.currentTime(0.0)

        # transfer skin
        # mesh_sc = cmds.ls(self.trainingData["mesh"], type="skinCluster")
        mesh_sc = deformers.get_deformers(self.trainingData["mesh"]).get(
            "skinCluster", None
        )
        if not mesh_sc:
            jointify_sc = skin_transfer.skin_transfer(
                source=self.demData["meshTransform"], target=self.trainingData["mesh"]
            )[0]
        else:
            jointify_sc = mesh_sc[0]
            cmds.skinCluster(jointify_sc, edit=True, normalizeWeights=0)
            # dem_sc = cmds.ls(self.demData["meshTransform"], type="skinCluster")[0]
            dem_sc = deformers.get_deformers(self.demData["meshTransform"]).get(
                "skinCluster", None
            )[0]
            mesh_sc_weights = skin.Weight(jointify_sc)
            dem_sc_weights = skin.Weight(dem_sc)
            dem_sc_influences = dem_sc_weights.get_all_influences()
            mesh_sc_influences = mesh_sc_weights.get_all_influences()
            # print("----------------------------")
            # print("----------------------------")
            # print("----------------------------")
            # print("----------------------------")
            # print("----------------------------")
            # print(dem_sc_influences)
            for inf in dem_sc_influences:
                # skip joint0 which is the root joint of dembones
                if inf == "joint0":
                    continue
                print("=--=--=")
                print("=--=--=")
                print(inf)
                _data = dem_sc_weights.get_influence_data(inf)
                mesh_sc_weights.add_influence(_data)
            # test_data = dem_sc_weights.get_influence_data("joint1")
            # mesh_sc_weights.add_influence(test_data)

            mesh_sc_weights.apply(jointify_sc)

        cmds.setAttr("%s.nodeState" % jointify_sc, 1)

        root_joints_data = {}
        for root_node in self.rootNodes:
            root_pos = api.get_world_translation(root_node)
            cmds.select(d=True)
            root_jnt = cmds.joint(name="jntfRoot_%s" % root_node)
            cmds.setAttr("%s.t" % root_jnt, *root_pos)

            # if self.parent_to_roots:
            #     root_jnt = root_node
            # else:
            #     cmds.select(d=True)
            #     root_jnt = cmds.joint(name="jntfRoot_%s" %root_node)
            #     cmds.setAttr("%s.t" % root_jnt, *root_pos)

            root_joints_data[root_jnt] = root_pos

        for dem_jnt in self.demData["joints"]:
            if len(self.rootNodes) > 1:
                parent_jnt = min(
                    root_joints_data.keys(),
                    key=lambda x: functions.get_distance(dem_jnt, x),
                )
            else:
                parent_jnt = list(root_joints_data.keys())[0]

            # relative positioning is not working in 2022 and before
            # cmds.parent(dem_jnt, parent_jnt)

            cmds.keyframe(
                "%s.tx" % dem_jnt,
                vc=root_joints_data[parent_jnt][0] * -1,
                relative=True,
            )
            cmds.keyframe(
                "%s.ty" % dem_jnt,
                vc=root_joints_data[parent_jnt][1] * -1,
                relative=True,
            )
            cmds.keyframe(
                "%s.tz" % dem_jnt,
                vc=root_joints_data[parent_jnt][2] * -1,
                relative=True,
            )

            # as a workaround, store the location of parent, move to 0,0,0, parent the children and move it back
            rest_position = cmds.getAttr("%s.t" % parent_jnt)[0]
            cmds.setAttr("%s.t" % parent_jnt, 0, 0, 0)  # zero out
            cmds.parent(dem_jnt, parent_jnt)  # parent in 0 pose
            cmds.setAttr(
                "%s.t" % parent_jnt, *rest_position
            )  # move it back all as group

        ######################################

        # tidy up the scene with groups
        drivers_grp = functions.validate_group("jointifyDrv_grp")

        # bone_objects = [Bone(x) for x in self.demData["joints"] if x is not "jointifyRoot_jnt"]
        bone_objects = [
            Bone(x) for x in self.demData["joints"] if x != "jointifyRoot_jnt"
        ]

        jointify_node = functions.validate_group("jointify")

        # before making connections (which clears joint keys), get all the transform data from joints since they are re-used
        shape_objects = []

        self.log.info("Creating drivers and making connections...")
        progress = Progressbar(
            title="Creating Drivers ...", max_value=len(self.originalData.items())
        )

        # self.log.debug("Original Data Items: %s" %self.originalData.items())

        for shape, data in self.originalData.items():
            if progress.is_cancelled():
                raise Exception("Cancelled by user")
            scene_hook = data["in"].split(".")[0] if data["in"] else None
            if data["type"] == "combination":
                print("debug")
                print(shape)
                print(data)
                scene_hooks = [
                    self.originalData[x]["in"]
                    for x in data["combinations"]
                    if self.originalData[x]["connected"]
                ]
            else:
                scene_hooks = [data["in"]] if data["connected"] else []

            delta_shape = None
            if self.correctives:
                dif_list = list(
                    self._get_difference(
                        self.demData["meshTransform"],
                        self.trainingData["mesh"],
                        at_time=data["timeGap"][-1],
                    )
                )
                std_deviation = round(get_std_deviation(dif_list), 3)
                self.log.info("{0} deviation value => {1}".format(shape, std_deviation))
                if self.correctiveThreshold < std_deviation:
                    self.log.info("{0} has a corrective shape!".format(shape))
                    original_shape = transform.duplicate(
                        self.trainingData["mesh"],
                        at_time=data["timeGap"][-1],
                        name="%s_orig_DUP" % shape,
                    )
                    dem_shape = transform.duplicate(
                        self.demData["meshTransform"],
                        at_time=data["timeGap"][-1],
                        name="%s_dem_DUP" % shape,
                    )
                    delta_shape = self._create_delta(
                        neutral=neutral_shape,
                        non_sculpted=dem_shape,
                        sculpted=original_shape,
                        name="%s_delta" % shape,
                    )

                    for shp in [original_shape, dem_shape, delta_shape]:
                        if functions.get_parent(shp) != temp_grp:
                            cmds.parent(shp, temp_grp)
                else:
                    delta_shape = None
            else:
                delta_shape = None

            shape_obj = Shape(
                name=shape,
                jointify_node=jointify_node,
                duration=data["timeGap"][1] - data["timeGap"][0],
                combination_of=data["combinations"],
                hook_attrs=scene_hooks,
                delta_shape=delta_shape,
                corrective_bs=self.correctiveBs,
            )
            # create a driver for each active bone object
            for bone_obj in bone_objects:
                # self.log.debug("bone_obj: %s" %bone_obj)
                if bone_obj.is_active(time_gap=data["timeGap"]):
                    drv_obj = Driver(
                        name="drv",
                        bone=bone_obj,
                        time_gap=data["timeGap"],
                        parent_node=drivers_grp,
                    )
                    drv_obj.copy_keys()
                    shape_obj.add_driver(drv_obj)
            shape_objects.append(shape_obj)
            progress.update()
            # self.log.debug("lastSuccess: %s" %shape)

        progress.close()

        progress = Progressbar(
            title="Making Connections ...", max_value=len(shape_objects)
        )
        for shape_obj in shape_objects:
            if progress.is_cancelled():
                raise Exception("Cancelled by user")
            # self.log.debug("shape_obj: %s" %shape_obj._name)
            shape_obj.make_connections()
            progress.update()
            # cmds.progressBar(gMainProgressBar, edit=True, step=1)
        progress.close()

        # post cleanup

        # delete the fbx and alembic files
        ###

        # delete the blendshape and transfer the skin weights to the original
        cmds.currentTime(0)
        cmds.refresh()
        functions.delete_object(self.blendshapeNode)

        # skinTransfer.skinTransfer(source=self.demData["meshTransform"], target=self.trainingData["mesh"])
        # activate the skincluster
        cmds.setAttr("%s.nodeState" % jointify_sc, 0)
        functions.delete_object(self.demData["meshTransform"])
        functions.delete_object(temp_grp)

        if self.parent_to_roots:
            for jnt in root_joints_data.keys():
                parent_jnt = jnt.replace("jntfRoot_", "")
                cmds.parent(jnt, parent_jnt)

        # rename all the dembones joints so they wont clash with other jointifies
        for bone in bone_objects:
            bone.name = "{0}_{1}".format(self.blendshapeNode, bone.name)

        end_time = time.time()
        self.log.info("Connections created in %s seconds" % (end_time - start_time))

    @staticmethod
    def _create_delta(neutral, non_sculpted, sculpted, name="delta_shape"):
        stack = transform.duplicate(neutral, name=name)
        temp_bs_node = cmds.blendShape(
            [non_sculpted, sculpted], stack, w=[(0, -1), (1, 1)]
        )
        cmds.delete(stack, ch=True)
        return stack

    @staticmethod
    def _get_difference(node_a, node_b, threshold=0.001, at_time=None):
        if at_time:
            cmds.currentTime(at_time)
        a_vertices = api.get_all_vertices(node_a)
        b_vertices = api.get_all_vertices(node_b)
        for a, b in zip(a_vertices, b_vertices):
            d = a.distanceTo(b)
            if d > threshold:
                yield (d)

    # TODO move the validations to validate module
    @staticmethod
    def _check_plugins():
        if not cmds.pluginInfo("AbcExport", l=True, q=True):
            try:
                cmds.loadPlugin("AbcExport")
            except:
                msg = "Alembic Export Plugin cannot be initialized."
                cmds.confirmDialog(title="Plugin Error", message=msg)
                raise Exception(msg)

        if not cmds.pluginInfo("AbcImport", l=True, q=True):
            try:
                cmds.loadPlugin("AbcImport")
            except:
                msg = "Alembic Import Plugin cannot be initialized."
                cmds.confirmDialog(title="Plugin Error", message=msg)
                raise Exception(msg)

        if not cmds.pluginInfo("fbxmaya", l=True, q=True):
            try:
                cmds.loadPlugin("fbxmaya")
            except:
                msg = "FBX Plugin cannot be initialized."
                cmds.confirmDialog(title="Plugin Error", message=msg)
                raise Exception(msg)

    @staticmethod
    def _get_dem_bones():
        """Checks the dem bones executables"""
        folder = os.path.split(os.path.realpath(__file__))[0]
        current_os = platform.system()

        if current_os == "Windows":
            executable = os.path.join(folder, "dembones", current_os, "DemBones.exe")
        elif current_os == "Linux" or os == "MacOs":
            # executable = os.path.join(folder, "dembones", current_os, "DemBones")
            try:
                v = subprocess.call(
                    ["DemBones", "--version"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                return "DemBones"
            except OSError:
                return False

        else:
            msg = "Unknown Operating System"
            cmds.confirmDialog(title="OS Error", message=msg)
            raise Exception(msg)

        if not os.path.isfile(executable):
            msg = "Dem-Bones executable cannot be found (%s)" % executable
            cmds.confirmDialog(title="Executable Error", message=msg)
            raise Exception(msg)

        return executable

    @staticmethod
    def _is_moving(
        obj, time_gap, translate_threshold=0.01, rotate_threshold=0.5, decimal=3
    ):
        """Checks if the object is moving between the given time gap"""

        def get_std_deviation(value_list):
            avg = sum(value_list) / len(value_list)
            var = sum((x - avg) ** 2 for x in value_list) / len(value_list)
            std = var**0.5
            return std

        for attr in "xyz":
            val_list = cmds.keyframe(
                "%s.t%s" % (obj, attr), q=True, valueChange=True, t=tuple(time_gap)
            )
            deviation = round(get_std_deviation(val_list), decimal)
            # print("t%s" %attr, deviation)
            if deviation > translate_threshold:
                return True
        for attr in "xyz":
            val_list = cmds.keyframe(
                "%s.r%s" % (obj, attr), q=True, valueChange=True, t=tuple(time_gap)
            )
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

    @staticmethod
    def get_inbetween_values(blendshape_node, target_name):
        """Returns percentages of inbetween targets. If there are no inbetweens, returns [100]"""

        # get the bs api mobject
        bs_sel = om.MSelectionList()
        bs_sel.add(blendshape_node)
        bs_mobj = om.MObject()
        bs_sel.getDependNode(0, bs_mobj)

        # get affected shapes api MObject
        mesh_name = cmds.deformer(blendshape_node, q=True, geometry=True)[0]
        mesh_sel = om.MSelectionList()
        mesh_sel.add(mesh_name)
        mesh_dag = om.MDagPath()
        mesh_mobj = om.MObject()
        mesh_sel.getDagPath(0, mesh_dag)
        mesh_sel.getDependNode(0, mesh_mobj)
        # mesh_mfnmesh = om.MFnMesh(mesh_dag)

        # function set for Blendshape
        m_bs_func = oma.MFnBlendShapeDeformer(bs_mobj)

        # find the target index from name
        attr = blendshape_node + ".w[{}]"
        weightCount = cmds.blendShape(blendshape_node, q=True, wc=True)
        for index in range(weightCount):
            if cmds.aliasAttr(attr.format(index), q=True) == target_name:
                target_index = index
                break
        if target_index == None:
            raise Exception("Target name cannot be found in the blendshape node")

        target_index = deformers.get_bs_index_by_name(blendshape_node, target_name)

        # get the target item index list
        m_target_arr = om.MIntArray()
        m_bs_func.targetItemIndexList(target_index, mesh_mobj, m_target_arr)

        return [int((x - 5000) / 10.0) for x in m_target_arr]

    def _get_shape_duration(self, blendshape_node, target_name):
        """
        Calculates the most optimized duration for the shapes which contains in-betweens
        """

        # TODO: test GCD with python 3.x

        inbetween_percentages = self.get_inbetween_values(blendshape_node, target_name)

        if len(inbetween_percentages) == 1:  # means this shape has no inbetweens
            return 1

        # calculate the closest keyframe range
        greatest_common_dividier = functools.reduce(gcd, inbetween_percentages)

        # if the GCD is too low, cap it with 10 frames
        greatest_common_dividier = (
            10 if greatest_common_dividier < 10 else greatest_common_dividier
        )

        keyframe_range = [
            int(x / float(greatest_common_dividier)) for x in inbetween_percentages
        ]
        return keyframe_range[-1]


class Progressbar(object):
    def __init__(self, title="", max_value=100):
        super(Progressbar, self).__init__()
        self.gMainProgressBar = mel.eval("$tmp = $gMainProgressBar")
        cmds.progressBar(
            self.gMainProgressBar,
            edit=True,
            beginProgress=True,
            isInterruptable=True,
            status="%s" % title,
            maxValue=max_value,
        )

    def update(self, step=1):
        cmds.progressBar(self.gMainProgressBar, edit=True, step=step)

    def close(self):
        cmds.progressBar(self.gMainProgressBar, edit=True, endProgress=True)

    def is_cancelled(self):
        if cmds.progressBar(self.gMainProgressBar, query=True, isCancelled=True):
            return True
        else:
            return False
