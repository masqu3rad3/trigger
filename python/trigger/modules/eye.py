from maya import cmds
import maya.api.OpenMaya as om
from trigger.library import api, joint
from trigger.library import functions, connection
from trigger.library import naming
from trigger.library import attribute
from trigger.objects.controller import Controller
from trigger.library import tools

from trigger.core import filelog
LOG = filelog.Filelog(logname=__name__, filename="trigger_log")

LIMB_DATA = {"members": ["EyeRoot", "EyeAim"],
             "properties": [
                 {
                     "attr_name": "localJoints",
                     "nice_name": "Local_Joints",
                     "attr_type": "bool",
                     "default_value": False},
                 {
                     "attr_name": "groupID",
                     "nice_name": "Group_ID",
                     "attr_type": "long",
                     "min_value": 0,
                     "max_value": 9999,
                     "default_value": 1
                 },
             ],

        "multi_guide": None,
        "sided": True,}

class Eye(object):
    def __init__(self, build_data=None, inits=None, *args, **kwargs):
        super(Eye, self).__init__()
        # fool proofing

        # reinitialize the initial Joints
        if build_data:
            eyeRoot = build_data.get("EyeRoot")
            eyeAim = build_data.get("EyeAim")
            self.inits = [eyeRoot, eyeAim]
            #parse build data
            pass
        elif inits:
            if len(inits) != 2:
                LOG.error("Simple FK setup needs exactly 2 initial joints")
                return
            self.inits = inits
            # parse inits
            pass
        else:
            LOG.error("Class needs either build_data or inits to be constructed")

        # get the properties from the root
        self.useRefOrientation = cmds.getAttr("%s.useRefOri" % self.inits[0])
        self.side = joint.get_joint_side(self.inits[0])
        self.sideMult = -1 if self.side == "R" else 1
        self.isLocal = bool(cmds.getAttr("%s.localJoints" % self.inits[0]))
        self.groupID = int(cmds.getAttr("%s.groupID" % self.inits[0]))

        # initialize coordinates
        self.up_axis, self.mirror_axis, self.look_axis = joint.get_rig_axes(self.inits[0])

        # initialize suffix
        self.module_name = (naming.unique_name(cmds.getAttr("%s.moduleName" % self.inits[0])))

        # module variables
        self.aim_bridge = None
        self.aim_cont = None
        self.aimDriven = None
        self.directDriven = None
        self.aimContGroupFollow = None
        self.plugDriven = None
        self.controllerGrp = None
        self.jointGrp = None
        self.other_eye_conts = []
        self.group_cont = None

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
        self.limbGrp = cmds.group(name=naming.parse([self.module_name], suffix="grp"), empty=True)
        self.scaleGrp = cmds.group(name=naming.parse([self.module_name, "scale"], suffix="grp"), empty=True)
        functions.align_to(self.scaleGrp, self.inits[0], position=True, rotation=False)
        self.nonScaleGrp = cmds.group(name=naming.parse([self.module_name, "nonScale"], suffix="grp"), empty=True)

        cmds.addAttr(self.scaleGrp, attributeType="bool", longName="Control_Visibility", shortName="contVis", defaultValue=True)
        cmds.addAttr(self.scaleGrp, attributeType="bool", longName="Joints_Visibility", shortName="jointVis", defaultValue=True)
        cmds.addAttr(self.scaleGrp, attributeType="bool", longName="Rig_Visibility", shortName="rigVis", defaultValue=False)
        # make the created attributes visible in the channelbox
        cmds.setAttr("%s.contVis" % self.scaleGrp, channelBox=True)
        cmds.setAttr("%s.jointVis" % self.scaleGrp, channelBox=True)
        cmds.setAttr("%s.rigVis" % self.scaleGrp, channelBox=True)

        self.controllerGrp = cmds.group(name=naming.parse([self.module_name, "controller"], suffix="grp"), empty=True)
        attribute.lock_and_hide(self.controllerGrp)
        cmds.parent(self.controllerGrp, self.limbGrp)

        self.jointGrp = cmds.group(name=naming.parse([self.module_name, "joint"], suffix="grp"), empty=True)
        attribute.lock_and_hide(self.controllerGrp)
        cmds.parent(self.jointGrp, self.limbGrp)

        cmds.parent(self.scaleGrp, self.limbGrp)
        cmds.parent(self.nonScaleGrp, self.limbGrp)

        self.localOffGrp = cmds.group(name=naming.parse([self.module_name, "localOffset"], suffix="grp"), empty=True)
        self.plugBindGrp = cmds.group(name=naming.parse([self.module_name, "bind"], suffix="grp"), empty=True)
        cmds.parent(self.localOffGrp, self.plugBindGrp)
        cmds.parent(self.plugBindGrp, self.limbGrp)

        if self.groupID:
            functions.validate_group("Eye_group%i" % self.groupID)
            cmds.parent(self.limbGrp, "Eye_group%i" % self.groupID)
            self.limbGrp = "Eye_group%i" % self.groupID
            c_shapes = cmds.listRelatives("Eye_group%i" % self.groupID, allDescendents=True, children=True,
                                          allParents=False, type="nurbsCurve")
            if c_shapes:
                self.other_eye_conts = [functions.get_parent(shape) for shape in c_shapes]

            if cmds.objExists("Eye_group%i_cont" %self.groupID):
                self.group_cont = "Eye_group%i_cont" % self.groupID
                self.other_eye_conts.remove(self.group_cont)


    def createJoints(self):
        cmds.select(d=True)
        self.limbPlug = cmds.joint(name=naming.parse([self.module_name, "plug"], suffix="j"), position=api.get_world_translation(self.inits[0]), radius=3)

        cmds.select(d=True)
        eye_jnt = cmds.joint(name=naming.parse([self.module_name, "eye"], suffix="jDef"))
        functions.align_to(eye_jnt, self.inits[0])
        eye_offset = functions.create_offset_group(eye_jnt, "OFF")
        self.plugDriven = functions.create_offset_group(eye_jnt, "PLUG_DRIVEN")
        self.aimDriven = functions.create_offset_group(eye_jnt, "AIM")
        self.directDriven = functions.create_offset_group(eye_jnt, "DIRECT")
        self.sockets.append(eye_jnt)
        self.deformerJoints.append(eye_jnt)

        if not self.useRefOrientation:
            joint.orient_joints(self.deformerJoints, world_up_axis=self.look_axis, up_axis=(0, 1, 0), reverse_aim=self.sideMult, reverse_up=self.sideMult)

        cmds.parent(eye_offset, self.jointGrp)

    def createControllers(self):
        self.aim_bridge = cmds.spaceLocator(name=naming.parse([self.module_name, "aim"], suffix="brg"))[0]
        attribute.drive_attrs("%s.rigVis" % self.scaleGrp, "%s.v" % self.aim_bridge)
        self.aim_cont = Controller(
            shape="Circle",
            name=naming.parse([self.module_name, "aim"], suffix="cont"),
            scale=(1, 1, 1),
            normal=(0, 0, 1)
        )
        self.controllers.append(self.aim_cont)

        self.other_eye_conts.append(self.aim_cont)

        functions.align_to(self.aim_bridge, self.inits[1], position=True, rotation=True)
        functions.align_to(self.aim_cont.name, self.inits[1], position=True, rotation=True)

        aimCont_OFF = self.aim_cont.add_offset("OFF")
        self.aimContGroupFollow = self.aim_cont.add_offset("GroupFollow")

        cmds.parent(self.aim_bridge, self.nonScaleGrp)

        cmds.parent(aimCont_OFF, self.controllerGrp)
        # aimConstraint -offset 0 0 0 -weight 1 -aimVector 0 0 1 -upVector 0 1 0 -worldUpType "objectrotation" -worldUpVector 0 1 0 -worldUpObject limbPlug_C_eye;

        if self.groupID:
            if not self.group_cont:
                self.group_cont = Controller(
                    shape="Circle",
                    name=naming.parse([self.module_name, "group", self.groupID], suffix="cont"),
                    scale=(2, 2, 2),
                    normal=(0, 0, 1)
                )
                self.group_cont.set_side("C", tier=0)
                attribute.drive_attrs("%s.contVis" % self.scaleGrp, "%s.v" % self.group_cont.name)
                cmds.delete(cmds.pointConstraint([x.name for x in self.other_eye_conts], self.group_cont.name, maintainOffset=False))
                groupCont_off = self.group_cont.add_offset("OFF")
                cmds.connectAttr("{}.scale".format(self.scaleGrp), "{}.scale".format(groupCont_off))
                cmds.parent(groupCont_off, self.limbGrp)
            for cont in self.other_eye_conts:
                g_follow = cont.parent
                _ = [attribute.disconnect_attr(g_follow, attr=attr, suppress_warnings=True) for attr in ["translate", "rotate", "scale"]]
                # connection.matrixConstraint(self.groupCont, g_follow, mo=True, source_parent_cutoff=self.localOffGrp)
                connection.matrixConstraint(self.group_cont.name, g_follow, maintainOffset=True)
            else:
                # if the group controller exists, update only its shape and rotation pivot
                # adjust the pivot
                cmds.xform(self.group_cont.name, absolute=True, worldSpace=True, pivots=api.get_center([x.name for x in self.other_eye_conts]))
                cmds.xform(self.group_cont.parent, absolute=True, worldSpace=True, pivots=api.get_center([x.name for x in self.other_eye_conts]))

                bb = cmds.exactWorldBoundingBox(*[x.name for x in self.other_eye_conts])
                x_dist = abs(bb[0] - bb[3])
                y_dist = abs(bb[1] - bb[4])
                z_dist = abs(bb[2] - bb[5])
                # temp_cont, _ = icon_handler.create_icon("Circle", icon_name="TEMP_%i_cont" % self.groupID, scale = (x_dist, z_dist, y_dist),
                #                                         normal=(0, 0, 1))
                #
                # # cmds.delete(cmds.pointConstraint(test_nodes, cont))
                # temp_cont_shape = functions.get_shapes(temp_cont)[0]
                # functions.align_to(temp_cont, self.groupCont, position=True)
                # # cmds.makeIdentity(temp_cont, a=True)
                #
                # # cmds.connectAttr("%s.worldSpace" % temp_cont_shape, "%s.create" % self.groupCont, f=True)
                # # oddly, it requires a viewport refresh before disconnecting (or deleting) the replacement shapes
                # # cmds.refresh()
                #
                # tools.replace_curve(self.groupCont, temp_cont)
                #
                # functions.delete_object(temp_cont)
                self.group_cont.set_shape("Circle", scale=(x_dist, z_dist, y_dist), normal=(0, 0, 1))

                self.anchors = [(self.group_cont.name, "parent", 1, None)]
                pass
        else:
            self.anchors = [(self.aim_cont.name, "parent", 1, None)]

        attribute.drive_attrs("%s.contVis" % self.scaleGrp, ["%s.v" % x.name for x in self.controllers])
        # functions.colorize(self.controllers, self.colorCodes[0])

    def createConnections(self):
        aim_con = cmds.aimConstraint(self.aim_bridge, self.aimDriven, upVector=self.up_axis, aimVector=self.look_axis,
                                     worldUpType="objectrotation", worldUpObject=self.limbPlug)

        connection.matrixConstraint(self.aim_cont.name, self.aim_bridge, maintainOffset=False,
                                    source_parent_cutoff=self.localOffGrp)



        if self.isLocal:
            connection.matrixConstraint(self.limbPlug, self.plugBindGrp)
            # connection.matrixConstraint(self.plugBindGrp, self.aimContGroupFollow)
        else:
            # connection.matrixConstraint(self.limbPlug, self.aimContGroupFollow)
            connection.matrixConstraint(self.limbPlug, self.plugDriven)

    def round_up(self):
        _ = [cmds.connectAttr("%s.jointVis" % self.scaleGrp, "%s.v" % x) for x in self.deformerJoints]
        self.scaleConstraints.append(self.scaleGrp)

    def createLimb(self):
        self.createGrp()
        self.createJoints()
        self.createControllers()
        self.createConnections()
        # self.createRoots()
        # self.createIKsetup()
        # self.createFKsetup()
        # self.ikfkSwitching()
        # self.createRibbons()
        # self.createTwistSplines()
        # self.createAngleExtractors()
        self.round_up()


