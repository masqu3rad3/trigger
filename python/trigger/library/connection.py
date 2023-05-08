# pylint: disable=consider-using-f-string

"""connections / constrains / attachments / procedural movements"""
import logging
from maya.api import OpenMaya

from trigger.core import validate

from trigger.library import api
from trigger.library import interface
from trigger.library import attribute
from trigger.library import arithmetic as op
from maya import cmds

validate.plugin("matrixNodes")

LOG = logging.getLogger(__name__)

def connections(node,
                exclude_nodes=None,
                exclude_types=None,
                return_mode="all"
                ):
    """
    Return the connections for the given node as a dictionary
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
        node (str): Node to get connections
        exclude_nodes (List): nodes in this list will be excluded
        exclude_types (List): nodes types in this list will be excluded
        return_mode (str): modifies return value:
            "all" : returns a dictionary with incoming and outgoing keys
            "incoming": returns a list of dictionaries for incoming connections
            "outgoing": returns a list of dictionaries for outgoing connections
            defaults to "all"
    Returns: (Dictionary) or (List)
    """

    raw_inputs = cmds.listConnections(node,
                                      plugs=True,
                                      source=True,
                                      destination=False,
                                      connections=True)
    raw_outputs = cmds.listConnections(node,
                                       plugs=True,
                                       source=False,
                                       destination=True,
                                       connections=True)
    input_plugs = raw_inputs[::2] if raw_inputs else []
    output_plugs = raw_outputs[::2] if raw_outputs else []
    result_dict = {"incoming": [], "outgoing": []}

    # filter input plug lists
    if exclude_nodes:
        input_plugs = [
            plug for plug in input_plugs
            if plug.split(".")[0] not in exclude_nodes]
    if exclude_types:
        input_plugs = [
            plug for plug in input_plugs if cmds.objectType(
                plug.split(".")[0]) not in exclude_types]

    for in_plug in input_plugs:
        conn = {
            "plug_out": cmds.listConnections(in_plug,
                                             plugs=True,
                                             source=True,
                                             destination=False,
                                             connections=True)[0],
            "plug_in": cmds.listConnections(in_plug,
                                            plugs=True,
                                            source=True,
                                            destination=False,
                                            connections=True)[1]
        }
        result_dict["incoming"].append(conn)

    for out_plug in output_plugs:
        out_connections = cmds.listConnections(out_plug,
                                               plugs=True,
                                               source=False,
                                               destination=True,
                                               connections=False)
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
        raise Exception("Not valid return_mode argument."
                        "Valid values are 'all', 'incoming', 'outgoing'")


def replace_connections(source_node,
                        target_node,
                        exclude_nodes=None,
                        exclude_types=None,
                        incoming=True,
                        outgoing=True):
    all_connections = connections(source_node,
                                  exclude_nodes=exclude_nodes,
                                  exclude_types=exclude_types)
    in_connections = all_connections["incoming"] if incoming else []
    out_connections = all_connections["outgoing"] if outgoing else []

    for con_dict in in_connections:
        out_p = con_dict["plug_out"]
        in_p = con_dict["plug_in"].replace(source_node, target_node)
        # prevent nasty warnings...
        existing_connections = cmds.listConnections(out_p,
                                                    p=True,
                                                    source=False,
                                                    destination=True
                                                    ) or []
        if in_p not in existing_connections:
            cmds.connectAttr(out_p, in_p, force=True)

    for con_dict in out_connections:
        out_p = con_dict["plug_out"].replace(source_node, target_node)
        in_p = con_dict["plug_in"]
        # stupid warnings...
        existing_connections = cmds.listConnections(in_p,
                                                    p=True,
                                                    source=True,
                                                    destination=False
                                                    ) or []
        if out_p not in existing_connections:
            cmds.connectAttr(out_p, in_p, force=True)


# camelCase is for keeping the constraint in-line with maya constraints

