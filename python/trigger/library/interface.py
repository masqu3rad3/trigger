"""Maya interface related methods"""
from maya import cmds
from trigger.core.decorators import undo
from trigger.library import functions
from maya.api import OpenMaya


def refresh_outliner():
    """Refresh the Maya outliner"""
    eds = cmds.lsUI(editors=True)
    for ed in eds:
        if cmds.outlinerEditor(ed, exists=True):
            cmds.outlinerEditor(ed, e=True, refresh=True)


@undo
def annotate(
    transform_node, text, name=None, offset=None, visibility_range=None, arrow=False
):
    name = name or "annotate_%s" % transform_node
    # center = cmds.objectCenter(transform_node, gl=True)
    bbx = cmds.xform(transform_node, q=True, bb=True, ws=True)  # world space
    center_x = (bbx[0] + bbx[3]) / 2.0
    center_y = (bbx[1] + bbx[4]) / 2.0
    center_z = (bbx[2] + bbx[5]) / 2.0
    center = (center_x, center_y, center_z)
    offset = offset or (0, 0, 0)
    pos = OpenMaya.MVector(center) + OpenMaya.MVector(offset)
    annotation_shape = cmds.annotate(transform_node, tx=text, p=pos)
    cmds.setAttr("%s.displayArrow" % annotation_shape, arrow)

    if visibility_range:
        cmds.setKeyframe(annotation_shape, at="v", t=visibility_range[0] - 1, value=0)
        cmds.setKeyframe(annotation_shape, at="v", t=visibility_range[0], value=1)
        cmds.setKeyframe(annotation_shape, at="v", t=visibility_range[1], value=1)
        cmds.setKeyframe(annotation_shape, at="v", t=visibility_range[1] + 1, value=0)

    annotation_transform = cmds.rename(functions.get_parent(annotation_shape), name)
    return annotation_transform
