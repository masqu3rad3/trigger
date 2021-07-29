import importlib
import os
from copy import deepcopy
from maya import cmds
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as omAnim

from trigger.core import io
from trigger.core import filelog
from trigger.core.decorators import keepselection, tracktime, logerror
from trigger.library import functions
from trigger.library import naming
from trigger.library import deformers

from trigger.ui.Qt import QtWidgets, QtGui # for progressbar
from trigger.ui import custom_widgets
from trigger.ui import feedback

log = filelog.Filelog(logname=__name__, filename="trigger_log")


ACTION_DATA = {
                "create_deformers": True,
                "deformers": [],
                "weights_file_path": ""
               }
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

class Weights(dict):
    def __init__(self):
        super(Weights, self).__init__()
        self.io = io.IO(file_name="tmp_weights.trw")
        self["deformer"] = None
        self.isCreateDeformers = True
        self.deformers_list = []
        self.weights_file_path = ""

    @property
    def deformer(self):
        return self["deformer"]

    @deformer.setter
    def deformer(self, obj_name):
        if cmds.objExists(obj_name):
            self["deformer"] = obj_name
        else:
            log.warning("The specified object does not exists")
            return

    def set_path(self, file_path):
        self.io.file_path = file_path

    def feed(self, action_data, *args, **kwargs):
        """Mandatory method for all action modules - feeds the builder data"""
        self.isCreateDeformers = action_data.get("create_deformers")
        self.deformers_list = action_data.get("deformers")
        self.weights_file_path = action_data.get("weights_file_path")

    def action(self):
        """Mandatory method for all action modules"""
        self.io.file_path = self.weights_file_path
        data_list = self.io.read()

        base_folder, file_name_and_ext = os.path.split(self.weights_file_path)
        file_name, ext = os.path.splitext(file_name_and_ext)
        weights_folder = os.path.join(base_folder, file_name)

        for data in data_list:
            deformer = data["deformer"]
            deformer_type = data["type"]
            influencers = data.get("influencers", 0) # leave them as get for backward compatibility
            affected = data.get("affected", 0)
            deformer_weight_path = os.path.join(weights_folder, "%s.json" %deformer)
            self.create_deformer(deformer_weight_path, deformer_type=deformer_type, deformer_name=deformer, affected=affected, influencers=influencers)

    def save_action(self, file_path=None, *args, **kwargs):
        """Mandatory method for all action modules"""
        file_path = file_path or self.weights_file_path
        base_folder, file_name_and_ext = os.path.split(file_path)
        file_name, ext = os.path.splitext(file_name_and_ext)
        weights_folder = os.path.join(base_folder, file_name)
        self.io._folderCheck(weights_folder)
        # build the dictionary
        data_list = []

        for deformer in self.deformers_list:
            data = {}
            deformer_weight_path = os.path.join(weights_folder, "%s.json" %deformer)
            deformer_type = cmds.objectType(deformer)
            data["deformer"] = deformer
            data["type"] = deformer_type
            if deformer_type == "skinCluster":
                data["influencers"] = 0 # we are currently skipping this since these will be read from the weights file
                data["affected"] = cmds.listConnections("%s.outputGeometry" % deformer, shapes=True, scn=True, source=False, destination=True)
            elif deformer_type == "shrinkWrap":
                data["influencers"] = cmds.listConnections("%s.targetGeom" % deformer, shapes=True, scn=True, source=True, destination=False)
                data["affected"] = cmds.listConnections("%s.outputGeometry" % deformer, shapes=True, scn=True, source=False, destination=True)
            elif deformer_type == "deltaMush":
                data["influencers"] = 0 # not needed
                data["affected"] = cmds.listConnections("%s.outputGeometry" % deformer, shapes=True, scn=True, source=False, destination=True)
            elif deformer_type == "blendShape":
                data["influencers"] = 0 # ??? not needed ???
                data["affected"] = cmds.listConnections("%s.outputGeometry" % deformer, shapes=True, scn=True, source=False, destination=True)
            else:
                # TODO ADD OTHER DEFORMERS
                raise Exception ("The deformer type <%s> needs to be added" % deformer_type)

            data_list.append(data)
            self.save_weights(deformer=deformer, file_path=deformer_weight_path)

        self.io.file_path = file_path
        self.io.write(data_list)

    def ui(self, ctrl, layout, handler, *args, **kwargs):
        "Mandatory Method"
        # deformers = importlib.import_module("trigger.library.deformers")

        file_path_lbl = QtWidgets.QLabel(text="File Path:")
        file_path_hLay = QtWidgets.QHBoxLayout()
        # file_path_le = QtWidgets.QLineEdit()
        file_path_le = custom_widgets.FileLineEdit()
        file_path_hLay.addWidget(file_path_le)
        browse_path_pb = custom_widgets.BrowserButton(mode="openFile", update_widget=file_path_le, filterExtensions=["Trigger Weight Files (*.trw)"], overwrite_check=False)
        file_path_hLay.addWidget(browse_path_pb)
        layout.addRow(file_path_lbl, file_path_hLay)

        deformers_lbl = QtWidgets.QLabel(text="Deformers")
        deformers_listbox = custom_widgets.ListBoxLayout(alignment="start", buttonUp=False, buttonDown=False)
        layout.addRow(deformers_lbl, deformers_listbox)

        ctrl.connect(file_path_le, "weights_file_path", str)
        ctrl.connect(deformers_listbox.viewWidget, "deformers", list)

        ctrl.update_ui()

        save_current_lbl = QtWidgets.QLabel(text="Save Current states")
        savebox_lay = custom_widgets.SaveBoxLayout(alignment="horizontal", update_widget=file_path_le, filter_extensions=["Trigger Weight Files (*.trw)"], overwrite_check=True, control_model=ctrl)
        layout.addRow(save_current_lbl, savebox_lay)

        # make connections with the controller object

        def get_deformers_menu():
            list_of_deformers = list(deformers.get_deformers(namesOnly=True))

            zortMenu = QtWidgets.QMenu()
            menuActions = [QtWidgets.QAction(str(deformer)) for deformer in list_of_deformers]
            zortMenu.addActions(menuActions)
            for defo, menu_action in zip(list_of_deformers, menuActions):
                menu_action.triggered.connect(lambda ignore=defo, item=defo: add_deformers([str(item)]))
            # add a last item to add all of them
            if menuActions:
                zortMenu.addSeparator()
                allitems_menuaction = QtWidgets.QAction("Add All Items")
                zortMenu.addAction(allitems_menuaction)
                allitems_menuaction.triggered.connect(lambda x: add_deformers(list_of_deformers))

            zortMenu.exec_((QtGui.QCursor.pos()))

        def add_deformers(deformer_list):
            deformers_listbox.viewWidget.addItems(deformer_list)
            ctrl.update_model()

        def update_deformers():
            self.deformers_list = deformers_listbox.listItemNames()

        ### Signals
        file_path_le.textChanged.connect(lambda x=0: ctrl.update_model())
        browse_path_pb.clicked.connect(lambda x=0: ctrl.update_model())
        browse_path_pb.clicked.connect(file_path_le.validate)  # to validate on initial browse result
        deformers_listbox.buttonGet.clicked.connect(get_deformers_menu)
        deformers_listbox.buttonNew.clicked.connect(lambda x: ctrl.update_model())
        deformers_listbox.buttonRemove.clicked.connect(lambda x: ctrl.update_model())

        savebox_lay.saved.connect(lambda file_path: update_deformers())
        savebox_lay.saved.connect(lambda file_path: self.save_action(file_path))

    def save_weights(self, deformer=None, file_path=None, vertexConnections=False, force=True, influencer=None):
        if not deformer and not self.deformer:
            log.error("Cannot save the weight %s \nNo Deformer defined. A Deformer needs to be defined either as argument or class variable)" % file_path)
        if not deformer:
            deformer = self.deformer
        if not force:
            if os.path.isfile(file_path):
                log.warning("This file already exists. Skipping")
                return False
        # Vertex connections is required for barycentric and bilinear modes when loading
        if not file_path:
            file_dir, file_name = os.path.split(self.io.file_path)
        else:
            file_dir, file_name = os.path.split(file_path)
        # extra attributes for recreation
        deformer_type = cmds.objectType(deformer)
        export_dq_weights = False
        if deformer_type == "skinCluster":
            attributes = ["envelope", "skinningMethod", "useComponents", "normalizeWeights", "deformUserNormals"]
            # in case DQ blendweight mode, flag for adding DQ to the file afterwards
            if cmds.getAttr("%s.skinningMethod" % deformer) == 2:
                export_dq_weights = True
        elif deformer_type == "shrinkWrap":
            attributes = ["projection", "closestIfNoIntersection", "reverse", "bidirectional", "offset", "targetInflation",
                          "axisReference", "alongX", "alongY", "alongZ", "targetSmoothLevel", "falloff", "falloffIterations",
                          "shapePreservationEnable", "shapePreservationSteps", "shapePreservationIterations",
                          "shapePreservationMethod", "shapePreservationReprojection"]
        elif deformer_type == "deltaMush":
            # attributes = []
            attributes = ["smoothingIterations", "smoothingStep", "inwardConstraint", "outwardConstraint", "distanceWeight", "displacement"]
        else:
            attributes = []
        # TODO: ADD ATTRIBUTES FOR ALL DEFORMER TYPES

        # default value -1 means export all weights!
        cmds.deformerWeights(file_name, export=True, deformer=deformer, path=file_dir, defaultValue=-1.0, vc=vertexConnections, at=attributes)

        if export_dq_weights:
            self.io.file_path = os.path.join(file_dir, file_name)
            data = self.io.read()
            # data["DQ_weights"] = cmds.getAttr("%s.ptw" % deformer[0])
            data["DQ_weights"] = cmds.getAttr("%s.ptw" % deformer)
            self.io.write(data)

        # there is no argument to define the influencer while exporting.
        # If a specific influencer needs to be exported, strip the rest after the file exported.
        if influencer:
            # read the exported data
            self.io.file_path = os.path.join(file_dir, file_name)
            data = self.io.read()
            operation_data = deepcopy(data)
            # do the surgery
            for weight_data_dict in data["deformerWeight"]["weights"]:
                if weight_data_dict["source"] != influencer:
                    operation_data["deformerWeight"]["weights"].remove(weight_data_dict)
            operation_data["deformerWeight"]["weights"][0]["layer"] = 0
            self.io.write(operation_data)

        log.info("File exported to %s successfully..." % os.path.join(file_dir, file_name))
        return True

    @keepselection
    def load_weights(self, deformer=None, file_path=None, method="index", ignore_name=True):
        if not deformer and not self.deformer:
            log.error(
                "No Deformer defined. A Deformer needs to be defined either as argument or class variable)")
        if not deformer:
            deformer = self.deformer

        if not file_path:
            file_dir, file_name = os.path.split(self.io.file_path)
        else:
            file_dir, file_name = os.path.split(file_path)

        cmds.deformerWeights(file_name, im=True, deformer=deformer, path=file_dir, method=method, ignoreName=ignore_name)

        # this is a bug I came across one with one test geo.
        # Somehow it does not assign the value to index: 0
        # the following part forces to assign the correct value to index 0
        self.io.file_path = os.path.join(file_dir, file_name)
        data = self.io.read()
        deformer_type = cmds.objectType(deformer)
        if deformer_type == "blendShape":
            point_attr_template = "{0}.inputTarget[0].inputTargetGroup[{1}].targetWeights[0]"
        # elif deformer_type == "ffd" or deformer_type == "shrinkWrap" or deformer_type == "deltaMush":
        #     point_attr_template = "{0}.weightList[{1}].weights[0]"
        elif deformer_type == "skinCluster":
            skin_meshes = cmds.listConnections(deformer, type="mesh")
            for mesh in skin_meshes:
                # Skin cluster weight loading has a bug - Its not loading the value of the first vertex
                cmds.select("%s.vtx[0]" % mesh)
                cmds.WeightHammer()
            if data.get("DQ_weights"):
                for nmb, weight in enumerate(data["DQ_weights"]):
                    cmds.setAttr('%s.bw[%s]' % (deformer, nmb), weight)
            # cmds.select(d=True)
            log.info("%s Weights Lodaded Successfully..." %deformer)
            return
            # point_attr_template = "{0}.weightList[{1}].weights[0]"
        else:
            point_attr_template = "{0}.weightList[{1}].weights[0]"

        for nmb, weight_dict in enumerate(data["deformerWeight"]["weights"]):
            index0_val = weight_dict["points"][0]["value"]
            # cmds.setAttr("%s.inputTarget[0].inputTargetGroup[%i].targetWeights[0]" % (deformer, nmb), index0_val)
            cmds.setAttr(point_attr_template.format(deformer, nmb), index0_val)
            # splitMaps_blendshape.inputTarget[0].inputTargetGroup[X].targetWeights[0]

        log.info("%s Weights Lodaded Successfully..." %deformer)
        return True

    def create_deformer(self, weights_file, deformer_type=None, force_unique_deformer=False, deformer_name=None, affected=None, influencers=None):
        """
        Creates the deformer defined in the weights file and applies the pre-saved weights.

        If a deformer with the same name exists, it uses that instead of creating

        Main function to re-create rig weights.
        Args:
            weights_file: (String) Path to the weights file save with
            deformer_type: (String) If the weights file does not contain the deformer type information this flag will
                    be used to identify the deformer type
            force_unique_deformer: (Bool) If True, in case of scene contains a node with the same name, it uses a
                    unique name instead. Otherwise it will throw an error

        Returns:

        """

        # load the weights file
        self.io.file_path = weights_file
        weights_data = self.io.read()

        weights_list = weights_data["deformerWeight"].get("weights", [])
        # get the deformer name
        if not weights_list and not deformer_name:
            log.error("deformer name cannot be obtained from file")
            raise

        deformer_name = deformer_name or weights_list[0]["deformer"]
        if force_unique_deformer:
            deformer_name = naming.uniqueName(deformer_name)

        # if the affected object does not have the deformer, create a new one
        if not cmds.objExists(deformer_name):
            deformer_info = weights_data["deformerWeight"].get("deformers")
            if not deformer_info and not deformer_type:
                log.error("Cannot identify the deformer type. Use the flag 'deformer_type' or export the weights with additional attributes")

            if deformer_info:
                deformer_type = weights_data["deformerWeight"]["deformers"][0]["type"]
                deformer_attrs = weights_data["deformerWeight"]["deformers"][0]["attributes"] # this is list of dictionaries
            else:
                deformer_attrs = []

            if deformer_type == "skinCluster":
                # collect the influencers (eg. joints if it is a skinCluster)
                influencers = [weight_dict.get("source") for weight_dict in weights_list]
                # first try the custom affected input. If there is none (backward-compatibility) use the weight data
                if not affected:
                    affected = functions.uniqueList([weight_dict.get("shape") for weight_dict in weights_list])
                # delete existing skin clusters first
                affected_history = cmds.listHistory(affected[0], pdo=True)
                old_skincluster = cmds.ls(affected_history, type="skinCluster")
                if old_skincluster:
                    cmds.delete(old_skincluster)
                deformer = cmds.skinCluster(influencers, affected[0], name=deformer_name, tsb=True)[0]

            elif deformer_type == "shrinkWrap":
                deformers.create_shrink_wrap(influencers[0], affected[0], name=deformer_name)

            elif deformer_type == "deltaMush":
                cmds.deltaMush(affected[0], name=deformer_name)

            else:
                # TODO : SUPPORT FOR ALL DEFORMERS
                log.error("deformers OTHER than skinCluster, shrinkWrap and deltaMush are not YET supported")
                return
            for attr_dict in deformer_attrs:
                attr_name = attr_dict["name"]
                attr_type = attr_dict["type"]
                # attr_value = float(attr_dict["value"]) # THIS IS NOT BULLET-PROOF
                if attr_type == "short":
                    attr_value = int(attr_dict["value"])
                elif attr_type == "doubleLinear":
                    attr_value = float(attr_dict["value"])
                elif attr_type == "bool":
                    attr_value = bool(attr_dict["value"])
                elif attr_type == "enum":
                    attr_value = int(attr_dict["value"])
                elif attr_type == "string":
                    attr_value = str(attr_dict["value"])
                elif attr_type == "float":
                    attr_value = float(attr_dict["value"])
                elif attr_type == "long":
                    attr_value = int(attr_dict["value"])
                else:
                    log.error("Undefined attribute type => %s" %attr_type)
                    raise

                cmds.setAttr("%s.%s" % (deformer_name, attr_name), attr_value)

        # finally load weights
        self.load_weights(deformer=deformer_name, file_path=weights_file, method="index", ignore_name=False)


        pass

    def save_matching_weights(self, deformer=None, file_path=None, vertexConnections=False, force=True, influencer=None):
        """
        Saves the weights AND the negated weights to the disk
        Args:
            deformer: Deformer node. If not specified, it will try to use the class variable.
            file_path: (String) Absolute File path. If not defined the class variable will be used
            vertexConnections: (Bool) defines whether or not to define Vertex Connections in the file. Required for Barycentric
            and Bilinear methods while loading

        Returns: (list) file locations for normal and negated weights

        """
        if not file_path:
            file_dir, file_name = os.path.split(self.io.file_path)
        else:
            file_dir, file_name = os.path.split(file_path)

        state = self.save_weights(deformer=deformer, file_path=os.path.join(file_dir, file_name), vertexConnections=vertexConnections, force=force, influencer=influencer)
        if not state:
            return

        name, extension = os.path.splitext(file_name)
        f_path = os.path.join(file_dir, extension)
        cmds.refresh()
        positive_weights_path = os.path.join(file_dir, file_name)
        temp_io= io.IO(file_path=positive_weights_path)
        to_be_negated = temp_io.read()
        negative_weights_path = "%sN%s" % (os.path.join(file_dir, name), extension)
        temp_io.file_path = negative_weights_path
        negated_weights = self.negateWeights(to_be_negated)
        temp_io.write(negated_weights)
        return (positive_weights_path, negative_weights_path)


    def negateWeights(self, json_data, influencer=None):
        """Negates the weights in json_data"""

        weights_list = None
        if not influencer:
            weights_list = json_data["deformerWeight"]["weights"]
        else:
            # find the influencer weights:
            for weights in json_data["deformerWeight"]["weights"]:
                if weights["source"] == influencer:
                    weights_list = [weights]
        if not weights_list:
            print("Cannot find the influencer")
            return
        for weights in weights_list:
            for vert in weights["points"]:
                vert["value"]=1-vert["value"]
        return json_data

    def multiplyWeights(self, data_list, influencer=None):
        """Multiplies the weights in the data list"""
        # take a copy of the first data list
        copy_data = deepcopy(data_list[0])
        # the json_datas in data_list must belong to the same deformer (same point count)
        for weights_list_nmb, weights in enumerate(copy_data["deformerWeight"]["weights"]):
            if influencer and weights["source"] != influencer:
                continue
            for point_nmb, point in enumerate(weights["points"]):
                point_values = []
                for data_list_nmb, json_data in enumerate(data_list):
                    val = json_data["deformerWeight"]["weights"][weights_list_nmb]["points"][point_nmb]["value"]
                    point_values.append(val)
                point["value"] = multiplyList(point_values)
        return copy_data

    def addWeights(self, data_list, influencer=None, clamp=True):
        # TODO : not tested
        copy_data = deepcopy(data_list[0])
        for weights_list_nmb, weights in enumerate(copy_data["deformerWeight"]["weights"]):
            if influencer and weights["source"] != influencer:
                continue
            for point_nmb, point in enumerate(weights["points"]):
                point_values = []
                for data_list_nmb, json_data in enumerate(data_list):
                    val = json_data["deformerWeight"]["weights"][weights_list_nmb]["points"][point_nmb]["value"]
                    point_values.append(val)
                point["value"] = addList(point_values)
                if clamp:
                    point["value"] = max(min(point["value"], 1.0), 0.0)
        return copy_data

    def subtractWeights(self, data_list, influencer=None, clamp=True):
        # TODO : not tested
        copy_data = deepcopy(data_list[0])
        for weights_list_nmb, weights in enumerate(copy_data["deformerWeight"]["weights"]):
            if influencer and weights["source"] != influencer:
                continue
            for point_nmb, point in enumerate(weights["points"]):
                point_values = []
                for data_list_nmb, json_data in enumerate(data_list):
                    val = json_data["deformerWeight"]["weights"][weights_list_nmb]["points"][point_nmb]["value"]
                    point_values.append(val)
                point["value"] = subtractList(point_values)
                if clamp:
                    point["value"] = max(min(point["value"], 1.0), 0.0)
        return copy_data


