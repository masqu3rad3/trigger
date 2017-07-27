import pymel.core as pm
import pymel.core.datatypes as dt
import extraProcedures as extra


def initSpineBones(segments):
    ID = 0
    suffix = str(ID)
    while pm.objExists("jInit_spine"+suffix):
        ID += 1
        suffix = str(ID)


    if pm.ls(sl=True, type="joint"):
        root = pm.ls(sl=True)[-1]
    else:
        root = None

    pm.select(d=True)
    if (segments + 1) < 2:
        pm.error("Define at least 3 segments for spine section")
        return
    rPoint = 14.0
    nPoint = 21.0
    add = (nPoint - rPoint) / ((segments + 1) - 1)
    jointList = []
    for i in range(0, (segments + 1)):
        spine = pm.joint(p=(0, (rPoint + (add * i)), 0), name="jInit_spine%s_%s" %(suffix, str(i)))
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

def initArmBones(whichArm, faceDir="+z", upDir="+y", constrainedTo=None):
    # check validity of arguments
    whichArmValids = ["left", "right", "both"]
    if whichArm not in whichArmValids:
        pm.error("whichArm argument is not valid. Valid arguments are: %s" %whichArmValids)
    dirValids = ["+x", "+y", "+z", "-x", "-y", "-z", "+X", "+Y", "+Z", "-X", "-Y", "-Z"]
    if faceDir not in dirValids:
        pm.error("faceDir argument is not valid. Valid arguments are: %s" %dirValids)
    if upDir not in dirValids:
        pm.error("upDir argument is not valid. Valid arguments are: %s" % dirValids)

    # make sure the imputs are lowercase:
    faceDir = faceDir.lower()
    upDir = upDir.lower()

    ## get the necessary info from arguments
    side = 1 if whichArm == "left" else 2
    lookAxis = faceDir.strip("+-")
    lookAxisMult = -1 if faceDir.strip(lookAxis) == "-" else 1

    upAxis = upDir.strip("+-")
    upAxisMult = -1 if upDir.strip(upAxis) == "-" else 1

    if lookAxis == upAxis:
        pm.error("faceDir and upDir cannot be the same axis")

    mirrorAxis = "xyz".strip(lookAxis + upAxis)
    sideMult = 1 if whichArm == "left" else -1


    currentselection=pm.ls(sl=True)


    ID = 0
    suffix = whichArm
    while pm.objExists("jInit_collar_"+suffix):
        ID += 1
        suffix = "%s%s" % (whichArm, str(ID))

    if pm.ls(sl=True, type="joint"):
        root = pm.ls(sl=True)[-1]
    else:
        root = None

    if whichArm=="both":
        leftLocs = initArmBones("left", faceDir, upDir)
        initArmBones("right", faceDir, upDir, constrainedTo=leftLocs)
        return
    pm.select(d=True)

    if lookAxis == "z" and upAxis == "y":
        ## Facing Z Up Y
        a = [("x","y","z"), 1*sideMult*lookAxisMult, 1*upAxisMult, 1*lookAxisMult]
    elif lookAxis == "z" and upAxis == "x":
        ## Facing Z Up X
        a = [("y", "x", "z"), -1*sideMult*lookAxisMult, 1*upAxisMult, 1*lookAxisMult]
    elif lookAxis == "y" and upAxis == "z":
        ## Facing Y Up Z
        a = [("x", "z", "y"), -1*sideMult*lookAxisMult, 1*upAxisMult, 1*lookAxisMult]
    elif lookAxis == "y" and upAxis == "x":
        ## Facing Y Up X
        a = [("y", "z", "x"), 1*sideMult*lookAxisMult, 1*upAxisMult, 1*lookAxisMult]
    elif lookAxis == "x" and upAxis == "z":
        ## Facing X Up Z
        a = [("z", "x", "y"), 1*sideMult*lookAxisMult, 1*upAxisMult, 1*lookAxisMult]
    elif lookAxis == "x" and upAxis == "y":
        ## Facing X Up Y
        a = [("z", "y", "x"), -1*sideMult*lookAxisMult, 1*upAxisMult, 1*lookAxisMult]


    order = a[0]
    dirX = a[1]
    dirY = a[2]
    dirZ = a[3]
    collarP = dt.Vector(2*dirX, 0, 0*dirZ)
    collarVec = eval("collarP.{0},collarP.{1},collarP.{2}".format(order[0],order[1],order[2]))
    shoulderP = dt.Vector(5*dirX,0,0*dirZ)
    shoulderVec = eval("shoulderP.{0},shoulderP.{1},shoulderP.{2}".format(order[0],order[1],order[2]))
    elbowP = dt.Vector(9*dirX,0,-1*dirZ)
    elbowVec = eval("elbowP.{0},elbowP.{1},elbowP.{2}".format(order[0],order[1],order[2]))
    handP = dt.Vector(14*dirX,0,0*dirZ)
    handVec = eval("handP.{0},handP.{1},handP.{2}".format(order[0],order[1],order[2]))

    pm.select(d=True)
    collar = pm.joint(p=collarVec, name=("jInit_collar_" + suffix))
    shoulder = pm.joint(p=shoulderVec, name=("jInit_shoulder_" + suffix))
    elbow = pm.joint(p=elbowVec, name=("jInit_elbow_" + suffix))
    hand = pm.joint(p=handVec, name=("jInit_hand_" + suffix))
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

    loc_grp_arm = pm.group(name=("locGrp_%s" %suffix), em=True)
    pm.setAttr(loc_grp_arm.v, 0)
    locatorsList=[]
    for i in range (0,len(jointList)):
        locator = pm.spaceLocator(name="loc_" + jointList[i].name())
        locatorsList.append(locator)
        if constrainedTo:
            extra.alignTo(locator, jointList[i], 2)
            pm.parentConstraint(locator, jointList[i], mo=True)
            extra.connectMirror(constrainedTo[i], locatorsList[i], mirrorAxis=mirrorAxis.upper())
        else:
            pm.parentConstraint(jointList[i], locator, mo=False)
        pm.parent(locator, loc_grp_arm)

    if root:
        if not constrainedTo:
            # align the none constrained near to the selected joint
            extra.alignTo(jointList[0], root)
            # move it a little along the mirrorAxis
            value = pm.getAttr("%s.t%s" %(jointList[0],mirrorAxis))
            pm.setAttr("%s.t%s" %(jointList[0],mirrorAxis), value+3)

        pm.parent(jointList[0], root)
    pm.select(currentselection)
    return locatorsList


