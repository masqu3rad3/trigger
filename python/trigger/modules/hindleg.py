"""Simple hind leg module for quadrupeds"""

from maya import cmds
import maya.api.OpenMaya as om
from trigger.library import functions
from trigger.library import naming
from trigger.library import attribute
from trigger.library import connection
from trigger.library import objects
from trigger.library import api
from trigger.library import controllers as ic
from trigger.library import tools

from trigger.core import filelog
log = filelog.Filelog(logname=__name__, filename="trigger_log")


LIMB_DATA = {"members": ["HindlegRoot", "Hindhip", "Stifle", "Hock", "Phalanges", "PhalangesTip"],
             "properties": [{"attr_name": "localJoints",
                             "nice_name": "Local_Joints",
                             "attr_type": "bool",
                             "default_value": False},
                            {"attr_name": "stretchyIK",
                             "nice_name": "Stretchy IK",
                             "attr_type": "bool",
                             "default_value": True},
                            {"attr_name": "ribbon",
                             "nice_name": "Ribbon",
                             "attr_type": "bool",
                             "default_value": True},
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
        self.init_foot_dist = functions.getDistance(self.phalanges_ref, self.phalangestip_ref)

        # get the properties from the root
        self.useRefOrientation = cmds.getAttr("%s.useRefOri" % self.hindleg_root_ref)
        self.side = functions.get_joint_side(self.hindleg_root_ref)
        self.sideMult = -1 if self.side == "R" else 1
        try:
            self.isLocal = bool(cmds.getAttr("%s.localJoints" % self.hindleg_root_ref))
        except ValueError:
            self.isLocal = False
        self.isStretchy = bool(cmds.getAttr("%s.stretchyIK" % self.hindleg_root_ref))
        self.isRibbon = bool(cmds.getAttr("%s.ribbon" % self.hindleg_root_ref))

        # initialize coordinates
        self.up_axis, self.mirror_axis, self.look_axis = functions.getRigAxes(self.hindleg_root_ref)

        # self.originalSuffix = suffix
        self.suffix = (naming.uniqueName(cmds.getAttr("%s.moduleName" % self.hindleg_root_ref)))

        # module variables
        self.poleBridge = None

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
        self.j_phalanges_tip = cmds.joint(name="j_PhalangesTip_%s" % self.suffix, p=self.phalangestip_pos, radius=1.0)
        self.sockets.append(self.j_def_phalanges)


        # IK Joints
        # IK Chain
        cmds.select(d=True)
        self.j_ik_hip = cmds.joint(name="jIK_Hindhip_%s" % self.suffix, p=self.hindhip_pos, radius=0.5)
        self.j_ik_stifle = cmds.joint(name="jIK_stifle_%s" % self.suffix, p=self.stifle_pos, radius=0.5)
        self.j_ik_hock = cmds.joint(name="jIK_hock_%s" % self.suffix, p=self.hock_pos, radius=0.5)
        self.j_ik_phalanges = cmds.joint(name="jIK_phalanges_%s" % self.suffix, p=self.phalanges_pos, radius=0.5)
        self.j_ik_phalanges_tip = cmds.joint(name="jIK_phalangesTip_%s" % self.suffix, p=self.phalangestip_pos, radius=0.5)
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

        # parent them under the collar
        connection.matrixConstraint(self.j_def_hindhip, self.rigJointsGrp, mo=False)
        cmds.parent(self.j_ik_hip, self.rigJointsGrp)
        cmds.parent(self.j_fk_hip, self.rigJointsGrp)

        self.deformerJoints += [self.j_def_hindleg_root, self.j_def_hindhip, self.j_def_stifle, self.j_def_hock, self.j_def_phalanges]

        for jnt in [self.j_def_hindhip, self.j_phalanges_tip]:
            cmds.connectAttr("%s.s" % self.scaleHook, "%s.s" % jnt)

    def create_controllers(self):

        #### IK ####

        # THIGH
        thigh_cont_scale = (self.init_upper_leg_dist / 16, self.init_upper_leg_dist / 4, self.init_upper_leg_dist / 4)
        self.cont_thigh = objects.Controller(shape="Cube",
                                             name="%s_Thigh_cont" % self.suffix,
                                             scale=thigh_cont_scale,
                                             normal=(0,0, -self.sideMult))

        self.cont_thigh.set_side(self.side, tier=0)
        self.controllers.append(self.cont_thigh.name)
        functions.alignTo(self.cont_thigh.name, self.j_def_hindhip, position=True, rotation=False)
        functions.alignTo(self.cont_thigh.name, self.j_def_hindleg_root, position=False, rotation=True)

        cmds.move(self.sideMult*(thigh_cont_scale[0] * 3), 0, 0, self.cont_thigh.name, r=True, os=True)

        _thigh_off = self.cont_thigh.add_offset("OFF")
        _thigh_ore = self.cont_thigh.add_offset("ORE")
        _thigh_pos = self.cont_thigh.add_offset("POS")

        cmds.xform(self.cont_thigh.name, piv=self.hindleg_root_pos, ws=True)

        cmds.parent(_thigh_off, self.contBindGrp)

        # FOOT
        foot_cont_scale = (self.init_foot_dist * 1.2, 1, self.init_foot_dist * 0.7)
        self.cont_foot = objects.Controller(shape="Circle",
                                            name="%s_Foot_cont" % self.suffix,
                                            scale=foot_cont_scale,
                                            normal=(0, self.sideMult, 0))
        self.cont_foot.set_side(self.side, tier=0)
        self.controllers.append(self.cont_foot.name)
        functions.alignBetween(self.cont_foot.name, self.j_def_phalanges, self.j_phalanges_tip)
        functions.alignTo(self.cont_foot.name, self.j_def_phalanges, position=False, rotation=True)

        _foot_off = self.cont_foot.add_offset("OFF")
        _foot_ore = self.cont_foot.add_offset("ORE")
        _foot_pos = self.cont_foot.add_offset("POS")

        cmds.xform(self.cont_foot.name, piv=self.phalanges_pos, ws=True)
        self.cont_thigh.lock_visibility()

        cmds.parent(_foot_off, self.contBindGrp)

        if self.isStretchy:
            cmds.addAttr(self.cont_foot.name, shortName="squash", longName="Squash", defaultValue=0.0, minValue=0.0,
                         maxValue=1.0, at="double", k=True)
            cmds.addAttr(self.cont_foot.name, shortName="stretch", longName="Stretch", defaultValue=0.0, minValue=0.0,
                         maxValue=1.0, at="double", k=True)
            cmds.addAttr(self.cont_foot.name, shortName="stretchLimit", longName="StretchLimit", defaultValue=100.0,
                         minValue=0.0, maxValue=1000.0, at="double", k=True)
            cmds.addAttr(self.cont_foot.name, shortName="softIK", longName="SoftIK", defaultValue=0.0,
                         minValue=0.0, maxValue=100.0, at="double", k=True)
        if self.isRibbon:
            cmds.addAttr(self.cont_foot.name, shortName="volume", longName="Volume_Preserve", defaultValue=0.0,
                         at="double", k=True)

        # HOCK
        hock_cont_scale = ((self.init_lower_leg_dist + self.init_pastern_dist)*0.1)
        self.cont_hock = objects.Controller(shape="DualCurvedArrow",
                                            name="%s_Hock_cont" % self.suffix,
                                            scale=(hock_cont_scale, hock_cont_scale, hock_cont_scale),
                                            normal=(-self.sideMult,0,0))
        self.cont_hock.set_side(self.side, tier=0)
        self.controllers.append(self.cont_hock.name)


        offset_mag_pole = ((self.init_lower_leg_dist + self.init_pastern_dist) / 4)
        offset_vector_pole = api.getBetweenVector(self.j_def_hock, [self.j_def_stifle, self.j_def_phalanges])

        functions.alignAndAim(self.cont_hock.name,
                              targetList=[self.j_def_hock],
                              aimTargetList=[self.j_def_hock],
                              upVector=self.up_axis,
                              translateOff=(offset_vector_pole * offset_mag_pole)
                              )

        functions.alignTo(self.cont_hock.name, self.j_def_phalanges, position=False, rotation=True)

        _hock_off = self.cont_hock.add_offset("OFF")
        _hock_ore = self.cont_hock.add_offset("ORE")
        _hock_pos = self.cont_hock.add_offset("POS")

        cmds.xform(self.cont_hock.name, piv=self.phalanges_pos, ws=True)
        self.cont_hock.lock_visibility()
        self.cont_hock.lock_translate()
        self.cont_hock.lock_scale()
        cmds.parent(_hock_off, self.cont_foot.name)

        # POLEVECTOR
        _scale = (((self.init_upper_leg_dist + self.init_lower_leg_dist) / 2) / 10)
        polecont_scale = (_scale, _scale, _scale)

        self.poleBridge = cmds.spaceLocator(name="poleVectorBridge_%s" % self.suffix)[0]
        cmds.parent(self.poleBridge, self.nonScaleGrp)
        self.poleCont = objects.Controller(shape="Sphere",
                                               name="%s_Pole_cont" % self.suffix,
                                               scale=polecont_scale,
                                               normal=(self.sideMult, 0, 0))
        self.poleCont.set_side(self.side, tier=0)
        self.controllers.append(self.poleCont.name)
        offset_mag_pole = ((self.init_upper_leg_dist + self.init_lower_leg_dist) / 4)
        offset_vector_pole = api.getBetweenVector(self.j_def_stifle, [self.j_def_hindhip, self.j_def_hock])

        functions.alignAndAim(self.poleBridge,
                              targetList=[self.j_def_stifle],
                              aimTargetList=[self.j_def_hindhip, self.j_def_hock],
                              upVector=self.up_axis,
                              translateOff=(offset_vector_pole * offset_mag_pole)
                              )
        # TODO: maybe alignAndAim function shouldnt be used in here
        # reset rotation
        cmds.setAttr("%s.rotate" % self.poleBridge, 0,0,0)

        functions.alignTo(self.poleCont.name, self.poleBridge, position=True, rotation=True)

        _poleCont_off = self.poleCont.add_offset("OFF")
        _poleCont_vis = self.poleCont.add_offset("VIS")
        self.poleCont.lock_rotate()
        self.poleCont.lock_scale()
        self.poleCont.lock_visibility()
        cmds.parent(_poleCont_off, self.contBindGrp)


        ###### FK ######

        self.upper_leg_fk_cont = self._create_fk_cont(self.j_fk_hip, self.init_upper_leg_dist, name="FK_UpperLeg")
        self.lower_leg_fk_cont = self._create_fk_cont(self.j_fk_stifle, self.init_lower_leg_dist, name="FK_LowerLeg")
        self.pastern_fk_cont = self._create_fk_cont(self.j_fk_hock, self.init_pastern_dist, name="FK_Pastern")
        self.foot_fk_cont = self._create_fk_cont(self.j_fk_phalanges, self.init_foot_dist, name="FK_Foot")

        # FK-IK SWITCH Controller
        icon_scale = (self.init_upper_leg_dist / 4, self.init_upper_leg_dist / 4, self.init_upper_leg_dist / 4)
        self.switchFkIkCont = objects.Controller(shape="FkikSwitch", name="%s_FK_IK_cont" % self.suffix, scale=icon_scale)
        self.switchFkIkCont.set_side(self.side, tier=0)
        self.controllers.append(self.switchFkIkCont.name)
        functions.alignAndAim(self.switchFkIkCont.name, targetList=[self.j_def_hock], aimTargetList=[self.j_def_stifle],
                              upVector=self.up_axis, rotateOff=(self.sideMult*90, self.sideMult*90, 0))
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

        cmds.parent(_switchFkIk_pos, self.contBindGrp)

    def _create_fk_cont(self, joint, length, name=""):

        scale = (length*0.5, length*0.125, length*0.125)
        cont = objects.Controller(shape="Cube", name="{0}_{1}_cont".format(self.suffix, name), scale=scale)
        cont.set_side(self.side, tier=0)
        cmds.xform(cont.name, piv=(self.sideMult * -(length*0.5), 0, 0), ws=True)
        functions.alignToAlter(cont.name, joint, mode=2)
        _off = cont.add_offset("OFF")
        _ore = cont.add_offset("ORE")
        cont.freeze(rotate=False)
        return cont

    def common(self):
        """Common stuff for both IK and FK"""

        # connect thigh controller
        connection.matrixConstraint(self.cont_thigh.name, self.j_def_hindleg_root, source_parent_cutoff=self.localOffGrp)
        attribute.disconnect_attr(node= self.j_def_hindleg_root, attr="inverseScale", suppress_warnings=True)


    def create_ik_setup(self):
        # create ik chains
        hock_ik_handle = cmds.ikHandle(sj=self.j_ik_hip, ee=self.j_ik_hock, name="ikHandle_Hock_%s" % self.suffix, sol="ikRPsolver")[0]
        phalanges_ik_handle = cmds.ikHandle(sj=self.j_ik_hock, ee=self.j_ik_phalanges, name="ikHandle_Phalanges_%s" % self.suffix, sol="ikSCsolver")[0]
        phalanges_tip_ik_handle = cmds.ikHandle(sj=self.j_ik_phalanges, ee=self.j_ik_phalanges_tip, name="ikHandle_PhalangesTip_%s" % self.suffix, sol="ikSCsolver")[0]

        def group_align(nodes, pivot_node, name):
            loc = cmds.spaceLocator(name="{0}_Loc_{1}".format(name, self.suffix))[0]
            functions.alignTo(loc, pivot_node, rotation=True, position=True)
            grp = functions.createUpGrp(loc, "OFF")
            cmds.parent(nodes, loc)
            return grp, loc

        hock_ik_grp, hock_ik_loc = group_align(hock_ik_handle, self.j_def_phalanges, "hock_trans")
        phalanges_ik_grp, phalanges_ik_loc = group_align(phalanges_ik_handle, self.j_def_phalanges, "phalanges_trans")
        phalanges_tip_ik_grp, phalanges_tip_ik_loc = group_align(phalanges_tip_ik_handle, self.j_def_phalanges, "phalangesTip_trans")
        toe_trans_grp, toe_trans_loc = group_align([hock_ik_grp,phalanges_ik_grp, phalanges_tip_ik_grp], self.j_phalanges_tip, "toe_trans")
        foot_trans_grp, foot_trans_loc = group_align(toe_trans_grp, self.j_def_phalanges, "foot_trans")


        connection.matrixConstraint(self.cont_foot.name, foot_trans_loc, source_parent_cutoff=self.localOffGrp)
        connection.matrixConstraint(self.cont_hock.name, hock_ik_loc, st="xyz", source_parent_cutoff=self.localOffGrp)

        cmds.poleVectorConstraint(self.poleBridge, hock_ik_handle)


        # stretchyness
        if self.isStretchy:
            hock_distance_start = cmds.spaceLocator(name="hock_distanceStart_%s" %self.suffix)[0]
            cmds.parent(hock_distance_start, self.nonScaleGrp)
            cmds.pointConstraint(self.j_def_hindhip, hock_distance_start, mo=False)

            hock_distance_end = cmds.spaceLocator(name="hock_distanceEnd_%s" % self.suffix)[0]
            cmds.parent(hock_distance_end, self.nonScaleGrp)
            functions.alignTo(hock_distance_end, self.j_def_hock, position=True)
            connection.matrixConstraint(hock_ik_loc, hock_distance_end, mo=True)

            hock_stretch_locs = tools.make_stretchy_ik([self.j_ik_hip, self.j_ik_stifle, self.j_ik_hock],
                                                       hock_ik_handle,
                                                       self.cont_thigh.name,
                                                       # self.cont_foot.name,
                                                       hock_distance_end,
                                                       # self.cont_hock.name,
                                                       # "hock_trans_Loc_L_Hindleg",
                                                       self.side,
                                                       source_parent_cutoff=self.localOffGrp,
                                                       name="hock_%s" %self.suffix,
                                                       distance_start=hock_distance_start,
                                                       distance_end=hock_distance_end,
                                                       is_local=self.isLocal)

            cmds.parent(hock_stretch_locs[:2], self.nonScaleGrp)

    def create_fk_setup(self):
        connection.matrixConstraint(self.upper_leg_fk_cont.name, self.j_fk_hip, mo=True, source_parent_cutoff=self.localOffGrp)
        connection.matrixConstraint(self.lower_leg_fk_cont.name, self.j_fk_stifle, mo=True, source_parent_cutoff=self.localOffGrp)
        connection.matrixConstraint(self.pastern_fk_cont.name, self.j_fk_hock, mo=True, source_parent_cutoff=self.localOffGrp)
        connection.matrixConstraint(self.foot_fk_cont.name, self.j_fk_phalanges, mo=True, source_parent_cutoff=self.localOffGrp)

        cmds.parent(self.foot_fk_cont.get_offsets()[-1], self.pastern_fk_cont.name)
        cmds.parent(self.pastern_fk_cont.get_offsets()[-1], self.lower_leg_fk_cont.name)
        cmds.parent(self.lower_leg_fk_cont.get_offsets()[-1], self.upper_leg_fk_cont.name)

        attribute.disconnect_attr(node= self.j_fk_hip, attr="inverseScale", suppress_warnings=True)
        attribute.disconnect_attr(node= self.j_fk_stifle, attr="inverseScale", suppress_warnings=True)
        attribute.disconnect_attr(node= self.j_fk_hock, attr="inverseScale", suppress_warnings=True)
        attribute.disconnect_attr(node= self.j_fk_phalanges, attr="inverseScale", suppress_warnings=True)

    # def ikfk_switching(self):


    def createLimb(self):
        self.createGrp()
        self.createJoints()
        self.create_controllers()
        self.common()
        # self.createRoots()
        self.create_ik_setup()
        self.create_fk_setup()
        # self.ikfk_switching()
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
