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

    def __init__(self, name="cont", shape="Circle"):
        super(Controller, self).__init__()
        self._offsets = []
        self.icon_handler = Icon()
        self._shape = shape.capitalize()
        self._name = self.icon_handler.createIcon(iconType=self._shape, iconName=name)[0]
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

    def create_offset(self, suffix="OFF"):
        offset_grp = functions.createUpGrp(self._name, suffix)
        self._offsets.insert(0, offset_grp)

    def list_offsets(self):
        return self._offsets

    @keepselection
    def set_shape(self, shape):
        if self._shape in self.lockedShapes:
            log.error("set_shape argument is not valid for locked shapes. Locked Shapes are %s" % self.lockedShapes)
        new_shape, _ = self.icon_handler.createIcon(iconType=shape.capitalize())
        replace_curve(self._name, new_shape, maintain_offset=True)
        cmds.delete(new_shape)






