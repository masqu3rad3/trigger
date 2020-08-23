"""This module is responsible for mandatory elements for each rig. It is called silently"""

from maya import cmds

from trigger.library import functions as extra
from trigger.library import controllers as ic

ACTION_DATA = {}
class Master(object):
    def __init__(self, *args, **kwargs):
        super(Master, self).__init__()
        # self.rigName = "trigger"

    def action(self):
        """Mandatory method for all action maya_modules"""
        pref_name = "pref_cont"

        rig_grp_name = "trigger_grp"
        if not cmds.objExists(rig_grp_name):
            rig_grp = cmds.group(name=rig_grp_name, em=True)
        if not cmds.objExists(pref_name):
            icon = ic.Icon()
            preferences_cont = icon.createIcon("Preferences", pref_name)
            cmds.parent(preferences_cont, rig_grp_name)
        # create attributes
        attributes = [{"attr_name": "Control_Visibility",
                       "nice_name": "Control_Visibility",
                       "attr_type": "bool",
                       # "attr_type": "enum",
                       # "enum_list": "Off:On",
                       "default_value": 1,
                       },
                      {"attr_name": "Joints_Visibility",
                       "nice_name": "Joints_Visibility",
                       "attr_type": "bool",
                       # "attr_type": "enum",
                       # "enum_list": "Off:On",
                       "default_value": 0,
                       },
                      {"attr_name": "Rig_Visibility",
                       "nice_name": "Rig_Visibility",
                       "attr_type": "bool",
                       # "attr_type": "enum",
                       # "enum_list": "Off:On",
                       "default_value": 0,
                       },
        ]
        for attr_dict in attributes:
            extra.create_attribute(pref_name, attr_dict, keyable=False)
        # extra.lockAndHide(pref_name)
