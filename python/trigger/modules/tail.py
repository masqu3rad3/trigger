from maya import cmds
import maya.api.OpenMaya as om

from trigger.library import functions, joint
from trigger.library import naming
from trigger.library import attribute
from trigger.library import api
from trigger.objects.controller import Controller
from trigger.modules import _module

from trigger.core import filelog

log = filelog.Filelog(logname=__name__, filename="trigger_log")

LIMB_DATA = {
    "members": ["TailRoot", "Tail"],
    "properties": [],
    "multi_guide": "Tail",
    "sided": True,
}


class Tail(_module.ModuleCore):

    def __init__(self, build_data=None, inits=None):
        super(Tail, self).__init__()
        if build_data:
            self.tailRoot = build_data.get("TailRoot")
            self.tails = (build_data.get("Tail"))
            self.inits = [self.tailRoot] + self.tails
        elif inits:
            if len(inits) < 2:
                log.error("Tail setup needs at least 2 initial joints")
                return
            self.inits = inits
        else:
            log.error("Class needs either build_data or inits to be constructed")

        # initialize coordinates
        self.up_axis, self.mirror_axis, self.look_axis = joint.get_rig_axes(self.inits[0])

        # get properties
        self.useRefOrientation = cmds.getAttr("%s.useRefOri" % self.inits[0])
        self.side = joint.get_joint_side(self.inits[0])
        self.sideMult = -1 if self.side == "R" else 1

        # initialize suffix
        self.module_name = (naming.unique_name(cmds.getAttr("%s.moduleName" % self.inits[0])))

    def create_joints(self):
        # draw Joints
        cmds.select(clear=True)
        self.limbPlug = cmds.joint(name=naming.parse([self.module_name, "plug"], suffix="j"),
                                   position=api.get_world_translation(self.inits[0]), radius=3)

        cmds.select(clear=True)
        for idx, jnt in enumerate(self.inits):
            location = api.get_world_translation(jnt)
            _def_jnt = cmds.joint(name=naming.parse([self.module_name, idx], suffix="jDef"), position=location)
            self.sockets.append(_def_jnt)
            self.deformerJoints.append(_def_jnt)

        if not self.useRefOrientation:
            joint.orient_joints(self.deformerJoints, world_up_axis=self.look_axis, up_axis=(0, 1, 0),
                                reverse_aim=self.sideMult, reverse_up=self.sideMult)
        else:
            for x in range(len(self.deformerJoints)):
                functions.align_to(self.deformerJoints[x], self.inits[x], position=True, rotation=True)
                cmds.makeIdentity(self.deformerJoints[x], apply=True)

        cmds.parent(self.deformerJoints[0], self.scaleGrp)

        attribute.drive_attrs("%s.jointVis" % self.scaleGrp, ["%s.v" % x for x in self.deformerJoints])

        cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % self.limbPlug)

        pass

    def create_controllers(self):

        self.controllers = []
        cont_off_list = []

        for nmb, jnt in enumerate(self.deformerJoints[:-1]):
            _scale_distance = functions.get_distance(jnt, self.deformerJoints[nmb + 1]) * 0.5
            cont = Controller(
                name=naming.parse([self.module_name, nmb], suffix="cont"),
                shape="Cube",
                scale=(_scale_distance, _scale_distance, _scale_distance),
                side=self.side,
                tier="primary"
            )
            cmds.xform(cont.name, pivots=(self.sideMult * (-_scale_distance), 0, 0))
            functions.align_to_alter(cont.name, jnt, 2)

            cont_off = cont.add_offset("OFF")
            _cont_ore = cont.add_offset("ORE")

            self.controllers.append(cont)
            cont_off_list.append(cont_off)

            if nmb != 0:
                cmds.parent(cont_off_list[nmb], self.controllers[nmb - 1].name)
            else:
                cmds.parent(cont_off_list[nmb], self.scaleGrp)

            cont.freeze()

        attribute.drive_attrs("%s.contVis" % self.scaleGrp, ["%s.v" % x for x in cont_off_list])

    def create_fk_setup(self):
        for x in range(len(self.controllers)):
            cmds.parentConstraint(self.controllers[x].name, self.deformerJoints[x], maintainOffset=False)

            # additive scalability
            s_global = cmds.createNode("multiplyDivide",
                                       name=naming.parse([self.module_name, "sGlobal", x], suffix="mult"))
            cmds.connectAttr("%s.scale" % self.limbPlug, "%s.input1" % s_global)
            cmds.connectAttr("%s.scale" % self.controllers[x].name, "%s.input2" % s_global)
            cmds.connectAttr("%s.output" % s_global, "%s.scale" % self.deformerJoints[x])

        # last joint has no cont, use the previous one to scale that
        s_global = cmds.createNode("multiplyDivide",
                                   name=naming.parse([self.module_name, "sGlobal", "Last"], suffix="mult"))
        cmds.connectAttr("%s.scale" % self.limbPlug, "%s.input1" % s_global)
        cmds.connectAttr("%s.scale" % self.controllers[-1].name, "%s.input2" % s_global)
        cmds.connectAttr("%s.output" % s_global, "%s.scale" % self.deformerJoints[-1])

    def round_up(self):
        cmds.parentConstraint(self.limbPlug, self.scaleGrp, maintainOffset=False)
        cmds.setAttr("%s.rigVis" % self.scaleGrp, 0)

        self.scaleConstraints.append(self.scaleGrp)

        for cont in self.controllers:
            cont.set_defaults()

    def execute(self):
        self.create_joints()
        self.create_controllers()
        self.create_fk_setup()
        self.round_up()


class Guides(_module.GuidesCore):
    limb_data = LIMB_DATA

    def __init__(self, *args, **kwargs):
        super(Guides, self).__init__(*args, **kwargs)
        self.segments = kwargs.get("segments", 1)  # minimum segments required for the module is 1

    def draw_joints(self):
        # fool check
        if not self.segments or self.segments < 1:
            log.warning("minimum segments required for the simple tail is two. current: %s" % self.segments)
            return

        r_point_tail = om.MVector(0, 14, 0) * self.tMatrix
        if self.side == "C":
            # Guide joint positions for limbs with no side orientation
            n_point_tail = om.MVector(0, 8.075, -7.673) * self.tMatrix
        else:
            # Guide-joint positions for limbs with sides
            n_point_tail = om.MVector(7.673 * self.sideMultiplier, 8.075, 0) * self.tMatrix

        # Define the offset vector
        self.offsetVector = (n_point_tail - r_point_tail).normal()
        add_tail = (n_point_tail - r_point_tail) / ((self.segments + 1) - 1)

        # Draw the joints / set joint side and type attributes
        for seg in range(self.segments + 1):
            jnt = cmds.joint(position=(r_point_tail + (add_tail * seg)),
                             name=naming.parse([self.name, seg], side=self.side, suffix="jInit"))

            joint.set_joint_side(jnt, self.side)
            # Update the guideJoints list
            self.guideJoints.append(jnt)

        # set orientation of joints
        joint.orient_joints(self.guideJoints, world_up_axis=self.lookVector, up_axis=(0, 1, 0),
                            reverse_aim=self.sideMultiplier, reverse_up=self.sideMultiplier)

    def define_guides(self):
        joint.set_joint_type(self.guideJoints[0], "TailRoot")
        _ = [joint.set_joint_type(jnt, "Tail") for jnt in self.guideJoints[1:]]
