"""Main module for the shape transfer tool."""

from maya import cmds

from trigger.utils.shape_transfer.scene_data import SceneDictionary
from trigger.utils.shape_transfer import protocols

class ShapeTransfer(object):
    def __init__(self):
        super(ShapeTransfer, self).__init__()

        self.master_group = "trTMP_blndtrans__master"
        self.scene_db = SceneDictionary(node=self.master_group)
        self.transform = "trTMP_blndtrans__transform"

        # create the groups if they don't exist
        self._create_groups()

        print("DEBUG")
        print(self.scene_db.get("source_mesh", ""))
        print(self.scene_db.get("source_mesh", ""))
        print(self.scene_db.get("source_mesh", ""))
        print(self.scene_db.get("source_mesh", ""))
        print(self.scene_db.get("source_mesh", ""))
        self._source_mesh = self.scene_db.get("source_mesh", "")
        self._target_mesh = self.scene_db.get("target_mesh", "")
        self._source_blendshape_grp = self.scene_db.get("source_blendshape_grp", "")

        self._offset_x = self.scene_db.get("offset_x", 0.0)
        self._offset_y = self.scene_db.get("offset_y", 0.0)
        self._offset_z = self.scene_db.get("offset_z", 0.0)

        # self.query_scene_data()

        # general settings
        # self.create_master_group()
        # if not cmds.objExists(self.master_group):
        #     cmds.group(name=self.master_group, empty=True)
        # if not cmds.objExists(self.transform):
        #     cmds.group(name=self.transform, empty=True, parent=self.master_group)
        # self.offsetValue = [0, 3, 0]
        # self.master_offset_transform = None

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
        self.scene_db["source_mesh"] = self._source_mesh
        # cmds.setAttr(
        #     "{}.source_mesh".format(self.master_group), self._source_mesh, type="string"
        # )

    def set_target_mesh(self, target_mesh):
        """Set the target mesh and update the message attribute."""
        self._target_mesh = target_mesh
        self.scene_db["target_mesh"] = self._target_mesh
        # cmds.setAttr(
        #     "{}.target_mesh".format(self.master_group), self._target_mesh, type="string"
        # )

    def set_source_blendshape_grp(self, source_blendshape_grp):
        """Set the source blendshape group and update the message attribute."""
        self._source_blendshape_grp = source_blendshape_grp
        self.scene_db["source_blendshape_grp"] = self._source_blendshape_grp
        # cmds.setAttr(
        #     "{}.source_blendshape_grp".format(self.master_group),
        #     self._source_blendshape_grp,
        #     type="string",
        # )

    # def query_scene_data(self):
    #     """Query the previously defined meshes from the scene and group message attribute."""
    #     # first check if the master group exists
    #     if not cmds.objExists(self.master_group):
    #         return False
    #     # check if the message attributes exist
    #     if cmds.attributeQuery("source_mesh", node=self.master_group, exists=True):
    #         _source_mesh = cmds.getAttr("{}.source_mesh".format(self.master_group))
    #         if cmds.objExists(_source_mesh):
    #             self._source_mesh = _source_mesh
    #     if cmds.attributeQuery("target_mesh", node=self.master_group, exists=True):
    #         _target_mesh = cmds.getAttr("{}.target_mesh".format(self.master_group))
    #         if cmds.objExists(_target_mesh):
    #             self._target_mesh = _target_mesh
    #     if cmds.attributeQuery(
    #         "source_blendshape_grp", node=self.master_group, exists=True
    #     ):
    #         _source_blendshape_grp = cmds.getAttr(
    #             "{}.source_blendshape_grp".format(self.master_group)
    #         )
    #         if cmds.objExists(_source_blendshape_grp):
    #             self._source_blendshape_grp = _source_blendshape_grp

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
        self.scene_db["offset_x"] = value

    def set_offset_y(self, value):
        cmds.setAttr("{}.ty".format(self.transform), value)
        self.scene_db["offset_y"] = value

    def set_offset_z(self, value):
        cmds.setAttr("{}.tz".format(self.transform), value)
        self.scene_db["offset_z"] = value

    def get_offset_x(self):
        return cmds.getAttr("{}.tx".format(self.transform))

    def get_offset_y(self):
        return cmds.getAttr("{}.ty".format(self.transform))

    def get_offset_z(self):
        return cmds.getAttr("{}.tz".format(self.transform))

    # def tweak_offset(self, values):
    #     if self.offsetCluster and cmds.objExists(self.offsetCluster[1]):
    #         cmds.setAttr("%s.t" % self.offsetCluster[1], *values)
    #         self.offsetValue = list(values)
    #     return

    def _create_groups(self):
        """Create the required groups if they doesn't exist."""
        if not cmds.objExists(self.master_group):
            cmds.group(name=self.master_group, empty=True)
        if not cmds.objExists(self.transform):
            cmds.group(name=self.transform, empty=True, parent=self.master_group)

    # def create_master_group(self):
    #     """Create the master group."""
    #     if cmds.objExists(self.master_group):
    #         return self.master_group
    #
    #     cmds.group(name=self.master_group, empty=True)
    #     # add the source_mesh, target_mesh and source_blendshape_grp info as a message attribute
    #     # so that we can query them later
    #     cmds.addAttr(self.master_group, longName="source_mesh", dataType="string")
    #     cmds.setAttr(
    #         "{}.source_mesh".format(self.master_group),
    #         self._source_mesh or "",
    #         type="string",
    #     )
    #     cmds.addAttr(self.master_group, longName="target_mesh", dataType="string")
    #     cmds.setAttr(
    #         "{}.target_mesh".format(self.master_group),
    #         self._target_mesh or "",
    #         type="string",
    #     )
    #     cmds.addAttr(
    #         self.master_group, longName="source_blendshape_grp", dataType="string"
    #     )
    #     cmds.setAttr(
    #         "{}.source_blendshape_grp".format(self.master_group),
    #         self._source_blendshape_grp or "",
    #         type="string",
    #     )
    #
    #     cmds.addAttr(self.master_group, longName="offset_x", attributeType="double", defaultValue=self._offset_x)
    #     cmds.addAttr(self.master_group, longName="offset_y", attributeType="double", defaultValue=self._offset_y)
    #     cmds.addAttr(self.master_group, longName="offset_z", attributeType="double", defaultValue=self._offset_z)

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

        # create the master and transform groups if they don't exist
        self._create_groups()

        # set the protocol variables
        self.active_protocol.source_mesh = self._source_mesh
        self.active_protocol.target_mesh = self._target_mesh
        self.active_protocol.source_blendshape_grp = self._source_blendshape_grp

        self.active_protocol.prepare()
        #
        if self.active_protocol.protocol_group not in cmds.listRelatives(
            self.master_group, children=True
        ):
            cmds.parent(self.active_protocol.protocol_group, self.master_group)
        # if the protocol cluster is not already a child of the transform, parent it
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

        # cmds.setAttr("%s.t" % self.transform, *self.offsetValue)

        # make sure the visibility of the master group is on:
        cmds.setAttr("{}.v".format(self.master_group), True)

