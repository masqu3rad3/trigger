"""Any connection / constrain / attachment / procedural movemen related methods goes here"""

from trigger.library import api
from trigger.library import interface
from trigger.library import attribute
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

    is_joint = True if cmds.objectType(child) == "joint" else False
    parents = cmds.listRelatives(child, parent=True)
    child_parent = parents[0] if parents else None
    next_index = -1

    mult_matrix = cmds.createNode("multMatrix", name="%s_multMatrix" % prefix)
    decompose_matrix = cmds.createNode("decomposeMatrix", name="%s_decomposeMatrix" % prefix)

    if mo:
        parentWorldMatrix = api.getMDagPath(parent).inclusiveMatrix()
        childWorldMatrix = api.getMDagPath(child).inclusiveMatrix()
        localOffset = childWorldMatrix * parentWorldMatrix.inverse()
        next_index += 1
        cmds.setAttr("%s.matrixIn[%i]" % (mult_matrix, next_index), localOffset, type="matrix")

    next_index += 1
    cmds.connectAttr("%s.worldMatrix[0]" % parent, "%s.matrixIn[%i]" % (mult_matrix, next_index))
    cmds.connectAttr("%s.matrixSum" % mult_matrix, "%s.inputMatrix" % decompose_matrix)

    if source_parent_cutoff:
        next_index += 1
        cmds.connectAttr("%s.worldInverseMatrix" % source_parent_cutoff, "%s.matrixIn[%i]" % (mult_matrix, next_index))


    if child_parent:
        next_index += 1
        cmds.connectAttr("%s.worldInverseMatrix[0]" %child_parent, "%s.matrixIn[%i]" %(mult_matrix, next_index))

    # if child_parent:
        # child_parentWorldMatrix = api.getMDagPath(child_parent).inclusiveMatrix().inverse()
        # next_index += 1
        # cmds.setAttr("%s.matrixIn[%i]" % (mult_matrix, next_index), child_parentWorldMatrix, type="matrix")


    if not st:
        cmds.connectAttr("%s.outputTranslate" % decompose_matrix, "%s.translate" % child)
    else:
        for attr in "XYZ":
            if attr.lower() not in st and attr.upper() not in st:
                cmds.connectAttr("%s.outputTranslate%s" % (decompose_matrix, attr), "%s.translate%s" % (child, attr))
    if not sr:
        ## Joint rotations needs to be handled differently because of the jointOrientation
        if is_joint:
            # store the orientation values
            rot_index = 0
            second_index = 0
            joint_orientation = cmds.getAttr("%s.jointOrient" % child)[0]

            # create the compensation node strand
            rotation_compose = cmds.createNode("composeMatrix", name="%s_rotateComposeMatrix" %prefix)
            rotation_first_mult_matrix = cmds.createNode("multMatrix", name="%s_firstRotateMultMatrix" %prefix)
            rotation_inverse_matrix = cmds.createNode("inverseMatrix", name="%s_rotateInverseMatrix" %prefix)
            rotation_sec_mult_matrix = cmds.createNode("multMatrix", name="%s_secRotateMultMatrix" %prefix)
            rotation_decompose_matrix = cmds.createNode("decomposeMatrix", name="%s_rotateDecomposeMatrix" %prefix)

            # set values and make connections for rotation strand
            cmds.setAttr("%s.inputRotate" %rotation_compose, *joint_orientation)
            cmds.connectAttr("%s.outputMatrix" %rotation_compose, "%s.matrixIn[%i]" %(rotation_first_mult_matrix, rot_index))
            # if source_parent_cutoff:
            #     rot_index +=1
            #     cmds.connectAttr("%s.worldInverseMatrix" % source_parent_cutoff, "%s.matrixIn[%i]" % (rotation_first_mult_matrix, rot_index))

            if child_parent:
                rot_index +=1
                cmds.connectAttr("%s.worldMatrix[0]" %child_parent, "%s.matrixIn[%i]" %(rotation_first_mult_matrix, rot_index))
            cmds.connectAttr("%s.matrixSum" %rotation_first_mult_matrix, "%s.inputMatrix" %rotation_inverse_matrix)

            cmds.connectAttr("%s.worldMatrix[0]" % parent, "%s.matrixIn[%i]" %(rotation_sec_mult_matrix, second_index))

            if source_parent_cutoff:
                second_index +=1
                cmds.connectAttr("%s.worldInverseMatrix" % source_parent_cutoff, "%s.matrixIn[%i]" % (rotation_sec_mult_matrix, second_index))

            second_index += 1
            cmds.connectAttr("%s.outputMatrix" %rotation_inverse_matrix, "%s.matrixIn[%i]" %(rotation_sec_mult_matrix, second_index))
            cmds.connectAttr("%s.matrixSum" %rotation_sec_mult_matrix, "%s.inputMatrix" %rotation_decompose_matrix)

            cmds.connectAttr("%s.outputRotate" % rotation_decompose_matrix, "%s.rotate" % child)
        else:
            cmds.connectAttr("%s.outputRotate" % decompose_matrix, "%s.rotate" % child)
    else:

        ## Joint rotations needs to be handled differently because of the jointOrientation
        if is_joint:
            # if all rotation axis defined, dont create the strand
            if len(sr) != 3:
                # store the orientation values
                rot_index = 0
                second_index = 0
                joint_orientation = cmds.getAttr("%s.jointOrient" % child)[0]

                # create the compensation node strand
                rotation_compose = cmds.createNode("composeMatrix", name="%s_rotateComposeMatrix" %prefix)
                rotation_first_mult_matrix = cmds.createNode("multMatrix", name="%s_firstRotateMultMatrix" %prefix)
                rotation_inverse_matrix = cmds.createNode("inverseMatrix", name="%s_rotateInverseMatrix" %prefix)
                rotation_sec_mult_matrix = cmds.createNode("multMatrix", name="%s_secRotateMultMatrix" %prefix)
                rotation_decompose_matrix = cmds.createNode("decomposeMatrix", name="%s_rotateDecomposeMatrix" %prefix)

                # set values and make connections for rotation strand
                cmds.setAttr("%s.inputRotate" %rotation_compose, *joint_orientation)
                cmds.connectAttr("%s.outputMatrix" %rotation_compose, "%s.matrixIn[%i]" %(rotation_first_mult_matrix, rot_index))
                # if source_parent_cutoff:
                #     rot_index +=1
                #     cmds.connectAttr("%s.worldInverseMatrix" % source_parent_cutoff, "%s.matrixIn[%i]" % (rotation_first_mult_matrix, rot_index))

                if child_parent:
                    rot_index +=1
                    cmds.connectAttr("%s.worldMatrix[0]" %child_parent, "%s.matrixIn[%i]" %(rotation_first_mult_matrix, rot_index))
                cmds.connectAttr("%s.matrixSum" %rotation_first_mult_matrix, "%s.inputMatrix" %rotation_inverse_matrix)

                cmds.connectAttr("%s.worldMatrix[0]" % parent, "%s.matrixIn[%i]" %(rotation_sec_mult_matrix, second_index))

                if source_parent_cutoff:
                    second_index +=1
                    cmds.connectAttr("%s.worldInverseMatrix" % source_parent_cutoff, "%s.matrixIn[%i]" % (rotation_sec_mult_matrix, second_index))

                second_index += 1
                cmds.connectAttr("%s.outputMatrix" %rotation_inverse_matrix, "%s.matrixIn[%i]" %(rotation_sec_mult_matrix, second_index))
                cmds.connectAttr("%s.matrixSum" %rotation_sec_mult_matrix, "%s.inputMatrix" %rotation_decompose_matrix)

                for attr in "XYZ":
                    if attr.lower() not in sr and attr.upper() not in sr:
                        cmds.connectAttr("%s.outputRotate%s" % (rotation_decompose_matrix, attr), "%s.rotate%s" % (child, attr))

            else:
                pass

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

