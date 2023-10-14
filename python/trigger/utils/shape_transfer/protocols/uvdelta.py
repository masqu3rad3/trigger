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

    def prepare(self):
        """Prepare the protocol for execution."""
        super(UvDeltaTransfer, self).prepare()

        # UV based delta transfer starts similar to a topology transfer
        # we will first match the shapes than apply the difference on top.

        # apply the blendshape to the SOURCE duplicate.
        self.blendshape_node = "trTMP_{0}_blendshape".format(self.name)
        if not cmds.objExists(self.blendshape_node):
            cmds.blendShape(
                self.blendshape_list,
                self.tmp_source,
                w=[0, 0],
                name=self.blendshape_node,
            )

        # create another duplicate of the target to hold the UV based vertex transfer.
        _tmp_match_mesh = "trTMP_{}_match_mesh".format(self.name)
        if not cmds.objExists(_tmp_match_mesh):
            cmds.duplicate(self.target_mesh, name=_tmp_match_mesh)[0]
            cmds.parent(_tmp_match_mesh, self.protocol_group)

        _tmp_attr_trns_node = "trTMP_{}_attr_trns".format(self.name)
        # TODO: EXPOSE source and target UV channel selections to the UI.
        if not cmds.objExists(_tmp_attr_trns_node):
            cmds.transferAttributes(
                self.tmp_source,
                _tmp_match_mesh,
                transferPositions=1,
                transferNormals=0,
                transferUVs=0,
                transferColors=0,
                sampleSpace=3,
                sourceUvSpace="map1",
                targetUvSpace="map1",
                searchMethod=3,
                flipUVs=0,
                colorBorders=1,
            )

        # duplicate the _tmp_match_mesh with its current neutral shape to be used as a delta negate.
        _tmp_delta_negate_mesh = "trTMP_{}_delta_negate".format(self.name)
        if not cmds.objExists(_tmp_delta_negate_mesh):
            cmds.duplicate(_tmp_match_mesh, name=_tmp_delta_negate_mesh)[0]

        # apply the _tmp_match_mesh and _tmp_delta_negate to the self.tmp_target with a blendshape.
        # make sure the _tmp_match_mesh has a weight of 1.0 and _tmp_delta_negate has a weight of -1.0
        _tmp_target_blendshape = "trTMP_{}_target_blendshape".format(self.name)
        if not cmds.objExists(_tmp_target_blendshape):
            cmds.blendShape(
                _tmp_match_mesh,
                _tmp_delta_negate_mesh,
                self.tmp_target,
                w=[(0, 1), (1, -1)],
                name=_tmp_target_blendshape,
            )

        self.create_cluster()
