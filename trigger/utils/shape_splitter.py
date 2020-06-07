"""splits blendshapes with the given maps"""
import os
from copy import deepcopy

from maya import cmds
import itertools
from trigger.actions import weights
from trigger.library import functions as extra
from trigger.library import deformers
from trigger.core import feedback

FEEDBACK = feedback.Feedback(logger_name=__name__)

class Splitter(dict):
    def __init__(self):
        super(Splitter, self).__init__()
        # initialize dictionary structure
        self["matches"] = {}
        self["splitMaps"] = {}
        self.weightsHandler = weights.Weights()
        self.neutral = None
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
        name, _ = os.path.splitext(os.path.basename(file_path)) if not name else name

        # check for the negative map, create if does not exist
        file_dir, basename = os.path.split(file_path)
        file_name, file_ext = os.path.splitext(basename)
        file_pathN = os.path.join(file_dir, "%sN%s" % (file_name, file_ext))
        if not os.path.isfile(file_pathN):
            self.weightsHandler.io.file_path = file_path
            positive_data = self.weightsHandler.io.read()
            negative_data = self.weightsHandler.negateWeights(positive_data)
            self.weightsHandler.io.file_path = file_pathN
            file_pathN = self.weightsHandler.io.write(negative_data)

        self["splitMaps"][name] = [file_path, file_pathN]

    def set_splitmap(self, blendshape, split_maps):
        if type(split_maps) == str:
            split_maps = [split_maps]
        self["matches"][blendshape] = split_maps

    def _bs_split(self, mesh, split_map_path, name, grp):
        splitted_mesh = cmds.duplicate(self.neutral, name=name)[0]
        cmds.blendShape(mesh, splitted_mesh, w=[0, 1], name="tmp_split_blendshape")
        self.weightsHandler.load_weights(deformer="tmp_split_blendshape", file_path=split_map_path)
        cmds.delete(splitted_mesh, ch=True)
        cmds.parent(splitted_mesh, grp)
        return splitted_mesh

    def _resolve_split_name(self, unsplit_name, map_path):
        map_name = os.path.splitext(os.path.basename(map_path))[0]
        suffix = ""
        if "vertical" in map_name:
            if map_name.endswith("N"):
                suffix = "R"
            else:
                suffix = "L"
        if "horizontal" in map_name:
            if map_name.endswith("N"):
                suffix = "%sD" % suffix
            else:
                suffix = "%sU" % suffix
        if not suffix:
            if map_name.endswith("N"):
                suffix = "B"
            else:
                suffix = "A"
        split_name = "%s_%s" % (unsplit_name, suffix)
        return split_name

    def split_shapes(self):
        if not self.neutral:
            FEEDBACK.throw_error("Neutral shape is not defined")
        splits_grp = "SPLITTED_SHAPES_grp"
        if not cmds.objExists(splits_grp):
            cmds.group(name="SPLITTED_SHAPES_grp", em=True)

        mort_list = []
        expandable_list = deepcopy(self["matches"].items())
        for shape, split_maps in expandable_list:
            if not split_maps:
                continue

            map_paths = self["splitMaps"][split_maps[0]]

            for nmb, map_path in enumerate(map_paths):
                # resolve the name suffix
                splitted_name = self._resolve_split_name(shape, map_path)
                splitted_mesh = self._bs_split(shape, map_path, splitted_name, splits_grp)

                if len(split_maps) > 1:
                    mort_list.append(splitted_mesh)
                    expandable_list.append((splitted_mesh, split_maps[1:]))

        cmds.delete(mort_list)
        return splits_grp

    # def split_shapes(self):
    #     if not self.neutral:
    #         FEEDBACK.throw_error("Neutral shape is not defined")
    #     splits_grp = "SPLITTED_SHAPES_grp"
    #     if not cmds.objExists(splits_grp):
    #         cmds.group(name="SPLITTED_SHAPES_grp", em = True)
    #
    #     for shape, split_maps in self["matches"].items():
    #         if not split_maps:
    #             continue
    #         if len(split_maps) > 1:
    #             # if there are multiple split maps, required shapes are quadrants, octants etc...
    #             work_path_list = []
    #             for s_map in split_maps:
    #                 work_path_list.append(self["splitMaps"][s_map])
    #             pGen = list(itertools.product(*work_path_list))
    #             # tmp_name = "tmp"
    #             for mult_path_list in pGen:
    #                 tmp_name = "tmp"
    #                 data_list = []
    #                 for mult_path in mult_path_list:
    #                     name = os.path.splitext(os.path.basename(mult_path))[0]
    #                     tmp_name = "%s_%s" %(tmp_name, name)
    #                     # get data
    #                     self.weightsHandler.io.file_path = mult_path
    #                     data = self.weightsHandler.io.read()
    #                     data_list.append(data)
    #                 multiplied_weights = self.weightsHandler.multiplyWeights(data_list)
    #                 tmp_name = "%s.json" % tmp_name
    #                 self.weightsHandler.io.file_path = tmp_name
    #                 self.weightsHandler.io.write(multiplied_weights)
    #                 map_path = self.weightsHandler.io.file_path
    #                 print("="*30)
    #                 print(shape, map_path)
    #                 print("="*30)
    #                 splitted_name = self._resolve_split_name(shape, map_path)
    #                 self._bs_split(shape, map_path, splitted_name, splits_grp)
    #             pass
    #         else:
    #             # there is a single map,
    #             # so we only require that one and the negative of it
    #             map_paths = self["splitMaps"][split_maps[0]]
    #             for nmb, map_path in enumerate(map_paths):
    #                 # resolve the name suffix
    #                 splitted_name = self._resolve_split_name(shape, map_path)
    #                 self._bs_split(shape, map_path, splitted_name, splits_grp)
    #
    #     return splits_grp
    # getters / cleaners
    def get_blendshapes(self):
        return self["matches"].keys()

    def get_splitmaps(self):
        return self["splitMaps"].keys()

    def clear_blendshapes(self):
        self["matches"] = {}

    def clear_splitmaps(self):
        self["splitMaps"] = {}

    # extras
    def prepare_for_painting(self, mesh, split_maps=None):
        bs_name = "splitMaps_blendshape"
        if not split_maps:
            split_maps = ["vertical_sharp", "vertical_smooth", "horizontal_sharp"]
        if type(split_maps) == str:
            split_maps = [split_maps]
        for map in split_maps:
            deformers.localize(mesh, "splitMaps_blendshape", local_target_name=map)

        return bs_name