def matrixSwitch(parentA, parentB, child, control_attribute, position=True, rotation=True, scale=False):
    """
    Creates a matrix blended switch between two locations

    Args:
        parentA: (string) first parent node
        parentB: (string) second parent node
        child: (string) child to be constrained
        control_attribute: (string) switch control attribute. e.g. masterCont.switch. If doesnt exist, it will be created
        position: (boolean) If True, makes the positional switch. Default True
        rotation: (boolean) If True, makes the rotational switch. Default True
        scale: (boolean) If True, makes the scale switch. Default False

    Returns:

    """
    attribute.validate_attr(control_attribute, attr_range=[0,1])

    mult_matrix_a = cmds.createNode("multMatrix", name="multMatrix_%s" %parentA)
    cmds.connectAttr("%s.worldMatrix[0]" %parentA, "%s.matrixIn[0]" %mult_matrix_a)

    mult_matrix_b = cmds.createNode("multMatrix", name="multMatrix_%s" %parentB)
    cmds.connectAttr("%s.worldMatrix[0]" %parentB, "%s.matrixIn[0]" %mult_matrix_b)

    wt_add_matrix = cmds.createNode("wtAddMatrix", name="wtAdd_%s_%s" %(parentA, parentB))
    cmds.connectAttr("%s.matrixSum" %mult_matrix_a, "%s.wtMatrix[0].matrixIn" %wt_add_matrix)
    cmds.connectAttr("%s.matrixSum" %mult_matrix_b, "%s.wtMatrix[1].matrixIn" %wt_add_matrix)

    attribute.drive_attrs(control_attribute, "%s.wtMatrix[0].weightIn" %wt_add_matrix, driver_range=[0,1], driven_range=[0,1], force=False)
    attribute.drive_attrs(control_attribute, "%s.wtMatrix[1].weightIn" %wt_add_matrix, driver_range=[0,1], driven_range=[1,0], force=False)

    decompose_node = cmds.createNode("decomposeMatrix", name="decompose_switch")
    cmds.connectAttr("%s.matrixSum" %wt_add_matrix, "%s.inputMatrix" %decompose_node)

    if position:
        cmds.connectAttr("%s.outputTranslate" %decompose_node, "%s.translate" %child)
    if rotation:
        cmds.connectAttr("%s.outputRotate" %decompose_node, "%s.rotate" %child)
    if scale:
        cmds.connectAttr("%s.outputScale" %decompose_node, "%s.scale" %child)

