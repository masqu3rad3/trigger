import pymel.core as pm
from trigger.library import functions as extra
from trigger.library import controllers as ic

class Fingers(object):
    def __init__(self, inits, suffix="", side="L", parentController=None, thumb=False, mirrorAxis="X"):

        # reinitialize the initial Joints
        if not isinstance(inits, list):
            self.fingerRoot = inits.get("FingerRoot")
            self.fingers = (inits.get("Finger"))
            self.inits = [self.fingerRoot] + (self.fingers)

        # fool proofing
        if (len(inits) < 2):
            pm.error("Insufficient Finger Initialization Joints")
            return

        # initialize sides and fingertype
        self.sideMult = -1 if side == "R" else 1
        self.side = side
        self.parentController=parentController

        self.fingerType = pm.getAttr(self.fingerRoot.fingerType, asString=True)
        self.isThumb = self.fingerType == "Thumb"

        # initialize coordinates
        self.up_axis, self.mirror_axis, self.look_axis = extra.getRigAxes(self.inits[0])

        # get if orientation should be derived from the initial Joints
        try: self.useRefOrientation = pm.getAttr(self.inits[0].useRefOri)
        except:
            pm.warning("Cannot find Inherit Orientation Attribute on Initial Root Joint %s... Skipping inheriting." %self.inits[0])
            self.useRefOrientation = False

        # initialize suffix
        self.suffix = "%s_%s" %(suffix, pm.getAttr(self.fingerRoot.fingerType, asString=True))

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

        #
        # self.limbGrp = None
        # self.deformerJoints = []
        # self.sockets = []
        # self.conts = []
        # self.scaleGrp = None
        # self.cont_body = None
        # self.cont_hips = None
        # self.limbPlug = None
        # self.nonScaleGrp = None
        # self.cont_IK_OFF = None
        # self.scaleConstraints = []
        # self.anchors = []
        # self.anchorLocations = []
        # self.colorCodes = [6, 18]
    #
    # rootMaster = None
    # allControllers = []
    # deformerJoints = []

    def createGrp(self):
        self.limbGrp = pm.group(name="limbGrp_%s" % self.suffix, em=True)
        self.scaleGrp = pm.group(name="scaleGrp_%s" % self.suffix, em=True)
        extra.alignTo(self.scaleGrp, self.fingerRoot, 0)
        self.nonScaleGrp = pm.group(name="NonScaleGrp_%s" % self.suffix, em=True)

        pm.addAttr(self.scaleGrp, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True)
        pm.addAttr(self.scaleGrp, at="bool", ln="Joints_Visibility", sn="jointVis", defaultValue=True)
        pm.addAttr(self.scaleGrp, at="bool", ln="Rig_Visibility", sn="rigVis", defaultValue=False)
        # make the created attributes visible in the channelbox
        pm.setAttr(self.scaleGrp.contVis, cb=True)
        pm.setAttr(self.scaleGrp.jointVis, cb=True)
        pm.setAttr(self.scaleGrp.rigVis, cb=True)

        pm.parent(self.scaleGrp, self.limbGrp)
        pm.parent(self.nonScaleGrp, self.limbGrp)

        # pm.parent(self.scaleGrp, self.nonScaleGrp, self.limbGrp)

    def createJoints(self):

        ## Create LimbPlug

        pm.select(d=True)
        self.limbPlug = pm.joint(name="limbPlug_%s" % self.suffix, p=self.inits[0].getTranslation(space="world"), radius=2)

        # jointOrientValue = (-180, 0 ,0) if self.side == "R" else (0, 0, 0)

        for i in self.inits:
            j = pm.joint(name="jDef_{0}_{1}".format(self.suffix, self.inits.index(i)), radius=1.0)
            extra.alignTo(j, i, mode=2)
            # pm.setAttr(j.jointOrient, jointOrientValue)
            if i == self.inits[-1]: # if it is the last joint dont add it to the deformers
                pm.rename(j, (j.name()).replace("jDef", "j"))
            self.sockets.append(j)
            self.deformerJoints.append(j)

        extra.orientJoints(self.deformerJoints, worldUpAxis=self.up_axis, upAxis=(0, -1, 0), reverseAim=self.sideMult,
                           reverseUp=self.sideMult)

        if not self.useRefOrientation:
            extra.orientJoints(self.deformerJoints, worldUpAxis=self.up_axis, upAxis=(0, -1, 0),
                               reverseAim=self.sideMult, reverseUp=self.sideMult)
        else:
            for x in range (len(self.deformerJoints)):
                extra.alignTo(self.deformerJoints[x], self.inits[x], mode=2)
                pm.makeIdentity(self.deformerJoints[x], a=True)


        pm.parentConstraint(self.limbPlug, self.scaleGrp)

        extra.colorize(self.deformerJoints, self.colorCodes[0], shape=False)

    def createControllers(self):
        icon = ic.Icon()

        ## Create Controllers

        self.conts = []
        self.conts_OFF = []
        conts_ORE = []
        contList = []
        self.contConList = []


        for i in range(0, len(self.deformerJoints)-1):
            contScl = (pm.getAttr(self.deformerJoints[1].tx) / 2)
            contName = ("cont_{0}_{1}".format(self.suffix, i))
            cont, dmp = icon.createIcon("Circle", iconName=contName,scale=(contScl,contScl,contScl), normal=(1,0,0))

            extra.alignToAlter(cont, self.deformerJoints[i], mode=2)

            cont_OFF=extra.createUpGrp(cont,"OFF")
            self.conts_OFF.append([cont_OFF])
            cont_ORE = extra.createUpGrp(cont, "ORE")
            cont_con = extra.createUpGrp(cont, "con")

            # if self.side == "R":
            #     pm.setAttr("%s.rotate%s" %(cont_ORE, mirrorAxis), -180)


            if i>0:
                pm.parent(cont_OFF, self.conts[len(self.conts)-1])
                # pm.makeIdentity(cont, a=True)
            self.conts.append(cont)
            contList.append(cont)
            self.contConList.append(cont_con)

            pm.parentConstraint(cont, self.deformerJoints[i], mo=True)

        pm.parent(self.deformerJoints[0], self.scaleGrp)
        pm.parent(self.conts_OFF[0], self.scaleGrp)

        extra.colorize(contList, self.colorCodes[0])

    def createFKsetup(self):
        ## Controller Attributtes
        ## If there is no parent controller defined, create one. Everyone needs a parent

        if not self.parentController:
            self.parentController=self.scaleGrp
        # Spread

        spreadAttr = "{0}_{1}".format(self.suffix, "Spread")
        pm.addAttr(self.parentController, shortName=spreadAttr , defaultValue=0.0, at="float", k=True)
        sprMult=pm.createNode("multiplyDivide", name="sprMult_{0}_{1}".format(self.side, self.suffix))
        pm.setAttr(sprMult.input1Y, 0.4)
        pm.connectAttr("%s.%s" %(self.parentController,spreadAttr), sprMult.input2Y)

        sprMult.outputY >> self.contConList[0].rotateY
        pm.connectAttr("%s.%s" % (self.parentController, spreadAttr), self.contConList[1].rotateY)

        # Bend
        # add bend attributes for each joint (except the end joint)
        for f in range (0, (len(self.inits)-1)):
            if f == 0 and self.isThumb == True:
                bendAttr="{0}{1}".format(self.suffix, "UpDown")
            else:
                bendAttr = "{0}{1}{2}".format(self.suffix, "Bend", f)

            pm.addAttr(self.parentController, shortName=bendAttr, defaultValue=0.0, at="float", k=True)
            pm.PyNode("{0}.{1}".format(self.parentController, bendAttr)) >> self.contConList[f].rotateZ


        # pm.parentConstraint(self.limbPlug, self.conts_OFF[0], mo=True)

    def roundUp(self):
        # pm.parentConstraint(self.limbPlug, self.scaleGrp, mo=False)
        pm.setAttr(self.scaleGrp.rigVis, 0)

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

            fingerType = pm.getAttr(fingerRoot.fingerType, asString=True)
            thumb = fingerType == "Thumb"
            suffix = "%s_%s" %(suffix, pm.getAttr(fingerRoot.fingerType, asString=True))

        suffix=(extra.uniqueName("limbGrp_%s" % suffix)).replace("limbGrp_", "")
        self.limbGrp = pm.group(name="limbGrp_%s" % suffix, em=True)

        if (len(inits) < 2):
            pm.error("Insufficient Finger Initialization Joints")
            return

        self.scaleGrp = pm.group(name="scaleGrp_%s" % suffix, em=True)
        self.scaleConstraints.append(self.scaleGrp)

        ## Create LimbPlug

        pm.select(d=True)
        self.limbPlug = pm.joint(name="limbPlug_%s" % suffix, p=inits[0].getTranslation(space="world"), radius=2)
        pm.parentConstraint(self.limbPlug, self.scaleGrp)

        pm.select(d=True)

        for i in inits:
            j = pm.joint(name="jDef_{0}_{1}".format(suffix, inits.index(i)), radius=1.0)
            extra.alignTo(j, i, 2)

            if i == inits[-1]: # if it is the last joint dont add it to the deformers

                replacedName = (j.name()).replace("jDef", "j")
                pm.rename(j, replacedName)
            self.sockets.append(j)
            self.deformerJoints.append(j)

        ## Create Controllers

        self.conts = []
        conts_OFF = []
        conts_ORE = []
        contList = []
        contConList = []

        icon = ic.Icon()

        for i in range(0, len(self.deformerJoints)-1):
            contScl = (pm.getAttr(self.deformerJoints[1].tx) / 2)
            contName = ("cont_{0}_{1}".format(suffix, i))
            # cont = icon.circle(contName,(contScl,contScl,contScl), normal=(1,0,0))

            cont, dmp = icon.createIcon("Circle", iconName=contName,scale=(contScl,contScl,contScl), normal=(1,0,0))

            cont_OFF=extra.createUpGrp(cont,"OFF", mi=False)
            conts_OFF.append([cont_OFF])
            cont_ORE = extra.createUpGrp(cont, "ORE", mi=False)
            cont_con = extra.createUpGrp(cont, "con", mi=False)

            if side == "R":
                pm.setAttr("%s.rotate%s" %(cont_ORE, mirrorAxis), -180)

            extra.alignTo(cont_OFF, self.deformerJoints[i], 2)

            if i>0:
                pm.parent(cont_OFF, self.conts[len(self.conts)-1])
                pm.makeIdentity(cont, a=True)
            self.conts.append(cont)
            contList.append(cont)
            contConList.append(cont_con)

            pm.parentConstraint(cont, self.deformerJoints[i], mo=True)

        pm.parent(self.deformerJoints[0], self.scaleGrp)
        pm.parent(conts_OFF[0], self.scaleGrp)

        ## Controller Attributtes
        ## If there is no parent controller defined, create one. Everyone needs a parent

        if not parentController:
            parentController=self.scaleGrp
        # Spread

        spreadAttr = "{0}_{1}".format(suffix, "Spread")
        pm.addAttr(parentController, shortName=spreadAttr , defaultValue=0.0, at="float", k=True)
        sprMult=pm.createNode("multiplyDivide", name="sprMult_{0}_{1}".format(side, suffix))
        pm.setAttr(sprMult.input1Y, 0.4)
        pm.connectAttr("%s.%s" %(parentController,spreadAttr), sprMult.input2Y)

        sprMult.outputY >> contConList[0].rotateY
        pm.connectAttr("%s.%s" % (parentController, spreadAttr), contConList[1].rotateY)

        # Bend
        # add bend attributes for each joint (except the end joint)
        for f in range (0, (len(inits)-1)):
            if f == 0 and thumb == True:
                bendAttr="{0}{1}".format(suffix, "UpDown")
            else:
                bendAttr = "{0}{1}{2}".format(suffix, "Bend", f)

            pm.addAttr(parentController, shortName=bendAttr, defaultValue=0.0, at="float", k=True)
            pm.PyNode("{0}.{1}".format(parentController, bendAttr)) >> contConList[f].rotateZ

        pm.parent(self.scaleGrp, self.nonScaleGrp, self.cont_IK_OFF, self.limbGrp)
        extra.colorize(contList, self.colorCodes[0])
        extra.colorize(self.deformerJoints, self.colorCodes[0], shape=False)
        pm.parentConstraint(self.limbPlug, conts_OFF[0], mo=True)