def initLegBones(whichLeg, faceDir="+z", upDir="+y", constrainedTo=None):

    # check validity of arguments
    whichLegValids = ["left", "right", "both"]
    if whichLeg not in whichLegValids:
        pm.error("whichArm argument is not valid. Valid arguments are: %s" %whichLegValids)
    dirValids = ["+x", "+y", "+z", "-x", "-y", "-z", "+X", "+Y", "+Z", "-X", "-Y", "-Z"]
    if faceDir not in dirValids:
        pm.error("faceDir argument is not valid. Valid arguments are: %s" %dirValids)
    if upDir not in dirValids:
        pm.error("upDir argument is not valid. Valid arguments are: %s" % dirValids)

    # make sure the imputs are lowercase:
    faceDir = faceDir.lower()
    upDir = upDir.lower()

    ## get the necessary info from arguments
    side = 1 if whichLeg == "left" else 2
    lookAxis = faceDir.strip("+-")
    lookAxisMult = -1 if faceDir.strip(lookAxis) == "-" else 1

    upAxis = upDir.strip("+-")
    upAxisMult = -1 if upDir.strip(upAxis) == "-" else 1

    if lookAxis == upAxis:
        pm.error("faceDir and upDir cannot be the same axis")

    mirrorAxis = "xyz".strip(lookAxis + upAxis)
    sideMult = 1 if whichLeg == "left" else -1


    currentselection=pm.ls(sl=True)



    ID = 0
    suffix = whichLeg
    while pm.objExists("jInit_LegRoot_"+suffix):
        ID += 1
        suffix = "%s%s" % (whichLeg, str(ID))

    if pm.ls(sl=True, type="joint"):
        masterParent = pm.ls(sl=True)[-1]
    else:
        masterParent = None

    if whichLeg=="both":
        leftLocs = initLegBones("left", faceDir, upDir)
        initLegBones("right", faceDir, upDir, constrainedTo=leftLocs)
        return
    pm.select(d=True)

    if lookAxis == "z" and upAxis == "y":
        ## Facing Z Up Y
        a = [("x","y","z"), 1*sideMult*lookAxisMult, 1*upAxisMult, 1*lookAxisMult]
    elif lookAxis == "z" and upAxis == "x":
        ## Facing Z Up X
        a = [("y", "x", "z"), -1*sideMult*lookAxisMult, 1*upAxisMult, 1*lookAxisMult]
    elif lookAxis == "y" and upAxis == "z":
        ## Facing Y Up Z
        a = [("x", "z", "y"), -1*sideMult*lookAxisMult, 1*upAxisMult, 1*lookAxisMult]
    elif lookAxis == "y" and upAxis == "x":
        ## Facing Y Up X
        a = [("y", "z", "x"), 1*sideMult*lookAxisMult, 1*upAxisMult, 1*lookAxisMult]
    elif lookAxis == "x" and upAxis == "z":
        ## Facing X Up Z
        a = [("z", "x", "y"), 1*sideMult*lookAxisMult, 1*upAxisMult, 1*lookAxisMult]
    elif lookAxis == "x" and upAxis == "y":
        ## Facing X Up Y
        a = [("z", "y", "x"), -1*sideMult*lookAxisMult, 1*upAxisMult, 1*lookAxisMult]

    order = a[0]
    dirX = a[1]
    dirY = a[2]
    dirZ = a[3]

    rootP = dt.Vector(2*dirX,14,0*dirZ)
    rootVec = eval("rootP.{0},rootP.{1},rootP.{2}".format(order[0],order[1],order[2]))
    hipP = dt.Vector(5*dirX,10,0*dirZ)
    hipVec = eval("hipP.{0},hipP.{1},hipP.{2}".format(order[0],order[1],order[2]))
    kneeP = dt.Vector(5*dirX,5,1*dirZ)
    kneeVec = eval("kneeP.{0},kneeP.{1},kneeP.{2}".format(order[0],order[1],order[2]))
    footP = dt.Vector(5*dirX,1,0*dirZ)
    footVec = eval("footP.{0},footP.{1},footP.{2}".format(order[0],order[1],order[2]))
    ballP = dt.Vector(5*dirX,0,2*dirZ)
    ballVec = eval("ballP.{0},ballP.{1},ballP.{2}".format(order[0],order[1],order[2]))
    toeP = dt.Vector(5*dirX,0,4*dirZ)
    toeVec = eval("toeP.{0},toeP.{1},toeP.{2}".format(order[0],order[1],order[2]))
    bankoutP = dt.Vector(4*dirX,0,2*dirZ)
    bankoutVec = eval("bankoutP.{0},bankoutP.{1},bankoutP.{2}".format(order[0],order[1],order[2]))
    bankinP = dt.Vector(6*dirX,0,2*dirZ)
    bankinVec = eval("bankinP.{0},bankinP.{1},bankinP.{2}".format(order[0],order[1],order[2]))
    toepvP = dt.Vector(5*dirX,0,4.3*dirZ)
    toepvVec = eval("toepvP.{0},toepvP.{1},toepvP.{2}".format(order[0],order[1],order[2]))
    heelpvP = dt.Vector(5*dirX,0,-0.2*dirZ)
    heelpvVec = eval("heelpvP.{0},heelpvP.{1},heelpvP.{2}".format(order[0],order[1],order[2]))


    root = pm.joint(p=rootVec, name=("jInit_LegRoot_" + whichLeg))
    hip = pm.joint(p=hipVec, name=("jInit_Hip_" + whichLeg))
    knee = pm.joint(p=kneeVec, name=("jInit_Knee_" + whichLeg))
    foot = pm.joint(p=footVec, name=("jInit_Foot_" + whichLeg))
    ball = pm.joint(p=ballVec, name=("jInit_Ball_" + whichLeg))
    toe = pm.joint(p=toeVec, name=("jInit_Toe_" + whichLeg))
    pm.select(d=True)
    bankout = pm.joint(p=bankoutVec, name=("jInit_BankOut_" + whichLeg))
    pm.select(d=True)
    bankin = pm.joint(p=bankinVec, name=("jInit_BankIn_" + whichLeg))
    pm.select(d=True)
    toepv = pm.joint(p=toepvVec, name=("jInit_ToePv_" + whichLeg))
    pm.select(d=True)
    heelpv = pm.joint(p=heelpvVec, name=("jInit_HeelPv_" + whichLeg))
    pm.joint(root, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(hip, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(knee, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(foot, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(ball, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(toe, e=True, zso=True, oj="xyz", sao="yup")
    pm.parent(heelpv, foot)
    pm.parent(toepv, foot)
    pm.parent(bankin, foot)
    pm.parent(bankout, foot)

    pm.setAttr(root + ".side", side)
    pm.setAttr(root + ".type", 18)
    pm.setAttr(root + ".otherType", "LegRoot")
    pm.setAttr(hip + ".side", side)
    pm.setAttr(hip + ".type", 2)
    pm.setAttr(knee + ".side", side)
    pm.setAttr(knee + ".type", 3)
    pm.setAttr(foot + ".side", side)
    pm.setAttr(foot + ".type", 4)

    pm.setAttr(ball + ".side", side)
    pm.setAttr(ball + ".type", 18)
    pm.setAttr(ball + ".otherType", "Ball")

    pm.setAttr(toe + ".side", side)
    pm.setAttr(toe + ".type", 5)

    pm.setAttr(heelpv + ".side", side)
    pm.setAttr(heelpv + ".type", 18)
    pm.setAttr(heelpv + ".otherType", "HeelPV")
    pm.setAttr(toepv + ".side", side)
    pm.setAttr(toepv + ".type", 18)
    pm.setAttr(toepv + ".otherType", "ToePV")
    pm.setAttr(bankin + ".side", side)
    pm.setAttr(bankin + ".type", 18)
    pm.setAttr(bankin + ".otherType", "BankIN")
    pm.setAttr(bankout + ".side", side)
    pm.setAttr(bankout + ".type", 18)
    pm.setAttr(bankout + ".otherType", "BankOUT")
    jointList = [root, hip, knee, foot, ball, toe, bankout, bankin, toepv, heelpv]
    for i in jointList:
        pm.setAttr(i + ".drawLabel", 1)

    loc_grp_leg = pm.group(name=("locGrp_%s" %suffix), em=True)
    pm.setAttr(loc_grp_leg.v, 0)
    locatorsList=[]
    for i in range (0,len(jointList)):
        locator = pm.spaceLocator(name="loc_" + jointList[i].name())
        locatorsList.append(locator)
        if constrainedTo:
            extra.alignTo(locator, jointList[i], 2)
            pm.parentConstraint(locator, jointList[i], mo=True)
            extra.connectMirror(constrainedTo[i], locatorsList[i], mirrorAxis=mirrorAxis.upper())
        else:
            pm.parentConstraint(jointList[i], locator, mo=False)
        pm.parent(locator, loc_grp_leg)

    if masterParent:
        if not constrainedTo:
            # align the none constrained near to the selected joint
            extra.alignTo(jointList[0], masterParent)
            # move it a little along the mirrorAxis
            value = pm.getAttr("%s.t%s" %(jointList[0],mirrorAxis))
            pm.setAttr("%s.t%s" %(jointList[0],mirrorAxis), value+3)

        pm.parent(jointList[0], masterParent)
    pm.select(currentselection)
    return locatorsList