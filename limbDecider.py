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
        shoulderChildren = pm.listRelatives(shoulder, c=True)
        if len(shoulderChildren) == 1:
            upArm = shoulderChildren[0]
            upArmChildren = pm.listRelatives(upArm, c=True)
            if len(upArmChildren) == 1:
                lowArm = upArmChildren[0]
                lowArmChildren = pm.listRelatives(lowArm, c=True)
                if len(lowArmChildren) == 1:
                    lowArmEnd = lowArmChildren[0]
                    # create the Dictionary
                    armInits = {"shoulder": shoulder, "upArm": upArm, "lowArm": lowArm, "lowArmEnd": lowArmEnd}
                else:
                    pm.error(errorMsg)
            else:
                pm.error(errorMsg)
        else:
            pm.error(errorMsg)


    print limbType
    print whichSide
    print armInits["shoulder"]

    # limbRoots = pm.listRelatives(rootJoint, c=True)
    # print limbRoots
    #
    # for i in range (len(limbRoots)):
    #     print limbRoots[i]
