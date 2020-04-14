from maya import cmds
from trigger.library import functions as extra
from trigger.library import controllers as ic

class SimpleTail(object):

    def __init__(self, inits, suffix="", side="C", conts="cube"):

        # reinitialize the initial Joints
        if not isinstance(inits, list):
            self.tailRoot = inits.get("TailRoot")
            self.tails = (inits.get("Tail"))
            self.inits = [self.tailRoot] + (self.tails)

        # fool proofing
        if (len(inits) < 2):
            cmds.error("Tail setup needs at least 2 initial joints")
            return

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