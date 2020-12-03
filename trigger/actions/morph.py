"""Action that identify and connect blendshapes"""

import re

from maya import cmds
from trigger.library import functions, attribute, deformers

ACTION_DATA = {
    "blendshapes_group": "",
    "neutral_mesh": "",
}

class Morph(object):
    def __init__(self, *args, **kwargs):
        super(Morph, self).__init__()

        # user defined
        self.neutralMesh = None
        self.blendshapesGroup = None

        # class variables
        self.shapeCategories = {
            "base": [],
            "inbetween": [],
            "combination": []
        }
        self.morphGrp = None
        self.morphHook = None
        self.morphMesh = None
        self.bsNode = None


    def feed(self, action_data, *args, **kwargs):
        self.blendshapesGroup = action_data.get("blendshapes_group")
        self.neutralMesh = action_data.get("neutral_mesh")

    def action(self):
        assert self.blendshapesGroup, "Blendshape Group not defined"
        self.categorize_blendshapes(functions.getMeshes(self.blendshapesGroup))
        # build hierarchy
        self._create_hierarchy()

        # ingest base shapes
        for target in self.shapeCategories["base"]:
            self.ingest_base(target)

        # ingest inbetween shapes


        # ingest combination shapes




    def save_action(self):
        pass

    def ui(self):
        pass

    def categorize_blendshapes(self, meshes):
        """puts each shape into the correct category"""
        self.shapeCategories["base"] = []
        self.shapeCategories["inbetween"] = []
        self.shapeCategories["combination"] = []

        # filter the X meshes
        filtered_meshes = [mesh for mesh in meshes if not mesh.endswith("X")]
        for mesh in filtered_meshes:
            if "_" in mesh:
                self.shapeCategories["combination"].append(mesh)
            elif re.search('.*?([0-9]+)$', mesh):
                self.shapeCategories["inbetween"].append(mesh)
            else:
                self.shapeCategories["base"].append(mesh)
        return self.shapeCategories

    def _create_hierarchy(self):
        """Creates the hook node for blendshapes"""
        rig_grp = "rig_grp"
        if not cmds.objExists(rig_grp):
            cmds.group(name=rig_grp, em=True)
            attribute.lockAndHide(rig_grp)
        self.morphGrp = cmds.group(name="morph_grp", em=True)
        attribute.lockAndHide(self.morphGrp)
        cmds.parent(self.morphGrp, rig_grp)
        self.morphHook = cmds.group(name="morph_hook", em=True)
        attribute.lockAndHide(self.morphHook)
        cmds.parent(self.morphHook, self.morphGrp)
        self.morphMesh = cmds.duplicate(self.neutralMesh, name="trigger_morphMesh")[0]
        cmds.parent(self.morphMesh, self.morphGrp)


    def create_hook_node(self):
        """Creates the hook node for blendshapes"""
        rig_grp = "rig_grp"
        if not cmds.objExists(rig_grp):
            cmds.group(name=rig_grp, em=True)
            attribute.lockAndHide(rig_grp)
        self.morphGrp = cmds.group(name="morph_grp", em=True)
        attribute.lockAndHide(self.morphGrp)
        cmds.parent(self.morphGrp, rig_grp)
        morph_hook = cmds.group(name="morph_hook", em=True)
        attribute.lockAndHide(rig_grp)
        cmds.parent(morph_hook, self.morphGrp)
        return morph_hook

    def ingest_base(self, blendshape):
        deformers.connect_bs_targets("%s.%s" % (self.morphHook, blendshape), {self.morphMesh: blendshape})

    def ingest_inbetween(self, blendshape):
        pass

    def ingest_combination(self, blendshape):
        if blendshape.endswith("Delta"):
            delta_shape = blendshape
        else:
            base_shapes = blendshape.split("_")
            # create a temporary blendshape with all base shapes triggered

        pass




