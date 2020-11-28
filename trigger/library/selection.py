"""Functions, checks and queries for selection dependant tasks"""
from maya import cmds

def get_selection_type():
    component_selection = cmds.ls(sl=True, type='float3')
    if not component_selection:
        obj_selection = cmds.ls(sl=True, o=True)
        if obj_selection:
            return "object"
        else:
            return None
    face_selection = cmds.polyListComponentConversion(component_selection, ff=True, tf=True)
    edge_selection = cmds.polyListComponentConversion(component_selection, fe=True, te=True)
    vertex_selection = cmds.polyListComponentConversion(component_selection, fv=True, tv=True)
    if face_selection:
        return "face"
    elif edge_selection:
        return "edge"
    elif vertex_selection:
        return "vertex"
    else:
        return "object"


def selection_validate():
    ## TODO Make this method useful
    """validates if only faces of a single object has been made"""
    all_object_selection = cmds.ls(sl=True, o=True)
    if len(all_object_selection) > 1:
        return False
    face_selection = cmds.polyListComponentConversion(cmds.ls(sl=True, type='float3'), ff=True, tf=True)
    if not face_selection:
        return False
    return True