"""New rig builder module"""
from maya import cmds
from trigger.core import feedback
from trigger.core import settings
from trigger import actions

FEEDBACK = feedback.Feedback(logger_name=__name__)

class Builder(settings.Settings):
    def __init__(self, progress_bar=None):
        super(Builder, self).__init__()

        self.action_dict = {}
        for mod in actions.__all__:
            print(mod)
            self.action_dict[mod]=eval('actions.{0}.ACTION_DATA'.format(mod))
        # self.action_dict = {mod: eval("actions.{0}.ACTION_DATA".format(mod)) for mod in actions.__all__}

