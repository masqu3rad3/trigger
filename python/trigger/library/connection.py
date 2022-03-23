"""Any connection / constrain / attachment / procedural movemen related methods goes here"""

import maya.api.OpenMaya as om

from trigger.core import validate

from trigger.library import api
from trigger.library import interface
from trigger.library import attribute
from trigger.library import arithmetic as op
from maya import cmds

validate.plugin("matrixNodes")


def connections(node, exclude_nodes=None, exclude_types=None, return_mode="all"):
    """
        Returns the connections for the given node in a nice dictionary format:

    result_dict = {
        "incoming": [
            {
                "plug_out": "someNode.outputX",
                "plug_in": "node.inputX"
            }
        ]
        "outgoing": [
            {
                "plug_out": "node.outputX",
                "plug_in": "someOtherNode.inputZ
            }
        ]
        }

    Args:
        node: (String) Node to get connections
        exclude_nodes: (List of Strings) nodes in this list will be excluded
        exclude_types: (List of Strings) nodes types in this list will be excluded
        return_mode: (str) modifies return value:
                            "all" : returns a dictionary with incoming and outgoing keys
                            "incoming": returns a list of dictionaries for incoming connections
                            "outgoing": returns a list of dictionaries for outgoing connections
                            default "all"

    Returns: (Dictionary) or (List) depending on the return_mode argument

    """

    raw_inputs = cmds.listConnections(node, plugs=True, source=True, destination=False, connections=True)
    raw_outputs = cmds.listConnections(node, plugs=True, source=False, destination=True, connections=True)

    input_plugs = raw_inputs[::2] if raw_inputs else []
    output_plugs = raw_outputs[::2] if raw_outputs else []

    result_dict = {"incoming": [], "outgoing": []}

    # filter input plug lists
    if exclude_nodes:
        input_plugs = [plug for plug in input_plugs if plug.split(".")[0] not in exclude_nodes]
    if exclude_types:
        input_plugs = [plug for plug in input_plugs if cmds.objectType(plug.split(".")[0]) not in exclude_types]

    for in_plug in input_plugs:
        conn = {"plug_out": cmds.listConnections(in_plug, plugs=True, source=True, destination=False,
                                                 connections=True)[0],
                "plug_in": cmds.listConnections(in_plug, plugs=True, source=True, destination=False,
                                                connections=True)[1]}
        result_dict["incoming"].append(conn)

    for out_plug in output_plugs:
        out_connections = cmds.listConnections(out_plug, plugs=True, source=False, destination=True, connections=False)
        for out_c in out_connections:
            if exclude_nodes:
                if out_c.split(".")[0] in exclude_nodes:
                    continue
            if exclude_types:
                if cmds.objectType(out_c.split(".")[0]) in exclude_types:
                    continue
            conn = {
                "plug_out": out_plug,
                "plug_in": out_c
            }
            result_dict["outgoing"].append(conn)

    if return_mode == "all":
        return result_dict
    elif return_mode == "incoming":
        return result_dict["incoming"]
    elif return_mode == "outgoing":
        return result_dict["outgoing"]
    else:
        raise Exception("Not valid return_mode argument. Valid values are 'all', 'incoming', 'outgoing'")


def replace_connections(source_node, target_node, exclude_nodes=None, exclude_types=None, incoming=True, outgoing=True):
    all_connections = connections(source_node, exclude_nodes=exclude_nodes, exclude_types=exclude_types)
    in_connections = all_connections["incoming"] if incoming else []
    out_connections = all_connections["outgoing"] if outgoing else []

    for con_dict in in_connections:
        out_p = con_dict["plug_out"]
        in_p = con_dict["plug_in"].replace(source_node, target_node)
        # prevent nasty warnings...
        existing_connections = cmds.listConnections(out_p, p=True, source=False, destination=True) or []
        if in_p not in existing_connections:
            cmds.connectAttr(out_p, in_p, force=True)

    for con_dict in out_connections:
        out_p = con_dict["plug_out"].replace(source_node, target_node)
        in_p = con_dict["plug_in"]
        # stupid warnings...
        existing_connections = cmds.listConnections(in_p, p=True, source=True, destination=False) or []
        if out_p not in existing_connections:
            cmds.connectAttr(out_p, in_p, force=True)


