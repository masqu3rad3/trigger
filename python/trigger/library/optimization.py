"""Collection of methods aiming to optimize the scene and rig itself"""

from maya import cmds
from trigger.library import arithmetic as ar

def switch_connections(switch, override_switch, kill_nodes, switch_on_visibles, switch_on_invisibles):
    """
    Creates visibility and nodeState connections between controllers and nodes

    Args:
        switch: (String) Attribute which will act as the on off switch. e.g. 'pref_cont.faceProxyMode'
        override_switch: (String) Attribute which will globally override the switch.
                This will make every defined node visible on both switch_on_visibles and switch_on_invisibles lists and
                switch the nodestates into 'normal' state no matter what
        kill_nodes: (List) nodes which will be turned off when the switch turned on
        switch_on_visibles: (List) nodes which their visibilities will turned on when the switch is on.
                These will be always visible if the override_switch is on
        switch_on_invisibles: (List) nodes which will be invisible when the switch is on.
                These will be always visible if the override_switch is on

    Returns: None

    """
    switch_n = ar.reverse(switch)
    condition_node = ar.if_else(override_switch, "==", 1, 1, switch_n, return_plug=False)
    cmds.setAttr("%s.colorIfTrueG" % condition_node, 1)
    cmds.setAttr("%s.colorIfTrueB" % condition_node, 0)
    cmds.connectAttr(switch, "%s.colorIfFalseG" % condition_node)
    cmds.connectAttr(switch, "%s.colorIfFalseB" % condition_node)

    switch_on_invisible_p = ("%s.outColorR" % condition_node)
    switch_on_visible_p = ("%s.outColorG" % condition_node)
    switch_on_kill_p = ("%s.outColorB" % condition_node)

    for node in switch_on_visibles:
        cmds.connectAttr(switch_on_visible_p, "%s.v" % node)

    for node in switch_on_invisibles:
        cmds.connectAttr(switch_on_invisible_p, "%s.v" % node)

    for node in kill_nodes:
        cmds.connectAttr(switch_on_kill_p, "%s.nodeState" % node)