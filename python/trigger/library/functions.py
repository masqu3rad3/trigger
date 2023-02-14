from maya import cmds
from trigger.library import api
from trigger.library import naming
# USING MAYA API 2.0
from maya.api import OpenMaya

from trigger.core import filelog
LOG = filelog.Filelog(logname=__name__, filename="trigger_log")


def get_distance(node1, node2):
    """Return the distance between two nodes."""
    ax, ay, az = api.get_world_translation(node1)
    bx, by, bz = api.get_world_translation(node2)
    return ((ax-bx)**2 + (ay-by)**2 + (az-bz)**2)**0.5


def align_to(node, target, position=True, rotation=False):
    """
    This is the fastest align method. May not work in all cases
    www.rihamtoulan.com/blog/2017/12/21/matching-transformation-in-maya-and-mfntransform-pitfalls

    Args:
        node: (String) Node to be aligned
        target: (String) Align target
        position: (Bool) Match world position. Default True
        rotation: (Bool) Match rotation. Defaults to False

    Returns: None

    """

    node_m_transform = OpenMaya.MFnTransform(api.get_m_dagpath(node))
    target_m_transform = OpenMaya.MFnTransform(api.get_m_dagpath(target))
    if position:
        target_rotate_pivot = OpenMaya.MVector(target_m_transform.rotatePivot(OpenMaya.MSpace.kWorld))
        node_m_transform.setTranslation(target_rotate_pivot, OpenMaya.MSpace.kWorld)
    if rotation:
        target_mt_matrix = OpenMaya.MTransformationMatrix(
            OpenMaya.MMatrix(cmds.xform(target, matrix=True, ws=1, q=True)))
        # using the target matrix decomposition
        # Worked on all cases tested
        node_m_transform.setRotation(target_mt_matrix.rotation(True), OpenMaya.MSpace.kWorld)


def align_to_alter(node1, node2, mode=0, offset=(0, 0, 0)):
    """
    Aligns the first node to the second. Alternative method to alignTo
    Args:
        node1: (String) Node to be aligned.
        node2: (String) Target Node.
        mode: (int) the alignment Mode. Valid Values: 0=position only, 1=Rotation Only, 2=Position and Rotation
        offset: (Tuple or List) Offset Value. Default: (0,0,0)

    Returns:None

    """
    if mode == 0:
        # Position Only
        cmds.delete(cmds.pointConstraint(node2, node1, mo=False))
    elif mode == 1:
        # Rotation Only
        cmds.delete(cmds.orientConstraint(node2, node1, o=offset, mo=False))
    elif mode == 2:
        # Position and Rotation
        cmds.delete(cmds.parentConstraint(node2, node1, mo=False))


def align_and_aim(node,
                  target_list,
                  aim_target_list,
                  up_object=None,
                  up_vector=None,
                  local_up=(0.0, 1.0, 0.0),
                  rotate_offset=None,
                  translate_offset=None,
                  freeze_transforms=False):
    """
    Aligns the position of the node to the target and rotation to the aimTarget object.
    Args:
        node: Node to be aligned
        target_list (List): Target nodes for positioning
        aim_target_list (List): Target nodes for aiming
        up_object (str): (Optional) if defined the up node will be up axis of this object
        up_vector (str): (Optional) if defined the up vector will be this vector
        local_up (tuple): (Optional) if defined the up vector will be this vector
        rotate_offset (tuple): (Optional) rotation offset with given value
        translate_offset (tuple): (Optional) translate offset with given value
        freeze_transforms (bool): (Optional) if set True, freezes transforms of the node at the end

    Returns:
        None

    """
    # TODO: Avoid using 'eval' function
    if up_object and up_vector:
        LOG.error("Both upObject and upVector parameters cannot be used")
        return

    point_flags = ""
    for i in range(len(target_list)):
        if not i == 0:
            point_flags = "%s, " % point_flags
        point_flags = "{0}target_list[{1}]".format(point_flags, str(i))
    point_flags = "%s, node" % point_flags
    point_command = "cmds.pointConstraint({0})".format(point_flags)
    temp_pc = eval(point_command)

    aim_flags = ""
    for i in range(len(aim_target_list)):
        if not i == 0:
            aim_flags = "%s, " % aim_flags
        aim_flags = "{0}aim_target_list[{1}]".format(aim_flags, str(i))
    aim_flags = "%s, node" % aim_flags
    aim_flags = "%s, u=%s" % (aim_flags, local_up)
    if up_object:
        aim_flags = "%s, wuo=up_object, wut='object'" % aim_flags
    if up_vector:
        aim_flags = "%s, wu=up_vector, wut='vector'" % aim_flags

    aim_command = "cmds.aimConstraint({0})".format(aim_flags)
    temp_aim = eval(aim_command)

    cmds.delete(temp_pc)
    cmds.delete(temp_aim)
    if translate_offset:
        cmds.move(translate_offset[0], translate_offset[1], translate_offset[2], node, r=True)
    if rotate_offset:
        cmds.rotate(rotate_offset[0], rotate_offset[1], rotate_offset[2], node, r=True, os=True)
    if freeze_transforms:
        cmds.makeIdentity(node, a=True, t=True)


