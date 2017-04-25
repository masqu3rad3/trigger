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
    grpName = (obj.name() + "_" + suffix)
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
