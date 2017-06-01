import pymel.core as pm

import createArms as arm
reload(arm)

import createLegs as leg
reload(leg)

import extraProcedures as extra
reload(extra)

def limbDecider(rootJoint, limbType="auto", whichSide="auto", mirrorAxis="-X"):

    validAxes = ("X", "Y", "Z", "-X", "-Y", "-Z")
    if not mirrorAxis in validAxes:
        pm.error("Not Valid mirrorAxis. Valid values are 'X', 'Y', 'Z', '-X', '-Y', '-Z'")

    mNegative = False
    if "-" in mirrorAxis:
        mNegative = True
    mAxis = mirrorAxis.replace("-", "")
    print "mNegative", "=>", mNegative
    print "mNaxis", "=>", mAxis
    validLimbTypes=("arm", "leg")
    rootName = rootJoint.name()

    # understand the limbType
    if limbType == "auto":
        for i in range (len(validLimbTypes)):
            if validLimbTypes[i] in rootName:
                limbType = validLimbTypes[i]
        if limbType == "auto":
             pm.error("No Matching Limb Type with the joint name. You may try override it by using 'limbType' flag")

    # understand which side is it
    if whichSide == "auto":
        rootP = rootJoint.getTranslation(space="world")
        val=0
        exec("val=rootP."+mAxis.lower())
        print "val", "=?", val
        if val > 0 and mNegative == True:
            whichSide="l"
        else:
            whichSide="r"

    if limbType == "arm":
        # get the necessary ref Joints
        errorMsg="arm joints missing or wrong"
        shoulder = rootJoint
        upArm = (jFoolProof(shoulder))[0]
        lowArm = (jFoolProof(upArm))[0]
        lowArmEnd = (jFoolProof(lowArm))[0]

        armInits = {
            "shoulder": shoulder,
            "upArm": upArm,
            "lowArm": lowArm,
            "lowArmEnd": lowArmEnd
        }
        arm.createArm(armInits, (whichSide+"_arm"), mirrorAxis=mAxis)






def getLegBones(rootNode):
    rCon = rootNode
    rootNodeChildren = pm.listRelatives(rootNode, c=True)
    if jFoolProof(rootNodeChildren):
        rootNodeChildren[0]




def jFoolProof(node, type="joint", limit=1):
    children = pm.listRelatives(node, c=True)
    validChildren=[]
    jCount=0
    for i in children:
        if i.type() == type:
            validChildren.append(i)
            jCount += 1
    if jCount > 0 < limit:
        return validChildren
    else:
        pm.error("joint count does not meet the requirements")

