"""Module to ease the arithmetic operations"""

from maya import cmds
from trigger.core import compatibility as compat

def add(a=None, b=None, value_list=None, return_plug=True, name="add"):
    """Creates plusMinusAverage Node, adds the values and returns the output node or plug"""
    if not value_list:
        if not a or not b:
            cmds.error("value_list or a / b arguments must defined")
        else:
            value_list = [a, b]

    add_node = cmds.createNode("plusMinusAverage", name=name)
    cmds.setAttr("%s.operation" %add_node, 1)
    for nmb, value in enumerate(value_list):
        if compat.is_string(value):
            cmds.connectAttr(value, "%s.input1D[%i]" %(add_node, nmb))
        else:
            cmds.setAttr("%s.input1D[%i]" %(add_node, nmb), value)

    if return_plug:
        return "%s.output1D" %add_node
    else:
        return add_node

def subtract(a=None, b=None, value_list=None, return_plug=True, name="subtract"):
    if not value_list:
        if not a or not b:
            cmds.error("value_list or a / b arguments must defined")
        else:
            value_list = [a, b]

    subtract_node = cmds.createNode("plusMinusAverage", name=name)
    cmds.setAttr("%s.operation" %subtract_node, 2)
    for nmb, value in enumerate(value_list):
        if compat.is_string(value):
            cmds.connectAttr(value, "%s.input1D[%i]" %(subtract_node, nmb))
        else:
            cmds.setAttr("%s.input1D[%i]" %(subtract_node, nmb), value)

    if return_plug:
        return "%s.output1D" %subtract_node
    else:
        return subtract_node

def multiply(a, b, return_plug=True, name="multiply"):
    mult_node = cmds.createNode("multDoubleLinear", name=name)

    for nmb, value in enumerate([a,b]):
        if compat.is_string(value):
            cmds.connectAttr(value, "%s.input%i" %(mult_node, nmb+1))
        else:
            cmds.setAttr("%s.input%i" %(mult_node, nmb+1), value)
    if return_plug:
        return "%s.output" %mult_node
    else:
        return mult_node

def divide(a, b, return_plug=True, name="divide"):
    div_node = cmds.createNode("multiplyDivide", name=name)
    cmds.setAttr("%s.operation" %div_node, 2)
    for nmb, value in enumerate([a,b]):
        if compat.is_string(value):
            cmds.connectAttr(value, "%s.input%iX" %(div_node, nmb+1))
        else:
            cmds.setAttr("%s.input%iX" %(div_node, nmb+1), value)
    if return_plug:
        return "%s.outputX" %div_node
    else:
        return div_node

def power(a, b, return_plug=True, name="power"):
    power_node = cmds.createNode("multiplyDivide", name=name)
    cmds.setAttr("%s.operation" %power_node, 3)
    for nmb, value in enumerate([a,b]):
        if compat.is_string(value):
            cmds.connectAttr(value, "%s.input%iX" %(power_node, nmb+1))
        else:
            cmds.setAttr("%s.input%iX" %(power_node, nmb+1), value)
    if return_plug:
        return "%s.outputX" %power_node
    else:
        return power_node

def invert(a, return_plug=True, name="invert"):
    return (multiply(a, -1, return_plug=return_plug, name=name))

def reverse(a, return_plug=True, name="reverse"):
    reverse_node = cmds.createNode("reverse", name=name)
    if compat.is_string(a):
        cmds.connectAttr(a, "%s.inputX" %reverse_node)
    else:
        cmds.setAttr("%s.inputX" %reverse_node, a)
    if return_plug:
        return "%s.outputX" %reverse_node
    else:
        return reverse_node

def if_else(first_term, operation, second_term, if_true, if_false, return_plug=True, name="condition"):
    operation_dict = {
        "==": 0,
        "!=": 1,
        ">": 2,
        ">=": 3,
        "<": 4,
        "<=": 5
    }
    if operation not in operation_dict.keys():
        cmds.error("Operation argument must be boolean operation. Valid values are : %s" %operation_dict.keys())
    condition_node = cmds.createNode("condition", name=name)
    cmds.setAttr("%s.operation" %condition_node, operation_dict.get(operation))
    if compat.is_string(first_term):
        cmds.connectAttr(first_term, "%s.firstTerm" %condition_node)
    else:
        cmds.setAttr("%s.firstTerm" %condition_node, first_term)

    if compat.is_string(second_term):
        cmds.connectAttr(second_term, "%s.secondTerm" %condition_node)
    else:
        cmds.setAttr("%s.secondTerm" %condition_node, second_term)

    if compat.is_string(if_true):
        cmds.connectAttr(if_true, "%s.colorIfTrueR" %condition_node)
    else:
        cmds.setAttr("%s.colorIfTrueR" %condition_node, if_true)

    if compat.is_string(if_false):
            cmds.connectAttr(if_false, "%s.colorIfFalseR" %condition_node)
    else:
        cmds.setAttr("%s.colorIfFalseR" %condition_node, if_false)

    if return_plug:
        return "%s.outColorR" %condition_node
    else:
        return condition_node