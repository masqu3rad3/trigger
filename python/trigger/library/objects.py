#!/usr/bin/env python

"""Object classes"""

from maya import cmds

from trigger.library import functions
from trigger.library.controllers import Icon

class Controller(str):
    def __init__(self, icon=None):
        super(Controller, self).__init__()
        self._offset_grps = []
        self.icon_handler = Icon()

    def create_offset_grp(self, suffix="OFF"):
        assert cmds.objExists(self), "Controller Object does not exist"
        offset_grp = functions.createUpGrp(self, suffix)
        self._offset_grps.insert(0, offset_grp)

    def list_offset_groups(self):
        return self._offset_grps




