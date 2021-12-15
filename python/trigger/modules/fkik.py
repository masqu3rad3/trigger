from maya import cmds
from maya import mel
import maya.api.OpenMaya as om
from trigger.library import api
from trigger.library import functions
from trigger.library import connection
from trigger.library import naming
from trigger.library import attribute
from trigger.library import controllers as ic
from trigger.library import arithmetic as op

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
            if (len(inits) < 2):
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
        self.side = functions.get_joint_side(self.fkRoot)
        self.sideMult = -1 if self.side == "R" else 1
        self.isLocal = bool(cmds.getAttr("%s.localJoints" % self.inits[0]))
        self.switchMode = int(cmds.getAttr("%s.switchMode" % self.inits[0]))
        self.stretchyIk = bool(cmds.getAttr("%s.stretchyIk" % self.inits[0]))
        self.ikSolver = int(cmds.getAttr("%s.ikSolver" % self.inits[0]))

        # initialize coordinates
        self.up_axis, self.mirror_axis, self.look_axis = functions.getRigAxes(self.inits[0])

        # initialize suffix
        self.suffix = (naming.uniqueName(cmds.getAttr("%s.moduleName" % self.inits[0])))

        # module specific variables
        self.fkJoints = []
        self.ikJoints = []
        self.fkControllers = []
        self.ikControllers = []
        self.rootIkCont = None
        self.endIKCont = None
        self.fkControllersOff = []
        self.ikControllersOff = []
        self.switchController = None
        self.poleVectorBridge = None
        self.poleVectorCont = None
        self.middleIndex = 1

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

        cmds.parent(self.scaleGrp, self.limbGrp)
        cmds.parent(self.nonScaleGrp, self.limbGrp)

        self.localOffGrp = cmds.group(name="%s_localOffset_grp" %self.suffix, em=True)
        self.plugBindGrp = cmds.group(name="%s_plugBind_grp" %self.suffix, em=True)
        cmds.parent(self.localOffGrp, self.plugBindGrp)
        cmds.parent(self.plugBindGrp, self.limbGrp)

    def createJoints(self):
        # draw Joints
        cmds.select(d=True)
        self.limbPlug = cmds.joint(name="limbPlug_%s" % self.suffix, p=api.getWorldTranslation(self.inits[0]), radius=3)

        cmds.select(d=True)
        for j in self.inits:
            jnt = cmds.joint(name="jDef_{0}_{1}".format(j, self.suffix))
            self.sockets.append(jnt)
            self.deformerJoints.append(jnt)

        if not self.useRefOrientation:
            functions.orientJoints(self.deformerJoints, worldUpAxis=(self.look_axis), upAxis=(0, 1, 0), reverseAim=self.sideMult, reverseUp=self.sideMult)
        else:
            for x in range (len(self.deformerJoints)):
                functions.alignTo(self.deformerJoints[x], self.inits[x], position=True, rotation=True)
                cmds.makeIdentity(self.deformerJoints[x], a=True)

        cmds.parent(self.deformerJoints[0], self.nonScaleGrp)

        # If the switch mode is fk&ik create duplicate chain for each
        if self.switchMode == 0:
            self.fkJoints=[]
            self.ikJoints=[]
            dupsIK = cmds.duplicate(self.deformerJoints[0], renameChildren=True)
            for dup, original in zip(dupsIK, self.inits):
                jnt = cmds.rename(dup, "jnt_IK_{0}_{1}".format(original, self.suffix))
                self.ikJoints.append(jnt)

            dupsFK = cmds.duplicate(self.deformerJoints[0], renameChildren=True)
            for dup, original in zip(dupsFK, self.inits):
                jnt = cmds.rename(dup, "jnt_FK_{0}_{1}".format(original, self.suffix))
                self.fkJoints.append(jnt)

            attribute.drive_attrs("%s.rigVis" % self.scaleGrp, ["%s.v" % x for x in self.ikJoints])
            attribute.drive_attrs("%s.rigVis" % self.scaleGrp, ["%s.v" % x for x in self.fkJoints])

        attribute.drive_attrs("%s.jointVis" % self.scaleGrp, ["%s.v" % x for x in self.deformerJoints])
        cmds.connectAttr("%s.jointVis" % self.scaleGrp,"%s.v" % self.limbPlug)
        functions.colorize(self.deformerJoints, self.colorCodes[0], shape=False)

    def createControllers(self):
        icon_handler = ic.Icon()


        # FK Controllers
        if self.switchMode == 0 or self.switchMode == 1:
            fk_joints = self.deformerJoints if self.switchMode != 0 else self.fkJoints
            # for nmb, jnt in enumerate(fk_joints[:-1]):
            scale_mult = None
            for nmb, jnt in enumerate(fk_joints):
                if nmb < (len(fk_joints)-1):
                    scale_mult = functions.getDistance(jnt, fk_joints[nmb + 1]) * 0.5

                cont, _ = icon_handler.createIcon("Cube", iconName="%s%i_FK_cont" % (self.suffix, nmb),
                                                  scale=(scale_mult, scale_mult, scale_mult))

                cmds.xform(cont, piv=(self.sideMult * (-scale_mult), 0, 0))
                functions.alignToAlter(cont, jnt, 2)

                cont_OFF = functions.createUpGrp(cont, "OFF", freezeTransform=True)
                cont_ORE = functions.createUpGrp(cont, "ORE")
                cmds.makeIdentity(cont, a=True)

                self.fkControllers.append(cont)
                self.fkControllersOff.append(cont_OFF)

                if nmb is not 0:
                    cmds.parent(self.fkControllersOff[nmb], self.fkControllers[nmb - 1])
            cmds.parent(self.fkControllersOff[0], self.localOffGrp)

            attribute.drive_attrs("%s.contVis" % self.scaleGrp, ["%s.v" % x for x in self.fkControllersOff])
            functions.colorize(self.controllers, self.colorCodes[0])

        # IK Controllers
        if self.switchMode == 0 or self.switchMode == 2:
            ik_joints = self.deformerJoints if self.switchMode != 0 else self.ikJoints
            ik_bind_grp = cmds.group(name="%s_IK_bind_grp" %self.suffix, em=True)
            cmds.parent(ik_bind_grp, self.localOffGrp)
            connection.matrixConstraint(self.limbPlug, ik_bind_grp, mo=True)

            scale_mult = functions.getDistance(ik_joints[0], ik_joints[1]) * 0.5
            self.rootIkCont, _ = icon_handler.createIcon("Circle", iconName="%s_rootIK_cont" % self.suffix, normal=(1,0,0), scale=(scale_mult, scale_mult, scale_mult))
            self.ikControllers.append(self.rootIkCont)
            root_ik_cont_off = functions.createUpGrp(self.rootIkCont, "OFF")
            self.ikControllersOff.append(root_ik_cont_off)
            functions.alignTo(root_ik_cont_off, ik_joints[0], rotation=True, position=True)

            self.endIKCont, _ = icon_handler.createIcon("Circle", iconName="%s_endIK_cont" % self.suffix, normal=(1,0,0), scale=(scale_mult, scale_mult, scale_mult))
            self.ikControllers.append(self.endIKCont)
            end_ik_cont_off = functions.createUpGrp(self.endIKCont, "OFF")
            self.ikControllersOff.append(end_ik_cont_off)
            functions.alignTo(end_ik_cont_off, ik_joints[-1], rotation=True, position=True)

            cmds.parent(root_ik_cont_off, ik_bind_grp)
            cmds.parent(end_ik_cont_off, ik_bind_grp)
            # POLE Vector
            if self.ikSolver != 0: # if it is a rotate plane or spring solver
                # create a bridge locator to stay with the local joints

                scale_mult = functions.getDistance(ik_joints[0], ik_joints[-1]) * 0.1
                self.poleVectorBridge = cmds.spaceLocator(name="poleVectorBridge_%s" %self.suffix)[0]
                self.poleVectorCont, _ = icon_handler.createIcon("Plus", iconName="%s_Pole_cont" % self.suffix, scale=(scale_mult, scale_mult, scale_mult),
                                                      normal=(self.sideMult, 0, 0))
                offset_magnitude = scale_mult
                self.middleIndex = int((len(ik_joints)-1)*0.5)
                offset_vector = api.getBetweenVector(ik_joints[self.middleIndex], ik_joints)

                functions.alignAndAim(self.poleVectorBridge,
                                      targetList=[ik_joints[self.middleIndex]],
                                      aimTargetList=ik_joints,
                                      upVector=self.up_axis,
                                      translateOff=(offset_vector * offset_magnitude)
                                      )

                functions.alignTo(self.poleVectorCont, self.poleVectorBridge, position=True, rotation=True)
                pole_cont_off = functions.createUpGrp(self.poleVectorCont, "OFF")
                # connection.matrixConstraint(self.poleVectorBridge, self.poleVectorCont, mo=False, source_parent_cutoff=self.localOffGrp)
                cmds.parent(pole_cont_off, ik_bind_grp)

            if self.stretchyIk:
                cmds.addAttr(self.endIKCont, shortName="squash", longName="Squash", defaultValue=0.0, minValue=0.0,
                             maxValue=1.0, at="double", k=True)
                cmds.addAttr(self.endIKCont, shortName="stretch", longName="Stretch", defaultValue=1.0, minValue=0.0,
                             maxValue=1.0, at="double", k=True)
                cmds.addAttr(self.endIKCont, shortName="stretchLimit", longName="StretchLimit", defaultValue=100.0,
                             minValue=0.0, maxValue=1000.0, at="double", k=True)
                cmds.addAttr(self.endIKCont, shortName="softIK", longName="SoftIK", defaultValue=0.0, minValue=0.0,
                             maxValue=100.0, k=True)

        self.controllers.extend(self.fkControllers)
        self.controllers.extend(self.ikControllers)

        # SWITCH Controller
        if self.switchMode == 0:
            scale_mult = functions.getDistance(self.ikJoints[0], self.ikJoints[1]) * 0.5
            self.switchController, _ = icon_handler.createIcon("FkikSwitch", iconName="%s_FK_IK_cont" % self.suffix,
                                                        scale=(scale_mult, scale_mult, scale_mult))
            self.controllers.append(self.switchController)
            cmds.parent(self.switchController, ik_bind_grp)


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

        ik_handle = cmds.ikHandle(sj=ik_joints[0], ee=ik_joints[-1], name="ikHandle_%s" % self.suffix, sol=solver)[0]
        cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" %ik_handle)
        cmds.parent(ik_handle, self.nonScaleGrp)
        if self.ikSolver != 0:
            cmds.poleVectorConstraint(self.poleVectorBridge, ik_handle)
            connection.matrixConstraint(self.poleVectorCont, self.poleVectorBridge, mo=False, source_parent_cutoff=self.localOffGrp)
            cmds.parent(self.poleVectorBridge, self.nonScaleGrp)
            cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" %self.poleVectorBridge)

        # scaling
        _ = [cmds.connectAttr("%s.s" %ik_joints[0], "%s.s" %jnt) for jnt in ik_joints[1:]]

        if self.stretchyIk:
            stretch_locs = self.make_stretchy_ik(ik_joints, ik_handle, self.rootIkCont, self.endIKCont, source_parent_cutoff=self.localOffGrp, name=self.suffix)
            cmds.parent(stretch_locs, self.nonScaleGrp)
            attribute.drive_attrs("%s.rigVis" % self.scaleGrp, ["%s.v" % x for x in stretch_locs])
        else:
            connection.matrixConstraint(self.ikControllers[-1], ik_handle, mo=False, source_parent_cutoff=self.localOffGrp)
        connection.matrixConstraint(self.ikControllers[0], ik_joints[0], mo=False, source_parent_cutoff=self.localOffGrp)
        connection.matrixConstraint(self.ikControllers[-1], ik_joints[-1], st="xyz", ss="xyz", mo=False, source_parent_cutoff=self.localOffGrp)

    def createFKsetup(self):
        if self.switchMode == 2: # if it is IK only
            return

        fk_joints = self.deformerJoints if self.switchMode != 0 else self.fkJoints

        # for cont, jnt in zip(self.fkControllers, fk_joints[:-1]):
        for cont, jnt in zip(self.fkControllers, fk_joints):
            connection.matrixConstraint(cont, jnt, source_parent_cutoff=self.localOffGrp)
            # disconnect inverse scale chain to inherit the scale from the controllers properly
            attribute.disconnect_attr(node=jnt, attr="inverseScale")

        if self.isLocal:
            connection.matrixConstraint(self.limbPlug, self.plugBindGrp)
        else:
            connection.matrixConstraint(self.limbPlug, self.fkControllersOff[0])

    def ikfkSwitching(self):
        if self.switchMode != 0:
            return
        # create blend nodes


        for fk_jnt, ik_jnt, def_jnt in zip(self.fkJoints, self.ikJoints, self.deformerJoints):
            blend_t = cmds.createNode("blendColors", name="%s_blend_t" %self.suffix)
            blend_r = cmds.createNode("blendColors", name="%s_blend_r" %self.suffix)
            blend_s = cmds.createNode("blendColors", name="%s_blend_s" %self.suffix)

            cmds.connectAttr("%s.translate" %fk_jnt, "%s.color1" %blend_t)
            cmds.connectAttr("%s.rotate" %fk_jnt, "%s.color1" %blend_r)
            cmds.connectAttr("%s.scale" %fk_jnt, "%s.color1" %blend_s)
            cmds.connectAttr("%s.translate" %ik_jnt, "%s.color2" %blend_t)
            cmds.connectAttr("%s.rotate" %ik_jnt, "%s.color2" %blend_r)
            cmds.connectAttr("%s.scale" %ik_jnt, "%s.color2" %blend_s)

            cmds.connectAttr("%s.output" %blend_t, "%s.translate" %def_jnt)
            cmds.connectAttr("%s.output" %blend_r, "%s.rotate" %def_jnt)
            cmds.connectAttr("%s.output" %blend_s, "%s.scale" %def_jnt)

            cmds.connectAttr("%s.fk_ik_reverse" %self.switchController, "%s.blender" %blend_t)
            cmds.connectAttr("%s.fk_ik_reverse" %self.switchController, "%s.blender" %blend_r)
            cmds.connectAttr("%s.fk_ik_reverse" %self.switchController, "%s.blender" %blend_s)

        for ik_co in self.ikControllers:
            cmds.connectAttr("%s.fk_ik" %(self.switchController), "%s.v" %ik_co)
        if self.ikSolver != 0:
            cmds.connectAttr("%s.fk_ik" %self.switchController, "%s.v" %self.poleVectorCont)
        for fk_co in self.fkControllers:
            cmds.connectAttr("%s.fk_ik_reverse" %(self.switchController), "%s.v" %fk_co)

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
        _ = [attribute.lockAndHide(cont, ["v"]) for cont in self.controllers]

        # color
        functions.colorize(self.fkControllers, self.colorCodes[0])
        functions.colorize(self.ikControllers, self.colorCodes[0])
        functions.colorize(self.poleVectorCont, self.colorCodes[0])
        functions.colorize(self.switchController, self.colorCodes[0])

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

    @staticmethod
    def make_stretchy_ik(joint_chain, ik_handle, root_controller, end_controller, source_parent_cutoff=None, name=None):
        if not name:
            name = joint_chain[0]

        attribute.validate_attr("%s.squash" %end_controller, attr_type="double", attr_range=[0.0, 1.0], default_value=0.0)
        attribute.validate_attr("%s.stretch" %end_controller, attr_type="double", attr_range=[0.0, 1.0], default_value=1.0)
        attribute.validate_attr("%s.stretchLimit" %end_controller, attr_type="double", attr_range=[0.0, 99999.0], default_value=100.0)
        attribute.validate_attr("%s.softIK" %end_controller, attr_type="double", attr_range=[0.0, 100.0], default_value=0.0)

        root_loc = cmds.spaceLocator(name="rootLoc_%s" %name)[0]
        connection.matrixConstraint(root_controller, root_loc, sr="xyz", mo=False)
        cmds.aimConstraint(end_controller, root_loc, wuo=root_controller)

        end_loc = cmds.spaceLocator(name="endLoc_%s" %name)[0]
        end_loc_shape = functions.getShapes(end_loc)[0]
        functions.alignTo(end_loc, end_controller, position=True, rotation=True)
        cmds.parent(end_loc, root_loc)
        soft_blend_loc = cmds.spaceLocator(name="softBlendLoc_%s" %name)[0]
        soft_blend_loc_shape = functions.getShapes(soft_blend_loc)[0]
        functions.alignTo(soft_blend_loc, end_controller, position=True, rotation=True)
        connection.matrixSwitch(end_controller, end_loc, soft_blend_loc, "%s.stretch" %end_controller, position=True, rotation=False)

        distance_start_loc =cmds.spaceLocator(name="distance_start_%s" %name)[0]
        connection.matrixConstraint(root_controller, distance_start_loc, sr="xyz", ss="xyz", mo=False)

        distance_end_loc =cmds.spaceLocator(name="distance_end_%s" %name)[0]
        connection.matrixConstraint(end_controller, distance_end_loc, sr="xyz", ss="xyz", mo=False)

        ctrl_distance = cmds.createNode("distanceBetween", name="distance_%s" % name)
        cmds.connectAttr("%s.translate" %distance_start_loc, "%s.point1" %ctrl_distance)
        cmds.connectAttr("%s.translate" %distance_end_loc, "%s.point2" %ctrl_distance)
        ctrl_distance_p = "%s.distance" %ctrl_distance


        plugs_to_sum = []
        for nmb, jnt in enumerate(joint_chain[1:]):
            dist = functions.getDistance(jnt, joint_chain[nmb])
            cmds.addAttr(jnt, ln="initialDistance", at="double", dv=dist)
            plugs_to_sum.append("%s.initialDistance" %jnt)
            # cmds.connectAttr("%s.initialDistance" %jnt, "%s.input1D[%i]" %(sum_of_initial_lengths, nmb))

        sum_of_lengths_p = op.add(value_list=plugs_to_sum)

        # SOFT IK PART
        softIK_sub1_p = op.subtract(sum_of_lengths_p, "%s.softIK" %end_controller)
        # get the scale value from controller
        scale_multMatrix = cmds.createNode("multMatrix", name="_multMatrix")
        scale_decomposeMatrix = cmds.createNode("decomposeMatrix", name="_decomposeMatrix")
        cmds.connectAttr("%s.worldMatrix[0]" %root_controller, "%s.matrixIn[0]" %scale_multMatrix)
        cmds.connectAttr("%s.matrixSum" %scale_multMatrix, "%s.inputMatrix" %scale_decomposeMatrix)

        global_scale_div_p = op.divide(1, "%s.outputScaleX" %scale_decomposeMatrix)
        global_mult_p = op.multiply(ctrl_distance_p, global_scale_div_p)
        softIK_sub2_p = op.subtract(global_mult_p, softIK_sub1_p)
        softIK_div_p = op.divide(softIK_sub2_p, "%s.softIK" %end_controller)
        softIK_invert_p = op.invert(softIK_div_p)
        softIK_exponent_p = op.power(2.71828, softIK_invert_p)
        softIK_mult_p = op.multiply(softIK_exponent_p, "%s.softIK" %end_controller)
        softIK_sub3_p = op.subtract(sum_of_lengths_p, softIK_mult_p)

        condition_zero_p = op.if_else("%s.softIK" %end_controller, ">", 0, softIK_sub3_p, sum_of_lengths_p)
        condition_length_p = op.if_else(global_mult_p, ">", softIK_sub1_p, condition_zero_p, global_mult_p)

        cmds.connectAttr(condition_length_p, "%s.tx" %end_loc)

        # STRETCHING PART
        soft_distance = cmds.createNode("distanceBetween", name="distanceSoft_%s" % name)
        cmds.connectAttr("%s.worldPosition[0]" %end_loc_shape, "%s.point1" %soft_distance)
        cmds.connectAttr("%s.worldPosition[0]" %soft_blend_loc_shape, "%s.point2" %soft_distance)
        soft_distance_p = "%s.distance" %soft_distance

        stretch_global_div_p = op.divide(soft_distance_p, "%s.outputScaleX" %scale_decomposeMatrix, name="globalDivide")
        initial_divide_p = op.divide(ctrl_distance_p, sum_of_lengths_p)

        for jnt in joint_chain[1:]:
            div_initial_by_sum_p = op.divide("%s.initialDistance" %jnt, sum_of_lengths_p)
            mult1_p = op.multiply(stretch_global_div_p, div_initial_by_sum_p)
            mult2_p = op.multiply("%s.stretch" %end_controller, mult1_p)
            sum1_p = op.add(mult2_p, "%s.initialDistance" %jnt)
            squash_mult_p = op.multiply(initial_divide_p, "%s.initialDistance" %jnt)

            squash_blend_node = cmds.createNode("blendColors", name="squash_blend_%s" %name)
            cmds.connectAttr(squash_mult_p, "%s.color1R" %squash_blend_node)
            cmds.connectAttr(sum1_p, "%s.color2R" %squash_blend_node)
            cmds.connectAttr("%s.squash" %end_controller, "%s.blender" %squash_blend_node)

            cmds.connectAttr("%s.outputR" %squash_blend_node, "%s.tx" %jnt)

        connection.matrixConstraint(soft_blend_loc, ik_handle, mo=False, source_parent_cutoff=source_parent_cutoff)
        return soft_blend_loc, root_loc, distance_start_loc, distance_end_loc

class Guides(object):
    def __init__(self, side="L", suffix="fkik", segments=None, tMatrix=None, upVector=(0, 1, 0), mirrorVector=(1, 0, 0), lookVector=(0,0,1), *args, **kwargs):
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
            jnt = cmds.joint(p=(rPointTail + (seperation_value * seg) + zig_zag_offset), name="jInit_fkik_%s_%i" %(self.suffix, seg))

            functions.set_joint_side(jnt, self.side)
            # Update the guideJoints list
            self.guideJoints.append(jnt)
            zig_zag = zig_zag*(-1)

        # set orientation of joints
        functions.orientJoints(self.guideJoints, worldUpAxis=self.lookVector, upAxis=(0, 1, 0), reverseAim=self.sideMultiplier, reverseUp=self.sideMultiplier)

    def define_attributes(self):
        # set joint side and type attributes
        functions.set_joint_type(self.guideJoints[0], "FkikRoot")
        _ = [functions.set_joint_type(jnt, "Fkik") for jnt in self.guideJoints[1:]]
        _ = [functions.set_joint_side(jnt, self.side) for jnt in self.guideJoints]

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