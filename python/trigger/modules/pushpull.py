"""Object class for simplify the module code."""
# pylint: disable=consider-using-f-string

from maya import cmds
import maya.api.OpenMaya as om

from trigger.library import functions, naming, joint
from trigger.core.module import ModuleCore, GuidesCore
from trigger.core.compatibility import MULT_NODE_NAME, ADD_NODE_NAME
import logging

LOG = logging.getLogger(__name__)

LIMB_DATA = {
    "members": ["PushPullBase", "PushPullEnd"],
    "properties": [
        {
            "attr_name": "rotationParent",
            "nice_name": "Rotation Parent",
            "attr_type": "string",
            "default_value": "",
        },
        {
            "attr_name": "extractAxis",
            "nice_name": "Extract Axis",
            "attr_type": "enum",
            "enum_list": "X:Y:Z",
            "default_value": 0,
        },
        {
            "attr_name": "extractMultiplier",
            "nice_name": "Extract Multiplier",
            "attr_type": "float",
            "default_value": 0.5,
        },
        {
            "attr_name": "reverseFlip",
            "nice_name": "Reverse Flip",
            "attr_type": "bool",
            "default_value": False,
        },
        {
            "attr_name": "translateAxis",
            "nice_name": "Translate Axis",
            "attr_type": "enum",
            "enum_list": "X:Y:Z",
            "default_value": 0,
        },
        {
            "attr_name": "bidirectional",
            "nice_name": "Bidirectional",
            "attr_type": "bool",
            "default_value": False,
        },
        {
            "attr_name": "driverRangeStart",
            "nice_name": "Driver Range Start",
            "attr_type": "float",
            "default_value": -90.0,
        },
        {
            "attr_name": "driverRangeEnd",
            "nice_name": "Driver Range End",
            "attr_type": "float",
            "default_value": 90.0,
        },
        {
            "attr_name": "drivenRangeStart",
            "nice_name": "Driven Range Start",
            "attr_type": "float",
            "default_value": 0.0,
        },
        {
            "attr_name": "drivenRangeEnd",
            "nice_name": "Driven Range End",
            "attr_type": "float",
            "default_value": 2.0,
        },
        {
            "attr_name": "interpolation",
            "nice_name": "Interpolation",
            "attr_type": "enum",
            "enum_list": "none:linear:smooth:spline",
            "default_value": 1,
        },
    ],
    "multi_guide": None,
    "sided": True,
}

