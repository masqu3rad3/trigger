"""Collection of methods aiming to optimize the scene and rig itself"""

from maya import cmds
from trigger.library import arithmetic as ar
from trigger.library.naming import convert_to_ranged_format


def switch_connections(
    switch, override_switch, kill_nodes, switch_on_visibles, switch_on_invisibles
):
    """
    Create visibility and nodeState connections between controllers and nodes.

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
    condition_node = ar.if_else(
        override_switch, "==", 1, 1, switch_n, return_plug=False
    )
    cmds.setAttr("%s.colorIfTrueG" % condition_node, 1)
    cmds.setAttr("%s.colorIfTrueB" % condition_node, 0)
    cmds.connectAttr(switch, "%s.colorIfFalseG" % condition_node)
    cmds.connectAttr(switch, "%s.colorIfFalseB" % condition_node)

    switch_on_invisible_p = "%s.outColorR" % condition_node
    switch_on_visible_p = "%s.outColorG" % condition_node
    switch_on_kill_p = "%s.outColorB" % condition_node

    for node in switch_on_visibles:
        cmds.connectAttr(switch_on_visible_p, "%s.v" % node)

    for node in switch_on_invisibles:
        cmds.connectAttr(switch_on_invisible_p, "%s.v" % node)

    for node in kill_nodes:
        cmds.connectAttr(switch_on_kill_p, "%s.nodeState" % node)


def set_deformer_influence(deformer, vertex_ids):
    """Limit the deformer influence to the given vertex ids."""

    # get the original geometry from the originalGeometry plug
    _original_geo = cmds.listConnections("{}.originalGeometry".format(deformer),  source=True, destination=False, shapes=True) or []
    _input_geo = cmds.listConnections("{}.input[0].inputGeometry".format(deformer),  source=True, destination=False, shapes=True) or []
    original_geo = (_original_geo + _input_geo)[0]

    # check if a groupID node already connected to the deformer.
    # if so, use that instead of creating a new one
    group_id_list = cmds.listConnections(deformer, type="groupId")
    if cmds.listConnections(deformer, type="groupId"):
        group_id_node = group_id_list[0]
    else:
        group_id_node = cmds.createNode("groupId")
        cmds.connectAttr(
            "{}.groupId".format(group_id_node), "{}.input[0].groupId".format(deformer)
        )

    # check if there is a groupParts node already connected to the deformer.
    # if so, use that instead of creating a new one
    group_parts_list = cmds.listConnections(deformer, type="groupParts")
    if group_parts_list:
        group_parts_node = group_parts_list[0]
    else:
        group_parts_node = cmds.createNode("groupParts")
        cmds.connectAttr(
            "{}.outputGeometry".format(group_parts_node),
            "{}.input[0].inputGeometry".format(deformer),
            force=True,
        )
        cmds.connectAttr(
            "{}.worldMesh[0]".format(original_geo),
            "{}.inputGeometry".format(group_parts_node),
        )

    # make sure out group_id connected to our groupParts node
    cmds.connectAttr(
        "{}.groupId".format(group_id_node),
        "{}.groupId".format(group_parts_node),
        force=True,
    )

    # convert the vetex ids to the custom format
    ranged_string_list = convert_to_ranged_format(vertex_ids, prefix="vtx")
    cmds.setAttr("{}.inputComponents".format(group_parts_node), len(ranged_string_list), *ranged_string_list, type="componentList")
