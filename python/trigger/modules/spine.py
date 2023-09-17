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
    "members": ["SpineRoot", "Spine", "SpineEnd"],
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
    ],
    "multi_guide": "Spine",
    "sided": False,
}


class Spine(_module.ModuleCore):
    def __init__(self, build_data=None, inits=None):
        super(Spine, self).__init__()
        if build_data:
            s_root = build_data.get("SpineRoot")
            try:
                self.spines = reversed(build_data.get("Spine"))
                self.spineEnd = build_data.get("SpineEnd")
                self.inits = [s_root] + sorted(self.spines) + [self.spineEnd]
            except:  # pylint: disable=bare-except
                self.spineEnd = build_data.get("SpineEnd")
                self.inits = [s_root] + [self.spineEnd]
        elif inits:
            # fool proofing
            if len(inits) < 2:
                cmds.error("Insufficient Spine Initialization Joints")
                return
            self.inits = inits

        else:
            log.error("Class needs either build_data or arminits to be constructed")

        # get positions
        self.rootPoint = api.get_world_translation(self.inits[0])
        self.chestPoint = api.get_world_translation(self.inits[-1])

        # initialize coordinates
        self.up_axis, self.mirror_axis, self.look_axis = joint.get_rig_axes(
            self.inits[0]
        )

        # get the properties from the root
        self.useRefOrientation = cmds.getAttr("%s.useRefOri" % self.inits[0])
        self.resolution = int(cmds.getAttr("%s.resolution" % self.inits[0]))
        self.dropoff = float(cmds.getAttr("%s.dropoff" % self.inits[0]))
        self.splineMode = cmds.getAttr("%s.mode" % self.inits[0], asString=True)
        self.twistType = cmds.getAttr("%s.twistType" % self.inits[0], asString=True)
        self.side = joint.get_joint_side(self.inits[0])
        self.sideMult = -1 if self.side == "R" else 1

        # initialize suffix
        self.module_name = naming.unique_name(
            cmds.getAttr("%s.moduleName" % self.inits[0])
        )

        # module variables
        self.endSocket = None
        self.startSocket = None
        self.guideJoints = None
        self.cont_hips = None
        self.cont_chest = None
        self.cont_body = None

    def create_joints(self):
        # draw Joints
        # # Create Plug Joints
        cmds.select(clear=True)
        self.limbPlug = cmds.joint(
            name=naming.parse([self.module_name, "plug"], suffix="j"),
            position=self.rootPoint,
            radius=3,
        )
        cmds.select(clear=True)
        self.endSocket = cmds.joint(
            name=naming.parse([self.module_name, "socket", "chest"], suffix="jDef"),
            position=self.chestPoint,
        )
        self.sockets.append(self.endSocket)
        cmds.select(clear=True)
        self.startSocket = cmds.joint(
            position=self.rootPoint,
            name=naming.parse([self.module_name, "socket", "root"], suffix="jDef"),
            radius=3,
        )
        self.sockets.append(self.startSocket)

        # Create temporary Guide Joints
        cmds.select(clear=True)
        self.guideJoints = [
            cmds.joint(position=api.get_world_translation(i)) for i in self.inits
        ]

        if not self.useRefOrientation:
            joint.orient_joints(
                self.guideJoints,
                world_up_axis=self.up_axis,
                up_axis=(0, 0, -1),
                reverse_aim=self.sideMult,
                reverse_up=self.sideMult,
            )
        else:
            for x in range(len(self.guideJoints)):
                functions.align_to(
                    self.guideJoints[x], self.inits[x], position=True, rotation=True
                )
                cmds.makeIdentity(self.guideJoints[x], apply=True)

        self.deformerJoints.append(self.startSocket)
        self.deformerJoints.append(self.endSocket)

        functions.align_to_alter(self.limbPlug, self.guideJoints[0], mode=2)

        cmds.parent(self.startSocket, self.scaleGrp)
        cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % self.limbPlug)

    def create_controllers(self):
        """Create the controllers for the module"""
        # Hips Controller
        icon_size = functions.get_distance(self.inits[0], self.inits[-1])
        cont_hips_scale = (icon_size / 1.5, icon_size / 1.5, icon_size / 1.5)
        self.cont_hips = Controller(
            name=naming.parse([self.module_name, "hips"], suffix="cont"),
            shape="Waist",
            scale=cont_hips_scale,
            normal=(1, 0, 0),
            side=self.side,
            tier="primary",
        )
        self.controllers.append(self.cont_hips)
        functions.align_to_alter(self.cont_hips.name, self.guideJoints[0], mode=2)
        cont_hips_ore = self.cont_hips.add_offset("ORE")

        # Body Controller
        cont_body_scale = (icon_size * 0.75, icon_size * 0.75, icon_size * 0.75)
        self.cont_body = Controller(
            name=naming.parse([self.module_name, "body"], suffix="cont"),
            shape="Square",
            scale=cont_body_scale,
            normal=(1, 0, 0),
            side=self.side,
            tier="primary",
        )
        self.controllers.insert(0, self.cont_body)
        functions.align_to_alter(self.cont_body.name, self.guideJoints[0], mode=2)
        cont_body_ore = self.cont_body.add_offset("POS")
        self.scaleConstraints.append(cont_body_ore)

        # create visibility attributes for cont_Body
        cmds.addAttr(
            self.cont_body.name,
            attributeType="bool",
            longName="FK_A_Visibility",
            shortName="fkAvis",
            defaultValue=True,
        )
        cmds.addAttr(
            self.cont_body.name,
            attributeType="bool",
            longName="FK_B_Visibility",
            shortName="fkBvis",
            defaultValue=True,
        )
        cmds.addAttr(
            self.cont_body.name,
            attributeType="bool",
            longName="Tweaks_Visibility",
            shortName="tweakVis",
            defaultValue=True,
        )
        # make the created attributes visible in the channelbox
        cmds.setAttr("{}.fkAvis".format(self.cont_body.name), channelBox=True)
        cmds.setAttr("{}.fkBvis".format(self.cont_body.name), channelBox=True)
        cmds.setAttr("{}.tweakVis".format(self.cont_body.name), channelBox=True)

        # Chest Controller
        cont_chest_scale = (icon_size * 0.5, icon_size * 0.35, icon_size * 0.2)
        self.cont_chest = Controller(
            name=naming.parse([self.module_name, "chest"], suffix="cont"),
            shape="Cube",
            scale=cont_chest_scale,
            normal=(0, 0, 1),
            side=self.side,
            tier="primary",
        )
        self.controllers.append(self.cont_chest)
        functions.align_to_alter(self.cont_chest.name, self.guideJoints[-1], mode=2)
        cont_chest_ore = self.cont_chest.add_offset("ORE")

        cont_spine_fk_a_list = []
        cont_spine_fk_b_list = []
        cont_spine_fk_a_scale = (icon_size / 2, icon_size / 2, icon_size / 2)
        cont_spine_fk_b_scale = (icon_size / 2.5, icon_size / 2.5, icon_size / 2.5)

        for m in range(0, len(self.guideJoints)):
            cont_a = Controller(
                name=naming.parse([self.module_name, "FK", "A", m], suffix="cont"),
                shape="Circle",
                scale=cont_spine_fk_a_scale,
                normal=(1, 0, 0),
                side=self.side,
                tier="primary",
            )
            functions.align_to_alter(cont_a.name, self.guideJoints[m], 2)
            _cont_a_ore = cont_a.add_offset("ORE")
            cont_spine_fk_a_list.append(cont_a)
            cont_b = Controller(
                name=naming.parse([self.module_name, "FK", "B", m], suffix="cont"),
                shape="Ngon",
                scale=cont_spine_fk_b_scale,
                normal=(1, 0, 0),
                side=self.side,
                tier="primary",
            )
            functions.align_to(
                cont_b.name, self.guideJoints[m], position=True, rotation=True
            )
            _cont_b_ore = cont_b.add_offset("ORE")
            cont_spine_fk_b_list.append(cont_b)

            if m != 0:
                a_start_parent = cont_spine_fk_a_list[m].parent
                b_end_parent = cont_spine_fk_b_list[m - 1].parent
                cmds.parent(a_start_parent, cont_spine_fk_a_list[m - 1].name)
                cmds.parent(b_end_parent, cont_spine_fk_b_list[m].name)

        cmds.parent(cont_hips_ore, cont_spine_fk_b_list[0].name)

        cmds.parent(cont_spine_fk_b_list[-1].parent, self.cont_body.name)

        cmds.parent(cont_chest_ore, cont_spine_fk_a_list[-1].name)
        cmds.parent(cont_spine_fk_a_list[0].parent, self.cont_body.name)
        cmds.parent(cont_body_ore, self.limbGrp)

        self.controllers.extend(cont_spine_fk_a_list)
        self.controllers.extend(cont_spine_fk_b_list)

        cmds.parentConstraint(self.limbPlug, cont_body_ore, maintainOffset=False)

        attribute.drive_attrs(
            "%s.fkAvis" % self.cont_body.name,
            ["%s.v" % x.shapes[0] for x in cont_spine_fk_a_list],
        )
        attribute.drive_attrs(
            "%s.fkBvis" % self.cont_body.name,
            ["%s.v" % x.shapes[0] for x in cont_spine_fk_b_list],
        )

        _ = [
            x.lock(["tx", "ty", "tz", "sx", "sy", "sz", "v"])
            for x in cont_spine_fk_a_list
        ]
        _ = [
            x.lock(["tx", "ty", "tz", "sx", "sy", "sz", "v"])
            for x in cont_spine_fk_b_list
        ]

    def create_ik_setup(self):
        spine = tspline.TwistSpline()
        spine.upAxis = -(om.MVector(self.look_axis))
        spine.create_t_spline(
            self.guideJoints,
            "Spine_%s" % self.module_name,
            self.resolution,
            dropoff=self.dropoff,
            mode=self.splineMode,
            twistType=self.twistType,
        )

        self.sockets.extend(spine.defJoints)

        attribute.attribute_pass(
            spine.scaleGrp,
            self.scaleGrp,
            attributes=["sx", "sy", "sz"],
            keepSourceAttributes=True,
        )

        _mid_connection = spine.contCurves_ORE[int((len(spine.contCurves_ORE) / 2))]

        # # connect the spine root to the master root
        cmds.parentConstraint(
            self.startSocket, spine.contCurve_Start, maintainOffset=True
        )

        # # connect the spine end
        cmds.parentConstraint(
            self.cont_chest.name, spine.contCurve_End, maintainOffset=True
        )

        # # connect the master root to the hips controller
        cmds.parentConstraint(
            self.cont_hips.name, self.startSocket, maintainOffset=True
        )
        # # connect upper plug points to the spine and orient it to the chest controller
        cmds.pointConstraint(spine.endLock, self.endSocket)
        cmds.orientConstraint(self.cont_chest.name, self.endSocket)

        # # pass Stretch controls from the splineIK to neck controller
        attribute.attribute_pass(spine.attPassCont, self.cont_chest.name)

        for m in range(len(spine.contCurves_ORE)):
            if 0 < m < len(spine.contCurves_ORE):
                o_con = cmds.parentConstraint(
                    self.cont_chest.name,
                    self.cont_hips.name,
                    spine.contCurves_ORE[m],
                    maintainOffset=True,
                )[0]
                blend_ratio = (m + 0.0) / len(spine.contCurves_ORE)
                cmds.setAttr(
                    "{0}.{1}W0".format(o_con, self.cont_chest.name), blend_ratio
                )
                cmds.setAttr(
                    "{0}.{1}W1".format(o_con, self.cont_hips.name), 1 - blend_ratio
                )

        cmds.parent(spine.contCurves_ORE, spine.scaleGrp)
        cmds.parent(self.endSocket, spine.scaleGrp)
        cmds.parent(spine.endLock, spine.scaleGrp)
        cmds.parent(spine.scaleGrp, self.scaleGrp)

        cmds.parent(spine.nonScaleGrp, self.nonScaleGrp)

        self.deformerJoints += spine.defJoints
        attribute.drive_attrs(
            "%s.jointVis" % self.scaleGrp, ["%s.v" % x for x in self.deformerJoints]
        )

        for i in range(len(spine.contCurves_ORE)):
            if i != 0 or i != len(spine.contCurves_ORE):
                node = functions.create_offset_group(spine.contCurves_ORE[i], "OFF")
                cmds.connectAttr("%s.tweakVis" % self.cont_body.name, "%s.v" % node)
                cmds.connectAttr(
                    "%s.contVis" % self.scaleGrp, "%s.v" % spine.contCurves_ORE[i]
                )
        cmds.connectAttr("%s.contVis" % self.scaleGrp, "%s.v" % self.cont_body.name)

        for lst in spine.noTouchData:
            attribute.drive_attrs(
                "%s.rigVis" % self.scaleGrp, ["%s.v" % x for x in lst]
            )

        # functions.colorize(self.deformerJoints, self.colorCodes[0], shape=False)

    def round_up(self):
        cmds.parentConstraint(self.limbPlug, self.scaleGrp, maintainOffset=False)
        cmds.setAttr("%s.rigVis" % self.scaleGrp, 0)

        self.anchorLocations = [
            self.cont_hips.name,
            self.cont_body.name,
            self.cont_chest.name,
        ]

        cmds.delete(self.guideJoints)
        # lock and hide
        self.cont_body.lock_visibility()
        self.cont_hips.lock(["sx", "sy", "sz", "v"])
        self.cont_chest.lock(["sx", "sy", "sz", "v"])

        for cont in self.controllers:
            cont.set_defaults()

    def execute(self):
        self.create_joints()
        self.create_controllers()
        self.create_ik_setup()
        self.round_up()


