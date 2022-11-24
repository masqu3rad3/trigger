from maya import cmds
import maya.api.OpenMaya as om

from trigger.library import functions, joint
from trigger.library import naming
from trigger.library import attribute
from trigger.library import api
from trigger.library import controllers as ic
from trigger.core import filelog

log = filelog.Filelog(logname=__name__, filename="trigger_log")

LIMB_DATA = {
        "members": ["TailRoot", "Tail"],
        "properties": [],
        "multi_guide": "Tail",
        "sided": True,
    }

class Tail(object):

    def __init__(self, build_data=None, inits=None, *args, **kwargs):
        super(Tail, self).__init__()
        if build_data:
            self.tailRoot = build_data.get("TailRoot")
            self.tails = (build_data.get("Tail"))
            self.inits = [self.tailRoot] + (self.tails)
        elif inits:
            if (len(inits) < 2):
                log.error("Tail setup needs at least 2 initial joints")
                return
            self.inits = inits
        else:
            log.error("Class needs either build_data or inits to be constructed")

        # initialize coordinates
        self.up_axis, self.mirror_axis, self.look_axis = joint.get_rig_axes(self.inits[0])

        # get properties
        self.useRefOrientation = cmds.getAttr("%s.useRefOri" % self.inits[0])
        self.side = joint.get_joint_side(self.inits[0])
        self.sideMult = -1 if self.side == "R" else 1

        # initialize suffix
        self.suffix = (naming.unique_name(cmds.getAttr("%s.moduleName" % self.inits[0])))

        # scratch variables
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
        self.colorCodes = [6, 18]

    def createGrp(self):
        self.limbGrp = cmds.group(name=self.suffix, em=True)
        self.scaleGrp = cmds.group(name="%s_scaleGrp" % self.suffix, em=True)
        functions.align_to(self.scaleGrp, self.tailRoot, position=True, rotation=False)
        self.nonScaleGrp = cmds.group(name="%s_nonScaleGrp" % self.suffix, em=True)

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
        self.limbPlug = cmds.joint(name="limbPlug_%s" % self.suffix, p=api.get_world_translation(self.inits[0]), radius=3)

        cmds.select(d=True)
        for j in range (0,len(self.inits)):
            location = api.get_world_translation(self.inits[j])
            jnt = cmds.joint(name="jDef_{0}_{1}".format(j, self.suffix), p=location)
            self.sockets.append(jnt)
            self.deformerJoints.append(jnt)

        if not self.useRefOrientation:
            joint.orient_joints(self.deformerJoints, world_up_axis=(self.look_axis), up_axis=(0, 1, 0), reverse_aim=self.sideMult, reverse_up=self.sideMult)
        else:
            for x in range (len(self.deformerJoints)):
                functions.align_to(self.deformerJoints[x], self.inits[x], position=True, rotation=True)
                cmds.makeIdentity(self.deformerJoints[x], a=True)

        cmds.parent(self.deformerJoints[0], self.scaleGrp)

        attribute.drive_attrs("%s.jointVis" % self.scaleGrp, ["%s.v" % x for x in self.deformerJoints])

        cmds.connectAttr("%s.rigVis" % self.scaleGrp,"%s.v" % self.limbPlug)
        functions.colorize(self.deformerJoints, self.colorCodes[0], shape=False)

        pass

    def createControllers(self):

        icon = ic.Icon()

        self.controllers=[]
        self.cont_off_list=[]

        for jnt in range (len(self.deformerJoints)-1):
            scaleDis = functions.get_distance(self.deformerJoints[jnt], self.deformerJoints[jnt + 1]) / 2
            cont, _ = icon.create_icon("Cube", icon_name="%s%i_cont" % (self.suffix, jnt), scale=(scaleDis, scaleDis, scaleDis))

            cmds.xform(cont, piv=(self.sideMult * (-scaleDis), 0, 0))
            functions.align_to_alter(cont, self.deformerJoints[jnt], 2)

            cont_OFF = functions.create_offset_group(cont, "OFF")
            cont_ORE = functions.create_offset_group(cont, "ORE")

            self.controllers.append(cont)
            self.cont_off_list.append(cont_OFF)

            if jnt is not 0:
                cmds.parent(self.cont_off_list[jnt], self.controllers[jnt - 1])
            else:
                cmds.parent(self.cont_off_list[jnt], self.scaleGrp)

            cmds.makeIdentity(cont, a=True)

        attribute.drive_attrs("%s.contVis" % self.scaleGrp, ["%s.v" % x for x in self.cont_off_list])
        functions.colorize(self.controllers, self.colorCodes[0])

    def createFKsetup(self):
        for x in range (len(self.controllers)):
            cmds.parentConstraint(self.controllers[x], self.deformerJoints[x], mo=False)

            # additive scalability
            sGlobal = cmds.createNode("multiplyDivide", name="sGlobal_%s_%s" %(x, self.suffix))
            cmds.connectAttr("%s.scale" % self.limbPlug,"%s.input1" % sGlobal)
            cmds.connectAttr("%s.scale" % self.controllers[x],"%s.input2" % sGlobal)
            cmds.connectAttr("%s.output" % sGlobal,"%s.scale" % self.deformerJoints[x])

        ## last joint has no cont, use the previous one to scale that
        sGlobal = cmds.createNode("multiplyDivide", name="sGlobal_Last_%s" %(self.suffix))
        cmds.connectAttr("%s.scale" %self.limbPlug, "%s.input1" %sGlobal)
        cmds.connectAttr("%s.scale" %self.controllers[-1], "%s.input2" %sGlobal)
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

class Guides(object):
    def __init__(self, side="C", suffix="tail", segments=None, tMatrix=None, upVector=(0, 1, 0), mirrorVector=(1, 0, 0), lookVector=(0,0,1), *args, **kwargs):
        super(Guides, self).__init__()


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
        # fool check
        if not self.segments or self.segments < 1:
            log.warning("minimum segments required for the simple tail is two. current: %s" % self.segments)
            return

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

        # Draw the joints / set joint side and type attributes
        for seg in range(self.segments + 1):
            jnt = cmds.joint(p=(rPointTail + (addTail * seg)), name="jInit_tail_%s_%i" %(self.suffix, seg))

            joint.set_joint_side(jnt, self.side)
            # Update the guideJoints list
            self.guideJoints.append(jnt)

        # set orientation of joints
        joint.orient_joints(self.guideJoints, world_up_axis=self.lookVector, up_axis=(0, 1, 0), reverse_aim=self.sideMultiplier, reverse_up=self.sideMultiplier)

    def define_attributes(self):
        joint.set_joint_type(self.guideJoints[0], "TailRoot")
        _ = [joint.set_joint_type(jnt, "Tail") for jnt in self.guideJoints[1:]]
        _ = [joint.set_joint_side(jnt, self.side) for jnt in self.guideJoints]

        # ----------Mandatory---------[Start]
        root_jnt = self.guideJoints[0]
        attribute.create_global_joint_attrs(root_jnt, moduleName="%s_Tail" % self.side, upAxis=self.upVector, mirrorAxis=self.mirrorVector, lookAxis=self.lookVector)
        # ----------Mandatory---------[End]
        for attr_dict in LIMB_DATA["properties"]:
            attribute.create_attribute(root_jnt, attr_dict)

    def createGuides(self):
        self.draw_joints()
        self.define_attributes()

    def convertJoints(self, joints_list):
        if len(joints_list) < 2:
            log.warning("Define or select at least 2 joints for Tail Guide conversion. Skipping")
            return
        self.guideJoints = joints_list
        self.define_attributes()