def getClosestUV(source_node, dest_node):
    xPos, yPos, zPos = api.getWorldTranslation(dest_node)
    CPOM = cmds.createNode('closestPointOnMesh')
    cmds.connectAttr("%s.outMesh" % source_node, "%s.inMesh" % CPOM, f=1)
    cmds.setAttr("%s.inPositionX" %CPOM, xPos)
    cmds.setAttr("%s.inPositionY" %CPOM, yPos)
    cmds.setAttr("%s.inPositionZ" %CPOM, zPos)
    uVal = cmds.getAttr("%s.parameterU" %CPOM)
    vVal = cmds.getAttr("%s.parameterV" %CPOM)
    cmds.delete(CPOM)

    return uVal, vVal

def getVertexUV(mesh, vertex_id):
    uv_map = cmds.polyListComponentConversion('{0}.vtx[{1}]'.format(mesh, vertex_id), toUV=True)
    return cmds.polyEditUV(uv_map, q=True)

def createFollicle(name, surfS, uv):
    follicle = (cmds.createNode('follicle', n='%s_follicleShape' %name))
    follicle_transform = (cmds.listRelatives(follicle, parent=True))[0]

    nType = cmds.nodeType(surfS)
    if nType == 'nurbsSurface':
        #NURBS
        out = '.local'
        inp = '.inputSurface'
    else:
        #POLY
        out = '.outMesh'
        inp = '.inputMesh'

    cmds.connectAttr('%s.worldMatrix'%surfS, '%s.inputWorldMatrix'%follicle)
    cmds.connectAttr(surfS+out, follicle+inp)
    cmds.connectAttr('%s.outTranslate'%follicle, '%s.translate'%follicle_transform)
    cmds.connectAttr('%s.outRotate'%follicle, '%s.rotate'%follicle_transform)
    cmds.setAttr('%s.parameterU'%follicle, uv[0])
    cmds.setAttr('%s.parameterV'%follicle, uv[1])
    return follicle_transform

def uvPin(mesh_transform, coordinates):
    assert cmds.about(api=True) > 20200000, "uv_pin requires Maya 2020 and later"
    all_shapes = cmds.listRelatives(mesh_transform, shapes=True, children=True, parent=False)
    #seperate intermediates
    intermediates = [x for x in all_shapes if cmds.getAttr("%s.intermediateObject" %x) == 1]
    non_intermediates = [x for x in all_shapes if x not in intermediates]
    deformed_mesh = non_intermediates[0]
    if not intermediates:
        # create original / deformed mesh hiearchy
        # deformed_mesh = cmds.listRelatives(mesh_transform, children=True, parent=False)[0]
        dup = cmds.duplicate(mesh_transform, name="%s_ORIG" % mesh_transform)[0]
        original_mesh = cmds.listRelatives(dup, children=True)[0]
        cmds.parent(original_mesh, mesh_transform, shape=True, r=True)
        cmds.delete(dup)
        incoming_connections = connections(deformed_mesh)["incoming"]
        for connection in incoming_connections:
            attribute.disconnect_attr(connection["plug_out"])
            cmds.connectAttr(connection["plug_in"], connection["plug_out"].replace(deformed_mesh, original_mesh))
        # cmds.connectAttr("%s.outMesh" % original_mesh, "%s.inMesh" % deformed_mesh)
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

