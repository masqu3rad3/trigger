import pymel.core as pm

import createArms as arm
reload(arm)

import createLegs as leg
reload(leg)

import extraProcedures as extra
reload(extra)

def limbDecider(rootJoint):

    if rootJoint.type() != "joint":
        pm.error("Root node must be a Joint")

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
            leg.createLeg(getLegBones(j), suffix=limbProperties[2] + "_leg", side=limbProperties[2])



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

