from maya import cmds
import maya.api.OpenMaya as om

from trigger.library import functions, joint, deformers
from trigger.library import naming
from trigger.library import attribute
from trigger.library import api
from trigger.objects.controller import Controller
from trigger.modules import _module

from trigger.core import filelog

log = filelog.Filelog(logname=__name__, filename="trigger_log")

LIMB_DATA = {
    "members": ["TentacleRoot", "Tentacle", "TentacleEnd"],
    "properties": [
        {
            "attr_name": "contRes",
            "nice_name": "Ctrl_Res",
            "attr_type": "long",
            "min_value": 1,
            "max_value": 9999,
            "default_value": 5,
        },
        {
            "attr_name": "jointRes",
            "nice_name": "Joint_Res",
            "attr_type": "long",
            "min_value": 1,
            "max_value": 9999,
            "default_value": 25,
        },
        {
            "attr_name": "deformerRes",
            "nice_name": "Deformer_Resolution",
            "attr_type": "long",
            "min_value": 1,
            "max_value": 9999,
            "default_value": 25,
        },
        {
            "attr_name": "dropoff",
            "nice_name": "Drop_Off",
            "attr_type": "float",
            "min_value": 0.1,
            "max_value": 5.0,
            "default_value": 1.0,
        },
    ],
    "multi_guide": "Tentacle",
    "sided": True,
}