def averageConstraint(target_mesh, vertex_list, source_object=None, offsetParent=False):
    """
    Creates a average weighted constraint between defined vertices. Works version 2020+
    Args:
        target_mesh: (String) Mesh object which holds the defined vertices
        vertex_list: (List) List of Integer vertex IDs
        source_object: (String) If not defined a locator will be created instead
        offsetParent: (Boolean) If True, the matrix output will be connected to offset parent matrix of
                    of the source object, leaving the transform values available

    Returns:(String) source object. It will be the created locator if none provided

    """
    assert cmds.about(api=True) > 20200000, "uv_pin requires Maya 2020 and later"
    average_node = cmds.createNode("wtAddMatrix")
    weight_value = 1.0 / float(len(vertex_list))
    for i, vertex_nmb in enumerate(vertex_list):
        uv = getVertexUV(target_mesh, vertex_nmb)
        pin_node = uvPin(target_mesh, uv)
        cmds.connectAttr("%s.outputMatrix[0]" % pin_node, "{0}.wtMatrix[{1}].matrixIn".format(average_node, i))
        cmds.setAttr("{0}.wtMatrix[{1}].weightIn".format(average_node, i), weight_value)

    if not source_object:
        source_object = cmds.spaceLocator(name="averaged_loc")[0]

    if not offsetParent:
        mult_matrix = cmds.createNode("multMatrix")
        decompose_matrix = cmds.createNode("decomposeMatrix")
        cmds.connectAttr("%s.matrixSum" % average_node, "%s.matrixIn[0]" % mult_matrix)
        cmds.connectAttr("%s.matrixSum" %mult_matrix, "%s.inputMatrix" %decompose_matrix)
        cmds.connectAttr("%s.outputTranslate" % decompose_matrix, "%s.translate" % source_object)
    else:
        pick_matrix = cmds.createNode("pickMatrix")
        cmds.connectAttr("%s.matrixSum" % average_node, "%s.inputMatrix" %pick_matrix)
        cmds.setAttr("%s.useRotate" %pick_matrix, 0)
        cmds.setAttr("%s.useScale" %pick_matrix, 0)
        cmds.setAttr("%s.useShear" %pick_matrix, 0)
        cmds.connectAttr("%s.outputMatrix" % pick_matrix, "%s.offsetParentMatrix" %source_object)
    return source_object

def connectMirror (node1, node2, mirrorAxis="X"):
    """
    Make a mirrored connection between node1 and node2 along the mirrorAxis
    Args:
        node1: Driver Node
        node2: Driven Node
        mirrorAxis: Mirror axis for the driven node.

    Returns: None

    """
    ## make sure the axis is uppercase:
    mirrorAxis = mirrorAxis.upper()
    ## strip - and +
    mirrorAxis = mirrorAxis.replace("+", "")
    mirrorAxis = mirrorAxis.replace("-", "")

    #nodes Translate
    rvsNodeT=cmds.createNode("reverse")
    minusOpT=cmds.createNode("plusMinusAverage")
    cmds.setAttr("%s.operation" %minusOpT, 2)
    cmds.connectAttr("{0}.translate".format(node1), "{0}.input".format(rvsNodeT))
    cmds.connectAttr("{0}.output".format(rvsNodeT), "{0}.input3D[0]".format(minusOpT))
    cmds.setAttr("%s.input3D[1]" %minusOpT, 1, 1, 1)
    #nodes Rotate
    rvsNodeR = cmds.createNode("reverse")
    minusOpR = cmds.createNode("plusMinusAverage")
    cmds.setAttr("%s.operation" %minusOpR, 2)
    cmds.connectAttr("{0}.rotate".format(node1), "{0}.input".format(rvsNodeR))

    cmds.connectAttr("{0}.output".format(rvsNodeR), "{0}.input3D[0]".format(minusOpR))

    cmds.setAttr("%s.input3D[1]" %minusOpR, 1, 1, 1)

    #Translate

    if (mirrorAxis=="X"):
        cmds.connectAttr("{0}.output3Dx".format(minusOpT), "{0}.tx".format(node2))
        cmds.connectAttr("{0}.ty".format(node1), "{0}.ty".format(node2))
        cmds.connectAttr("{0}.tz".format(node1), "{0}.tz".format(node2))
        cmds.connectAttr("{0}.rx".format(node1), "{0}.rx".format(node2))
        cmds.connectAttr("{0}.output3Dy".format(minusOpR), "{0}.ry".format(node2))
        cmds.connectAttr("{0}.output3Dz".format(minusOpR), "{0}.rz".format(node2))

    if (mirrorAxis=="Y"):
        cmds.connectAttr("{0}.tx".format(node1), "{0}.tx".format(node2))
        cmds.connectAttr("{0}.output3Dy".format(minusOpT), "{0}.ty".format(node2))
        cmds.connectAttr("{0}.tz".format(node1), "{0}.tz".format(node2))
        cmds.connectAttr("{0}.output3Dx".format(minusOpR), "{0}.rx".format(node2))
        cmds.connectAttr("{0}.ry".format(node1), "{0}.ry".format(node2))
        cmds.connectAttr("{0}.output3Dz".format(minusOpR), "{0}.rz".format(node2))

    if (mirrorAxis=="Z"):
        cmds.connectAttr("{0}.tx".format(node1), "{0}.tx".format(node2))
        cmds.connectAttr("{0}.ty".format(node1), "{0}.ty".format(node2))
        cmds.connectAttr("{0}.output3Dz".format(minusOpT), "{0}.tz".format(node2))
        cmds.connectAttr("{0}.rx".format(node1), "{0}.rx".format(node2))
        cmds.connectAttr("{0}.output3Dy".format(minusOpR), "{0}.ry".format(node2))
        cmds.connectAttr("{0}.output3Dz".format(minusOpR), "{0}.rz".format(node2))



