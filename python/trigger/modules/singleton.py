"""Singleton module"""

from maya import cmds
import maya.api.OpenMaya as om
from trigger.library import functions
from trigger.library import naming
from trigger.library import attribute
from trigger.library import connection
from trigger.library import api
from trigger.objects.controller import Controller
from trigger.utils import parentToSurface

from trigger.library import controllers as ic

from trigger.core import filelog

log = filelog.Filelog(logname=__name__, filename="trigger_log")

LIMB_DATA = {"members": ["SingletonRoot", "Singleton"],
             "properties": [
                 {
                     "attr_name": "localJoints",
                     "nice_name": "Local_Joints",
                     "attr_type": "bool",
                     "default_value": False,
                 },
                 {
                     "attr_name": "surface",
                     "nice_name": "Surface",
                     "attr_type": "string",
                     "default_value": "",
                 },

             ],
             "multi_guide": "Singleton",
             "sided": True, }


class Singleton(object):
    """Creates one or multiple loose controllers. They can be bound to a surface and can be local"""
    def __init__(self, build_data=None, inits=None, *args, **kwargs):
        super(Singleton, self).__init__()
        # fool proofing

        # reinitialize the initial Joints
        if build_data:
            self.singletonRoot = build_data.get("SingletonRoot")
            self.singletons = build_data.get("Singleton", [])
            self.inits = [self.singletonRoot] + self.singletons
        else:
            log.error("Class needs either build_data or inits to be constructed")

        # get distances

        # get positions

        # get the properties from the root
        self.useRefOrientation = cmds.getAttr("%s.useRefOri" % self.inits[0])
        self.side = functions.get_joint_side(self.inits[0])
        self.sideMult = -1 if self.side == "R" else 1
        self.isLocal = bool(cmds.getAttr("%s.localJoints" % self.inits[0]))
        self.surface = str(cmds.getAttr("%s.surface" % self.inits[0]))

        # initialize coordinates
        self.up_axis, self.mirror_axis, self.look_axis = functions.getRigAxes(self.inits[0])

        # initialize suffix
        self.suffix = (naming.uniqueName(cmds.getAttr("%s.moduleName" % self.inits[0])))

        # module specific variables
        self.localOffGrp = None
        self.plugBindGrp = None
        self.scaleHook = None
        self.joints_grp = None
        self.follicle_grp = None
        self.conts_grp = None

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

        self.localOffGrp = cmds.group(name="%s_localOffset_grp" % self.suffix, em=True)
        self.plugBindGrp = cmds.group(name="%s_plugBind_grp" % self.suffix, em=True)
        cmds.parent(self.localOffGrp, self.plugBindGrp)
        cmds.parent(self.plugBindGrp, self.limbGrp)

        # scale hook gets the scale value from the bind group but not from the localOffset
        self.scaleHook = cmds.group(name="%s_scaleHook" % self.suffix, em=True)
        cmds.parent(self.scaleHook, self.limbGrp)
        scale_skips = "xyz" if self.isLocal else ""
        connection.matrixConstraint(self.scaleGrp, self.scaleHook, ss=scale_skips)

        self.joints_grp = cmds.group(name="%s_joints_grp" % self.suffix, em=True)
        self.conts_grp = cmds.group(name="%s_conts_grp" % self.suffix, em=True)
        self.follicle_grp = cmds.group(name="%s_follicle_grp" % self.suffix, em=True)

        cmds.parent([self.joints_grp, self.conts_grp, self.follicle_grp], self.limbGrp)
        cmds.parent(self.conts_grp, self.localOffGrp)

    def _build_module(self):
        # draw Joints
        cmds.select(d=True)
        self.limbPlug = cmds.joint(name="limbPlug_%s" % self.suffix, p=api.getWorldTranslation(self.inits[0]), radius=3)
        cmds.connectAttr("%s.s" % self.scaleGrp, "%s.s" % self.limbPlug)

        if self.isLocal:
            # if the deformation joints are local, drive the plugBindGrp with limbPlug for negative compensation
            connection.matrixConstraint(self.limbPlug, self.plugBindGrp)
        else:
            # connection.matrixConstraint(self.limbPlug, self.conts_grp)
            # cmds.connectAttr("%s.s" % self.limbPlug, "%s.s" % self.conts_grp)
            # limbplug causes double scaling in here because of that we use scaleHook instead
            connection.matrixConstraint(self.scaleHook, self.conts_grp)

        cmds.select(d=True)
        for nmb, j in enumerate(self.inits):
            cmds.select(d=True)
            j_def = cmds.joint(name="jDef_{0}_{1}".format(j, self.suffix))

            cont = Controller(name="cont_%s%s" % (self.suffix, nmb + 1), shape="Circle")
            cont.set_side(side=self.side)
            cont_bind = cont.add_offset("bind")
            cont_off = cont.add_offset("pos")
            functions.alignTo(cont_off, j, position=True, rotation=True)
            connection.matrixConstraint(cont.name, j_def, mo=False, source_parent_cutoff=self.localOffGrp)
            if self.surface:
                # if there is a surface constraint, matrix constraint it to the surface and ignore limbPlug
                fol = parentToSurface.parentToSurface([cont_bind], self.surface, mode="matrixConstraint")
                cmds.parent(fol, self.follicle_grp)
            else:
                if not self.isLocal:
                    # follow the limb plug only if the joints are not local
                    pass
                    # connection.matrixConstraint(self.limbPlug, cont_bind, source_parent_cutoff=self.localOffGrp)

            cmds.parent(cont_bind, self.conts_grp)
            cmds.parent(j_def, self.joints_grp)

            self.sockets.append(j_def)
            self.deformerJoints.append(j_def)

        if not self.useRefOrientation:
            functions.orientJoints(self.deformerJoints, worldUpAxis=self.look_axis, upAxis=(0, 1, 0),
                                   reverseAim=self.sideMult, reverseUp=self.sideMult)
        else:
            for x in range (len(self.deformerJoints)):
                functions.alignTo(self.deformerJoints[x], self.inits[x], position=True, rotation=True)
                cmds.makeIdentity(self.deformerJoints[x], a=True)


        attribute.drive_attrs("%s.jointVis" % self.scaleGrp, ["%s.v" % x for x in self.deformerJoints])
        cmds.connectAttr("%s.jointVis" % self.scaleGrp,"%s.v" % self.limbPlug)
        functions.colorize(self.deformerJoints, self.colorCodes[0], shape=False)

    def roundUp(self):
        cmds.parentConstraint(self.limbPlug, self.scaleGrp, mo=False)
        cmds.setAttr("%s.rigVis" % self.scaleGrp, 0)

        self.scaleConstraints.append(self.scaleGrp)
        # lock and hide

    def createLimb(self):
        self.createGrp()
        self._build_module()
        self.roundUp()


