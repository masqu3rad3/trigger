from maya import cmds
import maya.api.OpenMaya as om

from trigger.library import functions as extra
from trigger.library import controllers as ic
from trigger.utils import parentToSurface
from trigger.core import feedback

FEEDBACK = feedback.Feedback(__name__)

LIMB_DATA = {
        "members": ["Surface"],
        "properties": [{"attr_name": "controllerSurface",
                        "nice_name": "Mesh to Stick",
                        "attr_type": "string",
                        "default_value": ""
                        },
                       {"attr_name": "stickMode",
                        "nice_name": "Stick Mode",
                        "attr_type": "enum",
                        "enum_list": "parentConstraint:pointConstraint",
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
        stickNo = cmds.getAttr("%s.stickMode" % self.rootInit)
        self.stickMode = "parentConstraint" if stickNo == 0 else "pointConstraint"

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

    def createGrp(self):
        self.scaleGrp = cmds.group(name="%s_scaleGrp" % self.suffix, em=True)
        cmds.addAttr(self.scaleGrp, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True)
        cmds.addAttr(self.scaleGrp, at="bool", ln="Joints_Visibility", sn="jointVis", defaultValue=True)
        cmds.addAttr(self.scaleGrp, at="bool", ln="Rig_Visibility", sn="rigVis", defaultValue=True)
        # make the created attributes visible in the channelbox
        cmds.setAttr("{0}.contVis".format(self.scaleGrp), cb=True)
        cmds.setAttr("{0}.jointVis".format(self.scaleGrp), cb=True)
        cmds.setAttr("{0}.rigVis".format(self.scaleGrp), cb=True)

        self.limbGrp = cmds.group(name=self.suffix, em=True)
        cmds.parent(self.scaleGrp, self.nonScaleGrp, self.cont_IK_OFF, self.limbGrp)
        self.scaleConstraints.append(self.scaleGrp)

    def createJoints(self):
        self.surface_jnt = cmds.joint(name="%s_jnt" % self.suffix)
        cmds.connectAttr("{0}.rigVis".format(self.scaleGrp), "{0}.v".format(self.surface_jnt))

        # extra.alignTo(self.surface_jnt, self.rootInit, position=True, rotation=True)
        self.limbPlug = self.surface_jnt
        self.sockets.append(self.surface_jnt)

        # Create connection groups
        self.surface_jnt_negate = extra.createUpGrp(self.surface_jnt, "negate")
        self.surface_jnt_bind = extra.createUpGrp(self.surface_jnt, "bind")

    def createControllers(self):
        icon = ic.Icon()
        self.cont, _ = icon.createIcon("Diamond", iconName="%s_cont" % self.suffix)
        self.cont_surface = extra.createUpGrp(self.cont, "surface")
        self.cont_offset = extra.createUpGrp(self.cont, "offset")

        # extra.alignTo(self.cont_offset, self.surface_jnt, position=True, rotation=True)

        extra.colorize(self.cont, self.colorCodes[0])

        cmds.connectAttr("%s.contVis" % self.scaleGrp, "%s.v" % self.cont_offset)

    def createConnections(self):
        negate_multMatrix = cmds.createNode("multMatrix", name="negate_multMatrix_%s" % self.suffix)
        negate_decompose = cmds.createNode("decomposeMatrix", name="negate_decompose_%s" % self.suffix)
        cmds.connectAttr("%s.worldInverseMatrix[0]" % self.cont_surface, "%s.matrixIn[0]" % negate_multMatrix)
        cmds.connectAttr("%s.matrixSum" % negate_multMatrix, "%s.inputMatrix" % negate_decompose)
        cmds.connectAttr("%s.outputTranslate" % negate_decompose, "%s.translate" % self.surface_jnt_negate)
        cmds.connectAttr("%s.outputRotate" % negate_decompose, "%s.rotate" % self.surface_jnt_negate)

        bind_multMatrix = cmds.createNode("multMatrix", name="bind_multMatrix_%s" % self.suffix)
        bind_decompose = cmds.createNode("decomposeMatrix", name="bind_decompose_%s" % self.suffix)
        cmds.connectAttr("%s.worldMatrix[0]" % self.cont, "%s.matrixIn[0]" % bind_multMatrix)
        cmds.connectAttr("%s.matrixSum" % bind_multMatrix, "%s.inputMatrix" % bind_decompose)
        cmds.connectAttr("%s.outputTranslate" % bind_decompose, "%s.translate" % self.surface_jnt_bind)
        cmds.connectAttr("%s.outputRotate" % bind_decompose, "%s.rotate" % self.surface_jnt_bind)

        extra.alignTo(self.cont_offset, self.rootInit, position=True, rotation=True)

        if self.controllerSurface:
            parentToSurface.parentToSurface(objects=[self.cont_surface], surface=self.controllerSurface, mode=self.stickMode)


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
        extra.set_joint_type(self.guideJoints[0], "Surface")
        cmds.setAttr("{0}.radius".format(self.guideJoints[0]), 2)
        _ = [extra.set_joint_side(jnt, self.side) for jnt in self.guideJoints]

        # ----------Mandatory---------[Start]
        root_jnt = self.guideJoints[0]
        extra.create_global_joint_attrs(root_jnt, moduleName="Surface", upAxis=self.upVector, mirrorAxis=self.mirrorVector, lookAxis=self.lookVector)
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