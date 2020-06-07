import os
from copy import deepcopy
from maya import cmds
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as omAnim

from trigger.core import io
from trigger.core import feedback

import time
from pprint import pprint

FEEDBACK = feedback.Feedback(__name__)

ACTION_DATA = {}


def multiplyList(list_of_values):
    # Multiply elements one by one
    result = 1
    for x in list_of_values:
        result = result * x
    return result

def addList(list_of_values):
    result = 0
    for x in list_of_values:
        result += x
    return result

def subractList(list_of_values):
    result = list_of_values[0]
    for x in list_of_values[1:]:
        result += x
    return result

class Weights(dict):
    def __init__(self, *args, **kwargs):
        super(Weights, self).__init__()
        self.io = io.IO(file_name="tmp_weights.json")
        self["deformer"] = None

    @property
    def deformer(self):
        return self["deformer"]

    @deformer.setter
    def deformer(self, obj_name):
        if cmds.objExists(obj_name):
            self["deformer"] = obj_name
        else:
            FEEDBACK.warning("The specified object does not exists")
            return

    def set_path(self, file_path):
        self.io.file_path = file_path

    def action(self):
        """Mandatory method for all action modules"""
        pass

    # def collect_deformers(self, mesh):
    #     """Collects defomers in a dictionary by type
    #
    #     Args:
    #         mesh (str): Shape or transform node
    #     Return:
    #         dictionary: {<type>: [list of deformers]}
    #
    #     """
    #
    #     valid_deformers = ["skinCluster", "blendShape", "nonLinear", "cluster"]
    #     if int(cmds.about(version=True)) >= 2019:
    #         valid_deformers.append("ffd")
    #     # get deformer from mesh
    #     history = cmds.listHistory(mesh, pruneDagObjects=True)
    #
    #     deformer_data = {deformer_type: cmds.ls(history, type=deformer_type, shapes=True) for deformer_type in valid_deformers}
    #
    #     return deformer_data

    def save_weights(self, deformer=None, file_path=None, vertexConnections=False, force=True, influencer=None):
        if not deformer and not self.deformer:
            FEEDBACK.throw_error("No Deformer defined. A Deformer needs to be defined either as argument or class variable)")
        if not deformer:
            deformer = self.deformer
        if not force:
            if os.path.isfile(file_path):
                FEEDBACK.warning("This file already exists. Skipping")
                return False
        # Vertex connections is required for barycentric and bilinear modes when loading
        if not file_path:
            file_dir, file_name = os.path.split(self.io.file_path)
        else:
            file_dir, file_name = os.path.split(file_path)
        # default value -1 means export all weights!
        cmds.deformerWeights(file_name, export=True, deformer=deformer, path=file_dir, defaultValue=-1.0, vc=vertexConnections)

        # there is no argument to define the influencer while exporting.
        # If a specific influencer needs to be exported, strip the rest after the file exported.
        if influencer:
            # read the exported data
            self.io.file_path = os.path.join(file_dir, file_name)
            data = self.io.read()
            operation_data = deepcopy(data)
            # do the surgery
            for weight_data_dict in data["deformerWeight"]["weights"]:
                if weight_data_dict["source"] != influencer:
                    operation_data["deformerWeight"]["weights"].remove(weight_data_dict)
            operation_data["deformerWeight"]["weights"][0]["layer"] = 0
            self.io.write(operation_data)

        FEEDBACK.info("File exported to %s successfully..." % os.path.join(file_dir, file_name))
        return True

    def load_weights(self, deformer=None, file_path=None, method="index", ignore_name=True):
        if not deformer and not self.deformer:
            FEEDBACK.throw_error(
                "No Deformer defined. A Deformer needs to be defined either as argument or class variable)")
        if not deformer:
            deformer = self.deformer

        if not file_path:
            file_dir, file_name = os.path.split(self.io.file_path)
        else:
            file_dir, file_name = os.path.split(file_path)

        cmds.deformerWeights(file_name, im=True, deformer=deformer, path=file_dir, method=method, ignoreName=ignore_name)

        # this is a bug I came across one with one test geo.
        # Somehow it does not assign the value to index: 0
        # the following part forces to assign the correct value to index 0
        self.io.file_path = os.path.join(file_dir, file_name)
        data = self.io.read()
        for nmb, weight_dict in enumerate(data["deformerWeight"]["weights"]):
            index0_val = weight_dict["points"][0]["value"]
            cmds.setAttr("%s.inputTarget[0].inputTargetGroup[%i].targetWeights[0]" % (deformer, nmb), index0_val)
            # splitMaps_blendshape.inputTarget[0].inputTargetGroup[X].targetWeights[0]
        return True

    def save_matching_weights(self, deformer=None, file_path=None, vertexConnections=False, force=True, influencer=None):
        """
        Saves the weights AND the negated weights to the disk
        Args:
            deformer: Deformer node. If not specified, it will try to use the class variable.
            file_path: (String) Absolute File path. If not defined the class variable will be used
            vertexConnections: (Bool) defines whether or not to define Vertex Connections in the file. Required for Barycentric
            and Bilinear methods while loading

        Returns: (list) file locations for normal and negated weights

        """
        if not file_path:
            file_dir, file_name = os.path.split(self.io.file_path)
        else:
            file_dir, file_name = os.path.split(file_path)

        state = self.save_weights(deformer=deformer, file_path=os.path.join(file_dir, file_name), vertexConnections=vertexConnections, force=force, influencer=influencer)
        if not state:
            return

        name, extension = os.path.splitext(file_name)
        f_path = os.path.join(file_dir, extension)
        cmds.refresh()
        positive_weights_path = os.path.join(file_dir, file_name)
        temp_io= io.IO(file_path=positive_weights_path)
        to_be_negated = temp_io.read()
        negative_weights_path = "%sN%s" % (os.path.join(file_dir, name), extension)
        temp_io.file_path = negative_weights_path
        negated_weights = self.negateWeights(to_be_negated)
        temp_io.write(negated_weights)
        return (positive_weights_path, negative_weights_path)


    def negateWeights(self, json_data, influencer=None):
        """Negates the weights in json_data"""

        weights_list = None
        if not influencer:
            weights_list = json_data["deformerWeight"]["weights"]
        else:
            # find the influencer weights:
            for weights in json_data["deformerWeight"]["weights"]:
                if weights["source"] == influencer:
                    weights_list = [weights]
        if not weights_list:
            print("Cannot find the influencer")
            return
        for weights in weights_list:
            # weights["defaultValue"] = 1-weights["defaultValue"]
            for vert in weights["points"]:
                vert["value"]=1-vert["value"]
        return json_data

    def multiplyWeights(self, data_list, influencer=None):
        """Multiplies the weights in the data list"""
        # take a copy of the first data list
        copy_data = deepcopy(data_list[0])
        # the json_datas in data_list must belong to the same deformer (same point count)
        for weights_list_nmb, weights in enumerate(copy_data["deformerWeight"]["weights"]):
            if influencer and weights["source"] != influencer:
                continue
            for point_nmb, point in enumerate(weights["points"]):
                point_values = []
                for data_list_nmb, json_data in enumerate(data_list):
                    val = json_data["deformerWeight"]["weights"][weights_list_nmb]["points"][point_nmb]["value"]
                    point_values.append(val)
                point["value"] = multiplyList(point_values)
        return copy_data

    def addWeights(self, data_list, influencer=None, clamp=True):
        # TODO : not tested
        copy_data = deepcopy(data_list[0])
        for weights_list_nmb, weights in enumerate(copy_data["deformerWeight"]["weights"]):
            if influencer and weights["source"] != influencer:
                continue
            for point_nmb, point in enumerate(weights["points"]):
                point_values = []
                for data_list_nmb, json_data in enumerate(data_list):
                    val = json_data["deformerWeight"]["weights"][weights_list_nmb]["points"][point_nmb]["value"]
                    point_values.append(val)
                point["value"] = addList(point_values)
                if clamp:
                    point["value"] = max(min(point["value"], 1.0), 0.0)
        return copy_data

    def subtractWeights(self, data_list, influencer=None, clamp=True):
        # TODO : not tested
        copy_data = deepcopy(data_list[0])
        for weights_list_nmb, weights in enumerate(copy_data["deformerWeight"]["weights"]):
            if influencer and weights["source"] != influencer:
                continue
            for point_nmb, point in enumerate(weights["points"]):
                point_values = []
                for data_list_nmb, json_data in enumerate(data_list):
                    val = json_data["deformerWeight"]["weights"][weights_list_nmb]["points"][point_nmb]["value"]
                    point_values.append(val)
                point["value"] = subtractList(point_values)
                if clamp:
                    point["value"] = max(min(point["value"], 1.0), 0.0)
        return copy_data