class Guides(_module.GuidesCore):
    limb_data = LIMB_DATA

    def __init__(self, *args, **kwargs):
        super(Guides, self).__init__(*args, **kwargs)
        self.segments = kwargs.get(
            "segments", 2
        )  # minimum segments required for the module is two

    def draw_joints(self):
        r_point = om.MVector(0, 14.0, 0) * self.tMatrix
        n_point = om.MVector(0, 21.0, 0) * self.tMatrix
        add = (n_point - r_point) / ((self.segments + 1) - 1)

        # Define the offset vector
        self.offsetVector = (n_point - r_point).normal()

        # Draw the joints & set joint side and type attributes
        for nmb in range(self.segments + 1):
            spine_jnt = cmds.joint(
                position=(r_point + (add * nmb)),
                name=naming.parse([self.name, nmb], side=self.side, suffix="jInit"),
            )
            # Update the guideJoints list
            self.guideJoints.append(spine_jnt)

        # set orientation of joints
        joint.orient_joints(
            self.guideJoints,
            world_up_axis=-self.lookVector,
            reverse_aim=self.sideMultiplier,
            reverse_up=self.sideMultiplier,
        )

    def define_guides(self):
        """Override the guide definition method"""
        joint.set_joint_type(self.guideJoints[0], "SpineRoot")
        _ = [joint.set_joint_type(jnt, "Spine") for jnt in self.guideJoints[1:-1]]
        joint.set_joint_type(self.guideJoints[-1], "SpineEnd")
