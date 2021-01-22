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
