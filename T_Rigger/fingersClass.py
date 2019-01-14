import pymel.core as pm
import extraProcedures as extra
import contIcons as icon

reload(extra)
reload(icon)

class Fingers(object):
    def __init__(self):
        super(Fingers, self).__init__()
        self.limbGrp = None
        self.deformerJoints = []
        self.sockets = []
        self.conts = []
        self.scaleGrp = None
        self.cont_body = None
        self.cont_hips = None
        self.limbPlug = None
        self.nonScaleGrp = None
        self.cont_IK_OFF = None
        self.scaleConstraints = []
        self.anchors = []
        self.anchorLocations = []
        self.colorCodes = [6, 18]

    rootMaster = None
    allControllers = []
    deformerJoints = []

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

        for i in range(0, len(self.deformerJoints)-1):
            contScl = (pm.getAttr(self.deformerJoints[1].tx) / 2)
            contName = ("cont_{0}_{1}".format(suffix, i))
            cont = icon.circle(contName,(contScl,contScl,contScl), normal=(1,0,0))
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