def matrixConstraint(drivers, driven, mo=True, prefix="", sr=None, st=None, ss=None, source_parent_cutoff=None):
    """
    Creates a Matrix Constraint
    Args:
        drivers: (String) Parent Node
        driven: (String) Child Node
        mo: (Bool) Maintain offset. If True, the existing distance between nodes will be preserved
        prefix: (String) Prefix for the nodes names which will be created
        sr: (List) Skip Rotations. Listed rotation values will be skipped. "xyz" or ["x", "y", "z"]
        st: (List) Skip Translation. Listed translation values will be skipped. "xyz" or ["x", "y", "z"]
        ss: (List) Skip Scale. Listed scale values will be skipped. "xyz" or ["x", "y", "z"]
        source_parent_cutoff: (String) The transformation matrices above this node won't affect to the child.

    Returns: (Tuple) mult_matrix, decompose_matrix

    """

    is_multi = True if type(drivers) == list else False
    is_joint = True if cmds.objectType(driven) == "joint" else False
    parents = cmds.listRelatives(driven, parent=True)
    parent_of_driven = parents[0] if parents else None
    next_index = -1

    mult_matrix = cmds.createNode("multMatrix", name="%s_multMatrix" % prefix)
    decompose_matrix = cmds.createNode("decomposeMatrix", name="%s_decomposeMatrix" % prefix)

    # if there are multiple targets, average them first separately

    ##########################
    if is_multi:
        driver_matrix_plugs = ["%s.worldMatrix[0]" % x for x in drivers]
        average_node = op.average_matrix(driver_matrix_plugs, return_plug=False)
        out_plug = "%s.matrixSum" % average_node
    else:
        out_plug = "%s.worldMatrix[0]" % drivers
        average_node = None

    if mo:
        driven_world_matrix = api.getMDagPath(driven).inclusiveMatrix()
        if is_multi:
            driver_world_matrix = om.MMatrix(cmds.getAttr(out_plug))

        else:
            driver_world_matrix = api.getMDagPath(drivers).inclusiveMatrix()

        local_offset = driven_world_matrix * driver_world_matrix.inverse()
        next_index += 1
        cmds.setAttr("%s.matrixIn[%i]" % (mult_matrix, next_index), local_offset, type="matrix")

    next_index += 1
    cmds.connectAttr(out_plug, "%s.matrixIn[%i]" % (mult_matrix, next_index))

    cmds.connectAttr("%s.matrixSum" % mult_matrix, "%s.inputMatrix" % decompose_matrix)

    if source_parent_cutoff:
        next_index += 1
        cmds.connectAttr("%s.worldInverseMatrix" % source_parent_cutoff, "%s.matrixIn[%i]" % (mult_matrix, next_index))

    if parent_of_driven:
        next_index += 1
        cmds.connectAttr("%s.worldInverseMatrix[0]" % parent_of_driven, "%s.matrixIn[%i]" % (mult_matrix, next_index))

    if not st:
        cmds.connectAttr("%s.outputTranslate" % decompose_matrix, "%s.translate" % driven)
    else:
        for attr in "XYZ":
            if attr.lower() not in st and attr.upper() not in st:
                cmds.connectAttr("%s.outputTranslate%s" % (decompose_matrix, attr), "%s.translate%s" % (driven, attr))
    if not sr:
        # Joint rotations needs to be handled differently because of the jointOrientation
        if is_joint:
            # store the orientation values
            rot_index = 0
            second_index = 0
            joint_orientation = cmds.getAttr("%s.jointOrient" % driven)[0]

            # create the compensation node strand
            rotation_compose = cmds.createNode("composeMatrix", name="%s_rotateComposeMatrix" % prefix)
            rotation_first_mult_matrix = cmds.createNode("multMatrix", name="%s_firstRotateMultMatrix" % prefix)
            rotation_inverse_matrix = cmds.createNode("inverseMatrix", name="%s_rotateInverseMatrix" % prefix)
            rotation_sec_mult_matrix = cmds.createNode("multMatrix", name="%s_secRotateMultMatrix" % prefix)
            rotation_decompose_matrix = cmds.createNode("decomposeMatrix", name="%s_rotateDecomposeMatrix" % prefix)

            # set values and make connections for rotation strand
            cmds.setAttr("%s.inputRotate" % rotation_compose, *joint_orientation)
            cmds.connectAttr("%s.outputMatrix" % rotation_compose,
                             "%s.matrixIn[%i]" % (rotation_first_mult_matrix, rot_index))

            if parent_of_driven:
                rot_index += 1
                cmds.connectAttr("%s.worldMatrix[0]" % parent_of_driven,
                                 "%s.matrixIn[%i]" % (rotation_first_mult_matrix, rot_index))
            cmds.connectAttr("%s.matrixSum" % rotation_first_mult_matrix, "%s.inputMatrix" % rotation_inverse_matrix)

            cmds.connectAttr(out_plug, "%s.matrixIn[%i]" % (rotation_sec_mult_matrix, second_index))

            if source_parent_cutoff:
                second_index += 1
                cmds.connectAttr("%s.worldInverseMatrix" % source_parent_cutoff,
                                 "%s.matrixIn[%i]" % (rotation_sec_mult_matrix, second_index))

            second_index += 1
            cmds.connectAttr("%s.outputMatrix" % rotation_inverse_matrix,
                             "%s.matrixIn[%i]" % (rotation_sec_mult_matrix, second_index))
            cmds.connectAttr("%s.matrixSum" % rotation_sec_mult_matrix, "%s.inputMatrix" % rotation_decompose_matrix)

            cmds.connectAttr("%s.outputRotate" % rotation_decompose_matrix, "%s.rotate" % driven)
        else:
            cmds.connectAttr("%s.outputRotate" % decompose_matrix, "%s.rotate" % driven)
    else:

        # Joint rotations needs to be handled differently because of the jointOrientation
        if is_joint:
            # if all rotation axis defined, dont create the strand
            if len(sr) != 3:
                # store the orientation values
                rot_index = 0
                second_index = 0
                joint_orientation = cmds.getAttr("%s.jointOrient" % driven)[0]

                # create the compensation node strand
                rotation_compose = cmds.createNode("composeMatrix", name="%s_rotateComposeMatrix" % prefix)
                rotation_first_mult_matrix = cmds.createNode("multMatrix", name="%s_firstRotateMultMatrix" % prefix)
                rotation_inverse_matrix = cmds.createNode("inverseMatrix", name="%s_rotateInverseMatrix" % prefix)
                rotation_sec_mult_matrix = cmds.createNode("multMatrix", name="%s_secRotateMultMatrix" % prefix)
                rotation_decompose_matrix = cmds.createNode("decomposeMatrix", name="%s_rotateDecomposeMatrix" % prefix)

                # set values and make connections for rotation strand
                cmds.setAttr("%s.inputRotate" % rotation_compose, *joint_orientation)
                cmds.connectAttr("%s.outputMatrix" % rotation_compose,
                                 "%s.matrixIn[%i]" % (rotation_first_mult_matrix, rot_index))

                if parent_of_driven:
                    rot_index += 1
                    cmds.connectAttr("%s.worldMatrix[0]" % parent_of_driven,
                                     "%s.matrixIn[%i]" % (rotation_first_mult_matrix, rot_index))
                cmds.connectAttr("%s.matrixSum" % rotation_first_mult_matrix,
                                 "%s.inputMatrix" % rotation_inverse_matrix)

                cmds.connectAttr(out_plug, "%s.matrixIn[%i]" % (rotation_sec_mult_matrix, second_index))

                if source_parent_cutoff:
                    second_index += 1
                    cmds.connectAttr("%s.worldInverseMatrix" % source_parent_cutoff,
                                     "%s.matrixIn[%i]" % (rotation_sec_mult_matrix, second_index))

                second_index += 1
                cmds.connectAttr("%s.outputMatrix" % rotation_inverse_matrix,
                                 "%s.matrixIn[%i]" % (rotation_sec_mult_matrix, second_index))
                cmds.connectAttr("%s.matrixSum" % rotation_sec_mult_matrix,
                                 "%s.inputMatrix" % rotation_decompose_matrix)

                for attr in "XYZ":
                    if attr.lower() not in sr and attr.upper() not in sr:
                        cmds.connectAttr("%s.outputRotate%s" % (rotation_decompose_matrix, attr),
                                         "%s.rotate%s" % (driven, attr))
            else:
                pass
        else:
            for attr in "XYZ":
                if attr.lower() not in sr and attr.upper() not in sr:
                    cmds.connectAttr("%s.outputRotate%s" % (decompose_matrix, attr), "%s.rotate%s" % (driven, attr))
    if not ss:
        cmds.connectAttr("%s.outputScale" % decompose_matrix, "%s.scale" % driven)
    else:
        for attr in "XYZ":
            if attr.lower() not in ss and attr.upper() not in ss:
                cmds.connectAttr("%s.outputScale%s" % (decompose_matrix, attr), "%s.scale%s" % (driven, attr))

    return mult_matrix, decompose_matrix, average_node


