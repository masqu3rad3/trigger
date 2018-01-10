import pymel.core as pm
import extraProcedures as extra

reload(extra)

import contIcons as icon

reload(icon)

import twistSplineClass as twistSpline

reload(twistSpline)

class Spine(object):

    def __init__(self):
        self.scaleConstraints = []
        self.scaleGrp = None
        self.cont_body = None
        self.cont_hips = None
        self.cont_chest = None
        self.cont_IK_OFF = None
        self.nonScaleGrp = None
        self.sockets = []
        self.connectsTo = None
        self.anchors = []
        self.anchorLocations = []
        self.endSocket = None
        self.startSocket = None
        self.upAxis = None
        self.spineDir = None
        self.deformerJoints = []


    def createSpine(self, inits, suffix="", resolution=4, dropoff=2.0):
        if not isinstance(inits, list):
            ## parse the dictionary inits into a list
            sRoot=inits.get("SpineRoot")
            try:
                spines=reversed(inits.get("Spine"))
                spineEnd = inits.get("SpineEnd")
                inits = [sRoot] + sorted(spines) + [spineEnd]
            except:
                spineEnd = inits.get("SpineEnd")
                inits = [sRoot] + [spineEnd]


        idCounter = 0
        ## create an unique suffix
        while pm.objExists("scaleGrp_" + "spine" + suffix):
            suffix = "%s%s" %(suffix, str(idCounter + 1))

        suffix=(extra.uniqueName("scaleGrp_%s" %(suffix))).replace("scaleGrp_", "")


        if (len(inits) < 2):
            pm.error("Insufficient Spine Initialization Joints")
            return

        iconSize = extra.getDistance(inits[0], inits[len(inits)-1])
        rootPoint = inits[0].getTranslation(space="world")
        chestPoint = inits[-1].getTranslation(space="world")

        ## Get the orientation axises
        self.upAxis, self.mirroAxis, self.spineDir = extra.getRigAxes(inits[0])
        splineMode = pm.getAttr(inits[0].mode, asString=True)
        # print "splineMode", splineMode
        twistType = pm.getAttr(inits[0].twistType, asString=True)
        # print "twistType", twistType


        # ## get the up axis
        # axisDict={"x":(1.0,0.0,0.0),"y":(0.0,1.0,0.0),"z":(0.0,0.0,1.0),"-x":(-1.0,0.0,0.0),"-y":(0.0,-1.0,0.0),"-z":(0.0,0.0,-1.0)}
        # spineDir = {"x": (-1.0, 0.0, 0.0), "y": (0.0, -1.0, 0.0), "z": (0.0, 0.0, 1.0), "-x": (1.0, 0.0, 0.0), "-y": (0.0, 1.0, 0.0), "-z": (0.0, 0.0, 1.0)}
        # if pm.attributeQuery("upAxis", node=inits[0], exists=True):
        #     try:
        #         self.upAxis=axisDict[pm.getAttr(inits[0].upAxis).lower()]
        #     except:
        #         pm.warning("upAxis attribute is not valid, proceeding with default value (y up)")
        #         self.upAxis = (0.0, 1.0, 0.0)
        # else:
        #     pm.warning("upAxis attribute of the root node does not exist. Using default value (y up)")
        #     self.upAxis = (0.0, 1.0, 0.0)
        # ## get the mirror axis
        # if pm.attributeQuery("mirrorAxis", node=inits[0], exists=True):
        #     try:
        #         self.mirrorAxis=axisDict[pm.getAttr(inits[0].mirrorAxis).lower()]
        #     except:
        #         pm.warning("mirrorAxis attribute is not valid, proceeding with default value (scene x)")
        #         self.mirrorAxis= (1.0, 0.0, 0.0)
        # else:
        #     pm.warning("mirrorAxis attribute of the root node does not exist. Using default value (scene x)")
        #     self.mirrorAxis = (1.0, 0.0, 0.0)
        #
        # ## get spine Direction
        # if pm.attributeQuery("lookAxis", node=inits[0], exists=True):
        #     try:
        #         self.spineDir = spineDir[pm.getAttr(inits[0].lookAxis).lower()]
        #     except:
        #         pm.warning("Cannot get spine direction from lookAxis attribute, proceeding with default value (-x)")
        #         self.spineDir = (-1.0, 0.0, 0.0)
        # else:
        #     pm.warning("lookAxis attribute of the root node does not exist. Using default value (-x) for spine direction")
        #     self.spineDir = (1.0, 0.0, 0.0)

        #     _____            _             _ _
        #    / ____|          | |           | | |
        #   | |     ___  _ __ | |_ _ __ ___ | | | ___ _ __ ___
        #   | |    / _ \| '_ \| __| '__/ _ \| | |/ _ \ '__/ __|
        #   | |___| (_) | | | | |_| | | (_) | | |  __/ |  \__ \
        #    \_____\___/|_| |_|\__|_|  \___/|_|_|\___|_|  |___/
        #
        #

        ## Hips Controller
        contHipsScale = (iconSize / 1.5, iconSize / 1.5, iconSize / 1.5)
        self.cont_hips = icon.waist("cont_Hips_"+suffix, contHipsScale)
        extra.alignAndAim(self.cont_hips, targetList=[inits[0]], aimTargetList=[inits[1]], upVector=self.spineDir, rotateOff=(-90,-90,0))
        self.cont_hips_ORE = extra.createUpGrp(self.cont_hips, "ORE")

        ## Body Controller
        contBodyScale = (iconSize * 0.75, iconSize * 0.75, iconSize * 0.75)
        self.cont_body = icon.square("cont_Body_"+suffix, contBodyScale)
        extra.alignAndAim(self.cont_body, targetList=[inits[0]], aimTargetList=[inits[1]], upVector=self.spineDir, rotateOff=(-90, -90,0))
        cont_Body_POS = extra.createUpGrp(self.cont_body, "POS")

        ## Chest Controller
        # self.cont_chest = icon.cube("cont_Chest", (iconSize*0.5, iconSize*0.35, iconSize*0.2))
        # extra.alignAndAim(self.cont_chest, targetList=[inits[-1]], aimTargetList=[inits[-2]], upVector=self.upAxis,  rotateOff=(0,0,90))
        self.cont_chest = icon.cube("cont_Chest_"+suffix, (iconSize*0.5, iconSize*0.35, iconSize*0.2))
        extra.alignAndAim(self.cont_chest, targetList=[inits[-1]], aimTargetList=[inits[-2]], upVector=self.spineDir,  rotateOff=(-90, 90,0))
        cont_Chest_ORE = extra.createUpGrp(self.cont_chest, "ORE")
        pm.setAttr(self.cont_chest.rotateOrder,3)
        pm.setAttr(cont_Chest_ORE.rotateOrder, 3)

        ## FK-A/B Controllers
        # contSpineFKAScale = (iconSize / 2, iconSize / 2, iconSize / 2)
        # contSpineFKBScale = (iconSize / 2.5, iconSize / 2.5, iconSize / 2.5)
        # for i in range (0, len(inits)):
        #     contA = icon.circle("t_cont_SpineFK_A" + str(i) + suffix, contSpineFKAScale)
        #     contB = icon.ngon("t_cont_SpineFK_B" + str(i) + suffix, contSpineFKBScale)
        #     if i == 0:
        #         extra.alignAndAim(contA, targetList=[inits[i]], aimTargetList=[inits[i + 1]], upVector=self.spineDir, rotateOff=(0,90,90))
        #         extra.alignAndAim(contB, targetList=[inits[i]], aimTargetList=[inits[i + 1]], upVector=self.spineDir, rotateOff=(0,90,90))
        #
        #     else:
        #         extra.alignAndAim(contA, targetList=[inits[i]], aimTargetList=[inits[i - 1]], upVector=self.spineDir, rotateOff=(0,90,90))
        #         extra.alignAndAim(contB, targetList=[inits[i]], aimTargetList=[inits[i - 1]], upVector=self.spineDir, rotateOff=(0,90,90))

        # # Create Plug Joints
        pm.select(None)
        self.limbPlug = pm.joint(name="limbPlug_" + suffix, p=rootPoint, radius=3)
        pm.select(None)
        self.endSocket = pm.joint(name="jDef_ChestSocket", p=chestPoint)
        self.sockets.append(self.endSocket)
        # parent upper plug joints
        pm.select(None)
        self.startSocket = pm.joint(p=rootPoint, name="jDef_RootSocket", radius=3)
        self.sockets.append(self.startSocket)

        self.cont_IK_OFF = cont_Body_POS
        pm.parentConstraint(self.limbPlug, cont_Body_POS, mo=True)


        # move the pivot to its base
        spine = twistSpline.TwistSpline()
        spine.createTspline(inits, "spine" + suffix, resolution, dropoff=dropoff, mode=splineMode, twistType=twistType)
        for i in spine.defJoints:
            self.sockets.append(i)

        midConnection = spine.contCurves_ORE[(len(spine.contCurves_ORE)/2)]

        self.nonScaleGrp = spine.nonScaleGrp
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

        # midSpineLocA_List = []
        # midSpineLocB_List = []
        cont_spineFK_A_List = []
        cont_spineFK_B_List = []
        contSpineFKAScale = (iconSize / 2, iconSize / 2, iconSize / 2)
        contSpineFKBScale = (iconSize / 2.5, iconSize / 2.5, iconSize / 2.5)
        ## create locators on the mid controller to be used as alignment


        for m in range (0, len(spine.contCurves_ORE)):
            pos = spine.contCurves_ORE[m].getTranslation(space="world")

            if m > 0 and m < (spine.contCurves_ORE):
                # midSpineLocA = pm.spaceLocator(name="midSpineLocA_%s_%s" % (str(m), suffix))
                # extra.alignTo(midSpineLocA, spine.contCurves_ORE[m], 2)
                # midSpineLocA_List.append(midSpineLocA)
                # midSpineLocB = pm.spaceLocator(name="midSpineLocB_%s_%s" % (str(m), suffix))
                # extra.alignTo(midSpineLocB, spine.contCurves_ORE[m], 2)
                # midSpineLocB_List.append(midSpineLocB)
                # # con = extra.createUpGrp(spine.contCurves_ORE[m],"CON")
                # # pm.parentConstraint(midSpineLocA, midSpineLocB, con, mo=True)
                # # pm.parentConstraint(midSpineLocA, midSpineLocB, spine.contCurves_ORE[m], mo=True)
                #
                # # pm.pointConstraint(midSpineLocA, midSpineLocB, spine.contCurves_ORE[m], mo=True)
                # # pm.orientConstraint(midSpineLocA, midSpineLocB, spine.contCurves_ORE[m], mo=False)

                # poCon = pm.pointConstraint(spine.contCurve_End, spine.contCurve_Start, spine.contCurves_ORE[m], mo=True)
                oCon = pm.parentConstraint(self.cont_chest, self.cont_hips, spine.contCurves_ORE[m], mo=True)
                blendRatio = (m + 0.0) / len(spine.contCurves_ORE)
                pm.setAttr("{0}.{1}W0".format(oCon, self.cont_chest), blendRatio)
                pm.setAttr("{0}.{1}W1".format(oCon, self.cont_hips), 1 - blendRatio)
                # pm.setAttr("{0}.{1}W0".format(poCon, spine.contCurve_End), blendRatio)
                # pm.setAttr("{0}.{1}W1".format(poCon, spine.contCurve_Start), 1 - blendRatio)

                # pm.parent(midSpineLocA, self.cont_chest)
                # pm.parent(midSpineLocB, self.cont_hips)

            # contA = icon.circle("cont_SpineFK_A" + str(m), contSpineFKAScale, location=pos)
            contA = icon.circle("cont_SpineFK_A" + str(m) + suffix, contSpineFKAScale)
            extra.alignTo(contA, spine.contCurves_ORE[m], 2)
            # pm.setAttr(contA.rotateAxisZ, 90)
            cont_spineFK_A_List.append(contA)

            # contB = icon.ngon("cont_SpineFK_B" + str(m), contSpineFKBScale, location=pos)
            contB = icon.ngon("cont_SpineFK_B" + str(m) + suffix, contSpineFKBScale)
            extra.alignTo(contB, spine.contCurves_ORE[m], 2)
            # pm.setAttr(contB.rotateAxisZ, 90)
            cont_spineFK_B_List.append(contB)

            if m != 0:
                pm.parent(cont_spineFK_A_List[m], cont_spineFK_A_List[m - 1])
                pm.parent(cont_spineFK_B_List[m - 1], cont_spineFK_B_List[m])

        pm.parent(cont_Chest_ORE, cont_spineFK_A_List[-1])
        pm.parent(cont_spineFK_A_List[0], self.cont_body)
        pm.parent(spine.contCurves_ORE, spine.scaleGrp)  # contcurve Ore s -> scaleGrp
        pm.parent(self.endSocket, spine.scaleGrp)

        pm.parent(self.cont_hips_ORE, cont_spineFK_B_List[0])
        pm.parent(cont_spineFK_B_List[-1], self.cont_body)
        pm.parent(spine.endLock, spine.scaleGrp)

        ## CONNECT RIG VISIBILITES

        # create visibility attributes for cont_Body
        pm.addAttr(self.cont_body, at="bool", ln="FK_A_Visibility", sn="fkAvis", defaultValue=True)
        pm.addAttr(self.cont_body, at="bool", ln="FK_B_Visibility", sn="fkBvis", defaultValue=True)
        pm.addAttr(self.cont_body, at="bool", ln="Tweaks_Visibility", sn="tweakVis", defaultValue=True)
        # make the created attributes visible in the channelbox
        pm.setAttr(self.cont_body.fkAvis, cb=True)
        pm.setAttr(self.cont_body.fkBvis, cb=True)
        pm.setAttr(self.cont_body.tweakVis, cb=True)

        self.deformerJoints=[self.startSocket, self.endSocket] + spine.defJoints

        for i in cont_spineFK_A_List:
            self.cont_body.fkAvis >> i.visibility
        for i in cont_spineFK_B_List:
            self.cont_body.fkBvis >> i.visibility

        for i in range(0, len(spine.contCurves_ORE)):
            if i != 0 or i != len(spine.contCurves_ORE):
                node = extra.createUpGrp(spine.contCurves_ORE[i], "OFF")
                self.cont_body.tweakVis >> node.v

        # global visibilities attributes

        pm.addAttr(spine.scaleGrp, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True)
        pm.addAttr(spine.scaleGrp, at="bool", ln="Joints_Visibility", sn="jointVis", defaultValue=True)
        pm.addAttr(spine.scaleGrp, at="bool", ln="Rig_Visibility", sn="rigVis", defaultValue=False)
        # make the created attributes visible in the channelbox
        pm.setAttr(spine.scaleGrp.contVis, cb=True)
        pm.setAttr(spine.scaleGrp.jointVis, cb=True)
        pm.setAttr(spine.scaleGrp.rigVis, cb=True)

        # global cont visibilities

        for i in range(0, len(spine.contCurves_ORE)):
            if i != 0 or i != len(spine.contCurves_ORE):
                spine.scaleGrp.contVis >> spine.contCurves_ORE[i].v
        spine.scaleGrp.contVis >> self.cont_body.v

        # global joint visibilities

        for i in self.deformerJoints:
            spine.scaleGrp.jointVis >> i.v
        # spine.scaleGrp.jointVis >> self.endSocket.v
        # spine.scaleGrp.jointVis >> self.startSocket.v

        # global rig visibilities

        spine.scaleGrp.rigVis >> spine.contCurves_ORE[0].v
        spine.scaleGrp.rigVis >> spine.contCurves_ORE[len(spine.contCurves_ORE) - 1].v

        # for i in midSpineLocA_List:
        #     spine.scaleGrp.rigVis >> i.v
        # for i in midSpineLocB_List:
        #     spine.scaleGrp.rigVis >> i.v

        for lst in spine.noTouchData:
            for i in lst:
                spine.scaleGrp.rigVis >> i.v

        ## FOOL PROOFING

        extra.lockAndHide(self.cont_body, "v")
        extra.lockAndHide(self.cont_hips, ["sx", "sy", "sz", "v"])
        extra.lockAndHide(self.cont_chest, ["sx", "sy", "sz", "v"])
        for i in cont_spineFK_A_List:
            extra.lockAndHide(i,["tx", "ty", "tz", "sx", "sy", "sz", "v"])
        for i in cont_spineFK_B_List:
            extra.lockAndHide(i,["tx", "ty", "tz", "sx", "sy", "sz", "v"])

        ## COLOR CODING

        index = 17
        indexIK = 20
        indexFKA = 30
        indexFKB = 31
        extra.colorize(self.cont_body, index)
        extra.colorize(self.cont_chest, index)
        extra.colorize(self.cont_hips, index)
        for i in cont_spineFK_A_List:
            extra.colorize(i, indexFKA)
        for i in cont_spineFK_B_List:
            extra.colorize(i, indexFKB)

        self.scaleGrp = spine.scaleGrp
        pm.parent(self.startSocket, self.scaleGrp)
        self.scaleConstraints.extend([self.scaleGrp, cont_Body_POS])
        self.anchorLocations = [self.cont_hips, self.cont_chest]


