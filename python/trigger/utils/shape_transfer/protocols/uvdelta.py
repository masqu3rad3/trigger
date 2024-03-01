"""Uv Delta Transfer Protocol.
This method allows the user to transfer Shapes between two topologically different meshes by sampling UVs.
"""

from maya import cmds
from trigger.utils.shape_transfer.protocol_core import ProtocolCore, Property


class UvDeltaTransfer(ProtocolCore):
    name = "uvDeltaTransfer"
    display_name = "UV Delta Transfer"
    type = "shape"

    def __init__(self):
        super(UvDeltaTransfer, self).__init__()

        self.blendshape_node = "trTMP_{0}_blendshape".format(self.name)
        self.transfer_attr_node = "trTMP_{}_attr_trns".format(self.name)
        self.tmp_match_mesh = "trTMP_{}_match_mesh".format(self.name)
        self.tmp_delta_negate_mesh = "trTMP_{}_delta_negate".format(self.name)
        self.tmp_target_blendshape = "trTMP_{}_target_blendshape".format(self.name)

        self.exposed_properties = [
            "envelope",
            "sourceUVSpace",
            "targetUVSpace",
        ]

        self["envelope"] = Property(
            attribute_name="envelope",
            attribute_type="slider",
            default_value=1.0,
            minimum=0.0,
            maximum=1.0,
            node=self.blendshape_node,
        )

        self["sourceUVSpace"] = Property(
            attribute_name="sourceUVSpace",
            attribute_type="list",
            nice_name="Source UV Set",
            default_value="",
            items=[],
            node=self.transfer_attr_node,
        )

        self["targetUVSpace"] = Property(
            attribute_name="targetUVSpace",
            attribute_type="list",
            nice_name="Target UV Set",
            default_value="",
            items=[],
            node=self.transfer_attr_node,
        )

        # self.ui_refresh()

    def ui_refresh(self):
        """Override the ui_refresh method to add the UV set selection."""
        super(UvDeltaTransfer, self).ui_refresh()

        if self.source_mesh:
            # get the UV sets from the source mesh
            _source_uv_sets = cmds.polyUVSet(
                self.source_mesh, query=True, allUVSets=True
            )
            # create the attributes for the source UV sets
            self["sourceUVSpace"].items = _source_uv_sets
            if self["sourceUVSpace"].value not in _source_uv_sets:
                self["sourceUVSpace"].value = _source_uv_sets[0]

        if self.target_mesh:
            # get the UV sets from the target mesh
            _target_uv_sets = cmds.polyUVSet(
                self.target_mesh, query=True, allUVSets=True
            )
            # create the attributes for the target UV sets
            self["targetUVSpace"].items = _target_uv_sets
            if self["targetUVSpace"].value not in _target_uv_sets:
                self["targetUVSpace"].value = _target_uv_sets[0]

    def prepare(self):
        """Prepare the protocol for execution."""
        super(UvDeltaTransfer, self).prepare()

        # UV based delta transfer starts similar to a topology transfer
        # we will first match the shapes than apply the difference on top.

        # apply the blendshape to the SOURCE duplicate.
        if not cmds.objExists(self.blendshape_node):
            cmds.blendShape(
                self.blendshape_list,
                self.tmp_source,
                w=[0, 0],
                name=self.blendshape_node,
            )

        # create another duplicate of the target to hold the UV based vertex transfer.
        if not cmds.objExists(self.tmp_match_mesh):
            cmds.duplicate(self.target_mesh, name=self.tmp_match_mesh)[0]
            cmds.parent(self.tmp_match_mesh, self.protocol_group)

        # _tmp_attr_trns_node = "trTMP_{}_attr_trns".format(self.name)
        # TODO: EXPOSE source and target UV channel selections to the UI.

        _source_uv_space = self["sourceUVSpace"].value
        _target_uv_space = self["targetUVSpace"].value

        if not cmds.objExists(self.transfer_attr_node):
            _to_be_renamed = cmds.transferAttributes(
                self.tmp_source,
                self.tmp_match_mesh,
                transferPositions=1,
                transferNormals=0,
                transferUVs=0,
                transferColors=0,
                sampleSpace=3,
                sourceUvSpace=_source_uv_space,
                targetUvSpace=_target_uv_space,
                searchMethod=3,
                flipUVs=0,
                colorBorders=1,
            )
            cmds.rename(_to_be_renamed[0], self.transfer_attr_node)

        # duplicate the _tmp_match_mesh with its current neutral shape to be used as a delta negate.
        if not cmds.objExists(self.tmp_delta_negate_mesh):
            cmds.duplicate(self.tmp_match_mesh, name=self.tmp_delta_negate_mesh)[0]

        # apply the _tmp_match_mesh and _tmp_delta_negate to the self.tmp_target with a blendshape.
        # make sure the _tmp_match_mesh has a weight of 1.0 and _tmp_delta_negate has a weight of -1.0
        if not cmds.objExists(self.tmp_target_blendshape):
            cmds.blendShape(
                self.tmp_match_mesh,
                self.tmp_delta_negate_mesh,
                self.tmp_target,
                w=[(0, 1), (1, -1)],
                name=self.tmp_target_blendshape,
            )

        cmds.hide([self.tmp_match_mesh, self.tmp_delta_negate_mesh])

        self.create_cluster()
