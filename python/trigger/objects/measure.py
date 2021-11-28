from maya import cmds
from trigger.library import connection, attribute


class Angle(object):
    """Creates set of locators to create angle extractors"""
    def __init__(self, suffix=""):
        self._angle_root = cmds.spaceLocator(name="angleExt_Root_IK_%s" % suffix)[0]
        self._angle_fixed = cmds.spaceLocator(name="angleExt_Fixed_IK_%s" % suffix)[0]
        self._angle_float = cmds.spaceLocator(name="angleExt_Float_IK_%s" % suffix)[0]
        cmds.parent(self._angle_fixed, self._angle_float, self._angle_root)

        # create calculation nodes
        self._angle_node = cmds.createNode("angleBetween", name="angleBetweenIK_%s" % suffix)
        self._remap_node = cmds.createNode("remapValue", name="angleRemapIK_%s" % suffix)
        self._mult_node = cmds.createNode("multDoubleLinear", name="angleMultIK_%s" % suffix)

        cmds.connectAttr("{0}.translate".format(self._angle_fixed), "{0}.vector1".format(self._angle_node))
        cmds.connectAttr("{0}.translate".format(self._angle_float), "{0}.vector2".format(self._angle_node))

        cmds.connectAttr("{0}.angle".format(self._angle_node), "{0}.inputValue".format(self._remap_node))
        self.calibrate()

        cmds.connectAttr("{0}.outValue".format(self._remap_node), "{0}.input1".format(self._mult_node))

        self.angle_attr, self.value_attr, self.value_mult_attr = self.__attributes()

    @property
    def root(self):
        return self._angle_root

    @property
    def fixed(self):
        return self._angle_fixed

    @property
    def float(self):
        return self._angle_float

    @property
    def degree_plug(self):
        return "%s.angle" % self._angle_node

    @property
    def value_plug(self):
        return "%s.output" % self._mult_node

    def set_value_multiplier(self, val):
        cmds.setAttr(self.value_mult_attr, val)

    def pin_root(self, node, mo=False):
        """Constraints the angle root to the node"""
        connection.matrixConstraint(node, self._angle_root, mo=mo)

    def pin_fixed(self, node, mo=False):
        """Constraints 'fixed' end to the node"""
        cmds.pointConstraint(node, self._angle_fixed, mo=mo)

    def calibrate(self):
        """Calibrates the value mapper accepting the current angle 100 percent"""
        cmds.setAttr("{0}.inputMin".format(self._remap_node), cmds.getAttr("{0}.angle".format(self._angle_node)))
        cmds.setAttr("{0}.inputMax".format(self._remap_node), 0)
        cmds.setAttr("{0}.outputMin".format(self._remap_node), 0)
        cmds.setAttr("{0}.outputMax".format(self._remap_node), cmds.getAttr("{0}.angle".format(self._angle_node)))

    def __attributes(self):
        angle_attr = attribute.create_attribute(self._angle_root, keyable=False, attr_name="Angle", attr_type="float")
        value_attr = attribute.create_attribute(self._angle_root, keyable=False, attr_name="Value", attr_type="float")
        value_mult_attr = attribute.create_attribute(self._angle_root, keyable=True, attr_name="valueMultiplier",
                                                     attr_type="float", default_value=1.0)

        cmds.connectAttr("%s.angle" % self._angle_node, angle_attr)
        cmds.connectAttr("%s.output" % self._mult_node, value_attr)
        cmds.connectAttr(value_mult_attr, "%s.input2" % self._mult_node)
        return angle_attr, value_attr, value_mult_attr
