"""transform related functions"""
from maya import cmds
from trigger.core.decorators import keepframe
from trigger.core import filelog
from trigger.library import api

log = filelog.Filelog(logname=__name__, filename="trigger_log")


def set_limits(node, attribute, attr_min, attr_max):
    """Set a control's transform attribute limits.

    Args:
        node(str): Name of node to set limits on.
        attribute(str): Name of transform attribute to set limits on.
        attr_min (float): Attribute minimum to be set.
        attr_max (float): Attribute maxiumum to be set.
    """
    flag_dict = {
        "translateX": {"etx": (1, 1), "tx": (attr_min, attr_max)},
        "tx": {"etx": (1, 1), "tx": (attr_min, attr_max)},
        "translateY": {"ety": (1, 1), "ty": (attr_min, attr_max)},
        "ty": {"ety": (1, 1), "ty": (attr_min, attr_max)},
        "translateZ": {"etz": (1, 1), "tz": (attr_min, attr_max)},
        "tz": {"etz": (1, 1), "tz": (attr_min, attr_max)},
        "rotateX": {"erx": (1, 1), "rx": (attr_min, attr_max)},
        "rx": {"erx": (1, 1), "rx": (attr_min, attr_max)},
        "rotateY": {"ery": (1, 1), "ry": (attr_min, attr_max)},
        "ry": {"ery": (1, 1), "ry": (attr_min, attr_max)},
        "rotateZ": {"erz": (1, 1), "rz": (attr_min, attr_max)},
        "rz": {"erz": (1, 1), "rz": (attr_min, attr_max)},
        "scaleX": {"esx": (1, 1), "sx": (attr_min, attr_max)},
        "sx": {"esx": (1, 1), "sx": (attr_min, attr_max)},
        "scaleY": {"esy": (1, 1), "sy": (attr_min, attr_max)},
        "sy": {"esy": (1, 1), "sy": (attr_min, attr_max)},
        "scaleZ": {"esz": (1, 1), "sz": (attr_min, attr_max)},
        "sz": {"esz": (1, 1), "sz": (attr_min, attr_max)},
    }
    if attribute in flag_dict.keys():
        cmds.transformLimits(node, **flag_dict[attribute])


def query_limits(node, attribute):
    """Query transform attribute limits.

    Args:
        node(str): Name of node to quert limits.
        attribute(str): Name of transform attribute to query limits.
    """
    log.warning("transform.query_limits is deprecated. Use attribute.query_limits instead")
    enabled_flag_dict = {
        "translateX": {"etx": True},
        "tx": {"etx": True},
        "translateY": {"ety": True},
        "ty": {"ety": True},
        "translateZ": {"etz": True},
        "tz": {"etz": True},
        "rotateX": {"erx": True},
        "rx": {"erx": True},
        "rotateY": {"ery": True},
        "ry": {"ery": True},
        "rotateZ": {"erz": True},
        "rz": {"erz": True},
        "scaleX": {"esx": True},
        "sx": {"esx": True},
        "scaleY": {"esy": True},
        "sy": {"esy": True},
        "scaleZ": {"esz": True},
        "sz": {"esz": True},
    }
    limits_flag_dict = {
        "translateX": {"tx": True},
        "tx": {"tx": True},
        "translateY": {"ty": True},
        "ty": {"ty": True},
        "translateZ": {"tz": True},
        "tz": {"tz": True},
        "rotateX": {"rx": True},
        "rx": {"rx": True},
        "rotateY": {"ry": True},
        "ry": {"ry": True},
        "rotateZ": {"rz": True},
        "rz": {"rz": True},
        "scaleX": {"sx": True},
        "sx": {"sx": True},
        "scaleY": {"sy": True},
        "sy": {"sy": True},
        "scaleZ": {"sz": True},
        "sz": {"sz": True},
    }
    if attribute in enabled_flag_dict.keys():
        state = cmds.transformLimits(node, q=True, **enabled_flag_dict[attribute])
        limits = cmds.transformLimits(node, q=True, **limits_flag_dict[attribute])
        return state, limits
    else:
        log.error("query_limits error. %s is not a valid transform attribute" % attribute)


def free_limits(node, attr_list=None):
    """Free the given transform attributes on the given node."""
    attr_list = attr_list or ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"]
    for attr in attr_list:
        cmd = "cmds.transformLimits('{0}', e{1}=(0,0))".format(node, attr)
        eval(cmd)


@keepframe
def duplicate(node, name=None, at_time=None):
    """
    Duplicate a node at the current time or at the given time.

    Args:
        node (str): Name of node to duplicate.
        name (str): Name of new node.
        at_time (int): Time to duplicate node at.

    Returns:
        str: Name of new node.
    """
    if not isinstance(at_time, (int, float)):
        raise ValueError("at_time must be an int or float")
    if at_time:
        cmds.currentTime(at_time)
    node_name = name or "%s_dup" % node
    return cmds.duplicate(node, name=node_name)[0]


def is_group(node):
    """Check if the given node is a group node or not."""
    if cmds.objectType(node) != "transform":
        return False
    return not bool(cmds.listRelatives(node, children=True, shapes=True))


def validate_group(group_name):
    """Check if the group exist, if not create it.
    If there are any non-group object with that name, raises exception"""
    if cmds.objExists(group_name):
        if is_group(group_name):
            return group_name
        else:
            log.error("%s is not a valid group name. There is another non-group object with the same same" % group_name)
    else:
        return cmds.group(name=group_name, em=True)


def get_color(node):
    """Return the normalized color values of given node."""
    _color = None
    # First check the node itself
    if cmds.getAttr("%s.overrideEnabled" % node):
        if cmds.getAttr("%s.overrideShading" % node):
            if cmds.getAttr("%s.overrideRGBColors" % node):
                _color = cmds.getAttr("%s.overrideColorRGB" % node)
                return _color[0]
            else:
                _color_id = cmds.getAttr("%s.overrideColor" % node)
                color_ids = {
                    0: (0.471, 0.471, 0.471),
                    1: (0, 0, 0),
                    2: (0.251, 0.251, 0.251),
                    3: (0.502, 0.502, 0.502),
                    4: (0.608, 0, 0.157),
                    5: (0, 0.016, 0.376),
                    6: (0, 0, 1),
                    7: (0, 0.275, 0.098),
                    8: (0.149, 0, 0.263),
                    9: (0.784, 0, 0.784),
                    10: (0.541, 0.282, 0.2),
                    11: (0.247, 0.137, 0.122),
                    12: (0.6, 0.149, 0),
                    13: (1, 0, 0),
                    14: (0, 1, 0),
                    15: (0, 0.255, 0.6),
                    16: (1, 1, 1),
                    17: (1, 1, 0),
                    18: (0.392, 0.863, 1),
                    19: (0.263, 1, 0.639),
                    20: (1, 0.69, 0.69),
                    21: (0.894, 0.675, 0.475),
                    22: (1, 1, 0.388),
                    23: (0, 0.6, 0.329),
                    24: (0.631, 0.412, 0.188),
                    25: (0.624, 0.631, 0.188),
                    26: (0.408, 0.631, 0.188),
                    27: (0.188, 0.631, 0.365),
                    28: (0.188, 0.631, 0.631),
                    29: (0.188, 0.404, 0.631),
                    30: (0.435, 0.188, 0.631),
                    31: (0.631, 0.188, 0.412)
                }
                return color_ids[_color_id]
    else:
        # check for the shapes
        _shapes = cmds.listRelatives(node, c=True, shapes=True, path=True, fullPath=True) or []
        for shape in _shapes:
            _color = get_color(shape)
    return _color
