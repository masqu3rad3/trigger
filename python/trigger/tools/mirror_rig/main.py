"""Main class for mirror rigging."""

from maya import cmds
from trigger.objects import controller
from trigger.objects.scene_data import SceneDictionary
from trigger.library import attribute
from trigger.library import naming

import logging

LOG = logging.getLogger(__name__)


class MirrorRig(object):
    """Mirror Rigging class."""

    axis_map = {"X": 0, "Y": 1, "Z": 2}
    normal_directions = {"X": (1, 0, 0), "Y": (0, 1, 0), "Z": (0, 0, 1)}

    def __init__(self, mirror_axis="Z", name="mirror"):
        """Initialize the Mirror Rig."""
        # self.meshes = []
        self.data = {}
        self._name = name
        self._mirror_axis = mirror_axis

        self.mirror_grp = "{}_grp".format(self._name)

    @property
    def controller(self):
        """Return the defined controller."""
        return self._controller

    @property
    def name(self):
        """Return the defined name."""
        return self._name

    @property
    def meshes(self):
        """Return the meshes in the mirror rig."""
        return list(self.data.get("mirror_pairs", {}).keys())

    def set_name(self, name):
        """Set the name of the mirror rig."""
        if not isinstance(name, str):
            raise ValueError("Name must be a string value. Got {}".format(type(name)))
        self._name = name

    def reset(self):
        """Reset the mirror rig."""
        for _mesh, reflection in self.data.get("mirror_pairs", {}).items():
            if cmds.objExists(reflection):
                cmds.delete(reflection)
        if cmds.objExists(self.mirror_grp):
            cmds.delete(self.mirror_grp)

    def _initialize(self):
        """Set up the initial mirror rig."""
        if not cmds.objExists(self.mirror_grp):
            # this is the firs time the mirror rig is created in the scene
            self.mirror_grp = cmds.group(empty=True, name=self.mirror_grp)
            self.data = SceneDictionary(self.mirror_grp)
            self.data["mirror_axis"] = self._mirror_axis
            ctrl = controller.Controller(
                shape="Square",
                name="{}_controller".format(self._name),
                normal=self.normal_directions[self._mirror_axis],
            )
            cmds.parent(ctrl.name, self.mirror_grp)
            attribute.lock_and_hide(self.mirror_grp)
            self.data["controller"] = cmds.ls(ctrl.name, long=True)[0]
        else:
            self.data = SceneDictionary(self.mirror_grp)
            print('self.data["mirror_axis"]', self.data["mirror_axis"])
            print("self._mirror_axis", self._mirror_axis)
            if self.data.get("mirror_axis") != self._mirror_axis:
                LOG.warning(
                    "The mirror axis of the scene is not matching to the mirror axis of the rig. "
                    "Resetting mirror."
                )
                self.reset()
                self._initialize()
                return

        ctrl_dag_path = self.data.get("controller")

        compose_matrix = self.data.get("composeMatrix", "")
        mirror_mult_matrix = self.data.get("mirrorMultMatrix", "")

        if not all([compose_matrix, mirror_mult_matrix]):
            compose_matrix = cmds.createNode(
                "composeMatrix", name="{}_composeMatrix".format(self._name)
            )
            self.data["composeMatrix"] = compose_matrix

            cmds.setAttr(
                "{0}.inputScale{1}".format(compose_matrix, self._mirror_axis), -1
            )
            mirror_mult_matrix = cmds.createNode(
                "multMatrix", name="{}_multMatrix".format(self._name)
            )
            self.data["mirrorMultMatrix"] = mirror_mult_matrix

            cmds.connectAttr(
                "{}.outputMatrix".format(compose_matrix),
                "{}.matrixIn[0]".format(mirror_mult_matrix),
                force=True,
            )
            cmds.connectAttr(
                "{}.worldInverseMatrix[0]".format(ctrl_dag_path),
                "{}.matrixIn[1]".format(mirror_mult_matrix),
                force=True,
            )
            cmds.connectAttr(
                "{}.outputMatrix".format(compose_matrix),
                "{}.matrixIn[2]".format(mirror_mult_matrix),
                force=True,
            )
            cmds.connectAttr(
                "{}.worldMatrix[0]".format(ctrl_dag_path),
                "{}.matrixIn[3]".format(mirror_mult_matrix),
                force=True,
            )

    def add_mesh(self, mesh):
        """Add a mesh to the mirror rig."""
        mirror_pairs = self.data.get("mirror_pairs", {})
        if mesh not in mirror_pairs.keys():
            mirror_pairs[mesh] = ""
            self.data["mirror_pairs"] = mirror_pairs
        else:
            LOG.warning(
                "Mesh {} already exists in this mirror rig. Skipping.".format(mesh)
            )

    def add_meshes_by_group(self, group, recursive=True):
        """Add all meshes in a group to the mirror rig."""
        meshes = cmds.listRelatives(
            group, children=True, type="mesh", allDescendents=recursive, fullPath=True
        )
        for mesh in meshes:
            self.add_mesh(cmds.listRelatives(mesh, parent=True, fullPath=True)[0])

    def _mirror_mesh(self, mesh):
        """Mirror a mesh."""
        if not cmds.objExists(mesh):
            LOG.warning("Mesh {} doesn't exist in the scene. Skipping.".format(mesh))
            return
        mirror_pairs = self.data.get("mirror_pairs", {})
        reflection_geo_name = naming.unique_name("{0}_{1}_REFLECTION".format(mesh.split("|")[-1], self._name))
        mirror_geo = cmds.instance(mesh, name=reflection_geo_name)[0]
        mirror_pairs[mesh] = mirror_geo
        self.data["mirror_pairs"] = mirror_pairs
        original_scale = cmds.getAttr("{0}.s{1}".format(mesh, self._mirror_axis.lower()))
        cmds.setAttr("{0}.s{1}".format(mirror_geo, self._mirror_axis.lower()), original_scale * -1)
        # compensate if the pivot is not in world center
        # get the existing value on mirror axis
        previous_value = cmds.getAttr(
            "{0}.t{1}".format(mirror_geo, self._mirror_axis.lower())
        )
        pivot_difference = cmds.xform(
            mirror_geo, absolute=True, rotatePivot=True, query=True
        )[self.axis_map[self._mirror_axis.upper()]]
        cmds.setAttr(
            "{0}.t{1}".format(mirror_geo, self._mirror_axis.lower()),
            (previous_value * -1) + (-pivot_difference * 2),
        )
        cmds.connectAttr(
            "{}.matrixSum".format(self.data["mirrorMultMatrix"]),
            "{}.offsetParentMatrix".format(mirror_geo),
        )

    def update(self):
        """Update the mirror rig."""
        for mesh, reflection in self.data.get("mirror_pairs", {}).items():
            if not cmds.objExists(reflection):
                self._mirror_mesh(mesh)

    def create(self):
        """Create the mirror rig."""
        self._initialize()
        self.update()
        # for mesh, reflection in self.data.get("mirror_pairs", {}).items():
        #     if not cmds.objExists(reflection):
        #         self._mirror_mesh(mesh)
