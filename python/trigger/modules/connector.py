from maya import cmds
import maya.api.OpenMaya as om

from trigger.library import functions, naming, joint
from trigger.library import attribute
from trigger.objects.controller import Controller

from trigger.core import filelog
LOG = filelog.Filelog(logname=__name__, filename="trigger_log")


LIMB_DATA = {
        "members": ["Root"],
        "properties": [
            {
                "attr_name": "curveAsShape",
                "nice_name": "Use_Curve_as_Joint_Shape",
                "attr_type": "bool",
                "default_value": False
            }
        ],
        "multi_guide": None,
        "sided": True,
    }

class Connector(object):
    def __init__(self, build_data=None, inits=None, *args, **kwargs):
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

        # get module properties
        self.useRefOrientation = cmds.getAttr("%s.useRefOri" % self.rootInit)
        self.side = joint.get_joint_side(self.rootInit)
        # try block for backward compatibility
        try:
            self.curveAsShape = cmds.getAttr("%s.curveAsShape" % self.rootInit)
        except ValueError:
            self.curveAsShape = False

        self.module_name = (naming.unique_name(cmds.getAttr("%s.moduleName" % self.rootInit)))

        self.controllers = []
        self.limbGrp = None
        self.scaleGrp = None
        self.limbPlug = None
        self.nonScaleGrp = None
        self.cont_IK_OFF = None
        self.sockets = []
        self.scaleConstraints = []
        self.anchors = []
        self.anchorLocations = []
        self.deformerJoints = []
        self.colorCodes = []

    def createLimb(self):
        """
        This will create a 'mid node' called connector. This single joint will act as a socket for other limbs to connect to.
        Args:
            inits: (dictionary or list) This is plural for naming convention only. In fact, the function accepts only one joint. If it is a dictionary, the key must be 'Root' and if it is a list it must contain only a single element
            suffix: (string) Name suffix for the nodes will be created

        Returns: None

        """
        LOG.info("Creating Root %s" % self.module_name)

        cmds.select(clear=True)
        self.scaleGrp = cmds.group(name=naming.parse([self.module_name, "scale"], suffix="grp"), empty=True)
        cmds.addAttr(self.scaleGrp, attributeType="bool", longName="Control_Visibility", shortName="contVis", defaultValue=True)
        cmds.addAttr(self.scaleGrp, attributeType="bool", longName="Joints_Visibility", shortName="jointVis", defaultValue=True)
        cmds.addAttr(self.scaleGrp, attributeType="bool", longName="Rig_Visibility", shortName="rigVis", defaultValue=False)
        # make the created attributes visible in the channelbox
        cmds.setAttr("%s.contVis" % self.scaleGrp, channelBox=True)
        cmds.setAttr("%s.jointVis" % self.scaleGrp, channelBox=True)
        cmds.setAttr("%s.rigVis" % self.scaleGrp, channelBox=True)

        self.limbGrp = cmds.group(name=naming.parse([self.module_name], suffix="grp"), empty=True)
        cmds.parent(self.scaleGrp, self.nonScaleGrp, self.cont_IK_OFF, self.limbGrp)

        self.scaleConstraints.append(self.scaleGrp)

        defJ_root = cmds.joint(name=naming.parse([self.module_name], suffix="jDef"))

        functions.align_to(defJ_root, self.rootInit, position=True, rotation=self.useRefOrientation)

        functions.colorize(defJ_root, self.colorCodes[0])
        self.limbPlug = defJ_root
        self.sockets.append(defJ_root)

        if self.curveAsShape:
            _controller = Controller(shape="Cube",
                                     name=naming.parse([self.module_name], suffix="cont"),
                                     scale=(1,1,1),
                                     normal=(0,0,0))
            _controller.set_side(self.side)
            cmds.parent(_controller.shapes[0], defJ_root, r=True, s=True)
            cmds.delete(_controller.name)
            cmds.setAttr("%s.drawStyle" % defJ_root, 2)
        else:
            self.deformerJoints.append(defJ_root)

        cmds.connectAttr("%s.jointVis" % self.scaleGrp, "%s.v" % defJ_root)
        cmds.connectAttr("%s.jointVis" % self.scaleGrp, "%s.v" % self.limbGrp)

class Guides(object):
    def __init__(self, side="L", suffix="root", segments=None, tMatrix=None, upVector=(0, 1, 0), mirrorVector=(1, 0, 0), lookVector=(0, 0, 1), *args, **kwargs):
        super(Guides, self).__init__()
        # fool check

        #-------Mandatory------[Start]
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
        #-------Mandatory------[End]

    def draw_joints(self):
        if self.side == "C":
            # Guide joint positions for limbs with no side orientation
            pass
        else:
            # Guide joint positions for limbs with sides
            pass

        # Define the offset vector
        self.offsetVector = om.MVector(0, 1, 0)

        # Draw the joints
        cmds.select(clear=True)
        root_jnt = cmds.joint(name=naming.parse([self.name, "root"], suffix="jInit"))

        # Update the guideJoints list
        self.guideJoints.append(root_jnt)

        # set orientation of joints

    def define_attributes(self):
        # set joint side and type attributes
        joint.set_joint_type(self.guideJoints[0], "Root")
        cmds.setAttr("{0}.radius".format(self.guideJoints[0]), 2)
        _ = [joint.set_joint_side(jnt, self.side) for jnt in self.guideJoints]

        # ----------Mandatory---------[Start]
        root_jnt = self.guideJoints[0]
        attribute.create_global_joint_attrs(root_jnt, moduleName="Connector", upAxis=self.upVector, mirrorAxis=self.mirrorVector, lookAxis=self.lookVector)
        # ----------Mandatory---------[End]

        for attr_dict in LIMB_DATA["properties"]:
            attribute.create_attribute(root_jnt, attr_dict)

    def createGuides(self):
        self.draw_joints()
        self.define_attributes()

    def convertJoints(self, joints_list):
        if len(joints_list) != 1:
            LOG.warning("Define or select a single joint for Root Guide conversion. Skipping")
            return
        self.guideJoints = joints_list
        self.define_attributes()