from maya import cmds
import maya.api.OpenMaya as om

from trigger.library import functions, joint
from trigger.library import naming
from trigger.library import attribute
from trigger.library import api
from trigger.objects.ribbon import Ribbon
from trigger.objects.controller import Controller
from trigger.modules import _module

from trigger.core import filelog

log = filelog.Filelog(logname=__name__, filename="trigger_log")

LIMB_DATA = {
    "members": [
        "LegRoot",
        "Hip",
        "Knee",
        "Foot",
        "Ball",
        "HeelPV",
        "ToePV",
        "BankIN",
        "BankOUT",
    ],
    "properties": [],
    "multi_guide": None,
    "sided": True,
}


class Leg(_module.ModuleCore):
    def __init__(self, build_data=None, inits=None):
        super(Leg, self).__init__()
        if build_data:
            self.leg_root_ref = build_data["LegRoot"]
            self.hip_ref = build_data["Hip"]
            self.knee_ref = build_data["Knee"]
            self.foot_ref = build_data["Foot"]
            self.ball_ref = build_data["Ball"]
            self.heel_pv_ref = build_data["HeelPV"]
            self.toe_pv_ref = build_data["ToePV"]
            self.bank_in_ref = build_data["BankIN"]
            self.bank_out_ref = build_data["BankOUT"]
            self.inits = [
                self.leg_root_ref,
                self.hip_ref,
                self.knee_ref,
                self.foot_ref,
                self.ball_ref,
                self.heel_pv_ref,
                self.toe_pv_ref,
                self.bank_in_ref,
                self.bank_out_ref,
            ]
        elif inits:
            if len(inits) < 9:
                cmds.error("Some or all Leg Init Bones are missing (or Renamed)")
                return
            self.leg_root_ref = inits[0]
            self.hip_ref = inits[1]
            self.knee_ref = inits[2]
            self.foot_ref = inits[3]
            self.ball_ref = inits[4]
            self.heel_pv_ref = inits[5]
            self.toe_pv_ref = inits[6]
            self.bank_in_ref = inits[7]
            self.bank_out_ref = inits[8]
            self.inits = inits
        else:
            log.error("Class needs either build_data or arm inits to be constructed")

        # get positions
        self.leg_root_pos = api.get_world_translation(self.leg_root_ref)
        self.hip_pos = api.get_world_translation(self.hip_ref)
        self.knee_pos = api.get_world_translation(self.knee_ref)
        self.foot_pos = api.get_world_translation(self.foot_ref)
        self.ball_pos = api.get_world_translation(self.ball_ref)
        self.toe_pv_pos = api.get_world_translation(self.toe_pv_ref)

        # get distances
        self.init_upper_leg_dist = functions.get_distance(self.hip_ref, self.knee_ref)
        self.init_lower_leg_dist = functions.get_distance(self.knee_ref, self.foot_ref)
        self.init_ball_dist = functions.get_distance(self.foot_ref, self.ball_ref)
        self.init_toe_dist = functions.get_distance(self.ball_ref, self.toe_pv_ref)
        self.init_foot_length = functions.get_distance(
            self.toe_pv_ref, self.heel_pv_ref
        )
        self.init_foot_width = functions.get_distance(
            self.bank_in_ref, self.bank_out_ref
        )

        self.up_axis, self.mirror_axis, self.look_axis = joint.get_rig_axes(
            self.leg_root_ref
        )

        # get properties from the root joint
        self.useRefOrientation = cmds.getAttr("%s.useRefOri" % self.leg_root_ref)
        self.side = joint.get_joint_side(self.leg_root_ref)
        self.sideMult = -1 if self.side == "R" else 1

        # self.originalSuffix = suffix
        self.module_name = naming.unique_name(
            cmds.getAttr("%s.moduleName" % self.leg_root_ref)
        )

        # module variables
        self.ik_parent_grp = None
        self.leg_root_j_def = None
        self.hip_j_def = None
        self.mid_leg_j_def = None
        self.foot_j_def = None
        self.ball_j_def = None
        self.toe_j_def = None
        self.socket_ball_j = None
        self.ik_orig_root_j = None
        self.ik_orig_knee_j = None
        self.ik_orig_end_j = None

        self.ik_orig_root_j = None
        self.ik_orig_knee_j = None
        self.ik_orig_end_j = None
        self.ik_sc_root_j = None
        self.ik_sc_knee_j = None
        self.ik_sc_end_j = None
        self.ik_rp_root_j = None
        self.ik_rp_knee_j = None
        self.ik_rp_end_j = None
        self.ik_foot_j = None
        self.ik_ball_j = None
        self.ik_toe_j = None
        self.fk_root_j = None
        self.fk_knee_j = None
        self.fk_foot_j = None
        self.fk_ball_j = None
        self.fk_toe_j = None
        self.cont_thigh = None
        self.cont_thigh_auto = None
        self.cont_IK_foot = None
        self.cont_IK_foot_auto = None
        self.cont_pole = None
        self.cont_pole_vis = None
        self.cont_fk_up_leg = None
        self.cont_fk_up_leg_off = None
        self.cont_fk_up_leg_ore = None
        self.cont_fk_low_leg = None
        self.cont_fk_low_leg_off = None
        self.cont_fk_low_leg_ore = None
        self.cont_fk_foot = None
        self.cont_fk_foot_off = None
        self.cont_fk_foot_ore = None
        self.cont_fk_ball = None
        self.cont_fk_ball_off = None
        self.cont_fk_ball_ore = None
        self.cont_fk_ik = None
        self.cont_fk_ik_pos = None
        self.cont_mid_lock = None
        self.cont_mid_lock_pos = None
        self.cont_mid_lock_ave = None
        self.master_root = None
        self.start_lock = None
        self.start_lock_ore = None
        self.mid_lock = None
        self.end_lock = None
        self.end_lock_ore = None
        self.end_lock_pos = None
        self.initial_length_multip_sc = None
        self.stretchiness_sc = None

    def create_joints(self):
        # Create Limb Plug
        cmds.select(deselect=True)
        self.limbPlug = cmds.joint(
            name=naming.parse([self.module_name, "plug"], suffix="j"),
            position=self.leg_root_pos,
            radius=3,
        )

        self.leg_root_j_def = cmds.joint(
            name=naming.parse([self.module_name, "legRoot"], suffix="jDef"),
            position=self.leg_root_pos,
            radius=1.5,
        )
        self.sockets.append(self.leg_root_j_def)
        self.hip_j_def = cmds.joint(
            name=naming.parse([self.module_name, "hip"], suffix="jDef"),
            position=self.hip_pos,
            radius=1.5,
        )
        self.sockets.append(self.hip_j_def)

        if not self.useRefOrientation:
            joint.orient_joints(
                [self.leg_root_j_def, self.hip_j_def],
                world_up_axis=om.MVector(self.mirror_axis),
                reverse_aim=self.sideMult,
            )
        else:
            functions.align_to(
                self.leg_root_j_def, self.leg_root_ref, position=True, rotation=True
            )
            cmds.makeIdentity(self.leg_root_j_def, apply=True)
            functions.align_to(
                self.hip_j_def, self.hip_ref, position=True, rotation=True
            )
            cmds.makeIdentity(self.hip_j_def, apply=True)

        cmds.select(deselect=True)
        self.mid_leg_j_def = cmds.joint(
            name=naming.parse([self.module_name, "knee"], suffix="jDef"),
            position=self.knee_pos,
            radius=1.5,
        )
        self.sockets.append(self.mid_leg_j_def)

        cmds.select(deselect=True)
        self.foot_j_def = cmds.joint(
            name=naming.parse([self.module_name, "foot"], suffix="jDef"),
            position=self.foot_pos,
            radius=1.0,
        )
        self.sockets.append(self.foot_j_def)
        self.ball_j_def = cmds.joint(
            name=naming.parse([self.module_name, "ball"], suffix="jDef"),
            position=self.ball_pos,
            radius=1.0,
        )
        self.sockets.append(self.ball_j_def)
        self.toe_j_def = cmds.joint(
            name=naming.parse([self.module_name, "toe"], suffix="jDef"),
            position=self.toe_pv_pos,
            radius=1.0,
        )  # POSSIBLE PROBLEM
        self.sockets.append(self.toe_j_def)

        cmds.select(deselect=True)
        self.socket_ball_j = cmds.joint(
            name=naming.parse([self.module_name, "ball", "socket"], suffix="j"),
            position=self.ball_pos,
            radius=3,
        )
        self.sockets.append(self.socket_ball_j)
        # IK Joints
        # Follow IK Chain
        cmds.select(deselect=True)
        self.ik_orig_root_j = cmds.joint(
            name=naming.parse([self.module_name, "IK", "orig", "root"], suffix="j"),
            position=self.hip_pos,
            radius=1.5,
        )
        self.ik_orig_knee_j = cmds.joint(
            name=naming.parse([self.module_name, "IK", "orig", "knee"], suffix="j"),
            position=self.knee_pos,
            radius=1.5,
        )
        self.ik_orig_end_j = cmds.joint(
            name=naming.parse([self.module_name, "IK", "orig", "end"], suffix="j"),
            position=self.foot_pos,
            radius=1.5,
        )

        # Single Chain IK
        cmds.select(deselect=True)
        self.ik_sc_root_j = cmds.joint(
            name=naming.parse([self.module_name, "IK", "sc", "root"], suffix="j"),
            position=self.hip_pos,
            radius=1,
        )
        self.ik_sc_knee_j = cmds.joint(
            name=naming.parse([self.module_name, "IK", "sc", "knee"], suffix="j"),
            position=self.knee_pos,
            radius=1,
        )
        self.ik_sc_end_j = cmds.joint(
            name=naming.parse([self.module_name, "IK", "sc", "end"], suffix="j"),
            position=self.foot_pos,
            radius=1,
        )

        # Rotate Plane IK
        cmds.select(deselect=True)
        self.ik_rp_root_j = cmds.joint(
            name=naming.parse([self.module_name, "IK", "rp", "root"], suffix="j"),
            position=self.hip_pos,
            radius=0.7,
        )
        self.ik_rp_knee_j = cmds.joint(
            name=naming.parse([self.module_name, "IK", "rp", "knee"], suffix="j"),
            position=self.knee_pos,
            radius=0.7,
        )
        self.ik_rp_end_j = cmds.joint(
            name=naming.parse([self.module_name, "IK", "rp", "end"], suffix="j"),
            position=self.foot_pos,
            radius=0.7,
        )

        cmds.select(deselect=True)
        self.ik_foot_j = cmds.joint(
            name=naming.parse([self.module_name, "IK", "foot"], suffix="j"),
            position=self.foot_pos,
            radius=1.0,
        )
        self.ik_ball_j = cmds.joint(
            name=naming.parse([self.module_name, "IK", "ball"], suffix="j"),
            position=self.ball_pos,
            radius=1.0,
        )
        self.ik_toe_j = cmds.joint(
            name=naming.parse([self.module_name, "IK", "toe"], suffix="j"),
            position=self.toe_pv_pos,
            radius=1.0,
        )

        cmds.select(deselect=True)

        # orientations
        if not self.useRefOrientation:
            joint.orient_joints(
                [self.ik_orig_root_j, self.ik_orig_knee_j, self.ik_orig_end_j],
                world_up_axis=om.MVector(self.mirror_axis),
                reverse_aim=self.sideMult,
            )
        else:
            functions.align_to(
                self.ik_orig_root_j, self.hip_ref, position=True, rotation=True
            )
            cmds.makeIdentity(self.ik_orig_root_j, apply=True)
            functions.align_to(
                self.ik_orig_knee_j, self.knee_ref, position=True, rotation=True
            )
            cmds.makeIdentity(self.ik_orig_knee_j, apply=True)
            functions.align_to(
                self.ik_orig_end_j, self.foot_ref, position=True, rotation=True
            )
            cmds.makeIdentity(self.ik_orig_end_j, apply=True)

        if not self.useRefOrientation:
            joint.orient_joints(
                [self.ik_sc_root_j, self.ik_sc_knee_j, self.ik_sc_end_j],
                world_up_axis=om.MVector(self.mirror_axis),
                reverse_aim=self.sideMult,
            )
        else:
            functions.align_to(
                self.ik_sc_root_j, self.hip_ref, position=True, rotation=True
            )
            cmds.makeIdentity(self.ik_sc_root_j, apply=True)
            functions.align_to(
                self.ik_sc_knee_j, self.knee_ref, position=True, rotation=True
            )
            cmds.makeIdentity(self.ik_sc_knee_j, apply=True)
            functions.align_to(
                self.ik_sc_end_j, self.foot_ref, position=True, rotation=True
            )
            cmds.makeIdentity(self.ik_sc_end_j, apply=True)

        if not self.useRefOrientation:
            joint.orient_joints(
                [self.ik_rp_root_j, self.ik_rp_knee_j, self.ik_rp_end_j],
                world_up_axis=om.MVector(self.mirror_axis),
                reverse_aim=self.sideMult,
            )
        else:
            functions.align_to(
                self.ik_rp_root_j, self.hip_ref, position=True, rotation=True
            )
            cmds.makeIdentity(self.ik_rp_root_j, apply=True)
            functions.align_to(
                self.ik_rp_knee_j, self.knee_ref, position=True, rotation=True
            )
            cmds.makeIdentity(self.ik_rp_knee_j, apply=True)
            functions.align_to(
                self.ik_rp_end_j, self.foot_ref, position=True, rotation=True
            )
            cmds.makeIdentity(self.ik_rp_end_j, apply=True)

        if not self.useRefOrientation:
            joint.orient_joints(
                [self.ik_foot_j, self.ik_ball_j, self.ik_toe_j],
                world_up_axis=om.MVector(self.mirror_axis),
                reverse_aim=self.sideMult,
            )
        else:
            functions.align_to(
                self.ik_foot_j, self.foot_ref, position=True, rotation=True
            )
            cmds.makeIdentity(self.ik_foot_j, apply=True)
            functions.align_to(
                self.ik_ball_j, self.ball_ref, position=True, rotation=True
            )
            cmds.makeIdentity(self.ik_ball_j, apply=True)
            functions.align_to(
                self.ik_toe_j, self.toe_pv_ref, position=True, rotation=True
            )
            cmds.makeIdentity(self.ik_toe_j, apply=True)

        # FK Joints
        cmds.select(deselect=True)
        self.fk_root_j = cmds.joint(
            name=naming.parse([self.module_name, "FK", "upLeg"], suffix="j"),
            position=self.hip_pos,
            radius=1.0,
        )
        self.fk_knee_j = cmds.joint(
            name=naming.parse([self.module_name, "FK", "knee"], suffix="j"),
            position=self.knee_pos,
            radius=1.0,
        )
        self.fk_foot_j = cmds.joint(
            name=naming.parse([self.module_name, "FK", "foot"], suffix="j"),
            position=self.foot_pos,
            radius=1.0,
        )
        self.fk_ball_j = cmds.joint(
            name=naming.parse([self.module_name, "FK", "ball"], suffix="j"),
            position=self.ball_pos,
            radius=1.0,
        )
        self.fk_toe_j = cmds.joint(
            name=naming.parse([self.module_name, "FK", "toe"], suffix="j"),
            position=self.toe_pv_pos,
            radius=1.0,
        )

        if not self.useRefOrientation:
            joint.orient_joints(
                [
                    self.fk_root_j,
                    self.fk_knee_j,
                    self.fk_foot_j,
                    self.fk_ball_j,
                    self.fk_toe_j,
                ],
                world_up_axis=om.MVector(self.mirror_axis),
                reverse_aim=self.sideMult,
            )
        else:
            functions.align_to(
                self.fk_root_j, self.hip_ref, position=True, rotation=True
            )
            cmds.makeIdentity(self.fk_root_j, apply=True)
            functions.align_to(
                self.fk_knee_j, self.knee_ref, position=True, rotation=True
            )
            cmds.makeIdentity(self.fk_knee_j, apply=True)
            functions.align_to(
                self.fk_foot_j, self.foot_ref, position=True, rotation=True
            )
            cmds.makeIdentity(self.fk_foot_j, apply=True)
            functions.align_to(
                self.fk_ball_j, self.ball_ref, position=True, rotation=True
            )
            cmds.makeIdentity(self.fk_ball_j, apply=True)
            functions.align_to(
                self.fk_toe_j, self.toe_pv_ref, position=True, rotation=True
            )
            cmds.makeIdentity(self.fk_toe_j, apply=True)

        # re-orient single joints
        functions.align_to_alter(self.hip_j_def, self.fk_root_j, mode=2)
        cmds.makeIdentity(self.hip_j_def, apply=True)
        functions.align_to_alter(self.mid_leg_j_def, self.fk_knee_j, mode=2)
        cmds.makeIdentity(self.mid_leg_j_def, apply=True)

        functions.align_to_alter(self.foot_j_def, self.fk_foot_j, mode=2)
        cmds.makeIdentity(self.foot_j_def, apply=True)
        functions.align_to_alter(self.ball_j_def, self.fk_ball_j, mode=2)
        cmds.makeIdentity(self.ball_j_def, apply=True)
        functions.align_to_alter(self.toe_j_def, self.fk_toe_j, mode=2)
        cmds.makeIdentity(self.toe_j_def, apply=True)

        functions.align_to_alter(self.socket_ball_j, self.fk_ball_j, mode=2)
        cmds.makeIdentity(self.socket_ball_j, apply=True)
        cmds.parent(self.socket_ball_j, self.ball_j_def)

        cmds.parent(self.mid_leg_j_def, self.scaleGrp)
        cmds.parent(self.fk_root_j, self.scaleGrp)
        cmds.parent(self.foot_j_def, self.scaleGrp)

        self.deformerJoints += [
            self.mid_leg_j_def,
            self.hip_j_def,
            self.leg_root_j_def,
            self.foot_j_def,
            self.ball_j_def,
        ]

        cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % self.fk_root_j)

    def create_controllers(self):
        # Thigh Controller
        thigh_cont_scale = (
            self.init_upper_leg_dist / 4,
            self.init_upper_leg_dist / 4,
            self.init_upper_leg_dist / 16,
        )
        self.cont_thigh = Controller(
            name=naming.parse([self.module_name, "thigh"], suffix="cont"),
            shape="Cube",
            scale=thigh_cont_scale,
            normal=(0, 0, self.sideMult),
            side=self.side,
            tier="primary",
        )
        self.controllers.append(self.cont_thigh)
        functions.align_to_alter(self.cont_thigh.name, self.fk_root_j, mode=2)
        cmds.move(
            0,
            self.sideMult * (thigh_cont_scale[0] * 2),
            0,
            self.cont_thigh.name,
            relative=True,
            objectSpace=True,
        )
        cmds.xform(self.cont_thigh.name, pivots=self.leg_root_pos, worldSpace=True)

        cont_thigh_off = self.cont_thigh.add_offset("OFF")
        cont_thigh_ore = self.cont_thigh.add_offset("ORE")
        self.cont_thigh_auto = self.cont_thigh.add_offset("Auto")

        cmds.xform(cont_thigh_off, pivots=self.leg_root_pos, worldSpace=True)
        cmds.xform(cont_thigh_ore, pivots=self.leg_root_pos, worldSpace=True)
        cmds.xform(self.cont_thigh_auto, pivots=self.leg_root_pos, worldSpace=True)

        self.cont_thigh.freeze()
        # cmds.makeIdentity(self.cont_thigh, a=True)

        # IK Foot Controller
        foot_cont_scale = (self.init_foot_length * 0.75, 1, self.init_foot_width * 0.8)
        self.cont_IK_foot = Controller(
            name=naming.parse([self.module_name, "IK", "foot"], suffix="cont"),
            shape="Circle",
            scale=foot_cont_scale,
            normal=(0, 0, self.sideMult),
            side=self.side,
            tier="primary",
        )
        self.controllers.append(self.cont_IK_foot)
        # align it to the ball socket
        functions.align_to_alter(self.cont_IK_foot.name, self.socket_ball_j, mode=2)
        cmds.xform(
            self.cont_IK_foot.name, pivots=self.foot_pos, preserve=True, worldSpace=True
        )

        self.cont_IK_OFF = self.cont_IK_foot.add_offset("OFF")
        _cont_ik_foot_ore = self.cont_IK_foot.add_offset("ORE")
        _cont_ik_foot_pos = self.cont_IK_foot.add_offset("POS")

        self.cont_IK_foot.freeze()

        cmds.addAttr(
            self.cont_IK_foot.name,
            shortName="polevector",
            longName="Pole_Vector",
            defaultValue=0.0,
            minValue=0.0,
            maxValue=1.0,
            attributeType="double",
            keyable=True,
        )
        cmds.addAttr(
            self.cont_IK_foot.name,
            shortName="sUpLeg",
            longName="Scale_Upper_Leg",
            defaultValue=1.0,
            minValue=0.0,
            attributeType="double",
            keyable=True,
        )
        cmds.addAttr(
            self.cont_IK_foot.name,
            shortName="sLowLeg",
            longName="Scale_Lower_Leg",
            defaultValue=1.0,
            minValue=0.0,
            attributeType="double",
            keyable=True,
        )
        cmds.addAttr(
            self.cont_IK_foot.name,
            shortName="squash",
            longName="Squash",
            defaultValue=0.0,
            minValue=0.0,
            maxValue=1.0,
            attributeType="double",
            keyable=True,
        )
        cmds.addAttr(
            self.cont_IK_foot.name,
            shortName="stretch",
            longName="Stretch",
            defaultValue=1.0,
            minValue=0.0,
            maxValue=1.0,
            attributeType="double",
            keyable=True,
        )
        cmds.addAttr(
            self.cont_IK_foot.name,
            shortName="stretchLimit",
            longName="StretchLimit",
            defaultValue=100.0,
            minValue=0.0,
            maxValue=1000.0,
            attributeType="double",
            keyable=True,
        )
        cmds.addAttr(
            self.cont_IK_foot.name,
            shortName="softIK",
            longName="SoftIK",
            defaultValue=0.0,
            minValue=0.0,
            maxValue=100.0,
            keyable=True,
        )
        cmds.addAttr(
            self.cont_IK_foot.name,
            shortName="volume",
            longName="Volume_Preserve",
            defaultValue=0.0,
            attributeType="double",
            keyable=True,
        )
        cmds.addAttr(
            self.cont_IK_foot.name,
            shortName="bLean",
            longName="Ball_Lean",
            defaultValue=0.0,
            attributeType="double",
            keyable=True,
        )
        cmds.addAttr(
            self.cont_IK_foot.name,
            shortName="bRoll",
            longName="Ball_Roll",
            defaultValue=0.0,
            attributeType="double",
            keyable=True,
        )
        cmds.addAttr(
            self.cont_IK_foot.name,
            shortName="bSpin",
            longName="Ball_Spin",
            defaultValue=0.0,
            attributeType="double",
            keyable=True,
        )
        cmds.addAttr(
            self.cont_IK_foot.name,
            shortName="hRoll",
            longName="Heel_Roll",
            defaultValue=0.0,
            attributeType="double",
            keyable=True,
        )
        cmds.addAttr(
            self.cont_IK_foot.name,
            shortName="hSpin",
            longName="Heel_Spin",
            defaultValue=0.0,
            attributeType="double",
            keyable=True,
        )
        cmds.addAttr(
            self.cont_IK_foot.name,
            shortName="tRoll",
            longName="Toes_Roll",
            defaultValue=0.0,
            attributeType="double",
            keyable=True,
        )
        cmds.addAttr(
            self.cont_IK_foot.name,
            shortName="tSpin",
            longName="Toes_Spin",
            defaultValue=0.0,
            attributeType="double",
            keyable=True,
        )
        cmds.addAttr(
            self.cont_IK_foot.name,
            shortName="tWiggle",
            longName="Toes_Wiggle",
            defaultValue=0.0,
            attributeType="double",
            keyable=True,
        )
        cmds.addAttr(
            self.cont_IK_foot.name,
            shortName="bank",
            longName="Bank",
            defaultValue=0.0,
            attributeType="double",
            keyable=True,
        )

        # Pole Vector Controller
        polecont_scale = (
            (((self.init_upper_leg_dist + self.init_lower_leg_dist) / 2) / 10),
            (((self.init_upper_leg_dist + self.init_lower_leg_dist) / 2) / 10),
            (((self.init_upper_leg_dist + self.init_lower_leg_dist) / 2) / 10),
        )
        self.cont_pole = Controller(
            name=naming.parse([self.module_name, "poleVector"], suffix="cont"),
            shape="Plus",
            scale=polecont_scale,
            normal=self.mirror_axis,
            side=self.side,
            tier="primary",
        )

        self.controllers.append(self.cont_pole)
        offset_mag_pole = (self.init_upper_leg_dist + self.init_lower_leg_dist) / 4
        offset_vector_pole = api.get_between_vector(
            self.mid_leg_j_def, [self.hip_j_def, self.fk_foot_j]
        )

        functions.align_and_aim(
            self.cont_pole.name,
            target_list=[self.mid_leg_j_def],
            aim_target_list=[self.hip_j_def, self.fk_foot_j],
            up_vector=self.up_axis,
            translate_offset=(offset_vector_pole * offset_mag_pole),
        )

        cont_pole_off = self.cont_pole.add_offset("OFF")
        self.cont_pole_vis = self.cont_pole.add_offset("VIS")

        # FK UP Leg Controller
        scalecont_fk_up_leg = (
            self.init_upper_leg_dist / 2,
            self.init_upper_leg_dist / 6,
            self.init_upper_leg_dist / 6,
        )

        self.cont_fk_up_leg = Controller(
            name=naming.parse([self.module_name, "FK", "upLeg"], suffix="cont"),
            shape="Cube",
            scale=scalecont_fk_up_leg,
            side=self.side,
            tier="primary",
        )
        self.controllers.append(self.cont_fk_up_leg)

        # move the pivot to the bottom
        cmds.xform(
            self.cont_fk_up_leg.name,
            pivots=(self.sideMult * -(self.init_upper_leg_dist / 2), 0, 0),
            worldSpace=True,
        )

        # move the controller to the shoulder
        functions.align_to_alter(self.cont_fk_up_leg.name, self.fk_root_j, mode=2)

        self.cont_fk_up_leg_off = self.cont_fk_up_leg.add_offset("OFF")
        self.cont_fk_up_leg_ore = self.cont_fk_up_leg.add_offset("ORE")
        cmds.xform(self.cont_fk_up_leg_off, pivots=self.hip_pos, worldSpace=True)
        cmds.xform(self.cont_fk_up_leg_ore, pivots=self.hip_pos, worldSpace=True)

        # FK LOW Leg Controller
        scalecont_fk_low_leg = (
            self.init_lower_leg_dist / 2,
            self.init_lower_leg_dist / 6,
            self.init_lower_leg_dist / 6,
        )
        self.cont_fk_low_leg = Controller(
            name=naming.parse([self.module_name, "FK", "lowLeg"], suffix="cont"),
            shape="Cube",
            scale=scalecont_fk_low_leg,
            side=self.side,
            tier="primary",
        )
        self.controllers.append(self.cont_fk_low_leg)

        # move the pivot to the bottom
        cmds.xform(
            self.cont_fk_low_leg.name,
            pivots=(self.sideMult * -(self.init_lower_leg_dist / 2), 0, 0),
            worldSpace=True,
        )

        # align position and orientation to the joint
        functions.align_to_alter(self.cont_fk_low_leg.name, self.fk_knee_j, mode=2)

        self.cont_fk_low_leg_off = self.cont_fk_low_leg.add_offset("OFF")
        self.cont_fk_low_leg_ore = self.cont_fk_low_leg.add_offset("ORE")
        cmds.xform(self.cont_fk_low_leg_off, pivots=self.knee_pos, worldSpace=True)
        cmds.xform(self.cont_fk_low_leg_ore, pivots=self.knee_pos, worldSpace=True)

        # FK FOOT Controller
        scalecont_fk_foot = (
            self.init_ball_dist / 2,
            self.init_ball_dist / 3,
            self.init_foot_width / 2,
        )
        self.cont_fk_foot = Controller(
            name=naming.parse([self.module_name, "FK", "foot"], suffix="cont"),
            shape="Cube",
            scale=scalecont_fk_foot,
            side=self.side,
            tier="primary",
        )
        self.controllers.append(self.cont_fk_foot)
        functions.align_to_alter(self.cont_fk_foot.name, self.fk_foot_j, mode=2)

        self.cont_fk_foot_off = self.cont_fk_foot.add_offset("OFF")
        self.cont_fk_foot_ore = self.cont_fk_foot.add_offset("ORE")

        # FK Ball Controller
        scalecont_fk_ball = (
            self.init_toe_dist / 2,
            self.init_toe_dist / 3,
            self.init_foot_width / 2,
        )
        self.cont_fk_ball = Controller(
            name=naming.parse([self.module_name, "FK", "ball"], suffix="cont"),
            shape="Cube",
            scale=scalecont_fk_ball,
            side=self.side,
            tier="primary",
        )
        self.controllers.append(self.cont_fk_ball)
        functions.align_to_alter(self.cont_fk_ball.name, self.fk_ball_j, mode=2)

        self.cont_fk_ball_off = self.cont_fk_ball.add_offset("OFF")
        self.cont_fk_ball_ore = self.cont_fk_ball.add_offset("ORE")

        # FK-IK SWITCH Controller
        icon_scale = self.init_upper_leg_dist / 4
        self.cont_fk_ik = Controller(
            name=naming.parse([self.module_name, "FKIK", "switch"], suffix="cont"),
            shape="FkikSwitch",
            scale=(icon_scale, icon_scale, icon_scale),
            side=self.side,
            tier="primary",
        )
        self.controllers.append(self.cont_fk_ik)

        functions.align_and_aim(
            self.cont_fk_ik.name,
            target_list=[self.fk_foot_j],
            aim_target_list=[self.mid_leg_j_def],
            up_vector=self.up_axis,
            rotate_offset=(self.sideMult * 90, self.sideMult * 90, 0),
        )
        cmds.move(
            icon_scale * 2, 0, 0, self.cont_fk_ik.name, relative=True, objectSpace=True
        )
        self.cont_fk_ik_pos = self.cont_fk_ik.add_offset("POS")

        cmds.setAttr("{0}.s{1}".format(self.cont_fk_ik.name, "x"), self.sideMult)

        # controller for twist orientation alignment
        cmds.addAttr(
            self.cont_fk_ik.name,
            shortName="autoHip",
            longName="Auto_Hip",
            defaultValue=1.0,
            attributeType="float",
            minValue=0.0,
            maxValue=1.0,
            keyable=True,
        )
        cmds.addAttr(
            self.cont_fk_ik.name,
            shortName="alignHip",
            longName="Align_Hip",
            defaultValue=0.0,
            attributeType="float",
            minValue=0.0,
            maxValue=1.0,
            keyable=True,
        )
        cmds.addAttr(
            self.cont_fk_ik.name,
            shortName="footAutoTwist",
            longName="Foot_Auto_Twist",
            defaultValue=1.0,
            minValue=0.0,
            maxValue=1.0,
            attributeType="float",
            keyable=True,
        )
        cmds.addAttr(
            self.cont_fk_ik.name,
            shortName="footManualTwist",
            longName="Foot_Manual_Twist",
            defaultValue=0.0,
            attributeType="float",
            keyable=True,
        )
        cmds.addAttr(
            self.cont_fk_ik.name,
            shortName="upLegAutoTwist",
            longName="UpLeg_Auto_Twist",
            defaultValue=1.0,
            minValue=0.0,
            maxValue=1.0,
            attributeType="float",
            keyable=True,
        )
        cmds.addAttr(
            self.cont_fk_ik.name,
            shortName="upLegManualTwist",
            longName="UpLeg_Manual_Twist",
            defaultValue=0.0,
            attributeType="float",
            keyable=True,
        )
        cmds.addAttr(
            self.cont_fk_ik.name,
            shortName="allowScaling",
            longName="Allow_Scaling",
            defaultValue=1.0,
            minValue=0.0,
            maxValue=1.0,
            attributeType="float",
            keyable=True,
        )
        cmds.addAttr(
            self.cont_fk_ik.name,
            attributeType="enum",
            keyable=True,
            shortName="interpType",
            longName="Interp_Type",
            enumName="No_Flip:Average:Shortest:Longest:Cache",
            defaultValue=0,
        )
        cmds.addAttr(
            self.cont_fk_ik.name,
            shortName="tweakControls",
            longName="Tweak_Controls",
            defaultValue=0,
            attributeType="bool",
        )
        cmds.setAttr("%s.tweakControls" % self.cont_fk_ik.name, channelBox=True)
        cmds.addAttr(
            self.cont_fk_ik.name,
            shortName="fingerControls",
            longName="Finger_Controls",
            defaultValue=1,
            attributeType="bool",
        )
        cmds.setAttr("%s.fingerControls" % self.cont_fk_ik.name, channelBox=True)

        # Create MidLock controller

        midcont_scale = (
            self.init_lower_leg_dist / 4,
            self.init_lower_leg_dist / 4,
            self.init_lower_leg_dist / 4,
        )
        self.cont_mid_lock = Controller(
            name=naming.parse([self.module_name, "mid"], suffix="cont"),
            shape="Star",
            scale=midcont_scale,
            normal=self.mirror_axis,
            side=self.side,
            tier="secondary",
        )
        self.controllers.append(self.cont_mid_lock)

        functions.align_to_alter(self.cont_mid_lock.name, self.fk_knee_j, 2)
        cont_mid_lock_ext = self.cont_mid_lock.add_offset("EXT")
        self.cont_mid_lock_pos = self.cont_mid_lock.add_offset("POS")
        self.cont_mid_lock_ave = self.cont_mid_lock.add_offset("AVE")

        cmds.parent(cont_thigh_off, self.scaleGrp)
        cmds.parent(self.cont_fk_up_leg_off, self.scaleGrp)
        cmds.parent(self.cont_fk_low_leg_off, self.scaleGrp)
        cmds.parent(self.cont_fk_foot_off, self.scaleGrp)
        cmds.parent(cont_mid_lock_ext, self.scaleGrp)
        cmds.parent(cont_pole_off, self.scaleGrp)
        cmds.parent(self.cont_fk_ik_pos, self.scaleGrp)
        cmds.parent(self.cont_fk_ball_off, self.scaleGrp)
        cmds.parent(self.cont_IK_OFF, self.limbGrp)

        nodes_cont_vis = [
            cont_pole_off,
            cont_thigh_off,
            self.cont_IK_OFF,
            self.cont_fk_foot_off,
            self.cont_fk_ik_pos,
            self.cont_fk_ball_off,
            self.cont_fk_low_leg_off,
            self.cont_fk_up_leg_off,
            self.cont_mid_lock_pos,
        ]

        attribute.drive_attrs(
            "%s.contVis" % self.scaleGrp, ["%s.v" % x for x in nodes_cont_vis]
        )

    def create_roots(self):
        self.master_root = cmds.group(
            empty=True,
            name=naming.parse([self.module_name, "masterRoot"], suffix="grp"),
        )
        functions.align_to(self.master_root, self.leg_root_ref, 0)
        cmds.makeIdentity(self.master_root, apply=True)

        # Create Start Lock

        self.start_lock = cmds.spaceLocator(
            name=naming.parse([self.module_name, "startLock"], suffix="loc")
        )[0]
        functions.align_to_alter(self.start_lock, self.ik_orig_root_j, 2)
        self.start_lock_ore = functions.create_offset_group(self.start_lock, "_Ore")
        _start_lock_pos = functions.create_offset_group(self.start_lock, "_Pos")
        _start_lock_twist = functions.create_offset_group(self.start_lock, "_AutoTwist")

        _start_lock_weight = cmds.parentConstraint(
            self.hip_j_def, self.start_lock, skipRotate=["y", "z"], maintainOffset=False
        )

        cmds.parentConstraint(self.start_lock, self.ik_sc_root_j, maintainOffset=True)
        cmds.parentConstraint(self.start_lock, self.ik_rp_root_j, maintainOffset=True)

        # Create Midlock

        self.mid_lock = cmds.spaceLocator(
            name=naming.parse([self.module_name, "midLock"], suffix="loc")
        )[0]
        cmds.parentConstraint(self.mid_lock, self.mid_leg_j_def)
        cmds.parentConstraint(
            self.cont_mid_lock.name, self.mid_lock, maintainOffset=False
        )

        # Create End Lock
        self.end_lock = cmds.spaceLocator(
            name=naming.parse([self.module_name, "endLock"], suffix="loc")
        )[0]
        functions.align_to(self.end_lock, self.fk_foot_j, position=True, rotation=True)
        self.end_lock_ore = functions.create_offset_group(self.end_lock, "Ore")
        self.end_lock_pos = functions.create_offset_group(self.end_lock, "Pos")
        end_lock_twist = functions.create_offset_group(self.end_lock, "Twist")

        cmds.parent(self.mid_lock, self.scaleGrp)
        cmds.parent(self.master_root, self.scaleGrp)

        cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % end_lock_twist)
        cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % self.start_lock_ore)
        cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % self.mid_lock)
        cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % self.master_root)

    def create_ik_setup(self):
        master_ik = cmds.spaceLocator(
            name=naming.parse([self.module_name, "IK", "master"], suffix="loc")
        )[0]
        functions.align_to(master_ik, self.foot_j_def)

        # axis for foot control groups
        foot_plane = cmds.spaceLocator(name="footPlaneLocator_TEMP")[0]
        cmds.setAttr("%s.rotateOrder" % foot_plane, 0)
        cmds.pointConstraint(self.heel_pv_ref, self.toe_pv_ref, foot_plane)
        cmds.aimConstraint(
            self.toe_pv_ref,
            foot_plane,
            worldUpObject=self.foot_ref,
            worldUpType="object",
        )

        pv_bank_in = cmds.group(
            name=naming.parse([self.module_name, "piv", "bankIn"], suffix="grp"),
            empty=True,
        )
        functions.align_to(pv_bank_in, self.bank_in_ref, position=True, rotation=True)
        cmds.makeIdentity(
            pv_bank_in, apply=True, translate=False, rotate=True, scale=True
        )
        pln_rot = cmds.getAttr("%s.rotate" % foot_plane)[0]
        cmds.setAttr("%s.rotate" % pv_bank_in, pln_rot[0], pln_rot[1], pln_rot[2])
        # cmds.parent(self.mid_lock, self.scaleGrp)

        pv_bank_out = cmds.group(name="Pv_BankOut_%s" % self.module_name, empty=True)
        functions.align_to(pv_bank_out, self.bank_out_ref, position=True, rotation=True)
        cmds.makeIdentity(
            pv_bank_out, apply=True, translate=False, rotate=True, scale=True
        )
        cmds.setAttr("%s.rotate" % pv_bank_out, pln_rot[0], pln_rot[1], pln_rot[2])

        pv_toe = cmds.group(
            name=naming.parse([self.module_name, "piv", "toe"], suffix="grp"),
            empty=True,
        )
        functions.align_to(pv_toe, self.toe_pv_ref, position=True, rotation=True)
        pv_toe_ore = functions.create_offset_group(pv_toe, "ORE")

        pv_ball = cmds.group(
            name=naming.parse([self.module_name, "piv", "ball"], suffix="grp"),
            empty=True,
        )
        functions.align_to(pv_ball, self.ball_ref, position=True, rotation=False)
        pv_ball_ore = functions.create_offset_group(pv_ball, "ORE")

        # TODO // SOCKETBALL NEEDS A IK/FK Switch

        pv_heel = cmds.group(
            name=naming.parse([self.module_name, "piv", "heel"], suffix="grp"),
            empty=True,
        )
        functions.align_to(pv_heel, self.heel_pv_ref, position=True, rotation=True)
        pv_heel_ore = functions.create_offset_group(pv_heel, "ORE")

        pv_ball_spin = cmds.group(
            name=naming.parse([self.module_name, "piv", "ballSpin"], suffix="grp"),
            empty=True,
        )
        functions.align_to(pv_ball_spin, self.ball_ref, position=True, rotation=True)
        pv_ball_spin_ore = functions.create_offset_group(pv_ball_spin, "ORE")

        pv_ball_roll = cmds.group(
            name=naming.parse([self.module_name, "piv", "ballRoll"], suffix="grp"),
            empty=True,
        )
        functions.align_to(pv_ball_roll, self.ball_ref, position=True, rotation=True)
        pv_ball_roll_ore = functions.create_offset_group(pv_ball_roll, "ORE")

        pv_ball_lean = cmds.group(
            name=naming.parse([self.module_name, "piv", "ballLean"], suffix="grp"),
            empty=True,
        )
        functions.align_to(pv_ball_lean, self.ball_ref, position=True, rotation=True)
        pv_ball_lean_ore = functions.create_offset_group(pv_ball_lean, "ORE")

        # Create IK handles

        ik_handle_sc = cmds.ikHandle(
            startJoint=self.ik_sc_root_j,
            endEffector=self.ik_sc_end_j,
            name=naming.parse([self.module_name, "sc"], suffix="IKHandle"),
        )
        ik_handle_rp = cmds.ikHandle(
            startJoint=self.ik_rp_root_j,
            endEffector=self.ik_rp_end_j,
            name=naming.parse([self.module_name, "rp"], suffix="IKHandle"),
            solver="ikRPsolver",
        )

        cmds.poleVectorConstraint(self.cont_pole.name, ik_handle_rp[0])
        cmds.aimConstraint(self.ik_rp_knee_j, self.cont_pole.name)

        ik_handle_ball = cmds.ikHandle(
            startJoint=self.ik_foot_j,
            endEffector=self.ik_ball_j,
            name=naming.parse([self.module_name, "ball"], suffix="IKHandle"),
        )
        ik_handle_toe = cmds.ikHandle(
            startJoint=self.ik_ball_j,
            endEffector=self.ik_toe_j,
            name=naming.parse([self.module_name, "toe"], suffix="IKHandle"),
        )

        # Create Hierarchy for Foot

        cmds.parent(ik_handle_ball[0], pv_ball)
        cmds.parent(ik_handle_toe[0], pv_ball)
        cmds.parent(master_ik, pv_ball_lean)
        cmds.parent(ik_handle_sc[0], master_ik)
        cmds.parent(ik_handle_rp[0], master_ik)
        cmds.parent(pv_ball_lean_ore, pv_ball_roll)
        cmds.parent(pv_ball_ore, pv_toe)
        cmds.parent(pv_ball_roll_ore, pv_toe)
        cmds.parent(pv_toe_ore, pv_ball_spin)
        cmds.parent(pv_ball_spin_ore, pv_heel)
        cmds.parent(pv_heel_ore, pv_bank_out)
        cmds.parent(pv_bank_out, pv_bank_in)

        # Create and constrain Distance Locators

        leg_start = cmds.spaceLocator(
            name=naming.parse([self.module_name, "legStart"], suffix="loc")
        )[0]
        cmds.pointConstraint(self.start_lock, leg_start, maintainOffset=False)

        leg_end = cmds.spaceLocator(
            name=naming.parse([self.module_name, "legEnd"], suffix="loc")
        )[0]
        cmds.pointConstraint(master_ik, leg_end, maintainOffset=False)

        # Create Nodes and Connections for Stretchy IK SC

        stretch_offset = cmds.createNode(
            "plusMinusAverage",
            name=naming.parse([self.module_name, "stretchOffset"], suffix="pma"),
        )
        distance_sc = cmds.createNode(
            "distanceBetween",
            name=naming.parse([self.module_name, "sc"], suffix="distance"),
        )
        ik_stretch_distance_clamp = cmds.createNode(
            "clamp",
            name=naming.parse(
                [self.module_name, "IK", "strecthDistance"], suffix="clamp"
            ),
        )
        ik_stretch_stretchiness_clamp = cmds.createNode(
            "clamp",
            name=naming.parse(
                [self.module_name, "IK", "stretchinessClamp"], suffix="clamp"
            ),
        )
        extra_scale_mult_sc = cmds.createNode(
            "multiplyDivide",
            name=naming.parse([self.module_name, "sc", "extraScale"], suffix="mult"),
        )
        initial_divide_sc = cmds.createNode(
            "multiplyDivide",
            name=naming.parse([self.module_name, "sc", "initialDivide"], suffix="div"),
        )
        self.initial_length_multip_sc = cmds.createNode(
            "multiplyDivide",
            name=naming.parse(
                [self.module_name, "sc", "initialLengthMultip"], suffix="mult"
            ),
        )
        stretch_amount_sc = cmds.createNode(
            "multiplyDivide",
            name=naming.parse([self.module_name, "sc", "stretchAmount"], suffix="mult"),
        )
        sum_of_j_lengths_sc = cmds.createNode(
            "plusMinusAverage",
            name=naming.parse([self.module_name, "sc", "sumOfJLengths"], suffix="pma"),
        )
        squashiness_sc = cmds.createNode(
            "blendColors",
            name=naming.parse([self.module_name, "sc", "squashiness"], suffix="blend"),
        )
        self.stretchiness_sc = cmds.createNode(
            "blendColors",
            name=naming.parse([self.module_name, "sc", "stretchiness"], suffix="blend"),
        )

        cmds.setAttr("%s.maxR" % ik_stretch_stretchiness_clamp, 1)
        cmds.setAttr(
            "%s.input1X" % self.initial_length_multip_sc, self.init_upper_leg_dist
        )
        cmds.setAttr(
            "%s.input1Y" % self.initial_length_multip_sc, self.init_lower_leg_dist
        )
        cmds.setAttr("%s.operation" % initial_divide_sc, 2)

        # IkSoft nodes
        ik_soft_clamp = cmds.createNode(
            "clamp", name=naming.parse([self.module_name, "ikSoft"], suffix="clamp")
        )
        cmds.setAttr("%s.minR" % ik_soft_clamp, 0.0001)
        cmds.setAttr("%s.maxR" % ik_soft_clamp, 99999)

        ik_soft_sub1 = cmds.createNode(
            "plusMinusAverage",
            name=naming.parse([self.module_name, "ikSoft", "sub1"], suffix="pma"),
        )
        cmds.setAttr("%s.operation" % ik_soft_sub1, 2)

        ik_soft_sub2 = cmds.createNode(
            "plusMinusAverage",
            name=naming.parse([self.module_name, "ikSoft", "sub2"], suffix="pma"),
        )
        cmds.setAttr("%s.operation" % ik_soft_sub2, 2)

        ik_soft_div1 = cmds.createNode(
            "multiplyDivide",
            name=naming.parse([self.module_name, "ikSoft", "div1"], suffix="mult"),
        )
        cmds.setAttr("%s.operation" % ik_soft_div1, 2)

        ik_soft_mult1 = cmds.createNode(
            "multDoubleLinear",
            name=naming.parse([self.module_name, "ikSoft", "mult1"], suffix="mult"),
        )
        cmds.setAttr("%s.input1" % ik_soft_mult1, -1)

        ik_soft_pow = cmds.createNode(
            "multiplyDivide",
            name=naming.parse([self.module_name, "ikSoft", "pow"], suffix="mult"),
        )
        cmds.setAttr("%s.operation" % ik_soft_pow, 3)
        cmds.setAttr("%s.input1X" % ik_soft_pow, 2.718)

        ik_soft_mult2 = cmds.createNode(
            "multDoubleLinear",
            name=naming.parse([self.module_name, "ikSoft", "mult2"], suffix="mult"),
        )

        ik_soft_sub3 = cmds.createNode(
            "plusMinusAverage",
            name=naming.parse([self.module_name, "ikSoft", "sub3"], suffix="mult"),
        )
        cmds.setAttr("%s.operation" % ik_soft_sub3, 2)

        ik_soft_condition = cmds.createNode(
            "condition", name=naming.parse([self.module_name, "ikSoft"], suffix="cond")
        )
        cmds.setAttr("%s.operation" % ik_soft_condition, 2)

        ik_soft_div2 = cmds.createNode(
            "multiplyDivide",
            name=naming.parse([self.module_name, "ikSoft", "div2"], suffix="mult"),
        )
        cmds.setAttr("%s.operation" % ik_soft_div2, 2)

        ik_soft_stretch_amount = cmds.createNode(
            "multiplyDivide",
            name=naming.parse(
                [self.module_name, "ikSoft", "sc", "stretchAmount"], suffix="mult"
            ),
        )
        cmds.setAttr("%s.operation" % ik_soft_stretch_amount, 1)

        # Bind Attributes and make constraints

        # Bind Stretch Attributes
        cmds.connectAttr("%s.translate" % leg_start, "%s.point1" % distance_sc)
        cmds.connectAttr("%s.translate" % leg_end, "%s.point2" % distance_sc)
        cmds.connectAttr(
            "%s.distance" % distance_sc, "%s.inputR" % ik_stretch_distance_clamp
        )
        cmds.connectAttr(
            "%s.outputR" % ik_stretch_distance_clamp, "%s.input1X" % initial_divide_sc
        )
        cmds.connectAttr(
            "%s.outputR" % ik_stretch_stretchiness_clamp,
            "%s.blender" % self.stretchiness_sc,
        )
        cmds.connectAttr(
            "%s.outputX" % initial_divide_sc, "%s.input2X" % stretch_amount_sc
        )
        cmds.connectAttr(
            "%s.outputX" % initial_divide_sc, "%s.input2Y" % stretch_amount_sc
        )
        cmds.connectAttr(
            "%s.outputX" % self.initial_length_multip_sc,
            "%s.input1X" % extra_scale_mult_sc,
        )
        cmds.connectAttr(
            "%s.outputY" % self.initial_length_multip_sc,
            "%s.input1Y" % extra_scale_mult_sc,
        )
        cmds.connectAttr(
            "%s.outputX" % self.initial_length_multip_sc,
            "%s.input1D[0]" % stretch_offset,
        )
        cmds.connectAttr(
            "%s.outputY" % self.initial_length_multip_sc,
            "%s.input1D[1]" % stretch_offset,
        )
        cmds.connectAttr(
            "%s.outputX" % extra_scale_mult_sc, "%s.input1X" % stretch_amount_sc
        )
        cmds.connectAttr(
            "%s.outputY" % extra_scale_mult_sc, "%s.input1Y" % stretch_amount_sc
        )
        cmds.connectAttr(
            "%s.outputX" % extra_scale_mult_sc, "%s.color2R" % self.stretchiness_sc
        )
        cmds.connectAttr(
            "%s.outputY" % extra_scale_mult_sc, "%s.color2G" % self.stretchiness_sc
        )
        cmds.connectAttr(
            "%s.outputX" % extra_scale_mult_sc, "%s.input1D[0]" % sum_of_j_lengths_sc
        )
        cmds.connectAttr(
            "%s.outputY" % extra_scale_mult_sc, "%s.input1D[1]" % sum_of_j_lengths_sc
        )
        cmds.connectAttr(
            "%s.outputX" % stretch_amount_sc, "%s.color1R" % squashiness_sc
        )
        cmds.connectAttr(
            "%s.outputY" % stretch_amount_sc, "%s.color1G" % squashiness_sc
        )
        cmds.connectAttr(
            "%s.output1D" % sum_of_j_lengths_sc, "%s.input2X" % initial_divide_sc
        )
        cmds.connectAttr(
            "%s.outputR" % squashiness_sc, "%s.color1R" % self.stretchiness_sc
        )
        cmds.connectAttr(
            "%s.outputG" % squashiness_sc, "%s.color1G" % self.stretchiness_sc
        )

        inverted_str_sc = cmds.createNode("multiplyDivide")
        cmds.setAttr("%s.input2X" % inverted_str_sc, self.sideMult)
        cmds.setAttr("%s.input2Y" % inverted_str_sc, self.sideMult)

        cmds.connectAttr(
            "%s.outputR" % self.stretchiness_sc, "%s.input1X" % inverted_str_sc
        )
        cmds.connectAttr(
            "%s.outputG" % self.stretchiness_sc, "%s.input1Y" % inverted_str_sc
        )

        cmds.connectAttr(
            "%s.outputX" % inverted_str_sc, "%s.translateX" % self.ik_sc_knee_j
        )
        cmds.connectAttr(
            "%s.outputY" % inverted_str_sc, "%s.translateX" % self.ik_sc_end_j
        )
        cmds.connectAttr(
            "%s.outputX" % inverted_str_sc, "%s.translateX" % self.ik_rp_knee_j
        )
        cmds.connectAttr(
            "%s.outputY" % inverted_str_sc, "%s.translateX" % self.ik_rp_end_j
        )

        # iksoft related
        cmds.connectAttr(
            "%s.softIK" % self.cont_IK_foot.name, "%s.inputR" % ik_soft_clamp
        )

        cmds.connectAttr(
            "%s.output1D" % sum_of_j_lengths_sc, "%s.input1D[0]" % ik_soft_sub1
        )
        cmds.connectAttr("%s.outputR" % ik_soft_clamp, "%s.input1D[1]" % ik_soft_sub1)
        cmds.connectAttr(
            "%s.outputR" % ik_stretch_distance_clamp, "%s.input1D[0]" % ik_soft_sub2
        )
        cmds.connectAttr("%s.output1D" % ik_soft_sub1, "%s.input1D[1]" % ik_soft_sub2)
        cmds.connectAttr("%s.output1D" % ik_soft_sub2, "%s.input1X" % ik_soft_div1)
        cmds.connectAttr("%s.outputR" % ik_soft_clamp, "%s.input2X" % ik_soft_div1)
        cmds.connectAttr("%s.outputX" % ik_soft_div1, "%s.input2" % ik_soft_mult1)

        cmds.connectAttr("%s.output" % ik_soft_mult1, "%s.input2X" % ik_soft_pow)
        cmds.connectAttr("%s.outputR" % ik_soft_clamp, "%s.input1" % ik_soft_mult2)
        cmds.connectAttr("%s.outputX" % ik_soft_pow, "%s.input2" % ik_soft_mult2)
        cmds.connectAttr(
            "%s.output1D" % sum_of_j_lengths_sc, "%s.input1D[0]" % ik_soft_sub3
        )
        cmds.connectAttr("%s.output" % ik_soft_mult2, "%s.input1D[1]" % ik_soft_sub3)
        cmds.connectAttr(
            "%s.outputR" % ik_stretch_distance_clamp, "%s.firstTerm" % ik_soft_condition
        )
        cmds.connectAttr(
            "%s.output1D" % ik_soft_sub1, "%s.secondTerm" % ik_soft_condition
        )
        cmds.connectAttr(
            "%s.output1D" % ik_soft_sub3, "%s.colorIfTrueR" % ik_soft_condition
        )
        cmds.connectAttr(
            "%s.outputR" % ik_stretch_distance_clamp,
            "%s.colorIfFalseR" % ik_soft_condition,
        )
        cmds.connectAttr(
            "%s.outputR" % ik_stretch_distance_clamp, "%s.input1X" % ik_soft_div2
        )
        cmds.connectAttr(
            "%s.outColorR" % ik_soft_condition, "%s.input2X" % ik_soft_div2
        )
        cmds.connectAttr(
            "%s.outputX" % extra_scale_mult_sc, "%s.input1X" % ik_soft_stretch_amount
        )
        cmds.connectAttr(
            "%s.outputY" % extra_scale_mult_sc, "%s.input1Y" % ik_soft_stretch_amount
        )
        cmds.connectAttr(
            "%s.outputX" % ik_soft_div2, "%s.input2X" % ik_soft_stretch_amount
        )
        cmds.connectAttr(
            "%s.outputX" % ik_soft_div2, "%s.input2Y" % ik_soft_stretch_amount
        )
        cmds.connectAttr(
            "%s.outputX" % ik_soft_stretch_amount, "%s.color2R" % squashiness_sc
        )
        cmds.connectAttr(
            "%s.outputY" % ik_soft_stretch_amount, "%s.color2G" % squashiness_sc
        )
        cmds.connectAttr(
            "%s.rotate" % self.cont_IK_foot.name, "%s.rotate" % self.ik_rp_end_j
        )
        # Stretch Attributes Controller connections
        cmds.connectAttr(
            "%s.sUpLeg" % self.cont_IK_foot.name, "%s.input2X" % extra_scale_mult_sc
        )
        cmds.connectAttr(
            "%s.sLowLeg" % self.cont_IK_foot.name, "%s.input2Y" % extra_scale_mult_sc
        )
        cmds.connectAttr(
            "%s.squash" % self.cont_IK_foot.name, "%s.blender" % squashiness_sc
        )
        cmds.connectAttr(
            "%s.output1D" % stretch_offset, "%s.maxR" % ik_stretch_distance_clamp
        )
        cmds.connectAttr(
            "%s.stretch" % self.cont_IK_foot.name,
            "%s.inputR" % ik_stretch_stretchiness_clamp,
        )
        cmds.connectAttr(
            "%s.stretchLimit" % self.cont_IK_foot.name, "%s.input1D[2]" % stretch_offset
        )

        #
        # Bind Foot Attributes to the controller
        # create multiply nodes for alignment fix
        mult_al_fix_b_lean = cmds.createNode(
            "multDoubleLinear",
            name=naming.parse([self.module_name, "multAlFix", "bLean"], suffix="mult"),
        )
        mult_al_fix_b_roll = cmds.createNode(
            "multDoubleLinear",
            name=naming.parse([self.module_name, "multAlFix", "bRoll"], suffix="mult"),
        )
        mult_al_fix_b_spin = cmds.createNode(
            "multDoubleLinear",
            name=naming.parse([self.module_name, "multAlFix", "bSpin"], suffix="mult"),
        )
        mult_al_fix_h_roll = cmds.createNode(
            "multDoubleLinear",
            name=naming.parse([self.module_name, "multAlFix", "hRoll"], suffix="mult"),
        )
        mult_al_fix_h_spin = cmds.createNode(
            "multDoubleLinear",
            name=naming.parse([self.module_name, "multAlFix", "hSpin"], suffix="mult"),
        )
        mult_al_fix_t_roll = cmds.createNode(
            "multDoubleLinear",
            name=naming.parse([self.module_name, "multAlFix", "tRoll"], suffix="mult"),
        )
        mult_al_fix_t_spin = cmds.createNode(
            "multDoubleLinear",
            name=naming.parse([self.module_name, "multAlFix", "tSpin"], suffix="mult"),
        )
        mult_al_fix_t_wiggle = cmds.createNode(
            "multDoubleLinear",
            name=naming.parse(
                [self.module_name, "multAlFix", "tWiggle"], suffix="mult"
            ),
        )

        cmds.setAttr("%s.input2" % mult_al_fix_b_lean, self.sideMult)
        cmds.setAttr("%s.input2" % mult_al_fix_b_roll, self.sideMult)
        cmds.setAttr("%s.input2" % mult_al_fix_b_spin, self.sideMult)
        # heel roll is an exception. It should be same for each side
        cmds.setAttr("%s.input2" % mult_al_fix_h_roll, 1)
        cmds.setAttr("%s.input2" % mult_al_fix_h_spin, self.sideMult)
        # toe roll is an exception too.
        cmds.setAttr("%s.input2" % mult_al_fix_t_roll, 1)
        cmds.setAttr("%s.input2" % mult_al_fix_t_spin, self.sideMult)
        cmds.setAttr("%s.input2" % mult_al_fix_t_wiggle, self.sideMult)

        cmds.connectAttr(
            "%s.bLean" % self.cont_IK_foot.name, "%s.input1" % mult_al_fix_b_lean
        )
        cmds.connectAttr(
            "%s.bRoll" % self.cont_IK_foot.name, "%s.input1" % mult_al_fix_b_roll
        )
        cmds.connectAttr(
            "%s.bSpin" % self.cont_IK_foot.name, "%s.input1" % mult_al_fix_b_spin
        )
        cmds.connectAttr(
            "%s.hRoll" % self.cont_IK_foot.name, "%s.input1" % mult_al_fix_h_roll
        )
        cmds.connectAttr(
            "%s.hSpin" % self.cont_IK_foot.name, "%s.input1" % mult_al_fix_h_spin
        )
        cmds.connectAttr(
            "%s.tRoll" % self.cont_IK_foot.name, "%s.input1" % mult_al_fix_t_roll
        )
        cmds.connectAttr(
            "%s.tSpin" % self.cont_IK_foot.name, "%s.input1" % mult_al_fix_t_spin
        )
        cmds.connectAttr(
            "%s.tWiggle" % self.cont_IK_foot.name, "%s.input1" % mult_al_fix_t_wiggle
        )

        cmds.connectAttr("%s.output" % mult_al_fix_b_lean, "%s.rotateZ" % pv_ball_lean)
        cmds.connectAttr("%s.output" % mult_al_fix_b_roll, "%s.rotateY" % pv_ball_roll)
        cmds.connectAttr("%s.output" % mult_al_fix_b_spin, "%s.rotateZ" % pv_ball_spin)
        cmds.connectAttr("%s.output" % mult_al_fix_h_roll, "%s.rotateX" % pv_heel)
        cmds.connectAttr("%s.output" % mult_al_fix_h_spin, "%s.rotateY" % pv_heel)
        cmds.connectAttr("%s.output" % mult_al_fix_t_roll, "%s.rotateX" % pv_toe)
        cmds.connectAttr("%s.output" % mult_al_fix_t_spin, "%s.rotateY" % pv_toe)
        cmds.connectAttr("%s.output" % mult_al_fix_t_wiggle, "%s.rotateY" % pv_ball)

        pv_bank_in_ore = functions.create_offset_group(pv_bank_in, "ORE")

        cmds.setDrivenKeyframe(
            "%s.rotateX" % pv_bank_out,
            currentDriver="%s.bank" % self.cont_IK_foot.name,
            driverValue=0,
            value=0,
            inTangentType="linear",
            outTangentType="linear",
        )
        cmds.setDrivenKeyframe(
            "%s.rotateX" % pv_bank_out,
            currentDriver="%s.bank" % self.cont_IK_foot.name,
            driverValue=90,
            value=90 * self.sideMult,
            inTangentType="linear",
            outTangentType="linear",
        )

        cmds.setDrivenKeyframe(
            "%s.rotateX" % pv_bank_in,
            currentDriver="%s.bank" % self.cont_IK_foot.name,
            driverValue=0,
            value=0,
            inTangentType="linear",
            outTangentType="linear",
        )
        cmds.setDrivenKeyframe(
            "%s.rotateX" % pv_bank_in,
            currentDriver="%s.bank" % self.cont_IK_foot.name,
            driverValue=-90,
            value=90 * (-1 * self.sideMult),
            inTangentType="linear",
            outTangentType="linear",
        )

        self.ik_parent_grp = cmds.group(
            name=naming.parse([self.module_name, "IK", "parent"], suffix="grp"),
            empty=True,
        )
        functions.align_to_alter(self.ik_parent_grp, self.cont_IK_foot.name, 2)
        cmds.parent(pv_bank_in_ore, self.ik_parent_grp)
        cmds.parent(self.ik_foot_j, self.ik_parent_grp)
        cmds.parentConstraint(self.ik_sc_end_j, self.ik_foot_j)

        cmds.parentConstraint(
            self.cont_IK_foot.name, self.ik_parent_grp, maintainOffset=False
        )

        # parenting should be after the constraint

        blend_ore_ik_root = cmds.createNode(
            "blendColors",
            name=naming.parse([self.module_name, "IK", "ore", "up"], suffix="blend"),
        )

        cmds.connectAttr(
            "%s.rotate" % self.ik_sc_root_j, "%s.color2" % blend_ore_ik_root
        )
        cmds.connectAttr(
            "%s.rotate" % self.ik_rp_root_j, "%s.color1" % blend_ore_ik_root
        )
        cmds.connectAttr(
            "%s.output" % blend_ore_ik_root, "%s.rotate" % self.ik_orig_root_j
        )
        cmds.connectAttr(
            "%s.polevector" % self.cont_IK_foot.name, "%s.blender" % blend_ore_ik_root
        )

        blend_pos_ik_root = cmds.createNode(
            "blendColors",
            name=naming.parse([self.module_name, "IK", "pos", "up"], suffix="blend"),
        )
        cmds.connectAttr(
            "%s.translate" % self.ik_sc_root_j, "%s.color2" % blend_pos_ik_root
        )
        cmds.connectAttr(
            "%s.translate" % self.ik_rp_root_j, "%s.color1" % blend_pos_ik_root
        )
        cmds.connectAttr(
            "%s.output" % blend_pos_ik_root, "%s.translate" % self.ik_orig_root_j
        )
        cmds.connectAttr(
            "%s.polevector" % self.cont_IK_foot.name, "%s.blender" % blend_pos_ik_root
        )

        blend_ore_ik_knee = cmds.createNode(
            "blendColors",
            name=naming.parse([self.module_name, "IK", "ore", "low"], suffix="blend"),
        )
        cmds.connectAttr(
            "%s.rotate" % self.ik_sc_knee_j, "%s.color2" % blend_ore_ik_knee
        )
        cmds.connectAttr(
            "%s.rotate" % self.ik_rp_knee_j, "%s.color1" % blend_ore_ik_knee
        )
        # Weird bug with skinned character / use seperate connections
        # if there is no skincluster, it works ok, but adding a skin cluster misses 2 out of 3 rotation axis
        # Therefore make SEPERATE CONNECTIONS
        cmds.connectAttr(
            "%s.outputR" % blend_ore_ik_knee, "%s.rotateX" % self.ik_orig_knee_j
        )
        cmds.connectAttr(
            "%s.outputG" % blend_ore_ik_knee, "%s.rotateY" % self.ik_orig_knee_j
        )
        cmds.connectAttr(
            "%s.outputB" % blend_ore_ik_knee, "%s.rotateZ" % self.ik_orig_knee_j
        )
        cmds.connectAttr(
            "%s.polevector" % self.cont_IK_foot.name, "%s.blender" % blend_ore_ik_knee
        )

        blend_pos_ik_knee = cmds.createNode(
            "blendColors",
            name=naming.parse([self.module_name, "IK", "pos", "low"], suffix="blend"),
        )
        cmds.connectAttr(
            "%s.translate" % self.ik_sc_knee_j, "%s.color2" % blend_pos_ik_knee
        )
        cmds.connectAttr(
            "%s.translate" % self.ik_rp_knee_j, "%s.color1" % blend_pos_ik_knee
        )
        cmds.connectAttr(
            "%s.output" % blend_pos_ik_knee, "%s.translate" % self.ik_orig_knee_j
        )
        cmds.connectAttr(
            "%s.polevector" % self.cont_IK_foot.name, "%s.blender" % blend_pos_ik_knee
        )

        blend_ore_ik_end = cmds.createNode(
            "blendColors",
            name=naming.parse(
                [self.module_name, "IK", "ore", "lowEnd"], suffix="blend"
            ),
        )
        cmds.connectAttr("%s.rotate" % self.ik_sc_end_j, "%s.color2" % blend_ore_ik_end)
        cmds.connectAttr("%s.rotate" % self.ik_rp_end_j, "%s.color1" % blend_ore_ik_end)
        # Weird bug with skinned character / use seperate connections
        # if there is no skincluster, it works ok, but adding a skin cluster misses 2 out of 3 rotation axis
        # Therefore make SEPERATE CONNECTIONS
        cmds.connectAttr(
            "%s.outputR" % blend_ore_ik_end, "%s.rotateX" % self.ik_orig_end_j
        )
        cmds.connectAttr(
            "%s.outputG" % blend_ore_ik_end, "%s.rotateY" % self.ik_orig_end_j
        )
        cmds.connectAttr(
            "%s.outputB" % blend_ore_ik_end, "%s.rotateZ" % self.ik_orig_end_j
        )
        cmds.connectAttr(
            "%s.polevector" % self.cont_IK_foot.name, "%s.blender" % blend_ore_ik_end
        )

        blend_pos_ik_end = cmds.createNode(
            "blendColors",
            name=naming.parse(
                [self.module_name, "IK", "pos", "lowEnd"], suffix="blend"
            ),
        )
        cmds.connectAttr(
            "%s.translate" % self.ik_sc_end_j, "%s.color2" % blend_pos_ik_end
        )
        cmds.connectAttr(
            "%s.translate" % self.ik_rp_end_j, "%s.color1" % blend_pos_ik_end
        )
        cmds.connectAttr(
            "%s.output" % blend_pos_ik_end, "%s.translate" % self.ik_orig_end_j
        )
        cmds.connectAttr(
            "%s.polevector" % self.cont_IK_foot.name, "%s.blender" % blend_pos_ik_end
        )

        pole_vector_rvs = cmds.createNode(
            "reverse",
            name=naming.parse([self.module_name, "poleVector", "rvs"], suffix="rvs"),
        )
        cmds.connectAttr(
            "%s.polevector" % self.cont_IK_foot.name, "%s.inputX" % pole_vector_rvs
        )
        cmds.connectAttr(
            "%s.polevector" % self.cont_IK_foot.name, "%s.v" % self.cont_pole.name
        )

        cmds.parent(self.ik_orig_root_j, self.master_root)
        cmds.parent(self.ik_sc_root_j, self.master_root)
        cmds.parent(self.ik_rp_root_j, self.master_root)

        pacon_locator_hip = cmds.spaceLocator(
            name=naming.parse([self.module_name, "pacon"], suffix="loc")
        )[0]
        functions.align_to(
            pacon_locator_hip, self.leg_root_j_def, position=True, rotation=True
        )
        #
        _pa_con_j_def = cmds.parentConstraint(
            self.cont_thigh.name, pacon_locator_hip, maintainOffset=False
        )
        #
        cmds.parent(leg_start, self.scaleGrp)
        cmds.parent(leg_end, self.scaleGrp)
        cmds.parent(self.ik_parent_grp, self.scaleGrp)
        cmds.parent(self.start_lock_ore, self.scaleGrp)
        cmds.parent(self.end_lock_ore, self.scaleGrp)

        cmds.parent(pacon_locator_hip, self.scaleGrp)
        cmds.parent(self.leg_root_j_def, pacon_locator_hip)
        #
        cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % leg_start)
        cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % leg_end)
        cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % self.ik_parent_grp)
        cmds.connectAttr(
            "%s.rigVis" % self.scaleGrp,
            "%s.v" % functions.get_shapes(pacon_locator_hip)[0],
        )

        cmds.delete(foot_plane)

    def create_fk_setup(self):
        cmds.connectAttr(
            "%s.scaleX" % self.cont_fk_up_leg.name, "%s.scaleX" % self.fk_root_j
        )
        cmds.connectAttr(
            "%s.scaleX" % self.cont_fk_low_leg.name, "%s.scaleX" % self.fk_knee_j
        )
        cmds.connectAttr(
            "%s.scaleX" % self.cont_fk_foot.name, "%s.scaleX" % self.fk_foot_j
        )
        cmds.connectAttr(
            "%s.scaleX" % self.cont_fk_ball.name, "%s.scaleX" % self.fk_ball_j
        )

        cmds.orientConstraint(
            self.cont_fk_up_leg.name, self.fk_root_j, maintainOffset=False
        )
        cmds.pointConstraint(self.start_lock, self.fk_root_j, maintainOffset=False)

        cmds.orientConstraint(
            self.cont_fk_low_leg.name, self.fk_knee_j, maintainOffset=False
        )
        cmds.orientConstraint(
            self.cont_fk_foot.name, self.fk_foot_j, maintainOffset=False
        )

        cmds.parentConstraint(
            self.cont_fk_ball.name, self.fk_ball_j, maintainOffset=False
        )

        # TODO : TAKE A LOOK TO THE OFFSET SOLUTION
        cmds.parentConstraint(
            self.cont_thigh.name,
            self.cont_fk_up_leg_off,
            skipRotate=["x", "y", "z"],
            maintainOffset=True,
        )
        cmds.parentConstraint(
            self.cont_fk_up_leg.name, self.cont_fk_low_leg_off, maintainOffset=True
        )
        cmds.parentConstraint(
            self.cont_fk_low_leg.name, self.cont_fk_foot_off, maintainOffset=True
        )
        cmds.parentConstraint(
            self.cont_fk_foot.name, self.cont_fk_ball_off, maintainOffset=True
        )

    def ik_fk_switching(self):
        cmds.connectAttr(
            "%s.FK_IK_Reverse" % self.cont_fk_ik.name,
            "%s.visibility" % self.cont_fk_up_leg_ore,
        )
        cmds.connectAttr(
            "%s.FK_IK_Reverse" % self.cont_fk_ik.name,
            "%s.visibility" % self.cont_fk_low_leg_ore,
        )
        cmds.connectAttr(
            "%s.FK_IK_Reverse" % self.cont_fk_ik.name,
            "%s.visibility" % self.cont_fk_foot_ore,
        )
        cmds.connectAttr(
            "%s.FK_IK_Reverse" % self.cont_fk_ik.name,
            "%s.visibility" % self.cont_fk_ball_ore,
        )
        cmds.connectAttr(
            "%s.fk_ik" % self.cont_fk_ik.name, "%s.visibility" % self.cont_IK_foot.name
        )
        cmds.connectAttr(
            "%s.fk_ik" % self.cont_fk_ik.name, "%s.visibility" % self.cont_pole_vis
        )

        mid_lock_pa_con_weight = cmds.parentConstraint(
            self.ik_orig_root_j,
            self.fk_root_j,
            self.cont_mid_lock_pos,
            maintainOffset=False,
        )[0]
        cmds.connectAttr(
            "%s.fk_ik" % self.cont_fk_ik.name,
            "%s.%sW0" % (mid_lock_pa_con_weight, self.ik_orig_root_j),
        )
        cmds.connectAttr(
            "%s.FK_IK_Reverse" % self.cont_fk_ik.name,
            "%s.%sW1" % (mid_lock_pa_con_weight, self.fk_root_j),
        )

        cmds.connectAttr(
            "%s.interpType" % self.cont_fk_ik.name,
            "%s.interpType" % mid_lock_pa_con_weight,
        )

        mid_lock_po_con_weight = cmds.pointConstraint(
            self.ik_orig_knee_j,
            self.fk_knee_j,
            self.cont_mid_lock_ave,
            maintainOffset=False,
        )[0]
        cmds.connectAttr(
            "%s.fk_ik" % self.cont_fk_ik.name,
            "%s.%sW0" % (mid_lock_po_con_weight, self.ik_orig_knee_j),
        )
        cmds.connectAttr(
            "%s.FK_IK_Reverse" % self.cont_fk_ik.name,
            "%s.%sW1" % (mid_lock_po_con_weight, self.fk_knee_j),
        )

        mid_lock_x_bln = cmds.createNode(
            "multiplyDivide",
            name=naming.parse([self.module_name, "midLock", "xBln"], suffix="loc"),
        )

        mid_lock_rot_xsw = cmds.createNode(
            "blendTwoAttr",
            name=naming.parse([self.module_name, "midLock", "rotXsw"], suffix="blend"),
        )
        cmds.connectAttr(
            "%s.rotateZ" % self.ik_orig_knee_j, "%s.input[0]" % mid_lock_rot_xsw
        )
        cmds.connectAttr(
            "%s.rotateZ" % self.fk_knee_j, "%s.input[1]" % mid_lock_rot_xsw
        )
        cmds.connectAttr(
            "%s.FK_IK_Reverse" % self.cont_fk_ik.name,
            "%s.attributesBlender" % mid_lock_rot_xsw,
        )
        cmds.connectAttr("%s.output" % mid_lock_rot_xsw, "%s.input1Z" % mid_lock_x_bln)

        cmds.setAttr("%s.input2Z" % mid_lock_x_bln, 0.5)

        cmds.connectAttr(
            "%s.outputZ" % mid_lock_x_bln, "%s.rotateZ" % self.cont_mid_lock_ave
        )

        end_lock_weight = cmds.pointConstraint(
            self.ik_orig_end_j, self.fk_foot_j, self.end_lock_pos, maintainOffset=False
        )[0]
        cmds.connectAttr(
            "%s.fk_ik" % self.cont_fk_ik.name,
            "%s.%sW0" % (end_lock_weight, self.ik_orig_end_j),
        )
        cmds.connectAttr(
            "%s.FK_IK_Reverse" % self.cont_fk_ik.name,
            "%s.%sW1" % (end_lock_weight, self.fk_foot_j),
        )

        # the following offset parent constraint is not important and won't cause any trouble since
        # it only affects the FK/IK icon
        cmds.parentConstraint(self.end_lock, self.cont_fk_ik_pos, maintainOffset=True)

        # ######
        end_lock_rot = cmds.parentConstraint(
            self.ik_parent_grp,
            self.fk_foot_j,
            self.end_lock,
            skipTranslate=["x", "y", "z"],
            maintainOffset=True,
        )[0]

        cmds.connectAttr(
            "%s.fk_ik" % self.cont_fk_ik.name,
            "%s.%sW0" % (end_lock_rot, self.ik_parent_grp),
        )
        cmds.connectAttr(
            "%s.FK_IK_Reverse" % self.cont_fk_ik.name,
            "%s.%sW1" % (end_lock_rot, self.fk_foot_j),
        )
        cmds.connectAttr(
            "%s.interpType" % self.cont_fk_ik.name, "%s.interpType" % end_lock_rot
        )

        foot_pa_con = cmds.parentConstraint(
            self.ik_foot_j, self.fk_foot_j, self.foot_j_def, maintainOffset=False
        )[0]
        ball_pa_con = cmds.parentConstraint(
            self.ik_ball_j, self.fk_ball_j, self.ball_j_def, maintainOffset=False
        )[0]
        toe_pa_con = cmds.parentConstraint(
            self.ik_toe_j, self.fk_toe_j, self.toe_j_def, maintainOffset=False
        )[0]

        cmds.connectAttr(
            "%s.fk_ik" % self.cont_fk_ik.name, "%s.%sW0" % (foot_pa_con, self.ik_foot_j)
        )
        cmds.connectAttr(
            "%s.FK_IK_Reverse" % self.cont_fk_ik.name,
            "%s.%sW1" % (foot_pa_con, self.fk_foot_j),
        )
        cmds.connectAttr(
            "%s.fk_ik" % self.cont_fk_ik.name,
            "%s." % "%s.%sW0" % (ball_pa_con, self.ik_ball_j),
        )
        cmds.connectAttr(
            "%s.FK_IK_Reverse" % self.cont_fk_ik.name,
            "%s." % "%s.%sW1" % (ball_pa_con, self.fk_ball_j),
        )
        cmds.connectAttr(
            "%s.fk_ik" % self.cont_fk_ik.name,
            "%s." % "%s.%sW0" % (toe_pa_con, self.ik_toe_j),
        )
        cmds.connectAttr(
            "%s.FK_IK_Reverse" % self.cont_fk_ik.name,
            "%s." % "%s.%sW1" % (toe_pa_con, self.fk_toe_j),
        )
        cmds.connectAttr(
            "%s.interpType" % self.cont_fk_ik.name, "%s.interpType" % foot_pa_con
        )
        cmds.connectAttr(
            "%s.interpType" % self.cont_fk_ik.name, "%s.interpType" % ball_pa_con
        )
        cmds.connectAttr(
            "%s.interpType" % self.cont_fk_ik.name, "%s.interpType" % toe_pa_con
        )

    def create_def_joints(self):
        # UPPERLEG RIBBON

        ribbon_upper_leg = Ribbon(
            self.hip_j_def,
            self.mid_leg_j_def,
            name=naming.parse([self.module_name, "up"]),
            connect_start_aim=False,
            up_vector=self.mirror_axis,
        )
        ribbon_upper_leg.create()

        ribbon_start_pa_con_upper_leg_start = ribbon_upper_leg.pin_start(
            self.start_lock
        )[0]
        ribbon_upper_leg.pin_end(self.mid_lock)

        # connect the knee scaling
        cmds.connectAttr(
            "%s.scale" % self.cont_mid_lock.name, "%s.scale" % ribbon_upper_leg.end_plug
        )
        cmds.connectAttr(
            "%s.scale" % self.cont_mid_lock.name, "%s.scale" % self.mid_leg_j_def
        )

        cmds.scaleConstraint(self.scaleGrp, ribbon_upper_leg.scale_grp)

        ribbon_start_ori_con = cmds.parentConstraint(
            self.ik_orig_root_j,
            self.fk_root_j,
            ribbon_upper_leg.start_aim,
            maintainOffset=False,
            skipTranslate=["x", "y", "z"],
        )[0]
        _ribbon_start_ori_con_ext = cmds.parentConstraint(
            self.hip_j_def,
            ribbon_upper_leg.start_aim,
            maintainOffset=False,
            skipTranslate=["x", "y", "z"],
        )[0]

        cmds.connectAttr(
            "%s.fk_ik" % self.cont_fk_ik.name,
            "%s.%sW0" % (ribbon_start_ori_con, self.ik_orig_root_j),
        )
        cmds.connectAttr(
            "%s.FK_IK_Reverse" % self.cont_fk_ik.name,
            "%s.%sW1" % (ribbon_start_ori_con, self.fk_root_j),
        )

        pair_blend_node = cmds.listConnections(
            ribbon_start_ori_con, destination=True, type="pairBlend"
        )[0]
        # disconnect the existing weight connection
        # re-connect to the custom attribute
        cmds.connectAttr(
            "%s.alignHip" % self.cont_fk_ik.name, "%s.w" % pair_blend_node, force=True
        )

        # Rotate the shoulder connection bone 180 degrees for Right Alignment
        if self.side == "R":
            right_rbn_startup_ore = cmds.listRelatives(
                ribbon_upper_leg.start_aim, children=True, type="transform"
            )[0]
            cmds.setAttr("%s.ry" % right_rbn_startup_ore, 180)

        # AUTO AND MANUAL TWIST

        # auto
        auto_twist_thigh = cmds.createNode(
            "multiplyDivide",
            name=naming.parse([self.module_name, "thigh", "autoTwist"], suffix="mult"),
        )
        cmds.connectAttr(
            "%s.upLegAutoTwist" % self.cont_fk_ik.name, "%s.input2X" % auto_twist_thigh
        )
        cmds.connectAttr(
            "%s.constraintRotate" % ribbon_start_pa_con_upper_leg_start,
            "%s.input1" % auto_twist_thigh,
        )

        # !!! The parent constrain override should be disconnected like this
        cmds.disconnectAttr(
            "%s.constraintRotateX" % ribbon_start_pa_con_upper_leg_start,
            "%s.rotateX" % ribbon_upper_leg.start_plug,
        )

        # manual
        add_manual_twist_thigh = cmds.createNode(
            "plusMinusAverage",
            name=naming.parse(
                [self.module_name, "upperLeg", "manualTwist"], suffix="pma"
            ),
        )
        cmds.connectAttr(
            "%s.output" % auto_twist_thigh, "%s.input3D[0]" % add_manual_twist_thigh
        )
        cmds.connectAttr(
            "%s.upLegManualTwist" % self.cont_fk_ik.name,
            "%s.input3D[1].input3Dx" % add_manual_twist_thigh,
        )

        # connect to the joint
        cmds.connectAttr(
            "%s.output3D" % add_manual_twist_thigh,
            "%s.rotate" % ribbon_upper_leg.start_plug,
        )

        # connect allowScaling
        cmds.connectAttr(
            "%s.allowScaling" % self.cont_fk_ik.name,
            "%s.scaleSwitch" % ribbon_upper_leg.start_plug,
        )

        # LOWERLEG RIBBON

        ribbon_lower_leg = Ribbon(
            self.mid_leg_j_def,
            self.foot_j_def,
            name=naming.parse([self.module_name, "low"]),
            connect_start_aim=True,
            up_vector=self.mirror_axis,
        )
        ribbon_lower_leg.create()
        ribbon_lower_leg.pin_start(self.mid_lock)
        ribbon_start_pa_con_lower_leg_end = ribbon_lower_leg.pin_end(self.end_lock)[0]

        # connect the midLeg scaling
        cmds.connectAttr(
            "%s.scale" % self.cont_mid_lock.name,
            "%s.scale" % ribbon_lower_leg.start_plug,
        )

        cmds.scaleConstraint(self.scaleGrp, ribbon_lower_leg.scale_grp)

        # AUTO AND MANUAL TWIST

        # auto
        auto_twist_ankle = cmds.createNode(
            "multiplyDivide",
            name=naming.parse([self.module_name, "ankle", "autoTwist"], suffix="mult"),
        )
        cmds.connectAttr(
            "%s.footAutoTwist" % self.cont_fk_ik.name, "%s.input2X" % auto_twist_ankle
        )
        cmds.connectAttr(
            "%s.constraintRotate" % ribbon_start_pa_con_lower_leg_end,
            "%s.input1" % auto_twist_ankle,
        )

        # !!! The parent constrain override should be disconnected like this
        cmds.disconnectAttr(
            "%s.constraintRotateX" % ribbon_start_pa_con_lower_leg_end,
            "%s.rotateX" % ribbon_lower_leg.end_plug,
        )

        # manual
        add_manual_twist_ankle = cmds.createNode(
            "plusMinusAverage",
            name=naming.parse(
                [self.module_name, "lowerLeg", "manualTwist"], suffix="pma"
            ),
        )
        cmds.connectAttr(
            "%s.output" % auto_twist_ankle, "%s.input3D[0]" % add_manual_twist_ankle
        )
        cmds.connectAttr(
            "%s.footManualTwist" % self.cont_fk_ik.name,
            "%s.input3D[1].input3Dx" % add_manual_twist_ankle,
        )

        # connect to the joint
        cmds.connectAttr(
            "%s.output3D" % add_manual_twist_ankle,
            "%s.rotate" % ribbon_lower_leg.end_plug,
        )

        # connect allowScaling
        cmds.connectAttr(
            "%s.allowScaling" % self.cont_fk_ik.name,
            "%s.scaleSwitch" % ribbon_lower_leg.start_plug,
        )

        # Volume Preservation Stuff
        vp_extra_input = cmds.createNode(
            "multiplyDivide",
            name=naming.parse([self.module_name, "vpExtraInput"], suffix="mult"),
        )
        cmds.setAttr("%s.operation" % vp_extra_input, 1)

        vp_mid_average = cmds.createNode(
            "plusMinusAverage",
            name=naming.parse([self.module_name, "vpMidAverage"], suffix="pma"),
        )
        cmds.setAttr("%s.operation" % vp_mid_average, 3)

        vp_power_mid = cmds.createNode(
            "multiplyDivide",
            name=naming.parse([self.module_name, "vpPowerMid"], suffix="mult"),
        )
        cmds.setAttr("%s.operation" % vp_power_mid, 3)
        vp_init_length = cmds.createNode(
            "multiplyDivide",
            name=naming.parse([self.module_name, "vpInitLength"], suffix="mult"),
        )
        cmds.setAttr("%s.operation" % vp_init_length, 2)

        vp_power_upper_leg = cmds.createNode(
            "multiplyDivide",
            name=naming.parse([self.module_name, "vpPowerUpperLeg"], suffix="mult"),
        )
        cmds.setAttr("%s.operation" % vp_power_upper_leg, 3)

        vp_power_lower_leg = cmds.createNode(
            "multiplyDivide",
            name=naming.parse([self.module_name, "vpPowerLowerLeg"], suffix="mult"),
        )
        cmds.setAttr("%s.operation" % vp_power_lower_leg, 3)

        vp_upper_lower_reduce = cmds.createNode(
            "multDoubleLinear",
            name=naming.parse([self.module_name, "vpUpperLowerReduce"], suffix="mult"),
        )
        cmds.setAttr("%s.input2" % vp_upper_lower_reduce, 0.5)

        # vp knee branch
        cmds.connectAttr(
            "%s.output" % vp_extra_input,
            "%s.scale" % ribbon_lower_leg.start_plug,
            force=True,
        )
        cmds.connectAttr(
            "%s.output" % vp_extra_input,
            "%s.scale" % ribbon_upper_leg.end_plug,
            force=True,
        )
        cmds.connectAttr(
            "%s.output" % vp_extra_input, "%s.scale" % self.mid_leg_j_def, force=True
        )
        cmds.connectAttr(
            "%s.scale" % self.cont_mid_lock.name,
            "%s.input1" % vp_extra_input,
            force=True,
        )
        cmds.connectAttr(
            "%s.output1D" % vp_mid_average, "%s.input2X" % vp_extra_input, force=True
        )
        cmds.connectAttr(
            "%s.output1D" % vp_mid_average, "%s.input2Y" % vp_extra_input, force=True
        )
        cmds.connectAttr(
            "%s.output1D" % vp_mid_average, "%s.input2Z" % vp_extra_input, force=True
        )
        cmds.connectAttr(
            "%s.outputX" % vp_power_mid, "%s.input1D[0]" % vp_mid_average, force=True
        )
        cmds.connectAttr(
            "%s.outputY" % vp_power_mid, "%s.input1D[1]" % vp_mid_average, force=True
        )
        cmds.connectAttr(
            "%s.outputX" % vp_init_length, "%s.input1X" % vp_power_mid, force=True
        )
        cmds.connectAttr(
            "%s.outputY" % vp_init_length, "%s.input1Y" % vp_power_mid, force=True
        )
        cmds.connectAttr(
            "%s.volume" % self.cont_IK_foot.name,
            "%s.input2X" % vp_power_mid,
            force=True,
        )
        cmds.connectAttr(
            "%s.volume" % self.cont_IK_foot.name,
            "%s.input2Y" % vp_power_mid,
            force=True,
        )
        cmds.connectAttr(
            "%s.outputX" % self.initial_length_multip_sc,
            "%s.input1X" % vp_init_length,
            force=True,
        )
        cmds.connectAttr(
            "%s.outputY" % self.initial_length_multip_sc,
            "%s.input1Y" % vp_init_length,
            force=True,
        )
        cmds.connectAttr(
            "%s.color1R" % self.stretchiness_sc,
            "%s.input2X" % vp_init_length,
            force=True,
        )
        cmds.connectAttr(
            "%s.color1G" % self.stretchiness_sc,
            "%s.input2Y" % vp_init_length,
            force=True,
        )

        # vp upper branch
        # mid_off_up = functions.get_parent(ribbon_upper_leg.controllers[0])
        mid_off_up = ribbon_upper_leg.controllers[0].parent
        cmds.connectAttr("%s.outputX" % vp_power_upper_leg, "%s.scaleX" % mid_off_up)
        cmds.connectAttr("%s.outputX" % vp_power_upper_leg, "%s.scaleY" % mid_off_up)
        cmds.connectAttr("%s.outputX" % vp_power_upper_leg, "%s.scaleZ" % mid_off_up)
        cmds.connectAttr(
            "%s.outputX" % vp_init_length, "%s.input1X" % vp_power_upper_leg
        )
        cmds.connectAttr(
            "%s.output" % vp_upper_lower_reduce, "%s.input2X" % vp_power_upper_leg
        )

        # vp lower branch
        # mid_off_low = functions.get_parent(ribbon_lower_leg.controllers[0])
        mid_off_low = ribbon_lower_leg.controllers[0].parent
        cmds.connectAttr("%s.outputX" % vp_power_lower_leg, "%s.scaleX" % mid_off_low)
        cmds.connectAttr("%s.outputX" % vp_power_lower_leg, "%s.scaleY" % mid_off_low)
        cmds.connectAttr("%s.outputX" % vp_power_lower_leg, "%s.scaleZ" % mid_off_low)
        cmds.connectAttr(
            "%s.outputX" % vp_init_length, "%s.input1X" % vp_power_lower_leg
        )
        cmds.connectAttr(
            "%s.output" % vp_upper_lower_reduce, "%s.input2X" % vp_power_lower_leg
        )
        cmds.connectAttr(
            "%s.volume" % self.cont_IK_foot.name, "%s.input1" % vp_upper_lower_reduce
        )

        cmds.parent(ribbon_upper_leg.ribbon_grp, self.nonScaleGrp)
        cmds.parent(ribbon_lower_leg.ribbon_grp, self.nonScaleGrp)

        cmds.connectAttr(
            "%s.tweakControls" % self.cont_fk_ik.name, "%s.v" % self.cont_mid_lock.name
        )
        tweak_conts = ribbon_upper_leg.controllers + ribbon_lower_leg.controllers
        attribute.drive_attrs(
            "%s.tweakControls" % self.cont_fk_ik.name,
            ["%s.v" % x.name for x in tweak_conts],
        )

        cmds.connectAttr(
            "%s.contVis" % self.scaleGrp, "%s.v" % ribbon_upper_leg.scale_grp
        )
        cmds.connectAttr(
            "%s.contVis" % self.scaleGrp, "%s.v" % ribbon_lower_leg.scale_grp
        )

        self.deformerJoints += (
            ribbon_lower_leg.deformer_joints + ribbon_upper_leg.deformer_joints
        )
        attribute.drive_attrs(
            "%s.jointVis" % self.scaleGrp, ["%s.v" % x for x in self.deformerJoints]
        )
        attribute.drive_attrs(
            "%s.rigVis" % self.scaleGrp, ["%s.v" % x for x in ribbon_lower_leg.to_hide]
        )
        attribute.drive_attrs(
            "%s.rigVis" % self.scaleGrp, ["%s.v" % x for x in ribbon_upper_leg.to_hide]
        )
        for cont in ribbon_upper_leg.controllers + ribbon_lower_leg.controllers:
            cont.set_side(self.side, tier="tertiary")

    def create_angle_extractors(self):
        # IK Angle Extractor
        angle_ext_root_ik = cmds.spaceLocator(
            name=naming.parse(
                [self.module_name, "IK", "angleExt", "root"], suffix="loc"
            )
        )[0]
        angle_ext_fixed_ik = cmds.spaceLocator(
            name=naming.parse(
                [self.module_name, "IK", "angleExt", "fixed"], suffix="loc"
            )
        )[0]
        angle_ext_float_ik = cmds.spaceLocator(
            name=naming.parse(
                [self.module_name, "IK", "angleExt", "float"], suffix="loc"
            )
        )[0]
        cmds.parent(angle_ext_fixed_ik, angle_ext_float_ik, angle_ext_root_ik)

        cmds.parentConstraint(self.limbPlug, angle_ext_root_ik, maintainOffset=False)
        cmds.parentConstraint(
            self.cont_IK_foot.name, angle_ext_fixed_ik, maintainOffset=False
        )
        functions.align_to_alter(angle_ext_float_ik, self.leg_root_j_def, 2)
        cmds.move(0, self.sideMult * 5, 0, angle_ext_float_ik, objectSpace=True)

        angle_node_ik = cmds.createNode(
            "angleBetween", name=naming.parse([self.module_name, "IK"], suffix="angle")
        )
        angle_remap_ik = cmds.createNode(
            "remapValue",
            name=naming.parse([self.module_name, "IK", "angle"], suffix="remap"),
        )
        angle_mult_ik = cmds.createNode(
            "multDoubleLinear",
            name=naming.parse([self.module_name, "IK", "angle"], suffix="mult"),
        )

        cmds.connectAttr(
            "%s.translate" % angle_ext_fixed_ik, "%s.vector1" % angle_node_ik
        )
        cmds.connectAttr(
            "%s.translate" % angle_ext_float_ik, "%s.vector2" % angle_node_ik
        )
        cmds.connectAttr("%s.angle" % angle_node_ik, "%s.inputValue" % angle_remap_ik)

        cmds.setAttr(
            "%s.inputMin" % angle_remap_ik, cmds.getAttr("%s.angle" % angle_node_ik)
        )
        cmds.setAttr("%s.inputMax" % angle_remap_ik, 0)
        cmds.setAttr("%s.outputMin" % angle_remap_ik, 0)
        cmds.setAttr(
            "%s.outputMax" % angle_remap_ik, cmds.getAttr("%s.angle" % angle_node_ik)
        )

        cmds.connectAttr("%s.outValue" % angle_remap_ik, "%s.input1" % angle_mult_ik)

        cmds.setAttr("%s.input2" % angle_mult_ik, 0.5)

        # FK Angle Extractor
        angle_remap_fk = cmds.createNode(
            "remapValue",
            name=naming.parse([self.module_name, "FK", "angle"], suffix="remap"),
        )
        angle_mult_fk = cmds.createNode(
            "multDoubleLinear",
            name=naming.parse([self.module_name, "FK", "angle"], suffix="mult"),
        )

        cmds.connectAttr(
            "%s.rotateZ" % self.cont_fk_up_leg.name, "%s.inputValue" % angle_remap_fk
        )

        cmds.setAttr("%s.inputMin" % angle_remap_fk, 0)
        cmds.setAttr("%s.inputMax" % angle_remap_fk, 90)
        cmds.setAttr("%s.outputMin" % angle_remap_fk, 0)
        cmds.setAttr("%s.outputMax" % angle_remap_fk, 90)

        cmds.connectAttr("%s.outValue" % angle_remap_fk, "%s.input1" % angle_mult_fk)

        cmds.setAttr("%s.input2" % angle_mult_fk, 0.5)

        # create blend attribute and global Mult
        angle_ext_blend = cmds.createNode(
            "blendTwoAttr",
            name=naming.parse([self.module_name, "angleExt"], suffix="blend"),
        )
        angle_global = cmds.createNode(
            "multDoubleLinear",
            name=naming.parse([self.module_name, "angleGlobal"], suffix="mult"),
        )

        cmds.connectAttr(
            "%s.fk_ik" % self.cont_fk_ik.name, "%s.attributesBlender" % angle_ext_blend
        )
        cmds.connectAttr("%s.output" % angle_mult_fk, "%s.input[0]" % angle_ext_blend)
        cmds.connectAttr("%s.output" % angle_mult_ik, "%s.input[1]" % angle_ext_blend)
        cmds.connectAttr("%s.output" % angle_ext_blend, "%s.input1" % angle_global)
        cmds.connectAttr(
            "%s.autoHip" % self.cont_fk_ik.name, "%s.input2" % angle_global
        )
        cmds.connectAttr(
            "%s.output" % angle_global, "%s.rotateZ" % self.cont_thigh_auto
        )

        cmds.parent(angle_ext_root_ik, self.scaleGrp)
        cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % angle_ext_root_ik)

    def round_up(self):
        cmds.parentConstraint(self.limbPlug, self.scaleGrp, maintainOffset=False)
        cmds.setAttr("%s.rigVis" % self.scaleGrp, 0)

        # attribute.lock_and_hide(self.cont_IK_foot, ["v"])
        self.cont_IK_foot.lock("v")
        self.cont_pole.lock(["rx", "ry", "rz", "sx", "sy", "sz", "v"])
        self.cont_mid_lock.lock(["v"])
        self.cont_fk_ik.lock(["sx", "sy", "sz", "v"])
        self.cont_fk_foot.lock(["tx", "ty", "tz", "v"])
        self.cont_fk_low_leg.lock(["tx", "ty", "tz", "sy", "sz", "v"])
        self.cont_fk_up_leg.lock(["tx", "ty", "tz", "sy", "sz", "v"])
        self.cont_thigh.lock(["sx", "sy", "sz", "v"])

        self.scaleConstraints.append(self.cont_IK_OFF)
        self.anchors = [
            (self.cont_IK_foot.name, "parent", 1, None),
            (self.cont_pole.name, "parent", 1, None),
        ]

        for cont in self.controllers:
            cont.set_defaults()

    def execute(self):
        self.create_joints()
        self.create_controllers()
        self.create_roots()
        self.create_ik_setup()
        self.create_fk_setup()
        self.ik_fk_switching()
        self.create_def_joints()
        self.create_angle_extractors()
        self.round_up()


