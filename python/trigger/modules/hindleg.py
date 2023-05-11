"""Simple hind leg module for quadrupeds"""

from maya import cmds
import maya.api.OpenMaya as om
from trigger.library import functions, joint
from trigger.library import naming
from trigger.library import attribute
from trigger.library import connection
from trigger.library import api
from trigger.library import tools
from trigger.objects.ribbon import Ribbon
from trigger.objects.controller import Controller

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
             "sided": True, }


class Hindleg(object):
    def __init__(self, build_data=None, inits=None, *args, **kwargs):
        super(Hindleg, self).__init__()

        # reinitialize the initial Joints
        if build_data:
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
        self.hindleg_root_pos = api.get_world_translation(self.hindleg_root_ref)
        self.hindhip_pos = api.get_world_translation(self.hindhip_ref)
        self.stifle_pos = api.get_world_translation(self.stifle_ref)
        self.hock_pos = api.get_world_translation(self.hock_ref)
        self.phalanges_pos = api.get_world_translation(self.phalanges_ref)
        self.phalangestip_pos = api.get_world_translation(self.phalangestip_ref)

        # get distances
        self.init_upper_leg_dist = functions.get_distance(self.hindhip_ref, self.stifle_ref)
        self.init_lower_leg_dist = functions.get_distance(self.stifle_ref, self.hock_ref)
        self.init_pastern_dist = functions.get_distance(self.hock_ref, self.phalanges_ref)
        self.init_foot_dist = functions.get_distance(self.phalanges_ref, self.phalangestip_ref)

        # get the properties from the root
        self.useRefOrientation = cmds.getAttr("%s.useRefOri" % self.hindleg_root_ref)
        self.side = joint.get_joint_side(self.hindleg_root_ref)
        self.sideMult = -1 if self.side == "R" else 1
        try:
            self.isLocal = bool(cmds.getAttr("%s.localJoints" % self.hindleg_root_ref))
        except ValueError:
            self.isLocal = False
        self.isStretchy = bool(cmds.getAttr("%s.stretchyIK" % self.hindleg_root_ref))
        self.isRibbon = bool(cmds.getAttr("%s.ribbon" % self.hindleg_root_ref))

        # initialize coordinates
        self.up_axis, self.mirror_axis, self.look_axis = joint.get_rig_axes(self.hindleg_root_ref)

        # self.originalSuffix = suffix
        self.module_name = (naming.unique_name(cmds.getAttr("%s.moduleName" % self.hindleg_root_ref)))

        # module variables
        self.pole_bridge = None
        self.j_def_hindleg_root = None
        self.j_def_hindhip = None
        self.j_def_stifle = None
        self.j_def_hock = None
        self.j_def_phalanges = None
        self.j_phalanges_tip = None
        self.j_ik_hip = None
        self.j_ik_stifle = None
        self.j_ik_hock = None
        self.j_ik_phalanges = None
        self.j_ik_phalanges_tip = None
        self.j_fk_hip = None
        self.j_fk_stifle = None
        self.j_fk_hock = None
        self.j_fk_phalanges = None
        self.j_fk_phalanges_tip = None
        self.thigh_cont = None
        self.foot_ik_cont = None
        self.hock_ik_cont = None
        self.pole_ik_cont = None
        self.upper_leg_fk_cont = None
        self.lower_leg_fk_cont = None
        self.pastern_fk_cont = None
        self.foot_fk_cont = None
        self.switch_cont = None

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
        self.localOffGrp = None
        self.controllerGrp = None
        self.contBindGrp = None
        self.scaleHook = None
        self.rigJointsGrp = None
        self.defJointsGrp = None

    def create_grp(self):
        self.limbGrp = cmds.group(name=naming.parse([self.module_name], suffix="grp"), empty=True)
        self.scaleGrp = cmds.group(name=naming.parse([self.module_name, "scale"], suffix="grp"), empty=True)
        functions.align_to(self.scaleGrp, self.hindleg_root_ref, position=True, rotation=False)
        self.nonScaleGrp = cmds.group(name="%s_nonScaleGrp" % self.module_name, empty=True)

        for nicename, attrname in zip(["Control_Visibility", "Joints_Visibility", "Rig_Visibility"], ["contVis", "jointVis", "rigVis"]):
            attribute.create_attribute(self.scaleGrp, nice_name=nicename, attr_name=attrname, attr_type="bool",
                                       keyable=False, display=True)

        cmds.parent(self.scaleGrp, self.limbGrp)
        cmds.parent(self.nonScaleGrp, self.limbGrp)

        self.localOffGrp = cmds.group(name=naming.parse([self.module_name, "localOffset"], suffix="grp"), empty=True)
        self.controllerGrp = cmds.group(name=naming.parse([self.module_name, "controller"], suffix="grp"), empty=True)
        cmds.parent(self.localOffGrp, self.controllerGrp)
        cmds.parent(self.controllerGrp, self.limbGrp)

        self.contBindGrp = cmds.group(name=naming.parse([self.module_name, "bind"], suffix="grp"), empty=True)
        cmds.parent(self.contBindGrp, self.localOffGrp)

        # scale hook gets the scale value from the bind group but not from the localOffset
        self.scaleHook = cmds.group(name=naming.parse([self.module_name, "scaleHook"], suffix="grp"), empty=True)
        cmds.parent(self.scaleHook, self.limbGrp)
        scale_skips = "xyz" if self.isLocal else ""
        connection.matrixConstraint(self.contBindGrp, self.scaleHook, self.localOffGrp, skipScale=scale_skips)

        self.rigJointsGrp = cmds.group(name=naming.parse([self.module_name, "rigJoints"], suffix="grp"), empty=True)
        self.defJointsGrp = cmds.group(name=naming.parse([self.module_name, "defJoints"], suffix="grp"), empty=True)

        cmds.parent(self.rigJointsGrp, self.limbGrp)
        cmds.parent(self.defJointsGrp, self.limbGrp)

    def create_joints(self):

        # limb plug
        cmds.select(deselect=True)
        self.limbPlug = cmds.joint(name=naming.parse([self.module_name, "plug"], suffix="j"), position=self.hindleg_root_pos, radius=3)
        cmds.parent(self.limbPlug, self.limbGrp)
        connection.matrixConstraint(self.limbPlug, self.contBindGrp, maintainOffset=True)
        if self.isLocal:
            connection.matrixConstraint(self.limbPlug, self.localOffGrp, maintainOffset=True)

        cmds.select(deselect=True)
        self.j_def_hindleg_root = cmds.joint(name=naming.parse([self.module_name, "hindLegRoot"], suffix="jDef"), position=self.hindleg_root_pos, radius=1.5)
        self.sockets.append(self.j_def_hindleg_root)
        self.deformerJoints.append(self.j_def_hindleg_root)
        self.j_def_hindhip = cmds.joint(name=naming.parse([self.module_name, "hindHip"], suffix="jDef"), position=self.hindhip_pos, radius=1.5)
        self.sockets.append(self.j_def_hindhip)

        if not self.useRefOrientation:
            joint.orient_joints([self.j_def_hindleg_root, self.j_def_hindhip], world_up_axis=self.look_axis,
                                up_axis=(0, 1, 0),
                                reverse_aim=self.sideMult, reverse_up=self.sideMult)
        else:
            functions.align_to(self.j_def_hindleg_root, self.hindleg_root_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_def_hindleg_root, apply=True)
            functions.align_to(self.j_def_hindhip, self.hindhip_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_def_hindhip, apply=True)

        cmds.select(deselect=True)
        self.j_def_stifle = cmds.joint(name=naming.parse([self.module_name, "stifle"], suffix="jDef"), position=self.stifle_pos, radius=1.5)
        self.sockets.append(self.j_def_stifle)
        self.deformerJoints.append(self.j_def_stifle)

        cmds.select(deselect=True)
        self.j_def_hock = cmds.joint(name=naming.parse([self.module_name, "hock"], suffix="jDef"), position=self.hock_pos, radius=1.0)
        self.sockets.append(self.j_def_hock)
        self.deformerJoints.append(self.j_def_hock)

        cmds.select(deselect=True)
        self.j_def_phalanges = cmds.joint(name=naming.parse([self.module_name, "phalanges"], suffix="jDef"), position=self.phalanges_pos, radius=1.0)
        self.sockets.append(self.j_def_phalanges)
        self.deformerJoints.append(self.j_def_phalanges)

        cmds.select(deselect=True)
        self.j_phalanges_tip = cmds.joint(name=naming.parse([self.module_name, "phalangesTip"], suffix="j"), position=self.phalangestip_pos, radius=1.0)
        self.sockets.append(self.j_phalanges_tip)
        self.deformerJoints.append(self.j_phalanges_tip)

        # IK Joints
        # IK Chain
        cmds.select(deselect=True)
        self.j_ik_hip = cmds.joint(name=naming.parse([self.module_name, "IK", "hindHip"], suffix="j"), position=self.hindhip_pos, radius=0.5)
        self.j_ik_stifle = cmds.joint(name=naming.parse([self.module_name, "IK", "stifle"], suffix="j"), position=self.stifle_pos, radius=0.5)
        self.j_ik_hock = cmds.joint(name=naming.parse([self.module_name, "IK", "hock"], suffix="j"), position=self.hock_pos, radius=0.5)
        self.j_ik_phalanges = cmds.joint(name=naming.parse([self.module_name, "IK", "phalanges"], suffix="j"), position=self.phalanges_pos, radius=0.5)
        self.j_ik_phalanges_tip = cmds.joint(name=naming.parse([self.module_name, "IK", "phalangesTip"], suffix="j"), position=self.phalangestip_pos, radius=0.5)
        cmds.select(deselect=True)

        # orientations

        if not self.useRefOrientation:
            joint.orient_joints(
                [self.j_ik_hip, self.j_ik_stifle, self.j_ik_hock, self.j_ik_phalanges, self.j_ik_phalanges_tip],
                world_up_axis=self.look_axis, up_axis=(0, 1, 0), reverse_aim=self.sideMult,
                reverse_up=self.sideMult)
        else:
            functions.align_to(self.j_ik_hip, self.hindhip_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_hip, apply=True)

            functions.align_to(self.j_ik_stifle, self.stifle_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_stifle, apply=True)

            functions.align_to(self.j_ik_hock, self.hock_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_hock, apply=True)

            functions.align_to(self.j_ik_phalanges, self.phalanges_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_phalanges, apply=True)

            functions.align_to(self.j_ik_phalanges_tip, self.phalangestip_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_ik_phalanges_tip, apply=True)

        # FK Joints
        cmds.select(deselect=True)
        self.j_fk_hip = cmds.joint(name=naming.parse([self.module_name, "FK", "hindHip"], suffix="j"), position=self.hindhip_pos, radius=2.0)
        self.j_fk_stifle = cmds.joint(name=naming.parse([self.module_name, "FK", "stifle"], suffix="j"), position=self.stifle_pos, radius=2.0)
        self.j_fk_hock = cmds.joint(name=naming.parse([self.module_name, "FK", "hock"], suffix="j"), position=self.hock_pos, radius=2.0)
        self.j_fk_phalanges = cmds.joint(name=naming.parse([self.module_name, "FK", "phalanges"], suffix="j"), position=self.phalanges_pos, radius=2.0)
        self.j_fk_phalanges_tip = cmds.joint(name=naming.parse([self.module_name, "FK", "phalangesTip"], suffix="j"), position=self.phalangestip_pos, radius=2.0)

        if not self.useRefOrientation:
            joint.orient_joints(
                [self.j_fk_hip, self.j_fk_stifle, self.j_fk_hock, self.j_fk_phalanges, self.j_fk_phalanges_tip],
                world_up_axis=self.look_axis, up_axis=(0, 1, 0), reverse_aim=self.sideMult,
                reverse_up=self.sideMult)
        else:
            functions.align_to(self.j_fk_hip, self.hindhip_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_fk_hip, apply=True)

            functions.align_to(self.j_fk_stifle, self.stifle_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_fk_stifle, apply=True)

            functions.align_to(self.j_fk_hock, self.hock_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_fk_hock, apply=True)

            functions.align_to(self.j_fk_phalanges, self.phalanges_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_fk_phalanges, apply=True)

            functions.align_to(self.j_fk_phalanges_tip, self.phalangestip_ref, position=True, rotation=True)
            cmds.makeIdentity(self.j_fk_phalanges_tip, apply=True)

        # re-orient single joints
        functions.align_to_alter(self.j_def_hindhip, self.j_fk_hip, 2)
        cmds.makeIdentity(self.j_def_hindhip, apply=True)
        functions.align_to_alter(self.j_def_stifle, self.j_fk_stifle, 2)
        cmds.makeIdentity(self.j_def_stifle, apply=True)
        functions.align_to_alter(self.j_def_hock, self.j_fk_hock, 2)
        cmds.makeIdentity(self.j_def_hock, apply=True)
        functions.align_to_alter(self.j_def_phalanges, self.j_fk_phalanges, 2)
        cmds.makeIdentity(self.j_def_phalanges, apply=True)

        # parent them under the collar
        connection.matrixConstraint(self.j_def_hindhip, self.rigJointsGrp, maintainOffset=False)
        cmds.parent(self.j_ik_hip, self.rigJointsGrp)
        cmds.parent(self.j_fk_hip, self.rigJointsGrp)

        for jnt in [self.j_def_hindhip, self.j_phalanges_tip]:
            cmds.connectAttr("%s.s" % self.scaleHook, "%s.s" % jnt)

        cmds.parent([self.j_def_hindleg_root, self.j_def_stifle, self.j_def_hock, self.j_def_phalanges],
                    self.defJointsGrp)

    def create_controllers(self):

        # THIGH
        thigh_cont_scale = (self.init_upper_leg_dist / 16, self.init_upper_leg_dist / 4, self.init_upper_leg_dist / 4)
        self.thigh_cont = Controller(shape="Cube",
                                     name=naming.parse([self.module_name, "thigh"], suffix="cont"),
                                     scale=thigh_cont_scale,
                                     normal=(0, 0, -self.sideMult)
                                     )

        self.thigh_cont.set_side(self.side, tier=0)
        self.controllers.append(self.thigh_cont.name)
        functions.align_to(self.thigh_cont.name, self.j_def_hindhip, position=True, rotation=False)
        functions.align_to(self.thigh_cont.name, self.j_def_hindleg_root, position=False, rotation=True)

        cmds.move(self.sideMult * (thigh_cont_scale[0] * 3), 0, 0, self.thigh_cont.name, relative=True,
                  objectSpace=True)

        _thigh_off = self.thigh_cont.add_offset("OFF")
        _thigh_ore = self.thigh_cont.add_offset("ORE")
        _thigh_pos = self.thigh_cont.add_offset("POS")

        cmds.xform(self.thigh_cont.name, pivots=self.hindleg_root_pos, worldSpace=True)

        cmds.parent(_thigh_off, self.contBindGrp)

        # #### IK ####

        # FOOT
        foot_cont_scale = (self.init_foot_dist * 1.2, 1, self.init_foot_dist * 0.7)
        self.foot_ik_cont = Controller(shape="Circle",
                                       name=naming.parse([self.module_name, "foot"], suffix="cont"),
                                       scale=foot_cont_scale,
                                       normal=(0, self.sideMult, 0)
                                       )
        self.foot_ik_cont.set_side(self.side, tier=0)
        self.controllers.append(self.foot_ik_cont.name)
        functions.align_between(self.foot_ik_cont.name, self.j_def_phalanges, self.j_phalanges_tip)
        functions.align_to(self.foot_ik_cont.name, self.j_def_phalanges, position=False, rotation=True)

        _foot_off = self.foot_ik_cont.add_offset("OFF")
        _foot_ore = self.foot_ik_cont.add_offset("ORE")
        _foot_pos = self.foot_ik_cont.add_offset("POS")

        cmds.xform(self.foot_ik_cont.name, pivots=self.phalanges_pos, worldSpace=True)
        self.thigh_cont.lock_visibility()

        cmds.parent(_foot_off, self.contBindGrp)

        cmds.addAttr(self.foot_ik_cont.name, shortName="footRoll", longName="Foot_Roll", defaultValue=0.0,
                     attributeType="double",
                     keyable=True)

        if self.isStretchy:
            cmds.addAttr(self.foot_ik_cont.name, shortName="squash", longName="Squash", defaultValue=0.0, minValue=0.0,
                         maxValue=1.0, attributeType="double", keyable=True)
            cmds.addAttr(self.foot_ik_cont.name, shortName="stretch", longName="Stretch", defaultValue=0.0,
                         minValue=0.0,
                         maxValue=1.0, attributeType="double", keyable=True)
            cmds.addAttr(self.foot_ik_cont.name, shortName="stretchLimit", longName="StretchLimit", defaultValue=100.0,
                         minValue=0.0, maxValue=1000.0, attributeType="double", keyable=True)
            cmds.addAttr(self.foot_ik_cont.name, shortName="softIK", longName="SoftIK", defaultValue=0.0,
                         minValue=0.0, maxValue=100.0, attributeType="double", keyable=True)

        # HOCK
        hock_cont_scale = ((self.init_lower_leg_dist + self.init_pastern_dist) * 0.1)
        self.hock_ik_cont = Controller(shape="DualCurvedArrow",
                                       name=naming.parse([self.module_name, "hock"], suffix="cont"),
                                       scale=(hock_cont_scale, hock_cont_scale, hock_cont_scale),
                                       normal=(-self.sideMult, 0, 0)
                                       )
        self.hock_ik_cont.set_side(self.side, tier=0)
        self.controllers.append(self.hock_ik_cont.name)

        offset_mag_pole = ((self.init_lower_leg_dist + self.init_pastern_dist) / 4)
        offset_vector_pole = api.get_between_vector(self.j_def_hock, [self.j_def_stifle, self.j_def_phalanges])

        functions.align_and_aim(self.hock_ik_cont.name,
                                target_list=[self.j_def_hock],
                                aim_target_list=[self.j_def_hock],
                                up_vector=self.up_axis,
                                translate_offset=(offset_vector_pole * offset_mag_pole)
                                )

        functions.align_to(self.hock_ik_cont.name, self.j_def_phalanges, position=False, rotation=True)

        _hock_off = self.hock_ik_cont.add_offset("OFF")
        _hock_ore = self.hock_ik_cont.add_offset("ORE")
        _hock_pos = self.hock_ik_cont.add_offset("POS")

        cmds.xform(self.hock_ik_cont.name, pivots=self.phalanges_pos, worldSpace=True)
        self.hock_ik_cont.lock_visibility()
        self.hock_ik_cont.lock_translate()
        self.hock_ik_cont.lock_scale()
        cmds.parent(_hock_off, self.foot_ik_cont.name)

        # POLEVECTOR
        _scale = (((self.init_upper_leg_dist + self.init_lower_leg_dist) / 2) / 10)
        polecont_scale = (_scale, _scale, _scale)

        self.pole_bridge = cmds.spaceLocator(name=naming.parse([self.module_name, "poleVector"], suffix="brg"))[0]
        cmds.parent(self.pole_bridge, self.nonScaleGrp)
        self.pole_ik_cont = Controller(shape="Sphere",
                                       name=naming.parse([self.module_name, "poleVector"], suffix="cont"),
                                       scale=polecont_scale,
                                       normal=(self.sideMult, 0, 0)
                                       )
        self.pole_ik_cont.set_side(self.side, tier=0)
        self.controllers.append(self.pole_ik_cont.name)
        offset_mag_pole = ((self.init_upper_leg_dist + self.init_lower_leg_dist) / 4)
        offset_vector_pole = api.get_between_vector(self.j_def_stifle, [self.j_def_hindhip, self.j_def_hock])

        functions.align_and_aim(self.pole_bridge,
                                target_list=[self.j_def_stifle],
                                aim_target_list=[self.j_def_hindhip, self.j_def_hock],
                                up_vector=self.up_axis,
                                translate_offset=(offset_vector_pole * offset_mag_pole)
                                )
        # TODO: maybe alignAndAim function shouldn't be used in here
        # reset rotation
        cmds.setAttr("%s.rotate" % self.pole_bridge, 0, 0, 0)

        functions.align_to(self.pole_ik_cont.name, self.pole_bridge, position=True, rotation=True)

        _poleCont_off = self.pole_ik_cont.add_offset("OFF")
        _poleCont_vis = self.pole_ik_cont.add_offset("VIS")
        self.pole_ik_cont.lock_rotate()
        self.pole_ik_cont.lock_scale()
        self.pole_ik_cont.lock_visibility()
        cmds.parent(_poleCont_off, self.contBindGrp)

        # ###### FK ######

        self.upper_leg_fk_cont = self._create_fk_cont(self.j_fk_hip, self.init_upper_leg_dist, name="UpperLeg")
        self.lower_leg_fk_cont = self._create_fk_cont(self.j_fk_stifle, self.init_lower_leg_dist, name="LowerLeg")
        self.pastern_fk_cont = self._create_fk_cont(self.j_fk_hock, self.init_pastern_dist, name="Pastern")
        self.foot_fk_cont = self._create_fk_cont(self.j_fk_phalanges, self.init_foot_dist, name="Foot")

        cmds.parent(self.upper_leg_fk_cont.get_offsets()[-1], self.thigh_cont.name)

        # FK-IK SWITCH Controller
        icon_scale = (self.init_upper_leg_dist / 4, self.init_upper_leg_dist / 4, self.init_upper_leg_dist / 4)
        self.switch_cont = Controller(shape="FkikSwitch", name=naming.parse([self.module_name, "FKIK", "switch"], suffix="cont"), scale=icon_scale)
        self.switch_cont.set_side(self.side, tier=0)
        self.controllers.append(self.switch_cont.name)
        functions.align_and_aim(self.switch_cont.name, target_list=[self.j_def_hock],
                                aim_target_list=[self.j_def_stifle],
                                up_vector=self.up_axis, rotate_offset=(self.sideMult * 90, self.sideMult * 90, 0))
        move_offset = (om.MVector(self.mirror_axis) * self.sideMult) * icon_scale[0]
        cmds.move(move_offset[0], move_offset[1], move_offset[2], self.switch_cont.name, relative=True)

        _switchFkIk_pos = self.switch_cont.add_offset("POS")

        cmds.setAttr("{0}.s{1}".format(self.switch_cont.name, "x"), self.sideMult)

        # controller for twist orientation alignment
        cmds.addAttr(self.switch_cont.name, shortName="alignHip", longName="Align_Hip", defaultValue=0.0,
                     attributeType="float",
                     minValue=0.0, maxValue=1.0, keyable=True)

        cmds.addAttr(self.switch_cont.name, shortName="tweakControls", longName="Tweak_Controls", defaultValue=0,
                     attributeType="bool")
        cmds.setAttr("{0}.tweakControls".format(self.switch_cont.name), channelBox=True)
        cmds.addAttr(self.switch_cont.name, shortName="fingerControls", longName="Finger_Controls", defaultValue=1,
                     attributeType="bool")
        cmds.setAttr("{0}.fingerControls".format(self.switch_cont.name), channelBox=True)

        self.switch_cont.lock_all()
        cmds.parent(_switchFkIk_pos, self.contBindGrp)

    def _create_fk_cont(self, joint, length, name=""):
        """Creates fk controls out of cube aligned to joints"""

        # TODO: This function will be used in all modules that has FK and should be moved outside
        scale = (length * 0.5, length * 0.125, length * 0.125)
        cont = Controller(
            shape="Cube",
            name=naming.parse([self.module_name, "FK", name], suffix="cont"),
            scale=scale
        )
        cont.set_side(self.side, tier=0)
        cmds.xform(cont.name, pivots=(self.sideMult * -(length * 0.5), 0, 0), worldSpace=True)
        functions.align_to_alter(cont.name, joint, mode=2)
        _off = cont.add_offset("OFF")
        _ore = cont.add_offset("ORE")
        cont.freeze(rotate=False)
        return cont

    def common(self):
        """Common stuff for both IK and FK"""

        # connect thigh controller
        connection.matrixConstraint(self.thigh_cont.name, self.j_def_hindleg_root,
                                    source_parent_cutoff=self.localOffGrp)
        attribute.disconnect_attr(node=self.j_def_hindleg_root, attr="inverseScale", suppress_warnings=True)
        cmds.connectAttr("%s.s" % self.scaleHook, "%s.s" % self.j_def_stifle)
        cmds.connectAttr("%s.s" % self.scaleHook, "%s.s" % self.j_def_phalanges)
        cmds.connectAttr("%s.s" % self.scaleHook, "%s.s" % self.j_def_hock)

    def create_ik_setup(self):
        # create ik chains
        hock_ik_handle = \
            cmds.ikHandle(startJoint=self.j_ik_hip,
                          endEffector=self.j_ik_hock,
                          name=naming.parse([self.module_name, "hock"], suffix="IKHandle"),
                          solver="ikRPsolver")[
                0]
        phalanges_ik_handle = \
            cmds.ikHandle(startJoint=self.j_ik_hock, endEffector=self.j_ik_phalanges,
                          name=naming.parse([self.module_name, "phalanges"], suffix="IKHandle"),
                          solver="ikSCsolver")[0]
        phalanges_tip_ik_handle = \
            cmds.ikHandle(startJoint=self.j_ik_phalanges, endEffector=self.j_ik_phalanges_tip,
                          name=naming.parse([self.module_name, "phalangesTip"], suffix="IKHandle"),
                          solver="ikSCsolver")[0]

        connection.matrixConstraint(self.pole_ik_cont.name, self.pole_bridge, maintainOffset=False,
                                    source_parent_cutoff=self.localOffGrp)

        def group_align(nodes, pivot_node, name):
            loc = cmds.spaceLocator(name=naming.parse([self.module_name, name, "trans"], suffix="loc"))[0]
            functions.align_to(loc, pivot_node, rotation=True, position=True)
            grp = functions.create_offset_group(loc, "OFF")
            cmds.parent(nodes, loc)
            return grp, loc

        hock_ik_grp, hock_ik_loc = group_align(hock_ik_handle, self.j_def_phalanges, "hock")
        phalanges_ik_grp, phalanges_ik_loc = group_align(phalanges_ik_handle, self.j_def_phalanges, "phalanges")
        phalanges_tip_ik_grp, phalanges_tip_ik_loc = group_align(phalanges_tip_ik_handle, self.j_def_phalanges,
                                                                 "phalangesTip")
        toe_trans_grp, toe_trans_loc = group_align([hock_ik_grp, phalanges_ik_grp, phalanges_tip_ik_grp],
                                                   self.j_phalanges_tip, "toe")
        foot_trans_grp, foot_trans_loc = group_align(toe_trans_grp, self.j_def_phalanges, "foot")

        cmds.parent(foot_trans_grp, self.nonScaleGrp)

        connection.matrixConstraint(self.foot_ik_cont.name, foot_trans_loc, source_parent_cutoff=self.localOffGrp)
        connection.matrixConstraint(self.hock_ik_cont.name, hock_ik_loc, skipTranslate="xyz",
                                    source_parent_cutoff=self.localOffGrp)

        cmds.poleVectorConstraint(self.pole_bridge, hock_ik_handle)

        # stretchyness
        if self.isStretchy:
            hock_distance_start = cmds.spaceLocator(name=naming.parse([self.module_name, "hock", "distanceStart"], suffix="loc"))[0]
            cmds.parent(hock_distance_start, self.nonScaleGrp)
            cmds.pointConstraint(self.j_def_hindhip, hock_distance_start, maintainOffset=False)

            hock_distance_end = cmds.spaceLocator(name=naming.parse([self.module_name, "hock", "distanceEnd"], suffix="loc"))[0]
            cmds.parent(hock_distance_end, self.nonScaleGrp)
            functions.align_to(hock_distance_end, self.j_def_hock, position=True)
            connection.matrixConstraint(hock_ik_loc, hock_distance_end, maintainOffset=True)

            # create a dummy controller to be used instead of the end controller
            dummy_hock_cont = cmds.spaceLocator(name=naming.parse([self.module_name, "hock", "dummy"], suffix="loc"))[0]
            functions.align_to(dummy_hock_cont, hock_distance_end, position=True, rotation=True)
            # connection.matrixConstraint(self.foot_ik_cont.name, dummy_hock_cont, mo=True)
            connection.matrixConstraint(self.hock_ik_cont.name, dummy_hock_cont, maintainOffset=True)

            cmds.parent(dummy_hock_cont, self.nonScaleGrp)

            hock_stretch_locs = tools.make_stretchy_ik([self.j_ik_hip, self.j_ik_stifle, self.j_ik_hock],
                                                       hock_ik_handle,
                                                       self.thigh_cont.name,
                                                       # self.cont_foot.name,
                                                       # hock_distance_end,
                                                       dummy_hock_cont,
                                                       # self.cont_hock.name,
                                                       # "hock_trans_Loc_L_Hindleg",
                                                       self.side,
                                                       source_parent_cutoff=self.localOffGrp,
                                                       name=naming.parse([self.module_name, "hock"]),
                                                       distance_start=hock_distance_start,
                                                       distance_end=hock_distance_end,
                                                       is_local=self.isLocal)

            attribute.attribute_pass(dummy_hock_cont, self.foot_ik_cont.name, attributes=[], inConnections=True,
                                     outConnections=True,
                                     keepSourceAttributes=False, values=True, daisyChain=False, overrideEx=False)
            cmds.parent(hock_stretch_locs[:2], self.nonScaleGrp)

            # foot roll
            # cmds.parentConstraint(toe_trans_loc, self.hock_ik_cont.get_offsets()[-1], maintainOffset=True)
            _m_matrix, _, _ = connection.matrixConstraint(toe_trans_loc, self.hock_ik_cont.get_offsets()[-1], source_parent_cutoff=self.localOffGrp, maintainOffset=True)
            # replace the inverse matrix with the world matrix for localoffset / hock offset connection. so local joint will work
            cmds.connectAttr("{}.worldMatrix[0]".format(self.localOffGrp), "{}.matrixIn[2]".format(_m_matrix), force=True)

            # connection.matrixConstraint(toe_trans_loc, self.hock_ik_cont.get_offsets()[-1], maintainOffset=True)
            cmds.connectAttr("%s.footRoll" % self.foot_ik_cont.name, "%s.rx" % toe_trans_loc)

    def create_fk_setup(self):
        connection.matrixConstraint(self.upper_leg_fk_cont.name, self.j_fk_hip, maintainOffset=True,
                                    source_parent_cutoff=self.localOffGrp)
        connection.matrixConstraint(self.lower_leg_fk_cont.name, self.j_fk_stifle, maintainOffset=True,
                                    source_parent_cutoff=self.localOffGrp)
        connection.matrixConstraint(self.pastern_fk_cont.name, self.j_fk_hock, maintainOffset=True,
                                    source_parent_cutoff=self.localOffGrp)
        connection.matrixConstraint(self.foot_fk_cont.name, self.j_fk_phalanges, maintainOffset=True,
                                    source_parent_cutoff=self.localOffGrp)

        cmds.parent(self.foot_fk_cont.get_offsets()[-1], self.pastern_fk_cont.name)
        cmds.parent(self.pastern_fk_cont.get_offsets()[-1], self.lower_leg_fk_cont.name)
        cmds.parent(self.lower_leg_fk_cont.get_offsets()[-1], self.upper_leg_fk_cont.name)

        attribute.disconnect_attr(node=self.j_fk_hip, attr="inverseScale", suppress_warnings=True)
        attribute.disconnect_attr(node=self.j_fk_stifle, attr="inverseScale", suppress_warnings=True)
        attribute.disconnect_attr(node=self.j_fk_hock, attr="inverseScale", suppress_warnings=True)
        attribute.disconnect_attr(node=self.j_fk_phalanges, attr="inverseScale", suppress_warnings=True)

    def ikfk_switching(self):

        # connection.matrixSwitch(self.j_ik_hip, self.j_fk_hip, self.j_def_hindhip, "%s.FK_IK" % self.switch_cont.name)
        connection.matrix_switch(self.j_ik_stifle, self.j_fk_stifle, self.j_def_stifle,
                                 "%s.FK_IK" % self.switch_cont.name, position=True, rotation=True)
        cmds.setAttr("%s.jointOrient" % self.j_def_stifle, 0, 0, 0)
        connection.matrix_switch(self.j_ik_hock, self.j_fk_hock, self.j_def_hock, "%s.FK_IK" % self.switch_cont.name)
        cmds.setAttr("%s.jointOrient" % self.j_def_hock, 0, 0, 0)
        connection.matrix_switch(self.j_ik_phalanges, self.j_fk_phalanges, self.j_def_phalanges,
                                 "%s.FK_IK" % self.switch_cont.name)
        cmds.setAttr("%s.jointOrient" % self.j_def_phalanges, 0, 0, 0)

        cmds.parent(self.j_phalanges_tip, self.j_def_phalanges)

        self.hock_ik_cont.drive_visibility("%s.FK_IK" % self.switch_cont.name)
        self.pole_ik_cont.drive_visibility("%s.FK_IK" % self.switch_cont.name)
        self.foot_ik_cont.drive_visibility("%s.FK_IK" % self.switch_cont.name)

        self.upper_leg_fk_cont.drive_visibility("%s.FK_IK_Reverse" % self.switch_cont.name)
        self.lower_leg_fk_cont.drive_visibility("%s.FK_IK_Reverse" % self.switch_cont.name)
        self.pastern_fk_cont.drive_visibility("%s.FK_IK_Reverse" % self.switch_cont.name)
        self.foot_fk_cont.drive_visibility("%s.FK_IK_Reverse" % self.switch_cont.name)

    def create_ribbons(self):
        # UPPER LEG RIBBON

        ribbon_upper_leg = Ribbon(self.j_def_hindhip, self.j_def_stifle, name=naming.parse([self.module_name, "up"]),
                                  connect_start_aim=False,
                                  up_vector=self.up_axis)
        ribbon_upper_leg.create()

        ribbon_upper_leg.pin_start(self.j_def_hindhip)
        ribbon_upper_leg.pin_end(self.j_def_stifle)

        if not self.isLocal:
            cmds.connectAttr("%s.s" % self.scaleHook, "%s.s" % ribbon_upper_leg.scale_grp)

        _upper_leg_ore_con = ribbon_upper_leg.orient(node_a=self.j_ik_hip, node_b=self.j_fk_hip,
                                                     switch_a="%s.FK_IK" % self.switch_cont.name,
                                                     switch_b="%s.FK_IK_Reverse" % self.switch_cont.name)

        # create a secondary parent con for aligning
        upper_leg_paired_con = cmds.parentConstraint(self.j_def_hindhip, ribbon_upper_leg.start_aim,
                                                     maintainOffset=True,
                                                     skipTranslate=["x", "y", "z"]
                                                     )[0]

        pair_blend_node = cmds.listConnections(upper_leg_paired_con, destination=True, type="pairBlend")[0]
        # re-connect to the custom attribute
        cmds.connectAttr("{0}.alignHip".format(self.switch_cont.name), "{0}.weight".format(pair_blend_node), force=True)

        cmds.parent(ribbon_upper_leg.ribbon_grp, self.nonScaleGrp)

        # LOWER LEG RIBBON
        ribbon_lower_leg = Ribbon(self.j_def_stifle, self.j_def_hock, name=naming.parse([self.module_name, "low"]),
                                  connect_start_aim=False,
                                  up_vector=self.up_axis)
        ribbon_lower_leg.create()

        ribbon_lower_leg.pin_start(self.j_def_stifle)
        ribbon_lower_leg.pin_end(self.j_def_hock)

        cmds.parent(ribbon_lower_leg.ribbon_grp, self.nonScaleGrp)

        if not self.isLocal:
            cmds.connectAttr("%s.s" % self.scaleHook, "%s.s" % ribbon_lower_leg.scale_grp)

        # PASTERN RIBBON
        ribbon_pastern = Ribbon(self.j_def_hock, self.j_def_phalanges,
                                name=naming.parse([self.module_name, "pastern"]),
                                connect_start_aim=False,
                                up_vector=self.up_axis
                                )

        ribbon_pastern.create()

        ribbon_pastern.pin_start(self.j_def_hock)
        ribbon_pastern.pin_end(self.j_def_phalanges)

        ribbon_pastern.orient(node_a=self.j_def_hock)

        cmds.parent(ribbon_pastern.ribbon_grp, self.nonScaleGrp)

        if not self.isLocal:
            cmds.connectAttr("%s.s" % self.scaleHook, "%s.s" % ribbon_pastern.scale_grp)

        tweak_conts = ribbon_upper_leg.controllers + ribbon_lower_leg.controllers + ribbon_pastern.controllers
        attribute.drive_attrs("%s.tweakControls" % self.switch_cont.name, ["%s.v" % x.name for x in tweak_conts])

        # add the ribbon deformer joints to the leg module
        self.deformerJoints.extend(ribbon_upper_leg.deformer_joints + ribbon_lower_leg.deformer_joints +
                                   ribbon_pastern.deformer_joints)

    def round_up(self):
        cmds.parentConstraint(self.limbPlug, self.scaleGrp, maintainOffset=False)
        cmds.setAttr("%s.rigVis" % self.scaleGrp, 0)

        self.scaleConstraints.append(self.scaleGrp)

        for jnt in self.deformerJoints:
            cmds.connectAttr("%s.jointVis" % self.scaleGrp, "%s.v" % jnt)
        cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % self.nonScaleGrp)
        cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % self.rigJointsGrp)
        # lock and hide
        # _ = []
        self.anchors = [(self.foot_ik_cont.name, "parent", 1, None), (self.pole_ik_cont.name, "parent", 1, None)]

    def createLimb(self):
        self.create_grp()
        self.create_joints()
        self.create_controllers()
        self.common()
        self.create_ik_setup()
        self.create_fk_setup()
        self.ikfk_switching()
        if self.isRibbon:
            self.create_ribbons()

        self.round_up()


