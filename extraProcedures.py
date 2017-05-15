import pymel.core as pm

def getDistance( node1, node2):
    """
    Calculates the distance between Node 1 and Node 2
    Args:
        node1: Node 1. Must be a transform node 
        node2: Node 2. Must be a transform node

    Returns: Distance value.

    """
    Ax, Ay, Az = node1.getTranslation(space="world")
    Bx, By, Bz = node2.getTranslation(space="world")
    return ((Ax-Bx)**2 + (Ay-By)**2 + (Az-Bz)**2)**0.5
    
def alignTo(node1, node2, mode=0, o=(0,0,0)):
    """
    Aligns the first node to the second.
    Args:
        node1: Node to be aligned.
        node2: Target Node.
        mode: Specifies the alignment Mode. Valid Values: 0=position only, 1=Rotation Only, 2=Position and Rotation
        o: Offset Value. Default: (0,0,0)

    Returns:None

    """
    if mode==0:
        ##Position Only
        pointCon=pm.pointConstraint (node2, node1, mo=False, o=o)
        pm.delete(pointCon)
    elif mode==1:
        ##Rotation Only
        orientCon=pm.orientConstraint (node2, node1, mo=False, o=o)
        pm.delete(orientCon)
    elif mode==2:
        ##Position and Rotation
        parentCon=pm.parentConstraint (node2, node1, mo=False)
        pm.delete(parentCon)

    
def createUpGrp(obj, suffix):
    """
    Creates an Upper Group for the given object.
    Args:
        obj: Source Object
        suffix: Suffix for the group. String.

    Returns: The created group node

    """
    grpName = (obj.nodeName() + "_" + suffix)
    slJoGrp = pm.group (em=True,name=grpName)

    #align the new created empty group to the selected object
    pointCon = pm.parentConstraint (obj, slJoGrp, mo=False)
    pm.delete (pointCon)
    
    #check if the target object has a parent
    originalParent = pm.listRelatives(obj, p=True)
    if (len(originalParent) > 0):
        pm.parent(slJoGrp, originalParent[0])

    pm.parent(obj,slJoGrp)
    return slJoGrp



## example use: connectMirror(obj1, obj2, "X")
def connectMirror (node1, node2, mirrorAxis="X"):
    """
    Make a mirrored connection between node1 and node2 along the mirrorAxis
    Args:
        node1: Driver Node
        node2: Driven Node
        mirrorAxis: Mirror axis for the driven node.

    Returns: None

    """
    #nodes Translate
    rvsNodeT=pm.createNode("reverse")
    minusOpT=pm.createNode("plusMinusAverage")
    pm.setAttr(minusOpT.operation, 2)
    node1.translate >> rvsNodeT.input
    rvsNodeT.output >> minusOpT.input3D[0]
    pm.setAttr(minusOpT.input3D[1], (1, 1, 1))
    #nodes Rotate
    rvsNodeR=pm.createNode("reverse")
    minusOpR=pm.createNode("plusMinusAverage")
    pm.setAttr(minusOpR.operation, 2)
    node1.rotate >> rvsNodeR.input
    rvsNodeR.output >> minusOpR.input3D[0]
    pm.setAttr(minusOpR.input3D[1], (1, 1, 1))
    
    #Translate
    
    if (mirrorAxis=="X"):
        minusOpT.output3Dx >> node2.tx
        node1.ty >> node2.ty
        node1.tz >> node2.tz
        
        node1.rx >> node2.rx
        minusOpR.output3Dy >> node2.ry
        minusOpR.output3Dz >> node2.rz
    if (mirrorAxis=="Y"):
        node1.tx >> node2.tx
        minusOpT.output3Dy >> node2.ty
        node1.tz >> node2.tz
        
        minusOpR.output3Dx >> node2.rx
        node1.ry >> node2.ry
        minusOpR.output3Dz >> node2.rz
        
    if (mirrorAxis=="Z"):
        node1.tx >> node2.tx
        node1.ty >> node2.ty
        minusOpT.output3Dz >> node2.tz
        
        node1.rx >> node2.rx
        minusOpR.output3Dy >> node2.ry
        minusOpR.output3Dz >> node2.rz


def colorize (node, index):
    """
    Changes the wire color of the node to the index
    Args:
        node: Node
        index: Index Number

    Returns:None

    """
    #shape=node.getShape()
    shapes=pm.listRelatives(node, s=True)
    for i in shapes:
        pm.setAttr(i.overrideEnabled, True)
        pm.setAttr(i.overrideColor, index)
        
def lockAndHide (node, channelArray):
    """
    Locks and hides the channels specified in the channelArray.
    Args:
        node: Node 
        channelArray: Must be list value containing the channels as string values. eg: ["sx", "sy", "sz"] or ["translateX", "rotateX", "sz"] 

    Returns: None

    """
    for i in channelArray:
        attribute=("{0}.{1}".format(node, i))
        pm.setAttr(attribute, lock=True, keyable=False, channelBox=False)
    
def alignBetween (node, targetA, targetB, pos=True, rot=True):
    """
    Alignes the node between target A and target B
    Args:
        node: Node to be aligned
        targetA: Target A
        targetB: Target B
        pos: bool. If True, aligns the position between targets. Default True
        rot: bool. If True, aligns the rotation between targets. Default True

    Returns: None

    """
    if pos:
        tempPo=pm.pointConstraint(targetA, targetB, node, mo=False)
        pm.delete(tempPo)
    if rot:
        tempAim=pm.aimConstraint(targetB,node, mo=False)
        pm.delete(tempAim)