def get_plug_ids(mesh, source_deformer, source_influence=None):
    node_type = cmds.nodeType(source_deformer)

    # target_num = 0
    if node_type == "blendShape":
        if source_influence == "baseWeights":
            weight_plug = "{}.inputTarget[0].baseWeights"
        else:
            targets = cmds.aliasAttr(source_deformer, query=True)
            target_names = targets[::2]
            target_weight = targets[1::2]
            target_index = target_names.index(source_influence)
            target_num = (target_weight[target_index].split("[")[1].split("]")[0])
            weight_plug = "{}.inputTarget[0].inputTargetGroup[%s].targetWeights" %str(target_num)
    elif node_type == "nonLinear" or node_type == "cluster":
        weight_plug = "{}.weightList[0].weights"
    elif node_type == "skinCluster":
        weight_plug = "{0}.weightList[0].weights"
    else:
        raise Exception ("deformer not identified => %s" %source_deformer)

    sel = om.MSelectionList()
    sel.add(weight_plug.format(source_deformer))
    plug = sel.getPlug(0)

    vtx_count = cmds.polyEvaluate(mesh, vertex=True)
    return plug, vtx_count




def get_influence_weights(mesh, deformer, influence, skip_checks=False):
    """Gets the weights for given influence object

    Args:
        mesh (str): Shape or transform Node
        deformer (str): Source deformer
        influence (str): Influence object

    Returns:
        list: [<list of weights for given influence>]

    """
    node_type = cmds.nodeType(deformer)
    if not skip_checks:
        if not cmds.objExists(mesh):
            msg = "{0} => does not exists".format(mesh)
            cmds.error(msg)
        # fool proof for non-mathcing mesh/deformers
        all_deformers = collect_deformers(mesh)

        if deformer not in all_deformers[node_type]:
            msg = "{0} either does not exist or not deforming {1}".format(deformer, mesh)
            cmds.error(msg)

    if node_type == "skinCluster":
        # get nodes
        node_dag = (
            om.MSelectionList().add(mesh).getDagPath(0).extendToShape()
        )
        skin_cluster_obj = (
            om.MSelectionList().add(deformer).getDependNode(0)
        )
        mfn_skc = omAnim.MFnSkinCluster(skin_cluster_obj)

        components = om.MFnSingleIndexedComponent().create(
            om.MFn.kMeshVertComponent
        )

        # get influence index
        skin_cluster_obj = (om.MSelectionList().add(deformer).getDependNode(0))
        influence_dag = om.MSelectionList().add(influence).getDagPath(0)
        index = int(omAnim.MFnSkinCluster(skin_cluster_obj).indexForInfluenceObject(influence_dag))

        # Get weights
        weights = mfn_skc.getWeights(node_dag, components, om.MIntArray([index]))

        return list(weights)

    if node_type == "nonLinear" or node_type == "cluster":
        influence = None # these deformers dont have seperate influencers

    plug, vtx_count = get_plug_ids(mesh, deformer, influence)

    weights = [plug.elementByLogicalIndex(i).asDouble() for i in range(vtx_count)]
    return weights


