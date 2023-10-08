"""Delta Transfer Protocol."""

from maya import cmds
from trigger.utils.shape_transfer.protocol_core import ProtocolCore


class DeltaTransfer(ProtocolCore):
    name = "deltaTransfer"
    display_name = "Delta Transfer"
    type = "shape"

    def __init__(self):
        super(DeltaTransfer, self).__init__()

    def prepare(self):
        """Prepare the protocol for execution."""
        super(DeltaTransfer, self).prepare()

        self.blendshape_node = "trTMP_{0}_blendshape".format(self.name)
        if not cmds.objExists(self.blendshape_node):
            cmds.blendShape(
                self.blendshape_list,
                self.tmp_target,
                w=[0, 0],
                name=self.blendshape_node,
                topologyCheck=False
            )

            next_index = cmds.blendShape(
                self.blendshape_node, query=True, weightCount=True
            )
            cmds.blendShape(
                self.blendshape_node,
                edit=True,
                t=(self.tmp_target, next_index, self.source_mesh, 1.0),
                w=[next_index, -1.0],
            )
            # rename is something obvious to treat differently in QC
            cmds.aliasAttr(
                "negateSource",
                "%s.w[%i]" % (self.blendshape_node, next_index),
            )

        self.source_blendshape_node = "trTMP_{0}_source_blendshape".format(self.name)
        if not cmds.objExists(self.source_blendshape_node):
            cmds.blendShape(
                self.blendshape_list,
                self.tmp_source,
                w=[0, 0],
                name=self.source_blendshape_node,
            )

        self.create_cluster()