class Guides(object):
    def __init__(self, side="L", suffix="hindleg", segments=None, tMatrix=None, upVector=(0, 1, 0),
                 mirrorVector=(1, 0, 0),
                 lookVector=(0, 0, 1), *args, **kwargs):
        super(Guides, self).__init__()

        self.side = side
        self.sideMultiplier = -1 if side == "R" else 1
        self.name = suffix
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
            hindleg_root_vec = om.MVector(0, 15, 0) * self.tMatrix
            hip_vec = om.MVector(0, 14, 0) * self.tMatrix
            stifle_vec = om.MVector(0, 8, 2) * self.tMatrix
            hock_vec = om.MVector(0, 3, 0) * self.tMatrix
            toes_vec = om.MVector(0, 0, 1) * self.tMatrix
            toetip_vec = om.MVector(0, 0, 3) * self.tMatrix
        else:
            hindleg_root_vec = om.MVector(2 * self.sideMultiplier, 14, 0) * self.tMatrix
            hip_vec = om.MVector(5 * self.sideMultiplier, 14, 0) * self.tMatrix
            stifle_vec = om.MVector(5 * self.sideMultiplier, 8, 2) * self.tMatrix
            hock_vec = om.MVector(5 * self.sideMultiplier, 3, 0) * self.tMatrix
            toes_vec = om.MVector(5 * self.sideMultiplier, 0, 1) * self.tMatrix
            toetip_vec = om.MVector(5 * self.sideMultiplier, 0, 3) * self.tMatrix

        self.offsetVector = -((hindleg_root_vec - hip_vec).normalize())

        cmds.select(deselect=True)
        hindleg = cmds.joint(position=hindleg_root_vec, name=naming.parse([self.name, "root"], side=self.side, suffix="jInit"))
        hip = cmds.joint(position=hip_vec, name=naming.parse([self.name, "hindHip"], side=self.side, suffix="jInit"))
        stifle = cmds.joint(position=stifle_vec, name=naming.parse([self.name, "stifle"], side=self.side, suffix="jInit"))
        hock = cmds.joint(position=hock_vec, name=naming.parse([self.name, "hock"], side=self.side, suffix="jInit"))
        toes = cmds.joint(position=toes_vec, name=naming.parse([self.name, "phalanges"], side=self.side, suffix="jInit"))
        toetip = cmds.joint(position=toetip_vec, name=naming.parse([self.name, "phalangesTip"], side=self.side, suffix="jInit"))

        self.guideJoints = [hindleg, hip, stifle, hock, toes, toetip]

        # Orientation
        joint.orient_joints(self.guideJoints, world_up_axis=self.lookVector, up_axis=(0, 1, 0),
                            reverse_aim=self.sideMultiplier, reverse_up=self.sideMultiplier)

    def define_attributes(self):
        joint.set_joint_type(self.guideJoints[0], "HindlegRoot")
        joint.set_joint_type(self.guideJoints[1], "Hindhip")
        joint.set_joint_type(self.guideJoints[2], "Stifle")
        joint.set_joint_type(self.guideJoints[3], "Hock")
        joint.set_joint_type(self.guideJoints[4], "Phalanges")
        joint.set_joint_type(self.guideJoints[5], "PhalangesTip")
        _ = [joint.set_joint_side(jnt, self.side) for jnt in self.guideJoints]

        root_jnt = self.guideJoints[0]
        attribute.create_global_joint_attrs(root_jnt, moduleName=naming.parse([self.name], side=self.side), upAxis=self.upVector,
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
        _ = [joint.set_joint_side(jnt, self.side) for jnt in self.guideJoints]
        self.define_attributes()
