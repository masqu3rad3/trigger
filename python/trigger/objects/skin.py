import uuid
import os
import copy
from maya import cmds
import maya.api.OpenMaya as api
from trigger.library import deformers
from trigger.core.io import IO

class Weight(IO):
    def __init__(self, file_path=None, deformer=None):
        if not file_path:
            file_name = "%s.json" % uuid.uuid4().time_low
            _file_path = os.path.join(os.path.expanduser("~"), file_name)
            self.temp_file = True
        else:
            file_name = None
            _file_path = file_path
            self.temp_file = False
        super(Weight, self).__init__(file_path=_file_path)

        self._data = None
        # self.set_file_path(self.file_path)
        if deformer:
            self.read_data_from_deformer(deformer)
        if file_path:
            self.read_data_from_file(file_path)

    def read_data_from_deformer(self, deformer):
        self._validate_deformer(deformer)
        # write the json file using maya thingie. Read it back and discard the temporary file

        # _temp_file_name = "%s.json" % uuid.uuid4().time_low
        # _path = os.path.join(os.path.expanduser("~"))
        # Specific attributes for skinClusters
        attributes = ["envelope", "skinningMethod", "useComponents", "normalizeWeights", "deformUserNormals"]
        _file_path, _file_name = os.path.split(self.file_path)
        cmds.deformerWeights(_file_name, export=True, deformer=deformer, path=_file_path, defaultValue=-1.0, vc=False, at=attributes)
        # cmds.deformerWeights(_file_name, export=True, deformer=deformer, path=_file_path, vc=False, at=attributes)
        # read it back

        self._data = self.read()
        # discard the file if no proper file path defined
        if self.temp_file:
            os.remove(self.file_path)

    def read_data_from_file(self, path):
        self._data = IO(file_path=path).read()

    def apply_data(self, deformer=None, file_path=None):
        # if a path is defined use that to get the data, otherwise use the data to define the file path
        if file_path:
            self.read_data_from_file(file_path)
        # else:
        #     self.write(self._data) # write this to read it back
        # if not cmds.ls(deformer, type="skinCluster"):
        #     # if the skincluster is not there, find the shape and create one
        deformer = deformer or self._data["deformerWeight"]["deformers"][0]["name"]
        # get the active influences
        _influences = cmds.skinCluster(deformer, query=True, influence=True)
        _data_influences = self.get_all_influences()

        # add the missing ones / remove the excess
        _ = [cmds.skinCluster(deformer, edit=True, addInfluence=x, nw=0) for x in _data_influences if x not in _influences]
        _ = [cmds.skinCluster(deformer, edit=True, removeInfluence=x, nw=0) for x in _influences if x not in _data_influences]

        # cmds.skinCluster(deformer, edit=True, normalizeWeights=0)
        # cmds.skinCluster(deformer, edit=True, maximumInfluences=500)


        for inf in _data_influences:
            # conform the influence dictionary to list
            # print(deformer, list(self.__generate_influence_list(inf)), inf)
            # deformers.set_deformer_weights(deformer, list(self.__generate_influence_list(inf)), inf)
            print(inf)
            self.__set_deformer_weights(deformer, inf)

        # file_dir, file_name = os.path.split(self.file_path)
        # cmds.deformerWeights(file_name, im=True, deformer=deformer, path=file_dir, method="index",
        #                      ignoreName=True)

        # JSON import bug with maya

    def __generate_influence_list(self, raw_weights_data):
        """spits out the json point data for given influence as list"""
        for p_data in raw_weights_data["points"]:
            yield p_data["index"], p_data["value"]
            # yield p_data["value"]

    @staticmethod
    def __get_plug_ids(deformer, layer):
        """
        Gets the plug of skin clusters weights
        Args:
            deformer: (string) the deformer
            layer: (int) the layer (influencer id) defined as in JSON file

        Returns:
            <plug object>
        """
        sel = api.MSelectionList()
        sel.add("%s.weightList[%i].weights" % (deformer, layer))
        return sel.getPlug(0)


    def __set_deformer_weights(self, deformer, influence_name):

        # this assumes the influence data count is always equal to the mesh vertex count

        # get the influences list and layer (influence weights id)
        weights_data = self.get_influence_data(influence_name)
        count = weights_data.get("size")
        layer = weights_data.get("layer")
        print("layerL", layer)
        print(count)

        influences_gen = (self.__generate_influence_list(weights_data))
        # print(len(influences_gen))
        plug = self.__get_plug_ids(deformer, layer)
        # for index, val in influences_gen:
        #     plug.elementByLogicalIndex(index).setDouble(val)

        # for index, val in enumerate(influences_gen):
        #     plug.elementByLogicalIndex(index).setDouble(val)
        # map(lambda i: plug.elementByLogicalIndex(i).setDouble(influences_gen[i]), range(count))
        map(lambda i, v: plug.elementByLogicalIndex(i).setDouble(v), influences_gen)

    def get_all_influences(self):
        """Returns the name of all influences the data contains"""
        return [x.get("source") for x in self._data["deformerWeight"]["weights"]]

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
            raise Exception ("Data already contains weights data for %s" % _influence_name)
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



    # def get_deformer(self):
    #     return self._deformer

    # def set_file_path(self, path):
    #     self.file_path = path
    #     self.temp_file = False
    #     self._data = self.read()

    def add_weights(self, deformer=None, path=None):
        self._validate_source(deformer=deformer, path=path)
        if deformer:
            b = Weight()
            b.read_deformer(deformer)



    def _validate_source(self, deformer=None, path=None):
        if deformer and path:
            raise Exception ("both deformer and path cannot be defined")
        if not deformer or not path:
            raise Exception ("Either deformer or path needs to be defined")
        # if deformer:
        #     if not cmds.ls(deformer):
        #         raise Exception ("Deformer %s cannot be found in the scene" % deformer)
        return True

    # @property
    # def deformer(self):
    #     return self._deformer
    #
    # @deformer.setter
    # def deformer(self, val):
    #    self._validate_deformer(val)

    # @property
    # def file_path(self):
    #     return self["file_path"]
    #
    # @file_path.setter
    # def file_path(self, val):
    #     super(Weight, self).file_path
    #     print("test")

    def _validate_deformer(self, deformer):
        # TODO
        pass


# some_weight = Weight()
#
# some_weight.file_path = "something/somethging.json"
# some_weight.deformer = "someDeformer"

#
# class Influence(dict):
#
#     @property
#     def deformer


