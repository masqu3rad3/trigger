import pymel.core as pm
import maya.mel as mel
import extraProcedures as extra

def createStretchyIK(nodeList, suffix = "strIK", solver="ikSCsolver"):
    """
    Nodelist must contain all the joints. Not only the first one and the last one.
    Args:
        nodeList: (List) list of joint which the IK will be build on.
        suffix: (String) A unique suffix for naming the nodes and joints. Optional, default is "strIK"
        solver: (String) Valid solvers are ikRPsolver, ikSCSolver and ikSpringSolver. Default is ikSCsolver

    Returns: None

    """

    ### Create and constrain Distance Locators

    startNode = nodeList[0]
    endNode = nodeList[-1]

    ## calculate the joint distances:
    distanceList=[]
    for j in range(1,len(nodeList)): ## skip the first joint
        distance = extra.getDistance(nodeList[j-1], nodeList[j])
        distanceList.append(distance)

    ### these joints will move the system
    pm.select(d=True)
    startJo = pm.joint(p=startNode.getTranslation(space="world"), name="startJo_" + suffix, radius=4)
    pm.select(d=True)
    endJo = pm.joint(p=endNode.getTranslation(space="world"), name="endJo_" + suffix, radius=4)
    ### constrain the existing joints to the new created control joints
    pm.parentConstraint(startJo, startNode, mo=True)

    if solver == "ikSpringSolver":
        mel.eval("ikSpringSolver;")

    ### create the ikHandle
    ikHandle = pm.ikHandle(sj=startNode, ee=endNode, name="ikHandle_" + suffix, sol=solver)
    # ikHandle = pm.ikHandle(sj=startNode, ee=endNode, name="ikHandle_" + suffix, sol="ikRPsolver")

    #
    pm.parentConstraint(endJo, ikHandle[0], mo=True)




    ## node creation starts from the nearest one to the joints
    ## Create nearMult nodes. No multipler for the first one, cause it is fixed
    nearMultList=[]
    for j in range(1,len(nodeList)): ## skip the first joint
        # print "hede", nodeList[j]
        nearMult_n = pm.createNode("multiplyDivide", name="nearMult%s_%s" %(j,suffix))
        nearMult_n.outputX >> nodeList[j].translateX
        nearMultList.append(nearMult_n)

    ### Create the condition Node
    condition_n = pm.createNode("condition", name="condition_n_" + suffix)
    pm.setAttr(condition_n + ".operation", 2) ## set the boolean operator to "Greater"
    for node in nearMultList:
        condition_n.outColorR >> node.input2X

    ## Create a Divide Node to calculate stretch ratio
    stretchRatio_n = pm.createNode("multiplyDivide", name="stretchRatio_" + suffix)
    pm.setAttr(stretchRatio_n + ".operation", 2) ## make the operation "divide"
    stretchRatio_n.outputX >> condition_n.colorIfTrueR

    ### create a plusMinusAverage node which will give the sum of total joint lengths in total
    totalLengthSum_n = pm.createNode("plusMinusAverage", name="totalLengthSum_" + suffix)
    totalLengthSum_n.output1D >> stretchRatio_n.input2X
    totalLengthSum_n.output1D >> condition_n.secondTerm

    ### Create a distance locator which will calculate the runtime distance constantly
    distanceBW_n = pm.createNode("distanceBetween", name="distanceBW_" + suffix)

    distanceBW_n.distance >> stretchRatio_n.input1X
    distanceBW_n.distance >> condition_n.firstTerm

    ### create locators for measurement
    startMeasure = pm.spaceLocator(name="startMeasure_" + suffix)
    pm.pointConstraint(startJo, startMeasure, mo=False)

    endMeasure = pm.spaceLocator(name="endMeasure_" + suffix)
    pm.pointConstraint(endJo, endMeasure, mo=False)

    startMeasure.translate >> distanceBW_n.point1
    endMeasure.translate >> distanceBW_n.point2

    ### Create a multiply node for each joint "WHICH WILL SCALE"
    ### These multiply nodes will hold the initial lengths of the joints
    ### By "WHICH WILL SCALE" I mean dont do that for the start joint, cause its x translate will stay fixed.
    initLengthMultList=[]
    for j in range(1,len(nodeList)): ## skip the first joint

        initLengthMult_n = pm.createNode("multiplyDivide", name="initLengthMult%s_%s" %(j,suffix))
        pm.setAttr(initLengthMult_n + ".input1X", distanceList[j-1])
        # and connect it to the next slot in plus node
        initLengthMult_n.outputX >> totalLengthSum_n.input1D[j-1]
        initLengthMult_n.outputX >> nearMultList[j-1].input1X
        initLengthMultList.append(initLengthMult_n)




    # totalDistance = 0
    # for j in range (len(nodeList)-1):
    #     distance = extra.getDistance(nodeList[j], nodeList[j+1])
    #     totalDistance += distance

    ### Create Nodes and Connections for Strethchy IK SC

    # stretchOffset = pm.createNode("plusMinusAverage", name="stretchOffset_" + suffix)
    # distance_SC = pm.createNode("distanceBetween", name="distance_SC_" + suffix)
    # IK_stretch_distanceClamp = pm.createNode("clamp", name="IK_stretch_distanceClamp" + suffix)
    # IK_stretch_stretchynessClamp = pm.createNode("clamp", name="IK_stretch_stretchynessClamp" + suffix)
    # extraScaleMult_SC = pm.createNode("multiplyDivide", name="extraScaleMult_SC" + suffix)
    # initialDivide_SC = pm.createNode("multiplyDivide", name="initialDivide_SC_" + suffix)
    # initialLengthMultip_SC = pm.createNode("multiplyDivide", name="initialLengthMultip_SC_" + suffix)
    # stretchAmount_SC = pm.createNode("multiplyDivide", name="stretchAmount_SC_" + suffix)
    # sumOfJLengths_SC = pm.createNode("plusMinusAverage", name="sumOfJLengths_SC_" + suffix)
    # stretchCondition_SC = pm.createNode("condition", name="stretchCondition_SC_" + suffix)
    # squashyness_SC = pm.createNode("blendColors", name="squashyness_SC_" + suffix)
    # stretchyness_SC = pm.createNode("blendColors", name="stretchyness_SC_" + suffix)
    # #
    # pm.setAttr(IK_stretch_stretchynessClamp + ".maxR", 1)
    # #
    # ### set the initial distances
    # #
    # pm.setAttr(initialLengthMultip_SC + ".input1X", totalDistance/2)
    # pm.setAttr(initialLengthMultip_SC + ".input1Y", totalDistance/2)
    # #
    # pm.setAttr(initialDivide_SC + ".operation", 2)
    # pm.setAttr(stretchCondition_SC + ".operation", 2)
    #
    # ### Bind Attributes and make constraints
    #
    # # Bind Stretch Attributes
    # startLoc.translate >> distance_SC.point1
    # endLoc.translate >> distance_SC.point2
    # distance_SC.distance >> IK_stretch_distanceClamp.inputR
    # #
    # IK_stretch_distanceClamp.outputR >> stretchCondition_SC.firstTerm
    # IK_stretch_distanceClamp.outputR >> initialDivide_SC.input1X
    # IK_stretch_stretchynessClamp.outputR >> stretchyness_SC.blender
    # #
    # initialDivide_SC.outputX >> stretchAmount_SC.input2X
    # initialDivide_SC.outputX >> stretchAmount_SC.input2Y
    # #
    # initialLengthMultip_SC.outputX >> extraScaleMult_SC.input1X
    # initialLengthMultip_SC.outputY >> extraScaleMult_SC.input1Y
    # initialLengthMultip_SC.outputX >> stretchOffset.input1D[0]
    # initialLengthMultip_SC.outputY >> stretchOffset.input1D[1]
    # #
    # extraScaleMult_SC.outputX >> stretchAmount_SC.input1X
    # extraScaleMult_SC.outputY >> stretchAmount_SC.input1Y
    # extraScaleMult_SC.outputX >> stretchyness_SC.color2R
    # extraScaleMult_SC.outputY >> stretchyness_SC.color2G
    # extraScaleMult_SC.outputX >> stretchCondition_SC.colorIfFalseR
    # extraScaleMult_SC.outputY >> stretchCondition_SC.colorIfFalseG
    # extraScaleMult_SC.outputX >> sumOfJLengths_SC.input1D[0]
    # extraScaleMult_SC.outputY >> sumOfJLengths_SC.input1D[1]
    # #
    # stretchAmount_SC.outputX >> squashyness_SC.color1R
    # stretchAmount_SC.outputY >> squashyness_SC.color1G
    # stretchAmount_SC.outputX >> stretchCondition_SC.colorIfTrueR
    # stretchAmount_SC.outputY >> stretchCondition_SC.colorIfTrueG
    # sumOfJLengths_SC.output1D >> initialDivide_SC.input2X
    # sumOfJLengths_SC.output1D >> stretchCondition_SC.secondTerm
    # stretchCondition_SC.outColorR >> squashyness_SC.color2R
    # stretchCondition_SC.outColorG >> squashyness_SC.color2G
    # squashyness_SC.outputR >> stretchyness_SC.color1R
    # squashyness_SC.outputG >> stretchyness_SC.color1G
    # stretchyness_SC.outputR >> nodeList[-2].translateX
    # stretchyness_SC.outputG >> nodeList[-1].translateX

    #
    # self.cont_IK_foot.rotate >> jIK_RP_End.rotate
    #
    # # Stretch Attributes Controller connections
    #
    # self.cont_IK_foot.sUpLeg >> extraScaleMult_SC.input2X
    # self.cont_IK_foot.sLowLeg >> extraScaleMult_SC.input2Y
    # self.cont_IK_foot.squash >> squashyness_SC.blender
    #
    # stretchOffset.output1D >> IK_stretch_distanceClamp.maxR
    # self.cont_IK_foot.stretch >> IK_stretch_stretchynessClamp.inputR
    # self.cont_IK_foot.stretch >> stretchOffset.input1D[2]
    #
    # # Bind Foot Attributes to the controller
    # self.cont_IK_foot.bLean >> Pv_BallLean.rotateY
    # self.cont_IK_foot.bRoll >> Pv_BallRoll.rotateX
    # self.cont_IK_foot.bSpin >> Pv_BallSpin.rotateY
    # self.cont_IK_foot.hRoll >> Pv_Heel.rotateX
    # self.cont_IK_foot.hSpin >> Pv_Heel.rotateY
    # self.cont_IK_foot.tRoll >> Pv_Toe.rotateX
    # self.cont_IK_foot.tSpin >> Pv_Toe.rotateY
    # self.cont_IK_foot.tWiggle >> Pv_Ball.rotateX
    # # // TODO: Reduction possible
    # pm.select(Pv_BankOut)
    # pm.setDrivenKeyframe(cd=self.cont_IK_foot.bank, at="rotateZ", dv=0, v=0)
    # pm.setDrivenKeyframe(cd=self.cont_IK_foot.bank, at="rotateZ", dv=-90, v=90)
    # pm.select(Pv_BankIn)
    # pm.setDrivenKeyframe(cd=self.cont_IK_foot.bank, at="rotateZ", dv=0, v=0)
    # pm.setDrivenKeyframe(cd=self.cont_IK_foot.bank, at="rotateZ", dv=90, v=-90)
    #
    # IK_parentGRP = pm.group(name="IK_parentGRP_" + suffix, em=True)
    # extra.alignTo(IK_parentGRP, footRef, 0)
    # pm.parent(Pv_BankIn, IK_parentGRP)
    # pm.parent(jIK_Foot, IK_parentGRP)
    #
    # pm.parentConstraint(jIK_SC_End, jIK_Foot)
    #
    # pm.parentConstraint(self.cont_IK_foot, IK_parentGRP, mo=True)
    #
    # # Create Orig Switch (Pole Vector On/Off)
    #
    # blendORE_IK_root = pm.createNode("blendColors", name="blendORE_IK_root_" + suffix)
    # jIK_SC_Root.rotate >> blendORE_IK_root.color2
    # jIK_RP_Root.rotate >> blendORE_IK_root.color1
    # blendORE_IK_root.output >> jIK_orig_Root.rotate
    # self.cont_IK_foot.polevector >> blendORE_IK_root.blender
    #
    # blendPOS_IK_root = pm.createNode("blendColors", name="blendPOS_IK_root_" + suffix)
    # jIK_SC_Root.translate >> blendPOS_IK_root.color2
    # jIK_RP_Root.translate >> blendPOS_IK_root.color1
    # blendPOS_IK_root.output >> jIK_orig_Root.translate
    # self.cont_IK_foot.polevector >> blendPOS_IK_root.blender
    #
    # blendORE_IK_knee = pm.createNode("blendColors", name="blendORE_IK_knee_" + suffix)
    # jIK_SC_Knee.rotate >> blendORE_IK_knee.color2
    # jIK_RP_Knee.rotate >> blendORE_IK_knee.color1
    # blendORE_IK_knee.output >> jIK_orig_Knee.rotate
    # self.cont_IK_foot.polevector >> blendORE_IK_knee.blender
    #
    # blendPOS_IK_knee = pm.createNode("blendColors", name="blendPOS_IK_knee_" + suffix)
    # jIK_SC_Knee.translate >> blendPOS_IK_knee.color2
    # jIK_RP_Knee.translate >> blendPOS_IK_knee.color1
    # blendPOS_IK_knee.output >> jIK_orig_Knee.translate
    # self.cont_IK_foot.polevector >> blendPOS_IK_knee.blender
    #
    # blendORE_IK_end = pm.createNode("blendColors", name="blendORE_IK_end_" + suffix)
    # jIK_SC_End.rotate >> blendORE_IK_end.color2
    # jIK_RP_End.rotate >> blendORE_IK_end.color1
    # blendORE_IK_end.output >> jIK_orig_End.rotate
    # self.cont_IK_foot.polevector >> blendORE_IK_end.blender
    #
    # blendPOS_IK_end = pm.createNode("blendColors", name="blendPOS_IK_end_" + suffix)
    # jIK_SC_End.translate >> blendPOS_IK_end.color2
    # jIK_RP_End.translate >> blendPOS_IK_end.color1
    # blendPOS_IK_end.output >> jIK_orig_End.translate
    # self.cont_IK_foot.polevector >> blendPOS_IK_end.blender
    #
    # poleVector_Rvs = pm.createNode("reverse", name="poleVector_Rvs_" + suffix)
    # self.cont_IK_foot.polevector >> poleVector_Rvs.inputX
    #
    # self.cont_IK_foot.polevector >> self.cont_Pole.v
    #
    # ### Create Tigh Controller
    #
    # thighContScale = initUpperLegDist / 4
    # cont_Thigh = pm.curve(name="cont_Thigh" + suffix, d=1,
    #                       p=[(-1, 1, 1), (-1, 1, -1), (1, 1, -1), (1, 1, 1), (-1, 1, 1), (-1, -1, 1), (-1, -1, -1),
    #                          (-1, 1, -1), (-1, 1, 1), (-1, -1, 1), (1, -1, 1), (1, 1, 1), (1, 1, -1), (1, -1, -1),
    #                          (1, -1, 1), (1, -1, -1), (-1, -1, -1)],
    #                       k=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16])
    # pm.setAttr(cont_Thigh.scale, (thighContScale, thighContScale / 4, thighContScale))
    # pm.makeIdentity(cont_Thigh, a=True)
    #
    # cont_Thigh_OFF = extra.createUpGrp(cont_Thigh, "OFF")
    # cont_Thigh_ORE = extra.createUpGrp(cont_Thigh, "ORE")
    # if side == "R":
    #     # pm.setAttr("%s.scale%s" % (cont_Thigh_ORE, mirrorAxis), -1)
    #     pm.setAttr("%s.rotate%s" % (cont_Thigh_ORE, mirrorAxis), -180)
    #     # pm.setAttr(cont_Thigh_ORE.rotateX, -180)
    #
    # pm.addAttr(shortName="autoTwist", longName="Auto_Twist", defaultValue=1.0, minValue=0.0, maxValue=1.0, at="float",
    #            k=True)
    # pm.addAttr(shortName="manualTwist", longName="Manual_Twist", defaultValue=0.0, at="float", k=True)
    #
    # extra.alignTo(cont_Thigh_OFF, hipRef, 0)
    #
    # pm.move(cont_Thigh, (0, thighContScale * 2, 0), r=True)
    # temp_AimCon = pm.aimConstraint(hipRef, cont_Thigh, o=(0, 0, 0))
    # pm.delete(temp_AimCon)
    # pm.makeIdentity(cont_Thigh, a=True)
    # pm.xform(cont_Thigh, piv=legRootPos, ws=True)
    # pm.makeIdentity(cont_Thigh, a=True, t=True, r=False, s=True)
    # pm.parentConstraint(cont_Thigh, jDef_legRoot, mo=True, st=("x", "y", "z"))
    # pm.pointConstraint(cont_Thigh, jDef_hip, mo=True)