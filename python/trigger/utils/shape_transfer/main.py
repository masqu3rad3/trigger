"""Main module for the shape transfer tool."""

from maya import cmds, mel

from trigger.library import api
from trigger.library import functions
from trigger.library import deformers
from trigger.library import interface

from trigger.utils.shape_transfer import protocols


class ShapeTransfer(object):
    def __init__(
        # self, source_mesh=None, target_mesh=None, source_blendshape_grp=None
        self,
    ):
        super(ShapeTransfer, self).__init__()

        # user defined
        # self.source_mesh = source_mesh or ""
        # self.target_mesh = target_mesh or ""
        # self.source_blendshape_grp = source_blendshape_grp or ""

        self.master_group = "trTMP_blndtrans__master"

        self._source_mesh = ""
        self._target_mesh = ""
        self._source_blendshape_grp = ""
        self.query_scene_data()

        # general settings
        self.create_master_group()
        # if not cmds.objExists(self.master_group):
        #     cmds.group(name=self.master_group, empty=True)
        self.transform = "trTMP_blndtrans__transform"
        if not cmds.objExists(self.transform):
            cmds.group(name=self.transform, empty=True, parent=self.master_group)
        self.offsetValue = [0, 3, 0]
        self.master_offset_transform = None

        self._source_visible = False
        self._target_visible = True

        self._meshes_ready = False

        self._shape_protocols = []
        self._topology_protocols = []
        for protocol in protocols.classes:
            if protocol.type == "shape":
                self._shape_protocols.append(protocol())
            elif protocol.type == "topology":
                self._topology_protocols.append(protocol())

        self.active_protocol = None

    def set_source_mesh(self, source_mesh):
        """Set the source mesh and update the message attribute."""
        self._source_mesh = source_mesh
        cmds.setAttr(
            "{}.source_mesh".format(self.master_group), self._source_mesh, type="string"
        )

    def set_target_mesh(self, target_mesh):
        """Set the target mesh and update the message attribute."""
        self._target_mesh = target_mesh
        cmds.setAttr(
            "{}.target_mesh".format(self.master_group), self._target_mesh, type="string"
        )

    def set_source_blendshape_grp(self, source_blendshape_grp):
        """Set the source blendshape group and update the message attribute."""
        self._source_blendshape_grp = source_blendshape_grp
        cmds.setAttr(
            "{}.source_blendshape_grp".format(self.master_group),
            self._source_blendshape_grp,
            type="string",
        )

    def query_scene_data(self):
        """Query the previously defined meshes from the scene and group message attribute."""
        # first check if the master group exists
        if not cmds.objExists(self.master_group):
            return False
        # check if the message attributes exist
        if cmds.attributeQuery("source_mesh", node=self.master_group, exists=True):
            _source_mesh = cmds.getAttr("{}.source_mesh".format(self.master_group))
            if cmds.objExists(_source_mesh):
                self._source_mesh = _source_mesh
        if cmds.attributeQuery("target_mesh", node=self.master_group, exists=True):
            _target_mesh = cmds.getAttr("{}.target_mesh".format(self.master_group))
            if cmds.objExists(_target_mesh):
                self._target_mesh = _target_mesh
        if cmds.attributeQuery(
            "source_blendshape_grp", node=self.master_group, exists=True
        ):
            _source_blendshape_grp = cmds.getAttr(
                "{}.source_blendshape_grp".format(self.master_group)
            )
            if cmds.objExists(_source_blendshape_grp):
                self._source_blendshape_grp = _source_blendshape_grp

    @property
    def shape_protocols(self):
        return self._shape_protocols

    @property
    def topology_protocols(self):
        return self._topology_protocols

    @property
    def all_protocols(self):
        return self._shape_protocols + self._topology_protocols

    def set_active_protocol(self, protocol):
        """Set the protocol."""
        # Validate the protocol
        if not isinstance(protocol, protocols.ProtocolCore):
            raise ValueError("Protocol must be a subclass of ProtocolCore")
        if protocol not in self.shape_protocols + self.topology_protocols:
            raise ValueError("Protocol {} doesn't exist".format(protocol))
        self.active_protocol = protocol

    def set_active_protocol_by_name(self, protocol_name):
        """Set the active protocol."""
        for protocol in self.shape_protocols + self.topology_protocols:
            if protocol.name == protocol_name:
                self.active_protocol = protocol
                return True
        raise ValueError("Protocol {} doesn't exist".format(protocol_name))

    def set_offset_x(self, value):
        cmds.setAttr("{}.tx".format(self.transform), value)

    def set_offset_y(self, value):
        cmds.setAttr("{}.ty".format(self.transform), value)

    def set_offset_z(self, value):
        cmds.setAttr("{}.tz".format(self.transform), value)

    def get_offset_x(self):
        return cmds.getAttr("{}.tx".format(self.transform))

    def get_offset_y(self):
        return cmds.getAttr("{}.ty".format(self.transform))

    def get_offset_z(self):
        return cmds.getAttr("{}.tz".format(self.transform))

    def tweak_offset(self, values):
        if self.offsetCluster and cmds.objExists(self.offsetCluster[1]):
            cmds.setAttr("%s.t" % self.offsetCluster[1], *values)
            self.offsetValue = list(values)
        return

    def create_master_group(self):
        """Create the master group."""
        if cmds.objExists(self.master_group):
            return self.master_group

        cmds.group(name=self.master_group, empty=True)
        # add the source_mesh, target_mesh and source_blendshape_grp info as a message attribute
        # so that we can query them later
        cmds.addAttr(self.master_group, longName="source_mesh", dataType="string")
        cmds.setAttr(
            "{}.source_mesh".format(self.master_group),
            self._source_mesh or "",
            type="string",
        )
        cmds.addAttr(self.master_group, longName="target_mesh", dataType="string")
        cmds.setAttr(
            "{}.target_mesh".format(self.master_group),
            self._target_mesh or "",
            type="string",
        )
        cmds.addAttr(
            self.master_group, longName="source_blendshape_grp", dataType="string"
        )
        cmds.setAttr(
            "{}.source_blendshape_grp".format(self.master_group),
            self._source_blendshape_grp or "",
            type="string",
        )

    def preview_mode(self, turn_on=True):
        """Make the preparations for the preview the transfer."""

        # if we are turning off the preview mode, simply hide the group, don't destroy anything.
        if not turn_on:
            cmds.setAttr("{}.v".format(self.master_group), False)
            return

        # validate variables
        if self.active_protocol == None:  # pylint: disable=singleton-comparison
            raise ValueError(
                "No protocol is set. Please set a protocol first using set_active_protocol()"
            )
        if not self._source_mesh:
            raise ValueError("Source mesh is not set")
        if not self._target_mesh:
            raise ValueError("Target mesh is not set")
        if not self._source_blendshape_grp:
            raise ValueError("Source blendshape group is not set")

        # create the master group if it doesn't exist
        self.create_master_group()
        # if not cmds.objExists(self.master_group):
        #     cmds.group(name=self.master_group, empty=True)

        # instance the protocol
        # protocol = self.active_protocol(self.source_mesh, self.target_mesh, self._source_blendshape_grp)
        # protocol.prepare()

        self.active_protocol.source_mesh = self._source_mesh
        self.active_protocol.target_mesh = self._target_mesh
        self.active_protocol.source_blendshape_grp = self._source_blendshape_grp

        self.active_protocol.prepare()

        if self.active_protocol.protocol_group not in cmds.listRelatives(
            self.master_group, children=True
        ):
            cmds.parent(self.active_protocol.protocol_group, self.master_group)
        # if the protocol cluster is not already a child of the transform, parent it
        # if not cmds.listRelatives(protocol.offset_cluster, parent=True) == self.transform:
        #     cmds.parent(protocol.offset_cluster[1], self.transform)

        _state = self.active_protocol.qc_blendshapes(separation=5)

        # make a direct connection to the protocol's offset cluster
        if _state:
            for ch in "xyz":
                cmds.connectAttr(
                    "{0}.t{1}".format(self.transform, ch),
                    "{0}.t{1}".format(self.active_protocol.offset_cluster, ch),
                    force=True,
                )
                cmds.connectAttr(
                    "{0}.t{1}".format(self.transform, ch),
                    "{0}.t{1}".format(self.active_protocol.annotations_group, ch),
                    force=True,
                )

        cmds.setAttr("%s.t" % self.transform, *self.offsetValue)

        # make sure the visibility of the master group is on:
        cmds.setAttr("{}.v".format(self.master_group), True)

        # self.offsetCluster = cmds.cluster(
        #     self.active_protocol.tmp_target, name="trTMP_blndtrans__offsetCluster"
        # )
        # cmds.parent(self.annotationsGrp, self.offsetCluster[1])
        # cmds.parent(self.offsetCluster[1], self.transferShapesGrp)
        # cmds.hide(functions.get_shapes(self.offsetCluster[1]))  # hide only shape

        # self._meshes_ready = True

    def preview_mode_off(self):
        functions.delete_object("trTMP_blndtrans_*")
        functions.delete_object(self.transferShapesGrp)
        functions.delete_object(self.wrap_node)

        self._meshes_ready = False

    def transfer(self):
        if not self._meshes_ready:
            self.preview_mode_off()
            self._prepare_meshes()
        else:
            # meshes are ready, just discard the offset cluster
            cmds.currentTime(0)
            functions.delete_object(self.offsetCluster)

        blend_attributes = deformers.get_influencers(self.blendshapeNode)
        if "negateSource" in blend_attributes:
            cmds.setAttr("{}.negateSource".format(self.blendshapeNode[0]), -1)
            blend_attributes.remove("negateSource")
        for attr in blend_attributes:
            cmds.setAttr("%s.%s" % (self.blendshapeNode[0], attr), 1)
            new_blendshape = cmds.duplicate(self.tmpTarget)[0]
            # cmds.parent(new_blendshape, self.transferShapesGrp)
            # get rid of the intermediates
            functions.delete_intermediates(new_blendshape)
            # put in a group which facial tools likes
            splits = attr.split("__")
            if len(splits) > 1:
                group_name = "{}_grp".format(splits[1])
                grp = cmds.group(
                    em=True, parent=self.transferShapesGrp, name=group_name
                )
                cmds.parent(new_blendshape, grp)

            cmds.rename(new_blendshape, attr)
            cmds.setAttr("%s.%s" % (self.blendshapeNode[0], attr), 0)
        functions.delete_object("trTMP_blndtrans_*")
        cmds.rename(
            self.transferShapesGrp,
            "TRANSFERRED_{}".format(self._source_blendshape_grp),
        )

    @staticmethod
    def is_same_topology(source, target):
        """checks if the source and target shares the same topology"""

        # assume they have the same topology if they have same vertex count
        source_count = len(api.get_all_vertices(source))
        target_count = len(api.get_all_vertices(target))

        return source_count == target_count

    @staticmethod
    def validate_plugin(plugin_name):
        """Make sure the given plugin is loaded."""
        if not cmds.pluginInfo(plugin_name, loaded=True, query=True):
            try:
                cmds.loadPlugin(plugin_name)
                return True
            except Exception as e:
                msg = "{} cannot be initialized".format(plugin_name)
                cmds.warning(msg)
                return False
        return True
