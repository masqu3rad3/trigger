import pymel.core as pm

import armClass as arm
reload(arm)

import legClass as leg
reload(leg)

import neckAndHeadClass as neckAndHead
reload(neckAndHead)

import extraProcedures as extra
reload(extra)

def limbDecider(rootJoint):


    # Collect all joints connected to the master root
    allJoints = [rootJoint]
    allJoints = allJoints + (pm.listRelatives(rootJoint, ad=True, type="joint"))
    # print allJoints
    limbJoints=[]

    armList=[]
    legList=[]
    neckList=[]
    for j in allJoints:
        limbProperties = extra.identifyMaster(j)
        # If the joint is a collar bone, create an arm there
        if limbProperties[0] == "Collar":
            limb_arm = arm.arm()
            limb_arm.createArm(getArmBones(j), suffix=limbProperties[2]+"_arm", side=limbProperties[2])
            armList.append(limb_arm)
            # arm.createArm(getArmBones(j), suffix=limbProperties[2]+"_arm", side=limbProperties[2])
        if limbProperties[0] == "LegRoot":
            limb_leg = leg.leg()
            limb_leg.createLeg(getLegBones(j), suffix=limbProperties[2]+"_leg", side=limbProperties[2])
            legList.append(limb_leg)
        if limbProperties[0] == "Neck":
            limb_neck = neckAndHead.neckAndHead()
            limb_neck.createNeckAndHead(getNeckAndHeadBones(j), suffix="_n")
            neckList.append(limb_neck)
        if limbProperties[0] == "Root":
            pass

        ## //TODO : Make Spine Class

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
    # validFootJoints = ["Ball", "HeelPV", "ToePV", "BankIN", "BankOUT"]
    root = rootNode
    hip = (jFoolProof(root))[0]
    knee = (jFoolProof(hip))[0]
    foot = (jFoolProof(knee))[0]
    footJoints = jFoolProof(foot, min=5, max=5)
    for j in footJoints:
        jID = extra.identifyMaster(j)
        if jID[0] == "Ball":
            ball = j
        elif jID[0] == "HeelPV":
            heelPV = j
        elif jID[0] == "ToePV":
            toePV = j
        elif jID[0] == "BankIN":
            bankIN = j
        elif jID[0] == "BankOUT":
            bankOUT = j
        else:
            pm.error("Problem getting Foot reference joints")
    legInits = {
        "LegRoot": root,
        "Hip": hip,
        "Knee": knee,
        "Foot": foot,
        "Ball": ball,
        "HeelPV": heelPV,
        "ToePV": toePV,
        "BankIN": bankIN,
        "BankOUT": bankOUT
    }
    return legInits

def getNeckAndHeadBones(rootNode):
    neck = rootNode
    head = (jFoolProof(neck))[0]
    rest = (jFoolProof(head, min=2, max=2))
    for j in rest:
        jID = extra.identifyMaster(j)
        if jID[0] == "Jaw":
            jaw =j
            jawEnd = jFoolProof(j)[0]
        if jID[0] == "Head":
            headEnd = j
    neckAndHeadInits = {
        "Neck": neck,
        "Head": head,
        "HeadEnd": headEnd,
        "Jaw": jaw,
        "JawEnd": jawEnd
    }
    return neckAndHeadInits

def getSpineBones(rootNode):
    spineRoot = rootNode
    spineNodes = []
    spineNodes.append(rootNode)
    firstSpine = jFoolProof(rootNode, min=1, max=100)[0]
    testSpine = firstSpine
    while testSpine != None:
        spineNodes.append(testSpine)
        testSpine = jFoolProof(testSpine)
    return spineNodes
    # return spineRoot+spineNodes


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
        return None
        # pm.error("joint count does not meet the requirements")

