from maya import cmds

from trigger.library import functions, attribute, transform, connection, shading
from trigger.objects.base_node import BaseNode
from trigger.core import filelog

log = filelog.Filelog(logname=__name__, filename="trigger_log")


class Filler(BaseNode):
    def __init__(self,
                 controller=None,
                 scaling=True,
                 normalize_scale=True,
                 coloring=True,
                 color_method="object",
                 color_match=False,
                 primary_channel="Auto",
                 visibility_controller=None,
                 id_tag="fillers"):
        """

        Args:
            controller: (string) Unique name or dag path for controller object
            scaling: (Bool) If True filler will be scaled with primary axis
            normalize_scale: (Bool) If True and if the ranges goes below 0, it will only do a positive scaling
                                    and will keep the 0 always 0 scale. Useful for two-way controllers.
                                    Default is True
            coloring: (Bool) If True filler change color with primary axis. Default True.
            color_method: (String) Defines either object color or shader will be used for coloring.
                                    Valid values are 'object', 'shader' and 'triswitch'. Default 'object'
            color_match: (Bool) If True, it matches BOTH color A and color B to the controllers color. In this case,
                                    Colors wont be animated
            primary_channel: (String) If set to 'Auto' the first available non-locked channel will be used.
            visibility_controller: (String) the attribute plug which will control the visibility of the filler
            id_tag: (String) When multiple fillers are created, this tag will be an identifier
                                    for shared node and group usage
        """
        super(Filler, self).__init__()
        self.hold_group = transform.validate_group("%s_grp" % id_tag)

        self.controller = None
        self.driver_hook = None
        if controller:
            self.set_controller(controller)

        self.colorA = (0, 0, 1)
        self.colorB = (0, 1, 0)
        self.scaling = scaling
        self.normalize_scale = normalize_scale
        self.coloring = coloring
        self.color_method = color_method
        self.color_match = color_match
        self.primary_channel = primary_channel
        self.visibility_controller = visibility_controller
        self.id_tag = str(id_tag)

    def set_controller(self, dag_path):
        """defines the controller and grabs its vaules in Origin class"""
        self.controller = Origin(dag_path, primary_channel=self.primary_channel)
        self.driver_hook = attribute.create_attribute(self.controller.dag_path,
                                                      attr_name="fillerPercentage_%s" % self.primary_channel,
                                                      attr_type="float")

        _range = self.controller.primary_ranges
        if not _range:
            raise Exception("Error with primary channel ranges. Primary Channel => {0}\n"
                            "Primary Ranges => {1}".format(self.controller.primary_channel,
                                                           _range))

        attribute.drive_attrs("{0}.{1}".format(self.controller.dag_path, self.controller.primary_channel),
                              self.driver_hook,
                              self.controller.primary_ranges,
                              self.controller.primary_ranges)
        # [0, 100])
        return

    def create(self):
        """Creates the shape filler"""
        # check if the controller is set
        if not self.controller:
            log.warning("Controller for filler is not set. Aborting")
            return

        # create the loft
        self.dag_path = cmds.ls(self.loft_curve(self.controller.dag_path,
                                                surface_parent=self.hold_group)[0], l=True)[0]
        bind_offset = functions.createUpGrp(self.name, "BIND")
        self.refresh_dag_path()
        connection.matrixConstraint(self.controller.dag_path, bind_offset)
        # drive the scale if enabled
        if self.scaling:
            self.drive_scale()

        if self.color_match:
            _color = transform.get_color(self.controller.dag_path)
            if _color:
                self.colorA = _color
                self.colorB = _color
            else:
                log.warning("Color Matching failed. Disabling Coloring")
                self.coloring = False

        if self.coloring:
            if self.color_method == "object":
                self.object_colorize([self.dag_path], color_a=self.colorA, color_b=self.colorB,
                                     driver_attr=self.driver_hook)
            elif self.color_method == "shader":
                self.shader_colorize([self.dag_path], color_a=self.colorA, color_b=self.colorB,
                                     driver_attr=self.driver_hook)
            else:
                log.error("Color Method %s is not a valid coloring method. Valid methods are 'object' and 'shader'"
                          % self.color_method)

        if self.visibility_controller:
            cmds.connectAttr(self.visibility_controller, "%s.v" % bind_offset)
        return self.dag_path

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
            name = curve.split("|")[-1]
            # name = curve.replace("_" + curve.split("_")[-1], "_" + str(i))

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

            if surface_parent:
                cmds.parent(surface, surface_parent)

            # Reference it so its not selectable.
            cmds.setAttr(surface + ".overrideEnabled", 1)
            cmds.setAttr(surface + ".overrideDisplayType", 2)

            cmds.delete(loft_curve)
        return surfaces

    def drive_scale(self):
        """Creates the scale connections for the filler object using the driver hook attribute on controller
        """
        _range = self.controller.primary_ranges
        if self.normalize_scale and (max(_range) - min(_range) > max(_range)):
            # Other than normalize status we check if the max range is lower than the difference of max and min
            name = "test"
            remap_node = cmds.createNode("remapValue", name="normalized_remap_%s" % name)

            # make a reverse V shaped mapping where mid point will correspond to the 0 value of controller
            zero_position = 1 / (((_range[0] * -1) + _range[1]) / (
                    _range[0] * -1))  # this gives the correct position of the 0 value between 0-1 scale
            # may it be abs? # 1/((abs(input_min)+input_max)/abs(input_min))
            cmds.setAttr("%s.value[0].value_Position" % remap_node, 0.0)
            cmds.setAttr("%s.value[0].value_Interp" % remap_node, 1.0)
            cmds.setAttr("%s.value[0].value_FloatValue" % remap_node, 1.0)

            cmds.setAttr("%s.value[1].value_Position" % remap_node, zero_position)
            cmds.setAttr("%s.value[1].value_Interp" % remap_node, 1.0)
            cmds.setAttr("%s.value[1].value_FloatValue" % remap_node, 0.0)

            cmds.setAttr("%s.value[2].value_Position" % remap_node, 1.0)
            cmds.setAttr("%s.value[2].value_Interp" % remap_node, 1.0)
            cmds.setAttr("%s.value[2].value_FloatValue" % remap_node, 1.0)

            cmds.setAttr("%s.inputMin" % remap_node, _range[0])
            cmds.setAttr("%s.inputMax" % remap_node, _range[1])
            cmds.setAttr("%s.outputMin" % remap_node, 0)
            cmds.setAttr("%s.outputMax" % remap_node, 1)

            cmds.connectAttr(self.driver_hook, "%s.inputValue" % remap_node)
            for attr in "xyz":
                cmds.connectAttr("%s.outValue" % remap_node, "{0}.s{1}".format(self.dag_path, attr))

        else:  # no normalization
            # TODO: This needs some optimization. Currently creates 3 remap nodes where 1 is enough
            for attr in "xyz":
                attribute.drive_attrs(self.driver_hook,
                                      "{0}.s{1}".format(self.dag_path, attr),
                                      _range,
                                      [0, 1])

    # #####################
    # SHADE / COLOR METHODS
    # #####################

    @staticmethod
    def object_colorize(loft_surfaces, color_a=(0, 0, 1), color_b=(0, 1, 0), driver_attr=None):
        """
        Colorizes the surfaces with drawing overrides (No Shader)

        Pros:   -Minimum extra nodes. Fast and efficient
                -Visible in shaded mode only. No texture mode necessary
                -No normal issues because of two sided lighting
        Cons:   -Cannot have transparency or reflectivity
        Args:
            loft_surfaces: (String) The surfaces which shaders will be applied
            color_a: (Tuple or List) normalized RGB color values for first color
            color_b: (Tuple or List) normalized RGB color values for second color
            driver_attr: (String) the attribute plug to drive the color from A to B

        Returns:

        """
        for loft in loft_surfaces:
            for shape in functions.getShapes(loft):
                blend_colors_node = cmds.createNode("blendColors", name="%s_bColor" % shape)
                cmds.setAttr("%s.color2" % blend_colors_node, *color_a)
                cmds.setAttr("%s.color1" % blend_colors_node, *color_b)
                if driver_attr:
                    attribute.drive_attrs(driver_attr, "%s.blender" % blend_colors_node, [0, 100], [0, 1])
                    # cmds.connectAttr(driver_attr, "%s.blender" % blend_colors_node)
                # enable overrides
                cmds.setAttr("%s.overrideEnabled" % shape, True)
                cmds.setAttr("%s.overrideRGBColors" % shape, 1)
                cmds.connectAttr("%s.output" % blend_colors_node, "%s.overrideColorRGB" % shape)
                # severe the shading group connection
                plug = cmds.listConnections("%s.instObjGroups[0]" % shape, source=True, plugs=True)
                cmds.disconnectAttr("%s.instObjGroups[0]" % shape, plug[0])
            # for some reason the transform node overriden too. bring it back to not overridden state
            cmds.setAttr("%s.overrideEnabled" % loft, 0)

    @staticmethod
    def shader_colorize(loft_surfaces, color_a=(0, 0, 1), color_b=(0, 1, 0), driver_attr=None,
                        transparency=0.7):
        """
        Colorizes the surfaces using separate shaders.
        Pros:   -Can have shader attributes like transparency and reflection
                -If both colors are same and no switching, colors are visible in simple shading mode
        Cons:   -Requires either 2 sided geometries or Two sided mode activated or one side will be black
                -One shader per filler. This can clutter the hypershade a lot and there may be performance issues
                -Textures needs to be activated to see the colors unless colarA == colorB. blendColors limitation
        Args:
            loft_surfaces: (String) The surfaces which shaders will be applied
            color_a: (Tuple or List) normalized RGB color values for first color
            color_b: (Tuple or List) normalized RGB color values for second color
            driver_attr: (String) the attribute plug to drive the color from A to B

        Returns:

        """
        for loft in loft_surfaces:
            name = loft.split("|")[-1]
            _shader = cmds.shadingNode("surfaceShader", asShader=True, name="%s_M" % name)
            shading.assign_shader(_shader, loft)
            cmds.setAttr("%s.outTransparency" % _shader, transparency, transparency, transparency)
            if color_a == color_b:
                cmds.setAttr("%s.outColor" % _shader, *color_a)
            else:
                blend_colors_node = cmds.createNode("blendColors", name="%s_bColor" % name)
                cmds.setAttr("%s.color2" % blend_colors_node, *color_a)
                cmds.setAttr("%s.color1" % blend_colors_node, *color_b)
                if driver_attr:
                    attribute.drive_attrs(driver_attr, "%s.blender" % blend_colors_node, [0, 100], [0, 1])
                cmds.connectAttr("%s.output" % blend_colors_node, "%s.outColor" % _shader)

        return

    @staticmethod
    def triswitch_colorize(loft_surfaces, color_a=(0, 0, 1), color_b=(0, 1, 0), driver_attr=None):
        """
        Colorizes surfaces using a common shader (uses id_tag to identify) and triswitches

        Pros:   -Can have shader attributes like transparency and reflection
                -Slightly more optimized than shader_colorize and does not clutter hypershade.
        Cons:   -Requires either 2 sided geometries or Two sided mode activated or one side will be black
                -Textures needs to be activated to see any color
        Args:
            loft_surfaces: (String) The surfaces which shaders will be applied
            color_a: (Tuple or List) normalized RGB color values for first color
            color_b: (Tuple or List) normalized RGB color values for second color
            driver_attr: (String) the attribute plug to drive the color from A to B

        Returns:

        """
        # TODO: Use a tripleShadingSwitch on a single shader to avoid unnecessary cluttering
        log.warning("color method => triswitch_colorize has not yet been implemented. Skipping.")
        pass


