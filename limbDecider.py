import pymel.core as pm

import createArms as arm
reload(arm)

import createLegs as leg
reload(leg)

import extraProcedures as extra
reload(extra)

def limbDecider(rootJoint, limbType="idByLabel", whichSide="idByLabel", mirrorAxis="X"):
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
    validAxes = ("X", "Y", "Z")
    if not mirrorAxis in validAxes:
        pm.error("Not Valid mirrorAxis. Valid values are 'X', 'Y', 'Z'")

    validLimbTypes=("arm", "leg") # // TODO: more will be added
    rootName = rootJoint.name()

    if limbType == "idByLabel" or "idByName":
        limbID = extra.identifyMaster(rootJoint, idBy=limbType)
        if not "N/A" in limbID:
            # //TODO FIX HERE
    ######################################


    # if this is an arm connection
    if limbType == "Collar" or "arm":
        arm.createArm(getArmBones(rootJoint), suffix=limbSide+"_arm", side=limbSide, mirrorAxis=mirrorAxis)


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


# def getLegBones(rootNode, getType="idByName"):
#     validFootJoints = ["Ball", "HeelPV", "ToePV", "BankIN", "BankOUT"]
#     root = rootNode
#     hip = (jFoolProof(root))[0]
#     knee = (jFoolProof(hip))[0]
#     foot = (jFoolProof(knee))[0]
#     footJoints = jFoolProof(foot, min=5, max=5)
#     if getType == "idByName":
#         for j in footJoints:
#             x = extra.jointTypeID(j, idBy="idByName")
#             if x in validFootJoints:


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

