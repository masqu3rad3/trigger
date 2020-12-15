from maya import cmds
import maya.api.OpenMaya as om
import pdb

ACTION_DATA = {}

def get_closest_vert(mayaMesh, pos, threshold=0.001):
    # mVector = api.MVector(pos)#using MVector type to represent position
    selectionList = om.MSelectionList()
    selectionList.add(mayaMesh)
    dPath = selectionList.getDagPath(0)
    mMesh = om.MFnMesh(dPath)
    ID = mMesh.getClosestPoint(pos, om.MSpace.kWorld)[1]  # getting closest face ID\
    verts = mMesh.getPolygonVertices(ID)

    point_list = mMesh.getPoints(om.MSpace.kTransform)
    for vert_index in verts:
        if pos.distanceTo(point_list[vert_index]) < threshold:
            return vert_index
    return None


def select_intersections(nodeA, nodeB, threshold=0.001):
    # iMeshVerts = getAllVerts(nodeB)
    selectionLs_nodeB = om.MSelectionList()
    selectionLs_nodeB.add(nodeB)
    selObj = selectionLs_nodeB.getDagPath(0)
    mfnObject = om.MFnMesh(selObj)

    iMeshVerts = mfnObject.getPoints(om.MSpace.kWorld)

    nodeA_intersectList = [get_closest_vert(nodeA, i, threshold=threshold) for i in iMeshVerts]
    nodeA_intersectList = (filter(lambda a: a, nodeA_intersectList))  # filter out non-intersecting vertices

    selectionList = om.MSelectionList()
    selectionList.add(nodeA)
    dPath = selectionList.getDagPath(0)
    mfn_components = om.MFnSingleIndexedComponent()
    components = mfn_components.create(om.MFn.kMeshVertComponent)
    map(mfn_components.addElement, nodeA_intersectList)
    to_sel = om.MSelectionList()
    to_sel.add((dPath, components))
    om.MGlobal.setActiveSelectionList(to_sel)


def connect_face_to_body(face_mesh, body_mesh, method="wrap", name="connect_face"):
    if method == "wrap":
        select_intersections(body_mesh, face_mesh, threshold=0.001)
        cmds.select(face_mesh, add=True)
        cmds.CreateWrap()
        temp_name = cmds.listHistory(body_mesh, levels=1, pruneDagObjects=True)[0]
        cmds.setAttr("{0}.exclusiveBind".format(temp_name), 1)
        wrap_node = "wrap_{0}".format(name)
        cmds.rename(temp_name, "wrap_{0}".format(name))
        cmds.select(d=True)
    elif method == "proximity":
        cmds.select(body_mesh)
        cmds.ProximityWrap()
        node_history = cmds.listHistory(body_mesh)
        wrap_node = [node for node in node_history if cmds.objectType(node) == "proximityWrap"][0]
        wrap_node = cmds.rename(wrap_node, "proximity_wrap_{0}".format(name))
        # Copy the face mesh and make a orig intermediate obj
        face_mesh_shape = cmds.listRelatives(face_mesh, c=True, type="shape")[0]
        # check if there is another orig shape
        if not cmds.objExists("{0}Orig".format(face_mesh_shape)):
            temp = cmds.duplicate(face_mesh_shape)[0]
            orig_shape = cmds.listRelatives(temp, c=True, type="shape")[0]
            cmds.parent(orig_shape, face_mesh, r=True, shape=True)
            orig_shape = cmds.rename(orig_shape, "%sOrig" % face_mesh_shape)
            cmds.delete(temp)
            cmds.setAttr("{0}.intermediateObject".format(orig_shape), 1)
        else:
            orig_shape = "{0}Orig".format(face_mesh_shape)

        cmds.connectAttr("{0}.outMesh".format(face_mesh_shape), "{0}.drivers[0].driverGeometry".format(wrap_node))
        cmds.connectAttr("{0}.outMesh".format(orig_shape), "{0}.drivers[0].driverBindGeometry".format(wrap_node))

        cmds.setAttr("{0}.maxDrivers".format(wrap_node), 1)
        cmds.setAttr("{0}.falloffScale".format(wrap_node), 0.01)
        cmds.setAttr("{0}.smoothInfluences".format(wrap_node), 0)
        cmds.setAttr("{0}.smoothNormals".format(wrap_node), 0)
        cmds.setAttr("{0}.softNormalization".format(wrap_node), 0)
        cmds.setAttr("{0}.spanSamples".format(wrap_node), 1)

    # put everything under the first skin cluster (if there is any)_
    node_history = cmds.listHistory(body_mesh)
    skin_clusters = [node for node in node_history if cmds.objectType(node) == "skinCluster"]
    if skin_clusters:
        cmds.reorderDeformers(skin_clusters[-1], wrap_node, body_mesh)
    return wrap_node


# connect_face_to_body("face_msh", "body_msh", method="wrap")