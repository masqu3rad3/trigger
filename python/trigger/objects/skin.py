import time
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


def clamp(num, min_value=0, max_value=1):
    return max(min(num, max_value), min_value)

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


def subtractList(list_of_values):
    result = list_of_values[0]
    for x in list_of_values[1:]:
        result += x
    return result

class Weight(object):
    def __init__(self, source=None):
        super(Weight, self).__init__()
        self.temp_io = IO(file_name="trigger_temp_skin.json")
        self._is_temp_dirty = True
        self._data = None

        if source:
            self.feed(source)

    @property
    def is_temp_dirty(self):
        """Checks the temp file and dirty flag and returns True if the temp file requires recreated or not"""
        if self._is_temp_dirty or not os.path.exists(self.temp_io.file_path):
            return True
        else:
            return False

    @is_temp_dirty.setter
    def is_temp_dirty(self, state):
        self._is_temp_dirty = state

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
            if os.path.isfile(source):
                _data = self.__read_data_from_file(source)
            elif cmds.ls(source, type="skinCluster"):
                _data = self.__read_data_from_deformer(source)
            else:
                raise Exception("Source (%s) cannot identified neither as a file or skinCluster" % source)
        else:
            raise Exception("invalid source (%s). Must be dictionary, file or deformer")

        if self.validate(_data):
            self._data = _data
        else:
            log.error("Data is corrupted")
            raise

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

        # # temporarily turn off the normalization
        # normalization = cmds.skinCluster(deformer, q=True, normalizeWeights=True)
        # cmds.skinCluster(deformer, edit=True, normalizeWeights=0)

        geo = cmds.skinCluster(deformer, q=True, geometry=True)[0]
        # compare the vertex size and act accordingly if the topologies are different
        if len(api.getAllVerts(geo)) == self.get_vertex_count():
            # same topology
            self.__set_weights(deformer, geo, self.__convert_to_m_array(self._data))
            if cmds.skinCluster(deformer, q=True, skinMethod=True):
                self.__set_blend_weights(deformer, geo, om.MDoubleArray(self._data.get("DQ_weights", [])))
        else:
            log.warning("Applying the values to different topologies is WIP")
            # different topology
            # Although writing data out and reading it back is not elegant, it is the easiest (and fastest atm)
            # Otherwise it requires some heavy barycentric calculations using maya.api. The better workaround
            # would be a custom python/C++ plugin for this purpose
            # write the data to a temporary location and read it back using
            # self.temp_io.write(self._data)
            # ... and apply it from there
            # first try barycentric if the data allows

            # TODO figure out a way get barycentric and/or bilinear values on different topos
            # TODO deformerWeighst => JSON does not support it and XML tends to crash a lot (and slower)
            # TODO It would be better and probably faster if can be done a conversion and apply __set_weights
            # if self._check_vc():
            #     method = "bilinear"
            # else:
            #     log.warning("There are no vertex connections provided with the weights file. Using 'nearest' method"
            #                 "instead of 'barycentric' to apply the weights")
            #     method = "nearest"

            method = "nearest"

            # TODO it turned out even the nearest method is not working with deformerWeights JSON implementation.
            # TODO json is still fast and good for read/write. We need to figure out to convert the data or come up
            # TODO with our implementation
            # _file_path, _file_name = os.path.split(self.temp_io.file_path)
            # cmds.deformerWeights(_file_name, im=True, deformer=deformer, path=_file_path, method=method,
            #                      ignoreName=True)
            # os.remove(self.temp_io.file_path)

        # back to original normalization setting
        # cmds.skinCluster(deformer, edit=True, normalizeWeights=normalization)

    def _check_vc(self):
        """Checks the data if vc (vertex connections) has or not"""
        # TODO test if its getting much faster when you query only the keys, not the values
        poly_counts = self._data["deformerWeight"]["shapes"][0].get("polygonCounts", None)
        poly_connects = self._data["deformerWeight"]["shapes"][0].get("polygonConnects", None)

        if poly_counts and poly_connects:
            return True
        else:
            return False

    def validate(self, data=None):
        """validates data against the maya weight format standards"""
        _data = data or self._data
        if not _data.get("deformerWeight", None):
            log.warning("skin.py => The weight data cannot be validated. key deformerWeight is missing")
            return False
        keys = ["headerInfo", "deformers", "shapes", "weights"]
        for key in keys:
            try:
                _d = _data["deformerWeight"][key]
            except KeyError:
                log.warning("skin.py => The weight data cannot be validated. key %s is missing" % key)
                return False
        return True

    def get_vertex_count(self):
        """Finds and returns the vertex count from the _data"""
        return self._data["deformerWeight"]["shapes"][0].get("size", None)

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
        cmds.deformerWeights(_file_name, export=True, deformer=deformer, path=_file_path, vc=True, at=attributes)
        # cmds.deformerWeights(_file_name, export=True, deformer=deformer, path=_file_path, vc=False, at=attributes)

        # read it back
        _data = self.temp_io.read()
        os.remove(self.temp_io.file_path)
        # Check for the DQ blend weights and add it to the data dictionary if required
        if cmds.skinCluster(deformer, q=True, skinMethod=True):
            geo = cmds.skinCluster(deformer, q=True, geometry=True)[0]
            _data["DQ_weights"] = list(self.__get_blend_weights(deformer, geo))
        return _data

    def __read_data_from_file(self, path):
        """Gets the weight dictionary from specified file path"""
        return IO(file_path=path).read()

    def __points_to_dict(self, points_data):
        """Converts hard to calculate point data in json file to easy to iterate dictionary"""
        _dict_data = {}
        for x in points_data:
            _dict_data[x["index"]] = x["value"]
        return _dict_data

    def __dict_to_points(self, dict_data):
        """Converts back the dict data to maya weights JSON compatible point data"""
        points_list = []
        for index, value in dict_data.items():
            points_list.append({"index": index, "value": value})
        return points_list


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

    def _get_last_layer(self):
        _layers = []
        for weights in self._data["deformerWeight"]["weights"]:
            _layers.append(weights.get("layer", 0))
        return max(_layers)

    def add_influence(self, influence_data, force=True, normalize_other_influences=True):
        """
        Adds the influence to the data
        Args:
            influence_data: (dict) data dictionary which can be get with get_influence_data()
            force: (bool) If true, replaces the existing influence. Else an exception raises

        Returns: None

        """
        if normalize_other_influences:
            self._clamp_point_weights(influence_data)
        start = time.time()
        _influence_name = influence_data.get("source", None)
        if self.get_influence_data(_influence_name) and not force:
            raise Exception("Data already contains weights data for %s" % _influence_name)
        # match the deformer and shape
        _deformer = self._data["deformerWeight"]["deformers"][0]["name"]
        _shape = self._data["deformerWeight"]["shapes"][0]["name"]
        influence_data["deformer"] = _deformer
        influence_data["shape"] = _shape
        influence_data["layer"] = self._get_last_layer()+1
        print("afer normalization: %s" %str(time.time() - start))

        s_b = time.time()
        self._data["deformerWeight"]["weights"].append(copy.copy(influence_data))
        print("apply data: %s" % str(time.time() - s_b))

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

    def subtract(self, influences, influence_data, clamp=True):
        """removes the influence data from defined influences"""
        if isinstance(influences, str):
            influences = [influences]
        # first convert the weights list of dictionaries data into a simpler dictionary
        # where the key is the vtx id and value is the value
        subtract_dict_data = self.__points_to_dict(influence_data["points"])
        for inf in influences:
            source_data = self.get_influence_data(inf)
            # Do the same conversion for the source influence weights
            weight_dict_data = self.__points_to_dict(source_data["points"])
            for idx, value in weight_dict_data.items():
                new_val = value - subtract_dict_data.get(idx, 0)
                if clamp:
                    new_val = max(min(new_val, 1.0), 0.0)
                weight_dict_data[idx] = new_val
            # convert it back and put it back
            source_data["points"] = self.__dict_to_points(weight_dict_data)





        # # TODO : not tested
        # copy_data = copy.deepcopy(data_list[0])
        # for weights_list_nmb, weights in enumerate(copy_data["deformerWeight"]["weights"]):
        #     if influencer and weights["source"] != influencer:
        #         continue
        #     for point_nmb, point in enumerate(weights["points"]):
        #         point_values = []
        #         for data_list_nmb, json_data in enumerate(data_list):
        #             val = json_data["deformerWeight"]["weights"][weights_list_nmb]["points"][point_nmb]["value"]
        #             point_values.append(val)
        #         point["value"] = subtractList(point_values)
        #         if clamp:
        #             point["value"] = max(min(point["value"], 1.0), 0.0)
        # return copy_data

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

    @staticmethod
    def barycentric_interpolate(vec_a, vec_b, vec_c, vec_p):
        '''
        Calculates barycentricInterpolation of a point in a triangle.

        :param vec_a - OpenMaya.MVector of a vertex point.
        :param vec_b - OpenMaya.MVector of a vertex point.
        :param vec_c - OpenMaya.MVector of a vertex point.
        :param vec_p - OpenMaya.MVector of a point to be interpolated.

        Returns list of 3 floats representing weight values per each point.
        '''
        # https://gamedev.stackexchange.com/questions/23743/whats-the-most-efficient-way-to-find-barycentric-coordinates
        v0 = vec_b - vec_a
        v1 = vec_c - vec_a
        v2 = vec_p - vec_a

        d00 = v0 * v0
        d01 = v0 * v1
        d11 = v1 * v1
        d20 = v2 * v0
        d21 = v2 * v1
        denom = d00 * d11 - d01 * d01
        v = (d11 * d20 - d01 * d21) / denom
        w = (d00 * d21 - d01 * d20) / denom
        u = 1.0 - v - w

        return [u, v, w]

    # def test_get_weights(self, skincluster, mesh):
    #     return self.__get_weights(skincluster, mesh)
    #
    # def test_set_weights(self, skincluster, mesh, m_array):
    #     self.__set_weights(skincluster, mesh, m_array)
    #
    # def test_get_blend_weights(self, skincluster, mesh):
    #     return self.__get_blend_weights(skincluster, mesh)
    #
    # def test_set_blend_weights(self, skincluster, mesh, m_array):
    #     self.__set_blend_weights(skincluster, mesh, m_array)
    def _clamp_point_weights(self, constant_inf_data):
        """uses the constant_inf_data values as constant and removes the excess values from other influences"""
        # convert all influence weights into dictionary right at the beginning (so only once per influence)
        inf_dict = {}
        for inf in self._data["deformerWeight"]["weights"]:
            p_dict = self.__points_to_dict(inf["points"])
            inf_dict[inf.get("source")] = p_dict

        # get the list of vtx and remaining values
        # reduction_dict = {} # dictionary of excess values that needs to be reduced from the other incluences
        for points_data in constant_inf_data["points"]:
            vtx_id = points_data["index"]
            excess_value = clamp(points_data["value"])
            # excess_value = clamp((1 - points_data["value"]))
            # reduction_dict[vtx_id] = excess_value
            # build a dictionary for that vtx where keys are influences
            vtx_inf_dict = {}
            for inf_name, p_dict in inf_dict.items():
                # p_dict = self.__points_to_dict(inf["points"])
                value = p_dict.get(vtx_id, 0) # get the value on the vtx id
                vtx_inf_dict[inf_name] = value
            #
            impact_list = list(reversed(sorted(vtx_inf_dict, key=vtx_inf_dict.get)))
            # print(impact_list)
            for _inf in impact_list:
                original_value = inf_dict[_inf].get(vtx_id, 0)
                inf_dict[_inf].update({vtx_id:clamp(original_value-excess_value)})
                excess_value = clamp(excess_value - original_value)

            # # TODO maybe this speed it up a bit
            # counter = 0
            # while excess_value:
            #     try:
            #         _inf = impact_list[counter]
            #     except IndexError:
            #         break
            #     original_value = inf_dict[_inf].get(vtx_id, 0)
            #     inf_dict[_inf].update({vtx_id: clamp(original_value - excess_value)})
            #     excess_value = clamp(excess_value - original_value)
            #     counter += 1


            # convert back to the maya JSON compatibility
            for inf_data in self._data["deformerWeight"]["weights"]:
                inf_name = inf_data.get("source")
                reconverted_points_data = self.__dict_to_points(inf_dict[inf_name])
                inf_data["points"] = reconverted_points_data

