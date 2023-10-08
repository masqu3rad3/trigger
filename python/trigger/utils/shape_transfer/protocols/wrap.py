"""Proximity Wrap Topology Transfer Protocol."""

from maya import cmds
from trigger.library import deformers
from trigger.utils.shape_transfer.protocol_core import ProtocolCore, Property


class WrapTransfer(ProtocolCore):
    name = "wrap"
    display_name = "Wrap"
    type = "topology"

    wrap_properties = [
        "weightThreshold",
        "maxDistance",
        "exclusiveBind",
        "autoWeightThreshold",
    ]

    def __init__(self):
        super(WrapTransfer, self).__init__()

        self.wrap_node = None

        # define the property values for the protocol
        self["weightThreshold"] = Property(
            attribute_name="weightThreshold",
            attribute_type="float",
            default_value=0.0,
            minimum=0.0,
            maximum=1.0,
        )

        self["maxDistance"] = Property(
            attribute_name="maxDistance",
            attribute_type="float",
            default_value=0.0,
            minimum=0.0,
            maximum=9999.0,
        )

        self["exclusiveBind"] = Property(
            attribute_name="exclusiveBind",
            attribute_type="boolean",
            default_value=True,
        )

        self["autoWeightThreshold"] = Property(
            attribute_name="autoWeightThreshold",
            attribute_type="boolean",
            default_value=True,
        )

    def prepare(self):
        super(WrapTransfer, self).prepare()
        self.blendshape_node = "trTMP_{0}_blendshape".format(self.name)
        if not cmds.objExists(self.blendshape_node):
            cmds.blendShape(
                self.blendshape_list,
                self.tmp_source,
                w=[0, 0],
                name=self.blendshape_node,
            )

        self.wrap_node = "trTMP_{0}_wrap".format(self.name)
        if not cmds.objExists(self.wrap_node):
            deformers.create_wrap(
                self.tmp_source,
                self.tmp_target,
                name=self.wrap_node,
                weight_threshold=0.0,
                max_distance=0.0,
                exclusive_bind=True,
                auto_weight_threshold=True,
                falloff_mode=0,
            )

        # add the wrap node to the property keys.
        # this way when the values are changed, the wrap node will be updated.
        for property_object in self.wrap_properties:
            self[property_object].node = self.wrap_node

        self.create_cluster()
