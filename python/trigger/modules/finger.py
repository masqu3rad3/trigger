from maya import cmds
import maya.api.OpenMaya as om

from trigger.library import functions, joint
from trigger.library import naming
from trigger.library import attribute
from trigger.library import api
from trigger.objects.controller import Controller
from trigger.core import filelog
log = filelog.Filelog(logname=__name__, filename="trigger_log")

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
                log.error("Insufficient Finger Initialization Joints")
                return
            self.inits = inits
        else:
            log.error("Class needs either build_data or finger inits to be constructed")

        hand_controller = cmds.getAttr("%s.handController" % self.inits[0])
        if hand_controller:
            if cmds.objExists(hand_controller):
                self.handController = hand_controller
            else:
                log.warning("Hand Control object %s is not exist. Skipping hand controller" % hand_controller)
                self.handController = None
        else:
            self.handController = None

        # initialize coordinates
        self.up_axis, self.mirror_axis, self.look_axis = joint.get_rig_axes(self.inits[0])

        # get the properties from the root
        self.useRefOrientation = cmds.getAttr("%s.useRefOri" % self.inits[0])
        self.fingerType = cmds.getAttr("%s.fingerType" % self.fingerRoot, asString=True)
        self.isThumb = self.fingerType == "Thumb"
        self.side = joint.get_joint_side(self.inits[0])
        self.sideMult = -1 if self.side == "R" else 1

        # initialize suffix
        self.suffix = (naming.unique_name("%s_%s" % (cmds.getAttr("%s.moduleName" % self.fingerRoot), self.fingerType)))

        # BASE variables
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
        functions.align_to(self.scaleGrp, self.fingerRoot, position=True)
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

        self.limbPlug = cmds.joint(name="limbPlug_%s" % self.suffix, p=api.get_world_translation(self.inits[0]), radius=2)

        for guide in self.inits:
            jnt = cmds.joint(name="jDef_{0}_{1}".format(self.suffix, self.inits.index(guide)), radius=1.0)
            functions.align_to(jnt, guide, position=True, rotation=True)
            if guide == self.inits[-1]: # if it is the last joint dont add it to the deformers
                jnt = cmds.rename(jnt, (jnt.replace("jDef", "jnt")))
            self.sockets.append(jnt)
            self.deformerJoints.append(jnt)

        joint.orient_joints(self.deformerJoints, world_up_axis=self.up_axis, up_axis=(0, -1, 0), reverse_aim=self.sideMult,
                            reverse_up=self.sideMult)

        if not self.useRefOrientation:
            joint.orient_joints(self.deformerJoints, world_up_axis=self.up_axis, up_axis=(0, -1, 0),
                                reverse_aim=self.sideMult, reverse_up=self.sideMult)
        else:
            for x in range (len(self.deformerJoints)):
                functions.align_to(self.deformerJoints[x], self.inits[x], position=True, rotation=True)
                cmds.makeIdentity(self.deformerJoints[x], a=True)


        cmds.parentConstraint(self.limbPlug, self.scaleGrp)
        attribute.drive_attrs("%s.jointVis" % self.scaleGrp, ["%s.v" % x for x in self.deformerJoints])

        functions.colorize(self.deformerJoints, self.colorCodes[0], shape=False)

    def createControllers(self):

        ## Create Controllers

        self.controllers = []
        self.conts_OFF = []
        conts_ORE = []
        contList = []
        self.contConList = []


        for index in range(0, len(self.deformerJoints)-1):
            contScl = (cmds.getAttr("%s.tx" % self.deformerJoints[1]) / 2)
            contName = ("{0}_{1}_cont".format(self.suffix, index))
            # cont, dmp = icon.create_icon("Circle", icon_name=contName, scale=(contScl, contScl, contScl), normal=(1, 0, 0))
            cont = Controller(name=contName,
                              shape="Circle",
                              scale=(contScl, contScl, contScl),
                              normal=(1, 0, 0),
                              side=self.side,
                              tier="primary"
                              )

            functions.align_to_alter(cont.name, self.deformerJoints[index], mode=2)

            cont_OFF = cont.add_offset("OFF")
            self.conts_OFF.append([cont_OFF])
            cont_ORE = cont.add_offset("ORE")
            cont_con = cont.add_offset("con")

            if index > 0:
                cmds.parent(cont_OFF, self.controllers[len(self.controllers)-1].name)
            self.controllers.append(cont)
            contList.append(cont)
            self.contConList.append(cont_con)

            cmds.parentConstraint(cont.name, self.deformerJoints[index], maintainOffset=True)

        cmds.parent(self.deformerJoints[0], self.scaleGrp)
        cmds.parent(self.conts_OFF[0], self.scaleGrp)

        attribute.drive_attrs("%s.contVis" % self.scaleGrp, ["%s.v" % x[0] for x in self.conts_OFF])

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

        for cont in self.controllers:
            cont.set_defaults()

    def createLimb(self):
        self.createGrp()
        self.createJoints()
        self.createControllers()
        self.createFKsetup()
        self.roundUp()

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
            log.warning("minimum segments for the fingers are two. current: %s" % self.segments)
            return
        rPointFinger = om.MVector(0, 0, 0) * self.tMatrix
        nPointFinger = om.MVector(5*self.sideMultiplier, 0, 0) * self.tMatrix
        addFinger = (nPointFinger - rPointFinger) / ((self.segments + 1) - 1)

        # Define the offset vector
        self.offsetVector = (nPointFinger-rPointFinger).normal()

        # Draw the joints
        for seg in range(self.segments + 1):
            finger_jnt = cmds.joint(p=(rPointFinger + (addFinger * seg)), name="jInit_finger_%s_%i" %(self.suffix, seg))
            # Update the guideJoints list
            cmds.setAttr("%s.radius" % finger_jnt, 0.5)
            self.guideJoints.append(finger_jnt)

        # set orientation of joints
        joint.orient_joints(self.guideJoints, world_up_axis=self.upVector, up_axis=(0, -1, 0), reverse_aim=self.sideMultiplier,
                            reverse_up=self.sideMultiplier)

    def define_attributes(self):
        # set joint side and type attributes
        _ = [joint.set_joint_side(jnt, self.side) for jnt in self.guideJoints]
        joint.set_joint_type(self.guideJoints[0], "FingerRoot")
        _ = [joint.set_joint_type(jnt, "Finger") for jnt in self.guideJoints[1:]]
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
            log.warning("Define or select at least 2 joints for Finger Guide conversion. Skipping")
            return
        self.guideJoints = joints_list
        self.define_attributes()