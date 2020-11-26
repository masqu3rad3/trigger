from maya import cmds
import maya.api.OpenMaya as om

from trigger.library import functions
from trigger.library import attribute
from trigger.library import api
from trigger.library import controllers as ic
from trigger.core import logger
FEEDBACK = logger.Logger(__name__)

LIMB_DATA = {
        "members": ["FingerRoot", "Finger"],
        "properties": [{"attr_name": "fingerType",
                        "nice_name": "Finger_Type",
                        "attr_type": "enum",
                        "enum_list": "Extra:Thumb:Index:Middle:Ring:Pinky:Toe",
                        "default_value": 0,
                        },
                       {"attr_name": "handController",
                        "nice_name": "Hand_Controller",
                        "attr_type": "string",
                        "default_value": "",
                        },
                       ],
        "multi_guide": "Finger",
        "sided": True,
    }


class Finger(object):
    def __init__(self, build_data=None, inits=None, *args, **kwargs):
        super(Finger, self).__init__()
        if build_data:
            self.fingerRoot = build_data.get("FingerRoot")
            self.fingers = (build_data.get("Finger"))
            self.inits = [self.fingerRoot] + (self.fingers)
        elif inits:
            # fool proofing
            if (len(inits) < 2):
                FEEDBACK.throw_error("Insufficient Finger Initialization Joints")
                return
            self.inits = inits
        else:
            FEEDBACK.throw_error("Class needs either build_data or arminits to be constructed")

        hand_controller = cmds.getAttr("%s.handController" % self.inits[0])
        if hand_controller:
            if cmds.objExists(hand_controller):
                self.handController = hand_controller
            else:
                FEEDBACK.warning("Hand Control object %s is not exist. Skipping hand controller" % hand_controller)
                self.handController = None
        else:
            self.handController = None



        # initialize coordinates
        self.up_axis, self.mirror_axis, self.look_axis = functions.getRigAxes(self.inits[0])

        # get the properties from the root
        self.useRefOrientation = cmds.getAttr("%s.useRefOri" % self.inits[0])
        self.fingerType = cmds.getAttr("%s.fingerType" % self.fingerRoot, asString=True)
        self.isThumb = self.fingerType == "Thumb"
        self.side = functions.get_joint_side(self.inits[0])
        self.sideMult = -1 if self.side == "R" else 1

        # initialize suffix
        # self.suffix = "%s_%s" %(suffix, cmds.getAttr("%s.fingerType" % self.fingerRoot, asString=True))
        # self.suffix = (extra.uniqueName("limbGrp_%s_%s" % (self.fingerType, suffix))).replace("limbGrp_", "")
        # self.suffix = (extra.uniqueName("%s_%s" % (suffix, self.fingerType)))
        self.suffix = (functions.uniqueName("%s_%s" % (cmds.getAttr("%s.moduleName" % self.fingerRoot), self.fingerType)))


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
        self.limbGrp = cmds.group(name=self.suffix, em=True)
        self.scaleGrp = cmds.group(name="%s_scaleGrp" % self.suffix, em=True)
        # extra.alignTo(self.scaleGrp, self.fingerRoot, 0)
        functions.alignTo(self.scaleGrp, self.fingerRoot, position=True)
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

        ## Create LimbPlug

        cmds.select(d=True)

        self.limbPlug = cmds.joint(name="limbPlug_%s" % self.suffix, p=api.getWorldTranslation(self.inits[0]), radius=2)

        for guide in self.inits:
            jnt = cmds.joint(name="jDef_{0}_{1}".format(self.suffix, self.inits.index(guide)), radius=1.0)
            functions.alignTo(jnt, guide, position=True, rotation=True)
            if guide == self.inits[-1]: # if it is the last joint dont add it to the deformers
                jnt = cmds.rename(jnt, (jnt.replace("jDef", "jnt")))
            self.sockets.append(jnt)
            self.deformerJoints.append(jnt)

        functions.orientJoints(self.deformerJoints, worldUpAxis=self.up_axis, upAxis=(0, -1, 0), reverseAim=self.sideMult,
                               reverseUp=self.sideMult)

        if not self.useRefOrientation:
            functions.orientJoints(self.deformerJoints, worldUpAxis=self.up_axis, upAxis=(0, -1, 0),
                                   reverseAim=self.sideMult, reverseUp=self.sideMult)
        else:
            for x in range (len(self.deformerJoints)):
                functions.alignTo(self.deformerJoints[x], self.inits[x], position=True, rotation=True)
                cmds.makeIdentity(self.deformerJoints[x], a=True)


        cmds.parentConstraint(self.limbPlug, self.scaleGrp)
        # map(lambda x: cmds.connectAttr("{0}.jointVis".format(self.scaleGrp), "{0}.v".format(x)), self.deformerJoints)
        attribute.drive_attrs("%s.jointVis" % self.scaleGrp, ["%s.v" % x for x in self.deformerJoints])

        functions.colorize(self.deformerJoints, self.colorCodes[0], shape=False)

    def createControllers(self):
        icon = ic.Icon()

        ## Create Controllers

        self.conts = []
        self.conts_OFF = []
        conts_ORE = []
        contList = []
        self.contConList = []


        for index in range(0, len(self.deformerJoints)-1):
            contScl = (cmds.getAttr("%s.tx" % self.deformerJoints[1]) / 2)
            contName = ("{0}_{1}_cont".format(self.suffix, index))
            cont, dmp = icon.createIcon("Circle", iconName=contName,scale=(contScl,contScl,contScl), normal=(1,0,0))

            functions.alignToAlter(cont, self.deformerJoints[index], mode=2)

            cont_OFF=functions.createUpGrp(cont, "OFF")
            self.conts_OFF.append([cont_OFF])
            cont_ORE = functions.createUpGrp(cont, "ORE")
            cont_con = functions.createUpGrp(cont, "con")

            if index>0:
                cmds.parent(cont_OFF, self.conts[len(self.conts)-1])
                # pm.makeIdentity(cont, a=True)
            self.conts.append(cont)
            contList.append(cont)
            self.contConList.append(cont_con)

            cmds.parentConstraint(cont, self.deformerJoints[index], mo=True)

        cmds.parent(self.deformerJoints[0], self.scaleGrp)
        cmds.parent(self.conts_OFF[0], self.scaleGrp)

        # map(lambda x: cmds.connectAttr("%s.contVis" % self.scaleGrp, "%s.v" % x[0]), self.conts_OFF)
        attribute.drive_attrs("%s.contVis" % self.scaleGrp, ["%s.v" % x[0] for x in self.conts_OFF])

        functions.colorize(contList, self.colorCodes[0])

    def createFKsetup(self):
        ## Controller Attributtes
        ## If there is no parent controller defined, create one. Everyone needs a parent

        if not self.handController:
            self.handController=self.scaleGrp
        # Spread

        spreadAttr = "{0}_{1}".format(self.suffix, "Spread")
        cmds.addAttr(self.handController, shortName=spreadAttr, defaultValue=0.0, at="float", k=True)
        sprMult = cmds.createNode("multiplyDivide", name="sprMult_{0}_{1}".format(self.side, self.suffix))
        cmds.setAttr("%s.input1Y" % sprMult, 0.4)
        cmds.connectAttr("%s.%s" % (self.handController, spreadAttr), "%s.input2Y" % sprMult)
        cmds.connectAttr("%s.outputY" % sprMult, "%s.rotateY" % self.contConList[0])
        cmds.connectAttr("%s.%s" % (self.handController, spreadAttr), "%s.rotateY" % self.contConList[1])

        # Bend
        # add bend attributes for each joint (except the end joint)
        for f in range (0, (len(self.inits)-1)):
            if f == 0 and self.isThumb == True:
                bendAttr="{0}{1}".format(self.suffix, "UpDown")
            else:
                bendAttr = "{0}{1}{2}".format(self.suffix, "Bend", f)

            cmds.addAttr(self.handController, shortName=bendAttr, defaultValue=0.0, at="float", k=True)
            cmds.connectAttr("{0}.{1}".format(self.handController, bendAttr), "%s.rotateZ" % self.contConList[f])

    def roundUp(self):
        cmds.setAttr("%s.rigVis" % self.scaleGrp, 0)

        self.scaleConstraints.append(self.scaleGrp)
        # lock and hide

    def createLimb(self):
        self.createGrp()
        self.createJoints()
        self.createControllers()
        self.createFKsetup()
        self.roundUp()

    def createFinger(self, inits, suffix="", side="L", handController=None, thumb=False, mirrorAxis="X"):

        if not isinstance(inits, list):
            fingerRoot = inits.get("FingerRoot")
            fingers = (inits.get("Finger"))
            inits = [fingerRoot] + (fingers)

            fingerType = cmds.getAttr("%s.fingerType" % fingerRoot, asString=True)
            thumb = fingerType == "Thumb"
            suffix = "%s_%s" %(suffix, cmds.getAttr("%s.fingerType" % fingerRoot, asString=True))

        suffix=(functions.uniqueName("limbGrp_%s" % suffix)).replace("limbGrp_", "")
        self.limbGrp = cmds.group(name="limbGrp_%s" % suffix, em=True)

        if (len(inits) < 2):
            cmds.error("Insufficient Finger Initialization Joints")
            return

        self.scaleGrp = cmds.group(name="scaleGrp_%s" % suffix, em=True)
        self.scaleConstraints.append(self.scaleGrp)

        ## Create LimbPlug
        cmds.select(d=True)
        self.limbPlug = cmds.joint(name="limbPlug_%s" % suffix, p=inits[0].getTranslation(space="world"), radius=2)
        cmds.parentConstraint(self.limbPlug, self.scaleGrp)

        cmds.select(d=True)

        for guide in inits:
            jnt = cmds.joint(name="jDef_{0}_{1}".format(suffix, inits.index(guide)), radius=1.0)
            functions.alignTo(jnt, guide, position=True, rotation=True)

            if guide == inits[-1]: # if it is the last joint dont add it to the deformers

                replacedName = (jnt.replace("jDef", "j"))
                cmds.rename(jnt, replacedName)
            self.sockets.append(jnt)
            self.deformerJoints.append(jnt)

        ## Create Controllers

        self.conts = []
        conts_OFF = []
        conts_ORE = []
        contList = []
        contConList = []

        icon = ic.Icon()

        for i in range(0, len(self.deformerJoints)-1):
            contScl = (cmds.getAttr("%s.tx" % self.deformerJoints[1]) / 2)
            contName = ("cont_{0}_{1}".format(suffix, i))

            cont, _ = icon.createIcon("Circle", iconName=contName,scale=(contScl,contScl,contScl), normal=(1,0,0))

            cont_OFF = functions.createUpGrp(cont, "OFF", freezeTransform=False)
            conts_OFF.append([cont_OFF])
            cont_ORE = functions.createUpGrp(cont, "ORE", freezeTransform=False)
            cont_con = functions.createUpGrp(cont, "con", freezeTransform=False)

            if side == "R":
                cmds.setAttr("%s.rotate%s" %(cont_ORE, mirrorAxis), -180)

            functions.alignTo(cont_OFF, self.deformerJoints[i], position=True, rotation=True)

            if i > 0:
                cmds.parent(cont_OFF, self.conts[len(self.conts)-1])
                cmds.makeIdentity(cont, a=True)
            self.conts.append(cont)
            contList.append(cont)
            contConList.append(cont_con)

            cmds.parentConstraint(cont, self.deformerJoints[i], mo=True)

        cmds.parent(self.deformerJoints[0], self.scaleGrp)
        cmds.parent(conts_OFF[0], self.scaleGrp)

        ## Controller Attributtes
        ## If there is no parent controller defined, create one. Everyone needs a parent

        if not handController:
            handController=self.scaleGrp
        # Spread

        spreadAttr = "{0}_{1}".format(suffix, "Spread")
        cmds.addAttr(handController, shortName=spreadAttr, defaultValue=0.0, at="float", k=True)
        sprMult = cmds.createNode("multiplyDivide", name="sprMult_{0}_{1}".format(side, suffix))
        cmds.setAttr("%s.input1Y" % sprMult, 0.4)
        cmds.connectAttr("%s.%s" % (handController, spreadAttr), "%s.input2Y" % sprMult)

        cmds.connectAttr("%s.outputY" % sprMult, "%s.rotateY" % contConList[0])
        cmds.connectAttr("%s.%s" % (handController, spreadAttr), "%s.rotateY" % contConList[1])

        # Bend
        # add bend attributes for each joint (except the end joint)
        for f in range (0, (len(inits)-1)):
            if f == 0 and thumb:
                bendAttr="{0}{1}".format(suffix, "UpDown")
            else:
                bendAttr = "{0}{1}{2}".format(suffix, "Bend", f)

            cmds.addAttr(handController, shortName=bendAttr, defaultValue=0.0, at="float", k=True)
            cmds.connectAttr("{0}.{1}".format(handController, bendAttr), "%s.rotateZ" % contConList[f])

        cmds.parent(self.scaleGrp, self.nonScaleGrp, self.cont_IK_OFF, self.limbGrp)
        functions.colorize(contList, self.colorCodes[0])
        functions.colorize(self.deformerJoints, self.colorCodes[0], shape=False)
        cmds.parentConstraint(self.limbPlug, conts_OFF[0], mo=True)

