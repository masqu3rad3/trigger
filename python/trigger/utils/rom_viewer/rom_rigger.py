import logging
from inspect import getmembers, isfunction

from maya import cmds
from . import script_job

TYPE_EXPRESSION = getmembers(script_job, isfunction)[0][0]
LOG = logging.getLogger(__name__)

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
    def __init__(self):

        # class variables
        self.script_node = None
        self.trackers = []
        self.script_job_as_string = self._import_file_as_string(script_job.__file__.replace("pyc", "py"))

    def initialize_scriptnode(self, force=False):
        """Create the scriptNode if it is not already exist"""
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

    def add_tracker(self):
        self.initialize_scriptnode()  # create the script node if it is not already exist
        # get the tracker index
        tracker_index = len(self.trackers)
        _tracker = Tracker(tracker_index)
        self.trackers.append(_tracker)

    @staticmethod
    def _import_file_as_string(file_path):
        with open(file_path, 'r') as file:
            return file.read()

    def set_tracker_sizes(self, value):
        """Set the size of all trackers"""
        for tracker in self.trackers:
            tracker.size = value

    def set_tracker_fonts(self, font):
        """Set the font of all trackers"""
        for tracker in self.trackers:
            tracker.font = font

    def cascade_trackers(self):
        """Cascade the trackers"""
        total_y_offset = 0
        for nmb, tracker in enumerate(self.trackers):
            if nmb:
                total_y_offset -= tracker.size
            tracker.set_position((0, total_y_offset, 0))

class Tracker(object):
    """Data Class for trackers"""
    def __init__(self, index):
        """Initialize the tracker"""
        self.index = index
        self.type_node, self.type_transform, self.type_extrude = create_type()

        cmds.setAttr("{}.enableExtrusion".format(self.type_extrude), 0)

        _expression = "{0}({1})".format(TYPE_EXPRESSION, self.index)
        cmds.setAttr('{}.generator'.format(self.type_node), 9)
        cmds.setAttr('{}.pythonExpression'.format(self.type_node), _expression, type='string')

    @property
    def deformable(self):
        """Get the deformable from the type node"""
        return cmds.getAttr('{}.deformableType'.format(self.type_node))

    @deformable.setter
    def deformable(self, deformable):
        """Set the deformable on the type node"""
        cmds.setAttr('{}.deformableType'.format(self.type_node), deformable)

    @property
    def size(self):
        """Get the size of the type node"""
        return cmds.getAttr('{}.fontSize'.format(self.type_node))

    @size.setter
    def size(self, size):
        """Set the size of the type node"""
        cmds.setAttr('{}.fontSize'.format(self.type_node), size)

    @property
    def font(self):
        """Set the font on the type node"""
        return cmds.getAttr('{}.currentFont'.format(self.type_node))

    @font.setter
    def font(self, font):
        """Get the font from the type node"""
        cmds.setAttr('{}.currentFont'.format(self.type_node), font, type="string")

    def set_position(self, position):
        """Set the position of the type node"""
        cmds.setAttr('{}.translate'.format(self.type_transform), *position)

