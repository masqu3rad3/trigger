# pylint: disable=consider-using-f-string
"""Tool for creating mirror lattices."""

import re
import logging

from maya import cmds, mel
from maya.api import OpenMaya

LOG = logging.getLogger(__name__)


def unique_name(name, return_counter=False):
    """
    Searches the scene for match and returns a unique name for given name
    Args:
        name: (String) Name to query
        return_counter: (Bool) If true, returns the next available number insted of the object name

    Returns: (String) uniquename

    """
    base_name = name
    idcounter = 0
    while cmds.objExists(name):
        name = "%s%s" % (base_name, str(idcounter + 1))
        idcounter = idcounter + 1
    if return_counter:
        return idcounter
    else:
        return name


def get_m_dagpath(node):
    """Return the API 2.0 dagPath of given node."""
    sel_list = OpenMaya.MSelectionList()
    sel_list.add(node)
    return sel_list.getDagPath(0)


def get_world_translation(node):
    """Return given nodes world translation of rotate pivot."""
    target_m_transform = OpenMaya.MFnTransform(get_m_dagpath(node))
    target_rotate_pivot = OpenMaya.MVector(
        target_m_transform.rotatePivot(OpenMaya.MSpace.kWorld)
    )
    return target_rotate_pivot


def refreshOutliners():
    eds = cmds.lsUI(editors=True)
    for ed in eds:
        if cmds.outlinerEditor(ed, exists=True):
            cmds.outlinerEditor(ed, e=True, refresh=True)


def uv_pin(mesh_transform, coordinates):
    assert cmds.about(api=True) >= 20200000, "uv_pin requires Maya 2020 and later"
    all_shapes = cmds.listRelatives(
        mesh_transform, shapes=True, children=True, parent=False
    )
    # seperate intermediates
    intermediates = [
        x for x in all_shapes if cmds.getAttr("{}.intermediateObject".format(x)) == 1
    ]
    non_intermediates = [x for x in all_shapes if x not in intermediates]
    deformed_mesh = non_intermediates[0]
    if not intermediates:
        # create original / deformed mesh hiearchy
        dup = cmds.duplicate(mesh_transform, name="{}_ORIG".format(mesh_transform))[0]
        original_mesh = cmds.listRelatives(dup, children=True)[0]
        cmds.parent(original_mesh, mesh_transform, shape=True, r=True)
        cmds.delete(dup)
        _raw_list = cmds.listConnections(
            deformed_mesh, source=True, destination=False, connections=True, plugs=True
        )
        if _raw_list:
            # pair the items in _raw_list into tuples of 2
            connection_pairs = list(zip(_raw_list[1::2], _raw_list[::2]))
            for pair in connection_pairs:
                cmds.connectAttr(
                    pair[0], pair[1].replace(deformed_mesh, original_mesh), force=True
                )

        # hide/intermediate original mesh
        cmds.setAttr("%s.hiddenInOutliner" % original_mesh, 1)
        cmds.setAttr("%s.intermediateObject" % original_mesh, 1)
        refreshOutliners()
    else:
        original_mesh = intermediates[0]

    uv_pin_node = cmds.createNode("uvPin")

    cmds.connectAttr(
        "{}.worldMesh".format(deformed_mesh), "{}.deformedGeometry".format(uv_pin_node)
    )
    cmds.connectAttr(
        "{}.outMesh".format(original_mesh), "{}.originalGeometry".format(uv_pin_node)
    )

    cmds.setAttr("%s.coordinate[0]" % uv_pin_node, *coordinates)

    return uv_pin_node


def get_uv_at_point(position, dest_node):
    """Get a tuple of u, v values for a point on a given mesh.

    Args:
        position (vector3): The world space position to get the uvs of.
        dest_node (str): The mesh with uvs.

    Returns:
        tuple: (float, float) The U and V values.
    """
    selection_list = OpenMaya.MSelectionList()
    selection_list.add(dest_node)
    dag_path = selection_list.getDagPath(0)

    mfn_mesh = OpenMaya.MFnMesh(dag_path)

    point = OpenMaya.MPoint(position)
    space = OpenMaya.MSpace.kWorld

    u_val, v_val, _ = mfn_mesh.getUVAtPoint(point, space)

    return u_val, v_val


