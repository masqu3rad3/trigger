"""Collection of deformer related functions"""

from maya import cmds

def connect_bs_targets(
        driver_attr,
        targets_dictionary,
        driver_range=None,
        force_new=False,
        front_of_chain=True,
):
    """Creates or adds Blendshape target and connects them into the same controller attribute

    Args:
        driver_attr (String): driver attribute which controls. tooth_ctrl.gumRetract
        targets_dictionary (Dict): Dictionary for the targets.
                    Format: {<base>: <target_blendShape>}
                    Example: {
                        "face_mesh": "faceGumRetract",
                        "meniscus": "meniscusGumRetract",
                    }
        driver_range (List): If defined, remaps the driver attribute. Example: [0, 100]
        force_new (Bool): If True, a new blendshape will be created for each mesh even though there are existing ones.
        front_of_chain: Created blendshapes will be added front of the chain. Default True
    """

    if driver_range:
        custom_range = True
    else:
        custom_range = False
        driver_range = [0, 1]

    # check the driver, create a float attr if not present
    ch_node, ch_attr = driver_attr.split(".")
    assert cmds.objExists(ch_node), (
            "The Driver object (%s) does not exist in the scene" % ch_node
    )
    attr_state = cmds.attributeQuery(ch_attr, node=ch_node, exists=True)
    if not attr_state:
        cmds.addAttr(
            ch_node,
            ln=ch_attr,
            at="float",
            min=driver_range[0],
            max=driver_range[1],
            k=True,
        )
    else:
        # check if the given values are in range
        min_val = cmds.addAttr("%s.%s" % (ch_node, ch_attr), q=True, min=True)
        max_val = cmds.addAttr("%s.%s" % (ch_node, ch_attr), q=True, max=True)
        if min_val > driver_range[0]:
            cmds.addAttr("%s.%s" % (ch_node, ch_attr), e=True, min=driver_range[0])
        if max_val < driver_range[1]:
            cmds.addAttr("%s.%s" % (ch_node, ch_attr), e=True, max=driver_range[1])

    if custom_range:
        remap_node = cmds.createNode("remapValue")
        cmds.setAttr("{0}.inputMin".format(remap_node), driver_range[0])
        cmds.setAttr("{0}.inputMax".format(remap_node), driver_range[1])
        cmds.setAttr("{0}.outputMin".format(remap_node), 0)
        cmds.setAttr("{0}.outputMax".format(remap_node), 1)
        cmds.connectAttr(driver_attr, "{0}.inputValue".format(remap_node))
        driver_attr = "{0}.outValue".format(remap_node)

    bs_attrs = []
    for base, target_shape in targets_dictionary.items():
        # get the blendshape
        history = cmds.listHistory(base, pdo=True)
        bs_nodes = cmds.ls(history, type="blendShape")
        if force_new or not bs_nodes:
            bs_node = cmds.blendShape(
                target_shape, base, w=[0, 1], foc=front_of_chain, sd=True
            )[0]
        else:
            bs_node = bs_nodes[0]
            next_index = cmds.blendShape(bs_node, q=True, wc=True)
            cmds.blendShape(
                bs_node,
                edit=True,
                t=(base, next_index, target_shape, 1.0),
                w=[next_index, 1.0],
            )
        bs_attrs.append("{0}.{1}".format(bs_node, target_shape))

    for bs_attr in bs_attrs:
        cmds.connectAttr(driver_attr, bs_attr)


def localize(mesh, blendshape_node, local_target_name="LocalRig"):
    """Creates a local rig by duplicating and using the duplicate as the blendshape target to the original mesh.

    Arguments:
        mesh {String} -- Original mesh
        blendshape_node {String} -- Name of the existing blendshape node on the original mesh. If this is an unexisting node, a new blendshape will be created with this name

    Keyword Arguments:
        local_target_name {String} -- Name of the localized target. If non given, default duplicate name will be used. (default: {LocalRig})

    Returns:
        [String] -- Name of the local target
    """

    # create a holding group
    local_rig_grp = "%s_grp" % local_target_name
    if not cmds.objExists(local_rig_grp):
        cmds.group(name="%s_grp" %local_target_name, em=True)

    # duplicate once
    local_mesh = cmds.duplicate(mesh, name=local_target_name)[0]


    if cmds.objExists(blendshape_node):
        shape = cmds.listRelatives(mesh, c=True, s=True)[0]
        # check the shape if it contains the blendshape
        if blendshape_node not in cmds.listConnections(shape):
            cmds.error(
                "Specified blendshape_node ({0}) exists in the scene but not connected to the specified mesh ({1})".format(
                    blendshape_node, mesh))
        # query the existing targets
        # ex_targets = cmds.blendShape(blendshape_node, q=True, t=True)
        next_index = cmds.blendShape(blendshape_node, q=True, wc=True)
        # this returns the total number of used indices. Theoratically, if index inputs follows order
        # it should return an empty index number. However:
        # if somewhere before another shape is inserted into a random weight input,
        # this assumption wont work
        cmds.blendShape(blendshape_node, edit=True, t=(mesh, next_index, local_mesh, 1.0), w=[next_index, 1.0])

    else:
        # create a blendshape
        cmds.blendShape(local_mesh, mesh, w=[0, 1], name=blendshape_node)

    cmds.parent(local_mesh, local_rig_grp)

    return local_mesh


