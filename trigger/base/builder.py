"""New rig builder module"""
from maya import cmds
from trigger.core import feedback
from trigger.core import settings
from trigger import actions

FEEDBACK = feedback.Feedback(logger_name=__name__)

class Builder(object):
    def __init__(self, progress_bar=None):
        super(Builder, self).__init__()

        self.action_dict = {}
        for mod in actions.__all__:
            self.action_dict[mod]=eval('actions.{0}.ACTION_DATA'.format(mod))
        # self.action_dict = {mod: eval("actions.{0}.ACTION_DATA".format(mod)) for mod in actions.__all__}
        self.action_list = []

    def get_valid_actions(self):
        return sorted(self.action_dict.keys())

    def add_action(self, action_name):
        pass

    def edit_action(self, action_index):
        pass

    def remove_action(self, action_index):
        pass

    def clear_actions(self):
        pass

    def save_build(self, file_path):
        pass

    def load_build(self, file_path):
        pass

    def build(self):
        pass

    def build_and_publish(self):
        pass
