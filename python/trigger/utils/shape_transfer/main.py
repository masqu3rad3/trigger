from maya import cmds, mel

from trigger.library import api
from trigger.library import functions
from trigger.library import deformers
from trigger.library import interface

from trigger.utils.shape_transfer import protocols


class ShapeTransfer(object):
    def __init__(
        self, source_mesh=None, target_mesh=None, source_blendshape_grp=None
    ):
        super(ShapeTransfer, self).__init__()

        # user defined
        self.source_mesh = source_mesh
        self.target_mesh = target_mesh
        self._source_blendshape_grp = source_blendshape_grp

        # general settings
        self.master_group = "trTMP_blndtrans__master"
        if not cmds.objExists(self.master_group):
            cmds.group(name=self.master_group, empty=True)
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
                self._shape_protocols.append(protocol)
            elif protocol.type == "topology":
                self._topology_protocols.append(protocol)

        self.active_protocol = None

    # @property
    # def source_mesh(self):
    #     return self._source_mesh
    #
    # @source_mesh.setter
    # def source_mesh(self, new_value):
    #     self._source_mesh = new_value
    #
    # @property
    # def target_mesh(self):
    #     return self._target_mesh
    #
    # @target_mesh.setter
    # def target_mesh(self, new_value):
    #     self._target_mesh = new_value
    #
    # @property
    # def source_blendshape_grp(self):
    #     return self._source_blendshape_grp
    #
    # @source_blendshape_grp.setter
    # def source_blendshape_grp(self, new_value):
    #     self._source_blendshape_grp = new_value

    @property
    def shape_protocols(self):
        return self._shape_protocols

    @property
    def topology_protocols(self):
        return self._topology_protocols

    def set_active_protocol(self, protocol_name):
        """Set the active protocol."""
        for protocol in protocols.classes:
            if protocol.name == protocol_name:
                self.active_protocol = protocol
                return True
        raise ValueError("Protocol {} doesn't exist".format(protocol_name))

    # def _prepare_meshes(self):
    #     """adds blendshape and wrap nodes to prepare the transfer"""
    #     if not self.active_protocol:
    #         raise ValueError("No protocol is set. Please set a protocol first using set_active_protocol()")
    #     if not self.source_mesh:
    #         raise ValueError("Source mesh is not set")
    #     if not self.target_mesh:
    #         raise ValueError("Target mesh is not set")
    #     if not self._source_blendshape_grp:
    #         raise ValueError("Source blendshape group is not set")
    #
    #     # instanciate the protocol
    #     protocol = self.active_protocol(self.source_mesh, self.target_mesh, self._source_blendshape_grp)
    #     protocol.prepare()
    #     return True


    def tweak_offset(self, values):
        if self.offsetCluster and cmds.objExists(self.offsetCluster[1]):
            cmds.setAttr("%s.t" % self.offsetCluster[1], *values)
            self.offsetValue = list(values)
        return

    def preview_mode_on(self):
        """Make the preparations for the preview the transfer."""

        # validate variables
        if not self.active_protocol:
            raise ValueError("No protocol is set. Please set a protocol first using set_active_protocol()")
        if not self.source_mesh:
            raise ValueError("Source mesh is not set")
        if not self.target_mesh:
            raise ValueError("Target mesh is not set")
        if not self._source_blendshape_grp:
            raise ValueError("Source blendshape group is not set")

        # create the master group if it doesn't exist
        if not cmds.objExists(self.master_group):
            cmds.group(name=self.master_group, empty=True)

        # instance the protocol
        protocol = self.active_protocol(self.source_mesh, self.target_mesh, self._source_blendshape_grp)
        protocol.prepare()

        if protocol.protocol_group not in cmds.listRelatives(self.master_group, children=True):
            cmds.parent(protocol.protocol_group, self.master_group)
        # if the protocol cluster is not already a child of the transform, parent it
        # if not cmds.listRelatives(protocol.offset_cluster, parent=True) == self.transform:
        #     cmds.parent(protocol.offset_cluster[1], self.transform)

        _state = protocol.qc_blendshapes(separation=5)

        # make a direct connection to the protocol's offset cluster
        if _state:
            for ch in "xyz":
                cmds.connectAttr("{0}.t{1}".format(self.transform, ch), "{0}.t{1}".format(protocol.offset_cluster, ch), force=True)
                cmds.connectAttr("{0}.t{1}".format(self.transform, ch), "{0}.t{1}".format(protocol.annotations_group, ch), force=True)

        cmds.setAttr("%s.t" % self.transform, *self.offsetValue)


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
                grp = cmds.group(em=True, parent=self.transferShapesGrp, name=group_name)
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