class Tentacle(_module.ModuleCore):
    def __init__(self, build_data=None, inits=None):
        super(Tentacle, self).__init__()
        if build_data:
            self.tentacleRoot = build_data.get("TentacleRoot")
            self.tentacles = build_data.get("Tentacle")
            self.inits = [self.tentacleRoot] + self.tentacles
        elif inits:
            if len(inits) < 2:
                cmds.error("Tentacle setup needs at least 2 initial joints")
                return
            self.inits = inits
        else:
            log.error("Class needs either build_data or inits to be constructed")

        # get distances

        # get positions

        self.rootPos = api.get_world_translation(self.inits[0])

        # initialize coordinates
        self.up_axis, self.mirror_axis, self.look_axis = joint.get_rig_axes(
            self.inits[0]
        )

        # get the properties from the root
        self.useRefOrientation = cmds.getAttr("%s.useRefOri" % self.inits[0])
        self.controller_resolution = float(cmds.getAttr("%s.contRes" % self.inits[0]))
        self.jointRes = float(cmds.getAttr("%s.jointRes" % self.inits[0]))
        self.deformerRes = float(cmds.getAttr("%s.deformerRes" % self.inits[0]))
        self.dropoff = float(cmds.getAttr("%s.dropoff" % self.inits[0]))
        self.side = joint.get_joint_side(self.inits[0])
        self.sideMult = -1 if self.side == "R" else 1

        # initialize suffix
        self.module_name = naming.unique_name(
            cmds.getAttr("%s.moduleName" % self.inits[0])
        )

        # module variables
        self.totalLength = 0
        self.contJointsList = None
        self.guideJoints = None
        self.wrapScaleJoint = None
        self.cont_special = None
        self.cont_fk_list = []
        self.cont_twk_list = []

    def create_joints(self):
        cmds.select(deselect=True)
        self.limbPlug = cmds.joint(
            name=naming.parse([self.module_name, "plug"], suffix="j"),
            position=self.rootPos,
            radius=3,
        )
        # Make a straight line from inits joints (like in the twistSpline)
        # calculate the necessary distance for the joints

        cont_distances = []
        ctrl_distance = 0
        for i in range(0, len(self.inits)):
            if i == 0:
                tmin = 0
            else:
                tmin = i - 1
            current_joint_length = functions.get_distance(
                self.inits[i], self.inits[tmin]
            )
            ctrl_distance = current_joint_length + ctrl_distance
            self.totalLength += current_joint_length
            # this list contains distance between each control point
            cont_distances.append(ctrl_distance)
        end_vc = om.MVector(
            self.rootPos.x, (self.rootPos.y + self.totalLength), self.rootPos.z
        )
        split_vc = end_vc - self.rootPos

        # Create Control Joints
        self.contJointsList = []
        cmds.select(deselect=True)
        for index in range(0, len(cont_distances)):
            ctrl_vc = split_vc.normal() * cont_distances[index]
            place = self.rootPos + ctrl_vc
            jnt = cmds.joint(
                position=place,
                name=naming.parse([self.module_name, "driver", index], suffix="j"),
                radius=5,
                orientation=(90, 0, 90),
            )
            self.contJointsList.append(jnt)
            cmds.select(deselect=True)

        # Create temporaray Guide Joints
        cmds.select(deselect=True)
        self.guideJoints = [
            cmds.joint(position=api.get_world_translation(i)) for i in self.inits
        ]
        # orientations
        if not self.useRefOrientation:
            joint.orient_joints(
                self.guideJoints,
                world_up_axis=self.up_axis,
                up_axis=(0, 1, 0),
                reverse_aim=self.sideMult,
                reverse_up=self.sideMult,
            )
        else:
            for x in range(len(self.guideJoints)):
                functions.align_to(
                    self.guideJoints[x], self.inits[x], position=True, rotation=True
                )
                cmds.makeIdentity(self.guideJoints[x], apply=True)

        cmds.select(deselect=True)
        self.wrapScaleJoint = cmds.joint(
            name=naming.parse([self.module_name, "wrapScale"], suffix="j")
        )

        cmds.parent(self.contJointsList, self.scaleGrp)
        cmds.parent(self.wrapScaleJoint, self.scaleGrp)

        attribute.drive_attrs(
            "%s.rigVis" % self.scaleGrp, ["%s.v" % x for x in self.contJointsList]
        )

        cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % self.wrapScaleJoint)

    def create_controllers(self):
        # specialController
        icon_scale = functions.get_distance(self.inits[0], self.inits[1]) / 3
        self.cont_special = Controller(
            name=naming.parse([self.module_name, "special"], suffix="cont"),
            shape="Looper",
            scale=(icon_scale, icon_scale, icon_scale),
            side=self.side,
            tier="primary",
        )
        self.controllers.append(self.cont_special)
        functions.align_and_aim(
            self.cont_special.name,
            target_list=[self.inits[0]],
            aim_target_list=[self.inits[-1]],
            up_vector=self.up_axis,
            rotate_offset=(90, 0, 0),
        )
        move_pos = om.MVector(self.up_axis) * (icon_scale * 2.0)
        # cmds.move(self.cont_special, om.MVector(self.up_axis) *(iconScale*2), r=True)
        cmds.move(
            move_pos[0], move_pos[1], move_pos[2], self.cont_special.name, relative=True
        )

        cont_special_ore = self.cont_special.add_offset("ORE")

        # seperator - curl
        cmds.addAttr(
            self.cont_special.name,
            shortName="curlSeperator",
            attributeType="enum",
            enumName="----------",
            keyable=True,
        )
        cmds.setAttr("%s.curlSeperator" % self.cont_special.name, lock=True)

        cmds.addAttr(
            self.cont_special.name,
            shortName="curl",
            longName="Curl",
            defaultValue=0.0,
            minValue=-10.0,
            maxValue=10.0,
            attributeType="float",
            keyable=True,
        )
        cmds.addAttr(
            self.cont_special.name,
            shortName="curlSize",
            longName="Curl_Size",
            defaultValue=1.0,
            attributeType="float",
            keyable=True,
        )

        cmds.addAttr(
            self.cont_special.name,
            shortName="curlAngle",
            longName="Curl_Angle",
            defaultValue=1.0,
            attributeType="float",
            keyable=True,
        )
        cmds.addAttr(
            self.cont_special.name,
            shortName="curlDirection",
            longName="Curl_Direction",
            defaultValue=0.0,
            attributeType="float",
            keyable=True,
        )

        cmds.addAttr(
            self.cont_special.name,
            shortName="curlShift",
            longName="Curl_Shift",
            defaultValue=0.0,
            attributeType="float",
            keyable=True,
        )

        # seperator - twist
        cmds.addAttr(
            self.cont_special.name,
            shortName="twistSeperator",
            attributeType="enum",
            enumName="----------",
            keyable=True,
        )
        cmds.setAttr("%s.twistSeperator" % self.cont_special.name, lock=True)

        cmds.addAttr(
            self.cont_special.name,
            shortName="twistAngle",
            longName="Twist_Angle",
            defaultValue=0.0,
            attributeType="float",
            keyable=True,
        )
        cmds.addAttr(
            self.cont_special.name,
            shortName="twistSlide",
            longName="Twist_Slide",
            defaultValue=0.0,
            attributeType="float",
            keyable=True,
        )
        cmds.addAttr(
            self.cont_special.name,
            shortName="twistArea",
            longName="Twist_Area",
            defaultValue=1.0,
            attributeType="float",
            keyable=True,
        )

        # seperator - sine
        cmds.addAttr(
            self.cont_special.name,
            shortName="sineSeperator",
            attributeType="enum",
            enumName="----------",
            keyable=True,
        )
        cmds.setAttr("%s.sineSeperator" % self.cont_special.name, lock=True)
        cmds.addAttr(
            self.cont_special.name,
            shortName="sineAmplitude",
            longName="Sine_Amplitude",
            defaultValue=0.0,
            attributeType="float",
            keyable=True,
        )
        cmds.addAttr(
            self.cont_special.name,
            shortName="sineWavelength",
            longName="Sine_Wavelength",
            defaultValue=1.0,
            attributeType="float",
            keyable=True,
        )
        cmds.addAttr(
            self.cont_special.name,
            shortName="sineDropoff",
            longName="Sine_Dropoff",
            defaultValue=0.0,
            attributeType="float",
            keyable=True,
        )
        cmds.addAttr(
            self.cont_special.name,
            shortName="sineSlide",
            longName="Sine_Slide",
            defaultValue=0.0,
            attributeType="float",
            keyable=True,
        )
        cmds.addAttr(
            self.cont_special.name,
            shortName="sineArea",
            longName="Sine_area",
            defaultValue=1.0,
            attributeType="float",
            keyable=True,
        )
        cmds.addAttr(
            self.cont_special.name,
            shortName="sineDirection",
            longName="Sine_Direction",
            defaultValue=0.0,
            attributeType="float",
            keyable=True,
        )

        cmds.addAttr(
            self.cont_special.name,
            shortName="sineAnimate",
            longName="Sine_Animate",
            defaultValue=0.0,
            attributeType="float",
            keyable=True,
        )

        for j in range(len(self.guideJoints)):
            s = cmds.getAttr("%s.tx" % self.guideJoints[j]) / 3
            s = icon_scale if s == 0 else s
            scale_twk = (s, s, s)
            cont_twk = Controller(
                name=naming.parse([self.module_name, "tweak", j], suffix="cont"),
                shape="Circle",
                scale=scale_twk,
                normal=self.mirror_axis,
                side=self.side,
                tier="primary",
            )

            functions.align_to_alter(cont_twk.name, self.guideJoints[j], mode=2)
            cont_twk_off = cont_twk.add_offset("OFF")
            _cont_twk_ore = cont_twk.add_offset("ORE")
            self.cont_twk_list.append(cont_twk)

            scale_fk = (s * 1.2, s * 1.2, s * 1.2)
            cont_fk = Controller(
                name=naming.parse([self.module_name, "FK", j], suffix="cont"),
                shape="Ngon",
                scale=scale_fk,
                normal=self.mirror_axis,
                side=self.side,
                tier="primary",
            )
            functions.align_to_alter(cont_fk.name, self.guideJoints[j], mode=2)
            cont_fk_off = cont_fk.add_offset("OFF")
            _cont_fk_ore = cont_fk.add_offset("ORE")
            self.cont_fk_list.append(cont_fk)

            cmds.parent(cont_twk_off, cont_fk.name)
            if not j == 0:
                cmds.parent(cont_fk_off, self.cont_fk_list[j - 1].name)
            else:
                cmds.parent(cont_fk_off, self.scaleGrp)

        self.controllers.extend(self.cont_fk_list)
        self.controllers.extend(self.cont_twk_list)

        cmds.parent(cont_special_ore, self.cont_fk_list[0].name)

        attribute.drive_attrs(
            "%s.contVis" % self.scaleGrp, ["%s.v" % x.name for x in self.cont_twk_list]
        )
        attribute.drive_attrs(
            "%s.contVis" % self.scaleGrp, ["%s.v" % x.name for x in self.cont_fk_list]
        )

    def create_ik_setup(self):
        # Create the Base Nurbs Plane (npBase)
        ribbon_length = functions.get_distance(
            self.contJointsList[0], self.contJointsList[-1]
        )

        np_base = cmds.nurbsPlane(
            axis=(0, 1, 0),
            patchesU=int(self.controller_resolution),
            patchesV=1,
            width=ribbon_length,
            lengthRatio=(1.0 / ribbon_length),
            name=naming.parse([self.module_name, "npBase"], suffix="surf"),
        )[0]
        cmds.rebuildSurface(
            np_base,
            constructionHistory=True,
            replaceOriginal=True,
            rebuildType=0,
            endKnots=1,
            keepRange=2,
            keepControlPoints=False,
            keepCorners=False,
            spansU=5,
            degreeU=3,
            spansV=1,
            degreeV=1,
            tolerance=0,
            fitRebuild=0,
            direction=1,
        )
        functions.align_and_aim(
            np_base,
            target_list=[self.contJointsList[0], self.contJointsList[-1]],
            aim_target_list=[self.contJointsList[-1]],
            up_vector=self.up_axis,
        )

        # Duplicate the Base Nurbs Plane as joint Holder (npJDefHolder)
        np_jdef_holder = cmds.nurbsPlane(
            axis=(0, 1, 0),
            patchesU=int(self.deformerRes),
            patchesV=1,
            width=ribbon_length,
            lengthRatio=(1.0 / ribbon_length),
            name=naming.parse([self.module_name, "npJointHolder"], suffix="surf"),
        )[0]
        cmds.rebuildSurface(
            np_jdef_holder,
            constructionHistory=True,
            replaceOriginal=True,
            rebuildType=0,
            endKnots=1,
            keepRange=2,
            keepControlPoints=False,
            keepCorners=False,
            spansU=5,
            degreeU=3,
            spansV=1,
            degreeV=1,
            tolerance=0,
            fitRebuild=0,
            direction=1,
        )
        functions.align_and_aim(
            np_jdef_holder,
            target_list=[self.contJointsList[0], self.contJointsList[-1]],
            aim_target_list=[self.contJointsList[-1]],
            up_vector=self.up_axis,
        )

        # Create the follicles on the npJDefHolder
        np_jdef_holder_shape = functions.get_shapes(np_jdef_holder)[0]
        follicle_list = []
        for idx in range(0, int(self.jointRes)):
            follicle = cmds.createNode(
                "follicle",
                name=naming.parse([self.module_name, idx], suffix="follicle"),
            )
            follicle_transform = functions.get_parent(follicle)
            cmds.connectAttr(
                "%s.local" % np_jdef_holder_shape, "%s.inputSurface" % follicle
            )
            cmds.connectAttr(
                "%s.worldMatrix[0]" % np_jdef_holder_shape,
                "%s.inputWorldMatrix" % follicle,
            )
            cmds.connectAttr(
                "%s.outRotate" % follicle, "%s.rotate" % follicle_transform
            )
            cmds.connectAttr(
                "%s.outTranslate" % follicle, "%s.translate" % follicle_transform
            )
            cmds.setAttr("%s.parameterV" % follicle, 0.5)
            cmds.setAttr(
                "%s.parameterU" % follicle,
                (
                    (1.0 / self.jointRes)
                    + (float(idx) / self.jointRes)
                    - ((1.0 / self.jointRes) / 2.0)
                ),
            )
            attribute.lock_and_hide(
                follicle_transform, ["tx", "ty", "tz", "rx", "ry", "rz"], hide=False
            )
            follicle_list.append(follicle)

            j_def = cmds.joint(
                name=naming.parse([self.module_name, idx], suffix="jDef")
            )
            cmds.joint(j_def, exists=True, zeroScaleOrient=True, orientJoint="zxy")
            self.deformerJoints.append(j_def)
            self.sockets.append(j_def)
            cmds.parent(follicle_transform, self.nonScaleGrp)
            cmds.scaleConstraint(self.scaleGrp, follicle_transform, maintainOffset=True)

        # create follicles for scaling calculations
        follicle_sca_list = []
        counter = 0
        for index in range(int(self.jointRes)):
            s_follicle = cmds.createNode(
                "follicle",
                name=naming.parse([self.module_name, "SCA", index], suffix="follicle"),
            )
            s_follicle_transform = functions.get_parent(s_follicle)
            cmds.connectAttr(
                "%s.local" % np_jdef_holder_shape, "%s.inputSurface" % s_follicle
            )
            cmds.connectAttr(
                "%s.worldMatrix[0]" % np_jdef_holder_shape,
                "%s.inputWorldMatrix" % s_follicle,
            )
            cmds.connectAttr(
                "%s.outRotate" % s_follicle, "%s.rotate" % s_follicle_transform
            )
            cmds.connectAttr(
                "%s.outTranslate" % s_follicle, "%s.translate" % s_follicle_transform
            )

            cmds.setAttr("%s.parameterV" % s_follicle, 0.0)
            cmds.setAttr(
                "%s.parameterU" % s_follicle,
                (
                    (1 / self.jointRes)
                    + (index / self.jointRes)
                    - ((1 / self.jointRes) / 2)
                ),
            )
            attribute.lock_and_hide(
                s_follicle_transform, ["tx", "ty", "tz", "rx", "ry", "rz"], hide=False
            )
            follicle_sca_list.append(s_follicle)
            cmds.parent(s_follicle_transform, self.nonScaleGrp)
            # create distance node
            dist_node = cmds.createNode(
                "distanceBetween",
                name=naming.parse([self.module_name, "fol", index], suffix="distance"),
            )
            cmds.connectAttr(
                "%s.outTranslate" % follicle_list[counter], "%s.point1" % dist_node
            )
            cmds.connectAttr("%s.outTranslate" % s_follicle, "%s.point2" % dist_node)

            multiplier = cmds.createNode(
                "multDoubleLinear",
                name=naming.parse([self.module_name, "fol", index], suffix="mult"),
            )
            cmds.connectAttr("%s.distance" % dist_node, "%s.input1" % multiplier)
            cmds.setAttr("%s.input2" % multiplier, 2)

            global_divide = cmds.createNode(
                "multiplyDivide",
                name=naming.parse([self.module_name, "globalDiv", index], suffix="div"),
            )
            cmds.setAttr("%s.operation" % global_divide, 2)
            cmds.connectAttr("%s.output" % multiplier, "%s.input1X" % global_divide)
            cmds.connectAttr("%s.scaleX" % self.scaleGrp, "%s.input2X" % global_divide)

            cmds.connectAttr(
                "%s.outputX" % global_divide, "%s.scaleX" % self.deformerJoints[counter]
            )
            cmds.connectAttr(
                "%s.outputX" % global_divide, "%s.scaleY" % self.deformerJoints[counter]
            )
            cmds.connectAttr(
                "%s.outputX" % global_divide, "%s.scaleZ" % self.deformerJoints[counter]
            )
            counter += 1

        # Duplicate it 3 more times for deformation targets (npDeformers, npTwist, npSine)
        np_deformers = cmds.duplicate(
            np_jdef_holder,
            name=naming.parse([self.module_name, "npDeformers"], suffix="surf"),
        )[0]
        cmds.move(0, self.totalLength / 2, 0, np_deformers)
        cmds.rotate(
            0,
            0,
            90,
            np_deformers,
        )

        # Create Blendshape node between np_jDefHolder and deformation targets
        _np_blend = cmds.blendShape(np_deformers, np_jdef_holder, weight=(0, 1))

        # Wrap npjDefHolder to the Base Plane
        # np_wrap, np_wrap_geo = self.createWrap(np_base, np_jdef_holder, weightThreshold=0.0, maxDistance=50,
        #                                        autoWeightThreshold=False)
        np_wrap, np_wrap_geo = deformers.create_wrap(
            np_base,
            np_jdef_holder,
            weight_threshold=0.0,
            max_distance=50,
            auto_weight_threshold=False,
        )

        max_distance_mult = cmds.createNode(
            "multDoubleLinear",
            name=naming.parse([self.module_name, "npWrap"], suffix="mult"),
        )
        cmds.connectAttr("%s.scaleX" % self.scaleGrp, "%s.input1" % max_distance_mult)
        cmds.setAttr("%s.input2" % max_distance_mult, 50)
        cmds.connectAttr("%s.output" % max_distance_mult, "%s.maxDistance" % np_wrap)

        # make the Wrap node Scale-able with the rig
        cmds.skinCluster(self.wrapScaleJoint, np_wrap_geo, toSelectedBones=True)

        # Create skin cluster
        cmds.skinCluster(
            self.contJointsList, np_base, toSelectedBones=True, dropoffRate=self.dropoff
        )

        # CURL DEFORMER
        curl_deformer = cmds.nonLinear(np_deformers, type="bend", curvature=1500)
        curl_loc = cmds.spaceLocator(
            name=naming.parse([self.module_name, "curl"], suffix="loc")
        )[0]
        cmds.parent(curl_deformer[1], curl_loc)
        cmds.setAttr("%s.lowBound" % curl_deformer[0], -1)
        cmds.setAttr("%s.highBound" % curl_deformer[0], 0)

        cmds.setDrivenKeyframe(
            "%s.curvature" % curl_deformer[0],
            currentDriver="%s.curl" % self.cont_special.name,
            value=0.0,
            driverValue=0.0,
            inTangentType="linear",
            outTangentType="linear",
        )
        cmds.setDrivenKeyframe(
            "%s.curvature" % curl_deformer[0],
            currentDriver="%s.curl" % self.cont_special.name,
            value=1500.0,
            driverValue=0.01,
            inTangentType="linear",
            outTangentType="linear",
        )
        cmds.setDrivenKeyframe(
            "%s.curvature" % curl_deformer[0],
            currentDriver="%s.curl" % self.cont_special.name,
            value=-1500.0,
            driverValue=-0.01,
            inTangentType="linear",
            outTangentType="linear",
        )

        cmds.setDrivenKeyframe(
            "%s.ty" % curl_deformer[1],
            currentDriver="%s.curl" % self.cont_special.name,
            value=0.0,
            driverValue=10.0,
            inTangentType="linear",
            outTangentType="linear",
        )
        cmds.setDrivenKeyframe(
            "%s.ty" % curl_deformer[1],
            currentDriver="%s.curl" % self.cont_special.name,
            value=0.0,
            driverValue=-10.0,
            inTangentType="linear",
            outTangentType="linear",
        )
        cmds.setDrivenKeyframe(
            [
                "%s.sx" % curl_deformer[1],
                "%s.sy" % curl_deformer[1],
                "%s.sz" % curl_deformer[1],
            ],
            currentDriver="%s.curl" % self.cont_special.name,
            value=(self.totalLength * 2),
            driverValue=10.0,
            inTangentType="linear",
            outTangentType="linear",
        )
        cmds.setDrivenKeyframe(
            [
                "%s.sx" % curl_deformer[1],
                "%s.sy" % curl_deformer[1],
                "%s.sz" % curl_deformer[1],
            ],
            currentDriver="%s.curl" % self.cont_special.name,
            value=(self.totalLength * 2),
            driverValue=-10.0,
            inTangentType="linear",
            outTangentType="linear",
        )
        cmds.setDrivenKeyframe(
            "%s.rz" % curl_deformer[1],
            currentDriver="%s.curl" % self.cont_special.name,
            value=4.0,
            driverValue=10.0,
            inTangentType="linear",
            outTangentType="linear",
        )
        cmds.setDrivenKeyframe(
            "%s.rz" % curl_deformer[1],
            currentDriver="%s.curl" % self.cont_special.name,
            value=-4.0,
            driverValue=-10.0,
            inTangentType="linear",
            outTangentType="linear",
        )
        cmds.setDrivenKeyframe(
            "%s.ty" % curl_deformer[1],
            currentDriver="%s.curl" % self.cont_special.name,
            value=self.totalLength,
            driverValue=0.0,
            inTangentType="linear",
            outTangentType="linear",
        )
        cmds.setDrivenKeyframe(
            [
                "%s.sx" % curl_deformer[1],
                "%s.sy" % curl_deformer[1],
                "%s.sz" % curl_deformer[1],
            ],
            currentDriver="%s.curl" % self.cont_special.name,
            value=(self.totalLength / 2),
            driverValue=0.0,
            inTangentType="linear",
            outTangentType="linear",
        )
        cmds.setDrivenKeyframe(
            "%s.rz" % curl_deformer[1],
            currentDriver="%s.curl" % self.cont_special.name,
            value=6.0,
            driverValue=0.01,
            inTangentType="linear",
            outTangentType="linear",
        )
        cmds.setDrivenKeyframe(
            "%s.rz" % curl_deformer[1],
            currentDriver="%s.curl" % self.cont_special.name,
            value=-6.0,
            driverValue=-0.01,
            inTangentType="linear",
            outTangentType="linear",
        )

        # create curl size multipliers

        curl_size_mult_x = cmds.createNode(
            "multDoubleLinear",
            name=naming.parse([self.module_name, "curlSizeMultX"], suffix="mult"),
        )
        curl_size_mult_y = cmds.createNode(
            "multDoubleLinear",
            name=naming.parse([self.module_name, "curlSizeMultY"], suffix="mult"),
        )
        curl_size_mult_z = cmds.createNode(
            "multDoubleLinear",
            name=naming.parse([self.module_name, "curlSizeMultZ"], suffix="mult"),
        )

        curl_angle_mult_z = cmds.createNode(
            "multDoubleLinear",
            name=naming.parse([self.module_name, "curlAngleMultZ"], suffix="mult"),
        )

        curl_shift_add = cmds.createNode(
            "plusMinusAverage",
            name=naming.parse([self.module_name, "curlAddShift"], suffix="pma"),
        )
        cmds.connectAttr(
            "%s.curlShift" % self.cont_special.name, "%s.input1D[0]" % curl_shift_add
        )
        cmds.setAttr("%s.input1D[1]" % curl_shift_add, 180)

        cmds.connectAttr("%s.output1D" % curl_shift_add, "%s.rx" % curl_deformer[1])
        cmds.connectAttr(
            "%s.curlSize" % self.cont_special.name, "%s.input1" % curl_size_mult_x
        )
        cmds.connectAttr(
            "%s.curlSize" % self.cont_special.name, "%s.input1" % curl_size_mult_y
        )
        cmds.connectAttr(
            "%s.curlSize" % self.cont_special.name, "%s.input1" % curl_size_mult_z
        )
        cmds.connectAttr(
            "%s.curlAngle" % self.cont_special.name, "%s.input1" % curl_angle_mult_z
        )

        cmds.connectAttr(
            "%s.output" % cmds.listConnections("%s.sx" % curl_deformer[1])[0],
            "%s.input2" % curl_size_mult_x,
        )
        cmds.connectAttr(
            "%s.output" % cmds.listConnections("%s.sy" % curl_deformer[1])[0],
            "%s.input2" % curl_size_mult_y,
        )
        cmds.connectAttr(
            "%s.output" % cmds.listConnections("%s.sz" % curl_deformer[1])[0],
            "%s.input2" % curl_size_mult_z,
        )
        cmds.connectAttr(
            "%s.output" % cmds.listConnections("%s.rz" % curl_deformer[1])[0],
            "%s.input2" % curl_angle_mult_z,
        )

        cmds.connectAttr(
            "%s.output" % curl_size_mult_x, "%s.sx" % curl_deformer[1], force=True
        )
        cmds.connectAttr(
            "%s.output" % curl_size_mult_y, "%s.sy" % curl_deformer[1], force=True
        )
        cmds.connectAttr(
            "%s.output" % curl_size_mult_z, "%s.sz" % curl_deformer[1], force=True
        )
        cmds.connectAttr(
            "%s.output" % curl_angle_mult_z, "%s.rz" % curl_deformer[1], force=True
        )
        cmds.connectAttr(
            "%s.curlDirection" % self.cont_special.name, "%s.ry" % curl_loc
        )

        # TWIST DEFORMER
        twist_deformer = cmds.nonLinear(np_deformers, type="twist")
        cmds.rotate(0, 0, 0, twist_deformer[1])
        twist_loc = cmds.spaceLocator(
            name=naming.parse([self.module_name, "twist"], suffix="loc")
        )[0]
        cmds.parent(twist_deformer[1], twist_loc)

        # make connections:
        cmds.connectAttr(
            "%s.twistAngle" % self.cont_special.name,
            "%s.endAngle" % twist_deformer[0],
            force=True,
        )
        cmds.connectAttr(
            "%s.twistSlide" % self.cont_special.name, "%s.translateY" % twist_loc
        )
        cmds.connectAttr(
            "%s.twistArea" % self.cont_special.name, "%s.scaleY" % twist_loc
        )

        # SINE DEFORMER
        sine_deformer = cmds.nonLinear(np_deformers, type="sine")
        cmds.rotate(0, 0, 0, sine_deformer[1])
        sine_loc = cmds.spaceLocator(
            name=naming.parse([self.module_name, "sine"], suffix="loc")
        )[0]
        cmds.parent(sine_deformer[1], sine_loc)

        # make connections:
        cmds.connectAttr(
            "%s.sineAmplitude" % self.cont_special.name,
            "%s.amplitude" % sine_deformer[0],
            force=True,
        )
        cmds.connectAttr(
            "%s.sineWavelength" % self.cont_special.name,
            "%s.wavelength" % sine_deformer[0],
            force=True,
        )
        cmds.connectAttr(
            "%s.sineDropoff" % self.cont_special.name,
            "%s.dropoff" % sine_deformer[0],
            force=True,
        )
        cmds.connectAttr(
            "%s.sineAnimate" % self.cont_special.name,
            "%s.offset" % sine_deformer[0],
            force=True,
        )

        cmds.connectAttr(
            "%s.sineSlide" % self.cont_special.name, "%s.translateY" % sine_loc
        )
        cmds.connectAttr("%s.sineArea" % self.cont_special.name, "%s.scaleY" % sine_loc)
        cmds.connectAttr(
            "%s.sineDirection" % self.cont_special.name, "%s.rotateY" % sine_loc
        )

        # TODO WHY THIS OFFSET IS NECESSARY?
        offset_val = (0, 180, 0) if self.sideMult == -1 else (0, 0, 0)
        for j in range(len(self.guideJoints)):
            functions.align_to_alter(
                self.contJointsList[j], self.guideJoints[j], mode=2
            )
            cmds.pointConstraint(
                self.cont_twk_list[j].name, self.contJointsList[j], maintainOffset=False
            )
            cmds.orientConstraint(
                self.cont_twk_list[j].name,
                self.contJointsList[j],
                maintainOffset=False,
                offset=offset_val,
            )

            cmds.scaleConstraint(
                self.cont_twk_list[j].name, self.contJointsList[j], maintainOffset=False
            )

        cmds.parent(np_base, self.nonScaleGrp)
        cmds.parent(np_deformers, self.nonScaleGrp)
        cmds.parent(curl_loc, self.nonScaleGrp)
        cmds.parent(twist_loc, self.nonScaleGrp)
        cmds.parent(sine_loc, self.nonScaleGrp)
        cmds.parent(np_wrap_geo, self.nonScaleGrp)
        cmds.parent(np_jdef_holder, self.scaleGrp)

        nodes_rig_vis = [
            np_base,
            np_jdef_holder,
            np_deformers,
            sine_loc,
            twist_loc,
            curl_loc,
        ]
        attribute.drive_attrs(
            "%s.rigVis" % self.scaleGrp, ["%s.v" % x for x in nodes_rig_vis]
        )
        attribute.drive_attrs(
            "%s.rigVis" % self.scaleGrp, ["%s.v" % x for x in follicle_sca_list]
        )
        attribute.drive_attrs(
            "%s.rigVis" % self.scaleGrp, ["%s.v" % x for x in follicle_list]
        )

    def round_up(self):
        cmds.parentConstraint(self.limbPlug, self.scaleGrp, maintainOffset=False)
        cmds.setAttr("%s.rigVis" % self.scaleGrp, 0)

        _ = [x.lock(["sx", "sy", "sz"]) for x in self.cont_fk_list]
        self.scaleConstraints = [self.scaleGrp]

        cmds.delete(self.guideJoints)

        for cont in self.controllers:
            cont.set_defaults()

    def execute(self):
        # self.createGrp()
        self.create_joints()
        self.create_controllers()
        self.create_ik_setup()
        self.round_up()


