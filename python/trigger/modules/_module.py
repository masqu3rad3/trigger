"""Core Class for all trigger modules."""

from maya import cmds
import maya.api.OpenMaya as om
from trigger.library import functions
from trigger.library import naming
from trigger.library import attribute
from trigger.library import connection
from trigger.library import joint

from trigger.core import filelog
LOG = filelog.Filelog(logname=__name__, filename="trigger_log")

LIMB_DATA = {
    "members": [],
    "properties": [],
    "multi_guide": None,
    "sided": True,
}

class ModuleCore(object):
    def __init__(self, build_data=None, inits=None, *args, **kwargs):

        self.scaleHook = None
        self.isLocal = False
        self.inits = []
        self.module_name = None
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
        self.localOffGrp = None
        self.controllerGrp = None
        self.contBindGrp = None
        self.scaleHook = None
        self.rigJointsGrp = None
        self.defJointsGrp = None
        self.contBindGrp = None

    def create_groups(self):
        """Create essential groups for the module. Mandatory for all modules."""

        # essential groups
        # limbGrp
        # scaleGrp
        # nonScaleGrp
        # localOffGrp
        # plugBindGrp
        # scaleHook

        # limb group does not have a suffix.
        self.limbGrp = cmds.group(name=naming.parse([self.module_name]), empty=True)

        self.scaleGrp = cmds.group(name=naming.parse([self.module_name, "scale"], suffix="grp"), empty=True)
        functions.align_to(self.scaleGrp, self.inits[0], position=True, rotation=False)
        self.nonScaleGrp = cmds.group(name=naming.parse([self.module_name, "nonScale"], suffix="grp"), empty=True)

        cmds.addAttr(self.scaleGrp, attributeType="bool", longName="Control_Visibility", shortName="contVis", defaultValue=True)
        cmds.addAttr(self.scaleGrp, attributeType="bool", longName="Joints_Visibility", shortName="jointVis", defaultValue=True)
        cmds.addAttr(self.scaleGrp, attributeType="bool", longName="Rig_Visibility", shortName="rigVis", defaultValue=False)
        # make the created attributes visible in the channel box
        cmds.setAttr("%s.contVis" % self.scaleGrp, channelBox=True)
        cmds.setAttr("%s.jointVis" % self.scaleGrp, channelBox=True)
        cmds.setAttr("%s.rigVis" % self.scaleGrp, channelBox=True)

        cmds.parent(self.scaleGrp, self.limbGrp)
        cmds.parent(self.nonScaleGrp, self.limbGrp)
        ################################################################################################################

        self.controllerGrp = cmds.group(name=naming.parse([self.module_name, "controller"], suffix="grp"), empty=True)
        attribute.lock_and_hide(self.controllerGrp)
        cmds.parent(self.controllerGrp, self.limbGrp)

        self.jointGrp = cmds.group(name=naming.parse([self.module_name, "joint"], suffix="grp"), empty=True)
        attribute.lock_and_hide(self.controllerGrp)
        cmds.parent(self.jointGrp, self.limbGrp)

        self.localOffGrp = cmds.group(name=naming.parse([self.module_name, "localOffset"], suffix="grp"), empty=True)
        self.plugBindGrp = cmds.group(name=naming.parse([self.module_name, "plugBind"], suffix="grp"), empty=True)
        cmds.parent(self.localOffGrp, self.plugBindGrp)
        cmds.parent(self.plugBindGrp, self.controllerGrp)

        self.contBindGrp = cmds.group(name=naming.parse([self.module_name, "controllerBind"], suffix="grp"), empty=True)
        cmds.parent(self.contBindGrp, self.localOffGrp)

        ################################################################################################################`
        # self.localOffGrp = cmds.group(name=naming.parse([self.module_name, "localOffset"], suffix="grp"), empty=True)
        # self.plugBindGrp = cmds.group(name=naming.parse([self.module_name, "bind"], suffix="grp"), empty=True)
        #
        # cmds.parent(self.localOffGrp, self.plugBindGrp)
        # cmds.parent(self.plugBindGrp, self.limbGrp)

        # scale hook gets the scale value from the bind group but not from the localOffset
        self.scaleHook = cmds.group(name=naming.parse([self.module_name, "scaleHook"], suffix="grp"), empty=True)
        cmds.parent(self.scaleHook, self.limbGrp)
        scale_skips = "xyz" if self.isLocal else ""
        connection.matrixConstraint(self.scaleGrp, self.scaleHook, skipScale=scale_skips)

        self.rigJointsGrp = cmds.group(name=naming.parse([self.module_name, "rigJoints"], suffix="grp"), empty=True)
        self.defJointsGrp = cmds.group(name=naming.parse([self.module_name, "defJoints"], suffix="grp"), empty=True)
        cmds.parent(self.rigJointsGrp, self.limbGrp)
        cmds.parent(self.defJointsGrp, self.limbGrp)

    def additional_groups(self):
        """Create additional groups for the module. This method will be overridden for each module."""
        pass

    def execute(self):
        """Execute the rig creation. This method will be overridden for each module."""
        pass

    def createLimb(self):
        """Create the limb rig."""
        self.create_groups()
        self.execute()

