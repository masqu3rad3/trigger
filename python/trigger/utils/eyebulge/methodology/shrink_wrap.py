# pylint: disable=consider-using-f-string
"""Eye-Bulge method using the shrink wrap methodology."""

import logging

from maya import cmds

from trigger.library import deformers
from trigger.library import functions
from trigger.library import attribute

from trigger.utils.eyebulge.methodology.method_base import MethodBase

LOG = logging.getLogger(__name__)

1
class ShrinkWrapEyeBulge(MethodBase):
    """Eye Bulging with dnSculpt Deformers."""

    method_name = "shrinkWrap"

    def __init__(self):
        super(ShrinkWrapEyeBulge, self).__init__()
        self.properties = {
            "resolution": 30,
            "look_axis": "z",
            "local_influence": 4,
            "eye_scale": 1.0,
            "influence_multiplier": 1.5,  # mult for the maximum radius
            "displace_inflation": 0.02,
            "displace_falloff": 0.2,
            "displace_falloff_iterations": 1,
            "default_amount": 1.0,  # z scale of the pupil transform grp
            "default_radius": 1.0,  # y-z scales of the pupil transform grp
            "default_intensity": 1.0,  # the amount of blendhshape value
            "default_thickness_falloff": 7.0,  # outside falloff of the FFD
            "amount_limits": [0.0, 1.0],
            "intensity_limits": [0.0, 2.0],
            "radius_limits": [0.0, 1.0],
            "thickness_limits":[0, 99999.9]
        }

        # class variables
        self._proxy_eye = None
        self._proxy_plane_displace = None
        self._proxy_plane_bind = None
        self._proxy_plane_push = None
        self._proxy_eye_transform = None
        self._proxy_eye_pupil_transform = None
        self._proxy_box = None
        self._shrink_wrap = None
        self._lattice_deformer = None
        self._blendshape_deformer = None
        self._lattice_deformer = None

        # to be resolved later in case the inputs get changed after init
        self.deformers_grp = None
        self.bulge_deformers_group_suffix = "_deformers_grp"

    def create_proxies(self):
        """Create the proxy objects."""
        axis_d = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}
        _look_axis = self.properties["look_axis"].lower()

        self._proxy_eye = functions.duplicate_clean(
            self.inputs["eye_mesh"],
            name="{0}_proxy".format(self.inputs["eye_mesh"]),
        )
        cmds.xform(self._proxy_eye, centerPivots=True)

        # group for eye pivot
        self._proxy_eye_transform = cmds.group(
            empty=True,
            name="{0}_proxy_transform".format(self.inputs["eye_mesh"]),
        )
        cmds.matchTransform(
            self._proxy_eye_transform, self.inputs["eye_joint"]
        )

        # Create a transform group for the proxy and align it to the pupil.
        self._proxy_eye_pupil_transform = cmds.group(
            empty=True,
            name="{0}_proxy_pupil_transform".format(self.inputs["eye_mesh"]),
        )
        cmds.matchTransform(
            self._proxy_eye_pupil_transform, self.inputs["pupil_joint"]
        )

        cmds.parent(self._proxy_eye_pupil_transform, self._proxy_eye_transform)

        cmds.parent(self._proxy_eye, self._proxy_eye_pupil_transform)

        scale_value = cmds.getAttr(
            "{0}.scale".format(self.inputs["eye_mesh"])
        )[0]
        proxy_scale = [x * self.properties["eye_scale"] for x in scale_value]
        cmds.setAttr(
            "{}.scale".format(self._proxy_eye_transform), *proxy_scale
        )

        cmds.parentConstraint(
            self.inputs["eye_joint"],
            self._proxy_eye_transform,
            maintainOffset=True,
        )

        _max, _min, _ave = self.calculate_eye_radii(self.inputs["eye_mesh"])
        radius = self.properties["influence_multiplier"] * (_max * 2)

        mesh_res = self.properties["resolution"] - 1
        self._proxy_plane_displace = cmds.polyPlane(
            width=radius,
            height=radius,
            subdivisionsHeight=mesh_res,
            subdivisionsWidth=mesh_res,
            name="proxy_plane_displace_{}".format(self.inputs["name"]),
            axis=axis_d[_look_axis],
        )[0]

        self._proxy_box = cmds.polyCube(
            name="proxy_cube_{}".format(self.inputs["name"]),
            width=radius,
            height=radius,
            depth=radius,
            axis=axis_d[_look_axis],
        )[0]

        functions.align_to(self._proxy_plane_displace, self.inputs["pupil_joint"], position=True, rotation=True)
        functions.align_to(self._proxy_box, self.inputs["pupil_joint"], position=True, rotation=True)

        self._proxy_plane_bind = cmds.duplicate(
            self._proxy_plane_displace,
            name="proxy_plane_bind_{}".format(self.inputs["name"]),
        )[0]
        self._proxy_plane_push = cmds.duplicate(
            self._proxy_plane_displace,
            name="proxy_plane_push_{}".format(self.inputs["name"]),
        )[0]

        cmds.setAttr("{0}.s{1}".format(self._proxy_box, _look_axis), 0.05)

    def create_deformers(self):
        """Create the required deformers."""

        # FIXME MAKE THIS PROPERLY COMPATIBLE
        # This is a very VERY bad workaround for 2022 compatibility. Fix this
        cmds.optionVar(intValue=["deformationUseComponentTags", 0])
        cmds.optionVar(intValue=["deformationCreateTweak", 1])
        # FIXME Seriously... Fix the above.

        _resolution = self.properties["resolution"]
        res_d = {
            "x": (2, _resolution, _resolution),
            "y": (_resolution, 2, _resolution),
            "z": (_resolution, _resolution, 2),
        }

        # Shrink wrap
        # -----------
        self._shrink_wrap = cmds.deformer(
            self._proxy_plane_displace, type="shrinkWrap"
        )[0]
        cmds.connectAttr(
            "{}.worldMesh[0]".format(self._proxy_eye),
            "{}.targetGeom".format(self._shrink_wrap),
        )

        cmds.setAttr("{0}.projection".format(self._shrink_wrap), 3)
        cmds.setAttr("{0}.reverse".format(self._shrink_wrap), True)
        cmds.setAttr("{0}.offset".format(self._shrink_wrap), 0)
        cmds.setAttr(
            "{0}.targetInflation".format(self._shrink_wrap),
            self.properties["displace_inflation"],
        )
        cmds.setAttr(
            "{0}.falloff".format(self._shrink_wrap),
            self.properties["displace_falloff"],
        )
        cmds.setAttr(
            "{0}.falloffIterations".format(self._shrink_wrap),
            self.properties["displace_falloff_iterations"],
        )

        # Blendshape
        # ----------

        # Create a flattened version by extracting the bind pose delta
        temporary_delta = cmds.duplicate(
            self._proxy_plane_displace, name="temp_delta"
        )[0]

        self._blendshape_deformer = cmds.blendShape(
            [self._proxy_plane_displace, temporary_delta],
            self._proxy_plane_push,
            weight=[(0, 1), (1, -1)],
        )[0]

        # Shrink Wrap PUSH
        # ----------------
        shrink_wrap_push = cmds.deformer(
            self._proxy_plane_bind, type="shrinkWrap"
        )[0]
        cmds.connectAttr(
            "{}.worldMesh[0]".format(self._proxy_plane_push),
            "{}.targetGeom".format(shrink_wrap_push),
        )

        cmds.setAttr("{0}.reverse".format(shrink_wrap_push), True)
        cmds.setAttr(
            "{0}.projection".format(shrink_wrap_push), 3
        )  # Push it along vertex normals.

        # Lattice
        # -------
        _local_inf = (self.properties["local_influence"],) * 3
        lattice_name = "eyelid_def_{0}".format(
            self.inputs["eye_joint"].replace("_env", "")
        )
        self._lattice_deformer, lattice_points, _lattice_base = cmds.lattice(
            self._proxy_box,
            divisions=res_d[self.properties["look_axis"]],
            commonParent=True,
            ldivisions=_local_inf,
            outsideLattice=True,
            objectCentered=True,
            name=lattice_name,
        )

        # get the deformer set for lattice
        lattice_set = cmds.listConnections(
            self._lattice_deformer,
            source=False,
            destination=True,
            type="objectSet",
        )[0]

        # detach the lattice from proxy and bind to face
        cmds.sets(self.inputs["face_mesh"], forceElement=lattice_set)

        # lattice attributes
        cmds.setAttr("{0}.outsideLattice".format(self._lattice_deformer), 2)
        cmds.setAttr(
            "{0}.outsideFalloffDist".format(self._lattice_deformer), 7
        )

        cmds.delete(self._proxy_box)
        cmds.delete(temporary_delta)

        # parent them under the rig. Do that before wrap two prevent
        # calculating wrap bind twice
        lattice_grp = cmds.listRelatives(
            lattice_points, parent=True, shapes=False
        )[0]

        self.deformers_grp = "{}_{}".format(
            self.inputs["name"], self.bulge_deformers_group_suffix
        )
        if not cmds.objExists(self.deformers_grp):
            cmds.group(name=self.deformers_grp, empty=True)
            if self.inputs["module_group"]:
                cmds.parent(self.deformers_grp, self.inputs["module_group"])
                cmds.parent(
                    self._proxy_eye_transform, self.inputs["module_group"]
                )

        cmds.parent(
            [
                self._proxy_plane_displace,
                self._proxy_plane_bind,
                self._proxy_plane_displace,
                self._proxy_plane_push,
                lattice_grp,
            ],
            self.deformers_grp,
        )

        # Wrap
        # ----
        wrap_deformer, _base = deformers.create_wrap(
            self._proxy_plane_bind, [lattice_points], exclusive_bind=False
        )

        # append all deformers to the pref_nodes to pass to the core
        self.pref_nodes.extend(
            [
                self._shrink_wrap,
                self._lattice_deformer,
                wrap_deformer,
                self._blendshape_deformer,
                shrink_wrap_push,
            ]
        )

    def connect_attributes(self, controller):
        """Create/Connect the attributes to the controller."""

        _name = self.inputs["name"]

        nice_name = _name.upper().replace("_", " ")

        # Create the attributes on Controller
        cmds.addAttr(
        controller,
        longName=_name,
        attributeType="enum",
        niceName=nice_name,
        enumName="------",
        )
        cmds.setAttr("{0}.{1}".format(controller, _name), channelBox=True, lock=True)

        # attribute names
        amount_attr = "{}_Bulge_Amount".format(_name)
        radius_attr = "{}_Bulge_Radius".format(_name)
        intensity_attr = "{}_Bulge_Intensity".format(_name)
        falloff_attr = "{}_Falloff_Intensity".format(_name)

        cmds.addAttr(
            controller,
            niceName="Amount",
            longName=amount_attr,
            attributeType="float",
            defaultValue=self.properties["default_amount"],
            minValue=self.properties["amount_limits"][0],
            maxValue=self.properties["amount_limits"][1],
            keyable=True,
        )

        cmds.addAttr(
            controller,
            niceName="Radius",
            longName=radius_attr,
            attributeType="float",
            defaultValue=self.properties["default_radius"],
            minValue=self.properties["radius_limits"][0],
            maxValue=self.properties["radius_limits"][1],
            keyable=True,
        )

        cmds.addAttr(
            controller,
            niceName="Intensity",
            longName=intensity_attr,
            attributeType="float",
            defaultValue=self.properties["default_intensity"],
            minValue=self.properties["intensity_limits"][0],
            maxValue=self.properties["intensity_limits"][1],
            keyable=True,
        )

        cmds.addAttr(
            controller,
            niceName="Thickness Falloff",
            longName=falloff_attr,
            attributeType="float",
            defaultValue=self.properties["default_thickness_falloff"],
            minValue=self.properties["thickness_limits"][0],
            maxValue=self.properties["thickness_limits"][1],
            keyable=True,
        )

        cmds.connectAttr(
            "{0}.{1}".format(controller, amount_attr),
            "{0}.sz".format(self._proxy_eye_pupil_transform),
        )

        cmds.connectAttr(
            "{0}.{1}".format(controller, radius_attr),
            "{0}.sy".format(self._proxy_eye_pupil_transform),
        )

        cmds.connectAttr(
            "{0}.{1}".format(controller, radius_attr),
            "{0}.sx".format(self._proxy_eye_pupil_transform),
        )

        cmds.connectAttr(
            "{0}.{1}".format(controller, intensity_attr),
            "{0}.{1}".format(
                self._blendshape_deformer, self._proxy_plane_displace
            ),
        )

        cmds.connectAttr(
            "{0}.{1}".format(controller, falloff_attr),
            "{0}.outsideFalloffDist".format(self._lattice_deformer),
        )

    def clean_up(self):
        """Final cleanup / grouping etc."""
        cmds.hide(self._proxy_eye_transform)
        cmds.hide(self.deformers_grp)
        attribute.lock_and_hide(self.deformers_grp)

    def run(self):
        "Execute the eye bulge"

        self.create_proxies()
        self.create_deformers()
        if self.inputs.get("controller", None):
            self.connect_attributes(self.inputs["controller"])
        else:
            LOG.warning(
                "Controller not defined Eye Bulge attributes are not getting created and connected"
            )
        if not self.dev_mode:
            self.clean_up()
