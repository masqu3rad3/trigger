import pymel.core as pm

def alignTo(node1, node2):
        pointCon=pm.parentConstraint (node2, node1, mo=False)
        pm.delete (pointCon)
        
def alignPositionTo(node1, node2):
        pointCon=pm.pointConstraint (node2, node1, mo=False)
        pm.delete (pointCon)        
        
def getDistance( objA, objB ):
    Ax, Ay, Az = objA.getTranslation(space="world")
    Bx, By, Bz = objB.getTranslation(space="world")
    return (  (Ax-Bx)**2 + (Ay-By)**2 + (Az-Bz)**2  )**0.5
    
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
    return slJoGrp
