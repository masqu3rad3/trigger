
from maya import cmds

# from trigger.ui.Qt import QtWidgets
# from PySide2 import QtWidgets, QtCore
from trigger.ui.Qt import QtWidgets
from trigger.core.decorators import keepselection, undo
from trigger.library.icons import Icon
from trigger.library.tools import replace_curve, mirror_controller

from trigger.ui.qtmaya import get_main_maya_window
from trigger.ui.feedback import Feedback


WINDOW_NAME = "Trigger Make-up v0.0.2"


class Makeup(object):
    """Visualization aimed tools for trigger"""
    side_items = ("Auto Side",
                  "_LEFT_ <> _RIGHT_",
                  "_LEFT <> _RIGHT",
                  "LEFT_ <> RIGHT_",
                  "LEFT <> RIGHT",
                  "_left_ <> _right_",
                  "_left <> _right",
                  "left_ <> right_",
                  "left <> right",
                  "_L_ <> _R_",
                  "_L <> _R",
                  "L_ <> R_",
                  "L <-> R",
                  )

    bias_items = ("Auto Bias",
                  "Start",
                  "End",
                  "Include",
                  )

    icon_handler = Icon()

    def __init__(self):
        super(Makeup, self).__init__()

    @property
    def list_of_icons(self):
        return self.icon_handler.get_icons_list()

    @undo
    def mirror_curve_controller(self, side, bias):
        """
        Finds the pair of the controller and mirrors it

        Args:
            side:(string) Search rule for finding the side pair. Must be a member of side_elements
            bias: (String) Defines the bias of the search rule. Must be a member of bias_elements

        Returns: Controller

        """
        side_flags = side.split(" <> ")
        if side_flags[0] == "Auto Side":
            side_try_list = [x.split(" <> ") for x in self.side_items[1:]]
        else:
            side_try_list = [side_flags]

        if bias == "Auto Bias":
            bias_try_list = [x.lower() for x in self.bias_items[1:]]
        else:
            bias_try_list = [bias.lower()]

        for side in side_try_list:
            for bias in bias_try_list:
                r = mirror_controller(axis="x", node_list=None, side_flags=side, side_bias=bias, continue_on_fail=False)
                if r == -1:
                    continue
                else:
                    return

    @undo
    @keepselection
    def replace_curve_controller(self, icon, objects=None, mo=True, scale=True):
        objects = objects or cmds.ls(sl=True)
        if not isinstance(objects, (tuple, list)):
            objects = [objects]

        for obj in objects:
            new_shape, _ = self.icon_handler.create_icon(icon_type=icon, scale=(1, 1, 1), normal=(0, 1, 0))
            if scale:
                obj_size = self.__get_max_size(obj)
                new_size = float(obj_size) / self.__get_max_size(new_shape)
                cmds.setAttr("%s.scale" % new_shape, new_size, new_size, new_size)
            cmds.makeIdentity(new_shape, apply=True, scale=True)
            replace_curve(obj, new_shape, snap=mo)
            cmds.delete(new_shape)

    @undo
    @keepselection
    def copy_from(self, source, target, snap=True, copy_color=False):
        """Copies the shape from one controller to other"""
        # if not isinstance(source, str) or not isinstance(target, str):
        #     raise ValueError("Both source and target needs to be string values. Got {0}, {1}".format(type(source), type(target)))

        replace_curve(target, source, snap=snap, transfer_color=copy_color)

    @staticmethod
    def __get_max_size(obj):
        _bb = cmds.xform(obj, query=True, boundingBox=True)
        dimensions = []
        dimensions.append(abs(_bb[3] - _bb[0]))
        dimensions.append(abs(_bb[4] - _bb[1]))
        dimensions.append(abs(_bb[5] - _bb[2]))
        return max(dimensions)


def launch(force=True):
    for entry in QtWidgets.QApplication.allWidgets():
        try:
            if entry.objectName() == WINDOW_NAME:
                if force:
                    entry.close()
                    entry.deleteLater()
                else:
                    return
        except (AttributeError, TypeError):
            pass
    MainUI().show()