def pin_to_surface(node, surface, sr="", st="", ss="xyz"):
    world_pos = get_world_translation(node)
    uv_coordinates = get_uv_at_point(world_pos, surface)
    _uv_pin = uv_pin(surface, uv_coordinates)
    decompose_matrix_node = cmds.createNode(
        "decomposeMatrix", name="decompose_pinMatrix"
    )
    cmds.connectAttr(
        "{}.outputMatrix[0]".format(_uv_pin),
        "{}.inputMatrix".format(decompose_matrix_node),
    )

    for attr in "XYZ":
        if attr.lower() not in sr and attr.upper() not in sr:
            cmds.connectAttr(
                "{0}.outputRotate{1}".format(decompose_matrix_node, attr),
                "{0}.rotate{1}".format(node, attr),
            )

    for attr in "XYZ":
        if attr.lower() not in st and attr.upper() not in st:
            cmds.connectAttr(
                "{0}.outputTranslate{1}".format(decompose_matrix_node, attr),
                "{0}.translate{1}".format(node, attr),
            )

    for attr in "XYZ":
        if attr.lower() not in ss and attr.upper() not in ss:
            cmds.connectAttr(
                "{0}.outputScale{1}".format(decompose_matrix_node, attr),
                "{0}.scale{1}".format(node, attr),
            )

    return _uv_pin


def add_object_to_lattice(obj, lattice_deformer):
    """
    Add the object to the lattice deformer.

    This function does not rely on deformer sets which makes the assignment
    possible where component tags are enabled in Maya versions 2022+
    """

    # create a duplicate of the shape. Make the duplicate final, the old one orig
    # this is in order to keep the incoming connections
    final_shape = cmds.listRelatives(obj, shapes=True)[0]
    orig_shape = cmds.rename(final_shape, "{0}Orig".format(final_shape))
    dup_transform = cmds.duplicate(obj)[0]
    dup_shape = cmds.listRelatives(dup_transform, shapes=True)[0]
    final_shape = cmds.rename(dup_shape, final_shape)
    cmds.parent(final_shape, obj, r=True, s=True)
    cmds.delete(dup_transform)
    cmds.setAttr("{}.intermediateObject".format(orig_shape), 1)

    next_index = mel.eval(
        "getNextFreeMultiIndex %s %s"
        % ("{}.originalGeometry".format(lattice_deformer), 0)
    )
    cmds.connectAttr(
        "{}.worldMesh[0]".format(orig_shape),
        "{0}.input[{1}].inputGeometry".format(lattice_deformer, next_index),
    )
    cmds.connectAttr(
        "{}.outMesh".format(orig_shape),
        "{0}.originalGeometry[{1}]".format(lattice_deformer, next_index),
    )
    cmds.connectAttr(
        "{0}.outputGeometry[{1}]".format(lattice_deformer, next_index),
        "{}.inMesh".format(final_shape),
    )


