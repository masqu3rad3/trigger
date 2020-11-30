"""Auto splitting action for symmetrical blendshapes inherits Weights action"""

import os

from maya import cmds

from trigger.core import io
from trigger.actions import weights
from trigger.library import deformers
from trigger.ui import custom_widgets
from trigger.ui.Qt import QtWidgets, QtGui
from trigger.ui import feedback
from trigger.core import logger
from trigger.utils import shape_splitter

LOG = logger.Logger()

ACTION_DATA = {
    "split_maps_file_path": "",
    "blendshapes_root_group": "",
    "neutral_mesh": "",
    "split_data1": [],
}


class Split_shapes(weights.Weights):
    def __init__(self, *args, **kwargs):
        super(Split_shapes, self).__init__()
        self.io = io.IO(file_name="tmp_shape_maps.trw")
        self.splitMapsFilePath = ""
        self.blendshapeRootGrp = ""
        self.neutralMesh = ""
        self.splitDatas = []

        # instantiate class objects
        self.splitter = shape_splitter.Splitter()
        self.paintMapBs = None

    def feed(self, action_data, *args, **kwargs):
        """Feeds the instance with the action data stored in actions session"""
        self.splitMapsFilePath = action_data.get("split_maps_file_path")
        self.blendshapeRootGrp = action_data.get("blendshapes_root_group")
        self.neutralMesh = action_data.get("neutral_mesh")
        for key, value in action_data.items():
            if key.startswith("split_data") and value:
                tdict = {"mesh": value[0],
                         "maps": value[1:]}
                self.splitDatas.append(tdict)



    def action(self):
        """Execute Action - Mandatory"""
        pass

    # def save_action(self):
    #     """Save Action - Mandatory"""
    #     base_folder, file_name_and_ext = os.path.split(self.splitMapsFilePath)
    #     file_name, ext = os.path.splitext(file_name_and_ext)
    #     split_maps_folder = os.path.join(base_folder, file_name)
    #     self.io._folderCheck(split_maps_folder)
    #
    #     pass

    def ui(self, ctrl, layout, handler, *args, **kwargs):
        """UI - Mandatory"""
        file_path_lbl = QtWidgets.QLabel(text="Split Maps Path:")
        file_path_hLay = QtWidgets.QHBoxLayout()
        file_path_le = QtWidgets.QLineEdit()
        file_path_hLay.addWidget(file_path_le)
        browse_path_pb = custom_widgets.BrowserButton(mode="openFile", update_widget=file_path_le, filterExtensions=["Trigger Weight Files (*.trw)"], overwrite_check=False)
        file_path_hLay.addWidget(browse_path_pb)
        layout.addRow(file_path_lbl, file_path_hLay)

        deformers_lbl = QtWidgets.QLabel(text="Split Map Blendshape")
        deformers_hLay = QtWidgets.QHBoxLayout()
        deformers_le = QtWidgets.QLineEdit()
        deformers_hLay.addWidget(deformers_le)
        prepare_bs_pb = QtWidgets.QPushButton(text="Prepare")
        deformers_hLay.addWidget(prepare_bs_pb)
        get_deformers_pb = QtWidgets.QPushButton(text="Get")
        deformers_hLay.addWidget(get_deformers_pb)
        layout.addRow(deformers_lbl, deformers_hLay)

        save_current_lbl = QtWidgets.QLabel(text="Save Split Maps")
        save_current_hlay = QtWidgets.QHBoxLayout()
        save_current_pb = QtWidgets.QPushButton(text="Save")
        increment_current_pb = QtWidgets.QPushButton(text="Increment")
        save_as_current_pb = custom_widgets.BrowserButton(mode="saveFile", text="Save As", update_widget=file_path_le, filterExtensions=["Trigger Weight Files (*.trw)"], overwrite_check=False)
        save_current_hlay.addWidget(save_current_pb)
        save_current_hlay.addWidget(increment_current_pb)
        save_current_hlay.addWidget(save_as_current_pb)
        layout.addRow(save_current_lbl, save_current_hlay)

        blendshapes_group_lbl = QtWidgets.QLabel(text="Blendshapes Root Group")
        blendshapes_group_le = QtWidgets.QLineEdit()

        ctrl.connect(file_path_le, "split_maps_file_path", str)
        ctrl.update_ui()

        def prepare_bs():
            self.paintMapBs = self.splitter.prepare_for_painting(cmds.ls(sl=True)[0])
            deformers_le.setText(self.paintMapBs)
            ctrl.update_model()

        def get_deformers_menu():
            list_of_deformers = list(deformers.get_deformers(namesOnly=True))
            if "splitMaps_blendshape" in list_of_deformers:
                self.paintMapBs = "splitMaps_blendshape"
                deformers_le.setText(self.paintMapBs)
                ctrl.update_model()


        #     zortMenu = QtWidgets.QMenu()
        #     menuActions = [QtWidgets.QAction(str(deformer)) for deformer in list_of_deformers]
        #     zortMenu.addActions(menuActions)
        #     for defo, menu_action in zip(list_of_deformers, menuActions):
        #         menu_action.triggered.connect(lambda ignore=defo, item=defo: add_deformers([str(item)]))
        #     # add a last item to add all of them
        #     if menuActions:
        #         zortMenu.addSeparator()
        #         allitems_menuaction = QtWidgets.QAction("Add All Items")
        #         zortMenu.addAction(allitems_menuaction)
        #         allitems_menuaction.triggered.connect(lambda x: add_deformers(list_of_deformers))
        #
        #     zortMenu.exec_((QtGui.QCursor.pos()))
        #
        # def add_deformers(deformer_list):
        #     current_deformers_text = deformers_le.text()
        #     if current_deformers_text:
        #         for deformer in deformer_list:
        #             if deformer in current_deformers_text:
        #                 LOG.warning("%s is already in the list" % deformer)
        #                 deformer_list.remove(deformer)
        #         new_deformers_text = "; ".join([current_deformers_text] + deformer_list)
        #     else:
        #         new_deformers_text = "; ".join(deformer_list)
        #     deformers_le.setText(new_deformers_text)
        #     ctrl.update_model()

        def save_deformers(increment=False, save_as=False):
            if increment:
                LOG.warning("NOT YET IMPLEMENTED")
                ctrl.update_ui()
                # TODO make an external incrementer
            elif save_as:
                ctrl.update_model()
                if not file_path_le.text():
                    return
                handler.run_save_action(ctrl.action_name)
            else:
                ctrl.update_model()
                if not file_path_le.text():
                    save_as_current_pb.browserEvent()
                    save_deformers(save_as=True)
                    return
                if os.path.isfile(file_path_le.text()):
                    question = feedback.Feedback()
                    state = question.pop_question(title="Overwrite", text="The file %s already exists.\nDo you want to OVERWRITE?" %file_path_le.text(), buttons=["ok", "cancel"])
                    if state == "cancel":
                        return
                handler.run_save_action(ctrl.action_name)

        ### Signals
        file_path_le.editingFinished.connect(lambda x=0: ctrl.update_model())
        browse_path_pb.clicked.connect(lambda x=0: ctrl.update_model())
        deformers_le.editingFinished.connect(lambda x=0: ctrl.update_model())
        prepare_bs_pb.clicked.connect(prepare_bs)
        get_deformers_pb.clicked.connect(get_deformers_menu)
        get_deformers_pb.clicked.connect(lambda x=0: ctrl.update_model())

        save_current_pb.clicked.connect(lambda x=0: save_deformers())
        increment_current_pb.clicked.connect(lambda x=0: save_deformers(increment=True))
        save_as_current_pb.clicked.connect(lambda x=0: save_deformers(save_as=True))