class PushPull(ModuleCore):
    """PushPull Module class."""
    name = "PushPull"

    def __init__(self, build_data=None, inits=None, *args, **kwargs):
        super(PushPull, self).__init__()

        if build_data:
            if len(build_data.keys()) != 2:
                LOG.error("PushPull module must have exactly 2 joints.")
                return
            self.inits = [build_data["PushPullBase"], build_data["PushPullEnd"]]
        elif inits:
            if len(inits) != 2:
                LOG.error("PushPull module must have exactly 2 joints.")
                return
            self.inits = inits
        else:
            LOG.error("PushPull module must have either build_data or inits defined.")
            return

        self.module_name = naming.unique_name(
            cmds.getAttr(f"{self.inits[0]}.moduleName")
        )
        self.offsetVector = om.MVector(0, 1, 0)

        side_mult = -1 if joint.get_joint_side(self.inits[0]) == "R" else 1
        self.compound = PushPullCompound()
        self.compound.extract_axis = cmds.getAttr(f"{self.inits[0]}.extractAxis", asString=True)
        self.compound.extract_multiplier = cmds.getAttr(f"{self.inits[0]}.extractMultiplier") * side_mult
        self.compound.reverse_flip = cmds.getAttr(f"{self.inits[0]}.reverseFlip")
        self.compound.translate_axis = cmds.getAttr(f"{self.inits[0]}.translateAxis", asString=True)
        self.compound.bidirectional = cmds.getAttr(f"{self.inits[0]}.bidirectional")
        self.compound.driver_range = [
            cmds.getAttr(f"{self.inits[0]}.driverRangeStart"),
            cmds.getAttr(f"{self.inits[0]}.driverRangeEnd"),
        ]
        self.compound.driven_range = [
            cmds.getAttr(f"{self.inits[0]}.drivenRangeStart"),
            cmds.getAttr(f"{self.inits[0]}.drivenRangeEnd"),
        ]
        self.compound.interpolation = cmds.getAttr(f"{self.inits[0]}.interpolation", asString=True)
        self.rotation_parent = cmds.getAttr(f"{self.inits[0]}.rotationParent")
        self.joints = Joints()


    def create_joints(self):
        """Create the joints."""
        self.joints.start = cmds.joint(name=naming.parse([self.module_name, "base"], suffix="j"))
        self.joints.end = cmds.joint(name=naming.parse([self.module_name, "end"], suffix="jDef"))
        cmds.connectAttr(f"{self.scaleGrp}.jointVis", f"{self.joints.start}.v", force=True)
        cmds.connectAttr(f"{self.scaleGrp}.jointVis", f"{self.joints.end}.v", force=True)

        functions.align_to(self.joints.start, self.inits[0], position=True, rotation=True)
        functions.align_to(self.joints.end, self.inits[1], position=True, rotation=True)
        cmds.makeIdentity( self.joints.start, apply=True)
        cmds.makeIdentity(self.joints.end, apply=True)

        self.limbPlug = self.joints.start
        self.sockets.append(self.joints.end)
        self.deformerJoints.append(self.joints.end)

    def post_connect(self):
        """Override the post connect to add custom connections."""
        # first try to get the parent
        parents = cmds.listRelatives(self.joints.start, parent=True)
        if not parents and self.rotation_parent:
            LOG.warning("Rotation parent not found. Skipping connection.")
            return

        self.compound.create_rig(self.module_name, self.name, self.rotation_parent or parents[0], self.joints)

    def execute(self):
        self.create_joints()
        # by default, nothing special happens. Real stuff happens in post_connect


class Guides(GuidesCore):
    """Data class for necessary guides in the module."""
    name = "PushPull"
    limb_data = LIMB_DATA

    def draw_joints(self):
        """Draw the guide joints."""
        if self.side == "C":
            base_vector = om.MVector(0, 0, 0)
            end_vector = om.MVector(0, 5, 0) * self.tMatrix
        else:
            base_vector = om.MVector(2 * self.sideMultiplier, 0, 0) * self.tMatrix
            end_vector = om.MVector(2 * self.sideMultiplier, 5, 0) * self.tMatrix

        cmds.select(clear=True)
        base_jnt = cmds.joint(
            position=base_vector,
            name=naming.parse([self.name, "base"], side=self.side, suffix="jInit")
        )

        end_jnt = cmds.joint(
            position=end_vector,
            name=naming.parse([self.name, "end"], side=self.side, suffix="jInit")
        )

        self.offsetVector = om.MVector(0, 1, 0)
        self.guideJoints = [base_jnt, end_jnt]

    def define_guides(self):
        """Define the guides."""
        joint.set_joint_type(self.guideJoints[0], "PushPullBase")
        joint.set_joint_type(self.guideJoints[1], "PushPullEnd")


class Nodes:
    """Data class for necessary nodes in compound."""

    def __init__(self):
        self.compose = None
        self.decompose = None
        self.direction = None # multiplier to negate if rotation axis is negative
        self.quat_to_euler = None
        self.remap = None
        self.multiply = None
        self.multiply_compensate = None


class Joints:
    """Data class for produced joints in the compound."""

    def __init__(self):
        self.start = None
        self.end = None


