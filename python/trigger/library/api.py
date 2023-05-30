"""Methods that use Maya Api"""

from maya.api import OpenMaya


def get_all_vertices(mesh_transform):
    """Return all vertices of given mesh"""

    selection_ls = OpenMaya.MSelectionList()
    selection_ls.add(mesh_transform)
    sel_obj = selection_ls.getDagPath(0)

    mfn_object = OpenMaya.MFnMesh(sel_obj)
    return mfn_object.getPoints(OpenMaya.MSpace.kWorld)


def get_mdag_path(node):
    """Return the API 2.0 dagPath of given node."""
    sel_list = OpenMaya.MSelectionList()
    sel_list.add(node)
    return sel_list.getDagPath(0)


def get_world_translation(node):
    """Return given nodes world translation of rotate pivot."""
    target_m_transform = OpenMaya.MFnTransform(get_mdag_path(node))
    target_rotate_pivot = OpenMaya.MVector(
        target_m_transform.rotatePivot(OpenMaya.MSpace.kWorld))
    return target_rotate_pivot


def get_between_vector(node, target_point_list):
    """
    Get the between vector between the source node and target node list.
    Args:
        node: (String) source node
        target_point_list: (List) Target nodes

    Returns: MVector

    """
    node_pos = get_world_translation(node)
    sum_vectors = OpenMaya.MVector(0, 0, 0)
    for point in target_point_list:
        p_vector = get_world_translation(point)
        add_vector = OpenMaya.MVector(
            OpenMaya.MVector(node_pos) - OpenMaya.MVector(p_vector)
        ).normal()
        sum_vectors += add_vector
    return sum_vectors.normal()


def get_center(node_list):
    """Return the center world position of the given nodes."""
    p_sum = OpenMaya.MVector(0, 0, 0)
    for x in node_list:
        p_sum += get_world_translation(x)
    return p_sum / len(node_list)


def select_vertices(mesh, id_list):
    """Selects vertices of the mesh with given id list"""
    sel = OpenMaya.MSelectionList()
    sel.add(mesh)
    dag, mObject = sel.getComponent(0)
    mfn_components = OpenMaya.MFnSingleIndexedComponent(mObject)
    mfn_object = mfn_components.create(OpenMaya.MFn.kMeshVertComponent)
    mfn_components.addElements(id_list)
    selection_list = OpenMaya.MSelectionList()
    selection_list.add((dag, mfn_object))
    OpenMaya.MGlobal.setActiveSelectionList(selection_list)

def unlock_normals(transform, soften=False):
    """Unlock the normals of the specified geometry.

    Args:
        geometries (str or list): string or list of strings for the geometries
            to unlock.
        soften (bool, optional): If true, softens the edges with given
            softedge_angle value. Defaults to True.
    """

    # Retrieve the MFnMesh api object.
    selection_list = OpenMaya.MSelectionList()
    selection_list.add(transform)
    mfn_mesh = OpenMaya.MFnMesh(selection_list.getDagPath(0))
    # if its already unlocked, do not process again.
    lock_state = any(
        mfn_mesh.isNormalLocked(normal_index)
        for normal_index in range(mfn_mesh.numNormals)
    )
    if lock_state:
        mfn_mesh.unlockVertexNormals(
            OpenMaya.MIntArray(range(mfn_mesh.numVertices))
        )
    if soften:
        edge_ids = OpenMaya.MIntArray(range(mfn_mesh.numEdges))
        smooths = OpenMaya.MIntArray([True] * mfn_mesh.numEdges)
        mfn_mesh.setEdgeSmoothings(edge_ids, smooths)
        mfn_mesh.cleanupEdgeSmoothing()
        mfn_mesh.updateSurface()