class Guides(_module.GuidesCore):
    limb_data = LIMB_DATA

    def draw_joints(self):
        if self.side == "C":
            # Guide joint positions for limbs with no side orientation
            root_vec = om.MVector(0, 14, 0) * self.tMatrix
            hip_vec = om.MVector(0, 10, 0) * self.tMatrix
            knee_vec = om.MVector(0, 5, 1) * self.tMatrix
            foot_vec = om.MVector(0, 1, 0) * self.tMatrix
            ball_vec = om.MVector(0, 0, 2) * self.tMatrix
            toe_vec = om.MVector(0, 0, 4) * self.tMatrix
            bankout_vec = om.MVector(-1, 0, 2) * self.tMatrix
            bankin_vec = om.MVector(1, 0, 2) * self.tMatrix
            toepv_vec = om.MVector(0, 0, 4.3) * self.tMatrix
            heelpv_vec = om.MVector(0, 0, -0.2) * self.tMatrix
        else:
            # Guide-joint positions for limbs with sides
            root_vec = om.MVector(2 * self.sideMultiplier, 14, 0) * self.tMatrix
            hip_vec = om.MVector(5 * self.sideMultiplier, 10, 0) * self.tMatrix
            knee_vec = om.MVector(5 * self.sideMultiplier, 5, 1) * self.tMatrix
            foot_vec = om.MVector(5 * self.sideMultiplier, 1, 0) * self.tMatrix
            ball_vec = om.MVector(5 * self.sideMultiplier, 0, 2) * self.tMatrix
            toe_vec = om.MVector(5 * self.sideMultiplier, 0, 4) * self.tMatrix
            bankout_vec = om.MVector(4 * self.sideMultiplier, 0, 2) * self.tMatrix
            bankin_vec = om.MVector(6 * self.sideMultiplier, 0, 2) * self.tMatrix
            toepv_vec = om.MVector(5 * self.sideMultiplier, 0, 4.3) * self.tMatrix
            heelpv_vec = om.MVector(5 * self.sideMultiplier, 0, -0.2) * self.tMatrix

        # Define the offset vector
        self.offsetVector = -((root_vec - hip_vec).normal())

        # Draw the joints & set orientation
        root = cmds.joint(
            position=root_vec,
            name=naming.parse([self.name, "legRoot"], side=self.side, suffix="jInit"),
        )
        hip = cmds.joint(
            position=hip_vec,
            name=naming.parse([self.name, "hip"], side=self.side, suffix="jInit"),
        )
        knee = cmds.joint(
            position=knee_vec,
            name=naming.parse([self.name, "knee"], side=self.side, suffix="jInit"),
        )
        foot = cmds.joint(
            position=foot_vec,
            name=naming.parse([self.name, "foot"], side=self.side, suffix="jInit"),
        )
        joint.orient_joints(
            [root, hip, knee, foot],
            world_up_axis=self.mirrorVector,
            up_axis=(0, 1, 0),
            reverse_aim=self.sideMultiplier,
        )

        ball = cmds.joint(
            position=ball_vec,
            name=naming.parse([self.name, "ball"], side=self.side, suffix="jInit"),
        )
        toe = cmds.joint(
            position=toe_vec,
            name=naming.parse([self.name, "toe"], side=self.side, suffix="jInit"),
        )
        cmds.select(clear=True)
        bankout = cmds.joint(
            position=bankout_vec,
            name=naming.parse([self.name, "bankOut"], side=self.side, suffix="jInit"),
        )
        cmds.select(clear=True)
        bankin = cmds.joint(
            position=bankin_vec,
            name=naming.parse([self.name, "bankIn"], side=self.side, suffix="jInit"),
        )
        cmds.select(clear=True)
        toepv = cmds.joint(
            position=toepv_vec,
            name=naming.parse([self.name, "toePivot"], side=self.side, suffix="jInit"),
        )
        cmds.select(clear=True)
        heelpv = cmds.joint(
            position=heelpv_vec,
            name=naming.parse([self.name, "heelPivot"], side=self.side, suffix="jInit"),
        )

        cmds.parent(heelpv, foot)
        cmds.parent(toepv, foot)
        cmds.parent(bankin, foot)
        cmds.parent(bankout, foot)

        joint.orient_joints(
            [ball, toe],
            world_up_axis=self.mirrorVector,
            up_axis=(0, 1, 0),
            reverse_aim=self.sideMultiplier,
        )

        # Update the guideJoints list
        self.guideJoints = [
            root,
            hip,
            knee,
            foot,
            ball,
            toe,
            bankout,
            bankin,
            toepv,
            heelpv,
        ]

    def define_guides(self):
        """Override the guide definition method"""
        joint.set_joint_type(self.guideJoints[0], "LegRoot")
        joint.set_joint_type(self.guideJoints[1], "Hip")
        joint.set_joint_type(self.guideJoints[2], "Knee")
        joint.set_joint_type(self.guideJoints[3], "Foot")
        joint.set_joint_type(self.guideJoints[4], "Ball")
        joint.set_joint_type(self.guideJoints[5], "Toe")
        joint.set_joint_type(self.guideJoints[6], "BankOUT")
        joint.set_joint_type(self.guideJoints[7], "BankIN")
        joint.set_joint_type(self.guideJoints[8], "ToePV")
        joint.set_joint_type(self.guideJoints[9], "HeelPV")
