import logging
from inspect import getmembers, isfunction

from maya import cmds
from . import script_job

TYPE_EXPRESSION = getmembers(script_job, isfunction)[0][0]
LOG = logging.getLogger(__name__)

def _check_plugins(plugins):
    """Check and make sure the required plugins are up and running.

    Raises:
        Exception: If one or more plugins are missing
    """
    if not isinstance(plugins, list):
        plugins = [plugins]
    missing_plugins = []
    for plugin in plugins:
        if not cmds.pluginInfo(plugin, loaded=True, query=True):
            try:
                cmds.loadPlugin(plugin)
            except:  # pylint: disable=bare-except
                missing_plugins.append(plugin)
    if missing_plugins:
        _mis_list = "\n".join(missing_plugins)
        msg = """Following plugins are missing => \n{0}
Make sure your Maya Environment set correctly and your show has access to those plugins""".format(
            _mis_list
        )
        LOG.error(msg)
        raise Exception(msg)

def create_type():
    """Create a 3d Type and return relevant nodes"""
    # subtract the current state and previous state to get the created type nodes
    transform = cmds.polyPlane(constructionHistory=False)[0]
    mesh = cmds.listRelatives(transform, children=True)[0]

    type_node = cmds.createNode("type")
    type_extrude = cmds.createNode("typeExtrude")
    cmds.setAttr("{}.extrudeDivisions".format(type_extrude), 1)

    cmds.connectAttr("time1.outTime", "{}.time".format(type_node))
    cmds.connectAttr("{}.outputMesh".format(type_node), "{}.inputMesh".format(type_extrude))
    cmds.connectAttr("{}.vertsPerChar".format(type_node), "{}.vertsPerChar".format(type_extrude))

    cmds.connectAttr("{}.outputMesh".format(type_extrude), "{}.inMesh".format(mesh))

    cmds.polyTriangulate(mesh, constructionHistory=True)
    cmds.polySoftEdge(mesh, angle=30, constructionHistory=True)
    cmds.select(deselect=True)
    return type_node, transform, type_extrude

class RomRigger(object):
    """Handle creating trackers."""
    def __init__(self):
        """Initialize the handler."""
        # class variables
        self.script_node = None
        self.trackers = []
        self.script_job_as_string = self._import_file_as_string(script_job.__file__.replace("pyc", "py"))

        _check_plugins("Type")

    def initialize_scriptnode(self, force=False):
        """Create the scriptNode if it is not already exist."""
        if self.script_node:
            if force:
                cmds.delete(self.script_node)
            else:
                LOG.warning("Script node already initialized")
                return

        self.script_node = cmds.scriptNode(beforeScript=self.script_job_as_string)
        cmds.setAttr('{}.sourceType'.format(self.script_node), 1)
        cmds.setAttr('{}.scriptType'.format(self.script_node), 1)
        cmds.scriptNode(self.script_node, executeBefore=True)

    def add_tracker(self, deformable=True, extrusion_depth=0, index_offset=0, exclude=None, include=None, replace=None, default_value="-"):
        """Create a new tracker and add it to the trackers list.

        Args:
            deformable (bool): Whether the tracker is deformable or not.
            extrusion_depth (int or float): Extrusion depth for the tracker.
            index_offset (int): Offset to add to the tracker index.
            exclude (list): List of strings to exclude from the tracker.
            include (list): List of strings to include in the tracker.
            replace (list): List of two strings to replace in the tracker display name.
        """
        self.initialize_scriptnode()  # create the script node if it is not already exist
        # get the tracker index
        tracker_index = len(self.trackers) + index_offset
        # add the filter for the referenced curves all the time
        exclude = exclude or []
        if ":" not in exclude:
            exclude.append(":")
        _tracker = Tracker(tracker_index, deformable=deformable, extrusion_depth=extrusion_depth, exclude=exclude, include=include, replace=replace, default_value=[default_value])
        self.trackers.append(_tracker)
        return _tracker

    @staticmethod
    def _import_file_as_string(file_path):
        """Import the script job as string to be implemented into the node."""
        with open(file_path, 'r') as file:
            return file.read()

    def set_tracker_sizes(self, value):
        """Set the size of all trackers."""
        for tracker in self.trackers:
            tracker.size = value

    def set_tracker_fonts(self, font):
        """Set the font of all trackers."""
        for tracker in self.trackers:
            tracker.font = font

    def cascade_trackers(self):
        """Cascade the trackers."""
        total_y_offset = 0
        for nmb, tracker in enumerate(self.trackers):
            if nmb:
                total_y_offset -= tracker.size
            tracker.set_position((0, total_y_offset, 0))

class Tracker(object):
    """Class for trackers."""
    def __init__(self, index, deformable=True, extrusion_depth=0, **extra_args):
        """Initialize the tracker."""
        self.index = index
        self.type_node, self.type_transform, self.type_extrude = create_type()

        cmds.setAttr("{}.enableExtrusion".format(self.type_extrude), 0)

        args = [str(self.index)] + ["{0}={1}".format(key, val) for key, val in extra_args.items()]
        args_str = ", ".join(args)
        _expression = "{0}({1})".format(TYPE_EXPRESSION, args_str)
        cmds.setAttr('{}.generator'.format(self.type_node), 9)
        cmds.setAttr('{}.pythonExpression'.format(self.type_node), _expression, type='string')

        self.name = "RomTracker_{}_geo".format(index)
        self.deformable = deformable
        self.extrusion_depth = extrusion_depth

    @property
    def name(self):
        """Get the name of the tracker. This is the transform name in the scene."""
        return self.type_transform

    @name.setter
    def name(self, value):
        """Set the name of the transform node."""
        if not isinstance(value, str):
            LOG.error("Name must be string value. Got %s", value)
            return
        self.type_transform = cmds.rename(self.type_transform, value)

    @property
    def deformable(self):
        """Get the deformable from the type node."""
        return cmds.getAttr('{}.deformableType'.format(self.type_node))

    @deformable.setter
    def deformable(self, deformable):
        """Set the deformable on the type node."""
        cmds.setAttr('{}.deformableType'.format(self.type_node), deformable)

    @property
    def extrusion_depth(self):
        """Get the extrusion depth."""
        return cmds.getAttr("{}.extrudeDistance".format(self.type_extrude))

    @extrusion_depth.setter
    def extrusion_depth(self, value):
        """Set the extrusion status.

        Args:
            value (int or float): value for extrusion distance
        """
        if not isinstance(value, (float,int)):
            LOG.error("Extrusion depth must be float or int. Got %s", value)
        if float(value) <= 0.0:
            cmds.setAttr("{}.enableExtrusion".format(self.type_extrude), 0)
        else:
            cmds.setAttr("{}.enableExtrusion".format(self.type_extrude), 1)
            cmds.setAttr("{}.extrudeDistance".format(self.type_extrude), float(value))
            cmds.setAttr("{}.extrudeDivisions".format(self.type_extrude), 1)

    @property
    def size(self):
        """Get the size of the type node."""
        return cmds.getAttr('{}.fontSize'.format(self.type_node))

    @size.setter
    def size(self, size):
        """Set the size of the type node."""
        cmds.setAttr('{}.fontSize'.format(self.type_node), size)

    @property
    def font(self):
        """Set the font on the type node."""
        return cmds.getAttr('{}.currentFont'.format(self.type_node))

    @font.setter
    def font(self, font):
        """Get the font from the type node."""
        cmds.setAttr('{}.currentFont'.format(self.type_node), font, type="string")

    def set_position(self, position):
        """Set the position of the type node."""
        cmds.setAttr('{}.translate'.format(self.type_transform), *position)
