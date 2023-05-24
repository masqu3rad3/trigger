from maya import cmds
import maya.api.OpenMaya as om

from trigger.library import functions, joint
from trigger.library import naming
from trigger.library import attribute
from trigger.library import connection
from trigger.library import api
from trigger.objects.controller import Controller
from trigger.modules import _module
from trigger.core import filelog

log = filelog.Filelog(logname=__name__, filename="trigger_log")

LIMB_DATA = {
    "members": ["FingerRoot", "Finger"],
    "properties": [{"attr_name": "fingerType",
                    "nice_name": "Finger_Type",
                    "attr_type": "enum",
                    "enum_list": "Extra:Thumb:Index:Middle:Ring:Pinky:Toe",
                    "default_value": 0,
                    },
                   {"attr_name": "handController",
                    "nice_name": "Hand_Controller",
                    "attr_type": "string",
                    "default_value": "",
                    },
                   ],
    "multi_guide": "Finger",
    "sided": True,
}


class Finger(_module.ModuleCore):
    def __init__(self, build_data=None, inits=None):
        super(Finger, self).__init__()
        if build_data:
            self.fingerRoot = build_data.get("FingerRoot")
            self.fingers = (build_data.get("Finger"))
            self.inits = [self.fingerRoot] + self.fingers
        elif inits:
            # fool proofing
            if len(inits) < 2:
                log.error("Insufficient Finger Initialization Joints")
                return
            self.inits = inits
        else:
            log.error("Class needs either build_data or finger inits to be constructed")

        # hand_controller = cmds.getAttr("%s.handController" % self.inits[0])
        # if hand_controller:
        #     if cmds.objExists(hand_controller):
        #         self.handController = hand_controller
        #     else:
        #         log.warning("Hand Control object %s is not exist. Skipping hand controller" % hand_controller)
        #         self.handController = None
        # else:
        #     self.handController = None

        # initialize coordinates
        self.up_axis, self.mirror_axis, self.look_axis = joint.get_rig_axes(self.inits[0])

        # get the properties from the root
        self.useRefOrientation = cmds.getAttr("%s.useRefOri" % self.inits[0])
        self.fingerType = cmds.getAttr("%s.fingerType" % self.fingerRoot, asString=True)
        self.isThumb = self.fingerType == "Thumb"
        self.side = joint.get_joint_side(self.inits[0])
        self.sideMult = -1 if self.side == "R" else 1
        self.handController = cmds.getAttr("%s.handController" % self.inits[0])

        # initialize suffix
        self.module_name = (
            naming.unique_name("%s_%s" % (cmds.getAttr("%s.moduleName" % self.fingerRoot), self.fingerType)))

        # module variables
        self.contConList = []

    def additional_groups(self):
        """Create additional groups for the module"""

        if self.handController:
            grp_name = naming.parse([self.handController, "Group"])
            functions.validate_group(grp_name)
            # functions.validate_group("Fingers_group%i" % self.groupID)
            cmds.parent(self.limbGrp, grp_name)
            self.limbGrp = grp_name
            # c_shapes = cmds.listRelatives(grp_name, allDescendents=True, children=True,
            #                               allParents=False, type="nurbsCurve")
            # if c_shapes:
            #     self.other_eye_conts = [Controller(functions.get_parent(shape)) for shape in c_shapes]
            # if not cmds.objExists(self.handController):
            #     self.handController = Controller(self.handController, shape="Square", side=self.side)

            # if cmds.objExists("Eye_group_%i_cont" % self.groupID):
            #     self.group_cont = Controller("Eye_group_%i_cont" % self.groupID)
            #     for cont in self.other_eye_conts:
            #         if self.group_cont.name == cont.name:
            #             self.other_eye_conts.remove(cont)
            #             break

    def create_joints(self):

        # Create LimbPlug

        cmds.select(clear=True)

        self.limbPlug = cmds.joint(name=naming.parse([self.module_name, "plug"], suffix="j"),
                                   position=api.get_world_translation(self.inits[0]), radius=2)

        for nmb, guide in enumerate(self.inits):
            # if this is the last one make the suffix "j"
            _suffix = "j" if nmb == len(self.inits) - 1 else "jDef"
            jnt = cmds.joint(name=naming.parse([self.module_name, nmb], suffix=_suffix), radius=1.0)
            functions.align_to(jnt, guide, position=True, rotation=True)
            self.sockets.append(jnt)
            if _suffix == "jDef":
                self.deformerJoints.append(jnt)

        joint.orient_joints(self.deformerJoints, world_up_axis=self.up_axis, up_axis=(0, -1, 0),
                            reverse_aim=self.sideMult,
                            reverse_up=self.sideMult)

        if not self.useRefOrientation:
            joint.orient_joints(self.deformerJoints, world_up_axis=self.up_axis, up_axis=(0, -1, 0),
                                reverse_aim=self.sideMult, reverse_up=self.sideMult)
        else:
            for x in range(len(self.deformerJoints)):
                functions.align_to(self.deformerJoints[x], self.inits[x], position=True, rotation=True)
                cmds.makeIdentity(self.deformerJoints[x], apply=True)

        cmds.parentConstraint(self.limbPlug, self.scaleGrp)
        attribute.drive_attrs("%s.jointVis" % self.scaleGrp, ["%s.v" % x for x in self.deformerJoints])


    def create_controllers(self):

        # Create Controllers

        self.controllers = []
        conts_off = []
        cont_list = []
        self.contConList = []

        for index in range(0, len(self.deformerJoints) - 1):
            cont_scl = (cmds.getAttr("%s.tx" % self.deformerJoints[1]) / 2)
            cont_name = naming.parse([self.module_name, index], suffix="cont")
            cont = Controller(name=cont_name,
                              shape="Circle",
                              scale=(cont_scl, cont_scl, cont_scl),
                              normal=(1, 0, 0),
                              side=self.side,
                              tier="primary"
                              )

            functions.align_to_alter(cont.name, self.deformerJoints[index], mode=2)

            cont_off = cont.add_offset("OFF")
            conts_off.append([cont_off])
            _cont_ORE = cont.add_offset("ORE")
            cont_con = cont.add_offset("con")

            if index > 0:
                cmds.parent(cont_off, self.controllers[len(self.controllers) - 1].name)
            self.controllers.append(cont)
            cont_list.append(cont)
            self.contConList.append(cont_con)

            cmds.parentConstraint(cont.name, self.deformerJoints[index], maintainOffset=True)

        cmds.parent(self.deformerJoints[0], self.scaleGrp)
        cmds.parent(conts_off[0], self.scaleGrp)

        attribute.drive_attrs("%s.contVis" % self.scaleGrp, ["%s.v" % x[0] for x in conts_off])

        if self.handController:
            if cmds.objExists(self.handController):
                self.handController = Controller(self.handController)
            else:
                self.handController = Controller(self.handController, shape="Square", side=self.side)
                _bind = self.handController.add_offset("bind")
                _offset = self.handController.add_offset("OFF")
                connection.matrixConstraint(self.limbPlug, _bind, maintainOffset=False)
                cmds.parent(_bind, self.limbGrp)


    def hand_setup(self):
        """Create the FK setup for the finger."""
        # If there is no parent controller defined, create one. Everyone needs a parent

        if not self.handController:
            return
        # Spread
        spread_attr = "{0}_{1}".format(self.module_name, "Spread")
        cmds.addAttr(self.handController.name, shortName=spread_attr, defaultValue=0.0, attributeType="float", keyable=True)
        # sprMult = cmds.createNode("multiplyDivide", name="sprMult_{0}_{1}".format(self.side, self.module_name))
        spread_mult = cmds.createNode("multDoubleLinear",
                                      name=naming.parse([self.module_name, "spread"], suffix="mult"))
        cmds.setAttr("{}.input1".format(spread_mult), 0.4)
        cmds.connectAttr("{0}.{1}".format(self.handController.name, spread_attr), "{0}.input2".format(spread_mult))
        cmds.connectAttr("{}.output".format(spread_mult), "{0}.rotateY".format(self.contConList[1]))

        # Bend
        # add bend attributes for each joint (except the end joint)
        for nmb in range(0, (len(self.inits) - 1)):
            if nmb == 0 and self.isThumb:
                bend_attr = "{0}{1}".format(self.module_name, "UpDown")
            else:
                bend_attr = "{0}{1}{2}".format(self.module_name, "Bend", nmb)

            cmds.addAttr(self.handController.name, shortName=bend_attr, defaultValue=0.0, attributeType="float",
                         keyable=True)
            cmds.connectAttr("{0}.{1}".format(self.handController.name, bend_attr), "%s.rotateZ" % self.contConList[nmb])

    def round_up(self):
        cmds.setAttr("%s.rigVis" % self.scaleGrp, 0)
        for cont in self.controllers:
            cont.set_defaults()

    def execute(self):
        self.create_joints()
        self.create_controllers()
        self.hand_setup()
        self.round_up()


