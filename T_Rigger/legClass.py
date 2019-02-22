import pymel.core as pm
import extraProcedures as extra
# import ribbonClass as rc
import powerRibbon as rc
import contIcons as icon
import pymel.core.datatypes as dt

reload(extra)
reload(rc)
reload(icon)

class Leg(object):
    def __init__(self, leginits, suffix="", side="L"):

        if len(leginits) < 9:
            pm.error("Some or all Leg Init Bones are missing (or Renamed)")
            return

        if not type(leginits) == dict and not type(leginits) == list:
            pm.error("Init joints must be list or dictionary")
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

        self.leg_root_pos = self.leg_root_ref.getTranslation(space="world")
        self.hip_pos = self.hip_ref.getTranslation(space="world")
        self.knee_pos = self.knee_ref.getTranslation(space="world")
        self.foot_pos = self.foot_ref.getTranslation(space="world")
        self.ball_pos = self.ball_ref.getTranslation(space="world")
        self.toe_pv_pos = self.toe_pv_ref.getTranslation(space="world")

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

        self.originalSuffix = suffix
        self.suffix = (extra.uniqueName("limbGrp_%s" % suffix)).replace("limbGrp_", "")

        self.sockets = []
        self.scaleGrp = None
        self.nonScaleGrp = None
        self.cont_IK_foot = None
        self.cont_IK_OFF = None
        self.cont_Pole = None
        self.limbPlug = None
        self.scaleConstraints = []
        self.anchors = []
        self.anchorLocations = []
        self.jDef_legRoot = None
        self.deformerJoints = []
        self.colorCodes = [6, 18]

    def createGrp(self):
        self.limbGrp = pm.group(name="limbGrp_%s" % self.suffix, em=True)
        self.scaleGrp = pm.group(name="scaleGrp_%s" % self.suffix, em=True)
        extra.alignTo(self.scaleGrp, self.leg_root_ref, 0)
        self.nonScaleGrp = pm.group(name="NonScaleGrp_%s" % self.suffix, em=True)

        pm.addAttr(self.scaleGrp, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True)
        pm.addAttr(self.scaleGrp, at="bool", ln="Joints_Visibility", sn="jointVis", defaultValue=True)
        pm.addAttr(self.scaleGrp, at="bool", ln="Rig_Visibility", sn="rigVis", defaultValue=False)
        # make the created attributes visible in the channelbox
        pm.setAttr(self.scaleGrp.contVis, cb=True)
        pm.setAttr(self.scaleGrp.jointVis, cb=True)
        pm.setAttr(self.scaleGrp.rigVis, cb=True)

        pm.parent(self.scaleGrp, self.limbGrp)
        pm.parent(self.nonScaleGrp, self.limbGrp)

    def createJoints(self):
        # Create Limb Plug
        pm.select(d=True)
        self.limbPlug = pm.joint(name="limbPlug_%s" % self.suffix, p=self.leg_root_pos, radius=3)

        self.jDef_legRoot = pm.joint(name="jDef_legRoot_%s" % self.suffix, p=self.leg_root_pos, radius=1.5)
        self.sockets.append(self.jDef_legRoot)
        self.j_def_hip = pm.joint(name="jDef_hip_%s" % self.suffix, p=self.hip_pos, radius=1.5)
        self.sockets.append(self.j_def_hip)

        extra.orientJoints([self.jDef_legRoot, self.j_def_hip], localMoveAxis=(dt.Vector(self.up_axis)),
                           mirrorAxis=(self.sideMult, 0.0, 0.0), upAxis=self.sideMult * (dt.Vector(self.up_axis)))

        pm.select(d=True)
        self.j_def_midLeg = pm.joint(name="jDef_knee_%s" % self.suffix, p=self.knee_pos, radius=1.5)
        self.sockets.append(self.j_def_midLeg)

        pm.select(d=True)
        self.j_def_foot = pm.joint(name="jDef_Foot_%s" % self.suffix, p=self.foot_pos, radius=1.0)
        self.sockets.append(self.j_def_foot)
        self.j_def_ball = pm.joint(name="jDef_Ball_%s" % self.suffix, p=self.ball_pos, radius=1.0)
        self.sockets.append(self.j_def_ball)
        self.j_toe = pm.joint(name="jDef_Toe_%s" % self.suffix, p=self.toe_pv_pos, radius=1.0)  # POSSIBLE PROBLEM
        self.sockets.append(self.j_toe)

        pm.select(d=True)
        self.j_socket_ball = pm.joint(name="jBallSocket_%s" % self.suffix, p=self.ball_pos, radius=3)
        self.sockets.append(self.j_socket_ball)
        # IK Joints
        # Follow IK Chain
        pm.select(d=True)
        self.j_ik_orig_root = pm.joint(name="jIK_orig_Root_%s" % self.suffix, p=self.hip_pos, radius=1.5)
        self.j_ik_orig_knee = pm.joint(name="jIK_orig_Knee_%s" % self.suffix, p=self.knee_pos, radius=1.5)
        self.j_ik_orig_end = pm.joint(name="jIK_orig_End_%s" % self.suffix, p=self.foot_pos, radius=1.5)

        # Single Chain IK
        pm.select(d=True)
        self.j_ik_sc_root = pm.joint(name="jIK_SC_Root_%s" % self.suffix, p=self.hip_pos, radius=1)
        self.j_ik_sc_knee = pm.joint(name="jIK_SC_Knee_%s" % self.suffix, p=self.knee_pos, radius=1)
        self.j_ik_sc_end = pm.joint(name="jIK_SC_End_%s" % self.suffix, p=self.foot_pos, radius=1)

        # Rotate Plane IK
        pm.select(d=True)
        self.j_ik_rp_root = pm.joint(name="jIK_RP_Root_%s" % self.suffix, p=self.hip_pos, radius=0.7)
        self.j_ik_rp_knee = pm.joint(name="jIK_RP_Knee_%s" % self.suffix, p=self.knee_pos, radius=0.7)
        self.j_ik_rp_end = pm.joint(name="jIK_RP_End_%s" % self.suffix, p=self.foot_pos, radius=0.7)

        pm.select(d=True)
        self.j_ik_foot = pm.joint(name="jIK_Foot_%s" % self.suffix, p=self.foot_pos, radius=1.0)
        self.j_ik_ball = pm.joint(name="jIK_Ball_%s" % self.suffix, p=self.ball_pos, radius=1.0)
        self.j_ik_toe = pm.joint(name="jIK_Toe_%s" % self.suffix, p=self.toe_pv_pos, radius=1.0)

        pm.select(d=True)

        # orientations
        extra.orientJoints([self.j_ik_orig_root, self.j_ik_orig_knee, self.j_ik_orig_end],
                           localMoveAxis=(dt.Vector(self.up_axis)),
                           mirrorAxis=(self.sideMult, 0.0, 0.0), upAxis=self.sideMult * (dt.Vector(self.up_axis)))

        extra.orientJoints([self.j_ik_sc_root, self.j_ik_sc_knee, self.j_ik_sc_end],
                           localMoveAxis=(dt.Vector(self.up_axis)),
                           mirrorAxis=(self.sideMult, 0.0, 0.0), upAxis=self.sideMult * (dt.Vector(self.up_axis)))

        extra.orientJoints([self.j_ik_rp_root, self.j_ik_rp_knee, self.j_ik_rp_end],
                           localMoveAxis=(dt.Vector(self.up_axis)),
                           mirrorAxis=(self.sideMult, 0.0, 0.0), upAxis=self.sideMult * (dt.Vector(self.up_axis)))

        extra.orientJoints([self.j_ik_foot, self.j_ik_ball, self.j_ik_toe],
                           localMoveAxis=(dt.Vector(self.up_axis)),
                           mirrorAxis=(self.sideMult, 0.0, 0.0), upAxis=self.sideMult * (dt.Vector(self.up_axis)))

        # FK Joints
        pm.select(d=True)
        self.jfk_root = pm.joint(name="jFK_UpLeg_%s" % self.suffix, p=self.hip_pos, radius=1.0)
        self.jfk_knee = pm.joint(name="jFK_Knee_%s" % self.suffix, p=self.knee_pos, radius=1.0)
        self.jfk_foot = pm.joint(name="jFK_Foot_%s" % self.suffix, p=self.foot_pos, radius=1.0)
        self.jfk_ball = pm.joint(name="jFK_Ball_%s" % self.suffix, p=self.ball_pos, radius=1.0)
        self.jfk_toe = pm.joint(name="jFK_Toe_%s" % self.suffix, p=self.toe_pv_pos, radius=1.0)

        extra.orientJoints([self.jfk_root, self.jfk_knee, self.jfk_foot, self.jfk_ball, self.jfk_toe], localMoveAxis=(dt.Vector(self.up_axis)),
                           mirrorAxis=(self.sideMult, 0.0, 0.0), upAxis=self.sideMult * (dt.Vector(self.up_axis)))

        # re-orient single joints
        extra.alignToAlter(self.j_def_hip, self.jfk_root, mode=2)
        pm.makeIdentity(self.j_def_hip, a=True)
        extra.alignToAlter(self.j_def_midLeg, self.jfk_knee, mode=2)
        pm.makeIdentity(self.j_def_midLeg, a=True)

        extra.alignToAlter(self.j_def_foot, self.jfk_foot, mode=2)
        pm.makeIdentity(self.j_def_foot, a=True)
        extra.alignToAlter(self.j_def_ball, self.jfk_ball, mode=2)
        pm.makeIdentity(self.j_def_ball, a=True)
        extra.alignToAlter(self.j_toe, self.jfk_toe, mode=2)
        pm.makeIdentity(self.j_toe, a=True)

        extra.alignToAlter(self.j_socket_ball, self.jfk_ball, mode=2)
        pm.makeIdentity(self.j_socket_ball, a=True)
        pm.parent(self.j_socket_ball, self.j_def_ball)


        pm.parent(self.j_def_midLeg, self.scaleGrp)
        pm.parent(self.jfk_root, self.scaleGrp)
        pm.parent(self.j_def_foot, self.scaleGrp)

        self.deformerJoints += [self.j_def_midLeg, self.j_def_hip, self.jDef_legRoot, self.j_def_foot, self.j_def_ball]

        self.scaleGrp.rigVis >> self.jfk_root.v

    def createControllers(self):
        # Thigh Controller
        thigh_cont_scale = (self.init_upper_leg_dist / 4, self.init_upper_leg_dist / 16, self.init_upper_leg_dist / 4)
        self.cont_thigh = icon.cube("cont_Thigh_%s" % self.suffix, thigh_cont_scale)
        pm.setAttr("{0}.s{1}".format(self.cont_thigh, "y"), self.sideMult)
        pm.makeIdentity(self.cont_thigh, a=True)
        # extra.alignAndAim(self.cont_thigh, targetList=[self.jDef_legRoot], aimTargetList=[self.j_def_hip], upVector=self.up_axis)
        extra.alignAndAim(self.cont_thigh, targetList=[self.hip_ref], aimTargetList=[self.knee_ref], upObject=self.leg_root_ref)
        pm.move(self.cont_thigh, (0, -thigh_cont_scale[0] * 2, 0), r=True, os=True)

        self.cont_thigh_off = extra.createUpGrp(self.cont_thigh, "OFF")
        self.cont_thigh_ore = extra.createUpGrp(self.cont_thigh, "ORE")
        self.cont_thigh_pos = extra.createUpGrp(self.cont_thigh, "POS")

        # IK Foot Controller
        foot_cont_scale = (self.init_foot_length * 0.75, 1, self.init_foot_width * 0.8)
        self.cont_IK_foot = icon.circle("cont_IK_foot_%s" % self.suffix, scale=foot_cont_scale, normal=(0, 1, 0))

        extra.alignAndAim(self.cont_IK_foot, targetList=[self.bank_out_ref, self.bank_in_ref, self.toe_pv_ref, self.heel_pv_ref], aimTargetList=[self.toe_pv_ref], upObject=self.foot_ref)
        pm.xform(self.cont_IK_foot, piv=self.foot_pos, p=True, ws=True)

        # extra.alignToAlter(self.cont_IK_foot, self.jfk_foot, mode=2)



        self.cont_IK_OFF = extra.createUpGrp(self.cont_IK_foot, "OFF")
        cont_ik_hand_ore = extra.createUpGrp(self.cont_IK_foot, "ORE")
        cont_ik_hand_pos = extra.createUpGrp(self.cont_IK_foot, "POS")

        pm.addAttr(self.cont_IK_foot, shortName="polevector", longName="Pole_Vector", defaultValue=0.0, minValue=0.0, maxValue=1.0,
                   at="double", k=True)
        pm.addAttr(self.cont_IK_foot, shortName="sUpLeg", longName="Scale_Upper_Leg", defaultValue=1.0, minValue=0.0, at="double", k=True)
        pm.addAttr(self.cont_IK_foot, shortName="sLowLeg", longName="Scale_Lower_Leg", defaultValue=1.0, minValue=0.0, at="double", k=True)
        pm.addAttr(self.cont_IK_foot, shortName="squash", longName="Squash", defaultValue=0.0, minValue=0.0, maxValue=1.0, at="double", k=True)
        pm.addAttr(self.cont_IK_foot, shortName="stretch", longName="Stretch", defaultValue=1.0, minValue=0.0, maxValue=1.0, at="double",
                   k=True)
        pm.addAttr(self.cont_IK_foot, shortName="stretchLimit", longName="StretchLimit", defaultValue=100.0, minValue=0.0,
                   maxValue=1000.0, at="double",
                   k=True)
        pm.addAttr(self.cont_IK_foot, shortName="softIK", longName="SoftIK", defaultValue=0.0, minValue=0.0, maxValue=100.0, k=True)
        pm.addAttr(self.cont_IK_foot, shortName="volume", longName="Volume_Preserve", defaultValue=0.0, at="double", k=True)
        pm.addAttr(self.cont_IK_foot, shortName="bLean", longName="Ball_Lean", defaultValue=0.0, at="double", k=True)
        pm.addAttr(self.cont_IK_foot, shortName="bRoll", longName="Ball_Roll", defaultValue=0.0, at="double", k=True)
        pm.addAttr(self.cont_IK_foot, shortName="bSpin", longName="Ball_Spin", defaultValue=0.0, at="double", k=True)
        pm.addAttr(self.cont_IK_foot, shortName="hRoll", longName="Heel_Roll", defaultValue=0.0, at="double", k=True)
        pm.addAttr(self.cont_IK_foot, shortName="hSpin", longName="Heel_Spin", defaultValue=0.0, at="double", k=True)
        pm.addAttr(self.cont_IK_foot, shortName="tRoll", longName="Toes_Roll", defaultValue=0.0, at="double", k=True)
        pm.addAttr(self.cont_IK_foot, shortName="tSpin", longName="Toes_Spin", defaultValue=0.0, at="double", k=True)
        pm.addAttr(self.cont_IK_foot, shortName="tWiggle", longName="Toes_Wiggle", defaultValue=0.0, at="double", k=True)
        pm.addAttr(self.cont_IK_foot, shortName="bank", longName="Bank", defaultValue=0.0, at="double", k=True)

        # Pole Vector Controller
        polecont_scale = ((((self.init_upper_leg_dist + self.init_lower_leg_dist) / 2) / 10), (((self.init_upper_leg_dist + self.init_lower_leg_dist) / 2) / 10), (((self.init_upper_leg_dist + self.init_lower_leg_dist) / 2) / 10))
        self.cont_Pole = icon.plus("cont_Pole_%s" % self.suffix, polecont_scale, normal=(0, 0, 1))
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

        self.cont_fk_up_leg = icon.cube("cont_FK_Upleg_%s" % self.suffix, scalecont_fk_up_leg)

        # move the pivot to the bottom
        pm.xform(self.cont_fk_up_leg, piv=(self.sideMult * -(self.init_upper_leg_dist / 2), 0, 0), ws=True)

        # move the controller to the shoulder
        extra.alignToAlter(self.cont_fk_up_leg, self.jfk_root, mode=2)

        self.cont_fk_up_leg_off = extra.createUpGrp(self.cont_fk_up_leg, "OFF")
        self.cont_fk_up_leg_ore = extra.createUpGrp(self.cont_fk_up_leg, "ORE")
        pm.xform(self.cont_fk_up_leg_off, piv=self.hip_pos, ws=True)
        pm.xform(self.cont_fk_up_leg_ore, piv=self.hip_pos, ws=True)

        ## FK LOW Leg Controller
        scalecont_fk_low_leg = (self.init_lower_leg_dist / 2, self.init_lower_leg_dist / 6, self.init_lower_leg_dist / 6)
        self.cont_fk_low_leg = icon.cube("cont_FK_LowArm_%s" % self.suffix, scalecont_fk_low_leg)

        # move the pivot to the bottom
        pm.xform(self.cont_fk_low_leg, piv=(self.sideMult * -(self.init_lower_leg_dist / 2), 0, 0), ws=True)

        # align position and orientation to the joint
        extra.alignToAlter(self.cont_fk_low_leg, self.jfk_knee, mode=2)

        self.cont_fk_low_leg_off = extra.createUpGrp(self.cont_fk_low_leg, "OFF")
        self.cont_fk_low_leg_ore = extra.createUpGrp(self.cont_fk_low_leg, "ORE")
        pm.xform(self.cont_fk_low_leg_off, piv=self.knee_pos, ws=True)
        pm.xform(self.cont_fk_low_leg_ore, piv=self.knee_pos, ws=True)

        ## FK FOOT Controller
        scalecont_fk_foot = (self.init_ball_dist / 2, self.init_ball_dist / 3, self.init_foot_width / 2)
        self.cont_fk_foot = icon.cube("cont_FK_Foot_%s" % self.suffix, scalecont_fk_foot)
        extra.alignToAlter(self.cont_fk_foot, self.jfk_foot, mode=2)

        self.cont_fk_foot_off = extra.createUpGrp(self.cont_fk_foot, "OFF")
        # self.cont_fk_foot_pos = extra.createUpGrp(self.cont_fk_foot, "POS")
        self.cont_fk_foot_ore = extra.createUpGrp(self.cont_fk_foot, "ORE")

        # FK Ball Controller
        scalecont_fk_ball = (self.init_toe_dist / 2, self.init_toe_dist / 3, self.init_foot_width / 2)
        self.cont_fk_ball = icon.cube(name="cont_FK_Ball_%s" % self.suffix, scale=scalecont_fk_ball)
        extra.alignToAlter(self.cont_fk_ball, self.jfk_ball, mode=2)

        self.cont_fk_ball_off = extra.createUpGrp(self.cont_fk_ball, "OFF")
        # self.cont_fk_ball_pos = extra.createUpGrp(self.cont_fk_ball, "POS")
        self.cont_fk_ball_ore = extra.createUpGrp(self.cont_fk_ball, "ORE")

        # FK-IK SWITCH Controller
        icon_scale = self.init_upper_leg_dist / 4
        self.cont_fk_ik, self.fk_ik_rvs = icon.fkikSwitch(("cont_FK_IK_%s" % self.suffix),
                                                          (icon_scale, icon_scale, icon_scale))
        extra.alignAndAim(self.cont_fk_ik, targetList=[self.jfk_foot], aimTargetList=[self.j_def_midLeg],
                          upVector=self.up_axis, rotateOff=(self.sideMult*90, self.sideMult*90, 0))
        pm.move(self.cont_fk_ik, (icon_scale * 2, 0, 0), r=True, os=True)
        self.cont_fk_ik_pos = extra.createUpGrp(self.cont_fk_ik, "POS")

        pm.setAttr("{0}.s{1}".format(self.cont_fk_ik, "x"), self.sideMult)

        # controller for twist orientation alignment
        pm.addAttr(self.cont_fk_ik, shortName="alignHip", longName="Align_Hip", defaultValue=1.0, at="float",
                   minValue=0.0, maxValue=1.0, k=True)

        pm.addAttr(self.cont_fk_ik, shortName="footAutoTwist", longName="Foot_Auto_Twist", defaultValue=1.0,
                   minValue=0.0,
                   maxValue=1.0, at="float", k=True)
        pm.addAttr(self.cont_fk_ik, shortName="footManualTwist", longName="Foot_Manual_Twist", defaultValue=0.0,
                   at="float",
                   k=True)

        pm.addAttr(self.cont_fk_ik, shortName="upLegAutoTwist", longName="UpLeg_Auto_Twist", defaultValue=1.0,
                   minValue=0.0, maxValue=1.0, at="float", k=True)
        pm.addAttr(self.cont_fk_ik, shortName="upLegManualTwist", longName="UpLeg_Manual_Twist", defaultValue=0.0,
                   at="float", k=True)

        pm.addAttr(self.cont_fk_ik, shortName="allowScaling", longName="Allow_Scaling", defaultValue=1.0, minValue=0.0,
                   maxValue=1.0, at="float", k=True)

        pm.addAttr(self.cont_fk_ik, shortName="tweakControls", longName="Tweak_Controls", defaultValue=0, at="bool")
        pm.setAttr(self.cont_fk_ik.tweakControls, cb=True)
        pm.addAttr(self.cont_fk_ik, shortName="fingerControls", longName="Finger_Controls", defaultValue=1, at="bool")
        pm.setAttr(self.cont_fk_ik.fingerControls, cb=True)

        ### Create MidLock controller

        midcont_scale = (self.init_lower_leg_dist / 4, self.init_lower_leg_dist / 4, self.init_lower_leg_dist / 4)
        self.cont_mid_lock = icon.star("cont_mid_%s" % self.suffix, midcont_scale, normal=(1, 0, 0))

        extra.alignToAlter(self.cont_mid_lock, self.jfk_knee, 2)

        self.cont_mid_lock_ext = extra.createUpGrp(self.cont_mid_lock, "EXT")
        self.cont_mid_lock_pos = extra.createUpGrp(self.cont_mid_lock, "POS")
        self.cont_mid_lock_ave = extra.createUpGrp(self.cont_mid_lock, "AVE")

        pm.parent(self.cont_thigh_off, self.scaleGrp)
        pm.parent(self.cont_fk_up_leg_off, self.scaleGrp)
        pm.parent(self.cont_fk_low_leg_off, self.scaleGrp)
        pm.parent(self.cont_fk_foot_off, self.scaleGrp)
        pm.parent(self.cont_mid_lock_ext, self.scaleGrp)
        pm.parent(self.cont_pole_off, self.scaleGrp)
        pm.parent(self.cont_fk_ik_pos, self.scaleGrp)
        pm.parent(self.cont_fk_ball_off, self.scaleGrp)
        pm.parent(self.cont_IK_OFF, self.limbGrp)

        nodesContVis = [self.cont_pole_off, self.cont_thigh_off, self.cont_IK_OFF, self.cont_fk_foot_off,
                        self.cont_fk_ik_pos,
                        self.cont_fk_low_leg_off, self.cont_fk_up_leg_off, self.cont_mid_lock_pos]

        for i in nodesContVis:
            self.scaleGrp.contVis >> i.v

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

        self.master_root = pm.group(em=True, name="masterRoot_%s" % self.suffix)
        extra.alignTo(self.master_root, self.leg_root_ref, 0)
        pm.makeIdentity(self.master_root, a=True)

        ## Create Start Lock

        self.start_lock = pm.spaceLocator(name="startLock_%s" % self.suffix)
        extra.alignToAlter(self.start_lock, self.j_ik_orig_root, 2)
        self.start_lock_ore = extra.createUpGrp(self.start_lock, "_Ore")
        self.start_lock_pos = extra.createUpGrp(self.start_lock, "_Pos")
        self.start_lock_twist = extra.createUpGrp(self.start_lock, "_AutoTwist")

        # start_lock_rot = pm.parentConstraint(j_def_hip, start_lock, mo=True)
        start_lock_weight = pm.parentConstraint(self.j_def_hip, self.start_lock, sr=("y", "z"), mo=False)

        pm.parentConstraint(self.start_lock, self.j_ik_sc_root, mo=True)
        pm.parentConstraint(self.start_lock, self.j_ik_rp_root, mo=True)

        # Create Midlock

        self.mid_lock = pm.spaceLocator(name="midLock_%s" % self.suffix)
        pm.parentConstraint(self.mid_lock, self.j_def_midLeg)
        pm.parentConstraint(self.cont_mid_lock, self.mid_lock, mo=False)

        ### Create End Lock
        self.end_lock = pm.spaceLocator(name="endLock_%s" % self.suffix)
        extra.alignTo(self.end_lock, self.jfk_foot, 2)
        self.end_lock_ore = extra.createUpGrp(self.end_lock, "Ore")
        self.end_lock_pos = extra.createUpGrp(self.end_lock, "Pos")
        self.end_lock_twist = extra.createUpGrp(self.end_lock, "Twist")

        pm.parent(self.mid_lock, self.scaleGrp)
        pm.parent(self.master_root, self.scaleGrp)

        self.scaleGrp.rigVis >> self.end_lock_twist.v
        self.scaleGrp.rigVis >> self.start_lock_ore.v
        self.scaleGrp.rigVis >> self.mid_lock.v
        self.scaleGrp.rigVis >> self.master_root.v


    def createIKsetup(self):

        master_ik = pm.spaceLocator(name="masterIK_" + self.suffix)
        extra.alignTo(master_ik, self.j_def_foot)

        # axis for foot control groups
        foot_plane = pm.spaceLocator(name="footPlaneLocator")
        pm.setAttr(foot_plane.rotateOrder, 0)
        pm.pointConstraint(self.heel_pv_ref, self.toe_pv_ref, foot_plane)
        pm.aimConstraint(self.toe_pv_ref, foot_plane, wuo=self.foot_ref, wut="object")

        self.pv_bank_in = pm.group(name="Pv_BankIn_%s" % self.suffix, em=True)
        extra.alignTo(self.pv_bank_in, self.bank_in_ref, 2)
        pm.makeIdentity(self.pv_bank_in, a=True, t=False, r=True, s=True)
        pm.setAttr(self.pv_bank_in.rotate, pm.getAttr(foot_plane.rotate))
        pm.parent(self.mid_lock, self.scaleGrp)

        self.pv_bank_out = pm.group(name="Pv_BankOut_%s" % self.suffix, em=True)
        extra.alignTo(self.pv_bank_out, self.bank_out_ref, 2)
        pm.makeIdentity(self.pv_bank_out, a=True, t=False, r=True, s=True)
        pm.setAttr(self.pv_bank_out.rotate, pm.getAttr(foot_plane.rotate))

        self.pv_toe = pm.group(name="Pv_Toe_%s" % self.suffix, em=True)
        extra.alignTo(self.pv_toe, self.toe_pv_ref, 2)
        self.pv_toe_ore = extra.createUpGrp(self.pv_toe, "ORE")

        self.pv_ball = pm.group(name="Pv_Ball_%s" % self.suffix, em=True)
        extra.alignTo(self.pv_ball, self.ball_ref, 2)
        self.pv_ball_ore = extra.createUpGrp(self.pv_ball, "ORE")

        pm.parentConstraint(self.pv_ball, self.j_socket_ball)
        # TODO // SOCKETBALL NEEDS A IK/FK Switch

        self.pv_heel = pm.group(name="Pv_Heel_%s" % self.suffix, em=True)
        extra.alignTo(self.pv_heel, self.heel_pv_ref, 2)
        pv_heel_ore = extra.createUpGrp(self.pv_heel, "ORE")

        self.pv_ball_spin = pm.group(name="Pv_BallSpin_%s" % self.suffix, em=True)
        extra.alignTo(self.pv_ball_spin, self.ball_ref, 2)
        self.pv_ball_spin_ore = extra.createUpGrp(self.pv_ball_spin, "ORE")

        self.pv_ball_roll = pm.group(name="Pv_BallRoll_%s" % self.suffix, em=True)
        extra.alignTo(self.pv_ball_roll, self.ball_ref, 2)
        self.pv_ball_roll_ore = extra.createUpGrp(self.pv_ball_roll, "ORE")

        self.pv_ball_lean = pm.group(name="Pv_BallLean_%s" % self.suffix, em=True)
        extra.alignTo(self.pv_ball_lean, self.ball_ref, 2)
        self.pv_ball_lean_ore = extra.createUpGrp(self.pv_ball_lean, "ORE")

        # Create IK handles

        ik_handle_sc = pm.ikHandle(sj=self.j_ik_sc_root, ee=self.j_ik_sc_end, name="ikHandle_SC_%s" % self.suffix)
        ik_handle_rp = pm.ikHandle(sj=self.j_ik_rp_root, ee=self.j_ik_rp_end, name="ikHandle_RP_%s" % self.suffix, sol="ikRPsolver")

        pm.poleVectorConstraint(self.cont_Pole, ik_handle_rp[0])
        pm.aimConstraint(self.j_ik_rp_knee, self.cont_Pole)

        ik_handle_ball = pm.ikHandle(sj=self.j_ik_foot, ee=self.j_ik_ball, name="ikHandle_Ball_%s" % self.suffix)
        ik_handle_toe = pm.ikHandle(sj=self.j_ik_ball, ee=self.j_ik_toe, name="ikHandle_Toe_%s" % self.suffix)

        # Create Hierarchy for Foot

        pm.parent(ik_handle_ball[0], self.pv_ball)
        pm.parent(ik_handle_toe[0], self.pv_ball)
        pm.parent(master_ik, self.pv_ball_lean)
        pm.parent(ik_handle_sc[0], master_ik)
        pm.parent(ik_handle_rp[0], master_ik)
        pm.parent(self.pv_ball_lean_ore, self.pv_ball_roll)
        pm.parent(self.pv_ball_ore, self.pv_toe)
        pm.parent(self.pv_ball_roll_ore, self.pv_toe)
        pm.parent(self.pv_toe_ore, self.pv_ball_spin)
        pm.parent(self.pv_ball_spin_ore, self.pv_heel)
        pm.parent(pv_heel_ore, self.pv_bank_out)
        pm.parent(self.pv_bank_out, self.pv_bank_in)

        ### Create and constrain Distance Locators

        leg_start = pm.spaceLocator(name="legStart_loc_%s" % self.suffix)
        pm.pointConstraint(self.start_lock, leg_start, mo=False)

        leg_end = pm.spaceLocator(name="legEnd_loc_%s" % self.suffix)
        pm.pointConstraint(master_ik, leg_end, mo=False)

        ### Create Nodes and Connections for Stretchy IK SC

        stretch_offset = pm.createNode("plusMinusAverage", name="stretchOffset_%s" % self.suffix)
        distance_sc = pm.createNode("distanceBetween", name="distance_SC_%s" % self.suffix)
        ik_stretch_distance_clamp = pm.createNode("clamp", name="IK_stretch_distanceClamp_%s" % self.suffix)
        ik_stretch_stretchiness_clamp = pm.createNode("clamp", name="IK_stretch_stretchinessClamp_%s" % self.suffix)
        extra_scale_mult_sc = pm.createNode("multiplyDivide", name="extraScaleMult_SC_%s" % self.suffix)
        initial_divide_sc = pm.createNode("multiplyDivide", name="initialDivide_SC_%s" % self.suffix)
        self.initial_length_multip_sc = pm.createNode("multiplyDivide", name="initialLengthMultip_SC_%s" % self.suffix)
        stretch_amount_sc = pm.createNode("multiplyDivide", name="stretchAmount_SC_%s" % self.suffix)
        sum_of_j_lengths_sc = pm.createNode("plusMinusAverage", name="sumOfJLengths_SC_%s" % self.suffix)
        squashiness_sc = pm.createNode("blendColors", name="squashiness_SC_%s" % self.suffix)
        self.stretchiness_sc = pm.createNode("blendColors", name="stretchiness_SC_%s" % self.suffix)

        pm.setAttr("%s.maxR" % ik_stretch_stretchiness_clamp, 1)
        pm.setAttr("%s.input1X" % self.initial_length_multip_sc, self.init_upper_leg_dist)
        pm.setAttr("%s.input1Y" % self.initial_length_multip_sc, self.init_lower_leg_dist)
        pm.setAttr("%s.operation" % initial_divide_sc, 2)
        #
        ### IkSoft nodes
        ik_soft_clamp = pm.createNode("clamp", name="ikSoft_clamp_%s" % self.suffix)
        pm.setAttr("%s.minR" % ik_soft_clamp, 0.0001)
        pm.setAttr("%s.maxR" % ik_soft_clamp, 99999)

        ik_soft_sub1 = pm.createNode("plusMinusAverage", name="ikSoft_Sub1_%s" % self.suffix)
        pm.setAttr("%s.operation" % ik_soft_sub1, 2)

        ik_soft_sub2 = pm.createNode("plusMinusAverage", name="ikSoft_Sub2_%s" % self.suffix)
        pm.setAttr("%s.operation" % ik_soft_sub2, 2)

        ik_soft_div1 = pm.createNode("multiplyDivide", name="ikSoft_Div1_%s" % self.suffix)
        pm.setAttr("%s.operation" % ik_soft_div1, 2)

        ik_soft_mult1 = pm.createNode("multDoubleLinear", name="ikSoft_Mult1_%s" % self.suffix)
        pm.setAttr("%s.input1" % ik_soft_mult1, -1)

        ik_soft_pow = pm.createNode("multiplyDivide", name="ikSoft_Pow_%s" % self.suffix)
        pm.setAttr("%s.operation" % ik_soft_pow, 3)
        pm.setAttr("%s.input1X" % ik_soft_pow, 2.718)

        ik_soft_mult2 = pm.createNode("multDoubleLinear", name="ikSoft_Mult2_%s" % self.suffix)

        ik_soft_sub3 = pm.createNode("plusMinusAverage", name="ikSoft_Sub3_%s" % self.suffix)
        pm.setAttr("%s.operation" % ik_soft_sub3, 2)

        ik_soft_condition = pm.createNode("condition", name="ikSoft_Condition_%s" % self.suffix)
        pm.setAttr("%s.operation" % ik_soft_condition, 2)

        ik_soft_div2 = pm.createNode("multiplyDivide", name="ikSoft_Div2_%s" % self.suffix)
        pm.setAttr("%s.operation" % ik_soft_div2, 2)

        ik_soft_stretch_amount = pm.createNode("multiplyDivide", name="ikSoft_stretchAmount_SC_%s" % self.suffix)
        pm.setAttr("%s.operation" % ik_soft_stretch_amount, 1)

        ### Bind Attributes and make constraints

        # Bind Stretch Attributes
        leg_start.translate >> distance_sc.point1
        leg_end.translate >> distance_sc.point2
        distance_sc.distance >> ik_stretch_distance_clamp.inputR

        ik_stretch_distance_clamp.outputR >> initial_divide_sc.input1X
        ik_stretch_stretchiness_clamp.outputR >> self.stretchiness_sc.blender

        initial_divide_sc.outputX >> stretch_amount_sc.input2X
        initial_divide_sc.outputX >> stretch_amount_sc.input2Y

        self.initial_length_multip_sc.outputX >> extra_scale_mult_sc.input1X
        self.initial_length_multip_sc.outputY >> extra_scale_mult_sc.input1Y
        self.initial_length_multip_sc.outputX >> stretch_offset.input1D[0]
        self.initial_length_multip_sc.outputY >> stretch_offset.input1D[1]

        extra_scale_mult_sc.outputX >> stretch_amount_sc.input1X
        extra_scale_mult_sc.outputY >> stretch_amount_sc.input1Y
        extra_scale_mult_sc.outputX >> self.stretchiness_sc.color2R
        extra_scale_mult_sc.outputY >> self.stretchiness_sc.color2G
        extra_scale_mult_sc.outputX >> sum_of_j_lengths_sc.input1D[0]
        extra_scale_mult_sc.outputY >> sum_of_j_lengths_sc.input1D[1]

        stretch_amount_sc.outputX >> squashiness_sc.color1R
        stretch_amount_sc.outputY >> squashiness_sc.color1G
        sum_of_j_lengths_sc.output1D >> initial_divide_sc.input2X
        squashiness_sc.outputR >> self.stretchiness_sc.color1R
        squashiness_sc.outputG >> self.stretchiness_sc.color1G

        invertedStrSC = pm.createNode("multiplyDivide")
        pm.setAttr(invertedStrSC.input2X, self.sideMult)
        pm.setAttr(invertedStrSC.input2Y, self.sideMult)
        self.stretchiness_sc.outputR >> invertedStrSC.input1X
        self.stretchiness_sc.outputG >> invertedStrSC.input1Y

        invertedStrSC.outputX >> self.j_ik_sc_knee.translateX
        invertedStrSC.outputY >> self.j_ik_sc_end.translateX

        invertedStrSC.outputX >> self.j_ik_rp_knee.translateX
        invertedStrSC.outputY >> self.j_ik_rp_end.translateX


        # self.stretchiness_sc.outputR >> self.j_ik_sc_knee.translateX
        # self.stretchiness_sc.outputG >> self.j_ik_sc_end.translateX
        # self.stretchiness_sc.outputR >> self.j_ik_rp_knee.translateX
        # self.stretchiness_sc.outputG >> self.j_ik_rp_end.translateX


        ## iksoft related
        self.cont_IK_foot.softIK >> ik_soft_clamp.inputR

        sum_of_j_lengths_sc.output1D >> ik_soft_sub1.input1D[0]
        ik_soft_clamp.outputR >> ik_soft_sub1.input1D[1]

        ik_stretch_distance_clamp.outputR >> ik_soft_sub2.input1D[0]
        ik_soft_sub1.output1D >> ik_soft_sub2.input1D[1]

        ik_soft_sub2.output1D >> ik_soft_div1.input1X
        ik_soft_clamp.outputR >> ik_soft_div1.input2X

        ik_soft_div1.outputX >> ik_soft_mult1.input2

        ik_soft_mult1.output >> ik_soft_pow.input2X

        ik_soft_clamp.outputR >> ik_soft_mult2.input1
        ik_soft_pow.outputX >> ik_soft_mult2.input2

        sum_of_j_lengths_sc.output1D >> ik_soft_sub3.input1D[0]
        ik_soft_mult2.output >> ik_soft_sub3.input1D[1]

        ik_stretch_distance_clamp.outputR >> ik_soft_condition.firstTerm
        ik_soft_sub1.output1D >> ik_soft_condition.secondTerm
        ik_soft_sub3.output1D >> ik_soft_condition.colorIfTrueR
        ik_stretch_distance_clamp.outputR >> ik_soft_condition.colorIfFalseR

        ik_stretch_distance_clamp.outputR >> ik_soft_div2.input1X
        ik_soft_condition.outColorR >> ik_soft_div2.input2X

        extra_scale_mult_sc.outputX >> ik_soft_stretch_amount.input1X
        extra_scale_mult_sc.outputY >> ik_soft_stretch_amount.input1Y
        ik_soft_div2.outputX >> ik_soft_stretch_amount.input2X
        ik_soft_div2.outputX >> ik_soft_stretch_amount.input2Y

        ik_soft_stretch_amount.outputX >> squashiness_sc.color2R
        ik_soft_stretch_amount.outputY >> squashiness_sc.color2G

        self.cont_IK_foot.rotate >> self.j_ik_rp_end.rotate

        # Stretch Attributes Controller connections

        self.cont_IK_foot.sUpLeg >> extra_scale_mult_sc.input2X
        self.cont_IK_foot.sLowLeg >> extra_scale_mult_sc.input2Y
        self.cont_IK_foot.squash >> squashiness_sc.blender

        stretch_offset.output1D >> ik_stretch_distance_clamp.maxR
        self.cont_IK_foot.stretch >> ik_stretch_stretchiness_clamp.inputR

        self.cont_IK_foot.stretchLimit >> stretch_offset.input1D[2]
        #
        # Bind Foot Attributes to the controller
        # create multiply nodes for alignment fix
        mult_al_fix_b_lean = pm.createNode("multDoubleLinear", name="multAlFix_bLean_{0}".format(self.suffix))
        mult_al_fix_b_roll = pm.createNode("multDoubleLinear", name="multAlFix_bRoll_{0}".format(self.suffix))
        mult_al_fix_b_spin = pm.createNode("multDoubleLinear", name="multAlFix_bSpin_{0}".format(self.suffix))
        mult_al_fix_h_roll = pm.createNode("multDoubleLinear", name="multAlFix_hRoll_{0}".format(self.suffix))
        mult_al_fix_h_spin = pm.createNode("multDoubleLinear", name="multAlFix_hSpin_{0}".format(self.suffix))
        mult_al_fix_t_roll = pm.createNode("multDoubleLinear", name="multAlFix_tRoll_{0}".format(self.suffix))
        mult_al_fix_t_spin = pm.createNode("multDoubleLinear", name="multAlFix_tSpin_{0}".format(self.suffix))
        mult_al_fix_t_wiggle = pm.createNode("multDoubleLinear", name="multAlFix_tWiggle_{0}".format(self.suffix))

        pm.setAttr(mult_al_fix_b_lean.input2, self.sideMult)
        pm.setAttr(mult_al_fix_b_roll.input2, self.sideMult)
        pm.setAttr(mult_al_fix_b_spin.input2, self.sideMult)
        # heel roll is an exception. It should be same for each side
        pm.setAttr(mult_al_fix_h_roll.input2, 1)
        pm.setAttr(mult_al_fix_h_spin.input2, self.sideMult)
        # toe roll is an exception too.
        pm.setAttr(mult_al_fix_t_roll.input2, 1)
        pm.setAttr(mult_al_fix_t_spin.input2, self.sideMult)
        pm.setAttr(mult_al_fix_t_wiggle.input2, self.sideMult)

        self.cont_IK_foot.bLean >> mult_al_fix_b_lean.input1
        self.cont_IK_foot.bRoll >> mult_al_fix_b_roll.input1
        self.cont_IK_foot.bSpin >> mult_al_fix_b_spin.input1
        self.cont_IK_foot.hRoll >> mult_al_fix_h_roll.input1
        self.cont_IK_foot.hSpin >> mult_al_fix_h_spin.input1
        self.cont_IK_foot.tRoll >> mult_al_fix_t_roll.input1
        self.cont_IK_foot.tSpin >> mult_al_fix_t_spin.input1
        self.cont_IK_foot.tWiggle >> mult_al_fix_t_wiggle.input1

        mult_al_fix_b_lean.output >> self.pv_ball_lean.rotateY
        mult_al_fix_b_roll.output >> self.pv_ball_roll.rotateZ
        mult_al_fix_b_spin.output >> self.pv_ball_spin.rotateY
        mult_al_fix_h_roll.output >> self.pv_heel.rotateX
        mult_al_fix_h_spin.output >> self.pv_heel.rotateY
        mult_al_fix_t_roll.output >> self.pv_toe.rotateX
        mult_al_fix_t_spin.output >> self.pv_toe.rotateY
        mult_al_fix_t_wiggle.output >> self.pv_ball.rotateZ

        pv_bank_in_ore = extra.createUpGrp(self.pv_bank_in, "ORE")

        pm.setDrivenKeyframe(self.pv_bank_out.rotateX, cd=self.cont_IK_foot.bank, dv=0, v=0, itt='linear', ott='linear')
        pm.setDrivenKeyframe(self.pv_bank_out.rotateX, cd=self.cont_IK_foot.bank, dv=90, v=90 * self.sideMult, itt='linear', ott='linear')

        pm.setDrivenKeyframe(self.pv_bank_in.rotateX, cd=self.cont_IK_foot.bank, dv=0, v=0, itt='linear', ott='linear')
        pm.setDrivenKeyframe(self.pv_bank_in.rotateX, cd=self.cont_IK_foot.bank, dv=-90, v=90 * (-1 * self.sideMult), itt='linear', ott='linear')





        self.ik_parent_grp = pm.group(name="IK_parentGRP_%s" % self.suffix, em=True)
        # extra.alignTo(self.ik_parent_grp, self.j_def_foot, 2)
        extra.alignToAlter(self.ik_parent_grp, self.cont_IK_foot, 2)
        pm.parent(pv_bank_in_ore, self.ik_parent_grp)
        pm.parent(self.j_ik_foot, self.ik_parent_grp)
        pm.parentConstraint(self.j_ik_sc_end, self.j_ik_foot)


        pm.parentConstraint(self.cont_IK_foot, self.ik_parent_grp, mo=False)

        # parenting should be after the constraint
        pm.parent(ik_handle_sc[0], self.ik_parent_grp)
        pm.parent(ik_handle_rp[0], self.ik_parent_grp)
        pm.parent(master_ik, self.ik_parent_grp)

        blend_ore_ik_root = pm.createNode("blendColors", name="blendORE_IK_Up_%s" % self.suffix)
        self.j_ik_sc_root.rotate >> blend_ore_ik_root.color2
        self.j_ik_rp_root.rotate >> blend_ore_ik_root.color1
        blend_ore_ik_root.output >> self.j_ik_orig_root.rotate
        self.cont_IK_foot.polevector >> blend_ore_ik_root.blender

        blend_pos_ik_root = pm.createNode("blendColors", name="blendPOS_IK_Up_%s" % self.suffix)
        self.j_ik_sc_root.translate >> blend_pos_ik_root.color2
        self.j_ik_rp_root.translate >> blend_pos_ik_root.color1
        blend_pos_ik_root.output >> self.j_ik_orig_root.translate
        self.cont_IK_foot.polevector >> blend_pos_ik_root.blender

        blend_ore_ik_knee = pm.createNode("blendColors", name="blendORE_IK_Low_%s" % self.suffix)
        self.j_ik_sc_knee.rotate >> blend_ore_ik_knee.color2
        self.j_ik_rp_knee.rotate >> blend_ore_ik_knee.color1
        # Weird bug with skinned character / use seperate connections
        # if there is no skincluster, it works ok, but adding a skin cluster misses 2 out of 3 rotation axis
        # Therefore make SEPERATE CONNECTIONS
        blend_ore_ik_knee.outputR >> self.j_ik_orig_knee.rotateX
        blend_ore_ik_knee.outputG >> self.j_ik_orig_knee.rotateY
        blend_ore_ik_knee.outputB >> self.j_ik_orig_knee.rotateZ
        self.cont_IK_foot.polevector >> blend_ore_ik_knee.blender

        blend_pos_ik_knee = pm.createNode("blendColors", name="blendPOS_IK_Low_%s" % self.suffix)
        self.j_ik_sc_knee.translate >> blend_pos_ik_knee.color2
        self.j_ik_rp_knee.translate >> blend_pos_ik_knee.color1
        blend_pos_ik_knee.output >> self.j_ik_orig_knee.translate
        self.cont_IK_foot.polevector >> blend_pos_ik_knee.blender

        blend_ore_ik_end = pm.createNode("blendColors", name="blendORE_IK_LowEnd_%s" % self.suffix)
        self.j_ik_sc_end.rotate >> blend_ore_ik_end.color2
        self.j_ik_rp_end.rotate >> blend_ore_ik_end.color1
        # Weird bug with skinned character / use seperate connections
        # if there is no skincluster, it works ok, but adding a skin cluster misses 2 out of 3 rotation axis
        # Therefore make SEPERATE CONNECTIONS
        blend_ore_ik_end.outputR >> self.j_ik_orig_end.rotateX
        blend_ore_ik_end.outputG >> self.j_ik_orig_end.rotateY
        blend_ore_ik_end.outputB >> self.j_ik_orig_end.rotateZ
        self.cont_IK_foot.polevector >> blend_ore_ik_end.blender

        blend_pos_ik_end = pm.createNode("blendColors", name="blendPOS_IK_LowEnd_%s" % self.suffix)
        self.j_ik_sc_end.translate >> blend_pos_ik_end.color2
        self.j_ik_rp_end.translate >> blend_pos_ik_end.color1
        blend_pos_ik_end.output >> self.j_ik_orig_end.translate
        self.cont_IK_foot.polevector >> blend_pos_ik_end.blender

        pole_vector_rvs = pm.createNode("reverse", name="poleVector_Rvs_%s" % self.suffix)
        self.cont_IK_foot.polevector >> pole_vector_rvs.inputX
        self.cont_IK_foot.polevector >> self.cont_Pole.v

        pm.parent(self.j_ik_orig_root, self.master_root)
        pm.parent(self.j_ik_sc_root, self.master_root)
        pm.parent(self.j_ik_rp_root, self.master_root)

        # pm.parentConstraint(self.cont_thigh, self.jDef_legRoot, mo=False, st=("x", "y", "z"))
        # pm.pointConstraint(self.cont_thigh, j_def_hip, mo=True)

        # pacon_locator_shou = pm.spaceLocator(name="paConLoc_%s" % self.suffix)
        # extra.alignTo(pacon_locator_shou, self.j_def_collar, mode=2)
        #
        # j_def_pa_con = pm.parentConstraint(self.cont_shoulder, pacon_locator_shou, mo=False)
        #
        pm.parent(leg_start, self.scaleGrp)
        pm.parent(leg_end, self.scaleGrp)
        pm.parent(self.ik_parent_grp, self.scaleGrp)
        pm.parent(self.start_lock_ore, self.scaleGrp)
        pm.parent(self.end_lock_ore, self.scaleGrp)
        #
        # pm.parent(pacon_locator_shou, self.scaleGrp)
        # pm.parent(self.j_def_collar, pacon_locator_shou)
        #
        self.scaleGrp.rigVis >> leg_start.v
        self.scaleGrp.rigVis >> leg_end.v
        self.scaleGrp.rigVis >> self.ik_parent_grp.v
        # self.scaleGrp.rigVis >> pacon_locator_shou.getShape().v

        pm.delete(foot_plane)

    def createFKsetup(self):
        pass

    def ikfkSwitching(self):
        pass

    def createDefJoints(self):
        pass

    def roundUp(self):
        pass

    def createLimb(self):
        self.createGrp()
        self.createJoints()
        self.createControllers()
        self.createRoots()
        self.createIKsetup()
        self.createFKsetup()
        self.ikfkSwitching()
        self.createDefJoints()
        self.roundUp()


    def createleg(self, leginits, suffix="", side="L"):




        ########
        ########
        foot_plane = pm.spaceLocator(name="testLocator")
        pm.setAttr(foot_plane.rotateOrder, 0)
        pm.pointConstraint(heel_pv_ref, toe_pv_ref, foot_plane)
        pm.aimConstraint(toe_pv_ref, foot_plane, wuo=foot_ref, wut="object")
        ########
        ########

        #     _____            _             _ _
        #    / ____|          | |           | | |
        #   | |     ___  _ __ | |_ _ __ ___ | | | ___ _ __ ___
        #   | |    / _ \| '_ \| __| '__/ _ \| | |/ _ \ '__/ __|
        #   | |___| (_) | | | | |_| | | (_) | | |  __/ |  \__ \
        #    \_____\___/|_| |_|\__|_|  \___/|_|_|\___|_|  |___/
        #
        #


        extra.alignAndAim(cont_thigh, targetList=[hip_ref], aimTargetList=[knee_ref], upObject=leg_root_ref)
        pm.move(cont_thigh, (0, -thigh_cont_scale[0] * 2, 0), r=True, os=True)

        cont_thigh_off = extra.createUpGrp(cont_thigh, "OFF")
        cont_thigh_ore = extra.createUpGrp(cont_thigh, "ORE")
        if side == "R":
            pm.setAttr(cont_thigh_ore.rotateZ, -180)

        pm.xform(cont_thigh, piv=leg_root_pos, ws=True)
        # pm.addAttr(shortName="autoTwist", longName="Auto_Twist", defaultValue=1.0, minValue=0.0, maxValue=1.0, at="float",
        #            k=True)
        # pm.addAttr(shortName="manualTwist", longName="Manual_Twist", defaultValue=0.0, at="float", k=True)




        # FK Upleg Controller
        scalecont_fk_up_leg = (init_upper_leg_dist / 2, init_upper_leg_dist / 6, init_upper_leg_dist / 6)
        cont_fk_up_leg = icon.cube("cont_FK_Upleg_%s" % suffix, scalecont_fk_up_leg)
        extra.alignAndAim(cont_fk_up_leg, targetList=[hip_ref, knee_ref], aimTargetList=[knee_ref], upVector=up_axis)

        cont_fk_up_leg_off = extra.createUpGrp(cont_fk_up_leg, "OFF")
        cont_fk_up_leg_ore = extra.createUpGrp(cont_fk_up_leg, "ORE")

        if side == "R":
            pm.setAttr("%s.r%s" % (cont_fk_up_leg_ore, "z"), -180)

        pm.xform(cont_fk_up_leg, piv=hip_pos, ws=True)
        pm.xform(cont_fk_up_leg_ore, piv=hip_pos, ws=True)
        pm.xform(cont_fk_up_leg_off, piv=hip_pos, ws=True)

        # FK Lowleg Controller
        scalecont_fk_low_leg = (init_lower_leg_dist / 2, init_lower_leg_dist / 6, init_lower_leg_dist / 6)
        cont_fk_low_leg = icon.cube("cont_FK_Lowleg_%s" % suffix, scalecont_fk_low_leg)
        extra.alignAndAim(cont_fk_low_leg, targetList=[knee_ref, foot_ref], aimTargetList=[foot_ref], upVector=up_axis)

        cont_fk_low_leg_off = extra.createUpGrp(cont_fk_low_leg, "OFF")
        cont_fk_low_leg_ore = extra.createUpGrp(cont_fk_low_leg, "ORE")

        if side == "R":
            pm.setAttr("%s.r%s" % (cont_fk_low_leg_ore, "z"), -180)

        pm.xform(cont_fk_low_leg, piv=knee_pos, ws=True)
        pm.xform(cont_fk_low_leg_ore, piv=knee_pos, ws=True)
        pm.xform(cont_fk_low_leg_off, piv=knee_pos, ws=True)

        # FK Foot Controller
        scalecont_fk_foot = (init_ball_dist / 2, init_ball_dist / 3, init_foot_width / 2)
        cont_fk_foot = icon.cube(name="cont_FK_Foot_%s" % suffix, scale=scalecont_fk_foot)
        # extra.alignAndAim(cont_FK_Foot, targetList=[footRef,ballRef], aimTargetList=[ballRef], upVector=self.upAxis)
        extra.alignAndAim(cont_fk_foot, targetList=[foot_ref, ball_ref], aimTargetList=[ball_ref], upVector=up_axis)

        cont_fk_foot_off = extra.createUpGrp(cont_fk_foot, "OFF")
        cont_fk_foot_ore = extra.createUpGrp(cont_fk_foot, "ORE")

        if side == "R":
            pm.setAttr("%s.r%s" % (cont_fk_foot_ore, "z"), -180)

        pm.xform(cont_fk_foot, piv=foot_pos, ws=True)
        pm.xform(cont_fk_foot_ore, piv=foot_pos, ws=True)
        pm.xform(cont_fk_foot_off, piv=foot_pos, ws=True)

        # FK Ball Controller
        scalecont_fk_ball = (init_toe_dist / 2, init_toe_dist / 3, init_foot_width / 2)
        cont_fk_ball = icon.cube(name="cont_FK_Ball_%s" % suffix, scale=scalecont_fk_ball)
        extra.alignAndAim(cont_fk_ball, targetList=[ball_ref, toe_pv_ref], aimTargetList=[toe_pv_ref], upVector=up_axis)

        cont_fk_ball_off = extra.createUpGrp(cont_fk_ball, "OFF")
        cont_fk_ball_ore = extra.createUpGrp(cont_fk_ball, "ORE")

        if side == "R":
            pm.setAttr("%s.r%s" % (cont_fk_ball_ore, "z"), -180)

        pm.xform(cont_fk_ball, piv=ball_pos, ws=True)
        pm.xform(cont_fk_ball_ore, piv=ball_pos, ws=True)
        pm.xform(cont_fk_ball_off, piv=ball_pos, ws=True)

        # FK-IK SWITCH Controller
        icon_scale = init_lower_leg_dist / 4
        cont_fk_ik, fk_ik_rvs = icon.fkikSwitch(("cont_FK_IK_%s" % suffix), (icon_scale, icon_scale, icon_scale))
        extra.alignAndAim(cont_fk_ik, targetList=[foot_ref], aimTargetList=[knee_ref], upVector=up_axis, rotateOff=(90, 90, 0))
        # pm.move(cont_FK_IK, (dt.Vector(self.upAxis) *(iconScale*2)), r=True)
        pm.move(cont_fk_ik, (icon_scale * 2, 0, 0), r=True, os=True)
        cont_fk_ik_pos = extra.createUpGrp(cont_fk_ik, "POS")

        if side == "R":
            pm.move(cont_fk_ik, (-icon_scale * 4, 0, 0), r=True, os=True)
            pm.makeIdentity(cont_fk_ik, a=True)

        pm.addAttr(cont_fk_ik, shortName="alignHip", longName="Align_Hip", defaultValue=1.0, at="float", minValue=0.0, maxValue=1.0, k=True)

        pm.addAttr(cont_fk_ik, shortName="footAutoTwist", longName="Foot_Auto_Twist", defaultValue=1.0, minValue=0.0, maxValue=1.0, at="float", k=True)
        pm.addAttr(cont_fk_ik, shortName="footManualTwist", longName="Foot_Manual_Twist", defaultValue=0.0, at="float", k=True)

        pm.addAttr(cont_fk_ik, shortName="upLegAutoTwist", longName="UpLeg_Auto_Twist", defaultValue=1.0, minValue=0.0, maxValue=1.0, at="float", k=True)
        pm.addAttr(cont_fk_ik, shortName="upLegManualTwist", longName="UpLeg_Manual_Twist", defaultValue=0.0, at="float", k=True)

        pm.addAttr(cont_fk_ik, shortName="allowScaling", longName="Allow_Scaling", defaultValue=1.0, minValue=0.0, maxValue=1.0, at="float", k=True)


        # pm.addAttr(cont_fk_ik, shortName="autoTwist", longName="Auto_Twist", defaultValue=1.0, minValue=0.0, maxValue=1.0,
        #            at="float", k=True)
        # pm.addAttr(cont_fk_ik, shortName="manualTwist", longName="Manual_Twist", defaultValue=0.0, at="float", k=True)
        pm.addAttr(cont_fk_ik, at="enum", k=True, shortName="interpType", longName="Interp_Type", en="No_Flip:Average:Shortest:Longest:Cache", defaultValue=0)
        pm.addAttr(cont_fk_ik, shortName="tweakControls", longName="Tweak_Controls", defaultValue=0, at="bool")
        pm.setAttr(cont_fk_ik.tweakControls, cb=True)
        pm.addAttr(cont_fk_ik, shortName="fingerControls", longName="Finger_Controls", defaultValue=1, at="bool")
        pm.setAttr(cont_fk_ik.fingerControls, cb=True)

        ###########################################################################################################################

        # Groups






        ###########################
        ######### IK LEG ##########
        ###########################

        master_ik = pm.spaceLocator(name="masterIK_" + suffix)
        extra.alignTo(master_ik, foot_ref)



        # extra.orientJoints([j_ik_orig_root, j_ik_orig_knee, j_ik_orig_end], localMoveAxis=look_axis, upAxis=up_axis)
        # extra.orientJoints([j_ik_sc_root, j_ik_sc_knee, j_ik_sc_end], localMoveAxis=look_axis, upAxis=up_axis)
        # extra.orientJoints([j_ik_rp_root, j_ik_rp_knee, j_ik_rp_end], localMoveAxis=look_axis, upAxis=up_axis)
        # extra.orientJoints([j_ik_foot, j_ik_ball, j_ik_toe], localMoveAxis=look_axis, upAxis=up_axis)
        extra.orientJoints([j_ik_orig_root, j_ik_orig_knee, j_ik_orig_end], localMoveAxis=up_axis, upAxis=up_axis)
        extra.orientJoints([j_ik_sc_root, j_ik_sc_knee, j_ik_sc_end], localMoveAxis=up_axis, upAxis=up_axis)
        extra.orientJoints([j_ik_rp_root, j_ik_rp_knee, j_ik_rp_end], localMoveAxis=up_axis, upAxis=up_axis)
        extra.orientJoints([j_ik_foot, j_ik_ball, j_ik_toe], localMoveAxis=up_axis, upAxis=up_axis)


        # pm.joint(j_ik_orig_root, e=True, zso=True, oj="xyz", sao="zdown")
        # pm.joint(j_ik_orig_knee, e=True, zso=True, oj="xyz", sao="zdown")
        # pm.joint(j_ik_orig_end, e=True, zso=True, oj="xyz", sao="zdown")
        # pm.joint(j_ik_sc_root, e=True, zso=True, oj="xyz", sao="zdown")
        # pm.joint(j_ik_sc_knee, e=True, zso=True, oj="xyz", sao="zdown")
        # pm.joint(j_ik_sc_end, e=True, zso=True, oj="xyz", sao="zdown")
        # pm.joint(j_ik_rp_root, e=True, zso=True, oj="xyz", sao="zdown")
        # pm.joint(j_ik_rp_knee, e=True, zso=True, oj="xyz", sao="zdown")
        # pm.joint(j_ik_rp_end, e=True, zso=True, oj="xyz", sao="zdown")
        # pm.joint(j_ik_foot, e=True, zso=True, oj="xyz", sao="zdown")
        # pm.joint(j_ik_ball, e=True, zso=True, oj="xyz", sao="zdown")
        # pm.joint(j_ik_toe, e=True, zso=True, oj="xyz", sao="zdown")

        # pm.delete(j_ik_orig_temp)
        # pm.delete(j_ik_sc_temp)
        # pm.delete(j_ik_rp_temp)
        # Create Foot Pivots and Ball Socket
        pm.select(cl=True)

        pv_bank_in = pm.group(name="Pv_BankIn_%s" % suffix, em=True)
        extra.alignTo(pv_bank_in, bank_in_ref, 2)
        pm.makeIdentity(pv_bank_in, a=True, t=False, r=True, s=True)
        pm.setAttr(pv_bank_in.rotate, pm.getAttr(foot_plane.rotate))

        pv_bank_out = pm.group(name="Pv_BankOut_%s" % suffix, em=True)
        extra.alignTo(pv_bank_out, bank_out_ref, 2)
        pm.makeIdentity(pv_bank_out, a=True, t=False, r=True, s=True)
        pm.setAttr(pv_bank_out.rotate, pm.getAttr(foot_plane.rotate))

        pv_toe = pm.group(name="Pv_Toe_%s" % suffix, em=True)
        extra.alignTo(pv_toe, toe_pv_ref, 2)
        pv_toe_ore = extra.createUpGrp(pv_toe, "ORE")

        pv_ball = pm.group(name="Pv_Ball_%s" % suffix, em=True)
        extra.alignTo(pv_ball, ball_ref, 2)
        pv_ball_ore = extra.createUpGrp(pv_ball, "ORE")

        j_socket_ball = pm.joint(name="jBallSocket_%s" % suffix, radius=3)
        pm.parentConstraint(pv_ball, j_socket_ball)
        # TODO // SOCKETBALL NEEDS A IK/FK Switch
        self.sockets.append(j_socket_ball)

        pv_heel = pm.group(name="Pv_Heel_%s" % suffix, em=True)
        extra.alignTo(pv_heel, heel_pv_ref, 2)
        pv_heel_ore = extra.createUpGrp(pv_heel, "ORE")

        pv_ball_spin = pm.group(name="Pv_BallSpin_%s" % suffix, em=True)
        extra.alignTo(pv_ball_spin, ball_ref, 2)
        pv_ball_spin_ore = extra.createUpGrp(pv_ball_spin, "ORE")

        pv_ball_roll = pm.group(name="Pv_BallRoll_%s" % suffix, em=True)
        extra.alignTo(pv_ball_roll, ball_ref, 2)
        pv_ball_roll_ore = extra.createUpGrp(pv_ball_roll, "ORE")

        pv_ball_lean = pm.group(name="Pv_BallLean_%s" % suffix, em=True)
        extra.alignTo(pv_ball_lean, ball_ref, 2)
        pv_ball_lean_ore = extra.createUpGrp(pv_ball_lean, "ORE")

        ## Create Start Lock

        start_lock = pm.spaceLocator(name="startLock_%s" % suffix)
        extra.alignTo(start_lock, hip_ref, 2)
        start_lock_ore = extra.createUpGrp(start_lock, "_Ore")
        start_lock_pos = extra.createUpGrp(start_lock, "_Pos")
        start_lock_twist = extra.createUpGrp(start_lock, "_AutoTwist")

        start_lock_rot = pm.parentConstraint(j_def_hip, start_lock, mo=True)

        pm.parentConstraint(start_lock, j_ik_sc_root, mo=True)
        pm.parentConstraint(start_lock, j_ik_rp_root, mo=True)

        # Create IK handles

        ik_handle_sc = pm.ikHandle(sj=j_ik_sc_root, ee=j_ik_sc_end, name="ikHandle_SC_%s" % suffix)
        ik_handle_rp = pm.ikHandle(sj=j_ik_rp_root, ee=j_ik_rp_end, name="ikHandle_RP_%s" % suffix, sol="ikRPsolver")

        pm.poleVectorConstraint(self.cont_Pole, ik_handle_rp[0])
        pm.aimConstraint(j_ik_rp_knee, self.cont_Pole)

        ik_handle_ball = pm.ikHandle(sj=j_ik_foot, ee=j_ik_ball, name="ikHandle_Ball_%s" % suffix)
        ik_handle_toe = pm.ikHandle(sj=j_ik_ball, ee=j_ik_toe, name="ikHandle_Toe_%s" % suffix)

        # Create Hierarchy for Foot

        pm.parent(ik_handle_ball[0], pv_ball)
        pm.parent(ik_handle_toe[0], pv_ball)
        pm.parent(master_ik, pv_ball_lean)
        pm.parent(ik_handle_sc[0], master_ik)
        pm.parent(ik_handle_rp[0], master_ik)
        pm.parent(pv_ball_lean_ore, pv_ball_roll)
        pm.parent(pv_ball_ore, pv_toe)
        pm.parent(pv_ball_roll_ore, pv_toe)
        pm.parent(pv_toe_ore, pv_ball_spin)
        pm.parent(pv_ball_spin_ore, pv_heel)
        pm.parent(pv_heel_ore, pv_bank_out)
        pm.parent(pv_bank_out, pv_bank_in)

        #########################################################

        ### Create and constrain Distance Locators

        leg_start = pm.spaceLocator(name="legStart_loc_%s" % suffix)
        pm.pointConstraint(start_lock, leg_start, mo=False)

        leg_end = pm.spaceLocator(name="legEnd_loc_%s" % suffix)
        pm.pointConstraint(master_ik, leg_end, mo=False)

        ### Create Nodes and Connections for Strethchy IK SC

        stretch_offset = pm.createNode("plusMinusAverage", name="stretchOffset_%s" % suffix)
        distance_sc = pm.createNode("distanceBetween", name="distance_SC_%s" % suffix)
        ik_stretch_distance_clamp = pm.createNode("clamp", name="IK_stretch_distanceClamp%s" % suffix)
        ik_stretch_stretchiness_clamp = pm.createNode("clamp", name="IK_stretch_stretchynessClamp%s" % suffix)
        extra_scale_mult_sc = pm.createNode("multiplyDivide", name="extraScaleMult_SC%s" % suffix)
        initial_divide_sc = pm.createNode("multiplyDivide", name="initialDivide_SC_%s" % suffix)
        initial_length_multip_sc = pm.createNode("multiplyDivide", name="initialLengthMultip_SC_%s" % suffix)
        stretch_amount_sc = pm.createNode("multiplyDivide", name="stretchAmount_SC_%s" % suffix)
        sum_of_j_lengths_sc = pm.createNode("plusMinusAverage", name="sumOfJLengths_SC_%s" % suffix)
        # stretch_condition_sc = pm.createNode("condition", name="stretchCondition_SC_%s" % suffix)
        squashiness_sc = pm.createNode("blendColors", name="squashyness_SC_%s" % suffix)
        stretchiness_sc = pm.createNode("blendColors", name="stretchyness_SC_%s" % suffix)

        pm.setAttr("%s.maxR" % ik_stretch_stretchiness_clamp, 1)
        pm.setAttr("%s.input1X" % initial_length_multip_sc, init_upper_leg_dist)
        pm.setAttr("%s.input1Y" % initial_length_multip_sc, init_lower_leg_dist)

        pm.setAttr("%s.operation" % initial_divide_sc, 2)
        # pm.setAttr("%s.operation" % stretch_condition_sc, 2)

        ### IkSoft nodes
        ik_soft_clamp = pm.createNode("clamp", name="ikSoft_clamp_%s" % suffix)
        pm.setAttr("%s.minR" %ik_soft_clamp, 0.0001)
        pm.setAttr("%s.maxR" % ik_soft_clamp, 99999)

        ik_soft_sub1 = pm.createNode("plusMinusAverage", name="ikSoft_Sub1_%s" % suffix)
        pm.setAttr("%s.operation" % ik_soft_sub1, 2)

        ik_soft_sub2 = pm.createNode("plusMinusAverage", name="ikSoft_Sub2_%s" % suffix)
        pm.setAttr("%s.operation" % ik_soft_sub2, 2)

        ik_soft_div1 = pm.createNode("multiplyDivide", name="ikSoft_Div1_%s" % suffix)
        pm.setAttr("%s.operation" % ik_soft_div1, 2)

        ik_soft_mult1 = pm.createNode("multDoubleLinear", name="ikSoft_Mult1_%s" % suffix)
        pm.setAttr("%s.input1" % ik_soft_mult1, -1)


        ik_soft_pow = pm.createNode("multiplyDivide", name="ikSoft_Pow_%s" % suffix)
        pm.setAttr("%s.operation" % ik_soft_pow, 3)
        pm.setAttr("%s.input1X" % ik_soft_pow, 2.718)

        ik_soft_mult2 = pm.createNode("multDoubleLinear", name="ikSoft_Mult2_%s" % suffix)

        ik_soft_sub3 = pm.createNode("plusMinusAverage", name="ikSoft_Sub3_%s" % suffix)
        pm.setAttr("%s.operation" % ik_soft_sub3, 2)

        ik_soft_condition = pm.createNode("condition", name="ikSoft_Condition_%s" % suffix)
        pm.setAttr("%s.operation" % ik_soft_condition, 2)

        ik_soft_div2 = pm.createNode("multiplyDivide", name="ikSoft_Div2_%s" % suffix)
        pm.setAttr("%s.operation" % ik_soft_div2, 2)

        ik_soft_stretch_amount = pm.createNode("multiplyDivide", name="ikSoft_stretchAmount_SC_%s" % suffix)
        pm.setAttr("%s.operation" % ik_soft_stretch_amount, 1)


        ### Bind Attributes and make constraints

        # Bind Stretch Attributes
        leg_start.translate >> distance_sc.point1
        leg_end.translate >> distance_sc.point2
        distance_sc.distance >> ik_stretch_distance_clamp.inputR

        # ik_stretch_distance_clamp.outputR >> stretch_condition_sc.firstTerm
        ik_stretch_distance_clamp.outputR >> initial_divide_sc.input1X
        ik_stretch_stretchiness_clamp.outputR >> stretchiness_sc.blender

        initial_divide_sc.outputX >> stretch_amount_sc.input2X
        initial_divide_sc.outputX >> stretch_amount_sc.input2Y

        initial_length_multip_sc.outputX >> extra_scale_mult_sc.input1X
        initial_length_multip_sc.outputY >> extra_scale_mult_sc.input1Y
        initial_length_multip_sc.outputX >> stretch_offset.input1D[0]
        initial_length_multip_sc.outputY >> stretch_offset.input1D[1]

        extra_scale_mult_sc.outputX >> stretch_amount_sc.input1X
        extra_scale_mult_sc.outputY >> stretch_amount_sc.input1Y
        extra_scale_mult_sc.outputX >> stretchiness_sc.color2R
        extra_scale_mult_sc.outputY >> stretchiness_sc.color2G
        # extra_scale_mult_sc.outputX >> stretch_condition_sc.colorIfFalseR
        # extra_scale_mult_sc.outputY >> stretch_condition_sc.colorIfFalseG
        extra_scale_mult_sc.outputX >> sum_of_j_lengths_sc.input1D[0]
        extra_scale_mult_sc.outputY >> sum_of_j_lengths_sc.input1D[1]

        stretch_amount_sc.outputX >> squashiness_sc.color1R
        stretch_amount_sc.outputY >> squashiness_sc.color1G
        # stretch_amount_sc.outputX >> stretch_condition_sc.colorIfTrueR
        # stretch_amount_sc.outputY >> stretch_condition_sc.colorIfTrueG
        sum_of_j_lengths_sc.output1D >> initial_divide_sc.input2X
        # sum_of_j_lengths_sc.output1D >> stretch_condition_sc.secondTerm
        # stretch_condition_sc.outColorR >> squashyness_sc.color2R
        # stretch_condition_sc.outColorG >> squashyness_sc.color2G
        squashiness_sc.outputR >> stretchiness_sc.color1R
        squashiness_sc.outputG >> stretchiness_sc.color1G
        stretchiness_sc.outputR >> j_ik_sc_knee.translateX
        stretchiness_sc.outputG >> j_ik_sc_end.translateX
        stretchiness_sc.outputR >> j_ik_rp_knee.translateX
        stretchiness_sc.outputG >> j_ik_rp_end.translateX

        ## iksoft related
        self.cont_IK_foot.softIK >> ik_soft_clamp.inputR

        sum_of_j_lengths_sc.output1D >> ik_soft_sub1.input1D[0]
        ik_soft_clamp.outputR >> ik_soft_sub1.input1D[1]

        ik_stretch_distance_clamp.outputR >> ik_soft_sub2.input1D[0]
        ik_soft_sub1.output1D >> ik_soft_sub2.input1D[1]

        ik_soft_sub2.output1D >> ik_soft_div1.input1X
        ik_soft_clamp.outputR >> ik_soft_div1.input2X

        ik_soft_div1.outputX >> ik_soft_mult1.input2

        ik_soft_mult1.output >> ik_soft_pow.input2X

        ik_soft_clamp.outputR >> ik_soft_mult2.input1
        ik_soft_pow.outputX >> ik_soft_mult2.input2

        sum_of_j_lengths_sc.output1D >> ik_soft_sub3.input1D[0]
        ik_soft_mult2.output >> ik_soft_sub3.input1D[1]

        ik_stretch_distance_clamp.outputR >> ik_soft_condition.firstTerm
        ik_soft_sub1.output1D >> ik_soft_condition.secondTerm
        ik_soft_sub3.output1D >> ik_soft_condition.colorIfTrueR
        ik_stretch_distance_clamp.outputR >> ik_soft_condition.colorIfFalseR

        ik_stretch_distance_clamp.outputR >> ik_soft_div2.input1X
        ik_soft_condition.outColorR >> ik_soft_div2.input2X

        extra_scale_mult_sc.outputX >> ik_soft_stretch_amount.input1X
        extra_scale_mult_sc.outputY >> ik_soft_stretch_amount.input1Y
        ik_soft_div2.outputX >> ik_soft_stretch_amount.input2X
        ik_soft_div2.outputX >> ik_soft_stretch_amount.input2Y

        ik_soft_stretch_amount.outputX >> squashiness_sc.color2R
        ik_soft_stretch_amount.outputY >> squashiness_sc.color2G


        ###########################################################





        self.cont_IK_foot.rotate >> j_ik_rp_end.rotate

        # Stretch Attributes Controller connections

        self.cont_IK_foot.sUpLeg >> extra_scale_mult_sc.input2X
        self.cont_IK_foot.sLowLeg >> extra_scale_mult_sc.input2Y
        self.cont_IK_foot.squash >> squashiness_sc.blender

        stretch_offset.output1D >> ik_stretch_distance_clamp.maxR
        # self.cont_IK_foot.stretch >> ik_stretch_stretchyness_clamp.inputR
        self.cont_IK_foot.stretch >> ik_stretch_stretchiness_clamp.inputR
        # self.cont_IK_foot.stretch >> stretch_offset.input1D[2]
        self.cont_IK_foot.stretchLimit >> stretch_offset.input1D[2]

        # Bind Foot Attributes to the controller
        # create multiply nodes for alignment fix
        mult_al_fix_b_lean = pm.createNode("multDoubleLinear", name="multAlFix_bLean_{0}".format(suffix))
        mult_al_fix_b_roll = pm.createNode("multDoubleLinear", name="multAlFix_bRoll_{0}".format(suffix))
        mult_al_fix_b_spin = pm.createNode("multDoubleLinear", name="multAlFix_bSpin_{0}".format(suffix))
        mult_al_fix_h_roll = pm.createNode("multDoubleLinear", name="multAlFix_hRoll_{0}".format(suffix))
        mult_al_fix_h_spin = pm.createNode("multDoubleLinear", name="multAlFix_hSpin_{0}".format(suffix))
        mult_al_fix_t_roll = pm.createNode("multDoubleLinear", name="multAlFix_tRoll_{0}".format(suffix))
        mult_al_fix_t_spin = pm.createNode("multDoubleLinear", name="multAlFix_tSpin_{0}".format(suffix))
        mult_al_fix_t_wiggle = pm.createNode("multDoubleLinear", name="multAlFix_tWiggle_{0}".format(suffix))

        if side == "R":
            mult = -1
        else:
            mult = 1

        pm.setAttr(mult_al_fix_b_lean.input2, mult)
        pm.setAttr(mult_al_fix_b_roll.input2, mult)
        pm.setAttr(mult_al_fix_b_spin.input2, mult)
        # heel roll is an exception. It should be same for each side
        pm.setAttr(mult_al_fix_h_roll.input2, 1)
        pm.setAttr(mult_al_fix_h_spin.input2, mult)
        # toe roll is an exception too.
        pm.setAttr(mult_al_fix_t_roll.input2, 1)
        pm.setAttr(mult_al_fix_t_spin.input2, mult)
        pm.setAttr(mult_al_fix_t_wiggle.input2, mult)

        self.cont_IK_foot.bLean >> mult_al_fix_b_lean.input1
        self.cont_IK_foot.bRoll >> mult_al_fix_b_roll.input1
        self.cont_IK_foot.bSpin >> mult_al_fix_b_spin.input1
        self.cont_IK_foot.hRoll >> mult_al_fix_h_roll.input1
        self.cont_IK_foot.hSpin >> mult_al_fix_h_spin.input1
        self.cont_IK_foot.tRoll >> mult_al_fix_t_roll.input1
        self.cont_IK_foot.tSpin >> mult_al_fix_t_spin.input1
        self.cont_IK_foot.tWiggle >> mult_al_fix_t_wiggle.input1

        mult_al_fix_b_lean.output >> pv_ball_lean.rotateY
        mult_al_fix_b_roll.output >> pv_ball_roll.rotateZ
        mult_al_fix_b_spin.output >> pv_ball_spin.rotateY
        mult_al_fix_h_roll.output >> pv_heel.rotateX
        mult_al_fix_h_spin.output >> pv_heel.rotateY
        mult_al_fix_t_roll.output >> pv_toe.rotateX
        mult_al_fix_t_spin.output >> pv_toe.rotateY
        mult_al_fix_t_wiggle.output >> pv_ball.rotateZ

        # self.cont_IK_foot.bLean >> Pv_BallLean.rotateY
        # self.cont_IK_foot.bRoll >> Pv_BallRoll.rotateZ
        # self.cont_IK_foot.bSpin >> Pv_BallSpin.rotateY
        # self.cont_IK_foot.hRoll >> Pv_Heel.rotateX
        # self.cont_IK_foot.hSpin >> Pv_Heel.rotateY
        # self.cont_IK_foot.tRoll >> Pv_Toe.rotateX
        # self.cont_IK_foot.tSpin >> Pv_Toe.rotateY
        # self.cont_IK_foot.tWiggle >> Pv_Ball.rotateZ
        # // TODO: Reduction possible
        ## create an upper group for bank in to zero out rotations
        pv_bank_in_ore = extra.createUpGrp(pv_bank_in, "ORE")

        if side == "R":
            order = [1, -1]
        else:
            order = [-1, 1]

        pm.setDrivenKeyframe(pv_bank_out.rotateX, cd=self.cont_IK_foot.bank, dv=0, v=0, itt='linear', ott='linear')
        pm.setDrivenKeyframe(pv_bank_out.rotateX, cd=self.cont_IK_foot.bank, dv=90, v=90 * order[1], itt='linear', ott='linear')

        pm.setDrivenKeyframe(pv_bank_in.rotateX, cd=self.cont_IK_foot.bank, dv=0, v=0, itt='linear', ott='linear')
        pm.setDrivenKeyframe(pv_bank_in.rotateX, cd=self.cont_IK_foot.bank, dv=-90, v=90 * order[0], itt='linear', ott='linear')

        #
        # pm.select(Pv_BankOut)
        # pm.setDrivenKeyframe(cd=self.cont_IK_foot.bank, at="rotateX", dv=0, v=0)
        # pm.setDrivenKeyframe(cd=self.cont_IK_foot.bank, at="rotateX", dv=-90, v=90)
        # pm.select(Pv_BankIn)
        # pm.setDrivenKeyframe(cd=self.cont_IK_foot.bank, at="rotateX", dv=0, v=0)
        # pm.setDrivenKeyframe(cd=self.cont_IK_foot.bank, at="rotateX", dv=90, v=-90)

        ik_parent_grp = pm.group(name="IK_parentGRP_%s" % suffix, em=True)
        extra.alignTo(ik_parent_grp, foot_ref, 0)
        pm.parent(pv_bank_in_ore, ik_parent_grp)
        pm.parent(j_ik_foot, ik_parent_grp)

        pm.parentConstraint(j_ik_sc_end, j_ik_foot)

        pm.parentConstraint(self.cont_IK_foot, ik_parent_grp, mo=True)

        # Create Orig Switch (Pole Vector On/Off)

        blend_ore_ik_root = pm.createNode("blendColors", name="blendORE_IK_root_%s" % suffix)
        j_ik_sc_root.rotate >> blend_ore_ik_root.color2
        j_ik_rp_root.rotate >> blend_ore_ik_root.color1
        blend_ore_ik_root.output >> j_ik_orig_root.rotate
        self.cont_IK_foot.polevector >> blend_ore_ik_root.blender

        blend_pos_ik_root = pm.createNode("blendColors", name="blendPOS_IK_root_%s" % suffix)
        j_ik_sc_root.translate >> blend_pos_ik_root.color2
        j_ik_rp_root.translate >> blend_pos_ik_root.color1
        blend_pos_ik_root.output >> j_ik_orig_root.translate
        self.cont_IK_foot.polevector >> blend_pos_ik_root.blender

        blend_ore_ik_knee = pm.createNode("blendColors", name="blendORE_IK_knee_%s" % suffix)
        j_ik_sc_knee.rotate >> blend_ore_ik_knee.color2
        j_ik_rp_knee.rotate >> blend_ore_ik_knee.color1
        # blend_ore_ik_knee.output >> j_ik_orig_knee.rotate
        # Weird bug with skinned character / use seperate connections
        # if there is no skincluster, it works ok, but adding a skin cluster misses 2 out of 3 rotation axis
        # Therefore make SEPERATE CONNECTIONS
        blend_ore_ik_knee.outputR >> j_ik_orig_knee.rotateX
        blend_ore_ik_knee.outputG >> j_ik_orig_knee.rotateY
        blend_ore_ik_knee.outputB >> j_ik_orig_knee.rotateZ
        self.cont_IK_foot.polevector >> blend_ore_ik_knee.blender

        blend_pos_ik_knee = pm.createNode("blendColors", name="blendPOS_IK_knee_%s" % suffix)
        j_ik_sc_knee.translate >> blend_pos_ik_knee.color2
        j_ik_rp_knee.translate >> blend_pos_ik_knee.color1
        blend_pos_ik_knee.output >> j_ik_orig_knee.translate
        self.cont_IK_foot.polevector >> blend_pos_ik_knee.blender

        blend_ore_ik_end = pm.createNode("blendColors", name="blendORE_IK_end_%s" % suffix)
        j_ik_sc_end.rotate >> blend_ore_ik_end.color2
        j_ik_rp_end.rotate >> blend_ore_ik_end.color1
        # blend_ore_ik_end.output >> j_ik_orig_end.rotate
        # Weird bug with skinned character / use seperate connections
        # if there is no skincluster, it works ok, but adding a skin cluster misses 2 out of 3 rotation axis
        # Therefore make SEPERATE CONNECTIONS
        blend_ore_ik_end.outputR >> j_ik_orig_end.rotateX
        blend_ore_ik_end.outputG >> j_ik_orig_end.rotateY
        blend_ore_ik_end.outputB >> j_ik_orig_end.rotateZ
        self.cont_IK_foot.polevector >> blend_ore_ik_end.blender

        blend_pos_ik_end = pm.createNode("blendColors", name="blendPOS_IK_end_%s" % suffix)
        j_ik_sc_end.translate >> blend_pos_ik_end.color2
        j_ik_rp_end.translate >> blend_pos_ik_end.color1
        blend_pos_ik_end.output >> j_ik_orig_end.translate
        self.cont_IK_foot.polevector >> blend_pos_ik_end.blender

        pole_vector_rvs = pm.createNode("reverse", name="poleVector_Rvs_%s" % suffix)
        self.cont_IK_foot.polevector >> pole_vector_rvs.inputX

        self.cont_IK_foot.polevector >> self.cont_Pole.v

        pm.parentConstraint(cont_thigh, self.jDef_legRoot, mo=True, st=("x", "y", "z"))
        pm.pointConstraint(cont_thigh, j_def_hip, mo=True)

        ###########################
        ######### FK LEG ##########
        ###########################



        # extra.alignTo(jfk_root, j_ik_orig_root, mode=2)
        # extra.alignTo(jfk_knee, j_ik_orig_knee, mode=2)
        # extra.alignTo(jfk_foot, j_ik_foot, mode=2)
        # extra.alignTo(jfk_ball, j_ik_ball, mode=2)
        # extra.alignTo(jfk_toe, j_ik_toe, mode=2)

        # extra.orientJoints([jfk_root, jfk_knee, jfk_foot, jfk_ball, jfk_toe], localMoveAxis=(dt.Vector(up_axis)),
        #                    upAxis=up_axis)

        if side == "R":
            pm.parent(jfk_knee, w=True)
            extra.alignTo(jfk_root, j_ik_orig_root, mode=2)
            pm.makeIdentity(jfk_root, a=True)
            pm.parent(jfk_knee, jfk_root)
            extra.orientJoints([jfk_root, jfk_knee, jfk_foot, jfk_ball, jfk_toe], localMoveAxis=-(dt.Vector(up_axis)), upAxis=up_axis)
        else:
            extra.orientJoints([jfk_root, jfk_knee, jfk_foot, jfk_ball, jfk_toe], localMoveAxis=(dt.Vector(up_axis)), upAxis=up_axis)



        # pm.joint(jfk_root, e=True, zso=True, oj="yzx", sao="yup")
        # pm.joint(jfk_knee, e=True, zso=True, oj="yzx", sao="yup")
        # pm.joint(jfk_foot, e=True, zso=True, oj="yzx", sao="yup")
        # pm.joint(jfk_ball, e=True, zso=True, oj="yzx", sao="yup")
        # pm.joint(jfk_toe, e=True, zso=True, oj="yzx", sao="yup")

        cont_fk_up_leg.scaleX >> jfk_root.scaleX
        cont_fk_low_leg.scaleX >> jfk_knee.scaleX
        cont_fk_foot.scaleX >> jfk_foot.scaleX
        cont_fk_ball.scaleX >> jfk_ball.scaleX

        ### CReate Constraints and Hierarchy
        pm.orientConstraint(cont_fk_up_leg, jfk_root, mo=True)
        pm.pointConstraint(start_lock, jfk_root, mo=False)

        pm.orientConstraint(cont_fk_low_leg, jfk_knee, mo=True)
        pm.orientConstraint(cont_fk_foot, jfk_foot, mo=True)
        # pm.orientConstraint(cont_fk_foot, jfk_foot, mo=False)

        ##
        pm.parentConstraint(cont_fk_ball, jfk_ball, mo=True)
        # pm.parentConstraint(cont_fk_ball, jfk_ball, mo=False)
        # extra.alignTo(jfk_toe, toe_pv_ref)

        # pm.parentConstraint(tor)

        pm.parentConstraint(cont_thigh, cont_fk_up_leg_off, sr=("x", "y", "z"), mo=True)
        pm.parentConstraint(cont_fk_up_leg, cont_fk_low_leg_off, mo=True)
        pm.parentConstraint(cont_fk_low_leg, cont_fk_foot_off, mo=True)
        pm.parentConstraint(cont_fk_foot, cont_fk_ball_off, mo=True)

        ### Create FK IK Icon
        # iconScale = (extra.getDistance(footRef, kneeRef)) / 4
        #
        # cont_FK_IK, fk_ik_rvs = icon.fkikSwitch(("cont_FK_IK_" + suffix), (iconScale, iconScale, iconScale))
        #
        # pm.addAttr(cont_FK_IK, shortName="autoTwist", longName="Auto_Twist", defaultValue=1.0, minValue=0.0, maxValue=1.0,
        #            at="float", k=True)
        # pm.addAttr(cont_FK_IK, shortName="manualTwist", longName="Manual_Twist", defaultValue=0.0, at="float", k=True)
        # pm.addAttr(cont_FK_IK, shortName="tweakControls", longName="Tweak_Controls", defaultValue=0, at="bool")
        # pm.setAttr(cont_FK_IK.tweakControls, cb=True)
        # pm.addAttr(cont_FK_IK, shortName="fingerControls", longName="Finger_Controls", defaultValue=0, at="bool")
        # pm.setAttr(cont_FK_IK.fingerControls, cb=True)

        fk_ik_rvs.outputX >> cont_fk_up_leg_ore.visibility
        fk_ik_rvs.outputX >> cont_fk_low_leg_ore.visibility
        fk_ik_rvs.outputX >> cont_fk_foot_ore.visibility
        fk_ik_rvs.outputX >> cont_fk_ball_ore.visibility
        cont_fk_ik.fk_ik >> self.cont_IK_foot.visibility

        cont_fk_ik.fk_ik >> cont_pole_vis.visibility

        # extra.alignAndAim(cont_FK_IK, targetList=[footRef], aimTargetList=[kneeRef], upVector=self.upAxis, rotateOff=(90,90,0))
        #
        # if side == "R":
        #     pm.move(cont_FK_IK, (-(iconScale * 2), 0, 0), r=True, os=True)
        # else:
        #     pm.move(cont_FK_IK, (iconScale * 2, 0, 0), r=True, os=True)
        #
        # cont_FK_IK_POS = extra.createUpGrp(cont_FK_IK, "_POS")
        pm.parent(cont_fk_ik_pos, self.scaleGrp)

        ### Create MidLock controller

        midcont_scale = extra.getDistance(foot_ref, knee_ref) / 3
        cont_mid_lock = icon.star("cont_mid_%s" % suffix, (midcont_scale, midcont_scale, midcont_scale), normal=(0, 1, 0))

        cont_midLock_pos = extra.createUpGrp(cont_mid_lock, "POS")
        cont_midLock_ave = extra.createUpGrp(cont_mid_lock, "AVE")
        extra.alignTo(cont_midLock_pos, knee_ref, 0)

        mid_lock_pa_con_weight = pm.parentConstraint(j_ik_orig_root, jfk_root, cont_midLock_pos, mo=True)
        # cont_FK_IK.fk_ik >> (midLock_paConWeight + "." + jIK_orig_Root + "W0")
        cont_fk_ik.fk_ik >> ("%s.%sW0" % (mid_lock_pa_con_weight, j_ik_orig_root))

        # fk_ik_rvs.outputX >> (midLock_paConWeight + "." + jFK_Root + "W1")
        fk_ik_rvs.outputX >> ("%s.%sW1" % (mid_lock_pa_con_weight, jfk_root))

        cont_fk_ik.interpType >> mid_lock_pa_con_weight.interpType

        mid_lock_po_con_weight = pm.pointConstraint(j_ik_orig_knee, jfk_knee, cont_midLock_ave, mo=False)
        # cont_FK_IK.fk_ik >> (midLock_poConWeight + "." + jIK_orig_Knee + "W0")
        cont_fk_ik.fk_ik >> ("%s.%sW0" % (mid_lock_po_con_weight, j_ik_orig_knee))

        # fk_ik_rvs.outputX >> (midLock_poConWeight + "." + jFK_Knee + "W1")
        fk_ik_rvs.outputX >> ("%s.%sW1" % (mid_lock_po_con_weight, jfk_knee))

        mid_lock_x_bln = pm.createNode("multiplyDivide", name="midLock_xBln%s" % suffix)

        mid_lock_rot_xsw = pm.createNode("blendTwoAttr", name="midLock_rotXsw%s" % suffix)
        j_ik_orig_knee.rotateZ >> mid_lock_rot_xsw.input[0]
        jfk_knee.rotateZ >> mid_lock_rot_xsw.input[1]
        fk_ik_rvs.outputX >> mid_lock_rot_xsw.attributesBlender

        mid_lock_rot_xsw.output >> mid_lock_x_bln.input1Z

        pm.setAttr(mid_lock_x_bln.input2Z, 0.5)
        mid_lock_x_bln.outputZ >> cont_midLock_ave.rotateX

        ### Create Midlock

        mid_lock = pm.spaceLocator(name="midLock_%s" % suffix)
        pm.parentConstraint(mid_lock, j_def_midLeg)
        # pm.scaleConstraint(midLock, jDef_midLeg)
        extra.alignTo(mid_lock, cont_mid_lock, 0)

        pm.parentConstraint(cont_mid_lock, mid_lock, mo=False)
        ### Create End Lock
        end_lock = pm.spaceLocator(name="endLock_%s" % suffix)
        extra.alignTo(end_lock, foot_ref, 2)
        end_lock_ore = extra.createUpGrp(end_lock, "_Ore")
        end_lock_pos = extra.createUpGrp(end_lock, "_Pos")
        end_lock_twist = extra.createUpGrp(end_lock, "_Twist")
        end_lock_weight = pm.pointConstraint(j_ik_orig_end, jfk_foot, end_lock_pos, mo=False)
        # cont_FK_IK.fk_ik >> (endLockWeight + "." + jIK_orig_End + "W0")
        cont_fk_ik.fk_ik >> ("%s.%sW0" % (end_lock_weight, j_ik_orig_end))

        # fk_ik_rvs.outputX >> (endLockWeight + "." + jFK_Foot + "W1")
        fk_ik_rvs.outputX >> ("%s.%sW1" % (end_lock_weight, jfk_foot))

        pm.parentConstraint(end_lock, cont_fk_ik_pos, mo=True)
        pm.parent(end_lock_ore, self.scaleGrp)

        end_lock_rot = pm.parentConstraint(ik_parent_grp, jfk_foot, end_lock, st=("x", "y", "z"), mo=True)
        # pm.setAttr(endLockRot.interpType, 0)
        # cont_FK_IK.fk_ik >> (endLockRot + "." + IK_parentGRP + "W0")
        cont_fk_ik.fk_ik >> ("%s.%sW0" % (end_lock_rot, ik_parent_grp))

        # fk_ik_rvs.outputX >> (endLockRot + "." + jFK_Foot + "W1")
        fk_ik_rvs.outputX >> ("%s.%sW1" % (end_lock_rot, jfk_foot))

        cont_fk_ik.interpType >> end_lock_rot.interpType
        ###################################
        #### CREATE DEFORMATION JOINTS ####
        ###################################

        # UPPERLEG RIBBON

        # ribbon_upper_leg = rc.Ribbon()
        ribbon_upper_leg = rc.PowerRibbon()
        # ribbon_upper_leg.createRibbon(hip_ref, knee_ref, "up_%s" % suffix, -90, connectStartAim=False)
        ribbon_upper_leg.createPowerRibbon(hip_ref, knee_ref, "up_%s" % suffix,  side=side,  orientation=-90, connectStartAim=False, upVector=up_axis)

        ribbon_start_pa_con_upper_leg_start = pm.parentConstraint(start_lock, ribbon_upper_leg.startConnection, mo=True)
        ribbon_start_pa_con_upper_leg_end = pm.parentConstraint(mid_lock, ribbon_upper_leg.endConnection, mo=True)

        # connect the midLeg scaling
        # cont_mid_lock.scale >> ribbon_upper_leg.endConnection.scale
        # cont_mid_lock.scale >> j_def_midLeg.scale

        pm.scaleConstraint(self.scaleGrp, ribbon_upper_leg.scaleGrp)

        # ribbon_start_ori_con = pm.orientConstraint(j_ik_orig_root, jfk_root, ribbon_upper_leg.startAim, mo=False)
        ribbon_start_ori_con = pm.parentConstraint(j_ik_orig_root, jfk_root, ribbon_upper_leg.startAim, mo=True, skipTranslate=["x","y","z"] )
        ribbon_start_ori_con2 = pm.parentConstraint(j_def_hip, ribbon_upper_leg.startAim, mo=True, skipTranslate=["x","y","z"] )
        cont_fk_ik.fk_ik >> ("%s.%sW0" %(ribbon_start_ori_con, j_ik_orig_root))
        fk_ik_rvs.outputX >> ("%s.%sW1" %(ribbon_start_ori_con, jfk_root))

        # cont_fk_ik.alignHip >> ribbon_upper_leg.startAim.blendParent2
        pairBlendNode = pm.listConnections(ribbon_start_ori_con, d=True, t="pairBlend")[0]
        # disconnect the existing weight connection
        pm.disconnectAttr(pairBlendNode.w)
        # re-connect to the custom attribute
        cont_fk_ik.alignHip >> pairBlendNode.w


        # AUTO AND MANUAL TWIST

        # auto
        auto_twist_thigh = pm.createNode("multiplyDivide", name="autoTwistThigh_%s" % suffix)
        cont_fk_ik.upLegAutoTwist >> auto_twist_thigh.input2X
        ribbon_start_pa_con_upper_leg_start.constraintRotate >> auto_twist_thigh.input1

        # !!! The parent constrain override should be disconnected like this
        pm.disconnectAttr(ribbon_start_pa_con_upper_leg_start.constraintRotateX, ribbon_upper_leg.startConnection.rotateX)

        # manual
        add_manual_twist_thigh = pm.createNode("plusMinusAverage", name=("AddManualTwist_UpperLeg_%s" % suffix))
        auto_twist_thigh.output >> add_manual_twist_thigh.input3D[0]
        cont_fk_ik.upLegManualTwist >> add_manual_twist_thigh.input3D[1].input3Dx

        # connect to the joint
        add_manual_twist_thigh.output3D >> ribbon_upper_leg.startConnection.rotate

        # connect allowScaling
        cont_fk_ik.allowScaling >> ribbon_upper_leg.startConnection.scaleSwitch

        # LOWERLEG RIBBON

        # ribbon_lower_leg = rc.Ribbon()
        ribbon_lower_leg = rc.PowerRibbon()
        # ribbon_lower_leg.createRibbon(knee_ref, foot_ref, "low_%s" % suffix, 90)
        ribbon_lower_leg.createPowerRibbon(knee_ref, foot_ref, "low_%s" % suffix, side=side,  orientation=90, upVector=up_axis)

        ribbon_start_pa_con_lower_leg_start = pm.parentConstraint(mid_lock, ribbon_lower_leg.startConnection, mo=True)
        ribbon_start_pa_con_lower_leg_end = pm.parentConstraint(end_lock, ribbon_lower_leg.endConnection, mo=True)

        # connect the midLeg scaling
        # cont_mid_lock.scale >>  ribbon_lower_leg.startConnection.scale

        pm.scaleConstraint(self.scaleGrp, ribbon_lower_leg.scaleGrp)

        # AUTO AND MANUAL TWIST

        # auto
        auto_twist_ankle = pm.createNode("multiplyDivide", name="autoTwistAnkle_%s" % suffix)
        cont_fk_ik.footAutoTwist >> auto_twist_ankle.input2X
        ribbon_start_pa_con_lower_leg_end.constraintRotate >> auto_twist_ankle.input1

        # !!! The parent constrain override should be disconnected like this
        pm.disconnectAttr(ribbon_start_pa_con_lower_leg_end.constraintRotateX, ribbon_lower_leg.endConnection.rotateX)

        # manual
        add_manual_twist_ankle = pm.createNode("plusMinusAverage", name=("AddManualTwist_LowerLeg_%s" % suffix))
        auto_twist_ankle.output >> add_manual_twist_ankle.input3D[0]
        cont_fk_ik.footManualTwist >> add_manual_twist_ankle.input3D[1].input3Dx

        # connect to the joint
        add_manual_twist_ankle.output3D >> ribbon_lower_leg.endConnection.rotate

        # connect allowScaling
        cont_fk_ik.allowScaling >> ribbon_lower_leg.startConnection.scaleSwitch

        # Volume Preservation Stuff
        vpExtraInput = pm.createNode("multiplyDivide", name="vpExtraInput_%s" % suffix)
        pm.setAttr(vpExtraInput.operation, 1)

        vpMidAverage = pm.createNode("plusMinusAverage", name="vpMidAverage_%s" % suffix)
        pm.setAttr(vpMidAverage.operation, 3)

        vpPowerMid = pm.createNode("multiplyDivide", name="vpPowerMid_%s" % suffix)
        pm.setAttr(vpPowerMid.operation, 3)
        vpInitLength = pm.createNode("multiplyDivide", name="vpInitLength_%s" % suffix)
        pm.setAttr(vpInitLength.operation, 2)

        vpPowerUpperLeg = pm.createNode("multiplyDivide", name="vpPowerUpperLeg_%s" % suffix)
        pm.setAttr(vpPowerUpperLeg.operation, 3)

        vpPowerLowerLeg = pm.createNode("multiplyDivide", name="vpPowerLowerLeg_%s" % suffix)
        pm.setAttr(vpPowerLowerLeg.operation, 3)
        #
        vpUpperLowerReduce = pm.createNode("multDoubleLinear", name="vpUpperLowerReduce_%s" % suffix)
        pm.setAttr(vpUpperLowerReduce.input2, 0.5)
        #
        #vp knee branch
        vpExtraInput.output >> ribbon_lower_leg.startConnection.scale
        vpExtraInput.output >> ribbon_upper_leg.endConnection.scale
        vpExtraInput.output >> j_def_midLeg.scale
        cont_mid_lock.scale >> vpExtraInput.input1

        vpMidAverage.output1D >> vpExtraInput.input2X
        vpMidAverage.output1D >> vpExtraInput.input2Y
        vpMidAverage.output1D >> vpExtraInput.input2Z

        vpPowerMid.outputX >> vpMidAverage.input1D[0]
        vpPowerMid.outputY >> vpMidAverage.input1D[1]

        vpInitLength.outputX >> vpPowerMid.input1X
        vpInitLength.outputY >> vpPowerMid.input1Y
        self.cont_IK_foot.volume >> vpPowerMid.input2X
        self.cont_IK_foot.volume >> vpPowerMid.input2Y
        initial_length_multip_sc.outputX >> vpInitLength.input1X
        initial_length_multip_sc.outputY >> vpInitLength.input1Y
        stretchiness_sc.color1R >> vpInitLength.input2X
        stretchiness_sc.color1G >> vpInitLength.input2Y

        #vp upper branch
        mid_off_up = ribbon_upper_leg.middleCont[0].getParent()
        vpPowerUpperLeg.outputX >> mid_off_up.scaleX
        vpPowerUpperLeg.outputX >> mid_off_up.scaleY
        vpPowerUpperLeg.outputX >> mid_off_up.scaleZ

        vpInitLength.outputX >> vpPowerUpperLeg.input1X
        vpUpperLowerReduce.output >> vpPowerUpperLeg.input2X

        # vp lower branch
        mid_off_low = ribbon_lower_leg.middleCont[0].getParent()
        vpPowerLowerLeg.outputX >> mid_off_low.scaleX
        vpPowerLowerLeg.outputX >> mid_off_low.scaleY
        vpPowerLowerLeg.outputX >> mid_off_low.scaleZ

        vpInitLength.outputX >> vpPowerLowerLeg.input1X
        vpUpperLowerReduce.output >> vpPowerLowerLeg.input2X

        self.cont_IK_foot.volume >> vpUpperLowerReduce.input1



        # Foot Joint

        pm.select(d=True)
        j_def_foot = pm.joint(name="jDef_Foot_%s" % suffix, p=foot_pos, radius=1.0)
        self.sockets.append(j_def_foot)
        j_def_ball = pm.joint(name="jDef_Ball_%s" % suffix, p=ball_pos, radius=1.0)
        self.sockets.append(j_def_ball)
        j_def_toe = pm.joint(name="jDef_Toe_%s" % suffix, p=toe_pv_pos, radius=1.0)  # POSSIBLE PROBLEM
        self.sockets.append(j_def_toe)

        foot_pa_con = pm.parentConstraint(j_ik_foot, jfk_foot, j_def_foot, mo=True)
        ball_pa_con = pm.parentConstraint(j_ik_ball, jfk_ball, j_def_ball, mo=False)
        # ball_pa_con = pm.parentConstraint(j_ik_ball, jfk_ball, j_def_ball, mo=True)
        toe_pa_con = pm.parentConstraint(j_ik_toe, jfk_toe, j_def_toe, mo=False)
        # toe_pa_con = pm.parentConstraint(j_ik_toe, jfk_toe, j_def_toe, mo=False)

        # cont_FK_IK.fk_ik >> (foot_paCon + "." + jIK_Foot + "W0")
        cont_fk_ik.fk_ik >> ("%s.%sW0" % (foot_pa_con, j_ik_foot))

        # fk_ik_rvs.outputX >> (foot_paCon + "." + jFK_Foot + "W1")
        fk_ik_rvs.outputX >> ("%s.%sW1" % (foot_pa_con, jfk_foot))

        # cont_FK_IK.fk_ik >> (ball_paCon + "." + jIK_Ball + "W0")
        cont_fk_ik.fk_ik >> ("%s.%sW0" % (ball_pa_con, j_ik_ball))

        # fk_ik_rvs.outputX >> (ball_paCon + "." + jFK_Ball + "W1")
        fk_ik_rvs.outputX >> ("%s.%sW1" % (ball_pa_con, jfk_ball))

        # cont_FK_IK.fk_ik >> (toe_paCon + "." + jIK_Toe + "W0")
        cont_fk_ik.fk_ik >> ("%s.%sW0" % (toe_pa_con, j_ik_toe))

        # fk_ik_rvs.outputX >> (toe_paCon + "." + jFK_Toe + "W1")
        fk_ik_rvs.outputX >> ("%s.%sW1" % (toe_pa_con, jfk_toe))

        cont_fk_ik.interpType >> foot_pa_con.interpType
        cont_fk_ik.interpType >> ball_pa_con.interpType
        cont_fk_ik.interpType >> toe_pa_con.interpType

        # # GOOD PARENTING

        pm.parentConstraint(self.limbPlug, self.scaleGrp, mo=True)

        # Create Master Root and Scale and nonScale Group

        pm.parent(j_ik_sc_root, start_lock)
        pm.parent(j_ik_rp_root, start_lock)
        pm.parent(j_ik_orig_root, start_lock)
        pm.parent(jfk_root, start_lock)

        pm.parent(start_lock_ore, self.scaleGrp)
        pm.parent(leg_start, self.scaleGrp)
        pm.parent(leg_end, self.scaleGrp)
        pm.parent(ik_parent_grp, self.scaleGrp)
        pm.parent(cont_thigh_off, self.scaleGrp)
        pm.parent(cont_fk_up_leg_off, self.scaleGrp)
        pm.parent(cont_fk_low_leg_off, self.scaleGrp)
        pm.parent(cont_fk_foot_off, self.scaleGrp)
        pm.parent(cont_fk_ball_off, self.scaleGrp)
        pm.parent(mid_lock, self.scaleGrp)
        pm.parent(cont_midLock_pos, self.scaleGrp)
        pm.parent(cont_pole_off, self.scaleGrp)
        pm.parent(j_def_midLeg, self.scaleGrp)

        pm.parent(ribbon_upper_leg.scaleGrp, self.nonScaleGrp)
        pm.parent(ribbon_upper_leg.nonScaleGrp, self.nonScaleGrp)

        pm.parent(ribbon_lower_leg.scaleGrp, self.nonScaleGrp)
        pm.parent(ribbon_lower_leg.nonScaleGrp, self.nonScaleGrp)

        pm.parent(j_def_foot, self.scaleGrp)

        pm.parent(self.scaleGrp, self.nonScaleGrp, self.cont_IK_OFF, self.limbGrp)

        ## CONNECT RIG VISIBILITIES

        # Tweak Controls

        tweak_controls = ribbon_upper_leg.middleCont + ribbon_lower_leg.middleCont + [cont_mid_lock]
        for i in tweak_controls:
            cont_fk_ik.tweakControls >> i.v



        nodes_cont_vis = [cont_pole_off, cont_thigh_off, self.cont_IK_OFF , cont_fk_foot_off, cont_midLock_pos, cont_fk_ik_pos,
                        cont_fk_ball_off, cont_fk_low_leg_off, cont_fk_up_leg_off, ribbon_upper_leg.scaleGrp, ribbon_lower_leg.scaleGrp]
        nodes_joint_vis = [j_def_midLeg, j_def_ball, j_def_foot, self.jDef_legRoot, j_def_toe, j_def_hip]
        self.deformerJoints = ribbon_upper_leg.deformerJoints + ribbon_lower_leg.deformerJoints + nodes_joint_vis
        nodes_rig_vis = [end_lock_ore, start_lock_ore, leg_start, leg_end, ik_parent_grp, mid_lock]

        # Cont visibilities
        for i in nodes_cont_vis:
            self.scaleGrp.contVis >> i.v

        # global joint visibilities
        for lst in self.deformerJoints:
            self.scaleGrp.jointVis >> lst.v

        # Rig Visibilities
        for i in nodes_rig_vis:
            self.scaleGrp.rigVis >> i.v
        for i in ribbon_lower_leg.toHide:
            self.scaleGrp.rigVis >> i.v
        for i in ribbon_upper_leg.toHide:
            self.scaleGrp.rigVis >> i.v

        # pm.setAttr(cont_FK_IK.rigVis, 0)

        # # FOOL PROOFING
        extra.lockAndHide(cont_thigh, ["sx", "sy", "sz", "v"])
        extra.lockAndHide(self.cont_IK_foot, ["sx", "sy", "sz", "v"])
        extra.lockAndHide(self.cont_Pole, ["rx", "ry", "rz", "sx", "sy", "sz", "v"])
        extra.lockAndHide(cont_fk_ik, ["sx", "sy", "sz", "v"])
        extra.lockAndHide(cont_fk_up_leg, ["tx", "ty", "tz", "sy", "sz", "v"])
        extra.lockAndHide(cont_fk_low_leg, ["tx", "ty", "tz", "sy", "sz", "v"])
        extra.lockAndHide(cont_fk_foot, ["tx", "ty", "tz", "sy", "sz", "v"])
        extra.lockAndHide(cont_fk_ball, ["tx", "ty", "tz", "sy", "sz", "v"])

        # # COLOR CODING

        extra.colorize(cont_thigh, self.colorCodes[0])
        extra.colorize(self.cont_IK_foot, self.colorCodes[0])
        extra.colorize(cont_fk_ik, self.colorCodes[0])
        extra.colorize(cont_fk_up_leg, self.colorCodes[0])
        extra.colorize(cont_fk_low_leg, self.colorCodes[0])
        extra.colorize(cont_fk_foot, self.colorCodes[0])
        extra.colorize(cont_fk_ball, self.colorCodes[0])
        extra.colorize(self.cont_Pole, self.colorCodes[0])
        extra.colorize(cont_mid_lock, self.colorCodes[1])
        extra.colorize(ribbon_upper_leg.middleCont, self.colorCodes[1])
        extra.colorize(ribbon_lower_leg.middleCont, self.colorCodes[1])

        extra.colorize(self.deformerJoints, self.colorCodes[0], shape=False)

        # # GOOD RIDDANCE
        pm.delete(foot_plane)

        # return
        self.scaleConstraints = [self.scaleGrp, self.cont_IK_OFF ]
        self.anchors = [(self.cont_IK_foot, "parent", 1, None), (self.cont_Pole, "parent", 1, None)]
        # self.cont_IK_OFF = cont_ik_foot_off
        pm.makeIdentity(self.cont_IK_foot, a=True, t=True, r=False, s=False)