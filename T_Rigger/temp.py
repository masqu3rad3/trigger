#! /usr/bin/python

"""
    File name: tpJointOrient.py
    Author: Tomas Poveda - www.cgart3d.com
    Description: Tool to orient joints quickly
"""

try:
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    from PySide2.QtWidgets import *
    from shiboken2 import wrapInstance
except:
    from PySide.QtGui import *
    from PySide.QtCore import *
    from shiboken import wrapInstance

import os
from functools import partial

import maya.cmds as cmds
import maya.OpenMayaUI as OpenMayaUI


# -------------------------------------------------------------------------------------------------

def _getMayaWindow():
    """
    Return the Maya main window widget as a Python object
    :return: Maya Window
    """

    ptr = OpenMayaUI.MQtUtil.mainWindow()
    if ptr is not None:
        return wrapInstance(long(ptr), QMainWindow)


def tpUndo(fn):
    """
    Simple undo wrapper. Use @tpUndo above the function to wrap it.
    @param fn: function to wrap
    @return wrapped function
    """

    def wrapper(*args, **kwargs):
        cmds.undoInfo(openChunk=True)
        try:
            ret = fn(*args, **kwargs)
        finally:
            cmds.undoInfo(closeChunk=True)
        return ret

    return wrapper


# -------------------------------------------------------------------------------------------------

