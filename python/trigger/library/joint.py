"""Joint related common functions."""

from maya import cmds
from maya.api import OpenMaya

from trigger.core import filelog

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
        value_list = [0] + list(JOINT_TYPE_DICT.values())
        type_int = value_list.index(type_name)
        cmds.setAttr("%s.type" % joint, type_int)
    else:
        cmds.setAttr("%s.type" % joint, 18)  # 18 is the other
        cmds.setAttr("%s.otherType" % joint, type_name, type="string")


def get_joint_type(joint, skip_errors=True):
    """
    Gets the joint type
    Args:
        joint: (String) source joint type
        skip_errors: (Bool) If True, silently return if the type cannot be found, else throw error. Default True

    Returns: (String) joint_type

    """
    type_int = cmds.getAttr("%s.type" % joint)
    if type_int not in JOINT_TYPE_DICT.keys():
        if skip_errors:
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


def get_joint_side(joint, skip_errors=True):
    """
    Gets the joint side
    Args:
        joint: (String) Joint to be queried
        skip_errors: (Bool) If true, error will be silenced and return None

    Returns: (String) Side

    """
    side_int = cmds.getAttr("{0}.side".format(joint))
    if side_int not in JOINT_SIDE_DICT.keys():
        if skip_errors:
            return
        else:
            log.error("Joint Side cannot not be detected (%s)" % joint)
    return JOINT_SIDE_DICT[side_int]

def orient_joints(joint_list, aim_axis=(1.0, 0.0, 0.0), up_axis=(0.0, 1.0, 0.0), world_up_axis=(0.0, 1.0, 0.0),
                  reverse_aim=1.0, reverse_up=1.0):
    """Orient joints.
    Alternative to Maya's native joint orient method
    Args:
        joint_list: (list) Joints list. Order is important.
        aim_axis: (Tuple) Aim Axis of each joint default X
        up_axis: (Tuple) Up Axis of each joint default Y
        world_up_axis: (Tuple) World up axis default Y
        reverse_aim: (int) multiplier for aim. Default 1
        reverse_up: (int) multiplier for reverseUp. Default 1

    Returns:

    """

    aim_axis = reverse_aim * OpenMaya.MVector(aim_axis)
    up_axis = reverse_up * OpenMaya.MVector(up_axis)

    if len(joint_list) == 1:
        return

    # for j in range(1, len(joint_list)):
    #     cmds.parent(joint_list[j], w=True)
    for joint in joint_list[1:]:
        cmds.parent(joint, world=True)

    for nmb, joint in enumerate(joint_list):
        # if its not the last joint:
        if nmb != len(joint_list) - 1:
            aim_con = cmds.aimConstraint(joint_list[nmb + 1], joint, aimVector=aim_axis, upVector=up_axis,
                                         worldUpVector=world_up_axis, worldUpType='vector', weight=1.0)
            cmds.delete(aim_con)
            cmds.makeIdentity(joint, apply=True)

    # re-parent the hierarchy
    for nmb, joint in enumerate(joint_list[1:]):
        cmds.parent(joint, joint_list[nmb])

    # for j in range(1, len(joint_list)):
    #     cmds.parent(joint_list[j], joint_list[j - 1])

    cmds.makeIdentity(joint_list[-1], apply=True)
    cmds.setAttr("{0}.jointOrient".format(joint_list[-1]), 0, 0, 0)


def identify(joint, modules_dictionary):
    """Identify joints for Trigger
    Args:
        joint: (String) Joint to query
        modules_dictionary: (Dictionary)

    Returns: (Tuple) joint_type, limb_type, side

    """
    # define values as no
    limb_type = "N/A"
    joint_type = get_joint_type(joint)

    for key, value in modules_dictionary.items():
        limb_type = key if joint_type in value["members"] else limb_type

    side = get_joint_side(joint)
    return joint_type, limb_type, side


def get_rig_axes(joint):
    """Gets the axis information from the joint.
    Args:
        joint (str): The node to look at the attributes

    Returns (tuple): up_axis, mirror_axis, spineDir

    """
    # get the up axis

    up_axis = [cmds.getAttr("%s.upAxis%s" % (joint, direction)) for direction in "XYZ"]
    mirror_axis = [cmds.getAttr("%s.mirrorAxis%s" % (joint, direction)) for direction in "XYZ"]
    look_axis = [cmds.getAttr("%s.lookAxis%s" % (joint, direction)) for direction in "XYZ"]

    return tuple(up_axis), tuple(mirror_axis), tuple(look_axis)