class GuidesCore(object):
    def __init__(self, side="L", suffix="fkik", segments=None, tMatrix=None, upVector=(0, 1, 0), mirrorVector=(1, 0, 0), lookVector=(0, 0, 1), *args, **kwargs):
        self.side = side
        self.sideMultiplier = -1 if side == "R" else 1
        self.name = suffix
        self.segments = segments
        self.tMatrix = om.MMatrix(tMatrix) if tMatrix else om.MMatrix()
        self.upVector = om.MVector(upVector)
        self.mirrorVector = om.MVector(mirrorVector)
        self.lookVector = om.MVector(lookVector)
        self.limb_data = LIMB_DATA

        self.offsetVector = None
        self.guideJoints = []

    def draw_joints(self):
        """Draw the guide joints and set Joint types/sides. This method will be overridden for each module."""
        pass

    def define_guides(self):
        """Define the guide joints. This method will be overridden for each module."""
        pass

    def define_attributes(self):
        """Define the attributes for the module."""

        # TODO: define_guides currently getting overridden on each module.
        #  We need to find a way to make it work without the need of overriding.
        self.define_guides()
        # multi_guide = self.limb_data["multi_guide"]
        # members = self.limb_data["members"]
        # if not multi_guide:
        #     # if its not a multi guide, set the joint type for each joint with corresponding member
        #     _ = [joint.set_joint_type(jnt, mem) for jnt, mem in zip(self.guideJoints, members)]
        # else:
        #     # if its multi, root is the first member
        #     joint.set_joint_type(self.guideJoints[0], members[0])
        #     for nmb, guide in enumerate(self.guideJoints):
        #         if nmb == 0:
        #             joint.set_joint_type(self.guideJoints[0], members[0])
        #             continue
        #         if members[nmb] == multi_guide:
        #             joint.set_joint_type(guide, multi_guide)
        #             # TODO: MAKE THIS WORK

        # # set joint side and type attributes
        # joint.set_joint_type(self.guideJoints[0], self.limb_data["members"][0]) # root is always first member
        # _ = [joint.set_joint_type(jnt, "Fkik") for jnt in self.guideJoints[1:]]

        # set sides
        _ = [joint.set_joint_side(jnt, self.side) for jnt in self.guideJoints]

        # ----------Mandatory---------[Start]
        root_jnt = self.guideJoints[0]
        attribute.create_global_joint_attrs(
            root_jnt,
            moduleName=naming.parse([self.name], side=self.side),
            upAxis=self.upVector,
            mirrorAxis=self.mirrorVector,
            lookAxis=self.lookVector)
        # ----------Mandatory---------[End]

        for attr_dict in self.limb_data["properties"]:
            attribute.create_attribute(root_jnt, attr_dict)


    def createGuides(self):
        """Create the guides."""
        self.draw_joints()
        self.define_attributes()

    def convertJoints(self, joints_list):
        if len(joints_list) < 2:
            LOG.warning("Define or select at least 2 joints for FK Guide conversion. Skipping")
            return
        self.guideJoints = joints_list
        self.define_attributes()