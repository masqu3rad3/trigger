## connects a controller, mesh surface and joint with follicle and makes it possible to
## create extra joint based tweaking over blendshapes
# import pymel.core as pm
from maya import cmds
from trigger.utils import parentToSurface
from importlib import reload
reload(parentToSurface)
# from trigger.utils import extraProcedures as extra
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

    # if type(joint) == str:
    #     joint = pm.PyNode(joint)
    # if type(controller) == str:
    #     controller = pm.PyNode(controller)
    # if type(surface) == str:
    #     surface = pm.PyNode(surface)

    # master = joint.getParent()

    ## double group the joint
    # rigConnect = pm.group(joint, name="%s_rigConnect" % (joint.name()))
    # contConnect = pm.group(joint, name="%s_contConnect" % (joint.name()))

    rigConnect = cmds.group(name="%s_rigConnect" % joint, em=True)
    contConnect = cmds.group(name="%s_contConnect" % joint, em=True)
    functions.alignToAlter(rigConnect, joint, mode=0)
    functions.alignToAlter(contConnect, joint, mode=0)
    functions.alignTo(rigConnect, controller, position=False, rotation=True)
    functions.alignTo(contConnect, controller, position=False, rotation=True)

    # joint_parent = joint.getParent()
    joint_parent = functions.getParent(joint)
    ## if the offset has anouther parent, parent the new hierarchy under that

    cmds.parent(joint, contConnect)
    cmds.parent(contConnect, rigConnect)

    if joint_parent:
        cmds.parent(rigConnect, joint_parent)


    cont_surfaceAttach = functions.createUpGrp(controller, "sAttach")
    cont_negative = functions.createUpGrp(controller, "negative")
    # follicleList = parentToSurface.parentToSurface([cont_surfaceAttach], surface, mode="pointConstraint")
    follicleList = parentToSurface.parentToSurface([cont_surfaceAttach], surface, mode=attach_mode)
    # pm.orientConstraint(master, cont_surfaceAttach, mo=False)

    # controller.translate >> contConnect.translate
    cmds.connectAttr("%s.translate" % controller, "%s.translate" % contConnect)
    # controller.rotate >> contConnect.rotate
    cmds.connectAttr("%s.rotate" % controller, "%s.rotate" % contConnect)

    ## negative node
    inverseNode = cmds.createNode("multiplyDivide", name="%s_inverse" % controller)
    cmds.setAttr("%s.input2" % inverseNode, -1, -1, -1)

    # controller.translate >> inverseNode.input1
    cmds.connectAttr("%s.translate" % controller, "%s.input1" % inverseNode)
    # inverseNode.output >> cont_negative.translate
    cmds.connectAttr("%s.output" % inverseNode, "%s.translate" % cont_negative)

    # print "HEHEHEHE" * 50
# jointOnBlendshapes()
