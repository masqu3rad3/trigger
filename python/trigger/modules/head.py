from maya import cmds
import maya.api.OpenMaya as om

from trigger.library import functions, joint
from trigger.library import naming
from trigger.library import attribute
from trigger.library import api
from trigger.objects.controller import Controller
from trigger.objects import twist_spline as tspline
from trigger.modules import _module

from trigger.core import filelog

log = filelog.Filelog(logname=__name__, filename="trigger_log")

LIMB_DATA = {
    "members": ["NeckRoot", "Neck", "Head", "Jaw", "HeadEnd"],
    "properties": [
        {
            "attr_name": "resolution",
            "nice_name": "Resolution",
            "attr_type": "long",
            "min_value": 1,
            "max_value": 9999,
            "default_value": 4,
        },
        {
            "attr_name": "dropoff",
            "nice_name": "Drop_Off",
            "attr_type": "float",
            "min_value": 0.1,
            "max_value": 5.0,
            "default_value": 1.0,
        },
        {
            "attr_name": "twistType",
            "nice_name": "Twist_Type",
            "attr_type": "enum",
            "enum_list": "regular:infinite",
            "default_value": 0,
        },
        {
            "attr_name": "mode",
            "nice_name": "Mode",
            "attr_type": "enum",
            "enum_list": "equalDistance:sameDistance",
            "default_value": 0,
        },
        {
            "attr_name": "stretchyHead",
            "nice_name": "Stretchy_Head",
            "attr_type": "bool",
            "default_value": False,
        },
    ],
    "multi_guide": "Neck",
    "sided": False,
}


