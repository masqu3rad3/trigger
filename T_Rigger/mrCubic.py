## Mr. Cubic

import pymel.core as pm

import extraProcedures as extra
reload(extra)

def alignBetween (node, targetA, targetB, pos=True, rot=True, ore=False, o=(0,0,0)):
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
        tempAim=pm.aimConstraint(targetB,node, mo=False, o=o)
        pm.delete(tempAim)
    if ore:
        tempOre=pm.orientConstraint(targetA, targetB, node, mo=False, o=o)
        pm.delete(tempOre)

def mrCube (jointList, width=1):
    mrCubeGrp = pm.group(name="mrCube", em=True)
    for j in jointList:
        if (j.type() == "joint"):
            widthRatio=1
            cubeRoot=j.getTranslation(space="world")
            ## get the child joints
            children=pm.listRelatives(j, children=True, type="joint")
            ## create a cube for each child

            for c in children:
                if c.type() == "joint":
                    cubeGuy = pm.polyCube(name="mrCube_"+c, h=width, d=width, w=width)
                    alignBetween(cubeGuy, j, c)
                    # scale it
                    height=extra.getDistance(j, c)
                    pm.setAttr(cubeGuy[0].sx, height)
                    pm.xform(cubeGuy[0], piv=cubeRoot, ws=True)
                    pm.parent(cubeGuy, mrCubeGrp)
                    # skin it
                    pm.skinCluster(cubeGuy[0], j)
            if len(children) == 0:
                pm.select(j)
                cubeGuy = pm.polyCube(name="mrCube_" + j, h=width, d=width, w=width)
                extra.alignTo(cubeGuy[0], j, 2)
                pm.parent(cubeGuy, mrCubeGrp)
                pm.skinCluster(j, cubeGuy)





