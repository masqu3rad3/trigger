"""Handles Display Shaders"""

from trigger.core import io

ACTION_DATA = {}

class Look(object):
    def __init__(self):
        super(Look, self).__init__()
        self.io = io.IO(file_name="tmp_look.json")

    def action(self):
        pass

    def save_look(self, nodes, file_path):
        pass

    def load_look(self, file_path):
        pass