"""transform related functions"""
from maya import cmds

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
    }
    if attribute in flag_dict.keys():
        cmds.transformLimits(node, **flag_dict[attribute])

def free_limits(node, attr_list = ("tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz")):
    for attr in attr_list:
        cmd = "cmds.transformLimits('{0}', e{1}=(0,0))".format(node, attr)
        eval(cmd)

def reference(node):
    cmds.setAttr("%s.overrideEnabled" %node, 1)
    cmds.setAttr("%s.overrideDisplayType" %node, 2)