def matrixSwitch(parentA, parentB, child, control_attribute, position=True, rotation=True, scale=False,
                 source_parent_cutoff=None):
    """
    Creates a matrix blended switch between two locations

    Args:
        parentA: (string) first parent node
        parentB: (string) second parent node
        child: (string) child to be constrained
        control_attribute: (string) switch control attribute. e.g. masterCont.switch. If missing, will created
        position: (boolean) If True, makes the positional switch. Default True
        rotation: (boolean) If True, makes the rotational switch. Default True
        scale: (boolean) If True, makes the scale switch. Default False
        source_parent_cutoff: Any transforms on this node and above wont affect the constraint

    Returns:

    """
    attribute.validate_attr(control_attribute, attr_range=[0, 1])
    mult_matrix_a, dump, _ = matrixConstraint(parentA, child, mo=False, prefix=parentA, sr="xyz", st="xyz", ss="xyz",
                                              source_parent_cutoff=None)
    attribute.disconnect_attr(dump, attr="inputMatrix")
    cmds.delete(dump)
    mult_matrix_b, dump, _ = matrixConstraint(parentB, child, mo=False, prefix=parentB, sr="xyz", st="xyz", ss="xyz",
                                              source_parent_cutoff=None)
    attribute.disconnect_attr(dump, attr="inputMatrix")
    cmds.delete(dump)

    wt_add_matrix = cmds.createNode("wtAddMatrix", name="wtAdd_%s_%s" % (parentA, parentB))
    cmds.connectAttr("%s.matrixSum" % mult_matrix_a, "%s.wtMatrix[0].matrixIn" % wt_add_matrix)
    cmds.connectAttr("%s.matrixSum" % mult_matrix_b, "%s.wtMatrix[1].matrixIn" % wt_add_matrix)

    attribute.drive_attrs(control_attribute, "%s.wtMatrix[0].weightIn" % wt_add_matrix, driver_range=[0, 1],
                          driven_range=[0, 1], force=False)
    attribute.drive_attrs(control_attribute, "%s.wtMatrix[1].weightIn" % wt_add_matrix, driver_range=[0, 1],
                          driven_range=[1, 0], force=False)

    if source_parent_cutoff:
        mult_matrix_cutoff = cmds.createNode("multMatrix", name="multMatrixCutoff_%s_%s" % (parentA, parentB))
        cmds.connectAttr("%s.matrixSum" % wt_add_matrix, "%s.matrixIn[0]" % mult_matrix_cutoff)
        cmds.connectAttr("%s.worldInverseMatrix" % source_parent_cutoff, "%s.matrixIn[1]" % mult_matrix_cutoff)
        out_plug = "%s.matrixSum" % mult_matrix_cutoff
    else:
        out_plug = "%s.matrixSum" % wt_add_matrix

    decompose_node = cmds.createNode("decomposeMatrix", name="decompose_switch")
    cmds.connectAttr(out_plug, "%s.inputMatrix" % decompose_node)

    if position:
        cmds.connectAttr("%s.outputTranslate" % decompose_node, "%s.translate" % child)
    if rotation:
        cmds.connectAttr("%s.outputRotate" % decompose_node, "%s.rotate" % child)
    if scale:
        cmds.connectAttr("%s.outputScale" % decompose_node, "%s.scale" % child)


