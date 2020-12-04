"""Action that identify and connect blendshapes"""

import re

from maya import cmds

from trigger.ui.Qt import QtWidgets, QtGui
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
        self.bsNode = functions.uniqueName("trigger_morph_blendshape")


    def feed(self, action_data, *args, **kwargs):
        """Feeds the instance with the action data stored in actions session"""
        self.blendshapesGroup = action_data.get("blendshapes_group")
        self.neutralMesh = action_data.get("neutral_mesh")

    def action(self):
        """Execute Action - Mandatory"""
        assert self.blendshapesGroup, "Blendshape Group not defined"
        self.categorize_blendshapes(functions.getMeshes(self.blendshapesGroup))
        # build hierarchy
        self._create_hierarchy()

        # ingest base shapes
        for target in self.shapeCategories["base"]:
            self.ingest_base(target)

        # ingest inbetween shapes
        for target in self.shapeCategories["inbetween"]:
            self.ingest_inbetween(target)

        # ingest combination shapes
        for target in self.shapeCategories["combination"]:
            self.ingest_combination(target)

    def save_action(self):
        pass

    def ui(self, ctrl, layout, handler, *args, **kwargs):
        """UI - Mandatory"""
        blendshapes_group_lbl = QtWidgets.QLabel(text="Blendshapes Group:")
        blendshapes_group_le = QtWidgets.QLineEdit()
        layout.addRow(blendshapes_group_lbl, blendshapes_group_le)

        neutral_mesh_lbl = QtWidgets.QLabel(text="Neutral Mesh:")
        neutral_mesh_le = QtWidgets.QLineEdit()
        layout.addRow(neutral_mesh_lbl, neutral_mesh_le)

        ctrl.connect(blendshapes_group_le, "blendshapes_group", str)
        ctrl.connect(neutral_mesh_le, "neutral_mesh", str)
        ctrl.update_ui()

        blendshapes_group_le.editingFinished.connect(lambda x=0: ctrl.update_model())
        neutral_mesh_le.editingFinished.connect(lambda x=0: ctrl.update_model())

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
        deformers.connect_bs_targets("%s.%s" % (self.morphHook, blendshape), {self.morphMesh: blendshape}, bs_node_name=self.bsNode)

    def ingest_inbetween(self, blendshape):
        # get the base shape
        digits = re.search('.*?([0-9]+)$', blendshape)
        percentage = (float(digits.groups()[0]) * 0.01)
        base = blendshape if not digits else re.search("(.*)(%s)$" % digits.groups()[0], blendshape).groups()[0]

        id = deformers.get_bs_index_by_name(self.bsNode, base)
        cmds.blendShape(self.bsNode, edit=True, ib=True,
                        t=(self.morphMesh, id, blendshape, percentage))

    def ingest_combination(self, blendshape):
        if blendshape.endswith("Delta"):
            delta_shape = blendshape
        else:
            delta_shape = self.create_combination_delta(self.neutralMesh, blendshape.split("_"), blendshape)

        # ingest combination delta just like a regular base and drive it with combinationShape node
        # self.ingest_base(delta_shape)
        next_index = cmds.blendShape(self.bsNode, q=True, wc=True)
        cmds.blendShape(self.bsNode, edit=True, t=(self.morphMesh, next_index, delta_shape, 1.0), w=[next_index, 0.0])
        combination_node = cmds.createNode("combinationShape")
        input_list = blendshape.split("_")
        for nmb, input_shape in enumerate(input_list):
            cmds.connectAttr("%s.%s" %(self.bsNode, input_shape), "%s.inputWeight[%s]" %(combination_node, nmb), force=True)
        cmds.connectAttr("%s.outputWeight" %combination_node, "%s.%s" %(self.bsNode, delta_shape), force=True)


    def create_combination_delta(self, neutral, non_sculpted_meshes, sculpted_mesh):
        """Creates a basic delta mesh of the sculpted combination shape against non-sculpted"""
        stack = cmds.duplicate(neutral)[0]
        temp_bs_node = cmds.blendShape(non_sculpted_meshes, stack)[0]
        for attr in cmds.aliasAttr(temp_bs_node, q=True)[::2]:
            cmds.setAttr("{0}.{1}".format(temp_bs_node, attr), -1)
        next_index = cmds.blendShape(temp_bs_node, q=True, wc=True)
        cmds.blendShape(temp_bs_node, edit=True, t=(stack, next_index, sculpted_mesh, 1.0), w=[next_index, 1.0],)
        # put it where the sculpted mesh is and rename it
        cmds.delete(stack, ch=True)
        parent_node = functions.getParent(sculpted_mesh)
        if parent_node:
            cmds.parent(stack, parent_node)
        return (cmds.rename(stack, "%sDelta" % sculpted_mesh))

