from maya import cmds
import maya.api.OpenMaya as om
from trigger.library import functions as extra
from trigger.library import controllers as ic
from trigger.library import ribbon as rc
from trigger.core import feedback
FEEDBACK = feedback.Feedback(__name__)

LIMB_DATA = {
        "members": ["Collar", "Shoulder", "Elbow", "Hand"],
        "properties": [],
        "multi_guide": None,
        "sided": True,
    }

class Arm(object):
    def __init__(self, build_data=None, inits=None, suffix="", *args, **kwargs):
        super(Arm, self).__init__()
        if build_data:
            self.collar_ref = build_data["Collar"]
            self.shoulder_ref = build_data["Shoulder"]
            self.elbow_ref = build_data["Elbow"]
            self.hand_ref = build_data["Hand"]
        elif inits:
            if len(inits) < 4:
                cmds.error("Missing Joints for Arm Setup")
                return

            if not type(inits) == dict and not type(inits) == list:
                cmds.error("Init joints must be list or dictionary")
                return

            if type(inits) == dict:
                # reinitialize the dictionary for easy use
                self.collar_ref = inits["Collar"]
                self.shoulder_ref = inits["Shoulder"]
                self.elbow_ref = inits["Elbow"]
                self.hand_ref = inits["Hand"]
            else:
                self.collar_ref = inits[0]
                self.shoulder_ref = inits[1]
                self.elbow_ref = inits[2]
                self.hand_ref = inits[3]
        else:
            FEEDBACK.throw_error("Class needs either build_data or arm inits to be constructed")

        self.collar_pos = extra.getWorldTranslation(self.collar_ref)
        self.shoulder_pos = extra.getWorldTranslation(self.shoulder_ref)
        self.elbow_pos = extra.getWorldTranslation(self.elbow_ref)
        self.hand_pos = extra.getWorldTranslation(self.hand_ref)

        # get distances
        self.init_shoulder_dist = extra.getDistance(self.collar_ref, self.shoulder_ref)
        self.init_upper_arm_dist = extra.getDistance(self.shoulder_ref, self.elbow_ref)
        self.init_lower_arm_dist = extra.getDistance(self.elbow_ref, self.hand_ref)

        self.up_axis, self.mirror_axis, self.look_axis = extra.getRigAxes(self.collar_ref)

        # get the properties from the root
        self.useRefOrientation = cmds.getAttr("%s.useRefOri" % self.collar_ref)
        self.side = extra.get_joint_side(self.collar_ref)
        self.sideMult = -1 if self.side == "R" else 1

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
        extra.alignTo(self.scaleGrp, self.collar_ref, position=True, rotation=False)
        self.nonScaleGrp = cmds.group(name="NonScaleGrp_%s" % self.suffix, em=True)

        cmds.addAttr(self.scaleGrp, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True)
        cmds.addAttr(self.scaleGrp, at="bool", ln="Joints_Visibility", sn="jointVis", defaultValue=True)
        cmds.addAttr(self.scaleGrp, at="bool", ln="Rig_Visibility", sn="rigVis", defaultValue=True)
        # make the created attributes visible in the channelbox
        cmds.setAttr("{0}.contVis".format(self.scaleGrp), cb=True)
        cmds.setAttr("{0}.jointVis".format(self.scaleGrp), cb=True)
        cmds.setAttr("{0}.rigVis".format(self.scaleGrp), cb=True)

        cmds.parent(self.scaleGrp, self.limbGrp)
        cmds.parent(self.nonScaleGrp, self.limbGrp)

    def createJoints(self):
        # Create Limb Plug
        cmds.select(d=True)
        self.limbPlug = cmds.joint(name="jPlug_%s" % self.suffix, p=self.collar_pos, radius=3)

        # Shoulder Joints
        cmds.select(d=True)
        self.j_def_collar = cmds.joint(name="jDef_Collar_%s" % self.suffix, p=self.collar_pos, radius=1.5)
        self.sockets.append(self.j_def_collar)
        self.j_collar_end = cmds.joint(name="j_CollarEnd_%s" % self.suffix, p=self.shoulder_pos, radius=1.5)
        self.sockets.append(self.j_collar_end)

        if not self.useRefOrientation:
            extra.orientJoints([self.j_def_collar, self.j_collar_end], worldUpAxis=(self.look_axis), upAxis=(0, 1, 0), reverseAim=self.sideMult, reverseUp=self.sideMult)
        else:
            extra.alignTo(self.j_def_collar, self.collar_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_def_collar, a=True)
            extra.alignTo(self.j_collar_end, self.shoulder_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_collar_end, a=True)


        cmds.select(d=True)
        self.j_def_elbow = cmds.joint(name="jDef_elbow_%s" % self.suffix, p=self.elbow_pos, radius=1.5)
        self.sockets.append(self.j_def_elbow)

        # IK Joints
        # Follow IK Chain
        cmds.select(d=True)
        self.j_ik_orig_up = cmds.joint(name="jIK_orig_Up_%s" % self.suffix, p=self.shoulder_pos, radius=0.5)
        self.j_ik_orig_low = cmds.joint(name="jIK_orig_Low_%s" % self.suffix, p=self.elbow_pos, radius=0.5)
        self.j_ik_orig_low_end = cmds.joint(name="jIK_orig_LowEnd_%s" % self.suffix, p=self.hand_pos, radius=0.5)

        # Single Chain IK
        cmds.select(d=True)
        self.j_ik_sc_up = cmds.joint(name="jIK_SC_Up_%s" % self.suffix, p=self.shoulder_pos, radius=1.0)
        self.j_ik_sc_low = cmds.joint(name="jIK_SC_Low_%s" % self.suffix, p=self.elbow_pos, radius=1.0)
        self.j_ik_sc_low_end = cmds.joint(name="jIK_SC_LowEnd_%s" % self.suffix, p=self.hand_pos, radius=1)

        # Rotate Plane IK
        cmds.select(d=True)
        self.j_ik_rp_up = cmds.joint(name="jIK_RP_Up_%s" % self.suffix, p=self.shoulder_pos, radius=1.5)
        self.j_ik_rp_low = cmds.joint(name="jIK_RP_Low_%s" % self.suffix, p=self.elbow_pos, radius=1.5)
        self.j_ik_rp_low_end = cmds.joint(name="jIK_RP_LowEnd_%s" % self.suffix, p=self.hand_pos, radius=1.5)

        cmds.select(d=True)


        if not self.useRefOrientation:
            extra.orientJoints([self.j_ik_orig_up, self.j_ik_orig_low, self.j_ik_orig_low_end], worldUpAxis=(self.look_axis), upAxis=(0, 1, 0), reverseAim=self.sideMult, reverseUp=self.sideMult)
        else:
            extra.alignTo(self.j_ik_orig_up, self.shoulder_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_orig_up, a=True)

            extra.alignTo(self.j_ik_orig_low, self.elbow_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_orig_low, a=True)

            extra.alignTo(self.j_ik_orig_low_end, self.hand_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_orig_low_end, a=True)


        if not self.useRefOrientation:
            extra.orientJoints([self.j_ik_sc_up, self.j_ik_sc_low, self.j_ik_sc_low_end], worldUpAxis=(self.look_axis), upAxis=(0, 1, 0), reverseAim=self.sideMult, reverseUp=self.sideMult)
        else:
            extra.alignTo(self.j_ik_sc_up, self.shoulder_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_sc_up, a=True)

            extra.alignTo(self.j_ik_sc_low, self.elbow_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_sc_low, a=True)

            extra.alignTo(self.j_ik_sc_low_end, self.hand_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_sc_low_end, a=True)

        if not self.useRefOrientation:
            extra.orientJoints([self.j_ik_rp_up, self.j_ik_rp_low, self.j_ik_rp_low_end], worldUpAxis=(self.look_axis), upAxis=(0, 1, 0), reverseAim=self.sideMult, reverseUp=self.sideMult)
        else:
            extra.alignTo(self.j_ik_rp_up, self.shoulder_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_rp_up, a=True)

            extra.alignTo(self.j_ik_rp_low, self.elbow_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_rp_low, a=True)

            extra.alignTo(self.j_ik_rp_low_end, self.hand_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_rp_low_end, a=True)

        # FK Joints
        cmds.select(d=True)
        self.j_fk_up = cmds.joint(name="jFK_Up_%s" % self.suffix, p=self.shoulder_pos, radius=2.0)
        self.j_fk_low = cmds.joint(name="jFK_Low_%s" % self.suffix, p=self.elbow_pos, radius=2.0)
        self.j_fk_low_end = cmds.joint(name="jFK_LowEnd_%s" % self.suffix, p=self.hand_pos, radius=2.0)

        if not self.useRefOrientation:
            extra.orientJoints([self.j_fk_up, self.j_fk_low, self.j_fk_low_end], worldUpAxis=(self.look_axis), upAxis=(0, 1, 0), reverseAim=self.sideMult, reverseUp=self.sideMult)
        else:
            extra.alignTo(self.j_fk_up, self.shoulder_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_fk_up, a=True)

            extra.alignTo(self.j_fk_low, self.elbow_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_fk_low, a=True)

            extra.alignTo(self.j_fk_low_end, self.hand_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_fk_low_end, a=True)

        # Hand joint
        self.j_def_hand = cmds.joint(name="jDef_Hand_%s" % self.suffix, p=self.hand_pos, radius=1.0)
        self.sockets.append(self.j_def_hand)

        # re-orient single joints
        extra.alignToAlter(self.j_collar_end, self.j_fk_up, 2)
        cmds.makeIdentity(self.j_collar_end, a=True)
        extra.alignToAlter(self.j_def_elbow, self.j_fk_low, 2)
        cmds.makeIdentity(self.j_def_elbow, a=True)
        extra.alignToAlter(self.j_def_hand, self.j_fk_low_end, 2)
        cmds.makeIdentity(self.j_def_hand, a=True)

        cmds.parent(self.j_def_elbow, self.scaleGrp)
        cmds.parent(self.j_fk_up, self.scaleGrp)

        self.deformerJoints += [self.j_def_elbow, self.j_def_collar, self.j_def_hand]

        cmds.connectAttr("{0}.rigVis".format(self.scaleGrp), "{0}.v".format(self.j_fk_up))

    def createControllers(self):
        icon = ic.Icon()

        ## shoulder controller
        shouldercont_scale = (self.init_shoulder_dist / 2, self.init_shoulder_dist / 2, self.init_shoulder_dist / 2)
        # self.cont_shoulder = icon.shoulder("cont_Shoulder_%s" % self.suffix, shouldercont_scale)
        self.cont_shoulder, dmp = icon.createIcon("Shoulder", iconName="%s_Shoulder_cont" % self.suffix, scale=shouldercont_scale, normal=(0,0,-self.sideMult))
        # cmds.setAttr("{0}.s{1}".format(self.cont_shoulder, "y"), self.sideMult)
        cmds.makeIdentity(self.cont_shoulder, a=True)
        # extra.alignAndAim(self.cont_shoulder, targetList=[self.j_def_collar], aimTargetList=[self.j_collar_end],
        #                   upVector=self.up_axis)
        extra.alignToAlter(self.cont_shoulder, self.j_def_collar, mode=2)

        self.cont_shoulder_off = extra.createUpGrp(self.cont_shoulder, "OFF")
        self.cont_shoulder_ore = extra.createUpGrp(self.cont_shoulder, "ORE")
        self.cont_shoulder_auto = extra.createUpGrp(self.cont_shoulder, "Auto")

        # cmds.setAttr("{0}.s{1}".format(self.cont_shoulder_pos, "z"), self.sideMult)
        ## IK hand controller
        ik_cont_scale = (self.init_lower_arm_dist / 3, self.init_lower_arm_dist / 3, self.init_lower_arm_dist / 3)
        # self.cont_IK_hand = icon.circle("cont_IK_hand_%s" % self.suffix, ik_cont_scale, normal=(1, 0, 0))
        self.cont_IK_hand, dmp = icon.createIcon("Circle", iconName="%s_IK_hand_cont" % self.suffix, scale=ik_cont_scale, normal=(self.sideMult, 0, 0))
        extra.alignToAlter(self.cont_IK_hand, self.j_fk_low_end, mode=2)

        self.cont_IK_OFF = extra.createUpGrp(self.cont_IK_hand, "OFF")
        cont_ik_hand_ore = extra.createUpGrp(self.cont_IK_hand, "ORE")
        cont_ik_hand_pos = extra.createUpGrp(self.cont_IK_hand, "POS")

        cmds.addAttr(self.cont_IK_hand, shortName="polevector", longName="Pole_Vector", defaultValue=0.0, minValue=0.0,
                   maxValue=1.0,
                   at="double", k=True)
        cmds.addAttr(self.cont_IK_hand, shortName="sUpArm", longName="Scale_Upper_Arm", defaultValue=1.0, minValue=0.0,
                   at="double", k=True)
        cmds.addAttr(self.cont_IK_hand, shortName="sLowArm", longName="Scale_Lower_Arm", defaultValue=1.0, minValue=0.0,
                   at="double", k=True)
        cmds.addAttr(self.cont_IK_hand, shortName="squash", longName="Squash", defaultValue=0.0, minValue=0.0,
                   maxValue=1.0, at="double",
                   k=True)
        cmds.addAttr(self.cont_IK_hand, shortName="stretch", longName="Stretch", defaultValue=1.0, minValue=0.0,
                   maxValue=1.0, at="double",
                   k=True)
        cmds.addAttr(self.cont_IK_hand, shortName="stretchLimit", longName="StretchLimit", defaultValue=100.0,
                   minValue=0.0,
                   maxValue=1000.0, at="double",
                   k=True)
        cmds.addAttr(self.cont_IK_hand, shortName="softIK", longName="SoftIK", defaultValue=0.0, minValue=0.0,
                   maxValue=100.0, k=True)
        cmds.addAttr(self.cont_IK_hand, shortName="volume", longName="Volume_Preserve", defaultValue=0.0, at="double",
                   k=True)

        ## Pole Vector Controller
        polecont_scale = (
            (((self.init_upper_arm_dist + self.init_lower_arm_dist) / 2) / 10),
            (((self.init_upper_arm_dist + self.init_lower_arm_dist) / 2) / 10),
            (((self.init_upper_arm_dist + self.init_lower_arm_dist) / 2) / 10)
        )
        # self.cont_Pole = icon.plus("cont_Pole_%s" % self.suffix, polecont_scale, normal=(0, 0, 1))
        self.cont_Pole, dmp = icon.createIcon("Plus", iconName="%s_Pole_cont" % self.suffix, scale=polecont_scale, normal=(self.sideMult, 0, 0))
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

        # self.cont_fk_up_arm = icon.cube("cont_FK_UpArm_%s" % self.suffix, fk_up_arm_scale)
        self.cont_fk_up_arm, dmp = icon.createIcon("Cube", iconName="%s_FK_UpArm_cont" % self.suffix, scale=fk_up_arm_scale)

        # move the pivot to the bottom
        cmds.xform(self.cont_fk_up_arm, piv=(self.sideMult * -(self.init_upper_arm_dist / 2), 0, 0), ws=True)

        # move the controller to the shoulder
        extra.alignToAlter(self.cont_fk_up_arm, self.j_fk_up, mode=2)

        self.cont_fk_up_arm_off = extra.createUpGrp(self.cont_fk_up_arm, "OFF")
        self.cont_fk_up_arm_ore = extra.createUpGrp(self.cont_fk_up_arm, "ORE")
        cmds.xform(self.cont_fk_up_arm_off, piv=self.shoulder_pos, ws=True)
        cmds.xform(self.cont_fk_up_arm_ore, piv=self.shoulder_pos, ws=True)

        ## FK LOW Arm Controller
        fk_low_arm_scale = (self.init_lower_arm_dist / 2, self.init_lower_arm_dist / 8, self.init_lower_arm_dist / 8)
        # self.cont_fk_low_arm = icon.cube("cont_FK_LowArm_%s" % self.suffix, fk_low_arm_scale)
        self.cont_fk_low_arm, dmp = icon.createIcon("Cube", iconName="%s_FK_LowArm_cont" % self.suffix, scale=fk_low_arm_scale)

        # move the pivot to the bottom
        cmds.xform(self.cont_fk_low_arm, piv=(self.sideMult * -(self.init_lower_arm_dist / 2), 0, 0), ws=True)

        # align position and orientation to the joint
        extra.alignToAlter(self.cont_fk_low_arm, self.j_fk_low, mode=2)

        self.cont_fk_low_arm_off = extra.createUpGrp(self.cont_fk_low_arm, "OFF")
        self.cont_fk_low_arm_ore = extra.createUpGrp(self.cont_fk_low_arm, "ORE")
        cmds.xform(self.cont_fk_low_arm_off, piv=self.elbow_pos, ws=True)
        cmds.xform(self.cont_fk_low_arm_ore, piv=self.elbow_pos, ws=True)

        ## FK HAND Controller
        fk_cont_scale = (self.init_lower_arm_dist / 5, self.init_lower_arm_dist / 5, self.init_lower_arm_dist / 5)
        # self.cont_fk_hand = icon.cube("cont_FK_Hand_%s" % self.suffix, fk_cont_scale)
        self.cont_fk_hand, dmp = icon.createIcon("Cube", iconName="%s_FK_Hand_cont" % self.suffix, scale=fk_cont_scale)
        extra.alignToAlter(self.cont_fk_hand, self.j_def_hand, mode=2)

        self.cont_fk_hand_off = extra.createUpGrp(self.cont_fk_hand, "OFF")
        self.cont_fk_hand_pos = extra.createUpGrp(self.cont_fk_hand, "POS")
        self.cont_fk_hand_ore = extra.createUpGrp(self.cont_fk_hand, "ORE")

        # FK-IK SWITCH Controller
        icon_scale = self.init_upper_arm_dist / 4
        # self.cont_fk_ik, self.fk_ik_rvs = icon.fkikSwitch(("cont_FK_IK_%s" % self.suffix), (icon_scale, icon_scale, icon_scale))
        self.cont_fk_ik, self.fk_ik_rvs = icon.createIcon("FkikSwitch", iconName="%s_FK_IK_cont" % self.suffix, scale=(icon_scale, icon_scale, icon_scale))
        extra.alignAndAim(self.cont_fk_ik, targetList=[self.j_def_hand], aimTargetList=[self.j_def_elbow],
                          upVector=self.up_axis, rotateOff=(0, 180, 0))
        # cmds.move(self.cont_fk_ik, (dt.Vector(self.up_axis) * (icon_scale * 2)), r=True)
        cmds.move((self.up_axis[0]*icon_scale*2), (self.up_axis[1]*icon_scale*2), (self.up_axis[2]*icon_scale*2), self.cont_fk_ik, r=True)

        self.cont_fk_ik_pos = extra.createUpGrp(self.cont_fk_ik, "POS")

        cmds.setAttr("{0}.s{1}".format(self.cont_fk_ik, "x"), self.sideMult)

        # controller for twist orientation alignment
        cmds.addAttr(self.cont_fk_ik, shortName="autoShoulder", longName="Auto_Shoulder", defaultValue=1.0, at="float",
                   minValue=0.0, maxValue=1.0, k=True)
        cmds.addAttr(self.cont_fk_ik, shortName="alignShoulder", longName="Align_Shoulder", defaultValue=1.0, at="float",
                   minValue=0.0, maxValue=1.0, k=True)

        cmds.addAttr(self.cont_fk_ik, shortName="handAutoTwist", longName="Hand_Auto_Twist", defaultValue=1.0,
                   minValue=0.0,
                   maxValue=1.0, at="float", k=True)
        cmds.addAttr(self.cont_fk_ik, shortName="handManualTwist", longName="Hand_Manual_Twist", defaultValue=0.0,
                   at="float",
                   k=True)

        cmds.addAttr(self.cont_fk_ik, shortName="shoulderAutoTwist", longName="Shoulder_Auto_Twist", defaultValue=1.0,
                   minValue=0.0, maxValue=1.0, at="float", k=True)
        cmds.addAttr(self.cont_fk_ik, shortName="shoulderManualTwist", longName="Shoulder_Manual_Twist", defaultValue=0.0,
                   at="float", k=True)

        cmds.addAttr(self.cont_fk_ik, shortName="allowScaling", longName="Allow_Scaling", defaultValue=1.0, minValue=0.0,
                   maxValue=1.0, at="float", k=True)
        cmds.addAttr(self.cont_fk_ik, at="enum", k=True, shortName="interpType", longName="Interp_Type", en="No_Flip:Average:Shortest:Longest:Cache", defaultValue=0)

        cmds.addAttr(self.cont_fk_ik, shortName="tweakControls", longName="Tweak_Controls", defaultValue=0, at="bool")
        cmds.setAttr("{0}.tweakControls".format(self.cont_fk_ik), cb=True)
        cmds.addAttr(self.cont_fk_ik, shortName="fingerControls", longName="Finger_Controls", defaultValue=1, at="bool")
        cmds.setAttr("{0}.fingerControls".format(self.cont_fk_ik), cb=True)

        ### Create MidLock controller

        midcont_scale = (self.init_lower_arm_dist / 4, self.init_lower_arm_dist / 4, self.init_lower_arm_dist / 4)
        # self.cont_mid_lock = icon.star("cont_mid_%s" % self.suffix, midcont_scale, normal=(1, 0, 0))
        self.cont_mid_lock, dmp = icon.createIcon("Star", iconName="%s_mid_cont" % self.suffix, scale=midcont_scale, normal=(self.sideMult, 0, 0))

        # extra.alignToAlter(cont_mid_lock, j_def_elbow, 2)
        extra.alignToAlter(self.cont_mid_lock, self.j_fk_low, 2)

        self.cont_mid_lock_ext = extra.createUpGrp(self.cont_mid_lock, "EXT")
        self.cont_mid_lock_pos = extra.createUpGrp(self.cont_mid_lock, "POS")
        self.cont_mid_lock_ave = extra.createUpGrp(self.cont_mid_lock, "AVE")

        cmds.parent(self.cont_shoulder_off, self.scaleGrp)
        cmds.parent(self.cont_fk_up_arm_off, self.nonScaleGrp)
        cmds.parent(self.cont_fk_low_arm_off, self.nonScaleGrp)
        cmds.parent(self.cont_fk_hand_off, self.nonScaleGrp)
        cmds.parent(self.cont_mid_lock_ext, self.scaleGrp)
        cmds.parent(self.cont_pole_off, self.scaleGrp)
        cmds.parent(self.cont_fk_ik_pos, self.nonScaleGrp)
        cmds.parent(self.cont_IK_OFF, self.limbGrp)

        nodesContVis = [self.cont_pole_off, self.cont_shoulder_off, self.cont_IK_OFF, self.cont_fk_hand_off,
                        self.cont_fk_ik_pos,
                        self.cont_fk_low_arm_off, self.cont_fk_up_arm_off, self.cont_mid_lock_pos]

        map(lambda x: cmds.connectAttr("{0}.contVis".format(self.scaleGrp), "{0}.v".format(x)), nodesContVis)

        extra.colorize(self.cont_shoulder, self.colorCodes[0])
        extra.colorize(self.cont_IK_hand, self.colorCodes[0])
        extra.colorize(self.cont_Pole, self.colorCodes[0])
        extra.colorize(self.cont_fk_ik, self.colorCodes[0])
        extra.colorize(self.cont_fk_up_arm, self.colorCodes[0])
        extra.colorize(self.cont_fk_low_arm, self.colorCodes[0])
        extra.colorize(self.cont_fk_hand, self.colorCodes[0])
        extra.colorize(self.cont_mid_lock, self.colorCodes[1])

    def createRoots(self):

        self.master_root = cmds.group(em=True, name="masterRoot_%s" % self.suffix)
        extra.alignTo(self.master_root, self.collar_ref, position=True, rotation=False)
        cmds.makeIdentity(self.master_root, a=True)

        # Create Start Lock

        self.start_lock = cmds.spaceLocator(name="startLock_%s" % self.suffix)[0]
        # extra.alignTo(start_lock, shoulder_ref, 2)
        extra.alignToAlter(self.start_lock, self.j_ik_orig_up, 2)
        self.start_lock_ore = extra.createUpGrp(self.start_lock, "Ore")
        self.start_lock_pos = extra.createUpGrp(self.start_lock, "Pos")
        self.start_lock_twist = extra.createUpGrp(self.start_lock, "AutoTwist")

        # start_lock_weight = cmds.parentConstraint(self.j_collar_end, self.start_lock, sr=("y", "z"), mo=False)
        start_lock_weight = extra.matrixConstraint(self.j_collar_end, self.start_lock, sr=("y", "z"), mo=False)

        cmds.parentConstraint(self.start_lock, self.j_ik_sc_up, mo=False)
        # extra.matrixConstraint(self.start_lock, self.j_ik_sc_up, mo=False)
        cmds.parentConstraint(self.start_lock, self.j_ik_rp_up, mo=False)
        # extra.matrixConstraint(self.start_lock, self.j_ik_rp_up, mo=False)

        # Create Midlock

        self.mid_lock = cmds.spaceLocator(name="midLock_%s" % self.suffix)[0]
        cmds.parentConstraint(self.mid_lock, self.j_def_elbow)
        # extra.matrixConstraint(self.mid_lock, self.j_def_elbow)

        # cmds.parentConstraint(self.cont_mid_lock, self.mid_lock, mo=False)
        extra.matrixConstraint(self.cont_mid_lock, self.mid_lock, mo=False)

        # Create End Lock
        self.end_lock = cmds.spaceLocator(name="endLock_%s" % self.suffix)[0]
        extra.alignTo(self.end_lock, self.j_def_hand, position=True, rotation=True)
        self.end_lock_ore = extra.createUpGrp(self.end_lock, "Ore")
        self.end_lock_pos = extra.createUpGrp(self.end_lock, "Pos")
        self.end_lock_twist = extra.createUpGrp(self.end_lock, "Twist")

        self.hand_lock = cmds.spaceLocator(name="handLock_%s" % self.suffix)[0]
        extra.alignTo(self.hand_lock, self.cont_fk_hand_off, position=True, rotation=True)

        # cmds.parentConstraint(self.cont_fk_hand, self.hand_lock, mo=False)
        extra.matrixConstraint(self.cont_fk_hand, self.hand_lock, mo=False)

        self.root_master = cmds.spaceLocator(name="handMaster_%s" % self.suffix)[0]
        extra.alignTo(self.root_master, self.j_def_hand, position=True, rotation=True)

        cmds.parent(self.j_def_hand, self.root_master)

        cmds.pointConstraint(self.end_lock, self.root_master, mo=False)

        # cmds.parent(self.mid_lock, self.scaleGrp)
        cmds.parent(self.mid_lock, self.nonScaleGrp)
        cmds.parent(self.hand_lock, self.nonScaleGrp)
        cmds.parent(self.master_root, self.scaleGrp)
        cmds.parent(self.root_master, self.scaleGrp)

        cmds.connectAttr("{0}.rigVis".format(self.scaleGrp), "{0}.v".format(self.end_lock_twist))
        cmds.connectAttr("{0}.rigVis".format(self.scaleGrp), "{0}.v".format(self.start_lock_ore))
        cmds.connectAttr("{0}.rigVis".format(self.scaleGrp), "{0}.v".format(self.mid_lock))
        cmds.connectAttr("{0}.rigVis".format(self.scaleGrp), "{0}.v".format(self.master_root))
        cmds.connectAttr("{0}.rigVis".format(self.scaleGrp), "{0}.v".format(self.hand_lock))
        # cmds.connectAttr("{0}.rigVis".format(self.scaleGrp), "{0}.v".format(cmds.listRelatives(self.root_master, c=True, type="shape")[0]))
        cmds.connectAttr("{0}.rigVis".format(self.scaleGrp), "{0}.v".format(extra.getShapes(self.root_master)[0]))

    def createIKsetup(self):

        master_ik = cmds.spaceLocator(name="masterIK_%s" % self.suffix)[0]
        extra.alignTo(master_ik, self.j_def_hand, position=True, rotation=False)

        # Create IK handles

        ik_handle_sc = cmds.ikHandle(sj=self.j_ik_sc_up, ee=self.j_ik_sc_low_end, name="ikHandle_SC_%s" % self.suffix)
        ik_handle_rp = cmds.ikHandle(sj=self.j_ik_rp_up, ee=self.j_ik_rp_low_end, name="ikHandle_RP_%s" % self.suffix,
                                   sol="ikRPsolver")

        cmds.poleVectorConstraint(self.cont_Pole, ik_handle_rp[0])
        cmds.aimConstraint(self.j_ik_rp_low, self.cont_Pole, u=self.up_axis, wut="vector")

        ### Create and constrain Distance Locators

        arm_start = cmds.spaceLocator(name="armStart_%s" % self.suffix)[0]
        cmds.pointConstraint(self.start_lock, arm_start, mo=False)

        arm_end = cmds.spaceLocator(name="armEnd_%s" % self.suffix)[0]
        cmds.pointConstraint(master_ik, arm_end, mo=False)

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
        cmds.setAttr("%s.input1X" % self.initial_length_multip_sc, self.init_upper_arm_dist)
        cmds.setAttr("%s.input1Y" % self.initial_length_multip_sc, self.init_lower_arm_dist)
        cmds.setAttr("%s.operation" % initial_divide_sc, 2)

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

        cmds.connectAttr("{0}.translate".format(arm_start), "{0}.point1".format(distance_sc))
        cmds.connectAttr("{0}.translate".format(arm_end), "{0}.point2".format(distance_sc))
        cmds.connectAttr("{0}.distance".format(distance_sc), "{0}.inputR".format(ik_stretch_distance_clamp))

        cmds.connectAttr("{0}.outputR".format(ik_stretch_distance_clamp), "{0}.input1X".format(initial_divide_sc))
        cmds.connectAttr("{0}.outputR".format(ik_stretch_stretchiness_clamp), "{0}.blender".format(self.stretchiness_sc))

        cmds.connectAttr("{0}.outputX".format(initial_divide_sc), "{0}.input2X".format(stretch_amount_sc))
        cmds.connectAttr("{0}.outputX".format(initial_divide_sc), "{0}.input2Y".format(stretch_amount_sc))

        cmds.connectAttr("{0}.outputX".format(self.initial_length_multip_sc), "{0}.input1X".format(extra_scale_mult_sc))
        cmds.connectAttr("{0}.outputY".format(self.initial_length_multip_sc), "{0}.input1Y".format(extra_scale_mult_sc))
        cmds.connectAttr("{0}.outputX".format(self.initial_length_multip_sc), "{0}.input1D[0]".format(stretch_offset))
        cmds.connectAttr("{0}.outputY".format(self.initial_length_multip_sc), "{0}.input1D[1]".format(stretch_offset))

        cmds.connectAttr("{0}.outputX".format(extra_scale_mult_sc), "{0}.input1X".format(stretch_amount_sc))
        cmds.connectAttr("{0}.outputY".format(extra_scale_mult_sc), "{0}.input1Y".format(stretch_amount_sc))
        cmds.connectAttr("{0}.outputX".format(extra_scale_mult_sc), "{0}.color2R".format(self.stretchiness_sc))
        cmds.connectAttr("{0}.outputY".format(extra_scale_mult_sc), "{0}.color2G".format(self.stretchiness_sc))
        cmds.connectAttr("{0}.outputX".format(extra_scale_mult_sc), "{0}.input1D[0]".format(sum_of_j_lengths_sc))
        cmds.connectAttr("{0}.outputY".format(extra_scale_mult_sc), "{0}.input1D[1]".format(sum_of_j_lengths_sc))

        cmds.connectAttr("{0}.outputX".format(stretch_amount_sc), "{0}.color1R".format(squashiness_sc))
        cmds.connectAttr("{0}.outputY".format(stretch_amount_sc), "{0}.color1G".format(squashiness_sc))
        cmds.connectAttr("{0}.output1D".format(sum_of_j_lengths_sc), "{0}.input2X".format(initial_divide_sc))
        cmds.connectAttr("{0}.outputR".format(squashiness_sc), "{0}.color1R".format(self.stretchiness_sc))
        cmds.connectAttr("{0}.outputG".format(squashiness_sc), "{0}.color1G".format(self.stretchiness_sc))

        invertedStrSC = cmds.createNode("multiplyDivide")
        cmds.setAttr("{0}.input2X".format(invertedStrSC), self.sideMult)
        cmds.setAttr("{0}.input2Y".format(invertedStrSC), self.sideMult)
        cmds.connectAttr("{0}.outputR".format(self.stretchiness_sc), "{0}.input1X".format(invertedStrSC))
        cmds.connectAttr("{0}.outputG".format(self.stretchiness_sc), "{0}.input1Y".format(invertedStrSC))

        cmds.connectAttr("{0}.outputX".format(invertedStrSC), "{0}.translateX".format(self.j_ik_sc_low))
        cmds.connectAttr("{0}.outputY".format(invertedStrSC), "{0}.translateX".format(self.j_ik_sc_low_end))

        cmds.connectAttr("{0}.outputX".format(invertedStrSC), "{0}.translateX".format(self.j_ik_rp_low))
        cmds.connectAttr("{0}.outputY".format(invertedStrSC), "{0}.translateX".format(self.j_ik_rp_low_end))

        ## iksoft related
        cmds.connectAttr("{0}.softIK".format(self.cont_IK_hand), "{0}.inputR".format(ik_soft_clamp))

        cmds.connectAttr("{0}.output1D".format(sum_of_j_lengths_sc), "{0}.input1D[0]".format(ik_soft_sub1))
        cmds.connectAttr("{0}.outputR".format(ik_soft_clamp), "{0}.input1D[1]".format(ik_soft_sub1))

        cmds.connectAttr("{0}.outputR".format(ik_stretch_distance_clamp), "{0}.input1D[0]".format(ik_soft_sub2))
        cmds.connectAttr("{0}.output1D".format(ik_soft_sub1), "{0}.input1D[1]".format(ik_soft_sub2))

        cmds.connectAttr("{0}.output1D".format(ik_soft_sub2), "{0}.input1X".format(ik_soft_div1))
        cmds.connectAttr("{0}.outputR".format(ik_soft_clamp), "{0}.input2X".format(ik_soft_div1))

        cmds.connectAttr("{0}.outputX".format(ik_soft_div1), "{0}.input2".format(ik_soft_mult1))

        cmds.connectAttr("{0}.output".format(ik_soft_mult1), "{0}.input2X".format(ik_soft_pow))

        cmds.connectAttr("{0}.outputR".format(ik_soft_clamp), "{0}.input1".format(ik_soft_mult2))
        cmds.connectAttr("{0}.outputX".format(ik_soft_pow), "{0}.input2".format(ik_soft_mult2))

        cmds.connectAttr("{0}.output1D".format(sum_of_j_lengths_sc), "{0}.input1D[0]".format(ik_soft_sub3))
        cmds.connectAttr("{0}.output".format(ik_soft_mult2), "{0}.input1D[1]".format(ik_soft_sub3))

        cmds.connectAttr("{0}.outputR".format(ik_stretch_distance_clamp), "{0}.firstTerm".format(ik_soft_condition))
        cmds.connectAttr("{0}.output1D".format(ik_soft_sub1), "{0}.secondTerm".format(ik_soft_condition))
        cmds.connectAttr("{0}.output1D".format(ik_soft_sub3), "{0}.colorIfTrueR".format(ik_soft_condition))
        cmds.connectAttr("{0}.outputR".format(ik_stretch_distance_clamp), "{0}.colorIfFalseR".format(ik_soft_condition))

        cmds.connectAttr("{0}.outputR".format(ik_stretch_distance_clamp), "{0}.input1X".format(ik_soft_div2))
        cmds.connectAttr("{0}.outColorR".format(ik_soft_condition), "{0}.input2X".format(ik_soft_div2))

        cmds.connectAttr("{0}.outputX".format(extra_scale_mult_sc), "{0}.input1X".format(ik_soft_stretch_amount))
        cmds.connectAttr("{0}.outputY".format(extra_scale_mult_sc), "{0}.input1Y".format(ik_soft_stretch_amount))
        cmds.connectAttr("{0}.outputX".format(ik_soft_div2), "{0}.input2X".format(ik_soft_stretch_amount))
        cmds.connectAttr("{0}.outputX".format(ik_soft_div2), "{0}.input2Y".format(ik_soft_stretch_amount))

        cmds.connectAttr("{0}.outputX".format(ik_soft_stretch_amount), "{0}.color2R".format(squashiness_sc))
        cmds.connectAttr("{0}.outputY".format(ik_soft_stretch_amount), "{0}.color2G".format(squashiness_sc))

        ###########################################################

        cmds.connectAttr("{0}.rotate".format(self.cont_IK_hand), "{0}.rotate".format(self.j_ik_rp_low))

        # Stretch Attributes Controller connections

        cmds.connectAttr("{0}.sUpArm".format(self.cont_IK_hand), "{0}.input2X".format(extra_scale_mult_sc))
        cmds.connectAttr("{0}.sLowArm".format(self.cont_IK_hand), "{0}.input2Y".format(extra_scale_mult_sc))
        cmds.connectAttr("{0}.squash".format(self.cont_IK_hand), "{0}.blender".format(squashiness_sc))

        cmds.connectAttr("{0}.output1D".format(stretch_offset), "{0}.maxR".format(ik_stretch_distance_clamp))
        cmds.connectAttr("{0}.stretch".format(self.cont_IK_hand), "{0}.inputR".format(ik_stretch_stretchiness_clamp))

        cmds.connectAttr("{0}.stretchLimit".format(self.cont_IK_hand), "{0}.input1D[2]".format(stretch_offset))

        self.ik_parent_grp = cmds.group(name="IK_parentGRP_%s" % self.suffix, em=True)
        extra.alignTo(self.ik_parent_grp, self.j_def_hand, position=True, rotation=True)

        # cmds.parentConstraint(self.cont_IK_hand, self.ik_parent_grp, mo=False)
        extra.matrixConstraint(self.cont_IK_hand, self.ik_parent_grp, mo=False)

        # parenting should be after the constraint
        cmds.parent(ik_handle_sc[0], self.ik_parent_grp)
        cmds.parent(ik_handle_rp[0], self.ik_parent_grp)
        cmds.parent(master_ik, self.ik_parent_grp)

        blend_ore_ik_up = cmds.createNode("blendColors", name="blendORE_IK_Up_%s" % self.suffix)
        cmds.connectAttr("{0}.rotate".format(self.j_ik_sc_up), "{0}.color2".format(blend_ore_ik_up))
        cmds.connectAttr("{0}.rotate".format(self.j_ik_rp_up), "{0}.color1".format(blend_ore_ik_up))
        cmds.connectAttr("{0}.output".format(blend_ore_ik_up), "{0}.rotate".format(self.j_ik_orig_up))
        cmds.connectAttr("{0}.polevector".format(self.cont_IK_hand), "{0}.blender".format(blend_ore_ik_up))

        blend_pos_ik_up = cmds.createNode("blendColors", name="blendPOS_IK_Up_%s" % self.suffix)
        cmds.connectAttr("{0}.translate".format(self.j_ik_sc_up), "{0}.color2".format(blend_pos_ik_up))
        cmds.connectAttr("{0}.translate".format(self.j_ik_rp_up), "{0}.color1".format(blend_pos_ik_up))
        cmds.connectAttr("{0}.output".format(blend_pos_ik_up), "{0}.translate".format(self.j_ik_orig_up))
        cmds.connectAttr("{0}.polevector".format(self.cont_IK_hand), "{0}.blender".format(blend_pos_ik_up))

        blend_ore_ik_low = cmds.createNode("blendColors", name="blendORE_IK_Low_%s" % self.suffix)
        cmds.connectAttr("{0}.rotate".format(self.j_ik_sc_low), "{0}.color2".format(blend_ore_ik_low))
        cmds.connectAttr("{0}.rotate".format(self.j_ik_rp_low), "{0}.color1".format(blend_ore_ik_low))
        # Weird bug with skinned character / use seperate connections
        # if there is no skincluster, it works ok, but adding a skin cluster misses 2 out of 3 rotation axis
        # Therefore make SEPERATE CONNECTIONS
        cmds.connectAttr("{0}.outputR".format(blend_ore_ik_low), "{0}.rotateX".format(self.j_ik_orig_low))
        cmds.connectAttr("{0}.outputG".format(blend_ore_ik_low), "{0}.rotateY".format(self.j_ik_orig_low))
        cmds.connectAttr("{0}.outputB".format(blend_ore_ik_low), "{0}.rotateZ".format(self.j_ik_orig_low))
        cmds.connectAttr("{0}.polevector".format(self.cont_IK_hand), "{0}.blender".format(blend_ore_ik_low))

        blend_pos_ik_low = cmds.createNode("blendColors", name="blendPOS_IK_Low_%s" % self.suffix)
        cmds.connectAttr("{0}.translate".format(self.j_ik_sc_low), "{0}.color2".format(blend_pos_ik_low))
        cmds.connectAttr("{0}.translate".format(self.j_ik_rp_low), "{0}.color1".format(blend_pos_ik_low))
        cmds.connectAttr("{0}.output".format(blend_pos_ik_low), "{0}.translate".format(self.j_ik_orig_low))
        cmds.connectAttr("{0}.polevector".format(self.cont_IK_hand), "{0}.blender".format(blend_pos_ik_low))

        blend_ore_ik_low_end = cmds.createNode("blendColors", name="blendORE_IK_LowEnd_%s" % self.suffix)
        cmds.connectAttr("{0}.rotate".format(self.j_ik_sc_low_end), "{0}.color2".format(blend_ore_ik_low_end))
        cmds.connectAttr("{0}.rotate".format(self.j_ik_rp_low_end), "{0}.color1".format(blend_ore_ik_low_end))
        # Weird bug with skinned character / use seperate connections
        # if there is no skincluster, it works ok, but adding a skin cluster misses 2 out of 3 rotation axis
        # Therefore make SEPERATE CONNECTIONS
        cmds.connectAttr("{0}.outputR".format(blend_ore_ik_low_end), "{0}.rotateX".format(self.j_ik_orig_low_end))
        cmds.connectAttr("{0}.outputG".format(blend_ore_ik_low_end), "{0}.rotateY".format(self.j_ik_orig_low_end))
        cmds.connectAttr("{0}.outputB".format(blend_ore_ik_low_end), "{0}.rotateZ".format(self.j_ik_orig_low_end))
        cmds.connectAttr("{0}.polevector".format(self.cont_IK_hand), "{0}.blender".format(blend_ore_ik_low_end))

        blend_pos_ik_low_end = cmds.createNode("blendColors", name="blendPOS_IK_LowEnd_%s" % self.suffix)
        cmds.connectAttr("{0}.translate".format(self.j_ik_sc_low_end), "{0}.color2".format(blend_pos_ik_low_end))
        cmds.connectAttr("{0}.translate".format(self.j_ik_rp_low_end), "{0}.color1".format(blend_pos_ik_low_end))
        cmds.connectAttr("{0}.output".format(blend_pos_ik_low_end), "{0}.translate".format(self.j_ik_orig_low_end))
        cmds.connectAttr("{0}.polevector".format(self.cont_IK_hand), "{0}.blender".format(blend_pos_ik_low_end))

        pole_vector_rvs = cmds.createNode("reverse", name="poleVector_Rvs_%s" % self.suffix)
        cmds.connectAttr("{0}.polevector".format(self.cont_IK_hand), "{0}.inputX".format(pole_vector_rvs))
        cmds.connectAttr("{0}.polevector".format(self.cont_IK_hand), "{0}.v".format(self.cont_Pole))

        cmds.parent(self.j_ik_orig_up, self.master_root)
        cmds.parent(self.j_ik_sc_up, self.master_root)
        cmds.parent(self.j_ik_rp_up, self.master_root)

        # cmds.select(cont_shoulder)

        pacon_locator_shou = cmds.spaceLocator(name="paConLoc_%s" % self.suffix)[0]
        extra.alignTo(pacon_locator_shou, self.j_def_collar, position=True, rotation=True)

        # j_def_pa_con = cmds.parentConstraint(self.cont_shoulder, pacon_locator_shou, mo=False)
        extra.matrixConstraint(self.cont_shoulder, pacon_locator_shou, mo=False)

        cmds.parent(arm_start, self.scaleGrp)
        cmds.parent(arm_end, self.scaleGrp)
        cmds.parent(self.ik_parent_grp, self.nonScaleGrp)
        # cmds.parent(self.start_lock_ore, self.scaleGrp)
        cmds.parent(self.start_lock_ore, self.nonScaleGrp)
        cmds.parent(self.end_lock_ore, self.scaleGrp)

        cmds.parent(pacon_locator_shou, self.nonScaleGrp)
        cmds.parent(self.j_def_collar, pacon_locator_shou)

        cmds.connectAttr("{0}.rigVis".format(self.scaleGrp), "{0}.v".format(arm_start))
        cmds.connectAttr("{0}.rigVis".format(self.scaleGrp), "{0}.v".format(arm_end))
        cmds.connectAttr("{0}.rigVis".format(self.scaleGrp), "{0}.v".format(self.ik_parent_grp))
        # cmds.connectAttr("{0}.rigVis".format(self.scaleGrp), "{0}.v".format(cmds.listRelatives(pacon_locator_shou, c=True, type="shape")[0]))
        cmds.connectAttr("{0}.rigVis".format(self.scaleGrp), "{0}.v".format(extra.getShapes(pacon_locator_shou)[0]))

    def createFKsetup(self):

        cmds.connectAttr("{0}.scaleX".format(self.cont_fk_up_arm), "{0}.scaleX".format(self.j_fk_up))
        cmds.connectAttr("{0}.scaleX".format(self.cont_fk_low_arm), "{0}.scaleX".format(self.j_fk_low))

        cmds.orientConstraint(self.cont_fk_up_arm, self.j_fk_up, mo=False)
        cmds.pointConstraint(self.start_lock, self.j_fk_up, mo=False)

        cmds.orientConstraint(self.cont_fk_low_arm, self.j_fk_low, mo=False)

        # cmds.parentConstraint(self.j_collar_end, self.cont_fk_up_arm_off, sr=("x", "y", "z"), mo=False)
        extra.matrixConstraint(self.j_collar_end, self.cont_fk_up_arm_off, sr=("x", "y", "z"), mo=False)

        # TODO : TAKE A LOOK TO THE OFFSET SOLUTION
        # cmds.parentConstraint(self.cont_fk_up_arm, self.cont_fk_low_arm_off, mo=True)
        extra.matrixConstraint(self.cont_fk_up_arm, self.cont_fk_low_arm_off, mo=True)

        # cmds.parentConstraint(self.cont_fk_low_arm, self.cont_fk_hand_pos, mo=True)
        extra.matrixConstraint(self.cont_fk_low_arm, self.cont_fk_hand_pos, mo=True)

    def ikfkSwitching(self):

        cmds.connectAttr("{0}.outputX".format(self.fk_ik_rvs), "{0}.visibility".format(self.cont_fk_up_arm_ore))
        cmds.connectAttr("{0}.outputX".format(self.fk_ik_rvs), "{0}.visibility".format(self.cont_fk_low_arm_ore))

        cmds.connectAttr("{0}.fk_ik".format(self.cont_fk_ik), "{0}.visibility".format(self.cont_IK_hand))
        cmds.connectAttr("{0}.fk_ik".format(self.cont_fk_ik), "{0}.visibility".format(self.cont_pole_vis))

        mid_lock_pa_con_weight = cmds.orientConstraint(self.j_ik_orig_low, self.j_fk_low, self.cont_mid_lock_pos, mo=False)[0]
        cmds.connectAttr("{0}.fk_ik".format(self.cont_fk_ik), ("%s.%sW0" % (mid_lock_pa_con_weight, self.j_ik_orig_low)))
        cmds.connectAttr("{0}.outputX".format(self.fk_ik_rvs),("%s.%sW1" % (mid_lock_pa_con_weight, self.j_fk_low)))

        cmds.connectAttr("{0}.interpType".format(self.cont_fk_ik), "{0}.interpType".format(mid_lock_pa_con_weight))

        mid_lock_po_con_weight = cmds.pointConstraint(self.j_ik_orig_low, self.j_fk_low, self.cont_mid_lock_ave, mo=False)[0]
        cmds.connectAttr("{0}.fk_ik".format(self.cont_fk_ik), ("%s.%sW0" % (mid_lock_po_con_weight, self.j_ik_orig_low)))
        cmds.connectAttr("{0}.outputX".format(self.fk_ik_rvs), ("%s.%sW1" % (mid_lock_po_con_weight, self.j_fk_low)))


        mid_lock_x_bln = cmds.createNode("multiplyDivide", name="midLock_xBln_%s" % self.suffix)

        mid_lock_rot_xsw = cmds.createNode("blendTwoAttr", name="midLock_rotXsw_%s" % self.suffix)
        cmds.connectAttr("{0}.rotateY".format(self.j_ik_orig_low), "{0}.input[0]".format(mid_lock_rot_xsw))
        cmds.connectAttr("{0}.rotateY".format(self.j_fk_low), "{0}.input[1]".format(mid_lock_rot_xsw))
        cmds.connectAttr("{0}.outputX".format(self.fk_ik_rvs), "{0}.attributesBlender".format(mid_lock_rot_xsw))

        cmds.connectAttr("{0}.output".format(mid_lock_rot_xsw), "{0}.input1Z".format(mid_lock_x_bln))

        cmds.setAttr("{0}.input2Z".format(mid_lock_x_bln), 0.5)
        cmds.connectAttr("{0}.outputZ".format(mid_lock_x_bln), "{0}.rotateY".format(self.cont_mid_lock_ave))

        end_lock_weight = cmds.pointConstraint(self.j_ik_orig_low_end, self.j_fk_low_end, self.end_lock_pos, mo=False)[0]
        cmds.connectAttr("{0}.fk_ik".format(self.cont_fk_ik), ("%s.%sW0" % (end_lock_weight, self.j_ik_orig_low_end)))
        cmds.connectAttr("{0}.outputX".format(self.fk_ik_rvs), ("%s.%sW1" % (end_lock_weight, self.j_fk_low_end)))

        # the following offset parent constraint is not important and wont cause any trouble since
        # it only affects the FK/IK icon
        # cmds.parentConstraint(self.end_lock, self.cont_fk_ik_pos, mo=True)
        extra.matrixConstraint(self.end_lock, self.cont_fk_ik_pos, mo=True)

        # end_lock_rot = pm.parentConstraint(ik_parent_grp, cont_fk_hand, end_lock_twist, st=("x", "y", "z"), mo=True)
        end_lock_rot =cmds.parentConstraint(self.ik_parent_grp, self.cont_fk_hand, self.end_lock_twist,
                                           st=("x", "y", "z"), mo=False)[0]

        cmds.connectAttr("{0}.fk_ik".format(self.cont_fk_ik), ("%s.%sW0" % (end_lock_rot, self.ik_parent_grp)))
        cmds.connectAttr("{0}.outputX".format(self.fk_ik_rvs), ("%s.%sW1" % (end_lock_rot, self.cont_fk_hand)))

        cmds.connectAttr("{0}.interpType".format(self.cont_fk_ik), "{0}.interpType".format(end_lock_rot))

        hand_ori_con = cmds.parentConstraint(self.cont_IK_hand, self.hand_lock, self.root_master, st=("x", "y", "z"),
                                           mo=False)[0]
        cmds.setAttr("{0}.interpType".format(hand_ori_con), 0)

        cmds.connectAttr("{0}.fk_ik".format(self.cont_fk_ik), ("%s.%sW0" % (hand_ori_con, self.cont_IK_hand)))
        cmds.connectAttr("{0}.outputX".format(self.fk_ik_rvs), ("%s.%sW1" % (hand_ori_con, self.hand_lock)))

        cmds.connectAttr("{0}.outputX".format(self.fk_ik_rvs), "{0}.v".format(self.cont_fk_hand))

        hand_sca_con = cmds.createNode("blendColors", name="handScaCon_%s" % self.suffix)
        cmds.connectAttr("{0}.scale".format(self.cont_IK_hand), "{0}.color1".format(hand_sca_con))
        cmds.connectAttr("{0}.scale".format(self.cont_fk_hand), "{0}.color2".format(hand_sca_con))
        cmds.connectAttr("{0}.fk_ik".format(self.cont_fk_ik), "{0}.blender".format(hand_sca_con))
        cmds.connectAttr("{0}.output".format(hand_sca_con), "{0}.scale".format(self.root_master))

    def createDefJoints(self):
        # UPPER ARM RIBBON

        # Constraint offsets cannot be False because of the orientation mismatches with PowerRibbon class

        ribbon_upper_arm = rc.PowerRibbon()
        ribbon_upper_arm.createPowerRibbon(self.j_collar_end, self.j_def_elbow, "up_%s" % self.suffix, side=self.side,
                                           orientation=0, connectStartAim=False, upVector=self.up_axis)

        ribbon_start_pa_con_upper_arm_start = cmds.parentConstraint(self.start_lock, ribbon_upper_arm.startConnection, mo=True)[0]
        cmds.parentConstraint(self.mid_lock, ribbon_upper_arm.endConnection, mo=True)
        # extra.matrixConstraint(self.mid_lock, ribbon_upper_arm.endConnection, mo=True)

        # connect the elbow scaling
        cmds.connectAttr("{0}.scale".format(self.cont_mid_lock), "{0}.scale".format(ribbon_upper_arm.endConnection))
        cmds.connectAttr("{0}.scale".format(self.cont_mid_lock), "{0}.scale".format(self.j_def_elbow))

        cmds.scaleConstraint(self.scaleGrp, ribbon_upper_arm.scaleGrp)

        ribbon_start_ori_con = cmds.parentConstraint(self.j_ik_orig_up, self.j_fk_up, ribbon_upper_arm.startAim, mo=True,
                                                   skipTranslate=["x", "y", "z"])[0]

        ribbon_start_ori_con2 = cmds.parentConstraint(self.j_collar_end, ribbon_upper_arm.startAim, mo=True,
                                                    skipTranslate=["x", "y", "z"])[0]

        cmds.connectAttr("{0}.fk_ik".format(self.cont_fk_ik), ("%s.%sW0" % (ribbon_start_ori_con, self.j_ik_orig_up)))
        cmds.connectAttr("{0}.outputX".format(self.fk_ik_rvs), ("%s.%sW1" % (ribbon_start_ori_con, self.j_fk_up)))

        pairBlendNode = cmds.listConnections(ribbon_start_ori_con, d=True, t="pairBlend")[0]
        # disconnect the existing weight connection
        # cmds.disconnectAttr("{0}.weight".format(pairBlendNode))
        # re-connect to the custom attribute
        cmds.connectAttr("{0}.alignShoulder".format(self.cont_fk_ik), "{0}.weight".format(pairBlendNode), force=True)

        # AUTO AND MANUAL TWIST

        # auto
        auto_twist = cmds.createNode("multiplyDivide", name="autoTwist_%s" % self.suffix)
        cmds.connectAttr("{0}.shoulderAutoTwist".format(self.cont_fk_ik), "{0}.input2X".format(auto_twist))
        cmds.connectAttr("{0}.constraintRotate".format(ribbon_start_pa_con_upper_arm_start), "{0}.input1".format(auto_twist))

        # !!! The parent constrain override should be disconnected like this
        cmds.disconnectAttr("{0}.constraintRotateX".format(ribbon_start_pa_con_upper_arm_start), "{0}.rotateX".format(ribbon_upper_arm.startConnection))

        # manual
        add_manual_twist = cmds.createNode("plusMinusAverage", name=("AddManualTwist_UpperArm_%s" % self.suffix))
        cmds.connectAttr("{0}.output".format(auto_twist), "{0}.input3D[0]".format(add_manual_twist))
        cmds.connectAttr("{0}.shoulderManualTwist".format(self.cont_fk_ik), "{0}.input3D[1].input3Dx".format(add_manual_twist))

        # connect to the joint
        cmds.connectAttr("{0}.output3D".format(add_manual_twist), "{0}.rotate".format(ribbon_upper_arm.startConnection))

        # connect allowScaling
        cmds.connectAttr("{0}.allowScaling".format(self.cont_fk_ik), "{0}.scaleSwitch".format(ribbon_upper_arm.startConnection))

        # LOWER ARM RIBBON

        ribbon_lower_arm = rc.PowerRibbon()
        ribbon_lower_arm.createPowerRibbon(self.j_def_elbow, self.j_def_hand, "low_%s" % self.suffix, side=self.side,
                                           orientation=0, upVector=self.up_axis)

        cmds.parentConstraint(self.mid_lock, ribbon_lower_arm.startConnection, mo=True)
        ribbon_start_pa_con_lower_arm_end = cmds.parentConstraint(self.end_lock, ribbon_lower_arm.endConnection, mo=True)[0]

        # connect the elbow scaling
        cmds.connectAttr("{0}.scale".format(self.cont_mid_lock), "{0}.scale".format(ribbon_lower_arm.startConnection))

        cmds.scaleConstraint(self.scaleGrp, ribbon_lower_arm.scaleGrp)

        # AUTO AND MANUAL TWIST

        # auto
        auto_twist = cmds.createNode("multiplyDivide", name="autoTwist_%s" % self.suffix)
        cmds.connectAttr("{0}.handAutoTwist".format(self.cont_fk_ik), "{0}.input2X".format(auto_twist))
        cmds.connectAttr("{0}.constraintRotate".format(ribbon_start_pa_con_lower_arm_end), "{0}.input1".format(auto_twist))

        # !!! The parent constrain override should be disconnected like this
        cmds.disconnectAttr("{0}.constraintRotateX".format(ribbon_start_pa_con_lower_arm_end), "{0}.rotateX".format(ribbon_lower_arm.endConnection))

        # manual
        add_manual_twist = cmds.createNode("plusMinusAverage", name=("AddManualTwist_LowerArm_%s" % self.suffix))
        cmds.connectAttr("{0}.output".format(auto_twist), "{0}.input3D[0]".format(add_manual_twist))
        cmds.connectAttr("{0}.handManualTwist".format(self.cont_fk_ik), "{0}.input3D[1].input3Dx".format(add_manual_twist))

        # connect to the joint
        cmds.connectAttr("{0}.output3D".format(add_manual_twist), "{0}.rotate".format(ribbon_lower_arm.endConnection))

        # connect allowScaling
        cmds.connectAttr("{0}.allowScaling".format(self.cont_fk_ik), "{0}.scaleSwitch".format(ribbon_lower_arm.startConnection))

        # Volume Preservation Stuff
        vpExtraInput = cmds.createNode("multiplyDivide", name="vpExtraInput_%s" % self.suffix)
        cmds.setAttr("{0}.operation".format(vpExtraInput), 1)

        vpMidAverage = cmds.createNode("plusMinusAverage", name="vpMidAverage_%s" % self.suffix)
        cmds.setAttr("{0}.operation".format(vpMidAverage), 3)

        vpPowerMid = cmds.createNode("multiplyDivide", name="vpPowerMid_%s" % self.suffix)
        cmds.setAttr("{0}.operation".format(vpPowerMid), 3)
        vpInitLength = cmds.createNode("multiplyDivide", name="vpInitLength_%s" % self.suffix)
        cmds.setAttr("{0}.operation".format(vpInitLength), 2)

        vpPowerUpperLeg = cmds.createNode("multiplyDivide", name="vpPowerUpperLeg_%s" % self.suffix)
        cmds.setAttr("{0}.operation".format(vpPowerUpperLeg), 3)

        vpPowerLowerLeg = cmds.createNode("multiplyDivide", name="vpPowerLowerLeg_%s" % self.suffix)
        cmds.setAttr("{0}.operation".format(vpPowerLowerLeg), 3)
        #
        vpUpperLowerReduce = cmds.createNode("multDoubleLinear", name="vpUpperLowerReduce_%s" % self.suffix)
        cmds.setAttr("{0}.input2".format(vpUpperLowerReduce), 0.5)
        #
        # vp knee branch
        cmds.connectAttr("{0}.output".format(vpExtraInput), "{0}.scale".format(ribbon_lower_arm.startConnection), f=True)
        cmds.connectAttr("{0}.output".format(vpExtraInput), "{0}.scale".format(ribbon_upper_arm.endConnection), f=True)
        cmds.connectAttr("{0}.output".format(vpExtraInput), "{0}.scale".format(self.j_def_elbow), f=True)
        cmds.connectAttr("{0}.scale".format(self.cont_mid_lock), "{0}.input1".format(vpExtraInput))

        cmds.connectAttr("{0}.output1D".format(vpMidAverage), "{0}.input2X".format(vpExtraInput))
        cmds.connectAttr("{0}.output1D".format(vpMidAverage), "{0}.input2Y".format(vpExtraInput))
        cmds.connectAttr("{0}.output1D".format(vpMidAverage), "{0}.input2Z".format(vpExtraInput))

        cmds.connectAttr("{0}.outputX".format(vpPowerMid), "{0}.input1D[0]".format(vpMidAverage))
        cmds.connectAttr("{0}.outputY".format(vpPowerMid), "{0}.input1D[1]".format(vpMidAverage))

        cmds.connectAttr("{0}.outputX".format(vpInitLength), "{0}.input1X".format(vpPowerMid))
        cmds.connectAttr("{0}.outputY".format(vpInitLength), "{0}.input1Y".format(vpPowerMid))

        cmds.connectAttr("{0}.volume".format(self.cont_IK_hand), "{0}.input2X".format(vpPowerMid))
        cmds.connectAttr("{0}.volume".format(self.cont_IK_hand), "{0}.input2Y".format(vpPowerMid))

        cmds.connectAttr("{0}.outputX".format(self.initial_length_multip_sc), "{0}.input1X".format(vpInitLength))
        cmds.connectAttr("{0}.outputY".format(self.initial_length_multip_sc), "{0}.input1Y".format(vpInitLength))

        cmds.connectAttr("{0}.color1R".format(self.stretchiness_sc), "{0}.input2X".format(vpInitLength))
        cmds.connectAttr("{0}.color1G".format(self.stretchiness_sc), "{0}.input2Y".format(vpInitLength))


        # vp upper branch
        mid_off_up = extra.getParent(ribbon_upper_arm.middleCont[0])
        cmds.connectAttr("{0}.outputX".format(vpPowerUpperLeg), "{0}.scaleX".format(mid_off_up))
        cmds.connectAttr("{0}.outputX".format(vpPowerUpperLeg), "{0}.scaleY".format(mid_off_up))
        cmds.connectAttr("{0}.outputX".format(vpPowerUpperLeg), "{0}.scaleZ".format(mid_off_up))

        cmds.connectAttr("{0}.outputX".format(vpInitLength), "{0}.input1X".format(vpPowerUpperLeg))
        cmds.connectAttr("{0}.output".format(vpUpperLowerReduce), "{0}.input2X".format(vpPowerUpperLeg))

        # vp lower branch
        mid_off_low = extra.getParent(ribbon_lower_arm.middleCont[0])
        cmds.connectAttr("{0}.outputX".format(vpPowerLowerLeg), "{0}.scaleX".format(mid_off_low))
        cmds.connectAttr("{0}.outputX".format(vpPowerLowerLeg), "{0}.scaleY".format(mid_off_low))
        cmds.connectAttr("{0}.outputX".format(vpPowerLowerLeg), "{0}.scaleZ".format(mid_off_low))

        cmds.connectAttr("{0}.outputX".format(vpInitLength), "{0}.input1X".format(vpPowerLowerLeg))
        cmds.connectAttr("{0}.output".format(vpUpperLowerReduce), "{0}.input2X".format(vpPowerLowerLeg))

        cmds.connectAttr("{0}.volume".format(self.cont_IK_hand), "{0}.input1".format(vpUpperLowerReduce))

        cmds.parent(ribbon_upper_arm.scaleGrp, self.nonScaleGrp)
        cmds.parent(ribbon_upper_arm.nonScaleGrp, self.nonScaleGrp)
        cmds.parent(ribbon_lower_arm.scaleGrp, self.nonScaleGrp)
        cmds.parent(ribbon_lower_arm.nonScaleGrp, self.nonScaleGrp)

        cmds.connectAttr("{0}.tweakControls".format(self.cont_fk_ik), "{0}.v".format(self.cont_mid_lock))
        tweakConts = ribbon_upper_arm.middleCont + ribbon_lower_arm.middleCont
        map(lambda x: cmds.connectAttr("{0}.tweakControls".format(self.cont_fk_ik), "{0}.v".format(x)), tweakConts)

        cmds.connectAttr("{0}.contVis".format(self.scaleGrp), "{0}.v".format(ribbon_upper_arm.scaleGrp))
        cmds.connectAttr("{0}.contVis".format(self.scaleGrp), "{0}.v".format(ribbon_lower_arm.scaleGrp))

        self.deformerJoints += ribbon_lower_arm.deformerJoints + ribbon_upper_arm.deformerJoints

        map(lambda x: cmds.connectAttr("{0}.jointVis".format(self.scaleGrp), "{0}.v".format(x)), self.deformerJoints)
        map(lambda x: cmds.connectAttr("{0}.rigVis".format(self.scaleGrp), "{0}.v".format(x)), ribbon_lower_arm.toHide)
        map(lambda x: cmds.connectAttr("{0}.rigVis".format(self.scaleGrp),"{0}.v".format(x)), ribbon_upper_arm.toHide)

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
        angleExt_Root_IK = cmds.spaceLocator(name="angleExt_Root_IK_%s" % self.suffix)[0]
        angleExt_Fixed_IK = cmds.spaceLocator(name="angleExt_Fixed_IK_%s" % self.suffix)[0]
        angleExt_Float_IK = cmds.spaceLocator(name="angleExt_Float_IK_%s" % self.suffix)[0]
        cmds.parent(angleExt_Fixed_IK, angleExt_Float_IK, angleExt_Root_IK)
        # cmds.error("BREAK")
        # cmds.parentConstraint(self.limbPlug, angleExt_Root_IK, mo=False)
        extra.matrixConstraint(self.limbPlug, angleExt_Root_IK, mo=False)
        # cmds.parentConstraint(self.cont_IK_hand, angleExt_Fixed_IK, mo=False)
        # extra.matrixConstraint(self.cont_IK_hand, angleExt_Fixed_IK, mo=False, ss=("x","y","z"))
        cmds.pointConstraint(self.cont_IK_hand, angleExt_Fixed_IK, mo=False)
        extra.alignToAlter(angleExt_Float_IK, self.j_def_collar, 2)
        cmds.move(0, 0, -self.sideMult*5, angleExt_Float_IK, objectSpace=True)

        angleNodeIK = cmds.createNode("angleBetween", name="angleBetweenIK_%s" % self.suffix)
        angleRemapIK = cmds.createNode("remapValue", name="angleRemapIK_%s" % self.suffix)
        angleMultIK = cmds.createNode("multDoubleLinear", name="angleMultIK_%s" % self.suffix)

        cmds.connectAttr("{0}.translate".format(angleExt_Fixed_IK), "{0}.vector1".format(angleNodeIK))
        cmds.connectAttr("{0}.translate".format(angleExt_Float_IK), "{0}.vector2".format(angleNodeIK))

        cmds.connectAttr("{0}.angle".format(angleNodeIK), "{0}.inputValue".format(angleRemapIK))
        cmds.setAttr("{0}.inputMin".format(angleRemapIK), cmds.getAttr("{0}.angle".format(angleNodeIK)))
        cmds.setAttr("{0}.inputMax".format(angleRemapIK), 0)
        cmds.setAttr("{0}.outputMin".format(angleRemapIK), 0)
        cmds.setAttr("{0}.outputMax".format(angleRemapIK), cmds.getAttr("{0}.angle".format(angleNodeIK)))

        cmds.connectAttr("{0}.outValue".format(angleRemapIK), "{0}.input1".format(angleMultIK))
        cmds.setAttr("{0}.input2".format(angleMultIK), 0.5)

        # FK Angle Extractor
        angleRemapFK = cmds.createNode("remapValue", name="angleRemapFK_%s" % self.suffix)
        angleMultFK = cmds.createNode("multDoubleLinear", name="angleMultFK_%s" % self.suffix)

        cmds.connectAttr("{0}.rotateY".format(self.cont_fk_up_arm), "{0}.inputValue".format(angleRemapFK))
        cmds.setAttr("{0}.inputMin".format(angleRemapFK), 0)
        cmds.setAttr("{0}.inputMax".format(angleRemapFK), 90)
        cmds.setAttr("{0}.outputMin".format(angleRemapFK), 0)
        cmds.setAttr("{0}.outputMax".format(angleRemapFK), 90)

        cmds.connectAttr("{0}.outValue".format(angleRemapFK), "{0}.input1".format(angleMultFK))
        cmds.setAttr("{0}.input2".format(angleMultFK), 0.5)


        # create blend attribute and global Mult
        angleExt_blend = cmds.createNode("blendTwoAttr", name="angleExt_blend_%s" % self.suffix)
        angleGlobal = cmds.createNode("multDoubleLinear", name="angleGlobal_mult_%s" % self.suffix)

        cmds.connectAttr("{0}.fk_ik".format(self.cont_fk_ik), "{0}.attributesBlender".format(angleExt_blend))
        cmds.connectAttr("{0}.output".format(angleMultFK), "{0}.input[0]".format(angleExt_blend))
        cmds.connectAttr("{0}.output".format(angleMultIK), "{0}.input[1]".format(angleExt_blend))

        cmds.connectAttr("{0}.output".format(angleExt_blend), "{0}.input1".format(angleGlobal))
        cmds.connectAttr("{0}.autoShoulder".format(self.cont_fk_ik), "{0}.input2".format(angleGlobal))


        cmds.connectAttr("{0}.output".format(angleGlobal), "{0}.rotateY".format(self.cont_shoulder_auto))

        cmds.parent(angleExt_Root_IK, self.nonScaleGrp)
        # cmds.connectAttr("{0}.rigVis".format(self.scaleGrp), "{0}.v".format(angleExt_Root_IK))
        return


    def roundUp(self):
        # cmds.parentConstraint(self.limbPlug, self.scaleGrp, mo=False)
        extra.matrixConstraint(self.limbPlug, self.scaleGrp, mo=False)

        cmds.setAttr("%s.rigVis" % self.scaleGrp, 0)

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