# pylint: disable=invalid-name
# pylint: disable=too-many-arguments
# pylint: disable=too-many-locals
# pylint: disable=too-many-branches
# pylint: disable=too-many-statements
def matrixConstraint(drivers,
                     driven,
                     maintainOffset=True,
                     prefix="",
                     skipRotate=None,
                     skipTranslate=None,
                     skipScale=None,
                     source_parent_cutoff=None,
                     **short_arguments
                     ):
    """
    Create a Matrix Constraint.
    Args:
        drivers (List) or (str): Parent Node(s)
        driven (str): Child Node
        maintainOffset (bool): Maintain offset.
            If True, the existing distance between nodes will be preserved
        prefix (str): Prefix for the nodes names which will be created
        skipRotate (str or list): Skip Rotations. Listed rotation values
                    will be skipped. "xyz" or ["x", "y", "z"]
        skipTranslate (str or list): Skip Translation. Listed translation values
                    will be skipped. "xyz" or ["x", "y", "z"]
        skipScale (str or list): Skip Scale. Listed scale values will be skipped.
                    "xyz" or ["x", "y", "z"]
        source_parent_cutoff (None or str): The transformation matrices above
                    this node won't affect to the child.
    Returns: (Tuple) mult_matrix, decompose_matrix, wtAddMatrix
    """

    # match the long names to the short ones if used
    for key, value in short_arguments:
        if key == "mo":
            maintainOffset = key
        elif key == "sr":
            skipRotate = value
        elif key == "st":
            skipTranslate = value
        elif key == "ss":
            skipScale = value
        elif key == "spc":
            source_parent_cutoff = value

    is_multi = bool(isinstance(drivers, list))
    is_joint = bool(cmds.objectType(driven) == "joint")
    if is_multi and source_parent_cutoff:
        LOG.warning("source_parent_cutoff is not supported for multiple inputs. Ignoring it.")
        source_parent_cutoff = None
    parents = cmds.listRelatives(driven, parent=True)
    parent_of_driven = parents[0] if parents else None
    next_index = -1

    mult_matrix = cmds.createNode("multMatrix", name="{}_multMatrix".format(prefix))
    decompose_matrix = cmds.createNode(
        "decomposeMatrix", name="{}_decomposeMatrix".format(prefix))

    # if there are multiple targets, average them first separately
    if is_multi:
        driver_matrix_plugs = ["{}.worldMatrix[0]".format(x) for x in drivers]
        average_node = op.average_matrix(driver_matrix_plugs,
                                         return_plug=False)
        out_plug = "{}.matrixSum".format(average_node)
    else:
        out_plug = "{}.worldMatrix[0]".format(drivers)
        average_node = None

    if maintainOffset:
        driven_world_matrix = api.get_m_dagpath(driven).inclusiveMatrix()
        if is_multi:
            driver_world_matrix = OpenMaya.MMatrix(cmds.getAttr(out_plug))
        else:
            driver_world_matrix = api.get_m_dagpath(drivers).inclusiveMatrix()
        local_offset = driven_world_matrix * driver_world_matrix.inverse()
        next_index += 1
        cmds.setAttr("{0}.matrixIn[{1}]".format(mult_matrix, next_index),
                     local_offset, type="matrix")

    next_index += 1
    cmds.connectAttr(out_plug, "{0}.matrixIn[{1}]".format(mult_matrix, next_index))

    cmds.connectAttr("{}.matrixSum".format(mult_matrix),
                     "{}.inputMatrix".format(decompose_matrix))

    if source_parent_cutoff:
        next_index += 1
        cmds.connectAttr("{}.worldInverseMatrix".format(source_parent_cutoff),
                         "{0}.matrixIn[{1}]".format(mult_matrix, next_index))

    if parent_of_driven:
        next_index += 1
        cmds.connectAttr("{}.worldInverseMatrix[0]".format(parent_of_driven),
                         "{0}.matrixIn[{1}]".format(mult_matrix, next_index))

    if not skipTranslate:
        cmds.connectAttr("{}.outputTranslate".format(decompose_matrix),
                         "{}.translate".format(driven))
    else:
        for attr in "XYZ":
            if attr.lower() not in skipTranslate and attr.upper() not in skipTranslate:
                cmds.connectAttr(
                    "{0}.outputTranslate{1}".format(
                        decompose_matrix, attr),
                    "{0}.translate{1}".format(driven, attr))

    # it the driven is a joint, the rotations needs to be handled differently
    # is there any rotation attribute to connect?
    if not skipRotate or len(skipRotate) != 3:
        if is_joint:
            # store the orientation values
            rot_index = 0
            second_index = 0
            joint_orientation = cmds.getAttr("{}.jointOrient".format(driven))[0]

            # create the compensation node strand
            rotation_compose = cmds.createNode(
                "composeMatrix", name="{}_rotateComposeMatrix".format(prefix))
            rotation_first_mult_matrix = cmds.createNode(
                "multMatrix", name="{}_firstRotateMultMatrix".format(prefix))
            rotation_inverse_matrix = cmds.createNode(
                "inverseMatrix", name="{}_rotateInverseMatrix".format(prefix))
            rotation_sec_mult_matrix = cmds.createNode(
                "multMatrix", name="{}_secRotateMultMatrix".format(prefix))
            rotation_decompose_matrix = cmds.createNode(
                "decomposeMatrix", name="{}_rotateDecomposeMatrix".format(prefix))

            # set values and make connections for rotation strand
            cmds.setAttr("{}.inputRotate".format(rotation_compose),
                         *joint_orientation)
            cmds.connectAttr("{}.outputMatrix".format(rotation_compose),
                             "{0}.matrixIn[{1}]".format(
                                 rotation_first_mult_matrix, rot_index))

            if parent_of_driven:
                rot_index += 1
                cmds.connectAttr("{}.worldMatrix[0]".format(parent_of_driven),
                                 "{0}.matrixIn[{1}]".format(
                                     rotation_first_mult_matrix,
                                     rot_index))
            cmds.connectAttr("{}.matrixSum".format(rotation_first_mult_matrix),
                             "{}.inputMatrix".format(rotation_inverse_matrix))

            cmds.connectAttr(out_plug, "{0}.matrixIn[{1}]".format(
                rotation_sec_mult_matrix, second_index))

            if source_parent_cutoff:
                second_index += 1
                cmds.connectAttr("{}.worldInverseMatrix".format(
                    source_parent_cutoff),
                    "{0}.matrixIn[{1}]".format(rotation_sec_mult_matrix, second_index))

            second_index += 1
            cmds.connectAttr("{}.outputMatrix".format(
                rotation_inverse_matrix),
                "{0}.matrixIn[{1}]".format(rotation_sec_mult_matrix, second_index))
            cmds.connectAttr("{}.matrixSum".format(
                rotation_sec_mult_matrix),
                "{}.inputMatrix".format(rotation_decompose_matrix))
            rotation_output_plug = "{}.outputRotate".format(rotation_decompose_matrix)
        else:
            rotation_output_plug = "{}.outputRotate".format(decompose_matrix)

        # it All rotation attrs will be connected?
        if not skipRotate:
            cmds.connectAttr(rotation_output_plug, "{}.rotate".format(driven))
        else:
            for attr in "XYZ":
                if attr.lower() not in skipRotate and attr.upper() not in skipRotate:
                    cmds.connectAttr(
                        "{0}{1}".format(
                            rotation_output_plug, attr),
                        "{0}.rotate{1}".format(driven, attr))

    if not skipScale:
        cmds.connectAttr("{}.outputScale".format(decompose_matrix),
                         "{}.scale".format(driven))
    else:
        for attr in "XYZ":
            if attr.lower() not in skipScale and attr.upper() not in skipScale:
                cmds.connectAttr("{0}.outputScale{1}".format(
                    decompose_matrix, attr),
                    "{0}.scale{1}".format(driven, attr))

    return mult_matrix, decompose_matrix, average_node