def get_plug_ids(mesh, source_deformer, source_influence=None):
    node_type = cmds.nodeType(source_deformer)

    # target_num = 0
    if node_type == "blendShape":
        if source_influence == "baseWeights":
            weight_plug = "{}.inputTarget[0].baseWeights"
        else:
            targets = cmds.aliasAttr(source_deformer, query=True)
            target_names = targets[::2]
            target_weight = targets[1::2]
            target_index = target_names.index(source_influence)
            target_num = (target_weight[target_index].split("[")[1].split("]")[0])
            weight_plug = "{}.inputTarget[0].inputTargetGroup[%s].targetWeights" %str(target_num)
    elif node_type == "nonLinear" or node_type == "cluster":
        weight_plug = "{}.weightList[0].weights"
    elif node_type == "skinCluster":
        weight_plug = "{0}.weightList[0].weights"
    else:
        raise Exception ("deformer not identified => %s" %source_deformer)

    sel = om.MSelectionList()
    sel.add(weight_plug.format(source_deformer))
    plug = sel.getPlug(0)

    vtx_count = cmds.polyEvaluate(mesh, vertex=True)
    return plug, vtx_count




def get_influence_weights(mesh, deformer, influence, skip_checks=False):
    """Gets the weights for given influence object

    Args:
        mesh (str): Shape or transform Node
        deformer (str): Source deformer
        influence (str): Influence object

    Returns:
        list: [<list of weights for given influence>]

    """
    node_type = cmds.nodeType(deformer)
    if not skip_checks:
        if not cmds.objExists(mesh):
            msg = "{0} => does not exists".format(mesh)
            cmds.error(msg)
        # fool proof for non-mathcing mesh/deformers
        all_deformers = collect_deformers(mesh)

        if deformer not in all_deformers[node_type]:
            msg = "{0} either does not exist or not deforming {1}".format(deformer, mesh)
            cmds.error(msg)

    if node_type == "skinCluster":
        # get nodes
        node_dag = (
            om.MSelectionList().add(mesh).getDagPath(0).extendToShape()
        )
        skin_cluster_obj = (
            om.MSelectionList().add(deformer).getDependNode(0)
        )
        mfn_skc = omAnim.MFnSkinCluster(skin_cluster_obj)

        components = om.MFnSingleIndexedComponent().create(
            om.MFn.kMeshVertComponent
        )

        # get influence index
        skin_cluster_obj = (om.MSelectionList().add(deformer).getDependNode(0))
        influence_dag = om.MSelectionList().add(influence).getDagPath(0)
        index = int(omAnim.MFnSkinCluster(skin_cluster_obj).indexForInfluenceObject(influence_dag))

        # Get weights
        weights = mfn_skc.getWeights(node_dag, components, om.MIntArray([index]))

        return list(weights)

    if node_type == "nonLinear" or node_type == "cluster":
        influence = None # these deformers dont have seperate influencers

    plug, vtx_count = get_plug_ids(mesh, deformer, influence)

    weights = [plug.elementByLogicalIndex(i).asDouble() for i in range(vtx_count)]
    return weights


