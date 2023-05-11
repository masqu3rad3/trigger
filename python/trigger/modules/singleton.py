"""Singleton module"""

from maya import cmds
import maya.api.OpenMaya as om
from trigger.library import functions, joint
from trigger.library import naming
from trigger.library import attribute
from trigger.library import connection
from trigger.library import api
from trigger.objects.controller import Controller
from trigger.utils import parentToSurface

from trigger.core import filelog

log = filelog.Filelog(logname=__name__, filename="trigger_log")

LIMB_DATA = {"members": ["SingletonRoot", "Singleton"],
             "properties": [
                 {
                     "attr_name": "localJoints",
                     "nice_name": "Local_Joints",
                     "attr_type": "bool",
                     "default_value": False,
                 },
                 {
                     "attr_name": "surface",
                     "nice_name": "Surface",
                     "attr_type": "string",
                     "default_value": "",
                 },
                 {
                     "attr_name": "directConnect",
                     "nice_name": "Direct_Connect",
                     "attr_type": "bool",
                     "default_value": False,
                     "tooltip": "If checked, controllers will drive joints with a direct connection. This can be"
                                "useful to prevent cycles"
                 },

             ],
             "multi_guide": "Singleton",
             "sided": True, }


class Singleton(object):
    """Creates one or multiple loose controllers. They can be bound to a surface and can be local"""

    def __init__(self, build_data=None, inits=None, *args, **kwargs):
        super(Singleton, self).__init__()
        # fool proofing

        # reinitialize the initial Joints
        if build_data:
            self.singletonRoot = build_data.get("SingletonRoot")
            self.singletons = build_data.get("Singleton", [])
            self.inits = [self.singletonRoot] + self.singletons
        elif inits:
            self.inits = inits
        else:
            log.error("Class needs either build_data or inits to be constructed")

        # get distances

        # get positions

        # get the properties from the root
        self.useRefOrientation = cmds.getAttr("%s.useRefOri" % self.inits[0])
        self.side = joint.get_joint_side(self.inits[0])
        self.sideMult = -1 if self.side == "R" else 1
        self.isLocal = bool(cmds.getAttr("%s.localJoints" % self.inits[0]))
        self.surface = str(cmds.getAttr("%s.surface" % self.inits[0]))
        try:
            self.isDirect = bool(cmds.getAttr("%s.directConnect" % self.inits[0]))
        except ValueError:
            self.isDirect = False

        # initialize coordinates
        self.up_axis, self.mirror_axis, self.look_axis = joint.get_rig_axes(self.inits[0])

        # initialize suffix
        self.module_name = (naming.unique_name(cmds.getAttr("%s.moduleName" % self.inits[0])))

        # module specific variables
        self.localOffGrp = None
        self.plugBindGrp = None
        self.scaleHook = None
        self.joints_grp = None
        self.follicle_grp = None
        self.conts_grp = None

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

    def create_grp(self):
        """Create the necessary groups for the module."""

        self.limbGrp = cmds.group(name=naming.parse([self.module_name], suffix="grp"), empty=True)
        self.scaleGrp = cmds.group(name=naming.parse([self.module_name, "scale"], suffix="grp"), empty=True)
        functions.align_to(self.scaleGrp, self.inits[0], position=True, rotation=False)
        self.nonScaleGrp = cmds.group(name=naming.parse([self.module_name, "nonScale"], suffix="grp"), empty=True)

        for nicename, attrname in zip(["Control_Visibility", "Joints_Visibility", "Rig_Visibility"], ["contVis", "jointVis", "rigVis"]):
            attribute.create_attribute(self.scaleGrp, nice_name=nicename, attr_name=attrname, attr_type="bool",
                                       keyable=False, display=True)

        cmds.parent(self.scaleGrp, self.limbGrp)
        cmds.parent(self.nonScaleGrp, self.limbGrp)

        self.localOffGrp = cmds.group(name=naming.parse([self.module_name, "localOffset"], suffix="grp"), empty=True)
        self.plugBindGrp = cmds.group(name=naming.parse([self.module_name, "bind"], suffix="grp"), empty=True)
        cmds.parent(self.localOffGrp, self.plugBindGrp)
        cmds.parent(self.plugBindGrp, self.limbGrp)

        # scale hook gets the scale value from the bind group but not from the localOffset
        self.scaleHook = cmds.group(name=naming.parse([self.module_name, "scaleHook"], suffix="grp"), empty=True)
        cmds.parent(self.scaleHook, self.limbGrp)
        scale_skips = "xyz" if self.isLocal else ""
        connection.matrixConstraint(self.scaleGrp, self.scaleHook, skipScale=scale_skips)

        self.joints_grp = cmds.group(name=naming.parse([self.module_name, "defJoints"], suffix="grp"), empty=True)
        self.conts_grp = cmds.group(name=naming.parse([self.module_name, "controller"], suffix="grp"), empty=True)
        self.follicle_grp = cmds.group(name=naming.parse([self.module_name, "follicle"], suffix="grp"), empty=True)

        cmds.parent([self.joints_grp, self.conts_grp, self.follicle_grp], self.limbGrp)
        cmds.parent(self.conts_grp, self.localOffGrp)

    def _build_module(self):
        # draw Joints
        cmds.select(deselect=True)
        self.limbPlug = cmds.joint(name=naming.parse([self.module_name, "plug"], suffix="j"), position=api.get_world_translation(self.inits[0]), radius=3)
        cmds.connectAttr("%s.s" % self.scaleGrp, "%s.s" % self.limbPlug)
        cmds.parent(self.limbPlug, self.limbGrp)

        if self.isLocal:
            # if the deformation joints are local, drive the plugBindGrp with limbPlug for negative compensation
            connection.matrixConstraint(self.limbPlug, self.plugBindGrp)
        else:
            # limbplug causes double scaling in here because of that we use scaleHook instead
            connection.matrixConstraint(self.scaleHook, self.conts_grp)

        cmds.select(deselect=True)
        for nmb, j in enumerate(self.inits):
            cmds.select(deselect=True)
            j_def = cmds.joint(name=naming.parse([self.module_name, j], suffix="jDef"))
            j_def_off = functions.create_offset_group(j_def, "off")
            j_def_bind = functions.create_offset_group(j_def, "bind")

            # connect the scale downstream

            cont = Controller(name=naming.parse([self.module_name, (nmb + 1)], suffix="cont"), shape="Circle")
            cont.drive_visibility("%s.contVis" % self.scaleGrp, lock_and_hide=True)
            cont.set_side(side=self.side)
            cont_bind = cont.add_offset("bind")
            cont_off = cont.add_offset("pos")
            functions.align_to(cont_off, j, position=True, rotation=True)

            _cutoff = self.localOffGrp
            if self.surface:
                # if there is a surface constraint, matrix constraint it to the surface and ignore limbPlug
                fol = parentToSurface.parentToSurface([cont_bind], self.surface, mode="matrixConstraint")
                cmds.parent(fol, self.follicle_grp)
                _cutoff = cont_bind if self.isLocal else self.localOffGrp

            if self.isDirect:
                cmds.connectAttr("%s.t" % cont.name, "%s.t" % j_def_bind)
                cmds.connectAttr("%s.r" % cont.name, "%s.r" % j_def_bind)
                cmds.connectAttr("%s.s" % cont.name, "%s.s" % j_def_bind)
                # Since the connection happening in local transform space, we need to move the joint to its position
                functions.align_to(j_def_off, j, position=True, rotation=True)
            else:
                connection.matrixConstraint(cont.name, j_def_bind, maintainOffset=False, source_parent_cutoff=_cutoff)

            cmds.parent(cont_bind, self.conts_grp)
            cmds.parent(j_def_off, self.joints_grp)

            self.sockets.append(j_def)
            self.deformerJoints.append(j_def)

        attribute.drive_attrs("%s.jointVis" % self.scaleGrp, ["%s.v" % x for x in self.deformerJoints])
        cmds.connectAttr("%s.jointVis" % self.scaleGrp, "%s.v" % self.limbPlug)
        functions.colorize(self.deformerJoints, self.colorCodes[0], shape=False)

    def round_up(self):
        cmds.parentConstraint(self.limbPlug, self.scaleGrp, maintainOffset=False)
        cmds.setAttr("%s.rigVis" % self.scaleGrp, 0)

        self.scaleConstraints.append(self.scaleGrp)
        # lock and hide

    def createLimb(self):
        """Create the limb module.
        Do not change the name of this module as it is called dynamically by the rig builder
        """
        self.create_grp()
        self._build_module()
        self.round_up()


