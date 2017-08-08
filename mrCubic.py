## Mr. Cubic

import pymel.core as pm

import extraProcedures as extra
reload(extra)

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
                    extra.alignBetween(cubeGuy, j, c)
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





