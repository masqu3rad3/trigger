import pymel.core as pm

import extraProcedures as extra

reload(extra)

import contIcons as icon

reload(icon)

import createTwistSpline as spline

reload(spline)
import twistSplineClass as twistSpline
reload(twistSpline)

class neckAndHead():

    scaleGrp = None
    nonScaleGrp = None
    neckRootLoc = None
    cont_neck = None
    cont_head = None
    cont_head_OFF = None

    def createNeckAndHead(self, inits, suffix=""):
        idCounter = 0
        ## create an unique suffix
        while pm.objExists("scaleGrp_" + suffix):
            suffix = "%s%s" % (suffix, str(idCounter + 1))

        if (len(inits) < 5):
            pm.error("Some or all Neck and Head Bones are missing (or Renamed)")
            return

        # define related joints
        neckStart = inits["Neck"]
        headStart = inits["Head"]
        headEnd = inits["HeadEnd"]
        jawStart = inits["Jaw"]
        jawEnd = inits["JawEnd"]

        # define groups
        self.scaleGrp = pm.group(name="scaleGrp_"+suffix, em=True)
        self.nonScaleGrp = pm.group(name="nonScaleGrp_"+suffix, em=True)

        # get necessary distances
        neckDist = extra.getDistance(neckStart, headStart)
        headDist = extra.getDistance(headStart, headEnd)

        # create Controllers

        # # neck Controller
        neckScale = (neckDist / 2, neckDist / 2, neckDist / 2)
        self.cont_neck = icon.curvedCircle(name="cont_neck_"+suffix, scale=neckScale, location=(neckStart.getTranslation(space="world")))
        cont_neck_ORE = extra.createUpGrp(self.cont_neck, "ORE")

        # # head Controller
        headCenterPos = (headStart.getTranslation(space="world") + headEnd.getTranslation(space="world")) / 2
        headPivPos = headStart.getTranslation(space="world")
        headScale = (extra.getDistance(headStart, headEnd) / 3)
        self.cont_head = icon.halfDome(name="cont_head_"+suffix, scale=(headScale, headScale, headScale), location=headCenterPos)
        self.cont_head_OFF = extra.createUpGrp(self.cont_head, "OFF")
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
        extra.alignTo(self.neckRootLoc, neckStart)

        # neckSpline = spline.createTspline([neckStart, headStart], "neckSplineIK_"+suffix, 4, dropoff=2)
        neckSpline = twistSpline.twistSpline()
        neckSpline.createTspline([neckStart, headStart], "neckSplineIK_"+suffix, 4, dropoff=2)
        # # Connect neck start to the neck controller
        pm.orientConstraint(self.cont_neck, neckSpline.contCurve_Start,
                            mo=True)  # This will be position constrained to the spine(or similar)

        pm.pointConstraint(neckSpline.contCurve_Start, cont_neck_ORE)
        # # Connect neck end to the head controller
        pm.parentConstraint(self.cont_head, neckSpline.contCurve_End, mo=True)

        # # pass Stretch controls from the splineIK to neck controller
        extra.attrPass(neckSpline.attPassCont, self.cont_neck)

        # # Connect the scale to the scaleGrp
        self.scaleGrp.scale >> neckSpline.scaleGrp.scale

        # create spline IK for Head squash
        # headSpline = spline.createTspline([headStart, headEnd], "headSquashSplineIK_"+suffix, 4, dropoff=2)
        headSpline = twistSpline.twistSpline()
        headSpline.createTspline([headStart, headEnd], "headSquashSplineIK_"+suffix, 4, dropoff=2)



        # # Position the head spline IK to end of the neck
        pm.pointConstraint(neckSpline.endLock, headSpline.contCurve_Start, mo=True)
        # # orient the head spline to the head controller
        pm.orientConstraint(self.cont_head, headSpline.contCurve_Start, mo=True)

        pm.parentConstraint(cont_headSquash, headSpline.contCurve_End, mo=True)
        # # pass Stretch controls from the splineIK to neck controller
        extra.attrPass(headSpline.attPassCont, cont_headSquash)

        # # Connect the scale to the scaleGrp
        self.scaleGrp.scale >> headSpline.scaleGrp.scale



        # GOOD PARENTING
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
        pm.parent(neckSpline.nonScaleGrp, self.nonScaleGrp)


        # RIG VISIBILITY

        # global visibilities attributes

        pm.addAttr(self.scaleGrp, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True)
        pm.addAttr(self.scaleGrp, at="bool", ln="Joints_Visibility", sn="jointVis", defaultValue=True)
        pm.addAttr(self.scaleGrp, at="bool", ln="Rig_Visibility", sn="rigVis", defaultValue=False)
        # make the created attributes visible in the channelbox
        pm.setAttr(self.scaleGrp.contVis, cb=True)
        pm.setAttr(self.scaleGrp.jointVis, cb=True)
        pm.setAttr(self.scaleGrp.rigVis, cb=True)

        # global control visibilities

        self.scaleGrp.contVis >> cont_head_ORE.v
        self.scaleGrp.contVis >> cont_neck_ORE.v
        self.scaleGrp.contVis >> cont_headSquash.v

        # global joint visibilities

        for i in headSpline.defJoints:
            self.scaleGrp.jointVis >> i.v

        for i in neckSpline.defJoints:
            self.scaleGrp.jointVis >> i.v

        # global rig visibilities

        self.scaleGrp.rigVis >> headSpline.contCurves_ORE[0].v
        self.scaleGrp.rigVis >> headSpline.contCurves_ORE[len(headSpline.contCurves_ORE) - 1].v

        self.scaleGrp.rigVis >> neckSpline.contCurves_ORE[0].v
        self.scaleGrp.rigVis >> neckSpline.contCurves_ORE[len(headSpline.contCurves_ORE) - 1].v

        for lst in headSpline.noTouchData:
            for i in lst:
                self.scaleGrp.rigVis >> i.v

        for lst in neckSpline.noTouchData:
            for i in lst:
                self.scaleGrp.rigVis >> i.v

        # //TODO

        # FOOL PROOF
        extra.lockAndHide(cont_headSquash, ["sx", "sy", "sz", "v"])
        extra.lockAndHide(self.cont_head, ["v"])
        extra.lockAndHide(self.cont_neck, ["tx", "ty", "tz", "v"])

        # COLORIZE
        index = 17
        extra.colorize(self.cont_head, index)
        extra.colorize(self.cont_neck, index)
        extra.colorize(cont_headSquash, index)
