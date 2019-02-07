import pymel.core as pm
import extraProcedures as extra
# import ribbonClass as rc
import powerRibbon as rc
import contIcons as icon
import pymel.core.datatypes as dt

reload(extra)
reload(rc)
reload(icon)


###########################
######### IK ARM ##########
###########################
class Arm(object):
    def __init__(self):
        self.limbGrp = None
        self.sockets = []
        self.scaleGrp = None
        self.nonScaleGrp = None
        self.cont_IK_hand = None
        # cont_IK_hand_OFF = None
        self.cont_IK_OFF = None
        self.rootSocket = None
        self.cont_Pole = None
        self.nodesContVis = None
        self.limbPlug = None
        self.scaleConstraints = []
        self.anchors = []
        self.anchorLocations = []
        self.j_def_collar = None
        self.deformerJoints = []
        self.colorCodes = [6, 18]
        ## get the up axis

    ## This is a joint node and should be parented to another joint.
    def createarm(self, arminits, suffix="", side="L"):
        ## create an unique suffix
        suffix = (extra.uniqueName("limbGrp_%s" % suffix)).replace("limbGrp_", "")
        self.limbGrp = pm.group(name="limbGrp_%s" % suffix, em=True)

        if len(arminits) < 4:
            pm.error("Missing Joints for Arm Setup")
            return

        if not type(arminits) == dict and not type(arminits) == list:
            pm.error("Init joints must be list or dictionary")
            return

        if type(arminits) == dict:
            # reinitialize the dictionary for easy use
            collar_ref = arminits["Collar"]
            shoulder_ref = arminits["Shoulder"]
            elbow_ref = arminits["Elbow"]
            hand_ref = arminits["Hand"]
        else:
            collar_ref = arminits[0]
            shoulder_ref = arminits[1]
            elbow_ref = arminits[2]
            hand_ref = arminits[3]

        if side == "R":
            sideMult = -1
        else:
            sideMult = 1

        up_axis, mirror_axis, look_axis = extra.getRigAxes(collar_ref)

        # Groups
        self.scaleGrp = pm.group(name="scaleGrp_%s" % suffix, em=True)
        extra.alignTo(self.scaleGrp, collar_ref, 0)
        self.nonScaleGrp = pm.group(name="NonScaleGrp_%s" % suffix, em=True)

        master_root = pm.group(em=True, name="masterRoot_%s" % suffix)
        extra.alignTo(master_root, collar_ref, 0)
        pm.makeIdentity(a=True)

        master_ik = pm.spaceLocator(name="masterIK_%s" % suffix)
        extra.alignTo(master_ik, hand_ref, 0)

        collar_pos = collar_ref.getTranslation(space="world")
        shoulder_pos = shoulder_ref.getTranslation(space="world")
        elbow_pos = elbow_ref.getTranslation(space="world")
        hand_pos = hand_ref.getTranslation(space="world")
        init_shoulder_dist = extra.getDistance(collar_ref, shoulder_ref)
        init_upper_arm_dist = extra.getDistance(shoulder_ref, elbow_ref)
        init_lower_arm_dist = extra.getDistance(elbow_ref, hand_ref)

        root_position = hand_ref.getTranslation(space="world")

        # -------------------------------------------
        # create JOINTS with proper orientation
        # -------------------------------------------

        # Create Limb Plug
        pm.select(d=True)
        self.limbPlug = pm.joint(name="jPlug_%s" % suffix, p=collar_pos, radius=3)

        # Shoulder Joints
        pm.select(d=True)
        self.j_def_collar = pm.joint(name="jDef_Collar_%s" % suffix, p=collar_pos, radius=1.5)
        self.sockets.append(self.j_def_collar)
        j_collar_end = pm.joint(name="j_CollarEnd_%s" % suffix, p=shoulder_pos, radius=1.5)
        self.sockets.append(j_collar_end)

        extra.orientJoints([self.j_def_collar, j_collar_end], localMoveAxis=(dt.Vector(up_axis)),
                           mirrorAxis=(sideMult, 0.0, 0.0), upAxis=sideMult*(dt.Vector(up_axis)))

        pm.select(d=True)
        j_def_elbow = pm.joint(name="jDef_elbow_%s" % suffix, p=elbow_pos, radius=1.5)
        self.sockets.append(j_def_elbow)

        # ---------
        # IK Joints
        # ---------

        # Follow IK Chain

        pm.select(d=True)
        j_ik_orig_up = pm.joint(name="jIK_orig_Up_%s" % suffix, p=shoulder_pos, radius=0.5)
        j_ik_orig_low = pm.joint(name="jIK_orig_Low_%s" % suffix, p=elbow_pos, radius=0.5)
        j_ik_orig_low_end = pm.joint(name="jIK_orig_LowEnd_%s" % suffix, p=hand_pos, radius=0.5)

        # Single Chain IK

        pm.select(d=True)
        j_ik_sc_up = pm.joint(name="jIK_SC_Up_%s" % suffix, p=shoulder_pos, radius=1.0)
        j_ik_sc_low = pm.joint(name="jIK_SC_Low_%s" % suffix, p=elbow_pos, radius=1.0)
        j_ik_sc_low_end = pm.joint(name="jIK_SC_LowEnd_%s" % suffix, p=hand_pos, radius=1)

        # Rotate Plane IK

        pm.select(d=True)
        j_ik_rp_up = pm.joint(name="jIK_RP_Up_%s" % suffix, p=shoulder_pos, radius=1.5)
        j_ik_rp_low = pm.joint(name="jIK_RP_Low_%s" % suffix, p=elbow_pos, radius=1.5)
        j_ik_rp_low_end = pm.joint(name="jIK_RP_LowEnd_%s" % suffix, p=hand_pos, radius=1.5)

        pm.select(d=True)

        # orientations

        extra.orientJoints([j_ik_orig_up, j_ik_orig_low, j_ik_orig_low_end], localMoveAxis=(dt.Vector(up_axis)),
                           mirrorAxis=(sideMult, 0.0, 0.0), upAxis=sideMult*(dt.Vector(up_axis)))

        extra.orientJoints([j_ik_sc_up, j_ik_sc_low, j_ik_sc_low_end], localMoveAxis=(dt.Vector(up_axis)),
                           mirrorAxis=(sideMult, 0.0, 0.0), upAxis=sideMult*(dt.Vector(up_axis)))

        extra.orientJoints([j_ik_rp_up, j_ik_rp_low, j_ik_rp_low_end], localMoveAxis=(dt.Vector(up_axis)),
                           mirrorAxis=(sideMult, 0.0, 0.0), upAxis=sideMult*(dt.Vector(up_axis)))

        # extra.orientJoints([j_ik_orig_up, j_ik_orig_low, j_ik_orig_low_end], localMoveAxis=(dt.Vector(up_axis)),
        #                    mirrorAxis=(1.0, 0.0, 0.0), upAxis=(dt.Vector(up_axis)))
        # extra.orientJoints([j_ik_sc_up, j_ik_sc_low, j_ik_sc_low_end], localMoveAxis=(dt.Vector(up_axis)),
        #                    mirrorAxis=(1.0, 0.0, 0.0), upAxis=(dt.Vector(up_axis)))
        # extra.orientJoints([j_ik_rp_up, j_ik_rp_low, j_ik_rp_low_end], localMoveAxis=(dt.Vector(up_axis)),
        #                    mirrorAxis=(1.0, 0.0, 0.0), upAxis=(dt.Vector(up_axis)))

        # pm.joint(self.j_def_collar, e=True, zso=True, oj="xyz", sao="yup")

        #test dup
        # pm.select(d=True)
        # pm.duplicate(j_ik_rp_up, name="TEST")

        # FK Joints

        pm.select(d=True)
        j_fk_up = pm.joint(name="jFK_Up_%s" % suffix, p=shoulder_pos, radius=2.0)
        j_fk_low = pm.joint(name="jFK_Low_%s" % suffix, p=elbow_pos, radius=2.0)
        j_fk_low_end = pm.joint(name="jFK_LowEnd_%s" % suffix, p=hand_pos, radius=2.0)

        # if side == "R":
        #     extra.orientJoints([j_fk_up, j_fk_low, j_fk_low_end], localMoveAxis=(dt.Vector(up_axis)), mirrorAxis=(-1.0, 0.0, 0.0), upAxis=-(dt.Vector(up_axis)))
        # else:
        #     extra.orientJoints([j_fk_up, j_fk_low, j_fk_low_end], localMoveAxis=(dt.Vector(up_axis)), mirrorAxis=(1.0, 0.0, 0.0), upAxis=(dt.Vector(up_axis)))

        extra.orientJoints([j_fk_up, j_fk_low, j_fk_low_end], localMoveAxis=(dt.Vector(up_axis)), mirrorAxis=(sideMult, 0.0, 0.0), upAxis=sideMult*(dt.Vector(up_axis)))


        # Hand joint

        j_def_hand = pm.joint(name="jDef_Hand_%s" % suffix, p=root_position, radius=1.0)

        # re-orient single joints

        extra.alignToAlter(j_collar_end, j_fk_up, mode=2)
        # pm.setAttr(j_collar_end.jointOrient, jOrShoulder)
        extra.alignToAlter(j_def_elbow, j_fk_low, mode=2)

        extra.alignToAlter(j_def_hand, j_fk_low_end, mode=2)

        #     _____            _             _ _
        #    / ____|          | |           | | |
        #   | |     ___  _ __ | |_ _ __ ___ | | | ___ _ __ ___
        #   | |    / _ \| '_ \| __| '__/ _ \| | |/ _ \ '__/ __|
        #   | |___| (_) | | | | |_| | | (_) | | |  __/ |  \__ \
        #    \_____\___/|_| |_|\__|_|  \___/|_|_|\___|_|  |___/
        #
        #

        ## shoulder controller
        shouldercont_scale = (init_shoulder_dist / 2, init_shoulder_dist / 2, init_shoulder_dist / 2)
        cont_shoulder = icon.shoulder("cont_Shoulder_%s" % suffix, shouldercont_scale)
        extra.alignAndAim(cont_shoulder, targetList=[collar_ref], aimTargetList=[shoulder_ref], upVector=up_axis)
        cont_shoulder_off = extra.createUpGrp(cont_shoulder, "OFF")
        cont_shoulder_ore = extra.createUpGrp(cont_shoulder, "ORE")
        cont_shoulder_pos = extra.createUpGrp(cont_shoulder, "POS")

        if side == "R":
            pm.setAttr("{0}.s{1}".format(cont_shoulder_pos, "z"), -1)

        ## IK hand controller
        ik_cont_scale = (init_lower_arm_dist / 3, init_lower_arm_dist / 3, init_lower_arm_dist / 3)
        self.cont_IK_hand = icon.circle("cont_IK_hand_%s" % suffix, ik_cont_scale, normal=(1, 0, 0))
        # extra.alignAndAim(self.cont_IK_hand, targetList=[hand_ref], aimTargetList=[elbow_ref], upVector=up_axis,
        #                   rotateOff=(0, -180, 0))
        # extra.alignAndAim(self.cont_IK_hand, targetList=[hand_ref], aimTargetList=[elbow_ref], upVector=up_axis)

        extra.alignToAlter(self.cont_IK_hand, j_fk_low_end, mode=2)

        self.cont_IK_OFF = extra.createUpGrp(self.cont_IK_hand, "OFF")
        cont_ik_hand_ore = extra.createUpGrp(self.cont_IK_hand, "ORE")
        cont_ik_hand_pos = extra.createUpGrp(self.cont_IK_hand, "POS")


        pm.addAttr(self.cont_IK_hand, shortName="polevector", longName="Pole_Vector", defaultValue=0.0, minValue=0.0,
                   maxValue=1.0,
                   at="double", k=True)
        pm.addAttr(self.cont_IK_hand, shortName="sUpArm", longName="Scale_Upper_Arm", defaultValue=1.0, minValue=0.0,
                   at="double", k=True)
        pm.addAttr(self.cont_IK_hand, shortName="sLowArm", longName="Scale_Lower_Arm", defaultValue=1.0, minValue=0.0,
                   at="double", k=True)
        pm.addAttr(self.cont_IK_hand, shortName="squash", longName="Squash", defaultValue=0.0, minValue=0.0,
                   maxValue=1.0, at="double",
                   k=True)
        pm.addAttr(self.cont_IK_hand, shortName="stretch", longName="Stretch", defaultValue=1.0, minValue=0.0,
                   maxValue=1.0, at="double",
                   k=True)
        pm.addAttr(self.cont_IK_hand, shortName="stretchLimit", longName="StretchLimit", defaultValue=100.0,
                   minValue=0.0,
                   maxValue=1000.0, at="double",
                   k=True)
        pm.addAttr(self.cont_IK_hand, shortName="softIK", longName="SoftIK", defaultValue=0.0, minValue=0.0,
                   maxValue=100.0, k=True)
        pm.addAttr(self.cont_IK_hand, shortName="volume", longName="Volume_Preserve", defaultValue=0.0, at="double",
                   k=True)

        ## Pole Vector Controller
        polecont_scale = (
            (((init_upper_arm_dist + init_lower_arm_dist) / 2) / 10),
            (((init_upper_arm_dist + init_lower_arm_dist) / 2) / 10),
            (((init_upper_arm_dist + init_lower_arm_dist) / 2) / 10)
        )
        self.cont_Pole = icon.plus("cont_Pole_%s" % suffix, polecont_scale, normal=(0, 0, 1))
        offset_mag_pole = ((init_upper_arm_dist + init_lower_arm_dist) / 4)
        offset_vector_pole = extra.getBetweenVector(elbow_ref, [shoulder_ref, hand_ref])
        extra.alignAndAim(self.cont_Pole,
                          targetList=[elbow_ref],
                          aimTargetList=[shoulder_ref, hand_ref],
                          upVector=up_axis,
                          translateOff=(offset_vector_pole * offset_mag_pole)
                          )
        cont_pole_off = extra.createUpGrp(self.cont_Pole, "OFF")
        cont_pole_vis = extra.createUpGrp(self.cont_Pole, "VIS")

        ## FK UP Arm Controller

        fk_up_arm_scale = (init_upper_arm_dist / 2, init_upper_arm_dist / 8, init_upper_arm_dist / 8)


        cont_fk_up_arm = icon.cube("cont_FK_UpArm_%s" % suffix, fk_up_arm_scale)

        # move the pivot to the bottom
        pm.xform(cont_fk_up_arm, piv=(sideMult*-(init_upper_arm_dist / 2), 0, 0 ), ws=True)

        # move the controller to the shoulder
        extra.alignToAlter(cont_fk_up_arm, j_fk_up, mode=2)

        cont_fk_up_arm_off = extra.createUpGrp(cont_fk_up_arm, "OFF")
        cont_fk_up_arm_ore = extra.createUpGrp(cont_fk_up_arm, "ORE")
        pm.xform(cont_fk_up_arm_off, piv=shoulder_pos, ws=True)
        pm.xform(cont_fk_up_arm_ore, piv=shoulder_pos, ws=True)

        ## FK LOW Arm Controller
        fk_low_arm_scale = (init_lower_arm_dist / 2, init_lower_arm_dist / 8, init_lower_arm_dist / 8)
        cont_fk_low_arm = icon.cube("cont_FK_LowArm_%s" % suffix, fk_low_arm_scale)
        # extra.alignAndAim(cont_fk_low_arm, targetList=[elbow_ref, hand_ref], aimTargetList=[hand_ref], upVector=up_axis)

        # move the pivot to the bottom
        pm.xform(cont_fk_low_arm, piv=(sideMult*-(init_lower_arm_dist / 2), 0, 0 ), ws=True)

        # align position and orientation to the joint
        extra.alignToAlter(cont_fk_low_arm, j_fk_low, mode=2)

        cont_fk_low_arm_off = extra.createUpGrp(cont_fk_low_arm, "OFF")
        cont_fk_low_arm_ore = extra.createUpGrp(cont_fk_low_arm, "ORE")
        pm.xform(cont_fk_low_arm_off, piv=elbow_pos, ws=True)
        pm.xform(cont_fk_low_arm_ore, piv=elbow_pos, ws=True)

        ## FK HAND Controller
        fk_cont_scale = (init_lower_arm_dist / 5, init_lower_arm_dist / 5, init_lower_arm_dist / 5)
        cont_fk_hand = icon.cube("cont_FK_Hand_%s" % suffix, fk_cont_scale)
        extra.alignToAlter(cont_fk_hand, j_def_hand, mode=2)

        cont_fk_hand_off = extra.createUpGrp(cont_fk_hand, "OFF")
        cont_fk_hand_pos = extra.createUpGrp(cont_fk_hand, "POS")
        cont_fk_hand_ore = extra.createUpGrp(cont_fk_hand, "ORE")

        # FK-IK SWITCH Controller
        icon_scale = init_upper_arm_dist / 4
        cont_fk_ik, fk_ik_rvs = icon.fkikSwitch(("cont_FK_IK_%s" % suffix), (icon_scale, icon_scale, icon_scale))
        extra.alignAndAim(cont_fk_ik, targetList=[hand_ref], aimTargetList=[elbow_ref], upVector=up_axis,
                          rotateOff=(0, 180, 0))
        pm.move(cont_fk_ik, (dt.Vector(up_axis) * (icon_scale * 2)), r=True)
        cont_fk_ik_pos = extra.createUpGrp(cont_fk_ik, "POS")

        if side == "R":
            pm.setAttr("{0}.s{1}".format(cont_fk_ik, "x"), -1)

        # TODO : REF
        # controller for twist orientation alignment
        pm.addAttr(cont_fk_ik, shortName="alignShoulder", longName="Align_Shoulder", defaultValue=1.0, at="float",
                   minValue=0.0, maxValue=1.0, k=True)
        # pm.addAttr(cont_fk_ik, shortName="alignHand", longName="Align Hand", defaultValue=1.0, at="float", minValue=0.0, maxValue=1.0, k=True)

        # pm.addAttr(cont_fk_ik, shortName="autoTwist", longName="Auto_Twist", defaultValue=1.0, minValue=0.0, maxValue=1.0, at="float", k=True)
        # pm.addAttr(cont_fk_ik, shortName="manualTwist", longName="Manual_Twist", defaultValue=0.0, at="float", k=True)

        pm.addAttr(cont_fk_ik, shortName="handAutoTwist", longName="Hand_Auto_Twist", defaultValue=1.0, minValue=0.0,
                   maxValue=1.0, at="float", k=True)
        pm.addAttr(cont_fk_ik, shortName="handManualTwist", longName="Hand_Manual_Twist", defaultValue=0.0, at="float",
                   k=True)

        pm.addAttr(cont_fk_ik, shortName="shoulderAutoTwist", longName="Shoulder_Auto_Twist", defaultValue=1.0,
                   minValue=0.0, maxValue=1.0, at="float", k=True)
        pm.addAttr(cont_fk_ik, shortName="shoulderManualTwist", longName="Shoulder_Manual_Twist", defaultValue=0.0,
                   at="float", k=True)

        pm.addAttr(cont_fk_ik, shortName="allowScaling", longName="Allow_Scaling", defaultValue=1.0, minValue=0.0,
                   maxValue=1.0, at="float", k=True)

        pm.addAttr(cont_fk_ik, shortName="tweakControls", longName="Tweak_Controls", defaultValue=0, at="bool")
        pm.setAttr(cont_fk_ik.tweakControls, cb=True)
        pm.addAttr(cont_fk_ik, shortName="fingerControls", longName="Finger_Controls", defaultValue=1, at="bool")
        pm.setAttr(cont_fk_ik.fingerControls, cb=True)

        # Create Start Lock

        start_lock = pm.spaceLocator(name="startLock_%s" % suffix)
        # extra.alignTo(start_lock, shoulder_ref, 2)
        extra.alignToAlter(start_lock, j_ik_orig_up, 2)
        start_lock_ore = extra.createUpGrp(start_lock, "Ore")
        start_lock_pos = extra.createUpGrp(start_lock, "Pos")
        start_lock_twist = extra.createUpGrp(start_lock, "AutoTwist")

        # start_lock_weight = pm.parentConstraint(j_collar_end, start_lock, sr=("y", "z"), mo=True)
        start_lock_weight = pm.parentConstraint(j_collar_end, start_lock, sr=("y", "z"), mo=False)

        # pm.setAttr(start_lock_weight.interpType, 0)

        # pm.parentConstraint(start_lock, j_ik_sc_up, mo=True)
        pm.parentConstraint(start_lock, j_ik_sc_up, mo=False)
        # pm.parentConstraint(start_lock, j_ik_rp_up, mo=True)
        pm.parentConstraint(start_lock, j_ik_rp_up, mo=False)

        # Create IK handles

        ik_handle_sc = pm.ikHandle(sj=j_ik_sc_up, ee=j_ik_sc_low_end, name="ikHandle_SC_%s" % suffix)
        ik_handle_rp = pm.ikHandle(sj=j_ik_rp_up, ee=j_ik_rp_low_end, name="ikHandle_RP_%s" % suffix, sol="ikRPsolver")

        pm.poleVectorConstraint(self.cont_Pole, ik_handle_rp[0])
        pm.aimConstraint(j_ik_rp_low, self.cont_Pole, u=up_axis, wut="vector")

        ### Create and constrain Distance Locators

        arm_start = pm.spaceLocator(name="armStart_%s" % suffix)
        pm.pointConstraint(start_lock, arm_start, mo=False)

        arm_end = pm.spaceLocator(name="armEnd_%s" % suffix)
        pm.pointConstraint(master_ik, arm_end, mo=False)

        ### Create Nodes and Connections for Stretchy IK SC

        stretch_offset = pm.createNode("plusMinusAverage", name="stretchOffset_%s" % suffix)
        distance_sc = pm.createNode("distanceBetween", name="distance_SC_%s" % suffix)
        ik_stretch_distance_clamp = pm.createNode("clamp", name="IK_stretch_distanceClamp_%s" % suffix)
        ik_stretch_stretchiness_clamp = pm.createNode("clamp", name="IK_stretch_stretchinessClamp_%s" % suffix)
        extra_scale_mult_sc = pm.createNode("multiplyDivide", name="extraScaleMult_SC_%s" % suffix)
        initial_divide_sc = pm.createNode("multiplyDivide", name="initialDivide_SC_%s" % suffix)
        initial_length_multip_sc = pm.createNode("multiplyDivide", name="initialLengthMultip_SC_%s" % suffix)
        stretch_amount_sc = pm.createNode("multiplyDivide", name="stretchAmount_SC_%s" % suffix)
        sum_of_j_lengths_sc = pm.createNode("plusMinusAverage", name="sumOfJLengths_SC_%s" % suffix)
        # stretch_condition_sc = pm.createNode("condition", name="stretchCondition_SC_%s" % suffix)
        squashiness_sc = pm.createNode("blendColors", name="squashiness_SC_%s" % suffix)
        stretchiness_sc = pm.createNode("blendColors", name="stretchiness_SC_%s" % suffix)

        # pm.setAttr(ik_stretch_stretchiness_clamp + ".maxR", 1)
        pm.setAttr("%s.maxR" % ik_stretch_stretchiness_clamp, 1)
        # pm.setAttr(initial_length_multip_sc + ".input1X", init_upper_arm_dist)
        pm.setAttr("%s.input1X" % initial_length_multip_sc, init_upper_arm_dist)
        # pm.setAttr(initial_length_multip_sc + ".input1Y", init_lower_arm_dist)
        pm.setAttr("%s.input1Y" % initial_length_multip_sc, init_lower_arm_dist)
        # pm.setAttr(initial_divide_sc + ".operation", 2)
        pm.setAttr("%s.operation" % initial_divide_sc, 2)
        # pm.setAttr(stretch_condition_sc + ".operation", 2)
        # pm.setAttr("%s.operation" % stretch_condition_sc, 2)

        ### IkSoft nodes
        ik_soft_clamp = pm.createNode("clamp", name="ikSoft_clamp_%s" % suffix)
        pm.setAttr("%s.minR" % ik_soft_clamp, 0.0001)
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
        arm_start.translate >> distance_sc.point1
        arm_end.translate >> distance_sc.point2
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
        # stretch_condition_sc.outColorR >> squashiness_sc.color2R
        # stretch_condition_sc.outColorG >> squashiness_sc.color2G
        squashiness_sc.outputR >> stretchiness_sc.color1R
        squashiness_sc.outputG >> stretchiness_sc.color1G
        stretchiness_sc.outputR >> j_ik_sc_low.translateX
        stretchiness_sc.outputG >> j_ik_sc_low_end.translateX
        stretchiness_sc.outputR >> j_ik_rp_low.translateX
        stretchiness_sc.outputG >> j_ik_rp_low_end.translateX

        ## iksoft related
        self.cont_IK_hand.softIK >> ik_soft_clamp.inputR

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

        self.cont_IK_hand.rotate >> j_ik_rp_low.rotate

        # Stretch Attributes Controller connections

        self.cont_IK_hand.sUpArm >> extra_scale_mult_sc.input2X
        self.cont_IK_hand.sLowArm >> extra_scale_mult_sc.input2Y
        self.cont_IK_hand.squash >> squashiness_sc.blender

        stretch_offset.output1D >> ik_stretch_distance_clamp.maxR
        # self.cont_IK_hand.stretch >> ik_stretch_stretchiness_clamp.inputR
        self.cont_IK_hand.stretch >> ik_stretch_stretchiness_clamp.inputR

        # self.cont_IK_hand.stretch >> stretch_offset.input1D[2]
        self.cont_IK_hand.stretchLimit >> stretch_offset.input1D[2]

        ik_parent_grp = pm.group(name="IK_parentGRP_%s" % suffix, em=True)
        extra.alignTo(ik_parent_grp, hand_ref, 2)
        # extra.alignToAlter(ik_parent_grp, j_def_hand, 2)

        # pm.parentConstraint(self.cont_IK_hand, ik_parent_grp, mo=True)
        pm.parentConstraint(self.cont_IK_hand, ik_parent_grp, mo=False)

        # parenting should be after the constraint
        pm.parent(ik_handle_sc[0], ik_parent_grp)
        pm.parent(ik_handle_rp[0], ik_parent_grp)
        pm.parent(master_ik, ik_parent_grp)

        blend_ore_ik_up = pm.createNode("blendColors", name="blendORE_IK_Up_%s" % suffix)
        j_ik_sc_up.rotate >> blend_ore_ik_up.color2
        j_ik_rp_up.rotate >> blend_ore_ik_up.color1
        blend_ore_ik_up.output >> j_ik_orig_up.rotate
        self.cont_IK_hand.polevector >> blend_ore_ik_up.blender

        blend_pos_ik_up = pm.createNode("blendColors", name="blendPOS_IK_Up_%s" % suffix)
        j_ik_sc_up.translate >> blend_pos_ik_up.color2
        j_ik_rp_up.translate >> blend_pos_ik_up.color1
        blend_pos_ik_up.output >> j_ik_orig_up.translate
        self.cont_IK_hand.polevector >> blend_pos_ik_up.blender

        blend_ore_ik_low = pm.createNode("blendColors", name="blendORE_IK_Low_%s" % suffix)
        j_ik_sc_low.rotate >> blend_ore_ik_low.color2
        j_ik_rp_low.rotate >> blend_ore_ik_low.color1
        # blend_ore_ik_low.output >> j_ik_orig_low.rotate
        # Weird bug with skinned character / use seperate connections
        # if there is no skincluster, it works ok, but adding a skin cluster misses 2 out of 3 rotation axis
        # Therefore make SEPERATE CONNECTIONS
        blend_ore_ik_low.outputR >> j_ik_orig_low.rotateX
        blend_ore_ik_low.outputG >> j_ik_orig_low.rotateY
        blend_ore_ik_low.outputB >> j_ik_orig_low.rotateZ
        self.cont_IK_hand.polevector >> blend_ore_ik_low.blender

        blend_pos_ik_low = pm.createNode("blendColors", name="blendPOS_IK_Low_%s" % suffix)
        j_ik_sc_low.translate >> blend_pos_ik_low.color2
        j_ik_rp_low.translate >> blend_pos_ik_low.color1
        blend_pos_ik_low.output >> j_ik_orig_low.translate
        self.cont_IK_hand.polevector >> blend_pos_ik_low.blender

        blend_ore_ik_low_end = pm.createNode("blendColors", name="blendORE_IK_LowEnd_%s" % suffix)
        j_ik_sc_low_end.rotate >> blend_ore_ik_low_end.color2
        j_ik_rp_low_end.rotate >> blend_ore_ik_low_end.color1
        # blend_ore_ik_low_end.output >> j_ik_orig_low_end.rotate
        # Weird bug with skinned character / use seperate connections
        # if there is no skincluster, it works ok, but adding a skin cluster misses 2 out of 3 rotation axis
        # Therefore make SEPERATE CONNECTIONS
        blend_ore_ik_low_end.outputR >> j_ik_orig_low_end.rotateX
        blend_ore_ik_low_end.outputG >> j_ik_orig_low_end.rotateY
        blend_ore_ik_low_end.outputB >> j_ik_orig_low_end.rotateZ
        self.cont_IK_hand.polevector >> blend_ore_ik_low_end.blender

        blend_pos_ik_low_end = pm.createNode("blendColors", name="blendPOS_IK_LowEnd_%s" % suffix)
        j_ik_sc_low_end.translate >> blend_pos_ik_low_end.color2
        j_ik_rp_low_end.translate >> blend_pos_ik_low_end.color1
        blend_pos_ik_low_end.output >> j_ik_orig_low_end.translate
        self.cont_IK_hand.polevector >> blend_pos_ik_low_end.blender

        pole_vector_rvs = pm.createNode("reverse", name="poleVector_Rvs_%s" % suffix)
        self.cont_IK_hand.polevector >> pole_vector_rvs.inputX
        self.cont_IK_hand.polevector >> self.cont_Pole.v

        pm.parent(j_ik_orig_up, master_root)
        pm.parent(j_ik_sc_up, master_root)
        pm.parent(j_ik_rp_up, master_root)

        pm.select(cont_shoulder)

        pacon_locator_shou = pm.spaceLocator(name="paConLoc_%s" % suffix)
        # extra.alignTo(pacon_locator_shou, self.j_def_collar)
        extra.alignTo(pacon_locator_shou, self.j_def_collar, mode=2)

        # j_def_pa_con = pm.parentConstraint(cont_shoulder, pacon_locator_shou, mo=True)
        j_def_pa_con = pm.parentConstraint(cont_shoulder, pacon_locator_shou, mo=False)

        ###########################
        ######### FK ARM ##########
        ###########################

        cont_fk_up_arm.scaleY >> j_fk_up.scaleX

        cont_fk_low_arm.scaleY >> j_fk_low.scaleX

        ### Create Midlock - FK

        # pm.orientConstraint(cont_fk_up_arm, j_fk_up, mo=True)
        pm.orientConstraint(cont_fk_up_arm, j_fk_up, mo=False)
        pm.pointConstraint(start_lock, j_fk_up, mo=False)

        # pm.orientConstraint(cont_fk_low_arm, j_fk_low, mo=True)
        pm.orientConstraint(cont_fk_low_arm, j_fk_low, mo=False)

        pm.parentConstraint(cont_shoulder, cont_fk_up_arm_off, sr=("x", "y", "z"), mo=True)
        # pm.orientConstraint(cont_shoulder, cont_fk_up_arm_ore, mo=False)
        pm.parentConstraint(cont_fk_up_arm, cont_fk_low_arm_off, mo=True)
        # pm.parentConstraint(cont_fk_up_arm, cont_fk_low_arm_off, mo=False)

        fk_ik_rvs.outputX >> cont_fk_up_arm_ore.visibility
        fk_ik_rvs.outputX >> cont_fk_low_arm_ore.visibility

        cont_fk_ik.fk_ik >> self.cont_IK_hand.visibility

        cont_fk_ik.fk_ik >> cont_pole_vis.visibility

        ### Create MidLock controller

        midcont_scale = (init_lower_arm_dist / 4, init_lower_arm_dist / 4, init_lower_arm_dist / 4)
        cont_mid_lock = icon.star("cont_mid_%s" % suffix, midcont_scale, normal=(1, 0, 0))

        extra.alignToAlter(cont_mid_lock, j_def_elbow, 2)

        cont_mid_lock_pos = extra.createUpGrp(cont_mid_lock, "POS")
        cont_mid_lock_ave = extra.createUpGrp(cont_mid_lock, "AVE")
        # extra.alignTo(cont_mid_lock_pos, elbow_ref, 0)

        mid_lock_pa_con_weight = pm.parentConstraint(j_ik_orig_up, j_fk_up, cont_mid_lock_pos, mo=True)
        # cont_fk_ik.fk_ik >> (mid_lock_pa_con_weight + "." + j_ik_orig_up + "W0")
        cont_fk_ik.fk_ik >> ("%s.%sW0" % (mid_lock_pa_con_weight, j_ik_orig_up))

        # fk_ik_rvs.outputX >> (mid_lock_pa_con_weight + "." + j_fk_up + "W1")
        fk_ik_rvs.outputX >> ("%s.%sW1" % (mid_lock_pa_con_weight, j_fk_up))

        mid_lock_po_con_weight = pm.pointConstraint(j_ik_orig_low, j_fk_low, cont_mid_lock_ave, mo=False)
        # cont_fk_ik.fk_ik >> (mid_lock_po_con_weight + "." + j_ik_orig_low + "W0")
        cont_fk_ik.fk_ik >> ("%s.%sW0" % (mid_lock_po_con_weight, j_ik_orig_low))

        # fk_ik_rvs.outputX >> (mid_lock_po_con_weight + "." + j_fk_low + "W1")
        fk_ik_rvs.outputX >> ("%s.%sW1" % (mid_lock_po_con_weight, j_fk_low))

        mid_lock_x_bln = pm.createNode("multiplyDivide", name="midLock_xBln_%s" % suffix)

        mid_lock_rot_xsw = pm.createNode("blendTwoAttr", name="midLock_rotXsw_%s" % suffix)
        j_ik_orig_low.rotateY >> mid_lock_rot_xsw.input[0]
        j_fk_low.rotateY >> mid_lock_rot_xsw.input[1]
        fk_ik_rvs.outputX >> mid_lock_rot_xsw.attributesBlender

        mid_lock_rot_xsw.output >> mid_lock_x_bln.input1Z

        pm.setAttr(mid_lock_x_bln.input2Z, 0.5)
        mid_lock_x_bln.outputZ >> cont_mid_lock_ave.rotateY

        ### Create Midlock

        mid_lock = pm.spaceLocator(name="midLock_%s" % suffix)
        pm.parentConstraint(mid_lock, j_def_elbow)
        extra.alignTo(mid_lock, cont_mid_lock, 0)

        pm.parentConstraint(cont_mid_lock, mid_lock, mo=False)

        ### Create End Lock
        end_lock = pm.spaceLocator(name="endLock_%s" % suffix)
        extra.alignTo(end_lock, hand_ref, 2)
        end_lock_ore = extra.createUpGrp(end_lock, "Ore")
        end_lock_pos = extra.createUpGrp(end_lock, "Pos")
        end_lock_twist = extra.createUpGrp(end_lock, "Twist")

        end_lock_weight = pm.pointConstraint(j_ik_orig_low_end, j_fk_low_end, end_lock_pos, mo=False)
        # cont_fk_ik.fk_ik >> (end_lock_weight + "." + j_ik_orig_low_end + "W0")
        cont_fk_ik.fk_ik >> ("%s.%sW0" % (end_lock_weight, j_ik_orig_low_end))

        # fk_ik_rvs.outputX >> (end_lock_weight + "." + j_fk_low_end + "W1")
        fk_ik_rvs.outputX >> ("%s.%sW1" % (end_lock_weight, j_fk_low_end))

        pm.parentConstraint(end_lock, cont_fk_ik_pos, mo=True)
        pm.parent(end_lock_ore, self.scaleGrp)

        end_lock_rot = pm.parentConstraint(ik_parent_grp, cont_fk_hand, end_lock_twist, st=("x", "y", "z"), mo=True)
        # cont_fk_ik.fk_ik >> (end_lock_rot + "." + ik_parent_grp + "W0")
        cont_fk_ik.fk_ik >> ("%s.%sW0" % (end_lock_rot, ik_parent_grp))
        # fk_ik_rvs.outputX >> (end_lock_rot + "." + cont_fk_hand + "W1")
        fk_ik_rvs.outputX >> ("%s.%sW1" % (end_lock_rot, cont_fk_hand))

        ###################################
        #### CREATE DEFORMATION JOINTS ####
        ###################################

        # UPPER ARM RIBBON

        # ribbonConnections_upperArm = rc..createRibbon(shoulder_ref, elbow_ref, "up_" + suffix, 0)
        # ribbon_upper_arm = rc.Ribbon()
        ribbon_upper_arm = rc.PowerRibbon()
        # ribbon_upper_arm.createRibbon(shoulder_ref, elbow_ref, "up_%s" % suffix, 0, connectStartAim=False)
        ribbon_upper_arm.createPowerRibbon(shoulder_ref, elbow_ref, "up_%s" % suffix, side=side, orientation=0,
                                           connectStartAim=False, upVector=up_axis)
        # ribbon_upper_arm.createPowerRibbon(shoulder_ref, elbow_ref, "up_%s" % suffix, orientation=0, connectStartAim=False)
        ribbon_start_pa_con_upper_arm_start = pm.parentConstraint(start_lock, ribbon_upper_arm.startConnection, mo=True)
        pm.parentConstraint(mid_lock, ribbon_upper_arm.endConnection, mo=True)

        # connect the elbow scaling
        cont_mid_lock.scale >> ribbon_upper_arm.endConnection.scale
        cont_mid_lock.scale >> j_def_elbow.scale

        pm.scaleConstraint(self.scaleGrp, ribbon_upper_arm.scaleGrp)

        # TODO : REF
        ribbon_start_ori_con = pm.parentConstraint(j_ik_orig_up, j_fk_up, ribbon_upper_arm.startAim, mo=True,
                                                   skipTranslate=["x", "y", "z"])
        ribbon_start_ori_con2 = pm.parentConstraint(j_collar_end, ribbon_upper_arm.startAim, mo=True,
                                                    skipTranslate=["x", "y", "z"])

        cont_fk_ik.fk_ik >> ("%s.%sW0" % (ribbon_start_ori_con, j_ik_orig_up))
        fk_ik_rvs.outputX >> ("%s.%sW1" % (ribbon_start_ori_con, j_fk_up))

        pairBlendNode = pm.listConnections(ribbon_start_ori_con, d=True, t="pairBlend")[0]
        # disconnect the existing weight connection
        pm.disconnectAttr(pairBlendNode.w)
        # re-connect to the custom attribute
        cont_fk_ik.alignShoulder >> pairBlendNode.w

        # ref ends here

        # AUTO AND MANUAL TWIST

        # auto
        auto_twist = pm.createNode("multiplyDivide", name="autoTwist_%s" % suffix)
        # cont_shoulder.autoTwist >> auto_twist.input2X
        # TODO : REF
        cont_fk_ik.shoulderAutoTwist >> auto_twist.input2X
        ribbon_start_pa_con_upper_arm_start.constraintRotate >> auto_twist.input1

        # !!! The parent constrain override should be disconnected like this
        pm.disconnectAttr(
            ribbon_start_pa_con_upper_arm_start.constraintRotateX,
            ribbon_upper_arm.startConnection.rotateX
        )

        # manual
        add_manual_twist = pm.createNode("plusMinusAverage", name=("AddManualTwist_UpperArm_%s" % suffix))
        auto_twist.output >> add_manual_twist.input3D[0]
        # cont_shoulder.manualTwist >> add_manual_twist.input3D[1].input3Dx
        # TODO : REF
        cont_fk_ik.shoulderAutoTwist >> add_manual_twist.input3D[1].input3Dx

        # connect to the joint
        add_manual_twist.output3D >> ribbon_upper_arm.startConnection.rotate

        # TODO : REF
        # connect allowScaling
        cont_fk_ik.allowScaling >> ribbon_upper_arm.startConnection.scaleSwitch

        # LOWER ARM RIBBON

        # ribbon_lower_arm = rc.Ribbon()
        ribbon_lower_arm = rc.PowerRibbon()
        # ribbon_lower_arm.createRibbon(elbow_ref, hand_ref, "low_%s" % suffix, 0)
        ribbon_lower_arm.createPowerRibbon(elbow_ref, hand_ref, "low_%s" % suffix, side=side, orientation=0,
                                           upVector=up_axis)

        pm.parentConstraint(mid_lock, ribbon_lower_arm.startConnection, mo=True)
        ribbon_start_pa_con_lower_arm_end = pm.parentConstraint(end_lock, ribbon_lower_arm.endConnection, mo=True)

        # connect the elbow scaling
        cont_mid_lock.scale >> ribbon_lower_arm.startConnection.scale

        pm.scaleConstraint(self.scaleGrp, ribbon_lower_arm.scaleGrp)

        # AUTO AND MANUAL TWIST

        # auto
        auto_twist = pm.createNode("multiplyDivide", name="autoTwist_%s" % suffix)
        # cont_fk_ik.autoTwist >> auto_twist.input2X
        # TODO : REF
        cont_fk_ik.handAutoTwist >> auto_twist.input2X
        ribbon_start_pa_con_lower_arm_end.constraintRotate >> auto_twist.input1

        # !!! The parent constrain override should be disconnected like this
        pm.disconnectAttr(ribbon_start_pa_con_lower_arm_end.constraintRotateX, ribbon_lower_arm.endConnection.rotateX)

        # manual
        add_manual_twist = pm.createNode("plusMinusAverage", name=("AddManualTwist_LowerArm_%s" % suffix))
        auto_twist.output >> add_manual_twist.input3D[0]
        # cont_fk_ik.manualTwist >> add_manual_twist.input3D[1].input3Dx
        # TODO : REF
        cont_fk_ik.handManualTwist >> add_manual_twist.input3D[1].input3Dx

        # connect to the joint
        add_manual_twist.output3D >> ribbon_lower_arm.endConnection.rotate

        # TODO : REF
        # connect allowScaling
        cont_fk_ik.allowScaling >> ribbon_lower_arm.startConnection.scaleSwitch

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
        # vp knee branch
        vpExtraInput.output >> ribbon_lower_arm.startConnection.scale
        vpExtraInput.output >> ribbon_upper_arm.endConnection.scale
        vpExtraInput.output >> j_def_elbow.scale
        cont_mid_lock.scale >> vpExtraInput.input1

        vpMidAverage.output1D >> vpExtraInput.input2X
        vpMidAverage.output1D >> vpExtraInput.input2Y
        vpMidAverage.output1D >> vpExtraInput.input2Z

        vpPowerMid.outputX >> vpMidAverage.input1D[0]
        vpPowerMid.outputY >> vpMidAverage.input1D[1]

        vpInitLength.outputX >> vpPowerMid.input1X
        vpInitLength.outputY >> vpPowerMid.input1Y
        self.cont_IK_hand.volume >> vpPowerMid.input2X
        self.cont_IK_hand.volume >> vpPowerMid.input2Y
        initial_length_multip_sc.outputX >> vpInitLength.input1X
        initial_length_multip_sc.outputY >> vpInitLength.input1Y
        stretchiness_sc.color1R >> vpInitLength.input2X
        stretchiness_sc.color1G >> vpInitLength.input2Y

        # vp upper branch
        mid_off_up = ribbon_upper_arm.middleCont[0].getParent()
        vpPowerUpperLeg.outputX >> mid_off_up.scaleX
        vpPowerUpperLeg.outputX >> mid_off_up.scaleY
        vpPowerUpperLeg.outputX >> mid_off_up.scaleZ

        vpInitLength.outputX >> vpPowerUpperLeg.input1X
        vpUpperLowerReduce.output >> vpPowerUpperLeg.input2X

        # vp lower branch
        mid_off_low = ribbon_lower_arm.middleCont[0].getParent()
        vpPowerLowerLeg.outputX >> mid_off_low.scaleX
        vpPowerLowerLeg.outputX >> mid_off_low.scaleY
        vpPowerLowerLeg.outputX >> mid_off_low.scaleZ

        vpInitLength.outputX >> vpPowerLowerLeg.input1X
        vpUpperLowerReduce.output >> vpPowerLowerLeg.input2X

        self.cont_IK_hand.volume >> vpUpperLowerReduce.input1

        ###############################################
        ################### HAND ######################
        ###############################################

        hand_lock = pm.spaceLocator(
            name="handLock_%s" % suffix)  # Bu iki satir r arm mirror posing icin dondurulse bile dogru bir \
        #  weighted constraint yapilmasi icin araya bir node olusturuyor.
        extra.alignTo(hand_lock, cont_fk_hand_off, 2)

        # pm.makeIdentity(hand_lock, a=True)
        pm.parentConstraint(cont_fk_hand, hand_lock, mo=True)  # Olusturulan ara node baglanir

        root_master = pm.spaceLocator(name="handMaster_%s" % suffix)
        extra.alignTo(root_master, hand_ref, 2)
        pm.select(d=True)

        self.sockets.append(j_def_hand)
        extra.alignTo(j_def_hand, hand_ref, 2)
        deformer_joints = [[j_def_hand]]
        pm.parent(j_def_hand, root_master)

        pm.pointConstraint(end_lock, root_master, mo=True)
        pm.parentConstraint(cont_fk_low_arm, cont_fk_hand_pos, mo=True)
        hand_ori_con = pm.parentConstraint(self.cont_IK_hand, hand_lock, root_master, st=("x", "y", "z"), mo=True)
        ## NO Flip
        pm.setAttr(hand_ori_con.interpType, 0)
        # hand_ori_con = pm.parentConstraint(self.cont_IK_hand, hand_lock, root_master, st=("x", "y", "z"), mo=False)
        # cont_fk_ik.fk_ik >> (hand_ori_con + "." + self.cont_IK_hand + "W0")
        cont_fk_ik.fk_ik >> ("%s.%sW0" % (hand_ori_con, self.cont_IK_hand))

        # fk_ik_rvs.outputX >> (hand_ori_con + "." + hand_lock + "W1")
        fk_ik_rvs.outputX >> ("%s.%sW1" % (hand_ori_con, hand_lock))

        fk_ik_rvs.outputX >> cont_fk_hand.v

        hand_sca_con = pm.createNode("blendColors", name="handScaCon_%s" % suffix)
        self.cont_IK_hand.scale >> hand_sca_con.color1
        cont_fk_hand.scale >> hand_sca_con.color2
        cont_fk_ik.fk_ik >> hand_sca_con.blender
        hand_sca_con.output >> root_master.scale

        ### FINAL ROUND UP

        pm.select(arm_start)

        pm.parentConstraint(self.limbPlug, self.scaleGrp, mo=True)
        pm.parent(start_lock_ore, self.scaleGrp)
        pm.parent(arm_start, self.scaleGrp)
        pm.parent(arm_end, self.scaleGrp)
        pm.parent(ik_parent_grp, self.scaleGrp)
        pm.parent(cont_shoulder_off, self.scaleGrp)
        pm.parent(cont_fk_up_arm_off, self.scaleGrp)
        pm.parent(cont_fk_low_arm_off, self.scaleGrp)

        pm.parent(ik_parent_grp, self.scaleGrp)
        pm.parent(cont_fk_hand_off, self.scaleGrp)
        pm.parent(mid_lock, self.scaleGrp)
        pm.parent(cont_mid_lock_pos, self.scaleGrp)
        pm.parent(cont_pole_off, self.scaleGrp)
        pm.parent(j_def_elbow, self.scaleGrp)

        pm.parent(ribbon_upper_arm.scaleGrp, self.nonScaleGrp)
        pm.parent(ribbon_upper_arm.nonScaleGrp, self.nonScaleGrp)

        pm.parent(ribbon_lower_arm.scaleGrp, self.nonScaleGrp)
        pm.parent(ribbon_lower_arm.nonScaleGrp, self.nonScaleGrp)

        pm.parent(pacon_locator_shou, self.scaleGrp)
        pm.parent(self.j_def_collar, pacon_locator_shou)

        pm.parent(hand_lock, self.scaleGrp)
        pm.parent(master_root, self.scaleGrp)
        pm.parent(j_fk_up, self.scaleGrp)
        pm.parent(cont_fk_ik_pos, self.scaleGrp)
        pm.parent(root_master, self.scaleGrp)

        pm.parent(self.scaleGrp, self.cont_IK_OFF, self.nonScaleGrp, self.limbGrp)

        pm.parent(self.scaleGrp, self.nonScaleGrp, self.cont_IK_OFF, self.limbGrp)

        ## CONNECT RIG VISIBILITIES

        # Tweak controls
        # powerRibbonChange
        # tweak_controls = (ribbon_upper_arm.middleCont, ribbon_lower_arm.middleCont, cont_mid_lock)
        tweak_controls = ribbon_upper_arm.middleCont + ribbon_lower_arm.middleCont + [cont_mid_lock]

        for i in tweak_controls:
            cont_fk_ik.tweakControls >> i.v

        pm.addAttr(self.scaleGrp, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True)
        pm.addAttr(self.scaleGrp, at="bool", ln="Joints_Visibility", sn="jointVis", defaultValue=True)
        pm.addAttr(self.scaleGrp, at="bool", ln="Rig_Visibility", sn="rigVis", defaultValue=True)
        # make the created attributes visible in the channelbox
        pm.setAttr(self.scaleGrp.contVis, cb=True)
        pm.setAttr(self.scaleGrp.jointVis, cb=True)
        pm.setAttr(self.scaleGrp.rigVis, cb=True)

        self.nodesContVis = [cont_pole_off, cont_shoulder_off, self.cont_IK_OFF, cont_fk_hand_off, cont_fk_ik_pos,
                             cont_fk_low_arm_off, cont_fk_up_arm_off, ribbon_lower_arm.scaleGrp,
                             ribbon_upper_arm.scaleGrp, cont_mid_lock_pos
                             ]
        nodes_joint_vis = [j_def_elbow, self.j_def_collar, j_def_hand]
        self.deformerJoints = ribbon_lower_arm.deformerJoints + ribbon_upper_arm.deformerJoints + nodes_joint_vis
        nodes_rig_vis = [end_lock_twist, start_lock_ore, arm_start, arm_end, ik_parent_grp, mid_lock, master_root,
                         j_fk_up, hand_lock, root_master.getShape(), pacon_locator_shou.getShape()
                         ]
        # global Cont visibilities
        for i in self.nodesContVis:
            self.scaleGrp.contVis >> i.v

        # global Joint visibilities
        for lst in self.deformerJoints:
            self.scaleGrp.jointVis >> lst.v

        # global Rig visibilities
        for i in nodes_rig_vis:
            self.scaleGrp.rigVis >> i.v
        for i in ribbon_lower_arm.toHide:
            self.scaleGrp.rigVis >> i.v
        for i in ribbon_upper_arm.toHide:
            self.scaleGrp.rigVis >> i.v

        pm.setAttr(self.scaleGrp.rigVis, 1)

        # FOOL PROOFING
        extra.lockAndHide(self.cont_IK_hand, ["v"])
        extra.lockAndHide(self.cont_Pole, ["rx", "ry", "rz", "sx", "sy", "sz", "v"])
        extra.lockAndHide(cont_mid_lock, ["v"])
        extra.lockAndHide(cont_fk_ik, ["sx", "sy", "sz", "v"])
        extra.lockAndHide(cont_fk_hand, ["tx", "ty", "tz", "v"])
        extra.lockAndHide(cont_fk_low_arm, ["tx", "ty", "tz", "sx", "sz", "v"])
        extra.lockAndHide(cont_fk_up_arm, ["tx", "ty", "tz", "sx", "sz", "v"])
        extra.lockAndHide(cont_shoulder, ["sx", "sy", "sz", "v"])

        extra.colorize(cont_shoulder, self.colorCodes[0])
        extra.colorize(self.cont_IK_hand, self.colorCodes[0])
        extra.colorize(self.cont_Pole, self.colorCodes[0])
        extra.colorize(cont_fk_ik, self.colorCodes[0])
        extra.colorize(cont_fk_up_arm, self.colorCodes[0])
        extra.colorize(cont_fk_low_arm, self.colorCodes[0])
        extra.colorize(cont_fk_hand, self.colorCodes[0])
        extra.colorize(cont_mid_lock, self.colorCodes[1])
        extra.colorize(ribbon_upper_arm.middleCont, self.colorCodes[1])
        extra.colorize(ribbon_lower_arm.middleCont, self.colorCodes[1])

        extra.colorize(self.deformerJoints, self.colorCodes[0], shape=False)

        self.scaleConstraints = [self.scaleGrp, self.cont_IK_OFF]
        self.anchors = [(self.cont_IK_hand, "parent", 1, None), (self.cont_Pole, "parent", 1, None)]