def matrix_switch(parent_a,
                  parent_b,
                  child,
                  control_attribute,
                  position=True,
                  rotation=True,
                  scale=False,
                  source_parent_cutoff=None):
    """
    Create a matrix blended switch between two locations.
    Args:
        parent_a (str): first parent node
        parent_b (str): second parent node
        child (str): child to be constrained
        control_attribute (str): switch control attribute.
                e.g. masterCont.switch. If missing, will created
        position (bool): If True, makes the positional switch. Defaults True
        rotation (bool): If True, makes the rotational switch. Defaults True
        scale (bool): If True, makes the scale switch. Default False
        source_parent_cutoff (str): Any transforms on this node and
                above won't affect the constraint

    Returns:
        (str) name of the blend node

    """
    attribute.validate_attr(control_attribute, attr_range=[0, 1])
    mult_matrix_a, dump, _ = matrixConstraint(parent_a,
                                              child,
                                              maintainOffset=False,
                                              prefix=parent_a,
                                              skipRotate="xyz",
                                              skipTranslate="xyz",
                                              skipScale="xyz",
                                              source_parent_cutoff=None)
    attribute.disconnect_attr(dump, attr="inputMatrix")
    cmds.delete(dump)
    mult_matrix_b, dump, _ = matrixConstraint(parent_b,
                                              child,
                                              maintainOffset=False,
                                              prefix=parent_b,
                                              skipRotate="xyz",
                                              skipTranslate="xyz",
                                              skipScale="xyz",
                                              source_parent_cutoff=None)
    attribute.disconnect_attr(dump, attr="inputMatrix")
    cmds.delete(dump)

    wt_add_matrix = cmds.createNode("wtAddMatrix",
                                    name="wtAdd_{0}_{1}".format(
                                        parent_a, parent_b))
    cmds.connectAttr("{}.matrixSum".format(mult_matrix_a),
                     "{}.wtMatrix[0].matrixIn".format(wt_add_matrix))
    cmds.connectAttr("{}.matrixSum".format(mult_matrix_b),
                     "{}.wtMatrix[1].matrixIn".format(wt_add_matrix))

    attribute.drive_attrs(control_attribute,
                          "{}.wtMatrix[0].weightIn".format(wt_add_matrix),
                          driver_range=[0, 1],
                          driven_range=[0, 1],
                          force=False)
    attribute.drive_attrs(control_attribute,
                          "{}.wtMatrix[1].weightIn".format(wt_add_matrix),
                          driver_range=[0, 1],
                          driven_range=[1, 0],
                          force=False)
    if source_parent_cutoff:
        mult_matrix_cutoff = cmds.createNode(
            "multMatrix",
            name="multMatrixCutoff_{0}_{1}".format(parent_a, parent_b))
        cmds.connectAttr("{}.matrixSum".format(wt_add_matrix),
                         "{}.matrixIn[0]".format(mult_matrix_cutoff))
        cmds.connectAttr("{}.worldInverseMatrix".format(source_parent_cutoff),
                         "{}.matrixIn[1]".format(mult_matrix_cutoff))
        out_plug = "{}.matrixSum".format(mult_matrix_cutoff)
    else:
        out_plug = "{}.matrixSum".format(wt_add_matrix)

    decompose_node = cmds.createNode("decomposeMatrix",
                                     name="decompose_switch")
    cmds.connectAttr(out_plug, "%s.inputMatrix" % decompose_node)

    if position:
        cmds.connectAttr("{}.outputTranslate".format(decompose_node),
                         "{}.translate".format(child))
    if rotation:
        cmds.connectAttr("{}.outputRotate".format(decompose_node),
                         "{}.rotate".format(child))
    if scale:
        cmds.connectAttr("{}.outputScale".format(decompose_node),
                         "{}.scale".format(child))