class Head(_module.ModuleCore):
    def __init__(self, build_data=None, inits=None):
        super(Head, self).__init__()
        if build_data:
            _neck_segments = build_data.get("Neck", [])
            self.neckNodes = [build_data["NeckRoot"]] + _neck_segments

            self.headStart = build_data["Head"]
            self.headEnd = build_data["HeadEnd"]
            self.inits = self.neckNodes + [self.headStart, self.headEnd]
        elif inits:
            if len(inits) < 2:
                cmds.error("Some or all Neck and Head Bones are missing (or Renamed)")
                return
            self.inits = inits
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
        self.up_axis, self.mirror_axis, self.look_axis = joint.get_rig_axes(
            self.neckNodes[0]
        )

        # get properties
        self.useRefOrientation = cmds.getAttr("%s.useRefOri" % self.neckNodes[0])
        self.resolution = int(cmds.getAttr("%s.resolution" % self.neckNodes[0]))
        self.dropoff = float(cmds.getAttr("%s.dropoff" % self.neckNodes[0]))
        self.splineMode = cmds.getAttr("%s.mode" % self.neckNodes[0], asString=True)
        self.twistType = cmds.getAttr("%s.twistType" % self.neckNodes[0], asString=True)
        self.side = joint.get_joint_side(self.neckNodes[0])
        self.sideMult = -1 if self.side == "R" else 1
        self.stretchyHead = cmds.getAttr("%s.stretchyHead" % self.neckNodes[0])

        # initialize suffix
        self.module_name = naming.unique_name(
            cmds.getAttr("%s.moduleName" % self.neckNodes[0])
        )

        # module variables
        self.guideJoints = []
        self.cont_neck = None
        self.cont_neck_ORE = None
        self.cont_head = None
        self.cont_headSquash = None
        self.neckRootLoc = None

    def create_joints(self):
        # Create Limb Plug
        cmds.select(clear=True)
        self.limbPlug = cmds.joint(
            name=naming.parse([self.module_name, "plug"], suffix="j"),
            position=self.root_pos,
            radius=3,
        )

        # Create temporaray Guide Joints
        cmds.select(clear=True)
        self.guideJoints = [
            cmds.joint(
                name=naming.parse([self.module_name, i], suffix="jTemp"),
                position=api.get_world_translation(i),
            )
            for i in self.neckNodes
        ]
        self.guideJoints.append(
            cmds.joint(
                name=naming.parse([self.module_name, "head"], suffix="jTemp"),
                position=self.headPivPos,
            )
        )
        self.guideJoints.append(
            cmds.joint(
                name=naming.parse([self.module_name, "headEnd"], suffix="jTemp"),
                position=self.headEndPivPos,
            )
        )

        # orientations
        if not self.useRefOrientation:
            joint.orient_joints(
                self.guideJoints,
                world_up_axis=self.look_axis,
                up_axis=(0, 1, 0),
                reverse_aim=self.sideMult,
                reverse_up=self.sideMult,
            )
        else:
            for x in range(len(self.guideJoints[:-2])):
                functions.align_to(
                    self.guideJoints[x], self.neckNodes[x], position=True, rotation=True
                )
                cmds.makeIdentity(self.guideJoints[x], apply=True)
            functions.align_to(
                self.guideJoints[-2], self.headStart, position=True, rotation=True
            )
            cmds.makeIdentity(self.guideJoints[-2], apply=True)
            functions.align_to(
                self.guideJoints[-1], self.headEnd, position=True, rotation=True
            )
            cmds.makeIdentity(self.guideJoints[-1], apply=True)

    def create_controllers(self):
        # Neck Controller
        neck_scale = (self.neckDist / 2, self.neckDist / 2, self.neckDist / 2)
        self.cont_neck = Controller(
            name=naming.parse([self.module_name, "neck"], suffix="cont"),
            shape="CurvedCircle",
            scale=neck_scale,
            normal=(1, 0, 0),
            side=self.side,
            tier="primary",
        )
        self.controllers.append(self.cont_neck)
        functions.align_to_alter(self.cont_neck.name, self.guideJoints[0], mode=2)
        self.cont_neck_ORE = self.cont_neck.add_offset("ORE")

        # Head Controller
        self.cont_head = Controller(
            name=naming.parse([self.module_name, "head"], suffix="cont"),
            shape="HalfDome",
            scale=(self.headDist, self.headDist, self.headDist),
            normal=(0, 1, 0),
            side=self.side,
            tier="primary",
        )
        self.controllers.append(self.cont_head)

        functions.align_to_alter(self.cont_head.name, self.guideJoints[-2], mode=2)
        self.cont_IK_OFF = self.cont_head.add_offset("OFF")
        cont_head_ore = self.cont_head.add_offset("ORE")

        if self.stretchyHead:
            # Head Squash Controller
            self.cont_headSquash = Controller(
                name=naming.parse([self.module_name, "headSquash"], suffix="cont"),
                shape="Circle",
                scale=(self.headDist / 2, self.headDist / 2, self.headDist / 2),
                normal=(0, 1, 0),
                side=self.side,
                tier="secondary",
            )
            self.controllers.append(self.cont_headSquash)
            functions.align_to_alter(self.cont_headSquash.name, self.guideJoints[-1])
            cont_head_squash_ore = self.cont_headSquash.add_offset("ORE")
            cmds.parent(cont_head_squash_ore, self.cont_head.name)
            cmds.connectAttr(
                "%s.contVis" % self.scaleGrp, "%s.v" % self.cont_headSquash.name
            )

        cmds.parent(self.cont_IK_OFF, self.limbGrp)
        cmds.parent(self.cont_neck_ORE, self.scaleGrp)

        cmds.connectAttr("%s.contVis" % self.scaleGrp, "%s.v" % cont_head_ore)
        cmds.connectAttr("%s.contVis" % self.scaleGrp, "%s.v" % self.cont_neck_ORE)

    def create_roots(self):
        self.neckRootLoc = cmds.spaceLocator(
            name=naming.parse([self.module_name, "neckRoot"], suffix="loc")
        )[0]
        functions.align_to_alter(self.neckRootLoc, self.guideJoints[0])

        cmds.parent(self.neckRootLoc, self.scaleGrp)

    def create_ik_setup(self):
        # create spline IK for neck
        neck_spline = tspline.TwistSpline()
        neck_spline.upAxis = -(om.MVector(self.look_axis))

        neck_spline.create_t_spline(
            list(self.guideJoints[:-1]),
            "neckSplineIK_%s" % self.module_name,
            self.resolution,
            dropoff=self.dropoff,
            mode=self.splineMode,
            twistType=self.twistType,
        )
        self.sockets.extend(
            neck_spline.defJoints[:-1]
        )  # do not add the last neck spline joint to the socket list

        # # Connect neck start to the neck controller
        cmds.orientConstraint(
            self.cont_neck.name, neck_spline.contCurve_Start, maintainOffset=False
        )
        cmds.pointConstraint(
            neck_spline.contCurve_Start, self.cont_neck_ORE, maintainOffset=False
        )
        # # Connect neck end to the head controller
        cmds.parentConstraint(
            self.cont_head.name, neck_spline.contCurve_End, maintainOffset=True
        )
        # # pass Stretch controls from the splineIK to neck controller
        attribute.attribute_pass(neck_spline.attPassCont, self.cont_neck.name)

        # # Connect the scale to the scaleGrp
        cmds.connectAttr("%s.scale" % self.scaleGrp, "%s.scale" % neck_spline.scaleGrp)
        # bring out contents.
        attribute.attribute_pass(
            neck_spline.scaleGrp,
            self.scaleGrp,
            attributes=["sx", "sy", "sz"],
            keepSourceAttributes=True,
        )
        cmds.disconnectAttr(
            cmds.listConnections(neck_spline.scaleGrp, plugs=True)[0],
            "%s.scale" % neck_spline.scaleGrp,
        )

        # create spline IK for Head squash
        if self.stretchyHead:
            head_spline = tspline.TwistSpline()
            head_spline.upAxis = -(om.MVector(self.look_axis))
            head_spline.create_t_spline(
                list(self.guideJoints[-2:]),
                "headSquashSplineIK_%s" % self.module_name,
                3,
                dropoff=2,
                mode=self.splineMode,
                twistType=self.twistType,
            )
            # map(self.sockets.append, headSpline.defJoints)
            self.sockets.extend(head_spline.defJoints)

            # # Position the head spline IK to end of the neck
            cmds.pointConstraint(
                neck_spline.endLock, head_spline.contCurve_Start, maintainOffset=False
            )

            # # orient the head spline to the head controller
            # TODO // FIX HERE
            cmds.orientConstraint(
                self.cont_head.name, head_spline.contCurve_Start, maintainOffset=True
            )

            functions.align_to_alter(
                self.cont_headSquash.name, head_spline.contCurve_End, mode=2
            )
            # TODO // FIX HERE
            cmds.parentConstraint(
                self.cont_headSquash.name,
                head_spline.contCurve_End,
                maintainOffset=True,
            )
            attribute.attribute_pass(head_spline.attPassCont, self.cont_headSquash.name)

            # # Connect the scale to the scaleGrp
            cmds.connectAttr(
                "%s.scale" % self.scaleGrp, "%s.scale" % head_spline.scaleGrp
            )
            # bring out contents.
            attribute.attribute_pass(
                head_spline.scaleGrp,
                self.scaleGrp,
                attributes=["sx", "sy", "sz"],
                keepSourceAttributes=True,
            )
            cmds.disconnectAttr(
                cmds.listConnections(head_spline.scaleGrp, plugs=True)[0],
                "%s.scale" % head_spline.scaleGrp,
            )
            self.deformerJoints.extend(head_spline.defJoints)
        else:
            head_joint = cmds.joint(
                name=naming.parse([self.module_name, "head"], suffix="jDef"),
                position=self.headPivPos,
                radius=3,
            )
            head_joint_end = cmds.joint(
                name=naming.parse([self.module_name, "headEnd"], suffix="jDef"),
                position=self.headEndPivPos,
                radius=3,
            )
            cmds.parent(head_joint, self.scaleGrp)
            self.sockets.append(head_joint)
            self.sockets.append(head_joint_end)
            cmds.pointConstraint(neck_spline.endLock, head_joint, maintainOffset=False)
            cmds.orientConstraint(self.cont_head.name, head_joint, maintainOffset=True)
            self.deformerJoints.extend([head_joint, head_joint_end])

        cmds.parentConstraint(self.limbPlug, self.neckRootLoc, maintainOffset=True)

        # ########### FOR LONG NECKS ##############

        mid_controls = []

        for m in range(0, len(neck_spline.contCurves_ORE)):
            if 0 < m < len(neck_spline.contCurves_ORE):
                mid_controls.append(neck_spline.contCurves_ORE[m])

                o_con = cmds.parentConstraint(
                    self.cont_head.name,
                    self.cont_neck.name,
                    neck_spline.contCurves_ORE[m],
                    maintainOffset=True,
                )[0]
                blend_ratio = (m + 0.0) / len(neck_spline.contCurves_ORE)
                cmds.setAttr(
                    "{0}.{1}W0".format(o_con, self.cont_head.name), blend_ratio
                )
                cmds.setAttr(
                    "{0}.{1}W1".format(o_con, self.cont_neck.name), 1 - blend_ratio
                )

        self.deformerJoints.extend(neck_spline.defJoints)

        cmds.parent(neck_spline.contCurves_ORE, self.scaleGrp)
        cmds.parent(neck_spline.contCurves_ORE[0], self.neckRootLoc)
        try:
            cmds.parent(
                neck_spline.contCurves_ORE[len(neck_spline.contCurves_ORE) - 1],
                self.scaleGrp,
            )
        except RuntimeError:
            pass
        cmds.parent(neck_spline.endLock, self.scaleGrp)
        cmds.parent(neck_spline.scaleGrp, self.scaleGrp)

        if self.stretchyHead:
            cmds.parent(head_spline.contCurves_ORE[0], self.scaleGrp)
            try:
                cmds.parent(
                    head_spline.contCurves_ORE[len(head_spline.contCurves_ORE) - 1],
                    self.scaleGrp,
                )
            except RuntimeError:
                pass
            cmds.parent(head_spline.endLock, self.scaleGrp)
            cmds.parent(head_spline.scaleGrp, self.scaleGrp)
            cmds.parent(head_spline.nonScaleGrp, self.nonScaleGrp)

        cmds.parent(neck_spline.nonScaleGrp, self.nonScaleGrp)
        attribute.drive_attrs(
            "%s.contVis" % self.scaleGrp, ["%s.v" % x for x in mid_controls]
        )
        attribute.drive_attrs(
            "%s.jointVis" % self.scaleGrp, ["%s.v" % x for x in self.deformerJoints]
        )

        if self.stretchyHead:
            cmds.connectAttr(
                "%s.rigVis" % self.scaleGrp,
                "%s.v" % head_spline.contCurves_ORE[0],
                force=True,
            )
            cmds.connectAttr(
                "%s.rigVis" % self.scaleGrp,
                "%s.v" % head_spline.contCurves_ORE[-1],
                force=True,
            )
        cmds.connectAttr(
            "%s.rigVis" % self.scaleGrp,
            "%s.v" % neck_spline.contCurves_ORE[0],
            force=True,
        )
        cmds.connectAttr(
            "%s.rigVis" % self.scaleGrp,
            "%s.v" % neck_spline.contCurves_ORE[-1],
            force=True,
        )
        cmds.connectAttr(
            "%s.rigVis" % self.scaleGrp, "%s.v" % self.neckRootLoc, force=True
        )

        if self.stretchyHead:
            for lst in head_spline.noTouchData:
                attribute.drive_attrs(
                    "%s.rigVis" % self.scaleGrp, ["%s.v" % x for x in lst]
                )

        for lst in neck_spline.noTouchData:
            attribute.drive_attrs(
                "%s.rigVis" % self.scaleGrp, ["%s.v" % x for x in lst]
            )

    def round_up(self):
        self.scaleConstraints.append(self.cont_IK_OFF)
        self.anchorLocations = [self.cont_neck.name, self.cont_head.name]
        self.anchors = [
            (self.cont_head.name, "point", 5, None),
            (self.cont_head.name, "orient", 1, None),
            (self.cont_neck.name, "orient", 4, [self.cont_head.name]),
        ]
        cmds.delete(self.guideJoints)

        for cont in self.controllers:
            cont.set_defaults()

    def execute(self):
        self.create_joints()
        self.create_controllers()
        self.create_roots()
        self.create_ik_setup()
        self.round_up()


