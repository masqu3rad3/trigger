import sys
from maya import cmds
from trigger.library import api
from trigger.library import naming
# USING MAYA API 2.0
import maya.api.OpenMaya as om

from trigger.core import filelog
# log = logger.Logger(logger_name=__name__)
log = filelog.Filelog(logname=__name__, filename="trigger_log")


JOINT_TYPE_DICT = {
    1: 'Root',
    2: 'Hip',
    3: 'Knee',
    4: 'Foot',
    5: 'Toe',
    6: 'Spine',
    7: 'Neck',
    8: 'Head',
    9: 'Collar',
    10: 'Shoulder',
    11: 'Elbow',
    12: 'Hand',
    13: 'Finger',
    14: 'Thumb',
    18: 'Other',
    19: 'Index_F',
    20: 'Middle_F',
    21: 'Ring_F',
    22: 'Pinky_F',
    23: 'Extra_F',
    24: 'Big_T',
    25: 'Index_T',
    26: 'Middle_T',
    27: 'Ring_T',
    28: 'Pinky_T',
    29: 'Extra_T'
}

JOINT_SIDE_DICT = {
    0: 'C',
    1: 'L',
    2: 'R',
}

AXIS_CONVERSION_DICT = {

}

def getDistance(node1, node2):
    """Returns the distance between two nodes"""
    Ax, Ay, Az = api.getWorldTranslation(node1)
    Bx, By, Bz = api.getWorldTranslation(node2)
    return ((Ax-Bx)**2 + (Ay-By)**2 + (Az-Bz)**2)**0.5

def alignTo(node, target, position=True, rotation=False):
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

    nodeMTransform = om.MFnTransform(api.getMDagPath(node))
    targetMTransform = om.MFnTransform(api.getMDagPath(target))
    if position:
        targetRotatePivot = om.MVector(targetMTransform.rotatePivot(om.MSpace.kWorld))
        nodeMTransform.setTranslation(targetRotatePivot, om.MSpace.kWorld)
    if rotation:
        targetMTMatrix = om.MTransformationMatrix(om.MMatrix(cmds.xform(target, matrix=True, ws=1, q=True)))
        # using the target matrix decomposition
        # Worked on all cases tested
        nodeMTransform.setRotation(targetMTMatrix.rotation(True), om.MSpace.kWorld)

def alignToAlter(node1, node2, mode=0, o=(0,0,0)):
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

def alignAndAim(node, targetList, aimTargetList, upObject=None, upVector=None, localUp=(0.0,1.0,0.0), rotateOff=None, translateOff=None, freezeTransform=False):
    """
    Aligns the position of the node to the target and rotation to the aimTarget object.
    Args:
        node: Node to be aligned
        targetList: (List) Target nodes for positioning
        aimTargetList: (List) Target nodes for aiming
        upObject: (Optional) if defined the up node will be up axis of this object
        rotateOff: (Optional) rotation offset with given value (tuple)
        translateOff: (Optional) translate offset with given value (tuple)
        freezeTransform: (Optional) if set True, freezes transforms of the node at the end

    Returns:
        None

    """
    if upObject and upVector:
        log.error("In alignAndAim function both upObject and upVector parameters cannot be used")
        return

    pointFlags = ""
    for i in range (len(targetList)):
        if not i == 0:
            pointFlags = "%s, " % pointFlags
        pointFlags = "{0}targetList[{1}]".format(pointFlags, str(i))
    pointFlags = "%s, node" % pointFlags
    pointCommand = "cmds.pointConstraint({0})".format(pointFlags)
    tempPo = eval(pointCommand)

    aimFlags = ""
    for i in range (len(aimTargetList)):
        if not i == 0:
            aimFlags = "%s, " % aimFlags
        aimFlags = "{0}aimTargetList[{1}]".format(aimFlags, str(i))
    aimFlags = "%s, node" % aimFlags
    aimFlags = "%s, u=%s" % (aimFlags, localUp)
    if upObject:
        aimFlags = "%s, wuo=upObject, wut='object'" % aimFlags
    if upVector:
        aimFlags = "%s, wu=upVector, wut='vector'" % aimFlags

    aimCommand = "cmds.aimConstraint({0})".format(aimFlags)
    tempAim = eval(aimCommand)

    cmds.delete(tempPo)
    cmds.delete(tempAim)
    if translateOff:
        cmds.move(translateOff[0], translateOff[1], translateOff[2], node, r=True)
    if rotateOff:
        cmds.rotate(rotateOff[0], rotateOff[1], rotateOff[2], node, r=True, os=True)
    if freezeTransform:
        cmds.makeIdentity(node, a=True, t=True)