class tpSplitter(QWidget, object):
    def __init__(self, text=None, shadow=True, color=(150, 150, 150)):

        """
        Basic standard splitter with optional text
        :param str text: Optional text to include as title in the splitter
        :param bool shadow: True if you want a shadow above the splitter
        :param tuple(int) color: Color of the slitter's text
        """

        super(tpSplitter, self).__init__()

        self.setMinimumHeight(2)
        self.setLayout(QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        self.layout().setAlignment(Qt.AlignVCenter)

        firstLine = QFrame()
        firstLine.setFrameStyle(QFrame.HLine)
        self.layout().addWidget(firstLine)

        mainColor = 'rgba(%s, %s, %s, 255)' % color
        shadowColor = 'rgba(45, 45, 45, 255)'

        bottomBorder = ''
        if shadow:
            bottomBorder = 'border-bottom:1px solid %s;' % shadowColor

        styleSheet = "border:0px solid rgba(0,0,0,0); \
                      background-color: %s; \
                      max-height: 1px; \
                      %s" % (mainColor, bottomBorder)

        firstLine.setStyleSheet(styleSheet)

        if text is None:
            return

        firstLine.setMaximumWidth(5)

        font = QFont()
        font.setBold(True)

        textWidth = QFontMetrics(font)
        width = textWidth.width(text) + 6

        label = QLabel()
        label.setText(text)
        label.setFont(font)
        label.setMaximumWidth(width)
        label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        self.layout().addWidget(label)

        secondLine = QFrame()
        secondLine.setFrameStyle(QFrame.HLine)
        secondLine.setStyleSheet(styleSheet)

        self.layout().addWidget(secondLine)


class tpSplitterLayout(QHBoxLayout, object):

    def __init__(self):
        """
        Basic splitter to separate layouts
        """

        super(tpSplitterLayout, self).__init__()

        self.setContentsMargins(40, 2, 40, 2)

        splitter = tpSplitter(shadow=False, color=(60, 60, 60))
        splitter.setFixedHeight(2)

        self.addWidget(splitter)


# -------------------------------------------------------------------------------------------------

class tpJointOrient(QDialog, object):
    def __init__(self):
        super(tpJointOrient, self).__init__(_getMayaWindow())

        winName = 'tpJointOrientDialog'

        # Check if this UI is already open. If it is then delete it before  creating it anew
        if cmds.window(winName, exists=True):
            cmds.deleteUI(winName, window=True)
        elif cmds.windowPref(winName, exists=True):
            cmds.windowPref(winName, remove=True)

        # Set the dialog object name, window title and size
        self.setObjectName(winName)
        self.setWindowTitle('tpJointOrient')
        self.setFixedSize(QSize(265, 600))

        self.customUI()

        self.show()

    def customUI(self):

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(5, 5, 5, 5)
        self.layout().setSpacing(10)
        self.layout().setAlignment(Qt.AlignTop)

        ### Auto Orient Joint Widget ###

        jointOriWidget = QWidget()
        jointOriWidget.setLayout(QVBoxLayout())
        jointOriWidget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        jointOriWidget.layout().setContentsMargins(0, 0, 0, 0)
        jointOriWidget.layout().setSpacing(2)

        self.layout().addWidget(jointOriWidget)

        jointOriSplitter = tpSplitter('JOINT ORIENT')
        jointOriWidget.layout().addWidget(jointOriSplitter)

        aimAxisLayout = QHBoxLayout()
        aimAxisLayout.setContentsMargins(5, 5, 5, 5)
        aimAxisLayout.setSpacing(2)

        # Aim Axis

        aimAxisBox = QGroupBox()
        aimAxisBox.setLayout(aimAxisLayout)
        aimAxisBox.setTitle('Aim Axis')
        jointOriWidget.layout().addWidget(aimAxisBox)
        self.aimXRadio = QRadioButton('X')
        self.aimYRadio = QRadioButton('Y')
        self.aimZRadio = QRadioButton('Z')
        self.aimRevCbx = QCheckBox('Reverse')
        self.aimXRadio.setChecked(True)

        aimAxisLayout.addWidget(self.aimXRadio)
        aimAxisLayout.addWidget(self.aimYRadio)
        aimAxisLayout.addWidget(self.aimZRadio)
        aimAxisLayout.addWidget(self.aimRevCbx)

        # Up Axis

        upAxisLayout = QHBoxLayout()
        upAxisLayout.setContentsMargins(5, 5, 5, 5)
        upAxisLayout.setSpacing(2)

        upAxisBox = QGroupBox()
        upAxisBox.setLayout(upAxisLayout)
        upAxisBox.setTitle('Up Axis')
        jointOriWidget.layout().addWidget(upAxisBox)
        self.upXRadio = QRadioButton('X')
        self.upYRadio = QRadioButton('Y')
        self.upZRadio = QRadioButton('Z')
        self.upRevCbx = QCheckBox('Reverse')
        self.upYRadio.setChecked(True)

        upAxisLayout.addWidget(self.upXRadio)
        upAxisLayout.addWidget(self.upYRadio)
        upAxisLayout.addWidget(self.upZRadio)
        upAxisLayout.addWidget(self.upRevCbx)

        # Up World Axis

        upWorldAxisLayout = QHBoxLayout()
        upWorldAxisLayout.setContentsMargins(5, 5, 5, 5)
        upWorldAxisLayout.setSpacing(5)

        upWorldAxisBox = QGroupBox()
        upWorldAxisBox.setLayout(upWorldAxisLayout)
        upWorldAxisBox.setTitle('Up World Axis')
        jointOriWidget.layout().addWidget(upWorldAxisBox)
        self.upWorldXSpin = QDoubleSpinBox()
        self.upWorldYSpin = QDoubleSpinBox()
        self.upWorldZSpin = QDoubleSpinBox()
        self.upWorldXSpin.setDecimals(3)
        self.upWorldYSpin.setDecimals(3)
        self.upWorldZSpin.setDecimals(3)
        self.upWorldXSpin.setRange(-360, 360)
        self.upWorldYSpin.setRange(-360, 360)
        self.upWorldZSpin.setRange(-360, 360)
        self.upWorldXSpin.setLocale(QLocale.English)
        self.upWorldYSpin.setLocale(QLocale.English)
        self.upWorldZSpin.setLocale(QLocale.English)
        self.upWorldXSpin.setValue(1.0)
        upWorldX = QPushButton('X')
        upWorldY = QPushButton('Y')
        upWorldZ = QPushButton('Z')
        upWorldX.setMaximumWidth(20)
        upWorldY.setMaximumWidth(20)
        upWorldZ.setMaximumWidth(20)

        upWorldAxisLayout.addWidget(self.upWorldXSpin)
        upWorldAxisLayout.addWidget(self.upWorldYSpin)
        upWorldAxisLayout.addWidget(self.upWorldZSpin)
        upWorldAxisLayout.addWidget(upWorldX)
        upWorldAxisLayout.addWidget(upWorldY)
        upWorldAxisLayout.addWidget(upWorldZ)

        jointOriWidget.layout().addLayout(tpSplitterLayout())

        jointOrientBtnLayout = QHBoxLayout()
        jointOrientBtnLayout.setAlignment(Qt.AlignCenter)
        jointOriWidget.layout().addLayout(jointOrientBtnLayout)
        spacerItem = QSpacerItem(2, 2, QSizePolicy.Minimum, QSizePolicy.Minimum)
        jointOrientBtnLayout.addSpacerItem(spacerItem)
        jointOrientBtn = QPushButton('Apply')
        self.jointOrientCbx = QCheckBox('Hierarchy')
        jointOrientBtn.setMaximumWidth(80)
        self.jointOrientCbx.setChecked(True)
        jointOrientBtnLayout.addWidget(jointOrientBtn)
        jointOrientBtnLayout.addWidget(self.jointOrientCbx)

        spacerItem = QSpacerItem(2, 2, QSizePolicy.Fixed)
        self.layout().addSpacerItem(spacerItem)

        ### Manual Orient Joint Widget ###

        manualJointOriWidget = QWidget()
        manualJointOriWidget.setLayout(QVBoxLayout())
        manualJointOriWidget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        manualJointOriWidget.layout().setContentsMargins(5, 5, 5, 5)
        manualJointOriWidget.layout().setSpacing(10)

        self.layout().addWidget(manualJointOriWidget)

        manualJointOriSplitter = tpSplitter('MANUAL JOINT ORIENT')
        manualJointOriWidget.layout().addWidget(manualJointOriSplitter)

        manualJointOriLayout = QHBoxLayout()
        manualJointOriWidget.layout().addLayout(manualJointOriLayout)

        manualJointOriLbl = QLabel('  X  Y  Z  ')
        self.manualJointOriXSpin = QDoubleSpinBox()
        self.manualJointOriYSpin = QDoubleSpinBox()
        self.manualJointOriZSpin = QDoubleSpinBox()
        self.manualJointOriXSpin.setDecimals(3)
        self.manualJointOriYSpin.setDecimals(3)
        self.manualJointOriZSpin.setDecimals(3)
        self.manualJointOriXSpin.setRange(-360, 360)
        self.manualJointOriYSpin.setRange(-360, 360)
        self.manualJointOriZSpin.setRange(-360, 360)
        self.manualJointOriXSpin.setLocale(QLocale.English)
        self.manualJointOriYSpin.setLocale(QLocale.English)
        self.manualJointOriZSpin.setLocale(QLocale.English)
        manualJointOriResetBtn = QPushButton('Reset')

        manualJointOriLayout.addWidget(manualJointOriLbl)
        manualJointOriLayout.addWidget(self.manualJointOriXSpin)
        manualJointOriLayout.addWidget(self.manualJointOriYSpin)
        manualJointOriLayout.addWidget(self.manualJointOriZSpin)
        manualJointOriLayout.addWidget(manualJointOriResetBtn)

        manualJointSplitterLayout = QVBoxLayout()
        manualJointOriWidget.layout().addLayout(manualJointSplitterLayout)

        degreeLayout = QHBoxLayout()
        degreeLayout.setContentsMargins(5, 5, 5, 5)
        degreeLayout.setSpacing(2)

        degreeBox = QGroupBox()
        degreeBox.setLayout(degreeLayout)
        degreeBox.setStyleSheet("border:0px;")
        manualJointSplitterLayout.layout().addWidget(degreeBox)
        self.degree1Radio = QRadioButton('1')
        self.degree5Radio = QRadioButton('5')
        self.degree10Radio = QRadioButton('10')
        self.degree20Radio = QRadioButton('20')
        self.degree45Radio = QRadioButton('45')
        self.degree90Radio = QRadioButton('90')
        self.degree90Radio.setChecked(True)
        self._setValueChange(90)

        degreeLayout.addWidget(self.degree1Radio)
        degreeLayout.addWidget(self.degree5Radio)
        degreeLayout.addWidget(self.degree10Radio)
        degreeLayout.addWidget(self.degree20Radio)
        degreeLayout.addWidget(self.degree45Radio)
        degreeLayout.addWidget(self.degree90Radio)

        manualJointSplitterLayout.addLayout(tpSplitterLayout())

        manualJointOriButtonsLayout = QHBoxLayout()
        manualJointOriButtonsLayout.setContentsMargins(2, 2, 2, 2)
        manualJointOriButtonsLayout.setSpacing(5)
        manualJointOriWidget.layout().addLayout(manualJointOriButtonsLayout)

        manualJointOriAddBtn = QPushButton('Add ( + ) ')
        manualJointOriSubtractBtn = QPushButton('Subract ( - ) ')

        manualJointOriButtonsLayout.addWidget(manualJointOriAddBtn)
        manualJointOriButtonsLayout.addWidget(manualJointOriSubtractBtn)

        manualJointOriSetBtnLayout = QVBoxLayout()
        manualJointOriSetBtnLayout.setAlignment(Qt.AlignCenter)
        manualJointOriSetBtnLayout.setContentsMargins(2, 2, 2, 2)
        manualJointOriSetBtnLayout.setSpacing(5)
        manualJointOriWidget.layout().addLayout(manualJointOriSetBtnLayout)

        manualJointOriSetBtn = QPushButton('Set')
        manualJointOriSetBtn.setMaximumWidth(100)
        self.manualJointOriSetCbx = QCheckBox('Affect children')

        manualJointOriSetBtnLayout.addWidget(manualJointOriSetBtn)
        manualJointOriSetBtnLayout.addWidget(self.manualJointOriSetCbx)

        setRotAxisWidget = QWidget()
        setRotAxisWidget.setLayout(QVBoxLayout())
        setRotAxisWidget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        setRotAxisWidget.layout().setContentsMargins(5, 5, 5, 5)
        setRotAxisWidget.layout().setSpacing(10)

        self.layout().addWidget(setRotAxisWidget)

        setRotAxisSplitter = tpSplitter('SET ROTATION AXIS')
        setRotAxisWidget.layout().addWidget(setRotAxisSplitter)

        setRotAxisLayout = QVBoxLayout()
        setRotAxisWidget.layout().addLayout(setRotAxisLayout)

        setRotTopLayout = QHBoxLayout()
        setRotTopLayout.setSpacing(5)
        setRotAxisLayout.addLayout(setRotTopLayout)
        self.setRotAxisBox = QComboBox()
        setRotTopLayout.addWidget(self.setRotAxisBox)
        for rotAxis in ['xyz', 'yzx', 'zxy', 'xzy', 'yxz', 'zyx']:
            self.setRotAxisBox.addItem(rotAxis)
        setRotAxisCommonBtn = QPushButton('   <')
        setRotAxisCommonBtn.setMaximumWidth(45)
        setRotAxisCommonBtn.setStyleSheet("QPushButton::menu-indicator{image:url(none.jpg);}")
        self.setRotAxisCommonBtnMenu = QMenu(self)
        self._setCommonRotationAxis()
        setRotAxisCommonBtn.setMenu(self.setRotAxisCommonBtnMenu)
        setRotTopLayout.addWidget(setRotAxisCommonBtn)

        setRotAxisBtnLayout = QHBoxLayout()
        setRotAxisBtnLayout.setAlignment(Qt.AlignCenter)
        setRotAxisLayout.addLayout(setRotAxisBtnLayout)
        setRotAxisBtn = QPushButton('Set')
        setRotAxisBtn.setMaximumWidth(100)
        setRotAxisBtnLayout.addWidget(setRotAxisBtn)

        setRotAxisSplitterLayout = QVBoxLayout()
        setRotAxisWidget.layout().addLayout(setRotAxisSplitterLayout)
        setRotAxisSplitterLayout.addLayout(tpSplitterLayout())

        spacerItem = QSpacerItem(2, 2, QSizePolicy.Fixed)
        self.layout().addSpacerItem(spacerItem)

        layoutLRAButtons = QHBoxLayout()
        self.layout().addLayout(layoutLRAButtons)
        displayLRABtn = QPushButton('Display LRA')
        hideLRABtn = QPushButton('Hide LRA')
        layoutLRAButtons.addWidget(displayLRABtn)
        layoutLRAButtons.addWidget(hideLRABtn)

        selectHierarchyBtn = QPushButton('Select Hierarchy')
        self.layout().addWidget(selectHierarchyBtn)

        # ==== SIGNALS ==== #
        upWorldX.clicked.connect(partial(self._resetAxis, 'x'))
        upWorldY.clicked.connect(partial(self._resetAxis, 'y'))
        upWorldZ.clicked.connect(partial(self._resetAxis, 'z'))
        jointOrientBtn.clicked.connect(self.orientJoints)

        manualJointOriResetBtn.clicked.connect(self._resetManualOrient)
        manualJointOriAddBtn.clicked.connect(partial(self.manualOrientJoints, 'add'))
        manualJointOriSubtractBtn.clicked.connect(partial(self.manualOrientJoints, 'subtract'))
        manualJointOriSetBtn.clicked.connect(self.setManualOrientJoints)

        self.degree1Radio.clicked.connect(partial(self._setValueChange, 0))
        self.degree5Radio.clicked.connect(partial(self._setValueChange, 5))
        self.degree10Radio.clicked.connect(partial(self._setValueChange, 10))
        self.degree20Radio.clicked.connect(partial(self._setValueChange, 20))
        self.degree45Radio.clicked.connect(partial(self._setValueChange, 45))
        self.degree90Radio.clicked.connect(partial(self._setValueChange, 90))

        setRotAxisBtn.clicked.connect(self.setRotAxis)

        displayLRABtn.clicked.connect(partial(self.setLRA, True))
        hideLRABtn.clicked.connect(partial(self.setLRA, False))
        selectHierarchyBtn.clicked.connect(self.selectHierarchy)

    def _resetAxis(self, axis):

        for spin in [self.upWorldXSpin, self.upWorldYSpin, self.upWorldZSpin]:
            spin.setValue(0.0)

        if axis == 'x':
            self.upWorldXSpin.setValue(1.0)
        elif axis == 'y':
            self.upWorldYSpin.setValue(1.0)
        elif axis == 'z':
            self.upWorldZSpin.setValue(1.0)

    def _resetManualOrient(self):
        for spin in [self.manualJointOriXSpin, self.manualJointOriYSpin, self.manualJointOriZSpin]:
            spin.setValue(0.0)

    def _setValueChange(self, value):
        for spin in [self.manualJointOriXSpin, self.manualJointOriYSpin, self.manualJointOriZSpin]:
            spin.setSingleStep(value)

    def _setCommonRotationAxis(self):
        self.setRotAxisCommonBtnMenu.addAction('Wrist             (YXZ)', partial(self._setCommonRotOrder, 'yxz'))
        self.setRotAxisCommonBtnMenu.addAction('Finger           (XYZ)', partial(self._setCommonRotOrder, 'xyz'))
        self.setRotAxisCommonBtnMenu.addAction('Spine            (ZYX)', partial(self._setCommonRotOrder, 'zyx'))
        self.setRotAxisCommonBtnMenu.addAction('Hips              (ZYX)', partial(self._setCommonRotOrder, 'zyx'))
        self.setRotAxisCommonBtnMenu.addAction('Root              (ZYX)', partial(self._setCommonRotOrder, 'zyx'))
        self.setRotAxisCommonBtnMenu.addAction('Upper Leg     (ZYX)', partial(self._setCommonRotOrder, 'zyx'))
        self.setRotAxisCommonBtnMenu.addAction('Knee              (YXZ)', partial(self._setCommonRotOrder, 'yxz'))
        self.setRotAxisCommonBtnMenu.addAction('Ankle             (XZY)', partial(self._setCommonRotOrder, 'xzy'))

    def _setCommonRotOrder(self, rotAxis):
        rotOrder = self._getRotOrder(rotAxis)
        self.setRotAxisBox.setCurrentIndex(rotOrder)

    def _getRotOrder(self, rotAxis):
        rotOrder = {}
        for i, order in enumerate(['xyz', 'yzx', 'zxy', 'xzy', 'yxz', 'zyx']):
            rotOrder[order] = i
            rotOrder[order.upper()] = i
        return rotOrder[rotAxis]

    @tpUndo
    def orientJoints(self):

        resetJoints = []

        # Get up and aim axis
        aimAxis = [0, 0, 0]
        upAxis = [0, 0, 0]

        for i, aimRadio in enumerate([self.aimXRadio, self.aimYRadio, self.aimZRadio]):
            if aimRadio.isChecked():
                aimAxisNum = i

        for i, upRadio in enumerate([self.upXRadio, self.upYRadio, self.upZRadio]):
            if upRadio.isChecked():
                upAxisNum = i

        if aimAxisNum == upAxisNum:
            cmds.warning('tpJointOrient: aim and up axis are the same, maybe orientation wont work correctly!')

        aimAxisReverse = 1.0
        if self.aimRevCbx.isChecked():
            aimAxisReverse = -1.0

        upAxisReverse = 1.0
        if self.upRevCbx.isChecked():
            upAxisReverse = -1.0

        aimAxis[aimAxisNum] = aimAxisReverse
        upAxis[upAxisNum] = upAxisReverse
        worldUpAxis = [self.upWorldXSpin.value(), self.upWorldYSpin.value(), self.upWorldZSpin.value()]

        # Get selected joints
        if self.jointOrientCbx.isChecked():
            cmds.select(hierarchy=True)
        joints = cmds.ls(selection=True, type='joint')

        # =======================================================================

        # Loop all selected joints ...
        for jnt in reversed(joints):

            # Get child node
            childs = cmds.listRelatives(jnt, children=True, type=['transform', 'joint'])

            # If the joints has direct childs, unparent that childs and store names
            if childs:
                if len(childs) > 0:
                    childs = cmds.parent(childs, world=True)

            # Get parent of this joints for later use
            parent = ''
            parents = cmds.listRelatives(jnt, parent=True)
            if parents:
                parent = parents[0]

            # Aim to the child
            aimTarget = ''
            if childs:
                for child in childs:
                    if cmds.nodeType(child) == 'joint':
                        aimTarget = child
                        break

            print '//DEBUG: JNT=' + jnt + " Parent=" + parent + " AimTarget=" + aimTarget + "//\n"

            if aimTarget != '':

                # Apply an aim constraint from the joint to its child (target)
                cmds.delete(cmds.aimConstraint(aimTarget, jnt, aim=aimAxis, upVector=upAxis, worldUpVector=worldUpAxis,
                                               worldUpType='vector', weight=1.0))

                # Clear joint axis
                cmds.joint(jnt, edit=True, zeroScaleOrient=True)
                cmds.makeIdentity(jnt, apply=True)

            elif parent != '':
                resetJoints.append(jnt)

            # Reparent child
            if childs:
                if len(childs) > 0:
                    cmds.parent(childs, jnt)

        for jnt in resetJoints:
            # If there is no target, the joint will take its parent orientation
            for axis in ['x', 'y', 'z']:
                cmds.setAttr(jnt + '.jointOrient' + axis.upper(), cmds.getAttr(jnt + '.r' + axis))
                cmds.setAttr(jnt + '.r' + axis, 0)

    @tpUndo
    def manualOrientJoints(self, type):

        if type == 'add':
            tweak = 1.0
        else:
            tweak = -1.0

        tweakRot = [self.manualJointOriXSpin.value() * tweak, self.manualJointOriYSpin.value() * tweak,
                    self.manualJointOriZSpin.value() * tweak]
        joints = cmds.ls(selection=True, type='joint')

        for jnt in joints:
            # Adjust the rotation axis
            cmds.xform(jnt, rotateAxis=[tweakRot[0], tweakRot[1], tweakRot[2]], relative=True, objectSpace=True)

            # Clear joint axis
            cmds.joint(jnt, edit=True, zeroScaleOrient=True)
            cmds.makeIdentity(jnt, apply=True)

        cmds.select(joints, replace=True)

    @tpUndo
    def setManualOrientJoints(self):

        tweakRot = [self.manualJointOriXSpin.value(), self.manualJointOriYSpin.value(),
                    self.manualJointOriZSpin.value()]
        joints = cmds.ls(selection=True, type='joint')

        for jnt in joints:

            if not self.manualJointOriSetCbx.isChecked():

                childs = cmds.listRelatives(jnt, children=True, type=['transform', 'joint'])

                if childs:
                    if len(childs) > 0:
                        for child in childs:
                            cmds.parent(child, world=True)

            # Set the rotation axis
            for i, axis in enumerate(['x', 'y', 'z']):
                cmds.setAttr(jnt + '.jointOrient' + axis.upper(), tweakRot[i])

            # Clear joint axis
            cmds.joint(jnt, edit=True, zeroScaleOrient=True)
            cmds.makeIdentity(jnt, apply=True)

            if childs:
                for child in childs:
                    cmds.parent(child, jnt)

        cmds.select(joints, replace=True)

    @tpUndo
    def setRotAxis(self, axis='xyz'):
        sel = cmds.ls(selection=True, type=['joint', 'transform'])
        for obj in sel:
            rotOrder = self._getRotOrder(self.setRotAxisBox.currentText())
            cmds.setAttr(obj + '.rotateOrder', rotOrder)

    @tpUndo
    def setLRA(self, state):

        sel = cmds.ls(selection=True)

        for obj in sel:
            if cmds.attributeQuery('displayLocalAxis', node=obj, exists=True):
                cmds.setAttr(obj + '.displayLocalAxis', state)

    def selectHierarchy(self):

        """
        Method that selects the hierachy of the selected nodes
        """

        sel = cmds.ls(selection=True)

        for obj in sel:
            cmds.select(obj, hi=True, add=True)


def initUI():
    tpJointOrient()


initUI()


