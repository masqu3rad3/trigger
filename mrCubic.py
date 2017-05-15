## Mr. Cubic

import pymel.core as pm

import extraProcedures as extra
reload(extra)

def mrCube (jointList, widthRatio=1):
    for j in jointList:
        widthRatio=1
        cubeRoot=j.getTranslation(space="world")
        ## get the child joints
        children=pm.listRelatives(j, children=True, type="joint")
        ## create a cube for each child
        for c in children:
            cubeGuy=pm.polyCube(name="mrCube_"+c)
            extra.alignBetween(cubeGuy, j, c)
            # scale it
            height=extra.getDistance(j, c)
            pm.setAttr(cubeGuy[0].sx, height)
            pm.xform(cubeGuy[0], piv=cubeRoot, ws=True)
            # skin it
            pm.skinCluster(cubeGuy[0], j)




