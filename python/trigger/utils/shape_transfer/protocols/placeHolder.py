"""Proximity Wrap Topology Transfer Protocol."""

from maya import cmds
from trigger.library import deformers
from trigger.utils.shape_transfer.protocol_core import ProtocolCore, Property


class ProximityTransfer(ProtocolCore):
    name = "testPlaceHolder"
    display_name = "Test Place Holder"
    type = "topology"
    def __init__(self):
        super(ProximityTransfer, self).__init__()

        self.wrap_node = None

        # define the property values for the protocol
        self["wrapModeTest"] = Property(attribute_name="wrapMode",
                                    attribute_type="combo",
                                    default_value=1,
                                    items=["offset", "surface", "snap", "rigid", "cluster"])
        self["maxDriversTest"] = Property(attribute_name="maxDrivers",
                                    attribute_type="integer",
                                    default_value=1,
                                    minimum=1,
                                    maximum=100)
        self["falloffScaleTest"] = Property(attribute_name="falloffScale",
                                    attribute_type="float",
                                    default_value=1.0,
                                    minimum=0.0,
                                    maximum=9999.0)
        self["smoothInfluencesTest"] = Property(attribute_name="smoothInfluences",
                                    attribute_type="integer",
                                    default_value=7,
                                    minimum=0,
                                    maximum=9999)
        self["smoothNormalsTest"] = Property(attribute_name="smoothNormals",
                                    attribute_type="integer",
                                    default_value=1,
                                    minimum=0,
                                    maximum=9999)
        self["softNormalizationTest"] = Property(attribute_name="softNormalization",
                                    attribute_type="boolean",
                                    default_value=False)
        self["spanSamplesTest"] = Property(attribute_name="spanSamples",
                                    attribute_type="integer",
                                    default_value=2,
                                    minimum=0,
                                    maximum=9999)


    def prepare(self):
        super(ProximityTransfer, self).prepare()

        self.blendshape_node = cmds.blendShape(
            self.blendshape_list,
            self.tmp_source,
            w=[0, 0],
            name="trTMP_{0}_blendshape".format(self.name),
        )

        self.wrap_node = deformers.create_proximity_wrap(
                    self.tmp_source,
                    self.tmp_target,
                    wrap_mode=self["wrapModeTest"].items[self["wrapModeTest"].value],
                    falloff_scale=self["falloffScaleTest"].value,
                    max_drivers=self["maxDriversTest"].value,
                    smooth_influences=self["smoothInfluencesTest"].value,
                    smooth_normals=self["smoothNormalsTest"].value,
                    soft_normalization=self["softNormalizationTest"].value,
                    span_samples=self["spanSamplesTest"].value,
                )

        # add the wrap node to the property keys.
        # this way when the values are changed, the wrap node will be updated.
        for property_object in self.values():
            property_object.node = self.wrap_node

