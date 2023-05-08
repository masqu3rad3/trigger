from maya import cmds
from maya import mel
import maya.api.OpenMaya as om
from trigger.library import api, joint
from trigger.library import functions
from trigger.library import connection
from trigger.library import naming
from trigger.library import attribute
from trigger.objects.controller import Controller
from trigger.library.tools import make_stretchy_ik

from trigger.core import filelog
log = filelog.Filelog(logname=__name__, filename="trigger_log")

LIMB_DATA = {
    "members": ["FkikRoot", "Fkik"],
    "properties": [{"attr_name": "localJoints",
                    "nice_name": "Local_Joints",
                    "attr_type": "bool",
                    "default_value": False},
                   {"attr_name": "switchMode",
                    "nice_name": "Switch_Mode",
                    "attr_type": "enum",
                    "enum_list": "Fk & IK:Fk Only:IK Only",
                    "default_value": 0},
                   {"attr_name": "stretchyIk",
                    "nice_name": "Stretchy_IK",
                    "attr_type": "bool",
                    "default_value": True},
                   {"attr_name": "ikSolver",
                    "nice_name": "Ik_Solver",
                    "attr_type": "enum",
                    "enum_list": "Single Chain Solver:Rotate Plane Solver:Spring Solver",
                    "default_value": 1,},
                   ],
    "multi_guide": "Fkik",
    "sided": True,
}