# pylint: disable=use-of-eval
class MirrorLattice(object):
    """Class for creating mirror lattices."""

    bias_dict = {
        "start": "'{0}'.startswith('{1}')",
        "end": "'{0}'.endswith('{1}')",
        "include": "'{1}' in '{0}'",
    }

    def __init__(self, meshes=None, set_from_selection=False):
        """Initialize the class."""
        self._side_keys = ["L_", "R_"]
        self._side_key_bias = "start"
        self.meshes = meshes or []
        if meshes and not set_from_selection:
            if not isinstance(meshes, (list, tuple)):
                meshes = [meshes]
        if set_from_selection:
            meshes = cmds.ls(sl=True, l=True)
        self.meshes = meshes or []
        self.mirror_meshes = []
        self.mirror_axis = "x"

        # lattice values
        self._divisions = [2, 5, 2]
        self._local_divisions = [2, 2, 2]

        # class variables
        self.master_deformer = None
        self.master_lattice = None
        self.master_base = None
        self.slave_deformer = None
        self.slave_lattice = None
        self.slave_base = None
        self._base_names = []  # names without any side information

        self.mirror_group = None
        self.data_group = None

    @property
    def side_keys(self):
        """Return the mirror keys."""
        return self._side_keys

    @side_keys.setter
    def side_keys(self, value):
        """Set the mirror keys."""
        if not isinstance(value, list):
            LOG.error("Mirror keys must be a list.")
            return
        self._side_keys = value

    @property
    def side_key_bias(self):
        """Return the mirror bias."""
        return self._side_key_bias

    @side_key_bias.setter
    def side_key_bias(self, value):
        """Set the mirror bias."""
        if value not in self.bias_dict.keys():
            LOG.error("Invalid mirror bias. Valid values are %s", self.bias_dict.keys())
            return
        self._side_key_bias = value

    @property
    def divisions(self):
        """Return the lattice divisions."""
        return self._divisions

    @divisions.setter
    def divisions(self, value):
        """Set the lattice divisions."""
        if not isinstance(value, list):
            LOG.error("Divisions must be a list.")
            return
        if len(value) != 3:
            LOG.error("Divisions must have 3 values.")
            return
        for val in value:
            if not isinstance(val, int):
                LOG.error("Divisions must be integers.")
                return
            if val < 2:
                LOG.error("Divisions must be greater than 1.")
                return
        self._divisions = value

    def create_lattice_pairs(self):
        """Create lattices for each side"""
        (
            self.master_deformer,
            self.master_lattice,
            self.master_base,
        ) = self._create_lattice(self.meshes)
        (
            self.slave_deformer,
            self.slave_lattice,
            self.slave_base,
        ) = self._create_lattice(self.mirror_meshes)

        self.mirror_group = cmds.group(
            em=True, name="{}_grp".format("_".join(self._base_names))
        )
        _master_parent = cmds.listRelatives(self.master_base, parent=True)[0]
        _slave_parent = cmds.listRelatives(self.slave_base, parent=True)[0]
        cmds.parent(_master_parent, _slave_parent, self.mirror_group)
        for attr in ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"]:
            cmds.setAttr(
                "{}.{}".format(self.mirror_group, attr),
                lock=True,
                keyable=False,
                channelBox=False,
            )

    def connect_lattices(self):
        """Connect slave lattice to the master"""
        master_points = cmds.ls("{}.pt[*]".format(self.master_lattice), flatten=True)
        name = unique_name(
            "multiMesh_cage"
            if len(self._base_names) > 1
            else "{}_cage".format(self._base_names[0])
        )

        # create a polygon cage for the master lattice which will be used to hold the locators
        mesh_cage = cmds.polyCube(
            subdivisionsWidth=self._divisions[0] - 1,
            subdivisionsHeight=self._divisions[1] - 1,
            subdivisionsDepth=self._divisions[2] - 1,
            name=name,
            constructionHistory=False,
        )[0]
        cmds.matchTransform(mesh_cage, self.master_base)
        add_object_to_lattice(mesh_cage, self.master_deformer)

        _data_grp = cmds.group(mesh_cage, name="data_grp", parent=self.mirror_group)
        # lock and hide the attributes
        for attr in ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"]:
            cmds.setAttr(
                "{}.{}".format(_data_grp, attr),
                lock=True,
                keyable=False,
                channelBox=False,
            )
        cmds.setAttr("{}.v".format(_data_grp), 0)

        for point in master_points:
            # find the mirror point
            _mirror_point_as_array = self._find_mirror_point(
                point, self._divisions, self.mirror_axis
            )
            # parse it back to str to be used as a plug
            slave_point = "{0}.pt[{1}][{2}][{3}]".format(
                self.slave_lattice, *_mirror_point_as_array
            )
            # cmds.connectAttr(point, slave_point)

            master_pos = cmds.xform(
                point, query=True, translation=True, worldSpace=True
            )
            # master_locator = cmds.spaceLocator(name="{0}_loc".format(point))[0]
            master_locator = cmds.group(em=True, name="{0}_loc".format(point))
            cmds.xform(master_locator, translation=master_pos, worldSpace=True)
            pin_to_surface(master_locator, mesh_cage, sr="xyz")

            slave_pos = cmds.xform(
                slave_point, query=True, translation=True, worldSpace=True
            )
            # slave_locator = cmds.spaceLocator(name="{0}_loc".format(slave_point))[0]
            slave_locator = cmds.group(em=True, name="{0}_loc".format(slave_point))
            cmds.xform(slave_locator, translation=slave_pos, worldSpace=True)

            cluster, cluster_handle = cmds.cluster(slave_point)

            cmds.parent(cluster_handle, slave_locator)

            cmds.parent(master_locator, slave_locator, _data_grp)

            for attr in "xyz":
                cmds.connectAttr(
                    "{0}.t{1}".format(master_locator, attr),
                    "{0}.t{1}".format(slave_locator, attr),
                )
            # # connect the locator to the cluster mirroring with mirror axis
            negate_node = cmds.createNode("multDoubleLinear", name="negate")
            cmds.setAttr("{0}.input2".format(negate_node), -1)
            cmds.connectAttr(
                "{0}.t{1}".format(master_locator, self.mirror_axis),
                "{0}.input1".format(negate_node),
            )
            cmds.connectAttr(
                "{0}.output".format(negate_node),
                "{0}.t{1}".format(slave_locator, self.mirror_axis),
                force=True,
            )

            # TODO make an optional keep offset option which will retain any asymmetry

    def _create_lattice(self, meshes):
        """Create a lattice on the mesh."""
        name = unique_name("multiMesh" if len(meshes) > 1 else self._base_names[0])
        deformer, points, base = cmds.lattice(
            meshes,
            divisions=self._divisions,
            objectCentered=True,
            ldivisions=self._local_divisions,
            commonParent=True,
            ol=True,
            name=name,
        )
        return deformer, points, base

    def _find_mirror_mesh_name(self, mesh):
        """Find the mirror mesh in the scene."""

        # temporarily remove the long name
        _short_name = mesh.split("|")[-1]
        print(_short_name)
        # find the mirror mesh using the mirror keys and bias
        if eval(
            self.bias_dict[self._side_key_bias].format(_short_name, self._side_keys[0])
        ):
            self._base_names.append(_short_name.replace(self._side_keys[0], ""))
            return mesh.replace(self._side_keys[0], self._side_keys[1])
        elif eval(
            self.bias_dict[self._side_key_bias].format(_short_name, self._side_keys[1])
        ):
            self._base_names.append(_short_name.replace(self._side_keys[1], ""))
            return mesh.replace(self._side_keys[1], self._side_keys[0])
        else:
            return None

    def validate_meshes(self):
        """Check the resolved meshes are in the scene or not."""
        if not self.meshes:
            LOG.error("No mesh given.")
            return False
        self.mirror_meshes.clear()
        self._base_names.clear()
        for mesh in self.meshes:
            if not cmds.objExists(mesh):
                LOG.error("Mesh {0} does not exist.".format(mesh))
                return False
            # append to mirror meshes only if it returns a valid mesh
            mirror_mesh = self._find_mirror_mesh_name(mesh)
            if mirror_mesh:
                self.mirror_meshes.append(mirror_mesh)
            else:
                LOG.error(
                    "Mirror of {0} cannot be identified with these keys: {1}".format(
                        mesh, self._side_keys
                    )
                )
                return False
            if not cmds.objExists(mirror_mesh):
                LOG.error("Mirror mesh {0} does not exist.".format(mirror_mesh))
                return False
        return True

    @staticmethod
    def _find_mirror_point(ffd_point, divisions, axis="x"):
        """
        Find the mirror point on the opposite side of the ffd.

        Args:
            ffd_point (str): The ffd point to mirror. Must be formatted like
                R_pCylinder_latticeLattice.pt[1][4][1]
            divisions (list): The number of divisions on the ffd in the form
            axis (str): The axis to mirror on. Valid values are x, y, z

        Returns:
            list: integers of mirror point. This needs to be parsed to str again
        """

        # parse the values
        parsed_array = [int(x) for x in re.findall(r"\d+", ffd_point.split(".")[1])]

        axis_map = {"x": 0, "y": 1, "z": 2}
        axis_index = axis_map[axis.lower()]
        axis_value = divisions[axis_index]

        mirror_value = abs(parsed_array[axis_index] - axis_value + 1)
        parsed_array[axis_index] = mirror_value
        return parsed_array

    def create(self):
        """Run the class."""
        if not self.validate_meshes():
            return
        self.create_lattice_pairs()
        self.connect_lattices()