def getClosestUV(source_node, dest_node):
    """Returns the UV coordinates of dest_node closest to the source_node

    Args:
        source_node (str): source node to collect position
        dest_node (str): destination node which will collect the uv coordinates from

    Returns:
        tuple: (float, float) The U and V values.
    """

    x_pos, y_pos, z_pos = api.getWorldTranslation(dest_node)
    closest_point_node = cmds.createNode('closestPointOnMesh')
    cmds.connectAttr("%s.outMesh" % source_node, "%s.inMesh" % closest_point_node, f=1)
    cmds.setAttr("%s.inPositionX" % closest_point_node, x_pos)
    cmds.setAttr("%s.inPositionY" % closest_point_node, y_pos)
    cmds.setAttr("%s.inPositionZ" % closest_point_node, z_pos)
    u_val = cmds.getAttr("%s.parameterU" % closest_point_node)
    v_val = cmds.getAttr("%s.parameterV" % closest_point_node)
    cmds.delete(closest_point_node)

    return u_val, v_val


def get_uv_at_point(position, dest_node):
    """Get a tuple of u, v values for a point on a given mesh.

    Args:
        position (vector3): The world space position to get the uvs of.
        dest_node (str): The mesh with uvs.

    Returns:
        tuple: (float, float) The U and V values.
    """
    selection_list = om.MSelectionList()
    selection_list.add(dest_node)
    dag_path = selection_list.getDagPath(0)

    mfn_mesh = om.MFnMesh(dag_path)

    point = om.MPoint(position)
    space = om.MSpace.kWorld

    u_val, v_val, _ = mfn_mesh.getUVAtPoint(point, space)

    return u_val, v_val


