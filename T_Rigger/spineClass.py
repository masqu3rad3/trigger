import pymel.core as pm
import extraProcedures as extra
import pymel.core.datatypes as dt
reload(extra)

import contIcons as icon

reload(icon)

import twistSplineClass as twistSpline

reload(twistSpline)

class Spine(object):

    def __init__(self, inits, suffix="", side="C", resolution=4, dropoff=2.0):

        # reinitialize the initial Joints
        if not isinstance(inits, list):
            ## parse the dictionary inits into a list
            sRoot=inits.get("SpineRoot")
            try:
                self.spines=reversed(inits.get("Spine"))
                self.spineEnd = inits.get("SpineEnd")
                self.inits = [sRoot] + sorted(self.spines) + [self.spineEnd]
            except:
                self.spineEnd = inits.get("SpineEnd")
                self.inits = [sRoot] + [self.spineEnd]

        self.resolution = int(resolution)
        self.dropoff = 1.0 * dropoff

        # fool proofing
        if (len(inits) < 2):
            pm.error("Insufficient Spine Initialization Joints")
            return

        # get distances
        self.iconSize = extra.getDistance(self.inits[0], self.inits[-1])

        # get positions
        self.rootPoint = self.inits[0].getTranslation(space="world")
        self.chestPoint = self.inits[-1].getTranslation(space="world")

        # initialize sides
        self.sideMult = -1 if side == "R" else 1
        self.side = side

        # initialize coordinates
        self.up_axis, self.mirror_axis, self.look_axis = extra.getRigAxes(self.inits[0])

        self.splineMode = pm.getAttr(self.inits[0].mode, asString=True)
        self.twistType = pm.getAttr(self.inits[0].twistType, asString=True)

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
        extra.alignTo(self.scaleGrp, self.inits[0], 0)
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
        # # Create Plug Joints
        pm.select(None)
        self.limbPlug = pm.joint(name="limbPlug_%s" % self.suffix, p=self.rootPoint, radius=3)
        pm.select(None)
        self.endSocket = pm.joint(name="jDef_ChestSocket", p=self.chestPoint)
        self.sockets.append(self.endSocket)
        pm.select(None)
        self.startSocket = pm.joint(p=self.rootPoint, name="jDef_RootSocket", radius=3)
        self.sockets.append(self.startSocket)

        ## Create temporaray Guide Joints
        pm.select(d=True)
        self.guideJoints = [pm.joint(p=i.getTranslation(space="world")) for i in self.inits]
        # orientations
        extra.orientJoints(self.guideJoints,
                           localMoveAxis=(dt.Vector(self.up_axis)),
                           mirrorAxis=(self.sideMult, 0.0, 0.0), upAxis=self.sideMult * (dt.Vector(self.up_axis)))

        self.deformerJoints.append(self.startSocket)
        self.deformerJoints.append(self.endSocket)


        pass

    def createControllers(self):
        ## Hips Controller
        contHipsScale = (self.iconSize / 1.5, self.iconSize / 1.5, self.iconSize / 1.5)
        self.cont_hips = icon.waist("cont_Hips_%s" % self.suffix, contHipsScale, normal=(0,0,1))
        extra.alignToAlter(self.cont_hips, self.guideJoints[0], mode=2)
        self.cont_hips_ORE = extra.createUpGrp(self.cont_hips, "ORE")

        ## Body Controller
        contBodyScale = (self.iconSize * 0.75, self.iconSize * 0.75, self.iconSize * 0.75)
        self.cont_body = icon.square("cont_Body_%s" % self.suffix, contBodyScale, normal=(0,0,1))
        extra.alignToAlter(self.cont_body, self.guideJoints[0], mode=2)
        self.cont_body_ORE = extra.createUpGrp(self.cont_body, "POS")

        # create visibility attributes for cont_Body
        pm.addAttr(self.cont_body, at="bool", ln="FK_A_Visibility", sn="fkAvis", defaultValue=True)
        pm.addAttr(self.cont_body, at="bool", ln="FK_B_Visibility", sn="fkBvis", defaultValue=True)
        pm.addAttr(self.cont_body, at="bool", ln="Tweaks_Visibility", sn="tweakVis", defaultValue=True)
        # make the created attributes visible in the channelbox
        pm.setAttr(self.cont_body.fkAvis, cb=True)
        pm.setAttr(self.cont_body.fkBvis, cb=True)
        pm.setAttr(self.cont_body.tweakVis, cb=True)

        ## Chest Controller
        contChestScale = (self.iconSize*0.5, self.iconSize*0.35, self.iconSize*0.2)
        self.cont_chest = icon.cube("cont_Chest_%s" % self.suffix, contChestScale, normal=(0,0,1))
        extra.alignToAlter(self.cont_chest, self.guideJoints[-1], mode=2)
        cont_Chest_ORE = extra.createUpGrp(self.cont_chest, "ORE")
        # pm.setAttr(self.cont_chest.rotateOrder,3)
        # pm.setAttr(cont_Chest_ORE.rotateOrder, 3)

        self.cont_spineFK_A_List = []
        self.cont_spineFK_B_List = []
        contSpineFKAScale = (self.iconSize / 2, self.iconSize / 2, self.iconSize / 2)
        contSpineFKBScale = (self.iconSize / 2.5, self.iconSize / 2.5, self.iconSize / 2.5)

        for m in range (0, len(self.guideJoints)):

            contA = icon.circle("cont_SpineFK_A_%s%s" %(str(m), self.suffix), contSpineFKAScale, normal=(1,0,0))
            extra.alignToAlter(contA, self.guideJoints[m], 2)
            contA_ORE = extra.createUpGrp(contA, "ORE")
            self.cont_spineFK_A_List.append(contA)

            contB = icon.ngon("cont_SpineFK_B_%s%s" %(str(m), self.suffix), contSpineFKBScale, normal=(0,0,1))
            extra.alignTo(contB, self.guideJoints[m], 2)
            contB_ORE = extra.createUpGrp(contB, "ORE")
            self.cont_spineFK_B_List.append(contB)

            if m != 0:
                pm.parent(self.cont_spineFK_A_List[m].getParent(), self.cont_spineFK_A_List[m - 1])
                pm.parent(self.cont_spineFK_B_List[m - 1].getParent(), self.cont_spineFK_B_List[m])

        pm.parent(self.cont_hips_ORE, self.cont_spineFK_B_List[0])
        pm.parent(self.cont_spineFK_B_List[-1].getParent(), self.cont_body)

        pm.parent(cont_Chest_ORE, self.cont_spineFK_A_List[-1])
        pm.parent(self.cont_spineFK_A_List[0].getParent(), self.cont_body)
        pm.parent(self.cont_body_ORE, self.limbGrp)


        pm.parentConstraint(self.limbPlug, self.cont_body_ORE, mo=True)

        map(lambda x: pm.connectAttr(self.cont_body.fkAvis, x.getShape().v), self.cont_spineFK_A_List)
        map(lambda x: pm.connectAttr(self.cont_body.fkBvis, x.getShape().v), self.cont_spineFK_B_List)


        extra.colorize(self.cont_body, self.colorCodes[0])
        extra.colorize(self.cont_chest, self.colorCodes[0])
        extra.colorize(self.cont_hips, self.colorCodes[0])

        extra.colorize(self.cont_spineFK_A_List, self.colorCodes[0])
        extra.colorize(self.cont_spineFK_B_List, self.colorCodes[1])

    def createRoots(self):
        pass

    def createIKsetup(self):
        spine = twistSpline.TwistSpline()
        spine.createTspline(self.guideJoints, "spine_%s" % self.suffix, self.resolution, dropoff=self.dropoff, mode=self.splineMode, twistType=self.twistType)
        # self.sockets += spine.defJoints
        self.sockets.extend(spine.defJoints)

        extra.attrPass(spine.scaleGrp, self.scaleGrp, attributes=["sx", "sy", "sz"], keepSourceAttributes=True)
        pm.disconnectAttr(spine.scaleGrp.scale)

        midConnection = spine.contCurves_ORE[(len(spine.contCurves_ORE) / 2)]


        # # connect the spine root to the master root
        pm.parentConstraint(self.startSocket, spine.contCurve_Start, mo=True)

        # # connect the spine end
        pm.parentConstraint(self.cont_chest, spine.contCurve_End, mo=True)

        # # connect the master root to the hips controller
        pm.parentConstraint(self.cont_hips, self.startSocket, mo=True)
        # # connect upper plug points to the spine and orient it to the chest controller
        pm.pointConstraint(spine.endLock, self.endSocket)
        pm.orientConstraint(self.cont_chest, self.endSocket)

        # # pass Stretch controls from the splineIK to neck controller
        extra.attrPass(spine.attPassCont, self.cont_chest)

        for m in range (len(spine.contCurves_ORE)):
            if m > 0 and m < (spine.contCurves_ORE):
                oCon = pm.parentConstraint(self.cont_chest, self.cont_hips, spine.contCurves_ORE[m], mo=True)
                blendRatio = (m + 0.0) / len(spine.contCurves_ORE)
                pm.setAttr("{0}.{1}W0".format(oCon, self.cont_chest), blendRatio)
                pm.setAttr("{0}.{1}W1".format(oCon, self.cont_hips), 1 - blendRatio)

        pm.parent(spine.contCurves_ORE, spine.scaleGrp)
        pm.parent(self.endSocket, spine.scaleGrp)
        pm.parent(spine.endLock, spine.scaleGrp)
        pm.parent(spine.scaleGrp, self.scaleGrp)

        pm.parent(spine.nonScaleGrp, self.nonScaleGrp)


        self.deformerJoints += spine.defJoints
        map(lambda x: pm.connectAttr(self.scaleGrp.jointVis, x.v), self.deformerJoints)

        for i in range(0, len(spine.contCurves_ORE)):
            if i != 0 or i != len(spine.contCurves_ORE):
                node = extra.createUpGrp(spine.contCurves_ORE[i], "OFF")
                self.cont_body.tweakVis >> node.v
                self.scaleGrp.contVis >> spine.contCurves_ORE[i].v
        self.scaleGrp.contVis >> self.cont_body.v

        self.scaleGrp.rigVis >> spine.contCurves_ORE[0].v
        self.scaleGrp.rigVis >> spine.contCurves_ORE[len(spine.contCurves_ORE) - 1].v

        for lst in spine.noTouchData:
            map(lambda x: pm.connectAttr(self.scaleGrp.rigVis, x.v), lst)

        extra.colorize(self.deformerJoints, self.colorCodes[0], shape=False)

    def createFKsetup(self):
        pass

    def ikfkSwitching(self):
        pass

    def createRibbons(self):
        pass

    def createTwistSplines(self):
        pass

    def createAngleExtractors(self):
        pass

    def roundUp(self):
        pm.parentConstraint(self.limbPlug, self.scaleGrp, mo=False)
        pm.setAttr(self.scaleGrp.rigVis, 0)

        self.scaleConstraints.extend([self.scaleGrp, self.cont_body_ORE])
        self.anchorLocations = [self.cont_hips, self.cont_body, self.cont_chest]

        pm.delete(self.guideJoints)
        # lock and hide
        extra.lockAndHide(self.cont_body, "v")
        extra.lockAndHide(self.cont_hips, ["sx", "sy", "sz", "v"])
        extra.lockAndHide(self.cont_chest, ["sx", "sy", "sz", "v"])

        map(lambda x: extra.lockAndHide(x, ["tx", "ty", "tz", "sx", "sy", "sz", "v"]), self.cont_spineFK_A_List)
        map(lambda x: extra.lockAndHide(x, ["tx", "ty", "tz", "sx", "sy", "sz", "v"]), self.cont_spineFK_B_List)


    def createLimb(self):
        self.createGrp()
        self.createJoints()
        self.createControllers()
        self.createRoots()
        self.createIKsetup()
        # self.createFKsetup()
        # self.ikfkSwitching()
        # self.createRibbons()
        # self.createTwistSplines()
        # self.createAngleExtractors()
        self.roundUp()
