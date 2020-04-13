# import pymel.core as pm
# import pymel.core.datatypes as dt

from maya import cmds
import maya.api.OpenMaya as om

from trigger.library import functions as extra
from trigger.library import controllers as ic
from trigger.library import twist_spline as twistSpline

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
            cmds.error("Insufficient Spine Initialization Joints")
            return

        # get distances
        self.iconSize = extra.getDistance(self.inits[0], self.inits[-1])

        # get positions
        self.rootPoint = extra.getWorldTranslation(self.inits[0])
        self.chestPoint = extra.getWorldTranslation(self.inits[-1])
        # self.rootPoint = self.inits[0].getTranslation(space="world")
        # self.chestPoint = self.inits[-1].getTranslation(space="world")

        # initialize sides
        self.sideMult = -1 if side == "R" else 1
        self.side = side

        # initialize coordinates
        self.up_axis, self.mirror_axis, self.look_axis = extra.getRigAxes(self.inits[0])

        # get if orientation should be derived from the initial Joints
        try: self.useRefOrientation = cmds.getAttr("%s.useRefOri" %self.inits[0])
        except:
            cmds.warning("Cannot find Inherit Orientation Attribute on Initial Root Joint %s... Skipping inheriting." %self.inits[0])
            self.useRefOrientation = False

        self.splineMode = cmds.getAttr("%s.mode" %self.inits[0], asString=True)
        self.twistType = cmds.getAttr("%s.twistType" %self.inits[0], asString=True)

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
        extra.alignTo(self.scaleGrp, self.inits[0], position=True, rotation=False)
        self.nonScaleGrp = cmds.group(name="NonScaleGrp_%s" % self.suffix, em=True)

        cmds.addAttr(self.scaleGrp, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True)
        cmds.addAttr(self.scaleGrp, at="bool", ln="Joints_Visibility", sn="jointVis", defaultValue=True)
        cmds.addAttr(self.scaleGrp, at="bool", ln="Rig_Visibility", sn="rigVis", defaultValue=False)
        # make the created attributes visible in the channelbox
        cmds.setAttr("%s.contVis" %self.scaleGrp, cb=True)
        cmds.setAttr("%s.jointVis" %self.scaleGrp, cb=True)
        cmds.setAttr("%s.rigVis" %self.scaleGrp, cb=True)

        cmds.parent(self.scaleGrp, self.limbGrp)
        cmds.parent(self.nonScaleGrp, self.limbGrp)

    def createJoints(self):
        # draw Joints
        # # Create Plug Joints
        cmds.select(None)
        self.limbPlug = cmds.joint(name="limbPlug_%s" % self.suffix, p=self.rootPoint, radius=3)
        cmds.select(None)
        self.endSocket = cmds.joint(name="jDef_ChestSocket", p=self.chestPoint)
        self.sockets.append(self.endSocket)
        cmds.select(None)
        self.startSocket = cmds.joint(p=self.rootPoint, name="jDef_RootSocket", radius=3)
        self.sockets.append(self.startSocket)

        ## Create temporaray Guide Joints
        cmds.select(d=True)
        self.guideJoints = [cmds.joint(p=extra.getWorldTranslation(i)) for i in self.inits]
        # orientations
        # extra.orientJoints(self.guideJoints,
        #                    localMoveAxis=(dt.Vector(self.up_axis)),
        #                    mirrorAxis=(self.sideMult, 0.0, 0.0), upAxis=self.sideMult * (dt.Vector(self.look_axis)))
        # extra.orientJoints(self.guideJoints, upAxis=(0,1,0), worldUpAxis=(self.up_axis), reverse=self.sideMult)
        # extra.orientJoints(self.guideJoints, worldUpAxis=-dt.Vector(self.look_axis), reverseAim=self.sideMult, reverseUp=self.sideMult)

        if not self.useRefOrientation:
            # extra.orientJoints(self.guideJoints, worldUpAxis=(self.look_axis), upAxis=(0, 1, 0), reverseAim=self.sideMult, reverseUp=self.sideMult)
            extra.orientJoints(self.guideJoints, worldUpAxis=(self.up_axis), upAxis=(0, 0, -1), reverseAim=self.sideMult, reverseUp=self.sideMult)
        else:
            for x in range (len(self.guideJoints)):
                extra.alignTo(self.guideJoints[x], self.inits[x], position=True, rotation=True)
                cmds.makeIdentity(self.guideJoints[x], a=True)


        self.deformerJoints.append(self.startSocket)
        self.deformerJoints.append(self.endSocket)

        extra.alignToAlter(self.limbPlug, self.guideJoints[0], mode=2)

        cmds.parent(self.startSocket, self.scaleGrp)
        # self.scaleGrp.rigVis >> self.limbPlug.v
        cmds.connectAttr("%s.rigVis" %self.scaleGrp, "%s.v" %self.limbPlug)

        # map(lambda x: pm.setAttr(x.displayLocalAxis, True), self.guideJoints)


        pass

    def createControllers(self):

        icon = ic.Icon()
        ## Hips Controller
        contHipsScale = (self.iconSize / 1.5, self.iconSize / 1.5, self.iconSize / 1.5)
        self.cont_hips, dmp = icon.createIcon("Waist", iconName="%s_Hips_cont" % self.suffix, scale=contHipsScale, normal=(1,0,0))
        extra.alignToAlter(self.cont_hips, self.guideJoints[0], mode=2)
        self.cont_hips_ORE = extra.createUpGrp(self.cont_hips, "ORE")


        ## Body Controller
        contBodyScale = (self.iconSize * 0.75, self.iconSize * 0.75, self.iconSize * 0.75)
        self.cont_body, dmp = icon.createIcon("Square", iconName="%s_Body_cont" % self.suffix, scale=contBodyScale, normal=(1,0,0))
        extra.alignToAlter(self.cont_body, self.guideJoints[0], mode=2)
        self.cont_body_ORE = extra.createUpGrp(self.cont_body, "POS")

        # create visibility attributes for cont_Body
        cmds.addAttr(self.cont_body, at="bool", ln="FK_A_Visibility", sn="fkAvis", defaultValue=True)
        cmds.addAttr(self.cont_body, at="bool", ln="FK_B_Visibility", sn="fkBvis", defaultValue=True)
        cmds.addAttr(self.cont_body, at="bool", ln="Tweaks_Visibility", sn="tweakVis", defaultValue=True)
        # make the created attributes visible in the channelbox
        cmds.setAttr("%s.fkAvis" %self.cont_body, cb=True)
        cmds.setAttr("%s.fkBvis" %self.cont_body, cb=True)
        cmds.setAttr("%s.tweakVis" %self.cont_body, cb=True)

        ## Chest Controller
        contChestScale = (self.iconSize*0.5, self.iconSize*0.35, self.iconSize*0.2)
        self.cont_chest, dmp = icon.createIcon("Cube", iconName="%s_Chest_cont" % self.suffix, scale=contChestScale, normal=(0,0,1))
        extra.alignToAlter(self.cont_chest, self.guideJoints[-1], mode=2)
        cont_Chest_ORE = extra.createUpGrp(self.cont_chest, "ORE")

        self.cont_spineFK_A_List = []
        self.cont_spineFK_B_List = []
        contSpineFKAScale = (self.iconSize / 2, self.iconSize / 2, self.iconSize / 2)
        contSpineFKBScale = (self.iconSize / 2.5, self.iconSize / 2.5, self.iconSize / 2.5)

        for m in range (0, len(self.guideJoints)):

            # contA = icon.circle("cont_SpineFK_A_%s%s" %(str(m), self.suffix), contSpineFKAScale, normal=(1,0,0))
            contA, _ = icon.createIcon("Circle", iconName="%s%i_SpineFK_A_cont" %(self.suffix, m), scale=contSpineFKAScale, normal=(1, 0, 0))
            extra.alignToAlter(contA, self.guideJoints[m], 2)
            contA_ORE = extra.createUpGrp(contA, "ORE")
            self.cont_spineFK_A_List.append(contA)

            # contB = icon.ngon("cont_SpineFK_B_%s%s" %(str(m), self.suffix), contSpineFKBScale, normal=(0,0,1))
            contB, dmp = icon.createIcon("Ngon", iconName="%s%i_SpineFK_B_cont" %(self.suffix, m), scale=contSpineFKBScale, normal=(1,0,0))
            extra.alignTo(contB, self.guideJoints[m], position=True, rotation=True)
            contB_ORE = extra.createUpGrp(contB, "ORE")
            self.cont_spineFK_B_List.append(contB)

            if m != 0:
                a_start_parent = cmds.listRelatives(self.cont_spineFK_A_List[m], parent=True)[0]
                b_end_parent = cmds.listRelatives(self.cont_spineFK_B_List[m - 1], parent=True)[0]
                cmds.parent(a_start_parent, self.cont_spineFK_A_List[m - 1])
                cmds.parent(b_end_parent, self.cont_spineFK_B_List[m])

        cmds.parent(self.cont_hips_ORE, self.cont_spineFK_B_List[0])

        cmds.parent(cmds.listRelatives(self.cont_spineFK_B_List[-1], parent=True), self.cont_body)

        cmds.parent(cont_Chest_ORE, self.cont_spineFK_A_List[-1])
        cmds.parent(cmds.listRelatives(self.cont_spineFK_A_List[0], parent=True), self.cont_body)
        cmds.parent(self.cont_body_ORE, self.limbGrp)


        cmds.parentConstraint(self.limbPlug, self.cont_body_ORE, mo=False)

        map(lambda x: cmds.connectAttr("%s.fkAvis" %self.cont_body, "%s.v" %cmds.listRelatives(x, s=True)[0]), self.cont_spineFK_A_List)
        map(lambda x: cmds.connectAttr("%s.fkBvis" %self.cont_body, "%s.v" %cmds.listRelatives(x, s=True)[0]), self.cont_spineFK_B_List)

        extra.colorize(self.cont_body, self.colorCodes[0])
        extra.colorize(self.cont_chest, self.colorCodes[0])
        extra.colorize(self.cont_hips, self.colorCodes[0])

        extra.colorize(self.cont_spineFK_A_List, self.colorCodes[0])
        extra.colorize(self.cont_spineFK_B_List, self.colorCodes[1])

    def createRoots(self):
        pass

    def createIKsetup(self):
        spine = twistSpline.TwistSpline()
        spine.upAxis =  -(om.MVector(self.look_axis))
        spine.createTspline(self.guideJoints, "Spine_%s" % self.suffix, self.resolution, dropoff=self.dropoff, mode=self.splineMode, twistType=self.twistType)

        # self.sockets += spine.defJoints
        self.sockets.extend(spine.defJoints)

        extra.attrPass(spine.scaleGrp, self.scaleGrp, attributes=["sx", "sy", "sz"], keepSourceAttributes=True)

        midConnection = spine.contCurves_ORE[(len(spine.contCurves_ORE) / 2)]


        # # connect the spine root to the master root
        cmds.parentConstraint(self.startSocket, spine.contCurve_Start, mo=True)

        # # connect the spine end
        cmds.parentConstraint(self.cont_chest, spine.contCurve_End, mo=True)

        # # connect the master root to the hips controller
        cmds.parentConstraint(self.cont_hips, self.startSocket, mo=True)
        # # connect upper plug points to the spine and orient it to the chest controller
        cmds.pointConstraint(spine.endLock, self.endSocket)
        cmds.orientConstraint(self.cont_chest, self.endSocket)

        # # pass Stretch controls from the splineIK to neck controller
        extra.attrPass(spine.attPassCont, self.cont_chest)

        for m in range (len(spine.contCurves_ORE)):
            if m > 0 and m < (spine.contCurves_ORE):
                oCon = cmds.parentConstraint(self.cont_chest, self.cont_hips, spine.contCurves_ORE[m], mo=True)[0]
                blendRatio = (m + 0.0) / len(spine.contCurves_ORE)
                cmds.setAttr("{0}.{1}W0".format(oCon, self.cont_chest), blendRatio)
                cmds.setAttr("{0}.{1}W1".format(oCon, self.cont_hips), 1 - blendRatio)

        cmds.parent(spine.contCurves_ORE, spine.scaleGrp)
        cmds.parent(self.endSocket, spine.scaleGrp)
        cmds.parent(spine.endLock, spine.scaleGrp)
        cmds.parent(spine.scaleGrp, self.scaleGrp)

        cmds.parent(spine.nonScaleGrp, self.nonScaleGrp)


        self.deformerJoints += spine.defJoints
        map(lambda x: cmds.connectAttr("%s.jointVis" %self.scaleGrp, "%s.v" %x), self.deformerJoints)

        for i in range(0, len(spine.contCurves_ORE)):
            if i != 0 or i != len(spine.contCurves_ORE):
                node = extra.createUpGrp(spine.contCurves_ORE[i], "OFF")
                cmds.connectAttr("%s.tweakVis" %self.cont_body, "%s.v" %node)
                # self.cont_body.tweakVis >> node.v
                cmds.connectAttr("%s.contVis" %self.scaleGrp, "%s.v" %spine.contCurves_ORE[i])
                # self.scaleGrp.contVis >> spine.contCurves_ORE[i].v
        # self.scaleGrp.contVis >> self.cont_body.v
        cmds.connectAttr("%s.contVis" %self.scaleGrp, "%s.v" %self.cont_body)

        # cmds.connectAttr("%s.rigVis" %self.scaleGrp, "%s.v" %spine.contCurves_ORE[0]) #ETF
        # cmds.connectAttr("%s.rigVis" %self.scaleGrp, "%s.v" %spine.contCurves_ORE[len(spine.contCurves_ORE) - 1])

        for lst in spine.noTouchData:
            map(lambda x: cmds.connectAttr("%s.rigVis" %self.scaleGrp, "%s.v" %x), lst)

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
        cmds.parentConstraint(self.limbPlug, self.scaleGrp, mo=False)
        cmds.setAttr("%s.rigVis" %self.scaleGrp, 0)

        self.scaleConstraints.extend([self.scaleGrp, self.cont_body_ORE])
        self.anchorLocations = [self.cont_hips, self.cont_body, self.cont_chest]

        cmds.delete(self.guideJoints)
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
        self.roundUp()
