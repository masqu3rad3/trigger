#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Creates a ribbon joint chain between given nodes"""

from maya import cmds
from trigger.library import functions, naming, connection
from trigger.library import arithmetic as op
from trigger.library import attribute

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
        self._name = naming.unique_name(name) if name else ""
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
    def ribbon_grp(self):
        return self._ribbonGrp

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
        constraint = cmds.parentConstraint(nodes, self._startPlug, maintainOffset=True)
        self._switch_weights(nodes, [switch_a, switch_b], constraint)
        return constraint

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
        constraint = cmds.parentConstraint(nodes, self._endPlug, maintainOffset=True)
        self._switch_weights(nodes, [switch_a, switch_b], constraint)
        return constraint

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
        constraint = cmds.parentConstraint(nodes, self._startAim, maintainOffset=True, skipTranslate=["x", "y", "z"])[0]
        self._switch_weights(nodes, [switch_a, switch_b], constraint)
        return constraint

    @staticmethod
    def _switch_weights(nodes, switches, constraint):
        if not nodes or not any(switches):
            return
        attrs = cmds.listAttr(constraint, userDefined=True)
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

        self._ribbonGrp = cmds.group(name=naming.parse(self._name, suffix="grp"), empty=True)
        self._scaleGrp = cmds.group(name=naming.parse([self._name, "RBN", "scale"], suffix="grp"), empty=True)
        self._nonScaleGrp = cmds.group(name=naming.parse([self._name, "RBN", "nonScale"], suffix="grp"), empty=True)
        cmds.parent([self._scaleGrp, self._nonScaleGrp], self._ribbonGrp)

    def _initial_ribbon(self, length):
        """
        Creates the initial ribbon object centered to world 0

        Args:
            length: (flaot) the length of ribbon in world units

        Returns:
            (string) nurbs surface shape

        """

        n_surf_trans = cmds.nurbsPlane(axis=(0, 0, 1),
                                       patchesU=int(self._ribbonResolution),
                                       patchesV=1,
                                       width=length,
                                       lengthRatio=(1.0 / length),
                                       name=naming.parse([self._name], suffix="nSurf")
                                       )[0]
        cmds.parent(n_surf_trans, self._nonScaleGrp)

        cmds.rebuildSurface(n_surf_trans,
                            constructionHistory=True,
                            replaceOriginal=True,
                            rebuildType=0,
                            endKnots=1,
                            keepRange=2,
                            keepControlPoints=False,
                            keepCorners=False,
                            spansU=5,
                            degreeU=3,
                            spansV=1,
                            degreeV=1,
                            tolerance=0,
                            fitRebuild=0,
                            direction=1
                            )
        cmds.makeIdentity(apply=True)
        n_surf = functions.get_shapes(n_surf_trans)[0]
        self._toHide.append(n_surf_trans)

        # Start up nodes
        cmds.select(clear=True)
        self._startAim = cmds.group(empty=True, name=naming.parse([self._name, "start", "aim"], suffix="grp"))
        cmds.move(-(length * 0.5), 0, 0, self._startAim)
        cmds.makeIdentity(self._startAim, apply=True)

        self._startUp = cmds.spaceLocator(name=naming.parse([self._name, "start", "up"], suffix="loc"))[0]
        self._toHide.append(functions.get_shapes(self._startUp)[0])
        cmds.move(-(length * 0.5), 0.5, 0, self._startUp)

        self._startPlug = cmds.spaceLocator(name=naming.parse([self._name, "start", "plug"], suffix="loc"))[0]
        self._toHide.append(functions.get_shapes(self._startPlug)[0])
        cmds.move(-(length * 0.5), 0, 0, self._startPlug)
        cmds.makeIdentity(self._startPlug, apply=True)

        cmds.parent(self._startAim, self._startUp, self._startPlug)
        # cmds.parent(self._startPlug, self._scaleGrp)

        if self._scaleable:
            cmds.addAttr(self._startPlug,
                         shortName="scaleSwitch",
                         longName="Scale_Switch",
                         defaultValue=1.0,
                         attributeType="float",
                         minValue=0.0,
                         maxValue=1.0,
                         keyable=True
                         )

        # End Upnodes
        cmds.select(clear=True)
        self._endAim = cmds.group(name=naming.parse([self._name, "end", "aim"], suffix="grp"), empty=True)
        cmds.move(-(length * -0.5), 0, 0, self._endAim)
        cmds.makeIdentity(self._endAim, apply=True)
        self._endUp = cmds.spaceLocator(name=naming.parse([self._name, "end", "up"], suffix="loc"))[0]
        self._toHide.append(functions.get_shapes(self._endUp)[0])
        cmds.move(-(length * -0.5), 0.5, 0, self._endUp)

        self._endPlug = cmds.spaceLocator(name=naming.parse([self._name, "end", "plug"], suffix="loc"))[0]
        self._toHide.append(functions.get_shapes(self._endPlug)[0])
        cmds.move(-(length * -0.5), 0, 0, self._endPlug)
        cmds.makeIdentity(self._endPlug, apply=True)

        return n_surf

    def _create_follicles(self, n_surf):

        follicle_list = []
        for index in range(int(self._jointResolution)):
            # _name = "follicle_{0}{1}".format(self._name, index)
            _name = naming.parse([self._name, index])
            _uv = (0.1 + (index / float(self._jointResolution)), 0.5)
            follicle_transform, follicle = connection.create_follicle(_name, n_surf, _uv)
            attribute.lock_and_hide(follicle_transform, ["tx", "ty", "tz", "rx", "ry", "rz"], hide=False)
            def_j = cmds.joint(name=naming.parse([self._name, index], suffix="jDef"))
            cmds.joint(def_j, edit=True, zeroScaleOrient=True, orientJoint='zxy')
            self._deformerJoints.append(def_j)
            cmds.parent(follicle_transform, self._nonScaleGrp)
            self._toHide.append(follicle)
            follicle_list.append(follicle)

        if self._scaleable:
            # create follicles for scaling calculations
            for index in range(int(self._jointResolution)):
                _name = naming.parse([self._name, index, "SCA"])
                _uv = (0.1 + (index / float(self._jointResolution)), 0.0)
                follicle_transform, follicle = connection.create_follicle(_name, n_surf, _uv)
                self._toHide.append(follicle)
                attribute.lock_and_hide(follicle_transform, ["tx", "ty", "tz", "rx", "ry", "rz"], hide=False)
                cmds.parent(follicle_transform, self._nonScaleGrp)
                dist_node = cmds.createNode("distanceBetween",
                                            name=naming.parse([self._name, "fDistance", index], suffix="loc"))
                cmds.connectAttr("%s.outTranslate" % follicle_list[index], "%s.point1" % dist_node)
                cmds.connectAttr("%s.outTranslate" % follicle, "%s.point2" % dist_node)

                mult_plug = op.multiply("%s.distance" % dist_node, 2)
                global_mult_plug = op.multiply(mult_plug, "%s.scaleX" % self._scaleGrp)
                global_div_plug = op.divide(global_mult_plug, "%s.scaleX" % self._scaleGrp)
                global_mixer = cmds.createNode("blendColors",
                                               name=naming.parse([self._name, "fGlobMix", index], suffix="blend"))

                for ch in "RGB":
                    cmds.connectAttr(global_div_plug, "{0}.color1{1}".format(global_mixer, ch))
                    cmds.setAttr("{0}.color2{1}".format(global_mixer, ch), 1)

                cmds.connectAttr("%s.output" % global_mixer, "%s.scale" % self._deformerJoints[index])
                cmds.connectAttr("%s.scaleSwitch" % self._startPlug, "%s.blender" % global_mixer)

        return follicle_list

    def _create_controllers(self, length):
        interval = length / (self._controllerCount + 1)

        for index in range(self._controllerCount):
            cont = Controller(
                name=naming.parse([self._name, "midRbn", index + 1], suffix="cont"),
                shape="Star",
                tier="secondary",
                normal=(1, 0, 0),
                pos=(-(length / 2.0) + (interval * (index + 1)), 0, 0),
            )
            yield cont.name

    # def _create_control_joints(self):
    #     cmds.select(clear=True)
    #     start_joint = cmds.joint(name=naming.parse([self._name, "start"], suffix="j"), radius=2)
    #     self._toHide.append(start_joint)
    #     functions.align_to(start_joint, self._startAim)
    #
    #     cmds.select(clear=True)
    #     end_joint = cmds.joint(name=naming.parse([self._name, "end"], suffix="j"), radius=2)
    #     self._toHide.append(end_joint)
    #     functions.align_to(end_joint, self._endAim)

    def create(self):
        if not self._validate():
            raise Exception("Start and/or End nodes are not defined")
        self._create_groups()

        ribbon_length = functions.get_distance(self.start_node, self.end_node)
        n_surf = self._initial_ribbon(ribbon_length)

        self._create_follicles(n_surf)

        # self._controllerList = list(self._create_controllers(ribbon_length))

        # cmds.error("WER")

        # create control joints
        cmds.select(clear=True)
        start_joint = cmds.joint(name=naming.parse([self._name, "start"], suffix="j"), radius=2)
        self._toHide.append(start_joint)
        functions.align_to(start_joint, self._startAim)
        # cmds.move(-(ribbon_length / 2.0), 0, 0, start_joint)

        cmds.select(clear=True)
        end_joint = cmds.joint(name=naming.parse([self._name, "end"], suffix="j"), radius=2)
        self._toHide.append(end_joint)
        cmds.move((ribbon_length / 2.0), 0, 0, end_joint)

        mid_joint_list = []
        counter = 0
        if self._controllerList:
            counter += 1
            for ctrl in self._controllerList:
                cmds.select(clear=True)
                mid_j = cmds.joint(name=naming.parse([self._name, "mid", counter], suffix="j"), radius=2)
                functions.align_to_alter(mid_j, ctrl)
                mid_joint_list.append(mid_j)
        else:
            interval = ribbon_length / (self._controllerCount + 1)

            for index in range(self._controllerCount):
                counter += 1
                cmds.select(clear=True)
                mid_j = cmds.joint(
                    name=naming.parse([self._name, "mid", index], suffix="j"),
                    position=(-(ribbon_length / 2.0) + (interval * counter), 0, 0),
                    radius=2)
                mid_joint_list.append(mid_j)

        cmds.skinCluster(start_joint, end_joint, mid_joint_list, n_surf, toSelectedBones=True,
                         dropoffRate=self._dropoff)

        # cmds.parent(start_joint, start_ore)
        cmds.parent(start_joint, self._startAim)
        if self._connectStartAim:
            # aim it to the next mid joint after the start
            cmds.aimConstraint(
                mid_joint_list[0],
                self._startAim,
                aimVector=(1, 0, 0),
                upVector=(0, 1, 0),
                worldUpType="object",
                worldUpObject=self._startUp,
                maintainOffset=False
            )

        cmds.parent(self._endAim, self._endUp, self._endPlug)
        # cmds.parent(self._endPlug, self._scaleGrp)
        cmds.parent(end_joint, self._endAim)
        cmds.aimConstraint(
            mid_joint_list[-1],
            self._endAim,
            aimVector=(1, 0, 0),
            upVector=(0, 1, 0),
            worldUpType="object",
            worldUpObject=self._endUp,
            maintainOffset=True
        )

        # middle_pos_list = []
        # counter = 0

        cmds.delete(cmds.pointConstraint([self._startPlug, self._endPlug], self._scaleGrp, maintainOffset=False)[0])

        cmds.makeIdentity(self._scaleGrp, apply=True, translate=True)

        cmds.parent([self._startPlug, self._endPlug], self._scaleGrp)

        for nmb, mid in enumerate(mid_joint_list):
            # counter += 1
            mid_cont = Controller(shape="Circle", name=naming.parse([self._name, "midRbn", nmb + 1], suffix="cont"),
                                  normal=(1, 0, 0))
            self._controllers.append(mid_cont)
            middle_off = cmds.spaceLocator(name=naming.parse([self._name, "off", nmb + 1], suffix="loc"))[0]
            self._toHide.append(functions.get_shapes(middle_off)[0])
            middle_aim = cmds.group(empty=True, name=naming.parse([self._name, "aim", nmb + 1], suffix="grp"))
            functions.align_to(middle_aim, mid, position=True, rotation=False)
            middle_up = cmds.spaceLocator(name=naming.parse([self._name, "mid", "up", nmb + 1], suffix="loc"))[0]
            self._toHide.append(functions.get_shapes(middle_up)[0])

            functions.align_to(middle_up, mid, position=True, rotation=False)
            cmds.setAttr("%s.ty" % middle_up, 0.5)

            middle_pos = cmds.spaceLocator(name=naming.parse([self._name, "mid", "pos", nmb + 1], suffix="loc"))[0]
            cmds.parent(middle_pos, self._scaleGrp)
            self._toHide.append(functions.get_shapes(middle_pos)[0])
            functions.align_to(middle_pos, mid, position=True, rotation=False)

            cmds.parent(mid, mid_cont.name)
            cmds.parent(mid_cont.name, middle_off)
            cmds.parent(middle_off, middle_aim)
            cmds.parent(middle_up, middle_aim, middle_pos)
            cmds.aimConstraint(
                self._startPlug,
                middle_aim,
                aimVector=(0, 0, -1),
                upVector=(0, 1, 0),
                worldUpType="object",
                worldUpObject=middle_up,
                maintainOffset=True
            )
            cmds.pointConstraint(self._startPlug, self._endPlug, middle_pos)

            cmds.pointConstraint(self._startUp, self._endUp, middle_up)

        functions.align_and_aim(self._scaleGrp, [self._startNode, self._endNode], [self._endNode],
                                up_vector=self._upVector)
