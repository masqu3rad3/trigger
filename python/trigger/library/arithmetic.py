"""Module to ease the arithmetic operations"""

from maya import cmds
from trigger.core import compatibility as compat
from trigger.core import filelog

LOG = filelog.Filelog(logname=__name__, filename="trigger_log")


def add(a=None, b=None, value_list=None, return_plug=True, name="add"):
    """
    Create plusMinusAverage Node, add the values or plugs and
    return the output node or plug.
    Accepts nodes or values, you can also use a list of nodes or plugs.
    Args:
        a (String): First value or plug to add
        b (String): Second value or plug to add
        value_list (List): List of values or plugs to add
        return_plug (Bool): Return the output plug or the node (optional)
        name (String): Name of the node (optional)

    Returns:
        String: Output plug or node
    """
    if not value_list:
        if not a or not b:
            cmds.error("value_list or a / b arguments must defined")
        else:
            value_list = [a, b]

    add_node = cmds.createNode("plusMinusAverage", name=name)
    cmds.setAttr("{}.operation".format(add_node), 1)
    for nmb, value in enumerate(value_list):
        if compat.is_string(value):
            cmds.connectAttr(value, "%s.input1D[%i]" % (add_node, nmb))
        else:
            cmds.setAttr("%s.input1D[%i]" % (add_node, nmb), value)

    if return_plug:
        return "{}.output1D".format(add_node)
    else:
        return add_node


def subtract(a=None, b=None, value_list=None, return_plug=True, name="subtract"):
    """
    Create plusMinusAverage Node, subtract the values and
    return the output node or plug.
    Accepts nodes or values, you can also use a list of nodes or plugs.
    Args:
        a (String): First value or plug to subtract
        b (String): Second value or plug to subtract
        value_list (List): List of values or plugs to subtract
        return_plug (Bool): Return the output plug or the node (optional)
        name (String): Name of the node (optional)

    Returns:
        String: Output plug or node
    """
    if not value_list:
        if not a or not b:
            cmds.error("value_list or a / b arguments must defined")
        else:
            value_list = [a, b]

    subtract_node = cmds.createNode("plusMinusAverage", name=name)
    cmds.setAttr("{}.operation".format(subtract_node), 2)
    for nmb, value in enumerate(value_list):
        if compat.is_string(value):
            cmds.connectAttr(value, "%s.input1D[%i]" % (subtract_node, nmb))
        else:
            cmds.setAttr("%s.input1D[%i]" % (subtract_node, nmb), value)

    if return_plug:
        return "{}.output1D".format(subtract_node)
    else:
        return subtract_node


def multiply(a, b, return_plug=True, name="multiply"):
    """
    Create multiplyDivide Node, multiply the values and
    return the output node or plug.
    Args:
        a (String): First value or plug to multiply
        b (String): Second value or plug to multiply
        return_plug (Bool): Return the output plug or the node (optional)
        name (String): Name of the node (optional)
    Returns:
        String: Output plug or node
    """
    mult_node = cmds.createNode("multDoubleLinear", name=name)

    for nmb, value in enumerate([a, b]):
        if compat.is_string(value):
            cmds.connectAttr(value, "%s.input%i" % (mult_node, nmb + 1))
        else:
            cmds.setAttr("%s.input%i" % (mult_node, nmb + 1), value)
    if return_plug:
        return "%s.output" % mult_node
    else:
        return mult_node


def divide(a, b, return_plug=True, name="divide"):
    """
    Create multiplyDivide Node, multiply the values and
    return the output node or plug.
    Args:
        a (String): First value or plug to divide
        b (String): Second value or plug to divide
        return_plug (Bool): Return the output plug or the node (optional)
        name (String): Name of the node (optional)
    Returns:
        String: Output plug or node
    """
    div_node = cmds.createNode("multiplyDivide", name=name)
    cmds.setAttr("%s.operation" % div_node, 2)
    for nmb, value in enumerate([a, b]):
        if compat.is_string(value):
            cmds.connectAttr(value, "%s.input%iX" % (div_node, nmb + 1))
        else:
            cmds.setAttr("%s.input%iX" % (div_node, nmb + 1), value)
    if return_plug:
        return "%s.outputX" % div_node
    else:
        return div_node