def get_all_weights(mesh, deformer):
    """Collects the weight data for the given deformer
    
    Args:
        mesh (str): Shape or transform Node
        deformer (str): Source deformer

    Returns:
        dictionary: {<influence>: [weights_list]}

    """
    # TODO : complete the function or merge with "get_imfluence_weights"
    node_type = cmds.nodeType(deformer)
    if node_type == "skinCluster":
        pass

    if node_type == "nonLinear" or node_type == "cluster":
        # these have only single influences
        weight_dictionary = {"baseWeights": get_influence_weights(mesh, deformer, None, skip_checks=True)}
        pass
    if node_type == "blendShape":
        # pass
        # get all the influences
        all_influences = ["baseWeights"]
        all_influences.extend(cmds.aliasAttr(deformer, query=True)[::2])
        weight_dictionary = {influence: get_influence_weights(mesh, deformer, influence, skip_checks=True) for influence in all_influences}

    return weight_dictionary

#########################################################################
#########################################################################
#########################################################################
#########################################################################
#########################################################################
#########################################################################

def get_skincluster_influence_index(skin_cluster, influence):
    """Get the index of given influence.

    Args:
        skin_cluster (str): skinCluster node
        influence (str): influence object

    Return:
        int: index
    """
    skin_cluster_obj = (
        OpenMaya.MSelectionList().add(skin_cluster).getDependNode(0)
    )
    influence_dag = OpenMaya.MSelectionList().add(influence).getDagPath(0)
    index = int(
        OpenMayaAnim.MFnSkinCluster(
            skin_cluster_obj
        ).indexForInfluenceObject(influence_dag)
    )

    return index