def matrixLocalize(
    inherit_transform,
    offset_transform,
    localized_transform,
    prefix=None,
    target_attrs=None,
    force=True,
):
    # This function uses matrices to stick the destination_transform to the world space of the source_transform, but without inheriting...

    if not prefix:
        prefix = inherit_transform
    if not target_attrs:
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
    offset_bindpose_matrix = ("%s_bindPose_fourByFourMatrix" %offset_transform)
    if not cmds.objExists(offset_bindpose_matrix):
        grabbed_matrix = cmds.getAttr("%s.worldMatrix[0]" %offset_transform )
        offset_bindpose_matrix = cmds.createNode("fourByFourMatrix", n=offset_bindpose_matrix)
        element_list = ["in00", "in01", "in02", "in03", "in10", "in11", "in12", "in13", "in20", "in21", "in22", "in23", "in30", "in31", "in32", "in33"]
        for index, element in enumerate(element_list):
            cmds.setAttr("%s.%s" %(offset_bindpose_matrix, element),grabbed_matrix[index])

    # multiply all of the matrices together #
    mult_matrix = cmds.createNode("multMatrix", n="%s_multMatrix" %localized_transform)
    cmds.connectAttr("%s.worldMatrix[0]" %localized_transform, "%s.matrixIn[0]" %mult_matrix)
    cmds.connectAttr("%s.worldInverseMatrix[0]" %offset_transform, "%s.matrixIn[1]" %mult_matrix)
    cmds.connectAttr("%s.output" %offset_bindpose_matrix, "%s.matrixIn[2]" %mult_matrix)

    # decompose result #
    decomp_matrix = cmds.createNode("decomposeMatrix", n="%s_decomposeMatrix" %localized_transform)
    cmds.connectAttr("%s.matrixSum" %mult_matrix, "%s.inputMatrix" %decomp_matrix)

    # connect up #
    for attr in target_attrs:
        outputAttr = "output" + attr
        outputAttr = outputAttr.replace("translate", "Translate")
        outputAttr = outputAttr.replace("rotate", "Rotate")
        outputAttr = outputAttr.replace("scale", "Scale")

        lock_state = cmds.getAttr("%s.%s" %(localized_transform, attr), lock=True)
        # unlock, connect, then reinstate lock state #
        cmds.setAttr("%s.%s" %(localized_transform, attr), lock=False)  # unlock #
        cmds.connectAttr("%s.%s" %(decomp_matrix, outputAttr), "%s.%s" %(localized_transform, attr), force=force)
        # set back to original lock state #
        cmds.setAttr("%s.%s" %(localized_transform, attr), lock=lock_state)


    return decomp_matrix, mult_matrix, offset_bindpose_matrix