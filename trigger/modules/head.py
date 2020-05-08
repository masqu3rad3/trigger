from maya import cmds
import maya.api.OpenMaya as om

from trigger.library import functions as extra
from trigger.library import controllers as ic
from trigger.library import twist_spline as twistSpline
from trigger.core import feedback
FEEDBACK = feedback.Feedback(__name__)

LIMB_DATA = {
        "members": ["NeckRoot", "Neck", "Head", "Jaw", "HeadEnd"],
        "properties": [{"attr_name": "resolution",
                        "nice_name": "Resolution",
                        "attr_type": "long",
                        "min_value": 1,
                        "max_value": 9999,
                        "default_value": 4,
                        },
                       {"attr_name": "dropoff",
                        "nice_name": "Drop_Off",
                        "attr_type": "float",
                        "min_value": 0.1,
                        "max_value": 5.0,
                        "default_value": 1.0,
                        },
                       {"attr_name": "twistType",
                        "nice_name": "Twist_Type",
                        "attr_type": "enum",
                        "enum_list": "regular:infinite",
                        "default_value": 0,
                        },
                       {"attr_name": "mode",
                        "nice_name": "Mode",
                        "attr_type": "enum",
                        "enum_list": "equalDistance:sameDistance",
                        "default_value": 0,
                        },
                       ],
        "multi_guide": "Neck",
        "sided": False,
    }

## TODO // NEEDS TO SUPPORT DIFFERENT ORIENTATIONS

