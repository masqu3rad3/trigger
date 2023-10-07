# pylint: disable=consider-using-f-string
"""Core Class for protocols."""
import re
from maya import cmds
from trigger.library import api
from trigger.library import functions
from trigger.library import deformers


class ProtocolCore(dict):
    """Base class for protocols."""

    name = ""
    display_name = ""
    type = None  # "shape" or "topology"

    def __init__(self):

        self.master_group = "trTMP_blndtrans__master"
        self.transform_group = None
        self.protocol_group = "trTMP_{0}__grp".format(self.name)
        self.blendshape_node = None
        self.source_blendshape_node = None
        self.transferred_shapes_grp = None

        self.source_mesh = None
        self.target_mesh = None
        self.source_blendshape_grp = None
        self.blendshape_list = []

        self.tmp_source = None
        self.tmp_target = None
        self.offset_cluster = None

        # we are deliberately not adding the node to the property objects.
        # that will be done in the prepare method
        self["visibility"] = Property(
            attribute_name="visibility",
            attribute_type="boolean",
            default_value=True,
        )

        self["source_visibility"] = Property(
            attribute_name="visibility",
            attribute_type="boolean",
            default_value=True,
        )

        self["target_visibility"] = Property(
            attribute_name="visibility",
            attribute_type="boolean",
            default_value=True,
        )

    def create_protocol_group(self):
        """Create the protocol group if it doesn't exist."""
        if not cmds.objExists(self.protocol_group):
            self.protocol_group = cmds.group(
                empty=True, name=self.protocol_group, parent=self.master_group
            )

        # first apply the existing visibility state to the mesh
        cmds.setAttr(
            "{0}.visibility".format(self.protocol_group), self["visibility"].value
        )

        # add the node to the visibility property
        self["visibility"].node = self.protocol_group

    def prepare(self):
        """Prepare temporary meshes for the protocol."""

        # if source target and blendshape packs are not defined raise error
        if (
            not self.source_mesh
            or not self.target_mesh
            or not self.source_blendshape_grp
        ):
            raise ValueError(
                "Source mesh, target mesh and blendshape pack must be defined"
            )

        # if source and target has different topology, raise error
        if self.type == "shape" and not self.is_same_topology(
            self.source_mesh, self.target_mesh
        ):
            raise ValueError("Source mesh and target mesh must have the same topology")

        # This is the bare minimum for a protocol to work.
        self.create_protocol_group()
        # If the tmp source and targets are already created, use them.
        tmp_source_name = "trTMP_{0}__source_mesh".format(self.name)
        if cmds.objExists("{0}|{1}".format(self.protocol_group, tmp_source_name)):
            self.tmp_source = tmp_source_name
        else:
            self.tmp_source = cmds.duplicate(
                self.source_mesh, name="trTMP_{0}__source_mesh".format(self.name)
            )[0]
            api.unlock_normals(self.tmp_source)
            cmds.parent(self.tmp_source, self.protocol_group)

        # first apply the existing visibility state to the mesh
        cmds.setAttr(
            "{0}.visibility".format(self.tmp_source), self["source_visibility"].value
        )

        # add the node to the source visibility property
        self["source_visibility"].node = self.tmp_source

        tmp_target_name = "trTMP_{0}__target_mesh".format(self.name)
        if cmds.objExists("{0}|{1}".format(self.protocol_group, tmp_target_name)):
            self.tmp_target = tmp_target_name
        else:
            self.tmp_target = cmds.duplicate(
                self.target_mesh, name="trTMP_{0}__target_mesh".format(self.name)
            )[0]
            api.unlock_normals(self.tmp_target)
            cmds.parent(self.tmp_target, self.protocol_group)

        # first apply the existing visibility state to the mesh
        cmds.setAttr(
            "{0}.visibility".format(self.tmp_target), self["target_visibility"].value
        )

        # add the node to the target visibility property
        self["target_visibility"].node = self.tmp_target

        self.blendshape_list = functions.get_meshes(
            self.source_blendshape_grp, full_path=True
        )

    def create_cluster(self):
        """Create a cluster to be used for offsetting the target mesh."""
        offset_cluster_name = "trTMP_{0}__offsetCluster".format(self.name)
        if cmds.objExists(offset_cluster_name):
            self.offset_cluster = cmds.listConnections(
                "{}.matrix".format(offset_cluster_name), source=True, destination=False
            )[0]
        else:
            # create a cluster to be used fo offsetting the target mesh
            self.offset_cluster = cmds.cluster(
                self.tmp_target, name=offset_cluster_name
            )[1]
            cmds.parent(self.offset_cluster, self.protocol_group)
            cmds.hide(functions.get_shapes(self.offset_cluster))  # hide only shape
            for cha in "xyz":
                cmds.connectAttr(
                    "{0}.t{1}".format(self.transform_group, cha),
                    "{0}.t{1}".format(self.offset_cluster, cha),
                )

    def get_blend_attributes(self):
        """Return the available blend attributes."""
        _blend_attributes = deformers.get_influencers(self.blendshape_node)
        if "negateSource" in _blend_attributes:  # remove negateSource
            _blend_attributes.remove("negateSource")
        return _blend_attributes

    def qc_blendshapes(self, separation=1, force=False):
        """Animate the blendshapes for preview."""

        # _current_time = cmds.currentTime(query=True)
        # cmds.currentTime(0)

        qc_data = {}

        # check if there are any keyframes on self.blendshape_node
        # if there are, assume everything is already set-up.
        if cmds.keyframe(self.blendshape_node, query=True, keyframeCount=True):
            if force:
                cmds.cutKey(self.blendshape_node, clear=True)
            else:
                return {}

        blend_attributes = self.get_blend_attributes()

        for nmb, attr in enumerate(blend_attributes):
            start_frame = separation * (nmb + 1)
            end_frame = start_frame + (separation - 1)
            cmds.setKeyframe(
                self.blendshape_node, attribute=attr, time=start_frame - 1, value=0
            )
            cmds.setKeyframe(
                self.blendshape_node, attribute=attr, time=start_frame, value=1
            )
            cmds.setKeyframe(
                self.blendshape_node, attribute=attr, time=end_frame, value=1
            )
            cmds.setKeyframe(
                self.blendshape_node, attribute=attr, time=end_frame + 1, value=0
            )

            if self.source_blendshape_node:
                # This is for comparing between the source and target.
                # Topology transfers doesn't have source blendshape node,
                # Only for same topo transfer
                cmds.setKeyframe(
                    self.source_blendshape_node,
                    attribute=attr,
                    time=start_frame - 1,
                    value=0,
                )
                cmds.setKeyframe(
                    self.source_blendshape_node,
                    attribute=attr,
                    time=start_frame,
                    value=1,
                )
                cmds.setKeyframe(
                    self.source_blendshape_node, attribute=attr, time=end_frame, value=1
                )
                cmds.setKeyframe(
                    self.source_blendshape_node,
                    attribute=attr,
                    time=end_frame + 1,
                    value=0,
                )

                qc_data[attr] = [start_frame, end_frame]
        if self.type == "shape":
            # if the same topo animate the delta shape at the beginning and end of range
            cmds.setKeyframe(
                self.blendshape_node,
                attribute="negateSource",
                time=separation - 1,
                value=0,
            )
            cmds.setKeyframe(
                self.blendshape_node,
                attribute="negateSource",
                time=separation,
                value=-1,
            )
            cmds.setKeyframe(
                self.blendshape_node,
                attribute="negateSource",
                time=separation * len(blend_attributes) + separation - 1,
                value=-1,
            )
            cmds.setKeyframe(
                self.blendshape_node,
                attribute="negateSource",
                time=separation * len(blend_attributes) + separation,
                value=0,
            )

        # extend the timeline range to fit the qc
        cmds.playbackOptions(
            minTime=0, maxTime=separation * len(blend_attributes) + separation
        )

        # cmds.currentTime(_current_time)
        return qc_data

    def refresh(self):
        """Refresh the node state of the blendshape node.
        This is to fix the weird bug in blendshape node where it sometimes fails to update.
        """
        cmds.setAttr("%s.nodeState" % self.blendshape_node, 1)
        cmds.setAttr("%s.nodeState" % self.blendshape_node, 0)

    def destroy(self):
        """Destroy the protocol."""
        if cmds.objExists(self.protocol_group):
            cmds.delete(self.protocol_group)

    @staticmethod
    def is_same_topology(source, target):
        """checks if the source and target shares the same topology"""

        # assume they have the same topology if they have same vertex count
        source_count = len(api.get_all_vertices(source))
        target_count = len(api.get_all_vertices(target))

        return source_count == target_count

    def transfer(self):
        """Bake the QC into a shape pack."""

        # make sure to move to the first frame
        _current_frame = cmds.currentTime(query=True)
        cmds.currentTime(0)

        blend_attributes = deformers.get_influencers(self.blendshape_node)

        # create a TRANSFERRED group to put the shapes in
        self.transferred_shapes_grp = cmds.group(
            empty=True,
            name="TRANSFERRED_{0}_{1}".format(self.source_blendshape_grp, self.name),
        )

        # negateSource is only for the neutral and preview purposes. Remove it from the list.
        if "negateSource" in blend_attributes:
            cmds.setAttr("{}.negateSource".format(self.blendshape_node), -1)
            blend_attributes.remove("negateSource")
        for attr in blend_attributes:
            cmds.setAttr("%s.%s" % (self.blendshape_node, attr), 1)
            new_blendshape = cmds.duplicate(self.tmp_target)[0]

            # cmds.parent(new_blendshape, self.transferShapesGrp)
            # get rid of the intermediates
            functions.delete_intermediates(new_blendshape)

            cmds.parent(new_blendshape, self.transferred_shapes_grp)

            cmds.rename(new_blendshape, attr)
            cmds.setAttr("%s.%s" % (self.blendshape_node, attr), 0)

        # destroy the tmp meshes
        self.destroy()

        cmds.currentTime(_current_frame)


