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
    name = ""
    def __init__(self, *args, **kwargs):
        self.inits = []
        self.limbGrp = None
        self.scaleGrp = None
        self.nonScaleGrp = None
        self.limbPlug = None
        self.scaleHook = None
        self.isLocal = False
        self.inits = []
        self.module_name = None
        self.controllers = []
        self.sockets = []
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
        self.plugBindGrp = None

        # TODO: Make this redundant. Check it against all modules.
        self.cont_IK_OFF = None

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
        self.scaleGrp = cmds.group(
            name=naming.parse([self.module_name, "scale"], suffix="grp"), empty=True
        )

        functions.align_to(self.scaleGrp, self.inits[0], position=True, rotation=False)
        self.nonScaleGrp = cmds.group(
            name=naming.parse([self.module_name, "nonScale"], suffix="grp"), empty=True
        )

        cmds.addAttr(
            self.scaleGrp,
            attributeType="bool",
            longName="Control_Visibility",
            shortName="contVis",
            defaultValue=True,
        )
        cmds.addAttr(
            self.scaleGrp,
            attributeType="bool",
            longName="Joints_Visibility",
            shortName="jointVis",
            defaultValue=True,
        )
        cmds.addAttr(
            self.scaleGrp,
            attributeType="bool",
            longName="Rig_Visibility",
            shortName="rigVis",
            defaultValue=False,
        )
        # make the created attributes visible in the channel box
        cmds.setAttr("%s.contVis" % self.scaleGrp, channelBox=True)
        cmds.setAttr("%s.jointVis" % self.scaleGrp, channelBox=True)
        cmds.setAttr("%s.rigVis" % self.scaleGrp, channelBox=True)

        cmds.parent(self.scaleGrp, self.limbGrp)
        cmds.parent(self.nonScaleGrp, self.limbGrp)

        self.controllerGrp = cmds.group(
            name=naming.parse([self.module_name, "controller"], suffix="grp"),
            empty=True,
        )
        attribute.drive_attrs(
            "%s.contVis" % self.scaleGrp, ["{}.v".format(self.controllerGrp)]
        )
        attribute.lock_and_hide(self.controllerGrp)
        cmds.parent(self.controllerGrp, self.limbGrp)

        self.localOffGrp = cmds.group(
            name=naming.parse([self.module_name, "localOffset"], suffix="grp"),
            empty=True,
        )
        self.plugBindGrp = cmds.group(
            name=naming.parse([self.module_name, "plugBind"], suffix="grp"), empty=True
        )
        cmds.parent(self.localOffGrp, self.plugBindGrp)
        cmds.parent(self.plugBindGrp, self.controllerGrp)

        self.contBindGrp = cmds.group(
            name=naming.parse([self.module_name, "controllerBind"], suffix="grp"),
            empty=True,
        )
        cmds.parent(self.contBindGrp, self.localOffGrp)

        # scale hook gets the scale value from the bind group but not from the localOffset
        self.scaleHook = cmds.group(
            name=naming.parse([self.module_name, "scaleHook"], suffix="grp"), empty=True
        )
        cmds.parent(self.scaleHook, self.limbGrp)
        scale_skips = "xyz" if self.isLocal else ""
        connection.matrixConstraint(
            self.scaleGrp, self.scaleHook, skipScale=scale_skips
        )

        self.rigJointsGrp = cmds.group(
            name=naming.parse([self.module_name, "rigJoints"], suffix="grp"), empty=True
        )
        self.defJointsGrp = cmds.group(
            name=naming.parse([self.module_name, "defJoints"], suffix="grp"), empty=True
        )
        cmds.parent(self.rigJointsGrp, self.limbGrp)
        cmds.parent(self.defJointsGrp, self.limbGrp)

        self.additional_groups()

    def additional_groups(self):
        """Create additional groups for the module. This method will be overridden for each module."""
        pass

    def execute(self):
        """Execute the rig creation. This method will be overridden for each module."""
        pass

    def finalize(self):
        """Finalize the rig creation. This method will be overridden for each module."""
        # TODO: remove this condition when the modules are finalized
        if self.scaleGrp in self.scaleConstraints:
            LOG.warning(
                "Scale group is in scale constraints list. This needs to be done in inherited class. \
                Remove this in module class"
            )
        else:
            self.scaleConstraints.append(self.scaleGrp)

    def createLimb(self):
        """Create the limb rig."""
        self.create_groups()
        self.execute()
        self.finalize()


class GuidesCore(object):
    name = ""
    limb_data = LIMB_DATA

    def __init__(
        self,
        side="L",
        suffix="",
        segments=None,
        tMatrix=None,
        upVector=(0, 1, 0),
        mirrorVector=(1, 0, 0),
        lookVector=(0, 0, 1),
        *args,
        **kwargs
    ):
        self.side = side
        self.sideMultiplier = -1 if side == "R" else 1
        self.name = suffix or "noName"
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

    def define_guides(self):
        """Define the guide joints. This method will be overridden for each module."""
        pass

    def define_attributes(self):
        """Define the attributes for the module."""

        # TODO: define_guides currently getting overridden on each module.
        #  We need to find a way to make it work without the need of overriding.
        self.define_guides()

        # set sides
        _ = [joint.set_joint_side(jnt, self.side) for jnt in self.guideJoints]

        root_jnt = self.guideJoints[0]
        attribute.create_global_joint_attrs(
            root_jnt,
            moduleName=naming.parse([self.name], side=self.side),
            upAxis=self.upVector,
            mirrorAxis=self.mirrorVector,
            lookAxis=self.lookVector,
        )

        for attr_dict in self.limb_data["properties"]:
            attribute.create_attribute(root_jnt, attr_dict)

    def createGuides(self):
        """Create the guides."""
        self.draw_joints()
        self.define_attributes()

    def convertJoints(self, joints_list):
        """Convert regular joints into guide joints."""
        self._validate(joints_list)
        self.guideJoints = joints_list
        self.define_attributes()

    def _validate(self, joints_list):
        """Validate the guide joints when converting guides."""
        _min = len(self.limb_data["members"])
        _max = _min if not self.limb_data["multi_guide"] else 99999
        if not joints_list:
            LOG.error(
                "joint list not defined for module {0}".format(self.name), proceed=False
            )
        if _min == _max and len(joints_list) != _min:
            LOG.error(
                "segments for module {0} must be equal to {1}".format(self.name, _min),
                proceed=False,
            )
        if _max < len(joints_list) < _min:
            LOG.error(
                "segments for module {0} must be between {1} and {2}".format(
                    self.name, _min, _max
                ),
                proceed=False,
            )