class Head(object):
    def __init__(self, build_data=None, inits=None, suffix="", side="C", resolution=3, dropoff=1, *args, **kwargs):
        super(Head, self).__init__()
        if build_data:
            try:
                self.neckNodes = [build_data["NeckRoot"]] + build_data["Neck"]
            except:
                self.neckNodes = [build_data["NeckRoot"]]
            self.headStart = build_data["Head"]
            self.headEnd = build_data["HeadEnd"]
            resolution = build_data.get("resolution")
            dropoff = build_data.get("dropoff")

        elif inits:
            if (len(inits) < 2):
                cmds.error("Some or all Neck and Head Bones are missing (or Renamed)")
                return
            if isinstance(inits, list):
                self.headEnd = inits.pop(-1)
                self.headStart = inits.pop(-1)
                self.neckNodes = list(inits)
        else:
            FEEDBACK.throw_error("Class needs either build_data or arminits to be constructed")


        self.resolution = resolution
        self.dropoff = dropoff

        # get distances
        self.neckDist = extra.getDistance(self.neckNodes[0], self.headStart)
        self.headDist = extra.getDistance(self.headStart, self.headEnd)

        # get positions
        self.root_pos = extra.getWorldTranslation(self.neckNodes[0])
        self.headPivPos = extra.getWorldTranslation(self.headStart)
        self.headEndPivPos = extra.getWorldTranslation(self.headEnd)

        # initialize sides
        self.sideMult = -1 if side == "R" else 1
        self.side = side

        # initialize coordinates
        self.up_axis, self.mirror_axis, self.look_axis = extra.getRigAxes(self.neckNodes[0])

        # get if orientation should be derived from the initial Joints
        try: self.useRefOrientation = cmds.getAttr("%s.useRefOri" % self.neckNodes[0])
        except:
            cmds.warning("Cannot find Inherit Orientation Attribute on Initial Root Joint %s... Skipping inheriting." %self.neckNodes[0])
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
        extra.alignTo(self.scaleGrp, self.neckNodes[0], 0)
        self.nonScaleGrp = cmds.group(name="nonScaleGrp_%s" % self.suffix, em=True)

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
        # Create Limb Plug
        cmds.select(d=True)
        self.limbPlug = cmds.joint(name="jPlug_%s" % self.suffix, p=self.root_pos, radius=3)

        ## Create temporaray Guide Joints
        cmds.select(d=True)
        self.guideJoints = [cmds.joint(name="jTemp_%s" %i, p=extra.getWorldTranslation(i)) for i in self.neckNodes]
        self.guideJoints.append(cmds.joint(name="jTemp_Head", p=self.headPivPos))
        self.guideJoints.append(cmds.joint(name="jTemp_HeadEnd", p=self.headEndPivPos))
        ## orientations
        if not self.useRefOrientation:
            extra.orientJoints(self.guideJoints, worldUpAxis=(self.look_axis), upAxis=(0, 1, 0), reverseAim=self.sideMult, reverseUp=self.sideMult)
        else:
            for x in range (len(self.guideJoints[:-2])):
                extra.alignTo(self.guideJoints[x], self.neckNodes[x], position=True, rotation=True)
                cmds.makeIdentity(self.guideJoints[x], a=True)
            extra.alignTo(self.guideJoints[-2], self.headStart, position=True, rotation=True)
            cmds.makeIdentity(self.guideJoints[-2], a=True)
            extra.alignTo(self.guideJoints[-1], self.headEnd, position=True, rotation=True)
            cmds.makeIdentity(self.guideJoints[-1], a=True)

    def createControllers(self):
        icon = ic.Icon()
        ## Neck Controller
        neckScale = (self.neckDist / 2, self.neckDist / 2, self.neckDist / 2)
        self.cont_neck, dmp = icon.createIcon("CurvedCircle", iconName="%s_neck_cont" % self.suffix, scale=neckScale, normal=(1,0,0))
        extra.alignToAlter(self.cont_neck, self.guideJoints[0], mode=2)
        self.cont_neck_ORE = extra.createUpGrp(self.cont_neck, "ORE")

        ## Head Controller
        self.cont_head, _ = icon.createIcon("HalfDome", iconName="cont_head_%s" % self.suffix, scale=(self.headDist, self.headDist, self.headDist), normal=(0,1,0))

        extra.alignToAlter(self.cont_head, self.guideJoints[-2], mode=2)
        self.cont_IK_OFF = extra.createUpGrp(self.cont_head, "OFF")
        self.cont_head_ORE = extra.createUpGrp(self.cont_head, "ORE")

        ## Head Squash Controller
        self.cont_headSquash, _ = icon.createIcon("Circle", iconName="%s_headSquash_cont" % self.suffix, scale=((self.headDist / 2), (self.headDist / 2), (self.headDist / 2)), normal=(0,1,0))
        extra.alignToAlter(self.cont_headSquash, self.guideJoints[-1])
        cont_headSquash_ORE = extra.createUpGrp(self.cont_headSquash, "ORE")

        cmds.parent(cont_headSquash_ORE, self.cont_head)
        cmds.parent(self.cont_IK_OFF, self.limbGrp)
        cmds.parent(self.cont_neck_ORE, self.scaleGrp)

        extra.colorize(self.cont_head, self.colorCodes[0])
        extra.colorize(self.cont_neck, self.colorCodes[0])
        extra.colorize(self.cont_headSquash, self.colorCodes[1])

        cmds.connectAttr("%s.contVis" % self.scaleGrp, "%s.v" % self.cont_head_ORE)
        cmds.connectAttr("%s.contVis" % self.scaleGrp, "%s.v" % self.cont_neck_ORE)
        cmds.connectAttr("%s.contVis" % self.scaleGrp, "%s.v" % self.cont_headSquash)

    def createRoots(self):
        self.neckRootLoc = cmds.spaceLocator(name="neckRootLoc_%s" % self.suffix)[0]
        extra.alignToAlter(self.neckRootLoc, self.guideJoints[0])

        cmds.parent(self.neckRootLoc, self.scaleGrp)

    def createIKsetup(self):
        # create spline IK for neck
        splineMode = cmds.getAttr("%s.mode" % self.neckNodes[0], asString=True)
        twistType = cmds.getAttr("%s.twistType" % self.neckNodes[0], asString=True)

        # create spline IK for neck
        neckSpline = twistSpline.TwistSpline()
        neckSpline.upAxis = -(om.MVector(self.look_axis))

        neckSpline.createTspline(list(self.guideJoints[:-1]), "neckSplineIK_%s" % self.suffix, self.resolution, dropoff=self.dropoff, mode=splineMode, twistType=twistType, colorCode=self.colorCodes[1])
        map(self.sockets.append, neckSpline.defJoints)

        # # Connect neck start to the neck controller
        # TODO // FIX HERE
        cmds.orientConstraint(self.cont_neck, neckSpline.contCurve_Start, mo=False)
        cmds.pointConstraint(neckSpline.contCurve_Start, self.cont_neck_ORE, mo=False)
        # # Connect neck end to the head controller
        # TODO // FIX HERE
        cmds.parentConstraint(self.cont_head, neckSpline.contCurve_End, mo=True)
        # # pass Stretch controls from the splineIK to neck controller
        extra.attrPass(neckSpline.attPassCont, self.cont_neck)

        # # Connect the scale to the scaleGrp
        cmds.connectAttr("%s.scale" % self.scaleGrp, "%s.scale" % neckSpline.scaleGrp)
        # bring out contents.
        extra.attrPass(neckSpline.scaleGrp, self.scaleGrp, attributes=["sx", "sy", "sz"], keepSourceAttributes=True)
        cmds.disconnectAttr(cmds.listConnections(neckSpline.scaleGrp, p=True)[0], "%s.scale" % neckSpline.scaleGrp)

        # create spline IK for Head squash
        headSpline = twistSpline.TwistSpline()
        headSpline.upAxis = -(om.MVector(self.look_axis))
        headSpline.createTspline(list(self.guideJoints[-2:]), "headSquashSplineIK_%s" % self.suffix, 3, dropoff=2,  mode=splineMode, twistType=twistType, colorCode=self.colorCodes[1])
        map(self.sockets.append, headSpline.defJoints)

        # # Position the head spline IK to end of the neck
        cmds.pointConstraint(neckSpline.endLock, headSpline.contCurve_Start, mo=False)

        # # orient the head spline to the head controller
        # TODO // FIX HERE
        cmds.orientConstraint(self.cont_head, headSpline.contCurve_Start, mo=True)

        extra.alignToAlter(self.cont_headSquash, headSpline.contCurve_End, mode=2)
        # TODO // FIX HERE
        cmds.parentConstraint(self.cont_headSquash, headSpline.contCurve_End, mo=True)
        extra.attrPass(headSpline.attPassCont, self.cont_headSquash)

        # # Connect the scale to the scaleGrp
        cmds.connectAttr("%s.scale" % self.scaleGrp, "%s.scale" % headSpline.scaleGrp)
        # bring out contents.
        extra.attrPass(headSpline.scaleGrp, self.scaleGrp, attributes=["sx", "sy", "sz"], keepSourceAttributes=True)
        cmds.disconnectAttr(cmds.listConnections(headSpline.scaleGrp, p=True)[0], "%s.scale" % headSpline.scaleGrp)

        cmds.parentConstraint(self.limbPlug, self.neckRootLoc, mo=True)

        ############ FOR LONG NECKS ##############

        midControls = []

        for m in range (0, len(neckSpline.contCurves_ORE)):
            if m > 0 and m < (neckSpline.contCurves_ORE):
                midControls.append(neckSpline.contCurves_ORE[m])

                oCon = cmds.parentConstraint(self.cont_head, self.cont_neck, neckSpline.contCurves_ORE[m], mo=True)[0]
                blendRatio = (m + 0.0) / len(neckSpline.contCurves_ORE)
                cmds.setAttr("{0}.{1}W0".format(oCon, self.cont_head), blendRatio)
                cmds.setAttr("{0}.{1}W1".format(oCon, self.cont_neck), 1 - blendRatio)

        self.deformerJoints = headSpline.defJoints + neckSpline.defJoints

        cmds.parent(neckSpline.contCurves_ORE, self.scaleGrp)
        cmds.parent(neckSpline.contCurves_ORE[0], self.neckRootLoc)
        try:
            cmds.parent(neckSpline.contCurves_ORE[len(headSpline.contCurves_ORE) - 1], self.scaleGrp)
        except RuntimeError:
            pass
        cmds.parent(neckSpline.endLock, self.scaleGrp)
        cmds.parent(neckSpline.scaleGrp, self.scaleGrp)

        cmds.parent(headSpline.contCurves_ORE[0], self.scaleGrp)
        try:
            cmds.parent(headSpline.contCurves_ORE[len(headSpline.contCurves_ORE) - 1], self.scaleGrp)
        except RuntimeError:
            pass
        cmds.parent(headSpline.endLock, self.scaleGrp)
        cmds.parent(headSpline.scaleGrp, self.scaleGrp)

        cmds.parent(neckSpline.nonScaleGrp, self.nonScaleGrp)
        cmds.parent(headSpline.nonScaleGrp, self.nonScaleGrp)
        map(lambda x: cmds.connectAttr("%s.contVis" % self.scaleGrp, "%s.v" % x), midControls)
        map(lambda x: cmds.connectAttr("%s.jointVis" % self.scaleGrp, "%s.v" % x), self.deformerJoints)

        cmds.connectAttr("%s.rigVis" % self.scaleGrp,"%s.v" % headSpline.contCurves_ORE[0], force=True)
        cmds.connectAttr("%s.rigVis" % self.scaleGrp,"%s.v" % headSpline.contCurves_ORE[-1], force=True)
        cmds.connectAttr("%s.rigVis" % self.scaleGrp,"%s.v" % neckSpline.contCurves_ORE[0], force=True)
        cmds.connectAttr("%s.rigVis" % self.scaleGrp,"%s.v" % neckSpline.contCurves_ORE[-1], force=True)
        cmds.connectAttr("%s.rigVis" % self.scaleGrp,"%s.v" % self.neckRootLoc, force=True)

        for lst in headSpline.noTouchData:
            map(lambda x: cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % x, force=True), lst)

        for lst in neckSpline.noTouchData:
            map(lambda x: cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % x, force=True), lst)

        extra.colorize(self.deformerJoints, self.colorCodes[0], shape=False)

    def roundUp(self):
        self.scaleConstraints = [self.scaleGrp, self.cont_IK_OFF]
        self.anchorLocations = [self.cont_neck, self.cont_head]
        self.anchors = [(self.cont_head, "point", 5, None),
                        (self.cont_head, "orient", 1, None),
                        (self.cont_neck, "orient", 4, [self.cont_head])
                        ]
        cmds.delete(self.guideJoints)

    def createLimb(self):
        self.createGrp()
        self.createJoints()
        self.createControllers()
        self.createRoots()
        self.createIKsetup()
        self.roundUp()

