from maya import cmds
import maya.api.OpenMaya as om
from trigger.library import functions
from trigger.library import naming
from trigger.library import attribute
from trigger.library import api
from trigger.library import connection
from trigger.library import arithmetic as op

from trigger.library import objects

from trigger.library import controllers as ic

from trigger.core import filelog
log = filelog.Filelog(logname=__name__, filename="trigger_log")

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

class New_arm(object):
    def __init__(self, build_data=None, inits=None, *args, **kwargs):
        super(New_arm, self).__init__()
        # fool proofing

        # reinitialize the initial Joints
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
            log.error("Class needs either build_data or inits to be constructed")

        self.collar_pos = api.getWorldTranslation(self.collar_ref)
        self.shoulder_pos = api.getWorldTranslation(self.shoulder_ref)
        self.elbow_pos = api.getWorldTranslation(self.elbow_ref)
        self.hand_pos = api.getWorldTranslation(self.hand_ref)


        # get distances
        self.init_shoulder_dist = functions.getDistance(self.collar_ref, self.shoulder_ref)
        self.init_upper_arm_dist = functions.getDistance(self.shoulder_ref, self.elbow_ref)
        self.init_lower_arm_dist = functions.getDistance(self.elbow_ref, self.hand_ref)

        self.up_axis, self.mirror_axis, self.look_axis = functions.getRigAxes(self.collar_ref)


        # get positions

        # get the properties from the root
        self.useRefOrientation = cmds.getAttr("%s.useRefOri" % self.collar_ref)
        self.side = functions.get_joint_side(self.collar_ref)
        self.sideMult = -1 if self.side == "R" else 1
        try:
            self.isLocal = bool(cmds.getAttr("%s.localJoints" % self.collar_ref))
        except ValueError:
            self.isLocal = False

        self.suffix = (naming.uniqueName(cmds.getAttr("%s.moduleName" % self.collar_ref)))

        # module variables
        self.shoulderCont = None
        # self.shoulderContOff = None
        # self.shoulderContOre = None
        # self.shoulderContAuto = None
        self.handIkCont = None
        # self.handIkContOff = None
        # self.handIkContOre = None
        # self.handIkContPos = None
        self.poleCont = None
        # self.poleContOff = None
        # self.poleContVis = None
        self.poleContBridge = None
        self.upArmFkCont = None
        # self.upArmFkContOff = None
        # self.upArmFkContOre = None
        self.lowArmFkCont = None
        # self.lowArmFkContOff = None
        # self.lowArmFkContOre = None
        self.handFkCont = None
        # self.handFkContOff = None
        # self.handFkContPos = None
        # self.handFkContOre = None
        self.switchIkFkCont = None
        self.switchIkFkContPos = None
        self.midLockCont = None
        # self.midLockContExt = None
        # self.midLockContPos = None
        # self.midLockContAve = None
        self.startLock = None
        self.startLockOre = None
        self.startLockPos = None
        self.startLockTwist = None

        # session variables
        self.controllers = []
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
        self.limbGrp = cmds.group(name=self.suffix, em=True)
        self.scaleGrp = cmds.group(name="%s_scaleGrp" % self.suffix, em=True)
        functions.alignTo(self.scaleGrp, self.collar_ref, position=True, rotation=False)
        self.nonScaleGrp = cmds.group(name="%s_nonScaleGrp" % self.suffix, em=True)

        cmds.addAttr(self.scaleGrp, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True)
        cmds.addAttr(self.scaleGrp, at="bool", ln="Joints_Visibility", sn="jointVis", defaultValue=True)
        cmds.addAttr(self.scaleGrp, at="bool", ln="Rig_Visibility", sn="rigVis", defaultValue=False)
        # make the created attributes visible in the channelbox
        cmds.setAttr("%s.contVis" % self.scaleGrp, cb=True)
        cmds.setAttr("%s.jointVis" % self.scaleGrp, cb=True)
        cmds.setAttr("%s.rigVis" % self.scaleGrp, cb=True)

        cmds.parent(self.scaleGrp, self.limbGrp)
        cmds.parent(self.nonScaleGrp, self.limbGrp)

        self.localOffGrp = cmds.group(name="%s_localOffset_grp" %self.suffix, em=True)
        self.plugBindGrp = cmds.group(name="%s_plugBind_grp" %self.suffix, em=True)
        cmds.parent(self.localOffGrp, self.plugBindGrp)
        cmds.parent(self.plugBindGrp, self.limbGrp)

        self.ikBindGrp = cmds.group(name="%s_IK_bind_grp" % self.suffix, em=True)
        cmds.parent(self.ikBindGrp, self.localOffGrp)

    def createJoints(self):
        # draw Joints

        # limb plug
        cmds.select(d=True)
        self.limbPlug = cmds.joint(name="jPlug_%s" % self.suffix, p=self.collar_pos, radius=3)
        connection.matrixConstraint(self.limbPlug, self.ikBindGrp, mo=True)

        # Shoulder Joints
        cmds.select(d=True)
        self.j_def_collar = cmds.joint(name="jDef_Collar_%s" % self.suffix, p=self.collar_pos, radius=1.5)
        self.sockets.append(self.j_def_collar)
        self.j_collar_end = cmds.joint(name="j_CollarEnd_%s" % self.suffix, p=self.shoulder_pos, radius=1.5)
        self.sockets.append(self.j_collar_end)

        if not self.useRefOrientation:
            functions.orientJoints([self.j_def_collar, self.j_collar_end], worldUpAxis=(self.look_axis), upAxis=(0, 1, 0),
                                   reverseAim=self.sideMult, reverseUp=self.sideMult)
        else:
            functions.alignTo(self.j_def_collar, self.collar_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_def_collar, a=True)
            functions.alignTo(self.j_collar_end, self.shoulder_ref, position=True, rotation=True)
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

        # orientations

        if not self.useRefOrientation:
            functions.orientJoints([self.j_ik_orig_up, self.j_ik_orig_low, self.j_ik_orig_low_end],
                                   worldUpAxis=(self.look_axis), upAxis=(0, 1, 0), reverseAim=self.sideMult,
                                   reverseUp=self.sideMult)
        else:
            functions.alignTo(self.j_ik_orig_up, self.shoulder_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_orig_up, a=True)

            functions.alignTo(self.j_ik_orig_low, self.elbow_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_orig_low, a=True)

            functions.alignTo(self.j_ik_orig_low_end, self.hand_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_orig_low_end, a=True)

        if not self.useRefOrientation:
            functions.orientJoints([self.j_ik_sc_up, self.j_ik_sc_low, self.j_ik_sc_low_end], worldUpAxis=(self.look_axis),
                                   upAxis=(0, 1, 0), reverseAim=self.sideMult, reverseUp=self.sideMult)
        else:
            functions.alignTo(self.j_ik_sc_up, self.shoulder_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_sc_up, a=True)

            functions.alignTo(self.j_ik_sc_low, self.elbow_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_sc_low, a=True)

            functions.alignTo(self.j_ik_sc_low_end, self.hand_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_sc_low_end, a=True)

        if not self.useRefOrientation:
            functions.orientJoints([self.j_ik_rp_up, self.j_ik_rp_low, self.j_ik_rp_low_end], worldUpAxis=(self.look_axis),
                                   upAxis=(0, 1, 0), reverseAim=self.sideMult, reverseUp=self.sideMult)
        else:
            functions.alignTo(self.j_ik_rp_up, self.shoulder_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_rp_up, a=True)

            functions.alignTo(self.j_ik_rp_low, self.elbow_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_rp_low, a=True)

            functions.alignTo(self.j_ik_rp_low_end, self.hand_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_rp_low_end, a=True)

        # FK Joints
        cmds.select(d=True)
        self.j_fk_up = cmds.joint(name="jFK_Up_%s" % self.suffix, p=self.shoulder_pos, radius=2.0)
        self.j_fk_low = cmds.joint(name="jFK_Low_%s" % self.suffix, p=self.elbow_pos, radius=2.0)
        self.j_fk_low_end = cmds.joint(name="jFK_LowEnd_%s" % self.suffix, p=self.hand_pos, radius=2.0)

        if not self.useRefOrientation:
            functions.orientJoints([self.j_fk_up, self.j_fk_low, self.j_fk_low_end], worldUpAxis=(self.look_axis),
                                   upAxis=(0, 1, 0), reverseAim=self.sideMult, reverseUp=self.sideMult)
        else:
            functions.alignTo(self.j_fk_up, self.shoulder_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_fk_up, a=True)

            functions.alignTo(self.j_fk_low, self.elbow_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_fk_low, a=True)

            functions.alignTo(self.j_fk_low_end, self.hand_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_fk_low_end, a=True)

        # Hand joint
        self.j_def_hand = cmds.joint(name="jDef_Hand_%s" % self.suffix, p=self.hand_pos, radius=1.0)
        self.sockets.append(self.j_def_hand)

        # re-orient single joints
        functions.alignToAlter(self.j_collar_end, self.j_fk_up, 2)
        cmds.makeIdentity(self.j_collar_end, a=True)
        functions.alignToAlter(self.j_def_elbow, self.j_fk_low, 2)
        cmds.makeIdentity(self.j_def_elbow, a=True)
        functions.alignToAlter(self.j_def_hand, self.j_fk_low_end, 2)
        cmds.makeIdentity(self.j_def_hand, a=True)

        # parent them under the collar
        cmds.parent(self.j_ik_orig_up, self.j_collar_end)
        cmds.parent(self.j_ik_sc_up, self.j_collar_end)
        cmds.parent(self.j_ik_rp_up, self.j_collar_end)
        cmds.parent(self.j_fk_up, self.j_collar_end)

        # cmds.parent(self.j_def_elbow, self.scaleGrp)
        # cmds.parent(self.j_fk_up, self.scaleGrp)

        self.deformerJoints += [self.j_def_elbow, self.j_def_collar, self.j_def_hand]

        # cmds.connectAttr("{0}.rigVis".format(self.scaleGrp), "{0}.v".format(self.j_fk_up))

    def createControllers(self):
        icon = ic.Icon()

        ## shoulder controller
        shouldercont_scale = (self.init_shoulder_dist / 2, self.init_shoulder_dist / 2, self.init_shoulder_dist / 2)
        self.shoulderCont = objects.Controller(shape="Shoulder",
                                               name="%s_Shoulder_cont" % self.suffix,
                                               scale=shouldercont_scale,
                                               normal=(0, 0, -self.sideMult))

        self.controllers.append(self.shoulderCont.name)
        functions.alignToAlter(self.shoulderCont.name, self.j_def_collar, mode=2)

        _shoulder_off = self.shoulderCont.add_offset("OFF")
        _shoulder_ore = self.shoulderCont.add_offset("ORE")
        _shoulder_auto = self.shoulderCont.add_offset("Auto")

        cmds.parent(_shoulder_auto, self.ikBindGrp)

        ## IK hand controller
        ik_cont_scale = (self.init_lower_arm_dist / 3, self.init_lower_arm_dist / 3, self.init_lower_arm_dist / 3)
        self.handIkCont = objects.Controller(shape="Circle",
                                               name="%s_IK_hand_cont" % self.suffix,
                                               scale=ik_cont_scale,
                                               normal=(self.sideMult, 0, 0))

        self.controllers.append(self.handIkCont.name)
        functions.alignToAlter(self.handIkCont.name, self.j_fk_low_end, mode=2)

        _handIK_off = self.handIkCont.add_offset("OFF")
        _handIK_ore = self.handIkCont.add_offset("ORE")
        _handIK_pos = self.handIkCont.add_offset("POS")

        cmds.parent(_handIK_pos, self.ikBindGrp)

        cmds.addAttr(self.handIkCont.name, shortName="polevector", longName="Pole_Vector", defaultValue=0.0, minValue=0.0,
                     maxValue=1.0,
                     at="double", k=True)
        cmds.addAttr(self.handIkCont.name, shortName="polevectorPin", longName="Pole_Pin", defaultValue=0.0, minValue=0.0,
                     maxValue=1.0,
                     at="double", k=True)
        cmds.addAttr(self.handIkCont.name, shortName="sUpArm", longName="Scale_Upper_Arm", defaultValue=1.0, minValue=0.0,
                     at="double", k=True)
        cmds.addAttr(self.handIkCont.name, shortName="sLowArm", longName="Scale_Lower_Arm", defaultValue=1.0, minValue=0.0,
                     at="double", k=True)
        cmds.addAttr(self.handIkCont.name, shortName="squash", longName="Squash", defaultValue=0.0, minValue=0.0,
                     maxValue=1.0, at="double",
                     k=True)
        cmds.addAttr(self.handIkCont.name, shortName="stretch", longName="Stretch", defaultValue=1.0, minValue=0.0,
                     maxValue=1.0, at="double",
                     k=True)
        cmds.addAttr(self.handIkCont.name, shortName="stretchLimit", longName="StretchLimit", defaultValue=100.0,
                     minValue=0.0,
                     maxValue=1000.0, at="double",
                     k=True)
        cmds.addAttr(self.handIkCont.name, shortName="softIK", longName="SoftIK", defaultValue=0.0, minValue=0.0,
                     maxValue=100.0, k=True)
        cmds.addAttr(self.handIkCont.name, shortName="volume", longName="Volume_Preserve", defaultValue=0.0, at="double",
                     k=True)

        ## Pole Vector Controller
        polecont_scale = (
            (((self.init_upper_arm_dist + self.init_lower_arm_dist) / 2) / 10),
            (((self.init_upper_arm_dist + self.init_lower_arm_dist) / 2) / 10),
            (((self.init_upper_arm_dist + self.init_lower_arm_dist) / 2) / 10)
        )
        self.poleContBridge = cmds.spaceLocator(name="poleVectorBridge_%s" %self.suffix)[0]
        self.poleCont = objects.Controller(shape="Plus",
                                               name="%s_Pole_cont" % self.suffix,
                                               scale=polecont_scale,
                                               normal=(self.sideMult, 0, 0))
        self.controllers.append(self.poleCont.name)
        offset_mag_pole = ((self.init_upper_arm_dist + self.init_lower_arm_dist) / 4)
        offset_vector_pole = api.getBetweenVector(self.j_def_elbow, [self.j_collar_end, self.j_def_hand])

        functions.alignAndAim(self.poleContBridge,
                              targetList=[self.j_def_elbow],
                              aimTargetList=[self.j_collar_end, self.j_def_hand],
                              upVector=self.up_axis,
                              translateOff=(offset_vector_pole * offset_mag_pole)
                              )

        functions.alignTo(self.poleCont.name, self.poleContBridge, position=True, rotation=True)

        _poleCont_off = self.poleCont.add_offset("OFF")
        _poleCont_vis = self.poleCont.add_offset("VIS")

        cmds.parent(_poleCont_vis, self.ikBindGrp)

        ## FK UP Arm Controller

        fk_up_arm_scale = (self.init_upper_arm_dist / 2, self.init_upper_arm_dist / 8, self.init_upper_arm_dist / 8)

        self.upArmFkCont = objects.Controller(shape="Cube",
                                               name="%s_FK_UpArm_cont" % self.suffix,
                                               scale=fk_up_arm_scale)

        self.controllers.append(self.upArmFkCont.name)

        # move the pivot to the bottom
        cmds.xform(self.upArmFkCont.name, piv=(self.sideMult * -(self.init_upper_arm_dist / 2), 0, 0), ws=True)

        # move the controller to the shoulder
        functions.alignToAlter(self.upArmFkCont.name, self.j_fk_up, mode=2)

        _upArmFK_off = self.upArmFkCont.add_offset("OFF")
        _upArmFK_ore = self.upArmFkCont.add_offset("ORE")
        cmds.xform(_upArmFK_off, piv=self.shoulder_pos, ws=True)
        cmds.xform(_upArmFK_ore, piv=self.shoulder_pos, ws=True)

        ## FK LOW Arm Controller
        fk_low_arm_scale = (self.init_lower_arm_dist / 2, self.init_lower_arm_dist / 8, self.init_lower_arm_dist / 8)
        self.lowArmFkCont = objects.Controller(shape="Cube",
                                               name="%s_FK_LowArm_cont" % self.suffix,
                                               scale=fk_low_arm_scale)
        self.controllers.append(self.lowArmFkCont.name)

        # move the pivot to the bottom
        cmds.xform(self.lowArmFkCont.name, piv=(self.sideMult * -(self.init_lower_arm_dist / 2), 0, 0), ws=True)

        # align position and orientation to the joint
        functions.alignToAlter(self.lowArmFkCont.name, self.j_fk_low, mode=2)

        _lowArmFkCont_off = self.lowArmFkCont.add_offset("OFF")
        _lowArmFkCont_ore = self.lowArmFkCont.add_offset("ORE")
        cmds.xform(_lowArmFkCont_off, piv=self.elbow_pos, ws=True)
        cmds.xform(_lowArmFkCont_ore, piv=self.elbow_pos, ws=True)

        ## FK HAND Controller
        fk_cont_scale = (self.init_lower_arm_dist / 5, self.init_lower_arm_dist / 5, self.init_lower_arm_dist / 5)
        # self.handFkCont, dmp = icon.createIcon("Cube", iconName="%s_FK_Hand_cont" % self.suffix, scale=fk_cont_scale)
        self.handFkCont = objects.Controller(shape="Cube", name="%s_FK_Hand_cont" % self.suffix, scale=fk_cont_scale)
        self.controllers.append(self.handFkCont.name)
        functions.alignToAlter(self.handFkCont.name, self.j_def_hand, mode=2)

        _handFkCont_off = self.handFkCont.add_offset("OFF")
        _handFkCont_pos = self.handFkCont.add_offset("POS")
        _handFkCont_ore = self.handFkCont.add_offset("ORE")

        # FK-IK SWITCH Controller
        icon_scale = (self.init_upper_arm_dist / 4, self.init_upper_arm_dist / 4, self.init_upper_arm_dist / 4)
        self.switchFkIkCont = objects.Controller(shape="FkikSwitch", name="%s_FK_IK_cont" % self.suffix, scale=icon_scale)
        self.controllers.append(self.switchFkIkCont.name)
        functions.alignAndAim(self.switchFkIkCont.name, targetList=[self.j_def_hand], aimTargetList=[self.j_def_elbow],
                              upVector=self.up_axis, rotateOff=(0, 180, 0))
        cmds.move((self.up_axis[0] * icon_scale[0] * 2), (self.up_axis[1] * icon_scale[1] * 2),
                  (self.up_axis[2] * icon_scale[2] * 2), self.switchFkIkCont.name, r=True)

        _switchFkIk_pos = self.switchFkIkCont.add_offset("POS")

        cmds.setAttr("{0}.s{1}".format(self.switchFkIkCont.name, "x"), self.sideMult)

        # controller for twist orientation alignment
        cmds.addAttr(self.switchFkIkCont.name, shortName="autoShoulder", longName="Auto_Shoulder", defaultValue=1.0, at="float",
                     minValue=0.0, maxValue=1.0, k=True)
        cmds.addAttr(self.switchFkIkCont.name, shortName="alignShoulder", longName="Align_Shoulder", defaultValue=1.0,
                     at="float",
                     minValue=0.0, maxValue=1.0, k=True)

        cmds.addAttr(self.switchFkIkCont.name, shortName="handAutoTwist", longName="Hand_Auto_Twist", defaultValue=1.0,
                     minValue=0.0,
                     maxValue=1.0, at="float", k=True)
        cmds.addAttr(self.switchFkIkCont.name, shortName="handManualTwist", longName="Hand_Manual_Twist", defaultValue=0.0,
                     at="float",
                     k=True)

        cmds.addAttr(self.switchFkIkCont.name, shortName="shoulderAutoTwist", longName="Shoulder_Auto_Twist", defaultValue=1.0,
                     minValue=0.0, maxValue=1.0, at="float", k=True)
        cmds.addAttr(self.switchFkIkCont.name, shortName="shoulderManualTwist", longName="Shoulder_Manual_Twist",
                     defaultValue=0.0,
                     at="float", k=True)

        cmds.addAttr(self.switchFkIkCont.name, shortName="allowScaling", longName="Allow_Scaling", defaultValue=1.0,
                     minValue=0.0,
                     maxValue=1.0, at="float", k=True)
        cmds.addAttr(self.switchFkIkCont.name, at="enum", k=True, shortName="interpType", longName="Interp_Type",
                     en="No_Flip:Average:Shortest:Longest:Cache", defaultValue=0)

        cmds.addAttr(self.switchFkIkCont.name, shortName="tweakControls", longName="Tweak_Controls", defaultValue=0, at="bool")
        cmds.setAttr("{0}.tweakControls".format(self.switchFkIkCont.name), cb=True)
        cmds.addAttr(self.switchFkIkCont.name, shortName="fingerControls", longName="Finger_Controls", defaultValue=1, at="bool")
        cmds.setAttr("{0}.fingerControls".format(self.switchFkIkCont.name), cb=True)

        ### Create MidLock controller

        midcont_scale = (self.init_lower_arm_dist / 4, self.init_lower_arm_dist / 4, self.init_lower_arm_dist / 4)
        # self.midLockCont, dmp = icon.createIcon("Star", iconName="%s_mid_cont" % self.suffix, scale=midcont_scale,
        #                                         normal=(self.sideMult, 0, 0))
        self.midLockCont = objects.Controller(shape="Star", name="%s_mid_cont" % self.suffix, scale=midcont_scale,
                                              normal=(self.sideMult, 0, 0))

        self.controllers.append(self.midLockCont.name)

        functions.alignToAlter(self.midLockCont.name, self.j_fk_low, 2)

        _midLock_ext = self.midLockCont.add_offset("EXT")
        _midLock_pos = self.midLockCont.add_offset("POS")
        _midLock_ave = self.midLockCont.add_offset("AVE")

        # cmds.parent(self.cont_shoulder_off, self.scaleGrp)
        # cmds.parent(self.cont_fk_up_arm_off, self.nonScaleGrp)
        # cmds.parent(self.cont_fk_low_arm_off, self.nonScaleGrp)
        # cmds.parent(self.cont_fk_hand_off, self.nonScaleGrp)
        # cmds.parent(self.cont_mid_lock_ext, self.scaleGrp)
        # cmds.parent(self.cont_pole_off, self.scaleGrp)
        # cmds.parent(self.cont_fk_ik_pos, self.nonScaleGrp)
        # cmds.parent(self.cont_IK_OFF, self.limbGrp)

        nodesContVis = [_poleCont_off, _shoulder_off, _handIK_off, _handFkCont_off,
                        _switchFkIk_pos,
                        _lowArmFkCont_off, _upArmFK_off, _midLock_ave]

        _ = [cmds.connectAttr("%s.contVis" % self.scaleGrp, "%s.v" % x) for x in nodesContVis]

        # functions.colorize(self.cont_shoulder, self.colorCodes[0])
        # functions.colorize(self.cont_IK_hand, self.colorCodes[0])
        # functions.colorize(self.cont_Pole, self.colorCodes[0])
        # functions.colorize(self.cont_fk_ik, self.colorCodes[0])
        # functions.colorize(self.cont_fk_up_arm, self.colorCodes[0])
        # functions.colorize(self.cont_fk_low_arm, self.colorCodes[0])
        # functions.colorize(self.cont_fk_hand, self.colorCodes[0])
        # functions.colorize(self.cont_mid_lock, self.colorCodes[1])


    # @staticmethod
    # def _ik_rp_setup(start_joint, end_joint, pole_node, suffix):
    #     ik_handle = cmds.ikHandle(sj=start_joint, ee=end_joint[-1], name="ikHandle_%s" % suffix, sol="ikRPsolver")[0]
    #     cmds.poleVectorConstraint(pole_node, ik_handle)
    #
    #     stretch_locs = self.make_stretchy_ik(ik_joints, ik_handle, self.rootIkCont, self.endIKCont,
    #                                          source_parent_cutoff=self.localOffGrp, name=self.suffix)
    #     return ik_handle

    def createRoots(self):
        pass

    def createIKsetup(self):

        # create IK chains
        sc_ik_handle = cmds.ikHandle(sj=self.j_ik_sc_up, ee=self.j_ik_sc_low_end, name="ikHandle_SC_%s" % self.suffix, sol="ikSCsolver")[0]
        rp_ik_handle = cmds.ikHandle(sj=self.j_ik_rp_up, ee=self.j_ik_rp_low_end, name="ikHandle_%s" % self.suffix, sol="ikRPsolver")[0]
        cmds.poleVectorConstraint(self.poleContBridge, rp_ik_handle)
        connection.matrixConstraint(self.poleCont.name, self.poleContBridge, mo=False,
                                    source_parent_cutoff=self.localOffGrp)
        cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % self.poleContBridge)

        # twist (start) lock and distance locators
        # -----------------------------
        # Create Start Lock
        self.startLock = cmds.spaceLocator(name="startLock_%s" % self.suffix)[0]
        functions.alignToAlter(self.startLock, self.j_ik_orig_up, 2)
        self.startLockOre = functions.createUpGrp(self.startLock, "Ore")
        self.startLockPos = functions.createUpGrp(self.startLock, "Pos")
        self.startLockTwist = functions.createUpGrp(self.startLock, "AutoTwist")

        self.endLock = cmds.spaceLocator(name="endLock_%s" %self.suffix)[0]
        functions.alignTo(self.endLock, self.j_def_hand, position=True, rotation=False)

        connection.matrixConstraint(self.j_collar_end, self.startLock, sr=("y", "z"), mo=False)

        distance_start = cmds.spaceLocator(name="distanceStart_%s" % self.suffix)[0]
        cmds.pointConstraint(self.startLock, distance_start, mo=False)

        distance_end = cmds.spaceLocator(name="distanceEnd_%s" % self.suffix)[0]
        cmds.pointConstraint(self.endLock, distance_end, mo=False)

        connection.matrixConstraint(self.handIkCont.name, self.endLock, source_parent_cutoff=self.localOffGrp)

        sc_stretch_locs = self.make_stretchy_ik([self.j_ik_sc_up, self.j_ik_sc_low, self.j_ik_sc_low_end], sc_ik_handle, self.shoulderCont.name, self.handIkCont.name,
                                             source_parent_cutoff=self.localOffGrp, name="sc_%s" %self.suffix, distance_start=distance_start, distance_end=distance_end)
        rp_stretch_locs = self.make_stretchy_ik([self.j_ik_rp_up, self.j_ik_rp_low, self.j_ik_rp_low_end], rp_ik_handle, self.shoulderCont.name, self.handIkCont.name,
                                             source_parent_cutoff=self.localOffGrp, name="rp_%s" %self.suffix, distance_start=distance_start, distance_end=distance_end)
        connection.matrixConstraint(self.handIkCont.name, self.j_ik_sc_low_end, st="xyz", ss="xyz", mo=False,
                                    source_parent_cutoff=self.localOffGrp)

        # # pole vector pinning
        pin_blender = cmds.createNode("blendColors", name="%s_polePin_Blender" %self.suffix)
        cmds.connectAttr("%s.polevectorPin" % self.handIkCont.name, "%s.blender" % pin_blender)

        upper_pin_distance = cmds.createNode("distanceBetween", name="%s_polePin_upperDistance" % self.suffix)
        lower_pin_distance = cmds.createNode("distanceBetween", name="%s_polePin_lowerDistance" % self.suffix)
        pin_root = functions.getShapes(rp_stretch_locs[1])[0]
        pin_mid = functions.getShapes(self.poleContBridge)[0]
        pin_end = functions.getShapes(rp_stretch_locs[0])[0]

        cmds.connectAttr("%s.worldPosition[0]" % pin_root, "%s.point1" % upper_pin_distance)
        cmds.connectAttr("%s.worldPosition[0]" % pin_mid, "%s.point2" % upper_pin_distance)
        cmds.connectAttr("%s.worldPosition[0]" % pin_mid, "%s.point1" % lower_pin_distance)
        cmds.connectAttr("%s.worldPosition[0]" % pin_end, "%s.point2" % lower_pin_distance)

        cmds.connectAttr("%s.distance" % upper_pin_distance, "%s.color1R" % pin_blender)
        cmds.connectAttr("%s.distance" % lower_pin_distance, "%s.color1G" % pin_blender)

        # hijack the joints translate X
        R_plug = connection.connections("%s.tx" % self.j_ik_rp_low, exclude_types=["ikEffector"], return_mode="incoming")[0]["plug_in"]
        G_plug = connection.connections("%s.tx" % self.j_ik_rp_low_end, exclude_types=["ikEffector"], return_mode="incoming")[0]["plug_in"]
        # R_plug = cmds.listConnections("%s.tx" % self.j_ik_rp_low, plugs=True, type="blendColors")[0]
        # G_plug = cmds.listConnections("%s.tx" % self.j_ik_rp_low_end, plugs=True, type="blendColors")[0]

        cmds.connectAttr(R_plug, "%s.color2R" % pin_blender, force=True)
        cmds.connectAttr(G_plug, "%s.color2G" % pin_blender, force=True)
        #
        cmds.connectAttr("%s.outputR" % pin_blender, "%s.tx" % self.j_ik_rp_low, force=True)
        cmds.connectAttr("%s.outputG" % pin_blender, "%s.tx" % self.j_ik_rp_low_end, force=True)



        # for joint, distance_loc, scale_attr in zip([self.j_ik_rp_low, self.j_ik_rp_low_end], [distance_start, distance_end], ["sUpArm", "sLowArm"]):
        #     distance_node = cmds.createNode("distanceBetween", name="%s_polePin_upperDistance" % self.suffix)
        #     cmds.connectAttr("%s.worldPosition[0]" % distance_loc, "%s.point1" % distance_node)
        #     cmds.connectAttr("%s.worldPosition[0]" % self.poleContBridge, "%s.point2" % distance_node)
        #     distance_p = "%s.distance" % distance_node
        #     initial_distance = cmds.getAttr("%s.initialDistance" % joint)
        #
        #     blend_node = cmds.createNode("blendTwoAttr", name="%s_polePin_blend" % self.suffix)
        #     mult_p = op.multiply(initial_distance, "{0}.{1}".format(self.handIkCont, scale_attr))
        #     cmds.connectAttr(mult_p, "%s.input[0]" % blend_node)
        #     cmds.connectAttr(distance_p, "%s.input[1]" % blend_node)
        #     cmds.connectAttr("%s.polevectorPin" % self.handIkCont, "%s.attributesBlender" % blend_node)
        #     cmds.connectAttr("%s.output" % blend_node, "%s.initialDistance" % joint)


        # return ik_handle

    def createFKsetup(self):
        # shoulder

        connection.matrixConstraint(self.shoulderCont.name, self.j_def_collar, ss="x", mo=True, source_parent_cutoff=self.localOffGrp)
        connection.matrixConstraint(self.upArmFkCont.name, self.j_fk_up, ss="x", mo=True, source_parent_cutoff=self.localOffGrp)
        connection.matrixConstraint(self.lowArmFkCont.name, self.j_fk_low, ss="x", mo=True, source_parent_cutoff=self.localOffGrp)
        connection.matrixConstraint(self.handFkCont.name, self.j_fk_low_end, ss="x", mo=True, source_parent_cutoff=self.localOffGrp)

        cmds.parent(self.handFkCont.get_offsets()[-1], self.lowArmFkCont.name)
        cmds.parent(self.lowArmFkCont.get_offsets()[-1], self.upArmFkCont.name)
        cmds.parent(self.upArmFkCont.get_offsets()[-1], self.shoulderCont.name)
        attribute.disconnect_attr(node= self.j_def_collar, attr="inverseScale")
        attribute.disconnect_attr(node= self.j_fk_up, attr="inverseScale")
        attribute.disconnect_attr(node= self.j_fk_low, attr="inverseScale")
        attribute.disconnect_attr(node= self.j_fk_low_end, attr="inverseScale")

        # if self.isLocal:
        #     connection.matrixConstraint(self.limbPlug, self.plugBindGrp)
        # else:
        #     connection.matrixConstraint(self.limbPlug, self.shoulderCont)

    def ikfkSwitching(self):
        pass

    def createRibbons(self):
        pass

    def createTwistSplines(self):
        pass

    def createAngleExtractors(self):
        pass

    def roundUp(self):
        cmds.parentConstraint(self.limbPlug, self.scaleGrp, mo=False)
        cmds.setAttr("%s.rigVis" % self.scaleGrp, 0)

        self.scaleConstraints.append(self.scaleGrp)
        # lock and hide

    def createLimb(self):
        self.createGrp()
        self.createJoints()
        self.createControllers()
        # self.createRoots()
        self.createIKsetup()
        self.createFKsetup()
        # self.ikfkSwitching()
        # self.createRibbons()
        # self.createTwistSplines()
        # self.createAngleExtractors()
        # self.roundUp()

    @staticmethod
    def make_stretchy_ik(joint_chain, ik_handle, root_controller, end_controller, source_parent_cutoff=None, name=None, distance_start=None, distance_end=None):
        if not name:
            name = joint_chain[0]

        attribute.validate_attr("%s.squash" %end_controller, attr_type="double", attr_range=[0.0, 1.0], default_value=0.0)
        attribute.validate_attr("%s.stretch" %end_controller, attr_type="double", attr_range=[0.0, 1.0], default_value=1.0)
        attribute.validate_attr("%s.stretchLimit" %end_controller, attr_type="double", attr_range=[0.0, 99999.0], default_value=100.0)
        attribute.validate_attr("%s.softIK" %end_controller, attr_type="double", attr_range=[0.0, 100.0], default_value=0.0)

        root_loc = cmds.spaceLocator(name="rootLoc_%s" %name)[0]
        functions.alignTo(root_loc, joint_chain[0], position=True, rotation=True)
        connection.matrixConstraint(root_controller, root_loc, sr="xyz", mo=True)
        cmds.aimConstraint(end_controller, root_loc, wuo=root_controller)

        end_loc = cmds.spaceLocator(name="endLoc_%s" %name)[0]
        end_loc_shape = functions.getShapes(end_loc)[0]
        functions.alignTo(end_loc, end_controller, position=True, rotation=True)
        cmds.parent(end_loc, root_loc)
        soft_blend_loc = cmds.spaceLocator(name="softBlendLoc_%s" %name)[0]
        soft_blend_loc_shape = functions.getShapes(soft_blend_loc)[0]
        functions.alignTo(soft_blend_loc, end_controller, position=True, rotation=True)
        connection.matrixSwitch(end_controller, end_loc, soft_blend_loc, "%s.stretch" %end_controller, position=True, rotation=False)

        if not distance_start:
            distance_start_loc =cmds.spaceLocator(name="distance_start_%s" %name)[0]
            connection.matrixConstraint(root_controller, distance_start_loc, sr="xyz", ss="xyz", mo=False)
        else:
            distance_start_loc = distance_start

        if not distance_end:
            distance_end_loc =cmds.spaceLocator(name="distance_end_%s" %name)[0]
            connection.matrixConstraint(end_controller, distance_end_loc, sr="xyz", ss="xyz", mo=False)
        else:
            distance_end_loc = distance_end

        ctrl_distance = cmds.createNode("distanceBetween", name="distance_%s" % name)
        cmds.connectAttr("%s.translate" %distance_start_loc, "%s.point1" %ctrl_distance)
        cmds.connectAttr("%s.translate" %distance_end_loc, "%s.point2" %ctrl_distance)
        ctrl_distance_p = "%s.distance" %ctrl_distance


        plugs_to_sum = []
        for nmb, jnt in enumerate(joint_chain[1:]):
            dist = functions.getDistance(jnt, joint_chain[nmb])
            cmds.addAttr(jnt, ln="initialDistance", at="double", dv=dist)
            plugs_to_sum.append("%s.initialDistance" %jnt)
            # cmds.connectAttr("%s.initialDistance" %jnt, "%s.input1D[%i]" %(sum_of_initial_lengths, nmb))

        sum_of_lengths_p = op.add(value_list=plugs_to_sum)

        # SOFT IK PART
        softIK_sub1_p = op.subtract(sum_of_lengths_p, "%s.softIK" %end_controller)
        # get the scale value from controller
        scale_multMatrix = cmds.createNode("multMatrix", name="_multMatrix")
        scale_decomposeMatrix = cmds.createNode("decomposeMatrix", name="_decomposeMatrix")
        cmds.connectAttr("%s.worldMatrix[0]" %root_controller, "%s.matrixIn[0]" %scale_multMatrix)
        cmds.connectAttr("%s.matrixSum" %scale_multMatrix, "%s.inputMatrix" %scale_decomposeMatrix)

        global_scale_div_p = op.divide(1, "%s.outputScaleX" %scale_decomposeMatrix)
        global_mult_p = op.multiply(ctrl_distance_p, global_scale_div_p)
        softIK_sub2_p = op.subtract(global_mult_p, softIK_sub1_p)
        softIK_div_p = op.divide(softIK_sub2_p, "%s.softIK" %end_controller)
        softIK_invert_p = op.invert(softIK_div_p)
        softIK_exponent_p = op.power(2.71828, softIK_invert_p)
        softIK_mult_p = op.multiply(softIK_exponent_p, "%s.softIK" %end_controller)
        softIK_sub3_p = op.subtract(sum_of_lengths_p, softIK_mult_p)

        condition_zero_p = op.if_else("%s.softIK" %end_controller, ">", 0, softIK_sub3_p, sum_of_lengths_p)
        condition_length_p = op.if_else(global_mult_p, ">", softIK_sub1_p, condition_zero_p, global_mult_p)

        cmds.connectAttr(condition_length_p, "%s.tx" %end_loc)

        # STRETCHING PART
        soft_distance = cmds.createNode("distanceBetween", name="distanceSoft_%s" % name)
        cmds.connectAttr("%s.worldPosition[0]" %end_loc_shape, "%s.point1" %soft_distance)
        cmds.connectAttr("%s.worldPosition[0]" %soft_blend_loc_shape, "%s.point2" %soft_distance)
        soft_distance_p = "%s.distance" %soft_distance

        stretch_global_div_p = op.divide(soft_distance_p, "%s.outputScaleX" %scale_decomposeMatrix, name="globalDivide")
        initial_divide_p = op.divide(ctrl_distance_p, sum_of_lengths_p)

        for jnt in joint_chain[1:]:
            div_initial_by_sum_p = op.divide("%s.initialDistance" %jnt, sum_of_lengths_p)
            mult1_p = op.multiply(stretch_global_div_p, div_initial_by_sum_p)
            # mult2_p = op.multiply("%s.stretch" %end_controller, mult1_p)
            sum1_p = op.add(mult1_p, "%s.initialDistance" %jnt)
            # sum1_p = op.add(mult2_p, "%s.initialDistance" %jnt)
            squash_mult_p = op.multiply(initial_divide_p, "%s.initialDistance" %jnt)

            squash_blend_node = cmds.createNode("blendColors", name="squash_blend_%s" %name)
            cmds.connectAttr(squash_mult_p, "%s.color1R" %squash_blend_node)
            ## Stretch limit
            clamp_node = cmds.createNode("clamp", name="stretchLimit_%s" %name)
            max_distance_p = op.add("%s.stretchLimit" %end_controller, "%s.initialDistance" %jnt)
            cmds.connectAttr(sum1_p, "%s.inputR" % clamp_node)
            cmds.connectAttr(max_distance_p, "%s.maxR" % clamp_node)
            cmds.connectAttr(sum1_p, "%s.minR" % clamp_node)
            ##
            cmds.connectAttr("%s.outputR" % clamp_node, "%s.color2R" %squash_blend_node)
            # cmds.connectAttr(sum1_p, "%s.color2R" %squash_blend_node)
            cmds.connectAttr("%s.squash" %end_controller, "%s.blender" %squash_blend_node)

            cmds.connectAttr("%s.outputR" %squash_blend_node, "%s.tx" %jnt)

        connection.matrixConstraint(soft_blend_loc, ik_handle, mo=False, source_parent_cutoff=source_parent_cutoff)
        return soft_blend_loc, root_loc, distance_start_loc, distance_end_loc