def get_closest_uv(source_node, dest_node):
    """Return the UV coordinates of dest_node closest to the source_node.
    Args:
        source_node (str): source node to collect position
        dest_node (str): destination node which will collect
                        the uv coordinates from
    Returns:
        tuple: (float, float) The U and V values.
    """

    x_pos, y_pos, z_pos = api.get_world_translation(dest_node)
    closest_point_node = cmds.createNode('closestPointOnMesh')
    cmds.connectAttr("{}.outMesh".format(source_node),
                     "{}.inMesh".format(closest_point_node),
                     f=1)
    cmds.setAttr("{}.inPositionX".format(closest_point_node),
                 x_pos)
    cmds.setAttr("{}.inPositionY".format(closest_point_node),
                 y_pos)
    cmds.setAttr("{}.inPositionZ".format(closest_point_node),
                 z_pos)
    u_val = cmds.getAttr("{}.parameterU".format(closest_point_node))
    v_val = cmds.getAttr("{}.parameterV".format(closest_point_node))
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
    selection_list = OpenMaya.MSelectionList()
    selection_list.add(dest_node)
    dag_path = selection_list.getDagPath(0)

    mfn_mesh = OpenMaya.MFnMesh(dag_path)

    point = OpenMaya.MPoint(position)
    space = OpenMaya.MSpace.kWorld

    u_val, v_val, _ = mfn_mesh.getUVAtPoint(point, space)

    return u_val, v_val


def get_vertex_uv(mesh, vertex_id):
    uv_map = cmds.polyListComponentConversion(
        '{0}.vtx[{1}]'.format(mesh, vertex_id), toUV=True)
    return cmds.polyEditUV(uv_map, q=True)


