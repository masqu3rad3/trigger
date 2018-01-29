import pymel.core as pm

import extraProcedures as extra

reload(extra)

import contIcons as icon

reload(icon)

import twistSplineClass as twistSpline
reload(twistSpline)

## TODO // NEEDS TO SUPPORT DIFFERENT ORIENTATIONS

class NeckAndHead():

    def __init__(self):
        # super(NeckAndHead, self).__init__()
        self.limbGrp = None
        self.scaleGrp = None
        self.nonScaleGrp = None
        self.neckRootLoc = None
        self.cont_neck = None
        self.cont_head = None
        # cont_head_OFF = None
        self.cont_IK_OFF = None
        self.sockets = []
        # startSocket = None
        # endSocket = None
        self.limbPlug = None
        self.connectsTo = None
        self.scaleConstraints = []
        self.anchors = []
        self.anchorLocations = []
        self.deformerJoints = []
        self.colorCodes = [17, 20]

    def createNeckAndHead(self, inits, suffix="", resolution=3, dropoff=1):

        # suffix=(extra.uniqueName("scaleGrp_%s" %(suffix))).replace("scaleGrp_", "")
        suffix=(extra.uniqueName("limbGrp_%s" % suffix)).replace("limbGrp_", "")
        self.limbGrp = pm.group(name="limbGrp_%s" % suffix, em=True)


        if (len(inits) < 2):
            pm.error("Some or all Neck and Head Bones are missing (or Renamed)")
            return

        # define related joints
        if isinstance(inits, list):
            headEnd = inits.pop(-1)
            headStart = inits.pop(-1)
            neckNodes = list(inits)

        else:
        # define related joints
            try:
                neckNodes = [inits["NeckRoot"]] + inits["Neck"]
            except:
                neckNodes = [inits["NeckRoot"]]
            headStart = inits["Head"]
            headEnd = inits["HeadEnd"]


        # jawStart = inits["Jaw"]
        # jawEnd = inits["JawEnd"]

        # find the Socket
        self.connectsTo = neckNodes[0].getParent()
        # if not neckParent == None:
        #     self.connectsTo = extra.identifyMaster(neckParent)[0]

        # define groups
        self.scaleGrp = pm.group(name="scaleGrp_"+suffix, em=True)
        self.nonScaleGrp = pm.group(name="nonScaleGrp_"+suffix, em=True)

        # get necessary distances and positions
        neckDist = extra.getDistance(neckNodes[0], headStart)
        headDist = extra.getDistance(headStart, headEnd)
        headPivPos = headStart.getTranslation(space="world")

        ## Get the orientation axises
        self.upAxis, self.mirroAxis, self.spineDir = extra.getRigAxes(neckNodes[0])
        print "spineDir", self.spineDir

        if self.spineDir[0] < 0 or self.spineDir[1] < 0 or self.spineDir[2] < 0:
            faceDir = 1
        else:
            faceDir = -1

        splineMode = pm.getAttr(neckNodes[0].mode, asString=True)
        # print "splineMode", splineMode
        twistType = pm.getAttr(neckNodes[0].twistType, asString=True)
        # print "twistType", twistType

        # ## get the up axis
        # axisDict={"x":(1.0,0.0,0.0),"y":(0.0,1.0,0.0),"z":(0.0,0.0,1.0),"-x":(-1.0,0.0,0.0),"-y":(0.0,-1.0,0.0),"-z":(0.0,0.0,-1.0)}
        # spineDir = {"x": (-1.0, 0.0, 0.0), "y": (0.0, -1.0, 0.0), "z": (0.0, 0.0, 1.0), "-x": (1.0, 0.0, 0.0), "-y": (0.0, 1.0, 0.0), "-z": (0.0, 0.0, 1.0)}
        # if pm.attributeQuery("upAxis", node=neckNodes[0], exists=True):
        #     try:
        #         self.upAxis=axisDict[pm.getAttr(neckNodes[0].upAxis).lower()]
        #     except:
        #         pm.warning("upAxis attribute is not valid, proceeding with default value (y up)")
        #         self.upAxis = (0.0, 1.0, 0.0)
        # else:
        #     pm.warning("upAxis attribute of the root node does not exist. Using default value (y up)")
        #     self.upAxis = (0.0, 1.0, 0.0)
        # ## get the mirror axis
        # if pm.attributeQuery("mirrorAxis", node=neckNodes[0], exists=True):
        #     try:
        #         self.mirrorAxis=axisDict[pm.getAttr(neckNodes[0].mirrorAxis).lower()]
        #     except:
        #         pm.warning("mirrorAxis attribute is not valid, proceeding with default value (scene x)")
        #         self.mirrorAxis= (1.0, 0.0, 0.0)
        # else:
        #     pm.warning("mirrorAxis attribute of the root node does not exist. Using default value (scene x)")
        #     self.mirrorAxis = (1.0, 0.0, 0.0)
        #
        # ## get spine Direction
        # if pm.attributeQuery("lookAxis", node=neckNodes[0], exists=True):
        #     try:
        #         self.spineDir = spineDir[pm.getAttr(neckNodes[0].lookAxis).lower()]
        #         if "-" in self.spineDir:
        #             faceDir = 1
        #         else:
        #             faceDir = -1
        #     except:
        #         pm.warning("Cannot get spine direction from lookAxis attribute, proceeding with default value (-x)")
        #         self.spineDir = (0.0, 0.0, -1.0)
        #         faceDir = -1
        # else:
        #     pm.warning("lookAxis attribute of the root node does not exist. Using default value (-x) for spine direction")
        #     self.spineDir = (0.0, 0.0, 1.0)
        #     faceDir = 1

        #     _____            _             _ _
        #    / ____|          | |           | | |
        #   | |     ___  _ __ | |_ _ __ ___ | | | ___ _ __ ___
        #   | |    / _ \| '_ \| __| '__/ _ \| | |/ _ \ '__/ __|
        #   | |___| (_) | | | | |_| | | (_) | | |  __/ |  \__ \
        #    \_____\___/|_| |_|\__|_|  \___/|_|_|\___|_|  |___/
        #
        #

        ## Neck Controller
        neckScale = (neckDist / 2, neckDist / 2, neckDist / 2)
        self.cont_neck = icon.curvedCircle(name="cont_neck_" + suffix, scale=neckScale)
        extra.alignAndAim(self.cont_neck, targetList=[neckNodes[0]], aimTargetList=[headStart], upVector=self.spineDir, rotateOff=(-90,-90,0))
        cont_neck_ORE = extra.createUpGrp(self.cont_neck, "ORE")


        ## Head Controller
        headScale = (extra.getDistance(headStart, headEnd) / 1)
        self.cont_head = icon.halfDome(name="cont_head_" + suffix, scale=(headScale, headScale, headScale), normal=(1,0,0))
        # extra.alignAndAim(self.cont_head, targetList=[headStart, headEnd], aimTargetList=[headEnd], upVector=self.spineDir, rotateOff=(90,-90,180))
        extra.alignAndAim(self.cont_head, targetList=[headStart, headEnd], aimTargetList=[headEnd], upVector=self.spineDir, rotateOff=(faceDir*-90,faceDir*-90,0))

        pm.xform(self.cont_head, piv=headPivPos, ws=True)
        self.cont_IK_OFF = extra.createUpGrp(self.cont_head, "OFF")
        cont_head_ORE = extra.createUpGrp(self.cont_head, "ORE")

        ## Head Squash Controller
        cont_headSquash = icon.circle(name="cont_headSquash_"+suffix, scale=((headScale / 2), (headScale / 2), (headScale / 2)), normal=(0, 0, 1))
        extra.alignAndAim(cont_headSquash, targetList=[headEnd], aimTargetList=[headStart], upVector=self.spineDir, rotateOff=(90,0,0))
        cont_headSquash_ORE = extra.createUpGrp(cont_headSquash, "ORE")


        # Create Limb Plug
        pm.select(d=True)
        self.limbPlug = pm.joint(name="jPlug_" + suffix, p=neckNodes[0].getTranslation(space="world"), radius=3)

        # create Controllers

        # # neck Controller
        # neckScale = (neckDist / 2, neckDist / 2, neckDist / 2)
        # self.cont_neck = icon.curvedCircle(name="cont_neck_" + suffix, scale=neckScale)
        # extra.alignTo(self.cont_neck, neckNodes[0], mode=0)
        # cont_neck_ORE = extra.createUpGrp(self.cont_neck, "ORE")

        # # head Controller
        # headCenterPos = (headStart.getTranslation(space="world") + headEnd.getTranslation(space="world")) / 2
        # headPivPos = headStart.getTranslation(space="world")
        # headScale = (extra.getDistance(headStart, headEnd) / 3)
        # self.cont_head = icon.halfDome(name="cont_head_"+suffix, scale=(headScale, headScale, headScale))
        # pm.move(self.cont_head, headCenterPos)
        # cont_head_OFF = extra.createUpGrp(self.cont_head, "OFF")
        # cont_head_ORE = extra.createUpGrp(self.cont_head, "ORE")
        # pm.rotate(self.cont_head, (-90, 0, 0))
        # pm.makeIdentity(self.cont_head, a=True)

        # pm.xform(self.cont_head, piv=headPivPos, ws=True)
        # pm.makeIdentity(self.cont_head, a=True)

        # # head Squash Controller
        # squashCenterPos = headEnd.getTranslation(space="world")
        #
        # cont_headSquash = icon.circle(name="cont_headSquash_"+suffix, scale=((headScale / 2), (headScale / 2), (headScale / 2)),
        #                               normal=(0, 0, 1), location=squashCenterPos)
        pm.parent(cont_headSquash_ORE, self.cont_head)

        # create spline IK for neck
        self.neckRootLoc = pm.spaceLocator(name="neckRootLoc_"+suffix)
        extra.alignTo(self.neckRootLoc, neckNodes[0])

        neckSpline = twistSpline.TwistSpline()
        neckSpline.createTspline(neckNodes+[headStart], "neckSplineIK_"+suffix, resolution, dropoff=dropoff, mode=splineMode, twistType=twistType, colorCode=self.colorCodes[1])
        for i in neckSpline.defJoints:
            self.sockets.append(i)
        # # Connect neck start to the neck controller
        pm.orientConstraint(self.cont_neck, neckSpline.contCurve_Start, mo=True)  # This will be position constrained to the spine(or similar)
        # self.cont_neck.rotateY >> neckSpline.twistNode.input1X

        pm.pointConstraint(neckSpline.contCurve_Start, cont_neck_ORE)
        # # Connect neck end to the head controller
        pm.parentConstraint(self.cont_head, neckSpline.contCurve_End, mo=True)
        # self.cont_head.rotateY >> neckSpline.twistNode.input1Y

        # # pass Stretch controls from the splineIK to neck controller
        extra.attrPass(neckSpline.attPassCont, self.cont_neck)

        # # Connect the scale to the scaleGrp
        self.scaleGrp.scale >> neckSpline.scaleGrp.scale

        # create spline IK for Head squash
        headSpline = twistSpline.TwistSpline()
        headSpline.createTspline([headStart, headEnd], "headSquashSplineIK_"+suffix, 3, dropoff=2,  mode=splineMode, twistType=twistType, colorCode=self.colorCodes[1])
        for i in headSpline.defJoints:
            self.sockets.append(i)



        # # Position the head spline IK to end of the neck
        pm.pointConstraint(neckSpline.endLock, headSpline.contCurve_Start, mo=True)
        # # orient the head spline to the head controller
        pm.orientConstraint(self.cont_head, headSpline.contCurve_Start, mo=True)
        # self.cont_head.rotateY >> headSpline.twistNode.input1X

        pm.parentConstraint(cont_headSquash, headSpline.contCurve_End, mo=True)
        # cont_headSquash.rotateY >> headSpline.twistNode.input1Y
        # # pass Stretch controls from the splineIK to neck controller
        extra.attrPass(headSpline.attPassCont, cont_headSquash)

        # # Connect the scale to the scaleGrp
        self.scaleGrp.scale >> headSpline.scaleGrp.scale

        pm.parentConstraint(self.limbPlug, self.neckRootLoc, mo=True)

        ############ FOR LONG NECKS ##############

        # midSpineLocA_List = []
        # midSpineLocB_List = []
        midControls = []
        # cont_spineFK_A_List = []
        # cont_spineFK_B_List = []
        # contSpineFKAScale = (iconSize / 2, iconSize / 2, iconSize / 2)
        # contSpineFKBScale = (iconSize / 2.5, iconSize / 2.5, iconSize / 2.5)
        ## create locators on the mid controller to be used as alignment
        for m in range (0, len(neckSpline.contCurves_ORE)):
            pos = neckSpline.contCurves_ORE[m].getTranslation(space="world")
            if m > 0 and m < (neckSpline.contCurves_ORE):


                # midSpineLocA = pm.spaceLocator(name="midSpineLocA_%s_%s" %(m, suffix), p=pos)
                # midSpineLocA_List.append(midSpineLocA)
                # midSpineLocB = pm.spaceLocator(name="midSpineLocB_%s_%s" % (m, suffix), p=pos)
                # midSpineLocB_List.append(midSpineLocB)
                # pm.parentConstraint(midSpineLocA, midSpineLocB, neckSpline.contCurves_ORE[m], mo=True)
                midControls.append(neckSpline.contCurves_ORE[m])
                # pm.parent(midSpineLocA, self.cont_head)
                # pm.parent(midSpineLocB, self.cont_neck)

                oCon = pm.parentConstraint(self.cont_head, self.cont_neck, neckSpline.contCurves_ORE[m], mo=True)
                blendRatio = (m + 0.0) / len(neckSpline.contCurves_ORE)
                pm.setAttr("{0}.{1}W0".format(oCon, self.cont_head), blendRatio)
                pm.setAttr("{0}.{1}W1".format(oCon, self.cont_neck), 1 - blendRatio)

            # contA = icon.circle("cont_SpineFK_A" + str(m), contSpineFKAScale, location=pos)
            # cont_spineFK_A_List.append(contA)
            #
            # contB = icon.ngon("cont_SpineFK_B" + str(m), contSpineFKBScale, location=pos)
            # cont_spineFK_B_List.append(contB)

            # if m != 0:
            #     pm.parent(cont_spineFK_A_List[m], cont_spineFK_A_List[m - 1])
            #     pm.parent(cont_spineFK_B_List[m - 1], cont_spineFK_B_List[m])


        # GOOD PARENTING
        pm.parent(neckSpline.contCurves_ORE, self.scaleGrp)
        pm.parent(neckSpline.contCurves_ORE[0], self.neckRootLoc)
        pm.parent(self.neckRootLoc, self.scaleGrp)
        pm.parent(neckSpline.contCurves_ORE[len(headSpline.contCurves_ORE) - 1], self.scaleGrp)
        pm.parent(neckSpline.endLock, self.scaleGrp)
        pm.parent(neckSpline.scaleGrp, self.scaleGrp)

        pm.parent(cont_neck_ORE, self.scaleGrp)

        pm.parent(headSpline.contCurves_ORE[0], self.scaleGrp)
        pm.parent(headSpline.contCurves_ORE[len(headSpline.contCurves_ORE) - 1], self.scaleGrp)
        pm.parent(headSpline.endLock, self.scaleGrp)
        pm.parent(headSpline.scaleGrp, self.scaleGrp)

        pm.parent(neckSpline.nonScaleGrp, self.nonScaleGrp)
        pm.parent(headSpline.nonScaleGrp, self.nonScaleGrp)

        self.deformerJoints = headSpline.defJoints + neckSpline.defJoints

        pm.parent(self.scaleGrp, self.nonScaleGrp, self.cont_IK_OFF, self.limbGrp)
        #### RIG VISIBILITY

        #### global visibilities attributes

        pm.addAttr(self.scaleGrp, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True)
        pm.addAttr(self.scaleGrp, at="bool", ln="Joints_Visibility", sn="jointVis", defaultValue=True)
        pm.addAttr(self.scaleGrp, at="bool", ln="Rig_Visibility", sn="rigVis", defaultValue=False)
        # make the created attributes visible in the channelbox
        pm.setAttr(self.scaleGrp.contVis, cb=True)
        pm.setAttr(self.scaleGrp.jointVis, cb=True)
        pm.setAttr(self.scaleGrp.rigVis, cb=True)

        #### global control visibilities

        self.scaleGrp.contVis >> cont_head_ORE.v
        self.scaleGrp.contVis >> cont_neck_ORE.v
        self.scaleGrp.contVis >> cont_headSquash.v
        for lst in midControls:
            self.scaleGrp.contVis >> lst.v

        # global joint visibilities

        for i in self.deformerJoints:
            self.scaleGrp.jointVis >> i.v

        #### global rig visibilities
        #
        self.scaleGrp.rigVis >> headSpline.contCurves_ORE[0].v
        self.scaleGrp.rigVis >> headSpline.contCurves_ORE[-1].v

        self.scaleGrp.rigVis >> neckSpline.contCurves_ORE[0].v
        self.scaleGrp.rigVis >> neckSpline.contCurves_ORE[-1].v

        self.scaleGrp.rigVis >> self.neckRootLoc.v

        # for lst in midSpineLocA_List:
        #     self.scaleGrp.rigVis >> lst.v
        # for lst in midSpineLocB_List:
        #     self.scaleGrp.rigVis >> lst.v


        for lst in headSpline.noTouchData:
            for i in lst:
                self.scaleGrp.rigVis >> i.v

        for lst in neckSpline.noTouchData:
            for i in lst:
                self.scaleGrp.rigVis >> i.v


        #### FOOL PROOF
        # extra.lockAndHide(cont_headSquash, ["sx", "sy", "sz", "v"])
        # extra.lockAndHide(self.cont_head, ["v"])
        # extra.lockAndHide(self.cont_neck, ["tx", "ty", "tz", "v"])

        # COLORIZE
        # index = 17
        extra.colorize(self.cont_head, self.colorCodes[0])
        extra.colorize(self.cont_neck, self.colorCodes[0])
        extra.colorize(cont_headSquash, self.colorCodes[1])

        extra.colorize(self.deformerJoints, self.colorCodes[0], shape=False)

        self.scaleConstraints = [self.scaleGrp, self.cont_IK_OFF]
        self.anchorLocations = [self.cont_neck, self.cont_head]

        self.anchors = [(self.cont_head, "point", 5, None),
                        (self.cont_head, "orient", 1, None),
                        (self.cont_neck, "orient", 4, [self.cont_head])
                        ]
        # self.cont_IK_OFF = cont_head_OFF
