from maya import cmds
import maya.api.OpenMaya as api
import maya.api.OpenMayaAnim as apiAnim
import time
from pprint import pprint

ACTION_DATA = {}


def get_skincluster_influence_index(skin_cluster, influence):
    """Get the index of given influence.

    Args:
        skin_cluster (str): skinCluster node
        influence (str): influence object

    Return:
        int: index
    """
    skin_cluster_obj = OpenMaya.MSelectionList().add(skin_cluster).getDependNode(0)
    influence_dag = OpenMaya.MSelectionList().add(influence).getDagPath(0)
    index = int(
        OpenMayaAnim.MFnSkinCluster(skin_cluster_obj).indexForInfluenceObject(
            influence_dag
        )
    )

    return index


def get_plug_ids(mesh, source_deformer, source_influence=None):
    node_type = cmds.nodeType(source_deformer)

    target_num = 0
    if node_type == "blendShape":
        targets = cmds.aliasAttr(source_deformer, query=True)
        target_names = targets[::2]
        target_weight = targets[1::2]
        target_index = target_names.index(source_influence)
        target_num = target_weight[target_index].split("[")[1].split("]")[0]

    weight_plug = {
        "blendShape": "{}.inputTarget[0].inputTargetGroup["
        + str(target_num)
        + "].targetWeights",
        "nonLinear": "{}.weightList[0].weights",
        "cluster": "{}.weightList[0].weights",
        "skinCluster": "{0}.weightList[1].weights",
    }

    sel = api.MSelectionList()
    print("DB", node_type)
    sel.add(weight_plug[node_type].format(source_deformer))
    plug = sel.getPlug(0)

    vtx_count = cmds.polyEvaluate(mesh, vertex=True)
    return plug, vtx_count

    # ids = plug.getExistingArrayAttributeIndices()  # this may not safe
    # return plug, len(ids)


def set_deformer_weights(
    mesh, target_deformer, list_of_weights, target_influence, data_type="double"
):
    plug, vtx_count = get_plug_ids(mesh, target_deformer, target_influence)

    if data_type == "double":
        # TODO: map function with LAMBDA may be slower than for loop
        # or list comprehension. Test it
        map(
            lambda i: plug.elementByLogicalIndex(i).setDouble(list_of_weights[i]),
            range(len(list_of_weights)),
        )
    elif data_type == "float":
        map(
            lambda i: plug.elementByLogicalIndex(i).setFloat(list_of_weights[i]),
            range(len(list_of_weights)),
        )

    return list_of_weights


def get_deformer_weights(
    mesh, source_deformer, source_influence=None, data_type="double"
):
    node_type = cmds.nodeType(source_deformer)
    if node_type == "skinCluster":
        # get nodes
        node_dag = api.MSelectionList().add(mesh).getDagPath(0).extendToShape()
        skin_cluster_obj = api.MSelectionList().add(source_deformer).getDependNode(0)
        mfn_skc = apiAnim.MFnSkinCluster(skin_cluster_obj)

        components = api.MFnSingleIndexedComponent().create(api.MFn.kMeshVertComponent)

        # get influence index
        skin_cluster_obj = api.MSelectionList().add(source_deformer).getDependNode(0)
        influence_dag = api.MSelectionList().add(source_influence).getDagPath(0)
        index = int(
            apiAnim.MFnSkinCluster(skin_cluster_obj).indexForInfluenceObject(
                influence_dag
            )
        )

        # Get weights
        weights = mfn_skc.getWeights(node_dag, components, api.MIntArray([index]))

        return list(weights)

    plug, vtx_count = get_plug_ids(mesh, source_deformer, source_influence)

    # reading
    if data_type == "double":
        weight_list = [
            plug.elementByLogicalIndex(i).asDouble() for i in range(vtx_count)
        ]
    elif data_type == "float":
        weight_list = [
            plug.elementByLogicalIndex(i).asFloat() for i in range(vtx_count)
        ]

    return weight_list


# start = time.time()
# test_skinCluster = get_deformer_weights("base_msh", "blendShape1", source_influence="baseWeights")
# # test_skinCluster = get_deformer_weights("base_msh", "bend1")
# # test_skinCluster = get_deformer_weights("base_msh", "skinCluster1", source_influence="joint5")
# end = time.time()
# print end-start
# pprint(test_skinCluster)
