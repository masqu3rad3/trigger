#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Creates a ribbon joint chain between given nodes"""

from maya import cmds
from trigger.library import functions, naming, connection
from trigger.library import arithmetic as op
from trigger.library import attribute
from trigger.library import controllers as ic

from trigger.objects.controller import Controller


class Ribbon(object):
    def __init__(self,
                 start_node=None,
                 end_node=None,
                 name=None,
                 ribbon_resolution=5,
                 joint_resolution=5,
                 controller_count=1,
                 controller_list=None,
                 dropoff=2.0,
                 connect_start_aim=True,
                 up_vector=(0, 1, 0),
                 scaleable=True
                 ):
        # input vars
        self._name = naming.uniqueName(name) if name else ""
        self._startNode = start_node
        self._endNode = end_node
        self._ribbonResolution = ribbon_resolution
        self._jointResolution = joint_resolution
        self._controllerCount = controller_count
        self._controllerList = controller_list
        self._dropoff = dropoff
        self._connectStartAim = connect_start_aim
        self._upVector = up_vector
        self._scaleable = scaleable

        # output vars
        self._startPlug = None
        self._endPlug = None
        self._ribbonGrp = None
        self._scaleGrp = None
        self._nonScaleGrp = None
        self._deformerJoints = []
        self._controllers = []
        self._toHide = []
        self._startAim = None
        self._endAim = None
        self._startUp = None
        self._endUp = None


    # INPUT Properties
    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @property
    def start_node(self):
        return self._startNode

    @start_node.setter
    def start_node(self, node):
        self._startNode = node

    @property
    def end_node(self):
        return self._endNode

    @end_node.setter
    def end_node(self, node):
        self._endNode = node

    @property
    def ribbon_resolution(self):
        return self._ribbonResolution

    @ribbon_resolution.setter
    def ribbon_resolution(self, val):
        self._ribbonResolution = val

    @property
    def joint_resolution(self):
        return self._jointResolution

    @joint_resolution.setter
    def joint_resolution(self, val):
        self._jointResolution = val

    @property
    def controller_count(self):
        return self._controllerCount

    @controller_count.setter
    def controller_count(self, val):
        self._controllerCount = val

    @property
    def controller_list(self):
        return self._controllerList

    @controller_list.setter
    def controller_list(self, val):
        self._controllerList = val

    @property
    def dropoff(self):
        return self._dropoff

    @dropoff.setter
    def dropoff(self, val):
        self._dropoff = val

    @property
    def connect_start_aim(self):
        return self._connectStartAim

    @connect_start_aim.setter
    def connect_start_aim(self, val):
        self._connectStartAim = val

    @property
    def up_vector(self):
        return self._upVector

    @up_vector.setter
    def up_vector(self, val):
        self._upVector = val

    @property
    def scaleable(self):
        return self._scaleable

    @scaleable.setter
    def scaleable(self, val):
        self._scaleable = val

    # OUTPUT Properties

    @property
    def start_plug(self):
        return self._startPlug

    @property
    def end_plug(self):
        return self._endPlug

    @property
    def scale_grp(self):
        return self._scaleGrp

    @property
    def nonscale_grp(self):
        return self._nonScaleGrp

    @property
    def deformer_joints(self):
        return self._deformerJoints

    @property
    def controllers(self):
        return self._controllers

    @property
    def start_aim(self):
        return self._startAim

    @property
    def end_aim(self):
        return self._endAim

    @property
    def start_up(self):
        return self._startUp

    @property
    def end_up(self):
        return self._endUp

    @property
    def to_hide(self):
        return self._toHide

    def pin_start(self, node_a, node_b=None, switch_a=None, switch_b=None):
        """
        Connects the start of the ribbon to given controller(s)

        Args:
            node_a: (String) The first controller that the start will be pinned to
            node_b: (String) If defined, the start will be pinned to both nodes
            switch_a: (String) Attribute that will drive the first switch. Optional
            switch_b: (String) Attribute that will drive the first switch. Optional

        Returns:
            (String) Parent Constraint

        """
        nodes = [node_a, node_b] if node_b else node_a
        constraint = cmds.parentConstraint(nodes, self._startPlug, mo=True)
        self._switch_weights(nodes, [switch_a, switch_b], constraint)
        return constraint
    #
    # def pin_start(self, node_a, node_b=None, switch_a=None, switch_b=None):
    #     nodes = [node_a, node_b] if node_b else node_a
    #     _, __, ave = connection.matrixConstraint(nodes, self._startPlug, mo=True, ss="xyz")
    #
    #     for nmb, sw in enumerate([switch_a, switch_b]):
    #         if sw:
    #             cmds.connectAttr("%s.wtMatrix[%i].weightIn" % (ave, nmb), sw)
    #     if switch_a and not switch_b:
    #         attribute.drive_attrs(switch_a, ["%s.wtMatrix[1].weightIn" % ave], [0, 1], [1, 0])


    def pin_end(self, node_a, node_b=None, switch_a=None, switch_b=None):
        """
        Connects the end of the ribbon to given controller(s)

        Args:
            node_a: (String) The first controller that the end will be pinned to
            node_b: (String) If defined, the end will be pinned to both nodes
            switch_a: (String) Attribute that will drive the first switch. Optional
            switch_b: (String) Attribute that will drive the first switch. Optional

        Returns:
            (String) Parent Constraint

        """
        nodes = [node_a, node_b] if node_b else node_a
        constraint = cmds.parentConstraint(nodes, self._endPlug, mo=True)
        self._switch_weights(nodes, [switch_a, switch_b], constraint)
        return constraint

    # def pin_end(self, node_a, node_b=None, switch_a=None, switch_b=None):
    #     nodes = [node_a, node_b] if node_b else node_a
    #     _, __, ave = connection.matrixConstraint(nodes, self._endPlug, mo=True, ss="xyz")
    #     for nmb, sw in enumerate([switch_a, switch_b]):
    #         if sw:
    #             cmds.connectAttr("%s.wtMatrix[%i].weightIn" % (ave, nmb), sw)
    #     if switch_a and not switch_b:
    #         attribute.drive_attrs(switch_a, ["%s.wtMatrix[1].weightIn" % ave], [0, 1], [1, 0])

        # if switch_a:
        #     cmds.connectAttr("%s.wtMatrix[0].weightIn" % ave, switch_a)
        # if switch_b:
        #     cmds.connectAttr("%s.wtMatrix[1].weightIn" % ave, switch_b)
        # else:
        #     attribute.drive_attrs(switch_a, ["%s.wtMatrix[1].weightIn" % ave], [0, 1], [1, 0])

    def orient(self, node_a, node_b=None, switch_a=None, switch_b=None):
        """
        Orients the start aim of the ribbon to given controller(s)

        Args:
            node_a: (String) The first controller that the end will be oriented to
            node_b: (String) If defined, the end will be oriented to both nodes
            switch_a: (String) Attribute that will drive the first switch. Optional
            switch_b: (String) Attribute that will drive the first switch. Optional

        Returns:
            (String) Parent Constraint (translates skipped)

        """
        nodes = [node_a, node_b] if node_b else node_a
        constraint = cmds.parentConstraint(nodes, self._startAim, mo=True, skipTranslate=["x", "y", "z"])[0]
        self._switch_weights(nodes, [switch_a, switch_b], constraint)
        return constraint

    @staticmethod
    def _switch_weights(nodes, switches, constraint):
        if not nodes or not any(switches):
            return
        attrs = cmds.listAttr(constraint, ud=True)
        for attr, sw in zip(attrs, switches):
            if sw:
                cmds.connectAttr(sw, "%s.%s" % (constraint, attr))

    def _validate(self):
        """Checks all variables are set before proceed"""

        if not self.start_node or \
                not self.end_node:
            return False
        else:
            return True

        # TODO: more validations

    def _create_groups(self):
        """Creates the holding groups"""

        self._ribbonGrp = cmds.group(name=self._name, em=True)
        self._scaleGrp = cmds.group(name="RBN_ScaleGrp_%s" % self._name, em=True)
        self._nonScaleGrp = cmds.group(name="RBN_nonScaleGrp_%s" % self._name, em=True)
        cmds.parent([self._scaleGrp, self._nonScaleGrp], self._ribbonGrp)

    def _initial_ribbon(self, length):
        """
        Creates the initial ribbon object centered to world 0

        Args:
            length: (flaot) the length of ribbon in world units

        Returns:
            (string) nurbs surface shape

        """
        n_surf_trans = \
            cmds.nurbsPlane(ax=(0, 0, 1), u=float(self._ribbonResolution), v=1, w=length,
                            lr=(1.0 / length),
                            name="nSurf_%s" % self._name)[0]
        cmds.parent(n_surf_trans, self._nonScaleGrp)
        cmds.rebuildSurface(n_surf_trans, ch=1, rpo=1, rt=0, end=1, kr=2, kcp=0, kc=0, su=5, du=3, sv=1, dv=1, tol=0,
                            fr=0, dir=1)
        cmds.makeIdentity(a=True)
        n_surf = functions.getShapes(n_surf_trans)[0]
        self._toHide.append(n_surf_trans)

        # Start up nodes
        cmds.select(d=True)
        self._startAim = cmds.group(em=True, name="jRbn_Start_CON_%s" % self._name)
        cmds.move(-(length * 0.5), 0, 0, self._startAim)
        cmds.makeIdentity(self._startAim, a=True)
        # start_ore = cmds.duplicate(self._startAim, name="jRbn_Start_ORE_%s" % self._name)[0]
        # cmds.parent(start_ore, self._startAim)

        self._startUp = cmds.spaceLocator(name="jRbn_StartUp_%s" % self._name)[0]
        self._toHide.append(functions.getShapes(self._startUp)[0])
        cmds.move(-(length * 0.5), 0.5, 0, self._startUp)

        self._startPlug = cmds.spaceLocator(name="jRbn_StartCn_%s" % self._name)[0]
        self._toHide.append(functions.getShapes(self._startPlug)[0])
        cmds.move(-(length * 0.5), 0, 0, self._startPlug)
        cmds.makeIdentity(self._startPlug, a=True)

        cmds.parent(self._startAim, self._startUp, self._startPlug)
        # cmds.parent(self._startPlug, self._scaleGrp)

        if self._scaleable:
            cmds.addAttr(self._startPlug, shortName="scaleSwitch", longName="Scale_Switch",
                         defaultValue=1.0, at="float", minValue=0.0, maxValue=1.0, k=True)

        # End Upnodes
        cmds.select(d=True)
        self._endAim = cmds.group(name="jRbn_End_%s_AIM" % self._name, em=True)
        cmds.move(-(length * -0.5), 0, 0, self._endAim)
        cmds.makeIdentity(self._endAim, a=True)
        self._endUp = cmds.spaceLocator(name="jRbn_End_%s_UP" % self._name)[0]
        self._toHide.append(functions.getShapes(self._endUp)[0])
        cmds.move(-(length * -0.5), 0.5, 0, self._endUp)

        self._endPlug = cmds.spaceLocator(name="jRbn_End_%s_endCon" % self._name)[0]
        self._toHide.append(functions.getShapes(self._endPlug)[0])
        cmds.move(-(length * -0.5), 0, 0, self._endPlug)
        cmds.makeIdentity(self._endPlug, a=True)

        return n_surf

    def _create_follicles(self, n_surf):

        follicle_list = []
        for index in range(int(self._jointResolution)):
            _name = "follicle_{0}{1}".format(self._name, index)
            _uv = (0.1 + (index / float(self._jointResolution)), 0.5)
            follicle_transform, follicle = connection.create_follicle(_name, n_surf, _uv)
            attribute.lockAndHide(follicle_transform, ["tx", "ty", "tz", "rx", "ry", "rz"], hide=False)
            def_j = cmds.joint(name="jDef_%s%i" % (self._name, index))
            cmds.joint(def_j, e=True, zso=True, oj='zxy')
            self._deformerJoints.append(def_j)
            cmds.parent(follicle_transform, self._nonScaleGrp)
            self._toHide.append(follicle)
            follicle_list.append(follicle)

        if self._scaleable:
            # create follicles for scaling calculations
            for index in range(int(self._jointResolution)):
                _name = "follicleSCA_%s%i" % (self._name, index)
                _uv = (0.1 + (index / float(self._jointResolution)), 0.0)
                follicle_transform, follicle = connection.create_follicle(_name, n_surf, _uv)
                attribute.lockAndHide(follicle_transform, ["tx", "ty", "tz", "rx", "ry", "rz"], hide=False)
                cmds.parent(follicle_transform, self._nonScaleGrp)
                dist_node = cmds.createNode("distanceBetween", name="fDistance_%s%i" % (self._name, index))
                cmds.connectAttr("%s.outTranslate" % follicle_list[index], "%s.point1" % dist_node)
                cmds.connectAttr("%s.outTranslate" % follicle, "%s.point2" % dist_node)

                mult_plug = op.multiply("%s.distance" % dist_node, 2)
                global_mult_plug = op.multiply(mult_plug, "%s.scaleX" % self._scaleGrp)
                global_div_plug = op.divide(global_mult_plug, "%s.scaleX" % self._scaleGrp)
                global_mixer = cmds.createNode("blendColors", name="fGlobMix_%s%i" % (self._name, index))

                for ch in "RGB":
                    cmds.connectAttr(global_div_plug, "{0}.color1{1}".format(global_mixer, ch))
                    cmds.setAttr("{0}.color2{1}".format(global_mixer, ch), 1)

                cmds.connectAttr("%s.output" % global_mixer, "%s.scale" % self._deformerJoints[index])
                cmds.connectAttr("%s.scaleSwitch" % self._startPlug, "%s.blender" % global_mixer)

        return follicle_list

    def _create_controllers(self, length):
        interval = length / (self._controllerCount + 1)

        for index in range(self._controllerCount):
            cont = Controller(name="cont_midRbn_%s%i" % (self._name, index+1),
                              shape="Star",
                              tier="secondary",
                              normal=(1,0,0),
                              pos=(-(length / 2.0) + (interval * (index + 1)), 0, 0),
                              )
            yield cont.name

    def _create_control_joints(self):
        cmds.select(d=True)
        start_joint = cmds.joint(name="jRbn_Start_%s" % self._name, radius=2)
        self._toHide.append(start_joint)
        functions.alignTo(start_joint, self._startAim)

        cmds.select(d=True)
        end_joint = cmds.joint(name="jRbn_End_%s" % self._name, radius=2)
        self._toHide.append(end_joint)
        functions.alignTo(end_joint, self._endAim)

    def create(self):
        if not self._validate():
            raise Exception("Start and/or End nodes are not defined")
        self._create_groups()

        ribbon_length = functions.getDistance(self.start_node, self.end_node)
        n_surf = self._initial_ribbon(ribbon_length)

        self._create_follicles(n_surf)

        # self._controllerList = list(self._create_controllers(ribbon_length))

        # cmds.error("WER")

        # create control joints
        cmds.select(d=True)
        start_joint = cmds.joint(name="jRbn_Start_%s" % self._name, radius=2)
        self._toHide.append(start_joint)
        functions.alignTo(start_joint, self._startAim)
        # cmds.move(-(ribbon_length / 2.0), 0, 0, start_joint)

        cmds.select(d=True)
        end_joint = cmds.joint(name="jRbn_End_%s" % self._name, radius=2)
        self._toHide.append(end_joint)
        cmds.move((ribbon_length / 2.0), 0, 0, end_joint)

        mid_joint_list = []
        counter = 0
        if self._controllerList:
            counter += 1
            for ctrl in self._controllerList:
                cmds.select(d=True)
                mid_j = cmds.joint(name="jRbn_Mid_%i_%s" % (counter, self._name), radius=2)
                functions.alignToAlter(mid_j, ctrl)
                mid_joint_list.append(mid_j)
        else:
            interval = ribbon_length / (self._controllerCount + 1)

            for index in range(self._controllerCount):
                counter += 1
                cmds.select(d=True)
                mid_j = cmds.joint(name="jRbn_Mid_%i_%s" % (index, self._name),
                                   p=(-(ribbon_length / 2.0) + (interval * counter), 0, 0), radius=2)
                mid_joint_list.append(mid_j)

        cmds.skinCluster(start_joint, end_joint, mid_joint_list, n_surf, tsb=True, dropoffRate=self._dropoff)

        # cmds.parent(start_joint, start_ore)
        cmds.parent(start_joint, self._startAim)
        if self._connectStartAim:
            # aim it to the next mid joint after the start
            cmds.aimConstraint(mid_joint_list[0], self._startAim, aimVector=(1, 0, 0), upVector=(0, 1, 0), wut=1,
                               wuo=self._startUp, mo=False)

        cmds.parent(self._endAim, self._endUp, self._endPlug)
        # cmds.parent(self._endPlug, self._scaleGrp)
        cmds.parent(end_joint, self._endAim)
        cmds.aimConstraint(mid_joint_list[-1], self._endAim, aimVector=(1, 0, 0), upVector=(0, 1, 0), wut=1,
                           wuo=self._endUp, mo=True)

        # middle_pos_list = []
        # counter = 0

        cmds.delete(cmds.pointConstraint([self._startPlug, self._endPlug], self._scaleGrp, mo=False)[0])

        cmds.makeIdentity(self._scaleGrp, a=True, t=True)

        cmds.parent([self._startPlug, self._endPlug], self._scaleGrp)


        for nmb, mid in enumerate(mid_joint_list):
            print(mid)
            # counter += 1
            mid_cont = Controller(shape="Circle", name="cont_midRbn_%s%i" % (self._name, nmb+1), normal=(1, 0, 0))
            # mid_con, _ = icon.createIcon("Circle", iconName="cont_midRbn_%s%i" % (self._name, nmb+1), normal=(1, 0, 0))
            self._controllers.append(mid_cont.name)
            middle_off = cmds.spaceLocator(name="mid_OFF_%s%i" % (self._name, nmb+1))[0]
            self._toHide.append(functions.getShapes(middle_off)[0])
            middle_aim = cmds.group(em=True, name="mid_AIM_%s%i" % (self._name, nmb+1))
            functions.alignTo(middle_aim, mid, position=True, rotation=False)
            middle_up = cmds.spaceLocator(name="mid_UP_{0}{1}".format(self._name, nmb+1))[0]
            self._toHide.append(functions.getShapes(middle_up)[0])

            functions.alignTo(middle_up, mid, position=True, rotation=False)
            cmds.setAttr("%s.ty" % middle_up, 0.5)

            middle_pos = cmds.spaceLocator(name="mid_POS_{0}{1}".format(self._name, nmb+1))[0]
            cmds.parent(middle_pos, self._scaleGrp)
            self._toHide.append(functions.getShapes(middle_pos)[0])
            functions.alignTo(middle_pos, mid, position=True, rotation=False)

            cmds.parent(mid, mid_cont.name)
            cmds.parent(mid_cont.name, middle_off)
            cmds.parent(middle_off, middle_aim)
            cmds.parent(middle_up, middle_aim, middle_pos)
            cmds.aimConstraint(self._startPlug, middle_aim, aimVector=(0, 0, -1), upVector=(0, 1, 0), wut=1,
                               wuo=middle_up, mo=True)
            cmds.pointConstraint(self._startPlug, self._endPlug, middle_pos)
            # connection.matrixConstraint([self._startPlug, self._endPlug], middle_pos, sr="xyz", ss="xyz")
            # connection.matrixConstraint([self._startPlug, self._endPlug], middle_pos, sr="xyz", ss="xyz", source_parent_cutoff="RBN_ScaleGrp_TESTTT")
            # pos_average_p = op.average_matrix(["%s.worldMatrix[0]" % self._startPlug, "%s.worldMatrix[0]" % self._endPlug])
            # pos_trans_p = op.decompose_matrix(pos_average_p)[0]
            # cmds.connectAttr(pos_trans_p, "%s.t" % middle_POS)
            cmds.pointConstraint(self._startUp, self._endUp, middle_up)
            # connection.matrixConstraint([self._startUp, self._endUp], middle_up, sr="xyz", ss="xyz")
            # connection.matrixConstraint([self._startUp, self._endUp], middle_up, sr="xyz", ss="xyz", source_parent_cutoff="RBN_ScaleGrp_TESTTT")
            # up_average_p = op.average_matrix(["%s.worldMatrix[0]" % self._startUp, "%s.worldMatrix[0]" % self._endUp])
            # up_trans_p = op.decompose_matrix(up_average_p)[0]
            # cmds.connectAttr(up_trans_p, "%s.t" % middle_up)


        # cmds.delete(cmds.pointConstraint([self._startPlug, self._endPlug], self._scaleGrp, mo=False)[0])
        #
        # cmds.makeIdentity(self._scaleGrp, a=True, t=True)
        #
        # cmds.parent([self._startPlug, self._endPlug] + middle_pos_list, self._scaleGrp)

        # for middle_pos, middle_up in zip(middle_pos_list, middle_up_list):
        #     connection.matrixConstraint([self._startPlug, self._endPlug], middle_pos, sr="xyz", ss="xyz")
        #     connection.matrixConstraint([self._startUp, self._endUp], middle_up, sr="xyz", ss="xyz")
            # cmds.pointConstraint(self._startPlug, self._endPlug, middle_pos)
            # cmds.pointConstraint(self._startUp, self._endUp, middle_up)


        functions.alignAndAim(self._scaleGrp, [self._startNode, self._endNode], [self._endNode],
                              upVector=self._upVector)


