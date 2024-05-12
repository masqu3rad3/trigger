# pylint: disable=consider-using-f-string
"""Main module for the shape transfer tool."""
from time import time
import logging

from maya import cmds

from trigger.library import interface
from trigger.library import functions
from trigger.objects.scene_data import SceneDictionary
from trigger.utils.shape_transfer import protocols

LOG = logging.getLogger(__name__)

class ShapeTransfer(object):
    """Shape Transfer Main Class."""

    def __init__(self):
        super(ShapeTransfer, self).__init__()

        self.master_group = "trTMP_blndtrans__master"
        self.annotations_group = "trTMP_blndtrans__annotations"
        self.scene_db = SceneDictionary(node=self.master_group)
        self.transform = "trTMP_blndtrans__transform"

        # create the groups if they don't exist
        self._create_groups()

        self._source_mesh = self.scene_db.get("source_mesh", "")
        self._target_mesh = self.scene_db.get("target_mesh", "")
        self._source_blendshape_grp = self.scene_db.get("source_blendshape_grp", "")

        self._offset_x = self.scene_db.get("offset_x", 0.0)
        self._offset_y = self.scene_db.get("offset_y", 0.0)
        self._offset_z = self.scene_db.get("offset_z", 0.0)

        self._shape_protocols = []
        self._topology_protocols = []
        for protocol in protocols.classes:
            if protocol.type == "shape":
                self._shape_protocols.append(protocol())
            elif protocol.type == "topology":
                self._topology_protocols.append(protocol())

        self.active_protocol = None
        self.is_preview_on = False

    def set_source_mesh(self, source_mesh):
        """Set the source mesh and update the message attribute."""
        self._source_mesh = source_mesh
        self.scene_db["source_mesh"] = self._source_mesh

    def set_target_mesh(self, target_mesh):
        """Set the target mesh and update the message attribute."""
        self._target_mesh = target_mesh
        self.scene_db["target_mesh"] = self._target_mesh

    def set_source_blendshape_grp(self, source_blendshape_grp):
        """Set the source blendshape group and update the message attribute."""
        self._source_blendshape_grp = source_blendshape_grp
        self.scene_db["source_blendshape_grp"] = self._source_blendshape_grp

    @property
    def shape_protocols(self):
        """Return the shape protocols."""
        return self._shape_protocols

    @property
    def topology_protocols(self):
        """Return the topology protocols."""
        return self._topology_protocols

    @property
    def all_protocols(self):
        """Return all the protocols."""
        return self._shape_protocols + self._topology_protocols

    def set_active_protocol(self, protocol):
        """Set the protocol."""
        # Validate the protocol
        if not isinstance(protocol, protocols.ProtocolCore):
            raise ValueError("Protocol must be a subclass of ProtocolCore")
        if protocol not in self.shape_protocols + self.topology_protocols:
            raise ValueError("Protocol {} doesn't exist".format(protocol))
        self.active_protocol = protocol

        # define the available variables for the protocol. Some values are required for ui_refresh()
        self.active_protocol.master_group = self.master_group # !!!
        self.active_protocol.source_mesh = self._source_mesh # !!!
        self.active_protocol.target_mesh = self._target_mesh # !!!
        self.active_protocol.source_blendshape_grp = self._source_blendshape_grp # !!!
        self.active_protocol.transform_group = self.transform # !!!
        self.active_protocol.ui_refresh() # !!!

        # keep the preview mode same as before (prepare the protocol if not prepared)
        self.preview_mode(turn_on=self.is_preview_on)

    def set_active_protocol_by_name(self, protocol_name):
        """Set the active protocol."""
        for protocol in self.shape_protocols + self.topology_protocols:
            if protocol.name == protocol_name:
                self.active_protocol = protocol
                return True
        raise ValueError("Protocol {} doesn't exist".format(protocol_name))

    def set_offset_x(self, value):
        """Set the offset x value."""
        cmds.setAttr("{}.tx".format(self.transform), value)
        self.scene_db["offset_x"] = value

    def set_offset_y(self, value):
        """Set the offset y value."""
        cmds.setAttr("{}.ty".format(self.transform), value)
        self.scene_db["offset_y"] = value

    def set_offset_z(self, value):
        """Set the offset z value."""
        cmds.setAttr("{}.tz".format(self.transform), value)
        self.scene_db["offset_z"] = value

    def get_offset_x(self):
        """Get the offset x value."""
        return cmds.getAttr("{}.tx".format(self.transform))

    def get_offset_y(self):
        """Get the offset y value."""
        return cmds.getAttr("{}.ty".format(self.transform))

    def get_offset_z(self):
        """Get the offset z value."""
        return cmds.getAttr("{}.tz".format(self.transform))

    def _create_groups(self):
        """Create the required groups if they doesn't exist."""
        if not cmds.objExists(self.master_group):
            cmds.group(name=self.master_group, empty=True)
        if not cmds.objExists(self.transform):
            cmds.group(name=self.transform, empty=True, parent=self.master_group)
        if not cmds.objExists(self.annotations_group):
            cmds.group(
                name=self.annotations_group, empty=True, parent=self.master_group
            )

    def validate_variables(self):
        """Validate if the variables are set correctly.
        Return the LOG message if not.
        """
        if self.active_protocol == None:  # pylint: disable=singleton-comparison
            return False, "No protocol is set. Please set a protocol first using set_active_protocol()"

        # if any of the variables are not set, return False
        inputs = [self._source_mesh, self._target_mesh, self._source_blendshape_grp]
        if not all(inputs):
            return False, ("Some of the variables are not set. "
                           "All Source mesh, Target mesh and Source blendshape group must be set.")

        return True, "Success"


    def preview_mode(self, turn_on=True):
        """Make the preparations for the preview the transfer."""

        # if we are turning off the preview mode, simply hide the group, don't destroy anything.
        if not turn_on:
            cmds.setAttr("{}.v".format(self.master_group), False)
            self.is_preview_on = False
            return True, "Disabled"

        # validate variables
        state, message = self.validate_variables()
        if not state:
            LOG.warning(message)
            return False, message

        # create the master and transform groups if they don't exist
        self._create_groups()

        # PROTOCOL PREPARE

        # set the protocol variables
        self.active_protocol.master_group = self.master_group
        self.active_protocol.source_mesh = self._source_mesh
        self.active_protocol.target_mesh = self._target_mesh
        self.active_protocol.source_blendshape_grp = self._source_blendshape_grp
        self.active_protocol.transform_group = self.transform

        force_qc = False
        # Check if the protocol is prepared (has the groups and nodes created)
        _protocol_scene_data = SceneDictionary(node=self.active_protocol.protocol_group)
        if cmds.objExists(self.active_protocol.protocol_group):
            # Get the defined variables.
            _sd_source_mesh = _protocol_scene_data.get("source_mesh", "")
            _sd_target_mesh = _protocol_scene_data.get("target_mesh", "")
            _sd_source_blendshape_grp = _protocol_scene_data.get(
                "source_blendshape_grp", ""
            )

            # if the variables are not the same, delete the protocol group and recreate it.
            if (
                _sd_source_mesh != self._source_mesh
                or _sd_target_mesh != self._target_mesh
                or _sd_source_blendshape_grp != self._source_blendshape_grp
            ):
                cmds.delete(self.active_protocol.protocol_group)
                cmds.delete(self.annotations_group)
                force_qc = True

        # protocols currently do not overwrite nodes.
        # existing ones will be skipped
        self.active_protocol.prepare()

        # PROTOCOL QC

        _qc_scene_data = SceneDictionary(node=self.annotations_group)

        state = self.active_protocol.qc_blendshapes(separation=1, force=force_qc)

        qc_data = state or _qc_scene_data.get("qc_data", {})


        if state:
            self._create_annotations(qc_data)

        # make sure the visibility of the master group is on:
        cmds.setAttr("{}.v".format(self.master_group), True)

        # set the scene data
        _protocol_scene_data["source_mesh"] = self._source_mesh
        _protocol_scene_data["target_mesh"] = self._target_mesh
        _protocol_scene_data["source_blendshape_grp"] = self._source_blendshape_grp

        _qc_scene_data.update({"qc_data": qc_data})

        self.is_preview_on = True

        return True, "Success"

    def _create_annotations(self, qc_data):
        """Create the annotations."""

        _temp_dup = cmds.duplicate(self._target_mesh, name="trTMP_GARBAGE")[0]
        cmds.setAttr("{}.v".format(_temp_dup), True)
        # parent the temp dup to the world
        # if the _temp_dup is not in the root, move it to the root
        _temp_dup_parent = cmds.listRelatives(_temp_dup, parent=True)
        if _temp_dup_parent:
            cmds.parent(_temp_dup, world=True)

        # delete everything under the annotations group
        _old_annotations = cmds.listRelatives(
            self.annotations_group, children=True, type="transform"
        )
        cmds.delete(_old_annotations)

        _annotation_transform = cmds.group(
            empty=True, name="trTMP_annotation_transform", parent=self.annotations_group
        )

        # get the offset vvalue
        bbx = cmds.xform(_temp_dup, query=True, boundingBox=True, objectSpace=True)
        center_y = (bbx[1] + bbx[4]) * 0.5
        offset = (0, center_y, 0)

        # create the annotations
        for attr, frame_range in qc_data.items():
            annotation = interface.annotate(
                _temp_dup,
                attr,
                offset=offset,
                name="trTMP_{0}_annotate".format(attr),
                visibility_range=frame_range,
            )
            cmds.parent(annotation, _annotation_transform)

        for cha in "xyz":
            cmds.connectAttr(
                "{0}.t{1}".format(self.transform, cha),
                "{0}.t{1}".format(_annotation_transform, cha),
            )

        cmds.delete(_temp_dup)

    def transfer(self, q_progressbar=None):
        """Bake the QC into a shape pack."""

        if not self.is_preview_on:
            state, message = self.preview_mode(turn_on=True)
            if not state:
                return state, message

        # Disable maya viewport update
        cmds.refresh(suspend=True)

        start = time()

        # get the qc data
        _qc_scene_data = SceneDictionary(node=self.annotations_group)

        _current_frame = cmds.currentTime(query=True)

        transferred_shapes_grp = cmds.group(
            empty=True,
            name="TRANSFERRED_{0}_{1}".format(
                self._source_blendshape_grp, self.active_protocol.name
            ),
        )

        # delete the offset cluster
        if self.active_protocol.offset_cluster:
            cmds.delete(self.active_protocol.offset_cluster)

        if q_progressbar:
            q_progressbar.reset()
            q_progressbar.setRange(0, len(_qc_scene_data.get("qc_data", {})))

        count = 0
        for attr, frames in _qc_scene_data.get("qc_data", {}).items():
            cmds.currentTime(frames[0])
            new_blendshape = cmds.duplicate(self.active_protocol.tmp_target)[0]
            functions.delete_intermediates(new_blendshape)

            cmds.setAttr("{}.v".format(new_blendshape), True)  # make sure it's visible
            cmds.parent(new_blendshape, transferred_shapes_grp)
            cmds.rename(new_blendshape, attr)

            # update the progress bar
            if q_progressbar:
                q_progressbar.setValue(count)
                count += 1

        # destroy the tmp meshes
        self.active_protocol.destroy()

        cmds.currentTime(_current_frame)

        if q_progressbar:
            q_progressbar.reset()

        # Enable maya viewport update
        cmds.refresh(suspend=False)
        LOG.info("Time taken: {}".format(time() - start))
        return True, "Transferred Successfully"