def get_all_weights(mesh, deformer):
    """Collects the weight data for the given deformer
    
    Args:
        mesh (str): Shape or transform Node
        deformer (str): Source deformer

    Returns:
        dictionary: {<influence>: [weights_list]}

    """
    # TODO : complete the function or merge with "get_imfluence_weights"
    node_type = cmds.nodeType(deformer)
    if node_type == "skinCluster":
        pass

    if node_type == "nonLinear" or node_type == "cluster":
        # these have only single influences
        weight_dictionary = {"baseWeights": get_influence_weights(mesh, deformer, None, skip_checks=True)}
        pass
    if node_type == "blendShape":
        # pass
        # get all the influences
        all_influences = ["baseWeights"]
        all_influences.extend(cmds.aliasAttr(deformer, query=True)[::2])
        weight_dictionary = {influence: get_influence_weights(mesh, deformer, influence, skip_checks=True) for influence in all_influences}

    return weight_dictionary

#########################################################################
#########################################################################
#########################################################################
#########################################################################
#########################################################################
#########################################################################

def get_skincluster_influence_index(skin_cluster, influence):
    """Get the index of given influence.

    Args:
        skin_cluster (str): skinCluster node
        influence (str): influence object

    Return:
        int: index
    """
    skin_cluster_obj = (
        OpenMaya.MSelectionList().add(skin_cluster).getDependNode(0)
    )
    influence_dag = OpenMaya.MSelectionList().add(influence).getDagPath(0)
    index = int(
        OpenMayaAnim.MFnSkinCluster(
            skin_cluster_obj
        ).indexForInfluenceObject(influence_dag)
    )

    return index


