"""Mocap mapper for importing motion capture data from an FBX file."""

import os
import glob
import json
import logging

from maya import cmds

from trigger.library import fbx
from trigger.library import connection


LOG = logging.getLogger(__name__)


class MocapMapper(object):
    """Mocap mapper for importing motion capture data from an FBX file."""

    def __init__(self, anim_fbx_file=None, bind_pose_fbx_file=None, keep_fbx=False, bake=True):
        """Initialize the mocap mapper.

        Args:
            fbx_file (str): Path to the FBX file.
            mapping (dict): Mapping of the FBX file to the scene.

        """
        self.bind_pose_fbx = self._validate_file(bind_pose_fbx_file) if bind_pose_fbx_file else None
        self.anim_fbx = self._validate_file(anim_fbx_file) if anim_fbx_file else None
        self.keep_fbx = keep_fbx
        self.bake = bake
        self.mapping = None
        self.mappings_dictionary = None
        self._get_mappings() # get the available mappings

        # set the first mapping as the default (if available)
        if self.mappings_dictionary:
            self.set_mapping(list(self.mappings_dictionary.keys())[0])

    def set_mapping_dictionary(self, mapping_dictionary):
        """Set the mapping.

        Args:
            mapping_dictionary (dict): Mapping of the FBX file to the scene.

        """
        if not isinstance(mapping_dictionary, dict):
            raise TypeError("Mapping must be a dictionary.")
        self.mapping = mapping_dictionary

    def set_keep_fbx(self, keep_fbx):
        """Set the keep_fbx flag.

        Args:
            keep_fbx (bool): Keep the FBX file after import.

        """
        if not isinstance(keep_fbx, (bool, int)):
            raise TypeError("Keep FBX must be a boolean.")
        self.keep_fbx = keep_fbx

    def set_bake(self, bake):
        """Set the bake flag.

        Args:
            bake (bool): Bake the animation.

        """
        if not isinstance(bake, bool):
            raise TypeError("Bake must be a boolean.")
        self.bake = bake

    def set_anim_fbx(self, fbx_file):
        """Set the FBX file.

        Args:
            fbx_file (str): Path to the FBX file.

        """
        self.anim_fbx = self._validate_file(fbx_file)

    def set_bind_pose_fbx(self, fbx_file):
        """Set the FBX file.

        Args:
            fbx_file (str): Path to the FBX file.

        """
        self.bind_pose_fbx = self._validate_file(fbx_file)

    def _validate_file(self, file_path):
        if not os.path.isfile(file_path):
            raise ValueError("File does not exist => {}".format(file_path))
        return file_path

    def _get_mappings(self):
        """Get the available mappings."""
        self.mappings_dictionary = {}
        # look at the mappings directory and list the available .json mappings
        dir_path = os.path.dirname(os.path.realpath(__file__))
        mappings_dir = os.path.join(dir_path, "mappings")
        # glob all json files from the mappings directory
        mappings_list = glob.glob(os.path.join(mappings_dir, "*.json"))
        for mapping_path in mappings_list:
            mapping_name = os.path.basename(mapping_path).split(".")[0]
            self.mappings_dictionary[mapping_name] = mapping_path
            LOG.info(mapping_name)

    def list_mappings(self):
        """List the available mappings."""
        mapping_names = list(self.mappings_dictionary.keys())
        LOG.info("Available Mappings: {}".format(mapping_names))
        return mapping_names

    def set_mapping(self, mapping_name):
        """Set the mapping from the list of available mappings.

        Args:
            mapping_name (str): Name of the mapping.

        """
        mapping_path = self.mappings_dictionary[mapping_name]
        if os.path.isfile(mapping_path):
            try:
                with open(mapping_path, 'r') as f:
                    self.mapping = json.load(f)
                    return True
            except ValueError:
                LOG.error("Missing JSON file => %s" % mapping_path)

    def apply_animation(self):
        """Apply the animation to the rig."""

        # validate the values
        if not self.anim_fbx:
            LOG.error("No Anim FBX file set.")
            return False
        if not self.mapping:
            LOG.error("No mapping set.")
            return False

        # set the FK mode and disable the auto shoulder and hip
        attrs = ["FK_IK", "Auto_Shoulder", "Auto_Hip"]
        for cont in cmds.ls("*_FK_IK_cont", type="transform"):
            for attr in attrs:
                try:
                    cmds.setAttr("{0}.{1}".format(cont, attr), 0)
                except RuntimeError:
                    pass

        if self.bind_pose_fbx:
            bind_pose_nodes = fbx.load(self.bind_pose_fbx, merge_mode="add", animation=False, skins=True)
        else:
            bind_pose_nodes = []

        self._stick_to_joints()

        anim_nodes = fbx.load(self.anim_fbx, merge_mode="merge", animation=True, skins=True)

        if self.bake:
            self._bake_ctrls()

        if not self.keep_fbx:
        # cmds.delete(cmds.ls("TRIGGER_MOCAP_IMPORT*"))
            all_nodes = list(set(bind_pose_nodes + anim_nodes))
            cmds.delete(all_nodes)

    def _stick_to_joints(self):
        """Make the controllers stick to the joints."""
        for method, data in self.mapping.items():
            if method == "parent":
                skip_rotate = []
                skip_translate = []
            elif method == "rotation":
                skip_rotate = []
                skip_translate = ["x", "y", "z"]
            elif method == "translation":
                skip_rotate = ["x", "y", "z"]
                skip_translate = []
            else:
                raise Exception("Invalid method: %s" % method)
            for joint, cont in data.items():
                if cmds.objExists(joint) and cmds.objExists(cont):
                    # connection.matrixConstraint(joint, cont, maintainOffset=True, skipRotate=skip_rotate, skipTranslate=skip_translate, prefix="TRIGGER_MOCAP_IMPORT")
                    # cmds.parentConstraint(joint, cont, maintainOffset=True, skipRotate=skip_rotate, skipTranslate=skip_translate)
                    # if cmds.objExists(joint) and cmds.objExists(cont):
                    locked_translates_raw = cmds.listAttr("%s.t" % cont, locked=True, shortNames=True)
                    locked_translates = [attr.replace("t", "") for attr in
                                         locked_translates_raw] if locked_translates_raw else []
                    locked_rotates_raw = cmds.listAttr("%s.r" % cont, locked=True, shortNames=True)
                    locked_rotates = [attr.replace("r", "") for attr in
                                      locked_rotates_raw] if locked_rotates_raw else []
                    # add the locked attributes to the skip list if it is not already there
                    for attr in locked_translates:
                        if attr not in skip_translate:
                            skip_translate.append(attr)
                    for attr in locked_rotates:
                        if attr not in skip_rotate:
                            skip_rotate.append(attr)

                    cmds.parentConstraint(joint, cont, maintainOffset=True, skipTranslate=skip_translate, skipRotate=skip_rotate)

    def _bake_ctrls(self):
        """Bake the controllers."""
        all_controllers = []
        first_keys = []
        last_keys = []
        for method, data in self.mapping.items():
            for joint, cont in data.items():
                if cmds.objExists(joint) and cmds.objExists(cont):
                    first = cmds.findKeyframe(joint, which="first")
                    last = cmds.findKeyframe(joint, which="last") + 1 # makes sure round up
                    all_controllers.append(cont)
                    first_keys.append(first)
                    last_keys.append(last)

        first = min(first_keys)
        last = max(last_keys)
        cmds.bakeResults(all_controllers, time=(first-1, last), simulation=True)
