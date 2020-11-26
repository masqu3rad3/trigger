"""Methods that use Maya Api"""

import maya.api.OpenMaya as om
from maya import cmds

def getMDagPath(node):
    """Returns the API 2.0 dagPath of given Node"""
    selList = om.MSelectionList()
    selList.add(node)
    return selList.getDagPath(0)

def getWorldTranslation(node):
    """Returns given nodes world translation of rotate pivot"""
    targetMTransform = om.MFnTransform(getMDagPath(node))
    targetRotatePivot = om.MVector(targetMTransform.rotatePivot(om.MSpace.kWorld))
    return targetRotatePivot

def getBetweenVector(node, targetPointNodeList):
    """
    Gets the between vector between the source node and target node list
    Args:
        node: (String) source node
        targetPointNodeList: (List) Target nodes

    Returns: MVector

    """
    nodePos = getWorldTranslation(node)
    sumVectors = om.MVector(0,0,0)
    for point in targetPointNodeList:
        pVector = getWorldTranslation(point)
        addVector = om.MVector(om.MVector(nodePos)-om.MVector(pVector)).normal()
        sumVectors += addVector
    return sumVectors.normal()