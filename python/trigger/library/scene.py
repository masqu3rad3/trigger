"""Collection of methods for maya scene management."""

from maya import cmds


def reset():
    """Reset the scene to a clean state and preserve the perspective camera."""
    # get the camera matrix before deleting everything
    camera_matrix = cmds.xform("persp", query=True, worldSpace=True, matrix=True)
    center_of_interest = cmds.getAttr("perspShape.centerOfInterest")
    # delete all nodes
    cmds.file(newFile=True, force=True)
    # set the camera matrix
    cmds.xform("persp", worldSpace=True, matrix=camera_matrix)
    cmds.setAttr("perspShape.centerOfInterest", center_of_interest)