class Fkik(object):
    def __init__(self, build_data=None, inits=None, *args, **kwargs):
        super(Fkik, self).__init__()
        # fool proofing

        # reinitialize the initial Joints
        if build_data:
            self.fkRoot = build_data.get("FkikRoot")
            self.fks = build_data.get("Fkik")
            self.inits = [self.fkRoot] + self.fks
            #parse build data
            pass
        elif inits:
            if len(inits) < 2:
                log.error("Simple FK setup needs at least 2 initial joints")
                return
            self.fkRoot = inits[0]
            self.inits = inits
        else:
            log.error("Class needs either build_data or inits to be constructed")

        # get distances

        # get positions

        # get the properties from the root
        self.useRefOrientation = cmds.getAttr("%s.useRefOri" % self.fkRoot)
        self.side = joint.get_joint_side(self.fkRoot)
        self.sideMult = -1 if self.side == "R" else 1
        self.isLocal = bool(cmds.getAttr("%s.localJoints" % self.inits[0]))
        self.switchMode = int(cmds.getAttr("%s.switchMode" % self.inits[0]))
        self.stretchyIk = bool(cmds.getAttr("%s.stretchyIk" % self.inits[0]))
        self.ikSolver = int(cmds.getAttr("%s.ikSolver" % self.inits[0]))

        # initialize coordinates
        self.up_axis, self.mirror_axis, self.look_axis = joint.get_rig_axes(self.inits[0])

        # initialize suffix
        self.module_name = (naming.unique_name(cmds.getAttr("%s.moduleName" % self.inits[0])))

        # module specific variables
        self.fkJoints = []
        self.ikJoints = []
        self.fkControllers = []
        self.ikControllers = []
        self.rootIkCont = None
        self.endIKCont = None
        self.fkControllersOff = []
        self.ikControllersOff = []
        self.switch_controller = None
        self.polevector_bridge = None
        self.polevector_cont = None
        self.middleIndex = 1
        self.scaleHook = None

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
        self.nonScaleGrp = cmds.group(name="%s_nonScaleGrp" % self.module_name, empty=True)
        self.nonScaleGrp = cmds.group(name=naming.parse([self.module_name, "nonScale"], suffix="grp"), empty=True)

        for nicename, attrname in zip(["Control_Visibility", "Joints_Visibility", "Rig_Visibility"], ["contVis", "jointVis", "rigVis"]):
            attribute.create_attribute(self.scaleGrp, nice_name=nicename, attr_name=attrname, attr_type="bool",
                                       keyable=False, display=True)
        # cmds.addAttr(self.scaleGrp, attributeType="bool", longName="Control_Visibility", shortName="contVis", defaultValue=True)
        # cmds.addAttr(self.scaleGrp, attributeType="bool", longName="Joints_Visibility", shortName="jointVis", defaultValue=True)
        # cmds.addAttr(self.scaleGrp, attributeType="bool", longName="Rig_Visibility", shortName="rigVis", defaultValue=False)
        # # make the created attributes visible in the channelbox
        # cmds.setAttr("%s.contVis" % self.scaleGrp, channelBox=True)
        # cmds.setAttr("%s.jointVis" % self.scaleGrp, channelBox=True)
        # cmds.setAttr("%s.rigVis" % self.scaleGrp, channelBox=True)

        cmds.parent(self.scaleGrp, self.limbGrp)
        cmds.parent(self.nonScaleGrp, self.limbGrp)

        self.localOffGrp = cmds.group(name=naming.parse([self.module_name, "localOffset"], suffix="grp"), empty=True)
        self.plugBindGrp = cmds.group(name=naming.parse([self.module_name, "bind"], suffix="grp"), empty=True)
        cmds.parent(self.localOffGrp, self.plugBindGrp)
        cmds.parent(self.plugBindGrp, self.limbGrp)

        # scale hook gets the scale value from the bind group but not from the localOffset
        self.scaleHook = cmds.group(name=naming.parse([self.module_name, "scaleHook"], suffix="grp"), empty=True)
        cmds.parent(self.scaleHook, self.limbGrp)
        scale_skips = "xyz" if self.isLocal else ""
        connection.matrixConstraint(self.scaleGrp, self.scaleHook, skipScale=scale_skips)

    def createJoints(self):
        # draw Joints
        cmds.select(deselect=True)
        self.limbPlug = cmds.joint(name=naming.parse([self.module_name, "plug"], suffix="j"), position=api.get_world_translation(self.inits[0]), radius=3)
        cmds.connectAttr("%s.s" %self.scaleGrp, "%s.s" %self.limbPlug)

        cmds.select(deselect=True)
        for nmb, j in enumerate(self.inits):
            # jnt = cmds.joint(name="{0}_{1}_jDef".format(self.suffix, nmb))
            # jnt = cmds.joint(name="jDef_{0}_{1}".format(j, self.module_name))
            jnt = cmds.joint(name=naming.parse([self.module_name, j], suffix="jDef"))
            self.sockets.append(jnt)
            self.deformerJoints.append(jnt)

        if not self.useRefOrientation:
            joint.orient_joints(self.deformerJoints, world_up_axis=(self.look_axis), up_axis=(0, 1, 0), reverse_aim=self.sideMult, reverse_up=self.sideMult)
        else:
            for x in range (len(self.deformerJoints)):
                functions.align_to(self.deformerJoints[x], self.inits[x], position=True, rotation=True)
                cmds.makeIdentity(self.deformerJoints[x], apply=True)

        cmds.parent(self.deformerJoints[0], self.nonScaleGrp)

        # If the switch mode is fk&ik create duplicate chain for each
        if self.switchMode == 0:
            self.fkJoints=[]
            self.ikJoints=[]
            dupsIK = cmds.duplicate(self.deformerJoints[0], renameChildren=True)
            for dup, original in zip(dupsIK, self.inits):
                jnt = cmds.rename(dup, "jnt_IK_{0}_{1}".format(original, self.module_name))
                self.ikJoints.append(jnt)

            dupsFK = cmds.duplicate(self.deformerJoints[0], renameChildren=True)
            for dup, original in zip(dupsFK, self.inits):
                jnt = cmds.rename(dup, "jnt_FK_{0}_{1}".format(original, self.module_name))
                self.fkJoints.append(jnt)

            attribute.drive_attrs("%s.rigVis" % self.scaleGrp, ["%s.v" % x for x in self.ikJoints])
            attribute.drive_attrs("%s.rigVis" % self.scaleGrp, ["%s.v" % x for x in self.fkJoints])

        attribute.drive_attrs("%s.jointVis" % self.scaleGrp, ["%s.v" % x for x in self.deformerJoints])
        cmds.connectAttr("%s.jointVis" % self.scaleGrp,"%s.v" % self.limbPlug)
        functions.colorize(self.deformerJoints, self.colorCodes[0], shape=False)

    def createControllers(self):

        # FK Controllers
        if self.switchMode == 0 or self.switchMode == 1:
            fk_joints = self.deformerJoints if self.switchMode != 0 else self.fkJoints
            # for nmb, jnt in enumerate(fk_joints[:-1]):
            scale_mult = None
            for nmb, jnt in enumerate(fk_joints):
                if nmb < (len(fk_joints)-1):
                    scale_mult = functions.get_distance(jnt, fk_joints[nmb + 1]) * 0.5

                # cont, _ = icon_handler.create_icon("Cube", icon_name="%s%i_FK_cont" % (self.module_name, nmb),
                #                                    scale=(scale_mult, scale_mult, scale_mult))
                cont = Controller(
                    shape="Cube",
                    name=naming.parse([self.module_name, "FK", nmb], suffix="cont"),
                    scale=(scale_mult, scale_mult, scale_mult),
                )

                cmds.xform(cont.name, pivots=(self.sideMult * (-scale_mult), 0, 0))
                functions.align_to_alter(cont.name, jnt, 2)

                cont_OFF = cont.add_offset("OFF")
                cont_ORE = cont.add_offset("ORE")
                cont.freeze()

                self.fkControllers.append(cont)
                self.fkControllersOff.append(cont_OFF)

                if nmb != 0:
                    cmds.parent(self.fkControllersOff[nmb], self.fkControllers[nmb - 1].name)
            cmds.parent(self.fkControllersOff[0], self.localOffGrp)

            attribute.drive_attrs("%s.contVis" % self.scaleGrp, ["%s.v" % x for x in self.fkControllersOff])
            functions.colorize(self.controllers, self.colorCodes[0])

        # IK Controllers
        if self.switchMode == 0 or self.switchMode == 2:
            ik_joints = self.deformerJoints if self.switchMode != 0 else self.ikJoints
            ik_bind_grp = cmds.group(name=naming.parse([self.module_name, "IK", "bing"], suffix="grp"), empty=True)
            cmds.parent(ik_bind_grp, self.localOffGrp)
            connection.matrixConstraint(self.limbPlug, ik_bind_grp, maintainOffset=True)

            scale_mult = functions.get_distance(ik_joints[0], ik_joints[1]) * 0.5
            self.rootIkCont = Controller(
                shape="Circle",
                name=naming.parse([self.module_name, "IK", "root"], suffix="cont"),
                normal=(1, 0, 0),
                scale=(scale_mult, scale_mult, scale_mult),
            )
            self.ikControllers.append(self.rootIkCont)
            root_ik_cont_off = self.rootIkCont.add_offset("OFF")
            self.ikControllersOff.append(root_ik_cont_off)
            functions.align_to(root_ik_cont_off, ik_joints[0], rotation=True, position=True)

            self.endIKCont = Controller(
                shape="Circle",
                name=naming.parse([self.module_name, "IK", "end"], suffix="cont"),
                normal=(1, 0, 0),
                scale=(scale_mult, scale_mult, scale_mult),
            )
            self.ikControllers.append(self.endIKCont)
            end_ik_cont_off = self.endIKCont.add_offset("OFF")
            self.ikControllersOff.append(end_ik_cont_off)
            functions.align_to(end_ik_cont_off, ik_joints[-1], rotation=True, position=True)

            cmds.parent(root_ik_cont_off, ik_bind_grp)
            cmds.parent(end_ik_cont_off, ik_bind_grp)
            # POLE Vector
            if self.ikSolver != 0: # if it is a rotate plane or spring solver
                # create a bridge locator to stay with the local joints

                scale_mult = functions.get_distance(ik_joints[0], ik_joints[-1]) * 0.1
                self.polevector_bridge = cmds.spaceLocator(name=naming.parse([self.module_name, "poleVector"], suffix="brg"))[0]
                self.polevector_cont = Controller(
                    shape="Plus",
                    name=naming.parse([self.module_name, "pole"], suffix="cont"),
                    normal=(self.sideMult, 0, 0),
                    scale=(scale_mult, scale_mult, scale_mult),
                )
                offset_magnitude = scale_mult
                self.middleIndex = int((len(ik_joints)-1)*0.5)
                offset_vector = api.get_between_vector(ik_joints[self.middleIndex], ik_joints)

                functions.align_and_aim(self.polevector_bridge,
                                        target_list=[ik_joints[self.middleIndex]],
                                        aim_target_list=ik_joints,
                                        up_vector=self.up_axis,
                                        translate_offset=(offset_vector * offset_magnitude)
                                        )

                functions.align_to(self.polevector_cont.name, self.polevector_bridge, position=True, rotation=True)
                pole_cont_off = self.polevector_cont.add_offset("OFF")
                # connection.matrixConstraint(self.poleVectorBridge, self.poleVectorCont, mo=False, source_parent_cutoff=self.localOffGrp)
                cmds.parent(pole_cont_off, ik_bind_grp)

            if self.stretchyIk:
                cmds.addAttr(self.endIKCont.name, shortName="squash", longName="Squash", defaultValue=0.0, minValue=0.0,
                             maxValue=1.0, attributeType="double", keyable=True)
                cmds.addAttr(self.endIKCont.name, shortName="stretch", longName="Stretch", defaultValue=1.0, minValue=0.0,
                             maxValue=1.0, attributeType="double", keyable=True)
                cmds.addAttr(self.endIKCont.name, shortName="stretchLimit", longName="StretchLimit", defaultValue=100.0,
                             minValue=0.0, maxValue=1000.0, attributeType="double", keyable=True)
                cmds.addAttr(self.endIKCont.name, shortName="softIK", longName="SoftIK", defaultValue=0.0, minValue=0.0,
                             maxValue=100.0, keyable=True)

        self.controllers.extend(self.fkControllers)
        self.controllers.extend(self.ikControllers)

        # SWITCH Controller
        if self.switchMode == 0:
            scale_mult = functions.get_distance(self.ikJoints[0], self.ikJoints[1]) * 0.5
            self.switch_controller = Controller(
                shape="FkikSwitch",
                name=naming.parse([self.module_name, "FKIK", "switch"], suffix="cont"),
                scale=(scale_mult, scale_mult, scale_mult),
            )
            self.controllers.append(self.switch_controller)
            cmds.parent(self.switch_controller.name, ik_bind_grp)


    def createRoots(self):
        pass

    def createIKsetup(self):
        if self.switchMode == 1: # if it is FK only
            return

        ik_joints = self.deformerJoints if self.switchMode != 0 else self.ikJoints

        if self.ikSolver == 0:
            solver = "ikSCsolver"
        elif self.ikSolver == 1:
            solver = "ikRPsolver"
        elif self.ikSolver == 2:
            mel.eval("ikSpringSolver;")
            solver = "ikSpringSolver"
        else:
            log.error("Unidentified Solver")
            raise

        # ik_handle = cmds.ikHandle(startJoint=ik_joints[0], endEffector=ik_joints[-1], name="ikHandle_%s" % self.module_name, solver=solver)[0]
        ik_handle = cmds.ikHandle(startJoint=ik_joints[0], endEffector=ik_joints[-1], name=naming.parse([self.module_name], suffix="IKHandle"), solver=solver)[0]
        cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" %ik_handle)
        cmds.parent(ik_handle, self.nonScaleGrp)
        if self.ikSolver != 0:
            cmds.poleVectorConstraint(self.polevector_bridge, ik_handle)
            connection.matrixConstraint(self.polevector_cont.name, self.polevector_bridge, maintainOffset=False, source_parent_cutoff=self.localOffGrp)
            cmds.parent(self.polevector_bridge, self.nonScaleGrp)
            cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % self.polevector_bridge)

        # scaling
        _ = [cmds.connectAttr("%s.s" %ik_joints[0], "%s.s" %jnt) for jnt in ik_joints[1:]]

        if self.stretchyIk:
            stretch_locs = make_stretchy_ik(ik_joints, ik_handle, self.rootIkCont.name, self.endIKCont.name, side=self.side,
                                            source_parent_cutoff=self.localOffGrp, name=self.module_name)
            cmds.parent(stretch_locs, self.nonScaleGrp)
            attribute.drive_attrs("%s.rigVis" % self.scaleGrp, ["%s.v" % x for x in stretch_locs])
        else:
            connection.matrixConstraint(self.ikControllers[-1].name, ik_handle, maintainOffset=True, source_parent_cutoff=self.localOffGrp)
        connection.matrixConstraint(self.ikControllers[0].name, ik_joints[0], maintainOffset=False, source_parent_cutoff=self.localOffGrp)
        connection.matrixConstraint(self.ikControllers[-1].name, ik_joints[-1], skipTranslate="xyz", skipScale="xyz", maintainOffset=False, source_parent_cutoff=self.localOffGrp)

    def createFKsetup(self):
        if self.switchMode == 2: # if it is IK only
            return

        fk_joints = self.deformerJoints if self.switchMode != 0 else self.fkJoints

        # for cont, jnt in zip(self.fkControllers, fk_joints[:-1]):
        for cont, jnt in zip(self.fkControllers, fk_joints):
            # connection.matrixConstraint(cont, jnt, source_parent_cutoff=self.localOffGrp)
            connection.matrixConstraint(cont.name, jnt, source_parent_cutoff=self.localOffGrp, skipScale="xyz")
            if not self.isLocal:
                # additive scalability
                s_global = cmds.createNode("multiplyDivide", name=naming.parse([self.module_name, "sGlobal", jnt], suffix="mult"))
                cmds.connectAttr("%s.scale" % self.scaleHook, "%s.input1" % s_global)
                cmds.connectAttr("%s.scale" % cont.name, "%s.input2" % s_global)
                cmds.connectAttr("%s.output" % s_global, "%s.scale" % jnt)
            else:
                cmds.connectAttr("%s.scale" % cont.name, "%s.scale" % jnt)
            # disconnect inverse scale chain to inherit the scale from the controllers properly
            # attribute.disconnect_attr(node=jnt, attr="inverseScale", suppress_warnings=True)

        if self.isLocal:
            connection.matrixConstraint(self.limbPlug, self.plugBindGrp)
        else:
            # for off in self.fkControllersOff:
            #     connection.matrixConstraint(self.limbPlug, off)
            connection.matrixConstraint(self.limbPlug, self.fkControllersOff[0])

    def ikfkSwitching(self):
        if self.switchMode != 0:
            return
        # create blend nodes

        for fk_jnt, ik_jnt, def_jnt in zip(self.fkJoints, self.ikJoints, self.deformerJoints):
            # connection.matrixSwitch(ik_jnt, fk_jnt, def_jnt, "%s.FK_IK" % self.switchController)

            blend_t = cmds.createNode("blendColors", name=naming.parse([self.module_name, "translate"], suffix="blend"))
            blend_r = cmds.createNode("blendColors", name=naming.parse([self.module_name, "rotate"], suffix="blend"))
            blend_s = cmds.createNode("blendColors", name=naming.parse([self.module_name, "scale"], suffix="blend"))

            cmds.connectAttr("%s.translate" %fk_jnt, "%s.color1" %blend_t)
            cmds.connectAttr("%s.rotate" %fk_jnt, "%s.color1" %blend_r)
            cmds.connectAttr("%s.scale" %fk_jnt, "%s.color1" %blend_s)
            cmds.connectAttr("%s.translate" %ik_jnt, "%s.color2" %blend_t)
            cmds.connectAttr("%s.rotate" %ik_jnt, "%s.color2" %blend_r)
            cmds.connectAttr("%s.scale" %ik_jnt, "%s.color2" %blend_s)

            cmds.connectAttr("%s.output" %blend_t, "%s.translate" %def_jnt)
            cmds.connectAttr("%s.output" %blend_r, "%s.rotate" %def_jnt)
            cmds.connectAttr("%s.output" %blend_s, "%s.scale" %def_jnt)

            cmds.connectAttr("%s.fk_ik_reverse" % self.switch_controller.name, "%s.blender" % blend_t)
            cmds.connectAttr("%s.fk_ik_reverse" % self.switch_controller.name, "%s.blender" % blend_r)
            cmds.connectAttr("%s.fk_ik_reverse" % self.switch_controller.name, "%s.blender" % blend_s)

        for ik_co in self.ikControllers:
            cmds.connectAttr("%s.fk_ik" % (self.switch_controller.name), "%s.v" % ik_co.name)
        if self.ikSolver != 0:
            cmds.connectAttr("%s.fk_ik" % self.switch_controller.name, "%s.v" % self.polevector_cont.name)
        for fk_co in self.fkControllers:
            cmds.connectAttr("%s.fk_ik_reverse" % (self.switch_controller.name), "%s.v" % fk_co.name)

    def createRibbons(self):
        pass

    def createTwistSplines(self):
        pass

    def createAngleExtractors(self):
        pass

    def roundUp(self):
        # cmds.parentConstraint(self.limbPlug, self.scaleGrp, mo=False)
        cmds.setAttr("%s.rigVis" % self.scaleGrp, 0)

        self.scaleConstraints.append(self.scaleGrp)
        # lock and hide
        _ = [cont.lock_visibility for cont in self.controllers]

        # color
        # functions.colorize(self.fkControllers, self.colorCodes[0])
        # functions.colorize(self.ikControllers, self.colorCodes[0])
        # functions.colorize(self.polevector_cont, self.colorCodes[0])
        # functions.colorize(self.switch_controller, self.colorCodes[0])

    def createLimb(self):
        self.createGrp()
        self.createJoints()
        self.createControllers()
        self.createRoots()
        self.createIKsetup()
        self.createFKsetup()
        self.ikfkSwitching()
        self.createRibbons()
        self.createTwistSplines()
        self.createAngleExtractors()
        self.roundUp()


