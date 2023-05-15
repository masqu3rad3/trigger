from maya import cmds
import maya.api.OpenMaya as om

from trigger.library import functions, joint
from trigger.library import attribute
from trigger.library import naming
from trigger.library import api
# from trigger.library import controllers as ic
from trigger.objects.controller import Controller


class TwistSpline(object):

    def __init__(self):
        self.contCurves_ORE = None
        self.contCurve_Start = None
        self.contCurve_End = None
        self.endLock = None
        self.scaleGrp = None
        self.nonScaleGrp = None
        self.attPassCont = None
        self.defJoints = []
        self.noTouchData = None
        self.moveAxis = None
        self.upAxis = (0.0, 1.0, 0.0)

    def create_t_spline(self, guide_joints, name, cuts=10, dropoff=2, mode="equalDistance", twistType="regular",
                        colorCode=17):
        """
        
        Args:
            guide_joints: (PyNode) Reference Joints to be taken as templates for start/end and controller locations
            name: (String) Naming convention for newly created nodes.
            cuts: (Integer) Determines the resolution of joint chain.
            dropoff: (Float) Drop off value for skin bind between control curve and control joints
            mode: (String) The mode for joint creation. Valid valuer are 'equalDistance' and 'sameDistance'. 
                            If 'equalDistance' The chain joints will be seperated evenly. If 'sameDistance'
                            cuts value will be ignored and reference joint lengths will be used. Default: 'equalDistance'
            twistType: (String) Valid values are 'infinite', 'regular' and 'simple'. 'infinite' will use the awesomeSpline method
                        which will allow 360 degree rotations, but will be problematic if many midcontrollers are present.
                        'regular' mode is better if there are several middle controllers, but the spine cannot turn a full 360
                        without flipping. 'simple' mode is best for tentacles and terminal limbs which twisting will occur only
                        one end of the limb.

        Returns: None

        """

        # self.scaleGrp = cmds.group(name="scaleGrp_%s" % name, empty=True)
        self.scaleGrp = cmds.group(name=naming.parse([name, "scale"], suffix="grp"), empty=True)
        # self.nonScaleGrp = cmds.group(name="nonScaleGrp_%s" % name, empty=True)
        self.nonScaleGrp = cmds.group(name=naming.parse([name, "nonScale"], suffix="grp"), empty=True)

        root_vc = api.get_world_translation(guide_joints[0])
        total_length = 0
        cont_distances = []
        cont_curves = []
        self.contCurves_ORE = []
        ctrl_distance = 0

        # calculate the necessary distance for the joints
        for pole_grp in range(0, len(guide_joints)):
            if pole_grp == 0:
                tmin = 0
            else:
                tmin = pole_grp - 1
            current_joint_length = functions.get_distance(guide_joints[pole_grp], guide_joints[tmin])
            ctrl_distance = current_joint_length + ctrl_distance
            total_length += current_joint_length
            cont_distances.append(ctrl_distance)  # this list contains distance between each control point

        end_vc = om.MVector(root_vc.x, (root_vc.y + total_length), root_vc.z)

        split_vc = end_vc - root_vc
        segment_vc = (split_vc / cuts)
        segment_loc = root_vc + segment_vc
        curve_points = []  # for curve creation
        ik_joints = []
        cmds.select(clear=True)

        # Create IK Joints ORIENTATION - ORIENTATION - ORIENTATION
        curve_type = 3
        if mode == "equalDistance":

            curve_type = 3
            for index in range(cuts + 2):  # iterates one extra to create an additional joint for orientation
                place = root_vc + (segment_vc * index)
                # j = cmds.joint(position=place, name="jIK_%s%i" % (name, index))
                j = cmds.joint(position=place, name=naming.parse([name, "IK", index], suffix="j"))
                if index < (cuts + 1):  # if it is not the extra bone, update the lists
                    ik_joints.append(j)
                    curve_points.append(place)

        elif mode == "sameDistance":
            curve_type = 1
            for index in range(0, len(cont_distances)):
                ctrl_vc = split_vc.normal() * cont_distances[index]
                place = root_vc + ctrl_vc
                # j = cmds.joint(position=place, name="jIK_%s%i" % (name, index), radius=2, orientation=(0, 0, 0))
                j = cmds.joint(position=place, name=naming.parse([name, "IK", index], suffix="j"), radius=2, orientation=(0, 0, 0))
                ik_joints.append(j)
                curve_points.append(place)
        else:
            cmds.error("Mode is not supported - twistSplineClass.py")

        cmds.parent(ik_joints[0], self.nonScaleGrp)

        # ORIENT JOINTS PROPERLY
        joint.orient_joints(ik_joints, world_up_axis=self.upAxis)

        map(lambda x: cmds.setAttr("%s.displayLocalAxis" % x, True), ik_joints)

        # get rid of the extra bone
        dead_bone = cmds.listRelatives(ik_joints[len(ik_joints) - 1], children=True)
        cmds.delete(dead_bone)

        # self.defJoints = cmds.duplicate(ik_joints, name="jDef_%s0" % name)

        _duplicates = cmds.duplicate(ik_joints, renameChildren=True)
        for nmb, jnt in enumerate(_duplicates):
            self.defJoints.append(cmds.rename(jnt, naming.parse([name, nmb], suffix="jDef")))


        # create the controller joints
        cont_joints = []
        cmds.select(clear=True)
        for index in range(len(cont_distances)):
            ctrl_vc = split_vc.normal() * cont_distances[index]
            place = root_vc + ctrl_vc
            # jnt = cmds.joint(position=place, name="jCont_spline_%s%i" % (name, index), radius=5, orientation=(0, 0, 0))
            jnt = cmds.joint(position=place, name=naming.parse([name, "splineDriver", index], suffix="j"), radius=5, orientation=(0, 0, 0))
            cont_joints.append(jnt)

        joint.orient_joints(cont_joints, world_up_axis=self.upAxis)

        cmds.select(clear=True)
        cmds.parent(cont_joints[1:], world=True)

        #############################################

        # create the splineIK for the IK joints
        # # create the spline curve
        # spline_curve = cmds.curve(name="splineCurve_%s" % name, degree=curve_type, point=curve_points)
        spline_curve = cmds.curve(name=naming.parse([name, "spline"], suffix="crv"), degree=curve_type, point=curve_points)
        # # create spline IK
        spline_ik = cmds.ikHandle(solver="ikSplineSolver", createCurve=False, curve=spline_curve,
                                  startJoint=ik_joints[0],
                                  endEffector=ik_joints[len(self.defJoints) - 1], weight=1.0)
        # # skin bind control joints
        cmds.select(cont_joints)
        cmds.select(spline_curve, add=True)
        cmds.skinCluster(dropoffRate=dropoff, toSelectedBones=True)

        # create the RP Solver IKs for the jDef joints
        pole_groups = []
        rp_handles = []

        if twistType == "infinite":
            for pole_grp in range(0, len(self.defJoints)):
                if pole_grp < len(self.defJoints) - 1:
                    rp = cmds.ikHandle(startJoint=self.defJoints[pole_grp], endEffector=self.defJoints[pole_grp + 1],
                                       # name="tSpine_RP_%s%i" % (name, pole_grp),
                                       name=naming.parse([name, "RP", pole_grp], suffix="IKHandle"),
                                       solver="ikRPsolver")
                    rp_handles.append(rp[0])
                    # # create locator and group for each rp
                    # loc = cmds.spaceLocator(name="tSpinePoleLoc_%s%i" % (name, pole_grp))[0]
                    loc = cmds.spaceLocator(name=naming.parse([name, "tSpinePole", pole_grp], suffix="loc"))[0]
                    loc_pos = functions.create_offset_group(loc, "POS")
                    loc_off = functions.create_offset_group(loc, "OFF")

                    functions.align_to_alter(loc_pos, self.defJoints[pole_grp], mode=2)
                    cmds.setAttr("%s.tz" % loc, 5)

                    # parent locator groups, pole vector locators >> RP Solvers, point constraint RP Solver >> IK Joints
                    cmds.parent(loc_pos, ik_joints[pole_grp])
                    pole_groups.append(loc_off)
                    cmds.poleVectorConstraint(loc, rp[0])
                    cmds.pointConstraint(ik_joints[pole_grp + 1], rp[0])
                    cmds.parent(rp[0], self.nonScaleGrp)

            # # connect the roots of two chains
            cmds.pointConstraint(ik_joints[0], self.defJoints[0], maintainOffset=False)

        else:
            for pole_grp in range(0, len(self.defJoints)):
                cmds.parentConstraint(ik_joints[pole_grp], self.defJoints[pole_grp])

            # adjust the twist controls for regular IK
            cmds.setAttr("{}.dTwistControlEnable".format(spline_ik[0]), 1)
            cmds.setAttr("{}.dWorldUpType".format(spline_ik[0]), 4)
            cmds.setAttr("{}.dWorldUpAxis".format(spline_ik[0]), 1)
            cmds.setAttr("{}.dWorldUpVectorX".format(spline_ik[0]), 0)
            cmds.setAttr("{}.dWorldUpVectorY".format(spline_ik[0]), 0)
            cmds.setAttr("{}.dWorldUpVectorZ".format(spline_ik[0]), -1)
            cmds.setAttr("{}.dWorldUpVectorEndX".format(spline_ik[0]), 0)
            cmds.setAttr("{}.dWorldUpVectorEndY".format(spline_ik[0]), 0)
            cmds.setAttr("{}.dWorldUpVectorEndZ".format(spline_ik[0]), -1)

            cmds.connectAttr("{}.worldMatrix[0]".format(cont_joints[0]), "{}.dWorldUpMatrix".format(spline_ik[0]))
            cmds.connectAttr("{}.worldMatrix[0]".format(cont_joints[-1]), "{}.dWorldUpMatrixEnd".format(spline_ik[0]))

        # connect rotations of locator groups

        # icon = ic.Icon()

        for jnt in range(0, len(cont_joints)):
            scale_ratio = (total_length / len(cont_joints))
            if jnt != 0 and jnt != (len(cont_joints) - 1):
                # Create control Curve if it is not the first or last control joint
                # cont_curve, dmp = icon.create_icon("Star", icon_name="%s%i_tweak_cont" % (name, jnt),
                #                                    scale=(scale_ratio, scale_ratio, scale_ratio), normal=(1, 0, 0))
                cont_curve = Controller(
                    name=naming.parse([name, jnt, "tweak"], suffix="cont"),
                    shape="Star",
                    scale=(scale_ratio, scale_ratio, scale_ratio),
                    normal=(1, 0, 0),
                    side="center",
                    tier="secondary"
                )
                _cont_curve_name = cont_curve.name # workaround to save some lines
            else:
                # cont_curve = cmds.spaceLocator(name="lockPoint_%s%i" % (name, jnt))[0]
                _cont_curve_name = cmds.spaceLocator(name=naming.parse([name, jnt, "lockPoint"], suffix="loc"))[0]
            functions.align_to_alter(_cont_curve_name, cont_joints[jnt], mode=2)
            cont_curve_ore = functions.create_offset_group(_cont_curve_name, "ORE")
            cmds.parentConstraint(_cont_curve_name, cont_joints[jnt], maintainOffset=False)
            cont_curves.append(_cont_curve_name)
            self.contCurves_ORE.append(cont_curve_ore)

        self.contCurve_Start = cont_curves[0]
        self.contCurve_End = cont_curves[len(cont_curves) - 1]

        if twistType == "infinite":
            # CREATE A TWIST NODE TO BE PASSED. this is the twist driver, connect it to rotation or attributes
            # first make a solid connection for the top and bottom:
            for pole_grp in range(0, len(pole_groups)):
                # if it is the first or the last group
                if pole_grp == 0:
                    cmds.orientConstraint(self.contCurve_Start, pole_groups[pole_grp], maintainOffset=False)
                elif pole_grp == len(pole_groups) - 1:
                    cmds.orientConstraint(self.contCurve_End, pole_groups[pole_grp], maintainOffset=False)
                else:
                    blender = cmds.createNode("blendColors", name="tSplineX_blend_{}".format(*str(pole_grp)))
                    cmds.connectAttr("{}.rotate".format(pole_groups[-1]), "{}.color1".format(blender))
                    cmds.connectAttr("{}.rotate".format(pole_groups[0]), "{}.color2".format(blender))
                    cmds.connectAttr("{}.outputR".format(blender), "{}.rotateX".format(pole_groups[pole_grp]))
                    blend_ratio = (pole_grp + 0.0) / (cuts - 1.0)
                    cmds.setAttr("{}.blender".format(blender), blend_ratio)
        else:
            pass

        # STRETCH and SQUASH
        #
        # Create Stretch and Squash Nodes
        #
        # first controller is the one which holds the attributes to be passed
        self.attPassCont = (cont_curves[0])

        cmds.addAttr(self.attPassCont, shortName='preserveVol', longName='Preserve_Volume', defaultValue=0.0,
                     minValue=0.0, maxValue=1.0, attributeType="double", keyable=True)
        cmds.addAttr(self.attPassCont, shortName='volumeFactor', longName='Volume_Factor', defaultValue=1,
                     attributeType="double", keyable=True)

        cmds.addAttr(self.attPassCont, shortName='stretchy', longName='Stretchyness', defaultValue=1, minValue=0.0,
                     maxValue=1.0, attributeType="double", keyable=True)

        curve_info = cmds.arclen(spline_curve, constructionHistory=True)
        initial_length = cmds.getAttr("%s.arcLength" % curve_info)

        pow_value = 0

        for pole_grp in range(0, len(ik_joints)):
            curve_glob_mult = cmds.createNode("multiplyDivide", name="curveGlobMult_{}".format(name))
            cmds.setAttr("{}.operation".format(curve_glob_mult), 2)
            bone_glob_mult = cmds.createNode("multiplyDivide", name="boneGlobMult_{}".format(name))

            length_mult = cmds.createNode("multiplyDivide", name="length_Multiplier_{}".format(name))
            cmds.setAttr("{}.operation".format(length_mult), 2)

            volume_sw = cmds.createNode("blendColors", name="volumeSw_{}".format(name))
            stretch_sw = cmds.createNode("blendTwoAttr", name="stretchSw_{}".format(name))

            middle_point = (len(ik_joints) * 0.5)
            volume_pow = cmds.createNode("multiplyDivide", name="volume_Power_{}".format(name))
            volume_factor = cmds.createNode("multiplyDivide", name="volume_Factor_{}".format(name))

            cmds.connectAttr("%s.volumeFactor" % self.attPassCont, "%s.input1Y" % volume_factor)
            cmds.connectAttr("%s.volumeFactor" % self.attPassCont, "%s.input1Z" % volume_factor)
            cmds.connectAttr("%s.output" % volume_factor, "%s.input2" % volume_pow)
            cmds.setAttr("%s.operation" % volume_pow, 3)

            # make sure first and last joints preserves the full volume
            if pole_grp == 0 or pole_grp == len(ik_joints) - 1:
                cmds.setAttr("%s.input2Y" % volume_factor, 0)
                cmds.setAttr("%s.input2Z" % volume_factor, 0)
            elif pole_grp <= middle_point:
                pow_value = pow_value - 1
                cmds.setAttr("%s.input2Y" % volume_factor, pow_value)
                cmds.setAttr("%s.input2Z" % volume_factor, pow_value)
            else:
                pow_value = pow_value + 1
                cmds.setAttr("%s.input2Y" % volume_factor, pow_value)
                cmds.setAttr("%s.input2Z" % volume_factor, pow_value)

            cmds.connectAttr("%s.arcLength" % curve_info, "%s.input1X" % curve_glob_mult)
            cmds.setAttr("%s.input[0]" % stretch_sw, initial_length)
            cmds.connectAttr("%s.outputX" % curve_glob_mult, "%s.input[1]" % stretch_sw)
            cmds.connectAttr("%s.stretchy" % self.attPassCont, "%s.attributesBlender" % stretch_sw)
            cmds.connectAttr("%s.sx" % self.scaleGrp, "%s.input2X" % curve_glob_mult)
            cmds.connectAttr("%s.output" % stretch_sw, "%s.input1X" % length_mult)
            cmds.setAttr("%s.input2X" % length_mult, initial_length)
            cmds.connectAttr("%s.outputX" % length_mult, "%s.input1X" % bone_glob_mult)
            cmds.connectAttr("%s.outputX" % length_mult, "%s.input1Y" % volume_pow)
            cmds.connectAttr("%s.outputX" % length_mult, "%s.input1Z" % volume_pow)
            cmds.setAttr("%s.color2G" % volume_sw, 1)
            cmds.setAttr("%s.color2B" % volume_sw, 1)
            cmds.connectAttr("%s.outputY" % volume_pow, "%s.color1G" % volume_sw)
            cmds.connectAttr("%s.outputZ" % volume_pow, "%s.color1B" % volume_sw)
            cmds.connectAttr("%s.outputG" % volume_sw, "%s.input1Y" % bone_glob_mult)
            cmds.connectAttr("%s.outputB" % volume_sw, "%s.input1Z" % bone_glob_mult)
            cmds.connectAttr("%s.sx" % self.scaleGrp, "%s.input2X" % bone_glob_mult)
            cmds.connectAttr("%s.sx" % self.scaleGrp, "%s.input2Y" % bone_glob_mult)
            cmds.connectAttr("%s.sx" % self.scaleGrp, "%s.input2Z" % bone_glob_mult)
            cmds.connectAttr("%s.preserveVol" % self.attPassCont, "%s.blender" % volume_sw)
            cmds.connectAttr("%s.output" % bone_glob_mult, "%s.scale" % ik_joints[pole_grp])
            cmds.connectAttr("%s.output" % bone_glob_mult, "%s.scale" % self.defJoints[pole_grp])

        # Create endLock
        # self.endLock = cmds.spaceLocator(name="endLock_%s" % name)[0]
        self.endLock = cmds.spaceLocator(name=naming.parse([name, "endLock"], suffix="loc"))[0]
        cmds.pointConstraint(self.defJoints[len(self.defJoints) - 1], self.endLock, maintainOffset=False)

        # Move them to original Positions
        for idx in range(len(self.contCurves_ORE)):
            if idx == 0:
                functions.align_to_alter(self.contCurves_ORE[idx], guide_joints[idx], mode=2)
            else:
                functions.align_to_alter(self.contCurves_ORE[idx], guide_joints[idx], mode=0)
                functions.align_to_alter(self.contCurves_ORE[idx], guide_joints[idx - 1], mode=1)

        # GOOD PARENTING
        cmds.parent(cont_joints, self.scaleGrp)
        cmds.parent(spline_ik[0], self.nonScaleGrp)

        # FOOL PROOFING
        for pole_grp in cont_curves:
            attribute.lock_and_hide(pole_grp, ["sx", "sy", "sz", "v"])

        # COLOR CODING
        functions.colorize(cont_curves, colorCode)

        # RETURN
        self.noTouchData = ([spline_curve, spline_ik[0], self.endLock], ik_joints, cont_joints, pole_groups, rp_handles)
