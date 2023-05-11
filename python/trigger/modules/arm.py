from maya import cmds
import maya.api.OpenMaya as om
from trigger.library import functions, joint
from trigger.library import naming
from trigger.library import attribute
from trigger.library import api
from trigger.library import connection
from trigger.library import arithmetic as op
from trigger.objects.ribbon import Ribbon
from trigger.objects.controller import Controller
from trigger.objects import measure
from trigger.library import tools
from trigger.modules import _module

from trigger.core import filelog

LOG = filelog.Filelog(logname=__name__, filename="trigger_log")

LIMB_DATA = {
    "members": ["Collar", "Shoulder", "Elbow", "Hand"],
    "properties": [{"attr_name": "localJoints",
                    "nice_name": "Local_Joints",
                    "attr_type": "bool",
                    "default_value": False},
                   ],
    "multi_guide": None,
    "sided": True,
}


class Arm(_module.ModuleCore):
    def __init__(self, build_data=None, inits=None, *args, **kwargs):
        super(Arm, self).__init__()
        # fool proofing

        # reinitialize the initial Joints
        if build_data:
            self.collar_ref = build_data["Collar"]
            self.shoulder_ref = build_data["Shoulder"]
            self.elbow_ref = build_data["Elbow"]
            self.hand_ref = build_data["Hand"]
        elif inits:
            if len(inits) < 4:
                LOG.error("Missing Joints for Arm Setup", proceed=False)
                return

            if isinstance(inits, dict):
                # reinitialize the dictionary for easy use
                self.collar_ref = inits["Collar"]
                self.shoulder_ref = inits["Shoulder"]
                self.elbow_ref = inits["Elbow"]
                self.hand_ref = inits["Hand"]
            elif isinstance(inits, list):
                self.collar_ref = inits[0]
                self.shoulder_ref = inits[1]
                self.elbow_ref = inits[2]
                self.hand_ref = inits[3]
            else:
                LOG.error("Init joints must be list or dictionary")
                return
        else:
            LOG.error("Class needs either build_data or inits to be constructed")

        self.collar_pos = api.get_world_translation(self.collar_ref)
        self.shoulder_pos = api.get_world_translation(self.shoulder_ref)
        self.elbow_pos = api.get_world_translation(self.elbow_ref)
        self.hand_pos = api.get_world_translation(self.hand_ref)

        # get distances
        self.init_shoulder_dist = functions.get_distance(self.collar_ref, self.shoulder_ref)
        self.init_upper_arm_dist = functions.get_distance(self.shoulder_ref, self.elbow_ref)
        self.init_lower_arm_dist = functions.get_distance(self.elbow_ref, self.hand_ref)

        self.up_axis, self.mirror_axis, self.look_axis = joint.get_rig_axes(self.collar_ref)

        # get the properties from the root
        self.use_ref_orientation = cmds.getAttr("%s.useRefOri" % self.collar_ref)
        self.side = joint.get_joint_side(self.collar_ref)
        self.sideMult = -1 if self.side == "R" else 1
        try:
            self.isLocal = bool(cmds.getAttr("%s.localJoints" % self.collar_ref))
        except ValueError:
            self.isLocal = False

        self.module_name = (naming.unique_name(cmds.getAttr("%s.moduleName" % self.collar_ref)))
        # module variables
        self.shoulderCont = None
        self.handIkCont = None
        self.poleCont = None
        self.poleBridge = None
        self.upArmFkCont = None
        self.lowArmFkCont = None
        self.handFkCont = None
        self.switchFkIkCont = None
        self.midLockCont = None
        self.defMid = None
        self.defStart = None
        self.defEnd = None
        self.midLockBridge_IK = None
        self.midLockBridge_FK = None
        self.startLock = None
        self.startLockOre = None
        self.startLockPos = None
        self.startLockTwist = None
        self.endLock = None
        # self.scaleHook = None
        # self.rigJointsGrp = None
        # self.defJointsGrp = None
        # self.localOffGrp = None
        # self.controllerGrp = None
        # self.contBindGrp = None

        # joints
        self.j_def_collar, self.j_collar_end, self.j_def_elbow = None, None, None
        self.j_ik_orig_up, self.j_ik_orig_low, self.j_ik_orig_low_end = None, None, None
        self.j_ik_sc_up, self.j_ik_sc_low, self.j_ik_sc_low_end = None, None, None
        self.j_ik_rp_up, self.j_ik_rp_low, self.j_ik_rp_low_end = None, None, None
        self.j_fk_up, self.j_fk_low, self.j_fk_low_end = None, None, None
        self.j_def_hand = None

        # session variables
        # self.controllers = []
        # self.sockets = []
        # self.limbGrp = None
        # self.scaleGrp = None
        # self.nonScaleGrp = None
        # self.limbPlug = None
        # self.scaleConstraints = []
        # self.anchors = []
        # self.anchorLocations = []
        # self.deformerJoints = []
        # self.colorCodes = [6, 18]

    def create_groups(self):
        """Create module groups."""

        self.limbGrp = cmds.group(name=naming.parse(self.module_name, suffix="grp"), empty=True)
        self.scaleGrp = cmds.group(name=naming.parse([self.module_name, "scale"], suffix="grp"), empty=True)
        functions.align_to(self.scaleGrp, self.collar_ref, position=True, rotation=False)
        self.nonScaleGrp = cmds.group(name=naming.parse([self.module_name, "nonScale"], suffix="grp"), empty=True)

        cmds.addAttr(self.scaleGrp, attributeType="bool", longName="Control_Visibility", shortName="contVis", defaultValue=True)
        cmds.addAttr(self.scaleGrp, attributeType="bool", longName="Joints_Visibility", shortName="jointVis", defaultValue=True)
        cmds.addAttr(self.scaleGrp, attributeType="bool", longName="Rig_Visibility", shortName="rigVis", defaultValue=False)
        # make the created attributes visible in the channel box
        cmds.setAttr("%s.contVis" % self.scaleGrp, channelBox=True)
        cmds.setAttr("%s.jointVis" % self.scaleGrp, channelBox=True)
        cmds.setAttr("%s.rigVis" % self.scaleGrp, channelBox=True)

        cmds.parent(self.scaleGrp, self.limbGrp)
        cmds.parent(self.nonScaleGrp, self.limbGrp)

        self.localOffGrp = cmds.group(name=naming.parse([self.module_name, "localOffset"], suffix="grp"), empty=True)
        self.controllerGrp = cmds.group(name=naming.parse([self.module_name, "controller"], suffix="grp"), empty=True)
        cmds.parent(self.localOffGrp, self.controllerGrp)
        cmds.parent(self.controllerGrp, self.limbGrp)

        self.contBindGrp = cmds.group(name=naming.parse([self.module_name, "controllerBind"], suffix="grp"), empty=True)
        cmds.parent(self.contBindGrp, self.localOffGrp)

        # scale hook gets the scale value from the bind group but not from the localOffset
        self.scaleHook = cmds.group(name=naming.parse([self.module_name, "scaleHook"], suffix="grp"), empty=True)
        cmds.parent(self.scaleHook, self.limbGrp)
        scale_skips = "xyz" if self.isLocal else ""
        connection.matrixConstraint(self.contBindGrp, self.scaleHook, self.localOffGrp, skipScale=scale_skips)

        self.rigJointsGrp = cmds.group(name=naming.parse([self.module_name, "rigJoints"], suffix="grp"), empty=True)
        self.defJointsGrp = cmds.group(name=naming.parse([self.module_name, "defJoints"], suffix="grp"), empty=True)
        cmds.parent(self.rigJointsGrp, self.limbGrp)
        cmds.parent(self.defJointsGrp, self.limbGrp)

    def create_joints(self):

        # limb plug
        cmds.select(deselect=True)
        self.limbPlug = cmds.joint(name=naming.parse([self.module_name, "plug"], suffix="j"), position=self.collar_pos, radius=3)
        cmds.parent(self.limbPlug, self.limbGrp)
        connection.matrixConstraint(self.limbPlug, self.contBindGrp, maintainOffset=True)
        if self.isLocal:
            connection.matrixConstraint(self.limbPlug, self.localOffGrp, maintainOffset=True)

        # Shoulder Joints
        cmds.select(deselect=True)
        self.j_def_collar = cmds.joint(name=naming.parse([self.module_name, "collar"], suffix="jDef"), position=self.collar_pos, radius=1.5)
        self.sockets.append(self.j_def_collar)
        self.j_collar_end = cmds.joint(name=naming.parse([self.module_name, "collarEnd"], suffix="j"), position=self.shoulder_pos, radius=1.5)
        self.sockets.append(self.j_collar_end)

        cmds.parent(self.j_def_collar, self.defJointsGrp)

        if not self.use_ref_orientation:
            joint.orient_joints([self.j_def_collar, self.j_collar_end], world_up_axis=self.look_axis, up_axis=(0, 1, 0),
                                reverse_aim=self.sideMult, reverse_up=self.sideMult)
        else:
            functions.align_to(self.j_def_collar, self.collar_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_def_collar, apply=True)
            functions.align_to(self.j_collar_end, self.shoulder_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_collar_end, apply=True)

        cmds.select(deselect=True)

        self.j_def_elbow = cmds.joint(name=naming.parse([self.module_name, "elbow"], suffix="jDef"), position=self.elbow_pos, radius=1.5)
        self.sockets.append(self.j_def_elbow)

        # IK Joints
        # Follow IK Chain
        cmds.select(deselect=True)
        self.j_ik_orig_up = cmds.joint(name=naming.parse([self.module_name, "IK", "orig", "up"], suffix="j"), position=self.shoulder_pos, radius=0.5)
        self.j_ik_orig_low = cmds.joint(name=naming.parse([self.module_name, "IK", "orig", "low"], suffix="j"), position=self.elbow_pos, radius=0.5)
        self.j_ik_orig_low_end = cmds.joint(name=naming.parse([self.module_name, "IK", "orig", "lowEnd"], suffix="j"), position=self.hand_pos, radius=0.5)

        # Single Chain IK
        cmds.select(deselect=True)
        self.j_ik_sc_up = cmds.joint(name=naming.parse([self.module_name, "IK", "SC", "up"], suffix="j"), position=self.shoulder_pos, radius=1.0)
        self.j_ik_sc_low = cmds.joint(name=naming.parse([self.module_name, "IK", "SC", "low"], suffix="j"), position=self.elbow_pos, radius=1.0)
        self.j_ik_sc_low_end = cmds.joint(name=naming.parse([self.module_name, "IK", "SC", "lowEnd"], suffix="j"), position=self.hand_pos, radius=1)

        # Rotate Plane IK
        cmds.select(deselect=True)
        self.j_ik_rp_up = cmds.joint(name=naming.parse([self.module_name, "IK", "RP", "up"], suffix="j"), position=self.shoulder_pos, radius=1.5)
        self.j_ik_rp_low = cmds.joint(name=naming.parse([self.module_name, "IK", "RP", "low"], suffix="j"), position=self.elbow_pos, radius=1.5)
        self.j_ik_rp_low_end = cmds.joint(name=naming.parse([self.module_name, "IK", "RP", "lowEnd"], suffix="j"), position=self.hand_pos, radius=1.5)

        cmds.select(deselect=True)

        # orientations

        if not self.use_ref_orientation:
            joint.orient_joints([self.j_ik_orig_up, self.j_ik_orig_low, self.j_ik_orig_low_end],
                                world_up_axis=self.look_axis, up_axis=(0, 1, 0), reverse_aim=self.sideMult,
                                reverse_up=self.sideMult)
        else:
            functions.align_to(self.j_ik_orig_up, self.shoulder_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_orig_up, apply=True)

            functions.align_to(self.j_ik_orig_low, self.elbow_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_orig_low, apply=True)

            functions.align_to(self.j_ik_orig_low_end, self.hand_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_orig_low_end, apply=True)

        if not self.use_ref_orientation:
            joint.orient_joints([self.j_ik_sc_up, self.j_ik_sc_low, self.j_ik_sc_low_end],
                                world_up_axis=self.look_axis,
                                up_axis=(0, 1, 0), reverse_aim=self.sideMult, reverse_up=self.sideMult)
        else:
            functions.align_to(self.j_ik_sc_up, self.shoulder_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_sc_up, apply=True)

            functions.align_to(self.j_ik_sc_low, self.elbow_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_sc_low, apply=True)

            functions.align_to(self.j_ik_sc_low_end, self.hand_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_sc_low_end, apply=True)

        if not self.use_ref_orientation:
            joint.orient_joints([self.j_ik_rp_up, self.j_ik_rp_low, self.j_ik_rp_low_end],
                                world_up_axis=self.look_axis,
                                up_axis=(0, 1, 0), reverse_aim=self.sideMult, reverse_up=self.sideMult)
        else:
            functions.align_to(self.j_ik_rp_up, self.shoulder_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_rp_up, apply=True)

            functions.align_to(self.j_ik_rp_low, self.elbow_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_rp_low, apply=True)

            functions.align_to(self.j_ik_rp_low_end, self.hand_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_rp_low_end, apply=True)

        # FK Joints
        cmds.select(deselect=True)
        self.j_fk_up = cmds.joint(name=naming.parse([self.module_name, "FK", "up"], suffix="j"), position=self.shoulder_pos, radius=2.0)
        self.j_fk_low = cmds.joint(name=naming.parse([self.module_name, "FK", "low"], suffix="j"), position=self.elbow_pos, radius=2.0)
        self.j_fk_low_end = cmds.joint(name=naming.parse([self.module_name, "FK", "lowEnd"], suffix="j"), position=self.hand_pos, radius=2.0)

        if not self.use_ref_orientation:
            joint.orient_joints([self.j_fk_up, self.j_fk_low, self.j_fk_low_end], world_up_axis=self.look_axis,
                                up_axis=(0, 1, 0), reverse_aim=self.sideMult, reverse_up=self.sideMult)
        else:
            functions.align_to(self.j_fk_up, self.shoulder_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_fk_up, apply=True)

            functions.align_to(self.j_fk_low, self.elbow_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_fk_low, apply=True)

            functions.align_to(self.j_fk_low_end, self.hand_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_fk_low_end, apply=True)

        # Hand joint
        self.j_def_hand = cmds.joint(name=naming.parse([self.module_name, "hand"], suffix="jDef"), position=self.hand_pos, radius=1.0)
        cmds.parent(self.j_def_hand, self.defJointsGrp)
        self.sockets.append(self.j_def_hand)

        # re-orient single joints
        functions.align_to_alter(self.j_collar_end, self.j_fk_up, 2)
        cmds.makeIdentity(self.j_collar_end, apply=True)
        functions.align_to_alter(self.j_def_elbow, self.j_fk_low, 2)
        cmds.makeIdentity(self.j_def_elbow, apply=True)
        functions.align_to_alter(self.j_def_hand, self.j_fk_low_end, 2)
        cmds.makeIdentity(self.j_def_hand, apply=True)

        # parent them under the collar
        connection.matrixConstraint(self.j_collar_end, self.rigJointsGrp, maintainOffset=False)
        cmds.parent(self.j_ik_orig_up, self.rigJointsGrp)
        cmds.parent(self.j_ik_sc_up, self.rigJointsGrp)
        cmds.parent(self.j_ik_rp_up, self.rigJointsGrp)
        cmds.parent(self.j_fk_up, self.rigJointsGrp)

        self.deformerJoints += [self.j_def_elbow, self.j_def_collar, self.j_def_hand]

        for jnt in [self.j_collar_end, self.j_def_hand]:
            cmds.connectAttr("%s.s" % self.scaleHook, "%s.s" % jnt)

    def create_controllers(self):
        # shoulder controller
        shoulder_cont_scale = (self.init_shoulder_dist / 2, self.init_shoulder_dist / 2, self.init_shoulder_dist / 2)
        self.shoulderCont = Controller(shape="Shoulder",
                                       name=naming.parse([self.module_name, "shoulder"], suffix="cont"),
                                       scale=shoulder_cont_scale,
                                       normal=(0, 0, -self.sideMult))
        self.shoulderCont.set_side(self.side, tier=0)

        self.controllers.append(self.shoulderCont)
        functions.align_to_alter(self.shoulderCont.name, self.j_def_collar, mode=2)

        _shoulder_off = self.shoulderCont.add_offset("OFF")
        _shoulder_ore = self.shoulderCont.add_offset("ORE")
        _shoulder_auto = self.shoulderCont.add_offset("Auto")

        cmds.parent(_shoulder_off, self.contBindGrp)

        # IK hand controller
        ik_cont_scale = (self.init_lower_arm_dist / 3, self.init_lower_arm_dist / 3, self.init_lower_arm_dist / 3)
        self.handIkCont = Controller(shape="Circle",
                                     name=naming.parse([self.module_name, "IK", "hand"], suffix="cont"),
                                     scale=ik_cont_scale,
                                     normal=(self.sideMult, 0, 0))
        self.handIkCont.set_side(self.side, tier=0)

        self.controllers.append(self.handIkCont)
        functions.align_to_alter(self.handIkCont.name, self.j_fk_low_end, mode=2)

        _handIK_off = self.handIkCont.add_offset("OFF")
        _handIK_ore = self.handIkCont.add_offset("ORE")
        _handIK_pos = self.handIkCont.add_offset("POS")

        cmds.parent(_handIK_off, self.contBindGrp)

        cmds.addAttr(self.handIkCont.name, shortName="polevector", longName="Pole_Vector", defaultValue=0.0,
                     minValue=0.0,
                     maxValue=1.0,
                     attributeType="double",
                     keyable=True)
        cmds.addAttr(self.handIkCont.name, shortName="polevectorPin", longName="Pole_Pin", defaultValue=0.0,
                     minValue=0.0,
                     maxValue=1.0,
                     attributeType="double",
                     keyable=True)
        cmds.addAttr(self.handIkCont.name, shortName="sUpArm", longName="Scale_Upper_Arm", defaultValue=1.0,
                     minValue=0.0,
                     attributeType="double",
                     keyable=True)
        cmds.addAttr(self.handIkCont.name, shortName="sLowArm", longName="Scale_Lower_Arm", defaultValue=1.0,
                     minValue=0.0,
                     attributeType="double",
                     keyable=True)
        cmds.addAttr(self.handIkCont.name, shortName="squash", longName="Squash", defaultValue=0.0, minValue=0.0,
                     maxValue=1.0,
                     attributeType="double",
                     keyable=True)
        cmds.addAttr(self.handIkCont.name, shortName="stretch", longName="Stretch", defaultValue=1.0, minValue=0.0,
                     maxValue=1.0,
                     attributeType="double",
                     keyable=True)
        cmds.addAttr(self.handIkCont.name, shortName="stretchLimit", longName="StretchLimit", defaultValue=100.0,
                     minValue=0.0,
                     maxValue=1000.0,
                     attributeType="double",
                     keyable=True)
        cmds.addAttr(self.handIkCont.name, shortName="softIK", longName="SoftIK", defaultValue=0.0, minValue=0.0,
                     maxValue=100.0,
                     keyable=True)
        cmds.addAttr(self.handIkCont.name, shortName="volume", longName="Volume_Preserve", defaultValue=0.0,
                     attributeType="double",
                     keyable=True)

        # Pole Vector Controller
        polecont_scale = (
            (((self.init_upper_arm_dist + self.init_lower_arm_dist) / 2) / 10),
            (((self.init_upper_arm_dist + self.init_lower_arm_dist) / 2) / 10),
            (((self.init_upper_arm_dist + self.init_lower_arm_dist) / 2) / 10)
        )
        self.poleBridge = cmds.spaceLocator(name=naming.parse([self.module_name, "poleVector"], suffix="brg"))[0]
        cmds.parent(self.poleBridge, self.nonScaleGrp)
        self.poleCont = Controller(shape="Sphere",
                                   name=naming.parse([self.module_name, "poleVector"], suffix="cont"),
                                   scale=polecont_scale,
                                   normal=(self.sideMult, 0, 0))
        self.poleCont.set_side(self.side, tier=0)
        self.controllers.append(self.poleCont)
        offset_mag_pole = ((self.init_upper_arm_dist + self.init_lower_arm_dist) / 4)
        offset_vector_pole = api.get_between_vector(self.j_def_elbow, [self.j_collar_end, self.j_def_hand])

        functions.align_and_aim(self.poleBridge,
                                target_list=[self.j_def_elbow],
                                aim_target_list=[self.j_collar_end, self.j_def_hand],
                                up_vector=self.up_axis,
                                translate_offset=(offset_vector_pole * offset_mag_pole)
                                )

        functions.align_to(self.poleCont.name, self.poleBridge, position=True, rotation=True)

        _poleCont_off = self.poleCont.add_offset("OFF")
        _poleCont_vis = self.poleCont.add_offset("VIS")

        cmds.parent(_poleCont_off, self.contBindGrp)

        # FK UP Arm Controller

        fk_up_arm_scale = (self.init_upper_arm_dist / 2, self.init_upper_arm_dist / 8, self.init_upper_arm_dist / 8)

        self.upArmFkCont = Controller(shape="Cube",
                                      name=naming.parse([self.module_name, "FK", "upArm"], suffix="cont"),
                                      scale=fk_up_arm_scale)
        self.upArmFkCont.set_side(self.side, tier=0)

        self.controllers.append(self.upArmFkCont)

        # move the pivot to the bottom
        cmds.xform(self.upArmFkCont.name, pivots=(self.sideMult * -(self.init_upper_arm_dist / 2), 0, 0), ws=True)

        # move the controller to the shoulder
        functions.align_to_alter(self.upArmFkCont.name, self.j_fk_up, mode=2)

        _upArmFK_off = self.upArmFkCont.add_offset("OFF")
        _upArmFK_ore = self.upArmFkCont.add_offset("ORE")

        cmds.xform(_upArmFK_off, pivots=self.shoulder_pos, worldSpace=True)
        cmds.xform(_upArmFK_ore, pivots=self.shoulder_pos, worldSpace=True)

        # matrix constraint doesnt like moving the pivot and freezing. We will move the offset manually
        cmds.setAttr("{}.tx".format(_upArmFK_ore), self.sideMult * (self.init_upper_arm_dist / 2))
        cmds.setAttr("{}.tx".format(self.upArmFkCont.name), 0)


        # FK LOW Arm Controller
        fk_low_arm_scale = (self.init_lower_arm_dist / 2, self.init_lower_arm_dist / 8, self.init_lower_arm_dist / 8)
        self.lowArmFkCont = Controller(shape="Cube",
                                       name=naming.parse([self.module_name, "FK", "lowArm"], suffix="cont"),
                                       scale=fk_low_arm_scale)
        self.lowArmFkCont.set_side(self.side, tier=0)
        self.controllers.append(self.lowArmFkCont)

        # move the pivot to the bottom
        cmds.xform(self.lowArmFkCont.name, pivots=(self.sideMult * -(self.init_lower_arm_dist / 2), 0, 0), ws=True)

        # align position and orientation to the joint
        functions.align_to_alter(self.lowArmFkCont.name, self.j_fk_low, mode=2)

        _low_arm_fk_cont_off = self.lowArmFkCont.add_offset("OFF")
        _lowArmFkCont_ore = self.lowArmFkCont.add_offset("ORE")
        cmds.xform(_low_arm_fk_cont_off, pivots=self.elbow_pos, worldSpace=True)
        cmds.xform(_lowArmFkCont_ore, pivots=self.elbow_pos, worldSpace=True)

        # matrix constraint doesnt like moving the pivot and freezing. We will move the offset manually
        cmds.setAttr("{}.tx".format(_lowArmFkCont_ore), self.sideMult * (self.init_lower_arm_dist / 2))
        cmds.setAttr("{}.tx".format(self.lowArmFkCont.name), 0)

        # FK HAND Controller
        fk_cont_scale = (self.init_lower_arm_dist / 5, self.init_lower_arm_dist / 5, self.init_lower_arm_dist / 5)
        # self.handFkCont, dmp = icon.createIcon("Cube", iconName="%s_FK_Hand_cont" % self.suffix, scale=fk_cont_scale)
        self.handFkCont = Controller(shape="Cube", name=naming.parse([self.module_name, "FK", "hand"], suffix="cont"), scale=fk_cont_scale)
        self.handFkCont.set_side(self.side, tier=0)
        self.controllers.append(self.handFkCont)
        functions.align_to_alter(self.handFkCont.name, self.j_def_hand, mode=2)

        _handFkCont_off = self.handFkCont.add_offset("OFF")
        _handFkCont_pos = self.handFkCont.add_offset("POS")
        _handFkCont_ore = self.handFkCont.add_offset("ORE")

        # FK-IK SWITCH Controller
        icon_scale = (self.init_upper_arm_dist / 4, self.init_upper_arm_dist / 4, self.init_upper_arm_dist / 4)
        self.switchFkIkCont = Controller(shape="FkikSwitch", name=naming.parse([self.module_name, "FKIK", "switch"], suffix="cont"), scale=icon_scale)
        self.switchFkIkCont.set_side(self.side, tier=0)
        self.controllers.append(self.switchFkIkCont)
        functions.align_and_aim(self.switchFkIkCont.name, target_list=[self.j_def_hand], aim_target_list=[self.j_def_elbow],
                                up_vector=self.up_axis, rotate_offset=(0, 180, 0))
        cmds.move((self.up_axis[0] * icon_scale[0] * 2), (self.up_axis[1] * icon_scale[1] * 2),
                  (self.up_axis[2] * icon_scale[2] * 2), self.switchFkIkCont.name, relative=True)

        _switch_fk_ik_pos = self.switchFkIkCont.add_offset("POS")

        cmds.setAttr("{0}.s{1}".format(self.switchFkIkCont.name, "x"), self.sideMult)

        # controller for twist orientation alignment
        cmds.addAttr(self.switchFkIkCont.name, shortName="autoShoulder", longName="Auto_Shoulder", defaultValue=1.0,
                     attributeType="float",
                     minValue=0.0, maxValue=1.0, keyable=True)
        cmds.addAttr(self.switchFkIkCont.name, shortName="alignShoulder", longName="Align_Shoulder", defaultValue=0.0,
                     attributeType="float",
                     minValue=0.0, maxValue=1.0, keyable=True)

        cmds.addAttr(self.switchFkIkCont.name, shortName="handAutoTwist", longName="Hand_Auto_Twist", defaultValue=1.0,
                     minValue=0.0,
                     maxValue=1.0, attributeType="float", keyable=True)
        cmds.addAttr(self.switchFkIkCont.name, shortName="handManualTwist", longName="Hand_Manual_Twist",
                     defaultValue=0.0,
                     attributeType="float",
                     keyable=True)

        cmds.addAttr(self.switchFkIkCont.name, shortName="shoulderAutoTwist", longName="Shoulder_Auto_Twist",
                     defaultValue=1.0,
                     minValue=0.0, maxValue=1.0, attributeType="float", keyable=True)
        cmds.addAttr(self.switchFkIkCont.name, shortName="shoulderManualTwist", longName="Shoulder_Manual_Twist",
                     defaultValue=0.0,
                     attributeType="float", keyable=True)

        cmds.addAttr(self.switchFkIkCont.name, shortName="allowScaling", longName="Allow_Scaling", defaultValue=1.0,
                     minValue=0.0,
                     maxValue=1.0, attributeType="float", keyable=True)
        cmds.addAttr(self.switchFkIkCont.name, attributeType="enum", keyable=True, shortName="interpType", longName="Interp_Type",
                     enumName="No_Flip:Average:Shortest:Longest:Cache", defaultValue=0)

        cmds.addAttr(self.switchFkIkCont.name, shortName="tweakControls", longName="Tweak_Controls", defaultValue=0,
                     attributeType="bool")
        cmds.setAttr("{0}.tweakControls".format(self.switchFkIkCont.name), channelBox=True)
        cmds.addAttr(self.switchFkIkCont.name, shortName="fingerControls", longName="Finger_Controls", defaultValue=1,
                     attributeType="bool")
        cmds.setAttr("{0}.fingerControls".format(self.switchFkIkCont.name), channelBox=True)

        cmds.parent(_switch_fk_ik_pos, self.contBindGrp)

        # Create MidLock controller

        midcont_scale = (self.init_lower_arm_dist / 4, self.init_lower_arm_dist / 4, self.init_lower_arm_dist / 4)
        self.midLockCont = Controller(shape="Star",
                                      name=naming.parse([self.module_name, "mid"], suffix="cont"),
                                      scale=midcont_scale,
                                      normal=(self.sideMult, 0, 0))
        self.midLockCont.set_side(self.side, tier=1)

        self.controllers.append(self.midLockCont)

        functions.align_to_alter(self.midLockCont.name, self.j_fk_low, 2)

        _mid_lock_ext = self.midLockCont.add_offset("EXT")
        _mid_lock_pos = self.midLockCont.add_offset("POS")
        _mid_lock_ave = self.midLockCont.add_offset("AVE")

        cmds.parent(_mid_lock_ext, self.localOffGrp)

        nodes_cont_vis = [_poleCont_off, _shoulder_off, _handIK_off, _handFkCont_off,
                          _switch_fk_ik_pos,
                          _low_arm_fk_cont_off, _upArmFK_off, _mid_lock_ave]

        _ = [cmds.connectAttr("%s.contVis" % self.scaleGrp, "%s.v" % x) for x in nodes_cont_vis]

    def create_roots(self):

        # Locators for positioning deformation joints
        self.defMid = cmds.spaceLocator(name=naming.parse([self.module_name, "defMid"], suffix="brg"))[0]
        functions.align_to(self.defMid, self.midLockCont.name, position=True, rotation=True)
        cmds.parent(self.defMid, self.defJointsGrp)
        self.defStart = cmds.spaceLocator(name=naming.parse([self.module_name, "defStart"], suffix="brg"))[0]
        cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % self.defStart)
        cmds.parent(self.defStart, self.nonScaleGrp)
        self.defEnd = cmds.spaceLocator(name=naming.parse([self.module_name, "defEnd"], suffix="brg"))[0]
        cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % self.defEnd)
        cmds.parent(self.defEnd, self.nonScaleGrp)

        # create two locators to hold the midLockCont
        self.midLockBridge_IK = cmds.spaceLocator(name=naming.parse([self.module_name, "IK", "midLock"], suffix="brg"))[0]
        cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % self.midLockBridge_IK)
        cmds.parent(self.midLockBridge_IK, self.nonScaleGrp)

        mult_matrix_ik_up_p = op.multiply_matrix(["%s.worldMatrix[0]" % self.j_ik_orig_up])
        mult_matrix_ik_low_p = op.multiply_matrix(["%s.worldMatrix[0]" % self.j_ik_orig_low])
        average_matrix_ik_p = op.average_matrix([mult_matrix_ik_up_p, mult_matrix_ik_low_p])
        decompose_ik_rot = cmds.createNode("decomposeMatrix", name=naming.parse([self.module_name, "IK", "rot"], suffix="decompose"))
        decompose_ik_trans = cmds.createNode("decomposeMatrix", name=naming.parse([self.module_name, "IK", "trans"], suffix="decompose"))
        cmds.connectAttr(average_matrix_ik_p, "%s.inputMatrix" % decompose_ik_rot)
        cmds.connectAttr(mult_matrix_ik_low_p, "%s.inputMatrix" % decompose_ik_trans)
        cmds.connectAttr("%s.outputRotate" % decompose_ik_rot, "%s.rotate" % self.midLockBridge_IK)
        cmds.connectAttr("%s.outputTranslate" % decompose_ik_trans, "%s.translate" % self.midLockBridge_IK)

        self.midLockBridge_FK = cmds.spaceLocator(name=naming.parse([self.module_name, "FK", "midLock"], suffix="brg"))[0]
        cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % self.midLockBridge_FK)
        cmds.parent(self.midLockBridge_FK, self.nonScaleGrp)

        mult_matrix_fk_up_p = op.multiply_matrix(["%s.worldMatrix[0]" % self.j_fk_up])
        mult_matrix_fk_low_p = op.multiply_matrix(["%s.worldMatrix[0]" % self.j_fk_low])
        average_matrix_fk_p = op.average_matrix([mult_matrix_fk_up_p, mult_matrix_fk_low_p])
        decompose_fk_rot = cmds.createNode("decomposeMatrix", name=naming.parse([self.module_name, "FK", "rot"], suffix="decompose"))
        decompose_fk_trans = cmds.createNode("decomposeMatrix", name=naming.parse([self.module_name, "FK", "trans"], suffix="decompose"))
        cmds.connectAttr(average_matrix_fk_p, "%s.inputMatrix" % decompose_fk_rot)
        cmds.connectAttr(mult_matrix_fk_low_p, "%s.inputMatrix" % decompose_fk_trans)
        cmds.connectAttr("%s.outputRotate" % decompose_fk_rot, "%s.rotate" % self.midLockBridge_FK)
        cmds.connectAttr("%s.outputTranslate" % decompose_fk_trans, "%s.translate" % self.midLockBridge_FK)

        cmds.parent(self.j_def_elbow, self.defMid)
        connection.matrixConstraint(self.midLockCont.name, self.j_def_elbow, maintainOffset=False,
                                    source_parent_cutoff=self.localOffGrp)

        # direct connection to the bridge
        cmds.connectAttr("%s.t" % self.defMid, "%s.t" % self.midLockCont.get_offsets()[-1])
        cmds.connectAttr("%s.r" % self.defMid, "%s.r" % self.midLockCont.get_offsets()[-1])
        cmds.connectAttr("%s.s" % self.scaleHook, "%s.s" % self.midLockCont.get_offsets()[-1])

    def create_ik_setup(self):

        # create IK chains
        sc_ik_handle = cmds.ikHandle(startJoint=self.j_ik_sc_up,
                                     endEffector=self.j_ik_sc_low_end,
                                     name=naming.parse([self.module_name, "SC"], suffix="IKHandle"),
                                     solver="ikSCsolver")[0]
        cmds.parent(sc_ik_handle, self.nonScaleGrp)
        cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % sc_ik_handle)
        rp_ik_handle = cmds.ikHandle(startJoint=self.j_ik_rp_up,
                                     endEffector=self.j_ik_rp_low_end,
                                     name=naming.parse([self.module_name, "RP"], suffix="IKHandle"),
                                     solver="ikRPsolver")[0]
        cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % rp_ik_handle)
        cmds.parent(rp_ik_handle, self.nonScaleGrp)
        cmds.poleVectorConstraint(self.poleBridge, rp_ik_handle)
        connection.matrixConstraint(self.poleCont.name, self.poleBridge, maintainOffset=False,
                                    source_parent_cutoff=self.localOffGrp)
        cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % self.poleBridge)

        # twist (start) lock and distance locators
        # -----------------------------
        # Create Start Lock
        self.startLock = cmds.spaceLocator(name=naming.parse([self.module_name, "startLock"], suffix="brg"))[0]
        functions.align_to_alter(self.startLock, self.j_ik_orig_up, 2)
        self.startLockOre = functions.create_offset_group(self.startLock, "Ore")
        self.startLockPos = functions.create_offset_group(self.startLock, "Pos")
        self.startLockTwist = functions.create_offset_group(self.startLock, "AutoTwist")
        cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % self.startLock)
        cmds.parent(self.startLockOre, self.nonScaleGrp)


        self.endLock = cmds.spaceLocator(name=naming.parse([self.module_name, "endLock"], suffix="brg"))[0]
        cmds.parent(self.endLock, self.nonScaleGrp)
        cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % self.endLock)
        functions.align_to(self.endLock, self.j_def_hand, position=True, rotation=False)

        connection.matrixConstraint(self.j_collar_end, self.startLock, skipRotate=("y", "z"), maintainOffset=False)

        distance_start = cmds.spaceLocator(name=naming.parse([self.module_name, "distanceStart"], suffix="loc"))[0]
        cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % distance_start)
        cmds.parent(distance_start, self.nonScaleGrp)
        cmds.pointConstraint(self.startLock, distance_start, maintainOffset=False)

        distance_end = cmds.spaceLocator(name=naming.parse([self.module_name, "distanceEnd"], suffix="loc"))[0]
        cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % distance_end)
        cmds.parent(distance_end, self.nonScaleGrp)
        cmds.pointConstraint(self.endLock, distance_end, maintainOffset=False)

        connection.matrixConstraint(self.handIkCont.name, self.endLock, source_parent_cutoff=self.localOffGrp)

        sc_stretch_locs = tools.make_stretchy_ik([self.j_ik_sc_up, self.j_ik_sc_low, self.j_ik_sc_low_end],
                                                 sc_ik_handle,
                                                 self.shoulderCont.name, self.handIkCont.name, side=self.side,
                                                 source_parent_cutoff=self.localOffGrp,
                                                 name=naming.parse([self.module_name, "sc"], suffix="loc"),
                                                 distance_start=distance_start, distance_end=distance_end,
                                                 is_local=self.isLocal)
        rp_stretch_locs = tools.make_stretchy_ik([self.j_ik_rp_up, self.j_ik_rp_low, self.j_ik_rp_low_end],
                                                 rp_ik_handle,
                                                 self.shoulderCont.name, self.handIkCont.name, side=self.side,
                                                 source_parent_cutoff=self.localOffGrp,
                                                 name=naming.parse([self.module_name, "rp"], suffix="loc"),
                                                 distance_start=distance_start, distance_end=distance_end,
                                                 is_local=self.isLocal)
        for x in sc_stretch_locs[:2] + rp_stretch_locs[:2]:
            cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % x)
        # _ = [cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % x) for x in sc_stretch_locs]
        # _ = [cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % x) for x in rp_stretch_locs]
        cmds.parent(sc_stretch_locs[:2] + rp_stretch_locs[:2], self.nonScaleGrp)


        connection.matrixConstraint(self.handIkCont.name, self.j_ik_sc_low_end, skipTranslate="xyz", skipScale="xyz", maintainOffset=False,
                                    source_parent_cutoff=self.localOffGrp)
        # # pole vector pinning
        pin_blender = cmds.createNode("blendColors", name=naming.parse([self.module_name, "polePin"], suffix="blend"))
        cmds.connectAttr("%s.polevectorPin" % self.handIkCont.name, "%s.blender" % pin_blender)

        mult_matrix_root_p = op.multiply_matrix(["%s.worldMatrix[0]" % self.j_ik_sc_up])
        pin_root_p = op.decompose_matrix(mult_matrix_root_p)[0]

        pin_mid = functions.get_shapes(self.poleBridge)[0]
        mult_matrix_end_p = op.multiply_matrix(["%s.worldMatrix[0]" % self.j_ik_sc_low_end])
        pin_end_p = op.decompose_matrix(mult_matrix_end_p)[0]

        upper_pin_distance = measure.Distance(start=pin_root_p, end="%s.worldPosition[0]" % pin_mid)
        lower_pin_distance = measure.Distance(start="%s.worldPosition[0]" % pin_mid, end=pin_end_p)
        upper_pin_divided_p = op.divide(upper_pin_distance.plug, "%s.sx" % self.scaleHook)
        lower_pin_divided_p = op.divide(lower_pin_distance.plug, "%s.sx" % self.scaleHook)
        cmds.connectAttr(upper_pin_divided_p, "%s.color1R" % pin_blender)
        cmds.connectAttr(lower_pin_divided_p, "%s.color1G" % pin_blender)

        # hijack the joints translate X
        low_output_plug = \
            connection.connections("%s.tx" % self.j_ik_rp_low, exclude_types=["ikEffector"], return_mode="incoming")[0][
                "plug_in"]
        low_end_output_plug = \
            connection.connections("%s.tx" % self.j_ik_rp_low_end, exclude_types=["ikEffector"],
                                   return_mode="incoming")[0][
                "plug_in"]

        r_plug = low_output_plug
        g_plug = low_end_output_plug

        cmds.connectAttr(r_plug, "%s.color2R" % pin_blender, force=True)
        cmds.connectAttr(g_plug, "%s.color2G" % pin_blender, force=True)
        #
        cmds.connectAttr("%s.outputR" % pin_blender, "%s.tx" % self.j_ik_rp_low, force=True)
        cmds.connectAttr("%s.outputG" % pin_blender, "%s.tx" % self.j_ik_rp_low_end, force=True)

        # Scale Upper / Lower Parts
        upper_list = [self.j_ik_rp_low, self.j_ik_sc_low]
        lower_list = [self.j_ik_rp_low_end, self.j_ik_sc_low_end]
        for jnt_list, scale_attr in zip([upper_list, lower_list], ["sUpArm", "sLowArm"]):
            for jnt in jnt_list:
                initial_distance = cmds.getAttr("%s.initialDistance" % jnt)
                mult_p = op.multiply(initial_distance, "{0}.{1}".format(self.handIkCont.name, scale_attr))
                cmds.connectAttr(mult_p, "%s.initialDistance" % jnt)

        connection.matrix_switch(self.j_ik_rp_up, self.j_ik_sc_up, self.j_ik_orig_up,
                                "%s.Pole_Vector" % self.handIkCont.name)
        elbow_switcher = cmds.spaceLocator(name=naming.parse([self.module_name, "elbowSwitcher"], suffix="brg"))[0]
        cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % elbow_switcher)
        cmds.parent(elbow_switcher, self.nonScaleGrp)
        connection.matrix_switch(self.j_ik_rp_low, self.j_ik_sc_low, elbow_switcher,
                                "%s.Pole_Vector" % self.handIkCont.name)
        connection.matrixConstraint(elbow_switcher, self.j_ik_orig_low)
        connection.matrix_switch(self.j_ik_rp_low_end, self.j_ik_sc_low_end, self.j_ik_orig_low_end,
                                "%s.Pole_Vector" % self.handIkCont.name)

    def create_fk_setup(self):
        connection.matrixConstraint(self.shoulderCont.name, self.j_def_collar, maintainOffset=True,
                                    source_parent_cutoff=self.localOffGrp)
        connection.matrixConstraint(self.upArmFkCont.name, self.j_fk_up, maintainOffset=True, source_parent_cutoff=self.localOffGrp)
        connection.matrixConstraint(self.lowArmFkCont.name, self.j_fk_low, maintainOffset=True,
                                    source_parent_cutoff=self.localOffGrp)
        connection.matrixConstraint(self.handFkCont.name, self.j_fk_low_end, maintainOffset=True,
                                    source_parent_cutoff=self.localOffGrp)

        cmds.parent(self.handFkCont.get_offsets()[-1], self.lowArmFkCont.name)
        cmds.parent(self.lowArmFkCont.get_offsets()[-1], self.upArmFkCont.name)
        cmds.parent(self.upArmFkCont.get_offsets()[-1], self.shoulderCont.name)
        attribute.disconnect_attr(node=self.j_def_collar, attr="inverseScale", suppress_warnings=True)
        attribute.disconnect_attr(node=self.j_fk_up, attr="inverseScale", suppress_warnings=True)
        attribute.disconnect_attr(node=self.j_fk_low, attr="inverseScale", suppress_warnings=True)
        attribute.disconnect_attr(node=self.j_fk_low_end, attr="inverseScale", suppress_warnings=True)

    def ik_fk_switching(self):

        connection.matrix_switch(self.j_ik_orig_up, self.j_fk_up, self.defStart, "%s.FK_IK" % self.switchFkIkCont.name)
        connection.matrix_switch(self.j_ik_orig_low_end, self.j_fk_low_end, self.defEnd,
                                "%s.FK_IK" % self.switchFkIkCont.name, position=True, rotation=False)
        connection.matrix_switch(self.handIkCont.name, self.handFkCont.name, self.defEnd,
                                "%s.FK_IK" % self.switchFkIkCont.name, position=False, rotation=True,
                                 source_parent_cutoff=self.localOffGrp)
        connection.matrix_switch(self.midLockBridge_IK, self.midLockBridge_FK, self.defMid,
                                "%s.FK_IK" % self.switchFkIkCont.name)

        connection.matrixConstraint(self.defEnd, self.j_def_hand, skipScale="xyz", maintainOffset=False)

        cmds.connectAttr("%s.FK_IK_Reverse" % self.switchFkIkCont.name, "%s.v" % self.upArmFkCont.name)
        cmds.connectAttr("%s.FK_IK_Reverse" % self.switchFkIkCont.name, "%s.v" % self.lowArmFkCont.name)
        cmds.connectAttr("%s.FK_IK_Reverse" % self.switchFkIkCont.name, "%s.v" % self.handFkCont.name)
        cmds.connectAttr("%s.FK_IK" % self.switchFkIkCont.name, "%s.v" % self.poleCont.name)
        cmds.connectAttr("%s.FK_IK" % self.switchFkIkCont.name, "%s.v" % self.handIkCont.name)

        connection.matrixConstraint(self.j_def_hand, self.switchFkIkCont.name, maintainOffset=True)

    def create_ribbons(self):
        # UPPER ARM RIBBON

        ####################
        ribbon_upper_arm = Ribbon(self.j_collar_end,
                                  self.j_def_elbow,
                                  name=naming.parse([self.module_name, "up"]),
                                  connect_start_aim=False,
                                  up_vector=self.up_axis)
        ribbon_upper_arm.create()

        ribbon_start_pa_con_upper_arm_start = ribbon_upper_arm.pin_start(self.defStart)[0]
        ribbon_upper_arm.pin_end(self.j_def_elbow)

        cmds.connectAttr("{0}.scale".format(self.midLockCont.name), "{0}.scale".format(ribbon_upper_arm.end_plug))

        if not self.isLocal:
            cmds.connectAttr("%s.s" % self.scaleHook, "%s.s" % ribbon_upper_arm.scale_grp)

        ribbon_start_ori_con = \
            cmds.parentConstraint(self.j_ik_orig_up, self.j_fk_up, ribbon_upper_arm.start_aim, maintainOffset=True,
                                  skipTranslate=["x", "y", "z"])[0]

        cmds.parentConstraint(self.j_collar_end, ribbon_upper_arm.start_aim, maintainOffset=True, skipTranslate=["x", "y", "z"])

        cmds.connectAttr("{0}.FK_IK".format(self.switchFkIkCont.name),
                         ("%s.%sW0" % (ribbon_start_ori_con, self.j_ik_orig_up)))
        cmds.connectAttr("{0}.FK_IK_Reverse".format(self.switchFkIkCont.name),
                         ("%s.%sW1" % (ribbon_start_ori_con, self.j_fk_up)))

        pair_blend_node = cmds.listConnections(ribbon_start_ori_con, destination=True, type="pairBlend")[0]
        # re-connect to the custom attribute
        cmds.connectAttr("{0}.alignShoulder".format(self.switchFkIkCont.name), "{0}.weight".format(pair_blend_node),
                         force=True)

        # AUTO AND MANUAL TWIST

        # auto
        auto_twist = cmds.createNode("multiplyDivide", name=naming.parse([self.module_name, "autoTwist"], suffix="mult"))
        cmds.connectAttr("{0}.shoulderAutoTwist".format(self.switchFkIkCont.name), "{0}.input2X".format(auto_twist))
        cmds.connectAttr("{0}.constraintRotate".format(ribbon_start_pa_con_upper_arm_start),
                         "{0}.input1".format(auto_twist))

        # !!! The parent constrain override should be disconnected like this
        cmds.disconnectAttr("{0}.constraintRotateX".format(ribbon_start_pa_con_upper_arm_start),
                            "{0}.rotateX".format(ribbon_upper_arm.start_plug))

        # manual
        add_manual_twist = cmds.createNode("plusMinusAverage", name=naming.parse([self.module_name, "upperArm", "addManualTwist"], suffix="plus"))
        cmds.connectAttr("{0}.output".format(auto_twist), "{0}.input3D[0]".format(add_manual_twist))
        cmds.connectAttr("{0}.shoulderManualTwist".format(self.switchFkIkCont.name),
                         "{0}.input3D[1].input3Dx".format(add_manual_twist))

        # connect to the joint
        cmds.connectAttr("{0}.output3D".format(add_manual_twist), "{0}.rotate".format(ribbon_upper_arm.start_plug))

        # connect allowScaling
        cmds.connectAttr("{0}.allowScaling".format(self.switchFkIkCont.name),
                         "{0}.scaleSwitch".format(ribbon_upper_arm.start_plug))

        # LOWER ARM RIBBON

        ribbon_lower_arm = Ribbon(self.j_def_elbow,
                                  self.j_def_hand,
                                  name=naming.parse([self.module_name, "low"]),
                                  connect_start_aim=True,
                                  up_vector=self.up_axis)

        ribbon_lower_arm.create()

        ribbon_lower_arm.pin_start(self.j_def_elbow)
        ribbon_start_pa_con_lower_arm_end = ribbon_lower_arm.pin_end(self.defEnd)[0]

        # connect the elbow scaling
        cmds.connectAttr("{0}.scale".format(self.midLockCont.name), "{0}.scale".format(ribbon_lower_arm.start_plug))

        if not self.isLocal:
            cmds.connectAttr("%s.s" % self.scaleHook, "%s.s" % ribbon_lower_arm.scale_grp)

        # AUTO AND MANUAL TWIST

        # auto
        auto_twist = cmds.createNode("multiplyDivide", name=naming.parse([self.module_name, "autoTwist"], suffix="mult"))
        cmds.connectAttr("{0}.handAutoTwist".format(self.switchFkIkCont.name), "{0}.input2X".format(auto_twist))
        cmds.connectAttr("{0}.constraintRotate".format(ribbon_start_pa_con_lower_arm_end),
                         "{0}.input1".format(auto_twist))

        # !!! The parent constrain override should be disconnected like this
        cmds.disconnectAttr("{0}.constraintRotateX".format(ribbon_start_pa_con_lower_arm_end),
                            "{0}.rotateX".format(ribbon_lower_arm.end_plug))

        # manual
        add_manual_twist = cmds.createNode("plusMinusAverage", name=naming.parse([self.module_name, "lowerArm", "addManualTwist"], suffix="plus"))
        cmds.connectAttr("{0}.output".format(auto_twist), "{0}.input3D[0]".format(add_manual_twist))
        cmds.connectAttr("{0}.handManualTwist".format(self.switchFkIkCont.name),
                         "{0}.input3D[1].input3Dx".format(add_manual_twist))

        # connect to the joint
        cmds.connectAttr("{0}.output3D".format(add_manual_twist), "{0}.rotate".format(ribbon_lower_arm.end_plug))

        # connect allowScaling
        cmds.connectAttr("{0}.allowScaling".format(self.switchFkIkCont.name),
                         "{0}.scaleSwitch".format(ribbon_lower_arm.start_plug))

        # Volume Preservation Stuff
        vp_extra_input = cmds.createNode("multiplyDivide", name=naming.parse([self.module_name, "vpExtraInput"]))
        cmds.setAttr("{0}.operation".format(vp_extra_input), 1)

        vp_mid_average = cmds.createNode("plusMinusAverage", name=naming.parse([self.module_name, "vpMidAverage"]))
        cmds.setAttr("{0}.operation".format(vp_mid_average), 3)

        vp_power_mid = cmds.createNode("multiplyDivide", name=naming.parse([self.module_name, "vpPowerMid"]))
        cmds.setAttr("{0}.operation".format(vp_power_mid), 3)
        vp_init_length = cmds.createNode("multiplyDivide", name=naming.parse([self.module_name, "vpInitLength"]))
        cmds.setAttr("{0}.operation".format(vp_init_length), 2)

        vp_power_upper_leg = cmds.createNode("multiplyDivide", name=naming.parse([self.module_name, "vpPowerUpperLeg"]))
        cmds.setAttr("{0}.operation".format(vp_power_upper_leg), 3)

        vp_power_lower_leg = cmds.createNode("multiplyDivide", name=naming.parse([self.module_name, "vpPowerLowerLeg"]))
        cmds.setAttr("{0}.operation".format(vp_power_lower_leg), 3)
        #
        vp_upper_lower_reduce = cmds.createNode("multDoubleLinear", name=naming.parse([self.module_name, "vpUpperLowerReduce"]))
        cmds.setAttr("{0}.input2".format(vp_upper_lower_reduce), 0.5)
        #
        # vp knee branch
        cmds.connectAttr("{0}.output".format(vp_extra_input), "{0}.scale".format(ribbon_lower_arm.start_plug),
                         force=True)
        cmds.connectAttr("{0}.output".format(vp_extra_input), "{0}.scale".format(ribbon_upper_arm.end_plug), f=True)
        if self.isLocal:
            cmds.connectAttr("{0}.output".format(vp_extra_input), "{0}.scale".format(self.j_def_elbow), f=True)
        else:
            _mult = cmds.createNode("multiplyDivide", name=naming.parse([self.module_name, "elbow_globalScale"], suffix="mult"))
            cmds.connectAttr("{0}.output".format(vp_extra_input), "{0}.input1".format(_mult))
            cmds.connectAttr("{0}.scale".format(self.scaleHook), "{0}.input2".format(_mult))
            cmds.connectAttr("{0}.output".format(_mult), "{0}.scale".format(self.j_def_elbow), force=True)

        cmds.connectAttr("{0}.scale".format(self.midLockCont.name), "{0}.input1".format(vp_extra_input))

        cmds.connectAttr("{0}.output1D".format(vp_mid_average), "{0}.input2X".format(vp_extra_input))
        cmds.connectAttr("{0}.output1D".format(vp_mid_average), "{0}.input2Y".format(vp_extra_input))
        cmds.connectAttr("{0}.output1D".format(vp_mid_average), "{0}.input2Z".format(vp_extra_input))

        cmds.connectAttr("{0}.outputX".format(vp_power_mid), "{0}.input1D[0]".format(vp_mid_average))
        cmds.connectAttr("{0}.outputY".format(vp_power_mid), "{0}.input1D[1]".format(vp_mid_average))

        cmds.connectAttr("{0}.outputX".format(vp_init_length), "{0}.input1X".format(vp_power_mid))
        cmds.connectAttr("{0}.outputY".format(vp_init_length), "{0}.input1Y".format(vp_power_mid))

        cmds.connectAttr("{0}.volume".format(self.handIkCont.name), "{0}.input2X".format(vp_power_mid))
        cmds.connectAttr("{0}.volume".format(self.handIkCont.name), "{0}.input2Y".format(vp_power_mid))

        cmds.connectAttr("{0}.initialDistance".format(self.j_ik_sc_low), "{0}.input1X".format(vp_init_length))
        cmds.connectAttr("{0}.initialDistance".format(self.j_ik_sc_low_end), "{0}.input1Y".format(vp_init_length))

        cmds.connectAttr("{0}.translateX".format(self.j_ik_sc_low), "{0}.input2X".format(vp_init_length))
        cmds.connectAttr("{0}.translateX".format(self.j_ik_sc_low_end), "{0}.input2Y".format(vp_init_length))

        # vp upper branch
        # mid_off_up = functions.get_parent(ribbon_upper_arm.controllers[0])
        mid_off_up = ribbon_upper_arm.controllers[0].parent
        cmds.connectAttr("{0}.outputX".format(vp_power_upper_leg), "{0}.scaleX".format(mid_off_up))
        cmds.connectAttr("{0}.outputX".format(vp_power_upper_leg), "{0}.scaleY".format(mid_off_up))
        cmds.connectAttr("{0}.outputX".format(vp_power_upper_leg), "{0}.scaleZ".format(mid_off_up))
        cmds.connectAttr("{0}.outputX".format(vp_init_length), "{0}.input1X".format(vp_power_upper_leg))
        cmds.connectAttr("{0}.output".format(vp_upper_lower_reduce), "{0}.input2X".format(vp_power_upper_leg))

        # vp lower branch
        # mid_off_low = functions.get_parent(ribbon_lower_arm.controllers[0])
        mid_off_low = ribbon_lower_arm.controllers[0].parent
        cmds.connectAttr("{0}.outputX".format(vp_power_lower_leg), "{0}.scaleX".format(mid_off_low))
        cmds.connectAttr("{0}.outputX".format(vp_power_lower_leg), "{0}.scaleY".format(mid_off_low))
        cmds.connectAttr("{0}.outputX".format(vp_power_lower_leg), "{0}.scaleZ".format(mid_off_low))
        cmds.connectAttr("{0}.outputX".format(vp_init_length), "{0}.input1X".format(vp_power_lower_leg))
        cmds.connectAttr("{0}.output".format(vp_upper_lower_reduce), "{0}.input2X".format(vp_power_lower_leg))
        cmds.connectAttr("{0}.volume".format(self.handIkCont.name), "{0}.input1".format(vp_upper_lower_reduce))

        cmds.parent(ribbon_upper_arm.ribbon_grp, self.nonScaleGrp)
        cmds.parent(ribbon_lower_arm.ribbon_grp, self.nonScaleGrp)

        cmds.connectAttr("{0}.tweakControls".format(self.switchFkIkCont.name), "{0}.v".format(self.midLockCont.name))
        tweak_conts = ribbon_upper_arm.controllers + ribbon_lower_arm.controllers

        attribute.drive_attrs("%s.tweakControls" % self.switchFkIkCont.name, ["%s.v" % x.name for x in tweak_conts])

        self.deformerJoints += ribbon_lower_arm.deformer_joints + ribbon_upper_arm.deformer_joints

        attribute.drive_attrs("%s.rigVis" % self.scaleGrp, ["%s.v" % x for x in ribbon_lower_arm.to_hide])
        attribute.drive_attrs("%s.rigVis" % self.scaleGrp, ["%s.v" % x for x in ribbon_upper_arm.to_hide])

        for cont in ribbon_upper_arm.controllers + ribbon_lower_arm.controllers:
            cont.set_side(self.side, tier="tertiary")

        cmds.parent(ribbon_upper_arm.nonscale_grp, self.defJointsGrp)
        cmds.parent(ribbon_lower_arm.nonscale_grp, self.defJointsGrp)

    def create_angle_extractors(self):
        # # IK Angle Extractor
        angle = measure.Angle(suffix=self.module_name)
        angle.pin_root(self.limbPlug)
        angle.pin_fixed(self.handIkCont.name)
        functions.align_to(angle.float, self.j_def_collar, rotation=True, position=True)
        cmds.move(0, 0, -self.sideMult * 5, angle.float, objectSpace=True)
        angle.calibrate()
        angle.set_value_multiplier(0.5)

        # FK Angle Extractor
        angle_remap_fk = cmds.createNode("remapValue", name=naming.parse([self.module_name, "FK", "angle"], suffix="remap"))
        angle_mult_fk = cmds.createNode("multDoubleLinear", name=naming.parse([self.module_name, "FK", "angle"], suffix="mult"))

        cmds.connectAttr("{0}.rotateY".format(self.upArmFkCont.name), "{0}.inputValue".format(angle_remap_fk))
        cmds.setAttr("{0}.inputMin".format(angle_remap_fk), 0)
        cmds.setAttr("{0}.inputMax".format(angle_remap_fk), 90)
        cmds.setAttr("{0}.outputMin".format(angle_remap_fk), 0)
        cmds.setAttr("{0}.outputMax".format(angle_remap_fk), 90)

        cmds.connectAttr("{0}.outValue".format(angle_remap_fk), "{0}.input1".format(angle_mult_fk))
        cmds.setAttr("{0}.input2".format(angle_mult_fk), 0.5)

        # create blend attribute and global Mult
        angle_ext_blend = cmds.createNode("blendTwoAttr", name=naming.parse([self.module_name, "angle", "ext"], suffix="blend"))
        angle_global = cmds.createNode("multDoubleLinear", name=naming.parse([self.module_name, "angle", "global"], suffix="mult"))

        cmds.connectAttr("{0}.fk_ik".format(self.switchFkIkCont.name), "{0}.attributesBlender".format(angle_ext_blend))
        cmds.connectAttr("{0}.output".format(angle_mult_fk), "{0}.input[0]".format(angle_ext_blend))

        cmds.connectAttr(angle.value_plug, "{0}.input[1]".format(angle_ext_blend))

        cmds.connectAttr("{0}.output".format(angle_ext_blend), "{0}.input1".format(angle_global))
        cmds.connectAttr("{0}.autoShoulder".format(self.switchFkIkCont.name), "{0}.input2".format(angle_global))

        cmds.connectAttr("{0}.output".format(angle_global), "{0}.rotateY".format(self.shoulderCont.get_offsets()[0]))

        cmds.parent(angle.root, self.nonScaleGrp)
        cmds.connectAttr("{0}.rigVis".format(self.scaleGrp), "{0}.v".format(angle.root))
        return

    def round_up(self):
        cmds.parentConstraint(self.limbPlug, self.scaleGrp, maintainOffset=False)
        cmds.setAttr("%s.rigVis" % self.scaleGrp, 0)

        self.scaleConstraints.append(self.scaleGrp)

        for jnt in self.deformerJoints:
            cmds.connectAttr("%s.jointVis" % self.scaleGrp, "%s.v" % jnt)
        cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % functions.get_shapes(self.defMid)[0])
        # cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % self.nonScaleGrp)
        cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % self.rigJointsGrp)
        # lock and hide
        self.handIkCont.lock_visibility()
        self.anchors = [(self.handIkCont.name, "parent", 1, None), (self.poleCont.name, "parent", 1, None)]
        for cont in self.controllers:
            cont.set_defaults()

    def execute(self):
        self.create_joints()
        self.create_controllers()
        self.create_roots()
        self.create_ik_setup()
        self.create_fk_setup()
        self.ik_fk_switching()
        self.create_ribbons()
        self.create_angle_extractors()
        self.round_up()

    # def createLimb(self):
    #     self.create_groups()
    #     self.create_joints()
    #     self.create_controllers()
    #     self.create_roots()
    #     self.create_ik_setup()
    #     self.create_fk_setup()
    #     self.ik_fk_switching()
    #     self.create_ribbons()
    #     self.create_angle_extractors()
    #     self.round_up()


