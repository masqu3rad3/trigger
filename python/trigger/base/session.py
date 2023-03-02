import os

from maya import cmds
from trigger.library import functions
from trigger.library import attribute
from trigger.library import joint
from trigger.library import api

from trigger.core import io
from trigger.core import filelog
from trigger.core import compatibility as compat

from trigger.base import initials

log = filelog.Filelog(logname=__name__, filename="trigger_log")


class Session(object):
    def __init__(self):
        super(Session, self).__init__()

        # at least a file name is necessary while instancing the IO
        self.io = io.IO(file_name="tmp_session.trg")
        self.init = initials.Initials()

    def save_session(self, file_path):
        """Saves the session to the given file path"""
        if not os.path.splitext(file_path)[1]:
            file_path = "%s.trg" %file_path
        self.io.file_path = file_path
        guides_data = self.collect_guides()
        self.io.write(guides_data)
        log.info("Session Saved Successfully...")

    # def load_session(self, file_path, reset_scene=True):
    def load_session(self, file_path, reset_scene=False):
        """Loads the session from the file"""

        if reset_scene:
            self.reset_scene()
        guides_data = self._get_guides_data(file_path)
        if guides_data:
            self.rebuild_guides(guides_data)
            log.info("Guides Loaded Successfully...")
        else:
            log.error("Guides File doesn't exist or unreadable => %s" %file_path)
            raise Exception

    def get_roots_from_file(self, file_path):
        guides_data = self._get_guides_data(file_path)
        for j in guides_data:
            if j["type"] in self.init.validRootList:
                yield j["name"]

    def _get_guides_data(self, file_path):
        self.io.file_path = file_path
        return self.io.read()

    def collect_guides(self):
        """Collect all necessary guide data ready to write"""

        all_root_jnts_data = self.init.get_scene_roots()
        root_joints_list = []

        all_trigger_joints = []
        for r_dict in all_root_jnts_data:
            root_jnt = (r_dict.get("root_joint"))
            root_joints_list.append(root_jnt)
            limb_dict, _, __ = self.init.getWholeLimb(root_jnt)
            all_trigger_joints.append(limb_dict.values())

        flat_jnt_list = list(compat.flatten(all_trigger_joints))

        save_data = []

        for jnt in flat_jnt_list:
            cmds.select(d=True)
            tmp_jnt = cmds.joint()
            functions.align_to(tmp_jnt, jnt, position=True, rotation=True)
            world_pos = tuple(api.get_world_translation(tmp_jnt))
            rotation = cmds.getAttr("%s.rotate" % tmp_jnt)[0]
            joint_orient = cmds.getAttr("%s.jointOrient" % tmp_jnt)[0]
            # scale = cmds.getAttr("%s.scale" % jnt)[0]
            scale = (1, 1, 1)
            side = joint.get_joint_side(jnt)
            j_type = joint.get_joint_type(jnt)
            color = cmds.getAttr("%s.overrideColor" % jnt)
            radius = cmds.getAttr("%s.radius" % jnt)
            parent = functions.get_parent(jnt)
            if parent in flat_jnt_list:
                pass
            else:
                parent = None
            # get all custom attributes
            # this returns list of dictionaries compatible with create_attribute method in library.functions
            user_attrs = self.init.get_user_attrs(jnt)

            jnt_dict = {"name": jnt,
                        "position": world_pos,
                        "rotation": rotation,
                        "joint_orient": joint_orient,
                        "scale": scale,
                        "parent": parent,
                        "side": side,
                        "type": j_type,
                        "color": color,
                        "radius": radius,
                        "user_attributes": user_attrs}
            save_data.append(jnt_dict)
            cmds.delete(tmp_jnt)
        return save_data

    def rebuild_guides(self, guides_data):
        """
        Rebuild all initial joints
        Args:
            guides_data: [list] List of dictionaries. Output from 'collect_initials' method

        Returns: None

        """
        holder_grp = "%s_refGuides" % self.init.projectName
        if not cmds.objExists(holder_grp):
            holder_grp = cmds.group(name=holder_grp, em=True)
        for jnt_dict in guides_data:
            cmds.select(d=True)
            jnt = cmds.joint(name=jnt_dict.get("name"), p=jnt_dict.get("position"))
            attribute.create_global_joint_attrs(jnt)
            cmds.setAttr("%s.rotate" % jnt, *jnt_dict.get("rotation"))
            cmds.setAttr("%s.jointOrient" % jnt, *jnt_dict.get("joint_orient"))
            cmds.setAttr("%s.scale" % jnt, *jnt_dict.get("scale"))
            cmds.setAttr("%s.radius" % jnt, jnt_dict.get("radius"))
            cmds.setAttr("%s.drawLabel" % jnt, 1)
            cmds.setAttr("%s.displayLocalAxis" % jnt, 1)
            cmds.setAttr("%s.overrideEnabled" % jnt, True)
            cmds.setAttr("%s.overrideColor" % jnt, jnt_dict.get("color"))
            joint.set_joint_side(jnt, jnt_dict.get("side"))
            joint.set_joint_type(jnt, jnt_dict.get("type"))
            property_attrs = jnt_dict.get("user_attributes")
            for attr_dict in property_attrs:
                attribute.create_attribute(jnt, attr_dict)

        for jnt_dict in guides_data:
            if jnt_dict.get("parent"):
                cmds.parent(jnt_dict.get("name"), jnt_dict.get("parent"))
            else:
                cmds.parent(jnt_dict.get("name"), holder_grp)

    def reset_scene(self):
        cmds.file(new=True, force=True)

