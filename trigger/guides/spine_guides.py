from maya import cmds
import maya.api.OpenMaya as om
from trigger.library import functions as extra

def initialSpine(segments, suffix, side=0, tMatrix=None, look_vector=(0,0,1)):
    """
    Creates a preset spine hieararchy with given segments
    Args:
        transformKey: the keyword for transformation matrix. transformator function will use this key to orienct joint in space
        segments: (int) segment count
        suffix: (String) name suffix - must be unique

    Returns: (List) jointList

    """
    tMatrix = om.MMatrix() if not tMatrix else tMatrix
    sideMult = -1 if side == 2 else 1

    rPoint = om.MVector(0, 14.0, 0) * tMatrix

    nPoint = om.MVector(0, 21.0, 0) * tMatrix
    offsetVector = (nPoint - rPoint).normal()
    add = (nPoint - rPoint) / ((segments + 1) - 1)
    jointList = []
    for i in range(0, (segments + 1)):
        spine = cmds.joint(p=(rPoint + (add * i)), name="jInit_spine_%s_%s" % (suffix, str(i)))
        cmds.setAttr("%s.side" % spine, 0)
        type = 18
        if i == 0:
            cmds.setAttr("%s.type" % spine, type)
            cmds.setAttr("%s.otherType" % spine, "SpineRoot", type="string")
            cmds.addAttr(shortName="resolution", longName="Resolution", defaultValue=4, minValue=1,
                         at="long", k=True)
            cmds.addAttr(shortName="dropoff", longName="DropOff", defaultValue=1.0, minValue=0.1,
                         at="float", k=True)
            cmds.addAttr(at="enum", k=True, shortName="twistType", longName="Twist_Type", en="regular:infinite")
            cmds.addAttr(at="enum", k=True, shortName="mode", longName="Mode", en="equalDistance:sameDistance")

            self.createAxisAttributes(spine)
            cmds.setAttr("{0}.radius".format(spine), 3)
        elif i == (segments):
            # type = 18
            cmds.setAttr("%s.type" % spine, type)
            cmds.setAttr("%s.otherType" % spine, "SpineEnd", type="string")
        else:
            type = 6
            cmds.setAttr("%s.type" % spine, type)

        jointList.append(spine)
        for i in jointList:
            cmds.setAttr("%s.drawLabel" % i, 1)
            cmds.setAttr("{0}.displayLocalAxis".format(i), 1)

    extra.orientJoints(jointList, worldUpAxis=-look_vector, reverseAim=sideMult, reverseUp=sideMult)

    self.spineJointsList.append(jointList)
    extra.colorize(jointList, self.majorCenterColor, shape=False)
    return jointList, offsetVector