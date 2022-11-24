from maya import cmds
import maya.api.OpenMaya as om

from trigger.library import functions, joint
from trigger.library import naming
from trigger.library import attribute
from trigger.library import connection
from trigger.library import controllers as ic
from trigger.utils import parentToSurface
from trigger.core import filelog

log = filelog.Filelog(logname=__name__, filename="trigger_log")

LIMB_DATA = {
    "members": ["Surface", "SurfaceItem"],
    "properties": [{"attr_name": "controllerSurface",
                    "nice_name": "Mesh to Stick",
                    "attr_type": "string",
                    "default_value": ""
                    },
                   {"attr_name": "rotateObject",
                    "nice_name": "Rotation Parent",
                    "attr_type": "string",
                    "default_value": ""
                    },
                   {
                       "attr_name": "bindScales",
                       "nice_name": "Bind Scales",
                       "attr_type": "bool",
                       "default_value": False
                   },
                   {"attr_name": "limbPlugLocation",
                    "nice_name": "Module Plug Location",
                    "attr_type": "enum",
                    "enum_list": "On Surface Controller:On Local Joint",
                    "default_value": 0,
                    },
                   ],
    "multi_guide": "SurfaceItem",
    "sided": True,
}


class Surface(object):
    def __init__(self, build_data=None, inits=None, *args, **kwargs):
        super(Surface, self).__init__()

        if build_data:
            self.surfaceRoot = build_data.get("Surface")
            self.surfaceItems = build_data.get("SurfaceItem", [])
            self.inits = [self.surfaceRoot] + self.surfaceItems
        elif inits:
            self.inits = inits
        else:
            log.error("Class needs either build_data or inits to be constructed")

        # get properties
        self.controllerSurface = cmds.getAttr("%s.controllerSurface" % self.inits[0])
        self.rotateObject = cmds.getAttr("%s.rotateObject" % self.inits[0])
        self.isPlugOnLocal = cmds.getAttr("%s.limbPlugLocation" % self.inits[0])
        try:
            self.bindScales = cmds.getAttr("%s.bindScales" % self.inits[0])
        except ValueError:
            self.bindScales = False

        self.suffix = (naming.unique_name(cmds.getAttr("%s.moduleName" % self.inits[0])))

        self.controllerGrp = None

        self.controllers = []
        self.jointBinds = []
        self.limbGrp = None
        self.scaleGrp = None
        self.limbPlug = None
        self.nonScaleGrp = None
        self.cont_IK_OFF = None
        self.sockets = []
        self.scaleConstraints = []
        self.anchors = []
        self.anchorLocations = []
        self.deformerJoints = []
        self.colorCodes = []

    def createGrp(self):
        self.controllerGrp = cmds.group(name="%s_contGrp" % self.suffix, em=True)
        self.scaleGrp = cmds.group(name="%s_scaleGrp" % self.suffix, em=True)
        functions.align_to(self.scaleGrp, self.inits[0], 0)
        self.nonScaleGrp = cmds.group(name="%s_nonScaleGrp" % self.suffix, em=True)
        cmds.addAttr(self.scaleGrp, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True)
        cmds.addAttr(self.scaleGrp, at="bool", ln="Joints_Visibility", sn="jointVis", defaultValue=True)
        cmds.addAttr(self.scaleGrp, at="bool", ln="Rig_Visibility", sn="rigVis", defaultValue=True)
        # make the created attributes visible in the channelbox
        cmds.setAttr("{0}.contVis".format(self.scaleGrp), cb=True)
        cmds.setAttr("{0}.jointVis".format(self.scaleGrp), cb=True)
        cmds.setAttr("{0}.rigVis".format(self.scaleGrp), cb=True)

        self.limbGrp = cmds.group(name=self.suffix, em=True)
        cmds.parent(self.scaleGrp, self.nonScaleGrp, self.controllerGrp, self.limbGrp)
        self.scaleConstraints.append(self.scaleGrp)

    def createJoints(self):

        for nmb, init in enumerate(self.inits):
            cmds.select(d=True)
            if len(self.inits) == 1:
                joint_name = "%s_jnt" % self.suffix
            nmb = "" if len(self.inits) == 1 else nmb  # for backward compatibility
            j_def = cmds.joint(name="%s%s_jnt" % (self.suffix, nmb))
            self.deformerJoints.append(j_def)
            cmds.connectAttr("{0}.rigVis".format(self.scaleGrp), "{0}.v".format(j_def), force=True)
            # Create connection groups
            j_def_offset = functions.create_offset_group(j_def, "offset")
            j_def_bind = functions.create_offset_group(j_def, "bind")
            self.jointBinds.append(j_def_bind)
            functions.align_to(j_def_offset, init, position=True, rotation=True)
            cmds.parent(j_def_offset, self.nonScaleGrp)

        # extra.alignTo(self.surface_jnt, self.rootInit, position=True, rotation=True)
        if self.isPlugOnLocal:
            self.limbPlug = self.deformerJoints[0]
        else:
            self.limbPlug = cmds.joint(name="limbPlug_%s" % self.suffix, radius=2)
            cmds.parent(self.limbPlug, self.scaleGrp)
        self.sockets.append(self.limbPlug)

        attribute.drive_attrs("%s.jointVis" % self.scaleGrp, ["%s.v" % x for x in self.deformerJoints])
        cmds.connectAttr("%s.jointVis" % self.scaleGrp, "%s.v" % self.limbPlug, force=True)
        functions.colorize(self.deformerJoints, self.colorCodes[0], shape=False)

    def create_controllers_and_connections(self):
        for nmb, (init, joint_bind) in enumerate(zip(self.inits, self.jointBinds)):
            nmb = "" if len(self.inits) == 1 else nmb  # for backward compatibility
            icon = ic.Icon()
            _cont, _ = icon.create_icon("Diamond", icon_name="%s%s_cont" % (self.suffix, nmb))
            self.controllers.append(_cont)
            _cont_offset = functions.create_offset_group(_cont, "offset")
            _cont_bind = functions.create_offset_group(_cont, "bind")
            _cont_negate = functions.create_offset_group(_cont, "negate")
            _cont_pos = functions.create_offset_group(_cont, "pos")

            # functions.alignTo(self.cont_offset, self.rootInit, position=True, rotation=False)
            functions.align_to(_cont_offset, init, position=True, rotation=True)
            # functions.alignTo(self.cont_pos, self.rootInit, position=True, rotation=True)
            functions.colorize(_cont, self.colorCodes[0])

            cmds.connectAttr("%s.contVis" % self.scaleGrp, "%s.v" % _cont_offset, force=True)
            cmds.parent(_cont_offset, self.controllerGrp)

            if self.controllerSurface:
                follicle = parentToSurface.parentToSurface([_cont_bind], surface=self.controllerSurface, mode="none")[0]
                # constrain controller translate to the follicle
                # connection.matrixConstraint(follicle, self.cont_bind, mo=False, sr="xyz", ss="xyz")
                _sr = "xyz" if self.rotateObject else None
                if self.bindScales:
                    cmds.connectAttr("%s.scale" % self.scaleGrp, "%s.scale" % follicle, force=True)
                    _ss = None
                else:
                    _ss = "xyz"
                _mo = False if self.rotateObject else True
                connection.matrixConstraint(follicle, _cont_bind, maintainOffset=_mo, skipRotate=_sr, skipScale=_ss)

                cmds.parent(follicle, self.nonScaleGrp)
                cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % follicle, force=True)

            if self.rotateObject:
                connection.matrixConstraint(self.rotateObject, _cont_bind, maintainOffset=True, skipTranslate="xyz", skipScale="xyz")
                # connection.matrixConstraint(self.rotateObject, self.cont_bind, mo=True, st="xyz", ss=_ss)

            negate_multMatrix = cmds.createNode("multMatrix", name="negate_multMatrix_%s" % self.suffix)
            negate_decompose = cmds.createNode("decomposeMatrix", name="negate_decompose_%s" % self.suffix)
            cmds.connectAttr("%s.inverseMatrix" % _cont, "%s.matrixIn[0]" % negate_multMatrix, force=True)
            cmds.connectAttr("%s.matrixSum" % negate_multMatrix, "%s.inputMatrix" % negate_decompose, force=True)
            cmds.connectAttr("%s.outputTranslate" % negate_decompose, "%s.translate" % _cont_negate, force=True)
            cmds.connectAttr("%s.outputRotate" % negate_decompose, "%s.rotate" % _cont_negate, force=True)
            cmds.connectAttr("%s.outputScale" % negate_decompose, "%s.scale" % _cont_negate, force=True)

            if self.isPlugOnLocal:
                pass  # nothing to connect because plug is local joint itself
            else:
                cmds.parentConstraint(_cont, self.limbPlug, mo=False)

            # Direct connection between controller and joint
            for attr in "trs":
                for axis in "xyz":
                    cmds.connectAttr("%s.%s%s" % (_cont, attr, axis), "%s.%s%s" % (joint_bind, attr, axis), force=True)

    def createLimb(self):
        self.createGrp()
        self.createJoints()
        self.create_controllers_and_connections()


