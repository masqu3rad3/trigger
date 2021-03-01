#!/usr/bin/env python

"""Object classes"""

from maya import cmds

from trigger.core import filelog
from trigger.core.decorators import keepselection

from trigger.library import functions
from trigger.library.controllers import Icon
from trigger.library.tools import replace_curve

log = filelog.Filelog(logname=__name__, filename="trigger_log")

class Controller(object):

    def __init__(self, name="cont", shape="Circle", scale=(1,1,1), normal=(0,1,0), pos=None):
        super(Controller, self).__init__()
        self._offsets = []
        self.icon_handler = Icon()
        self._shape = shape
        self._name = self.icon_handler.createIcon(iconType=self._shape, iconName=name, scale=scale, normal=normal, location=pos)[0]
        self.lockedShapes = ["FkikSwitch"]

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, new_name):
        cmds.rename(self._name, new_name)
        self._name = new_name

    @property
    def shapes(self):
        return functions.getShapes(self._name)

    def add_offset(self, suffix="OFF"):
        offset_grp = functions.createUpGrp(self._name, suffix)
        self._offsets.insert(0, offset_grp)
        return offset_grp

    def get_offsets(self):
        return self._offsets

    @keepselection
    def set_shape(self, shape):
        if self._shape in self.lockedShapes:
            log.error("set_shape argument is not valid for locked shapes. Locked Shapes are %s" % self.lockedShapes)
        new_shape, _ = self.icon_handler.createIcon(iconType=shape)
        replace_curve(self._name, new_shape, maintain_offset=True)
        cmds.delete(new_shape)

    def set_scale(self, values):
        cmds.setAttr("%s.scale" % self.name, *values)
        self.freeze()
        # cmds.makeIdentity(self.name, a=True)

    def set_normal(self, normals):
        functions.alignNormal(self.name, normals)
        self.freeze()
        # cmds.makeIdentity(self.name, a=True)

    def freeze(self, rotate=True, scale=True, translate=True):
        cmds.makeIdentity(self.name, a=True, r=rotate, s=scale, t=translate)