class Guides(object):
    def __init__(self, side="L", suffix="singleton", segments=1, tMatrix=None, upVector=(0, 1, 0),
                 mirrorVector=(1, 0, 0), lookVector=(0, 0, 1), *args, **kwargs):
        super(Guides, self).__init__()
        # fool check

        # -------Mandatory------[Start]
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
        # -------Mandatory------[End]

    def draw_joints(self):
        cmds.select(d=True)
        r_point_j = om.MVector(0, 0, 0) * self.tMatrix
        if not self.segments:
            self.offsetVector = om.MVector(0, 1, 0)
            singleton_root_jnt = cmds.joint(name="root_{0}".format(self.suffix))
            self.guideJoints.append(singleton_root_jnt)
            return

        if self.side == "C":
            # Guide joint positions for limbs with no side orientation
            n_point_j = om.MVector(0, 0, 10) * self.tMatrix
        else:
            # Guide joint positions for limbs with sides
            n_point_j = om.MVector(10 * self.sideMultiplier, 0, 0) * self.tMatrix

        add_val = (n_point_j - r_point_j) / ((self.segments + 1) - 1)

        # Define the offset vector
        self.offsetVector = (n_point_j - r_point_j).normal()

        # Draw the joints
        for seg in range(self.segments + 1):
            tentacle_jnt = cmds.joint(p=(r_point_j + (add_val * seg)),
                                      name="jInit_singleton_%s_%i" % (self.suffix, seg))
            # Update the guideJoints list
            self.guideJoints.append(tentacle_jnt)

        # Update the guideJoints list

        # set orientation of joints
        functions.orientJoints(self.guideJoints, worldUpAxis=self.upVector, upAxis=(0, 1, 0),
                               reverseAim=self.sideMultiplier, reverseUp=self.sideMultiplier)

    def define_attributes(self):
        # set joint side and type attributes
        functions.set_joint_type(self.guideJoints[0], "SingletonRoot")
        if len(self.guideJoints) > 1:
            _ = [functions.set_joint_type(jnt, "Singleton") for jnt in self.guideJoints[1:]]
        _ = [functions.set_joint_side(jnt, self.side) for jnt in self.guideJoints]

        # ----------Mandatory---------[Start]
        root_jnt = self.guideJoints[0]
        attribute.create_global_joint_attrs(root_jnt, moduleName="%s_Singleton" % self.side, upAxis=self.upVector,
                                            mirrorAxis=self.mirrorVector, lookAxis=self.lookVector)
        # ----------Mandatory---------[End]

        for attr_dict in LIMB_DATA["properties"]:
            attribute.create_attribute(root_jnt, attr_dict)

    def createGuides(self):
        self.draw_joints()
        self.define_attributes()

    def convertJoints(self, joints_list):
        self.guideJoints = joints_list
        self.define_attributes()
