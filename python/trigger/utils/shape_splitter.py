"""splits blendshapes with the given maps"""
import os
from copy import deepcopy

from maya import cmds
import itertools
from trigger.core import filelog
from trigger.core.decorators import keepselection
from trigger.actions import weights
from trigger.library import functions
from trigger.library import deformers


log = filelog.Filelog(logname=__name__, filename="trigger_log")

class Splitter(dict):
    def __init__(self):
        super(Splitter, self).__init__()
        # initialize dictionary structure
        self["matches"] = {}
        self["splitMaps"] = {}
        self.weightsHandler = weights.Weights()
        self.neutral = None
        self.splittedShapesGrp = "SPLITTED_SHAPES_grp"

    def add_blendshapes(self, meshes=None):
        if not meshes:
            selection = cmds.ls(sl=True, type="transform")
            # remove groups
            selection = filter(lambda x: functions.getShapes(x), selection)
            # remove non-meshes
            selection = filter(lambda x: cmds.objectType(functions.getShapes(x)[0]) == "mesh", selection)
            self["matches"].update({mesh: [] for mesh in selection})
        else:
            self["matches"].update({mesh: [] for mesh in meshes})

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

        combination_parts = unsplit_name.split("_")
        if combination_parts:
            ## dont touch digits
            split_named_combination_parts = []
            for part in combination_parts:
                if part.isdigit():
                    split_named_combination_parts.append(part)
                else:
                    split_named_combination_parts.append("{0}{1}".format(suffix, part))

            # split_named_combination_parts = ["%s%s" %(suffix, part) for part in combination_parts]
            split_name = "_".join(split_named_combination_parts)
        else:
            split_name = "%s%s" % (suffix, unsplit_name)
        return split_name

    def split_shapes(self):
        if not self.neutral:
            log.error("Neutral shape is not defined")
        # splits_grp = "SPLITTED_SHAPES_grp"
        if not cmds.objExists(self.splittedShapesGrp):
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
                splitted_mesh = self._bs_split(shape, map_path, splitted_name, self.splittedShapesGrp)

                if len(split_maps) > 1:
                    mort_list.append(splitted_mesh)
                    expandable_list.append((splitted_mesh, split_maps[1:]))

        cmds.delete(mort_list)
        return self.splittedShapesGrp

    # getters / cleaners
    def get_blendshapes(self):
        return self["matches"].keys()

    def get_splitmaps(self):
        return self["splitMaps"].keys()

    def clear_blendshapes(self):
        self["matches"] = {}

    def clear_splitmaps(self):
        self["splitMaps"] = {}

    @keepselection
    def prepare_for_painting(self, mesh, split_maps=None):
        bs_name = "splitMaps_blendshape"
        if not split_maps:
            split_maps = ["vertical_sharp", "vertical_smooth", "horizontal_sharp"]
        if type(split_maps) == str:
            split_maps = [split_maps]
        for map in split_maps:
            local_target = deformers.localize(mesh, "splitMaps_blendshape", local_target_name=map)
            functions.deleteObject(functions.getParent(local_target))

        return bs_name