class Origin(BaseNode):
    """Database object for storing and restoring controller attributes """

    def __init__(self, dag_path, primary_channel="Auto"):
        super(Origin, self).__init__()
        self.dag_path = cmds.ls(dag_path, l=True)[0]

        self.non_user_attributes, self.user_attributes = self._get_attributes()
        if primary_channel == "Auto":
            # get the first available non-user channel as primary
            self.primary_channel = self.non_user_attributes[0] if self.non_user_attributes else None
        self.attribute_states = self._get_attribute_states()
        self.ranges = self._get_all_ranges()

    @property
    def primary_ranges(self):
        """Returns the primary channel ranges if exists"""
        if not self.primary_channel:
            return None
        return self.ranges.get(self.primary_channel, None)

    def get_ranges(self, attr):
        """Returns the minimum an maximum range for specified attribute in a list"""
        return self.ranges[attr]

    def _get_attributes(self):
        """Returns the active and keyable non-user and user attritutes for the controller object"""
        all_attrs = cmds.listAttr(self.dag_path, k=True, s=True, u=True)
        if not all_attrs:
            return [], []

        user_attrs = cmds.listAttr(self.dag_path, k=True, s=True, u=True, ud=True) or []
        non_user_attrs = [attr for attr in all_attrs if attr not in user_attrs and attr != "visibility"]
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

    def _get_all_ranges(self):
        """Get ranges for all active channels and returns a dictionary"""
        _ranges = {}
        # Non-user attribute limits
        for attr in self.non_user_attributes:
            _, limits = transform.query_limits(self.dag_path, attr)
            _ranges[attr] = limits

        for attr in self.user_attributes:
            _min_exists = cmds.attributeQuery(attr, node=self.dag_path, minExists=True)
            _min = cmds.attributeQuery(attr, node=self.dag_path, min=True) if _min_exists else 0
            _max_exists = cmds.attributeQuery(attr, node=self.dag_path, maxExists=True)
            _max = cmds.attributeQuery(attr, node=self.dag_path, max=True) if _max_exists else 1
            _ranges[attr] = [_min, _max]

        return _ranges

    def open_scales(self):
        """Makes sure the scale channels are not locked"""
        for axis in "xyz":
            cmds.setAttr("%s.s%s" % (self.dag_path, axis), lock=False, channelBox=False, keyable=True)

    def revert(self):
        """Revert channel states back to original"""
        for attr, data in self.attribute_states.items():
            cmds.setAttr("%s.%s" % (self.dag_path, attr), keyable=data["keyable"],
                         channelBox=data["channelBox"], lock=data["lock"])


