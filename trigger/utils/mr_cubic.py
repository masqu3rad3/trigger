## Mr. Cubic
from maya import cmds
import trigger.library.functions as extra

def mrCube (jointList, width=1):
    mrCubeGrp = cmds.group(name="mrCube", em=True)
    for jnt in jointList:
        if cmds.objectType(jnt, isType="joint"):
            children=cmds.listRelatives(jnt, children=True, type="joint")
            if children:
                for c in children:
                    cubeGuy = cmds.polyCube(name=extra.uniqueName("mrCube_%s" %c), h=width, d=width, w=width)[0]
                    extra.alignBetween(cubeGuy, jnt, c)
                    height=extra.getDistance(jnt, c)
                    cmds.setAttr("%s.sx" % cubeGuy, height)
                    extra.matrixConstraint(jnt, cubeGuy, mo=True)
                    cmds.parent(cubeGuy, mrCubeGrp)
            else:
                cubeGuy = cmds.polyCube(name=extra.uniqueName("mrCube_%s" % jnt), h=width, d=width, w=width)[0]
                extra.matrixConstraint(jnt, cubeGuy, mo=False)
                cmds.parent(cubeGuy, mrCubeGrp)





