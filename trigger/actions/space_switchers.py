"""Creates extra space switchers"""

from maya import cmds
from trigger.core import feedback
import trigger.library.functions as functions
import trigger.library.controllers as ic

from trigger.base import session

from trigger import modules
import trigger.utils.space_switcher as anchorMaker
from trigger.core import settings

from trigger.actions import master

from trigger.ui.Qt import QtWidgets

FEEDBACK = feedback.Feedback(logger_name=__name__)

ACTION_DATA = {
               "swithcer_definitions": []
               }

"""
example action data:
ACTION_DATA = {
                "switcher_definitions": [
                        {
                            "anchor": "IK_L_Hand_cont",
                            "locations": ["pelvis_cont", "master_cont", "chest_cont"]
                        },
                        {
                            "anchor": "head_cont",
                            "locations": ["pelvis_cont", "neck_cont", "master_cont"]
                        }
                    ]
                }
"""