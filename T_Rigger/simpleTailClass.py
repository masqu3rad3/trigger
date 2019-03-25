import pymel.core as pm
import extraProcedures as extra
import pymel.core.datatypes as dt

reload(extra)

# import contIcons as icon
# reload(icon)

import icons as ic
reload(ic)

class SimpleTail(object):

    def __init__(self, inits, suffix="", side="C", conts="cube"):

        # reinitialize the initial Joints
        if not isinstance(inits, list):
            self.tailRoot = inits.get("TailRoot")
            self.tails = (inits.get("Tail"))
            self.inits = [self.tailRoot] + (self.tails)

        # fool proofing
        if (len(inits) < 2):
            pm.error("Tail setup needs at least 2 initial joints")
            return

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
        self.limbGrp = pm.group(name="limbGrp_%s" % self.suffix, em=True)
        self.scaleGrp = pm.group(name="scaleGrp_%s" % self.suffix, em=True)
        extra.alignTo(self.scaleGrp, self.tailRoot, 0)
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

    def createJoints(self):
        # draw Joints
        pm.select(d=True)
        self.limbPlug = pm.joint(name="limbPlug_%s" % self.suffix, p=self.inits[0].getTranslation(space="world"), radius=3)

        pm.select(d=True)
        for j in range (0,len(self.inits)):
            location = self.inits[j].getTranslation(space="world")
            bone = pm.joint(name="jDef_{0}_{1}".format(j, self.suffix), p=location)
            self.sockets.append(bone)
            self.deformerJoints.append(bone)

        extra.orientJoints(self.deformerJoints,
                           localMoveAxis=(dt.Vector(self.up_axis)),
                           mirrorAxis=(self.sideMult, 0.0, 0.0), upAxis=self.sideMult * (dt.Vector(self.up_axis)))


        pm.parent(self.deformerJoints[0], self.scaleGrp)

        map(lambda x: pm.connectAttr(self.scaleGrp.jointVis, x.v), self.deformerJoints)

        self.scaleGrp.rigVis >> self.limbPlug.v

        extra.colorize(self.deformerJoints, self.colorCodes[0], shape=False)

        pass

    def createControllers(self):

        icon = ic.Icon()

        self.contList=[]
        self.cont_off_list=[]

        for j in range (len(self.deformerJoints)-1):
            scaleDis = extra.getDistance(self.deformerJoints[j], self.deformerJoints[j + 1]) / 2
            # cont = icon.cube(name="cont_%s_%s" % (self.suffix, str(j)), scale=(scaleDis, scaleDis, scaleDis))
            cont, dmp = icon.createIcon("Cube", iconName="cont_%s_%s" % (self.suffix, str(j)), scale=(scaleDis, scaleDis, scaleDis))

            pm.xform(cont, piv=(self.sideMult * (-scaleDis), 0, 0))
            extra.alignToAlter(cont, self.deformerJoints[j], 2)

            cont_OFF = extra.createUpGrp(cont, "OFF")
            cont_ORE = extra.createUpGrp(cont, "ORE")

            self.contList.append(cont)
            self.cont_off_list.append(cont_OFF)

            if j is not 0:
                pm.parent(self.cont_off_list[j], self.contList[j - 1])
            else:
                pm.parent(self.cont_off_list[j], self.scaleGrp)

        map(lambda x: pm.connectAttr(self.scaleGrp.contVis, x.v), self.cont_off_list)
        extra.colorize(self.contList, self.colorCodes[0])

    def createFKsetup(self):
        for x in range (len(self.contList)):
            pm.parentConstraint(self.contList[x], self.deformerJoints[x], mo=False)

            # additive scalability
            sGlobal = pm.createNode("multiplyDivide", name="sGlobal_%s_%s" %(x, self.suffix))
            self.limbPlug.scale >> sGlobal.input1
            self.contList[x].scale >> sGlobal.input2
            sGlobal.output >> self.deformerJoints[x].scale

        ## last joint has no cont, use the previous one to scale that
        sGlobal = pm.createNode("multiplyDivide", name="sGlobal_Last_%s" %(self.suffix))
        self.limbPlug.scale >> sGlobal.input1
        self.contList[-1].scale >> sGlobal.input2
        sGlobal.output >> self.deformerJoints[-1].scale


    def roundUp(self):
        pm.parentConstraint(self.limbPlug, self.scaleGrp, mo=False)
        pm.setAttr(self.scaleGrp.rigVis, 0)

        self.scaleConstraints.append(self.scaleGrp)
        # lock and hide

    def createLimb(self):
        self.createGrp()
        self.createJoints()
        self.createControllers()
        self.createFKsetup()
        self.roundUp()