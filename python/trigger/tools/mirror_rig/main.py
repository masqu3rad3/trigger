"""Main class for mirror rigging."""

from maya import cmds
from trigger.objects import controller

import logging

LOG = logging.getLogger(__name__)

class MirrorRig(object):
    """Mirror Rigging class."""
    axis_map = {"X": 0, "Y": 1, "Z": 2}

    def __init__(self, mirror_axis="Z", name="mirror_rig"):
        """Initialize the Mirror Rig."""
        self.meshes = []

        self._mirror_group = (
            None  # this is the group that holds all the mirrored meshes.
        )
        self._name = name
        self._mirror_axis = mirror_axis

    @property
    def controller(self):
        """Return the defined controller."""
        return self._controller

    @property
    def name(self):
        """Return the defined name."""
        return self._name

    def set_name(self, name):
        """Set the name of the mirror rig."""
        if not isinstance(name, str):
            raise ValueError("Name must be a string value. Got {}".format(type(name)))
        self._name = name

    def _initialize(self):
        """Set up the initial mirror rig."""
        self._mirror_group = cmds.group(empty=True, name="{}_group".format(self._name))
        self._controller = controller.Controller(
            shape="Square", name="{}_controller".format(self._name), normal=(0, 0, 1)
        )

        compose_matrix = cmds.createNode("composeMatrix", name="{}_composeMatrix".format(self._name))
        cmds.setAttr("{0}.inputScale{1}".format(compose_matrix, self._mirror_axis), -1)
        mult_matrix = cmds.createNode("multMatrix", name="{}_multMatrix".format(self._name))
        decompose_matrix = cmds.createNode("decomposeMatrix", name="{}_decomposeMatrix".format(self._name))

        cmds.connectAttr("{}.outputMatrix".format(compose_matrix), "{}.matrixIn[0]".format(mult_matrix))
        cmds.connectAttr("{}.worldInverseMatrix[0]".format(self._controller.name), "{}.matrixIn[1]".format(mult_matrix))
        cmds.connectAttr("{}.outputMatrix".format(compose_matrix), "{}.matrixIn[2]".format(mult_matrix))
        cmds.connectAttr("{}.worldMatrix[0]".format(self._controller.name), "{}.matrixIn[3]".format(mult_matrix))

        cmds.connectAttr("{}.matrixSum".format(mult_matrix), "{}.inputMatrix".format(decompose_matrix))
        cmds.connectAttr("{}.outputTranslate".format(decompose_matrix), "{}.translate".format(self._mirror_group))
        cmds.connectAttr("{}.outputRotate".format(decompose_matrix), "{}.rotate".format(self._mirror_group))


    def add_mesh(self, mesh):
        """Add a mesh to the mirror rig."""
        if mesh not in self.meshes:
            self.meshes.append(mesh)
        else:
            LOG.warning("Mesh {} already exists in this mirror rig. Skipping.".format(mesh))
    def add_meshes_by_group(self, group, recursive=True):
        """Add all meshes in a group to the mirror rig."""
        meshes = cmds.listRelatives(
            group, children=True, shapes=True, allDescendents=recursive
        )
        for mesh in meshes:
            self.add_mesh(cmds.listRelatives(mesh, parent=True)[0])

    def _mirror_mesh(self, mesh):
        """Mirror a mesh."""
        mirror_geo = cmds.instance(mesh, name="{}_MIRROR".format(mesh))[0]
        cmds.setAttr("{0}.s{1}".format(mirror_geo, self._mirror_axis.lower()), -1)
        # compensate if the pivot is not in world center
        # get the existing value on mirror axis
        previous_value = cmds.getAttr("{0}.t{1}".format(mirror_geo, self._mirror_axis.lower()))
        pivot_difference = cmds.xform(mirror_geo, absolute=True, rotatePivot=True, query=True)[self.axis_map[self._mirror_axis.upper()]]
        cmds.setAttr("{0}.t{1}".format(mirror_geo, self._mirror_axis.lower()), (previous_value*-1) + (-pivot_difference*2))
        cmds.parent(mirror_geo, self._mirror_group, relative=True)

    def update(self):
        """Update the mirror rig."""
        for mesh in self.meshes:
            if not cmds.objExists("{}_MIRROR".format(mesh)):
                self._mirror_mesh(mesh)

    def create(self):
        """Create the mirror rig."""
        self._initialize()
        for mesh in self.meshes:
            self._mirror_mesh(mesh)