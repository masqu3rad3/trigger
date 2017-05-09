import pymel.core as pm

# def alignTo(node1, node2):
#         pointCon=pm.parentConstraint (node2, node1, mo=False)
#         pm.delete (pointCon)
        
        
def getDistance( objA, objB ):
    Ax, Ay, Az = objA.getTranslation(space="world")
    Bx, By, Bz = objB.getTranslation(space="world")
    return (  (Ax-Bx)**2 + (Ay-By)**2 + (Az-Bz)**2  )**0.5
    
def alignTo(node1, node2, mode, o=None):
    if mode==0:
        ##Position Only
        if o==None:
            pointCon=pm.pointConstraint (node2, node1, mo=False)
        else:
            pointCon=pm.pointConstraint (node2, node1, mo=False, o=o)
        pm.delete(pointCon)
    elif mode==1:
        ##Rotation Only
        if o==None:
            orientCon=pm.orientConstraint (node2, node1, mo=False)
        else:
            orientCon=pm.orientConstraint (node2, node1, mo=False, o=o)
        pm.delete(orientCon)
    elif mode==2:
        ##Position and Rotation
        parentCon=pm.parentConstraint (node2, node1, mo=False)
        pm.delete(parentCon)

    
def createUpGrp(obj, suffix):
    grpName = (obj.nodeName() + "_" + suffix)
    slJoGrp = pm.group (em=True,name=grpName)

    #align the new created empty group to the selected object
    pointCon=pm.parentConstraint (obj, slJoGrp, mo=False)
    pm.delete (pointCon)
    
    #check if the target object has a parent
    originalParent=pm.listRelatives(obj, p=True)
    if (len(originalParent) > 0):
        pm.parent(slJoGrp,originalParent[0])

    pm.parent(obj,slJoGrp)
    grpName =""
    return slJoGrp



## example use: connectMirror(obj1, obj2, "X")
def connectMirror (node1, node2, mirrorAxis):
    #nodes Translate
    rvsNodeT=pm.createNode("reverse")
    minusOpT=pm.createNode("plusMinusAverage")
    pm.setAttr(minusOpT.operation,2)
    node1.translate >> rvsNodeT.input
    rvsNodeT.output >> minusOpT.input3D[0]
    pm.setAttr(minusOpT.input3D[1],(1,1,1))
    #nodes Rotate
    rvsNodeR=pm.createNode("reverse")
    minusOpR=pm.createNode("plusMinusAverage")
    pm.setAttr(minusOpR.operation, 2)
    node1.rotate >> rvsNodeR.input
    rvsNodeR.output >> minusOpR.input3D[0]
    pm.setAttr(minusOpR.input3D[1],(1,1,1))
    
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
    
    #shape=node.getShape()
    shapes=pm.listRelatives(node, s=True)
    for i in shapes:
        pm.setAttr(i.overrideEnabled, True)
        pm.setAttr(i.overrideColor, index)
        
def lockAndHide (node, channelArray):
    for i in channelArray:
        pm.setAttr(node+"."+i, lock=True, keyable=False, channelBox=False)
    
