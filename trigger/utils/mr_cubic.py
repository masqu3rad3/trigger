## Mr. Cubic
from maya import cmds
from trigger.library import connection
from trigger.library import functions

def mrCube (jointList, width=1):
    mrCubeGrp = cmds.group(name="mrCube", em=True)
    for jnt in jointList:
        if cmds.objectType(jnt, isType="joint"):
            children=cmds.listRelatives(jnt, children=True, type="joint")
            if children:
                for c in children:
                    cubeGuy = cmds.polyCube(name=functions.uniqueName("mrCube_%s" % c), h=width, d=width, w=width)[0]
                    functions.alignBetween(cubeGuy, jnt, c)
                    height=functions.getDistance(jnt, c)
                    cmds.setAttr("%s.sx" % cubeGuy, height)
                    connection.matrixConstraint(jnt, cubeGuy, mo=True)
                    cmds.parent(cubeGuy, mrCubeGrp)
            else:
                cubeGuy = cmds.polyCube(name=functions.uniqueName("mrCube_%s" % jnt), h=width, d=width, w=width)[0]
                connection.matrixConstraint(jnt, cubeGuy, mo=False)
                cmds.parent(cubeGuy, mrCubeGrp)





