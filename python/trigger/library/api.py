"""Methods that use Maya Api"""

import maya.api.OpenMaya as om
from maya import cmds

def getAllVerts(node):
    """
    Using Maya Python API 2.0
    """

    selectionLs = om.MSelectionList()
    selectionLs.add(node)
    selObj = selectionLs.getDagPath(0)

    # ___________Query vertex position ___________
    # create a Mesh functionset from our dag object
    mfnObject = om.MFnMesh(selObj)

    return mfnObject.getPoints(om.MSpace.kWorld)

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

def getCenter(node_list):
    "returns the center world position of the given nodes"
    p_sum = om.MVector(0,0,0)
    for x in node_list:
        p_sum += getWorldTranslation(x)
    return p_sum / len(node_list)

def select_vertices(mesh, id_list):
    """Selects vertices of the mesh with given id list"""
    sel = om.MSelectionList()
    sel.add(mesh)
    dag, mObject = sel.getComponent(0)
    mfn_components = om.MFnSingleIndexedComponent(mObject)
    mfn_object = mfn_components.create(om.MFn.kMeshVertComponent)
    mfn_components.addElements(id_list)
    selection_list = om.MSelectionList()
    selection_list.add((dag, mfn_object))
    om.MGlobal.setActiveSelectionList(selection_list)

