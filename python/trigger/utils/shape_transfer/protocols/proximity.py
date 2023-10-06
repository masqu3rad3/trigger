"""Proximity Wrap Topology Transfer Protocol."""

from maya import cmds
from trigger.library import deformers
from trigger.utils.shape_transfer.protocol_core import ProtocolCore, Property


class ProximityTransfer(ProtocolCore):
    name = "proximity"
    display_name = "Proximity"
    type = "topology"

    wrap_properties = [
        "wrapMode",
        "maxDrivers",
        "falloffScale",
        "smoothInfluences",
        "smoothNormals",
        "softNormalization",
        "spanSamples"
    ]

    def __init__(self):
        super(ProximityTransfer, self).__init__()

        self.wrap_node = None

        # define the property values for the protocol
        self["wrapMode"] = Property(
            attribute_name="wrapMode",
            attribute_type="combo",
            default_value=1,
            items=["offset", "surface", "snap", "rigid", "cluster"],
        )
        self["maxDrivers"] = Property(
            attribute_name="maxDrivers",
            attribute_type="integer",
            default_value=1,
            minimum=1,
            maximum=100,
        )
        self["falloffScale"] = Property(
            attribute_name="falloffScale",
            attribute_type="float",
            default_value=1.0,
            minimum=0.0,
            maximum=9999.0,
        )
        self["smoothInfluences"] = Property(
            attribute_name="smoothInfluences",
            attribute_type="integer",
            default_value=7,
            minimum=0,
            maximum=9999,
        )
        self["smoothNormals"] = Property(
            attribute_name="smoothNormals",
            attribute_type="integer",
            default_value=1,
            minimum=0,
            maximum=9999,
        )
        self["softNormalization"] = Property(
            attribute_name="softNormalization",
            attribute_type="boolean",
            default_value=False,
        )
        self["spanSamples"] = Property(
            attribute_name="spanSamples",
            attribute_type="integer",
            default_value=2,
            minimum=0,
            maximum=9999,
        )

    def prepare(self):
        super(ProximityTransfer, self).prepare()
        self.blendshape_node = "trTMP_{0}_blendshape".format(self.name)
        if not cmds.objExists(self.blendshape_node):
            cmds.blendShape(
                self.blendshape_list,
                self.tmp_source,
                w=[0, 0],
                name="trTMP_{0}_blendshape".format(self.name),
            )

        self.wrap_node = "proximity_wrap_trTMP_{0}_wrap".format(self.name)
        if not cmds.objExists(self.wrap_node):
            deformers.create_proximity_wrap(
                self.tmp_source,
                self.tmp_target,
                name="trTMP_{0}_wrap".format(self.name),
                wrap_mode=self["wrapMode"].items[self["wrapMode"].value],
                falloff_scale=self["falloffScale"].value,
                max_drivers=self["maxDrivers"].value,
                smooth_influences=self["smoothInfluences"].value,
                smooth_normals=self["smoothNormals"].value,
                soft_normalization=self["softNormalization"].value,
                span_samples=self["spanSamples"].value,
            )

        # add the wrap node to the property keys.
        # this way when the values are changed, the wrap node will be updated.
        # for property_object in self.values():
        #     property_object.node = self.wrap_node

        for property_object in self.wrap_properties:
            self[property_object].node = self.wrap_node

        self.create_cluster()
