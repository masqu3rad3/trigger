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

    def collect_deformers(self, mesh):
        """Collects defomers in a dictionary by type

        Args:
            mesh (str): Shape or transform node
        Return:
            dictionary: {<type>: [list of deformers]}

        """

        valid_deformers = ["skinCluster", "blendShape", "nonLinear", "cluster"]
        if int(cmds.about(version=True)) >= 2019:
            valid_deformers.append("ffd")
        # get deformer from mesh
        history = cmds.listHistory(mesh, pruneDagObjects=True)

        deformer_data = {deformer_type: cmds.ls(history, type=deformer_type, shapes=True) for deformer_type in valid_deformers}

        return deformer_data

    def save_weights(self, deformer=None, file_path=None, vertexConnections=False, force=True):
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
        return True

    def save_matching_weights(self, deformer=None, file_path=None, vertexConnections=False, force=True):
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

        state = self.save_weights(deformer=deformer, file_path=os.path.join(file_dir, file_name), vertexConnections=vertexConnections, force=force)
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
        copy_data = deepcopy(data_list[0])

        for json_data in data_list[1:]:
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
            for weights_cpy, weights_mlt in zip(weights_list, copy_data["deformerWeight"]["weights"]):
                print("=="*30)
                # print(copy_data["deformerWeight"]["weights"]["points"])
                # print("=="*30)
                # print(weights["points"])
                for vert_cpy, vert_mlt in zip(weights_cpy["points"], weights_mlt["points"]):
                    vert_cpy["value"] = vert_cpy["value"] * vert_mlt["value"]
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
    

