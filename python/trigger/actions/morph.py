"""Action that identify and connect blendshapes"""

import re
import itertools

from maya import cmds

from trigger.core.decorators import viewportOff
from trigger.ui.Qt import QtWidgets, QtGui
from trigger.library import functions, attribute, deformers, naming

from trigger.core import filelog

log = filelog.Filelog(logname=__name__, filename="trigger_log")

ACTION_DATA = {
    "blendshapes_group": "",
    "neutral_mesh": "",
    "hook_node": "morph_hook",
    "morph_mesh": ""
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
        self.bsNode = ("trigger_morph_blendshape")


    def feed(self, action_data, *args, **kwargs):
        """Feeds the instance with the action data stored in actions session"""
        self.blendshapesGroup = action_data.get("blendshapes_group")
        self.neutralMesh = action_data.get("neutral_mesh")
        self.morphHook = action_data.get("hook_node")
        self.morphMesh = action_data.get("morph_mesh")

    @viewportOff
    def action(self):
        """Execute Action - Mandatory"""
        assert self.blendshapesGroup, "Blendshape Group not defined"
        self.categorize_blendshapes(functions.getMeshes(self.blendshapesGroup))
        # build hierarchy
        self._create_hierarchy()
        print(self.shapeCategories)
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

        hook_node_lbl = QtWidgets.QLabel(text="Hook Node:")
        hook_node_le = QtWidgets.QLineEdit(placeholderText="(Optional)")
        layout.addRow(hook_node_lbl, hook_node_le)

        morph_mesh_lbl = QtWidgets.QLabel(text="Morph Mesh:")
        morph_mesh_le = QtWidgets.QLineEdit(placeholderText="(Optional)")
        layout.addRow(morph_mesh_lbl, morph_mesh_le)

        ctrl.connect(blendshapes_group_le, "blendshapes_group", str)
        ctrl.connect(neutral_mesh_le, "neutral_mesh", str)
        ctrl.connect(hook_node_le, "hook_node", str)
        ctrl.connect(morph_mesh_le, "morph_mesh", str)
        ctrl.update_ui()

        blendshapes_group_le.textChanged.connect(lambda x=0: ctrl.update_model())
        neutral_mesh_le.textChanged.connect(lambda x=0: ctrl.update_model())
        hook_node_le.textChanged.connect(lambda x=0: ctrl.update_model())
        morph_mesh_le.textChanged.connect(lambda x=0: ctrl.update_model())

    def categorize_blendshapes(self, meshes):
        """puts each shape into the correct category"""
        self.shapeCategories["base"] = []
        self.shapeCategories["inbetween"] = []
        self.shapeCategories["combination"] = []

        # filter the X meshes
        filtered_meshes = [mesh for mesh in meshes if not mesh.endswith("X")]
        for mesh in filtered_meshes:
            if "_" in mesh:
                # make sure combination inbetweens stay at the end of the list
                if mesh.split("_")[-1].isdigit():
                    self.shapeCategories["combination"].append(mesh)
                else:
                    self.shapeCategories["combination"].insert(0, mesh)
            elif re.search('.*?([0-9]+)$', mesh):
                self.shapeCategories["inbetween"].append(mesh)
            else:
                self.shapeCategories["base"].append(mesh)
        return self.shapeCategories

    def _create_hierarchy(self):
        """Creates the hook node for blendshapes"""
        rig_grp = functions.validateGroup("rig_grp")
        attribute.lockAndHide(rig_grp)
        self.morphGrp = functions.validateGroup("morph_grp")
        attribute.lockAndHide(self.morphGrp)
        if functions.getParent(self.morphGrp) != rig_grp:
            cmds.parent(self.morphGrp, rig_grp)

        if not self.morphHook:
            self.morphHook = functions.validateGroup("morph_hook")
            attribute.lockAndHide(self.morphHook)
            cmds.parent(self.morphHook, rig_grp)
        elif not cmds.objExists(self.morphHook):
            self.morphHook = functions.validateGroup(self.morphHook)
            attribute.lockAndHide(rig_grp)
            cmds.parent(self.morphHook, rig_grp)

        if not self.morphMesh:
            self.morphMesh = cmds.duplicate(self.neutralMesh, name="trigger_morphMesh")[0]
            cmds.parent(self.morphMesh, self.morphGrp)
        elif not cmds.objExists(self.morphMesh):
            self.morphMesh = cmds.duplicate(self.neutralMesh, name=self.morphMesh)[0]
            cmds.parent(self.morphMesh, self.morphGrp)

        if not cmds.objExists(rig_grp):
            cmds.group(name=rig_grp, em=True)
            attribute.lockAndHide(rig_grp)

        # self.morphGrp = cmds.group(name="morph_grp", em=True)
        # attribute.lockAndHide(self.morphGrp)
        # cmds.parent(self.morphGrp, rig_grp)
        # self.morphHook = cmds.group(name="morph_hook", em=True)
        # attribute.lockAndHide(self.morphHook)
        # cmds.parent(self.morphHook, self.morphGrp)
        # self.morphMesh = cmds.duplicate(self.neutralMesh, name="trigger_morphMesh")[0]
        # cmds.parent(self.morphMesh, self.morphGrp)


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

    # def ingest_inbetween(self, blendshape):
    #     # is it delta?
    #     if blendshape.endswith("Delta"):
    #         search_name = blendshape.replace("Delta", "")
    #     else:
    #         search_name = blendshape
    #
    #     # get the base shape
    #     digits = re.search('.*?([0-9]+)$', search_name)
    #     percentage = (float(digits.groups()[0]) * 0.01)
    #     base = blendshape if not digits else re.search("(.*)(%s)$" % digits.groups()[0], blendshape).groups()[0]
    #
    #     id = deformers.get_bs_index_by_name(self.bsNode, base)
    #     cmds.blendShape(self.bsNode, edit=True, ib=True,
    #                     t=(self.morphMesh, id, blendshape, percentage))

    def ingest_inbetween(self, blendshape):
        # get the base shape
        digits = re.search('.*?([0-9]+)$', blendshape)
        percentage = (float(digits.groups()[0]) * 0.01)
        base = blendshape if not digits else re.search("(.*)(%s)$" % digits.groups()[0], blendshape).groups()[0]

        id = deformers.get_bs_index_by_name(self.bsNode, base)
        cmds.blendShape(self.bsNode, edit=True, ib=True,
                        t=(self.morphMesh, id, blendshape, percentage))

    def ingest_combination(self, blendshape):
        is_inbetween = False
        # if blendshape.endswith("Delta"):
        if "Delta" in blendshape:
            delta_shape = blendshape
        else:
            parts = blendshape.split("_")
            # check if this is inbetween combination or base combination
            if parts[-1].isdigit():
                is_inbetween = True
                parts = parts[:-1]
            delta_shape = self.create_combination_delta(self.neutralMesh, parts, blendshape, inbetween=is_inbetween)

        if not is_inbetween:
            # ingest combination delta just like a regular base and drive it with combinationShape node
            next_index = cmds.blendShape(self.bsNode, q=True, wc=True)
            cmds.blendShape(self.bsNode, edit=True, t=(self.morphMesh, next_index, delta_shape, 1.0), w=[next_index, 0.0])
            combination_node = cmds.createNode("combinationShape", name="cmb_%s" %blendshape)
            input_list = blendshape.split("_")
            for nmb, input_shape in enumerate(input_list):
                cmds.connectAttr("%s.%s" %(self.bsNode, input_shape), "%s.inputWeight[%s]" %(combination_node, nmb), force=True)
            cmds.connectAttr("%s.outputWeight" %combination_node, "%s.%s" %(self.bsNode, delta_shape), force=True)
        else:
            self.ingest_inbetween(delta_shape)


    def create_combination_delta(self, neutral, non_sculpted_meshes, sculpted_mesh, check_sub_combinations=True, inbetween=False):
        """Creates a basic delta mesh of the sculpted combination shape against non-sculpted"""
        # if it already exists, return it immediately
        parts = sculpted_mesh.split("_")
        if inbetween:
            weight = (float(parts[-1]) * 0.01)
            suffix = "Delta%s" % parts[-1]
            combination_delta = "_".join(parts[:-1]) + suffix
        else:
            weight = 1.0
            combination_delta = "%sDelta" % sculpted_mesh
        if cmds.objExists(combination_delta):
            return combination_delta

        # # if it already exists, return it immediately
        # combination_delta = "%sDelta" % sculpted_mesh
        # if cmds.objExists(combination_delta):
        #     return combination_delta

        # check for the nested sub-combination shapes if it contains more than 2 shapes
        sub_combination_deltas = []
        if len(non_sculpted_meshes) > 2 and check_sub_combinations:
            sub_combinations = []
            for L in range(2, len(non_sculpted_meshes)):
                for subset in itertools.permutations(non_sculpted_meshes, L):
                    check = "_".join(subset)
                    if cmds.objExists(check):
                        sub_combinations.append(check)
            #recursively create deltas for sub-combinations
            for sub in sub_combinations:
                parts = sub.split("_")
                sub_combination_deltas.append(self.create_combination_delta(neutral, parts, sub, check_sub_combinations=False))

        stack = cmds.duplicate(neutral)[0]
        ###########
        # if one or more combination shapes does not exist, try to create them
        temp_bs_node = cmds.blendShape(non_sculpted_meshes+sub_combination_deltas, stack)[0]
        # set the last attr with the negative weight value instead of -1 to get the combination inbetween shape correct
        # so... the ORDER of the combination matters!!!
        attr_list = cmds.aliasAttr(temp_bs_node, q=True)[::2]
        for attr in attr_list[:-1]:
            cmds.setAttr("{0}.{1}".format(temp_bs_node, attr), -1)
        cmds.setAttr("{0}.{1}".format(temp_bs_node, attr_list[-1]), -1 * weight)

        # for attr in cmds.aliasAttr(temp_bs_node, q=True)[::2]:
        #     print("DEBUG_weight", weight)
        #     cmds.setAttr("{0}.{1}".format(temp_bs_node, attr), -1*weight)
        next_index = cmds.blendShape(temp_bs_node, q=True, wc=True)
        cmds.blendShape(temp_bs_node, edit=True, t=(stack, next_index, sculpted_mesh, 1.0), w=[next_index, 1.0],)


        # put it where the sculpted mesh is and rename it
        cmds.delete(stack, ch=True)
        parent_node = functions.getParent(sculpted_mesh)
        # print("DEBUG:", parent_node)
        if parent_node:
            # print("DEBUG:", stack)
            if functions.getParent(stack) != parent_node:
                cmds.parent(stack, parent_node)
        return (cmds.rename(stack, combination_delta))