class Guides(object):
    def __init__(self, side="L", suffix="surface", segments=None, tMatrix=None, upVector=(0, 1, 0),
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
            surface_root_jnt = cmds.joint(name="jInit_surface_{0}".format(self.suffix))
            self.guideJoints.append(surface_root_jnt)
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
            surface_jnt = cmds.joint(p=(r_point_j + (add_val * seg)),
                                     name="jInit_surface_%s_%i" % (self.suffix, seg))
            # Update the guideJoints list
            self.guideJoints.append(surface_jnt)

        # Update the guideJoints list

        # set orientation of joints
        joint.orient_joints(self.guideJoints, world_up_axis=self.upVector, up_axis=(0, 1, 0),
                            reverse_aim=self.sideMultiplier, reverse_up=self.sideMultiplier)

    def define_attributes(self):
        # set joint side and type attributes
        joint.set_joint_type(self.guideJoints[0], "Surface")
        if len(self.guideJoints) > 1:
            _ = [joint.set_joint_type(jnt, "SurfaceItem") for jnt in self.guideJoints[1:]]
        _ = [joint.set_joint_side(jnt, self.side) for jnt in self.guideJoints]

        # ----------Mandatory---------[Start]
        root_jnt = self.guideJoints[0]
        attribute.create_global_joint_attrs(root_jnt, moduleName="%s_Surface" % self.side, upAxis=self.upVector,
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
