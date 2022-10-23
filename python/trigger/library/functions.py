import sys
from maya import cmds
from trigger.library import api
from trigger.library import naming
# USING MAYA API 2.0
import maya.api.OpenMaya as om

from trigger.core import filelog
# log = logger.Logger(logger_name=__name__)
LOG = filelog.Filelog(logname=__name__, filename="trigger_log")

def get_distance(node1, node2):
    """Return the distance between two nodes."""
    ax, ay, az = api.get_world_translation(node1)
    bx, by, bz = api.get_world_translation(node2)
    return ((ax-bx)**2 + (ay-by)**2 + (az-bz)**2)**0.5

def align_to(node, target, position=True, rotation=False):
    """
    This is the fastest align method. May not work in all cases
    http://www.rihamtoulan.com/blog/2017/12/21/matching-transformation-in-maya-and-mfntransform-pitfalls

    Args:
        node: (String) Node to be aligned
        target: (String) Align target
        position: (Bool) Match world position. Default True
        rotation: (Bool) Match rotation. Defaulf False

    Returns: None

    """

    nodeMTransform = om.MFnTransform(api.get_m_dagpath(node))
    targetMTransform = om.MFnTransform(api.get_m_dagpath(target))
    if position:
        targetRotatePivot = om.MVector(targetMTransform.rotatePivot(om.MSpace.kWorld))
        nodeMTransform.setTranslation(targetRotatePivot, om.MSpace.kWorld)
    if rotation:
        targetMTMatrix = om.MTransformationMatrix(om.MMatrix(cmds.xform(target, matrix=True, ws=1, q=True)))
        # using the target matrix decomposition
        # Worked on all cases tested
        nodeMTransform.setRotation(targetMTMatrix.rotation(True), om.MSpace.kWorld)