def create_follicle(name, surface, uv):
    follicle = (cmds.createNode('follicle', n='%s_follicleShape' % name))
    follicle_transform = (cmds.listRelatives(follicle, parent=True))[0]

    node_type = cmds.nodeType(surface)
    if node_type == 'nurbsSurface':
        # NURBS
        out = 'local'
        inp = 'inputSurface'
    else:
        # POLY
        out = 'outMesh'
        inp = 'inputMesh'

    cmds.connectAttr("{}.worldMatrix[0]".format(surface),
                     "{}.inputWorldMatrix".format(follicle))
    cmds.connectAttr("{0}.{1}".format(surface, out),
                     "{0}.{1}".format(follicle, inp))
    cmds.connectAttr("{}.outTranslate".format(follicle),
                     "{}.translate".format(follicle_transform))
    cmds.connectAttr("{}.outRotate".format(follicle),
                     "{}.rotate".format(follicle_transform))
    cmds.setAttr("{}.parameterU".format(follicle), uv[0])
    cmds.setAttr("{}.parameterV".format(follicle), uv[1])
    return follicle_transform, follicle


def uv_pin(mesh_transform, coordinates):
    assert cmds.about(api=True) >= 20200000, \
        "uv_pin requires Maya 2020 and later"
    all_shapes = cmds.listRelatives(mesh_transform,
                                    shapes=True,
                                    children=True,
                                    parent=False)
    # seperate intermediates
    intermediates = [x for x in all_shapes
                     if cmds.getAttr("{}.intermediateObject".format(x)) == 1]
    non_intermediates = [x for x in all_shapes if x not in intermediates]
    deformed_mesh = non_intermediates[0]
    if not intermediates:
        # create original / deformed mesh hiearchy
        dup = cmds.duplicate(mesh_transform,
                             name="{}_ORIG".format(mesh_transform))[0]
        original_mesh = cmds.listRelatives(dup, children=True)[0]
        cmds.parent(original_mesh, mesh_transform, shape=True, r=True)
        cmds.delete(dup)
        incoming_connections = connections(deformed_mesh)["incoming"]
        for connection in incoming_connections:
            attribute.disconnect_attr(connection["plug_out"])
            cmds.connectAttr(connection["plug_in"],
                             connection["plug_out"].replace(
                                 deformed_mesh, original_mesh))
        # hide/intermediate original mesh
        cmds.setAttr("%s.hiddenInOutliner" % original_mesh, 1)
        cmds.setAttr("%s.intermediateObject" % original_mesh, 1)
        interface.refresh_outliner()
    else:
        original_mesh = intermediates[0]

    uv_pin_node = cmds.createNode("uvPin")

    cmds.connectAttr("{}.worldMesh".format(deformed_mesh),
                     "{}.deformedGeometry".format(uv_pin_node))
    cmds.connectAttr("{}.outMesh".format(original_mesh),
                     "{}.originalGeometry".format(uv_pin_node))

    cmds.setAttr("%s.coordinate[0]" % uv_pin_node, *coordinates)

    return uv_pin_node


def pin_to_surface(node, surface, sr="", st="", ss="xyz"):
    world_pos = api.get_world_translation(node)
    uv_coordinates = get_uv_at_point(world_pos, surface)
    _uv_pin = uv_pin(surface, uv_coordinates)
    decompose_matrix_node = cmds.createNode("decomposeMatrix",
                                            name="decompose_pinMatrix")
    cmds.connectAttr("{}.outputMatrix[0]".format(_uv_pin),
                     "{}.inputMatrix".format(decompose_matrix_node))

    for attr in "XYZ":
        if attr.lower() not in sr and attr.upper() not in sr:
            cmds.connectAttr("{0}.outputRotate{1}".format(
                decompose_matrix_node, attr),
                "{0}.rotate{1}".format(node, attr))

    for attr in "XYZ":
        if attr.lower() not in st and attr.upper() not in st:
            cmds.connectAttr("{0}.outputTranslate{1}".format(
                decompose_matrix_node, attr),
                "{0}.translate{1}".format(node, attr))

    for attr in "XYZ":
        if attr.lower() not in ss and attr.upper() not in ss:
            cmds.connectAttr("{0}.outputScale{1}".format(
                decompose_matrix_node, attr),
                "{0}.scale{1}".format(node, attr))

    return _uv_pin


