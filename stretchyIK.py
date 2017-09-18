import pymel.core as pm
import maya.mel as mel
import extraProcedures as extra
import contIcons as icon

def createStretchyIK(nodeList, suffix = "strIK", solver="ikSCsolver", controllerNode=None):
    """
    Nodelist must contain all the joints. Not only the first one and the last one.
    Args:
        nodeList: (List) list of joint which the IK will be build on.
        suffix: (String) A unique suffix for naming the nodes and joints. Optional, default is "strIK"
        solver: (String) Valid solvers are ikRPsolver, ikSCSolver and ikSpringSolver. Default is ikSCsolver

    Returns: None

    """
    if not controllerNode:
        ## get the controller icon scale:
        contScale = extra.getDistance(nodeList[-1], nodeList[-2])
        controllerNode = icon.circle(name="cont_"+suffix, scale=(contScale,contScale,contScale))
        extra.alignTo(controllerNode, nodeList[-1])
        controllerNode_ORE = extra.createUpGrp(controllerNode,"ORE")

    ## Create the custom attributes on the controller Node
    pm.select(controllerNode)
    pm.addAttr(shortName="squash", longName="Squash", defaultValue=0.0, minValue=0.0, maxValue=1.0, at="double", k=True)
    pm.addAttr(shortName="stretch", longName="Stretch", defaultValue=100.0, minValue=0.0, maxValue=100.0, at="double",
               k=True)

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

    nearMultList = []
    for j in range(1, len(nodeList)):  ## skip the first joint
        # Create a clamp node for stretchLimit
        stretchClamp = pm.createNode("clamp", name="stretchClamp%s_%s" %(j, suffix))
        stretchClamp.outputR >> nodeList[j].translateX
        # Create a clamp offset to negate initial length
        clampOffset = pm.createNode("plusMinusAverage", name="clampOffset%s_%s" %(j, suffix))
        clampOffset.output1D >> stretchClamp.maxR
        # Create the near multiplier
        nearMult_n = pm.createNode("multiplyDivide", name="nearMult%s_%s" % (j, suffix))
        nearMult_n.input1X >> clampOffset.input1D[0]
        nearMult_n.outputX >> stretchClamp.inputR

        controllerNode.stretch >> clampOffset.input1D[1]
        nearMultList.append(nearMult_n)

    ## Create the squashBlend
    squashBlend = pm.createNode("blendTwoAttr", name="squashBlend_" + suffix)
    controllerNode.squash >> squashBlend.attributesBlender
    for node in nearMultList:
        squashBlend.output >> node.input2X

    ### Create the condition Node
    condition_n = pm.createNode("condition", name="condition_n_" + suffix)
    pm.setAttr(condition_n + ".operation", 2) ## set the boolean operator to "Greater"
    condition_n.outColorR >> squashBlend.input[0]
    ## Create a Divide Node to calculate stretch ratio
    stretchRatio_n = pm.createNode("multiplyDivide", name="stretchRatio_" + suffix)
    pm.setAttr(stretchRatio_n + ".operation", 2) ## make the operation "divide"
    stretchRatio_n.outputX >> condition_n.colorIfTrueR
    stretchRatio_n.outputX >> squashBlend.input[1]

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