def alignBetween (node, targetA, targetB, position=True, aim_b=True, orientation=False, o=(0,0,0)):
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
def createUpGrp(node, suffix, freezeTransform=True):
    """
    Creates an Upper Group for the given object.
    Args:
        node: (String) Source Object
        suffix: (String) Suffix for the group. String.
        freezeTransform: (Boolean) Stands for "makeIdentity" If True, freezes the transformations of the new group. Default is True

    Returns: The created group node

    """
    grpName = naming.uniqueName("%s_%s" % (node, suffix))
    newGrp = cmds.group(em=True, name=grpName)

    #align the new created empty group to the selected object

    alignTo(newGrp, node, position=True, rotation=True)

    #check if the target object has a parent
    originalParent = cmds.listRelatives(node, p=True)
    if originalParent:
        cmds.parent(newGrp, originalParent[0], r=False)
        if freezeTransform:
            cmds.makeIdentity(newGrp, a=True)

    cmds.parent(node,newGrp)
    return newGrp

# TODO: MOVE TO THE TRANSFORM MODULE
def isGroup(node):
    """Checks if the given node is a group node or not"""
    if cmds.listRelatives(node, children=True, shapes=True):
        return False
    else:
        return True

# TODO: MOVE TO THE TRANSFORM MODULE
def validateGroup(group_name):
    "checks if the group exist, if not creates it. If there are any non-group object with that name, raises exception"
    if cmds.objExists(group_name):
        if isGroup(group_name):
            return group_name
        else:
            log.error("%s is not a valid group name. There is another non-group object with the same same" %group_name)
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
        log.error("index or customColor arguments must defined", proceed=False)
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
                log.error("Colorize error... Unknown index command", proceed=False)
        else:
            log.error("Colorize error... Index flag must be integer or string('L', 'R', 'C')", proceed=False)
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

def set_joint_type(joint, type_name):
    """
    Sets Trigger Joint Type
    Args:
        joint: (String) Source Joint
        type_name: (String) Name of the joint

    Returns: None

    """
    if type_name in JOINT_TYPE_DICT.values():
        # get the key from the value. This is compatible with both python3 and python2
        value_list = [0]+list(JOINT_TYPE_DICT.values())
        type_int = value_list.index(type_name)
        cmds.setAttr("%s.type" % joint, type_int)
    else:
        cmds.setAttr("%s.type" % joint , 18) # 18 is the other
        cmds.setAttr("%s.otherType" % joint, type_name, type="string")

def get_joint_type(joint, skipErrors=True):
    """
    Gets the joint type
    Args:
        joint: (String) source joint type
        skipErrors: (Bool) If True, silently return if the type cannot be found, else throw error. Default True

    Returns: (String) joint_type

    """
    type_int = cmds.getAttr("%s.type" % joint)
    if type_int not in JOINT_TYPE_DICT.keys():
        if skipErrors:
            return
        else:
            log.error("Cannot detect joint type => %s" % joint)
    if type_int == 18:
        type_name = cmds.getAttr("{0}.otherType".format(joint))
    else:
        type_name = JOINT_TYPE_DICT[type_int]
    return type_name

def set_joint_side(joint, side):
    """
    Sets the Joint side
    Args:
        joint: (String) Joint to work on
        side: (String) Side value. Valid values are 'l', 'r', 'c', 'left', 'right', 'center' Not Case sensitive

    Returns:

    """
    if side.lower() == "left" or side.lower() == "l":
        cmds.setAttr("%s.side" % joint, 1)
    elif side.lower() == "right" or side.lower() == "r":
        cmds.setAttr("%s.side" % joint, 2)
    elif side.lower() == "center" or side.lower() == "c":
        cmds.setAttr("%s.side" % joint, 0)
    else:
        log.error("%s is not a valid side value" % side)

def get_joint_side(joint, skipErrors=True):
    """
    Gets the joint side
    Args:
        joint: (String) Joint to be queried
        skipErrors: (Bool) If true, error will be silenced and return None

    Returns: (String) Side

    """
    side_int = cmds.getAttr("{0}.side".format(joint))
    if side_int not in JOINT_SIDE_DICT.keys():
        if skipErrors:
            return
        else:
            log.error("Joint Side cannot not be detected (%s)" % joint)
    return JOINT_SIDE_DICT[side_int]

def identifyMaster(joint, modules_dictionary):
    """
    Trigger Joint identification
    Args:
        joint: (String) Joint to query
        modules_dictionary: (Dictionary)

    Returns: (Tuple) jointType, limbType, side

    """
    # define values as no
    limbType = "N/A"
    jointType = get_joint_type(joint)

    for key, value in modules_dictionary.items():
        limbType = key if jointType in value["members"] else limbType

    side = get_joint_side(joint)
    return jointType, limbType, side

