## AUTHOR:	Arda Kutlu
## e-mail: ardakutlu@gmail.com
## Web: http://www.ardakutlu.com
## VERSION:0.0.2
## CREATION DATE: 17.06.2017
## LAST MODIFIED DATE: 23.08.2020
## Coverted to cmds / pyqt / compatible with Python 3
## DESCRIPTION: Simple maya tool to mass-color code objects (control curves mostly)

#####################################################################################################################
import sys

from trigger.ui import Qt
from trigger.ui.Qt import QtWidgets, QtCore, QtGui
from maya import OpenMayaUI as omui

if Qt.__binding__ == "PySide":
    from shiboken import wrapInstance
elif Qt.__binding__.startswith('PyQt'):
    from sip import wrapinstance as wrapInstance
else:
    from shiboken2 import wrapInstance

from maya import cmds
slider = None

VERSION = "0.0.2"
WINDOW_NAME = "Colorize %s" % VERSION


def getMayaMainWindow():
    """
    Gets the memory adress of the main window to connect Qt dialog to it.
    Returns:
        (long) Memory Adress
    """
    win = omui.MQtUtil_mainWindow()
    if sys.version_info.major == 3:
        ptr = wrapInstance(int(win), QtWidgets.QMainWindow)
    else:
        ptr = wrapInstance(long(win), QtWidgets.QMainWindow)
    return ptr

class Colorize():
    def __init__(self):
        self.colorIndices = (
            (0.471, 0.471, 0.471),
            (0, 0, 0),
            (0.251, 0.251, 0.251),
            (0.502, 0.502, 0.502),
            (0.608, 0, 0.157),
            (0, 0.016, 0.376),
            (0, 0, 1),
            (0, 0.275, 0.098),
            (0.149, 0, 0.263),
            (0.784, 0, 0.784),
            (0.541, 0.282, 0.2),
            (0.247, 0.137, 0.122),
            (0.6, 0.149, 0),
            (1, 0, 0),
            (0, 1, 0),
            (0, 0.255, 0.6),
            (1, 1, 1),
            (1, 1, 0),
            (0.392, 0.863, 1),
            (0.263, 1, 0.639),
            (1, 0.69, 0.69),
            (0.894, 0.675, 0.475),
            (1, 1, 0.388),
            (0, 0.6, 0.329),
            (0.631, 0.412, 0.188),
            (0.624, 0.631, 0.188),
            (0.408, 0.631, 0.188),
            (0.188, 0.631, 0.365),
            (0.188, 0.631, 0.631),
            (0.188, 0.404, 0.631),
            (0.435, 0.188, 0.631),
            (0.631, 0.188, 0.412)
        )
        self.customColor = (0.471, 0.471, 0.471)
        self.primaryLeftID = 6
        self.primaryCenterID = 17
        self.primaryRightID = 13
        self.secondaryLeftID = 18
        self.secondaryCenterID = 21
        self.secondaryRightID = 20
        self.tertiaryLeftID = 29
        self.tertiaryCenterID = 24
        self.tertiaryRightID = 31


    def get_custom_color(self):
        """Opens maya color picker and gets the selected custom color"""
        cmds.colorEditor()
        if cmds.colorEditor(query=True, result=True):
            val = (cmds.colorEditor(query=True, rgb=True))
            self.customColor = tuple(val)
        return


    def changeColor(self, index, customColor=None):
        """
        Changes the wire color of selected nodes to the with the index
        Args:
            index: Index Number
            customColor: (Tuple) If defined, this overrides index number.
        Returns:None

        """
        node = cmds.ls(sl=True)
        if not node:
            return
        shapes = cmds.listRelatives(node, s=True)
        if not shapes:
            return
        if not customColor:
            for shape in shapes:
                try: cmds.setAttr("%s.overrideRGBColors", 0)
                except: pass
                cmds.setAttr("%s.overrideEnabled" % shape, True)
                cmds.setAttr("%s.overrideColor" % shape, index)
        else:
            for shape in shapes:
                cmds.setAttr("%s.overrideRGBColors" % shape, 1)
                cmds.setAttr("%s.overrideColorRGB" % shape, *customColor)


