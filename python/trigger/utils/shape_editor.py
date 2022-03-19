"""Editor for fixing/editing blendshape packs"""

class ShapeEditor(object):
    """
    Logic class responsible to storing blendshape pack data, preparing scene and objects for edit,
    previewing animations and committing change
    """
    def __init__(self, blendshape_grp=None, neutral_shape=None):
        super(ShapeEditor, self).__init__()

        self.blendshapes = []
        self.neutral = neutral_shape
        if blendshape_grp:
            self.blendshapes = self.get_blendshapes(blendshape_grp)

        self.work_group = "shape_editor_work_grp"

    def get_blendshapes(self, blendshape_pack_group):
        """
        Gathers the blendshapes under the given group
        Args:
            blendshape_pack_group: (String) Name of the group that holds blendshapes

        Returns:
            (List) List of blendshapes
        """
        pass

    def prep_shape(self, shape_dag_path):
        """
        Prepares the shape for editing
        Args:
            shape_dag_path: (String) scene path of the shape

        Returns:
            None
        """
        pass

    def commit_shape(self):
        """Commits the working blendshape in work group and replaces it with the original"""
        pass





