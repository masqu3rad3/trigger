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
        super(DeltaTransfer, self).prepare()

        blendshape_node_name = "trTMP_{0}_blendshape".format(self.name)
        if cmds.objExists(blendshape_node_name):
            self.blendshape_node = blendshape_node_name
        else:
            self.blendshape_node = cmds.blendShape(
                        self.blendshape_list,
                        self.tmp_target,
                        w=[0, 0],
                        name="trTMP_{0}_blendshape".format(self.name),
                    )[0]

            next_index = cmds.blendShape(self.blendshape_node, query=True, weightCount=True)
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


        source_blendshape_node_name = "trTMP_{0}_source_blendshape".format(self.name)
        if cmds.objExists(source_blendshape_node_name):
            self.source_blendshape_node = source_blendshape_node_name
        else:
            self.source_blendshape_node = cmds.blendShape(
                self.blendshape_list,
                self.tmp_source,
                w=[0, 0],
                name="trTMP_{0}_source_blendshape".format(self.name),
            )

        self.create_cluster()


