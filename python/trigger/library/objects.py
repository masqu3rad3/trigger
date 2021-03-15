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
    def __init__(self, name="cont", shape="Circle", scale=(1,1,1), normal=(0,1,0), pos=None, side=None, tier=None):
        super(Controller, self).__init__()

        self.side_dict = {"center": [17, 21, 24],
                          "left": [6, 18, 29],
                          "right": [13, 20, 31]
                          }
        self._offsets = []
        self.icon_handler = Icon()
        self._shape = shape
        if cmds.objExists(name):
            self._name = name
        else:
            self._name = self.icon_handler.createIcon(iconType=self._shape, iconName=name, scale=scale, normal=normal, location=pos)[0]
        self.lockedShapes = ["FkikSwitch"]

        if side:
            self.set_side(side, tier=tier)
            self._side = side
            self._tier = tier or "primary"
        else:
            self._side = "center"
            self._tier = tier or "primary"


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

    @property
    def side(self):
        return self._side

    @property
    def tier(self):
        return self._tier

    def add_offset(self, suffix="OFF"):
        offset_grp = functions.createUpGrp(self._name, suffix)
        self._offsets.insert(0, offset_grp)
        return offset_grp

    def get_offsets(self):
        return self._offsets

    @keepselection
    def set_shape(self, shape, scale=(1,1,1), normal=(0,1,0)):
        if self._shape in self.lockedShapes:
            log.error("set_shape argument is not valid for locked shapes. Locked Shapes are %s" % self.lockedShapes)
        new_shape, _ = self.icon_handler.createIcon(iconType=shape, scale=scale, normal=normal)
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

    def set_side(self, side, tier=None):
        if side.lower() == "c":
            side_vals = self.side_dict["center"]
        elif side.lower() == "l":
            side_vals = self.side_dict["left"]
        elif side.lower() == "r":
            side_vals = self.side_dict["right"]
        else:
            side_vals = self.side_dict.get(side.lower())
        if not side_vals:
            log.error("side value is not valid => %s" % side)
            raise

        tier = tier or self._tier
        if type(tier) == str:
            if tier.lower() == "primary":
                tier = 0
            elif tier.lower() == "secondary":
                tier = 1
            elif tier.lower() == "tertiary":
                tier = 2
        elif type(tier) == int:
            pass
        elif tier < 0 or tier > 2:
            log.error("out of range value for tier (%s)" %tier)
            raise
        else:
            log.error("invalid tier value %s" %tier)
            raise

        functions.colorize(self.name, index=side_vals[tier])
        self._side = side
        self._tier = tier











