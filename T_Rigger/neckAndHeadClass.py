import pymel.core as pm
import pymel.core.datatypes as dt
import extraProcedures as extra

reload(extra)

# import contIcons as icon
import icons as ic

# reload(icon)
reload(ic)

import twistSplineClass as twistSpline
reload(twistSpline)

## TODO // NEEDS TO SUPPORT DIFFERENT ORIENTATIONS

class NeckAndHead():

    def __init__(self, inits, suffix="", side="C", resolution=3, dropoff=1):


        # fool proofing
        if (len(inits) < 2):
            pm.error("Some or all Neck and Head Bones are missing (or Renamed)")
            return

        # reinitialize the initial joints and arguments
        if isinstance(inits, list):
            self.headEnd = inits.pop(-1)
            self.headStart = inits.pop(-1)
            self.neckNodes = list(inits)

        else:
            try:
                self.neckNodes = [inits["NeckRoot"]] + inits["Neck"]
            except:
                self.neckNodes = [inits["NeckRoot"]]
            self.headStart = inits["Head"]
            self.headEnd = inits["HeadEnd"]

        self.resolution = resolution
        self.dropoff = dropoff

        # get distances
        self.neckDist = extra.getDistance(self.neckNodes[0], self.headStart)
        self.headDist = extra.getDistance(self.headStart, self.headEnd)

        # get positions
        self.root_pos = self.neckNodes[0].getTranslation(space="world")
        self.headPivPos = self.headStart.getTranslation(space="world")
        self.headEndPivPos = self.headEnd.getTranslation(space="world")

        # initialize sides
        self.sideMult = -1 if side == "R" else 1
        self.side = side

        # initialize coordinates
        self.up_axis, self.mirror_axis, self.look_axis = extra.getRigAxes(self.neckNodes[0])

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
        extra.alignTo(self.scaleGrp, self.neckNodes[0], 0)
        self.nonScaleGrp = pm.group(name="nonScaleGrp_%s" % self.suffix, em=True)

        pm.addAttr(self.scaleGrp, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True)
        pm.addAttr(self.scaleGrp, at="bool", ln="Joints_Visibility", sn="jointVis", defaultValue=True)
        pm.addAttr(self.scaleGrp, at="bool", ln="Rig_Visibility", sn="rigVis", defaultValue=False)
        # make the created attributes visible in the channelbox
        pm.setAttr(self.scaleGrp.contVis, cb=True)
        pm.setAttr(self.scaleGrp.jointVis, cb=True)
        pm.setAttr(self.scaleGrp.rigVis, cb=True)

        pm.parent(self.scaleGrp, self.limbGrp)
        pm.parent(self.nonScaleGrp, self.limbGrp)
        pass

    def createJoints(self):
        # Create Limb Plug
        pm.select(d=True)
        self.limbPlug = pm.joint(name="jPlug_%s" % self.suffix, p=self.root_pos, radius=3)

        ## Create temporaray Guide Joints
        pm.select(d=True)
        self.guideJoints = [pm.joint(name="jTemp_%s" %i, p=i.getTranslation(space="world")) for i in self.neckNodes]
        self.guideJoints.append(pm.joint(name="jTemp_Head", p=self.headPivPos))
        self.guideJoints.append(pm.joint(name="jTemp_HeadEnd", p=self.headEndPivPos))
        ## orientations
        # extra.orientJoints(self.guideJoints,
        #                    localMoveAxis=-(dt.Vector(self.up_axis)),
        #                    mirrorAxis=(self.sideMult, 0.0, 0.0), upAxis=self.sideMult * (dt.Vector(self.up_axis)))

        extra.orientJoints(self.guideJoints,
                           localMoveAxis=-(dt.Vector(self.up_axis)),
                           mirrorAxis=(self.sideMult, 0.0, 0.0), upAxis=self.sideMult * (dt.Vector(self.look_axis)))


    def createControllers(self):
        icon = ic.Icon()
        ## Neck Controller
        neckScale = (self.neckDist / 2, self.neckDist / 2, self.neckDist / 2)
        # self.cont_neck = icon.curvedCircle(name="cont_neck_%s" % self.suffix, scale=neckScale, normal=(0,0,1))
        self.cont_neck, dmp = icon.createIcon("CurvedCircle", iconName="cont_neck_%s" % self.suffix, scale=neckScale, normal=self.mirror_axis)
        # extra.alignAndAim(self.cont_neck, targetList=[self.neckNodes[0]], aimTargetList=[self.headStart], upVector=self.look_axis, rotateOff=(-90,-90,0))
        extra.alignToAlter(self.cont_neck, self.guideJoints[0], mode=2)
        self.cont_neck_ORE = extra.createUpGrp(self.cont_neck, "ORE")

        ## Head Controller
        # faceDir = 1 if self.look_axis[0] < 0 or self.look_axis[1] < 0 or self.look_axis[2] < 0 else -1
        # self.cont_head = icon.halfDome(name="cont_head_%s" % self.suffix, scale=(self.headDist, self.headDist, self.headDist), normal=(0,-1,0))
        self.cont_head, dmp = icon.createIcon("HalfDome", iconName="cont_head_%s" % self.suffix, scale=(self.headDist, self.headDist, self.headDist), normal=-dt.Vector(self.up_axis))

        # extra.alignAndAim(self.cont_head, targetList=[self.headStart, self.headEnd], aimTargetList=[self.headEnd], upVector=self.look_axis, rotateOff=(faceDir*-90,faceDir*-90,0))
        extra.alignToAlter(self.cont_head, self.guideJoints[-2], mode=2)
        # pm.xform(self.cont_head, piv=self.headPivPos, ws=True)
        self.cont_IK_OFF = extra.createUpGrp(self.cont_head, "OFF")
        self.cont_head_ORE = extra.createUpGrp(self.cont_head, "ORE")

        ## Head Squash Controller
        # self.cont_headSquash = icon.circle(name="cont_headSquash_%s" % self.suffix, scale=((self.headDist / 2), (self.headDist / 2), (self.headDist / 2)), normal=(0, 0, 1))
        self.cont_headSquash, dmp = icon.createIcon("Circle", iconName="cont_headSquash_%s" % self.suffix, scale=((self.headDist / 2), (self.headDist / 2), (self.headDist / 2)), normal=self.up_axis)
        # extra.alignAndAim(self.cont_headSquash, targetList=[self.headEnd], aimTargetList=[self.headStart], upVector=self.look_axis, rotateOff=(90,0,0))
        # extra.alignToAlter(self.cont_headSquash, self.guideJoints[-1])
        extra.alignToAlter(self.cont_headSquash, self.guideJoints[-1])
        cont_headSquash_ORE = extra.createUpGrp(self.cont_headSquash, "ORE")

        pm.parent(cont_headSquash_ORE, self.cont_head)
        pm.parent(self.cont_IK_OFF, self.limbGrp)
        pm.parent(self.cont_neck_ORE, self.scaleGrp)

        extra.colorize(self.cont_head, self.colorCodes[0])
        extra.colorize(self.cont_neck, self.colorCodes[0])
        extra.colorize(self.cont_headSquash, self.colorCodes[1])

        self.scaleGrp.contVis >> self.cont_head_ORE.v
        self.scaleGrp.contVis >> self.cont_neck_ORE.v
        self.scaleGrp.contVis >> self.cont_headSquash.v

        pass

    def createRoots(self):
        self.neckRootLoc = pm.spaceLocator(name="neckRootLoc_%s" % self.suffix)
        extra.alignToAlter(self.neckRootLoc, self.guideJoints[0])

        pm.parent(self.neckRootLoc, self.scaleGrp)

        pass

    def createIKsetup(self):
        # create spline IK for neck
        splineMode = pm.getAttr(self.neckNodes[0].mode, asString=True)
        twistType = pm.getAttr(self.neckNodes[0].twistType, asString=True)

        # create spline IK for neck
        neckSpline = twistSpline.TwistSpline()
        # print self.neckNodes+[self.headStart]
        # print list(self.guideJoints[:-1])
        # neckSpline.createTspline(self.neckNodes+[self.headStart], "neckSplineIK_%s" % self.suffix, self.resolution, dropoff=self.dropoff, mode=splineMode, twistType=twistType, colorCode=self.colorCodes[1])
        neckSpline.localMoveAxis = -(dt.Vector(self.up_axis))
        neckSpline.upAxis = self.sideMult * (dt.Vector(self.look_axis))
        neckSpline.mirrorAxis = (self.sideMult, 0.0, 0.0)

        print "-----------"
        print neckSpline.localMoveAxis, neckSpline.upAxis, neckSpline.mirrorAxis

        extra.orientJoints(self.guideJoints,
                           localMoveAxis=-(dt.Vector(self.up_axis)),
                           mirrorAxis=(self.sideMult, 0.0, 0.0), upAxis=self.sideMult * (dt.Vector(self.up_axis)))


        neckSpline.createTspline(list(self.guideJoints[:-1]), "neckSplineIK_%s" % self.suffix, self.resolution, dropoff=self.dropoff, mode=splineMode, twistType=twistType, colorCode=self.colorCodes[1])
        map(self.sockets.append, neckSpline.defJoints)

        # # Connect neck start to the neck controller
        # TODO // FIX HERE
        pm.orientConstraint(self.cont_neck, neckSpline.contCurve_Start, mo=False)
        pm.pointConstraint(neckSpline.contCurve_Start, self.cont_neck_ORE, mo=False)
        # # Connect neck end to the head controller
        # TODO // FIX HERE
        pm.parentConstraint(self.cont_head, neckSpline.contCurve_End, mo=True)
        # # pass Stretch controls from the splineIK to neck controller
        extra.attrPass(neckSpline.attPassCont, self.cont_neck)

        # # Connect the scale to the scaleGrp
        self.scaleGrp.scale >> neckSpline.scaleGrp.scale
        # bring out contents.
        # map(lambda x: pm.parent(x, self.scaleGrp), pm.listRelatives(neckSpline.scaleGrp, type="transform"))
        extra.attrPass(neckSpline.scaleGrp, self.scaleGrp, attributes=["sx", "sy", "sz"], keepSourceAttributes=True)
        pm.disconnectAttr(neckSpline.scaleGrp.scale)


        # create spline IK for Head squash
        headSpline = twistSpline.TwistSpline()
        # headSpline.createTspline([self.headStart, self.headEnd], "headSquashSplineIK_%s" % self.suffix, 3, dropoff=2,  mode=splineMode, twistType=twistType, colorCode=self.colorCodes[1])
        # print
        headSpline.createTspline(list(self.guideJoints[-2:]), "headSquashSplineIK_%s" % self.suffix, 3, dropoff=2,  mode=splineMode, twistType=twistType, colorCode=self.colorCodes[1])
        map(self.sockets.append, headSpline.defJoints)

        # # Position the head spline IK to end of the neck
        pm.pointConstraint(neckSpline.endLock, headSpline.contCurve_Start, mo=False)

        # # orient the head spline to the head controller
        # TODO // FIX HERE
        pm.orientConstraint(self.cont_head, headSpline.contCurve_Start, mo=True)

        extra.alignToAlter(self.cont_headSquash, headSpline.contCurve_End, mode=2)
        # TODO // FIX HERE
        pm.parentConstraint(self.cont_headSquash, headSpline.contCurve_End, mo=True)
        extra.attrPass(headSpline.attPassCont, self.cont_headSquash)

        # # Connect the scale to the scaleGrp
        self.scaleGrp.scale >> headSpline.scaleGrp.scale
        # bring out contents.
        # map(lambda x: pm.parent(x, self.scaleGrp), pm.listRelatives(headSpline.scaleGrp, type="transform"))
        extra.attrPass(headSpline.scaleGrp, self.scaleGrp, attributes=["sx", "sy", "sz"], keepSourceAttributes=True)
        pm.disconnectAttr(headSpline.scaleGrp.scale)

        pm.parentConstraint(self.limbPlug, self.neckRootLoc, mo=True)

        ############ FOR LONG NECKS ##############

        midControls = []

        for m in range (0, len(neckSpline.contCurves_ORE)):
            if m > 0 and m < (neckSpline.contCurves_ORE):
                midControls.append(neckSpline.contCurves_ORE[m])

                oCon = pm.parentConstraint(self.cont_head, self.cont_neck, neckSpline.contCurves_ORE[m], mo=True)
                blendRatio = (m + 0.0) / len(neckSpline.contCurves_ORE)
                pm.setAttr("{0}.{1}W0".format(oCon, self.cont_head), blendRatio)
                pm.setAttr("{0}.{1}W1".format(oCon, self.cont_neck), 1 - blendRatio)

        self.deformerJoints = headSpline.defJoints + neckSpline.defJoints

        pm.parent(neckSpline.contCurves_ORE, self.scaleGrp)
        pm.parent(neckSpline.contCurves_ORE[0], self.neckRootLoc)
        pm.parent(neckSpline.contCurves_ORE[len(headSpline.contCurves_ORE) - 1], self.scaleGrp)
        pm.parent(neckSpline.endLock, self.scaleGrp)
        pm.parent(neckSpline.scaleGrp, self.scaleGrp)

        pm.parent(headSpline.contCurves_ORE[0], self.scaleGrp)
        pm.parent(headSpline.contCurves_ORE[len(headSpline.contCurves_ORE) - 1], self.scaleGrp)
        pm.parent(headSpline.endLock, self.scaleGrp)
        pm.parent(headSpline.scaleGrp, self.scaleGrp)

        pm.parent(neckSpline.nonScaleGrp, self.nonScaleGrp)
        pm.parent(headSpline.nonScaleGrp, self.nonScaleGrp)

        # for lst in midControls:
        #     self.scaleGrp.contVis >> lst.v
        map(lambda x: pm.connectAttr(self.scaleGrp.contVis, x.v), midControls)


        # for i in self.deformerJoints:
        #     self.scaleGrp.jointVis >> i.v
        map(lambda x: pm.connectAttr(self.scaleGrp.jointVis, x.v), self.deformerJoints)


        self.scaleGrp.rigVis >> headSpline.contCurves_ORE[0].v
        self.scaleGrp.rigVis >> headSpline.contCurves_ORE[-1].v

        self.scaleGrp.rigVis >> neckSpline.contCurves_ORE[0].v
        self.scaleGrp.rigVis >> neckSpline.contCurves_ORE[-1].v

        self.scaleGrp.rigVis >> self.neckRootLoc.v

        for lst in headSpline.noTouchData:
            map(lambda x: pm.connectAttr(self.scaleGrp.rigVis, x.v), lst)

        for lst in neckSpline.noTouchData:
            map(lambda x: pm.connectAttr(self.scaleGrp.rigVis, x.v), lst)

        extra.colorize(self.deformerJoints, self.colorCodes[0], shape=False)

        pass

    def roundUp(self):
        self.scaleConstraints = [self.scaleGrp, self.cont_IK_OFF]
        self.anchorLocations = [self.cont_neck, self.cont_head]
        self.anchors = [(self.cont_head, "point", 5, None),
                        (self.cont_head, "orient", 1, None),
                        (self.cont_neck, "orient", 4, [self.cont_head])
                        ]
        pass

    def createLimb(self):
        self.createGrp()
        self.createJoints()
        self.createControllers()
        self.createRoots()
        self.createIKsetup()
        self.roundUp()
