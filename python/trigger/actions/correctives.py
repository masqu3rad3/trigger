"""Action Module for Pose space deformations"""

from trigger.core import io
from trigger.core import filelog
from trigger.core.decorators import tracktime

from trigger.ui import custom_widgets
from trigger.ui import feedback

log = filelog.Filelog(logname=__name__, filename="trigger_log")

"""
example action data:
ACTION_DATA = {
                "psd_definitions": [
                        {
                            "type": "angle",
                            "
                        },
                        {
                            "anchor": "head_cont",
                            "locations": ["pelvis_cont", "neck_cont", "master_cont"]
                        }
                    ]
                }
"""

ACTION_DATA = {
    "psd_definitions": [],
}

# Name of the class MUST be the capitalized version of file name. eg. morph.py => Morph, split_shapes.py => Split_shapes
class Psd(object):
    def __init__(self, *args, **kwargs):
        super(Psd, self).__init__()

        # user defined variables
        self.someProperty = None
        self.someMoreProperty = None

        # class variables

    def feed(self, action_data, *args, **kwargs):
        """Mandatory Method - Feeds the instance with the action data stored in actions session"""
        self.someProperty = action_data.get("some_property")
        self.someMoreProperty = action_data.get("some_more_property")

    def action(self):
        """Mandatory Method - Execute Action"""
        # everything in this method will be executed automatically.
        # This method does not accept any arguments. all the user variable must be defined to the instance before
        pass

    def save_action(self, file_path=None, *args, **kwargs):
        """Mandatory Method - Save Action"""
        # This method will be called automatically and accepts no arguments.
        # If the action has an option to save files, this method will be used by the UI.
        # Else, this method can stay empty
        pass

    def ui(self, ctrl, layout, handler, *args, **kwargs):
        """
        Mandatory Method - UI setting definitions

        Args:
            ctrl: (model_ctrl) ctrl object instance of /ui/model_ctrl. Updates UI and Model
            layout: (QLayout) The layout object from the main ui. All setting widgets should be added to this layout
            handler: (actions_session) An instance of the actions_session. TRY NOT TO USE HANDLER UNLESS ABSOLUTELY NECESSARY
            *args:
            **kwargs:

        Returns: None

        """

        pass


from importlib import reload

from maya import cmds

from trigger.library import functions
from trigger.library import connection
from trigger.library import api
from trigger.library import attribute
reload(attribute)

driver_transform = "joint1"
target_rotation = (-20,-30, 60)
corrected_shape = ""
up_vector = None
up_object = "nurbsCircle1"




# basic angle in the world 0
root_loc = cmds.spaceLocator(name="angleExt_root")[0]
point_a = cmds.spaceLocator(name="angleExt_pointA")[0]
cmds.setAttr("%s.tx" % point_a, 5)
point_b = cmds.spaceLocator(name="angleExt_pointB")[0]
point_b_offset = functions.createUpGrp(point_b, "offset")
cmds.setAttr("%s.tx" % point_b, 5)
cmds.parent(point_a, root_loc)
cmds.parent(point_b_offset, root_loc)

functions.alignTo(root_loc, driver_transform, position=True, rotation=True)
cmds.pointConstraint(driver_transform, root_loc, mo=False)
cmds.parentConstraint(driver_transform, point_a, mo=True)

connection.matrixConstraint(up_object, point_b_offset, st="xyz", mo=True)

#store current rotation
current_rotation = cmds.getAttr("%s.r" % driver_transform)[0]

# temporarily parent point_b to the transform to move it to the goal rotation
cmds.parent(point_b, driver_transform)
cmds.setAttr("%s.r" % driver_transform, *target_rotation)
cmds.parent(point_b, point_b_offset)
cmds.setAttr("%s.r" % driver_transform, *current_rotation)

angle_between = cmds.createNode("angleBetween", name="angleExt_angleBetween")
cmds.connectAttr("%s.t" % point_a, "%s.vector1" % angle_between)
cmds.connectAttr("%s.t" % point_b, "%s.vector2" % angle_between)

attribute.drive_attrs(angle_between,)

