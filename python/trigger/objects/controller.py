#!/usr/bin/env python

"""Object classes"""

from maya import cmds

from trigger.core import filelog
from trigger.core.decorators import keepselection

from trigger.library import functions, attribute
from trigger.library.controllers import Icon
from trigger.library.tools import replace_curve

log = filelog.Filelog(logname=__name__, filename="trigger_log")


class Controller(object):
    side_dict = {
        "center": [17, 21, 24],
        "left": [6, 18, 29],
        "right": [13, 20, 31]
    }
    side_enum_resolve = {
        "center": 0,
        "left": 1,
        "right": 2,
        "c": 0,
        "l": 1,
        "r": 2,
        "C": 0,
        "L": 1,
        "R": 2
    }
    side_enums = {
        0: "center",
        1: "left",
        2: "right",
    }
    tier_enums = {
        0: "primary",
        1: "secondary",
        2: "tertiary",
    }
    lockedShapes = ["FkikSwitch"]
    def __init__(self, name="cont", shape="Circle", scale=(1, 1, 1), normal=(0, 1, 0), pos=None, side=None, tier=None):




        self._offsets = []
        self.icon_handler = Icon()
        self._shape = shape
        if cmds.objExists(name):
            self._name = name
        else:
            self._name = \
            self.icon_handler.create_icon(icon_type=self._shape, icon_name=name, scale=scale, normal=normal,
                                          location=pos)[0]

        self._side = side or self._get_side_from_node()
        self._tier = tier or self._get_tier_from_node()

        self.add_custom_attributes()

        self.set_side(self._side, tier=self._tier)
        # if side:
        #     self.set_side(side, tier=tier)
        #     self._side = side
        #     self._tier = tier or "primary"
        # else:
        #     self._side = "center"
        #     self._tier = tier or "primary"



    def _get_side_from_node(self):
        """Resolve the side from controller in the scene."""
        # first try the attribute
        if cmds.objExists("%s.side" % self._name):
            return self.side_enums[(cmds.getAttr("%s.side" % self._name))]
        # then try the name
        elif self._name.startswith("L_"):
            return "left"
        elif self._name.startswith("R_"):
            return "right"
        else:
            return "center"

    def _get_tier_from_node(self):
        """Resolve the tier from the controller in the scene"""
        # first try the attribute
        if cmds.objExists("%s.tier" % self._name):
            return cmds.getAttr("%s.tier" % self._name)
        # return the default as primary
        return "primary"

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, new_name):
        cmds.rename(self._name, new_name)
        self._name = new_name

    @property
    def shapes(self):
        return functions.get_shapes(self._name)

    @property
    def side(self):
        return self._side

    @property
    def tier(self):
        return self._tier

    @property
    def parent(self):
        parents = cmds.listRelatives(self._name, parent=True)
        return parents[0] if parents else None

    @parent.setter
    def parent(self, new_parent):
        cmds.parent(self._name, new_parent)

    def add_offset(self, suffix="OFF"):
        offset_grp = functions.create_offset_group(self._name, suffix)
        self._offsets.insert(0, offset_grp)
        return offset_grp

    def get_offsets(self):
        return self._offsets

    @keepselection
    def set_shape(self, shape, scale=(1, 1, 1), normal=(0, 1, 0)):
        if self._shape in self.lockedShapes:
            log.error("set_shape argument is not valid for locked shapes. Locked Shapes are %s" % self.lockedShapes)
        new_shape, _ = self.icon_handler.create_icon(icon_type=shape, scale=scale, normal=normal)
        replace_curve(self._name, new_shape, snap=True)
        cmds.delete(new_shape)

    def set_scale(self, values):
        cmds.setAttr("%s.scale" % self.name, *values)
        self.freeze()

    def set_normal(self, normals):
        functions.align_to_normal(self.name, normals)
        self.freeze()

    def freeze(self, rotate=True, scale=True, translate=True):
        cmds.makeIdentity(self.name, apply=True, rotate=rotate, scale=scale, translate=translate)

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

        cmds.setAttr("{}.side".format(self.name), self.side_enum_resolve[side.lower()])

        tier = tier or self._tier
        if isinstance(tier, str):
            if tier.lower() == "primary":
                tier = 0
            elif tier.lower() == "secondary":
                tier = 1
            elif tier.lower() == "tertiary":
                tier = 2
        elif isinstance(tier, int):
            pass
        elif tier < 0 or tier > 2:
            log.error("out of range value for tier (%s)" % tier)
            raise
        else:
            log.error("invalid tier value %s" % tier)
            raise

        cmds.setAttr("{}.tier".format(self.name), tier)

        functions.colorize(self.name, index=side_vals[tier])
        self._side = side
        self._tier = tier

    def lock_translate(self, skip="", hide=True):
        array = ["t%s" % attr for attr in "xyz" if attr not in skip]
        attribute.lock_and_hide(self.name, channelArray=array, hide=hide)

    def lock_rotate(self, skip="", hide=True):
        array = ["r%s" % attr for attr in "xyz" if attr not in skip]
        attribute.lock_and_hide(self.name, channelArray=array, hide=hide)

    def lock_scale(self, skip="", hide=True):
        array = ["s%s" % attr for attr in "xyz" if attr not in skip]
        attribute.lock_and_hide(self.name, channelArray=array, hide=hide)

    def lock_visibility(self, hide=True):
        attribute.lock_and_hide(self.name, channelArray=["v"], hide=hide)

    def lock(self, attrs, hide=True):
        if isinstance(attrs, str):
            attrs = [attrs]
        attribute.lock_and_hide(self.name, channelArray=attrs, hide=hide)

    def lock_all(self, hide=True):
        self.lock_translate(hide=hide)
        self.lock_rotate(hide=hide)
        self.lock_scale(hide=hide)
        self.lock_visibility(hide=hide)

    def drive_visibility(self, driver_attr, up_level=None, lock_and_hide=True):
        """
        Drives the visibility of the controller with the given attribute

        Args:
            driver_attr: attribute to drive the visibility
            up_level: (integer) if defined the upper group visibility will be used instead
            lock_and_hide: (bool) locks and hides the attribute after driven

        Returns:

        """
        vis_attr = "%s.v" % self.name if up_level is None else "%s.v" % self.get_offsets()[up_level]
        cmds.setAttr(vis_attr, edit=True, keyable=True, lock=False)
        cmds.connectAttr(driver_attr, vis_attr, force=True)
        if lock_and_hide:
            cmds.setAttr(vis_attr, lock=True, keyable=False, channelBox=False)

    def add_custom_attributes(self):
        """Add default attributes for translate, rotate and scale."""

        for ch in ["Translate", "Rotate", "Scale"]:
            attr_name = "default{}".format(ch)
            if not cmds.attributeQuery(attr_name, node=self.name, exists=True):
                cmds.addAttr(self.name,
                             longName=attr_name,
                             attributeType="double3"
                             )
                for axis in "XYZ":
                    _value = 1.0 if ch == "Scale" else 0.0
                    cmds.addAttr(self.name,
                                 longName="{}{}".format(attr_name, axis),
                                 attributeType="double",
                                 defaultValue=_value,
                                 parent=attr_name
                                 )
        attribute.create_attribute(self.name, attr_name="side", attr_type="enum", enum_list="center:left:right", default_value=0, keyable=False, display=False)
        attribute.create_attribute(self.name, attr_name="tier", attr_type="enum", enum_list="primary:secondary:tertiary", default_value=0, keyable=False, display=False)

    def set_defaults(self):
        """Grabs the current values of the controller and sets them as default values."""
        for ch in ["Translate", "Rotate", "Scale"]:
            for axis in "XYZ":
                cmds.setAttr("{}.default{}{}".format(self.name, ch, axis),
                             cmds.getAttr("{}.{}{}".format(self.name, ch.lower(), axis)))
