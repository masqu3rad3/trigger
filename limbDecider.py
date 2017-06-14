import pymel.core as pm

import armClass as arm
reload(arm)

import legClass as leg
reload(leg)

import neckAndHeadClass as neckAndHead
reload(neckAndHead)

import spineClass as spine
reload(spine)

import extraProcedures as extra
reload(extra)

import contIcons as icon

def limbDecider(rootJoint):


    # Collect all joints connected to the master root
    allJoints = [rootJoint]
    allJoints = allJoints + (pm.listRelatives(rootJoint, ad=True, type="joint"))
    # print allJoints



    limbJoints=[]

    armList=[]
    legList=[]
    neckList=[]
    spineList=[]
    limbList=[]
    rightHip = None
    leftHip = None
    for j in allJoints:
        limbProperties = extra.identifyMaster(j)

        # Get the HipSize
        # get the Right Hip

        if limbProperties[0] == "Hip" and limbProperties[2] == "R":
            rightHip = j
        # get the Left Hip
        if limbProperties[0] == "Hip" and limbProperties[2] == "L":
            leftHip = j


        ## If the joint is a collar bone, create an arm there
        if limbProperties[0] == "Collar":
            limb_arm = arm.arm()
            limb_arm.createArm(getArmBones(j), suffix=limbProperties[2]+"_arm", side=limbProperties[2])
            limbList.append(limb_arm)
            print limb_arm.connectsTo
            # arm.createArm(getArmBones(j), suffix=limbProperties[2]+"_arm", side=limbProperties[2])
        if limbProperties[0] == "LegRoot":
            limb_leg = leg.leg()
            limb_leg.createLeg(getLegBones(j), suffix=limbProperties[2]+"_leg", side=limbProperties[2])
            limbList.append(limb_leg)
            print limb_leg.connectsTo

        if limbProperties[0] == "Neck":
            limb_neck = neckAndHead.neckAndHead()
            limb_neck.createNeckAndHead(getNeckAndHeadBones(j), suffix="_n")
            limbList.append(limb_neck)
            print limb_neck.connectsTo

        if limbProperties[0] == "Root":
            # print getSpineBones(j)
            limb_spine = spine.spine()
            limb_spine.createSpine(getSpineBones(j), suffix="_s") # s for spine...
            spineList.append(limb_spine)

    # # Create the master and placement Controllers

    if rightHip != None and leftHip != None:
        hipSize = extra.getDistance(rightHip, leftHip)
    else:
        hipSize = 1
    cont_placement = icon.circle("cont_Placement", (hipSize, hipSize, hipSize))
    cont_master = icon.triCircle("cont_Master", (hipSize * 1.5, hipSize * 1.5, hipSize * 1.5))
    pm.addAttr(cont_master, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True)
    pm.addAttr(cont_master, at="bool", ln="Joints_Visibility", sn="jointVis")
    pm.addAttr(cont_master, at="bool", ln="Rig_Visibility", sn="rigVis")
    # make the created attributes visible in the channelbox
    pm.setAttr(cont_master.contVis, cb=True)
    pm.setAttr(cont_master.jointVis, cb=True)
    pm.setAttr(cont_master.rigVis, cb=True)
    pm.parent(cont_placement, cont_master)

    # print "limbList", limbList
    # print "sCons", limbList[0].scaleConstraints
    # if there is a spine...
    for sp in spineList:
        # Connect the plugs
        for limb in limbList:
            print "limbConnects", limb.connectsTo
            if limb.connectsTo == "Spine":  # this limb is gonna connected to the chest area
                # parent the plug to the chest socket
                pm.parent(limb.limbPlug, sp.chestSocket)

            if limb.connectsTo == "Root":  # this limb is gonna connected to the root
                # parent the plug to the root socket
                pm.parent(limb.limbPlug, sp.rootSocket)
                # print limb_spine.connectsTo
            for s in limb.scaleConstraints:
                pm.scaleConstraint(cont_master, s)
            # pass the attributes
            extra.attrPass(limb.scaleGrp, cont_master, values=True, daisyChain=True, overrideEx=False)
            print limb.anchors
            ## //TODO : WRITE A FUNCTION TO CREATE ANCHOR SWITCHES FOR EVERY ANCHOR IN EVERY LIMB TO OTHER ANCHOR POINTS EXCEPT ITSELF




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

    ## get the first Spine after root
    rootChildren = jFoolProof(rootNode, min=1, max=1000)
    firstSpine = [j for j in rootChildren if extra.identifyMaster(j)[0] == "Spine"]
    testSpine = firstSpine
    while len(testSpine) == 1:
        spineNodes.append(testSpine[0])
        testSpine = jFoolProof(testSpine, min=1, max=100)

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

