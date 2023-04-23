from maya import cmds
import maya.api.OpenMaya as om

from trigger.library import functions, joint
from trigger.library import naming
from trigger.library import attribute
from trigger.library import api
from trigger.objects.controller import Controller
from trigger.objects import twist_spline as twistSpline

from trigger.core import filelog
log = filelog.Filelog(logname=__name__, filename="trigger_log")

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
                       {"attr_name": "stretchyHead",
                        "nice_name": "Stretchy_Head",
                        "attr_type": "bool",
                        "default_value": False,
                        },
                       ],
        "multi_guide": "Neck",
        "sided": False,
    }

## TODO // NEEDS TO SUPPORT DIFFERENT ORIENTATIONS

class Head(object):
    def __init__(self, build_data=None, inits=None, *args, **kwargs):
        super(Head, self).__init__()
        if build_data:
            try:
                self.neckNodes = [build_data["NeckRoot"]] + build_data["Neck"]
            except:
                self.neckNodes = [build_data["NeckRoot"]]
            self.headStart = build_data["Head"]
            self.headEnd = build_data["HeadEnd"]
        elif inits:
            if (len(inits) < 2):
                cmds.error("Some or all Neck and Head Bones are missing (or Renamed)")
                return
            if isinstance(inits, list):
                self.headEnd = inits.pop(-1)
                self.headStart = inits.pop(-1)
                self.neckNodes = list(inits)
        else:
            log.error("Class needs either build_data or arminits to be constructed")

        # get distances
        self.neckDist = functions.get_distance(self.neckNodes[0], self.headStart)
        self.headDist = functions.get_distance(self.headStart, self.headEnd)

        # get positions
        self.root_pos = api.get_world_translation(self.neckNodes[0])
        self.headPivPos = api.get_world_translation(self.headStart)
        self.headEndPivPos = api.get_world_translation(self.headEnd)

        # initialize coordinates
        self.up_axis, self.mirror_axis, self.look_axis = joint.get_rig_axes(self.neckNodes[0])

        # get properties
        self.useRefOrientation = cmds.getAttr("%s.useRefOri" % self.neckNodes[0])
        self.resolution = int(cmds.getAttr("%s.resolution" %self.neckNodes[0]))
        self.dropoff = float(cmds.getAttr("%s.dropoff" %self.neckNodes[0]))
        self.splineMode = cmds.getAttr("%s.mode" %self.neckNodes[0], asString=True)
        self.twistType = cmds.getAttr("%s.twistType" %self.neckNodes[0], asString=True)
        self.side = joint.get_joint_side(self.neckNodes[0])
        self.sideMult = -1 if self.side == "R" else 1
        self.stretchyHead = cmds.getAttr("%s.stretchyHead" % self.neckNodes[0])

        # initialize suffix
        self.suffix = (naming.unique_name(cmds.getAttr("%s.moduleName" % self.neckNodes[0])))

        # scratch variables
        self.controllers = []
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
        self.limbGrp = cmds.group(name=self.suffix, em=True)
        self.scaleGrp = cmds.group(name="%s_scaleGrp" % self.suffix, em=True)
        functions.align_to(self.scaleGrp, self.neckNodes[0], 0)
        self.nonScaleGrp = cmds.group(name="%s_nonScaleGrp" % self.suffix, em=True)

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
        self.guideJoints = [cmds.joint(name="jTemp_%s" %i, p=api.get_world_translation(i)) for i in self.neckNodes]
        self.guideJoints.append(cmds.joint(name="jTemp_Head", p=self.headPivPos))
        self.guideJoints.append(cmds.joint(name="jTemp_HeadEnd", p=self.headEndPivPos))
        ## orientations
        if not self.useRefOrientation:
            joint.orient_joints(self.guideJoints, world_up_axis=(self.look_axis), up_axis=(0, 1, 0), reverse_aim=self.sideMult, reverse_up=self.sideMult)
        else:
            for x in range (len(self.guideJoints[:-2])):
                functions.align_to(self.guideJoints[x], self.neckNodes[x], position=True, rotation=True)
                cmds.makeIdentity(self.guideJoints[x], a=True)
            functions.align_to(self.guideJoints[-2], self.headStart, position=True, rotation=True)
            cmds.makeIdentity(self.guideJoints[-2], a=True)
            functions.align_to(self.guideJoints[-1], self.headEnd, position=True, rotation=True)
            cmds.makeIdentity(self.guideJoints[-1], a=True)

    def createControllers(self):
        ## Neck Controller
        neckScale = (self.neckDist / 2, self.neckDist / 2, self.neckDist / 2)
        self.cont_neck = Controller(name="{}_neck_cont".format(self.suffix),
                                    shape="CurvedCircle",
                                    scale=neckScale,
                                    normal=(1, 0, 0),
                                    side=self.side,
                                    tier="primary"
                                    )
        self.controllers.append(self.cont_neck)
        functions.align_to_alter(self.cont_neck.name, self.guideJoints[0], mode=2)
        self.cont_neck_ORE = self.cont_neck.add_offset("ORE")

        ## Head Controller
        self.cont_head = Controller(name="{}_head_cont".format(self.suffix),
                                    shape="HalfDome",
                                    scale=(self.headDist, self.headDist, self.headDist),
                                    normal=(0, 1, 0),
                                    side=self.side,
                                    tier="primary"
                                    )
        self.controllers.append(self.cont_head)

        functions.align_to_alter(self.cont_head.name, self.guideJoints[-2], mode=2)
        self.cont_IK_OFF = self.cont_head.add_offset("OFF")
        self.cont_head_ORE = self.cont_head.add_offset("ORE")

        if self.stretchyHead:
            ## Head Squash Controller
            self.cont_headSquash = Controller(name="{}_headSquash_cont".format(self.suffix),
                                              shape="Circle",
                                              scale=(self.headDist / 2, self.headDist / 2, self.headDist / 2),
                                              normal=(0, 1, 0),
                                              side=self.side,
                                              tier="secondary",
                                              )
            self.controllers.append(self.cont_headSquash)
            functions.align_to_alter(self.cont_headSquash.name, self.guideJoints[-1])
            cont_headSquash_ORE = self.cont_headSquash.add_offset("ORE")
            cmds.parent(cont_headSquash_ORE, self.cont_head.name)
            cmds.connectAttr("%s.contVis" % self.scaleGrp, "%s.v" % self.cont_headSquash.name)

        cmds.parent(self.cont_IK_OFF, self.limbGrp)
        cmds.parent(self.cont_neck_ORE, self.scaleGrp)

        cmds.connectAttr("%s.contVis" % self.scaleGrp, "%s.v" % self.cont_head_ORE)
        cmds.connectAttr("%s.contVis" % self.scaleGrp, "%s.v" % self.cont_neck_ORE)

    def createRoots(self):
        self.neckRootLoc = cmds.spaceLocator(name="neckRootLoc_%s" % self.suffix)[0]
        functions.align_to_alter(self.neckRootLoc, self.guideJoints[0])

        cmds.parent(self.neckRootLoc, self.scaleGrp)

    def createIKsetup(self):

        # create spline IK for neck
        neckSpline = twistSpline.TwistSpline()
        neckSpline.upAxis = -(om.MVector(self.look_axis))

        neckSpline.createTspline(list(self.guideJoints[:-1]), "neckSplineIK_%s" % self.suffix, self.resolution, dropoff=self.dropoff, mode=self.splineMode, twistType=self.twistType, colorCode=self.colorCodes[1])
        self.sockets.extend(neckSpline.defJoints[:-1]) # do not add the last neck spline joint to the socket list

        # # Connect neck start to the neck controller
        cmds.orientConstraint(self.cont_neck.name, neckSpline.contCurve_Start, maintainOffset=False)
        cmds.pointConstraint(neckSpline.contCurve_Start, self.cont_neck_ORE, maintainOffset=False)
        # # Connect neck end to the head controller
        cmds.parentConstraint(self.cont_head.name, neckSpline.contCurve_End, maintainOffset=True)
        # # pass Stretch controls from the splineIK to neck controller
        attribute.attribute_pass(neckSpline.attPassCont, self.cont_neck.name)

        # # Connect the scale to the scaleGrp
        cmds.connectAttr("%s.scale" % self.scaleGrp, "%s.scale" % neckSpline.scaleGrp)
        # bring out contents.
        attribute.attribute_pass(neckSpline.scaleGrp, self.scaleGrp, attributes=["sx", "sy", "sz"], keepSourceAttributes=True)
        cmds.disconnectAttr(cmds.listConnections(neckSpline.scaleGrp, p=True)[0], "%s.scale" % neckSpline.scaleGrp)

        # create spline IK for Head squash
        if self.stretchyHead:
            headSpline = twistSpline.TwistSpline()
            headSpline.upAxis = -(om.MVector(self.look_axis))
            headSpline.createTspline(list(self.guideJoints[-2:]), "headSquashSplineIK_%s" % self.suffix, 3, dropoff=2,  mode=self.splineMode, twistType=self.twistType, colorCode=self.colorCodes[1])
            # map(self.sockets.append, headSpline.defJoints)
            self.sockets.extend(headSpline.defJoints)

            # # Position the head spline IK to end of the neck
            cmds.pointConstraint(neckSpline.endLock, headSpline.contCurve_Start, mo=False)

            # # orient the head spline to the head controller
            # TODO // FIX HERE
            cmds.orientConstraint(self.cont_head.name, headSpline.contCurve_Start, mo=True)

            functions.align_to_alter(self.cont_headSquash.name, headSpline.contCurve_End, mode=2)
            # TODO // FIX HERE
            cmds.parentConstraint(self.cont_headSquash.name, headSpline.contCurve_End, mo=True)
            attribute.attribute_pass(headSpline.attPassCont, self.cont_headSquash.name)

            # # Connect the scale to the scaleGrp
            cmds.connectAttr("%s.scale" % self.scaleGrp, "%s.scale" % headSpline.scaleGrp)
            # bring out contents.
            attribute.attribute_pass(headSpline.scaleGrp, self.scaleGrp, attributes=["sx", "sy", "sz"], keepSourceAttributes=True)
            cmds.disconnectAttr(cmds.listConnections(headSpline.scaleGrp, plugs=True)[0], "%s.scale" % headSpline.scaleGrp)
            self.deformerJoints.extend(headSpline.defJoints)
        else:
            headJoint = cmds.joint(name="jDef_head_%s" % self.suffix, position=self.headPivPos, radius=3)
            headJoint_end = cmds.joint(name="jDef_headEnd_%s" % self.suffix, position=self.headEndPivPos, radius=3)
            cmds.parent(headJoint, self.scaleGrp)
            self.sockets.append(headJoint)
            self.sockets.append(headJoint_end)
            cmds.pointConstraint(neckSpline.endLock, headJoint, maintainOffset=False)
            cmds.orientConstraint(self.cont_head.name, headJoint, maintainOffset=True)
            self.deformerJoints.extend([headJoint, headJoint_end])

        cmds.parentConstraint(self.limbPlug, self.neckRootLoc, maintainOffset=True)

        ############ FOR LONG NECKS ##############

        midControls = []

        for m in range (0, len(neckSpline.contCurves_ORE)):
            if m > 0 and m < len(neckSpline.contCurves_ORE):
                midControls.append(neckSpline.contCurves_ORE[m])

                oCon = cmds.parentConstraint(self.cont_head.name, self.cont_neck.name, neckSpline.contCurves_ORE[m], mo=True)[0]
                blendRatio = (m + 0.0) / len(neckSpline.contCurves_ORE)
                cmds.setAttr("{0}.{1}W0".format(oCon, self.cont_head.name), blendRatio)
                cmds.setAttr("{0}.{1}W1".format(oCon, self.cont_neck.name), 1 - blendRatio)


        self.deformerJoints.extend(neckSpline.defJoints)

        cmds.parent(neckSpline.contCurves_ORE, self.scaleGrp)
        cmds.parent(neckSpline.contCurves_ORE[0], self.neckRootLoc)
        try:
            cmds.parent(neckSpline.contCurves_ORE[len(neckSpline.contCurves_ORE) - 1], self.scaleGrp)
        except RuntimeError:
            pass
        cmds.parent(neckSpline.endLock, self.scaleGrp)
        cmds.parent(neckSpline.scaleGrp, self.scaleGrp)

        if self.stretchyHead:
            cmds.parent(headSpline.contCurves_ORE[0], self.scaleGrp)
            try:
                cmds.parent(headSpline.contCurves_ORE[len(headSpline.contCurves_ORE) - 1], self.scaleGrp)
            except RuntimeError:
                pass
            cmds.parent(headSpline.endLock, self.scaleGrp)
            cmds.parent(headSpline.scaleGrp, self.scaleGrp)
            cmds.parent(headSpline.nonScaleGrp, self.nonScaleGrp)

        cmds.parent(neckSpline.nonScaleGrp, self.nonScaleGrp)
        attribute.drive_attrs("%s.contVis" % self.scaleGrp, ["%s.v" % x for x in midControls])
        attribute.drive_attrs("%s.jointVis" % self.scaleGrp, ["%s.v" % x for x in self.deformerJoints])

        if self.stretchyHead:
            cmds.connectAttr("%s.rigVis" % self.scaleGrp,"%s.v" % headSpline.contCurves_ORE[0], force=True)
            cmds.connectAttr("%s.rigVis" % self.scaleGrp,"%s.v" % headSpline.contCurves_ORE[-1], force=True)
        cmds.connectAttr("%s.rigVis" % self.scaleGrp,"%s.v" % neckSpline.contCurves_ORE[0], force=True)
        cmds.connectAttr("%s.rigVis" % self.scaleGrp,"%s.v" % neckSpline.contCurves_ORE[-1], force=True)
        cmds.connectAttr("%s.rigVis" % self.scaleGrp,"%s.v" % self.neckRootLoc, force=True)

        if self.stretchyHead:
            for lst in headSpline.noTouchData:
                attribute.drive_attrs("%s.rigVis" % self.scaleGrp, ["%s.v" % x for x in lst])

        for lst in neckSpline.noTouchData:
            attribute.drive_attrs("%s.rigVis" % self.scaleGrp, ["%s.v" % x for x in lst])

        functions.colorize(self.deformerJoints, self.colorCodes[0], shape=False)

    def roundUp(self):
        self.scaleConstraints = [self.scaleGrp, self.cont_IK_OFF]
        self.anchorLocations = [self.cont_neck.name, self.cont_head.name]
        self.anchors = [(self.cont_head.name, "point", 5, None),
                        (self.cont_head.name, "orient", 1, None),
                        (self.cont_neck.name, "orient", 4, [self.cont_head.name])
                        ]
        cmds.delete(self.guideJoints)

        for cont in self.controllers:
            cont.set_defaults()

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

        # Update the guideJoints list
        joint.orient_joints(self.guideJoints, world_up_axis=-self.lookVector, reverse_aim=self.sideMultiplier, reverse_up=self.sideMultiplier)

        # set orientation of joints

    def define_attributes(self):
        # set joint side and type attributes
        joint.set_joint_type(self.guideJoints[0], "NeckRoot")
        cmds.setAttr("{0}.radius".format(self.guideJoints[0]), 2)
        _ = [joint.set_joint_type(jnt, "Neck") for jnt in self.guideJoints[1:-2]]
        joint.set_joint_type(self.guideJoints[-2], "Head")
        joint.set_joint_type(self.guideJoints[-1], "HeadEnd")
        _ = [joint.set_joint_side(jnt, "C") for jnt in self.guideJoints]

        # ----------Mandatory---------[Start]
        root_jnt = self.guideJoints[0]
        attribute.create_global_joint_attrs(root_jnt, moduleName="Head", upAxis=self.upVector, mirrorAxis=self.mirrorVector, lookAxis=self.lookVector)
        # ----------Mandatory---------[End]

        for attr_dict in LIMB_DATA["properties"]:
            attribute.create_attribute(root_jnt, attr_dict)

    def createGuides(self):
        self.draw_joints()
        self.define_attributes()

    def convertJoints(self, joints_list):
        if len(joints_list) < 3:
            log.warning("Define or select at least 3 joints for Finger Guide conversion. Skipping")
            return
        self.guideJoints = joints_list
        self.define_attributes()