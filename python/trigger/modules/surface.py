from maya import cmds
import maya.api.OpenMaya as om

from trigger.library import functions
from trigger.library import naming
from trigger.library import attribute
from trigger.library import connection
from trigger.library import controllers as ic
from trigger.utils import parentToSurface
from trigger.core import logger

FEEDBACK = logger.Logger(__name__)

LIMB_DATA = {
        "members": ["Surface"],
        "properties": [{"attr_name": "controllerSurface",
                        "nice_name": "Mesh to Stick",
                        "attr_type": "string",
                        "default_value": ""
                        },
                       {"attr_name": "rotateObject",
                        "nice_name": "Rotation Parent",
                        "attr_type": "string",
                        "default_value": ""
                        },
                       {"attr_name": "limbPlugLocation",
                        "nice_name": "Module Plug Location",
                        "attr_type": "enum",
                        "enum_list": "On Surface Controller:On Local Joint",
                        "default_value": 0,
                        },
                       ],
        "multi_guide": None,
        "sided": True,
    }

class Surface(object):
    def __init__(self, build_data=None, inits=None, *args, **kwargs):
        super(Surface, self).__init__()
        if build_data:
            if len(build_data.keys()) > 1:
                FEEDBACK.throw_error("Surface Module can only have one initial joint")
                return
            self.rootInit = build_data["Surface"]
        elif inits:
            if len(inits) > 1:
                cmds.error("Surface Module can only have one initial joint")
                return
            self.rootInit = inits[0]
        else:
            FEEDBACK.throw_error("Class needs either build_data or inits to be constructed")

        # get properties
        self.controllerSurface = cmds.getAttr("%s.controllerSurface" % self.rootInit)
        self.rotateObject = cmds.getAttr("%s.rotateObject" % self.rootInit)
        self.isPlugOnLocal = cmds.getAttr("%s.limbPlugLocation" % self.rootInit)

        self.suffix = (naming.uniqueName(cmds.getAttr("%s.moduleName" % self.rootInit)))


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

    def createGrp(self):
        self.controllerGrp = cmds.group(name="%s_contGrp" %self.suffix, em=True)
        self.scaleGrp = cmds.group(name="%s_scaleGrp" % self.suffix, em=True)
        functions.alignTo(self.scaleGrp, self.rootInit, 0)
        self.nonScaleGrp = cmds.group(name="%s_nonScaleGrp" % self.suffix, em=True)
        cmds.addAttr(self.scaleGrp, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True)
        cmds.addAttr(self.scaleGrp, at="bool", ln="Joints_Visibility", sn="jointVis", defaultValue=True)
        cmds.addAttr(self.scaleGrp, at="bool", ln="Rig_Visibility", sn="rigVis", defaultValue=True)
        # make the created attributes visible in the channelbox
        cmds.setAttr("{0}.contVis".format(self.scaleGrp), cb=True)
        cmds.setAttr("{0}.jointVis".format(self.scaleGrp), cb=True)
        cmds.setAttr("{0}.rigVis".format(self.scaleGrp), cb=True)

        self.limbGrp = cmds.group(name=self.suffix, em=True)
        cmds.parent(self.scaleGrp, self.nonScaleGrp,  self.controllerGrp, self.limbGrp)
        self.scaleConstraints.append(self.scaleGrp)

    def createJoints(self):
        cmds.select(d=True)
        self.surface_jnt = cmds.joint(name="%s_jnt" % self.suffix)
        cmds.connectAttr("{0}.rigVis".format(self.scaleGrp), "{0}.v".format(self.surface_jnt))

        # extra.alignTo(self.surface_jnt, self.rootInit, position=True, rotation=True)
        if self.isPlugOnLocal:
            self.limbPlug = self.surface_jnt
        else:
            self.limbPlug = cmds.joint(name="limbPlug_%s" % self.suffix, radius=2)
            cmds.parent(self.limbPlug, self.scaleGrp)

        self.sockets.append(self.limbPlug)

        # Create connection groups
        self.surface_jnt_offset = functions.createUpGrp(self.surface_jnt, "offset")
        self.surface_jnt_bind = functions.createUpGrp(self.surface_jnt, "bind")

        functions.alignTo(self.surface_jnt_offset, self.rootInit, position=True, rotation=True)

        cmds.parent(self.surface_jnt_offset, self.nonScaleGrp)

    def createControllers(self):
        icon = ic.Icon()
        self.cont, _ = icon.createIcon("Diamond", iconName="%s_cont" % self.suffix)
        self.cont_offset = functions.createUpGrp(self.cont, "offset")
        self.cont_bind = functions.createUpGrp(self.cont, "bind")
        self.cont_negate = functions.createUpGrp(self.cont, "negate")

        functions.alignTo(self.cont_offset, self.rootInit, position=True, rotation=True)
        functions.colorize(self.cont, self.colorCodes[0])

        cmds.connectAttr("%s.contVis" % self.scaleGrp, "%s.v" % self.cont_offset)
        cmds.parent(self.cont_offset, self.controllerGrp)

    def createConnections(self):


        if self.controllerSurface:
            follicle = parentToSurface.parentToSurface([self.cont_bind], surface=self.controllerSurface, mode="none")[0]
            # constrain controller translate to the follicle
            connection.matrixConstraint(follicle, self.cont_bind, mo=True, sr="xyz", ss="xyz")
            cmds.parent(follicle, self.nonScaleGrp)
        if self.rotateObject:
            connection.matrixConstraint(self.rotateObject, self.cont_bind, mo=True, st="xyz", ss="xyz")


        negate_multMatrix = cmds.createNode("multMatrix", name="negate_multMatrix_%s" % self.suffix)
        negate_decompose = cmds.createNode("decomposeMatrix", name="negate_decompose_%s" % self.suffix)
        cmds.connectAttr("%s.inverseMatrix" % self.cont, "%s.matrixIn[0]" % negate_multMatrix)
        cmds.connectAttr("%s.matrixSum" % negate_multMatrix, "%s.inputMatrix" % negate_decompose)
        cmds.connectAttr("%s.outputTranslate" % negate_decompose, "%s.translate" % self.cont_negate)
        cmds.connectAttr("%s.outputRotate" % negate_decompose, "%s.rotate" % self.cont_negate)
        cmds.connectAttr("%s.outputScale" % negate_decompose, "%s.scale" % self.cont_negate)

        if self.isPlugOnLocal:
            pass # nothing to connect because plug is local joint itself
        else:
            cmds.parentConstraint(self.cont, self.limbPlug, mo=False)

        # Direct connection between controller and joint
        for attr in "trs":
            for axis in "xyz":
                cmds.connectAttr("%s.%s%s" % (self.cont, attr, axis), "%s.%s%s" % (self.surface_jnt_bind, attr, axis))

    def createLimb(self):
        """


        """
        self.createGrp()
        self.createJoints()
        self.createControllers()
        self.createConnections()

