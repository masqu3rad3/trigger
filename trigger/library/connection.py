"""Any connection / constrain / attachment / procedural movemen related methods goes here"""

from trigger.library import api
from maya import cmds


def connections(node, exclude_nodes=None, exclude_types=None):
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

    Returns: (Dictionary)

    """

    raw_inputs = cmds.listConnections(node, plugs=True, source=True, destination=False, connections=True)
    raw_outputs = cmds.listConnections(node, plugs=True, source=False, destination=True, connections=True)

    input_plugs = raw_inputs[::2] if raw_inputs else []
    output_plugs = raw_outputs[::2] if raw_outputs else []

    result_dict = {}
    result_dict["incoming"] = []
    result_dict["outgoing"] = []

    # filter input plug lists
    if exclude_nodes:
        input_plugs = [plug for plug in input_plugs if plug.split(".")[0] not in exclude_nodes]
    if exclude_types:
        input_plugs = [plug for plug in input_plugs if cmds.objectType(plug.split(".")[0]) not in exclude_types]

    for in_plug in input_plugs:
        conn = {}
        conn["plug_out"], conn["plug_in"] = cmds.listConnections(in_plug, plugs=True, source=True, destination=False,
                                                                 connections=True)
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

    return result_dict

def matrixConstraint(parent, child, mo=True, prefix="", sr=None, st=None, ss=None, source_parent_cutoff=None):
    """
    Creates a Matrix Constraint
    Args:
        parent: (String) Parent Node
        child: (String) Child Node
        mo: (Bool) Maintain offset. If True, the existing distance between nodes will be preserved
        prefix: (String) Prefix for the nodes names which will be created
        sr: (List) Skip Rotations. Listed rotation values will be skipped. "xyz" or ["x", "y", "z"]
        st: (List) Skip Translation. Listed translation values will be skipped. "xyz" or ["x", "y", "z"]
        ss: (List) Skip Scale. Listed scale values will be skipped. "xyz" or ["x", "y", "z"]
        source_parent_cutoff: (String) The transformation matrices above this node won't affect to the child.

    Returns: (Tuple) mult_matrix, decompose_matrix

    """

    parents = cmds.listRelatives(parent=True)
    child_parent = parents[0] if parents else None
    next_index = -1

    mult_matrix = cmds.createNode("multMatrix", name="%s_multMatrix" % prefix)
    decompose_matrix = cmds.createNode("decomposeMatrix", name="%s_decomposeMatrix" % prefix)

    if mo:
        parentWorldMatrix = api.getMDagPath(parent).inclusiveMatrix()
        childWorldMatrix = api.getMDagPath(child).inclusiveMatrix()
        localOffset = childWorldMatrix * parentWorldMatrix.inverse()
        # next_index = getNextIndex("%s.matrixIn" % mult_matrix)
        next_index += 1
        cmds.setAttr("%s.matrixIn[%i]" % (mult_matrix, next_index), localOffset, type="matrix")

    # next_index = getNextIndex("%s.matrixIn" % mult_matrix)
    next_index += 1
    cmds.connectAttr("%s.worldMatrix[0]" % parent, "%s.matrixIn[%i]" % (mult_matrix, next_index))
    cmds.connectAttr("%s.matrixSum" % mult_matrix, "%s.inputMatrix" % decompose_matrix)

    if source_parent_cutoff:
        # next_index = getNextIndex("%s.matrixIn" % mult_matrix)
        next_index += 1
        cmds.connectAttr("%s.worldInverseMatrix" % source_parent_cutoff, "%s.matrixIn[%i]" % (mult_matrix, next_index))


    if child_parent:
        child_parentWorldMatrix = api.getMDagPath(child_parent).inclusiveMatrix().inverse()
        # childWorldMatrix = getMDagPath(child).inclusiveMatrix()
        # localOffset = childWorldMatrix * child_parentWorldMatrix.inverse()
        # next_index = getNextIndex("%s.matrixIn" % mult_matrix)
        next_index += 1
        cmds.setAttr("%s.matrixIn[%i]" % (mult_matrix, next_index), child_parentWorldMatrix, type="matrix")


    if not st:
        cmds.connectAttr("%s.outputTranslate" % decompose_matrix, "%s.translate" % child)
    else:
        for attr in "XYZ":
            if attr.lower() not in st and attr.upper() not in st:
                cmds.connectAttr("%s.outputTranslate%s" % (decompose_matrix, attr), "%s.translate%s" % (child, attr))
    if not sr:
        cmds.connectAttr("%s.outputRotate" % decompose_matrix, "%s.rotate" % child)
    else:
        for attr in "XYZ":
            if attr.lower() not in sr and attr.upper() not in sr:
                cmds.connectAttr("%s.outputRotate%s" % (decompose_matrix, attr), "%s.rotate%s" % (child, attr))
    if not ss:
        cmds.connectAttr("%s.outputScale" % decompose_matrix, "%s.scale" % child)
    else:
        for attr in "XYZ":
            if attr.lower() not in ss and attr.upper() not in ss:
                cmds.connectAttr("%s.outputScale%s" % (decompose_matrix, attr), "%s.scale%s" % (child, attr))

    return mult_matrix, decompose_matrix