def average_constraint(target_mesh,
                       vertex_list,
                       source_object=None,
                       offset_parent=False,
                       force_follicle=False):
    """
    Create a average weighted constraint between defined vertices.
    Works version 2020+
    ATTENTION: Follicles won't follow face normals if the
    normals are locked
    Args:
        target_mesh (str): Mesh object which holds the defined vertices
        vertex_list (List): List of Integer vertex IDs
        source_object (str): If not defined a locator
                                will be created instead
        offset_parent (bool): If True, the matrix output will be connected
                                to offset parent matrix of the source object,
                                leaving the transform values available
        force_follicle (bool): If True, follicles will be used instead
                                of pin constraints.

    Returns:(String) source object. It will be the created locator
                                if none provided
    """
    if not force_follicle:
        assert cmds.about(api=True) >= 20200000, \
            "uv_pin requires Maya 2020 and later"
    average_node = cmds.createNode("wtAddMatrix")
    weight_value = 1.0 / float(len(vertex_list))
    for i, vertex_nmb in enumerate(vertex_list):
        uv = get_vertex_uv(target_mesh, vertex_nmb)
        if force_follicle:
            pin_node, _ = create_follicle(
                "pin%i" % i, target_mesh, uv)
            cmds.connectAttr("{}.worldMatrix[0]".format(pin_node),
                             "{0}.wtMatrix[{1}].matrixIn".format(
                                 average_node, i))
        else:
            pin_node = uv_pin(target_mesh, uv)
            cmds.connectAttr("{}.outputMatrix[0]".format(pin_node),
                             "{0}.wtMatrix[{1}].matrixIn".format(
                                 average_node, i))
        cmds.setAttr("{0}.wtMatrix[{1}].weightIn".format(
            average_node, i), weight_value)

    if not source_object:
        source_object = cmds.spaceLocator(name="averaged_loc")[0]

    if not offset_parent:
        mult_matrix = cmds.createNode("multMatrix")
        decompose_matrix = cmds.createNode("decomposeMatrix")
        cmds.connectAttr("{}.matrixSum".format(average_node),
                         "{}.matrixIn[0]".format(mult_matrix))
        cmds.connectAttr("{}.matrixSum".format(mult_matrix),
                         "{}.inputMatrix".format(decompose_matrix))
        cmds.connectAttr("{}.outputTranslate".format(decompose_matrix),
                         "{}.translate".format(source_object))
        cmds.connectAttr("{}.outputRotate".format(decompose_matrix),
                         "{}.rotate".format(source_object))

    else:
        pick_matrix = cmds.createNode("pickMatrix")
        cmds.connectAttr("{}.matrixSum".format(average_node),
                         "{}.inputMatrix".format(pick_matrix))
        cmds.setAttr("{}.useRotate".format(pick_matrix), 1)
        cmds.setAttr("{}.useScale".format(pick_matrix), 0)
        cmds.setAttr("{}.useShear".format(pick_matrix), 0)
        cmds.connectAttr("{}.outputMatrix".format(pick_matrix),
                         "{}.offsetParentMatrix".format(source_object))
        cmds.connectAttr("{}.outputMatrix".format(pick_matrix),
                         "{}.offsetParentMatrix".format(source_object))
    return source_object


