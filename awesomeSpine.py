import pymel.core as pm
import extraProcedures as extra
import contIcons as icon

def createSpine(inits, cuts=8, suffix="test", dropoff=2, mode="equalDistance"):
    #     _____ _______ ______ _____    __
    #    / ____|__   __|  ____|  __ \  /_ |
    #   | (___    | |  | |__  | |__) |  | |
    #    \___ \   | |  |  __| |  ___/   | |
    #    ____) |  | |  | |____| |       | |
    #   |_____/   |_|  |______|_|       |_|
    #
    # JOINT CREATION

    ### NEW METHOD

    ## calculate the joint distances:
    distanceList=[]
    totalLength = 0
    for j in range(1,len(inits)): ## skip the first joint
        distance = extra.getDistance(inits[j-1], inits[j])
        totalLength += distance
        distanceList.append(distance)

    ## DONT TOUCH TO THE REF JOINTS

    rootVc = inits[0].getTranslation(space="world")  # Root Vector
    endVc = (rootVc.x, (rootVc.y + totalLength), rootVc.z) # End Vector
    splitVc = endVc - rootVc
    segmentVc = (splitVc / (cuts))
    segmentLoc = rootVc + segmentVc

    pm.select(d=True)

    # Create IK Joints
    curvePoints = []  # for curve creation
    IKjoints = []
    if mode == "equalDistance":

        for i in range(0, cuts + 2):  # iterates one extra to create an additional joint for orientation
            place = rootVc + (segmentVc * (i))
            j = pm.joint(p=place, name="jIK_" + suffix + str(i))
            pm.setAttr(j.displayLocalAxis, 1)
            if i < (cuts + 1):  # if it is not the extra bone, update the lists
                IKjoints.append(j)
                curvePoints.append(place)

    ## TODO : // Will be implemented later
    # elif mode == "sameDistance":
    #     for i in range(0, len(distanceList)):
    #         ctrlVc = splitVc.normal() * distanceList[i]
    #         place = rootVc + (ctrlVc)
    #         j = pm.joint(p=place, name="jIK_" + suffix + str(i), radius=2, o=(0, 90, 0))
    #
    #         # extra.alignTo(j, refJoints[i], 2)
    #
    #         IKjoints.append(j)
    #         curvePoints.append(place)
    else:
        pm.error("Mode is not supported - twistSplineClass.py")

    for j in IKjoints:
        pm.joint(j, e=True, zso=True, oj="xyz", sao="yup")

    # get rid of the extra bone
    deadBone = pm.listRelatives(IKjoints[len(IKjoints) - 1], c=True)
    pm.delete(deadBone)

    BINDjoints = pm.duplicate(IKjoints, name="jDef_%s0" %suffix)



    ## BABY STEPS : FIRST BE SURE THAT IT IS WORKING WITH 2 CONTROL POINTS
    # pm.select(d=True)
    # print "sdf", IKjoints[-1]
    shoulderContJoint = pm.duplicate(IKjoints[-1], name="jCont_Shoulder" + suffix)[0]
    pm.parent(shoulderContJoint, w=True)
    hipsContJoint = pm.duplicate(IKjoints[-1], name="jCont_Hips" + suffix)[0]
    pm.parent(hipsContJoint, w=True)
    extra.alignTo(hipsContJoint,IKjoints[0])
    pm.setAttr(shoulderContJoint.radius, 3)
    pm.setAttr(hipsContJoint.radius, 3)


    #     _____ _______ ______ _____    ___
    #    / ____|__   __|  ____|  __ \  |__ \
    #   | (___    | |  | |__  | |__) |    ) |
    #    \___ \   | |  |  __| |  ___/    / /
    #    ____) |  | |  | |____| |       / /_
    #   |_____/   |_|  |______|_|      |____|
    #
    # IK SOLVERS, POLE VECTORS

    ## create the splineIK for the IK joints
    ### create the spline curve
    splineCurve = pm.curve(name="splineCurve_" + suffix, p=curvePoints)
    splineIK = pm.ikHandle(sol="ikSplineSolver", createCurve=False, c=splineCurve, sj=IKjoints[0], ee=IKjoints[-1], w=1.0)
    ### skin bind control joints
    pm.select(shoulderContJoint)
    pm.select(hipsContJoint, add=True)
    pm.select(splineCurve, add=True)
    pm.skinCluster(dr=dropoff, tsb=True)

    ### Create IK RP Solvers for each binding joint
    RPhandleList = []
    for j in range (len(BINDjoints)-1):
        RP = pm.ikHandle(sj=BINDjoints[j], ee=BINDjoints[j + 1], name="RP_%s_%s" % (i, suffix), sol="ikRPsolver")
        RPhandleList.append(RP[0])

    ### Create locators for pole constraint targets
    poleLocatorList = []
    poleLocatorGrpList = []
    for j in range (len(BINDjoints)-1):
        poleLocator = pm.spaceLocator(name="PoleLoc_%s_%s" % (j, suffix))
        poleLocatorList.append(poleLocator)
        extra.alignTo(poleLocator, BINDjoints[j], 2)
        pm.move(poleLocator,(3,0,0), r=True)
        grp = pm.group(name="PoleLocGrp_%s_%s" % (j, suffix), em=True)
        poleLocatorGrpList.append(grp)
        extra.alignTo(grp, BINDjoints[j],2)
        pm.parent(poleLocator, grp)
    ### Create Pole Vectors
    for id in range (len(RPhandleList)):
        pm.poleVectorConstraint(poleLocatorList[id], RPhandleList[id])
    ### parent the pole groups to the corresponding spine IK joint
    for id in range(len(poleLocatorGrpList)):
        pm.parent(poleLocatorGrpList[id], IKjoints[id])

    #     _____ _______ ______ _____    ____
    #    / ____|__   __|  ____|  __ \  |___ \
    #   | (___    | |  | |__  | |__) |   __) |
    #    \___ \   | |  |  __| |  ___/   |__ <
    #    ____) |  | |  | |____| |       ___) |
    #   |_____/   |_|  |______|_|      |____/
    #
    #

    # connect rotations of locator groups
    for i in range(len(poleLocatorGrpList)):
        blender = pm.createNode("blendTwoAttr", name="tSplineX_blend" + str(i))
        hipsContJoint.rotateX >> blender.input[0]
        shoulderContJoint.rotateX >> blender.input[1]
        blender.output >> poleLocatorGrpList[i].rotateX
        blendRatio = (i + 0.0) / (cuts - 1.0)
        pm.setAttr(blender.attributesBlender, blendRatio)






    #
    #
    # ## Create Controllers
    # ### For now there will be only two controllers - shoulder and hip
    # scaleRatio = (totalLength / 16)
    # cont_Shoulder = icon.cube("cont_splineUP_" + suffix + str(i), (scaleRatio*3, scaleRatio, scaleRatio))
    # extra.alignTo(cont_Shoulder, shoulderContJoint)
    # pm.makeIdentity(cont_Shoulder, a=True)
    # cont_Hips = icon.cube("cont_splineDOWN_" + suffix + str(i), (scaleRatio*3, scaleRatio, scaleRatio))
    # extra.alignTo(cont_Hips, hipsContJoint)
    # pm.makeIdentity(cont_Hips, a=True)
    #
    # ### Create the custom attributes on the hips (Down) controller
    # pm.addAttr(cont_Hips, shortName='preserveVol', longName='Preserve_Volume', defaultValue=0.0,
    #                minValue=0.0,
    #                maxValue=1.0, at="double", k=True)
    # pm.addAttr(cont_Hips, shortName='volumeFactor', longName='Volume_Factor', defaultValue=1, at="double",
    #                k=True)
    #
    # pm.addAttr(cont_Hips, shortName='stretchy', longName='Stretchyness', defaultValue=1, minValue=0.0,
    #                maxValue=1.0,
    #                at="double", k=True)
    #
    # ### Get the info needed for calculation nodes and create them
    # curveInfo = pm.arclen(splineCurve, ch=True)
    # initialLength = pm.getAttr(curveInfo.arcLength)
    # powValue = 0
    #
    # for i in range(0, len(IKjoints)):
    #
    #     curveGlobMult = pm.createNode("multiplyDivide", name="curveGlobMult_" + suffix)
    #     pm.setAttr(curveGlobMult.operation, 2)
    #     boneGlobMult = pm.createNode("multiplyDivide", name="boneGlobMult_" + suffix)
    #
    #     lengthMult = pm.createNode("multiplyDivide", name="length_Multiplier_" + suffix)
    #     pm.setAttr(lengthMult.operation, 2)
    #
    #     volumeSw = pm.createNode("blendColors", name="volumeSw_" + suffix)
    #     stretchSw = pm.createNode("blendTwoAttr", name="stretchSw_" + suffix)
    #
    #     middlePoint = (len(IKjoints) / 2)
    #     volumePow = pm.createNode("multiplyDivide", name="volume_Power_" + suffix)
    #     volumeFactor = pm.createNode("multiplyDivide", name="volume_Factor_" + suffix)
    #     cont_Hips.volumeFactor >> volumeFactor.input1X
    #     cont_Hips.volumeFactor >> volumeFactor.input1Z
    #     volumeFactor.output >> volumePow.input2
    #
    #     pm.setAttr(volumePow.operation, 3)
    #
    #     ## make sure first and last joints preserves the full volume
    #     if i == 0 or i == len(IKjoints) - 1:
    #         pm.setAttr(volumeFactor.input2X, 0)
    #         pm.setAttr(volumeFactor.input2Z, 0)
    #
    #     elif (i <= middlePoint):
    #         powValue = powValue - 1
    #         pm.setAttr(volumeFactor.input2X, powValue)
    #         pm.setAttr(volumeFactor.input2Z, powValue)
    #
    #     else:
    #         powValue = powValue + 1
    #         pm.setAttr(volumeFactor.input2X, powValue)
    #         pm.setAttr(volumeFactor.input2Z, powValue)
    #
    #     curveInfo.arcLength >> curveGlobMult.input1X
    #     pm.setAttr(stretchSw.input[0], initialLength)
    #     curveGlobMult.outputX >> stretchSw.input[1]
    #     cont_Hips.stretchy >> stretchSw.attributesBlender
    #
    #     # self.scaleGrp.sx >> curveGlobMult.input2X
    #     stretchSw.output >> lengthMult.input1X
    #     pm.setAttr(lengthMult.input2X, initialLength)
    #     lengthMult.outputX >> boneGlobMult.input1Y
    #
    #     lengthMult.outputX >> volumePow.input1X
    #     lengthMult.outputX >> volumePow.input1Z
    #     pm.setAttr(volumeSw.color2R, 1)
    #     pm.setAttr(volumeSw.color2B, 1)
    #     volumePow.outputX >> volumeSw.color1R
    #     volumePow.outputX >> volumeSw.color1B
    #     volumeSw.outputR >> boneGlobMult.input1X
    #     volumeSw.outputB >> boneGlobMult.input1Z
    #     # self.scaleGrp.sx >> boneGlobMult.input2X
    #     # self.scaleGrp.sx >> boneGlobMult.input2Y
    #     # self.scaleGrp.sx >> boneGlobMult.input2Z
    #     cont_Hips.preserveVol >> volumeSw.blender
    #
    #     boneGlobMult.output >> IKjoints[i].scale
    #     boneGlobMult.output >> BINDjoints[i].scale