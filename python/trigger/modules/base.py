from maya import cmds
import maya.api.OpenMaya as om

from trigger.library import functions, naming, joint
from trigger.library import connection
from trigger.objects.controller import Controller
from trigger.modules import _module

from trigger.core import filelog

LOG = filelog.Filelog(logname=__name__, filename="trigger_log")

LIMB_DATA = {
    "members": ["Base"],
    "properties": [],
    "multi_guide": None,
    "sided": False,
}


class Base(_module.ModuleCore):
    def __init__(self, build_data=None, inits=None):
        super(Base, self).__init__()
        if build_data:
            if len(build_data.keys()) > 1:
                LOG.error("Base can only have one initial joint")
                return
            self.inits = [build_data["Base"]]
        elif inits:
            if len(inits) > 1:
                cmds.error("Root can only have one initial joint")
                return

            self.inits = inits
        else:
            LOG.error("Class needs either build_data or inits to be constructed")

        self.module_name = (naming.unique_name(cmds.getAttr("%s.moduleName" % self.inits[0])))
        self.base_jnt = None

    def create_joints(self):
        self.base_jnt = cmds.joint(name=naming.parse([self.module_name], suffix="j"))
        cmds.connectAttr("{0}.rigVis".format(self.scaleGrp), "{0}.v".format(self.base_jnt))

        functions.align_to(self.base_jnt, self.inits[0], position=True, rotation=False)
        self.limbPlug = self.base_jnt
        self.sockets.append(self.base_jnt)

    def create_controllers(self):
        placement_cont = Controller(shape="Circle",
                                    name=naming.parse([self.module_name, "placement"], suffix="cont"),
                                    scale=(10, 10, 10),
                                    side="C",
                                    tier="primary"
                                    )
        master_cont = Controller(shape="TriCircle",
                                 name=naming.parse([self.module_name, "master"], suffix="cont"),
                                 scale=(15, 15, 15),
                                 side="C",
                                 tier="primary"
                                 )

        self.controllers = [master_cont, placement_cont]

        placement_off = placement_cont.add_offset("off")
        master_off = master_cont.add_offset("off")
        functions.align_to(placement_off, self.base_jnt)
        functions.align_to(master_off, self.base_jnt)

        cmds.parent(placement_off, master_cont.name)
        cmds.parent(master_off, self.limbGrp)
        cmds.parentConstraint(placement_cont.name, self.base_jnt, maintainOffset=False)

        self.anchorLocations.append(placement_cont.name)
        self.anchorLocations.append(master_cont.name)

        cmds.connectAttr("%s.contVis" % self.scaleGrp, "%s.v" % placement_off)
        cmds.connectAttr("%s.contVis" % self.scaleGrp, "%s.v" % master_off)

        connection.matrixConstraint(master_cont.name, self.scaleGrp, skipScale="xyz")

        placement_cont.lock(["sx", "sy", "sz", "v"])
        master_cont.lock(["sx", "sy", "sz", "v"])

    def execute(self):
        self.create_joints()
        self.create_controllers()


class Guides(_module.GuidesCore):
    limb_data = LIMB_DATA

    def draw_joints(self):
        # Define the offset vector
        self.offsetVector = om.MVector(0, 1, 0)

        # Draw the joints
        cmds.select(clear=True)
        root_jnt = cmds.joint(name=naming.parse([self.name, "root"], side=self.side, suffix="jInit"))

        # Update the guideJoints list
        self.guideJoints.append(root_jnt)

        # set orientation of joints

    def define_guides(self):
        """Override the guide definition method"""
        joint.set_joint_type(self.guideJoints[0], "Base")
