"""Simple hind leg module for quadrupeds"""

from maya import cmds
import maya.api.OpenMaya as om
from trigger.library import functions
from trigger.library import naming
from trigger.library import attribute
from trigger.library import connection
from trigger.library import api
from trigger.library import controllers as ic

from trigger.core import filelog
log = filelog.Filelog(logname=__name__, filename="trigger_log")


LIMB_DATA = {"members": ["HindlegRoot", "Hindhip", "Stifle", "Hock", "Phalanges", "PhalangesTip"],
             "properties": [
                       ],
        "multi_guide": None,
        "sided": True,}

class Hindleg(object):
    def __init__(self, build_data=None, inits=None, *args, **kwargs):
        super(Hindleg, self).__init__()

        # reinitialize the initial Joints
        if build_data:
            log.debug(build_data)
            self.hindleg_root_ref = build_data["HindlegRoot"]
            self.hindhip_ref = build_data["Hindhip"]
            self.stifle_ref = build_data["Stifle"]
            self.hock_ref = build_data["Hock"]
            self.phalanges_ref = build_data["Phalanges"]
            self.phalangestip_ref = build_data["PhalangesTip"]
        elif inits:
            if len(inits) != 6:
                log.error("Some or all Hind Leg Guide Bones are missing", proceed=False)
            self.hindleg_root_ref = inits[0]
            self.hindhip_ref = inits[1]
            self.stifle_ref = inits[2]
            self.hock_ref = inits[3]
            self.phalanges_ref = inits[4]
            self.phalangestip_ref = inits[5]

        else:
            log.error("Class needs either build_data or inits to be constructed", proceed=False)

        # get positions
        self.hindleg_root_pos = api.getWorldTranslation(self.hindleg_root_ref)
        self.hindhip_pos = api.getWorldTranslation(self.hindhip_ref)
        self.stifle_pos = api.getWorldTranslation(self.stifle_ref)
        self.hock_pos = api.getWorldTranslation(self.hock_ref)
        self.phalanges_pos = api.getWorldTranslation(self.phalanges_ref)
        self.phalangestip_pos = api.getWorldTranslation(self.phalangestip_ref)

        # get distances
        self.init_upper_leg_dist = functions.getDistance(self.hindhip_ref, self.stifle_ref)
        self.init_lower_leg_dist = functions.getDistance(self.stifle_ref, self.hock_ref)
        self.init_pastern_dist = functions.getDistance(self.hock_ref, self.phalanges_ref)

        # get the properties from the root
        self.useRefOrientation = cmds.getAttr("%s.useRefOri" % self.hindleg_root_ref)
        self.side = functions.get_joint_side(self.hindleg_root_ref)
        self.sideMult = -1 if self.side == "R" else 1
        try:
            self.isLocal = bool(cmds.getAttr("%s.localJoints" % self.hindleg_root_ref))
        except ValueError:
            self.isLocal = False

        # initialize coordinates
        self.up_axis, self.mirror_axis, self.look_axis = functions.getRigAxes(self.hindleg_root_ref)

        # self.originalSuffix = suffix
        self.suffix = (naming.uniqueName(cmds.getAttr("%s.moduleName" % self.hindleg_root_ref)))

        # scratch variables
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
        functions.alignTo(self.scaleGrp, self.hindleg_root_ref, position=True, rotation=False)
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
        self.controllerGrp = cmds.group(name="%s_controller_grp" % self.suffix, em=True)
        cmds.parent(self.localOffGrp, self.controllerGrp)
        cmds.parent(self.controllerGrp, self.limbGrp)

        self.contBindGrp = cmds.group(name="%s_bind_grp" % self.suffix, em=True)
        cmds.parent(self.contBindGrp, self.localOffGrp)

        # scale hook gets the scale value from the bind group but not from the localOffset
        self.scaleHook = cmds.group(name="%s_scaleHook" % self.suffix, em=True)
        cmds.parent(self.scaleHook, self.limbGrp)
        scale_skips = "xyz" if self.isLocal else ""
        connection.matrixConstraint(self.contBindGrp, self.scaleHook, self.localOffGrp, ss=scale_skips)

        self.rigJointsGrp = cmds.group(name="%s_rigJoints_grp" % self.suffix, em=True)
        self.defJointsGrp = cmds.group(name="%s_defJoints_grp" % self.suffix, em=True)
        cmds.parent(self.rigJointsGrp, self.limbGrp)
        cmds.parent(self.defJointsGrp, self.limbGrp)

    def createJoints(self):

        # limb plug
        cmds.select(d=True)
        self.limbPlug = cmds.joint(name="jPlug_%s" % self.suffix, p=self.hindleg_root_pos, radius=3)
        cmds.parent(self.limbPlug, self.limbGrp)
        connection.matrixConstraint(self.limbPlug, self.contBindGrp, mo=True)
        if self.isLocal:
            connection.matrixConstraint(self.limbPlug, self.localOffGrp, mo=True)

        cmds.select(d=True)
        self.j_def_hindleg_root = cmds.joint(name="jDef_HindlegRoot_%s" %self.suffix, p=self.hindleg_root_pos, radius=1.5)
        self.sockets.append(self.j_def_hindleg_root)
        self.j_def_hindhip = cmds.joint(name="jDef_Hindhip_%s" %self.suffix, p=self.hindhip_pos, radius=1.5)
        self.sockets.append(self.j_def_hindhip)

        ## PARENTING??

        if not self.useRefOrientation:
            functions.orientJoints([self.j_def_hindleg_root, self.j_def_hindhip], worldUpAxis=(self.look_axis), upAxis=(0, 1, 0),
                                   reverseAim=self.sideMult, reverseUp=self.sideMult)
        else:
            functions.alignTo(self.j_def_hindleg_root, self.hindleg_root_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_def_hindleg_root, a=True)
            functions.alignTo(self.j_def_hindhip, self.hindhip_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_def_hindhip, a=True)

        cmds.select(d=True)
        self.j_def_stifle = cmds.joint(name="jDef_Stifle_%s" %self.suffix, p=self.stifle_pos, radius=1.5)
        self.sockets.append(self.j_def_stifle)

        cmds.select(d=True)
        self.j_def_hock = cmds.joint(name="jDef_Hock_%s" %self.suffix, p=self.hock_pos, radius=1.0)
        self.sockets.append(self.j_def_hock)

        cmds.select(d=True)
        self.j_def_phalanges = cmds.joint(name="jDef_Phalanges_%s" %self.suffix, p=self.phalanges_pos, radius=1.0)
        self.sockets.append(self.j_def_phalanges)

        cmds.select(d=True)
        self.j_phalanges_tip = cmds.joint(name="jDef_PhalangesTip_%s" % self.suffix, p=self.phalangestip_pos, radius=1.0)
        self.sockets.append(self.j_def_phalanges)


        # IK Joints
        # IK Chain
        cmds.select(d=True)
        self.j_ik_hip = cmds.joint(name="jIK_orig_hip_%s" % self.suffix, p=self.hindhip_pos, radius=0.5)
        self.j_ik_stifle = cmds.joint(name="jIK_orig_stifle_%s" % self.suffix, p=self.stifle_pos, radius=0.5)
        self.j_ik_hock = cmds.joint(name="jIK_orig_hock_%s" % self.suffix, p=self.hock_pos, radius=0.5)
        self.j_ik_phalanges = cmds.joint(name="jIK_orig_phalanges_%s" % self.suffix, p=self.phalanges_pos, radius=0.5)
        self.j_ik_phalanges_tip = cmds.joint(name="jIK_orig_phalangesTip_%s" % self.suffix, p=self.phalangestip_pos, radius=0.5)
        cmds.select(d=True)

        # orientations

        if not self.useRefOrientation:
            functions.orientJoints([self.j_ik_hip, self.j_ik_stifle, self.j_ik_hock, self.j_ik_phalanges, self.j_ik_phalanges_tip],
                                   worldUpAxis=(self.look_axis), upAxis=(0, 1, 0), reverseAim=self.sideMult,
                                   reverseUp=self.sideMult)
        else:
            functions.alignTo(self.j_ik_hip, self.hindhip_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_hip, a=True)

            functions.alignTo(self.j_ik_stifle, self.stifle_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_stifle, a=True)

            functions.alignTo(self.j_ik_hock, self.hock_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_hock, a=True)

            functions.alignTo(self.j_ik_phalanges, self.phalanges_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_phalanges, a=True)

            functions.alignTo(self.j_ik_phalanges_tip, self.phalangestip_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_phalanges_tip, a=True)

        # FK Joints
        cmds.select(d=True)
        self.j_fk_hip = cmds.joint(name="jFK_Hindhip_%s" % self.suffix, p=self.hindhip_pos, radius=2.0)
        self.j_fk_stifle = cmds.joint(name="jFK_stifle_%s" % self.suffix, p=self.stifle_pos, radius=2.0)
        self.j_fk_hock = cmds.joint(name="jFK_hock_%s" % self.suffix, p=self.hock_pos, radius=2.0)
        self.j_fk_phalanges = cmds.joint(name="jFK_phalanges_%s" % self.suffix, p=self.phalanges_pos, radius=2.0)
        self.j_fk_phalanges_tip = cmds.joint(name="jFK_phalangesTip_%s" % self.suffix, p=self.phalangestip_pos, radius=2.0)

        if not self.useRefOrientation:
            functions.orientJoints(
                [self.j_fk_hip, self.j_fk_stifle, self.j_fk_hock, self.j_fk_phalanges, self.j_fk_phalanges_tip],
                worldUpAxis=(self.look_axis), upAxis=(0, 1, 0), reverseAim=self.sideMult,
                reverseUp=self.sideMult)
        else:
            functions.alignTo(self.j_fk_hip, self.hindhip_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_fk_hip, a=True)

            functions.alignTo(self.j_fk_stifle, self.stifle_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_fk_stifle, a=True)

            functions.alignTo(self.j_fk_hock, self.hock_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_fk_hock, a=True)

            functions.alignTo(self.j_fk_phalanges, self.phalanges_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_fk_phalanges, a=True)

            functions.alignTo(self.j_fk_phalanges_tip, self.phalangestip_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_fk_phalanges_tip, a=True)

        # re-orient single joints
        functions.alignToAlter(self.j_def_hindhip, self.j_fk_hip, 2)
        cmds.makeIdentity(self.j_def_hindhip, a=True)
        functions.alignToAlter(self.j_def_stifle, self.j_fk_stifle, 2)
        cmds.makeIdentity(self.j_def_stifle, a=True)
        functions.alignToAlter(self.j_def_hock, self.j_fk_hock, 2)
        cmds.makeIdentity(self.j_def_hock, a=True)
        functions.alignToAlter(self.j_def_phalanges, self.j_fk_phalanges, 2)
        cmds.makeIdentity(self.j_def_phalanges, a=True)


    def createLimb(self):
        self.createGrp()
        self.createJoints()
        # self.createControllers()
        # self.createRoots()
        # self.createIKsetup()
        # self.createFKsetup()
        # self.ikfkSwitching()
        # self.createRibbons()
        # self.createTwistSplines()
        # self.createAngleExtractors()
        # self.roundUp()

