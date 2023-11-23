from maya import cmds
import maya.api.OpenMaya as om

from trigger.library import functions, joint
from trigger.library import naming
from trigger.library import attribute
from trigger.library import connection
from trigger.objects.controller import Controller
from trigger.utils import parentToSurface
from trigger.core.module import ModuleCore, GuidesCore
from trigger.core import filelog

LOG = filelog.Filelog(logname=__name__, filename="trigger_log")

LIMB_DATA = {
    "members": ["Surface", "SurfaceItem"],
    "properties": [
        {
            "attr_name": "controllerSurface",
            "nice_name": "Mesh to Stick",
            "attr_type": "string",
            "default_value": "",
        },
        {
            "attr_name": "rotateObject",
            "nice_name": "Rotation Parent",
            "attr_type": "string",
            "default_value": "",
        },
        {
            "attr_name": "bindScales",
            "nice_name": "Bind Scales",
            "attr_type": "bool",
            "default_value": False,
        },
        {
            "attr_name": "limbPlugLocation",
            "nice_name": "Module Plug Location",
            "attr_type": "enum",
            "enum_list": "On Surface Controller:On Local Joint",
            "default_value": 0,
        },
    ],
    "multi_guide": "SurfaceItem",
    "sided": True,
}


class Surface(ModuleCore):
    name = "Surface"
    def __init__(self, build_data=None, inits=None):
        super(Surface, self).__init__()

        if build_data:
            self.surfaceRoot = build_data.get("Surface")
            self.surfaceItems = build_data.get("SurfaceItem", [])
            self.inits = [self.surfaceRoot] + self.surfaceItems
        elif inits:
            self.inits = inits
        else:
            LOG.error("Class needs either build_data or inits to be constructed")

        # get properties
        self.controllerSurface = cmds.getAttr("%s.controllerSurface" % self.inits[0])
        self.rotateObject = cmds.getAttr("%s.rotateObject" % self.inits[0])
        self.isPlugOnLocal = cmds.getAttr("%s.limbPlugLocation" % self.inits[0])
        self.side = joint.get_joint_side(self.inits[0])
        try:
            self.bindScales = cmds.getAttr("%s.bindScales" % self.inits[0])
        except ValueError:
            self.bindScales = False

        self.module_name = naming.unique_name(
            cmds.getAttr("%s.moduleName" % self.inits[0])
        )
        self.jointBinds = []

    def create_joints(self):
        for nmb, init in enumerate(self.inits):
            cmds.select(clear=True)
            if len(self.inits) == 1:
                _joint_name = "%s_jnt" % self.module_name
            nmb = "" if len(self.inits) == 1 else nmb  # for backward compatibility
            j_def = cmds.joint(
                name=naming.parse([self.module_name, nmb], suffix="jDef")
            )
            self.deformerJoints.append(j_def)
            cmds.connectAttr(
                "{0}.rigVis".format(self.scaleGrp), "{0}.v".format(j_def), force=True
            )
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
            self.limbPlug = cmds.joint(
                name=naming.parse([self.module_name, "plug"], suffix="j"), radius=2
            )
            cmds.parent(self.limbPlug, self.scaleGrp)
        self.sockets.append(self.limbPlug)

        attribute.drive_attrs(
            "%s.jointVis" % self.scaleGrp, ["%s.v" % x for x in self.deformerJoints]
        )
        cmds.connectAttr(
            "%s.jointVis" % self.scaleGrp, "%s.v" % self.limbPlug, force=True
        )
        # functions.colorize(self.deformerJoints, self.colorCodes[0], shape=False)

    def create_controllers_and_connections(self):
        for nmb, (init, joint_bind) in enumerate(zip(self.inits, self.jointBinds)):
            nmb = "" if len(self.inits) == 1 else nmb  # for backward compatibility

            # _cont, _ = icon.create_icon("Diamond", icon_name="%s%s_cont" % (self.module_name, nmb))
            _cont = Controller(
                shape="Diamond",
                name=naming.parse([self.module_name, nmb], suffix="cont"),
                side=self.side,
                tier="primary",
            )
            self.controllers.append(_cont)
            _cont_offset = _cont.add_offset("offset")
            _cont_bind = _cont.add_offset("bind")
            _cont_negate = _cont.add_offset("negate")
            _cont_pos = _cont.add_offset("pos")

            # functions.alignTo(self.cont_offset, self.rootInit, position=True, rotation=False)
            functions.align_to(_cont_offset, init, position=True, rotation=True)
            # functions.alignTo(self.cont_pos, self.rootInit, position=True, rotation=True)

            cmds.connectAttr(
                "%s.contVis" % self.scaleGrp, "%s.v" % _cont_offset, force=True
            )
            cmds.parent(_cont_offset, self.controllerGrp)

            if self.controllerSurface:
                follicle = parentToSurface.parentToSurface(
                    [_cont_bind], surface=self.controllerSurface, mode="none"
                )[0]
                # constrain controller translate to the follicle
                # connection.matrixConstraint(follicle, self.cont_bind, mo=False, sr="xyz", ss="xyz")
                _sr = "xyz" if self.rotateObject else None
                if self.bindScales:
                    cmds.connectAttr(
                        "%s.scale" % self.scaleGrp, "%s.scale" % follicle, force=True
                    )
                    _ss = None
                else:
                    _ss = "xyz"
                _mo = False if self.rotateObject else True
                connection.matrixConstraint(
                    follicle,
                    _cont_bind,
                    maintainOffset=_mo,
                    skipRotate=_sr,
                    skipScale=_ss,
                )

                cmds.parent(follicle, self.nonScaleGrp)
                cmds.connectAttr(
                    "%s.rigVis" % self.scaleGrp, "%s.v" % follicle, force=True
                )

            if self.rotateObject:
                connection.matrixConstraint(
                    self.rotateObject,
                    _cont_bind,
                    maintainOffset=True,
                    skipTranslate="xyz",
                    skipScale="xyz",
                )
                # connection.matrixConstraint(self.rotateObject, self.cont_bind, mo=True, st="xyz", ss=_ss)

            negate_mult_matrix = cmds.createNode(
                "multMatrix",
                name=naming.parse([self.module_name, "negate"], suffix="multMatrix"),
            )
            negate_decompose = cmds.createNode(
                "decomposeMatrix",
                name=naming.parse([self.module_name, "negate"], suffix="decompose"),
            )
            cmds.connectAttr(
                "%s.inverseMatrix" % _cont.name,
                "%s.matrixIn[0]" % negate_mult_matrix,
                force=True,
            )
            cmds.connectAttr(
                "%s.matrixSum" % negate_mult_matrix,
                "%s.inputMatrix" % negate_decompose,
                force=True,
            )
            cmds.connectAttr(
                "%s.outputTranslate" % negate_decompose,
                "%s.translate" % _cont_negate,
                force=True,
            )
            cmds.connectAttr(
                "%s.outputRotate" % negate_decompose,
                "%s.rotate" % _cont_negate,
                force=True,
            )
            cmds.connectAttr(
                "%s.outputScale" % negate_decompose,
                "%s.scale" % _cont_negate,
                force=True,
            )

            if self.isPlugOnLocal:
                pass  # nothing to connect because plug is local joint itself
            else:
                cmds.parentConstraint(_cont.name, self.limbPlug, maintainOffset=False)

            # Direct connection between controller and joint
            for attr in "trs":
                for axis in "xyz":
                    cmds.connectAttr(
                        "%s.%s%s" % (_cont.name, attr, axis),
                        "%s.%s%s" % (joint_bind, attr, axis),
                        force=True,
                    )

    def execute(self):
        # self.createGrp()
        self.create_joints()
        self.create_controllers_and_connections()