class Guides(object):
    def __init__(self, side="L", suffix="surface", segments=None, tMatrix=None, upVector=(0, 1, 0), mirrorVector=(1, 0, 0), lookVector=(0,0,1), *args, **kwargs):
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
            position = om.MVector(0, 0, 0)
            pass
        else:
            # Guide joint positions for limbs with sides
            position = om.MVector(2 * self.sideMultiplier, 0, 0) * self.tMatrix
            pass

        # Define the offset vector
        self.offsetVector = om.MVector(0, 1, 0)

        # Draw the joints
        cmds.select(d=True)
        root_jnt = cmds.joint(name="surface_{0}".format(self.suffix), p=position)

        # Update the guideJoints list
        self.guideJoints.append(root_jnt)

        # set orientation of joints

    def define_attributes(self):
        # set joint side and type attributes
        functions.set_joint_type(self.guideJoints[0], "Surface")
        cmds.setAttr("{0}.radius".format(self.guideJoints[0]), 2)
        _ = [functions.set_joint_side(jnt, self.side) for jnt in self.guideJoints]

        # ----------Mandatory---------[Start]
        root_jnt = self.guideJoints[0]
        attribute.create_global_joint_attrs(root_jnt, moduleName="Surface", upAxis=self.upVector, mirrorAxis=self.mirrorVector, lookAxis=self.lookVector)
        # ----------Mandatory---------[End]

        for attr_dict in LIMB_DATA["properties"]:
            attribute.create_attribute(root_jnt, attr_dict)

    def createGuides(self):
        self.draw_joints()
        self.define_attributes()

    def convertJoints(self, joints_list):
        if len(joints_list) != 1:
            FEEDBACK.warning("Define or select a single joint for Root Guide conversion. Skipping")
            return
        self.guideJoints = joints_list
        self.define_attributes()