class Guides(object):
    def __init__(self, side="L", suffix="hindleg", segments=None, tMatrix=None, upVector=(0, 1, 0), mirrorVector=(1, 0, 0),
                 lookVector=(0, 0, 1), *args, **kwargs):
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

        # initial joint positions
        if self.side == "C":
            hindleg_root_vec =  om.MVector(0, 15, 0) * self.tMatrix
            hip_vec =  om.MVector(0, 14, 0) * self.tMatrix
            stifle_vec =  om.MVector(0, 8, 2) * self.tMatrix
            hock_vec = om.MVector(0, 3, 0) * self.tMatrix
            toes_vec = om.MVector(0, 0, 1) * self.tMatrix
            toetip_vec = om.MVector(0, 0, 3) * self.tMatrix
        else:
            hindleg_root_vec =  om.MVector(2 * self.sideMultiplier, 14, 0) * self.tMatrix
            hip_vec =  om.MVector(5 * self.sideMultiplier, 14, 0) * self.tMatrix
            stifle_vec =  om.MVector(5 * self.sideMultiplier, 8, 2) * self.tMatrix
            hock_vec = om.MVector(5 * self.sideMultiplier, 3, 0) * self.tMatrix
            toes_vec = om.MVector(5 * self.sideMultiplier, 0, 1) * self.tMatrix
            toetip_vec = om.MVector(5 * self.sideMultiplier, 0, 3) * self.tMatrix


        self.offsetVector = -((hindleg_root_vec - hip_vec).normalize())

        cmds.select(d=True)
        hindleg = cmds.joint(p=hindleg_root_vec, name="jInit_hindleg_root_%s" % self.suffix)
        hip = cmds.joint(p=hip_vec, name="jInit_hindhip_%s" % self.suffix)
        stifle = cmds.joint(p=stifle_vec, name="jInit_stifle_%s" % self.suffix)
        hock = cmds.joint(p=hock_vec, name="jInit_hock_%s" % self.suffix)
        toes = cmds.joint(p=toes_vec, name="jInit_phalanges_%s" % self.suffix)
        toetip = cmds.joint(p=toetip_vec, name="jInit_phalangestip_%s" % self.suffix)

        self.guideJoints = [hindleg, hip, stifle, hock, toes, toetip]

        # Orientation
        functions.orientJoints(self.guideJoints, worldUpAxis=self.lookVector, upAxis=(0, 1, 0),
                               reverseAim=self.sideMultiplier, reverseUp=self.sideMultiplier)

    def define_attributes(self):
        functions.set_joint_type(self.guideJoints[0], "HindlegRoot")
        functions.set_joint_type(self.guideJoints[1], "Hindhip")
        functions.set_joint_type(self.guideJoints[2], "Stifle")
        functions.set_joint_type(self.guideJoints[3], "Hock")
        functions.set_joint_type(self.guideJoints[4], "Phalanges")
        functions.set_joint_type(self.guideJoints[5], "PhalangesTip")
        _ = [functions.set_joint_side(jnt, self.side) for jnt in self.guideJoints]

        root_jnt = self.guideJoints[0]
        attribute.create_global_joint_attrs(root_jnt, moduleName="%s_Hindleg" % self.side, upAxis=self.upVector,
                                            mirrorAxis=self.mirrorVector, lookAxis=self.lookVector)

        for attr_dict in LIMB_DATA["properties"]:
            attribute.create_attribute(root_jnt, attr_dict)

    def createGuides(self):
        """Main Function to create Guides"""
        self.draw_joints()
        self.define_attributes()

    def convertJoints(self, joints_list):
        if len(joints_list) != 6:
            log.warning("Define or select exactly 5 joints for Arm Guide conversion. Skipping")
            return
        self.guideJoints = joints_list
        _ = [functions.set_joint_side(jnt, self.side) for jnt in self.guideJoints]
        self.define_attributes()