class Guides(object):
    def __init__(self, side="L", suffix="finger", segments=None, tMatrix=None, upVector=(0, 1, 0), mirrorVector=(1, 0, 0), lookVector=(0,0,1), *args, **kwargs):
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
        if self.segments < 2:
            FEEDBACK.warning("minimum segments for the fingers are two. current: %s" % self.segments)
            return
        rPointFinger = om.MVector(0, 0, 0) * self.tMatrix
        nPointFinger = om.MVector(5*self.sideMultiplier, 0, 0) * self.tMatrix
        addFinger = (nPointFinger - rPointFinger) / ((self.segments + 1) - 1)

        if self.side == "C":
            # Guide joint positions for limbs with no side orientation
            pass
        else:
            # Guide joint positions for limbs with sides
            pass

        # Define the offset vector
        self.offsetVector = (nPointFinger-rPointFinger).normal()

        # Draw the joints
        for seg in range(self.segments + 1):
            finger_jnt = cmds.joint(p=(rPointFinger + (addFinger * seg)), name="jInit_finger_%s_%i" %(self.suffix, seg))
            # Update the guideJoints list
            cmds.setAttr("%s.radius" % finger_jnt, 0.5)
            self.guideJoints.append(finger_jnt)

        # set orientation of joints
        functions.orientJoints(self.guideJoints, worldUpAxis=self.upVector, upAxis=(0, -1, 0), reverseAim=self.sideMultiplier,
                               reverseUp=self.sideMultiplier)

    def define_attributes(self):
        # set joint side and type attributes
        _ = [functions.set_joint_side(jnt, self.side) for jnt in self.guideJoints]
        functions.set_joint_type(self.guideJoints[0], "FingerRoot")
        _ = [functions.set_joint_type(jnt, "Finger") for jnt in self.guideJoints[1:]]
        cmds.setAttr("%s.radius" % self.guideJoints[0], 1)

        # ----------Mandatory---------[Start]
        root_jnt = self.guideJoints[0]
        attribute.create_global_joint_attrs(root_jnt, moduleName="%s_Finger" % self.side, upAxis=self.upVector, mirrorAxis=self.mirrorVector, lookAxis=self.lookVector)
        # ----------Mandatory---------[End]

        for attr_dict in LIMB_DATA["properties"]:
            attribute.create_attribute(root_jnt, attr_dict)

    def createGuides(self):
        self.draw_joints()
        self.define_attributes()

    def convertJoints(self, joints_list):
        if len(joints_list) < 2:
            FEEDBACK.warning("Define or select at least 2 joints for Finger Guide conversion. Skipping")
            return
        self.guideJoints = joints_list
        self.define_attributes()