class Guides(GuidesCore):
    name = "Surface"
    limb_data = LIMB_DATA

    def draw_joints(self):
        cmds.select(clear=True)
        r_point_j = om.MVector(0, 0, 0) * self.tMatrix
        if not self.segments:
            self.offsetVector = om.MVector(0, 1, 0)
            surface_root_jnt = cmds.joint(
                name=naming.parse([self.name, "root"], side=self.side, suffix="jInit")
            )
            self.guideJoints.append(surface_root_jnt)
            return

        if self.side == "C":
            # Guide joint positions for limbs with no side orientation
            n_point_j = om.MVector(0, 0, 10) * self.tMatrix
        else:
            # Guide-joint positions for limbs with sides
            n_point_j = om.MVector(10 * self.sideMultiplier, 0, 0) * self.tMatrix

        add_val = (n_point_j - r_point_j) / ((self.segments + 1) - 1)

        # Define the offset vector
        self.offsetVector = (n_point_j - r_point_j).normal()

        # Draw the joints
        for seg in range(self.segments + 1):
            surface_jnt = cmds.joint(
                position=(r_point_j + (add_val * seg)),
                name=naming.parse([self.name, seg], side=self.side, suffix="jInit"),
            )
            # Update the guideJoints list
            self.guideJoints.append(surface_jnt)

        # Update the guideJoints list

        # set orientation of joints
        joint.orient_joints(
            self.guideJoints,
            world_up_axis=self.upVector,
            up_axis=(0, 1, 0),
            reverse_aim=self.sideMultiplier,
            reverse_up=self.sideMultiplier,
        )

    def define_guides(self):
        joint.set_joint_type(self.guideJoints[0], "Surface")
        if len(self.guideJoints) > 1:
            _ = [
                joint.set_joint_type(jnt, "SurfaceItem") for jnt in self.guideJoints[1:]
            ]