class Guides(object):
    def __init__(self, side="L", suffix="singleton", segments=1, tMatrix=None, upVector=(0, 1, 0),
                 mirrorVector=(1, 0, 0), lookVector=(0, 0, 1), *args, **kwargs):
        super(Guides, self).__init__()
        # fool check

        # -------Mandatory------[Start]
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
        # -------Mandatory------[End]

    def draw_joints(self):
        cmds.select(deselect=True)
        r_point_j = om.MVector(0, 0, 0) * self.tMatrix
        if not self.segments:
            self.offsetVector = om.MVector(0, 1, 0)
            singleton_root_jnt = cmds.joint(name=naming.parse([self.name, "root"], side=self.side, suffix="jInit"))
            self.guideJoints.append(singleton_root_jnt)
            return

        if self.side == "C":
            # Guide joint positions for limbs with no side orientation
            n_point_j = om.MVector(0, 0, 10) * self.tMatrix
        else:
            # Guide joint positions for limbs with sides
            n_point_j = om.MVector(10 * self.sideMultiplier, 0, 0) * self.tMatrix

        add_val = (n_point_j - r_point_j) / ((self.segments + 1) - 1)

        # Define the offset vector
        self.offsetVector = (n_point_j - r_point_j).normal()

        # Draw the joints
        for seg in range(self.segments + 1):
            singleton_jnt = cmds.joint(position=(r_point_j + (add_val * seg)),
                                       name=naming.parse([self.name, seg], side=self.side, suffix="jInit"))
            # Update the guideJoints list
            self.guideJoints.append(singleton_jnt)

        # Update the guideJoints list

        # set orientation of joints
        joint.orient_joints(self.guideJoints, world_up_axis=self.upVector, up_axis=(0, 1, 0),
                            reverse_aim=self.sideMultiplier, reverse_up=self.sideMultiplier)

    def define_attributes(self):
        # set joint side and type attributes
        joint.set_joint_type(self.guideJoints[0], "SingletonRoot")
        if len(self.guideJoints) > 1:
            _ = [joint.set_joint_type(jnt, "Singleton") for jnt in self.guideJoints[1:]]
        _ = [joint.set_joint_side(jnt, self.side) for jnt in self.guideJoints]

        # ----------Mandatory---------[Start]
        root_jnt = self.guideJoints[0]
        attribute.create_global_joint_attrs(root_jnt, moduleName=naming.parse([self.name], side=self.side), upAxis=self.upVector,
                                            mirrorAxis=self.mirrorVector, lookAxis=self.lookVector)
        # ----------Mandatory---------[End]

        for attr_dict in LIMB_DATA["properties"]:
            attribute.create_attribute(root_jnt, attr_dict)

    def createGuides(self):
        self.draw_joints()
        self.define_attributes()

    def convertJoints(self, joints_list):
        self.guideJoints = joints_list
        self.define_attributes()
