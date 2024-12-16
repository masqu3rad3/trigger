from maya import cmds
import maya.api.OpenMaya as om
from trigger.library import api, joint
from trigger.library import functions, connection
from trigger.library import naming
from trigger.library import attribute
from trigger.objects.controller import Controller
from trigger.core.module import ModuleCore, GuidesCore

from trigger.core import filelog

LOG = filelog.Filelog(logname=__name__, filename="trigger_log")

LIMB_DATA = {
    "members": ["EyeRoot", "EyeAim", "EyePupil"],
    "properties": [
        {
            "attr_name": "localJoints",
            "nice_name": "Local_Joints",
            "attr_type": "bool",
            "default_value": False,
        },
        {
            "attr_name": "groupID",
            "nice_name": "Group_ID",
            "attr_type": "long",
            "min_value": 0,
            "max_value": 9999,
            "default_value": 1,
        },
    ],
    "multi_guide": None,
    "sided": True,
}


class Eye(ModuleCore):
    name = "Eye"
    def __init__(self, build_data=None, inits=None):
        super(Eye, self).__init__()
        # fool proofing

        # reinitialize the initial Joints
        if build_data:
            eye_root = build_data.get("EyeRoot")
            eye_aim = build_data.get("EyeAim")
            eye_pupil = build_data.get("EyePupil")
            self.inits = [eye_root, eye_aim, eye_pupil]
        elif inits:
            if len(inits) != 3:
                LOG.error("Eye Module needs exactly 3 initial joints (EyeRoot, EyeAim, EyePupil)")
                return
            self.inits = inits
            # parse inits
        else:
            LOG.error("Class needs either build_data or inits to be constructed")

        # get the properties from the root
        self.useRefOrientation = cmds.getAttr("%s.useRefOri" % self.inits[0])
        self.side = joint.get_joint_side(self.inits[0])
        self.sideMult = -1 if self.side == "R" else 1
        self.isLocal = bool(cmds.getAttr("%s.localJoints" % self.inits[0]))
        self.groupID = int(cmds.getAttr("%s.groupID" % self.inits[0]))

        # initialize coordinates
        self.up_axis, self.mirror_axis, self.look_axis = joint.get_rig_axes(
            self.inits[0]
        )

        # initialize suffix
        self.module_name = naming.unique_name(
            cmds.getAttr("%s.moduleName" % self.inits[0])
        )

        # module variables
        self.aim_bridge = None
        self.aim_cont = None
        self.aimDriven = None
        self.directDriven = None
        self.aimContGroupFollow = None
        self.plugDriven = None
        self.controllerGrp = None
        self.other_eye_conts = []
        self.group_cont = None

    def additional_groups(self):
        """Create additional groups for the module"""

        if self.groupID:
            functions.validate_group("Eye_group%i" % self.groupID)
            cmds.parent(self.limbGrp, "Eye_group%i" % self.groupID)
            self.limbGrp = "Eye_group%i" % self.groupID
            c_shapes = cmds.listRelatives(
                "Eye_group%i" % self.groupID,
                allDescendents=True,
                children=True,
                allParents=False,
                type="nurbsCurve",
            )
            if c_shapes:
                self.other_eye_conts = [
                    Controller(functions.get_parent(shape)) for shape in c_shapes
                ]

            if cmds.objExists("Eye_group_%i_cont" % self.groupID):
                self.group_cont = Controller("Eye_group_%i_cont" % self.groupID)
                for cont in self.other_eye_conts:
                    if self.group_cont.name == cont.name:
                        self.other_eye_conts.remove(cont)
                        break

    def create_joints(self):
        cmds.select(clear=True)
        self.limbPlug = cmds.joint(
            name=naming.parse([self.module_name, "plug"], suffix="j"),
            position=api.get_world_translation(self.inits[0]),
            radius=3,
        )

        cmds.select(clear=True)
        eye_jnt = cmds.joint(
            name=naming.parse([self.module_name, "eye"], suffix="jDef")
        )
        functions.align_to(eye_jnt, self.inits[0])
        # for backward compatibility purposes, don't create the pupil joint if its not in the data
        if self.inits[2]:
            pupil_jnt = cmds.joint(
                name=naming.parse([self.module_name, "pupil"], suffix="jDef")
            )
            functions.align_to(pupil_jnt, self.inits[2])
        eye_offset = functions.create_offset_group(eye_jnt, "OFF")
        self.plugDriven = functions.create_offset_group(eye_jnt, "PLUG_DRIVEN")
        self.aimDriven = functions.create_offset_group(eye_jnt, "AIM")
        self.directDriven = functions.create_offset_group(eye_jnt, "DIRECT")
        self.sockets.append(eye_jnt)
        self.deformerJoints.append(eye_jnt)

        if not self.useRefOrientation:
            joint.orient_joints(
                self.deformerJoints,
                world_up_axis=self.look_axis,
                up_axis=(0, 1, 0),
                reverse_aim=self.sideMult,
                reverse_up=self.sideMult,
            )

        cmds.parent(eye_offset, self.defJointsGrp)

    def create_controllers(self):
        self.aim_bridge = cmds.spaceLocator(
            name=naming.parse([self.module_name, "aim"], suffix="brg")
        )[0]
        attribute.drive_attrs("%s.rigVis" % self.scaleGrp, "%s.v" % self.aim_bridge)
        self.aim_cont = Controller(
            shape="Circle",
            name=naming.parse([self.module_name, "aim"], suffix="cont"),
            scale=(1, 1, 1),
            normal=(0, 0, 1),
        )
        self.controllers.append(self.aim_cont)

        self.other_eye_conts.append(self.aim_cont)

        functions.align_to(self.aim_bridge, self.inits[1], position=True, rotation=True)
        functions.align_to(
            self.aim_cont.name, self.inits[1], position=True, rotation=True
        )

        aim_cont_off = self.aim_cont.add_offset("OFF")
        self.aimContGroupFollow = self.aim_cont.add_offset("GroupFollow")

        cmds.parent(self.aim_bridge, self.nonScaleGrp)

        cmds.parent(aim_cont_off, self.controllerGrp)

        if self.groupID:
            if not self.group_cont:
                self.group_cont = Controller(
                    shape="Circle",
                    name=naming.parse(["Eye_group", self.groupID], suffix="cont"),
                    scale=(2, 2, 2),
                    normal=(0, 0, 1),
                )
                self.group_cont.set_side("C", tier=0)
                attribute.drive_attrs(
                    "%s.contVis" % self.scaleGrp, "%s.v" % self.group_cont.name
                )
                cmds.delete(
                    cmds.pointConstraint(
                        [x.name for x in self.other_eye_conts],
                        self.group_cont.name,
                        maintainOffset=False,
                    )
                )
                group_cont_off = self.group_cont.add_offset("OFF")
                cmds.connectAttr(
                    "{}.scale".format(self.scaleGrp), "{}.scale".format(group_cont_off)
                )
                cmds.parent(group_cont_off, self.limbGrp)
            for cont in self.other_eye_conts:
                g_follow = cont.parent
                _ = [
                    attribute.disconnect_attr(
                        g_follow, attr=attr, suppress_warnings=True
                    )
                    for attr in ["translate", "rotate", "scale"]
                ]
                connection.matrixConstraint(
                    self.group_cont.name, g_follow, maintainOffset=True
                )
            else:
                # if the group controller exists, update only its shape and rotation pivot
                # adjust the pivot
                cmds.xform(
                    self.group_cont.name,
                    absolute=True,
                    worldSpace=True,
                    pivots=api.get_center([x.name for x in self.other_eye_conts]),
                )
                cmds.xform(
                    self.group_cont.parent,
                    absolute=True,
                    worldSpace=True,
                    pivots=api.get_center([x.name for x in self.other_eye_conts]),
                )

                bb = cmds.exactWorldBoundingBox(*[x.name for x in self.other_eye_conts])
                x_dist = abs(bb[0] - bb[3])
                y_dist = abs(bb[1] - bb[4])
                z_dist = abs(bb[2] - bb[5])
                self.group_cont.set_shape(
                    "Circle", scale=(x_dist, z_dist, y_dist), normal=(0, 0, 1)
                )

                self.anchors = [(self.group_cont.name, "parent", 1, None)]
                pass
        else:
            self.anchors = [(self.aim_cont.name, "parent", 1, None)]

        attribute.drive_attrs(
            "%s.contVis" % self.scaleGrp, ["%s.v" % x.name for x in self.controllers]
        )

    def create_connections(self):
        _aim_con = cmds.aimConstraint(
            self.aim_bridge,
            self.aimDriven,
            upVector=self.up_axis,
            aimVector=self.look_axis,
            worldUpType="objectrotation",
            worldUpObject=self.limbPlug,
        )

        connection.matrixConstraint(
            self.aim_cont.name,
            self.aim_bridge,
            maintainOffset=False,
            source_parent_cutoff=self.localOffGrp,
        )

        if self.isLocal:
            connection.matrixConstraint(self.limbPlug, self.plugBindGrp)
        else:
            connection.matrixConstraint(self.limbPlug, self.plugDriven)

    def round_up(self):
        _ = [
            cmds.connectAttr("%s.jointVis" % self.scaleGrp, "%s.v" % x)
            for x in self.deformerJoints
        ]

    def execute(self):
        self.create_joints()
        self.create_controllers()
        self.create_connections()
        self.round_up()