class Guides(object):
    def __init__(self, side="L", suffix="head", segments=None, tMatrix=None, upVector=(0, 1, 0), mirrorVector=(1, 0, 0), lookVector=(0,0,1), *args, **kwargs):
        super(Guides, self).__init__()
        # fool check

        #-------Mandatory------[Start]
        self.side = side
        self.sideMultiplier = -1 if side == "R" else 1
        self.suffix = suffix
        self.segments = segments
        self.tMatrix = om.MMatrix(tMatrix) if tMatrix else om.MMatrix()
        self.upVector = om.MVector(upVector)
        self.mirrorVector = om.MVector(mirrorVector)
        self.lookVector = om.MVector(lookVector)

        self.offsetVector = None
        self.guideJoints = []
        #-------Mandatory------[End]

    def draw_joints(self):
        if self.side == "C":
            # Guide joint positions for limbs with no side orientation
            pass
        else:
            # Guide joint positions for limbs with sides
            pass

        rPointNeck =  om.MVector(0, 25.757, 0) * self.tMatrix
        nPointNeck =  om.MVector(0, 29.418, 0.817) * self.tMatrix
        pointHead =  om.MVector(0, 32,0.817) * self.tMatrix
        addNeck = (nPointNeck - rPointNeck) / ((self.segments + 1) - 1)

        # Define the offset vector
        self.offsetVector = (nPointNeck-rPointNeck).normal()

        # Draw the joints
        for seg in range(self.segments):
            neck_jnt = cmds.joint(p=(rPointNeck + (addNeck * seg)), name="jInit_neck_%s_%i" %(self.suffix, seg))
            self.guideJoints.append(neck_jnt)
        for seg in range(1):
            head_jnt = cmds.joint(p=(rPointNeck + (addNeck * (seg + self.segments))), name="jInit_head_%s_%i" %(self.suffix, seg))
            self.guideJoints.append(head_jnt)
        headEnd = cmds.joint(p=pointHead, name="jInit_headEnd_%s" %(self.suffix))
        self.guideJoints.append(headEnd)

        # for seg in range(self.segments + 1):
        #     if not seg == (self.segments):
        #         head = cmds.joint(p=(rPointNeck + (addNeck * seg)), name="jInit_neck_%s_%s" %(self.suffix, str(seg)))
        #         cmds.setAttr("%s.side" % head, 0)
        #         if seg == 0:
        #             cmds.setAttr("%s.type" % head, 18)
        #             cmds.setAttr("%s.otherType" % head, "NeckRoot", type="string")
        #             cmds.addAttr(shortName="resolution", longName="Resolution", defaultValue=4, minValue=1,
        #                        at="long", k=True)
        #             cmds.addAttr(shortName="dropoff", longName="DropOff", defaultValue=1.0, minValue=0.1,
        #                        at="float", k=True)
        #             cmds.addAttr(at="enum", k=True, shortName="twistType", longName="Twist_Type", en="regular:infinite")
        #             cmds.addAttr(at="enum", k=True, shortName="mode", longName="Mode", en="equalDistance:sameDistance")
        #             cmds.setAttr("%s.radius" %head, 3)
        #         else:
        #             cmds.setAttr("%s.type" % head, 7)
        #     else:
        #         head= cmds.joint(p=(rPointNeck + (addNeck * seg)), name="jInit_head_%s_%s" %(suffix, str(seg)))
        #         cmds.setAttr("%s.type" % head, 8)
        #     cmds.setAttr("%s.drawLabel" % head, 1)
        #     jointList.append(head)


        # Update the guideJoints list
        extra.orientJoints(self.guideJoints, worldUpAxis=-self.lookVector, reverseAim=self.sideMultiplier, reverseUp=self.sideMultiplier)

        # set orientation of joints

    def define_attributes(self):
        # set joint side and type attributes
        extra.set_joint_type(self.guideJoints[0], "NeckRoot")
        cmds.setAttr("{0}.radius".format(self.guideJoints[0]), 2)
        _ = [extra.set_joint_type(jnt, "Neck") for jnt in self.guideJoints[1:-2]]
        extra.set_joint_type(self.guideJoints[-2], "Head")
        extra.set_joint_type(self.guideJoints[-1], "HeadEnd")
        _ = [extra.set_joint_side(jnt, "C") for jnt in self.guideJoints]

        # ----------Mandatory---------[Start]
        root_jnt = self.guideJoints[0]
        extra.create_global_joint_attrs(root_jnt, upAxis=self.upVector, mirrorAxis=self.mirrorVector, lookAxis=self.lookVector)
        # ----------Mandatory---------[End]

        for attr_dict in LIMB_DATA["properties"]:
            extra.create_attribute(root_jnt, attr_dict)

    def createGuides(self):
        self.draw_joints()
        self.define_attributes()

    def convertJoints(self, joints_list):
        if len(joints_list) < 3:
            FEEDBACK.warning("Define or select at least 3 joints for Finger Guide conversion. Skipping")
            return
        self.guideJoints = joints_list
        self.define_attributes()