def getVertexUV(mesh, vertex_id):
    uv_map = cmds.polyListComponentConversion('{0}.vtx[{1}]'.format(mesh, vertex_id), toUV=True)
    return cmds.polyEditUV(uv_map, q=True)


def create_follicle(name, surface, uv):
    follicle = (cmds.createNode('follicle', n='%s_follicleShape' % name))
    follicle_transform = (cmds.listRelatives(follicle, parent=True))[0]

    nType = cmds.nodeType(surface)
    if nType == 'nurbsSurface':
        # NURBS
        out = 'local'
        inp = 'inputSurface'
    else:
        # POLY
        out = 'outMesh'
        inp = 'inputMesh'

    cmds.connectAttr("%s.worldMatrix[0]" % surface, "%s.inputWorldMatrix" % follicle)
    cmds.connectAttr("%s.%s" % (surface, out), "%s.%s" % (follicle, inp))
    cmds.connectAttr("%s.outTranslate" % follicle, '%s.translate' % follicle_transform)
    cmds.connectAttr('%s.outRotate' % follicle, '%s.rotate' % follicle_transform)
    cmds.setAttr('%s.parameterU' % follicle, uv[0])
    cmds.setAttr('%s.parameterV' % follicle, uv[1])
    return follicle_transform, follicle


