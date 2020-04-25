from maya import cmds
from trigger.library import functions as extra
from trigger.library import controllers as ic

class Fingers(object):
    # def __init__(self, inits, suffix="", side="L", parentController=None, thumb=False, mirrorAxis="X"):
    def __init__(self, inits, suffix="", side="L", parentController=None, *args, **kwargs):

        # reinitialize the initial Joints
        if not isinstance(inits, list):
            self.fingerRoot = inits.get("FingerRoot")
            self.fingers = (inits.get("Finger"))
            self.inits = [self.fingerRoot] + (self.fingers)

        # fool proofing
        if (len(inits) < 2):
            cmds.error("Insufficient Finger Initialization Joints")
            return

        # initialize sides and fingertype
        self.sideMult = -1 if side == "R" else 1
        self.side = side
        self.parentController=parentController

        self.fingerType = cmds.getAttr("%s.fingerType" % self.fingerRoot, asString=True)
        self.isThumb = self.fingerType == "Thumb"

        # initialize coordinates
        self.up_axis, self.mirror_axis, self.look_axis = extra.getRigAxes(self.inits[0])

        # get if orientation should be derived from the initial Joints
        try: self.useRefOrientation = cmds.getAttr("%s.useRefOri" % self.inits[0])
        except:
            cmds.warning("Cannot find Inherit Orientation Attribute on Initial Root Joint %s... Skipping inheriting." %self.inits[0])
            self.useRefOrientation = False

        # initialize suffix
        self.suffix = "%s_%s" %(suffix, cmds.getAttr("%s.fingerType" % self.fingerRoot, asString=True))

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
        extra.alignTo(self.scaleGrp, self.fingerRoot, 0)
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

        ## Create LimbPlug

        cmds.select(d=True)

        self.limbPlug = cmds.joint(name="limbPlug_%s" % self.suffix, p=extra.getWorldTranslation(self.inits[0]), radius=2)

        for guide in self.inits:
            jnt = cmds.joint(name="jDef_{0}_{1}".format(self.suffix, self.inits.index(guide)), radius=1.0)
            extra.alignTo(jnt, guide, position=True, rotation=True)
            if guide == self.inits[-1]: # if it is the last joint dont add it to the deformers
                jnt = cmds.rename(jnt, (jnt.replace("jDef", "jnt")))
            self.sockets.append(jnt)
            self.deformerJoints.append(jnt)

        extra.orientJoints(self.deformerJoints, worldUpAxis=self.up_axis, upAxis=(0, -1, 0), reverseAim=self.sideMult,
                           reverseUp=self.sideMult)

        if not self.useRefOrientation:
            extra.orientJoints(self.deformerJoints, worldUpAxis=self.up_axis, upAxis=(0, -1, 0),
                               reverseAim=self.sideMult, reverseUp=self.sideMult)
        else:
            for x in range (len(self.deformerJoints)):
                extra.alignTo(self.deformerJoints[x], self.inits[x], position=True, rotation=True)
                cmds.makeIdentity(self.deformerJoints[x], a=True)


        cmds.parentConstraint(self.limbPlug, self.scaleGrp)

        extra.colorize(self.deformerJoints, self.colorCodes[0], shape=False)

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

            extra.alignToAlter(cont, self.deformerJoints[index], mode=2)

            cont_OFF=extra.createUpGrp(cont,"OFF")
            self.conts_OFF.append([cont_OFF])
            cont_ORE = extra.createUpGrp(cont, "ORE")
            cont_con = extra.createUpGrp(cont, "con")

            if index>0:
                cmds.parent(cont_OFF, self.conts[len(self.conts)-1])
                # pm.makeIdentity(cont, a=True)
            self.conts.append(cont)
            contList.append(cont)
            self.contConList.append(cont_con)

            cmds.parentConstraint(cont, self.deformerJoints[index], mo=True)

        cmds.parent(self.deformerJoints[0], self.scaleGrp)
        cmds.parent(self.conts_OFF[0], self.scaleGrp)

        extra.colorize(contList, self.colorCodes[0])

    def createFKsetup(self):
        ## Controller Attributtes
        ## If there is no parent controller defined, create one. Everyone needs a parent

        if not self.parentController:
            self.parentController=self.scaleGrp
        # Spread

        spreadAttr = "{0}_{1}".format(self.suffix, "Spread")
        cmds.addAttr(self.parentController, shortName=spreadAttr , defaultValue=0.0, at="float", k=True)
        sprMult = cmds.createNode("multiplyDivide", name="sprMult_{0}_{1}".format(self.side, self.suffix))
        cmds.setAttr("%s.input1Y" % sprMult, 0.4)
        cmds.connectAttr("%s.%s" %(self.parentController,spreadAttr), "%s.input2Y" % sprMult)
        cmds.connectAttr("%s.outputY" % sprMult, "%s.rotateY" % self.contConList[0])
        cmds.connectAttr("%s.%s" % (self.parentController, spreadAttr), "%s.rotateY" % self.contConList[1])

        # Bend
        # add bend attributes for each joint (except the end joint)
        for f in range (0, (len(self.inits)-1)):
            if f == 0 and self.isThumb == True:
                bendAttr="{0}{1}".format(self.suffix, "UpDown")
            else:
                bendAttr = "{0}{1}{2}".format(self.suffix, "Bend", f)

            cmds.addAttr(self.parentController, shortName=bendAttr, defaultValue=0.0, at="float", k=True)
            cmds.connectAttr("{0}.{1}".format(self.parentController, bendAttr), "%s.rotateZ" % self.contConList[f])

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

    def createFinger(self, inits, suffix="", side="L", parentController=None, thumb=False, mirrorAxis="X"):

        if not isinstance(inits, list):
            fingerRoot = inits.get("FingerRoot")
            fingers = (inits.get("Finger"))
            inits = [fingerRoot] + (fingers)

            fingerType = cmds.getAttr("%s.fingerType" % fingerRoot, asString=True)
            thumb = fingerType == "Thumb"
            suffix = "%s_%s" %(suffix, cmds.getAttr("%s.fingerType" % fingerRoot, asString=True))

        suffix=(extra.uniqueName("limbGrp_%s" % suffix)).replace("limbGrp_", "")
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
            extra.alignTo(jnt, guide, position=True, rotation=True)

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

            cont_OFF = extra.createUpGrp(cont,"OFF", freezeTransform=False)
            conts_OFF.append([cont_OFF])
            cont_ORE = extra.createUpGrp(cont, "ORE", freezeTransform=False)
            cont_con = extra.createUpGrp(cont, "con", freezeTransform=False)

            if side == "R":
                cmds.setAttr("%s.rotate%s" %(cont_ORE, mirrorAxis), -180)

            extra.alignTo(cont_OFF, self.deformerJoints[i], position=True, rotation=True)

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

        if not parentController:
            parentController=self.scaleGrp
        # Spread

        spreadAttr = "{0}_{1}".format(suffix, "Spread")
        cmds.addAttr(parentController, shortName=spreadAttr , defaultValue=0.0, at="float", k=True)
        sprMult = cmds.createNode("multiplyDivide", name="sprMult_{0}_{1}".format(side, suffix))
        cmds.setAttr("%s.input1Y" % sprMult, 0.4)
        cmds.connectAttr("%s.%s" %(parentController,spreadAttr), "%s.input2Y" % sprMult)

        cmds.connectAttr("%s.outputY" % sprMult, "%s.rotateY" % contConList[0])
        cmds.connectAttr("%s.%s" % (parentController, spreadAttr), "%s.rotateY" % contConList[1])

        # Bend
        # add bend attributes for each joint (except the end joint)
        for f in range (0, (len(inits)-1)):
            if f == 0 and thumb:
                bendAttr="{0}{1}".format(suffix, "UpDown")
            else:
                bendAttr = "{0}{1}{2}".format(suffix, "Bend", f)

            cmds.addAttr(parentController, shortName=bendAttr, defaultValue=0.0, at="float", k=True)
            cmds.connectAttr("{0}.{1}".format(parentController, bendAttr), "%s.rotateZ" % contConList[f])

        cmds.parent(self.scaleGrp, self.nonScaleGrp, self.cont_IK_OFF, self.limbGrp)
        extra.colorize(contList, self.colorCodes[0])
        extra.colorize(self.deformerJoints, self.colorCodes[0], shape=False)
        cmds.parentConstraint(self.limbPlug, conts_OFF[0], mo=True)