class PushPullInstance(object):
    """PushPull Instance object."""

    def __init__(self):
        super(PushPullInstance, self).__init__()
        self._module_name = ""
        self._name = ""
        self._parent = None
        self._rotation_parent = None
        self._guide_start = None
        self._guide_end = None
        self._index = None

        self.joints = Joints()

        self.compounds = []

    @property
    def module_name(self):
        """Return the name of the module."""
        return self._module_name

    @module_name.setter
    def module_name(self, value):
        """Set the module name."""
        self._module_name = value

    @property
    def index(self):
        """Return the index of the instance."""
        return self._index

    @index.setter
    def index(self, value):
        """Set the index of the instance."""
        self._index = int(value)

    @property
    def name(self):
        """Return the name of the instance."""
        return self._name

    @name.setter
    def name(self, value):
        """Set the name of the compound."""
        self._name = value

    @property
    def parent(self):
        """Return the parent."""
        return self._parent

    @parent.setter
    def parent(self, value):
        """Set the parent."""
        self._parent = value

    @property
    def rotation_parent(self):
        """Return the rotation parent."""
        return self._rotation_parent or self._parent

    @rotation_parent.setter
    def rotation_parent(self, value):
        """Set the rotation parent."""
        self._rotation_parent = value

    @property
    def guide_start(self):
        """Return first guide joint."""
        return self._guide_start

    @guide_start.setter
    def guide_start(self, value):
        """Set the guide start."""
        self._guide_start = value

    @property
    def guide_end(self):
        """Return last guide joint."""
        return self._guide_end

    @guide_end.setter
    def guide_end(self, value):
        """Set the guide end."""
        self._guide_end = value

    def add_compound(
        self,
        extract_axis,
        extract_multiplier,
        translate_axis,
        driver_range,
        driven_range,
        reverse_flip = False,
        bidirectional = False
    ):
        """Add a push-pull compound to the instance."""
        compound = PushPullCompound()
        compound.extract_axis = extract_axis
        compound.extract_multiplier = extract_multiplier
        compound.translate_axis = translate_axis
        compound.driver_range = driver_range
        compound.driven_range = driven_range
        compound.reverse_flip = reverse_flip
        compound.bidirectional = bidirectional
        self.compounds.append(compound)

    def create_joints(self):
        """Create the joints."""

        if not all([self.guide_start, self.guide_end]):
            raise ValueError(
                "Both guide_start and guide_end needs to be defined create the deformation joints."
            )

        start_joint_name = f"{self.module_name}_{self.name}_base_jDef"
        end_joint_name = f"{self.module_name}_{self.name}_end_jDef"

        self.joints.start = self.__create_joint(
            start_joint_name, self.guide_start
        )
        self.joints.end = self.__create_joint(end_joint_name, self.guide_end)
        if not self.joints.end.parent:
            self.joints.end.set_parent(self.joints.start)

    def connect(self):
        """Connect the joint to the designated parent."""
        if self.parent:
            self.joints.start.set_parent(self.parent)

    def build_compounds(self):
        """Build the compounds in the list."""
        for compound in self.compounds:
            compound.create_rig(
                self.module_name, self.name, self.rotation_parent, self.joints
            )

    def __create_joint(self, name, guide):
        """Create the joint if it doesn't exist and snap to the guide.

        Args:
            name (str): name of the joint
            guide (node.Node): rigUtils Node object as guide.
        """
        if cmds.objExists(name):
            return name
        node = cmds.creatNode("joint", name=name)
        functions.align_to(node, guide)
        cmds.makeIdentity(node, apply=True)
        return node


