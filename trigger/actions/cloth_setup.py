"""Prepares Cloth Sim Setup"""

import os
from maya import cmds
from maya import mel
from trigger.core import logger
import trigger.library.functions as functions
import trigger.library.controllers as ic

from trigger.ui.Qt import QtWidgets, QtGui # for progressbar
from trigger.ui import feedback

LOG = logger.Logger(logger_name=__name__)

ACTION_DATA = {
    "cloth_objects": [],
    "collider_objects": [],
    "motion_multiplier_vertices": [],
}

class Cloth_setup(object):
    def __init__(self, *args, **kwargs):
        super(Cloth_setup, self).__init__()
        self.clothObjects = []
        self.colliderObjects = []
        self.motionMultiplierVertices = []

    def feed(self, action_data):
        """Feeds the instance with the action data stored in actions session"""
        self.clothObjects = action_data.get("cloth_objects")
        self.colliderObjects = action_data.get("collider_objects")
        self.motionMultiplierVertices = action_data.get("motion_multiplier_vertices")

    def action(self):
        """Execute Action"""

        ## setupHierarchy

        ## createClothGroup

        ## createCloth Loop

        ## createStartFrameLoc

        ## createWindControl

        ## makeMotionMult

        ## createCollider Loop

        pass

    def save_action(self):
        pass

    def ui(self, ctrl, layout, *args, **kwargs):
        feedback_handler = feedback.Feedback()
        cloth_objects_lbl = QtWidgets.QLabel(text="Cloth Objects:")
        cloth_objects_hlay = QtWidgets.QHBoxLayout()
        cloth_objects_le = QtWidgets.QLineEdit()
        cloth_objects_hlay.addWidget(cloth_objects_le)
        get_cloth_objects_pb = QtWidgets.QPushButton(text="Set")
        cloth_objects_hlay.addWidget(get_cloth_objects_pb)
        layout.addRow(cloth_objects_lbl, cloth_objects_hlay)

        collider_objects_lbl = QtWidgets.QLabel(text="Collider Objects:")
        collider_objects_hlay = QtWidgets.QHBoxLayout()
        collider_objects_le = QtWidgets.QLineEdit()
        collider_objects_hlay.addWidget(collider_objects_le)
        get_collider_objects_pb = QtWidgets.QPushButton(text="Set")
        collider_objects_hlay.addWidget(get_collider_objects_pb)
        layout.addRow(collider_objects_lbl, collider_objects_hlay)

        mm_vertices_lbl = QtWidgets.QLabel(text="Motion Multiplier Vertices:")
        mm_vertices_hlay = QtWidgets.QHBoxLayout()
        mm_vertices_le = QtWidgets.QLineEdit()
        mm_vertices_hlay.addWidget(mm_vertices_le)
        set_vertices_pb = QtWidgets.QPushButton(text="Set")
        mm_vertices_hlay.addWidget(set_vertices_pb)
        layout.addRow(mm_vertices_lbl, mm_vertices_hlay)

        # make connections with the controller object
        ctrl.connect(cloth_objects_le, "cloth_objects", list)
        ctrl.connect(collider_objects_le, "collider_objects", list)
        ctrl.connect(mm_vertices_le, "motion_multiplier_vertices", list)

        ctrl.update_ui()

        def set_cloth_objects():
            selection = cmds.ls(sl=True)
            if not selection:
                return
            for obj in selection:
                if obj in cloth_objects_le.text():
                    selection.remove(obj)
                if obj in collider_objects_le.text():
                    feedback_handler.pop_info(title="Conflict", text="%s defined as collider. Objects cannot be defined both cloth and passive collider, Skipping" %obj)
                    continue
            cloth_objects_le.setText(ctrl.list_to_text(selection))

        def set_collider_objects():
            selection = cmds.ls(sl=True)
            if not selection:
                return
            for obj in selection:
                if obj in collider_objects_le.text():
                    selection.remove(obj)
                if obj in cloth_objects_le.text():
                    feedback_handler.pop_info(title="Conflict", text="%s defined as cloth. Objects cannot be defined both cloth and passive collider, Skipping" %obj)
                    continue
            collider_objects_le.setText(ctrl.list_to_text(selection))

