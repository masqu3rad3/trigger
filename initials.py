import pymel.core as pm
import pymel.core.datatypes as dt
import extraProcedures as extra


def initSpineBones(segments):

    if pm.ls(sl=True, type="joint"):
        root = pm.ls(sl=True)[-1]
    else:
        root = None
    if pm.objExists("jInit_spine*"):
        pm.error("Naming mismatch!!! There are Spine Initializers in the Scene")
        return
    pm.select(d=True)
    if (segments + 1) < 2:
        pm.error("Define at least 3 segments for spine section")
        return
    rPoint = 14.0
    nPoint = 21.0
    add = (nPoint - rPoint) / ((segments + 1) - 1)
    jointList = []
    for i in range(0, (segments + 1)):
        spine = pm.joint(p=(0, (rPoint + (add * i)), 0), name="jInit_spine" + str(i))
        pm.setAttr(spine + ".side", 0)
        type = 1 if i == 0 else 6
        pm.setAttr(spine + ".type", type)
        jointList.append(spine)
        for i in jointList:
            pm.setAttr(i + ".drawLabel", 1)
    if root:
        extra.alignTo(jointList[0], root)
        pm.move(jointList[0], (0,2,0), relative=True)
        pm.parent(jointList[0],root)

def initArmBones(whichArm, dir):

## //TODO elaborate
    idCounter = 0
    while pm.objExists("jInit_*"+whichArm):
        suffix = "%s%s" % (suffix, str(idCounter + 1))

    if whichArm=="both":
        initArmBones("left", 1)
        initArmBones("right",1)

    if dir == -1:
        side = 2
    if dir == 1:
        side = 1
    if pm.objExists("jInit_*"+whichArm):
        pm.error("Naming mismatch!!! There are Arm Initializers in the Scene")
        return
    pm.select(d=True)
    collar=pm.joint(p=(2*dir,25,0), name=("jInit_collar_"+whichArm))
    shoulder=pm.joint(p=(5*dir,25,0), name=("jInit_shoulder_"+whichArm))
    elbow=pm.joint(p=(9*dir,25,-1), name=("jInit_elbow_"+whichArm))
    hand=pm.joint(p=(14*dir,25,0), name=("jInit_hand_"+whichArm))
    # Orientation
    pm.joint(collar, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(shoulder, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(elbow, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(hand, e=True, zso=True, oj="xyz", sao="yup")
    # Joint Labeling
    pm.setAttr(collar+".side", side)
    pm.setAttr(collar+".type", 9)
    pm.setAttr(shoulder + ".side", side)
    pm.setAttr(shoulder + ".type", 10)
    pm.setAttr(elbow + ".side", side)
    pm.setAttr(elbow + ".type", 11)
    pm.setAttr(hand + ".side", side)
    pm.setAttr(hand + ".type", 12)

    jointList=[collar, shoulder, elbow, hand]
    for i in jointList:
        pm.setAttr(i + ".drawLabel", 1)


L_loc_grp_arm=pm.group(name="locGrp_L_arm", em=True)
pm.setAttr(L_loc_grp_arm.v,0)
R_loc_grp_arm=pm.group(name="locGrp_R_arm", em=True)
pm.setAttr(R_loc_grp_arm.v,0)
joints_l_arm=initArmBones("L_arm", 1)
locators_l_arm=[]
for i in range (0,len(joints_l_arm)):
    locator=pm.spaceLocator(name="loc_"+joints_l_arm[i].name())
    locators_l_arm.append(locator)
    pm.parentConstraint(joints_l_arm[i], locator, mo=False)
    pm.parent(locator,L_loc_grp_arm)
joints_r_arm=initArmBones("R_arm", -1)
locators_r_arm=[]
for x in range (0,len(joints_r_arm)):
    locator=pm.spaceLocator(name="loc_"+joints_r_arm[x].name())
    locators_r_arm.append(locator)
    extra.alignTo(locator,joints_r_arm[x],2)
    pm.parentConstraint(locator, joints_r_arm[x], mo=True)
    extra.connectMirror(locators_l_arm[x], locators_r_arm[x],"X")
    pm.parent(locator,R_loc_grp_arm)


# def initNeckBones
#     if pm.objExists("jInit_neck*"):
#         pm.error("Naming mismatch!!! There are Spine Initializers in the Scene")
#         return
#
#     # pm.select(d=True)
#     rPointNeck = dt.Vector(0, 25.757, 0)
#     nPointNeck = dt.Vector(0, 29.418, 0.817)
#     addNeck = (nPointNeck - rPointNeck) / (self.neckSegments)
#     jointListNeck = []
#     for i in range(0, (self.neckSegments)):
#         neck = pm.joint(p=(rPointNeck + (addNeck * i)), name="jInit_neck" + str(i))
#         pm.setAttr(neck + ".side", 0)
#
#         if i == 0:
#             pm.setAttr(neck + ".type", 18)
#             pm.setAttr(neck + ".otherType", "NeckRoot")
#         else:
#             pm.setAttr(neck + ".type", 7)
#         jointListNeck.append(neck)
#
#     # neck = pm.joint(p=(0, 25.757, 0.249), name=("jInit_neck"))
#     # jointList.append(neck)
#     head = pm.joint(p=(0, 29.418, 0.817), name=("jInit_head"))
#     jointList.append(head)
#     headEnd = pm.joint(p=(0, 32.848, 0.817), name=("jInit,headEnd"))
#     jointList.append(headEnd)
#     pm.select(d=True)
#     jawStart = pm.joint(p=(0, 28.735, 1.367), name=("jInit_jawStart"))
#     jointList.append(jawStart)
#     jawEnd = pm.joint(p=(0, 27.857, 3.161), name=("jInit_jawEnd"))
#     jointList.append(jawEnd)
#
#     pm.setAttr(head + ".side", 0)
#     pm.setAttr(head + ".type", 8)
#
#     pm.setAttr(headEnd + ".side", 0)
#     pm.setAttr(headEnd + ".type", 8)
#
#     pm.setAttr(jawStart + ".side", 0)
#     pm.setAttr(jawStart + ".type", 18)
#     pm.setAttr(jawStart + ".otherType", "Jaw")
#
#     pm.setAttr(jawEnd + ".side", 0)
#     pm.setAttr(jawEnd + ".type", 18)
#     pm.setAttr(jawEnd + ".otherType", "Jaw")
#
#     pm.parent(jawStart, head)
#     for i in jointList:
#         pm.setAttr(i + ".drawLabel", 1)
#     return jointList