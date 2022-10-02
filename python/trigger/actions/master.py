"""This module is responsible for mandatory elements for each rig. It is called silently"""

from maya import cmds

from trigger.library import functions
from trigger.library import attribute
from trigger.library import controllers as ic

ACTION_DATA = {}
class Master(object):
    def __init__(self, *args, **kwargs):
        super(Master, self).__init__()

    def action(self):
        """Mandatory method for all action maya_modules"""
        pref_name = "pref_cont"
        master_rig_grp = "rig_grp"
        trigger_rig_grp = "trigger_grp"
        render_geo_grp = "renderGeo_grp"
        for grp in [master_rig_grp, trigger_rig_grp, render_geo_grp]:
            if not cmds.objExists(grp):
                cmds.group(name=grp, em=True)
        if functions.getParent(trigger_rig_grp) != master_rig_grp:
            cmds.parent(trigger_rig_grp, master_rig_grp)
        if functions.getParent(render_geo_grp) != master_rig_grp:
            cmds.parent(render_geo_grp, master_rig_grp)
        if not cmds.objExists(pref_name):
            icon = ic.Icon()
            preferences_cont = icon.create_icon("Preferences", pref_name)
            cmds.parent(preferences_cont, trigger_rig_grp)
        # create attributes
        attributes = [{"attr_name": "cacheMode",
                       "nice_name": "Cache_Mode",
                       "attr_type": "bool",
                       "default_value": 0,
                       },
                      {"attr_name": "Control_Visibility",
                       "nice_name": "Control_Visibility",
                       "attr_type": "bool",
                       "default_value": 1,
                       },
                      {"attr_name": "Joints_Visibility",
                       "nice_name": "Joints_Visibility",
                       "attr_type": "bool",
                       "default_value": 0,
                       },
                      {"attr_name": "Rig_Visibility",
                       "nice_name": "Rig_Visibility",
                       "attr_type": "bool",
                       "default_value": 0,
                       },
        ]
        for attr_dict in attributes:
            attribute.create_attribute(pref_name, attr_dict, keyable=False)
        # extra.lockAndHide(pref_name)

    def feed(self, action_data, *args, **kwargs):
        """Mandatory Method"""
        pass

    def save_action(self, *args, **kwargs):
        """Mandatory Method"""
        pass

    def ui(self, ctrl, layout, handler, *args, **kwargs):
        """Mandatory Method"""
        pass