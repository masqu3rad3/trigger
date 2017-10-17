import pymel.core as pm

import extraProcedures as extra

reload(extra)

import contIcons as icon

reload(icon)

import twistSplineClass as twistSpline
reload(twistSpline)

## TODO // NEEDS TO SUPPORT DIFFERENT ORIENTATIONS

class neckAndHead():

    scaleGrp = None
    nonScaleGrp = None
    neckRootLoc = None
    cont_neck = None
    cont_head = None
    # cont_head_OFF = None
    cont_IK_OFF = None
    sockets = []
    # startSocket = None
    # endSocket = None
    limbPlug = None
    connectsTo = None
    scaleConstraints = []
    anchors = []
    anchorLocations = []

    def createNeckAndHead(self, inits, suffix="", resolution=3, dropoff=1):
        idCounter = 0
        ## create an unique suffix
        while pm.objExists("scaleGrp_" + suffix):
            suffix = "%s%s" % (suffix, str(idCounter + 1))

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

        # get necessary distances
        neckDist = extra.getDistance(neckNodes[0], headStart)
        headDist = extra.getDistance(headStart, headEnd)

        # Create Limb Plug
        pm.select(d=True)
        self.limbPlug = pm.joint(name="jPlug_" + suffix, p=neckNodes[0].getTranslation(space="world"), radius=3)

        # create Controllers

        # # neck Controller
        neckScale = (neckDist / 2, neckDist / 2, neckDist / 2)
        # self.cont_neck = icon.curvedCircle(name="cont_neck_"+suffix, scale=neckScale, location=(neckNodes[0].getTranslation(space="world")))
        self.cont_neck = icon.curvedCircle(name="cont_neck_" + suffix, scale=neckScale)
        extra.alignTo(self.cont_neck, neckNodes[0], mode=0)
        cont_neck_ORE = extra.createUpGrp(self.cont_neck, "ORE")

        # # head Controller
        headCenterPos = (headStart.getTranslation(space="world") + headEnd.getTranslation(space="world")) / 2
        headPivPos = headStart.getTranslation(space="world")
        headScale = (extra.getDistance(headStart, headEnd) / 3)
        self.cont_head = icon.halfDome(name="cont_head_"+suffix, scale=(headScale, headScale, headScale))
        pm.move(self.cont_head, headCenterPos)
        cont_head_OFF = extra.createUpGrp(self.cont_head, "OFF")
        cont_head_ORE = extra.createUpGrp(self.cont_head, "ORE")
        pm.rotate(self.cont_head, (-90, 0, 0))
        pm.makeIdentity(self.cont_head, a=True)

        pm.xform(self.cont_head, piv=headPivPos, ws=True)
        pm.makeIdentity(self.cont_head, a=True)

        # # head Squash Controller
        squashCenterPos = headEnd.getTranslation(space="world")

        cont_headSquash = icon.circle(name="cont_headSquash_"+suffix, scale=((headScale / 2), (headScale / 2), (headScale / 2)),
                                      normal=(0, 0, 1), location=squashCenterPos)
        pm.parent(cont_headSquash, self.cont_head)

        # create spline IK for neck
        self.neckRootLoc = pm.spaceLocator(name="neckRootLoc_"+suffix)
        extra.alignTo(self.neckRootLoc, neckNodes[0])

        neckSpline = twistSpline.twistSpline()
        neckSpline.createTspline(neckNodes+[headStart], "neckSplineIK_"+suffix, resolution, dropoff=dropoff)
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
        headSpline = twistSpline.twistSpline()
        headSpline.createTspline([headStart, headEnd], "headSquashSplineIK_"+suffix, 3, dropoff=2)



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

        midSpineLocA_List = []
        midSpineLocB_List = []
        midControls = []
        # cont_spineFK_A_List = []
        # cont_spineFK_B_List = []
        # contSpineFKAScale = (iconSize / 2, iconSize / 2, iconSize / 2)
        # contSpineFKBScale = (iconSize / 2.5, iconSize / 2.5, iconSize / 2.5)
        ## create locators on the mid controller to be used as alignment
        for m in range (0, len(neckSpline.contCurves_ORE)):
            pos = neckSpline.contCurves_ORE[m].getTranslation(space="world")
            if m > 0 and m < (neckSpline.contCurves_ORE):

                # anan = pm.spaceLocator(name="anan%s_%s" % (m, suffix), p=location)
                # baban = pm.spaceLocator(name="baban%s_%s" % (m, suffix), p=location)
                midSpineLocA = pm.spaceLocator(name="midSpineLocA_%s_%s" %(m, suffix), p=pos)
                midSpineLocA_List.append(midSpineLocA)
                midSpineLocB = pm.spaceLocator(name="midSpineLocB_%s_%s" % (m, suffix), p=pos)
                midSpineLocB_List.append(midSpineLocB)
                pm.parentConstraint(midSpineLocA, midSpineLocB, neckSpline.contCurves_ORE[m], mo=True)
                midControls.append(neckSpline.contCurves_ORE[m])
                pm.parent(midSpineLocA, self.cont_head)
                pm.parent(midSpineLocB, self.cont_neck)

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

        for i in headSpline.defJoints:
            self.scaleGrp.jointVis >> i.v

        for i in neckSpline.defJoints:
            self.scaleGrp.jointVis >> i.v

        #### global rig visibilities
        #
        self.scaleGrp.rigVis >> headSpline.contCurves_ORE[0].v
        self.scaleGrp.rigVis >> headSpline.contCurves_ORE[-1].v

        self.scaleGrp.rigVis >> neckSpline.contCurves_ORE[0].v
        self.scaleGrp.rigVis >> neckSpline.contCurves_ORE[-1].v

        self.scaleGrp.rigVis >> self.neckRootLoc.v

        for lst in midSpineLocA_List:
            self.scaleGrp.rigVis >> lst.v
        for lst in midSpineLocB_List:
            self.scaleGrp.rigVis >> lst.v


        for lst in headSpline.noTouchData:
            for i in lst:
                self.scaleGrp.rigVis >> i.v

        for lst in neckSpline.noTouchData:
            for i in lst:
                self.scaleGrp.rigVis >> i.v

        # //TODO

        #### FOOL PROOF
        extra.lockAndHide(cont_headSquash, ["sx", "sy", "sz", "v"])
        extra.lockAndHide(self.cont_head, ["v"])
        extra.lockAndHide(self.cont_neck, ["tx", "ty", "tz", "v"])

        # COLORIZE
        index = 17
        extra.colorize(self.cont_head, index)
        extra.colorize(self.cont_neck, index)
        extra.colorize(cont_headSquash, index)

        self.scaleConstraints = [self.scaleGrp, cont_head_OFF]
        self.anchorLocations = [self.cont_neck, self.cont_head]

        self.anchors = [(self.cont_head, "point", 5, None),
                        (self.cont_head, "orient", 1, None),
                        (self.cont_neck, "orient", 4, [self.cont_head])
                        ]
        self.cont_IK_OFF = cont_head_OFF
