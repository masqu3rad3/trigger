# pylint: disable=consider-using-f-string
"""Base Class for all methodologies."""

from maya import cmds

class MethodBase(object):
    """Base for all methods."""

    method_name = ""

    def __init__(self):
        self.properties = {}
        self.inputs = {
            "name": "",
            "face_mesh": None,
            "eye_mesh": None,
            "eye_joint": None,
            "pupil_joint": None,
            "controller": None,
            "module_group": None,
        }

        self.dev_mode = False
        self.pref_nodes = (
            []
        )  # the nodes populated in here will get preference connections

    @staticmethod
    def calculate_eye_radii(eye_mesh):
        """Calculate the maximum eye radius by bounding box"""
        b_box = cmds.xform(
            eye_mesh, boundingBox=True, query=True, worldSpace=True
        )
        _radii = (
            abs(b_box[0] - b_box[3]),
            abs(b_box[1] - b_box[4]),
            abs(b_box[2] - b_box[5]),
        )
        max_radius = max(_radii) * 0.5
        min_radius = min(_radii) * 0.5
        average_radius = (sum(_radii) / len(_radii)) * 0.5

        return max_radius, min_radius, average_radius

    def run(self):
        """Build the eye-bulge."""
        raise Exception("Run method must be overriden on after inheritance.")
