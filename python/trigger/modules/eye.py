from maya import cmds
import maya.api.OpenMaya as om
from trigger.library import api
from trigger.library import functions, connection, attribute
from trigger.library import naming
from trigger.library import attribute
from trigger.library import controllers as ic
from trigger.library import tools

from trigger.core import filelog
log = filelog.Filelog(logname=__name__, filename="trigger_log")

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
                log.error("Simple FK setup needs exactly 2 initial joints")
                return
            self.inits = inits
            # parse inits
            pass
        else:
            log.error("Class needs either build_data or inits to be constructed")

        # get the properties from the root
        self.useRefOrientation = cmds.getAttr("%s.useRefOri" % self.inits[0])
        self.side = functions.get_joint_side(self.inits[0])
        self.sideMult = -1 if self.side == "R" else 1
        self.isLocal = bool(cmds.getAttr("%s.localJoints" % self.inits[0]))
        self.groupID = int(cmds.getAttr("%s.groupID" % self.inits[0]))

        # initialize coordinates
        self.up_axis, self.mirror_axis, self.look_axis = functions.getRigAxes(self.inits[0])

        # initialize suffix
        self.suffix = (naming.uniqueName(cmds.getAttr("%s.moduleName" % self.inits[0])))

        # module variables
        self.aimBridge = None
        self.aimCont = None
        self.aimDriven = None
        self.directDriven = None
        self.aimContGroupFollow = None
        self.plugDriven = None
        self.controllerGrp = None
        self.jointGrp = None
        self.otherEyeConts = []
        self.groupCont = None

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
        functions.alignTo(self.scaleGrp, self.inits[0], position=True, rotation=False)
        self.nonScaleGrp = cmds.group(name="%s_nonScaleGrp" % self.suffix, em=True)

        cmds.addAttr(self.scaleGrp, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True)
        cmds.addAttr(self.scaleGrp, at="bool", ln="Joints_Visibility", sn="jointVis", defaultValue=True)
        cmds.addAttr(self.scaleGrp, at="bool", ln="Rig_Visibility", sn="rigVis", defaultValue=False)
        # make the created attributes visible in the channelbox
        cmds.setAttr("%s.contVis" % self.scaleGrp, cb=True)
        cmds.setAttr("%s.jointVis" % self.scaleGrp, cb=True)
        cmds.setAttr("%s.rigVis" % self.scaleGrp, cb=True)

        self.controllerGrp = cmds.group(name="%s_controller_grp" % self.suffix, em=True)
        attribute.lockAndHide(self.controllerGrp)
        cmds.parent(self.controllerGrp, self.limbGrp)

        self.jointGrp = cmds.group(name="%s_joint_grp" % self.suffix, em=True)
        attribute.lockAndHide(self.controllerGrp)
        cmds.parent(self.jointGrp, self.limbGrp)

        cmds.parent(self.scaleGrp, self.limbGrp)
        cmds.parent(self.nonScaleGrp, self.limbGrp)

        self.localOffGrp = cmds.group(name="%s_localOffset_grp" %self.suffix, em=True)
        self.plugBindGrp = cmds.group(name="%s_plugBind_grp" %self.suffix, em=True)
        cmds.parent(self.localOffGrp, self.plugBindGrp)
        cmds.parent(self.plugBindGrp, self.limbGrp)

        if self.groupID:
            functions.validateGroup("Eye_group%i" % self.groupID)
            cmds.parent(self.limbGrp, "Eye_group%i" % self.groupID)
            self.limbGrp = "Eye_group%i" % self.groupID
            c_shapes = cmds.listRelatives("Eye_group%i" % self.groupID, ad=True, children=True, ap=False, type="nurbsCurve")
            if c_shapes:
                self.otherEyeConts = [functions.getParent(shape) for shape in c_shapes]

            if cmds.objExists("Eye_group%i_cont" %self.groupID):
                self.groupCont = "Eye_group%i_cont" %self.groupID
                self.otherEyeConts.remove(self.groupCont)


    def createJoints(self):
        cmds.select(d=True)
        self.limbPlug = cmds.joint(name="limbPlug_%s" % self.suffix, p=api.get_world_translation(self.inits[0]), radius=3)

        cmds.select(d=True)
        eye_jnt = cmds.joint(name="jDef_eye_{0}".format(self.suffix))
        functions.alignTo(eye_jnt, self.inits[0])
        eye_offset = functions.createUpGrp(eye_jnt, "OFF")
        self.plugDriven = functions.createUpGrp(eye_jnt, "PLUG_DRIVEN")
        self.aimDriven = functions.createUpGrp(eye_jnt, "AIM")
        self.directDriven = functions.createUpGrp(eye_jnt, "DIRECT")
        self.sockets.append(eye_jnt)
        self.deformerJoints.append(eye_jnt)

        # if not self.useRefOrientation:
        #     functions.alignTo(eye_jnt, self.inits[0], position=False, rotation=True)
        #     cmds.makeIdentity(eye_jnt, a=True)
        if not self.useRefOrientation:
            functions.orientJoints(self.deformerJoints, worldUpAxis=(self.look_axis), upAxis=(0, 1, 0), reverseAim=self.sideMult, reverseUp=self.sideMult)

        cmds.parent(eye_offset, self.jointGrp)

    def createControllers(self):
        icon_handler = ic.Icon()

        self.aimBridge = cmds.spaceLocator(name="aimBridge_%s" %self.suffix)[0]
        attribute.drive_attrs("%s.rigVis" % self.scaleGrp, "%s.v" % self.aimBridge)
        self.aimCont, _ = icon_handler.create_icon("Circle", icon_name="%s_Aim_cont" % self.suffix, scale = (1, 1, 1),
                                                   normal=(0, 0, 1))
        self.controllers.append(self.aimCont)

        self.otherEyeConts.append(self.aimCont)

        functions.alignTo(self.aimBridge, self.inits[1], position=True, rotation=True)
        functions.alignTo(self.aimCont, self.inits[1], position=True, rotation=True)

        aimCont_OFF = functions.createUpGrp(self.aimCont, "OFF")
        self.aimContGroupFollow = functions.createUpGrp(self.aimCont, "GroupFollow")

        cmds.parent(self.aimBridge, self.nonScaleGrp)

        cmds.parent(aimCont_OFF, self.controllerGrp)
        # aimConstraint -offset 0 0 0 -weight 1 -aimVector 0 0 1 -upVector 0 1 0 -worldUpType "objectrotation" -worldUpVector 0 1 0 -worldUpObject limbPlug_C_eye;

        if self.groupID:
            if not self.groupCont:
                self.groupCont, _ = icon_handler.create_icon("Circle", icon_name="Eye_group%i_cont" % self.groupID, scale = (2, 2, 2),
                                                             normal=(0, 0, 1))
                functions.colorize(self.groupCont, "C")
                attribute.drive_attrs("%s.contVis" % self.scaleGrp, "%s.v" % self.groupCont)
                cmds.delete(cmds.pointConstraint(self.otherEyeConts, self.groupCont, mo=False))
                groupCont_off = functions.createUpGrp(self.groupCont, "OFF")
                cmds.connectAttr("%s.scale" % self.scaleGrp, "%s.scale" %groupCont_off)
                cmds.parent(groupCont_off, self.limbGrp)
            for cont in self.otherEyeConts:
                g_follow = functions.getParent(cont)
                _ = [attribute.disconnect_attr(g_follow, attr=attr, suppress_warnings=True) for attr in ["translate", "rotate", "scale"]]
                # connection.matrixConstraint(self.groupCont, g_follow, mo=True, source_parent_cutoff=self.localOffGrp)
                connection.matrixConstraint(self.groupCont, g_follow, mo=True)
            else:
                # if the group controller exists, update only its shape and rotation pivot
                # adjust the pivot
                cmds.xform(self.groupCont, a=True, ws=True, piv=api.get_center(self.otherEyeConts))
                cmds.xform(functions.getParent(self.groupCont), a=True, ws=True, piv=api.get_center(self.otherEyeConts))

                bb = cmds.exactWorldBoundingBox(*self.otherEyeConts)
                x_dist = abs(bb[0] - bb[3])
                y_dist = abs(bb[1] - bb[4])
                z_dist = abs(bb[2] - bb[5])
                temp_cont, _ = icon_handler.create_icon("Circle", icon_name="TEMP_%i_cont" % self.groupID, scale = (x_dist, z_dist, y_dist),
                                                        normal=(0, 0, 1))

                # cmds.delete(cmds.pointConstraint(test_nodes, cont))
                temp_cont_shape = functions.getShapes(temp_cont)[0]
                functions.alignTo(temp_cont, self.groupCont, position=True)
                # cmds.makeIdentity(temp_cont, a=True)

                # cmds.connectAttr("%s.worldSpace" % temp_cont_shape, "%s.create" % self.groupCont, f=True)
                # oddly, it requires a viewport refresh before disconnecting (or deleting) the replacement shapes
                # cmds.refresh()

                tools.replace_curve(self.groupCont, temp_cont)

                functions.deleteObject(temp_cont)
                self.anchors = [(self.groupCont, "parent", 1, None)]
                pass
        else:
            self.anchors = [(self.aimCont, "parent", 1, None)]

        attribute.drive_attrs("%s.contVis" % self.scaleGrp, ["%s.v" % x for x in self.controllers])
        functions.colorize(self.controllers, self.colorCodes[0])

    def createConnections(self):
        aim_con = cmds.aimConstraint(self.aimBridge, self.aimDriven, upVector=self.up_axis, aimVector=self.look_axis,
                                     wut="objectrotation", wuo=self.limbPlug)

        connection.matrixConstraint(self.aimCont, self.aimBridge, mo=False,
                                    source_parent_cutoff=self.localOffGrp)



        if self.isLocal:
            connection.matrixConstraint(self.limbPlug, self.plugBindGrp)
            # connection.matrixConstraint(self.plugBindGrp, self.aimContGroupFollow)
        else:
            # connection.matrixConstraint(self.limbPlug, self.aimContGroupFollow)
            connection.matrixConstraint(self.limbPlug, self.plugDriven)

    def round_up(self):
        _ = [cmds.connectAttr("%s.jointVis" % self.scaleGrp, "%s.v" % x) for x in self.deformerJoints]

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
    def __init__(self, side="L", suffix="eye", segments=None, tMatrix=None, upVector=(0, 1, 0), mirrorVector=(1, 0, 0), lookVector=(0,0,1), *args, **kwargs):
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
        cmds.select(d=True)
        root_jnt = cmds.joint(name="jInit_eyeRoot_{0}".format(self.suffix), position=root_point)
        aim_jnt = cmds.joint(name="jInit_eyeAim_{0}".format(self.suffix), position=self.offsetVector)

        # Update the guideJoints list
        self.guideJoints.append(root_jnt)
        self.guideJoints.append(aim_jnt)

        # set orientation of joints

    def define_attributes(self):
        # set joint side and type attributes
        functions.set_joint_type(self.guideJoints[0], "EyeRoot")
        functions.set_joint_type(self.guideJoints[1], "EyeAim")
        _ = [functions.set_joint_side(jnt, self.side) for jnt in self.guideJoints]

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
            log.warning("Eye Module needs to have exactly 2 Guid Joints! (root, aim)")
            return
        self.guideJoints = joints_list
        self.define_attributes()