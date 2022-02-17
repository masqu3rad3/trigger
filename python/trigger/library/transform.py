"""transform related functions"""
from maya import cmds
from trigger.core.decorators import keepframe
from trigger.core import filelog

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

def free_limits(node, attr_list = ("tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz")):
    for attr in attr_list:
        cmd = "cmds.transformLimits('{0}', e{1}=(0,0))".format(node, attr)
        eval(cmd)

def reference(node):
    cmds.setAttr("%s.overrideEnabled" %node, 1)
    cmds.setAttr("%s.overrideDisplayType" %node, 2)

@keepframe
def duplicate(node, name=None, at_time=None):
    if at_time != None:
        cmds.currentTime(at_time)
    node_name = name or "%s_dup" % node
    return cmds.duplicate(node, name=node_name)[0]

def is_group(node):
    """Checks if the given node is a group node or not"""
    if cmds.listRelatives(node, children=True, shapes=True):
        return False
    else:
        return True

def validate_group(group_name):
    "checks if the group exist, if not creates it. If there are any non-group object with that name, raises exception"
    if cmds.objExists(group_name):
        if is_group(group_name):
            return group_name
        else:
            log.error("%s is not a valid group name. There is another non-group object with the same same" %group_name)
    else:
        return cmds.group(name=group_name, em=True)