class Guides(_module.GuidesCore):
    limb_data = LIMB_DATA

    def __init__(self, *args, **kwargs):
        super(Guides, self).__init__(*args, **kwargs)

        self.segments = kwargs.get("segments", 2)  # minimum segments required for the fk/ik module is two

    def draw_joints(self):
        if self.segments < 2:
            log.warning("minimum segments for the fingers are two. current: %s" % self.segments)
            return
        r_point_finger = om.MVector(0, 0, 0) * self.tMatrix
        n_point_finger = om.MVector(5 * self.sideMultiplier, 0, 0) * self.tMatrix
        add_finger = (n_point_finger - r_point_finger) / ((self.segments + 1) - 1)

        # Define the offset vector
        self.offsetVector = (n_point_finger - r_point_finger).normal()

        # Draw the joints
        for seg in range(self.segments + 1):
            finger_jnt = cmds.joint(position=(r_point_finger + (add_finger * seg)),
                                    name=naming.parse([self.name, seg], side=self.side, suffix="jInit"))
            # Update the guideJoints list
            cmds.setAttr("%s.radius" % finger_jnt, 0.5)
            self.guideJoints.append(finger_jnt)

        # set orientation of joints
        joint.orient_joints(self.guideJoints, world_up_axis=self.upVector, up_axis=(0, -1, 0),
                            reverse_aim=self.sideMultiplier, reverse_up=self.sideMultiplier)

    def define_guides(self):
        """Override the guide definition method"""
        joint.set_joint_type(self.guideJoints[0], "FingerRoot")
        _ = [joint.set_joint_type(jnt, "Finger") for jnt in self.guideJoints[1:]]