class PushPullCompound(object):
    """PushPull Compound object.

    This module holds/pass the information between states and responsible
    for creating the joints and connections.

    Please note that this is not an instance but it creates the compound.
    There can be multiple PushPull Compounds with the same name name but
    different extract/translate axes.
    """

    valid_axes = "XYZ"
    interpolation_dict = {"none": 0, "linear": 1, "smooth": 2, "spline": 3}

    def __init__(self):
        """initialize"""
        # pylint: disable=super-with-arguments
        super(PushPullCompound, self).__init__()
        self._extract_axis = "X"
        self._extract_multiplier = 0.5
        self._reverse_flip = False
        self._translate_axis = "X"
        self._bidirectional = False
        self._driver_range = None
        self._driven_range = None
        self._interpolation = "linear"

        # class vars
        self.nodes = Nodes()

    @property
    def extract_axis(self):
        """Return the extract axis."""
        return self._extract_axis

    @extract_axis.setter
    def extract_axis(self, value):
        """Set the extract axis."""
        if not isinstance(value, str) or value.upper() not in self.valid_axes:
            raise ValueError(
                f"extract_axis must be a valid str value. \
                    Valid values are {self.valid_axes}. Got {value}"
                )
        self._extract_axis = value.upper()

    @property
    def translate_axis(self):
        """Return the translate axis."""
        return self._translate_axis

    @translate_axis.setter
    def translate_axis(self, value):
        """Set the translate axis."""
        if not isinstance(value, str) or value.upper() not in self.valid_axes:
            raise ValueError(
                "translate_axis must be a valid ingeger value. \
                    Valid values are {0}. Got {1}".format(
                    self.valid_axes, value
                )
            )
        self._translate_axis = value.upper()

    @property
    def bidirectional(self):
        """Return the bidirectional state."""
        return self._bidirectional

    @bidirectional.setter
    def bidirectional(self, value):
        """Set the bidirectional state."""
        self._bidirectional = bool(value)

    @property
    def reverse_flip(self):
        """Return the reverse flip value.

        Reverse flip defines where the 180 degree quaternion flip happens.
        If checked, it will happen on the opposite side of the circle.
        """
        return self._reverse_flip

    @reverse_flip.setter
    def reverse_flip(self, value):
        """Set the reverse flip value.

        Reverse flip defines where the 180 degree quaternion flip happens.
        If checked, it will happen on the opposite side of the circle.
        """
        self._reverse_flip = bool(value)

    @property
    def extract_multiplier(self):
        """Return the extract multiplier."""
        return self._extract_multiplier

    @extract_multiplier.setter
    def extract_multiplier(self, value):
        """Set the extract multiplier."""
        self._extract_multiplier = float(value)

    @property
    def driver_range(self):
        """Return the driver range."""
        return self._driver_range

    @driver_range.setter
    def driver_range(self, value):
        """Set the driver range."""
        self._driver_range = self._validate_range(value)

    @property
    def driven_range(self):
        """Return the driven range."""
        return self._driven_range

    @driven_range.setter
    def driven_range(self, value):
        """Set the driven range."""
        self._driven_range = self._validate_range(value)

    @property
    def interpolation(self):
        """Return the interpolation type."""
        return self._interpolation

    @interpolation.setter
    def interpolation(self, value):
        """Set the interpolation type."""
        if not isinstance(value, str) or value.lower() not in self.interpolation_dict.keys():
            raise ValueError(
                "interpolation must be a valid str value. \
                    Valid values are {0}. Got {1}".format(
                    ", ".join(self.interpolation_dict.keys()), value
                )
            )
        self._interpolation = value.lower()

    def _create_nodes(self, module_name, instance_name):
        """Populate the nodes."""

        # common nodes per instance
        self.nodes.compose = self.__create_node(
            f"{module_name}_{instance_name}_composeMatrix",
            "composeMatrix",
        )

        self.nodes.decompose = self.__create_node(
            f"{module_name}_{instance_name}_composeDecompose",
            "decomposeMatrix",
        )

        self.nodes.quat_to_euler = self.__create_node(
            f"{module_name}_{instance_name}_quatToEuler",
            "quatToEuler",
        )

        # compound specific nodes

        # direction is specific per extract axis
        self.nodes.direction = self.__create_node(
            f"{module_name}_{instance_name}_{self.extract_axis}_direction",
            MULT_NODE_NAME
        )

        # remap is specifix per translate axis
        self.nodes.remap = self.__create_node(
            f"{module_name}_{instance_name}_{self.translate_axis}_remapValue",
            "remapValue",
        )

        self.nodes.multiply_compensate = self.__create_node(
            f"{module_name}_{instance_name}_{self.extract_axis}_compensate",
            ADD_NODE_NAME,
        )

    def create_rig(self, module_name, instance_name, rotation_parent, joints):
        """Create logic rig.

        Args:
            module_name (str): Name of the module
            instance_name (str): Name of the instance
            rotation_parent (node.Node): parent rotation joint.
            joints (Joints): Joints data class which holds start and end joint.
        """

        self._create_nodes(module_name, instance_name)

        # direction value
        input2_value = -1 if self.reverse_flip else 1
        cmds.setAttr(f"{self.nodes.direction}.input2", input2_value)
        # self.nodes.direction.input2.value = -1 if self.reverse_flip else 1

        # node connections
        connection_pairs = {
            f"{rotation_parent}.rotateX": f"{self.nodes.compose}.inputRotateX",
            f"{rotation_parent}.rotateY": f"{self.nodes.compose}.inputRotateY",
            f"{rotation_parent}.rotateZ": f"{self.nodes.compose}.inputRotateZ",
            f"{self.nodes.compose}.outputMatrix": f"{self.nodes.decompose}.inputMatrix",
            f"{self.nodes.decompose}.outputQuat{self.extract_axis}": f"{self.nodes.quat_to_euler}.inputQuat{self.extract_axis}",
            f"{self.nodes.decompose}.outputQuatW": f"{self.nodes.direction}.input1",
            f"{self.nodes.direction}.output": f"{self.nodes.quat_to_euler}.inputQuatW",
            f"{self.nodes.quat_to_euler}.outputRotate{self.extract_axis}": f"{self.nodes.remap}.inputValue",
            f"{self.nodes.quat_to_euler}.outputRotate{self.extract_axis}": f"{self.nodes.multiply_compensate}.input1",
        }

        # make the rotation connection separately to be able to optimize where applicable

        if self.extract_multiplier != 0.0:
            self.nodes.multiply = self.__create_node(
                f"{module_name}_{instance_name}_{self.extract_axis}_multDoubleLinear",
                MULT_NODE_NAME,
            )
            additional_pairs = {
            f"{self.nodes.multiply_compensate}.output": f"{self.nodes.multiply}.input1",
            f"{self.nodes.multiply}.output": f"{joints.start}.rotate{self.extract_axis}",
            }
            connection_pairs.update(additional_pairs)
            cmds.setAttr(f"{self.nodes.multiply}.input2", self.extract_multiplier)

        for source, target in connection_pairs.items():
            # We are reconnecting same plugs a lot for the sake of simplicity
            # This is in order to not to get excess warnings in the logs.
            _inputs = (
                cmds.listConnections(source, source=True, skipConversionNodes=True, plugs=True)
                or []
            )
            if target not in _inputs:
                cmds.connectAttr(source, target, force=True)

        # set the node values

        # multiply value
        rotate_value = cmds.getAttr(f"{self.nodes.quat_to_euler}.outputRotate{self.extract_axis}")
        cmds.setAttr(f"{self.nodes.multiply_compensate}.input2", rotate_value * -1)

        cmds.connectAttr(f"{self.nodes.quat_to_euler}.outputRotate{self.extract_axis}", f"{self.nodes.remap}.inputValue")

        # we don't want to alter the original list.
        driver_value_range = list(self.driver_range)
        driver_neutral = cmds.getAttr(f"{self.nodes.quat_to_euler}.outputRotate{self.extract_axis}")
        driver_value_range.insert(0, driver_neutral)

        driven_neutral = cmds.getAttr(f"{joints.end}.translate{self.translate_axis}")
        driven_value_range = list(self.driven_range)
        driven_value_range.insert(0, driven_neutral)

        # if the compound is not bidirectional, override the minimum values to
        # match the initial values too.
        if not self.bidirectional:
            driver_value_range[1] = driver_neutral
            driven_value_range[1] = driven_neutral

        for index, (driver_value, driven_value) in enumerate(
            zip(driver_value_range, driven_value_range)
        ):
            cmds.setAttr(f"{self.nodes.remap}.value[{index}].value_Position", driver_value)
            cmds.setAttr(f"{self.nodes.remap}.value[{index}].value_FloatValue", driven_value)
            cmds.setAttr(f"{self.nodes.remap}.value[{index}].value_Interp", self.interpolation_dict[self._interpolation])

        cmds.connectAttr(f"{self.nodes.remap}.outValue", f"{joints.end}.translate{self.translate_axis}", force=True)

    def __create_node(self, name, node_type):
        """Create the node. If exists, use the existing one.

        Args:
            name (str): name of the node
            node_type (str): maya node type

        Returns:
            node.Node
        """
        if not cmds.objExists(name):
            cmds.createNode(node_type, name=name)
        return name

    def _validate_range(self, value, minimum_value=2, maximum_value=2):
        """Validate the range value."""
        if not isinstance(value, (list, tuple)):
            raise ValueError("range must be a list or tuple.")
        if not minimum_value >= len(value) >= maximum_value:
            raise ValueError(
                "Range count is not within limits ({0} - {1})".format(
                    minimum_value, maximum_value
                )
            )
        return value