def uvPin(mesh_transform, coordinates):
    assert cmds.about(api=True) >= 20200000, "uv_pin requires Maya 2020 and later"
    all_shapes = cmds.listRelatives(mesh_transform, shapes=True, children=True, parent=False)
    # seperate intermediates
    intermediates = [x for x in all_shapes if cmds.getAttr("%s.intermediateObject" % x) == 1]
    non_intermediates = [x for x in all_shapes if x not in intermediates]
    deformed_mesh = non_intermediates[0]
    if not intermediates:
        # create original / deformed mesh hiearchy
        dup = cmds.duplicate(mesh_transform, name="%s_ORIG" % mesh_transform)[0]
        original_mesh = cmds.listRelatives(dup, children=True)[0]
        cmds.parent(original_mesh, mesh_transform, shape=True, r=True)
        cmds.delete(dup)
        incoming_connections = connections(deformed_mesh)["incoming"]
        for connection in incoming_connections:
            attribute.disconnect_attr(connection["plug_out"])
            cmds.connectAttr(connection["plug_in"], connection["plug_out"].replace(deformed_mesh, original_mesh))
        # hide/intermediate original mesh
        cmds.setAttr("%s.hiddenInOutliner" % original_mesh, 1)
        cmds.setAttr("%s.intermediateObject" % original_mesh, 1)
        interface.refreshOutliners()
    else:
        original_mesh = intermediates[0]

    uv_pin = cmds.createNode("uvPin")

    cmds.connectAttr("%s.worldMesh" % deformed_mesh, "%s.deformedGeometry" % uv_pin)
    cmds.connectAttr("%s.outMesh" % original_mesh, "%s.originalGeometry" % uv_pin)

    cmds.setAttr("%s.coordinate[0]" % uv_pin, *coordinates)

    return uv_pin


def pin_to_surface(node, surface, sr="", st="", ss="xyz"):
    world_pos = api.getWorldTranslation(node)
    uv_coordinates = get_uv_at_point(world_pos, surface)
    uv_pin = uvPin(surface, uv_coordinates)
    decompose_matrix_node = cmds.createNode("decomposeMatrix", name="decompose_pinMatrix")
    cmds.connectAttr("%s.outputMatrix[0]" % uv_pin, "%s.inputMatrix" % decompose_matrix_node)

    for attr in "XYZ":
        if attr.lower() not in sr and attr.upper() not in sr:
            cmds.connectAttr("%s.outputRotate%s" % (decompose_matrix_node, attr), "%s.rotate%s" % (node, attr))

    for attr in "XYZ":
        if attr.lower() not in st and attr.upper() not in st:
            cmds.connectAttr("%s.outputTranslate%s" % (decompose_matrix_node, attr), "%s.translate%s" % (node, attr))

    for attr in "XYZ":
        if attr.lower() not in ss and attr.upper() not in ss:
            cmds.connectAttr("%s.outputScale%s" % (decompose_matrix_node, attr), "%s.scale%s" % (node, attr))

    return uv_pin