def getRigAxes(joint):
    """
    Gets the axis information from the joint which should be written with initBonesClass when created or defined.
    Args:
        joint: The node to look at the attributes

    Returns: upAxis, mirrorAxis, spineDir

    """
    # get the up axis

    upAxis = [cmds.getAttr("%s.upAxis%s" % (joint, dir)) for dir in "XYZ"]
    mirrorAxis = [cmds.getAttr("%s.mirrorAxis%s" % (joint, dir)) for dir in "XYZ"]
    lookAxis = [cmds.getAttr("%s.lookAxis%s" % (joint, dir)) for dir in "XYZ"]

    return tuple(upAxis), tuple(mirrorAxis), tuple(lookAxis)

def getMirror(node):
    """Returns the mirror controller if exists"""

    if "_LEFT_" in node:
        mirrorNode = node.replace("_L", "_R")

    elif "_RIGHT_" in node:
        mirrorNode = node.replace("_R", "_L")
    else:
        mirrorNode = None
        cmds.warning("Cannot find the mirror controller")
    if mirrorNode:
        return mirrorNode

def alignNormal(node, normalVector):
    """
    Aligns the object according to the given normal vector
    Args:
        node: The node to be aligned
        normalVector: Alignment vector

    Returns: None

    """
    # create a temporary alignment locator
    tempTarget = cmds.spaceLocator(name="tempAlignTarget")[0]
    alignTo(tempTarget, node)
    cmds.makeIdentity(tempTarget, a=True)
    cmds.move(normalVector[0], normalVector[1], normalVector[2], tempTarget)
    cmds.delete(cmds.aimConstraint(tempTarget, node, aim=(0,1,0), mo=False))
    cmds.delete(tempTarget)


def orientJoints(jointList, aimAxis=(1.0,0.0,0.0), upAxis=(0.0,1.0,0.0), worldUpAxis=(0.0,1.0,0.0), reverseAim=1, reverseUp=1):
    """
    Orients joints. Alternative to maya's native joint orient method
    Args:
        jointList: (list) Joints list. Order is important.
        aimAxis: (Tuple) Aim Axis of each joint default X
        upAxis: (Tuple) Up Axis of each joint default Y
        worldUpAxis: (Tuple) Worls up axis default Y
        reverseAim: (int) multiplier for aim. Default 1
        reverseUp: (int) multiplier for reverseUp. Default 1

    Returns:

    """

    aimAxis = reverseAim*om.MVector(aimAxis)
    upAxis = reverseUp*om.MVector(upAxis)

    if len(jointList) == 1:
        pass
        return


    for j in range(1, len(jointList)):
        cmds.parent(jointList[j], w=True)

    for j in range (0, len(jointList)):

        if not (j == (len(jointList)-1)):
            aimCon = cmds.aimConstraint(jointList[j+1], jointList[j], aim=aimAxis, upVector=upAxis, worldUpVector=worldUpAxis, worldUpType='vector', weight=1.0)
            cmds.delete(aimCon)
            cmds.makeIdentity(jointList[j], a=True)
    #
    # re-parent the hierarchy
    for j in range (1, len(jointList)):
        cmds.parent(jointList[j], jointList[j-1])

    cmds.makeIdentity(jointList[-1], a=True)
    cmds.setAttr("{0}.jointOrient".format(jointList[-1]), 0,0,0)

def uniqueList(seq): # Dave Kirby
    """Returns an ordered unique list from the given list"""
    # Order preserving
    seen = set()
    return [x for x in seq if x not in seen and not seen.add(x)]

def getParent(node):
    """Returns the parent of the given node"""
    parentList = cmds.listRelatives(node, parent=True)
    return parentList[0] if parentList else None

def getShapes(node):
    """Returns shapes of the given node"""
    return cmds.listRelatives(node, c=True, shapes=True)

# TODO: MOVE TO THE TRANSFORM MODULE ??
def getMeshes(node):
    """Gets only the mesh transform nodes under a group"""
    all_mesh_shapes = cmds.listRelatives(node, ad=True, children=True, type="mesh")
    return uniqueList([getParent(mesh) for mesh in all_mesh_shapes])

def delete_intermediates(transform_node):
    """deletes the intermediate shapes under given transform node"""
    shapes = getShapes(transform_node)
    for shape in shapes:
        if cmds.getAttr("%s.intermediateObject" % shape) == 1:
            deleteObject(shape)


def deleteObject(keyword, force=True):
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
