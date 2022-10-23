"""Maya interface related methods"""
from maya import cmds
from trigger.core.decorators import undo
from trigger.library import functions
import maya.api.OpenMaya as om

def refreshOutliners():
    eds = cmds.lsUI(editors=True)
    for ed in eds:
        if cmds.outlinerEditor(ed, exists=True):
            cmds.outlinerEditor(ed, e=True, refresh=True)

@undo
def annotate(object, text, name=None, offset=None, visibility_range=None, arrow=False):
    name = name or "annotate_%s" %object
    center = cmds.objectCenter(object, gl=True)
    offset = offset or (0,0,0)
    pos = om.MVector(center)+om.MVector(offset)
    annotation_shape = cmds.annotate(object, tx=text, p=pos)
    cmds.setAttr("%s.displayArrow" %annotation_shape, arrow)

    if visibility_range:
        cmds.setKeyframe(annotation_shape, at="v", t=visibility_range[0] - 1, value=0)
        cmds.setKeyframe(annotation_shape, at="v", t=visibility_range[0], value=1)
        cmds.setKeyframe(annotation_shape, at="v", t=visibility_range[1], value=1)
        cmds.setKeyframe(annotation_shape, at="v", t=visibility_range[1] + 1, value=0)

    annotation_transform = cmds.rename(functions.get_parent(annotation_shape), name)
    return annotation_transform