def power(a, b, return_plug=True, name="power"):
    """
    Get power of a and b.
    Accepts nodes or values.
    Args:
        a (String): First value or plug to power
        b (String): Second value or plug to power
        return_plug (Bool): Return the output plug or the node (optional)
        name (String): Name of the node (optional)
    Returns:
        String: Output plug or node
    """
    power_node = cmds.createNode("multiplyDivide", name=name)
    cmds.setAttr("%s.operation" % power_node, 3)
    for nmb, value in enumerate([a, b]):
        if compat.is_string(value):
            cmds.connectAttr(value, "%s.input%iX" % (power_node, nmb + 1))
        else:
            cmds.setAttr("%s.input%iX" % (power_node, nmb + 1), value)
    if return_plug:
        return "%s.outputX" % power_node
    else:
        return power_node


def abs(a, return_plug=True, name="absolute"):
    """
    Return absolute value of a.
    Args:
        a (String): Value or plug to get absolute value from
        return_plug (Bool): Return the output plug or the node (optional)
        name (String): Name of the node (optional)

    Returns:
        String: Output plug or node
    """
    p2_p = power(a, 2, name="pow2_%s" % name)
    abs_p = power(p2_p, 0.5, name=name)
    if return_plug:
        return abs_p
    else:
        return abs_p.split(".")[0]


def invert(a, return_plug=True, name="invert"):
    """
    Invert a value or plug.
    Args:
        a (String): Value or plug to invert
        return_plug (Bool): Return the output plug or the node (optional)
        name (String): Name of the node (optional)
    Returns:
        String: Output plug or node
    """
    return multiply(a, -1, return_plug=return_plug, name=name)


def reverse(a, return_plug=True, name="reverse"):
    """
    Reverse a value or plug.
    Args:
        a (String): Value or plug to reverse
        return_plug (Bool): Return the output plug or the node (optional)
        name (String): Name of the node (optional)
    Returns:
        String: Output plug or node
    """
    reverse_node = cmds.createNode("reverse", name=name)
    if compat.is_string(a):
        cmds.connectAttr(a, "%s.inputX" % reverse_node)
    else:
        cmds.setAttr("%s.inputX" % reverse_node, a)
    if return_plug:
        return "%s.outputX" % reverse_node
    else:
        return reverse_node


def clamp(a, minimum=0, maximum=1, return_plug=True, name="clamp"):
    """
    Clamp a value or plug between min and max.
    Args:
        a (String): Value or plug to clamp
        minimum (Float): Minimum value (optional). Defaults to 0.
        maximum (Float): Maximum value (optional). Defaults to 1.
        return_plug (Bool): Return the output plug or the node (optional)
        name (String): Name of the node (optional)
    Returns:
        String: Output plug or node
    """
    clamp_node = cmds.createNode("clamp", name=name)
    if compat.is_string(a):
        cmds.connectAttr(a, "%s.inputR" % clamp_node)
    else:
        cmds.setAttr("%s.inputR" % clamp_node, a)
    if compat.is_string(minimum):
        cmds.connectAttr(minimum, "%s.minR" % clamp_node)
    else:
        cmds.setAttr("%s.minR" % clamp_node, minimum)
    if compat.is_string(maximum):
        cmds.connectAttr(maximum, "%s.maxR" % clamp_node)
    else:
        cmds.setAttr("%s.maxR" % clamp_node, maximum)
    if return_plug:
        return "%s.outputR" % clamp_node
    else:
        return clamp_node


def switch(a, b, switch_value, return_plug=True, name="switch"):
    """
    Switch between a and b based on switch value.
    Args:
        a (String): First value or plug to switch
        b (String): Second value or plug to switch
        switch_value (String): Switch value or plug
        return_plug (Bool): Return the output plug or the node (optional)
        name (String): Name of the node (optional)
    Returns:
        String: Output plug or node
    """
    switch_node = cmds.createNode("blendTwoAttr", name=name)
    if compat.is_string(a):
        cmds.connectAttr(a, "%s.input[0]" % switch_node)
    else:
        cmds.setAttr("%s.input[0]" % switch_node, a)
    if compat.is_string(b):
        cmds.connectAttr(b, "%s.input[1]" % switch_node)
    else:
        cmds.setAttr("%s.input[1]" % switch_node, b)
    if compat.is_string(switch_value):
        cmds.connectAttr(switch_value, "%s.attributesBlender" % switch_node)
    else:
        cmds.setAttr("%s.attributesBlender" % switch_node, switch_value)
    if return_plug:
        return "%s.output" % switch_node
    else:
        return switch_node


