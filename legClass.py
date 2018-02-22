import pymel.core as pm
import extraProcedures as extra
import ribbonClass as rc
import contIcons as icon

reload(extra)
reload(rc)
reload(icon)

class Leg(object):
    def __init__(self):
        # none = None
        self.limbGrp = None
        self.scaleGrp = None
        self.cont_IK_foot = None
        self.cont_Pole = None
        self.nonScaleGrp = None
        # cont_IK_foot_OFF = None
        self.cont_IK_OFF = None
        self.sockets = []
        # startSocket = None
        # endSocket = None
        self.limbPlug = None
        self.connectsTo = None
        self.scaleConstraints = []
        self.anchors = []
        self.anchorLocations = []
        self.jDef_legRoot = None
        self.deformerJoints = []
        self.colorCodes = [6, 18]

    def createleg(self, leginits, suffix="", side="L"):
        # suffix = (extra.uniqueName("scaleGrp_%s" % suffix)).replace("scaleGrp_", "")
        suffix = (extra.uniqueName("limbGrp_%s" % suffix)).replace("limbGrp_", "")

        self.limbGrp = pm.group(name="limbGrp_%s" % suffix, em=True)


        if len(leginits) < 9:
            pm.error("Some or all Leg Init Bones are missing (or Renamed)")
            return

        if not type(leginits) == dict and not type(leginits) == list:
            pm.error("Init joints must be list or dictionary")
            return

        # reinitialize the dictionary for easy use
        if type(leginits) == dict:
            leg_root_ref = leginits["LegRoot"]
            hip_ref = leginits["Hip"]
            knee_ref = leginits["Knee"]
            foot_ref = leginits["Foot"]
            ball_ref = leginits["Ball"]
            heel_pv_ref = leginits["HeelPV"]
            toe_pv_ref = leginits["ToePV"]
            bank_in_ref = leginits["BankIN"]
            bank_out_ref = leginits["BankOUT"]
        else:
            leg_root_ref = leginits[0]
            hip_ref = leginits[1]
            knee_ref = leginits[2]
            foot_ref = leginits[3]
            ball_ref = leginits[4]
            heel_pv_ref = leginits[5]
            toe_pv_ref = leginits[6]
            bank_in_ref = leginits[7]
            bank_out_ref = leginits[8]

        up_axis = extra.getRigAxes(leg_root_ref)[0]

        # find the Socket
        self.connectsTo = leg_root_ref.getParent()

        leg_root_pos = leg_root_ref.getTranslation(space="world")
        hip_pos = hip_ref.getTranslation(space="world")
        knee_pos = knee_ref.getTranslation(space="world")
        foot_pos = foot_ref.getTranslation(space="world")
        ball_pos = ball_ref.getTranslation(space="world")
        # heel_pv_pos = heel_pv_ref.getTranslation(space="world")
        toe_pv_pos = toe_pv_ref.getTranslation(space="world")
        # bank_in_pos = bank_in_ref.getTranslation(space="world")
        # bank_out_pos = bank_out_ref.getTranslation(space="world")

        init_upper_leg_dist = extra.getDistance(hip_ref, knee_ref)
        init_lower_leg_dist = extra.getDistance(knee_ref, foot_ref)
        init_ball_dist = extra.getDistance(foot_ref, ball_ref)
        init_toe_dist = extra.getDistance(ball_ref, toe_pv_ref)
        init_foot_length = extra.getDistance(toe_pv_ref, heel_pv_ref)
        init_foot_width = extra.getDistance(bank_in_ref, bank_out_ref)

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

        # Thigh Controller

        thigh_cont_scale = (init_upper_leg_dist / 4, init_upper_leg_dist / 16, init_upper_leg_dist / 4)
        cont_thigh = icon.cube("cont_Thigh_%s" % suffix, thigh_cont_scale)
        extra.alignAndAim(cont_thigh, targetList=[hip_ref], aimTargetList=[knee_ref], upObject=leg_root_ref)
        pm.move(cont_thigh, (0, -thigh_cont_scale[0] * 2, 0), r=True, os=True)

        cont_thigh_off = extra.createUpGrp(cont_thigh, "OFF")
        cont_thigh_ore = extra.createUpGrp(cont_thigh, "ORE")
        if side == "R":
            pm.setAttr(cont_thigh_ore.rotateZ, -180)

        pm.xform(cont_thigh, piv=leg_root_pos, ws=True)
        pm.addAttr(shortName="autoTwist", longName="Auto_Twist", defaultValue=1.0, minValue=0.0, maxValue=1.0, at="float",
                   k=True)
        pm.addAttr(shortName="manualTwist", longName="Manual_Twist", defaultValue=0.0, at="float", k=True)

        # IK Foot Controller

        foot_cont_scale = (init_foot_length * 0.75, 1, init_foot_width * 0.8)
        self.cont_IK_foot = icon.circle("cont_IK_foot_%s" % suffix, scale=foot_cont_scale, normal=(0, 1, 0))
        extra.alignAndAim(self.cont_IK_foot, targetList=[bank_out_ref, bank_in_ref, toe_pv_ref, heel_pv_ref], aimTargetList=[toe_pv_ref], upObject=foot_ref)
        pm.xform(self.cont_IK_foot, piv=foot_pos, ws=True)

        self.cont_IK_OFF  = extra.createUpGrp(self.cont_IK_foot, "OFF")


        pm.addAttr(self.cont_IK_foot, shortName="polevector", longName="Pole_Vector", defaultValue=0.0, minValue=0.0, maxValue=1.0,
                   at="double", k=True)
        pm.addAttr(self.cont_IK_foot, shortName="sUpLeg", longName="Scale_Upper_Leg", defaultValue=1.0, minValue=0.0, at="double", k=True)
        pm.addAttr(self.cont_IK_foot, shortName="sLowLeg", longName="Scale_Lower_Leg", defaultValue=1.0, minValue=0.0, at="double", k=True)
        pm.addAttr(self.cont_IK_foot, shortName="squash", longName="Squash", defaultValue=0.0, minValue=0.0, maxValue=1.0, at="double", k=True)
        pm.addAttr(self.cont_IK_foot, shortName="stretch", longName="Stretch", defaultValue=100.0, minValue=0.0, maxValue=100.0, at="double",
                   k=True)
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
        polecont_scale = ((((init_upper_leg_dist + init_lower_leg_dist) / 2) / 10), (((init_upper_leg_dist + init_lower_leg_dist) / 2) / 10), (((init_upper_leg_dist + init_lower_leg_dist) / 2) / 10))
        self.cont_Pole = icon.plus("cont_Pole_%s" % suffix, polecont_scale, normal=(0, 0, 1))
        offset_mag_pole = ((init_upper_leg_dist + init_lower_leg_dist) / 4)
        offset_vector_pole = extra.getBetweenVector(knee_ref, [hip_ref, foot_ref])
        extra.alignAndAim(self.cont_Pole, targetList=[knee_ref], aimTargetList=[hip_ref, foot_ref], upVector=up_axis, translateOff=(offset_vector_pole * offset_mag_pole))
        cont_pole_off = extra.createUpGrp(self.cont_Pole, "OFF")

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

        pm.addAttr(cont_fk_ik, shortName="autoTwist", longName="Auto_Twist", defaultValue=1.0, minValue=0.0, maxValue=1.0,
                   at="float", k=True)
        pm.addAttr(cont_fk_ik, shortName="manualTwist", longName="Manual_Twist", defaultValue=0.0, at="float", k=True)
        pm.addAttr(cont_fk_ik, at="enum", k=True, shortName="interpType", longName="Interp_Type", en="No_Flip:Average:Shortest:Longest:Cache", defaultValue=0)
        pm.addAttr(cont_fk_ik, shortName="tweakControls", longName="Tweak_Controls", defaultValue=0, at="bool")
        pm.setAttr(cont_fk_ik.tweakControls, cb=True)
        pm.addAttr(cont_fk_ik, shortName="fingerControls", longName="Finger_Controls", defaultValue=1, at="bool")
        pm.setAttr(cont_fk_ik.fingerControls, cb=True)

        ###########################################################################################################################

        # Groups
        self.scaleGrp = pm.group(name="scaleGrp_%s" % suffix, em=True)
        extra.alignTo(self.scaleGrp, leg_root_ref, 0)
        self.nonScaleGrp = pm.group(name="NonScaleGrp_%s" % suffix, em=True)

        # Create Limb Plug
        pm.select(d=True)
        self.limbPlug = pm.joint(name="limbPlug_%s" % suffix, p=leg_root_pos, radius=3)

        # Create common Joints
        pm.select(d=True)
        j_def_midLeg = pm.joint(name="jDef_knee_%s" % suffix, p=knee_pos, radius=1.5)
        self.sockets.append(j_def_midLeg)
        pm.select(d=True)
        self.jDef_legRoot = pm.joint(name="jDef_legRoot_%s" % suffix, p=leg_root_pos, radius=1.5)
        self.sockets.append(self.jDef_legRoot)
        j_def_hip = pm.joint(name="jDef_hip_%s" % suffix, p=hip_pos, radius=1.5)
        pm.joint(self.jDef_legRoot, e=True, zso=True, oj="xyz")
        pm.joint(j_def_hip, e=True, zso=True, oj="xyz")
        pm.parent(self.jDef_legRoot, self.scaleGrp)

        ###########################
        ######### IK LEG ##########
        ###########################

        master_ik = pm.spaceLocator(name="masterIK_" + suffix)
        extra.alignTo(master_ik, foot_ref)

        pm.select(d=True)
        j_ik_orig_root = pm.joint(name="jIK_orig_Root_%s" % suffix, p=hip_pos, radius=1.5)
        j_ik_orig_knee = pm.joint(name="jIK_orig_Knee_%s" % suffix, p=knee_pos, radius=1.5)
        j_ik_orig_end = pm.joint(name="jIK_orig_End_%s" % suffix, p=foot_pos, radius=1.5)
        pm.select(d=True)
        j_ik_sc_root = pm.joint(name="jIK_SC_Root_%s" % suffix, p=hip_pos, radius=1)
        j_ik_sc_knee = pm.joint(name="jIK_SC_Knee_%s" % suffix, p=knee_pos, radius=1)
        j_ik_sc_end = pm.joint(name="jIK_SC_End_%s" % suffix, p=foot_pos, radius=1)
        pm.select(d=True)
        j_ik_rp_root = pm.joint(name="jIK_RP_Root_%s" % suffix, p=hip_pos, radius=0.7)
        j_ik_rp_knee = pm.joint(name="jIK_RP_Knee_%s" % suffix, p=knee_pos, radius=0.7)
        j_ik_rp_end = pm.joint(name="jIK_RP_End_%s" % suffix, p=foot_pos, radius=0.7)
        pm.select(d=True)
        j_ik_foot = pm.joint(name="jIK_Foot_%s" % suffix, p=foot_pos, radius=1.0)
        j_ik_ball = pm.joint(name="jIK_Ball_%s" % suffix, p=ball_pos, radius=1.0)
        j_ik_toe = pm.joint(name="jIK_Toe_%s" % suffix, p=toe_pv_pos,  # POSSIBLE PROBLEM
                           radius=1.0)

        pm.joint(j_ik_orig_root, e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(j_ik_orig_knee, e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(j_ik_orig_end, e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(j_ik_sc_root, e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(j_ik_sc_knee, e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(j_ik_sc_end, e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(j_ik_rp_root, e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(j_ik_rp_knee, e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(j_ik_rp_end, e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(j_ik_foot, e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(j_ik_ball, e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(j_ik_toe, e=True, zso=True, oj="xyz", sao="yup")

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
        ik_stretch_stretchyness_clamp = pm.createNode("clamp", name="IK_stretch_stretchynessClamp%s" % suffix)
        extra_scale_mult_sc = pm.createNode("multiplyDivide", name="extraScaleMult_SC%s" % suffix)
        initial_divide_sc = pm.createNode("multiplyDivide", name="initialDivide_SC_%s" % suffix)
        initial_length_multip_sc = pm.createNode("multiplyDivide", name="initialLengthMultip_SC_%s" % suffix)
        stretch_amount_sc = pm.createNode("multiplyDivide", name="stretchAmount_SC_%s" % suffix)
        sum_of_j_lengths_sc = pm.createNode("plusMinusAverage", name="sumOfJLengths_SC_%s" % suffix)
        stretch_condition_sc = pm.createNode("condition", name="stretchCondition_SC_%s" % suffix)
        squashyness_sc = pm.createNode("blendColors", name="squashyness_SC_%s" % suffix)
        stretchyness_sc = pm.createNode("blendColors", name="stretchyness_SC_%s" % suffix)

        pm.setAttr("%s.maxR" % ik_stretch_stretchyness_clamp, 1)
        pm.setAttr("%s.input1X" % initial_length_multip_sc, init_upper_leg_dist)
        pm.setAttr("%s.input1Y" % initial_length_multip_sc, init_lower_leg_dist)

        pm.setAttr("%s.operation" % initial_divide_sc, 2)
        pm.setAttr("%s.operation" % stretch_condition_sc, 2)

        ### Bind Attributes and make constraints

        # Bind Stretch Attributes
        leg_start.translate >> distance_sc.point1
        leg_end.translate >> distance_sc.point2
        distance_sc.distance >> ik_stretch_distance_clamp.inputR

        ik_stretch_distance_clamp.outputR >> stretch_condition_sc.firstTerm
        ik_stretch_distance_clamp.outputR >> initial_divide_sc.input1X
        ik_stretch_stretchyness_clamp.outputR >> stretchyness_sc.blender

        initial_divide_sc.outputX >> stretch_amount_sc.input2X
        initial_divide_sc.outputX >> stretch_amount_sc.input2Y

        initial_length_multip_sc.outputX >> extra_scale_mult_sc.input1X
        initial_length_multip_sc.outputY >> extra_scale_mult_sc.input1Y
        initial_length_multip_sc.outputX >> stretch_offset.input1D[0]
        initial_length_multip_sc.outputY >> stretch_offset.input1D[1]

        extra_scale_mult_sc.outputX >> stretch_amount_sc.input1X
        extra_scale_mult_sc.outputY >> stretch_amount_sc.input1Y
        extra_scale_mult_sc.outputX >> stretchyness_sc.color2R
        extra_scale_mult_sc.outputY >> stretchyness_sc.color2G
        extra_scale_mult_sc.outputX >> stretch_condition_sc.colorIfFalseR
        extra_scale_mult_sc.outputY >> stretch_condition_sc.colorIfFalseG
        extra_scale_mult_sc.outputX >> sum_of_j_lengths_sc.input1D[0]
        extra_scale_mult_sc.outputY >> sum_of_j_lengths_sc.input1D[1]

        stretch_amount_sc.outputX >> squashyness_sc.color1R
        stretch_amount_sc.outputY >> squashyness_sc.color1G
        stretch_amount_sc.outputX >> stretch_condition_sc.colorIfTrueR
        stretch_amount_sc.outputY >> stretch_condition_sc.colorIfTrueG
        sum_of_j_lengths_sc.output1D >> initial_divide_sc.input2X
        sum_of_j_lengths_sc.output1D >> stretch_condition_sc.secondTerm
        stretch_condition_sc.outColorR >> squashyness_sc.color2R
        stretch_condition_sc.outColorG >> squashyness_sc.color2G
        squashyness_sc.outputR >> stretchyness_sc.color1R
        squashyness_sc.outputG >> stretchyness_sc.color1G
        stretchyness_sc.outputR >> j_ik_sc_knee.translateX
        stretchyness_sc.outputG >> j_ik_sc_end.translateX
        stretchyness_sc.outputR >> j_ik_rp_knee.translateX
        stretchyness_sc.outputG >> j_ik_rp_end.translateX

        ###########################################################

        self.cont_IK_foot.rotate >> j_ik_rp_end.rotate

        # Stretch Attributes Controller connections

        self.cont_IK_foot.sUpLeg >> extra_scale_mult_sc.input2X
        self.cont_IK_foot.sLowLeg >> extra_scale_mult_sc.input2Y
        self.cont_IK_foot.squash >> squashyness_sc.blender

        stretch_offset.output1D >> ik_stretch_distance_clamp.maxR
        self.cont_IK_foot.stretch >> ik_stretch_stretchyness_clamp.inputR
        self.cont_IK_foot.stretch >> stretch_offset.input1D[2]

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
        blend_ore_ik_knee.output >> j_ik_orig_knee.rotate
        self.cont_IK_foot.polevector >> blend_ore_ik_knee.blender

        blend_pos_ik_knee = pm.createNode("blendColors", name="blendPOS_IK_knee_%s" % suffix)
        j_ik_sc_knee.translate >> blend_pos_ik_knee.color2
        j_ik_rp_knee.translate >> blend_pos_ik_knee.color1
        blend_pos_ik_knee.output >> j_ik_orig_knee.translate
        self.cont_IK_foot.polevector >> blend_pos_ik_knee.blender

        blend_ore_ik_end = pm.createNode("blendColors", name="blendORE_IK_end_%s" % suffix)
        j_ik_sc_end.rotate >> blend_ore_ik_end.color2
        j_ik_rp_end.rotate >> blend_ore_ik_end.color1
        blend_ore_ik_end.output >> j_ik_orig_end.rotate
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

        pm.select(d=True)
        jfk_root = pm.joint(name="jFK_UpLeg_%s" % suffix, p=hip_pos, radius=1.0)
        jfk_knee = pm.joint(name="jFK_Knee_%s" % suffix, p=knee_pos, radius=1.0)
        jfk_foot = pm.joint(name="jFK_Foot_%s" % suffix, p=foot_pos, radius=1.0)
        jfk_ball = pm.joint(name="jFK_Ball_%s" % suffix, p=ball_pos, radius=1.0)
        jfk_toe = pm.joint(name="jFK_Toe_%s" % suffix, p=toe_pv_pos, radius=1.0)

        pm.joint(jfk_root, e=True, zso=True, oj="yzx", sao="yup")
        pm.joint(jfk_knee, e=True, zso=True, oj="yzx", sao="yup")
        pm.joint(jfk_foot, e=True, zso=True, oj="yzx", sao="yup")
        pm.joint(jfk_ball, e=True, zso=True, oj="yzx", sao="yup")
        pm.joint(jfk_toe, e=True, zso=True, oj="yzx", sao="yup")

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
        pm.parentConstraint(cont_fk_ball, jfk_ball, mo=True)
        # pm.parentConstraint(cont_fk_ball, jfk_ball, mo=False)

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

        ribbon_upper_leg = rc.Ribbon()
        ribbon_upper_leg.createRibbon(hip_ref, knee_ref, "up_%s" % suffix, -90, connectStartAim=False)

        ribbon_start_pa_con_upper_leg_start = pm.parentConstraint(start_lock, ribbon_upper_leg.startConnection, mo=True)
        ribbon_start_pa_con_upper_leg_end = pm.parentConstraint(mid_lock, ribbon_upper_leg.endConnection, mo=True)

        pm.scaleConstraint(self.scaleGrp, ribbon_upper_leg.scaleGrp)

        # ribbon_start_ori_con = pm.orientConstraint(j_ik_orig_root, jfk_root, ribbon_upper_leg.startAim, mo=False)
        ribbon_start_ori_con = pm.parentConstraint(j_ik_orig_root, jfk_root, ribbon_upper_leg.startAim, mo=True, skipTranslate=["x","y","z"] )
        cont_fk_ik.fk_ik >> ("%s.%sW0" %(ribbon_start_ori_con, j_ik_orig_root))
        fk_ik_rvs.outputX >> ("%s.%sW1" %(ribbon_start_ori_con, jfk_root))

        # AUTO AND MANUAL TWIST

        # auto
        auto_twist_thigh = pm.createNode("multiplyDivide", name="autoTwistThigh_%s" % suffix)
        cont_thigh.autoTwist >> auto_twist_thigh.input2X
        ribbon_start_pa_con_upper_leg_start.constraintRotate >> auto_twist_thigh.input1

        # !!! The parent constrain override should be disconnected like this
        pm.disconnectAttr(ribbon_start_pa_con_upper_leg_start.constraintRotateX, ribbon_upper_leg.startConnection.rotateX)

        # manual
        add_manual_twist_thigh = pm.createNode("plusMinusAverage", name=("AddManualTwist_UpperLeg_%s" % suffix))
        auto_twist_thigh.output >> add_manual_twist_thigh.input3D[0]
        cont_thigh.manualTwist >> add_manual_twist_thigh.input3D[1].input3Dx

        # connect to the joint
        add_manual_twist_thigh.output3D >> ribbon_upper_leg.startConnection.rotate

        # LOWERLEG RIBBON

        ribbon_lower_leg = rc.Ribbon()
        ribbon_lower_leg.createRibbon(knee_ref, foot_ref, "low_%s" % suffix, 90)

        ribbon_start_pa_con_lower_leg_start = pm.parentConstraint(mid_lock, ribbon_lower_leg.startConnection, mo=True)
        ribbon_start_pa_con_lower_leg_end = pm.parentConstraint(end_lock, ribbon_lower_leg.endConnection, mo=True)

        pm.scaleConstraint(self.scaleGrp, ribbon_lower_leg.scaleGrp)

        # AUTO AND MANUAL TWIST

        # auto
        auto_twist_ankle = pm.createNode("multiplyDivide", name="autoTwistAnkle_%s" % suffix)
        cont_fk_ik.autoTwist >> auto_twist_ankle.input2X
        ribbon_start_pa_con_lower_leg_end.constraintRotate >> auto_twist_ankle.input1

        # !!! The parent constrain override should be disconnected like this
        pm.disconnectAttr(ribbon_start_pa_con_lower_leg_end.constraintRotateX, ribbon_lower_leg.endConnection.rotateX)

        # manual
        add_manual_twist_ankle = pm.createNode("plusMinusAverage", name=("AddManualTwist_LowerLeg_%s" % suffix))
        auto_twist_ankle.output >> add_manual_twist_ankle.input3D[0]
        cont_fk_ik.manualTwist >> add_manual_twist_ankle.input3D[1].input3Dx

        # connect to the joint
        add_manual_twist_ankle.output3D >> ribbon_lower_leg.endConnection.rotate

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
        toe_pa_con = pm.parentConstraint(j_ik_toe, jfk_toe, j_def_toe, mo=False)

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

        tweak_controls = (ribbon_upper_leg.middleCont, ribbon_lower_leg.middleCont, cont_mid_lock)
        for i in tweak_controls:
            cont_fk_ik.tweakControls >> i.v

        pm.addAttr(self.scaleGrp, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True)
        pm.addAttr(self.scaleGrp, at="bool", ln="Joints_Visibility", sn="jointVis", defaultValue=True)
        pm.addAttr(self.scaleGrp, at="bool", ln="Rig_Visibility", sn="rigVis", defaultValue=False)
        # make the created attributes visible in the channelbox
        pm.setAttr(self.scaleGrp.contVis, cb=True)
        pm.setAttr(self.scaleGrp.jointVis, cb=True)
        pm.setAttr(self.scaleGrp.rigVis, cb=True)

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

        self.scaleConstraints = [self.scaleGrp, self.cont_IK_OFF ]
        self.anchors = [(self.cont_IK_foot, "parent", 1, None), (self.cont_Pole, "parent", 1, None)]
        # self.cont_IK_OFF = cont_ik_foot_off
