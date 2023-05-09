"""Core Class for all trigger modules."""

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

LIMB_DATA = {
    "members": [],
    "properties": [],
    "multi_guide": None,
    "sided": True,
}

class ModuleCore(object):
    def __init__(self, build_data=None, inits=None, *args, **kwargs):

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

    def create_groups(self):
        """Create essential groups for the module. Mandatory for all modules."""
        self.limbGrp = cmds.group(name=naming.parse([self.module_name], suffix="grp"), empty=True)
        self.scaleGrp = cmds.group(name=naming.parse([self.module_name, "scale"], suffix="grp"), empty=True)
        functions.align_to(self.scaleGrp, self.inits[0], position=True, rotation=False)
        self.nonScaleGrp = cmds.group(name="%s_nonScaleGrp" % self.module_name, empty=True)
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

        self.offsetVector = None
        self.guideJoints = []

    def draw_joints(self):
        """Draw the guide joints and set Joint types/sides. This method will be overridden for each module."""
        pass

    def define_attributes(self):
        # ----------Mandatory---------[Start]
        root_jnt = self.guideJoints[0]
        attribute.create_global_joint_attrs(
            root_jnt,
            moduleName="{}_fkik".format(self.side),
            upAxis=self.upVector,
            mirrorAxis=self.mirrorVector,
            lookAxis=self.lookVector)
        # ----------Mandatory---------[End]

        for attr_dict in LIMB_DATA["properties"]:
            attribute.create_attribute(root_jnt, attr_dict)

    def createGuides(self):
        """Create the guides."""
        self.draw_joints()
        self.define_attributes()