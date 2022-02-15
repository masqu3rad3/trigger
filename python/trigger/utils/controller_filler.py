from maya import cmds

from trigger.library import functions, attribute


class Filler(object):
    def __init__(self):
        super(Filler, self).__init__()
        self.controller = None
        self.colorA = (0, 0, 1)
        self.colorB = (0, 1, 0)

    def set_controller(self, dag_path, primary_channel="Auto"):
        self.controller = Origin(dag_path, primary_channel=primary_channel)

    def create(self):
        """Single axis, planar shape filler"""
        # create loft Curves
        driver = attribute.create_attribute(self.controller.dag_path, attr_name="fillerDrive", attr_type="float", min_value=0, max_value=1)
        surfaces = self.loft_curve(self.controller.dag_path)
        self.colorize_surfaces(surfaces, colorA=self.colorA, colorB=self.colorB, driver_attr=driver)
        pass

    @staticmethod
    def loft_curve(curve, surface_parent=None):
        """Creates a surface from lofting curves.
        Great for ctrl visualising. Also works with multiple shapes.
        Args:
            curve (str): Name of curve to loft.
            surface_parent (str): Parent lofted surface to this.
        Returns:
        list: [surface, surface_back, shaders]
        """
        surfaces = []
        for i, curve_shape in enumerate(cmds.listRelatives(curve, s=True)):
            name = curve.replace("_" + curve.split("_")[-1], "_" + str(i))

            # Duplicate curve, unlock the scale, scale it to almost zero, then loft.
            loft_curve = cmds.duplicate(curve)[0]
            for axis in "xyz":
                cmds.setAttr("{0}.s{1}".format(loft_curve, axis), e=True, l=False)

            # If more than one shape under the curve, delete the other shapes to get correct pivot.
            loft_curve_shapes = cmds.listRelatives(loft_curve, s=True)
            for j, loft_curve_shape in enumerate(loft_curve_shapes):
                if j != i:
                    cmds.delete(loft_curve_shape)

            # Recenter pivot and then scale down to almost zero.
            cmds.xform(loft_curve, cp=True)
            curve_pivot = cmds.xform(loft_curve, q=True, rp=True, ws=True)
            cmds.setAttr(loft_curve + ".scale", *[0.001, 0.001, 0.001])

            # Loft between curves.
            surface = cmds.loft(
                curve_shape,
                loft_curve_shapes[i],
                n=name + "Front_surface",
                ch=False,
            )[0]
            surfaces.append(surface)

            # Create surface grp, and centre pivot of surface.
            cmds.xform(surface, rp=curve_pivot, sp=curve_pivot)
            surface_grp = cmds.group(n=name + "Surface_grp", em=True)
            cmds.delete(cmds.parentConstraint(curve, surface_grp))
            cmds.parent(surface, surface_grp)
            if surface_parent:
                cmds.parent(surface_grp, surface_parent)

            # Reference it so its not selectable.
            cmds.setAttr(surface + ".overrideEnabled", 1)
            cmds.setAttr(surface + ".overrideDisplayType", 2)

        return surfaces

    @staticmethod
    def colorize_surfaces(loft_surfaces, colorA=(0,0,1), colorB=(0,1,0), driver_attr=None):
        """Colorizes the surfaces with drawing overrides (No Shader)"""
        for loft in loft_surfaces:
            for shape in functions.getShapes(loft):
                blend_colors_node = cmds.createNode("blendColors", name="%s_bColor" % shape)
                cmds.setAttr("%s.color2" % blend_colors_node, *colorA)
                cmds.setAttr("%s.color1" % blend_colors_node, *colorB)
                if driver_attr:
                    cmds.connectAttr(driver_attr, "%s.blender" % blend_colors_node)
                # enable overrides
                cmds.setAttr("%s.overrideEnabled" % shape, True)
                cmds.setAttr("%s.overrideRGBColors" % shape, 1)
                cmds.connectAttr("%s.output" % blend_colors_node, "%s.overrideColorRGB" % shape)
                # severe the shading group connection
                plug = cmds.listConnections("%s.instObjGroups[0]" % shape, source=True, plugs=True)
                cmds.disconnectAttr("%s.instObjGroups[0]" % shape, plug[0])
            # for some reason the transform node overriden too. bring it back to not overridden state
            cmds.setAttr("%s.overrideEnabled" % loft, 0)


class Origin(object):
    """Database object for storing and restoring controller attributes """

    def __init__(self, dag_path, primary_channel="Auto"):
        self.dag_path = dag_path
        self.name = dag_path.split("|")[-1]


        self.non_user_attributes, self.user_attributes = self._get_attributes()
        if primary_channel == "Auto":
            # get the first available non-user channel as primary
            self.primary_channel = self.non_user_attributes[0] if self.non_user_attributes else None
        self.primary_channel = primary_channel
        self.attribute_states = self._get_attribute_states()

    def _get_attributes(self):
        """Returns the active and keyable non-user and user attritutes for the controller object"""
        all_attrs = cmds.listAttr(self.dag_path, k=True, s=True, u=True)
        if not all_attrs:
            return [], []

        user_attrs = cmds.listAttr(self.dag_path, k=True, s=True, u=True, ud=True) or []
        non_user_attrs = [attr for attr in all_attrs if attr not in user_attrs]
        return non_user_attrs, user_attrs

    def _get_attribute_states(self):
        """Collects and returns the current non-user attribute states as dictionary"""
        _states = {}
        for ch in "trs":  # translate, rotate, scale
            for axis in "xyz":
                attr = "%s%s" % (ch, axis)
                _states[attr] = {
                    "keyable": cmds.getAttr("%s.%s" % (self.dag_path, attr), keyable=True),
                    "channelBox": cmds.getAttr("%s.%s" % (self.dag_path, attr), channelBox=True),
                    "lock": cmds.getAttr("%s.%s" % (self.dag_path, attr), lock=True),
                }
        return _states

    def open_scales(self):
        """Makes sure the scale channels are not locked"""
        for axis in "xyz":
            cmds.setAttr("%s.s%s" % (self.dag_path, axis), lock=False, channelBox = False, keyable=True)

    def revert(self):
        """Revert channel states back to original"""
        for attr, data in self.attribute_states.items():
            cmds.setAttr("%s.%s" % (self.dag_path, attr), keyable=data["keyable"],
                         channelBox=data["channelBox"], lock=data["lock"])




