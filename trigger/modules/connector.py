from maya import cmds
import maya.api.OpenMaya as om

from trigger.library import functions as extra
from trigger.core import feedback
FEEDBACK = feedback.Feedback(__name__)

LIMB_DATA = {
        "members": ["Root"],
        "properties": [],
        "multi_guide": None,
        "sided": False,
    }

class Connector(object):
    def __init__(self, build_data=None, inits=None, *args, **kwargs):
        super(Connector, self).__init__()
        if build_data:
            if len(build_data.keys()) > 1:
                FEEDBACK.throw_error("Root can only have one initial joint")
                return
            self.rootInit = build_data["Root"]
        elif inits:
            if len(inits) > 1:
                cmds.error("Root can only have one initial joint")
                return
            self.rootInit = inits[0]
        else:
            FEEDBACK.throw_error("Class needs either build_data or inits to be constructed")

        # self.suffix=(extra.uniqueName("limbGrp_%s" %(suffix))).replace("limbGrp_", "")
        # self.suffix = (extra.uniqueName(suffix))
        self.suffix = (extra.uniqueName(cmds.getAttr("%s.moduleName" % self.rootInit)))


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
        This will create a 'mid node' called root. This single joint will act as a socket for other limbs to connect to.
        Args:
            inits: (dictionary or list) This is plural for naming convention only. In fact, the function accepts only one joint. If it is a dictionary, the key must be 'Root' and if it is a list it must contain only a single element
            suffix: (string) Name suffix for the nodes will be created

        Returns: None

        """
        FEEDBACK.info("Creating Root %s" %self.suffix)

        self.scaleGrp = cmds.group(name="%s_scaleGrp" % self.suffix, em=True)
        # suffix=(extra.uniqueName("limbGrp_%s" % suffix)).replace("limbGrp_", "")
        self.limbGrp = cmds.group(name=self.suffix, em=True)
        cmds.parent(self.scaleGrp, self.nonScaleGrp, self.cont_IK_OFF, self.limbGrp)

        self.scaleConstraints.append(self.scaleGrp)

        defJ_root = cmds.joint(name="jDef_%s" % self.suffix)
        extra.alignTo(defJ_root, self.rootInit, position=True, rotation=False)

        extra.colorize(defJ_root, self.colorCodes[0])
        self.limbPlug = defJ_root
        self.sockets.append(defJ_root)
        self.deformerJoints.append(defJ_root)

class Guides(object):
    def __init__(self, side="L", suffix="root", segments=None, tMatrix=None, upVector=(0, 1, 0), mirrorVector=(1, 0, 0), lookVector=(0,0,1), *args, **kwargs):
        super(Guides, self).__init__()
        # fool check

        #-------Mandatory------[Start]
        self.side = side
        self.sideMultiplier = -1 if side == "R" else 1
        self.suffix = suffix
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
        cmds.select(d=True)
        root_jnt = cmds.joint(name="root_{0}".format(self.suffix))

        # Update the guideJoints list
        self.guideJoints.append(root_jnt)

        # set orientation of joints

    def define_attributes(self):
        # set joint side and type attributes
        extra.set_joint_type(self.guideJoints[0], "Root")
        cmds.setAttr("{0}.radius".format(self.guideJoints[0]), 2)
        _ = [extra.set_joint_side(jnt, self.side) for jnt in self.guideJoints]

        # ----------Mandatory---------[Start]
        root_jnt = self.guideJoints[0]
        extra.create_global_joint_attrs(root_jnt, moduleName="Connector", upAxis=self.upVector, mirrorAxis=self.mirrorVector, lookAxis=self.lookVector)
        # ----------Mandatory---------[End]

        for attr_dict in LIMB_DATA["properties"]:
            extra.create_attribute(root_jnt, attr_dict)

    def createGuides(self):
        self.draw_joints()
        self.define_attributes()

    def convertJoints(self, joints_list):
        if len(joints_list) != 1:
            FEEDBACK.warning("Define or select a single joint for Root Guide conversion. Skipping")
            return
        self.guideJoints = joints_list
        self.define_attributes()