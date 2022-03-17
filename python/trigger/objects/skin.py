import uuid
import os
import copy
from maya import cmds
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as omanim
from trigger.library import api
from trigger.library import deformers
from trigger.core.io import IO

from trigger.core import filelog

log = filelog.Filelog(logname=__name__, filename="trigger_log")

class Weight(object):
    def __init__(self, source=None):
        super(Weight, self).__init__()
        self.temp_io = IO(file_name="trigger_temp_skin.json")
        self._data = None

        if source:
            self.feed(source)

    def feed(self, source):
        """provides the data that the class needs to work with.
        The source can be:
         - absolute json path (string) (valid weight formatted matching cmds.deformerWeights output))
         - dictionary item (matching cmds.deformerWeights output
         - skinCluster node (String) (must be present in the current maya scene)
         """
        if isinstance(source, dict):
            _data = source
        elif isinstance(source, str):
            if cmds.ls(source, type="skinCluster"):
                _data = self.__read_data_from_deformer(source)
            elif os.path.isfile(source):
                _data = self.__read_data_from_file(source)
            else:
                raise Exception("Source (%s) cannot identified neither as a file or skinCluster" % source)
        else:
            raise Exception("invalid source (%s). Must be dictionary, file or deformer")

        # TODO some data validation
        self._data = _data

    def export(self, file_path):
        """
        Exports the data to specified json file path

        """
        "TODO data validation?"
        IO().write(self._data, file_path)

    def apply(self, deformer):
        """Applies the data to specified deformer"""
        if not self._data:
            raise Exception("There is no data to apply")
        # TODO data validation?

        deformer = deformer or self._data["deformerWeight"]["deformers"][0]["name"]
        # get the active influences
        _influences = cmds.skinCluster(deformer, query=True, influence=True)
        _data_influences = self.get_all_influences()

        # add the missing ones / remove the excess
        _ = [cmds.skinCluster(deformer, edit=True, addInfluence=x, nw=0) for x in _data_influences if
             x not in _influences]
        _ = [cmds.skinCluster(deformer, edit=True, removeInfluence=x, nw=0) for x in _influences if
             x not in _data_influences]

        # temporarily turn off the normalization
        normalization = cmds.skinCluster(deformer, q=True, normalizeWeights=True)
        cmds.skinCluster(deformer, edit=True, normalizeWeights=0)

        geo = cmds.skinCluster(deformer, q=True, geometry=True)[0]
        # compare the vertex size and act accordingly if the topologies are different
        if len(api.getAllVerts(geo)) == self.get_vertex_count():
            # same topology
            self.__set_weights(deformer, geo, self.__convert_to_m_array(self._data))
            if cmds.skinCluster(deformer, q=True, skinMethod=True):
                self.__set_blend_weights(deformer, geo, om.MDoubleArray(self._data.get("DQ_weights", [])))
        else:
            # different topology
            # TODO try to figure out a more elegant way (and faster)
            # write the data to a temporary location and read it back using
            self.temp_io.write(self._data)
            # ... and apply it from there
            # first try barycentric if the data allows
            if self._check_vc():
                method = "bilinear"
            else:
                method = "nearest"
            _file_path, _file_name = os.path.split(self.temp_io.file_path)
            cmds.deformerWeights(_file_name, im=True, deformer=deformer, path=_file_path, method=method,
                                 ignoreName=True)
            os.remove(self.temp_io.file_path)

        # back to original normalization setting
        cmds.skinCluster(deformer, edit=True, normalizeWeights=normalization)

    def _check_vc(self):
        """Checks the data if vc (vertex connections) has or not"""
        poly_counts = self._data["deformerWeight"]["shapes"][0].get("polyCounts", None)
        poly_connects = self._data["deformerWeight"]["shapes"][0].get("polyConnects", None)

        if poly_counts and poly_connects:
            return True
        else:
            return False

    def validate(self):
        """validates data against the maya weight format standards"""
        if not self._data.get("deformerWeight", None):
            log.warning("skin.py => The weight data cannot be validated. key deformerWeight is missing")
            return False
        keys = ["headerInfo", "deformers", "shapes", "weights"]
        for key in keys:
            try:
                _d = self._data[key]
            except KeyError:
                log.warning("skin.py => The weight data cannot be validated. key %s is missing" %key)
                return False
        return True

    def get_vertex_count(self):
        """Finds and returns the vertex count from the _data"""
        return self._data.get("shapes", {}).get("size", None)

    def get_all_influences(self):
        """Returns the name of all influences the data contains"""
        return [x.get("source") for x in self._data["deformerWeight"]["weights"]]

    def __read_data_from_deformer(self, deformer):
        """Gets the weight dictionary from specified deformer"""
        # write the json file using maya thingie. Read it back and discard the temporary file
        # Specific attributes for skinClusters
        attributes = ["envelope", "skinningMethod", "useComponents", "normalizeWeights", "deformUserNormals"]
        _file_path, _file_name = os.path.split(self.temp_io.file_path)
        # cmds.deformerWeights(_file_name, export=True, deformer=deformer, path=_file_path, defaultValue=-1.0, vc=False, at=attributes)
        cmds.deformerWeights(_file_name, export=True, deformer=deformer, path=_file_path, vc=False, at=attributes)
        # cmds.deformerWeights(_file_name, export=True, deformer=deformer, path=_file_path, vc=False, at=attributes)

        # read it back
        _data = self.temp_io.read()
        os.remove(self.temp_io.file_path)
        # Check for the DQ blend weights and add it to the data dictionary if required
        if cmds.skinCluster(deformer, q=True, skinMethod=True):
            geo = cmds.skinCluster(deformer, q=True, geometry=True)[0]
            _data["DQ_weights"] = self.__get_blend_weights(deformer, geo)
        return _data

    def __read_data_from_file(self, path):
        """Gets the weight dictionary from specified file path"""
        return IO(file_path=path).read()

    def get_influence_data(self, influence_name):
        """searches the data dictionary and returns the related influence dictionary like
        Args:
            influence_name: name of the influence object

        The returned data is similar to this:
            {
                "deformer": "testCylinder_skinCluster",
                "source": "jDef_Collar_L_Arm",
                "shape": "testCylinder_Shape1",
                "layer": 0,
                "defaultValue": -1.0,
                "points": [
                    {
                        "index": 0,
                        "value": 0.9989053498388121
                    },
                    ...
                    ...
                "size": 4122,
                "max": 4121
            },

        returns: (dict) influence data (weights)

        """
        for weights in self._data["deformerWeight"]["weights"]:
            if weights["source"] == influence_name:
                return weights

    def remove_influence(self, influence_name):
        """Removes the given influence (weights) from the data"""

        for weights in self._data["deformerWeight"]["weights"]:
            if weights["source"] == influence_name:
                self._data["deformerWeight"]["weights"].remove(weights)

    def add_influence(self, influence_data, force=True):
        """
        Adds the influence to the data
        Args:
            influence_data: (dict) data dictionary which can be get with get_influence_data()
            force: (bool) If true, replaces the existing influence. Else an exception raises

        Returns: None

        """
        _influence_name = influence_data.get("source", None)
        if self.get_influence_data(_influence_name) and not force:
            raise Exception("Data already contains weights data for %s" % _influence_name)
        self._data["deformerWeight"]["weights"].append(influence_data)

    def negate(self, influences=None):
        """
        Negates the point weights

        Args:
            influences: (List) negates only given influences. If None negates all

        Returns:

        """
        weight_list = []
        if not influences:
            weight_list = self._data["deformerWeight"]["weights"]
        else:
            for weights in self._data["deformerWeight"]["weights"]:
                if weights["source"] in influences:
                    weight_list.append(weights)

        for weights in weight_list:
            for vert in weights["points"]:
                vert["value"] = 1 - vert["value"]

    @staticmethod
    def __convert_to_m_array(json_data):
        """Converts the json data weights compatible to be applied with MFnSkincluster"""
        vertex_count = json_data["deformerWeight"]["shapes"][0]["size"]
        weights_data = json_data["deformerWeight"]["weights"]
        m_array = om.MDoubleArray()
        # first create a base
        for vtx_id in range(vertex_count * len(weights_data)):
            m_array.append(0.0)
        # if there are 3 influences (jnt1, jnt2, jnt3):
        #  Vertex ID         vtx0   vtx1   vtx2   .....
        #  M Array           | | |  | | |  | | |  .....
        #  Influence (Layer) 1 2 3  1 2 3  1 2 3  .....
        inf_count = len(weights_data)
        for inf_data in weights_data:
            layer = inf_data.get("layer")
            for point_data in inf_data["points"]:
                data_index = (point_data["index"] * inf_count) + layer
                m_array[data_index] = point_data["value"]
                if point_data["value"] > 1.0:
                    print(point_data["value"])

        return m_array

    @staticmethod
    def __get_path_and_component(mesh, skincluster):
        """Convenience method to get mesh dag path, components and MFnSkinCluster from a given mesh and skincluster
        to be used setting and getting weights
        """
        vert_sel_list = om.MGlobal.getSelectionListByName(mesh)
        mesh_path = vert_sel_list.getDagPath(0)
        mesh_node = mesh_path.node()
        mesh_ver_it_fn = om.MItMeshVertex(mesh_node)
        indices = range(mesh_ver_it_fn.count())
        single_id_comp = om.MFnSingleIndexedComponent()
        vertex_comp = single_id_comp.create(om.MFn.kMeshVertComponent)
        single_id_comp.addElements(indices)

        sel_list = om.MGlobal.getSelectionListByName(skincluster)
        skin_fn = omanim.MFnSkinCluster(sel_list.getDependNode(0))
        return mesh_path, vertex_comp, skin_fn

    def __get_weights(self, skincluster, mesh):
        """
        Gets the weights fast usin API 2.0

        Args:
            skincluster: (String) skincluster deformer from the current scene
            mesh: (String) mesh shape name from the scene

        Returns:
            <MDoubleArray> of skin weights

        """
        mesh_path, vertex_comp, skin_fn = self.__get_path_and_component(mesh, skincluster)
        return skin_fn.getWeights(mesh_path, vertex_comp)

    def __set_weights(self, skincluster, mesh, m_array):
        """
        Sets the weights really fast using API 2.0

        Args:
            skincluster: (String) skincluster deformer from the current scene
            mesh: (String) mesh shape name from the scene
            m_array: (MDoubleArray) Array of weights data

        Returns:
            None
        """
        # https://gist.github.com/utatsuya/a95afe3c5523ab61e61b
        mesh_path, vertex_comp, skin_fn = self.__get_path_and_component(mesh, skincluster)

        inf_dags = skin_fn.influenceObjects()
        inf_indexes = om.MIntArray(len(inf_dags), 0)
        for x in range(len(inf_dags)):
            inf_indexes[x] = int(skin_fn.indexForInfluenceObject(inf_dags[x]))

        skin_fn.setWeights(mesh_path, vertex_comp, inf_indexes, m_array, True)

    def __get_blend_weights(self, skincluster, mesh):
        """
        Gets the DQ blend weights fast usin API 2.0

        Args:
            skincluster: (String) skincluster deformer from the current scene
            mesh: (String) mesh shape name from the scene

        Returns:
            <MDoubleArray> of DQ blend weights

        """
        mesh_path, vertex_comp, skin_fn = self.__get_path_and_component(mesh, skincluster)
        return skin_fn.getBlendWeights(mesh_path, vertex_comp)

    def __set_blend_weights(self, skincluster, mesh, m_array):
        """
        Sets the DQ blend weights really fast using API 2.0

        Args:
            skincluster: (String) skincluster deformer from the current scene
            mesh: (String) mesh shape name from the scene
            m_array: (MDoubleArray) Array of weights data

        Returns:
            None
        """
        mesh_path, vertex_comp, skin_fn = self.__get_path_and_component(mesh, skincluster)
        skin_fn.setBlendWeights(mesh_path, vertex_comp, m_array)

    def test_get_weights(self, skincluster, mesh):
        return self.__get_weights(skincluster, mesh)

    def test_set_weights(self, skincluster, mesh, m_array):
        self.__set_weights(skincluster, mesh, m_array)

    def test_get_blend_weights(self, skincluster, mesh):
        return self.__get_blend_weights(skincluster, mesh)

    def test_set_blend_weights(self, skincluster, mesh, m_array):
        self.__set_blend_weights(skincluster, mesh, m_array)

