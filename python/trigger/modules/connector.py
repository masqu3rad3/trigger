from maya import cmds
import maya.api.OpenMaya as om

from trigger.library import functions, naming, joint
from trigger.objects.controller import Controller
from trigger.modules import _module

from trigger.core import filelog

LOG = filelog.Filelog(logname=__name__, filename="trigger_log")

LIMB_DATA = {
    "members": ["Root"],
    "properties": [
        {
            "attr_name": "curveAsShape",
            "nice_name": "Use_Curve_as_Joint_Shape",
            "attr_type": "bool",
            "default_value": False,
        }
    ],
    "multi_guide": None,
    "sided": True,
}


class Connector(_module.ModuleCore):
    def __init__(self, build_data=None, inits=None):
        super(Connector, self).__init__()
        if build_data:
            if len(build_data.keys()) > 1:
                LOG.error("Connector can only have one initial joint")
                return
            self.rootInit = build_data["Root"]
        elif inits:
            if len(inits) > 1:
                cmds.error("Connector can only have one initial joint")
                return
            self.rootInit = inits[0]
        else:
            LOG.error("Class needs either build_data or inits to be constructed")
        self.inits.append(self.rootInit)

        # get module properties
        self.useRefOrientation = cmds.getAttr("%s.useRefOri" % self.rootInit)
        self.side = joint.get_joint_side(self.rootInit)
        # try block for backward compatibility
        try:
            self.curveAsShape = cmds.getAttr("%s.curveAsShape" % self.rootInit)
        except ValueError:
            self.curveAsShape = False

        self.module_name = naming.unique_name(
            cmds.getAttr("%s.moduleName" % self.rootInit)
        )

    def execute(self):
        """Execute the module. This is the main function that is called when the module is built."""
        LOG.info("Creating Connector %s" % self.module_name)
        def_j_root = cmds.joint(name=naming.parse([self.module_name], suffix="jDef"))

        functions.align_to(
            def_j_root, self.rootInit, position=True, rotation=self.useRefOrientation
        )

        self.limbPlug = def_j_root
        self.sockets.append(def_j_root)

        if self.curveAsShape:
            _controller = Controller(
                shape="Cube",
                name=naming.parse([self.module_name], suffix="cont"),
                scale=(1, 1, 1),
                normal=(0, 0, 0),
            )
            _controller.set_side(self.side)
            cmds.parent(_controller.shapes[0], def_j_root, relative=True, shape=True)
            cmds.delete(_controller.name)
            cmds.setAttr("%s.drawStyle" % def_j_root, 2)
        else:
            self.deformerJoints.append(def_j_root)

        cmds.connectAttr("%s.jointVis" % self.scaleGrp, "%s.v" % def_j_root)
        cmds.connectAttr("%s.jointVis" % self.scaleGrp, "%s.v" % self.limbGrp)


class Guides(_module.GuidesCore):
    limb_data = LIMB_DATA

    def draw_joints(self):
        # Define the offset vector
        self.offsetVector = om.MVector(0, 1, 0)

        # Draw the joints
        cmds.select(clear=True)
        root_jnt = cmds.joint(
            name=naming.parse([self.name, "root"], side=self.side, suffix="jInit")
        )

        # Update the guideJoints list
        self.guideJoints.append(root_jnt)

        # set orientation of joints

    def define_guides(self):
        """Override the guide definition method"""
        joint.set_joint_type(self.guideJoints[0], "Root")