class Property(object):
    """Property item for holding, getting and setting values."""

    def __init__(
        self,
        attribute_name,
        attribute_type,
        default_value,
        minimum=None,
        maximum=None,
        items=None,
        node=None,
        nice_name=None,
    ):
        self.attribute = attribute_name
        self.type = attribute_type
        self.default = default_value
        self.minimum = minimum
        self.maximum = maximum
        self.items = items
        self.nice_name = nice_name or self.camel_case_to_nice_name(attribute_name)
        self.node = node

        self._current_value = default_value

    @property
    def value(self):
        """Get the current value."""
        if self.node and cmds.objExists(self.node):
            return cmds.getAttr("{0}.{1}".format(self.node, self.attribute))
        return self._current_value

    @value.setter
    def value(self, val):
        """Set the value."""
        # if the node is not created yet, use the memory value
        self.set_value(val)
        self._current_value = val

    def set_value(self, val):
        """Set the value."""
        # if the node is not created yet, use the memory value
        if self.type == "boolean":
            val = bool(val)
        if self.node and cmds.objExists(self.node):
            cmds.setAttr("{0}.{1}".format(self.node, self.attribute), val)
        self._current_value = val

    @staticmethod
    def camel_case_to_nice_name(input_str):
        """Convert camel case to nice name."""
        # Use regular expression to split the string at camel case boundaries
        words = re.findall(r"[A-Z][a-z]*|[a-z]+", input_str)

        # Capitalize the first letter of each word and join them with a space
        nice_name = " ".join(word.capitalize() for word in words)

        return nice_name
