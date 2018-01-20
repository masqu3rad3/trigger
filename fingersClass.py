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
        # self.connectsTo = None
        self.cont_IK_OFF = None
        self.scaleConstraints = []
        self.anchors = []
        self.anchorLocations = []

    rootMaster = None
    allControllers = []
    deformerJoints = []

    def createFinger(self, inits, suffix="", side="L", parentController=None, thumb=False, mirrorAxis="X"):

        # if not isinstance(inits, list):
        #     fingerRoot = inits.get("FingerRoot")
        #     tails = (inits.get("Tail"))
        #     inits = [tailRoot] + (tails)

        if not isinstance(inits, list):

            validRoots=["FingerRoot",
                        "ThumbRoot",
                        "IndexRoot",
                        "MiddleRoot",
                        "RingRoot",
                        "PinkyRoot",
                        "ExtraRoot"]

            validFingers=["Finger",
                          "Thumb",
                          "Index_F",
                          "Middle_F",
                          "Ring_F",
                          "Pinky_F",
                          "Extra_F"]

            fingers = None
            for root in validRoots:
                if inits.get(root):
                    fingerRoot=[inits.get(root)]
            for finger in validFingers:
                if inits.get(finger):
                    fingers = inits.get(finger)
                    suffix = "%s_%s" %(suffix, finger)

            if inits.get("Thumb") or inits.get("ThumbRoot"):
                thumb = True

            ## reinitialize the inits as a list
            if fingerRoot and fingers:
                inits = fingerRoot + fingers
            else:
                pm.error("fingers must have at least one root and one other joint")

            # thumb = pm.getAttr(inits[0].thumb)
            try:
                thumb = pm.getAttr(inits[0].thumb)
            except AttributeError:
                pass

        # suffix=(extra.uniqueName("scaleGrp_%s" %(suffix))).replace("scaleGrp_", "")

        suffix=(extra.uniqueName("limbGrp_%s" % suffix)).replace("limbGrp_", "")
        self.limbGrp = pm.group(name="limbGrp_%s" % suffix, em=True)

        # if pm.objExists("scaleGrp_" + suffix):
        #     self.idCounter = 1
        #
        #     newSuffix = "%s%s" %(suffix, str(self.idCounter))
        #     while pm.objExists("scaleGrp_" + newSuffix):
        #         self.idCounter += 1
        #         newSuffix = "%s%s" %(suffix, str(self.idCounter))
        #     suffix = newSuffix

        if (len(inits) < 2):
            pm.error("Insufficient Finger Initialization Joints")
            return

        self.scaleGrp = pm.group(name="scaleGrp_%s" % suffix, em=True)
        self.scaleConstraints.append(self.scaleGrp)

        # self.connectsTo = inits[0].getParent()

        ## Create LimbPlug

        pm.select(d=True)
        self.limbPlug = pm.joint(name="limbPlug_%s" % suffix, p=inits[0].getTranslation(space="world"), radius=2)
        # self.scaleConstraints.append(self.limbPlug)
        pm.parentConstraint(self.limbPlug, self.scaleGrp)

        pm.select(d=True)

        for i in inits:
            # jPos = i.getTranslation(space="world")
            # jOri = pm.joint(i, q=True, o=True)
            j = pm.joint(name="jDef_{0}_{1}".format(suffix, inits.index(i)), radius=1.0)
            extra.alignTo(j, i, 2)

            if i == inits[-1]: # if it is the last joint dont add it to the deformers

                replacedName = (j.name()).replace("jDef", "j")
                pm.rename(j, replacedName)
                # self.sockets.append(j)

            # if inits.index(i) == 0:
            #     self.sockets.append(i)
            self.sockets.append(j)
            self.deformerJoints.append(j)

        ## Create Controllers

        self.conts = []
        conts_OFF = []
        conts_ORE = []
        contList = []

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
            contList.append(cont_con)

            pm.parentConstraint(cont, self.deformerJoints[i], mo=True)

        pm.parent(self.deformerJoints[0], self.scaleGrp)
        pm.parent(conts_OFF[0], self.scaleGrp)

        ## Controller Attributtes

        ## If there is no parent controller defined, create one. Everyone needs a parent

        if not parentController:
            # parentController = icon.circle(("cont_{0}_{1}_Master".format(side, suffix)),(contScl*2,contScl*2,contScl*2), normal=(1,0,0))
            # extra.alignTo(parentController, self.defJoints[0], 2)
            parentController=self.scaleGrp
        # Spread

        spreadAttr = "{0}_{1}".format(suffix, "Spread")
        pm.addAttr(parentController, shortName=spreadAttr , defaultValue=0.0, at="float", k=True)
        sprMult=pm.createNode("multiplyDivide", name="sprMult_{0}_{1}".format(side, suffix))
        pm.setAttr(sprMult.input1Y, 0.4)
        pm.connectAttr("%s.%s" %(parentController,spreadAttr), sprMult.input2Y)
        # pm.PyNode("{0}.{1}{2}".format(parentController, side, "Spread")) >> sprMult.input2Y

        sprMult.outputY >> contList[0].rotateY
        # pm.PyNode("{0}.{1}{2}".format(parentController, side, "Spread")) >> contList[1].rotateY
        pm.connectAttr("%s.%s" % (parentController, spreadAttr), contList[1].rotateY)

        # Bend
        # add bend attributes for each joint (except the end joint)
        for f in range (0, (len(inits)-1)):
            if f == 0 and thumb == True:
                bendAttr="{0}{1}".format(suffix, "UpDown")
            else:
                bendAttr = "{0}{1}{2}".format(suffix, "Bend", f)

            pm.addAttr(parentController, shortName=bendAttr, defaultValue=0.0, at="float", k=True)
            pm.PyNode("{0}.{1}".format(parentController, bendAttr)) >> contList[f].rotateZ

        # pm.parent(conts_OFF[0], self.limbPlug)
        pm.parent(self.scaleGrp, self.nonScaleGrp, self.cont_IK_OFF, self.limbGrp)

        extra.colorize(contList, side)
        pm.parentConstraint(self.limbPlug, conts_OFF[0], mo=True)



