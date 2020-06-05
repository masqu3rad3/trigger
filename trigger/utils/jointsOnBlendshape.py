## connects a controller, mesh surface and joint with follicle and makes it possible to
## create extra joint based tweaking over blendshapes
import pymel.core as pm
from trigger.utils import parentToSurface
reload(parentToSurface)
from trigger.utils import extraProcedures as extra


def jointOnBlendshapes(joint=None, controller=None, surface=None):
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
        selection = pm.ls(sl=True)
        if len(selection) != 3:
            pm.warning("3 objects must be selected (control curve, joint, mesh surface")
            return
        else:
            try:
                joint = pm.ls(selection, type="joint")[0]
                selection.remove(joint)
            except IndexError:
                pm.warning("No joint selected")
                return
            try:
                transformObjects = pm.ls(selection, type="transform")
                controller = transformObjects[0]
                surface = transformObjects[1]
            except IndexError:
                pm.warning("Transform objects must be selected")
                return

    if type(joint) == str:
        joint = pm.PyNode(joint)
    if type(controller) == str:
        controller = pm.PyNode(controller)
    if type(surface) == str:
        surface = pm.PyNode(surface)

    master = joint.getParent()
    ## double group the joint
    rigConnect = pm.group(joint, name="%s_rigConnect" % (joint.name()))
    contConnect = pm.group(joint, name="%s_contConnect" % (joint.name()))

    cont_surfaceAttach = extra.createUpGrp(controller, "sAttach")
    cont_negative = extra.createUpGrp(controller, "negative")
    follicleList = parentToSurface.parentToSurface([cont_surfaceAttach], surface, mode="pointConstraint")
    pm.orientConstraint(master, cont_surfaceAttach, mo=False)

    controller.translate >> contConnect.translate
    controller.rotate >> contConnect.rotate

    ## negative node
    inverseNode = pm.createNode("multiplyDivide", name="%s_inverse" % (controller.name()))
    pm.setAttr(inverseNode.input2, (-1, -1, -1))

    controller.translate >> inverseNode.input1
    inverseNode.output >> cont_negative.translate

# jointOnBlendshapes()
