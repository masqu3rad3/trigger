"""Editor for fixing/editing blendshape packs"""
import re
from maya import cmds
from trigger.library import transform, functions
from trigger.objects.base_node import BaseNode

class ShapeEditor(object):
    """
    Logic class responsible to storing blendshape pack data, preparing scene and objects for edit,
    previewing animations and committing change
    """

    def __init__(self, blendshape_grp=None, neutral_shape=None):
        super(ShapeEditor, self).__init__()

        ShapeEditorException().clear()
        self.blendshapes = []
        self.neutral = neutral_shape
        if blendshape_grp:
            # self.blendshapes = self.build_blendshape_data(blendshape_grp)
            self.blendshapes = self.get_blendshapes(blendshape_grp)

        self.work_group = "shape_editor_work_grp"
        self.base_shapes = []
        self.inbetweem_shapes = []
        self.combination_shapes = []
        self.shape_wip = None

    # def build_blendshape_data(self, blendshape_pack_group):
    #     """
    #     Builds a dictionary containing the necessary (and some unnecessary atm) data from the scene
    #     The idea is extend the dictionary where it is necessary and re-use or exchange same data with other modules
    #
    #     Args:
    #         blendshape_pack_group: (String) Name of the group that holds blendshapes
    #
    #     Returns:
    #         (Dictionary) Blendshape data dictionary:
    #                         {
    #                         "all": <list of all shapes under given group>
    #                         "bases": <list of base shapes>
    #                         "inbetweens": <list of inbetweens>
    #                         "combinations" <list of combinations>
    #                         "statistics": {
    #                                         "total_count": <integer number of all shape count>
    #                                         "bases_count": <count of base shapes>
    #                                         "inbetweens_count": <count of inbetweens>
    #                                         "combinations_count": <count of combinations>
    #                                         "pack_group_name": <name of the given blendshape pack group>
    #                         }
    #     """
    #
    #     _bs_data = {}
    #     _bs_data["all"] = functions.getMeshes(blendshape_pack_group)
    #     _bs_data["bases"], _bs_data["inbetweens"], _bs_data["combinations"] = self.categorize_shapes(_bs_data["all"])
    #     _bs_data["statistics"] = {
    #         "total_count": len(_bs_data["_all"]),
    #         "bases_count": len(_bs_data["bases"]),
    #         "inbetweens_count": len(_bs_data["inbetweens"]),
    #         "combinations_count": len(_bs_data["combinations"]),
    #         "pack_group_name": blendshape_pack_group
    #     }
    #     return _bs_data

    def get_blendshapes(self, blendshape_pack_group):
        _meshes = functions.getMeshes(blendshape_pack_group)
        for mesh in _meshes:
            pass



    def prep_shape(self, shape_dag_path):
        """
        Prepares the shape for editing
        Args:
            shape_dag_path: (String) scene path of the shape

        Returns:
            None
        """
        shape_name = shape_dag_path.split("|")[-1]
        if not self._validate_workspace():
            return -1

        # setup work object
        work_object = cmds.duplicate(shape_dag_path, name="%s_SE_WIP" % shape_name)
        cmds.parent(work_object, self.work_group)

        # Create a visualization mesh
        vis_object = cmds.duplicate(self.neutral, name="%s_VIS")
        pass

    def commit_shape(self):
        """Commits the working blendshape in work group and replaces it with the original"""
        pass

    def _validate_workspace(self):
        """Validates presence of required elements"""
        transform.validate_group(self.work_group)  # checks the group existence, creates if not
        if not self.neutral:
            ShapeEditorException().raise_error("Neutral Shape not defined")
            return False


    @staticmethod
    def categorize_shapes(meshes):
        """puts each shape into the correct category"""
        _base_shapes = []
        _inbetweem_shapes = []
        _combination_shapes = []
        # filter the X meshes
        filtered_meshes = [mesh for mesh in meshes if not mesh.endswith("X")]
        for mesh in filtered_meshes:
            if "_" in mesh:
                # make sure combination inbetweens stay at the end of the list
                if mesh.split("_")[-1].isdigit():
                    _combination_shapes.append(mesh)
                else:
                    _combination_shapes.insert(0, mesh)
            elif re.search('.*?([0-9]+)$', mesh):
                _inbetweem_shapes.append(mesh)
            else:
                _base_shapes.append(mesh)
        return _base_shapes, _inbetweem_shapes, _combination_shapes

class ShapeEditorException:
    msg = ""
    critical = False

    def __init__(self):
        pass

    @classmethod
    def raise_warning(cls, msg):
        cls.msg = msg
        cls.critical = False

    @classmethod
    def raise_error(cls, msg):
        cls.msg = msg
        cls.critical = True

    @classmethod
    def clear(cls):
        cls.msg = ""
        cls.critical = False


class Blendshape(BaseNode):
    def __init__(self, dag_path):
        super(Blendshape, self).__init__()
        self.dag_path = dag_path
        self.type = self.get_shape_type(self.name) # base, inbetween, combination, combination_inbetween or None
        if self.type == "inbetween" or self.type == "combination_inbetween":
            self.percentage = self.get_percentage(self.name)
        else:
            self.percentage = 0 # valid only if its an inbetween
        if self.type.startswith("combination"):
            self.combination_parts = self.get_combination_parts(self.name) # valid only if its a combination
        else:
            self.combination_parts = []

    @staticmethod
    def get_shape_type(shape):
        """Resolves the type of the blendshape"""
        if shape.endswith("X"):
            return None
        if "_" in shape:
            if shape.split("_")[-1].isdigit():
                _type = "combination_inbetween"
            else:
                _type = "combination"
        elif re.search('.*?([0-9]+)$', shape):
            _type = "inbetween"
        else:
            _type = "base"
        return _type

    @staticmethod
    def get_percentage(shape):
        pass

    @staticmethod
    def get_combination_parts(shape):
        return shape.split("_")