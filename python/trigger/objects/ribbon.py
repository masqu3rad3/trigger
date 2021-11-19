#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Creates a power ribbon joint chain between given locations"""

from maya import cmds
from trigger.library import functions, naming
from trigger.library import attribute
from trigger.library import controllers as ic


class Ribbon(object):
    def __init__(self, name=None,
                 start_node=None,
                 end_node=None,
                 ribbon_resolution=5,
                 joint_resolution=5,
                 controller_count=1,
                 controller_list=None,
                 dropoff=2.0,
                 connect_start_aim=True,
                 up_vector=(0, 1, 0)
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

        # output vars
        self._startPlug = None
        self._endPlug = None
        self._ribbonGrp = None
        self._scaleGrp = None
        self._nonScaleGrp = None
        self._deformerJoints = []
        self._controllers = []
        self.toHide = []
        self.startAim = None

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

    def pin_start(self, node_a, node_b=None, switch_a=None, switch_b=None):
        nodes = [node_a, node_b] if node_b else node_a
        constraint = cmds.parentConstraint(nodes, self._startPlug, mo=True)
        self._switch_weights(nodes, [switch_a, switch_b], constraint)
        return constraint

    def pin_end(self, node_a, node_b=None, switch_a=None, switch_b=None):
        nodes = [node_a, node_b] if node_b else node_a
        constraint = cmds.parentConstraint(nodes, self._endPlug, mo=True)
        self._switch_weights(nodes, [switch_a, switch_b], constraint)
        return constraint

    def orient(self, node_a, node_b=None, switch_a=None, switch_b=None):
        nodes = [node_a, node_b] if node_b else node_a
        constraint = cmds.parentConstraint(nodes, self.startAim, mo=True, skipTranslate=["x", "y", "z"])[0]
        self._switch_weights(nodes, [switch_a, switch_b], constraint)
        # if node_b and any([switch_a, switch_b]):
        #     attrs = cmds.listAttr(constraint, ud=True)
        #     if switch_a:
        #         cmds.connectAttr(switch_a, "%s.%s" %(constraint, attrs[0]))
        #     if switch_b:
        #         cmds.connectAttr(switch_b, "%s.%s" % (constraint, attrs[1]))
        return constraint

    @staticmethod
    def _switch_weights(nodes, switches, constraint):
        if not nodes or not any(switches):
            return
        attrs = cmds.listAttr(constraint, ud=True)
        for attr, sw in zip(attrs, switches):
            if sw:
                cmds.connectAttr(sw, "%s.%s" % (constraint, attr))

    def _create_groups(self):
        self._ribbonGrp = cmds.group(name=self._name, em=True)
        self._scaleGrp = cmds.group(name=naming.uniqueName("RBN_ScaleGrp_%s" % self._name), em=True)
        self._nonScaleGrp = cmds.group(name=naming.uniqueName("RBN_nonScaleGrp_%s" % self._name), em=True)

    def _validate(self):
        if not self.start_node or \
                not self.end_node:
            return False
        else:
            return True

    def create(self):

        # Create groups
        # name = naming.uniqueName("RBN_ScaleGrp_%s" % name)
        # self._scaleGrp = cmds.group(name="RBN_ScaleGrp_%s" % name, em=True)
        # self._nonScaleGrp = cmds.group(name="RBN_nonScaleGrp_%s" % name, em=True)
        self._create_groups()

        ribbon_length = functions.getDistance(self.start_node, self.end_node)
        n_surf_trans = \
            cmds.nurbsPlane(ax=(0, 0, 1), u=float(self._ribbonResolution), v=1, w=ribbon_length,
                            lr=(1.0 / ribbon_length),
                            name="nSurf_%s" % self._name)[0]
        cmds.parent(n_surf_trans, self._nonScaleGrp)
        cmds.rebuildSurface(n_surf_trans, ch=1, rpo=1, rt=0, end=1, kr=2, kcp=0, kc=0, su=5, du=3, sv=1, dv=1, tol=0,
                            fr=0, dir=1)
        cmds.makeIdentity(a=True)
        n_surf = functions.getShapes(n_surf_trans)[0]

        self.toHide.append(n_surf_trans)

        # Start up nodes
        cmds.select(d=True)
        self.startAim = cmds.group(em=True, name="jRbn_Start_CON_%s" % self._name)
        cmds.move(-(ribbon_length / 2.0), 0, 0, self.startAim)
        cmds.makeIdentity(self.startAim, a=True)
        start_ore = cmds.duplicate(self.startAim, name="jRbn_Start_ORE_%s" % self._name)[0]
        cmds.parent(start_ore, self.startAim)

        start_UP = cmds.spaceLocator(name="jRbn_StartUp_%s" % self._name)[0]
        self.toHide.append(functions.getShapes(start_UP)[0])
        cmds.move(-(ribbon_length / 2.0), 0.5, 0, start_UP)

        self._startPlug = cmds.spaceLocator(name="jRbn_StartCn_%s" % self._name)[0]
        self.toHide.append(functions.getShapes(self._startPlug)[0])
        cmds.move(-(ribbon_length / 2.0), 0, 0, self._startPlug)
        cmds.makeIdentity(self._startPlug, a=True)

        cmds.parent(self.startAim, start_UP, self._startPlug)

        cmds.addAttr(self._startPlug, shortName="scaleSwitch", longName="Scale_Switch",
                     defaultValue=1.0, at="float", minValue=0.0, maxValue=1.0, k=True)

        # End Upnodes
        cmds.select(d=True)
        end_AIM = cmds.group(name="jRbn_End_%s_AIM" % self._name, em=True)
        cmds.move(-(ribbon_length / -2.0), 0, 0, end_AIM)
        cmds.makeIdentity(end_AIM, a=True)
        end_UP = cmds.spaceLocator(name="jRbn_End_%s_UP" % self._name)[0]
        self.toHide.append(functions.getShapes(end_UP)[0])
        cmds.move(-(ribbon_length / -2.0), 0.5, 0, end_UP)

        self._endPlug = cmds.spaceLocator(name="jRbn_End_%s_endCon" % self._name)[0]
        self.toHide.append(functions.getShapes(self._endPlug)[0])
        cmds.move(-(ribbon_length / -2.0), 0, 0, self._endPlug)
        cmds.makeIdentity(self._endPlug, a=True)

        follicleList = []
        # create follicles and deformer joints
        for index in range(int(self._jointResolution)):
            follicle = cmds.createNode('follicle', name="follicle_{0}{1}".format(self._name, index))
            follicle_transform = functions.getParent(follicle)
            cmds.connectAttr("%s.local" % n_surf, "%s.inputSurface" % follicle)
            cmds.connectAttr("%s.worldMatrix[0]" % n_surf, "%s.inputWorldMatrix" % follicle)
            cmds.connectAttr("%s.outRotate" % follicle, "%s.rotate" % follicle_transform)
            cmds.connectAttr("%s.outTranslate" % follicle, "%s.translate" % follicle_transform)
            cmds.setAttr("%s.parameterV" % follicle, 0.5)
            cmds.setAttr("%s.parameterU" % follicle, 0.1 + (index / float(self._jointResolution)))
            attribute.lockAndHide(follicle_transform, ["tx", "ty", "tz", "rx", "ry", "rz"], hide=False)
            follicleList.append(follicle)
            defJ = cmds.joint(name="jDef_%s%i" % (self._name, index))
            cmds.joint(defJ, e=True, zso=True, oj='zxy')
            self._deformerJoints.append(defJ)
            cmds.parent(follicle_transform, self._nonScaleGrp)
            self.toHide.append(follicle)

        # create follicles for scaling calculations
        follicle_sca_list = []
        counter = 0  # TODO : Why did I use this?
        for index in range(int(self._jointResolution)):
            s_follicle = cmds.createNode('follicle', name="follicleSCA_%s%i" % (self._name, index))
            s_follicle_transform = functions.getParent(s_follicle)
            cmds.connectAttr("%s.local" % n_surf, "%s.inputSurface" % s_follicle)
            cmds.connectAttr("%s.worldMatrix[0]" % n_surf, "%s.inputWorldMatrix" % s_follicle)
            cmds.connectAttr("%s.outRotate" % s_follicle, "%s.rotate" % s_follicle_transform)
            cmds.connectAttr("%s.outTranslate" % s_follicle, "%s.translate" % s_follicle_transform)
            cmds.setAttr("%s.parameterV" % s_follicle, 0.0)
            cmds.setAttr("%s.parameterU" % s_follicle, 0.1 + (index / float(self._jointResolution)))
            attribute.lockAndHide(s_follicle_transform, ["tx", "ty", "tz", "rx", "ry", "rz"], hide=False)
            follicle_sca_list.append(s_follicle)
            cmds.parent(s_follicle_transform, self._nonScaleGrp)
            self.toHide.append(s_follicle)
            # create distance node
            distNode = cmds.createNode("distanceBetween", name="fDistance_%s%i" % (self._name, index))
            cmds.connectAttr("%s.outTranslate" % follicleList[counter], "%s.point1" % distNode)
            cmds.connectAttr("%s.outTranslate" % s_follicle, "%s.point2" % distNode)

            multiplier = cmds.createNode("multDoubleLinear", name="fMult_%s%i" % (self._name, index))
            cmds.connectAttr("%s.distance" % distNode, "%s.input1" % multiplier)

            cmds.setAttr("%s.input2" % multiplier, 2)

            global_mult = cmds.createNode("multDoubleLinear", name="fGlobal_%s%i" % (self._name, index))
            cmds.connectAttr("%s.output" % multiplier, "%s.input1" % global_mult)
            cmds.connectAttr("%s.scaleX" % self._scaleGrp, "%s.input2" % global_mult)

            global_divide = cmds.createNode("multiplyDivide", name="fGlobDiv_%s%i" % (self._name, index))
            cmds.setAttr("%s.operation" % global_divide, 2)
            cmds.connectAttr("%s.output" % global_mult, "%s.input1X" % global_divide)
            cmds.connectAttr("%s.scaleX" % self._scaleGrp, "%s.input2X" % global_divide)

            global_mixer = cmds.createNode("blendColors", name="fGlobMix_%s%i" % (self._name, index))

            cmds.connectAttr("%s.outputX" % global_divide, "%s.color1R" % global_mixer)
            cmds.connectAttr("%s.outputX" % global_divide, "%s.color1G" % global_mixer)
            cmds.connectAttr("%s.outputX" % global_divide, "%s.color1B" % global_mixer)

            cmds.setAttr("%s.color2R" % global_mixer, 1)
            cmds.setAttr("%s.color2G" % global_mixer, 1)
            cmds.setAttr("%s.color2B" % global_mixer, 1)

            cmds.connectAttr("%s.output" % global_mixer, "%s.scale" % self._deformerJoints[counter])

            cmds.connectAttr("%s.scaleSwitch" % self._startPlug, "%s.blender" % global_mixer)
            counter += 1

        # create control joints
        cmds.select(d=True)
        startJoint = cmds.joint(name="jRbn_Start_%s" % self._name, radius=2)
        self.toHide.append(startJoint)
        cmds.move(-(ribbon_length / 2.0), 0, 0, startJoint)

        cmds.select(d=True)
        endJoint = cmds.joint(name="jRbn_End_%s" % self._name, radius=2)
        self.toHide.append(endJoint)
        cmds.move((ribbon_length / 2.0), 0, 0, endJoint)

        mid_joint_list = []
        counter = 0
        if self._controllerList:
            counter += 1
            for ctrl in self._controllerList:
                cmds.select(d=True)
                midJ = cmds.joint(name="jRbn_Mid_%i_%s" % (counter, self._name), radius=2)
                functions.alignToAlter(midJ, ctrl)
                mid_joint_list.append(midJ)
        else:
            interval = ribbon_length / (self._controllerCount + 1)

            for index in range(self._controllerCount):
                counter += 1
                cmds.select(d=True)
                midJ = cmds.joint(name="jRbn_Mid_%i_%s" % (index, self._name),
                                  p=(-(ribbon_length / 2.0) + (interval * counter), 0, 0), radius=2)
                mid_joint_list.append(midJ)

        cmds.skinCluster(startJoint, endJoint, mid_joint_list, n_surf, tsb=True, dropoffRate=self._dropoff)

        cmds.parent(startJoint, start_ore)
        if self._connectStartAim:
            # aim it to the next midjoint after the start
            cmds.aimConstraint(mid_joint_list[0], self.startAim, aimVector=(1, 0, 0), upVector=(0, 1, 0), wut=1,
                               wuo=start_UP, mo=False)

        cmds.parent(end_AIM, end_UP, self._endPlug)
        cmds.parent(endJoint, end_AIM)
        cmds.aimConstraint(mid_joint_list[-1], end_AIM, aimVector=(1, 0, 0), upVector=(0, 1, 0), wut=1, wuo=end_UP,
                           mo=True)

        middle_POS_list = []
        counter = 0

        icon = ic.Icon()
        for mid in mid_joint_list:
            counter += 1
            midCon, _ = icon.createIcon("Circle", iconName="cont_midRbn_%s%i" % (self._name, counter), normal=(1, 0, 0))
            self._controllers.append(midCon)
            middle_OFF = cmds.spaceLocator(name="mid_OFF_%s%i" % (self._name, counter))[0]
            self.toHide.append(functions.getShapes(middle_OFF)[0])
            middle_AIM = cmds.group(em=True, name="mid_AIM_%s%i" % (self._name, counter))
            functions.alignTo(middle_AIM, mid, position=True, rotation=False)
            middle_UP = cmds.spaceLocator(name="mid_UP_{0}{1}".format(self._name, counter))[0]
            self.toHide.append(functions.getShapes(middle_UP)[0])

            functions.alignTo(middle_UP, mid, position=True, rotation=False)
            cmds.setAttr("%s.ty" % middle_UP, 0.5)

            middle_POS = cmds.spaceLocator(name="mid_POS_{0}{1}".format(self._name, counter))[0]
            self.toHide.append(functions.getShapes(middle_POS)[0])
            functions.alignTo(middle_POS, mid, position=True, rotation=False)

            cmds.parent(mid, midCon)
            cmds.parent(midCon, middle_OFF)
            cmds.parent(middle_OFF, middle_AIM)
            cmds.parent(middle_UP, middle_AIM, middle_POS)
            cmds.aimConstraint(self._startPlug, middle_AIM, aimVector=(0, 0, -1), upVector=(0, 1, 0), wut=1,
                               wuo=middle_UP, mo=True)
            cmds.pointConstraint(self._startPlug, self._endPlug, middle_POS)
            cmds.pointConstraint(start_UP, end_UP, middle_UP)
            middle_POS_list.append(middle_POS)

        cmds.delete(cmds.pointConstraint([self._startPlug, self._endPlug], self._scaleGrp, mo=False)[0])

        cmds.makeIdentity(self._scaleGrp, a=True, t=True)

        cmds.parent([self._startPlug, self._endPlug] + middle_POS_list, self._scaleGrp)

        functions.alignAndAim(self._scaleGrp, [self._startNode, self._endNode], [self._endNode],
                              upVector=self._upVector)