class Guides(object):
    def __init__(self, side="L", suffix="arm", segments=None, tMatrix=None, upVector=(0, 1, 0), mirrorVector=(1, 0, 0), lookVector=(0,0,1), *args, **kwargs):
        super(Guides, self).__init__()

        self.side = side
        self.sideMultiplier = -1 if side == "R" else 1
        self.suffix = suffix
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
            collarVec = om.MVector(0, 0, 2) * self.tMatrix
            shoulderVec = om.MVector(0, 0, 5) * self.tMatrix
            elbowVec = om.MVector(0, -1, 9) * self.tMatrix
            handVec = om.MVector(0, 0, 14 ) * self.tMatrix
        # Initial Joint positions for left arm
        else:
            collarVec = om.MVector(2 * self.sideMultiplier, 0, 0) * self.tMatrix
            shoulderVec = om.MVector(5 * self.sideMultiplier, 0, 0) * self.tMatrix
            elbowVec = om.MVector(9 * self.sideMultiplier, 0, -1) * self.tMatrix
            handVec = om.MVector(14 * self.sideMultiplier, 0, 0) * self.tMatrix

        self.offsetVector = -((collarVec - shoulderVec).normalize())

        cmds.select(d=True)
        collar = cmds.joint(p=collarVec, name=("jInit_collar_%s" % self.suffix))
        cmds.setAttr("{0}.radius".format(collar), 2)
        shoulder = cmds.joint(p=shoulderVec, name=("jInit_shoulder_%s" % self.suffix))
        elbow = cmds.joint(p=elbowVec, name=("jInit_elbow_%s" % self.suffix))
        hand = cmds.joint(p=handVec, name=("jInit_hand_%s" % self.suffix))

        self.guideJoints = [collar, shoulder, elbow, hand]

        # Orientation
        extra.orientJoints(self.guideJoints, worldUpAxis=self.lookVector, upAxis=(0, 1, 0), reverseAim=self.sideMultiplier, reverseUp=self.sideMultiplier)

    def define_attributes(self):
        extra.set_joint_type(self.guideJoints[0], "Collar")
        extra.set_joint_type(self.guideJoints[1], "Shoulder")
        extra.set_joint_type(self.guideJoints[2], "Elbow")
        extra.set_joint_type(self.guideJoints[3], "Hand")
        _ = [extra.set_joint_side(jnt, self.side) for jnt in self.guideJoints]

        root_jnt = self.guideJoints[0]
        extra.create_global_joint_attrs(root_jnt, moduleName="%s_Arm" % self.side, upAxis=self.upVector, mirrorAxis=self.mirrorVector, lookAxis=self.lookVector)

        for attr_dict in LIMB_DATA["properties"]:
            extra.create_attribute(root_jnt, attr_dict)

    def createGuides(self):
        """Main Function to create Guides"""
        self.draw_joints()
        self.define_attributes()

    def convertJoints(self, joints_list):
        if len(joints_list) != 4:
            FEEDBACK.warning("Define or select exactly 5 joints for Arm Guide conversion. Skipping")
            return
        self.guideJoints = joints_list
        _ = [extra.set_joint_side(jnt, self.side) for jnt in self.guideJoints]
        self.define_attributes()
