from maya import cmds
from trigger.library import functions as extra
from trigger.library import controllers as ic
from trigger.library import ribbon as rc

import pymel.core.datatypes as dt

class Leg(object):
    def __init__(self, leginits, suffix="", side="L"):

        if len(leginits) < 9:
            cmds.error("Some or all Leg Init Bones are missing (or Renamed)")
            return

        if not type(leginits) == dict and not type(leginits) == list:
            cmds.error("Init joints must be list or dictionary")
            return

        # reinitialize the dictionary for easy use
        if type(leginits) == dict:
            self.leg_root_ref = leginits["LegRoot"]
            self.hip_ref = leginits["Hip"]
            self.knee_ref = leginits["Knee"]
            self.foot_ref = leginits["Foot"]
            self.ball_ref = leginits["Ball"]
            self.heel_pv_ref = leginits["HeelPV"]
            self.toe_pv_ref = leginits["ToePV"]
            self.bank_in_ref = leginits["BankIN"]
            self.bank_out_ref = leginits["BankOUT"]
        else:
            self.leg_root_ref = leginits[0]
            self.hip_ref = leginits[1]
            self.knee_ref = leginits[2]
            self.foot_ref = leginits[3]
            self.ball_ref = leginits[4]
            self.heel_pv_ref = leginits[5]
            self.toe_pv_ref = leginits[6]
            self.bank_in_ref = leginits[7]
            self.bank_out_ref = leginits[8]

        # get positions
        self.leg_root_pos = extra.getWorldTranslation(self.leg_root_ref)
        self.hip_pos = extra.getWorldTranslation(self.hip_ref)
        self.knee_pos = extra.getWorldTranslation(self.knee_ref)
        self.foot_pos = extra.getWorldTranslation(self.foot_ref)
        self.ball_pos = extra.getWorldTranslation(self.ball_ref)
        self.toe_pv_pos = extra.getWorldTranslation(self.toe_pv_ref)

        # get distances
        self.init_upper_leg_dist = extra.getDistance(self.hip_ref, self.knee_ref)
        self.init_lower_leg_dist = extra.getDistance(self.knee_ref, self.foot_ref)
        self.init_ball_dist = extra.getDistance(self.foot_ref, self.ball_ref)
        self.init_toe_dist = extra.getDistance(self.ball_ref, self.toe_pv_ref)
        self.init_foot_length = extra.getDistance(self.toe_pv_ref, self.heel_pv_ref)
        self.init_foot_width = extra.getDistance(self.bank_in_ref, self.bank_out_ref)

        self.sideMult = -1 if side == "R" else 1
        self.side = side

        self.up_axis, self.mirror_axis, self.look_axis = extra.getRigAxes(self.leg_root_ref)

        # get if orientation should be derived from the initial Joints
        try: self.useRefOrientation = cmds.getAttr("%s.useRefOri" % self.leg_root_ref)
        except:
            cmds.warning("Cannot find Inherit Orientation Attribute on Initial Root Joint %s... Skipping inheriting." %self.leg_root_ref)
            self.useRefOrientation = False

        # self.originalSuffix = suffix
        self.suffix = (extra.uniqueName("limbGrp_%s" % suffix)).replace("limbGrp_", "")

        # scratch variables
        self.sockets = []
        self.limbGrp = None
        self.scaleGrp = None
        self.nonScaleGrp = None
        self.limbPlug = None
        self.scaleConstraints = []
        self.anchors = []
        self.anchorLocations = []
        self.deformerJoints = []
        self.colorCodes = [6, 18]

    def createGrp(self):
        self.limbGrp = cmds.group(name="limbGrp_%s" % self.suffix, em=True)
        self.scaleGrp = cmds.group(name="scaleGrp_%s" % self.suffix, em=True)
        extra.alignTo(self.scaleGrp, self.leg_root_ref, position=True, rotation=False)
        self.nonScaleGrp = cmds.group(name="NonScaleGrp_%s" % self.suffix, em=True)

        cmds.addAttr(self.scaleGrp, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True)
        cmds.addAttr(self.scaleGrp, at="bool", ln="Joints_Visibility", sn="jointVis", defaultValue=True)
        cmds.addAttr(self.scaleGrp, at="bool", ln="Rig_Visibility", sn="rigVis", defaultValue=False)
        # make the created attributes visible in the channelbox
        cmds.setAttr("%s.contVis" % self.scaleGrp, cb=True)
        cmds.setAttr("%s.jointVis" % self.scaleGrp, cb=True)
        cmds.setAttr("%s.rigVis" % self.scaleGrp, cb=True)

        cmds.parent(self.scaleGrp, self.limbGrp)
        cmds.parent(self.nonScaleGrp, self.limbGrp)

    def createJoints(self):
        # Create Limb Plug
        cmds.select(d=True)
        self.limbPlug = cmds.joint(name="limbPlug_%s" % self.suffix, p=self.leg_root_pos, radius=3)

        self.jDef_legRoot = cmds.joint(name="jDef_legRoot_%s" % self.suffix, p=self.leg_root_pos, radius=1.5)
        self.sockets.append(self.jDef_legRoot)
        self.j_def_hip = cmds.joint(name="jDef_hip_%s" % self.suffix, p=self.hip_pos, radius=1.5)
        self.sockets.append(self.j_def_hip)

        if not self.useRefOrientation:
            extra.orientJoints([self.jDef_legRoot, self.j_def_hip], worldUpAxis=dt.Vector(self.mirror_axis),
                               reverseAim=self.sideMult)
        else:
            extra.alignTo(self.jDef_legRoot, self.leg_root_ref, position=True, rotation=True)
            cmds.makeIdentity(self.jDef_legRoot, a=True)
            extra.alignTo(self.j_def_hip, self.hip_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_def_hip, a=True)

        cmds.select(d=True)
        self.j_def_midLeg = cmds.joint(name="jDef_knee_%s" % self.suffix, p=self.knee_pos, radius=1.5)
        self.sockets.append(self.j_def_midLeg)

        cmds.select(d=True)
        self.j_def_foot = cmds.joint(name="jDef_Foot_%s" % self.suffix, p=self.foot_pos, radius=1.0)
        self.sockets.append(self.j_def_foot)
        self.j_def_ball = cmds.joint(name="jDef_Ball_%s" % self.suffix, p=self.ball_pos, radius=1.0)
        self.sockets.append(self.j_def_ball)
        self.j_toe = cmds.joint(name="jDef_Toe_%s" % self.suffix, p=self.toe_pv_pos, radius=1.0)  # POSSIBLE PROBLEM
        self.sockets.append(self.j_toe)

        cmds.select(d=True)
        self.j_socket_ball = cmds.joint(name="jBallSocket_%s" % self.suffix, p=self.ball_pos, radius=3)
        self.sockets.append(self.j_socket_ball)
        # IK Joints
        # Follow IK Chain
        cmds.select(d=True)
        self.j_ik_orig_root = cmds.joint(name="jIK_orig_Root_%s" % self.suffix, p=self.hip_pos, radius=1.5)
        self.j_ik_orig_knee = cmds.joint(name="jIK_orig_Knee_%s" % self.suffix, p=self.knee_pos, radius=1.5)
        self.j_ik_orig_end = cmds.joint(name="jIK_orig_End_%s" % self.suffix, p=self.foot_pos, radius=1.5)

        # Single Chain IK
        cmds.select(d=True)
        self.j_ik_sc_root = cmds.joint(name="jIK_SC_Root_%s" % self.suffix, p=self.hip_pos, radius=1)
        self.j_ik_sc_knee = cmds.joint(name="jIK_SC_Knee_%s" % self.suffix, p=self.knee_pos, radius=1)
        self.j_ik_sc_end = cmds.joint(name="jIK_SC_End_%s" % self.suffix, p=self.foot_pos, radius=1)

        # Rotate Plane IK
        cmds.select(d=True)
        self.j_ik_rp_root = cmds.joint(name="jIK_RP_Root_%s" % self.suffix, p=self.hip_pos, radius=0.7)
        self.j_ik_rp_knee = cmds.joint(name="jIK_RP_Knee_%s" % self.suffix, p=self.knee_pos, radius=0.7)
        self.j_ik_rp_end = cmds.joint(name="jIK_RP_End_%s" % self.suffix, p=self.foot_pos, radius=0.7)

        cmds.select(d=True)
        self.j_ik_foot = cmds.joint(name="jIK_Foot_%s" % self.suffix, p=self.foot_pos, radius=1.0)
        self.j_ik_ball = cmds.joint(name="jIK_Ball_%s" % self.suffix, p=self.ball_pos, radius=1.0)
        self.j_ik_toe = cmds.joint(name="jIK_Toe_%s" % self.suffix, p=self.toe_pv_pos, radius=1.0)

        cmds.select(d=True)

        # orientations
        if not self.useRefOrientation:
            extra.orientJoints([self.j_ik_orig_root, self.j_ik_orig_knee, self.j_ik_orig_end],
                               worldUpAxis=dt.Vector(self.mirror_axis), reverseAim=self.sideMult)

        else:
            extra.alignTo(self.j_ik_orig_root, self.hip_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_orig_root, a=True)
            extra.alignTo(self.j_ik_orig_knee, self.knee_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_orig_knee, a=True)
            extra.alignTo(self.j_ik_orig_end, self.foot_ref,  position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_orig_end, a=True)

        if not self.useRefOrientation:
            extra.orientJoints([self.j_ik_sc_root, self.j_ik_sc_knee, self.j_ik_sc_end],
                               worldUpAxis=dt.Vector(self.mirror_axis), reverseAim=self.sideMult)
        else:
            extra.alignTo(self.j_ik_sc_root, self.hip_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_sc_root, a=True)
            extra.alignTo(self.j_ik_sc_knee, self.knee_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_sc_knee, a=True)
            extra.alignTo(self.j_ik_sc_end, self.foot_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_sc_end, a=True)

        if not self.useRefOrientation:
            extra.orientJoints([self.j_ik_rp_root, self.j_ik_rp_knee, self.j_ik_rp_end], worldUpAxis=dt.Vector(self.mirror_axis), reverseAim=self.sideMult)


        else:
            extra.alignTo(self.j_ik_rp_root, self.hip_ref,  position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_rp_root, a=True)
            extra.alignTo(self.j_ik_rp_knee, self.knee_ref,  position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_rp_knee, a=True)
            extra.alignTo(self.j_ik_rp_end, self.foot_ref,  position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_rp_end, a=True)

        if not self.useRefOrientation:
            extra.orientJoints([self.j_ik_foot, self.j_ik_ball, self.j_ik_toe], worldUpAxis=dt.Vector(self.mirror_axis),
                               reverseAim=self.sideMult)
        else:
            extra.alignTo(self.j_ik_foot, self.foot_ref,  position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_foot, a=True)
            extra.alignTo(self.j_ik_ball, self.ball_ref,  position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_ball, a=True)
            extra.alignTo(self.j_ik_toe, self.toe_pv_ref,  position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_toe, a=True)

        # FK Joints
        cmds.select(d=True)
        self.jfk_root = cmds.joint(name="jFK_UpLeg_%s" % self.suffix, p=self.hip_pos, radius=1.0)
        self.jfk_knee = cmds.joint(name="jFK_Knee_%s" % self.suffix, p=self.knee_pos, radius=1.0)
        self.jfk_foot = cmds.joint(name="jFK_Foot_%s" % self.suffix, p=self.foot_pos, radius=1.0)
        self.jfk_ball = cmds.joint(name="jFK_Ball_%s" % self.suffix, p=self.ball_pos, radius=1.0)
        self.jfk_toe = cmds.joint(name="jFK_Toe_%s" % self.suffix, p=self.toe_pv_pos, radius=1.0)

        if not self.useRefOrientation:
            extra.orientJoints([self.jfk_root, self.jfk_knee, self.jfk_foot, self.jfk_ball, self.jfk_toe],
                               worldUpAxis=dt.Vector(self.mirror_axis), reverseAim=self.sideMult)
        else:
            extra.alignTo(self.jfk_root, self.hip_ref,  position=True, rotation=True)
            cmds.makeIdentity(self.jfk_root, a=True)
            extra.alignTo(self.jfk_knee, self.knee_ref,  position=True, rotation=True)
            cmds.makeIdentity(self.jfk_knee, a=True)
            extra.alignTo(self.jfk_foot, self.foot_ref,  position=True, rotation=True)
            cmds.makeIdentity(self.jfk_foot, a=True)
            extra.alignTo(self.jfk_ball, self.ball_ref,  position=True, rotation=True)
            cmds.makeIdentity(self.jfk_ball, a=True)
            extra.alignTo(self.jfk_toe, self.toe_pv_ref,  position=True, rotation=True)
            cmds.makeIdentity(self.jfk_toe, a=True)

        # re-orient single joints
        extra.alignToAlter(self.j_def_hip, self.jfk_root, mode=2)
        cmds.makeIdentity(self.j_def_hip, a=True)
        extra.alignToAlter(self.j_def_midLeg, self.jfk_knee, mode=2)
        cmds.makeIdentity(self.j_def_midLeg, a=True)

        extra.alignToAlter(self.j_def_foot, self.jfk_foot, mode=2)
        cmds.makeIdentity(self.j_def_foot, a=True)
        extra.alignToAlter(self.j_def_ball, self.jfk_ball, mode=2)
        cmds.makeIdentity(self.j_def_ball, a=True)
        extra.alignToAlter(self.j_toe, self.jfk_toe, mode=2)
        cmds.makeIdentity(self.j_toe, a=True)

        extra.alignToAlter(self.j_socket_ball, self.jfk_ball, mode=2)
        cmds.makeIdentity(self.j_socket_ball, a=True)
        cmds.parent(self.j_socket_ball, self.j_def_ball)


        cmds.parent(self.j_def_midLeg, self.scaleGrp)
        cmds.parent(self.jfk_root, self.scaleGrp)
        cmds.parent(self.j_def_foot, self.scaleGrp)

        self.deformerJoints += [self.j_def_midLeg, self.j_def_hip, self.jDef_legRoot, self.j_def_foot, self.j_def_ball]

        cmds.connectAttr("%s.rigVis" % self.scaleGrp,"%s.v" %self.jfk_root)

    def createControllers(self):
        icon = ic.Icon()
        # Thigh Controller
        thigh_cont_scale = (self.init_upper_leg_dist / 4, self.init_upper_leg_dist / 4, self.init_upper_leg_dist / 16)
        self.cont_thigh, _ = icon.createIcon("Cube", iconName="%s_Thigh_cont" % self.suffix, scale=thigh_cont_scale, normal=(0, 0, self.sideMult))
        extra.alignToAlter(self.cont_thigh, self.jfk_root, mode=2)
        cmds.move(0, self.sideMult*((thigh_cont_scale[0] * 2)), 0, self.cont_thigh, r=True, os=True)
        cmds.xform(self.cont_thigh, piv=self.leg_root_pos, ws=True)

        self.cont_thigh_off = extra.createUpGrp(self.cont_thigh, "OFF")
        self.cont_thigh_ore = extra.createUpGrp(self.cont_thigh, "ORE")
        self.cont_thigh_auto = extra.createUpGrp(self.cont_thigh, "Auto")

        cmds.xform(self.cont_thigh_off, piv=self.leg_root_pos, ws=True)
        cmds.xform(self.cont_thigh_ore, piv=self.leg_root_pos, ws=True)
        cmds.xform(self.cont_thigh_auto, piv=self.leg_root_pos, ws=True)

        # IK Foot Controller
        foot_cont_scale = (self.init_foot_length * 0.75, 1, self.init_foot_width * 0.8)
        # self.cont_IK_foot = icon.circle("cont_IK_foot_%s" % self.suffix, scale=foot_cont_scale, normal=(0, 1, 0))
        self.cont_IK_foot, _ = icon.createIcon("Circle", iconName="%s_IK_foot_cont" % self.suffix, scale=foot_cont_scale, normal=(0, 0, self.sideMult))

        # align it to the ball socket
        extra.alignToAlter(self.cont_IK_foot, self.j_socket_ball, mode=2)
        cmds.xform(self.cont_IK_foot, piv=self.foot_pos, p=True, ws=True)

        self.cont_IK_OFF = extra.createUpGrp(self.cont_IK_foot, "OFF")
        cont_ik_foot_ore = extra.createUpGrp(self.cont_IK_foot, "ORE")
        cont_ik_foot_pos = extra.createUpGrp(self.cont_IK_foot, "POS")

        cmds.addAttr(self.cont_IK_foot, shortName="polevector", longName="Pole_Vector", defaultValue=0.0, minValue=0.0, maxValue=1.0,
                   at="double", k=True)
        cmds.addAttr(self.cont_IK_foot, shortName="sUpLeg", longName="Scale_Upper_Leg", defaultValue=1.0, minValue=0.0, at="double", k=True)
        cmds.addAttr(self.cont_IK_foot, shortName="sLowLeg", longName="Scale_Lower_Leg", defaultValue=1.0, minValue=0.0, at="double", k=True)
        cmds.addAttr(self.cont_IK_foot, shortName="squash", longName="Squash", defaultValue=0.0, minValue=0.0, maxValue=1.0, at="double", k=True)
        cmds.addAttr(self.cont_IK_foot, shortName="stretch", longName="Stretch", defaultValue=1.0, minValue=0.0, maxValue=1.0, at="double",
                 k=True)
        cmds.addAttr(self.cont_IK_foot, shortName="stretchLimit", longName="StretchLimit", defaultValue=100.0, minValue=0.0,
                 maxValue=1000.0, at="double", k=True)
        cmds.addAttr(self.cont_IK_foot, shortName="softIK", longName="SoftIK", defaultValue=0.0, minValue=0.0, maxValue=100.0, k=True)
        cmds.addAttr(self.cont_IK_foot, shortName="volume", longName="Volume_Preserve", defaultValue=0.0, at="double", k=True)
        cmds.addAttr(self.cont_IK_foot, shortName="bLean", longName="Ball_Lean", defaultValue=0.0, at="double", k=True)
        cmds.addAttr(self.cont_IK_foot, shortName="bRoll", longName="Ball_Roll", defaultValue=0.0, at="double", k=True)
        cmds.addAttr(self.cont_IK_foot, shortName="bSpin", longName="Ball_Spin", defaultValue=0.0, at="double", k=True)
        cmds.addAttr(self.cont_IK_foot, shortName="hRoll", longName="Heel_Roll", defaultValue=0.0, at="double", k=True)
        cmds.addAttr(self.cont_IK_foot, shortName="hSpin", longName="Heel_Spin", defaultValue=0.0, at="double", k=True)
        cmds.addAttr(self.cont_IK_foot, shortName="tRoll", longName="Toes_Roll", defaultValue=0.0, at="double", k=True)
        cmds.addAttr(self.cont_IK_foot, shortName="tSpin", longName="Toes_Spin", defaultValue=0.0, at="double", k=True)
        cmds.addAttr(self.cont_IK_foot, shortName="tWiggle", longName="Toes_Wiggle", defaultValue=0.0, at="double", k=True)
        cmds.addAttr(self.cont_IK_foot, shortName="bank", longName="Bank", defaultValue=0.0, at="double", k=True)

        # Pole Vector Controller
        polecont_scale = ((((self.init_upper_leg_dist + self.init_lower_leg_dist) / 2) / 10), (((self.init_upper_leg_dist + self.init_lower_leg_dist) / 2) / 10), (((self.init_upper_leg_dist + self.init_lower_leg_dist) / 2) / 10))
        self.cont_Pole, _ = icon.createIcon("Plus", iconName="%s_Pole_cont" % self.suffix, scale=polecont_scale, normal=self.mirror_axis)
        offset_mag_pole = ((self.init_upper_leg_dist + self.init_lower_leg_dist) / 4)
        offset_vector_pole = extra.getBetweenVector(self.j_def_midLeg, [self.j_def_hip, self.jfk_foot])

        extra.alignAndAim(self.cont_Pole,
                          targetList=[self.j_def_midLeg],
                          aimTargetList=[self.j_def_hip, self.jfk_foot],
                          upVector=self.up_axis,
                          translateOff=(offset_vector_pole * offset_mag_pole)
                          )

        self.cont_pole_off = extra.createUpGrp(self.cont_Pole, "OFF")
        self.cont_pole_vis = extra.createUpGrp(self.cont_Pole, "VIS")

        ## FK UP Leg Controller
        scalecont_fk_up_leg = (self.init_upper_leg_dist / 2, self.init_upper_leg_dist / 6, self.init_upper_leg_dist / 6)

        self.cont_fk_up_leg, dmp = icon.createIcon("Cube", iconName="cont_FK_Upleg_%s" % self.suffix, scale=scalecont_fk_up_leg)

        # move the pivot to the bottom
        cmds.xform(self.cont_fk_up_leg, piv=(self.sideMult * -(self.init_upper_leg_dist / 2), 0, 0), ws=True)

        # move the controller to the shoulder
        extra.alignToAlter(self.cont_fk_up_leg, self.jfk_root, mode=2)

        self.cont_fk_up_leg_off = extra.createUpGrp(self.cont_fk_up_leg, "OFF")
        self.cont_fk_up_leg_ore = extra.createUpGrp(self.cont_fk_up_leg, "ORE")
        cmds.xform(self.cont_fk_up_leg_off, piv=self.hip_pos, ws=True)
        cmds.xform(self.cont_fk_up_leg_ore, piv=self.hip_pos, ws=True)

        ## FK LOW Leg Controller
        scalecont_fk_low_leg = (self.init_lower_leg_dist / 2, self.init_lower_leg_dist / 6, self.init_lower_leg_dist / 6)
        # self.cont_fk_low_leg = icon.cube("cont_FK_LowLeg_%s" % self.suffix, scalecont_fk_low_leg)
        self.cont_fk_low_leg, dmp = icon.createIcon("Cube", iconName="cont_FK_LowLeg_%s" % self.suffix, scale=scalecont_fk_low_leg)

        # move the pivot to the bottom
        cmds.xform(self.cont_fk_low_leg, piv=(self.sideMult * -(self.init_lower_leg_dist / 2), 0, 0), ws=True)

        # align position and orientation to the joint
        extra.alignToAlter(self.cont_fk_low_leg, self.jfk_knee, mode=2)

        self.cont_fk_low_leg_off = extra.createUpGrp(self.cont_fk_low_leg, "OFF")
        self.cont_fk_low_leg_ore = extra.createUpGrp(self.cont_fk_low_leg, "ORE")
        cmds.xform(self.cont_fk_low_leg_off, piv=self.knee_pos, ws=True)
        cmds.xform(self.cont_fk_low_leg_ore, piv=self.knee_pos, ws=True)

        ## FK FOOT Controller
        scalecont_fk_foot = (self.init_ball_dist / 2, self.init_ball_dist / 3, self.init_foot_width / 2)
        # self.cont_fk_foot = icon.cube("cont_FK_Foot_%s" % self.suffix, scalecont_fk_foot)
        self.cont_fk_foot, _ = icon.createIcon("Cube", iconName="%s_FK_Foot_cont" % self.suffix, scale=scalecont_fk_foot)
        extra.alignToAlter(self.cont_fk_foot, self.jfk_foot, mode=2)

        self.cont_fk_foot_off = extra.createUpGrp(self.cont_fk_foot, "OFF")
        self.cont_fk_foot_ore = extra.createUpGrp(self.cont_fk_foot, "ORE")

        # FK Ball Controller
        scalecont_fk_ball = (self.init_toe_dist / 2, self.init_toe_dist / 3, self.init_foot_width / 2)
        self.cont_fk_ball, _ = icon.createIcon("Cube", iconName="%s_FK_Ball_cont" % self.suffix, scale=scalecont_fk_ball)
        extra.alignToAlter(self.cont_fk_ball, self.jfk_ball, mode=2)

        self.cont_fk_ball_off = extra.createUpGrp(self.cont_fk_ball, "OFF")
        self.cont_fk_ball_ore = extra.createUpGrp(self.cont_fk_ball, "ORE")

        # FK-IK SWITCH Controller
        icon_scale = self.init_upper_leg_dist / 4
        self.cont_fk_ik, self.fk_ik_rvs = icon.createIcon("FkikSwitch", iconName="cont_FK_IK_%s" % self.suffix, scale=(icon_scale, icon_scale, icon_scale))

        extra.alignAndAim(self.cont_fk_ik, targetList=[self.jfk_foot], aimTargetList=[self.j_def_midLeg],
                          upVector=self.up_axis, rotateOff=(self.sideMult*90, self.sideMult*90, 0))
        cmds.move(icon_scale * 2, 0, 0, self.cont_fk_ik, r=True, os=True)
        self.cont_fk_ik_pos = extra.createUpGrp(self.cont_fk_ik, "POS")

        cmds.setAttr("{0}.s{1}".format(self.cont_fk_ik, "x"), self.sideMult)

        # controller for twist orientation alignment
        cmds.addAttr(self.cont_fk_ik, shortName="autoHip", longName="Auto_Hip", defaultValue=1.0, at="float",
                   minValue=0.0, maxValue=1.0, k=True)
        cmds.addAttr(self.cont_fk_ik, shortName="alignHip", longName="Align_Hip", defaultValue=1.0, at="float",
                   minValue=0.0, maxValue=1.0, k=True)

        cmds.addAttr(self.cont_fk_ik, shortName="footAutoTwist", longName="Foot_Auto_Twist", defaultValue=1.0,
                   minValue=0.0,
                   maxValue=1.0, at="float", k=True)
        cmds.addAttr(self.cont_fk_ik, shortName="footManualTwist", longName="Foot_Manual_Twist", defaultValue=0.0,
                   at="float",
                   k=True)

        cmds.addAttr(self.cont_fk_ik, shortName="upLegAutoTwist", longName="UpLeg_Auto_Twist", defaultValue=1.0,
                   minValue=0.0, maxValue=1.0, at="float", k=True)
        cmds.addAttr(self.cont_fk_ik, shortName="upLegManualTwist", longName="UpLeg_Manual_Twist", defaultValue=0.0,
                   at="float", k=True)

        cmds.addAttr(self.cont_fk_ik, shortName="allowScaling", longName="Allow_Scaling", defaultValue=1.0, minValue=0.0,
                   maxValue=1.0, at="float", k=True)
        cmds.addAttr(self.cont_fk_ik, at="enum", k=True, shortName="interpType", longName="Interp_Type", en="No_Flip:Average:Shortest:Longest:Cache", defaultValue=0)

        cmds.addAttr(self.cont_fk_ik, shortName="tweakControls", longName="Tweak_Controls", defaultValue=0, at="bool")
        cmds.setAttr("%s.tweakControls" % self.cont_fk_ik, cb=True)
        cmds.addAttr(self.cont_fk_ik, shortName="fingerControls", longName="Finger_Controls", defaultValue=1, at="bool")
        cmds.setAttr("%s.fingerControls" % self.cont_fk_ik, cb=True)

        ### Create MidLock controller

        midcont_scale = (self.init_lower_leg_dist / 4, self.init_lower_leg_dist / 4, self.init_lower_leg_dist / 4)
        self.cont_mid_lock, _ = icon.createIcon("Star", iconName="%s_mid_cont" % self.suffix, scale=midcont_scale, normal=self.mirror_axis)

        extra.alignToAlter(self.cont_mid_lock, self.jfk_knee, 2)
        self.cont_mid_lock_ext = extra.createUpGrp(self.cont_mid_lock, "EXT")
        self.cont_mid_lock_pos = extra.createUpGrp(self.cont_mid_lock, "POS")
        self.cont_mid_lock_ave = extra.createUpGrp(self.cont_mid_lock, "AVE")

        cmds.parent(self.cont_thigh_off, self.scaleGrp)
        cmds.parent(self.cont_fk_up_leg_off, self.scaleGrp)
        cmds.parent(self.cont_fk_low_leg_off, self.scaleGrp)
        cmds.parent(self.cont_fk_foot_off, self.scaleGrp)
        cmds.parent(self.cont_mid_lock_ext, self.scaleGrp)
        cmds.parent(self.cont_pole_off, self.scaleGrp)
        cmds.parent(self.cont_fk_ik_pos, self.scaleGrp)
        cmds.parent(self.cont_fk_ball_off, self.scaleGrp)
        cmds.parent(self.cont_IK_OFF, self.limbGrp)

        nodesContVis = [self.cont_pole_off, self.cont_thigh_off, self.cont_IK_OFF, self.cont_fk_foot_off,
                        self.cont_fk_ik_pos,
                        self.cont_fk_low_leg_off, self.cont_fk_up_leg_off, self.cont_mid_lock_pos]

        map(lambda x: cmds.connectAttr("%s.contVis" % self.scaleGrp, "%s.v" % x), nodesContVis)

        extra.colorize(self.cont_thigh, self.colorCodes[0])
        extra.colorize(self.cont_IK_foot, self.colorCodes[0])
        extra.colorize(self.cont_Pole, self.colorCodes[0])
        extra.colorize(self.cont_fk_ik, self.colorCodes[0])
        extra.colorize(self.cont_fk_up_leg, self.colorCodes[0])
        extra.colorize(self.cont_fk_low_leg, self.colorCodes[0])
        extra.colorize(self.cont_fk_foot, self.colorCodes[0])
        extra.colorize(self.cont_fk_ball, self.colorCodes[0])
        extra.colorize(self.cont_mid_lock, self.colorCodes[1])

    def createRoots(self):

        self.master_root = cmds.group(em=True, name="masterRoot_%s" % self.suffix)
        extra.alignTo(self.master_root, self.leg_root_ref, 0)
        cmds.makeIdentity(self.master_root, a=True)

        ## Create Start Lock

        self.start_lock = cmds.spaceLocator(name="startLock_%s" % self.suffix)[0]
        extra.alignToAlter(self.start_lock, self.j_ik_orig_root, 2)
        self.start_lock_ore = extra.createUpGrp(self.start_lock, "_Ore")
        self.start_lock_pos = extra.createUpGrp(self.start_lock, "_Pos")
        self.start_lock_twist = extra.createUpGrp(self.start_lock, "_AutoTwist")

        start_lock_weight = cmds.parentConstraint(self.j_def_hip, self.start_lock, sr=("y", "z"), mo=False)

        cmds.parentConstraint(self.start_lock, self.j_ik_sc_root, mo=True)
        cmds.parentConstraint(self.start_lock, self.j_ik_rp_root, mo=True)

        # Create Midlock

        self.mid_lock = cmds.spaceLocator(name="midLock_%s" % self.suffix)[0]
        cmds.parentConstraint(self.mid_lock, self.j_def_midLeg)
        cmds.parentConstraint(self.cont_mid_lock, self.mid_lock, mo=False)

        ### Create End Lock
        self.end_lock = cmds.spaceLocator(name="endLock_%s" % self.suffix)[0]
        extra.alignTo(self.end_lock, self.jfk_foot, 2)
        self.end_lock_ore = extra.createUpGrp(self.end_lock, "Ore")
        self.end_lock_pos = extra.createUpGrp(self.end_lock, "Pos")
        self.end_lock_twist = extra.createUpGrp(self.end_lock, "Twist")

        cmds.parent(self.mid_lock, self.scaleGrp)
        cmds.parent(self.master_root, self.scaleGrp)

        cmds.connectAttr("%s.rigVis" % self.scaleGrp ,"%s.v" % self.end_lock_twist)
        cmds.connectAttr("%s.rigVis" % self.scaleGrp ,"%s.v" % self.start_lock_ore)
        cmds.connectAttr("%s.rigVis" % self.scaleGrp ,"%s.v" % self.mid_lock)
        cmds.connectAttr("%s.rigVis" % self.scaleGrp ,"%s.v" % self.master_root)

    def createIKsetup(self):

        master_ik = cmds.spaceLocator(name="masterIK_%s" % self.suffix)[0]
        extra.alignTo(master_ik, self.j_def_foot)

        # axis for foot control groups
        foot_plane = cmds.spaceLocator(name="footPlaneLocator")[0]
        cmds.setAttr("%s.rotateOrder" % foot_plane, 0)
        cmds.pointConstraint(self.heel_pv_ref, self.toe_pv_ref, foot_plane)
        cmds.aimConstraint(self.toe_pv_ref, foot_plane, wuo=self.foot_ref, wut="object")

        self.pv_bank_in = cmds.group(name="Pv_BankIn_%s" % self.suffix, em=True)
        extra.alignTo(self.pv_bank_in, self.bank_in_ref, position=True, rotation=True)
        cmds.makeIdentity(self.pv_bank_in, a=True, t=False, r=True, s=True)
        pln_rot = cmds.getAttr("%s.rotate" % foot_plane)[0]
        cmds.setAttr("%s.rotate" % self.pv_bank_in, pln_rot[0], pln_rot[1], pln_rot[2])
        # cmds.parent(self.mid_lock, self.scaleGrp)

        self.pv_bank_out = cmds.group(name="Pv_BankOut_%s" % self.suffix, em=True)
        extra.alignTo(self.pv_bank_out, self.bank_out_ref, position=True, rotation=True)
        cmds.makeIdentity(self.pv_bank_out, a=True, t=False, r=True, s=True)
        cmds.setAttr("%s.rotate" % self.pv_bank_out, pln_rot[0], pln_rot[1], pln_rot[2])

        self.pv_toe = cmds.group(name="Pv_Toe_%s" % self.suffix, em=True)
        extra.alignTo(self.pv_toe, self.toe_pv_ref, position=True, rotation=True)
        self.pv_toe_ore = extra.createUpGrp(self.pv_toe, "ORE")

        self.pv_ball = cmds.group(name="Pv_Ball_%s" % self.suffix, em=True)
        extra.alignTo(self.pv_ball, self.ball_ref, position=True, rotation=False)
        self.pv_ball_ore = extra.createUpGrp(self.pv_ball, "ORE")

        # pm.parentConstraint(self.pv_ball, self.j_socket_ball)
        # TODO // SOCKETBALL NEEDS A IK/FK Switch

        self.pv_heel = cmds.group(name="Pv_Heel_%s" % self.suffix, em=True)
        extra.alignTo(self.pv_heel, self.heel_pv_ref, position=True, rotation=True)
        pv_heel_ore = extra.createUpGrp(self.pv_heel, "ORE")

        self.pv_ball_spin = cmds.group(name="Pv_BallSpin_%s" % self.suffix, em=True)
        extra.alignTo(self.pv_ball_spin, self.ball_ref, position=True, rotation=True)
        self.pv_ball_spin_ore = extra.createUpGrp(self.pv_ball_spin, "ORE")

        self.pv_ball_roll = cmds.group(name="Pv_BallRoll_%s" % self.suffix, em=True)
        extra.alignTo(self.pv_ball_roll, self.ball_ref, position=True, rotation=True)
        self.pv_ball_roll_ore = extra.createUpGrp(self.pv_ball_roll, "ORE")

        self.pv_ball_lean = cmds.group(name="Pv_BallLean_%s" % self.suffix, em=True)
        extra.alignTo(self.pv_ball_lean, self.ball_ref, position=True, rotation=True)
        self.pv_ball_lean_ore = extra.createUpGrp(self.pv_ball_lean, "ORE")

        # Create IK handles

        ik_handle_sc = cmds.ikHandle(sj=self.j_ik_sc_root, ee=self.j_ik_sc_end, name="ikHandle_SC_%s" % self.suffix)
        ik_handle_rp = cmds.ikHandle(sj=self.j_ik_rp_root, ee=self.j_ik_rp_end, name="ikHandle_RP_%s" % self.suffix, sol="ikRPsolver")

        cmds.poleVectorConstraint(self.cont_Pole, ik_handle_rp[0])
        cmds.aimConstraint(self.j_ik_rp_knee, self.cont_Pole)

        ik_handle_ball = cmds.ikHandle(sj=self.j_ik_foot, ee=self.j_ik_ball, name="ikHandle_Ball_%s" % self.suffix)
        ik_handle_toe = cmds.ikHandle(sj=self.j_ik_ball, ee=self.j_ik_toe, name="ikHandle_Toe_%s" % self.suffix)

        # Create Hierarchy for Foot

        cmds.parent(ik_handle_ball[0], self.pv_ball)
        cmds.parent(ik_handle_toe[0], self.pv_ball)
        cmds.parent(master_ik, self.pv_ball_lean)
        cmds.parent(ik_handle_sc[0], master_ik)
        cmds.parent(ik_handle_rp[0], master_ik)
        cmds.parent(self.pv_ball_lean_ore, self.pv_ball_roll)
        cmds.parent(self.pv_ball_ore, self.pv_toe)
        cmds.parent(self.pv_ball_roll_ore, self.pv_toe)
        cmds.parent(self.pv_toe_ore, self.pv_ball_spin)
        cmds.parent(self.pv_ball_spin_ore, self.pv_heel)
        cmds.parent(pv_heel_ore, self.pv_bank_out)
        cmds.parent(self.pv_bank_out, self.pv_bank_in)

        ### Create and constrain Distance Locators

        leg_start = cmds.spaceLocator(name="legStart_loc_%s" % self.suffix)[0]
        cmds.pointConstraint(self.start_lock, leg_start, mo=False)

        leg_end = cmds.spaceLocator(name="legEnd_loc_%s" % self.suffix)[0]
        cmds.pointConstraint(master_ik, leg_end, mo=False)

        ### Create Nodes and Connections for Stretchy IK SC

        stretch_offset = cmds.createNode("plusMinusAverage", name="stretchOffset_%s" % self.suffix)
        distance_sc = cmds.createNode("distanceBetween", name="distance_SC_%s" % self.suffix)
        ik_stretch_distance_clamp = cmds.createNode("clamp", name="IK_stretch_distanceClamp_%s" % self.suffix)
        ik_stretch_stretchiness_clamp = cmds.createNode("clamp", name="IK_stretch_stretchinessClamp_%s" % self.suffix)
        extra_scale_mult_sc = cmds.createNode("multiplyDivide", name="extraScaleMult_SC_%s" % self.suffix)
        initial_divide_sc = cmds.createNode("multiplyDivide", name="initialDivide_SC_%s" % self.suffix)
        self.initial_length_multip_sc = cmds.createNode("multiplyDivide", name="initialLengthMultip_SC_%s" % self.suffix)
        stretch_amount_sc = cmds.createNode("multiplyDivide", name="stretchAmount_SC_%s" % self.suffix)
        sum_of_j_lengths_sc = cmds.createNode("plusMinusAverage", name="sumOfJLengths_SC_%s" % self.suffix)
        squashiness_sc = cmds.createNode("blendColors", name="squashiness_SC_%s" % self.suffix)
        self.stretchiness_sc = cmds.createNode("blendColors", name="stretchiness_SC_%s" % self.suffix)

        cmds.setAttr("%s.maxR" % ik_stretch_stretchiness_clamp, 1)
        cmds.setAttr("%s.input1X" % self.initial_length_multip_sc, self.init_upper_leg_dist)
        cmds.setAttr("%s.input1Y" % self.initial_length_multip_sc, self.init_lower_leg_dist)
        cmds.setAttr("%s.operation" % initial_divide_sc, 2)
        #
        ### IkSoft nodes
        ik_soft_clamp = cmds.createNode("clamp", name="ikSoft_clamp_%s" % self.suffix)
        cmds.setAttr("%s.minR" % ik_soft_clamp, 0.0001)
        cmds.setAttr("%s.maxR" % ik_soft_clamp, 99999)

        ik_soft_sub1 = cmds.createNode("plusMinusAverage", name="ikSoft_Sub1_%s" % self.suffix)
        cmds.setAttr("%s.operation" % ik_soft_sub1, 2)

        ik_soft_sub2 = cmds.createNode("plusMinusAverage", name="ikSoft_Sub2_%s" % self.suffix)
        cmds.setAttr("%s.operation" % ik_soft_sub2, 2)

        ik_soft_div1 = cmds.createNode("multiplyDivide", name="ikSoft_Div1_%s" % self.suffix)
        cmds.setAttr("%s.operation" % ik_soft_div1, 2)

        ik_soft_mult1 = cmds.createNode("multDoubleLinear", name="ikSoft_Mult1_%s" % self.suffix)
        cmds.setAttr("%s.input1" % ik_soft_mult1, -1)

        ik_soft_pow = cmds.createNode("multiplyDivide", name="ikSoft_Pow_%s" % self.suffix)
        cmds.setAttr("%s.operation" % ik_soft_pow, 3)
        cmds.setAttr("%s.input1X" % ik_soft_pow, 2.718)

        ik_soft_mult2 = cmds.createNode("multDoubleLinear", name="ikSoft_Mult2_%s" % self.suffix)

        ik_soft_sub3 = cmds.createNode("plusMinusAverage", name="ikSoft_Sub3_%s" % self.suffix)
        cmds.setAttr("%s.operation" % ik_soft_sub3, 2)

        ik_soft_condition = cmds.createNode("condition", name="ikSoft_Condition_%s" % self.suffix)
        cmds.setAttr("%s.operation" % ik_soft_condition, 2)

        ik_soft_div2 = cmds.createNode("multiplyDivide", name="ikSoft_Div2_%s" % self.suffix)
        cmds.setAttr("%s.operation" % ik_soft_div2, 2)

        ik_soft_stretch_amount = cmds.createNode("multiplyDivide", name="ikSoft_stretchAmount_SC_%s" % self.suffix)
        cmds.setAttr("%s.operation" % ik_soft_stretch_amount, 1)

        ### Bind Attributes and make constraints


        # Bind Stretch Attributes
        cmds.connectAttr("%s.translate" % leg_start, "%s.point1" % distance_sc)
        cmds.connectAttr("%s.translate" % leg_end, "%s.point2" % distance_sc)
        cmds.connectAttr("%s.distance" % distance_sc, "%s.inputR" % ik_stretch_distance_clamp)
        cmds.connectAttr("%s.outputR" % ik_stretch_distance_clamp, "%s.input1X" % initial_divide_sc)
        cmds.connectAttr("%s.outputR" % ik_stretch_stretchiness_clamp, "%s.blender" % self.stretchiness_sc)
        cmds.connectAttr("%s.outputX" % initial_divide_sc, "%s.input2X" % stretch_amount_sc)
        cmds.connectAttr("%s.outputX" % initial_divide_sc, "%s.input2Y" % stretch_amount_sc)
        cmds.connectAttr("%s.outputX" % self.initial_length_multip_sc, "%s.input1X" % extra_scale_mult_sc)
        cmds.connectAttr("%s.outputY" % self.initial_length_multip_sc, "%s.input1Y" % extra_scale_mult_sc)
        cmds.connectAttr("%s.outputX" % self.initial_length_multip_sc, "%s.input1D[0]" % stretch_offset)
        cmds.connectAttr("%s.outputY" % self.initial_length_multip_sc, "%s.input1D[1]" % stretch_offset)
        cmds.connectAttr("%s.outputX" % extra_scale_mult_sc, "%s.input1X" % stretch_amount_sc)
        cmds.connectAttr("%s.outputY" % extra_scale_mult_sc, "%s.input1Y" % stretch_amount_sc)
        cmds.connectAttr("%s.outputX" % extra_scale_mult_sc, "%s.color2R" % self.stretchiness_sc)
        cmds.connectAttr("%s.outputY" % extra_scale_mult_sc, "%s.color2G" % self.stretchiness_sc)
        cmds.connectAttr("%s.outputX" % extra_scale_mult_sc, "%s.input1D[0]" % sum_of_j_lengths_sc)
        cmds.connectAttr("%s.outputY" % extra_scale_mult_sc, "%s.input1D[1]" % sum_of_j_lengths_sc)
        cmds.connectAttr("%s.outputX" % stretch_amount_sc, "%s.color1R" % squashiness_sc)
        cmds.connectAttr("%s.outputY" % stretch_amount_sc, "%s.color1G" % squashiness_sc)
        cmds.connectAttr("%s.output1D" % sum_of_j_lengths_sc, "%s.input2X" % initial_divide_sc)
        cmds.connectAttr("%s.outputR" % squashiness_sc, "%s.color1R" % self.stretchiness_sc)
        cmds.connectAttr("%s.outputG" % squashiness_sc, "%s.color1G" % self.stretchiness_sc)

        invertedStrSC = cmds.createNode("multiplyDivide")
        cmds.setAttr("%s.input2X" % invertedStrSC, self.sideMult)
        cmds.setAttr("%s.input2Y" % invertedStrSC, self.sideMult)

        cmds.connectAttr("%s.outputR" % self.stretchiness_sc, "%s.input1X" % invertedStrSC)
        cmds.connectAttr("%s.outputG" % self.stretchiness_sc, "%s.input1Y" % invertedStrSC)

        cmds.connectAttr("%s.outputX" % invertedStrSC, "%s.translateX" % self.j_ik_sc_knee)
        cmds.connectAttr("%s.outputY" % invertedStrSC, "%s.translateX" % self.j_ik_sc_end)
        cmds.connectAttr("%s.outputX" % invertedStrSC, "%s.translateX" % self.j_ik_rp_knee)
        cmds.connectAttr("%s.outputY" % invertedStrSC, "%s.translateX" % self.j_ik_rp_end)

        ## iksoft related
        cmds.connectAttr("%s.softIK" % self.cont_IK_foot, "%s.inputR" % ik_soft_clamp)

        cmds.connectAttr("%s.output1D" % sum_of_j_lengths_sc, "%s.input1D[0]" % ik_soft_sub1)
        cmds.connectAttr("%s.outputR" % ik_soft_clamp, "%s.input1D[1]" % ik_soft_sub1)
        cmds.connectAttr("%s.outputR" % ik_stretch_distance_clamp, "%s.input1D[0]" % ik_soft_sub2)
        cmds.connectAttr("%s.output1D" % ik_soft_sub1, "%s.input1D[1]" % ik_soft_sub2)
        cmds.connectAttr("%s.output1D" % ik_soft_sub2, "%s.input1X" % ik_soft_div1)
        cmds.connectAttr("%s.outputR" % ik_soft_clamp, "%s.input2X" % ik_soft_div1)
        cmds.connectAttr("%s.outputX" % ik_soft_div1, "%s.input2" % ik_soft_mult1)

        cmds.connectAttr("%s.output" % ik_soft_mult1, "%s.input2X" % ik_soft_pow)
        cmds.connectAttr("%s.outputR" % ik_soft_clamp, "%s.input1" % ik_soft_mult2)
        cmds.connectAttr("%s.outputX" % ik_soft_pow, "%s.input2" % ik_soft_mult2)
        cmds.connectAttr("%s.output1D" % sum_of_j_lengths_sc, "%s.input1D[0]" % ik_soft_sub3)
        cmds.connectAttr("%s.output" % ik_soft_mult2, "%s.input1D[1]" % ik_soft_sub3)
        cmds.connectAttr("%s.outputR" % ik_stretch_distance_clamp, "%s.firstTerm" % ik_soft_condition)
        cmds.connectAttr("%s.output1D" % ik_soft_sub1, "%s.secondTerm" % ik_soft_condition)
        cmds.connectAttr("%s.output1D" % ik_soft_sub3, "%s.colorIfTrueR" % ik_soft_condition)
        cmds.connectAttr("%s.outputR" % ik_stretch_distance_clamp, "%s.colorIfFalseR" % ik_soft_condition)
        cmds.connectAttr("%s.outputR" % ik_stretch_distance_clamp, "%s.input1X" % ik_soft_div2)
        cmds.connectAttr("%s.outColorR" % ik_soft_condition, "%s.input2X" % ik_soft_div2)
        cmds.connectAttr("%s.outputX" % extra_scale_mult_sc, "%s.input1X" % ik_soft_stretch_amount)
        cmds.connectAttr("%s.outputY" % extra_scale_mult_sc, "%s.input1Y" % ik_soft_stretch_amount)
        cmds.connectAttr("%s.outputX" % ik_soft_div2, "%s.input2X" % ik_soft_stretch_amount)
        cmds.connectAttr("%s.outputX" % ik_soft_div2, "%s.input2Y" % ik_soft_stretch_amount)
        cmds.connectAttr("%s.outputX" % ik_soft_stretch_amount, "%s.color2R" % squashiness_sc)
        cmds.connectAttr("%s.outputY" % ik_soft_stretch_amount, "%s.color2G" % squashiness_sc)
        cmds.connectAttr("%s.rotate" % self.cont_IK_foot, "%s.rotate" % self.j_ik_rp_end)
        # Stretch Attributes Controller connections
        cmds.connectAttr("%s.sUpLeg" % self.cont_IK_foot, "%s.input2X" % extra_scale_mult_sc)
        cmds.connectAttr("%s.sLowLeg" % self.cont_IK_foot, "%s.input2Y" % extra_scale_mult_sc)
        cmds.connectAttr("%s.squash" % self.cont_IK_foot, "%s.blender" % squashiness_sc)
        cmds.connectAttr("%s.output1D" % stretch_offset, "%s.maxR" % ik_stretch_distance_clamp)
        cmds.connectAttr("%s.stretch" % self.cont_IK_foot, "%s.inputR" % ik_stretch_stretchiness_clamp)
        cmds.connectAttr("%s.stretchLimit" % self.cont_IK_foot, "%s.input1D[2]" % stretch_offset)

        #
        # Bind Foot Attributes to the controller
        # create multiply nodes for alignment fix
        mult_al_fix_b_lean = cmds.createNode("multDoubleLinear", name="multAlFix_bLean_{0}".format(self.suffix))
        mult_al_fix_b_roll = cmds.createNode("multDoubleLinear", name="multAlFix_bRoll_{0}".format(self.suffix))
        mult_al_fix_b_spin = cmds.createNode("multDoubleLinear", name="multAlFix_bSpin_{0}".format(self.suffix))
        mult_al_fix_h_roll = cmds.createNode("multDoubleLinear", name="multAlFix_hRoll_{0}".format(self.suffix))
        mult_al_fix_h_spin = cmds.createNode("multDoubleLinear", name="multAlFix_hSpin_{0}".format(self.suffix))
        mult_al_fix_t_roll = cmds.createNode("multDoubleLinear", name="multAlFix_tRoll_{0}".format(self.suffix))
        mult_al_fix_t_spin = cmds.createNode("multDoubleLinear", name="multAlFix_tSpin_{0}".format(self.suffix))
        mult_al_fix_t_wiggle = cmds.createNode("multDoubleLinear", name="multAlFix_tWiggle_{0}".format(self.suffix))

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

        cmds.connectAttr("%s.bLean" % self.cont_IK_foot, "%s.input1" %mult_al_fix_b_lean)
        cmds.connectAttr("%s.bRoll" % self.cont_IK_foot, "%s.input1" %mult_al_fix_b_roll)
        cmds.connectAttr("%s.bSpin" % self.cont_IK_foot, "%s.input1" %mult_al_fix_b_spin)
        cmds.connectAttr("%s.hRoll" % self.cont_IK_foot, "%s.input1" %mult_al_fix_h_roll)
        cmds.connectAttr("%s.hSpin" % self.cont_IK_foot, "%s.input1" %mult_al_fix_h_spin)
        cmds.connectAttr("%s.tRoll" % self.cont_IK_foot, "%s.input1" %mult_al_fix_t_roll)
        cmds.connectAttr("%s.tSpin" % self.cont_IK_foot, "%s.input1" %mult_al_fix_t_spin)
        cmds.connectAttr("%s.tWiggle" % self.cont_IK_foot, "%s.input1" %mult_al_fix_t_wiggle)


        cmds.connectAttr("%s.output" % mult_al_fix_b_lean, "%s.rotateZ" % self.pv_ball_lean)
        cmds.connectAttr("%s.output" % mult_al_fix_b_roll, "%s.rotateY" % self.pv_ball_roll)
        cmds.connectAttr("%s.output" % mult_al_fix_b_spin, "%s.rotateZ" % self.pv_ball_spin)
        cmds.connectAttr("%s.output" % mult_al_fix_h_roll, "%s.rotateX" % self.pv_heel)
        cmds.connectAttr("%s.output" % mult_al_fix_h_spin, "%s.rotateY" % self.pv_heel)
        cmds.connectAttr("%s.output" % mult_al_fix_t_roll, "%s.rotateX" % self.pv_toe)
        cmds.connectAttr("%s.output" % mult_al_fix_t_spin, "%s.rotateY" % self.pv_toe)
        cmds.connectAttr("%s.output" % mult_al_fix_t_wiggle, "%s.rotateY" % self.pv_ball)

        pv_bank_in_ore = extra.createUpGrp(self.pv_bank_in, "ORE")

        cmds.setDrivenKeyframe("%s.rotateX" % self.pv_bank_out, cd="%s.bank" % self.cont_IK_foot, dv=0, v=0, itt='linear', ott='linear')
        cmds.setDrivenKeyframe("%s.rotateX" % self.pv_bank_out, cd="%s.bank" % self.cont_IK_foot, dv=90, v=90 * self.sideMult, itt='linear', ott='linear')

        cmds.setDrivenKeyframe("%s.rotateX" % self.pv_bank_in, cd="%s.bank" % self.cont_IK_foot, dv=0, v=0, itt='linear', ott='linear')
        cmds.setDrivenKeyframe("%s.rotateX" % self.pv_bank_in, cd="%s.bank" % self.cont_IK_foot, dv=-90, v=90 * (-1 * self.sideMult), itt='linear', ott='linear')

        self.ik_parent_grp = cmds.group(name="IK_parentGRP_%s" % self.suffix, em=True)
        extra.alignToAlter(self.ik_parent_grp, self.cont_IK_foot, 2)
        cmds.parent(pv_bank_in_ore, self.ik_parent_grp)
        cmds.parent(self.j_ik_foot, self.ik_parent_grp)
        cmds.parentConstraint(self.j_ik_sc_end, self.j_ik_foot)


        cmds.parentConstraint(self.cont_IK_foot, self.ik_parent_grp, mo=False)

        # parenting should be after the constraint

        blend_ore_ik_root = cmds.createNode("blendColors", name="blendORE_IK_Up_%s" % self.suffix)

        cmds.connectAttr("%s.rotate" % self.j_ik_sc_root, "%s.color2" % blend_ore_ik_root)
        cmds.connectAttr("%s.rotate" % self.j_ik_rp_root, "%s.color1" % blend_ore_ik_root)
        cmds.connectAttr("%s.output" % blend_ore_ik_root, "%s.rotate" % self.j_ik_orig_root)
        cmds.connectAttr("%s.polevector" % self.cont_IK_foot, "%s.blender" % blend_ore_ik_root)

        blend_pos_ik_root = cmds.createNode("blendColors", name="blendPOS_IK_Up_%s" % self.suffix)
        cmds.connectAttr("%s.translate" % self.j_ik_sc_root, "%s.color2" % blend_pos_ik_root)
        cmds.connectAttr("%s.translate" % self.j_ik_rp_root, "%s.color1" % blend_pos_ik_root)
        cmds.connectAttr("%s.output" % blend_pos_ik_root, "%s.translate" % self.j_ik_orig_root)
        cmds.connectAttr("%s.polevector" % self.cont_IK_foot, "%s.blender" % blend_pos_ik_root)

        blend_ore_ik_knee = cmds.createNode("blendColors", name="blendORE_IK_Low_%s" % self.suffix)
        cmds.connectAttr("%s.rotate" % self.j_ik_sc_knee, "%s.color2" % blend_ore_ik_knee)
        cmds.connectAttr("%s.rotate" % self.j_ik_rp_knee, "%s.color1" % blend_ore_ik_knee)
        # Weird bug with skinned character / use seperate connections
        # if there is no skincluster, it works ok, but adding a skin cluster misses 2 out of 3 rotation axis
        # Therefore make SEPERATE CONNECTIONS
        cmds.connectAttr("%s.outputR" % blend_ore_ik_knee, "%s.rotateX" % self.j_ik_orig_knee)
        cmds.connectAttr("%s.outputG" % blend_ore_ik_knee, "%s.rotateY" % self.j_ik_orig_knee)
        cmds.connectAttr("%s.outputB" % blend_ore_ik_knee, "%s.rotateZ" % self.j_ik_orig_knee)
        cmds.connectAttr("%s.polevector" % self.cont_IK_foot, "%s.blender" % blend_ore_ik_knee)

        blend_pos_ik_knee = cmds.createNode("blendColors", name="blendPOS_IK_Low_%s" % self.suffix)
        cmds.connectAttr("%s.translate" % self.j_ik_sc_knee, "%s.color2" % blend_pos_ik_knee)
        cmds.connectAttr("%s.translate" % self.j_ik_rp_knee, "%s.color1" % blend_pos_ik_knee)
        cmds.connectAttr("%s.output" % blend_pos_ik_knee, "%s.translate" % self.j_ik_orig_knee)
        cmds.connectAttr("%s.polevector" % self.cont_IK_foot, "%s.blender" % blend_pos_ik_knee)

        blend_ore_ik_end = cmds.createNode("blendColors", name="blendORE_IK_LowEnd_%s" % self.suffix)
        cmds.connectAttr("%s.rotate" % self.j_ik_sc_end, "%s.color2" % blend_ore_ik_end)
        cmds.connectAttr("%s.rotate" % self.j_ik_rp_end, "%s.color1" % blend_ore_ik_end)
        # Weird bug with skinned character / use seperate connections
        # if there is no skincluster, it works ok, but adding a skin cluster misses 2 out of 3 rotation axis
        # Therefore make SEPERATE CONNECTIONS
        cmds.connectAttr("%s.outputR" % blend_ore_ik_end, "%s.rotateX" % self.j_ik_orig_end)
        cmds.connectAttr("%s.outputG" % blend_ore_ik_end, "%s.rotateY" % self.j_ik_orig_end)
        cmds.connectAttr("%s.outputB" % blend_ore_ik_end, "%s.rotateZ" % self.j_ik_orig_end)
        cmds.connectAttr("%s.polevector" % self.cont_IK_foot, "%s.blender" % blend_ore_ik_end)

        blend_pos_ik_end = cmds.createNode("blendColors", name="blendPOS_IK_LowEnd_%s" % self.suffix)
        cmds.connectAttr("%s.translate" % self.j_ik_sc_end, "%s.color2" % blend_pos_ik_end)
        cmds.connectAttr("%s.translate" % self.j_ik_rp_end, "%s.color1" % blend_pos_ik_end)
        cmds.connectAttr("%s.output" % blend_pos_ik_end, "%s.translate" % self.j_ik_orig_end)
        cmds.connectAttr("%s.polevector" % self.cont_IK_foot, "%s.blender" % blend_pos_ik_end)

        pole_vector_rvs = cmds.createNode("reverse", name="poleVector_Rvs_%s" % self.suffix)
        cmds.connectAttr("%s.polevector" % self.cont_IK_foot, "%s.inputX" % pole_vector_rvs)
        cmds.connectAttr("%s.polevector" % self.cont_IK_foot, "%s.v" % self.cont_Pole)

        cmds.parent(self.j_ik_orig_root, self.master_root)
        cmds.parent(self.j_ik_sc_root, self.master_root)
        cmds.parent(self.j_ik_rp_root, self.master_root)

        pacon_locator_hip = cmds.spaceLocator(name="paConLoc_%s" % self.suffix)[0]
        extra.alignTo(pacon_locator_hip, self.jDef_legRoot, position=True, rotation=True)
        #
        j_def_pa_con = cmds.parentConstraint(self.cont_thigh, pacon_locator_hip, mo=False)
        #
        cmds.parent(leg_start, self.scaleGrp)
        cmds.parent(leg_end, self.scaleGrp)
        cmds.parent(self.ik_parent_grp, self.scaleGrp)
        cmds.parent(self.start_lock_ore, self.scaleGrp)
        cmds.parent(self.end_lock_ore, self.scaleGrp)

        cmds.parent(pacon_locator_hip, self.scaleGrp)
        cmds.parent(self.jDef_legRoot, pacon_locator_hip)
        #
        cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % leg_start)
        cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % leg_end)
        cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % self.ik_parent_grp)
        cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % extra.getShapes(pacon_locator_hip)[0])

        cmds.delete(foot_plane)

    def createFKsetup(self):
        cmds.connectAttr("%s.scaleX" % self.cont_fk_up_leg, "%s.scaleX" % self.jfk_root)
        cmds.connectAttr("%s.scaleX" % self.cont_fk_low_leg, "%s.scaleX" % self.jfk_knee)
        cmds.connectAttr("%s.scaleX" % self.cont_fk_foot, "%s.scaleX" % self.jfk_foot)
        cmds.connectAttr("%s.scaleX" % self.cont_fk_ball, "%s.scaleX" % self.jfk_ball)

        cmds.orientConstraint(self.cont_fk_up_leg, self.jfk_root, mo=False)
        cmds.pointConstraint(self.start_lock, self.jfk_root, mo=False)

        cmds.orientConstraint(self.cont_fk_low_leg, self.jfk_knee, mo=False)
        cmds.orientConstraint(self.cont_fk_foot, self.jfk_foot, mo=False)

        cmds.parentConstraint(self.cont_fk_ball, self.jfk_ball, mo=False)

        # TODO : TAKE A LOOK TO THE OFFSET SOLUTION
        cmds.parentConstraint(self.cont_thigh, self.cont_fk_up_leg_off, sr=("x", "y", "z"), mo=True)
        cmds.parentConstraint(self.cont_fk_up_leg, self.cont_fk_low_leg_off, mo=True)
        cmds.parentConstraint(self.cont_fk_low_leg, self.cont_fk_foot_off, mo=True)
        cmds.parentConstraint(self.cont_fk_foot, self.cont_fk_ball_off, mo=True)

    def ikfkSwitching(self):
        cmds.connectAttr("%s.outputX" % self.fk_ik_rvs, "%s.visibility" % self.cont_fk_up_leg_ore)
        cmds.connectAttr("%s.outputX" % self.fk_ik_rvs, "%s.visibility" % self.cont_fk_low_leg_ore)
        cmds.connectAttr("%s.outputX" % self.fk_ik_rvs, "%s.visibility" % self.cont_fk_foot_ore)
        cmds.connectAttr("%s.outputX" % self.fk_ik_rvs, "%s.visibility" % self.cont_fk_ball_ore)
        cmds.connectAttr("%s.fk_ik" % self.cont_fk_ik, "%s.visibility" % self.cont_IK_foot)
        cmds.connectAttr("%s.fk_ik" % self.cont_fk_ik, "%s.visibility" % self.cont_pole_vis)


        mid_lock_pa_con_weight = cmds.parentConstraint(self.j_ik_orig_root, self.jfk_root, self.cont_mid_lock_pos, mo=False)[0]
        cmds.connectAttr("%s.fk_ik" % self.cont_fk_ik, "%s.%sW0" % (mid_lock_pa_con_weight, self.j_ik_orig_root))
        cmds.connectAttr("%s.outputX" % self.fk_ik_rvs, "%s.%sW1" % (mid_lock_pa_con_weight, self.jfk_root))

        cmds.connectAttr("%s.interpType" % self.cont_fk_ik, "%s.interpType" % mid_lock_pa_con_weight)

        mid_lock_po_con_weight = cmds.pointConstraint(self.j_ik_orig_knee, self.jfk_knee, self.cont_mid_lock_ave, mo=False)[0]
        cmds.connectAttr("%s.fk_ik" % self.cont_fk_ik, "%s.%sW0" % (mid_lock_po_con_weight, self.j_ik_orig_knee))
        cmds.connectAttr("%s.outputX" % self.fk_ik_rvs, "%s.%sW1" % (mid_lock_po_con_weight, self.jfk_knee))

        mid_lock_x_bln = cmds.createNode("multiplyDivide", name="midLock_xBln%s" % self.suffix)

        mid_lock_rot_xsw = cmds.createNode("blendTwoAttr", name="midLock_rotXsw%s" % self.suffix)
        cmds.connectAttr("%s.rotateZ" % self.j_ik_orig_knee, "%s.input[0]" % mid_lock_rot_xsw)
        cmds.connectAttr("%s.rotateZ" % self.jfk_knee, "%s.input[1]" % mid_lock_rot_xsw)
        cmds.connectAttr("%s.outputX" % self.fk_ik_rvs, "%s.attributesBlender" % mid_lock_rot_xsw)
        cmds.connectAttr("%s.output" % mid_lock_rot_xsw, "%s.input1Z" % mid_lock_x_bln)

        cmds.setAttr("%s.input2Z" % mid_lock_x_bln, 0.5)

        cmds.connectAttr("%s.outputZ" % mid_lock_x_bln, "%s.rotateZ" % self.cont_mid_lock_ave)

        end_lock_weight = cmds.pointConstraint(self.j_ik_orig_end, self.jfk_foot, self.end_lock_pos, mo=False)[0]
        cmds.connectAttr("%s.fk_ik" % self.cont_fk_ik, "%s.%sW0" % (end_lock_weight, self.j_ik_orig_end))
        cmds.connectAttr("%s.outputX" % self.fk_ik_rvs, "%s.%sW1" % (end_lock_weight, self.jfk_foot))

        # the following offset parent constraint is not important and wont cause any trouble since
        # it only affects the FK/IK icon
        cmds.parentConstraint(self.end_lock, self.cont_fk_ik_pos, mo=True)

        # ######
        end_lock_rot = cmds.parentConstraint(self.ik_parent_grp, self.jfk_foot, self.end_lock, st=("x", "y", "z"), mo=True)[0]

        cmds.connectAttr("%s.fk_ik" % self.cont_fk_ik,"%s.%sW0" % (end_lock_rot, self.ik_parent_grp))
        cmds.connectAttr("%s.outputX" % self.fk_ik_rvs, "%s.%sW1" % (end_lock_rot, self.jfk_foot))
        cmds.connectAttr("%s.interpType" % self.cont_fk_ik, "%s.interpType" % end_lock_rot)

        foot_pa_con = cmds.parentConstraint(self.j_ik_foot, self.jfk_foot, self.j_def_foot, mo=False)[0]
        ball_pa_con = cmds.parentConstraint(self.j_ik_ball, self.jfk_ball, self.j_def_ball, mo=False)[0]
        toe_pa_con = cmds.parentConstraint(self.j_ik_toe, self.jfk_toe, self.j_toe, mo=False)[0]

        cmds.connectAttr("%s.fk_ik" % self.cont_fk_ik, "%s.%sW0" % (foot_pa_con, self.j_ik_foot))
        cmds.connectAttr("%s.outputX" % self.fk_ik_rvs, "%s.%sW1" % (foot_pa_con, self.jfk_foot))
        cmds.connectAttr("%s.fk_ik" % self.cont_fk_ik, "%s." % "%s.%sW0" % (ball_pa_con, self.j_ik_ball))
        cmds.connectAttr("%s.outputX" % self.fk_ik_rvs, "%s." % "%s.%sW1" % (ball_pa_con, self.jfk_ball))
        cmds.connectAttr("%s.fk_ik" % self.cont_fk_ik, "%s." % "%s.%sW0" % (toe_pa_con, self.j_ik_toe))
        cmds.connectAttr("%s.outputX" % self.fk_ik_rvs, "%s." % "%s.%sW1" % (toe_pa_con, self.jfk_toe))
        cmds.connectAttr("%s.interpType" % self.cont_fk_ik, "%s.interpType" % foot_pa_con)
        cmds.connectAttr("%s.interpType" %  self.cont_fk_ik, "%s.interpType" % ball_pa_con)
        cmds.connectAttr("%s.interpType" % self.cont_fk_ik, "%s.interpType" % toe_pa_con)

    def createDefJoints(self):
        # UPPERLEG RIBBON

        ribbon_upper_leg = rc.PowerRibbon()
        ribbon_upper_leg.createPowerRibbon(self.j_def_hip, self.j_def_midLeg, "up_%s" % self.suffix,  side=self.side, connectStartAim=False, upVector=self.mirror_axis)

        ribbon_start_pa_con_upper_leg_start = cmds.parentConstraint(self.start_lock, ribbon_upper_leg.startConnection, mo=False)[0]

        cmds.parentConstraint(self.mid_lock, ribbon_upper_leg.endConnection, mo=False)

        # connect the knee scaling
        cmds.connectAttr("%s.scale" % self.cont_mid_lock, "%s.scale" % ribbon_upper_leg.endConnection)
        cmds.connectAttr("%s.scale" % self.cont_mid_lock, "%s.scale" % self.j_def_midLeg)

        cmds.scaleConstraint(self.scaleGrp, ribbon_upper_leg.scaleGrp)

        ribbon_start_ori_con = cmds.parentConstraint(self.j_ik_orig_root, self.jfk_root, ribbon_upper_leg.startAim, mo=False, skipTranslate=["x","y","z"] )[0]
        ribbon_start_ori_con2 = cmds.parentConstraint(self.j_def_hip, ribbon_upper_leg.startAim, mo=False, skipTranslate=["x","y","z"] )[0]

        cmds.connectAttr("%s.fk_ik" % self.cont_fk_ik, "%s.%sW0" %(ribbon_start_ori_con, self.j_ik_orig_root))
        cmds.connectAttr("%s.outputX" % self.fk_ik_rvs, "%s.%sW1" %(ribbon_start_ori_con, self.jfk_root))

        pairBlendNode = cmds.listConnections(ribbon_start_ori_con, d=True, t="pairBlend")[0]
        # disconnect the existing weight connection
        # re-connect to the custom attribute
        cmds.connectAttr("%s.alignHip" % self.cont_fk_ik, "%s.w" % pairBlendNode, force=True)

        # Rotate the shoulder connection bone 180 degrees for Right Alignment
        if self.side == "R":
            rightRBN_startupORE = cmds.listRelatives(ribbon_upper_leg.startAim, children=True, type="transform")[0]
            cmds.setAttr("%s.ry" % rightRBN_startupORE, 180)

        # AUTO AND MANUAL TWIST

        # auto
        auto_twist_thigh = cmds.createNode("multiplyDivide", name="autoTwistThigh_%s" % self.suffix)
        cmds.connectAttr("%s.upLegAutoTwist" % self.cont_fk_ik, "%s.input2X" % auto_twist_thigh)
        cmds.connectAttr("%s.constraintRotate" % ribbon_start_pa_con_upper_leg_start, "%s.input1" % auto_twist_thigh)

        # !!! The parent constrain override should be disconnected like this
        cmds.disconnectAttr(
            "%s.constraintRotateX" % ribbon_start_pa_con_upper_leg_start,
            "%s.rotateX" % ribbon_upper_leg.startConnection
        )

        # manual
        add_manual_twist_thigh = cmds.createNode("plusMinusAverage", name=("AddManualTwist_UpperLeg_%s" % self.suffix))
        cmds.connectAttr("%s.output" % auto_twist_thigh, "%s.input3D[0]" % add_manual_twist_thigh)
        cmds.connectAttr("%s.upLegManualTwist" % self.cont_fk_ik, "%s.input3D[1].input3Dx" % add_manual_twist_thigh)

        # connect to the joint
        cmds.connectAttr("%s.output3D" % add_manual_twist_thigh, "%s.rotate" % ribbon_upper_leg.startConnection)

        # connect allowScaling
        cmds.connectAttr("%s.allowScaling" % self.cont_fk_ik, "%s.scaleSwitch" % ribbon_upper_leg.startConnection)

        # LOWERLEG RIBBON

        ribbon_lower_leg = rc.PowerRibbon()
        ribbon_lower_leg.createPowerRibbon(self.j_def_midLeg, self.j_def_foot, "low_%s" % self.suffix, side=self.side,  orientation=90, upVector=self.look_axis)

        cmds.parentConstraint(self.mid_lock, ribbon_lower_leg.startConnection, mo=False)
        ribbon_start_pa_con_lower_leg_end = cmds.parentConstraint(self.end_lock, ribbon_lower_leg.endConnection, mo=False)[0]

        # connect the midLeg scaling
        cmds.connectAttr("%s.scale" % self.cont_mid_lock, "%s.scale" % ribbon_lower_leg.startConnection)

        cmds.scaleConstraint(self.scaleGrp, ribbon_lower_leg.scaleGrp)


        # AUTO AND MANUAL TWIST

        # auto
        auto_twist_ankle = cmds.createNode("multiplyDivide", name="autoTwistAnkle_%s" % self.suffix)
        cmds.connectAttr("%s.footAutoTwist" % self.cont_fk_ik, "%s.input2X" % auto_twist_ankle)
        cmds.connectAttr("%s.constraintRotate" % ribbon_start_pa_con_lower_leg_end, "%s.input1" % auto_twist_ankle)

        # !!! The parent constrain override should be disconnected like this
        cmds.disconnectAttr("%s.constraintRotateX" % ribbon_start_pa_con_lower_leg_end, "%s.rotateX" % ribbon_lower_leg.endConnection)

        # manual
        add_manual_twist_ankle = cmds.createNode("plusMinusAverage", name=("AddManualTwist_LowerLeg_%s" % self.suffix))
        cmds.connectAttr("%s.output" % auto_twist_ankle, "%s.input3D[0]" % add_manual_twist_ankle)
        cmds.connectAttr("%s.footManualTwist" % self.cont_fk_ik, "%s.input3D[1].input3Dx" % add_manual_twist_ankle)

        # connect to the joint
        cmds.connectAttr("%s.output3D" % add_manual_twist_ankle, "%s.rotate" % ribbon_lower_leg.endConnection)

        # connect allowScaling
        cmds.connectAttr("%s.allowScaling" % self.cont_fk_ik, "%s.scaleSwitch" % ribbon_lower_leg.startConnection)

        # Volume Preservation Stuff
        vpExtraInput = cmds.createNode("multiplyDivide", name="vpExtraInput_%s" % self.suffix)
        cmds.setAttr("%s.operation" % vpExtraInput, 1)

        vpMidAverage = cmds.createNode("plusMinusAverage", name="vpMidAverage_%s" % self.suffix)
        cmds.setAttr("%s.operation" % vpMidAverage, 3)

        vpPowerMid = cmds.createNode("multiplyDivide", name="vpPowerMid_%s" % self.suffix)
        cmds.setAttr("%s.operation" % vpPowerMid, 3)
        vpInitLength = cmds.createNode("multiplyDivide", name="vpInitLength_%s" % self.suffix)
        cmds.setAttr("%s.operation" % vpInitLength, 2)

        vpPowerUpperLeg = cmds.createNode("multiplyDivide", name="vpPowerUpperLeg_%s" % self.suffix)
        cmds.setAttr("%s.operation" % vpPowerUpperLeg, 3)

        vpPowerLowerLeg = cmds.createNode("multiplyDivide", name="vpPowerLowerLeg_%s" % self.suffix)
        cmds.setAttr("%s.operation" % vpPowerLowerLeg, 3)

        vpUpperLowerReduce = cmds.createNode("multDoubleLinear", name="vpUpperLowerReduce_%s" % self.suffix)
        cmds.setAttr("%s.input2" % vpUpperLowerReduce, 0.5)

        # vp knee branch
        cmds.connectAttr("%s.output" % vpExtraInput, "%s.scale" % ribbon_lower_leg.startConnection, force=True)
        cmds.connectAttr("%s.output" % vpExtraInput, "%s.scale" % ribbon_upper_leg.endConnection, force=True)
        cmds.connectAttr("%s.output" % vpExtraInput, "%s.scale" % self.j_def_midLeg, force=True)
        cmds.connectAttr("%s.scale" % self.cont_mid_lock, "%s.input1" % vpExtraInput, force=True)
        cmds.connectAttr("%s.output1D" % vpMidAverage, "%s.input2X" % vpExtraInput, force=True)
        cmds.connectAttr("%s.output1D" % vpMidAverage, "%s.input2Y" % vpExtraInput, force=True)
        cmds.connectAttr("%s.output1D" % vpMidAverage, "%s.input2Z" % vpExtraInput, force=True)
        cmds.connectAttr("%s.outputX" % vpPowerMid, "%s.input1D[0]" % vpMidAverage, force=True)
        cmds.connectAttr("%s.outputY" % vpPowerMid, "%s.input1D[1]" % vpMidAverage, force=True)
        cmds.connectAttr("%s.outputX" % vpInitLength, "%s.input1X" % vpPowerMid, force=True)
        cmds.connectAttr("%s.outputY" % vpInitLength, "%s.input1Y" % vpPowerMid, force=True)
        cmds.connectAttr("%s.volume" % self.cont_IK_foot, "%s.input2X" % vpPowerMid, force=True)
        cmds.connectAttr("%s.volume" % self.cont_IK_foot, "%s.input2Y" % vpPowerMid, force=True)
        cmds.connectAttr("%s.outputX" % self.initial_length_multip_sc, "%s.input1X" % vpInitLength, force=True)
        cmds.connectAttr("%s.outputY" % self.initial_length_multip_sc, "%s.input1Y" % vpInitLength, force=True)
        cmds.connectAttr("%s.color1R" % self.stretchiness_sc, "%s.input2X" % vpInitLength, force=True)
        cmds.connectAttr("%s.color1G" % self.stretchiness_sc, "%s.input2Y" % vpInitLength, force=True)


        # vp upper branch
        mid_off_up = extra.getParent(ribbon_upper_leg.middleCont[0])
        cmds.connectAttr("%s.outputX" % vpPowerUpperLeg, "%s.scaleX" % mid_off_up)
        cmds.connectAttr("%s.outputX" % vpPowerUpperLeg, "%s.scaleY" % mid_off_up)
        cmds.connectAttr("%s.outputX" % vpPowerUpperLeg, "%s.scaleZ" % mid_off_up)
        cmds.connectAttr("%s.outputX" % vpInitLength, "%s.input1X" % vpPowerUpperLeg)
        cmds.connectAttr("%s.output" % vpUpperLowerReduce, "%s.input2X" % vpPowerUpperLeg)

        # vp lower branch
        mid_off_low = extra.getParent(ribbon_lower_leg.middleCont[0])
        cmds.connectAttr("%s.outputX" % vpPowerLowerLeg, "%s.scaleX" % mid_off_low)
        cmds.connectAttr("%s.outputX" % vpPowerLowerLeg, "%s.scaleY" % mid_off_low)
        cmds.connectAttr("%s.outputX" % vpPowerLowerLeg, "%s.scaleZ" % mid_off_low)
        cmds.connectAttr("%s.outputX" % vpInitLength, "%s.input1X" % vpPowerLowerLeg)
        cmds.connectAttr("%s.output" % vpUpperLowerReduce, "%s.input2X" % vpPowerLowerLeg)
        cmds.connectAttr("%s.volume" % self.cont_IK_foot, "%s.input1" % vpUpperLowerReduce)

        cmds.parent(ribbon_upper_leg.scaleGrp, self.nonScaleGrp)
        cmds.parent(ribbon_upper_leg.nonScaleGrp, self.nonScaleGrp)
        cmds.parent(ribbon_lower_leg.scaleGrp, self.nonScaleGrp)
        cmds.parent(ribbon_lower_leg.nonScaleGrp, self.nonScaleGrp)

        cmds.connectAttr("%s.tweakControls" %  self.cont_fk_ik, "%s.v" %  self.cont_mid_lock)
        tweakConts = ribbon_upper_leg.middleCont + ribbon_lower_leg.middleCont
        map(lambda x: cmds.connectAttr("%s.tweakControls" % self.cont_fk_ik, "%s.v" % x), tweakConts)

        cmds.connectAttr("%s.contVis" % self.scaleGrp, "%s.v" % ribbon_upper_leg.scaleGrp)
        cmds.connectAttr("%s.contVis" % self.scaleGrp, "%s.v" % ribbon_lower_leg.scaleGrp)

        self.deformerJoints += ribbon_lower_leg.deformerJoints + ribbon_upper_leg.deformerJoints
        map(lambda x: cmds.connectAttr("%s.jointVis" % self.scaleGrp, "%s.v" % x), self.deformerJoints)
        map(lambda x: cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % x), ribbon_lower_leg.toHide)
        map(lambda x: cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % x), ribbon_upper_leg.toHide)
        extra.colorize(ribbon_upper_leg.middleCont, self.colorCodes[1])
        extra.colorize(ribbon_lower_leg.middleCont, self.colorCodes[1])

    def createAngleExtractors(self):
        # IK Angle Extractor
        angleExt_Root_IK = cmds.spaceLocator(name="angleExt_Root_IK_%s" % self.suffix)[0]
        angleExt_Fixed_IK = cmds.spaceLocator(name="angleExt_Fixed_IK_%s" % self.suffix)[0]
        angleExt_Float_IK = cmds.spaceLocator(name="angleExt_Float_IK_%s" % self.suffix)[0]
        cmds.parent(angleExt_Fixed_IK, angleExt_Float_IK, angleExt_Root_IK)

        cmds.parentConstraint(self.limbPlug, angleExt_Root_IK, mo=False)
        cmds.parentConstraint(self.cont_IK_foot, angleExt_Fixed_IK, mo=False)
        extra.alignToAlter(angleExt_Float_IK, self.jDef_legRoot, 2)
        cmds.move(0,self.sideMult*5, 0, angleExt_Float_IK, objectSpace=True)

        angleNodeIK = cmds.createNode("angleBetween", name="angleBetweenIK_%s" % self.suffix)
        angleRemapIK = cmds.createNode("remapValue", name="angleRemapIK_%s" % self.suffix)
        angleMultIK = cmds.createNode("multDoubleLinear", name="angleMultIK_%s" % self.suffix)

        cmds.connectAttr("%s.translate" % angleExt_Fixed_IK, "%s.vector1" % angleNodeIK)
        cmds.connectAttr("%s.translate" % angleExt_Float_IK, "%s.vector2" % angleNodeIK)
        cmds.connectAttr("%s.angle" % angleNodeIK, "%s.inputValue" % angleRemapIK)

        cmds.setAttr("%s.inputMin" % angleRemapIK, cmds.getAttr("%s.angle" % angleNodeIK))
        cmds.setAttr("%s.inputMax" % angleRemapIK, 0)
        cmds.setAttr("%s.outputMin" % angleRemapIK, 0)
        cmds.setAttr("%s.outputMax" % angleRemapIK, cmds.getAttr("%s.angle" % angleNodeIK))

        cmds.connectAttr("%s.outValue" % angleRemapIK, "%s.input1" % angleMultIK)

        cmds.setAttr("%s.input2" % angleMultIK, 0.5)

        # FK Angle Extractor
        angleRemapFK = cmds.createNode("remapValue", name="angleRemapFK_%s" % self.suffix)
        angleMultFK = cmds.createNode("multDoubleLinear", name="angleMultFK_%s" % self.suffix)

        cmds.connectAttr("%s.rotateZ" % self.cont_fk_up_leg, "%s.inputValue" % angleRemapFK)

        cmds.setAttr("%s.inputMin" % angleRemapFK, 0)
        cmds.setAttr("%s.inputMax" % angleRemapFK, 90)
        cmds.setAttr("%s.outputMin" % angleRemapFK, 0)
        cmds.setAttr("%s.outputMax" % angleRemapFK, 90)

        cmds.connectAttr("%s.outValue" % angleRemapFK, "%s.input1" % angleMultFK)

        cmds.setAttr("%s.input2" % angleMultFK, 0.5)


        # create blend attribute and global Mult
        angleExt_blend = cmds.createNode("blendTwoAttr", name="angleExt_blend_%s" % self.suffix)
        angleGlobal = cmds.createNode("multDoubleLinear", name="angleGlobal_mult_%s" % self.suffix)

        cmds.connectAttr("%s.fk_ik" % self.cont_fk_ik, "%s.attributesBlender" % angleExt_blend)
        cmds.connectAttr("%s.output" % angleMultFK, "%s.input[0]" % angleExt_blend)
        cmds.connectAttr("%s.output" % angleMultIK, "%s.input[1]" % angleExt_blend)
        cmds.connectAttr("%s.output" % angleExt_blend, "%s.input1" % angleGlobal)
        cmds.connectAttr("%s.autoHip" % self.cont_fk_ik, "%s.input2" % angleGlobal)
        cmds.connectAttr("%s.output" % angleGlobal, "%s.rotateZ" % self.cont_thigh_auto)

        cmds.parent(angleExt_Root_IK, self.scaleGrp)
        cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % angleExt_Root_IK)
        return


    def roundUp(self):
        cmds.parentConstraint(self.limbPlug, self.scaleGrp, mo=False)
        cmds.setAttr("%s.rigVis" % self.scaleGrp, 0)

        extra.lockAndHide(self.cont_IK_foot, ["v"])
        extra.lockAndHide(self.cont_Pole, ["rx", "ry", "rz", "sx", "sy", "sz", "v"])
        extra.lockAndHide(self.cont_mid_lock, ["v"])
        extra.lockAndHide(self.cont_fk_ik, ["sx", "sy", "sz", "v"])
        extra.lockAndHide(self.cont_fk_foot, ["tx", "ty", "tz", "v"])
        extra.lockAndHide(self.cont_fk_low_leg, ["tx", "ty", "tz", "sy", "sz", "v"])
        extra.lockAndHide(self.cont_fk_up_leg, ["tx", "ty", "tz", "sy", "sz", "v"])
        extra.lockAndHide(self.cont_thigh, ["sx", "sy", "sz", "v"])

        self.scaleConstraints = [self.scaleGrp, self.cont_IK_OFF]
        self.anchors = [(self.cont_IK_foot, "parent", 1, None), (self.cont_Pole, "parent", 1, None)]

    def createLimb(self):
        self.createGrp()
        self.createJoints()
        self.createControllers()
        self.createRoots()
        self.createIKsetup()
        self.createFKsetup()
        self.ikfkSwitching()
        self.createDefJoints()
        self.createAngleExtractors()
        self.roundUp()