def connect_mirror(node1, node2, mirror_axis="X"):
    """
    Make a mirrored connection between node1 and node2 along the mirrorAxis.
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
    cmds.connectAttr("{}.translate".format(node1),
                     "{}.input".format(rvs_node_t))
    cmds.connectAttr("{}.output".format(rvs_node_t),
                     "{}.input3D[0]".format(minus_op_t))
    cmds.setAttr("{}.input3D[1]".format(minus_op_t), 1, 1, 1)
    # nodes Rotate
    rvs_node_r = cmds.createNode("reverse")
    minus_op_r = cmds.createNode("plusMinusAverage")
    cmds.setAttr("%s.operation" % minus_op_r, 2)
    cmds.connectAttr("{}.rotate".format(node1),
                     "{}.input".format(rvs_node_r))
    cmds.connectAttr("{}.output".format(rvs_node_r),
                     "{}.input3D[0]".format(minus_op_r))

    cmds.setAttr("%s.input3D[1]" % minus_op_r, 1, 1, 1)

    # Translate

    if mirror_axis == "X":
        cmds.connectAttr("{}.output3Dx".format(minus_op_t),
                         "{}.tx".format(node2))
        cmds.connectAttr("{}.ty".format(node1),
                         "{}.ty".format(node2))
        cmds.connectAttr("{}.tz".format(node1),
                         "{}.tz".format(node2))
        cmds.connectAttr("{}.rx".format(node1),
                         "{}.rx".format(node2))
        cmds.connectAttr("{}.output3Dy".format(minus_op_r),
                         "{}.ry".format(node2))
        cmds.connectAttr("{}.output3Dz".format(minus_op_r),
                         "{}.rz".format(node2))

    if mirror_axis == "Y":
        cmds.connectAttr("{}.tx".format(node1),
                         "{}.tx".format(node2))
        cmds.connectAttr("{}.output3Dy".format(minus_op_t),
                         "{}.ty".format(node2))
        cmds.connectAttr("{}.tz".format(node1),
                         "{}.tz".format(node2))
        cmds.connectAttr("{}.output3Dx".format(minus_op_r),
                         "{}.rx".format(node2))
        cmds.connectAttr("{}.ry".format(node1),
                         "{}.ry".format(node2))
        cmds.connectAttr("{}.output3Dz".format(minus_op_r),
                         "{}.rz".format(node2))

    if mirror_axis == "Z":
        cmds.connectAttr("{}.tx".format(node1),
                         "{}.tx".format(node2))
        cmds.connectAttr("{}.ty".format(node1),
                         "{}.ty".format(node2))
        cmds.connectAttr("{}.output3Dz".format(minus_op_t),
                         "{}.tz".format(node2))
        cmds.connectAttr("{}.rx".format(node1),
                         "{}.rx".format(node2))
        cmds.connectAttr("{}.output3Dy".format(minus_op_r),
                         "{}.ry".format(node2))
        cmds.connectAttr("{}.output3Dz".format(minus_op_r),
                         "{}.rz".format(node2))


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

    # grab 'bindPose' world matrix from transform
    # we don't want to inherit from #
    no_inherit_matrix = ("%s_bindPose_fourByFourMatrix" % no_inherit)
    if not cmds.objExists(no_inherit_matrix):
        grabbed_matrix = cmds.getAttr("{}.worldMatrix[0]".format(no_inherit))
        no_inherit_matrix = cmds.createNode("fourByFourMatrix",
                                            n=no_inherit_matrix)
        element_list = ["in00", "in01", "in02", "in03", "in10", "in11",
                        "in12", "in13", "in20", "in21", "in22", "in23",
                        "in30", "in31", "in32", "in33"]
        for index, element in enumerate(element_list):
            cmds.setAttr("{0}.{1}".format(no_inherit_matrix, element),
                         grabbed_matrix[index])

    # multiply all of the matrices together #
    mult_matrix = cmds.createNode("multMatrix",
                                  n="{}_multMatrix".format(inherit))
    cmds.connectAttr("{}.worldMatrix[0]".format(inherit),
                     "{}.matrixIn[0]".format(mult_matrix))
    cmds.connectAttr("{}.worldInverseMatrix[0]".format(no_inherit),
                     "{}.matrixIn[1]".format(mult_matrix))
    cmds.connectAttr("{}.output".format(no_inherit_matrix),
                     "{}.matrixIn[2]".format(mult_matrix))
    # decompose result #
    decomp_matrix = cmds.createNode("decomposeMatrix",
                                    name="{}_decomposeMatrix".format(destination))
    cmds.connectAttr("{}.matrixSum".format(mult_matrix),
                     "{}.inputMatrix".format(decomp_matrix))

    # connect up #
    for attr in target_attrs:
        output_attr = "output{0}{1}".format(
            attr[0].capitalize(), attr[1:])  # capitalize only first letter

        lock_state = cmds.getAttr("{0}.{1}".format(destination, attr),
                                  lock=True)
        # unlock, connect, then reinstate lock state #
        cmds.setAttr("{0}.{1}".format(destination, attr),
                     lock=False)  # unlock #
        cmds.connectAttr("{0}.{1}".format(decomp_matrix, output_attr),
                         "{0}.{1}".format(destination, attr),
                         force=force)

        # set back to original lock state #
        cmds.setAttr("{0}.{1}".format(destination, attr), lock=lock_state)

    return decomp_matrix, mult_matrix, no_inherit_matrix
