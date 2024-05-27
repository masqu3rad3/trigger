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
from trigger.core.module import ModuleCore, GuidesCore

from trigger.core import filelog

LOG = filelog.Filelog(logname=__name__, filename="trigger_log")

LIMB_DATA = {
    "members": ["SingletonRoot", "Singleton"],
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
            "useful to prevent cycles",
        },
    ],
    "multi_guide": "Singleton",
    "sided": True,
}


class Singleton(ModuleCore):
    """Creates one or multiple loose controllers. They can be bound to a surface and can be local"""
    name = "Singleton"
    def __init__(self, build_data=None, inits=None):
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
            LOG.error("Class needs either build_data or inits to be constructed")

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
        self.up_axis, self.mirror_axis, self.look_axis = joint.get_rig_axes(
            self.inits[0]
        )

        # initialize suffix
        self.module_name = naming.unique_name(
            cmds.getAttr("%s.moduleName" % self.inits[0])
        )
        self.follicle_grp = None

    def additional_groups(self):
        """Create additional follicle group."""
        self.follicle_grp = cmds.group(
            name=naming.parse([self.module_name, "follicle"], suffix="grp"), empty=True
        )
        cmds.parent(self.follicle_grp, self.limbGrp)

    def _build_module(self):
        # draw Joints
        cmds.select(deselect=True)
        self.limbPlug = cmds.joint(
            name=naming.parse([self.module_name, "plug"], suffix="j"),
            position=api.get_world_translation(self.inits[0]),
            radius=3,
        )
        cmds.connectAttr("%s.s" % self.scaleGrp, "%s.s" % self.limbPlug)
        cmds.parent(self.limbPlug, self.limbGrp)

        if self.isLocal:
            # if the deformation joints are local, drive the plugBindGrp with limbPlug for negative compensation
            connection.matrixConstraint(self.limbPlug, self.plugBindGrp)
        else:
            # limbplug causes double scaling in here because of that we use scaleHook instead
            connection.matrixConstraint(self.scaleHook, self.controllerGrp)

        cmds.select(deselect=True)
        for nmb, j in enumerate(self.inits):
            cmds.select(deselect=True)
            j_def = cmds.joint(name=naming.parse([self.module_name, j], suffix="jDef"))
            j_def_off = functions.create_offset_group(j_def, "off")
            j_def_bind = functions.create_offset_group(j_def, "bind")

            # connect the scale downstream

            cont = Controller(
                name=naming.parse([self.module_name, (nmb + 1)], suffix="cont"),
                shape="Circle",
            )
            cont.drive_visibility("%s.contVis" % self.scaleGrp, lock_and_hide=True)
            cont.set_side(side=self.side)
            cont_bind = cont.add_offset("bind")
            cont_off = cont.add_offset("pos")
            functions.align_to(cont_off, j, position=True, rotation=True)

            _cutoff = self.localOffGrp
            if self.surface:
                # if there is a surface constraint, matrix constraint it to the surface and ignore limbPlug
                fol = parentToSurface.parentToSurface(
                    [cont_bind], self.surface, mode="matrixConstraint"
                )
                cmds.parent(fol, self.follicle_grp)
                _cutoff = cont_bind if self.isLocal else self.localOffGrp

            if self.isDirect:
                cmds.connectAttr("%s.t" % cont.name, "%s.t" % j_def_bind)
                cmds.connectAttr("%s.r" % cont.name, "%s.r" % j_def_bind)
                cmds.connectAttr("%s.s" % cont.name, "%s.s" % j_def_bind)
                # Since the connection happening in local transform space, we need to move the joint to its position
                functions.align_to(j_def_off, j, position=True, rotation=True)
            else:
                connection.matrixConstraint(
                    cont.name,
                    j_def_bind,
                    maintainOffset=False,
                    source_parent_cutoff=_cutoff,
                )

            cmds.parent(cont_bind, self.controllerGrp)
            cmds.parent(j_def_off, self.defJointsGrp)

            self.sockets.append(j_def)
            self.deformerJoints.append(j_def)

        attribute.drive_attrs(
            "%s.jointVis" % self.scaleGrp, ["%s.v" % x for x in self.deformerJoints]
        )
        cmds.connectAttr("%s.jointVis" % self.scaleGrp, "%s.v" % self.limbPlug)

    def round_up(self):
        cmds.parentConstraint(self.limbPlug, self.scaleGrp, maintainOffset=False)
        cmds.setAttr("%s.rigVis" % self.scaleGrp, 0)
        # lock and hide

    def execute(self):
        """Create the limb module."""
        # self.create_grp()
        self._build_module()
        self.round_up()


class Guides(GuidesCore):
    name = "Singleton"
    limb_data = LIMB_DATA

    def draw_joints(self):
        cmds.select(deselect=True)
        r_point_j = om.MVector(0, 0, 0) * self.tMatrix
        if not self.segments:
            self.offsetVector = om.MVector(0, 1, 0)
            singleton_root_jnt = cmds.joint(
                name=naming.parse([self.name, "root"], side=self.side, suffix="jInit")
            )
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
        # for seg in range(self.segments + 1):
        for seg in range(self.segments):
            singleton_jnt = cmds.joint(
                position=(r_point_j + (add_val * seg)),
                name=naming.parse([self.name, seg], side=self.side, suffix="jInit"),
            )
            # Update the guideJoints list
            self.guideJoints.append(singleton_jnt)

        # Update the guideJoints list

        # set orientation of joints
        joint.orient_joints(
            self.guideJoints,
            world_up_axis=self.upVector,
            up_axis=(0, 1, 0),
            reverse_aim=self.sideMultiplier,
            reverse_up=self.sideMultiplier,
        )

    def define_guides(self):
        """Define the guides for the limb."""
        joint.set_joint_type(self.guideJoints[0], "SingletonRoot")
        if len(self.guideJoints) > 1:
            _ = [joint.set_joint_type(jnt, "Singleton") for jnt in self.guideJoints[1:]]