class Guides(_module.GuidesCore):
    limb_data = LIMB_DATA

    def __init__(self, *args, **kwargs):
        super(Guides, self).__init__(*args, **kwargs)
        self.segments = kwargs.get(
            "segments", 2
        )  # minimum segments required for the module is 2

    def draw_joints(self):
        r_point_tentacle = om.MVector(0, 14, 0) * self.tMatrix
        if self.side == "C":
            # Guide joint positions for limbs with no side orientation
            n_point_tentacle = om.MVector(0, 14, 10) * self.tMatrix
        else:
            # Guide joint positions for limbs with sides
            n_point_tentacle = (
                om.MVector(10 * self.sideMultiplier, 14, 0) * self.tMatrix
            )

        add_tentacle = (n_point_tentacle - r_point_tentacle) / ((self.segments + 1) - 1)

        # Define the offset vector
        self.offsetVector = (n_point_tentacle - r_point_tentacle).normal()

        # Draw the joints
        for seg in range(self.segments + 1):
            tentacle_jnt = cmds.joint(
                position=(r_point_tentacle + (add_tentacle * seg)),
                name=naming.parse([self.name, seg], side=self.side, suffix="jInit"),
            )
            # Update the guideJoints list
            self.guideJoints.append(tentacle_jnt)

        # set orientation of joints
        joint.orient_joints(
            self.guideJoints,
            world_up_axis=self.upVector,
            up_axis=(0, 1, 0),
            reverse_aim=self.sideMultiplier,
            reverse_up=self.sideMultiplier,
        )

    def define_guides(self):
        joint.set_joint_type(self.guideJoints[0], "TentacleRoot")
        _ = [joint.set_joint_type(jnt, "Tentacle") for jnt in self.guideJoints[1:]]
