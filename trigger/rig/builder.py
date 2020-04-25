"""New rig builder module"""
from maya import cmds
import trigger.library.functions as extra
import trigger.library.controllers as ic
import trigger.modules.arm as arm
import trigger.modules.leg as leg
import trigger.modules.head as neckAndHead
import trigger.modules.spine as spine
import trigger.modules.tail as simpleTail
import trigger.modules.digits as finger
import trigger.modules.tentacle as tentacle
import trigger.modules.root as root
import trigger.utils.space_switcher_old as anchorMaker
import trigger.library.tools as tools
from trigger.core import io

from trigger.Qt import QtWidgets

import logging
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)

class Builder(object):
    def __init__(self, name="trigger", progress_bar=None):
        self.progress_bar = progress_bar
        if self.progress_bar:
            self.progress_bar.setProperty("value", 0)
        self.rig_name = name

        pass

    def start_building(self, root=None):
        if not root:
            selection = cmds.ls(sl=True)
            if len(selection) == 1:
                root = selection[0]
            else:
                LOG.warning("Select a single root joint")
        if cmds.objectType(root, isType="joint")