def set_deformer_weights(mesh, target_deformer, list_of_weights, target_influence, data_type="double"):
    plug, vtx_count = get_plug_ids(mesh, target_deformer, target_influence)

    if data_type == "double":
        # TODO: map function with LAMBDA may be slower than for loop
        # or list comprehension. Test it
        map(
            lambda i: plug.elementByLogicalIndex(i).setDouble(
                list_of_weights[i]
            ),
            range(len(list_of_weights)),
        )
    elif data_type == "float":
        map(
            lambda i: plug.elementByLogicalIndex(i).setFloat(
                list_of_weights[i]
            ),
            range(len(list_of_weights)),
        )

    return list_of_weights

def get_deformer_weights(mesh, source_deformer, source_influence=None, data_type="double"):
    node_type = cmds.nodeType(source_deformer)
    if node_type == "skinCluster":
        # get nodes
        node_dag = (
            om.MSelectionList().add(mesh).getDagPath(0).extendToShape()
        )
        skin_cluster_obj = (
            om.MSelectionList().add(source_deformer).getDependNode(0)
        )
        mfn_skc = omAnim.MFnSkinCluster(skin_cluster_obj)

        components = om.MFnSingleIndexedComponent().create(
            om.MFn.kMeshVertComponent
        )

        # get influence index
        skin_cluster_obj = (om.MSelectionList().add(source_deformer).getDependNode(0))
        influence_dag = om.MSelectionList().add(source_influence).getDagPath(0)
        index = int(omAnim.MFnSkinCluster(skin_cluster_obj).indexForInfluenceObject(influence_dag))
            
        # Get weights
        weights = mfn_skc.getWeights(node_dag, components, om.MIntArray([index]))
        
        return list(weights)

    plug, vtx_count = get_plug_ids(mesh, source_deformer, source_influence)

    # reading
    if data_type == "double":
        weight_list = [
            plug.elementByLogicalIndex(i).asDouble()
            for i in range(vtx_count)
        ]
    elif data_type == "float":
        weight_list = [
            plug.elementByLogicalIndex(i).asFloat()   
            for i in range(vtx_count)
        ]

    return weight_list
    