class Guides(object):
    def __init__(self, side="L", suffix="arm", segments=None, tMatrix=None, upVector=(0, 1, 0), mirrorVector=(1, 0, 0),
                 lookVector=(0, 0, 1), *args, **kwargs):
        super(Guides, self).__init__()

        self.side = side
        self.sideMultiplier = -1 if side == "R" else 1
        self.name = suffix
        self.segments = segments
        self.tMatrix = om.MMatrix(tMatrix) if tMatrix else om.MMatrix()
        self.upVector = om.MVector(upVector)
        self.mirrorVector = om.MVector(mirrorVector)
        self.lookVector = om.MVector(lookVector)

        self.offsetVector = None
        self.guideJoints = []

    def draw_joints(self):
        self.guideJoints = []
        if self.side == "C":
            collar_vec = om.MVector(0, 0, 2) * self.tMatrix
            shoulder_vec = om.MVector(0, 0, 5) * self.tMatrix
            elbow_vec = om.MVector(0, -1, 9) * self.tMatrix
            hand_vec = om.MVector(0, 0, 14) * self.tMatrix
        # Initial Joint positions for left arm
        else:
            collar_vec = om.MVector(2 * self.sideMultiplier, 0, 0) * self.tMatrix
            shoulder_vec = om.MVector(5 * self.sideMultiplier, 0, 0) * self.tMatrix
            elbow_vec = om.MVector(9 * self.sideMultiplier, 0, -1) * self.tMatrix
            hand_vec = om.MVector(14 * self.sideMultiplier, 0, 0) * self.tMatrix

        self.offsetVector = -((collar_vec - shoulder_vec).normalize())

        cmds.select(deselect=True)
        collar = cmds.joint(position=collar_vec, name=naming.parse([self.name, "collar"], side=self.side, suffix="jInit"))
        cmds.setAttr("{0}.radius".format(collar), 2)
        shoulder = cmds.joint(position=shoulder_vec, name=naming.parse([self.name, "shoulder"], side=self.side, suffix="jInit"))
        elbow = cmds.joint(position=elbow_vec, name=naming.parse([self.name, "elbow"], side=self.side, suffix="jInit"))
        hand = cmds.joint(position=hand_vec, name=naming.parse([self.name, "hand"], side=self.side, suffix="jInit"))

        self.guideJoints = [collar, shoulder, elbow, hand]

        # Orientation
        joint.orient_joints(self.guideJoints, world_up_axis=self.lookVector, up_axis=(0, 1, 0),
                            reverse_aim=self.sideMultiplier, reverse_up=self.sideMultiplier)

    def define_attributes(self):
        joint.set_joint_type(self.guideJoints[0], "Collar")
        joint.set_joint_type(self.guideJoints[1], "Shoulder")
        joint.set_joint_type(self.guideJoints[2], "Elbow")
        joint.set_joint_type(self.guideJoints[3], "Hand")
        _ = [joint.set_joint_side(jnt, self.side) for jnt in self.guideJoints]

        root_jnt = self.guideJoints[0]
        attribute.create_global_joint_attrs(root_jnt, moduleName=naming.parse([self.name], side=self.side),
                                            mirrorAxis=self.mirrorVector, lookAxis=self.lookVector)

        for attr_dict in LIMB_DATA["properties"]:
            attribute.create_attribute(root_jnt, attr_dict)

    def createGuides(self):
        """Main Function to create Guides"""
        self.draw_joints()
        self.define_attributes()

    def convertJoints(self, joints_list):
        if len(joints_list) != 4:
            LOG.warning("Define or select exactly 5 joints for Arm Guide conversion. Skipping")
            return
        self.guideJoints = joints_list
        _ = [joint.set_joint_side(jnt, self.side) for jnt in self.guideJoints]
        self.define_attributes()