def averageConstraint(target_mesh, vertex_list, source_object=None, offsetParent=False, force_follicle=False):
    """
    Creates a average weighted constraint between defined vertices. Works version 2020+
    Args:
        target_mesh: (String) Mesh object which holds the defined vertices
        vertex_list: (List) List of Integer vertex IDs
        source_object: (String) If not defined a locator will be created instead
        offsetParent: (Boolean) If True, the matrix output will be connected to offset parent matrix of
                    of the source object, leaving the transform values available
        force_follicle: (Boolean) If True, follicles will be used instead of pin constraints.
                                ATTENTION: Follicles wont follow face normals if the normals are locked

    Returns:(String) source object. It will be the created locator if none provided

    """
    if not force_follicle:
        assert cmds.about(api=True) >= 20200000, "uv_pin requires Maya 2020 and later"
    average_node = cmds.createNode("wtAddMatrix")
    weight_value = 1.0 / float(len(vertex_list))
    for i, vertex_nmb in enumerate(vertex_list):
        uv = getVertexUV(target_mesh, vertex_nmb)
        if force_follicle:
            pin_node, _ = create_follicle("pin%i" %i, target_mesh, uv)
            cmds.connectAttr("%s.worldMatrix[0]" % pin_node, "{0}.wtMatrix[{1}].matrixIn".format(average_node, i))
        else:
            pin_node = uvPin(target_mesh, uv)
            cmds.connectAttr("%s.outputMatrix[0]" % pin_node, "{0}.wtMatrix[{1}].matrixIn".format(average_node, i))
        cmds.setAttr("{0}.wtMatrix[{1}].weightIn".format(average_node, i), weight_value)

    if not source_object:
        source_object = cmds.spaceLocator(name="averaged_loc")[0]

    if not offsetParent:
        mult_matrix = cmds.createNode("multMatrix")
        decompose_matrix = cmds.createNode("decomposeMatrix")
        cmds.connectAttr("%s.matrixSum" % average_node, "%s.matrixIn[0]" % mult_matrix)
        cmds.connectAttr("%s.matrixSum" % mult_matrix, "%s.inputMatrix" % decompose_matrix)
        cmds.connectAttr("%s.outputTranslate" % decompose_matrix, "%s.translate" % source_object)
        cmds.connectAttr("%s.outputRotate" % decompose_matrix, "%s.rotate" % source_object)

    else:
        pick_matrix = cmds.createNode("pickMatrix")
        cmds.connectAttr("%s.matrixSum" % average_node, "%s.inputMatrix" % pick_matrix)
        cmds.setAttr("%s.useRotate" % pick_matrix, 1)
        cmds.setAttr("%s.useScale" % pick_matrix, 0)
        cmds.setAttr("%s.useShear" % pick_matrix, 0)
        cmds.connectAttr("%s.outputMatrix" % pick_matrix, "%s.offsetParentMatrix" % source_object)
        cmds.connectAttr("%s.outputMatrix" % pick_matrix, "%s.offsetParentMatrix" % source_object)
    return source_object


def connectMirror(node1, node2, mirror_axis="X"):
    """
    Make a mirrored connection between node1 and node2 along the mirrorAxis
    Args:
        node1: Driver Node
        node2: Driven Node
        mirror_axis: Mirror axis for the driven node.

    Returns: None

    """
    # make sure the axis is uppercase:
    mirror_axis = mirror_axis.upper()
    # strip - and +
    mirror_axis = mirror_axis.replace("+", "")
    mirror_axis = mirror_axis.replace("-", "")

    # nodes Translate
    rvs_node_t = cmds.createNode("reverse")
    minus_op_t = cmds.createNode("plusMinusAverage")
    cmds.setAttr("%s.operation" % minus_op_t, 2)
    cmds.connectAttr("{0}.translate".format(node1), "{0}.input".format(rvs_node_t))
    cmds.connectAttr("{0}.output".format(rvs_node_t), "{0}.input3D[0]".format(minus_op_t))
    cmds.setAttr("%s.input3D[1]" % minus_op_t, 1, 1, 1)
    # nodes Rotate
    rvs_node_r = cmds.createNode("reverse")
    minus_op_r = cmds.createNode("plusMinusAverage")
    cmds.setAttr("%s.operation" % minus_op_r, 2)
    cmds.connectAttr("{0}.rotate".format(node1), "{0}.input".format(rvs_node_r))

    cmds.connectAttr("{0}.output".format(rvs_node_r), "{0}.input3D[0]".format(minus_op_r))

    cmds.setAttr("%s.input3D[1]" % minus_op_r, 1, 1, 1)

    # Translate

    if mirror_axis == "X":
        cmds.connectAttr("{0}.output3Dx".format(minus_op_t), "{0}.tx".format(node2))
        cmds.connectAttr("{0}.ty".format(node1), "{0}.ty".format(node2))
        cmds.connectAttr("{0}.tz".format(node1), "{0}.tz".format(node2))
        cmds.connectAttr("{0}.rx".format(node1), "{0}.rx".format(node2))
        cmds.connectAttr("{0}.output3Dy".format(minus_op_r), "{0}.ry".format(node2))
        cmds.connectAttr("{0}.output3Dz".format(minus_op_r), "{0}.rz".format(node2))

    if mirror_axis == "Y":
        cmds.connectAttr("{0}.tx".format(node1), "{0}.tx".format(node2))
        cmds.connectAttr("{0}.output3Dy".format(minus_op_t), "{0}.ty".format(node2))
        cmds.connectAttr("{0}.tz".format(node1), "{0}.tz".format(node2))
        cmds.connectAttr("{0}.output3Dx".format(minus_op_r), "{0}.rx".format(node2))
        cmds.connectAttr("{0}.ry".format(node1), "{0}.ry".format(node2))
        cmds.connectAttr("{0}.output3Dz".format(minus_op_r), "{0}.rz".format(node2))

    if mirror_axis == "Z":
        cmds.connectAttr("{0}.tx".format(node1), "{0}.tx".format(node2))
        cmds.connectAttr("{0}.ty".format(node1), "{0}.ty".format(node2))
        cmds.connectAttr("{0}.output3Dz".format(minus_op_t), "{0}.tz".format(node2))
        cmds.connectAttr("{0}.rx".format(node1), "{0}.rx".format(node2))
        cmds.connectAttr("{0}.output3Dy".format(minus_op_r), "{0}.ry".format(node2))
        cmds.connectAttr("{0}.output3Dz".format(minus_op_r), "{0}.rz".format(node2))

