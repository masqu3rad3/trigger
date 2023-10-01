"""Core Class for protocols."""
import re
from maya import cmds
from trigger.library import api
from trigger.library import functions
from trigger.library import deformers
from trigger.library import interface


class ProtocolCore(dict):
    """Base class for protocols."""

    name = ""
    display_name = ""
    type = None  # "shape" or "topology"

    def __init__(self, source_mesh, target_mesh, blendshape_pack):

        self.master_group = "trTMP_blndtrans__master"
        self.protocol_group = None
        self.annotations_group = None
        self.blendshape_node = None
        self.source_blendshape_node = None

        self.source_mesh = source_mesh
        self.target_mesh = target_mesh
        self.blendshape_pack = blendshape_pack
        self.blendshape_list = []

        self.tmp_source = None
        self.tmp_target = None
        self.offset_cluster = None

    # @property
    # def visibility(self):
    #     """Return the visibility of the protocol."""
    #     return cmds.getAttr("{}.v".format(self.protocol_group))
    #
    # @visibility.setter
    # def visibility(self, value):
    #     """Set the visibility of the protocol."""
    #     cmds.setAttr("{}.v".format(self.protocol_group), value)
    #
    # @property
    # def source_visibility(self):
    #     """Return the source mesh visibility."""
    #     return cmds.getAttr("{}.v".format(self.tmp_source))
    #
    # @source_visibility.setter
    # def source_visibility(self, value):
    #     """Set the source mesh visibility."""
    #     cmds.setAttr("{}.v".format(self.tmp_source), value)
    #
    # @property
    # def target_visibility(self):
    #     """Return the target mesh visibility."""
    #     return cmds.getAttr("{}.v".format(self.tmp_target))
    #
    # @target_visibility.setter
    # def target_visibility(self, value):
    #     """Set the target mesh visibility."""
    #     cmds.setAttr("{}.v".format(self.tmp_target), value)

    def create_protocol_group(self):
        """Create the protocol group if it doesn't exist."""
        _grp_name = "trTMP_{0}__grp".format(self.name)
        if not cmds.objExists(_grp_name):
            self.protocol_group = cmds.group(empty=True, name=_grp_name)
        else:
            self.protocol_group = _grp_name
        self["visibility"] = Property(
            attribute_name="visibility",
            attribute_type="float",
            node=self.protocol_group,
            default_value=0.0,
            minimum=-99999,
            maximum=99999,
        )

    def prepare(self):
        """Prepare temporary meshes for the protocol."""

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

        self["source_visibility"] = Property(
            attribute_name="visibility",
            attribute_type="float",
            node=self.tmp_source,
            default_value=0.0,
            minimum=-99999,
            maximum=99999,
        )

        tmp_target_name = "trTMP_{0}__target_mesh".format(self.name)
        if cmds.objExists("{0}|{1}".format(self.protocol_group, tmp_target_name)):
            self.tmp_target = tmp_target_name
        else:
            self.tmp_target = cmds.duplicate(
                self.target_mesh, name="trTMP_{0}__target_mesh".format(self.name)
            )[0]
            api.unlock_normals(self.tmp_target)
            cmds.parent(self.tmp_target, self.protocol_group)

        self["target_visibility"] = Property(
            attribute_name="visibility",
            attribute_type="float",
            node=self.tmp_target,
            default_value=0.0,
            minimum=-99999,
            maximum=99999,
        )

        offset_cluster_name = "trTMP_{0}__offsetCluster".format(self.name)
        if cmds.objExists(offset_cluster_name):
            self.offset_cluster = offset_cluster_name
        else:
            # create a cluster to be used fo offsetting the target mesh
            self.offset_cluster = cmds.cluster(
                self.tmp_target, name=offset_cluster_name
            )
            cmds.parent(self.offset_cluster[1], self.protocol_group)
            cmds.hide(functions.get_shapes(self.offset_cluster[1])) # hide only shape

        self.blendshape_list = functions.get_meshes(
            self.blendshape_pack, full_path=True
        )

    def qc_blendshapes(self, separation=5):
        """Animate the blendshapes for preview."""
        annotations_group_name = "trTMP_{0}__annotations".format(self.name)
        if cmds.objExists(
            "{0}|{1}".format(self.protocol_group, annotations_group_name)
        ):
            self.annotations_group = annotations_group_name
            # if the annotations group already exists, assume that qc blendshapes are ready
            return

        self.annotations_group = cmds.group(empty=True, name=annotations_group_name)
        cmds.parent(self.annotations_group, self.protocol_group)

        blend_attributes = deformers.get_influencers(self.blendshape_node)
        if "negateSource" in blend_attributes:
            blend_attributes.remove("negateSource")

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
            # annotations
            center = cmds.objectCenter(self.tmp_target, gl=True)
            raw = cmds.xform(self.tmp_target, query=1, boundingBox=1)
            offset = (0, (raw[4] - center[1]) * 1.1, 0)

            annotation = interface.annotate(
                self.tmp_target,
                attr,
                offset=offset,
                name="trTMP_{0}_annotate_{1}".format(self.name, attr),
                visibility_range=[start_frame, end_frame],
            )
            cmds.parent(annotation, self.annotations_group)
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
        cmds.playbackOptions(min=1, max=separation * len(blend_attributes) + separation)

    def refresh(self):
        """To fix weird maya bug with blendshape node which is not triggering the next target after the cursor
        for some reason"""
        cmds.setAttr("%s.nodeState" % self.blendshape_node[0], 1)
        cmds.setAttr("%s.nodeState" % self.blendshape_node[0], 0)

    def destroy(self):
        """Destroy the protocol."""
        if cmds.objExists(self.protocol_group):
            cmds.delete(self.protocol_group)


class Property(object):
    """Simple property item."""

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
        if self.node:
            return cmds.getAttr("{0}.{1}".format(self.node, self.attribute))
        return self._current_value

    @value.setter
    def value(self, val):
        """Set the value."""
        # if the node is not created yet, use the memory value
        if self.node:
            cmds.setAttr("{0}.{1}".format(self.node, self.attribute), val)
        self._current_value = val

    @staticmethod
    def camel_case_to_nice_name(input_str):
        # Use regular expression to split the string at camel case boundaries
        words = re.findall(r"[A-Z][a-z]*|[a-z]+", input_str)

        # Capitalize the first letter of each word and join them with a space
        nice_name = " ".join(word.capitalize() for word in words)

        return nice_name