def if_else(
    first_term,
    operation,
    second_term,
    if_true,
    if_false,
    return_plug=True,
    name="condition",
):
    """
    Create a condition node with given information
    Args:
        first_term (String): First term of the condition. Value or Plug
        operation (String): Operation to perform. Valid values are: ">", "<",
            ">=", "<=", "==", "!="
        second_term (String): Second term of the condition. Value or Plug
        if_true (String): Value or plug to return if condition is true
        if_false (String): Value or plug to return if condition is false
        return_plug (Bool): Return the output plug or the node (optional)
        name (String): Name of the node (optional)
    Returns:
        String: Output plug or node
    """
    operation_dict = {"==": 0, "!=": 1, ">": 2, ">=": 3, "<": 4, "<=": 5}
    if operation not in operation_dict.keys():
        msg = "Operation must be one of the following: {}".format(operation_dict.keys())
        LOG.error(msg)
        raise ValueError(msg)
    condition_node = cmds.createNode("condition", name=name)
    cmds.setAttr("{}.operation".format(condition_node), operation_dict.get(operation))
    if compat.is_string(first_term):
        cmds.connectAttr(first_term, "{}.firstTerm".format(condition_node))
    else:
        cmds.setAttr("{}.firstTerm".format(condition_node), first_term)

    if compat.is_string(second_term):
        cmds.connectAttr(second_term, "{}.secondTerm".format(condition_node))
    else:
        cmds.setAttr("{}.secondTerm".format(condition_node), second_term)

    if compat.is_string(if_true):
        cmds.connectAttr(if_true, "{}.colorIfTrueR".format(condition_node))
    else:
        cmds.setAttr("{}.colorIfTrueR".format(condition_node), if_true)

    if compat.is_string(if_false):
        cmds.connectAttr(if_false, "{}.colorIfFalseR".format(condition_node))
    else:
        cmds.setAttr("{}.colorIfFalseR".format(condition_node), if_false)

    if return_plug:
        return "{}.outColorR".format(condition_node)
    else:
        return condition_node


def multiply_matrix(matrices_list, return_plug=True, name="multMatrix"):
    """
    Multiply a list of matrices.
    Args:
        matrices_list (List): List of matrices to multiply
        return_plug (Bool): Return the output plug or the node (optional)
        name (String): Name of the node (optional)
    Returns:
        String: Output plug or node
    """
    mult_matrix_node = cmds.createNode("multMatrix", name=name)
    for index, matrix in enumerate(matrices_list):
        if compat.is_string(matrix):
            cmds.connectAttr(matrix, "%s.matrixIn[%i]" % (mult_matrix_node, index))
        else:
            cmds.setAttr(
                "%s.matrixIn[%i]" % (mult_matrix_node, index), matrix, type="matrix"
            )
    if return_plug:
        return "%s.matrixSum" % mult_matrix_node
    else:
        return mult_matrix_node


def decompose_matrix(matrix, return_plug=True, name="decomposeMatrix"):
    """
    Decompose a matrix into its components.
    Args:
        matrix (String): Matrix to decompose
        return_plug (Bool): Return the output plug or the node (optional)
        name (String): Name of the node (optional)
    Returns:
        String: Output plug or node
    """
    decompose_matrix_node = cmds.createNode("decomposeMatrix", name=name)
    if compat.is_string(matrix):
        cmds.connectAttr(matrix, "%s.inputMatrix" % decompose_matrix_node)
    else:
        cmds.setAttr(
            "{}.inputMatrix".format(decompose_matrix_node), matrix, type="matrix"
        )
    if return_plug:
        return [
            "{}.outputTranslate".format(decompose_matrix_node),
            "{}.outputRotate".format(decompose_matrix_node),
            "{}.outputScale".format(decompose_matrix_node),
        ]
    else:
        return decompose_matrix_node


def average_matrix(matrices_list, return_plug=True, name="averageMatrix"):
    """
    Average a list of matrices.
    Args:
        matrices_list (List): List of matrices to average
        return_plug (Bool): Return the output plug or the node (optional)
        name (String): Name of the node (optional)
    Returns:
        String: Output plug or node
    """
    average_matrix_node = cmds.createNode("wtAddMatrix", name=name)
    average_value = 1.0 / len(matrices_list)
    for index, matrix in enumerate(matrices_list):
        cmds.connectAttr(
            matrix, "{0}.wtMatrix[{1}].matrixIn".format(average_matrix_node, index)
        )
        cmds.setAttr(
            "{0}.wtMatrix[{1}].weightIn".format(average_matrix_node, index),
            average_value,
        )
    if return_plug:
        return "{}.matrixSum".format(average_matrix_node)
    else:
        return average_matrix_node
