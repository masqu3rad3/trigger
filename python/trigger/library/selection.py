"""Functions, checks and queries for selection dependant tasks"""
from maya import cmds
from trigger.library import functions

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

def validate(min=None, max=None, groupsOnly=False, meshesOnly=False, nurbsCurvesOnly=False, transforms=True, fullPath=False):

    selected = cmds.ls(sl=True, long=fullPath)
    if not selected:
        return False, "Nothing selected"

    if groupsOnly:
        non_groups = [node for node in selected if not functions.isGroup(node)]
        if non_groups:
            return False, "Selection contains non-group nodes" %non_groups

    check_list = []
    if meshesOnly:
        check_list.append("mesh")
    if nurbsCurvesOnly:
        check_list.append("nurbsCurve")

    for check in check_list:
        if not transforms:
            filtered = cmds.ls(selected, type=check)
            if len(filtered) != len(selected):
                return False, "Selection type Error. Only %s type objects can be selected. (No Transform nodes)" %check
        else:
            for node in selected:
                shapes = functions.getShapes(node)
                if not shapes:
                    return False, "Selection contains objects other than %s (No shape node)" % check
                for shape in shapes:
                    if cmds.objectType(shape) != check:
                        return False, "Selection contains objects other than %s" %check

    if min and len(selected) < min:
        return False, "The minimum required selection is %s" %min
    if max and len(selected) > max:
        return False, "The maximum selection is %s" % max
    return selected, ""