## connects a controller, mesh surface and joint with follicle and makes it possible to
## create extra joint based tweaking over blendshapes
import sys
from maya import cmds
from trigger.utils import parentToSurface

if sys.version_info.major == 3:
    from importlib import reload
reload(parentToSurface)
from trigger.library import functions


def jointOnBlendshapes(joint=None, controller=None, surface=None, attach_mode="parentConstraint"):
    """
    Creates the follicle and makes the necessary connections for using joint tweaking over
    blendshapes. If no arguments are given, it uses current selection to find out nodes.
    If this is the case, controller must be selected before the surface node.
    JOINTS MUST HAVE PARENT NODES WHICH MOVES AND SCALES WITH THE RIG
    Args:
        joint: (pyNode) joint node
        controller: (pyNode) controller node
        surface: (pyNode) surface node which holds the skin cluster and blendshape node

    Returns: None

    """
    if joint == None and controller == None and surface == None:
        selection = cmds.ls(sl=True)
        if len(selection) != 3:
            cmds.warning("3 objects must be selected (control curve, joint, mesh surface")
            return
        else:
            try:
                joint = cmds.ls(selection, type="joint")[0]
                selection.remove(joint)
            except IndexError:
                cmds.warning("No joint selected")
                return
            try:
                transformObjects = cmds.ls(selection, type="transform")
                controller = transformObjects[0]
                surface = transformObjects[1]
            except IndexError:
                cmds.warning("Transform objects must be selected")
                return

    rigConnect = cmds.group(name="%s_rigConnect" % joint, em=True)
    contConnect = cmds.group(name="%s_contConnect" % joint, em=True)
    functions.align_to_alter(rigConnect, joint, mode=0)
    functions.align_to_alter(contConnect, joint, mode=0)
    functions.align_to(rigConnect, controller, position=False, rotation=True)
    functions.align_to(contConnect, controller, position=False, rotation=True)

    joint_parent = functions.get_parent(joint)
    ## if the offset has anouther parent, parent the new hierarchy under that

    cmds.parent(joint, contConnect)
    cmds.parent(contConnect, rigConnect)

    if joint_parent:
        cmds.parent(rigConnect, joint_parent)


    cont_surfaceAttach = functions.create_offset_group(controller, "sAttach")
    cont_negative = functions.create_offset_group(controller, "negative")
    follicleList = parentToSurface.parentToSurface([cont_surfaceAttach], surface, mode=attach_mode)

    cmds.connectAttr("%s.translate" % controller, "%s.translate" % contConnect)
    cmds.connectAttr("%s.rotate" % controller, "%s.rotate" % contConnect)

    ## negative node
    inverseNode = cmds.createNode("multiplyDivide", name="%s_inverse" % controller)
    cmds.setAttr("%s.input2" % inverseNode, -1, -1, -1)

    cmds.connectAttr("%s.translate" % controller, "%s.input1" % inverseNode)
    cmds.connectAttr("%s.output" % inverseNode, "%s.translate" % cont_negative)

    return [rigConnect, cont_surfaceAttach, follicleList[0]]
