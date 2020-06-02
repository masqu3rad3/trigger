"""This module is for saving / loading custom shapes"""

from maya import cmds

from trigger.library import functions as extra
from trigger.library import controllers as ic

ACTION_DATA = {}

class Shapes(object):
    def __init__(self, *args, **kwargs):
        super(Shapes, self).__init__()
        # self.rigName = "trigger"

    def action(self):
        """Mandatory method for all action modules"""
        pass

    def gather_scene_shapes(self, key="*_cont"):
        """
        Duplicates all controllers and gathers them under the 'replaceShapes_grp'
        Args:
            key: (string) Optional key string with wildcards to search shapes.

        Returns: replaceShapes_grp

        """
        all_ctrl = cmds.ls(key, type="transform")
        # EXCLUDE FK/IK icons always
        all_ctrl = filter(lambda x: "FK_IK" not in x, all_ctrl)
        export_grp = cmds.group(name="replaceShapes_grp", em=True)
        for ctrl in all_ctrl:
            dup_ctrl = cmds.duplicate(ctrl, name="%s_REPLACE" % ctrl, renameChildren=True)[0]
            # #delete everything below
            garbage = cmds.listRelatives(dup_ctrl, c=True, typ="transform")
            # print garbage
            cmds.delete(garbage)
            for attr in ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz", "v"]:
                cmds.setAttr("%s.%s" % (dup_ctrl, attr), e=True, k=True, l=False)
            cmds.setAttr("%s.v" % dup_ctrl, 1)
            cmds.parent(dup_ctrl, export_grp)
        return export_grp