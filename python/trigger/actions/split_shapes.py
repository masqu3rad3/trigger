"""Auto splitting action for symmetrical blendshapes inherits Weights action"""

import os

from maya import cmds

from trigger.core import io
from trigger.actions import weights
from trigger.library import deformers, functions, selection
from trigger.ui import custom_widgets
from trigger.ui.widgets.browser import BrowserButton, FileLineEdit
from trigger.ui.layouts.save_box import SaveBoxLayout
from trigger.ui.Qt import QtWidgets
from trigger.ui import feedback
from trigger.core import filelog
from trigger.core.action import ActionCore

from trigger.utils import shape_splitter

log = filelog.Filelog(logname=__name__, filename="trigger_log")


ACTION_DATA = {
    "split_maps_file_path": "",
    "blendshapes_root_group": "",
    "neutral_mesh": "",
    "split_data": {},
}


class Split_shapes(weights.Weights):
    def __init__(self):
        super(Split_shapes, self).__init__()
        self.io = io.IO(file_name="tmp_shape_maps.trsplit")
        self.splitMapsFilePath = ""
        self.blendshapeRootGrp = ""
        self.neutralMesh = ""
        self.splitData = {}

        # instantiate class objects
        self.splitter = shape_splitter.Splitter()
        self.paintMapBs = None

    def feed(self, action_data, *args, **kwargs):
        """Feeds the instance with the action data stored in actions session"""
        self.splitMapsFilePath = action_data.get("split_maps_file_path")
        self.blendshapeRootGrp = action_data.get("blendshapes_root_group")
        self.neutralMesh = action_data.get("neutral_mesh")
        self.splitData = action_data.get("split_data")

    def action(self):
        """Execute Action - Mandatory"""
        if (
            not self.splitMapsFilePath
            or not self.blendshapeRootGrp
            or not self.neutralMesh
            or not self.splitData
        ):
            raise Exception("MISSING ACTION DATA IN SPLIT SHAPES ")

        # instanciate class object
        splitter = shape_splitter.Splitter()
        split_grp = "SPLITTED_SHAPES_grp"
        if not cmds.objExists(split_grp):
            split_grp = cmds.group(name=split_grp, em=True)
        splitter.splittedShapesGrp = "SPLITTED_SHAPES_grp"

        # define neutral
        splitter.neutral = self.neutralMesh

        # add the blendshapes
        meshes = functions.get_meshes(self.blendshapeRootGrp)
        splitter.clear_blendshapes()
        splitter.add_blendshapes(meshes=meshes)

        splitter.clear_splitmaps()
        file_root, basename_with_ext = os.path.split(self.splitMapsFilePath)
        maps_folder_name, ext = os.path.splitext(basename_with_ext)
        import_root = os.path.join(file_root, maps_folder_name)
        if not os.path.isdir(import_root):
            raise Exception("Maps folder does not exist")
        split_maps = self.io.read(self.splitMapsFilePath)
        for split_map in split_maps:
            # add available split maps
            splitter.add_splitmap(os.path.join(import_root, "%s.json" % split_map))

        # Define Split Maps
        dead_list = []
        for mesh_name, split_maps in self.splitData.items():
            splitter.set_splitmap(mesh_name, split_maps)
            if not split_maps:
                cmds.parent(mesh_name, splitter.splittedShapesGrp)
            else:
                dead_list.append(mesh_name)

        splitter.split_shapes()
        _ = [functions.delete_object(x) for x in dead_list]

    def save_action(self, file_path=None, *args, **kwargs):
        file_path = file_path or self.splitMapsFilePath

        base_folder, file_name_and_ext = os.path.split(file_path)
        file_name, ext = os.path.splitext(file_name_and_ext)
        weights_folder = os.path.join(base_folder, file_name)
        self.io.folder_check(weights_folder)

        # build the deformers list from the influencers
        if not self.paintMapBs:
            if cmds.objExists("splitMaps_blendshape"):
                self.paintMapBs = "splitMaps_blendshape"
            else:
                feedback.Feedback().pop_info(
                    title="Cannot find Blendshape",
                    text="splitMaps blendshape cannot be found",
                )
        influencers = deformers.get_influencers(self.paintMapBs)
        for influencer in influencers:
            inf_file_path = os.path.join(weights_folder, "%s.json" % influencer)
            self.io.file_path = inf_file_path
            self.save_matching_weights(deformer=self.paintMapBs, influencer=influencer)

        self.io.file_path = file_path
        self.io.write(influencers)

        # export the whole weights for future paint fixes
        whole_weights_path = os.path.join(weights_folder, "wholeWeights.json")
        self.save_weights(
            deformer=self.paintMapBs,
            file_path=whole_weights_path,
        )

    def ui(self, ctrl, layout, handler, *args, **kwargs):
        """UI - Mandatory"""
        file_path_lbl = QtWidgets.QLabel(text="Split Maps Path:")
        file_path_hLay = QtWidgets.QHBoxLayout()
        file_path_le = FileLineEdit()
        file_path_hLay.addWidget(file_path_le)
        prepare_bs_pb = QtWidgets.QPushButton(text="Prepare")
        file_path_hLay.addWidget(prepare_bs_pb)
        browse_path_pb = BrowserButton(
            mode="openFile",
            update_widget=file_path_le,
            filterExtensions=["Trigger Split Files (*.trsplit)"],
            overwrite_check=False,
        )
        file_path_hLay.addWidget(browse_path_pb)
        layout.addRow(file_path_lbl, file_path_hLay)

        save_current_lbl = QtWidgets.QLabel(text="Save Current states")
        savebox_lay = SaveBoxLayout(
            alignment="horizontal",
            update_widget=file_path_le,
            filter_extensions=["Trigger Split Files (*.trsplit)"],
            overwrite_check=True,
            control_model=ctrl,
        )
        layout.addRow(save_current_lbl, savebox_lay)

        blendshapes_group_lbl = QtWidgets.QLabel(text="Blendshapes Root Group:")
        blendshapes_group_le = QtWidgets.QLineEdit()
        layout.addRow(blendshapes_group_lbl, blendshapes_group_le)

        neutral_mesh_lbl = QtWidgets.QLabel(text="Neutral Mesh:")
        neutral_mesh_le = QtWidgets.QLineEdit()
        layout.addRow(neutral_mesh_lbl, neutral_mesh_le)

        split_definitions_lbl = QtWidgets.QLabel(text="Split Definitions:")
        split_definitions_treeBox = custom_widgets.TreeBoxLayout(
            buttonAdd=False, buttonNew=True
        )
        split_definitions_treeBox.viewWidget.setMinimumHeight(300)

        def on_add():
            dialog = QtWidgets.QDialog()
            dialog.setModal(True)
            master_layout = QtWidgets.QVBoxLayout()
            dialog.setLayout(master_layout)
            form_layout = QtWidgets.QFormLayout()
            master_layout.addLayout(form_layout)

            key_lbl = QtWidgets.QLabel(text="Mesh")
            key_le = QtWidgets.QLineEdit()
            # if the selection is a mesh, get the name
            sel = cmds.ls(sl=True, type="transform")
            if sel:
                key_le.setText(sel[0])
            form_layout.addRow(key_lbl, key_le)

            value_lbl = QtWidgets.QLabel(text="Split Maps")
            value_listbox = custom_widgets.ListBoxLayout(buttonGet=False)
            if file_path_le.text():
                split_maps = self.io.read(file_path=file_path_le.text())
                if split_maps:
                    value_listbox.buttonNew.setHidden(True)
                    value_listbox.buttonRename.setHidden(True)
                for smap in split_maps:
                    extra_button = QtWidgets.QPushButton(text=smap)
                    value_listbox.buttonslayout.addWidget(extra_button)
                    extra_button.clicked.connect(
                        lambda ignore=0, val=smap: value_listbox.viewWidget.addItem(
                            str(val)
                        )
                    )
            form_layout.addRow(value_lbl, value_listbox)

            button_box = QtWidgets.QDialogButtonBox(dialog)
            button_box.setStandardButtons(
                QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok
            )
            master_layout.addWidget(button_box)

            # Signals
            button_box.accepted.connect(
                lambda x=0: split_definitions_treeBox._add_tree_item(
                    key_le.text(), value_listbox.listItemNames()
                )
            )
            button_box.accepted.connect(dialog.close)
            button_box.rejected.connect(dialog.close)

            dialog.exec_()

            # ctrl.update_model()

        split_definitions_treeBox._on_new = on_add
        layout.addRow(split_definitions_lbl, split_definitions_treeBox)

        ctrl.connect(file_path_le, "split_maps_file_path", str)
        ctrl.connect(blendshapes_group_le, "blendshapes_root_group", str)
        ctrl.connect(neutral_mesh_le, "neutral_mesh", str)
        ctrl.connect(split_definitions_treeBox.viewWidget, "split_data", dict)
        ctrl.update_ui()

        def prepare_bs():
            sel, msg = selection.validate(
                minimum=1, maximum=1, meshes_only=True, transforms=True, full_path=False
            )
            if not sel:
                feedback.Feedback().pop_info(
                    title="Selection Error", text=msg, critical=True
                )
                return
            self.paintMapBs = self.splitter.prepare_for_painting(sel[0])
            file_path = file_path_le.text()
            # if there is a wholeWeights.json file, use that to get back the pre-painted values
            if file_path and os.path.isfile(file_path):
                file_root, basename_with_ext = os.path.split(file_path)
                maps_folder_name, ext = os.path.splitext(basename_with_ext)
                import_root = os.path.join(file_root, maps_folder_name)
                whole_weights_file = os.path.join(import_root, "wholeWeights.json")
                if os.path.isfile(whole_weights_file):
                    self.load_weights(
                        deformer=self.paintMapBs, file_path=whole_weights_file
                    )
            ctrl.update_model()

        ### Signals
        file_path_le.textChanged.connect(lambda x=0: ctrl.update_model())
        browse_path_pb.clicked.connect(lambda x=0: ctrl.update_model())
        browse_path_pb.clicked.connect(
            file_path_le.validate
        )  # to validate on initial browse result
        prepare_bs_pb.clicked.connect(prepare_bs)

        savebox_lay.saved.connect(lambda file_path: self.save_action(file_path))

        blendshapes_group_le.editingFinished.connect(lambda x=0: ctrl.update_model())
        neutral_mesh_le.editingFinished.connect(lambda x=0: ctrl.update_model())

        split_definitions_treeBox.buttonNew.clicked.connect(
            lambda x=0: ctrl.update_model()
        )
        split_definitions_treeBox.buttonRemove.clicked.connect(
            lambda x=0: ctrl.update_model()
        )
        split_definitions_treeBox.buttonClear.clicked.connect(
            lambda x=0: ctrl.update_model()
        )
        split_definitions_treeBox.buttonRename.clicked.connect(
            lambda x=0: ctrl.update_model()
        )