def align_to_alter(node1, node2, mode=0, o=(0, 0, 0)):
    """
    Aligns the first node to the second. Alternative method to alignTo
    Args:
        node1: (String) Node to be aligned.
        node2: (String) Target Node.
        mode: (int) Specifies the alignment Mode. Valid Values: 0=position only, 1=Rotation Only, 2=Position and Rotation
        o: (Tuple or List) Offset Value. Default: (0,0,0)

    Returns:None

    """
    if mode==0:
        ##Position Only
        cmds.delete(cmds.pointConstraint(node2, node1, mo=False))
    elif mode==1:
        ##Rotation Only
        cmds.delete(cmds.orientConstraint(node2, node1, o=o, mo=False))
    elif mode==2:
        ##Position and Rotation
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
        rotate_offset (tuple): (Optional) rotation offset with given value
        translate_offset (tuple): (Optional) translate offset with given value
        freeze_transforms (bool): (Optional) if set True, freezes transforms of the node at the end

    Returns:
        None

    """
    # TODO: Avoid using 'eval' function
    if up_object and up_vector:
        LOG.error("In alignAndAim function both upObject and upVector parameters cannot be used")
        return

    point_flags = ""
    for i in range (len(target_list)):
        if not i == 0:
            point_flags = "%s, " % point_flags
        point_flags = "{0}target_list[{1}]".format(point_flags, str(i))
    point_flags = "%s, node" % point_flags
    point_command = "cmds.pointConstraint({0})".format(point_flags)
    temp_pc = eval(point_command)

    aimFlags = ""
    for i in range (len(aim_target_list)):
        if not i == 0:
            aimFlags = "%s, " % aimFlags
        aimFlags = "{0}aim_target_list[{1}]".format(aimFlags, str(i))
    aimFlags = "%s, node" % aimFlags
    aimFlags = "%s, u=%s" % (aimFlags, local_up)
    if up_object:
        aimFlags = "%s, wuo=up_object, wut='object'" % aimFlags
    if up_vector:
        aimFlags = "%s, wu=up_vector, wut='vector'" % aimFlags

    aimCommand = "cmds.aimConstraint({0})".format(aimFlags)
    temp_aim = eval(aimCommand)

    cmds.delete(temp_pc)
    cmds.delete(temp_aim)
    if translate_offset:
        cmds.move(translate_offset[0], translate_offset[1], translate_offset[2], node, r=True)
    if rotate_offset:
        cmds.rotate(rotate_offset[0], rotate_offset[1], rotate_offset[2], node, r=True, os=True)
    if freeze_transforms:
        cmds.makeIdentity(node, a=True, t=True)

def align_between (node, targetA, targetB, position=True, aim_b=True, orientation=False, o=(0, 0, 0)):
    """
    Alignes the node between target A and target B
    Args:
        node(String): Node to be aligned
        targetA(String): Target A
        targetB(String): Target B
        position(bool): If True, aligns the position between targets. Default True
        aim_b(bool): If True, node aims to the targetB
        orientation(bool): If true orients between targetA and targetB
        o(tuple): orientation offset vector


    Returns: None

    """
    if position:
        cmds.delete(cmds.pointConstraint(targetA, targetB, node, mo=False))
    if aim_b:
        cmds.delete(cmds.aimConstraint(targetB,node, mo=False, o=o))
    if orientation:
        cmds.delete(cmds.orientConstraint(targetA, targetB, node, mo=False, o=o))

# TODO: MOVE TO THE TRANSFORM MODULE
def create_offset_group(node, suffix, freezeTransform=True):
    """
    Creates an Upper Group for the given object.
    Args:
        node: (String) Source Object
        suffix: (String) Suffix for the group. String.
        freezeTransform: (Boolean) Stands for "makeIdentity" If True, freezes the transformations of the new group. Default is True

    Returns: The created group node

    """
    grpName = naming.unique_name("%s_%s" % (node, suffix))
    newGrp = cmds.group(em=True, name=grpName)

    #align the new created empty group to the selected object

    align_to(newGrp, node, position=True, rotation=True)

    #check if the target object has a parent
    originalParent = cmds.listRelatives(node, p=True)
    if originalParent:
        cmds.parent(newGrp, originalParent[0], r=False)
        if freezeTransform:
            cmds.makeIdentity(newGrp, a=True)

    cmds.parent(node,newGrp)
    return newGrp

# TODO: MOVE TO THE TRANSFORM MODULE
def is_group(node):
    """Checks if the given node is a group node or not"""
    LOG.warning("isGroup function is moved to transform.is_group. Use that one instead")
    if cmds.listRelatives(node, children=True, shapes=True):
        return False
    else:
        return True

# TODO: MOVE TO THE TRANSFORM MODULE
def validate_group(group_name):
    "checks if the group exist, if not creates it. If there are any non-group object with that name, raises exception"
    LOG.warning("isGroup function is moved to transform.validate_group. Use that one instead")
    if cmds.objExists(group_name):
        if is_group(group_name):
            return group_name
        else:
            LOG.error("%s is not a valid group name. There is another non-group object with the same same" % group_name)
    else:
        return cmds.group(name=group_name, em=True)

def colorize (node_list, index=None, customColor=None, shape=True):
    """
    Changes the wire color of the node to the index
    Args:
        node_list: (list) List of nodes to be processed
        index: (int) Index Number

    Returns:None

    """
    if not index and not customColor:
        LOG.error("index or customColor arguments must defined", proceed=False)
    if customColor: # very ugly backward compatibility workaround
        index = 1
    if not isinstance(node_list, list):
        node_list=[node_list]
    for node in node_list:
        if isinstance(index, int):
            pass
        elif isinstance(index, str):
            sidesDict={"L":6, "R":13, "C":17, "RMIN":9, "LMIN":18, "CMIN":20}
            if index.upper() in sidesDict.keys():
                index = sidesDict[index.upper()]
            else:
                LOG.error("Colorize error... Unknown index command", proceed=False)
        else:
            LOG.error("Colorize error... Index flag must be integer or string('L', 'R', 'C')", proceed=False)
        if shape:
            shapes=cmds.listRelatives(node, s=True)
            node_list = [] if shapes == None else shapes

        if not customColor:
            for node in node_list:
                try: cmds.setAttr("%s.overrideRGBColors", 0)
                except: pass
                cmds.setAttr("%s.overrideEnabled" % node, True)
                cmds.setAttr("%s.overrideColor" % node, index)
        else:
            for node in node_list:
                cmds.setAttr("%s.overrideRGBColors" % node, 1)
                cmds.setAttr("%s.overrideColorRGB" % node, *customColor)

def align_to_normal(node, normalVector):
    """
    Aligns the object according to the given normal vector
    Args:
        node: The node to be aligned
        normalVector: Alignment vector

    Returns: None

    """
    # create a temporary alignment locator
    temp_target = cmds.spaceLocator(name="tempAlignTarget")[0]
    align_to(temp_target, node)
    cmds.makeIdentity(temp_target, a=True)
    cmds.move(normalVector[0], normalVector[1], normalVector[2], temp_target)
    cmds.delete(cmds.aimConstraint(temp_target, node, aim=(0,1,0), mo=False))
    cmds.delete(temp_target)

def unique_list(seq): # Dave Kirby
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
        force: (Bool) If True, the node will be deleted even if its locked. Default True

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