def align_between(node, target_a, target_b, position=True, aim_b=True, orientation=False, offset=(0, 0, 0)):
    """Align the node between target A and target B
    Args:
        node(String): Node to be aligned
        target_a(String): Target A
        target_b(String): Target B
        position(bool): If True, aligns the position between targets. Default True
        aim_b(bool): If True, node aims to the targetB
        orientation(bool): If true orients between target_a and target_b
        offset(tuple): orientation offset vector


    Returns: None

    """
    if position:
        cmds.delete(cmds.pointConstraint(target_a, target_b, node, maintainOffset=False))
    if aim_b:
        cmds.delete(cmds.aimConstraint(target_b, node, maintainOffset=False, offset=offset))
    if orientation:
        cmds.delete(cmds.orientConstraint(target_a, target_b, node, maintainOffset=False, offset=offset))


# TODO: MOVE TO THE TRANSFORM MODULE
def create_offset_group(node, suffix, freeze_transform=True):
    """
    Creates an Upper Group for the given object.
    Args:
        node: (String) Source Object
        suffix: (String) Suffix for the group. String.
        freeze_transform: (Boolean) Stands for "makeIdentity" If True, freezes the transformations of the new group.
                        Defaults to True

    Returns: The created group node

    """
    grp_name = naming.unique_name("%s_%s" % (node, suffix))
    new_grp = cmds.group(em=True, name=grp_name)

    # align the new created empty group to the selected object
    align_to(new_grp, node, position=True, rotation=True)

    # check if the target object has a parent
    original_parent = cmds.listRelatives(node, p=True)
    if original_parent:
        cmds.parent(new_grp, original_parent[0], r=False)
        if freeze_transform:
            cmds.makeIdentity(new_grp, a=True)

    cmds.parent(node, new_grp)
    return new_grp


# TODO: MOVE TO THE TRANSFORM MODULE
def is_group(node):
    """Check if the given node is a group node or not."""
    LOG.warning("is_group function moved to transform.is_group. Use that one instead")
    if cmds.listRelatives(node, children=True, shapes=True):
        return False
    else:
        return True


# TODO: MOVE TO THE TRANSFORM MODULE
def validate_group(group_name):
    """Check if the group exist, if not creates it.
    If there are any non-group object with that name, raises exception
    """
    LOG.warning("validate_group function moved to transform.validate_group. Use that one instead")
    if cmds.objExists(group_name):
        if is_group(group_name):
            return group_name
        else:
            LOG.error("%s is not a valid group name. There is another non-group object with the same same" % group_name)
    else:
        return cmds.group(name=group_name, em=True)


