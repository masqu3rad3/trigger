import pymel.core as pm
import extraProcedures as extra
# import ribbonClass as rc
import powerRibbon as rc
import contIcons as icon
import pymel.core.datatypes as dt

reload(extra)
reload(rc)
reload(icon)

class Arm(object):
    def __init__(self, arminits, suffix="", side="L"):

        if len(arminits) < 4:
            pm.error("Missing Joints for Arm Setup")
            return

        if not type(arminits) == dict and not type(arminits) == list:
            pm.error("Init joints must be list or dictionary")
            return

        if type(arminits) == dict:
            # reinitialize the dictionary for easy use
            self.collar_ref = arminits["Collar"]
            self.shoulder_ref = arminits["Shoulder"]
            self.elbow_ref = arminits["Elbow"]
            self.hand_ref = arminits["Hand"]
        else:
            self.collar_ref = arminits[0]
            self.shoulder_ref = arminits[1]
            self.elbow_ref = arminits[2]
            self.hand_ref = arminits[3]

        self.collar_pos = self.collar_ref.getTranslation(space="world")
        self.shoulder_pos = self.shoulder_ref.getTranslation(space="world")
        self.elbow_pos = self.elbow_ref.getTranslation(space="world")
        self.hand_pos = self.hand_ref.getTranslation(space="world")

        # get distances
        self.init_shoulder_dist = extra.getDistance(self.collar_ref, self.shoulder_ref)
        self.init_upper_arm_dist = extra.getDistance(self.shoulder_ref, self.elbow_ref)
        self.init_lower_arm_dist = extra.getDistance(self.elbow_ref, self.hand_ref)

        self.sideMult = -1 if side == "R" else 1
        self.side = side

        self.up_axis, self.mirror_axis, self.look_axis = extra.getRigAxes(self.collar_ref)

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
        self.limbGrp = pm.group(name="limbGrp_%s" % self.suffix, em=True)
        self.scaleGrp = pm.group(name="scaleGrp_%s" % self.suffix, em=True)
        extra.alignTo(self.scaleGrp, self.collar_ref, 0)
        self.nonScaleGrp = pm.group(name="NonScaleGrp_%s" % self.suffix, em=True)

        pm.addAttr(self.scaleGrp, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True)
        pm.addAttr(self.scaleGrp, at="bool", ln="Joints_Visibility", sn="jointVis", defaultValue=True)
        pm.addAttr(self.scaleGrp, at="bool", ln="Rig_Visibility", sn="rigVis", defaultValue=True)
        # make the created attributes visible in the channelbox
        pm.setAttr(self.scaleGrp.contVis, cb=True)
        pm.setAttr(self.scaleGrp.jointVis, cb=True)
        pm.setAttr(self.scaleGrp.rigVis, cb=True)

        pm.parent(self.scaleGrp, self.limbGrp)
        pm.parent(self.nonScaleGrp, self.limbGrp)

    def createJoints(self):
        # Create Limb Plug
        pm.select(d=True)
        self.limbPlug = pm.joint(name="jPlug_%s" % self.suffix, p=self.collar_pos, radius=3)

        # Shoulder Joints
        pm.select(d=True)
        self.j_def_collar = pm.joint(name="jDef_Collar_%s" % self.suffix, p=self.collar_pos, radius=1.5)
        self.sockets.append(self.j_def_collar)
        self.j_collar_end = pm.joint(name="j_CollarEnd_%s" % self.suffix, p=self.shoulder_pos, radius=1.5)
        self.sockets.append(self.j_collar_end)

        extra.orientJoints([self.j_def_collar, self.j_collar_end], localMoveAxis=(dt.Vector(self.up_axis)),
                           mirrorAxis=(self.sideMult, 0.0, 0.0), upAxis=self.sideMult * (dt.Vector(self.up_axis)))

        pm.select(d=True)
        self.j_def_elbow = pm.joint(name="jDef_elbow_%s" % self.suffix, p=self.elbow_pos, radius=1.5)
        self.sockets.append(self.j_def_elbow)

        # IK Joints
        # Follow IK Chain
        pm.select(d=True)
        self.j_ik_orig_up = pm.joint(name="jIK_orig_Up_%s" % self.suffix, p=self.shoulder_pos, radius=0.5)
        self.j_ik_orig_low = pm.joint(name="jIK_orig_Low_%s" % self.suffix, p=self.elbow_pos, radius=0.5)
        self.j_ik_orig_low_end = pm.joint(name="jIK_orig_LowEnd_%s" % self.suffix, p=self.hand_pos, radius=0.5)

        # Single Chain IK
        pm.select(d=True)
        self.j_ik_sc_up = pm.joint(name="jIK_SC_Up_%s" % self.suffix, p=self.shoulder_pos, radius=1.0)
        self.j_ik_sc_low = pm.joint(name="jIK_SC_Low_%s" % self.suffix, p=self.elbow_pos, radius=1.0)
        self.j_ik_sc_low_end = pm.joint(name="jIK_SC_LowEnd_%s" % self.suffix, p=self.hand_pos, radius=1)

        # Rotate Plane IK
        pm.select(d=True)
        self.j_ik_rp_up = pm.joint(name="jIK_RP_Up_%s" % self.suffix, p=self.shoulder_pos, radius=1.5)
        self.j_ik_rp_low = pm.joint(name="jIK_RP_Low_%s" % self.suffix, p=self.elbow_pos, radius=1.5)
        self.j_ik_rp_low_end = pm.joint(name="jIK_RP_LowEnd_%s" % self.suffix, p=self.hand_pos, radius=1.5)

        pm.select(d=True)

        # orientations
        extra.orientJoints([self.j_ik_orig_up, self.j_ik_orig_low, self.j_ik_orig_low_end],
                           localMoveAxis=(dt.Vector(self.up_axis)),
                           mirrorAxis=(self.sideMult, 0.0, 0.0), upAxis=self.sideMult * (dt.Vector(self.up_axis)))

        extra.orientJoints([self.j_ik_sc_up, self.j_ik_sc_low, self.j_ik_sc_low_end],
                           localMoveAxis=(dt.Vector(self.up_axis)),
                           mirrorAxis=(self.sideMult, 0.0, 0.0), upAxis=self.sideMult * (dt.Vector(self.up_axis)))

        extra.orientJoints([self.j_ik_rp_up, self.j_ik_rp_low, self.j_ik_rp_low_end],
                           localMoveAxis=(dt.Vector(self.up_axis)),
                           mirrorAxis=(self.sideMult, 0.0, 0.0), upAxis=self.sideMult * (dt.Vector(self.up_axis)))

        # FK Joints
        pm.select(d=True)
        self.j_fk_up = pm.joint(name="jFK_Up_%s" % self.suffix, p=self.shoulder_pos, radius=2.0)
        self.j_fk_low = pm.joint(name="jFK_Low_%s" % self.suffix, p=self.elbow_pos, radius=2.0)
        self.j_fk_low_end = pm.joint(name="jFK_LowEnd_%s" % self.suffix, p=self.hand_pos, radius=2.0)

        extra.orientJoints([self.j_fk_up, self.j_fk_low, self.j_fk_low_end], localMoveAxis=(dt.Vector(self.up_axis)),
                           mirrorAxis=(self.sideMult, 0.0, 0.0), upAxis=self.sideMult * (dt.Vector(self.up_axis)))

        # Hand joint
        self.j_def_hand = pm.joint(name="jDef_Hand_%s" % self.suffix, p=self.hand_pos, radius=1.0)
        self.sockets.append(self.j_def_hand)

        # re-orient single joints
        extra.alignToAlter(self.j_collar_end, self.j_fk_up, mode=2)
        pm.makeIdentity(self.j_collar_end, a=True)
        extra.alignToAlter(self.j_def_elbow, self.j_fk_low, mode=2)
        pm.makeIdentity(self.j_def_elbow, a=True)
        extra.alignToAlter(self.j_def_hand, self.j_fk_low_end, mode=2)
        pm.makeIdentity(self.j_def_hand, a=True)

        pm.parent(self.j_def_elbow, self.scaleGrp)
        pm.parent(self.j_fk_up, self.scaleGrp)

        self.deformerJoints += [self.j_def_elbow, self.j_def_collar, self.j_def_hand]

        # self.scaleGrp.jointVis >> self.j_def_elbow.v
        # self.scaleGrp.jointVis >> self.j_def_collar.v
        # self.scaleGrp.jointVis >> self.j_def_hand.v

        self.scaleGrp.rigVis >> self.j_fk_up.v

    def createControllers(self):

        ## shoulder controller
        shouldercont_scale = (self.init_shoulder_dist / 2, self.init_shoulder_dist / 2, self.init_shoulder_dist / 2)
        self.cont_shoulder = icon.shoulder("cont_Shoulder_%s" % self.suffix, shouldercont_scale)
        pm.setAttr("{0}.s{1}".format(self.cont_shoulder, "y"), self.sideMult)
        pm.makeIdentity(self.cont_shoulder, a=True)
        extra.alignAndAim(self.cont_shoulder, targetList=[self.j_def_collar], aimTargetList=[self.j_collar_end],
                          upVector=self.up_axis)

        self.cont_shoulder_off = extra.createUpGrp(self.cont_shoulder, "OFF")
        self.cont_shoulder_ore = extra.createUpGrp(self.cont_shoulder, "ORE")
        self.cont_shoulder_auto = extra.createUpGrp(self.cont_shoulder, "Auto")

        # pm.setAttr("{0}.s{1}".format(self.cont_shoulder_pos, "z"), self.sideMult)
        ## IK hand controller
        ik_cont_scale = (self.init_lower_arm_dist / 3, self.init_lower_arm_dist / 3, self.init_lower_arm_dist / 3)
        self.cont_IK_hand = icon.circle("cont_IK_hand_%s" % self.suffix, ik_cont_scale, normal=(1, 0, 0))
        extra.alignToAlter(self.cont_IK_hand, self.j_fk_low_end, mode=2)

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
            (((self.init_upper_arm_dist + self.init_lower_arm_dist) / 2) / 10),
            (((self.init_upper_arm_dist + self.init_lower_arm_dist) / 2) / 10),
            (((self.init_upper_arm_dist + self.init_lower_arm_dist) / 2) / 10)
        )
        self.cont_Pole = icon.plus("cont_Pole_%s" % self.suffix, polecont_scale, normal=(0, 0, 1))
        offset_mag_pole = ((self.init_upper_arm_dist + self.init_lower_arm_dist) / 4)
        # offset_vector_pole = extra.getBetweenVector(elbow_ref, [shoulder_ref, hand_ref])
        offset_vector_pole = extra.getBetweenVector(self.j_def_elbow, [self.j_collar_end, self.j_def_hand])

        extra.alignAndAim(self.cont_Pole,
                          targetList=[self.j_def_elbow],
                          aimTargetList=[self.j_collar_end, self.j_def_hand],
                          upVector=self.up_axis,
                          translateOff=(offset_vector_pole * offset_mag_pole)
                          )

        self.cont_pole_off = extra.createUpGrp(self.cont_Pole, "OFF")
        self.cont_pole_vis = extra.createUpGrp(self.cont_Pole, "VIS")

        ## FK UP Arm Controller

        fk_up_arm_scale = (self.init_upper_arm_dist / 2, self.init_upper_arm_dist / 8, self.init_upper_arm_dist / 8)

        self.cont_fk_up_arm = icon.cube("cont_FK_UpArm_%s" % self.suffix, fk_up_arm_scale)

        # move the pivot to the bottom
        pm.xform(self.cont_fk_up_arm, piv=(self.sideMult * -(self.init_upper_arm_dist / 2), 0, 0), ws=True)

        # move the controller to the shoulder
        extra.alignToAlter(self.cont_fk_up_arm, self.j_fk_up, mode=2)

        self.cont_fk_up_arm_off = extra.createUpGrp(self.cont_fk_up_arm, "OFF")
        self.cont_fk_up_arm_ore = extra.createUpGrp(self.cont_fk_up_arm, "ORE")
        pm.xform(self.cont_fk_up_arm_off, piv=self.shoulder_pos, ws=True)
        pm.xform(self.cont_fk_up_arm_ore, piv=self.shoulder_pos, ws=True)

        ## FK LOW Arm Controller
        fk_low_arm_scale = (self.init_lower_arm_dist / 2, self.init_lower_arm_dist / 8, self.init_lower_arm_dist / 8)
        self.cont_fk_low_arm = icon.cube("cont_FK_LowArm_%s" % self.suffix, fk_low_arm_scale)

        # move the pivot to the bottom
        pm.xform(self.cont_fk_low_arm, piv=(self.sideMult * -(self.init_lower_arm_dist / 2), 0, 0), ws=True)

        # align position and orientation to the joint
        extra.alignToAlter(self.cont_fk_low_arm, self.j_fk_low, mode=2)

        self.cont_fk_low_arm_off = extra.createUpGrp(self.cont_fk_low_arm, "OFF")
        self.cont_fk_low_arm_ore = extra.createUpGrp(self.cont_fk_low_arm, "ORE")
        pm.xform(self.cont_fk_low_arm_off, piv=self.elbow_pos, ws=True)
        pm.xform(self.cont_fk_low_arm_ore, piv=self.elbow_pos, ws=True)

        ## FK HAND Controller
        fk_cont_scale = (self.init_lower_arm_dist / 5, self.init_lower_arm_dist / 5, self.init_lower_arm_dist / 5)
        self.cont_fk_hand = icon.cube("cont_FK_Hand_%s" % self.suffix, fk_cont_scale)
        extra.alignToAlter(self.cont_fk_hand, self.j_def_hand, mode=2)

        self.cont_fk_hand_off = extra.createUpGrp(self.cont_fk_hand, "OFF")
        self.cont_fk_hand_pos = extra.createUpGrp(self.cont_fk_hand, "POS")
        self.cont_fk_hand_ore = extra.createUpGrp(self.cont_fk_hand, "ORE")

        # FK-IK SWITCH Controller
        icon_scale = self.init_upper_arm_dist / 4
        self.cont_fk_ik, self.fk_ik_rvs = icon.fkikSwitch(("cont_FK_IK_%s" % self.suffix),
                                                          (icon_scale, icon_scale, icon_scale))
        extra.alignAndAim(self.cont_fk_ik, targetList=[self.j_def_hand], aimTargetList=[self.j_def_elbow],
                          upVector=self.up_axis, rotateOff=(0, 180, 0))
        pm.move(self.cont_fk_ik, (dt.Vector(self.up_axis) * (icon_scale * 2)), r=True)
        self.cont_fk_ik_pos = extra.createUpGrp(self.cont_fk_ik, "POS")

        pm.setAttr("{0}.s{1}".format(self.cont_fk_ik, "x"), self.sideMult)

        # controller for twist orientation alignment
        pm.addAttr(self.cont_fk_ik, shortName="autoShoulder", longName="Auto_Shoulder", defaultValue=1.0, at="float",
                   minValue=0.0, maxValue=1.0, k=True)
        pm.addAttr(self.cont_fk_ik, shortName="alignShoulder", longName="Align_Shoulder", defaultValue=1.0, at="float",
                   minValue=0.0, maxValue=1.0, k=True)

        pm.addAttr(self.cont_fk_ik, shortName="handAutoTwist", longName="Hand_Auto_Twist", defaultValue=1.0,
                   minValue=0.0,
                   maxValue=1.0, at="float", k=True)
        pm.addAttr(self.cont_fk_ik, shortName="handManualTwist", longName="Hand_Manual_Twist", defaultValue=0.0,
                   at="float",
                   k=True)

        pm.addAttr(self.cont_fk_ik, shortName="shoulderAutoTwist", longName="Shoulder_Auto_Twist", defaultValue=1.0,
                   minValue=0.0, maxValue=1.0, at="float", k=True)
        pm.addAttr(self.cont_fk_ik, shortName="shoulderManualTwist", longName="Shoulder_Manual_Twist", defaultValue=0.0,
                   at="float", k=True)

        pm.addAttr(self.cont_fk_ik, shortName="allowScaling", longName="Allow_Scaling", defaultValue=1.0, minValue=0.0,
                   maxValue=1.0, at="float", k=True)
        pm.addAttr(self.cont_fk_ik, at="enum", k=True, shortName="interpType", longName="Interp_Type", en="No_Flip:Average:Shortest:Longest:Cache", defaultValue=0)

        pm.addAttr(self.cont_fk_ik, shortName="tweakControls", longName="Tweak_Controls", defaultValue=0, at="bool")
        pm.setAttr(self.cont_fk_ik.tweakControls, cb=True)
        pm.addAttr(self.cont_fk_ik, shortName="fingerControls", longName="Finger_Controls", defaultValue=1, at="bool")
        pm.setAttr(self.cont_fk_ik.fingerControls, cb=True)

        ### Create MidLock controller

        midcont_scale = (self.init_lower_arm_dist / 4, self.init_lower_arm_dist / 4, self.init_lower_arm_dist / 4)
        self.cont_mid_lock = icon.star("cont_mid_%s" % self.suffix, midcont_scale, normal=(1, 0, 0))

        # extra.alignToAlter(cont_mid_lock, j_def_elbow, 2)
        extra.alignToAlter(self.cont_mid_lock, self.j_fk_low, 2)

        self.cont_mid_lock_ext = extra.createUpGrp(self.cont_mid_lock, "EXT")
        self.cont_mid_lock_pos = extra.createUpGrp(self.cont_mid_lock, "POS")
        self.cont_mid_lock_ave = extra.createUpGrp(self.cont_mid_lock, "AVE")

        pm.parent(self.cont_shoulder_off, self.scaleGrp)
        pm.parent(self.cont_fk_up_arm_off, self.scaleGrp)
        pm.parent(self.cont_fk_low_arm_off, self.scaleGrp)
        pm.parent(self.cont_fk_hand_off, self.scaleGrp)
        pm.parent(self.cont_mid_lock_ext, self.scaleGrp)
        pm.parent(self.cont_pole_off, self.scaleGrp)
        pm.parent(self.cont_fk_ik_pos, self.scaleGrp)
        pm.parent(self.cont_IK_OFF, self.limbGrp)

        nodesContVis = [self.cont_pole_off, self.cont_shoulder_off, self.cont_IK_OFF, self.cont_fk_hand_off,
                        self.cont_fk_ik_pos,
                        self.cont_fk_low_arm_off, self.cont_fk_up_arm_off, self.cont_mid_lock_pos]

        # for i in nodesContVis:
        #     self.scaleGrp.contVis >> i.v
        map(lambda x: pm.connectAttr(self.scaleGrp.contVis, x.v), nodesContVis)

        extra.colorize(self.cont_shoulder, self.colorCodes[0])
        extra.colorize(self.cont_IK_hand, self.colorCodes[0])
        extra.colorize(self.cont_Pole, self.colorCodes[0])
        extra.colorize(self.cont_fk_ik, self.colorCodes[0])
        extra.colorize(self.cont_fk_up_arm, self.colorCodes[0])
        extra.colorize(self.cont_fk_low_arm, self.colorCodes[0])
        extra.colorize(self.cont_fk_hand, self.colorCodes[0])
        extra.colorize(self.cont_mid_lock, self.colorCodes[1])

    def createRoots(self):

        self.master_root = pm.group(em=True, name="masterRoot_%s" % self.suffix)
        extra.alignTo(self.master_root, self.collar_ref, 0)
        pm.makeIdentity(self.master_root, a=True)

        # Create Start Lock

        self.start_lock = pm.spaceLocator(name="startLock_%s" % self.suffix)
        # extra.alignTo(start_lock, shoulder_ref, 2)
        extra.alignToAlter(self.start_lock, self.j_ik_orig_up, 2)
        self.start_lock_ore = extra.createUpGrp(self.start_lock, "Ore")
        self.start_lock_pos = extra.createUpGrp(self.start_lock, "Pos")
        self.start_lock_twist = extra.createUpGrp(self.start_lock, "AutoTwist")

        start_lock_weight = pm.parentConstraint(self.j_collar_end, self.start_lock, sr=("y", "z"), mo=False)

        pm.parentConstraint(self.start_lock, self.j_ik_sc_up, mo=False)
        pm.parentConstraint(self.start_lock, self.j_ik_rp_up, mo=False)

        # Create Midlock

        self.mid_lock = pm.spaceLocator(name="midLock_%s" % self.suffix)
        pm.parentConstraint(self.mid_lock, self.j_def_elbow)

        # extra.alignTo(self.mid_lock, self.cont_mid_lock, 0)

        pm.parentConstraint(self.cont_mid_lock, self.mid_lock, mo=False)

        # Create End Lock
        self.end_lock = pm.spaceLocator(name="endLock_%s" % self.suffix)
        extra.alignTo(self.end_lock, self.j_def_hand, 2)
        self.end_lock_ore = extra.createUpGrp(self.end_lock, "Ore")
        self.end_lock_pos = extra.createUpGrp(self.end_lock, "Pos")
        self.end_lock_twist = extra.createUpGrp(self.end_lock, "Twist")

        self.hand_lock = pm.spaceLocator(name="handLock_%s" % self.suffix)
        extra.alignTo(self.hand_lock, self.cont_fk_hand_off, 2)

        pm.parentConstraint(self.cont_fk_hand, self.hand_lock, mo=False)

        self.root_master = pm.spaceLocator(name="handMaster_%s" % self.suffix)
        extra.alignTo(self.root_master, self.j_def_hand, 2)

        pm.parent(self.j_def_hand, self.root_master)

        pm.pointConstraint(self.end_lock, self.root_master, mo=False)

        pm.parent(self.mid_lock, self.scaleGrp)
        pm.parent(self.hand_lock, self.scaleGrp)
        pm.parent(self.master_root, self.scaleGrp)
        pm.parent(self.root_master, self.scaleGrp)

        self.scaleGrp.rigVis >> self.end_lock_twist.v
        self.scaleGrp.rigVis >> self.start_lock_ore.v
        self.scaleGrp.rigVis >> self.mid_lock.v
        self.scaleGrp.rigVis >> self.master_root.v
        self.scaleGrp.rigVis >> self.hand_lock.v
        self.scaleGrp.rigVis >> (self.root_master.getShape()).v
        self.scaleGrp.rigVis >> (self.root_master.getShape()).v

    def createIKsetup(self):

        master_ik = pm.spaceLocator(name="masterIK_%s" % self.suffix)
        extra.alignTo(master_ik, self.j_def_hand, 0)

        # Create IK handles

        ik_handle_sc = pm.ikHandle(sj=self.j_ik_sc_up, ee=self.j_ik_sc_low_end, name="ikHandle_SC_%s" % self.suffix)
        ik_handle_rp = pm.ikHandle(sj=self.j_ik_rp_up, ee=self.j_ik_rp_low_end, name="ikHandle_RP_%s" % self.suffix,
                                   sol="ikRPsolver")

        pm.poleVectorConstraint(self.cont_Pole, ik_handle_rp[0])
        pm.aimConstraint(self.j_ik_rp_low, self.cont_Pole, u=self.up_axis, wut="vector")

        ### Create and constrain Distance Locators

        arm_start = pm.spaceLocator(name="armStart_%s" % self.suffix)
        pm.pointConstraint(self.start_lock, arm_start, mo=False)

        arm_end = pm.spaceLocator(name="armEnd_%s" % self.suffix)
        pm.pointConstraint(master_ik, arm_end, mo=False)

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
        pm.setAttr("%s.input1X" % self.initial_length_multip_sc, self.init_upper_arm_dist)
        pm.setAttr("%s.input1Y" % self.initial_length_multip_sc, self.init_lower_arm_dist)
        pm.setAttr("%s.operation" % initial_divide_sc, 2)

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
        arm_start.translate >> distance_sc.point1
        arm_end.translate >> distance_sc.point2
        distance_sc.distance >> ik_stretch_distance_clamp.inputR

        # ik_stretch_distance_clamp.outputR >> stretch_condition_sc.firstTerm
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

        invertedStrSC.outputX >> self.j_ik_sc_low.translateX
        invertedStrSC.outputY >> self.j_ik_sc_low_end.translateX

        invertedStrSC.outputX >> self.j_ik_rp_low.translateX
        invertedStrSC.outputY >> self.j_ik_rp_low_end.translateX

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

        self.cont_IK_hand.rotate >> self.j_ik_rp_low.rotate

        # Stretch Attributes Controller connections

        self.cont_IK_hand.sUpArm >> extra_scale_mult_sc.input2X
        self.cont_IK_hand.sLowArm >> extra_scale_mult_sc.input2Y
        self.cont_IK_hand.squash >> squashiness_sc.blender

        stretch_offset.output1D >> ik_stretch_distance_clamp.maxR
        self.cont_IK_hand.stretch >> ik_stretch_stretchiness_clamp.inputR

        self.cont_IK_hand.stretchLimit >> stretch_offset.input1D[2]

        self.ik_parent_grp = pm.group(name="IK_parentGRP_%s" % self.suffix, em=True)
        extra.alignTo(self.ik_parent_grp, self.j_def_hand, 2)

        pm.parentConstraint(self.cont_IK_hand, self.ik_parent_grp, mo=False)

        # parenting should be after the constraint
        pm.parent(ik_handle_sc[0], self.ik_parent_grp)
        pm.parent(ik_handle_rp[0], self.ik_parent_grp)
        pm.parent(master_ik, self.ik_parent_grp)

        blend_ore_ik_up = pm.createNode("blendColors", name="blendORE_IK_Up_%s" % self.suffix)
        self.j_ik_sc_up.rotate >> blend_ore_ik_up.color2
        self.j_ik_rp_up.rotate >> blend_ore_ik_up.color1
        blend_ore_ik_up.output >> self.j_ik_orig_up.rotate
        self.cont_IK_hand.polevector >> blend_ore_ik_up.blender

        blend_pos_ik_up = pm.createNode("blendColors", name="blendPOS_IK_Up_%s" % self.suffix)
        self.j_ik_sc_up.translate >> blend_pos_ik_up.color2
        self.j_ik_rp_up.translate >> blend_pos_ik_up.color1
        blend_pos_ik_up.output >> self.j_ik_orig_up.translate
        self.cont_IK_hand.polevector >> blend_pos_ik_up.blender

        blend_ore_ik_low = pm.createNode("blendColors", name="blendORE_IK_Low_%s" % self.suffix)
        self.j_ik_sc_low.rotate >> blend_ore_ik_low.color2
        self.j_ik_rp_low.rotate >> blend_ore_ik_low.color1
        # Weird bug with skinned character / use seperate connections
        # if there is no skincluster, it works ok, but adding a skin cluster misses 2 out of 3 rotation axis
        # Therefore make SEPERATE CONNECTIONS
        blend_ore_ik_low.outputR >> self.j_ik_orig_low.rotateX
        blend_ore_ik_low.outputG >> self.j_ik_orig_low.rotateY
        blend_ore_ik_low.outputB >> self.j_ik_orig_low.rotateZ
        self.cont_IK_hand.polevector >> blend_ore_ik_low.blender

        blend_pos_ik_low = pm.createNode("blendColors", name="blendPOS_IK_Low_%s" % self.suffix)
        self.j_ik_sc_low.translate >> blend_pos_ik_low.color2
        self.j_ik_rp_low.translate >> blend_pos_ik_low.color1
        blend_pos_ik_low.output >> self.j_ik_orig_low.translate
        self.cont_IK_hand.polevector >> blend_pos_ik_low.blender

        blend_ore_ik_low_end = pm.createNode("blendColors", name="blendORE_IK_LowEnd_%s" % self.suffix)
        self.j_ik_sc_low_end.rotate >> blend_ore_ik_low_end.color2
        self.j_ik_rp_low_end.rotate >> blend_ore_ik_low_end.color1
        # Weird bug with skinned character / use seperate connections
        # if there is no skincluster, it works ok, but adding a skin cluster misses 2 out of 3 rotation axis
        # Therefore make SEPERATE CONNECTIONS
        blend_ore_ik_low_end.outputR >> self.j_ik_orig_low_end.rotateX
        blend_ore_ik_low_end.outputG >> self.j_ik_orig_low_end.rotateY
        blend_ore_ik_low_end.outputB >> self.j_ik_orig_low_end.rotateZ
        self.cont_IK_hand.polevector >> blend_ore_ik_low_end.blender

        blend_pos_ik_low_end = pm.createNode("blendColors", name="blendPOS_IK_LowEnd_%s" % self.suffix)
        self.j_ik_sc_low_end.translate >> blend_pos_ik_low_end.color2
        self.j_ik_rp_low_end.translate >> blend_pos_ik_low_end.color1
        blend_pos_ik_low_end.output >> self.j_ik_orig_low_end.translate
        self.cont_IK_hand.polevector >> blend_pos_ik_low_end.blender

        pole_vector_rvs = pm.createNode("reverse", name="poleVector_Rvs_%s" % self.suffix)
        self.cont_IK_hand.polevector >> pole_vector_rvs.inputX
        self.cont_IK_hand.polevector >> self.cont_Pole.v

        pm.parent(self.j_ik_orig_up, self.master_root)
        pm.parent(self.j_ik_sc_up, self.master_root)
        pm.parent(self.j_ik_rp_up, self.master_root)

        # pm.select(cont_shoulder)

        pacon_locator_shou = pm.spaceLocator(name="paConLoc_%s" % self.suffix)
        extra.alignTo(pacon_locator_shou, self.j_def_collar, mode=2)

        j_def_pa_con = pm.parentConstraint(self.cont_shoulder, pacon_locator_shou, mo=False)

        pm.parent(arm_start, self.scaleGrp)
        pm.parent(arm_end, self.scaleGrp)
        pm.parent(self.ik_parent_grp, self.scaleGrp)
        pm.parent(self.start_lock_ore, self.scaleGrp)
        pm.parent(self.end_lock_ore, self.scaleGrp)

        pm.parent(pacon_locator_shou, self.scaleGrp)
        pm.parent(self.j_def_collar, pacon_locator_shou)

        self.scaleGrp.rigVis >> arm_start.v
        self.scaleGrp.rigVis >> arm_end.v
        self.scaleGrp.rigVis >> self.ik_parent_grp.v
        self.scaleGrp.rigVis >> pacon_locator_shou.getShape().v

    def createFKsetup(self):

        self.cont_fk_up_arm.scaleX >> self.j_fk_up.scaleX
        self.cont_fk_low_arm.scaleX >> self.j_fk_low.scaleX

        pm.orientConstraint(self.cont_fk_up_arm, self.j_fk_up, mo=False)
        pm.pointConstraint(self.start_lock, self.j_fk_up, mo=False)

        pm.orientConstraint(self.cont_fk_low_arm, self.j_fk_low, mo=False)

        pm.parentConstraint(self.j_collar_end, self.cont_fk_up_arm_off, sr=("x", "y", "z"), mo=False)

        # TODO : TAKE A LOOK TO THE OFFSET SOLUTION
        pm.parentConstraint(self.cont_fk_up_arm, self.cont_fk_low_arm_off, mo=True)

        pm.parentConstraint(self.cont_fk_low_arm, self.cont_fk_hand_pos, mo=True)

    def ikfkSwitching(self):

        self.fk_ik_rvs.outputX >> self.cont_fk_up_arm_ore.visibility
        self.fk_ik_rvs.outputX >> self.cont_fk_low_arm_ore.visibility

        self.cont_fk_ik.fk_ik >> self.cont_IK_hand.visibility

        self.cont_fk_ik.fk_ik >> self.cont_pole_vis.visibility

        mid_lock_pa_con_weight = pm.orientConstraint(self.j_ik_orig_low, self.j_fk_low, self.cont_mid_lock_pos,
                                                     mo=False)
        self.cont_fk_ik.fk_ik >> ("%s.%sW0" % (mid_lock_pa_con_weight, self.j_ik_orig_low))

        self.fk_ik_rvs.outputX >> ("%s.%sW1" % (mid_lock_pa_con_weight, self.j_fk_low))

        self.cont_fk_ik.interpType >> mid_lock_pa_con_weight.interpType

        mid_lock_po_con_weight = pm.pointConstraint(self.j_ik_orig_low, self.j_fk_low, self.cont_mid_lock_ave, mo=False)
        self.cont_fk_ik.fk_ik >> ("%s.%sW0" % (mid_lock_po_con_weight, self.j_ik_orig_low))

        self.fk_ik_rvs.outputX >> ("%s.%sW1" % (mid_lock_po_con_weight, self.j_fk_low))

        mid_lock_x_bln = pm.createNode("multiplyDivide", name="midLock_xBln_%s" % self.suffix)

        mid_lock_rot_xsw = pm.createNode("blendTwoAttr", name="midLock_rotXsw_%s" % self.suffix)
        self.j_ik_orig_low.rotateY >> mid_lock_rot_xsw.input[0]
        self.j_fk_low.rotateY >> mid_lock_rot_xsw.input[1]
        self.fk_ik_rvs.outputX >> mid_lock_rot_xsw.attributesBlender

        mid_lock_rot_xsw.output >> mid_lock_x_bln.input1Z

        pm.setAttr(mid_lock_x_bln.input2Z, 0.5)
        mid_lock_x_bln.outputZ >> self.cont_mid_lock_ave.rotateY

        end_lock_weight = pm.pointConstraint(self.j_ik_orig_low_end, self.j_fk_low_end, self.end_lock_pos, mo=False)
        self.cont_fk_ik.fk_ik >> ("%s.%sW0" % (end_lock_weight, self.j_ik_orig_low_end))

        self.fk_ik_rvs.outputX >> ("%s.%sW1" % (end_lock_weight, self.j_fk_low_end))

        # the following offset parent constraint is not important and wont cause any trouble since
        # it only affects the FK/IK icon
        pm.parentConstraint(self.end_lock, self.cont_fk_ik_pos, mo=True)
        # pm.parent(self.end_lock_ore, self.scaleGrp)

        # end_lock_rot = pm.parentConstraint(ik_parent_grp, cont_fk_hand, end_lock_twist, st=("x", "y", "z"), mo=True)
        end_lock_rot = pm.parentConstraint(self.ik_parent_grp, self.cont_fk_hand, self.end_lock_twist,
                                           st=("x", "y", "z"), mo=False)
        self.cont_fk_ik.fk_ik >> ("%s.%sW0" % (end_lock_rot, self.ik_parent_grp))
        self.fk_ik_rvs.outputX >> ("%s.%sW1" % (end_lock_rot, self.cont_fk_hand))
        # pm.setAttr(end_lock_rot.interpType, 0)
        self.cont_fk_ik.interpType >> end_lock_rot.interpType

        hand_ori_con = pm.parentConstraint(self.cont_IK_hand, self.hand_lock, self.root_master, st=("x", "y", "z"),
                                           mo=False)
        pm.setAttr(hand_ori_con.interpType, 0)

        self.cont_fk_ik.fk_ik >> ("%s.%sW0" % (hand_ori_con, self.cont_IK_hand))

        self.fk_ik_rvs.outputX >> ("%s.%sW1" % (hand_ori_con, self.hand_lock))

        self.fk_ik_rvs.outputX >> self.cont_fk_hand.v

        hand_sca_con = pm.createNode("blendColors", name="handScaCon_%s" % self.suffix)
        self.cont_IK_hand.scale >> hand_sca_con.color1
        self.cont_fk_hand.scale >> hand_sca_con.color2
        self.cont_fk_ik.fk_ik >> hand_sca_con.blender
        hand_sca_con.output >> self.root_master.scale

    def createDefJoints(self):
        # UPPER ARM RIBBON

        ribbon_upper_arm = rc.PowerRibbon()
        ribbon_upper_arm.createPowerRibbon(self.j_collar_end, self.j_def_elbow, "up_%s" % self.suffix, side=self.side,
                                           orientation=0, connectStartAim=False, upVector=self.up_axis)

        ribbon_start_pa_con_upper_arm_start = pm.parentConstraint(self.start_lock, ribbon_upper_arm.startConnection,
                                                                  mo=False)
        pm.parentConstraint(self.mid_lock, ribbon_upper_arm.endConnection, mo=False)

        # connect the elbow scaling
        self.cont_mid_lock.scale >> ribbon_upper_arm.endConnection.scale
        self.cont_mid_lock.scale >> self.j_def_elbow.scale

        pm.scaleConstraint(self.scaleGrp, ribbon_upper_arm.scaleGrp)

        ribbon_start_ori_con = pm.parentConstraint(self.j_ik_orig_up, self.j_fk_up, ribbon_upper_arm.startAim, mo=False,
                                                   skipTranslate=["x", "y", "z"])

        ribbon_start_ori_con2 = pm.parentConstraint(self.j_collar_end, ribbon_upper_arm.startAim, mo=False,
                                                    skipTranslate=["x", "y", "z"])

        self.cont_fk_ik.fk_ik >> ("%s.%sW0" % (ribbon_start_ori_con, self.j_ik_orig_up))
        self.fk_ik_rvs.outputX >> ("%s.%sW1" % (ribbon_start_ori_con, self.j_fk_up))

        pairBlendNode = pm.listConnections(ribbon_start_ori_con, d=True, t="pairBlend")[0]
        # disconnect the existing weight connection
        pm.disconnectAttr(pairBlendNode.w)
        # re-connect to the custom attribute
        self.cont_fk_ik.alignShoulder >> pairBlendNode.w

        # Rotate the shoulder connection bone 180 degrees for Right Alignment
        if self.side == "R":
            rightRBN_startupORE = pm.listRelatives(ribbon_upper_arm.startAim, children=True, type="transform")[0]
            pm.setAttr(rightRBN_startupORE.ry, 180)

        # AUTO AND MANUAL TWIST

        # auto
        auto_twist = pm.createNode("multiplyDivide", name="autoTwist_%s" % self.suffix)
        # cont_shoulder.autoTwist >> auto_twist.input2X
        self.cont_fk_ik.shoulderAutoTwist >> auto_twist.input2X
        ribbon_start_pa_con_upper_arm_start.constraintRotate >> auto_twist.input1

        # !!! The parent constrain override should be disconnected like this
        pm.disconnectAttr(
            ribbon_start_pa_con_upper_arm_start.constraintRotateX,
            ribbon_upper_arm.startConnection.rotateX
        )

        # manual
        add_manual_twist = pm.createNode("plusMinusAverage", name=("AddManualTwist_UpperArm_%s" % self.suffix))
        auto_twist.output >> add_manual_twist.input3D[0]
        self.cont_fk_ik.shoulderManualTwist >> add_manual_twist.input3D[1].input3Dx

        # connect to the joint
        add_manual_twist.output3D >> ribbon_upper_arm.startConnection.rotate

        # connect allowScaling
        self.cont_fk_ik.allowScaling >> ribbon_upper_arm.startConnection.scaleSwitch

        # LOWER ARM RIBBON

        ribbon_lower_arm = rc.PowerRibbon()
        ribbon_lower_arm.createPowerRibbon(self.j_def_elbow, self.j_def_hand, "low_%s" % self.suffix, side=self.side,
                                           orientation=0, upVector=self.up_axis)

        pm.parentConstraint(self.mid_lock, ribbon_lower_arm.startConnection, mo=False)
        ribbon_start_pa_con_lower_arm_end = pm.parentConstraint(self.end_lock, ribbon_lower_arm.endConnection, mo=False)

        # connect the elbow scaling
        self.cont_mid_lock.scale >> ribbon_lower_arm.startConnection.scale

        pm.scaleConstraint(self.scaleGrp, ribbon_lower_arm.scaleGrp)

        # AUTO AND MANUAL TWIST

        # auto
        auto_twist = pm.createNode("multiplyDivide", name="autoTwist_%s" % self.suffix)
        self.cont_fk_ik.handAutoTwist >> auto_twist.input2X
        ribbon_start_pa_con_lower_arm_end.constraintRotate >> auto_twist.input1

        # !!! The parent constrain override should be disconnected like this
        pm.disconnectAttr(ribbon_start_pa_con_lower_arm_end.constraintRotateX, ribbon_lower_arm.endConnection.rotateX)

        # manual
        add_manual_twist = pm.createNode("plusMinusAverage", name=("AddManualTwist_LowerArm_%s" % self.suffix))
        auto_twist.output >> add_manual_twist.input3D[0]
        self.cont_fk_ik.handManualTwist >> add_manual_twist.input3D[1].input3Dx

        # connect to the joint
        add_manual_twist.output3D >> ribbon_lower_arm.endConnection.rotate

        # connect allowScaling
        self.cont_fk_ik.allowScaling >> ribbon_lower_arm.startConnection.scaleSwitch

        # Volume Preservation Stuff
        vpExtraInput = pm.createNode("multiplyDivide", name="vpExtraInput_%s" % self.suffix)
        pm.setAttr(vpExtraInput.operation, 1)

        vpMidAverage = pm.createNode("plusMinusAverage", name="vpMidAverage_%s" % self.suffix)
        pm.setAttr(vpMidAverage.operation, 3)

        vpPowerMid = pm.createNode("multiplyDivide", name="vpPowerMid_%s" % self.suffix)
        pm.setAttr(vpPowerMid.operation, 3)
        vpInitLength = pm.createNode("multiplyDivide", name="vpInitLength_%s" % self.suffix)
        pm.setAttr(vpInitLength.operation, 2)

        vpPowerUpperLeg = pm.createNode("multiplyDivide", name="vpPowerUpperLeg_%s" % self.suffix)
        pm.setAttr(vpPowerUpperLeg.operation, 3)

        vpPowerLowerLeg = pm.createNode("multiplyDivide", name="vpPowerLowerLeg_%s" % self.suffix)
        pm.setAttr(vpPowerLowerLeg.operation, 3)
        #
        vpUpperLowerReduce = pm.createNode("multDoubleLinear", name="vpUpperLowerReduce_%s" % self.suffix)
        pm.setAttr(vpUpperLowerReduce.input2, 0.5)
        #
        # vp knee branch
        vpExtraInput.output >> ribbon_lower_arm.startConnection.scale
        vpExtraInput.output >> ribbon_upper_arm.endConnection.scale
        vpExtraInput.output >> self.j_def_elbow.scale
        self.cont_mid_lock.scale >> vpExtraInput.input1

        vpMidAverage.output1D >> vpExtraInput.input2X
        vpMidAverage.output1D >> vpExtraInput.input2Y
        vpMidAverage.output1D >> vpExtraInput.input2Z

        vpPowerMid.outputX >> vpMidAverage.input1D[0]
        vpPowerMid.outputY >> vpMidAverage.input1D[1]

        vpInitLength.outputX >> vpPowerMid.input1X
        vpInitLength.outputY >> vpPowerMid.input1Y
        self.cont_IK_hand.volume >> vpPowerMid.input2X
        self.cont_IK_hand.volume >> vpPowerMid.input2Y
        self.initial_length_multip_sc.outputX >> vpInitLength.input1X
        self.initial_length_multip_sc.outputY >> vpInitLength.input1Y
        self.stretchiness_sc.color1R >> vpInitLength.input2X
        self.stretchiness_sc.color1G >> vpInitLength.input2Y

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

        pm.parent(ribbon_upper_arm.scaleGrp, self.nonScaleGrp)
        pm.parent(ribbon_upper_arm.nonScaleGrp, self.nonScaleGrp)
        pm.parent(ribbon_lower_arm.scaleGrp, self.nonScaleGrp)
        pm.parent(ribbon_lower_arm.nonScaleGrp, self.nonScaleGrp)

        self.cont_fk_ik.tweakControls >> self.cont_mid_lock.v
        tweakConts = ribbon_upper_arm.middleCont + ribbon_lower_arm.middleCont
        # for i in tweakConts:
        #     self.cont_fk_ik.tweakControls >> i.v
        map(lambda x: pm.connectAttr(self.cont_fk_ik.tweakControls, x.v), tweakConts)

        self.scaleGrp.contVis >> ribbon_upper_arm.scaleGrp.v
        self.scaleGrp.contVis >> ribbon_lower_arm.scaleGrp.v

        self.deformerJoints += ribbon_lower_arm.deformerJoints + ribbon_upper_arm.deformerJoints

        map(lambda x: pm.connectAttr(self.scaleGrp.jointVis, x.v), self.deformerJoints)
        map(lambda x: pm.connectAttr(self.scaleGrp.rigVis, x.v), ribbon_lower_arm.toHide)
        map(lambda x: pm.connectAttr(self.scaleGrp.rigVis, x.v), ribbon_upper_arm.toHide)

        # for i in self.deformerJoints:
        #     self.scaleGrp.jointVis >> i.v
        # for i in ribbon_lower_arm.toHide:
        #     self.scaleGrp.rigVis >> i.v
        # for i in ribbon_upper_arm.toHide:
        #     self.scaleGrp.rigVis >> i.v

        extra.colorize(ribbon_upper_arm.middleCont, self.colorCodes[1])
        extra.colorize(ribbon_lower_arm.middleCont, self.colorCodes[1])

    def createAngleExtractors(self):
        # IK Angle Extractor
        angleExt_Root_IK = pm.spaceLocator(name="angleExt_Root_IK_%s" % self.suffix)
        angleExt_Fixed_IK = pm.spaceLocator(name="angleExt_Fixed_IK_%s" % self.suffix)
        angleExt_Float_IK = pm.spaceLocator(name="angleExt_Float_IK_%s" % self.suffix)
        pm.parent(angleExt_Fixed_IK, angleExt_Float_IK, angleExt_Root_IK)

        pm.parentConstraint(self.limbPlug, angleExt_Root_IK, mo=False)
        pm.parentConstraint(self.cont_IK_hand, angleExt_Fixed_IK, mo=False)
        extra.alignToAlter(angleExt_Float_IK, self.j_def_collar, 2)
        pm.move(angleExt_Float_IK, (0,self.sideMult*5,0), objectSpace=True)

        angleNodeIK = pm.createNode("angleBetween", name="angleBetweenIK_%s" % self.suffix)
        angleRemapIK = pm.createNode("remapValue", name="angleRemapIK_%s" % self.suffix)
        angleMultIK = pm.createNode("multDoubleLinear", name="angleMultIK_%s" % self.suffix)

        angleExt_Fixed_IK.translate >> angleNodeIK.vector1
        angleExt_Float_IK.translate >> angleNodeIK.vector2

        angleNodeIK.angle >> angleRemapIK.inputValue
        pm.setAttr(angleRemapIK.inputMin, pm.getAttr(angleNodeIK.angle))
        pm.setAttr(angleRemapIK.inputMax, 0)
        pm.setAttr(angleRemapIK.outputMin, 0)
        pm.setAttr(angleRemapIK.outputMax, pm.getAttr(angleNodeIK.angle))

        angleRemapIK.outValue >> angleMultIK.input1
        pm.setAttr(angleMultIK.input2, 0.5)

        # FK Angle Extractor
        angleRemapFK = pm.createNode("remapValue", name="angleRemapFK_%s" % self.suffix)
        angleMultFK = pm.createNode("multDoubleLinear", name="angleMultFK_%s" % self.suffix)

        self.cont_fk_up_arm.rotateZ >> angleRemapFK.inputValue
        pm.setAttr(angleRemapFK.inputMin, 0)
        pm.setAttr(angleRemapFK.inputMax, 90)
        pm.setAttr(angleRemapFK.outputMin, 0)
        pm.setAttr(angleRemapFK.outputMax, 90)

        angleRemapFK.outValue >> angleMultFK.input1
        pm.setAttr(angleMultFK.input2, 0.5)


        # create blend attribute and global Mult
        angleExt_blend = pm.createNode("blendTwoAttr", name="angleExt_blend_%s" % self.suffix)
        angleGlobal = pm.createNode("multDoubleLinear", name="angleGlobal_mult_%s" % self.suffix)

        self.cont_fk_ik.fk_ik >> angleExt_blend.attributesBlender
        angleMultFK.output >> angleExt_blend.input[0]
        angleMultIK.output >> angleExt_blend.input[1]

        angleExt_blend.output >> angleGlobal.input1
        self.cont_fk_ik.autoShoulder >> angleGlobal.input2

        angleGlobal.output >> self.cont_shoulder_auto.rotateZ

        pm.parent(angleExt_Root_IK, self.scaleGrp)
        self.scaleGrp.rigVis >> angleExt_Root_IK.v
        return


    def roundUp(self):
        pm.parentConstraint(self.limbPlug, self.scaleGrp, mo=False)

        pm.setAttr(self.scaleGrp.rigVis, 0)

        extra.lockAndHide(self.cont_IK_hand, ["v"])
        extra.lockAndHide(self.cont_Pole, ["rx", "ry", "rz", "sx", "sy", "sz", "v"])
        extra.lockAndHide(self.cont_mid_lock, ["v"])
        extra.lockAndHide(self.cont_fk_ik, ["sx", "sy", "sz", "v"])
        extra.lockAndHide(self.cont_fk_hand, ["tx", "ty", "tz", "v"])
        extra.lockAndHide(self.cont_fk_low_arm, ["tx", "ty", "tz", "sy", "sz", "v"])
        extra.lockAndHide(self.cont_fk_up_arm, ["tx", "ty", "tz", "sy", "sz", "v"])
        extra.lockAndHide(self.cont_shoulder, ["sx", "sy", "sz", "v"])

        self.scaleConstraints = [self.scaleGrp, self.cont_IK_OFF]
        self.anchors = [(self.cont_IK_hand, "parent", 1, None), (self.cont_Pole, "parent", 1, None)]

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