def matrix_constrain_localised(
        inherit,
        no_inherit,
        destination,
        target_attrs="",
        force=True,
):
    if target_attrs == "":
        target_attrs = [
            "translateX",
            "translateY",
            "translateZ",
            "rotateX",
            "rotateY",
            "rotateZ",
            "scaleX",
            "scaleY",
            "scaleZ",
        ]

    # grab 'bindPose' world matrix from transform we don't want to inherit from #
    dont_inherit_bindPose_matrix = ("%s_bindPose_fourByFourMatrix" % no_inherit)
    if cmds.objExists(dont_inherit_bindPose_matrix) == False:
        grabbed_matrix = cmds.getAttr("%s.worldMatrix[0]" % no_inherit)
        dont_inherit_bindPose_matrix = cmds.createNode("fourByFourMatrix", n=dont_inherit_bindPose_matrix)
        element_list = ["in00", "in01", "in02", "in03", "in10", "in11", "in12", "in13", "in20", "in21", "in22", "in23",
                        "in30", "in31", "in32", "in33"]
        for index, element in enumerate(element_list):
            cmds.setAttr("%s.%s" % (dont_inherit_bindPose_matrix, element), grabbed_matrix[index])
    else:
        print(
            "detected a fourByFourMatrix already exists called " + dont_inherit_bindPose_matrix + ", so using that one.")

    # multiply all of the matrices together #
    mult_matrix = cmds.createNode("multMatrix", n="%s_multMatrix" % inherit)
    cmds.connectAttr("%s.worldMatrix[0]" % inherit, "%s.matrixIn[0]" % mult_matrix)
    cmds.connectAttr("%s.worldInverseMatrix[0]" % no_inherit, "%s.matrixIn[1]" % mult_matrix)
    cmds.connectAttr("%s.output" % dont_inherit_bindPose_matrix, "%s.matrixIn[2]" % mult_matrix)

    # decompose result #
    decomp_matrix = cmds.createNode("decomposeMatrix", n="%s_decomposeMatrix" % destination)
    cmds.connectAttr("%s.matrixSum" % mult_matrix, "%s.inputMatrix" % decomp_matrix)

    # connect up #
    for  attr in target_attrs:
        output_attr = "output%s%s" % (attr[0].capitalize(), attr[1:]) # capitalize only first letter

        lock_state = cmds.getAttr("%s.%s" % (destination, attr), lock=True)
        # unlock, connect, then reinstate lock state #
        cmds.setAttr("%s.%s" % (destination, attr), lock=False)  # unlock #
        cmds.connectAttr("%s.%s" % (decomp_matrix, output_attr), "%s.%s" % (destination, attr), force=force)

        # set back to original lock state #
        cmds.setAttr("%s.%s" % (destination, attr), lock=lock_state)

    return decomp_matrix, mult_matrix, dont_inherit_bindPose_matrix