def set_deformer_weights(mesh, target_deformer, list_of_weights, target_influence, data_type="double"):
    plug, vtx_count = get_plug_ids(mesh, target_deformer, target_influence)

    if data_type == "double":
        # TODO: map function with LAMBDA may be slower than for loop
        # or list comprehension. Test it
        map(
            lambda i: plug.elementByLogicalIndex(i).setDouble(
                list_of_weights[i]
            ),
            range(len(list_of_weights)),
        )
    elif data_type == "float":
        map(
            lambda i: plug.elementByLogicalIndex(i).setFloat(
                list_of_weights[i]
            ),
            range(len(list_of_weights)),
        )

    return list_of_weights

def get_deformer_weights(mesh, source_deformer, source_influence=None, data_type="double"):
    node_type = cmds.nodeType(source_deformer)
    if node_type == "skinCluster":
        # get nodes
        node_dag = (
            om.MSelectionList().add(mesh).getDagPath(0).extendToShape()
        )
        skin_cluster_obj = (
            om.MSelectionList().add(source_deformer).getDependNode(0)
        )
        mfn_skc = omAnim.MFnSkinCluster(skin_cluster_obj)

        components = om.MFnSingleIndexedComponent().create(
            om.MFn.kMeshVertComponent
        )

        # get influence index
        skin_cluster_obj = (om.MSelectionList().add(source_deformer).getDependNode(0))
        influence_dag = om.MSelectionList().add(source_influence).getDagPath(0)
        index = int(omAnim.MFnSkinCluster(skin_cluster_obj).indexForInfluenceObject(influence_dag))

        # Get weights
        weights = mfn_skc.getWeights(node_dag, components, om.MIntArray([index]))

        return list(weights)

    plug, vtx_count = get_plug_ids(mesh, source_deformer, source_influence)

    # reading
    if data_type == "double":
        weight_list = [
            plug.elementByLogicalIndex(i).asDouble()
            for i in range(vtx_count)
        ]
    elif data_type == "float":
        weight_list = [
            plug.elementByLogicalIndex(i).asFloat()
            for i in range(vtx_count)
        ]

    return weight_list

