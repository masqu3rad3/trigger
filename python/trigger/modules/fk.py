from maya import cmds
import maya.api.OpenMaya as om
from trigger.library import api
from trigger.library import functions
from trigger.library import connection
from trigger.library import naming
from trigger.library import attribute
from trigger.library import controllers as ic

from trigger.core import filelog
log = filelog.Filelog(logname=__name__, filename="trigger_log")

LIMB_DATA = {
    "members": ["FkRoot", "Fk"],
    "properties": [{"attr_name": "localJoints",
                    "nice_name": "Local_Joints",
                    "attr_type": "bool",
                    "default_value": False}],
    "multi_guide": "Fk",
    "sided": True,
}

log.warning("FK module is deprecated. Use fkik module instead")

class Fk(object):
    def __init__(self, build_data=None, inits=None, *args, **kwargs):
        super(Fk, self).__init__()
        # fool proofing

        # reinitialize the initial Joints
        if build_data:
            self.fkRoot = build_data.get("FkRoot")
            self.fks = build_data.get("Fk")
            self.inits = [self.fkRoot] + self.fks
            #parse build data
            pass
        elif inits:
            if (len(inits) < 2):
                log.error("Simple FK setup needs at least 2 initial joints")
                return
            self.fkRoot = inits[0]
            self.inits = inits
        else:
            log.error("Class needs either build_data or inits to be constructed")

        # get distances

        # get positions

        # get the properties from the root
        self.useRefOrientation = cmds.getAttr("%s.useRefOri" % self.fkRoot)
        self.side = functions.get_joint_side(self.fkRoot)
        self.sideMult = -1 if self.side == "R" else 1
        self.isLocal = bool(cmds.getAttr("%s.localJoints" % self.inits[0]))

        # initialize coordinates
        self.up_axis, self.mirror_axis, self.look_axis = functions.getRigAxes(self.inits[0])

        # initialize suffix
        self.suffix = (naming.uniqueName(cmds.getAttr("%s.moduleName" % self.inits[0])))

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
        functions.alignTo(self.scaleGrp, self.inits[0], position=True, rotation=False)
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

        self.localOffGrp = cmds.group(name="%s_localOffset_grp" %self.suffix, em=True)
        self.plugBindGrp = cmds.group(name="%s_plugBind_grp" %self.suffix, em=True)
        cmds.parent(self.localOffGrp, self.plugBindGrp)
        cmds.parent(self.plugBindGrp, self.limbGrp)
        # self.jointsOffGrp = cmds.group(name="%s_jointsOff_grp" %self.suffix, em=True)
        # cmds.parent(self.jointsOffGrp, self.limbGrp)


    def createJoints(self):
        # draw Joints
        cmds.select(d=True)
        self.limbPlug = cmds.joint(name="limbPlug_%s" % self.suffix, p=api.getWorldTranslation(self.inits[0]), radius=3)

        cmds.select(d=True)
        for j in self.inits:
            jnt = cmds.joint(name="jDef_{0}_{1}".format(j, self.suffix))
            self.sockets.append(jnt)
            self.deformerJoints.append(jnt)

        if not self.useRefOrientation:
            functions.orientJoints(self.deformerJoints, worldUpAxis=(self.look_axis), upAxis=(0, 1, 0), reverseAim=self.sideMult, reverseUp=self.sideMult)
        else:
            for x in range (len(self.deformerJoints)):
                functions.alignTo(self.deformerJoints[x], self.inits[x], position=True, rotation=True)
                cmds.makeIdentity(self.deformerJoints[x], a=True)

        cmds.parent(self.deformerJoints[0], self.nonScaleGrp)

        attribute.drive_attrs("%s.jointVis" % self.scaleGrp, ["%s.v" % x for x in self.deformerJoints])
        cmds.connectAttr("%s.rigVis" % self.scaleGrp,"%s.v" % self.limbPlug)
        functions.colorize(self.deformerJoints, self.colorCodes[0], shape=False)

    def createControllers(self):
        icon_handler = ic.Icon()

        self.controllers = []
        self.cont_off_list = []

        for nmb, jnt in enumerate(self.deformerJoints[:-1]):
            scale_mult = functions.getDistance(jnt, self.deformerJoints[nmb + 1]) * 0.5
            cont, _ = icon_handler.createIcon("Cube", iconName="%s%i_cont" % (self.suffix, nmb), scale=(scale_mult, scale_mult, scale_mult))

            cmds.xform(cont, piv=(self.sideMult * (-scale_mult), 0, 0))
            functions.alignToAlter(cont, jnt, 2)
            # functions.alignTo(cont, jnt, position=True, rotation=True)

            cont_OFF = functions.createUpGrp(cont, "OFF", freezeTransform=True)
            cont_ORE = functions.createUpGrp(cont, "ORE")
            cmds.makeIdentity(cont, a=True)

            self.controllers.append(cont)
            self.cont_off_list.append(cont_OFF)

            if nmb is not 0:
                cmds.parent(self.cont_off_list[nmb], self.controllers[nmb - 1])
            # else:
                # cmds.parent(self.cont_off_list[nmb], self.scaleGrp)
        cmds.parent(self.cont_off_list[0], self.localOffGrp)

        attribute.drive_attrs("%s.contVis" % self.scaleGrp, ["%s.v" % x for x in self.cont_off_list])
        functions.colorize(self.controllers, self.colorCodes[0])

        pass

    def createRoots(self):
        pass

    def createIKsetup(self):
        pass

    def createFKsetup(self):


        for cont, jnt in zip(self.controllers, self.deformerJoints[:-1]):
            connection.matrixConstraint(cont, jnt, source_parent_cutoff=self.localOffGrp)
            # disconnect inverse scale chain to inherit the scale from the controllers properly
            attribute.disconnect_attr(node=jnt, attr="inverseScale")


        # functions.alignToAlter(self.deformerJoints[-1], self.inits[-1])
        #
        # cmds.connectAttr("%s.worldInverseMatrix[0]" %self.localOffGrp, "%s.offsetParentMatrix" %self.jointsOffGrp)
        #
        if self.isLocal:
            connection.matrixConstraint(self.limbPlug, self.plugBindGrp)
        else:
            connection.matrixConstraint(self.limbPlug, self.cont_off_list[0])
        #     cmds.connectAttr("%s.s" %self.scaleGrp, "%s.s" %self.cont_off_list[0], force=True)

        # cmds.connectAttr("%s.s" %self.scaleGrp, "%s.s" %self.limbPlug)
        # #
        # cmds.connectAttr("%s.worldMatrix[0]" %self.limbPlug, "%s.offsetParentMatrix" %self.cont_off_list[0])
        # connection.matrixConstraint(self.limbPlug, self.cont_off_list[0])
        #
        # cmds.connectAttr("%s.s" %self.scaleGrp, "%s.s" %self.localOffGrp)
        # cmds.connectAttr("%s.s" %self.scaleGrp, "%s.s" %self.jointsOffGrp)

        pass

    # def createFKsetup(self):
    #     # # unparent and move the deformation joints to world 0
    #     cmds.parent(self.deformerJoints[:-1], world=True)
    #     # # cmds.parent(self.deformerJoints, self.scaleGrp)
    #     for jnt in self.deformerJoints[:-1]:
    #         cmds.setAttr("%s.t" %jnt, 0,0,0)
    #         cmds.setAttr("%s.r" %jnt, 0,0,0)
    #         cmds.setAttr("%s.jointOrient" %jnt, 0,0,0)
    #         cmds.parent(jnt, self.jointsOffGrp)
    #
    #     for cont, jnt in zip(self.cont_list, self.deformerJoints[:-1]):
    #         cmds.connectAttr("%s.worldMatrix[0]" %cont, "%s.offsetParentMatrix" %jnt)
    #
    #     functions.alignToAlter(self.deformerJoints[-1], self.inits[-1])
    #
    #     cmds.connectAttr("%s.worldInverseMatrix[0]" %self.localOffGrp, "%s.offsetParentMatrix" %self.jointsOffGrp)
    #
    #     if self.isLocal:
    #         connection.matrixConstraint(self.limbPlug, self.localOffGrp)
    #     else:
    #         connection.matrixConstraint(self.limbPlug, self.cont_off_list[0], ss=False)
    #         cmds.connectAttr("%s.s" %self.scaleGrp, "%s.s" %self.cont_off_list[0], force=True)
    #
    #     # cmds.connectAttr("%s.worldMatrix[0]" %self.limbPlug, "%s.offsetParentMatrix" %self.cont_off_list[0])
    #     # connection.matrixConstraint(self.limbPlug, self.cont_off_list[0])
    #
    #     # cmds.connectAttr("%s.s" %self.scaleGrp, "%s.s" %self.localOffGrp)
    #     # cmds.connectAttr("%s.s" %self.scaleGrp, "%s.s" %self.jointsOffGrp)
    #
    #     pass

    def ikfkSwitching(self):
        pass

    def createRibbons(self):
        pass

    def createTwistSplines(self):
        pass

    def createAngleExtractors(self):
        pass

    def roundUp(self):
        # cmds.parentConstraint(self.limbPlug, self.scaleGrp, mo=False)
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

