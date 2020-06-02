from maya import cmds
import maya.api.OpenMaya as om
from trigger.library import functions as extra

from trigger.core import io
from trigger import modules


class Session(object):
    def __init__(self):
        super(Session, self).__init__()

    def save_session(self):
        # save the initial setup
        pass
    def save_session_as(self, file_path):
        pass

    def load_initials(self, file_path):
        pass