class Guides(object):
    def __init__(self, side="L", name="fkik", segments=None, tMatrix=None, upVector=(0, 1, 0), mirrorVector=(1, 0, 0), lookVector=(0, 0, 1), *args, **kwargs):
        super(Guides, self).__init__()
        # fool check

        #-------Mandatory------[Start]
        self.side = side
        self.sideMultiplier = -1 if side == "R" else 1
        self.name = name
        self.segments = segments or 1
        self.tMatrix = om.MMatrix(tMatrix) if tMatrix else om.MMatrix()
        self.upVector = om.MVector(upVector)
        self.mirrorVector = om.MVector(mirrorVector)
        self.lookVector = om.MVector(lookVector)

        self.offsetVector = None
        self.guideJoints = []
        #-------Mandatory------[End]

    def draw_joints(self):
        # fool check
        if not self.segments or self.segments < 1:
            log.warning("minimum segments required for the fk/ik module is two. current: %s" % self.segments)
            return

        # rPointTail = om.MVector(0, 0, 0) * self.tMatrix
        if self.side == "C":
            # Guide joint positions for limbs with no side orientation
            rPointTail = om.MVector(0, 0, -1) * self.tMatrix
            nPointTail = om.MVector(0, 0, -11) * self.tMatrix
        else:
            # Guide joint positions for limbs with sides
            rPointTail = om.MVector(1 * self.sideMultiplier, 0, 0) * self.tMatrix
            nPointTail = om.MVector(11 * self.sideMultiplier, 0, 0) * self.tMatrix
            pass

        # Define the offset vector
        self.offsetVector = (nPointTail - rPointTail).normal()
        seperation_value = (nPointTail - rPointTail) / ((self.segments + 1) - 1)

        # Draw the joints
        zig_zag = 1

        for seg in range(self.segments + 1):
            zig_zag_offset = om.MVector(0, zig_zag*0.3, 0)
            jnt = cmds.joint(position=(rPointTail + (seperation_value * seg) + zig_zag_offset), name=naming.parse([self.name, seg], side=self.side, suffix="jInit"))

            joint.set_joint_side(jnt, self.side)
            # Update the guideJoints list
            self.guideJoints.append(jnt)
            zig_zag = zig_zag*(-1)

        # set orientation of joints
        joint.orient_joints(self.guideJoints, world_up_axis=self.lookVector, up_axis=(0, 1, 0), reverse_aim=self.sideMultiplier, reverse_up=self.sideMultiplier)

    def define_attributes(self):
        # set joint side and type attributes
        joint.set_joint_type(self.guideJoints[0], "FkikRoot")
        _ = [joint.set_joint_type(jnt, "Fkik") for jnt in self.guideJoints[1:]]
        _ = [joint.set_joint_side(jnt, self.side) for jnt in self.guideJoints]

        # ----------Mandatory---------[Start]
        root_jnt = self.guideJoints[0]
        attribute.create_global_joint_attrs(root_jnt, moduleName="%s_fkik" % self.side, upAxis=self.upVector, mirrorAxis=self.mirrorVector, lookAxis=self.lookVector)
        # ----------Mandatory---------[End]

        for attr_dict in LIMB_DATA["properties"]:
            attribute.create_attribute(root_jnt, attr_dict)

    def createGuides(self):
        self.draw_joints()
        self.define_attributes()

    def convertJoints(self, joints_list):
        if len(joints_list) < 2:
            log.warning("Define or select at least 2 joints for FK Guide conversion. Skipping")
            return
        self.guideJoints = joints_list
        self.define_attributes()