class Guides(object):
    def __init__(self, side="L", suffix="fk", segments=None, tMatrix=None, upVector=(0, 1, 0), mirrorVector=(1, 0, 0), lookVector=(0,0,1), *args, **kwargs):
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
        # fool check
        if not self.segments or self.segments < 1:
            log.warning("minimum segments required for the simple tail is two. current: %s" % self.segments)
            return

        # rPointTail = om.MVector(0, 0, 0) * self.tMatrix
        if self.side == "C":
            # Guide joint positions for limbs with no side orientation
            rPointTail = om.MVector(0, 0, -1) * self.tMatrix
            nPointTail = om.MVector(0, 0, -11) * self.tMatrix
        else:
            # Guide joint positions for limbs with sides
            rPointTail = om.MVector(1 * self.sideMultiplier, 0, 0) * self.tMatrix
            nPointTail = om.MVector(11 * self.sideMultiplier, 0, 0) * self.tMatrix
            pass

        # Define the offset vector
        self.offsetVector = (nPointTail - rPointTail).normal()
        seperation_value = (nPointTail - rPointTail) / ((self.segments + 1) - 1)

        # Draw the joints
        for seg in range(self.segments + 1):
            jnt = cmds.joint(p=(rPointTail + (seperation_value * seg)), name="jInit_fk_%s_%i" %(self.suffix, seg))

            functions.set_joint_side(jnt, self.side)
            # Update the guideJoints list
            self.guideJoints.append(jnt)

        # set orientation of joints
        functions.orientJoints(self.guideJoints, worldUpAxis=self.lookVector, upAxis=(0, 1, 0), reverseAim=self.sideMultiplier, reverseUp=self.sideMultiplier)

    def define_attributes(self):
        # set joint side and type attributes
        functions.set_joint_type(self.guideJoints[0], "FkRoot")
        _ = [functions.set_joint_type(jnt, "Fk") for jnt in self.guideJoints[1:]]
        _ = [functions.set_joint_side(jnt, self.side) for jnt in self.guideJoints]

        # ----------Mandatory---------[Start]
        root_jnt = self.guideJoints[0]
        attribute.create_global_joint_attrs(root_jnt, moduleName="%s_fk" % self.side, upAxis=self.upVector, mirrorAxis=self.mirrorVector, lookAxis=self.lookVector)
        # ----------Mandatory---------[End]

        for attr_dict in LIMB_DATA["properties"]:
            attribute.create_attribute(root_jnt, attr_dict)

    def createGuides(self):
        self.draw_joints()
        self.define_attributes()

    def convertJoints(self, joints_list):
        if len(joints_list) < 2:
            log.warning("Define or select at least 2 joints for FK Guide conversion. Skipping")
            return
        self.guideJoints = joints_list
        self.define_attributes()