class Guides(object):
    def __init__(self, side="L", suffix="eye", segments=None, tMatrix=None, upVector=(0, 1, 0), mirrorVector=(1, 0, 0), lookVector=(0, 0, 1), *args, **kwargs):
        super(Guides, self).__init__()
        # fool check

        #-------Mandatory------[Start]
        self.side = side
        self.sideMultiplier = -1 if side == "R" else 1
        self.name = suffix
        self.segments = segments
        self.tMatrix = om.MMatrix(tMatrix) if tMatrix else om.MMatrix()
        self.upVector = om.MVector(upVector)
        self.mirrorVector = om.MVector(mirrorVector)
        self.lookVector = om.MVector(lookVector)

        self.offsetVector = None
        self.guideJoints = []
        #-------Mandatory------[End]

    def draw_joints(self):
        # fool check
        # if self.segments != 2:
        #     log.warning("Eye Module needs to have exactly 2 Guid Joints! (root, aim)")
        #     return

        if self.side == "C":
            root_point = om.MVector(0, 0, 0)
            self.offsetVector = om.MVector(0, 0, 10) * self.tMatrix
            pass
        else:
            root_point = om.MVector(2 * self.sideMultiplier, 0, 0) * self.tMatrix
            self.offsetVector = om.MVector(2 * self.sideMultiplier, 0, 10) * self.tMatrix
            pass

        # Draw the joints
        cmds.select(clear=True)
        root_jnt = cmds.joint(name=naming.parse([self.name, "root"], side=self.side, suffix="jInit"), position=root_point)
        aim_jnt = cmds.joint(name=naming.parse([self.name, "aim"], side=self.side, suffix="jInit"), position=self.offsetVector)

        # Update the guideJoints list
        self.guideJoints.append(root_jnt)
        self.guideJoints.append(aim_jnt)

        # set orientation of joints

    def define_attributes(self):
        # set joint side and type attributes
        joint.set_joint_type(self.guideJoints[0], "EyeRoot")
        joint.set_joint_type(self.guideJoints[1], "EyeAim")
        _ = [joint.set_joint_side(jnt, self.side) for jnt in self.guideJoints]

        # ----------Mandatory---------[Start]
        root_jnt = self.guideJoints[0]
        attribute.create_global_joint_attrs(root_jnt, moduleName="%s_eye" % self.side, upAxis=self.upVector, mirrorAxis=self.mirrorVector, lookAxis=self.lookVector)
        # ----------Mandatory---------[End]

        for attr_dict in LIMB_DATA["properties"]:
            attribute.create_attribute(root_jnt, attr_dict)

    def createGuides(self):
        self.draw_joints()
        self.define_attributes()

    def convertJoints(self, joints_list):
        if len(joints_list) != 2:
            LOG.warning("Eye Module needs to have exactly 2 Guid Joints! (root, aim)")
            return
        self.guideJoints = joints_list
        self.define_attributes()