def colorize(node_list, index=None, custom_color=None, shape=True):
    """
    Changes the wire color of the node to the index
    Args:
        node_list (list): List of nodes to be processed
        index (int): Index Number
        custom_color (tuple): Custom color value
        shape (bool): If True, changes the shape color. Default is True

    Returns:None
    """
    if not index and not custom_color:
        LOG.error("index or customColor arguments must defined", proceed=False)
    if custom_color:  # very ugly backward compatibility workaround
        index = 1
    if not isinstance(node_list, list):
        node_list = [node_list]
    for node in node_list:
        if isinstance(index, int):
            pass
        elif isinstance(index, str):
            sides_dict = {"L": 6, "R": 13, "C": 17, "RMIN": 9, "LMIN": 18, "CMIN": 20}
            if index.upper() in sides_dict.keys():
                index = sides_dict[index.upper()]
            else:
                LOG.error("Colorize error... Unknown index command", proceed=False)
        else:
            LOG.error("Colorize error... Index flag must be integer or string('L', 'R', 'C')", proceed=False)
        if shape:
            process_nodes = cmds.listRelatives(node, s=True) or []
        else:
            process_nodes = [node]

        if not custom_color:
            for p_node in process_nodes:
                # for node in node_list:
                try:
                    cmds.setAttr("{}.overrideRGBColors".format(p_node), 0)
                except ValueError:
                    pass
                cmds.setAttr("{}.overrideEnabled".format(p_node), True)
                cmds.setAttr("{}.overrideColor".format(p_node), index)
        else:
            for p_node in process_nodes:
                cmds.setAttr("{}.overrideRGBColors".format(p_node), 1)
                cmds.setAttr("{}.overrideColorRGB".format(p_node), *custom_color)


def align_to_normal(node, normal_vector):
    """
    Aligns the object according to the given normal vector
    Args:
        node: The node to be aligned
        normal_vector: Alignment vector

    Returns: None

    """
    # create a temporary alignment locator
    temp_target = cmds.spaceLocator(name="tempAlignTarget")[0]
    align_to(temp_target, node)
    cmds.makeIdentity(temp_target, a=True)
    cmds.move(normal_vector[0], normal_vector[1], normal_vector[2], temp_target)
    cmds.delete(cmds.aimConstraint(temp_target, node, aim=(0, 1, 0), mo=False))
    cmds.delete(temp_target)


def unique_list(seq):  # Dave Kirby
    """Return an ordered unique list from the given list."""
    # Order preserving
    seen = set()
    return [x for x in seq if x not in seen and not seen.add(x)]


def get_parent(node, full_path=False):
    """Return the parent of the given node."""
    parent_list = cmds.listRelatives(node, parent=True, path=True, fullPath=full_path)
    return parent_list[0] if parent_list else None


def get_shapes(node, full_path=False):
    """Return shapes of the given node."""
    return cmds.listRelatives(node, c=True, shapes=True, path=True, fullPath=full_path)


# TODO: MOVE TO THE TRANSFORM MODULE ??
def get_meshes(node, full_path=False):
    """Gets only the mesh transform nodes under a group"""
    all_mesh_shapes = cmds.listRelatives(node, ad=True, children=True, type="mesh", fullPath=full_path)
    return unique_list([get_parent(mesh) for mesh in all_mesh_shapes])


def delete_intermediates(transform_node):
    """deletes the intermediate shapes under given transform node"""
    shapes = get_shapes(transform_node)
    for shape in shapes:
        if cmds.getAttr("%s.intermediateObject" % shape) == 1:
            delete_object(shape)


def delete_object(keyword, force=True):
    """
    Deletes the object only if exists.
    Accepts wildcards.

    Args:
        keyword: (String) name of the object with or without wildcards
        force: (Bool) If True, the node will be deleted even if it's locked. Default True

    Returns: (List) Non - existing nodes

    """
    node_list = cmds.ls(keyword)
    non_existing = []
    for node in node_list:
        if cmds.objExists(node):
            if force:
                cmds.lockNode(node, lock=False)
            cmds.delete(node)
        else:
            non_existing.append(node)
    return non_existing
