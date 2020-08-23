"""Drag & Drop installer for Maya 2018+"""

import os, sys

# confirm the maya python interpreter
try:
    from maya import cmds
    confirmed = True
except ImportError:
    confirmed = False


def _add_module():
    pass

def _edit_usersetup():
    file_location = os.path.join(os.path.dirname(__file__))
    pass