class Guides(_module.GuidesCore):
    limb_data = LIMB_DATA

    def __init__(self, *args, **kwargs):
        super(Guides, self).__init__(*args, **kwargs)
        self.segments = kwargs.get(
            "segments", 1
        )  # minimum segments required for the module

    def draw_joints(self):
        r_point_neck = om.MVector(0, 25.757, 0) * self.tMatrix
        n_point_neck = om.MVector(0, 29.418, 0.817) * self.tMatrix
        point_head = om.MVector(0, 32, 0.817) * self.tMatrix
        add_neck = (n_point_neck - r_point_neck) / ((self.segments + 1) - 1)

        # Define the offset vector
        self.offsetVector = (n_point_neck - r_point_neck).normal()

        # Draw the joints
        for seg in range(self.segments):
            neck_jnt = cmds.joint(
                position=(r_point_neck + (add_neck * seg)),
                name=naming.parse(
                    [self.name, "neck", seg], side=self.side, suffix="jInit"
                ),
            )
            self.guideJoints.append(neck_jnt)
        for seg in range(1):
            head_jnt = cmds.joint(
                position=(r_point_neck + (add_neck * (seg + self.segments))),
                name=naming.parse(
                    [self.name, "head", seg], side=self.side, suffix="jInit"
                ),
            )
            self.guideJoints.append(head_jnt)
        headEnd = cmds.joint(
            position=point_head,
            name=naming.parse([self.name, "headEnd"], side=self.side, suffix="jInit"),
        )
        self.guideJoints.append(headEnd)

        # Update the guideJoints list
        joint.orient_joints(
            self.guideJoints,
            world_up_axis=-self.lookVector,
            reverse_aim=self.sideMultiplier,
            reverse_up=self.sideMultiplier,
        )

        # set orientation of joints

    def define_guides(self):
        """Override the guide definition method"""
        joint.set_joint_type(self.guideJoints[0], "NeckRoot")
        cmds.setAttr("{0}.radius".format(self.guideJoints[0]), 2)
        _ = [joint.set_joint_type(jnt, "Neck") for jnt in self.guideJoints[1:-2]]
        joint.set_joint_type(self.guideJoints[-2], "Head")
        joint.set_joint_type(self.guideJoints[-1], "HeadEnd")