class Guides(GuidesCore):
    name = "Eye"
    limb_data = LIMB_DATA

    def draw_joints(self):
        if self.side == "C":
            root_point = om.MVector(0, 0, 0)
            pupil_point = om.MVector(0, 0, 1) * self.tMatrix
            aim_point = om.MVector(0, 0, 10) * self.tMatrix
            self.offsetVector = om.MVector(0, 0, 10) * self.tMatrix
            # pass
        else:
            root_point = om.MVector(2 * self.sideMultiplier, 0, 0) * self.tMatrix
            pupil_point = om.MVector(2 * self.sideMultiplier, 0, 1) * self.tMatrix
            aim_point = om.MVector(2 * self.sideMultiplier, 0, 10) * self.tMatrix
            self.offsetVector = (
                om.MVector(2 * self.sideMultiplier, 0, 10) * self.tMatrix
            )
            # pass

        # Draw the joints
        cmds.select(clear=True)
        root_jnt = cmds.joint(
            name=naming.parse([self.name, "root"], side=self.side, suffix="jInit"),
            position=root_point,
        )

        pupil_jnt = cmds.joint(
            name=naming.parse([self.name, "pupil"], side=self.side, suffix="jInit"),
            position=pupil_point,
        )

        cmds.select(clear=True)
        aim_jnt = cmds.joint(
            name=naming.parse([self.name, "aim"], side=self.side, suffix="jInit"),
            position=aim_point,
        )
        cmds.parent(aim_jnt, root_jnt)

        # Update the guideJoints list
        self.guideJoints.append(root_jnt)
        self.guideJoints.append(aim_jnt)
        self.guideJoints.append(pupil_jnt)


    def define_guides(self):
        """Override the guide definition method"""
        joint.set_joint_type(self.guideJoints[0], "EyeRoot")
        joint.set_joint_type(self.guideJoints[1], "EyeAim")
        joint.set_joint_type(self.guideJoints[2], "EyePupil")
