import pymel.core as pm
import extraProcedures as extra

reload(extra)

import contIcons as icon

reload(icon)

import twistSplineClass as twistSpline

reload(twistSpline)

class spine(object):

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


    def createSpine(self, inits, suffix="", resolution=4, dropoff=2.0):
        if not isinstance(inits, list):
            ## parse the dictionary inits into a list
            sRoot=inits.get("Root")
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

        if (len(inits) < 2):
            pm.error("Insufficient Spine Initialization Joints")
            return

        iconSize = extra.getDistance(inits[0], inits[len(inits)-1])
        rootPoint = inits[0].getTranslation(space="world")
        chestPoint = inits[-1].getTranslation(space="world")

        ## get the up axis
        if pm.attributeQuery("upAxis", node=inits[0], exists=True):
            if pm.getAttr(inits[0].upAxis) == "x":
                self.upAxis = (1.0,0.0,0.0)
            elif pm.getAttr(inits[0].upAxis) == "y":
                self.upAxis = (0.0, 1.0, 0.0)
            elif pm.getAttr(inits[0].upAxis) == "z":
                self.upAxis = (0.0, 0.0, 1.0)
            elif pm.getAttr(inits[0].upAxis) == "-x":
                self.upAxis = (-1.0, 0.0, 0.0)
            elif pm.getAttr(inits[0].upAxis) == "-y":
                self.upAxis = (0.0, -1.0, 0.0)
            elif pm.getAttr(inits[0].upAxis) == "-z":
                self.upAxis = (0.0, 0.0, -1.0)
        else:
            pm.warning("upAxis attribute of the root node does not exist. Using default value (y up)")
            self.upAxis = (0.0, 1.0, 0.0)

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
        self.cont_hips = icon.waist("cont_Hips", contHipsScale)
        extra.alignAndAim(self.cont_hips, targetList=[inits[0]], aimTargetList=[inits[1]], upVector=self.upAxis, rotateOff=(0,0,-90))
        self.cont_hips_ORE = extra.createUpGrp(self.cont_hips, "ORE")

        ## Body Controller
        contBodyScale = (iconSize * 0.75, iconSize * 0.75, iconSize * 0.75)
        self.cont_body = icon.square("cont_Body", contBodyScale)
        extra.alignAndAim(self.cont_body, targetList=[inits[0]], aimTargetList=[inits[1]], upVector=self.upAxis, rotateOff=(0,0,-90))
        cont_Body_POS = extra.createUpGrp(self.cont_body, "POS")

        ## Chest Controller
        # self.cont_chest = icon.cube("cont_Chest", (iconSize*0.5, iconSize*0.35, iconSize*0.2))
        # extra.alignAndAim(self.cont_chest, targetList=[inits[-1]], aimTargetList=[inits[-2]], upVector=self.upAxis,  rotateOff=(0,0,90))






        # # Create Plug Joints
        pm.select(None)
        self.limbPlug = pm.joint(name="limbPlug_" + suffix, p=rootPoint, radius=3)
        pm.select(None)
        self.endSocket = pm.joint(name="jDef_ChestSocket", p=chestPoint)
        self.sockets.append(self.endSocket)
        # self.socketDict[inits[-1]]=self.endSocket
        # parent upper plug joints
        pm.select(None)
        self.startSocket = pm.joint(p=rootPoint, name="jDef_RootSocket", radius=3)

        # self.socketDict[inits[0]]=self.startSocket
        self.sockets.append(self.startSocket)
        # contHipsScale = (iconSize / 1.5, iconSize / 1.5, iconSize / 1.5)
        # self.cont_hips = icon.waist("cont_Hips", contHipsScale)
        # extra.alignAndAim(self.cont_hips, targetList=[inits[0]], aimTargetList=[inits[1]], upVector=self.upAxis, rotateOff=(0,0,-90))
        # self.cont_hips_ORE = extra.createUpGrp(self.cont_hips, "ORE")

        # contBodyScale = (iconSize * 0.75, iconSize * 0.75, iconSize * 0.75)
        # self.cont_body = icon.square("cont_Body", contBodyScale)
        # extra.alignAndAim(self.cont_body, targetList=[inits[0]], aimTargetList=[inits[1]], upVector=self.upAxis, rotateOff=(0,0,-90))
        # cont_Body_POS = extra.createUpGrp(self.cont_body, "POS")
        self.cont_IK_OFF = cont_Body_POS
        pm.parentConstraint(self.limbPlug, cont_Body_POS, mo=True)

        self.cont_chest = icon.cube("cont_Chest", (iconSize*0.5, iconSize*0.35, iconSize*0.2))
        extra.alignAndAim(self.cont_chest, targetList=[inits[-1]], aimTargetList=[inits[-2]], upVector=self.upAxis,  rotateOff=(180,0,-90))
        ## extra.alignTo(self.cont_chest, inits[-1])
        ## extra.alignTo(self.cont_chest, inits[len(inits)-2],1)


        # move the pivot to its base
        # pm.xform(self.cont_chest, piv=(0,-iconSize/2,0))
        # pm.move(self.cont_chest, chestPoint, rpr=True)

        spine = twistSpline.twistSpline()
        spine.createTspline(inits, "spine" + suffix, resolution, dropoff=dropoff)

        midConnection = spine.contCurves_ORE[(len(spine.contCurves_ORE)/2)]


        self.nonScaleGrp = spine.nonScaleGrp
        # # connect the spine root to the master root
        pm.parentConstraint(self.startSocket, spine.contCurve_Start, mo=True)
        # self.startSocket.rotateY >> spine.twistNode.input1X

        # # connect the spine end
        pm.parentConstraint(self.cont_chest, spine.contCurve_End, mo=True)
        # self.cont_chest.rotateY >> spine.twistNode.input1Y

        # # connect the master root to the hips controller
        pm.parentConstraint(self.cont_hips, self.startSocket, mo=True)
        # # connect upper plug points to the spine and orient it to the chest controller
        pm.pointConstraint(spine.endLock, self.endSocket)
        pm.orientConstraint(self.cont_chest, self.endSocket)

        # # pass Stretch controls from the splineIK to neck controller
        extra.attrPass(spine.attPassCont, self.cont_chest)

        midSpineLocA_List = []
        midSpineLocB_List = []
        cont_spineFK_A_List = []
        cont_spineFK_B_List = []
        contSpineFKAScale = (iconSize / 2, iconSize / 2, iconSize / 2)
        contSpineFKBScale = (iconSize / 2.5, iconSize / 2.5, iconSize / 2.5)
        ## create locators on the mid controller to be used as alignment
        for m in range (0, len(spine.contCurves_ORE)):
            pos = spine.contCurves_ORE[m].getTranslation(space="world")

            if m > 0 and m < (spine.contCurves_ORE):
                # midSpineLocA = pm.spaceLocator(name="midSpineLocA_%s_%s" %(str(m), suffix), p=pos)
                midSpineLocA = pm.spaceLocator(name="midSpineLocA_%s_%s" % (str(m), suffix))
                extra.alignTo(midSpineLocA, spine.contCurves_ORE[m], 2)
                midSpineLocA_List.append(midSpineLocA)
                # midSpineLocB = pm.spaceLocator(name="midSpineLocB_%s_%s" % (str(m), suffix), p=pos)
                midSpineLocB = pm.spaceLocator(name="midSpineLocB_%s_%s" % (str(m), suffix))
                extra.alignTo(midSpineLocB, spine.contCurves_ORE[m], 2)
                midSpineLocB_List.append(midSpineLocB)
                pm.parentConstraint(midSpineLocA, midSpineLocB, spine.contCurves_ORE[m], mo=True)

                pm.parent(midSpineLocA, self.cont_chest)
                pm.parent(midSpineLocB, self.cont_hips)

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

        pm.parent(self.cont_chest, cont_spineFK_A_List[-1])
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

        for i in spine.defJoints:
            spine.scaleGrp.jointVis >> i.v
        spine.scaleGrp.jointVis >> self.endSocket.v
        spine.scaleGrp.jointVis >> self.startSocket.v

        # global rig visibilities

        spine.scaleGrp.rigVis >> spine.contCurves_ORE[0].v
        spine.scaleGrp.rigVis >> spine.contCurves_ORE[len(spine.contCurves_ORE) - 1].v

        for i in midSpineLocA_List:
            spine.scaleGrp.rigVis >> i.v
        for i in midSpineLocB_List:
            spine.scaleGrp.rigVis >> i.v

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