class MainUI(QtWidgets.QDialog):
    makeup_handler = Makeup()

    def __init__(self):
        parent = get_main_maya_window()
        super(MainUI, self).__init__(parent=parent)

        self.feedback = Feedback()
        self.replace_controllers_combo = None
        self.mirror_controllers_side_combo = None
        self.mirror_controllers_bias_combo = None
        self.build_ui()
        # self.setWindowFlag(QtCore.Qt.WindowMaximizeButtonHint, False)

    def build_ui(self):
        self.setObjectName(WINDOW_NAME)
        self.setWindowTitle(WINDOW_NAME)
        self.resize(288, 100)

        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        size_policy.setHorizontalStretch(1)
        size_policy.setVerticalStretch(0)

        master_lay = QtWidgets.QVBoxLayout(self)

        form_lay = QtWidgets.QFormLayout()
        master_lay.addLayout(form_lay)

        replace_controllers_pb = QtWidgets.QPushButton(self)
        replace_controllers_pb.setText("Replace Controller(s)")
        replace_controllers_pb.setSizePolicy(size_policy)
        replace_controllers_combo_lay = QtWidgets.QHBoxLayout()
        self.replace_controllers_combo = QtWidgets.QComboBox(self)
        self.replace_controllers_combo.setSizePolicy(size_policy)
        replace_controllers_combo_lay.addWidget(self.replace_controllers_combo)
        scale_controllers_lbl = QtWidgets.QLabel(self, text="Try Scale Match")
        self.scale_controllers_cb = QtWidgets.QCheckBox(self)
        self.scale_controllers_cb.setChecked(True)
        replace_controllers_combo_lay.addWidget(scale_controllers_lbl)
        replace_controllers_combo_lay.addWidget(self.scale_controllers_cb)
        form_lay.addRow(replace_controllers_pb, replace_controllers_combo_lay)

        self.replace_controllers_combo.addItems(self.makeup_handler.list_of_icons)

        mirror_controllers_pb = QtWidgets.QPushButton(self)
        mirror_controllers_pb.setText("Mirror Controller(s)")
        mirror_controllers_combo_lay = QtWidgets.QHBoxLayout()
        self.mirror_controllers_side_combo = QtWidgets.QComboBox(self)
        self.mirror_controllers_side_combo.setSizePolicy(size_policy)
        self.mirror_controllers_bias_combo = QtWidgets.QComboBox(self)
        self.mirror_controllers_bias_combo.setSizePolicy(size_policy)
        mirror_controllers_combo_lay.addWidget(self.mirror_controllers_side_combo)
        mirror_controllers_combo_lay.addWidget(self.mirror_controllers_bias_combo)
        form_lay.addRow(mirror_controllers_pb, mirror_controllers_combo_lay)

        copy_controller_pb = QtWidgets.QPushButton(self)
        copy_controller_pb.setText("Copy Shape from another")
        copy_controller_pb.setToolTip("Copies shape from another controller curve. First select the source than the target")
        copy_controller_snap_lbl = QtWidgets.QLabel(self, text="Snap")
        self.copy_controller_snap_cb = QtWidgets.QCheckBox(self)
        self.copy_controller_snap_cb.setChecked(True)
        copy_controller_transfer_color_lbl = QtWidgets.QLabel(self, text="Copy Color")
        self.copy_controller_transfer_color_cb = QtWidgets.QCheckBox(self)
        copy_controller_lay = QtWidgets.QHBoxLayout()
        copy_controller_lay.addWidget(copy_controller_snap_lbl)
        copy_controller_lay.addWidget(self.copy_controller_snap_cb)
        copy_controller_lay.addWidget(copy_controller_transfer_color_lbl)
        copy_controller_lay.addWidget(self.copy_controller_transfer_color_cb)

        form_lay.addRow(copy_controller_pb, copy_controller_lay)

        # fill the combos
        self.mirror_controllers_side_combo.addItems(self.makeup_handler.side_items)
        self.mirror_controllers_bias_combo.addItems(self.makeup_handler.bias_items)

        # SIGNALS
        replace_controllers_pb.clicked.connect(self.on_replace)
        mirror_controllers_pb.clicked.connect(self.on_mirror)
        copy_controller_pb.clicked.connect(self.on_copy)

    def on_replace(self):
        new_icon = self.replace_controllers_combo.currentText()
        self.makeup_handler.replace_curve_controller(new_icon, scale=self.scale_controllers_cb.isChecked())

    def on_mirror(self):
        side_rule = self.mirror_controllers_side_combo.currentText()
        bias_rule = self.mirror_controllers_bias_combo.currentText()
        self.makeup_handler.mirror_curve_controller(side_rule, bias_rule)

    def on_copy(self):
        selection = cmds.ls(selection=True)
        if len(selection) != 2:
            msg = "Please select exactly 2 control curves (source than target)"
            self.feedback.pop_info(title="Selection Error", text=msg, critical=True)
            raise ValueError(msg)
        snap = bool(self.copy_controller_snap_cb.isChecked())
        copy_color = bool(self.copy_controller_transfer_color_cb.isChecked())
        self.makeup_handler.copy_from(selection[0], selection[1], snap=snap, copy_color=copy_color)