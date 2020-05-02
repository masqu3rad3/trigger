from maya import cmds
import maya.api.OpenMaya as om
from trigger.library import functions as extra
from trigger.library import controllers as ic
from trigger.core import settings

from trigger.core import feedback
FEEDBACK = feedback.Feedback(__name__)

class Limb(settings.Settings):
    def __init__(self, build_data=None, inits=None, suffix="", side="L", *args, **kwargs):
        super(Limb, self).__init__()
        # fool proofing

        # reinitialize the initial Joints
        if build_data:
            #parse build data
            pass
        elif inits:
            # parse inits
            pass
        else:
            FEEDBACK.throw_error("Class needs either build_data or inits to be constructed")

        # get distances

        # get positions

        # initialize sides
        self.sideMult = -1 if side == "R" else 1
        self.side = side

        # initialize coordinates
        self.up_axis, self.mirror_axis, self.look_axis = extra.getRigAxes(self.inits[0])

        # initialize suffix
        self.suffix = (extra.uniqueName("limbGrp_%s" % suffix)).replace("limbGrp_", "")

        # scratch variables
        self.sockets = []
        self.limbGrp = None
        self.scaleGrp = None
        self.nonScaleGrp = None
        self.limbPlug = None
        self.scaleConstraints = []
        self.anchors = []
        self.anchorLocations = []
        self.deformerJoints = []
        self.colorCodes = [6, 18]

    def createGrp(self):
        self.limbGrp = cmds.group(name="limbGrp_%s" % self.suffix, em=True)
        self.scaleGrp = cmds.group(name="scaleGrp_%s" % self.suffix, em=True)
        extra.alignTo(self.scaleGrp, self.inits[0], 0)
        self.nonScaleGrp = cmds.group(name="NonScaleGrp_%s" % self.suffix, em=True)

        cmds.addAttr(self.scaleGrp, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True)
        cmds.addAttr(self.scaleGrp, at="bool", ln="Joints_Visibility", sn="jointVis", defaultValue=True)
        cmds.addAttr(self.scaleGrp, at="bool", ln="Rig_Visibility", sn="rigVis", defaultValue=False)
        # make the created attributes visible in the channelbox
        cmds.setAttr("%s.contVis" % self.scaleGrp, cb=True)
        cmds.setAttr("%s.jointVis" % self.scaleGrp, cb=True)
        cmds.setAttr("%s.rigVis" % self.scaleGrp, cb=True)

        cmds.parent(self.scaleGrp, self.limbGrp)
        cmds.parent(self.nonScaleGrp, self.limbGrp)

    def createJoints(self):
        # draw Joints

        # orientations
        pass

    def createControllers(self):
        pass

    def createRoots(self):
        pass

    def createIKsetup(self):
        pass

    def createFKsetup(self):
        pass

    def ikfkSwitching(self):
        pass

    def createRibbons(self):
        pass

    def createTwistSplines(self):
        pass

    def createAngleExtractors(self):
        pass

    def roundUp(self):
        cmds.parentConstraint(self.limbPlug, self.scaleGrp, mo=False)
        cmds.setAttr("%s.rigVis" % self.scaleGrp, 0)

        self.scaleConstraints.append(self.scaleGrp)
        # lock and hide

    def createLimb(self):
        self.createGrp()
        self.createJoints()
        self.createControllers()
        self.createRoots()
        self.createIKsetup()
        self.createFKsetup()
        self.ikfkSwitching()
        self.createRibbons()
        self.createTwistSplines()
        self.createAngleExtractors()
        self.roundUp()

class Guides(settings.Settings):
    def __init__(self, side="L", suffix="LIMBNAME", segments=None, tMatrix=None, lookVector=(0,0,1), *args, **kwargs):
        super(Guides, self).__init__()
        # fool check

        #-------Mandatory------[Start]
        self.side = side
        if self.side == "L":
            self.sideMultiplier = 1 # this is the multiplier value to place joints
            self.sideAttr = 1 # this is attribute value for side identification
        elif self.side == "R":
            self.sideMultiplier = -1
            self.sideAttr = 2
        else:
            self.sideMultiplier = 1
            self.sideAttr = 0
        self.segments = segments
        self.suffix = suffix
        self.tMatrix = om.MMatrix(tMatrix) if tMatrix else om.MMatrix()
        self.lookVector = lookVector
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

        # Draw the joints

        # Update the guideJoints list

        # set orientation of joints

        # set joint side and type attributes

    def define_attributes(self):
        # ----------Mandatory---------[Start]
        root_jnt = self.guideJoints[0]
        axisAttributes=["upAxis", "mirrorAxis", "lookAxis"]
        for att in axisAttributes:
            if not cmds.attributeQuery(att, node=root_jnt, exists=True):
                cmds.addAttr(root_jnt, longName=att, dt="string")

        cmds.setAttr("{0}.upAxis".format(root_jnt), self.get("upAxis"), type="string")
        cmds.setAttr("{0}.mirrorAxis".format(root_jnt), self.get("mirrorAxis"), type="string")
        cmds.setAttr("{0}.lookAxis".format(root_jnt), self.get("lookAxis"), type="string")

        if not cmds.attributeQuery("useRefOri", node=root_jnt, exists=True):
            cmds.addAttr(root_jnt, longName="useRefOri", niceName="Inherit_Orientation", at="bool", keyable=True)

        cmds.setAttr("{0}.useRefOri".format(root_jnt), True)
        # ----------Mandatory---------[End]

    def adjust_display(self):
        # ----------Mandatory---------[Start]
        # display joint orientation
        for jnt in self.guideJoints:
            cmds.setAttr("%s.displayLocalAxis" % jnt, 1)
            cmds.setAttr("%s.drawLabel" % jnt, 1)

        if self.side == "C":
            extra.colorize(self.guideJoints, self.get("majorCenterColor"), shape=False)
        if self.side == "L":
            extra.colorize(self.guideJoints, self.get("majorLeftColor"), shape=False)
        if self.side == "R":
            extra.colorize(self.guideJoints, self.get("majorRightColor"), shape=False)
        # ----------Mandatory---------[End]

    def createGuides(self):
        self.draw_joints()
        self.define_attributes()
        self.adjust_display()
