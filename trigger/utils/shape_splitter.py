"""splits blendshapes with the given maps"""
import os
from maya import cmds

from trigger.actions import weights
from trigger.library import functions as extra

class Splitter(dict):
    def __init__(self):
        super(Splitter, self).__init__()
        # initialize dictionary structure
        self["matches"] = {}
        self["splitMaps"] = {}
        self.weightsHandler = weights.Weights()
        self.getMapMethod = "File"


    def add_blendshapes(self):
        selection = cmds.ls(sl=True, type="transform")
        # remove groups
        selection = filter(lambda x: extra.getShapes(x), selection)
        # remove non-meshes
        selection = filter(lambda x: cmds.objectType(extra.getShapes(x)[0]) == "mesh", selection)
        self["matches"].update({mesh: [] for mesh in selection})

    def add_splitmap(self, file_path, name=None):
        file_path = os.path.normpath(file_path) # stupid slashes
        name = os.path.basename(file_path) if not name else name
        # create a negative map and store it on a temp location
        self.weightsHandler.io.file_path = file_path

        positive_data = self.weightsHandler.io.read()
        negative_data = self.weightsHandler.negateWeights(positive_data)
        file_name, ext = os.path.splitext(os.path.basename(file_path))
        negative_file_name = ("%sN%s" % (file_name, ext))
        # file name is enough. IO module will use the last defined root dir (default documents)
        # this location is not important
        print("=="*30)
        print(negative_file_name)
        print("=="*30)
        self.weightsHandler.io.file_path = negative_file_name
        file_pathN = self.weightsHandler.io.write(negative_data)
        self["splitMaps"][name] = [file_path, file_pathN]

    def set_splitmap(self, blendshape, split_maps):
        self["matches"][blendshape] = split_maps

    def split_shapes(self):
        for shape, split_maps in self["matches"]:
            if len(split_maps > 1):
                # if required shapes are quadrants, octants etc...
                pass
            else:
                # there is a single map,
                # so we only require that one and the negative of it
                file_path_positive = self["splitMaps"][split_maps[0]]
                file_path_negative = "ASDF"
                working_lists = []

            side_a = cmds.duplicate(shape)
        return splitted_shapes
    # getters / cleaners
    def get_blendshapes(self):
        return self["matches"].keys()

    def get_splitmaps(self):
        return self["splitMaps"].keys()

    def clear_blendshapes(self):
        self["matches"] = {}

    def clear_splitmaps(self):
        self["splitMaps"] = {}
