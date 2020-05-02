from maya import cmds
import maya.api.OpenMaya as om

from trigger.core import settings
from trigger.library import functions as extra
from trigger.library import controllers as ic
from trigger.core import feedback
FEEDBACK = feedback.Feedback(__name__)

class Tail(settings.Settings):

    def __init__(self, build_data=None, inits=None, suffix="", side="C", *args, **kwargs):
        super(Tail, self).__init__()
        if build_data:
            self.tailRoot = build_data.get("TailRoot")
            self.tails = (build_data.get("Tail"))
            self.inits = [self.tailRoot] + (self.tails)
        elif inits:
            if (len(inits) < 2):
                FEEDBACK.throw_error("Tail setup needs at least 2 initial joints")
                return
            self.inits = inits
        else:
            FEEDBACK.throw_error("Class needs either build_data or inits to be constructed")

        # initialize sides
        self.sideMult = -1 if side == "R" else 1
        self.side = side

        # initialize coordinates
        self.up_axis, self.mirror_axis, self.look_axis = extra.getRigAxes(self.inits[0])

        # get if orientation should be derived from the initial Joints
        try: self.useRefOrientation = cmds.getAttr("%s.useRefOri" % self.inits[0])
        except:
            cmds.warning("Cannot find Inherit Orientation Attribute on Initial Root Joint %s... Skipping inheriting." %self.inits[0])
            self.useRefOrientation = False


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
        extra.alignTo(self.scaleGrp, self.tailRoot, position=True, rotation=False)
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
        cmds.select(d=True)
        self.limbPlug = cmds.joint(name="limbPlug_%s" % self.suffix, p=extra.getWorldTranslation(self.inits[0]), radius=3)

        cmds.select(d=True)
        for j in range (0,len(self.inits)):
            location = extra.getWorldTranslation(self.inits[j])
            jnt = cmds.joint(name="jDef_{0}_{1}".format(j, self.suffix), p=location)
            self.sockets.append(jnt)
            self.deformerJoints.append(jnt)

        if not self.useRefOrientation:
            extra.orientJoints(self.deformerJoints, worldUpAxis=(self.look_axis), upAxis=(0, 1, 0), reverseAim=self.sideMult, reverseUp=self.sideMult)
        else:
            for x in range (len(self.deformerJoints)):
                extra.alignTo(self.deformerJoints[x], self.inits[x], position=True, rotation=True)
                cmds.makeIdentity(self.deformerJoints[x], a=True)

        cmds.parent(self.deformerJoints[0], self.scaleGrp)

        map(lambda x: cmds.connectAttr("%s.jointVis" % self.scaleGrp, "%s.v" % x), self.deformerJoints)

        cmds.connectAttr("%s.rigVis" % self.scaleGrp,"%s.v" % self.limbPlug)
        extra.colorize(self.deformerJoints, self.colorCodes[0], shape=False)

        pass

    def createControllers(self):

        icon = ic.Icon()

        self.contList=[]
        self.cont_off_list=[]

        for jnt in range (len(self.deformerJoints)-1):
            scaleDis = extra.getDistance(self.deformerJoints[jnt], self.deformerJoints[jnt + 1]) / 2
            cont, _ = icon.createIcon("Cube", iconName="%s%i_cont" % (self.suffix, jnt), scale=(scaleDis, scaleDis, scaleDis))

            cmds.xform(cont, piv=(self.sideMult * (-scaleDis), 0, 0))
            extra.alignToAlter(cont, self.deformerJoints[jnt], 2)

            cont_OFF = extra.createUpGrp(cont, "OFF")
            cont_ORE = extra.createUpGrp(cont, "ORE")

            self.contList.append(cont)
            self.cont_off_list.append(cont_OFF)

            if jnt is not 0:
                cmds.parent(self.cont_off_list[jnt], self.contList[jnt - 1])
            else:
                cmds.parent(self.cont_off_list[jnt], self.scaleGrp)

        map(lambda x: cmds.connectAttr("%s.contVis" % self.scaleGrp, "%s.v" % x), self.cont_off_list)
        extra.colorize(self.contList, self.colorCodes[0])

    def createFKsetup(self):
        for x in range (len(self.contList)):
            cmds.parentConstraint(self.contList[x], self.deformerJoints[x], mo=False)

            # additive scalability
            sGlobal = cmds.createNode("multiplyDivide", name="sGlobal_%s_%s" %(x, self.suffix))
            cmds.connectAttr("%s.scale" % self.limbPlug,"%s.input1" % sGlobal)
            cmds.connectAttr("%s.scale" % self.contList[x],"%s.input2" % sGlobal)
            cmds.connectAttr("%s.output" % sGlobal,"%s.scale" % self.deformerJoints[x])

        ## last joint has no cont, use the previous one to scale that
        sGlobal = cmds.createNode("multiplyDivide", name="sGlobal_Last_%s" %(self.suffix))
        cmds.connectAttr("%s.scale" %self.limbPlug, "%s.input1" %sGlobal)
        cmds.connectAttr("%s.scale" %self.contList[-1], "%s.input2" %sGlobal)
        cmds.connectAttr("%s.output" %sGlobal, "%s.scale" %self.deformerJoints[-1])

    def roundUp(self):
        cmds.parentConstraint(self.limbPlug, self.scaleGrp, mo=False)
        cmds.setAttr("%s.rigVis" % self.scaleGrp, 0)

        self.scaleConstraints.append(self.scaleGrp)
        # lock and hide

    def createLimb(self):
        self.createGrp()
        self.createJoints()
        self.createControllers()
        self.createFKsetup()
        self.roundUp()

class Guides(settings.Settings):
    def __init__(self, side="C", suffix="tail", segments=None, tMatrix=None, lookVector=(0,0,1), *args, **kwargs):
        super(Guides, self).__init__()
        # fool check
        if not segments or segments < 1:
            FEEDBACK.warning("minimum segments required for the simple tail is two. current: %s" %segments)
            return

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
        rPointTail = om.MVector(0, 14, 0) * self.tMatrix
        if self.side == "C":
            # Guide joint positions for limbs with no side orientation
            nPointTail = om.MVector(0, 8.075, -7.673) * self.tMatrix
        else:
            # Guide joint positions for limbs with sides
            nPointTail = om.MVector(7.673 * self.sideMultiplier, 8.075, 0) * self.tMatrix

        # Define the offset vector
        self.offsetVector = (nPointTail - rPointTail).normal()
        addTail = (nPointTail - rPointTail) / ((self.segments + 1) - 1)

        # Draw the joints
        for i in range(0, (self.segments + 1)):
            tail = cmds.joint(p=(rPointTail + (addTail * i)), name="jInit_tail_%s_%s" %(self.suffix, str(i)))

            # Update the guideJoints list
            self.guideJoints.append(tail)

        # set orientation of joints
        extra.orientJoints(self.guideJoints, worldUpAxis=self.lookVector, upAxis=(0, 1, 0), reverseAim=self.sideMultiplier, reverseUp=self.sideMultiplier)

        # set joint side and type attributes
        for nmb, jnt in enumerate(self.guideJoints):
            if nmb == 0:
                cmds.setAttr("%s.type" % jnt, 18)
                cmds.setAttr("%s.otherType" % jnt, "TailRoot", type="string")
                cmds.setAttr("%s.radius" % jnt, 2)
            else:
                cmds.setAttr("%s.type" % jnt, 18)
                cmds.setAttr("%s.otherType" % jnt, "Tail", type="string")
            cmds.setAttr("%s.side" % jnt, self.sideAttr)

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
