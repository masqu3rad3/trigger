import pymel.core as pm

import createArms as arm
reload(arm)

import createLegs as leg
reload(leg)

import extraProcedures as extra
reload(extra)

def limbDecider(rootJoint, limbType="idByLabel", whichSide="idByLabel", mirrorAxis="-X"):

    validAxes = ("X", "Y", "Z", "-X", "-Y", "-Z")
    if not mirrorAxis in validAxes:
        pm.error("Not Valid mirrorAxis. Valid values are 'X', 'Y', 'Z', '-X', '-Y', '-Z'")

    mNegative = False
    if "-" in mirrorAxis:
        mNegative = True
    mAxis = mirrorAxis.replace("-", "")
    validLimbTypes=("arm", "leg") # // TODO: more will be added
    rootName = rootJoint.name()


    limbType = extra.jointTypeID(rootJoint, limbType)
    print "limbType", limbType
    limbSide = extra.jointSideID(rootJoint, whichSide)
    print "limbSide", limbSide

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

