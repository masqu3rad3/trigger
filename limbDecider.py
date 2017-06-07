import pymel.core as pm

import createArms as arm
reload(arm)

import createLegs as leg
reload(leg)

import extraProcedures as extra
reload(extra)

def limbDecider(rootJoint, limbType="idByLabel", whichSide="idByLabel", mirrorAxis="-X"):
    """
    Creates a limb or body part.
    Args:
        rootJoint: (Joint) The root joint of the limb or body part which will be created. This is a Collar bone for the arms, a thigh bone for legs, etc.
        limbType: (String) Specifies the type of the limb. Valid values are, "arm", "leg", TODO// MORE WILL COME, "idByLabel", "idByName". idByLabel checks the label values of the joint. If there is a mismatch it throws an error. ifByName checks the name conventions of the node. If there is a mismatch it throws an error.
        whichSide: (String) Specifies which side of this lim resides. Valid values are, "right",
        mirrorAxis:

    Returns:

    """
    if rootJoint.type() != "joint":
        pm.error("Root node must be a Joint")
<<<<<<< Updated upstream
    validAxes = ("X", "Y", "Z", "-X", "-Y", "-Z")
    if not mirrorAxis in validAxes:
        pm.error("Not Valid mirrorAxis. Valid values are 'X', 'Y', 'Z', '-X', '-Y', '-Z'")

    mNegative = False
    if "-" in mirrorAxis:
        mNegative = True
    mAxis = mirrorAxis.replace("-", "")
    validLimbTypes=("arm", "leg") # // TODO: more will be added
    rootName = rootJoint.name()

    if limbType == "idByName" or "idByLabel":
        limbType = extra.jointTypeID(rootJoint, limbType)
    if whichSide == "idByName" or "idByLabel":
        limbSide = extra.jointSideID(rootJoint, whichSide)


    # if this is an arm connection
    if limbType == "Collar" or "arm":
        arm.createArm(getArmBones(rootJoint), suffix=limbSide+"_arm", side=limbSide, mirrorAxis=mAxis)


## TODO
    # # understand the limbType
    # if limbType == "auto":
    #     for i in range (len(validLimbTypes)):
    #         if validLimbTypes[i] in rootName:
    #             limbType = validLimbTypes[i]
    #     if limbType == "auto":
    #          pm.error("No Matching Limb Type with the joint name. You may try override it by using 'limbType' flag")
    #
    # # understand which side is it
    # if whichSide == "auto":
    #     rootP = rootJoint.getTranslation(space="world")
    #     val=0
    #     exec("val=rootP."+mAxis.lower())
    #     print "val", "=?", val
    #     if val > 0 and mNegative == True:
    #         whichSide="l"
    #     else:
    #         whichSide="r"

    # if limbType == "arm":
    #     arm.createArm(getArmBones(rootJoint), (whichSide+"_arm"), mirrorAxis=mAxis)
    #
    # if limbType == "leg":
    #     getLegBones(rootJoint)
    #     # // TODO: LEG CREATION


=======

    # Collect all joints connected to the master root
    allJoints = pm.listRelatives(rootJoint, ad=True, type="joint")
    # print allJoints
    limbJoints=[]
    for j in allJoints:
        limbProperties = extra.identifyMaster(j)
        print limbProperties
        # If the joint is a collar bone, create an arm there
        # if limbProperties[0] == "Collar":
        #     arm.createArm(getArmBones(j), suffix=limbProperties[2]+"_arm", side=limbProperties[2])
        if limbProperties[0] == "LegRoot":
            leg.createLeg(getLegBones(j), suffix=limbProperties[2]+"_leg", side=limbProperties[2])
>>>>>>> Stashed changes


def getArmBones(rootNode):
    collar = rootNode
    shoulder = (jFoolProof(collar))[0]
    elbow = (jFoolProof(shoulder))[0]
    hand = (jFoolProof(elbow))[0]
    armInits = {
        "Collar": collar,
        "Shoulder": shoulder,
        "Elbow": elbow,
        "Hand": hand
    }
    return armInits


def getLegBones(rootNode):
    rCon = rootNode
    upLeg = (jFoolProof(rCon))[0]
    knee = (jFoolProof(upLeg))[0]
    foot = (jFoolProof(knee))[0]
    footJoints = jFoolProof(foot, min=5, max=5)
    print footJoints
    # // TODO: GET ALL LEG BONES






def jFoolProof(node, type="joint", min=1, max=1):
    children = pm.listRelatives(node, c=True)
    validChildren=[]
    jCount=0
    for i in children:
        if i.type() == type:
            validChildren.append(i)
            jCount += 1
    print jCount
    if min <= jCount <= max:
        return validChildren
    else:
        pm.error("joint count does not meet the requirements")