class MainUI(QtWidgets.QDialog):
    def __init__(self):
        for entry in QtWidgets.QApplication.allWidgets():
            try:
                if entry.objectName() == WINDOW_NAME:
                    entry.close()
            except (AttributeError, TypeError):
                pass

        parent = getMayaMainWindow()
        super(MainUI, self).__init__(parent=parent)

        self.setWindowTitle(WINDOW_NAME)

        # create guide and rig objects
        self.colorize = Colorize()

        # Build the UI elements
        self.buildUI(self)
        # self.show()

        self.initialize()


    def buildUI(self, colorize_dialog):
        colorize_dialog.setObjectName("colorize_dialog")
        colorize_dialog.resize(700, 250)
        colorize_dialog.setWindowTitle(WINDOW_NAME)

        self.master_vlay = QtWidgets.QVBoxLayout(colorize_dialog)
        self.master_vlay.setContentsMargins(4, 4, 4, 4)
        self.master_vlay.setSpacing(2)

        self.color_select_hlay = QtWidgets.QHBoxLayout()
        self.color_select_hlay.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)

        self.color_index_lbl = QtWidgets.QLabel(colorize_dialog)
        self.color_index_lbl.setText("Color Index")

        self.color_select_hlay.addWidget(self.color_index_lbl)

        self.color_index_spinbox = QtWidgets.QSpinBox(colorize_dialog)
        self.color_index_spinbox.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.color_select_hlay.addWidget(self.color_index_spinbox)

        self.color_index_slider = QtWidgets.QSlider(colorize_dialog)
        self.color_index_slider.setOrientation(QtCore.Qt.Horizontal)
        self.color_select_hlay.addWidget(self.color_index_slider)
        self.color_index_slider.setMaximum(len(self.colorize.colorIndices)-1)

        self.custom_cb = QtWidgets.QCheckBox(colorize_dialog)
        self.custom_cb.setText("Custom")
        self.color_select_hlay.addWidget(self.custom_cb)

        self.select_custom_pb = QtWidgets.QPushButton(colorize_dialog)
        self.select_custom_pb.setText("Select")
        self.color_select_hlay.addWidget(self.select_custom_pb)
        self.master_vlay.addLayout(self.color_select_hlay)

        self.colorize_pb = QtWidgets.QPushButton(colorize_dialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.colorize_pb.sizePolicy().hasHeightForWidth())
        self.colorize_pb.setSizePolicy(sizePolicy)
        self.colorize_pb.setText("Colorize")
        self.master_vlay.addWidget(self.colorize_pb)

        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setSpacing(2)
        self.primary_left_pb = QtWidgets.QPushButton(colorize_dialog)
        self.primary_left_pb.setText("Primary Left")
        self.gridLayout.addWidget(self.primary_left_pb, 0, 2, 1, 1)

        self.secondary_center_pb = QtWidgets.QPushButton(colorize_dialog)
        self.secondary_center_pb.setText("Secondary Center")
        self.gridLayout.addWidget(self.secondary_center_pb, 1, 1, 1, 1)

        self.primary_right_pb = QtWidgets.QPushButton(colorize_dialog)
        self.primary_right_pb.setText("Primary Right")
        self.gridLayout.addWidget(self.primary_right_pb, 0, 0, 1, 1)

        self.secondary_right_pb = QtWidgets.QPushButton(colorize_dialog)
        self.secondary_right_pb.setText("Secondary Right")
        self.gridLayout.addWidget(self.secondary_right_pb, 1, 0, 1, 1)

        self.primary_center_pb = QtWidgets.QPushButton(colorize_dialog)
        self.primary_center_pb.setText("Primary Center")
        self.gridLayout.addWidget(self.primary_center_pb, 0, 1, 1, 1)

        self.secondary_left_pb = QtWidgets.QPushButton(colorize_dialog)
        self.secondary_left_pb.setText("Secondary Left")
        self.gridLayout.addWidget(self.secondary_left_pb, 1, 2, 1, 1)

        self.tertiary_right_pb = QtWidgets.QPushButton(colorize_dialog)
        self.tertiary_right_pb.setText("Tertiary Right")
        self.gridLayout.addWidget(self.tertiary_right_pb, 2, 0, 1, 1)

        self.tertiary_center_pb = QtWidgets.QPushButton(colorize_dialog)
        self.tertiary_center_pb.setText("Tertiary Center")
        self.gridLayout.addWidget(self.tertiary_center_pb, 2, 1, 1, 1)

        self.tertiary_left_pb = QtWidgets.QPushButton(colorize_dialog)
        self.tertiary_left_pb.setText("Tertiary Left")
        self.gridLayout.addWidget(self.tertiary_left_pb, 2, 2, 1, 1)
        self.master_vlay.addLayout(self.gridLayout)

        # SIGNALS #
        self.color_index_slider.valueChanged.connect(self.on_slider_change)
        self.color_index_spinbox.valueChanged.connect(self.on_spinbox_change)
        self.custom_cb.stateChanged.connect(self.update)
        self.select_custom_pb.clicked.connect(self.on_select_custom)

        self.colorize_pb.clicked.connect(self.on_colorize)

        self.primary_right_pb.clicked.connect(lambda x=0: self.colorize.changeColor(self.colorize.primaryRightID))
        self.primary_left_pb.clicked.connect(lambda x=0: self.colorize.changeColor(self.colorize.primaryLeftID))
        self.primary_center_pb.clicked.connect(lambda x=0: self.colorize.changeColor(self.colorize.primaryCenterID))
        self.secondary_right_pb.clicked.connect(lambda x=0: self.colorize.changeColor(self.colorize.secondaryRightID))
        self.secondary_left_pb.clicked.connect(lambda x=0: self.colorize.changeColor(self.colorize.secondaryLeftID))
        self.secondary_center_pb.clicked.connect(lambda x=0: self.colorize.changeColor(self.colorize.secondaryCenterID))
        self.tertiary_right_pb.clicked.connect(lambda x=0: self.colorize.changeColor(self.colorize.tertiaryRightID))
        self.tertiary_left_pb.clicked.connect(lambda x=0: self.colorize.changeColor(self.colorize.tertiaryLeftID))
        self.tertiary_center_pb.clicked.connect(lambda x=0: self.colorize.changeColor(self.colorize.tertiaryCenterID))

    def initialize(self):
        self.primary_right_pb.setStyleSheet("color: black; background-color:rgb{0}".format(self._f2b(self.colorize.colorIndices[self.colorize.primaryRightID])))
        self.primary_left_pb.setStyleSheet("color: black; background-color:rgb{0}".format(self._f2b(self.colorize.colorIndices[self.colorize.primaryLeftID])))
        self.primary_center_pb.setStyleSheet("color: black; background-color:rgb{0}".format(self._f2b(self.colorize.colorIndices[self.colorize.primaryCenterID])))
        self.secondary_right_pb.setStyleSheet("color: black; background-color:rgb{0}".format(self._f2b(self.colorize.colorIndices[self.colorize.secondaryRightID])))
        self.secondary_left_pb.setStyleSheet("color: black; background-color:rgb{0}".format(self._f2b(self.colorize.colorIndices[self.colorize.secondaryLeftID])))
        self.secondary_center_pb.setStyleSheet("color: black; background-color:rgb{0}".format(self._f2b(self.colorize.colorIndices[self.colorize.secondaryCenterID])))
        self.tertiary_right_pb.setStyleSheet("color: black; background-color:rgb{0}".format(self._f2b(self.colorize.colorIndices[self.colorize.tertiaryRightID])))
        self.tertiary_left_pb.setStyleSheet("color: black; background-color:rgb{0}".format(self._f2b(self.colorize.colorIndices[self.colorize.tertiaryLeftID])))
        self.tertiary_center_pb.setStyleSheet("color: black; background-color:rgb{0}".format(self._f2b(self.colorize.colorIndices[self.colorize.tertiaryCenterID])))
        self.update()

    def update(self):
        if self.custom_cb.isChecked():
            self.select_custom_pb.setEnabled(True)
            self.color_index_spinbox.setEnabled(False)
            self.color_index_slider.setEnabled(False)
            float_index_color = self.colorize.customColor
        else:
            self.select_custom_pb.setEnabled(False)
            self.color_index_spinbox.setEnabled(True)
            self.color_index_slider.setEnabled(True)
            index_number = self.color_index_spinbox.value()
            float_index_color = self.colorize.colorIndices[index_number]
        # byte_color = [int(f*255.999) for f in float_index_color]
        self.colorize_pb.setStyleSheet("background-color:rgb{0}".format(self._f2b(float_index_color)))
        # self.colorize_pb.style().polish(self.colorize_pb) # not necessary

    def on_slider_change(self, value):
        self.color_index_spinbox.setValue(value)
        self.update()

    def on_spinbox_change(self, value):
        self.color_index_slider.setValue(value)
        self.update()

    def on_select_custom(self):
        self.colorize.get_custom_color()
        self.update()

    def on_colorize(self):
        if self.custom_cb.isChecked():
            self.colorize.changeColor(0, customColor=self.colorize.customColor)
        else:
            self.colorize.changeColor(self.color_index_spinbox.value())

    @staticmethod
    def _f2b(float_index_color):
        byte_list = [int(f*255.999) for f in float_index_color]
        return tuple(byte_list)