class Guides(object):
    def __init__(self, side="L", suffix="LIMBNAME", segments=None, tMatrix=None, upVector=(0, 1, 0), mirrorVector=(1, 0, 0), lookVector=(0,0,1), *args, **kwargs):
        super(Guides, self).__init__()
        # fool check

        #-------Mandatory------[Start]
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
        #-------Mandatory------[End]

    def draw_joints(self):
        if self.side == "C":
            # Guide joint positions for limbs with no side orientation
            pass
        else:
            # Guide joint positions for limbs with sides
            pass

        # Define the offset vector

        # Draw the joints

        # Update the guideJoints list

        # set orientation of joints

    def define_attributes(self):
        # set joint side and type attributes
        _ = [functions.set_joint_side(jnt, self.side) for jnt in self.guideJoints]

        # ----------Mandatory---------[Start]
        root_jnt = self.guideJoints[0]
        attribute.create_global_joint_attrs(root_jnt, moduleName="%s_MODULENAME" % self.side, upAxis=self.upVector, mirrorAxis=self.mirrorVector, lookAxis=self.lookVector)
        # ----------Mandatory---------[End]

        for attr_dict in LIMB_DATA["properties"]:
            attribute.create_attribute(root_jnt, attr_dict)

    def createGuides(self):
        self.draw_joints()
        self.define_attributes()

    def convertJoints(self, joints_list):
        self.guideJoints = joints_list
        self.define_attributes()