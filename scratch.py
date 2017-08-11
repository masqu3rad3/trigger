import time
import pymel.core as pm
import extraProcedures as extra
reload(extra)
import contIcons as icon

import pprint

import armClass as arm
reload(arm)
import legClass as leg
reload(leg)
import neckAndHeadClass as neckAndHead
reload(neckAndHead)
import spineClass as spine
reload(spine)
import simpleTailClass as simpleTail
reload(simpleTail)

import pprint

class LimbBuilder():

    def __init__(self):
        # self.catalogueRoots(pm.ls(sl=True)[0])
        self.validRootList = ["Collar", "LegRoot", "Root", "NeckRoot", "FingerRoot", "TailRoot", "FingerRoot", "ThumbRoot", "IndexRoot", "MiddleRoot", "RingRoot", "PinkyRoot"]
        self.limbList = []
        self.hipDistance = 1
        self.shoulderDistance = 1
        self.anchorLocations = []
        self.anchors = []
        self.hipSize = 1.0
        self.chestSize = 1.0
        self.socketDictionary={}


    def startBuilding(self):
        selection = pm.ls(sl=True, type="joint")
        if len(selection) != 1:
            pm.warning("select a single root joint")
            return
        # first initialize the dimensions for icon creation
        self.hipDistance, self.shoulderDistance = self.getDimensions(selection[0])
        # then create the master and placement controllers
        self.createMasters()
        # Create limbs and make connection to the parents
        self.createLimbs(selection[0])

        # Create anchors (spaceswithcers)




    def getDimensions(self, rootNode):
        hipDist = 1
        shoulderDist = 1
        leftHip = None
        rightHip = None
        leftShoulder = None
        rightShoulder = None
        allJoints = pm.listRelatives(rootNode, type="joint", ad=True)
        for j in allJoints:
            jID = extra.identifyMaster(j)

            if jID[0] == "Hip" and jID[2] == "L":
                leftHip = j
            if jID[0] == "Hip" and jID[2] == "R":
                rightHip = j
            if jID[0] == "Shoulder" and jID[2] == "L":
                leftShoulder = j
            if jID[0] == "Shoulder" and jID[2] == "R":
                rightShoulder = j
        if leftHip and rightHip:
            hipDist = extra.getDistance(leftHip, rightHip)
        if leftShoulder and rightShoulder:
            shoulderDist = extra.getDistance(leftShoulder, rightShoulder)
        return hipDist, shoulderDist

    def createMasters(self):
        self.cont_placement = icon.circle("cont_Placement", (self.hipDistance, self.hipDistance, self.hipDistance))
        self.cont_master = icon.triCircle("cont_Master", (self.hipDistance * 1.5, self.hipDistance * 1.5, self.hipDistance * 1.5))
        pm.addAttr(self.cont_master, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True)
        pm.addAttr(self.cont_master, at="bool", ln="Joints_Visibility", sn="jointVis")
        pm.addAttr(self.cont_master, at="bool", ln="Rig_Visibility", sn="rigVis")

        # make the created attributes visible in the channelbox
        pm.setAttr(self.cont_master.contVis, cb=True)
        pm.setAttr(self.cont_master.jointVis, cb=True)
        pm.setAttr(self.cont_master.rigVis, cb=True)
        pm.parent(self.cont_placement, self.cont_master)

        # add these to the anchor locations
        self.anchorLocations.append(self.cont_master)
        self.anchorLocations.append(self.cont_placement)

        # COLOR CODING
        index = 17
        extra.colorize(self.cont_master, index)
        extra.colorize(self.cont_placement, index)

        # # GOOD PARENTING
        self.rootGroup = pm.group(name="tik_autoRig", em=True)
        extra.lockAndHide(self.rootGroup, ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"])
        pm.parent(self.cont_master, self.rootGroup)

    def createLimbs(self, rootNode, connectedLimb=None, isRoot=True):
        limb = None
        if isRoot:
            # print "rootNode", rootNode
            inits, type, side = self.getWholeLimb(rootNode)
            ### LIMB CREATION HERE #####
            if type == "arm":

                if side == "L":
                    self.rightShoulder = inits["Shoulder"]
                if side == "R":
                    self.leftShoulder = inits["Shoulder"]
                limb = arm.arm()
                limb.createArm(inits, suffix=side + "_arm", side=side)
                print limb.limbPlug
                # print "armsokets", limb.sockets
                # self.limbList.append(limb_arm)
                # //TODO: add socket connections

            elif type == "leg":
                if side == "L":
                    self.leftHip = inits["Hip"]
                if side == "R":
                    self.rightHip = inits["Hip"]

                limb = leg.leg()
                limb.createLeg(inits, suffix=side + "_leg", side=side)
                # self.limbList.append(limb_leg)
                # //TODO: add socket connections

            elif type == "neck":
                limb = neckAndHead.neckAndHead()
                limb.createNeckAndHead(inits, suffix="_n")
                # self.limbList.append(limb_neck)
                # //TODO: add socket connections

            elif type == "spine":
                limb = spine.spine()
                limb.createSpine(inits, suffix="_s")  # s for spine...
                # self.limbList.append(limb)
                # update the socketPointDict with the new created values
                # for key in limb_spine.socketDict.keys():
                #     if key in self.socketPointDict.keys():
                #         self.socketPointDict[key] = limb_spine.socketDict.get(key)

            elif type == "tail":
                limb = simpleTail.simpleTail()
                limb.createSimpleTail(inits, suffix="_tail")
                # self.limbList.append(limb)
                # //TODO: add socket connections


            # make the connections while the limb is still hot

            # if not limb:
            #     pm.error("limb cannot be identified")

            if connectedLimb:
                print "%s connects to %s:" %(limb,connectedLimb)
                # ## get the parent initials connection socket
                parentInitial = rootNode.getParent()
                connectionSocket = self.getNearestSocket(parentInitial, connectedLimb.sockets)
                # print "currentLimb", limb
                # print "connectingLimb", connectedLimb
                # print "connectionSocket", connectionSocket
                pm.parent(limb.limbPlug, connectionSocket)


            # if connectedLimb and limb:
            #     print "connects to %s:" %connectedLimb
            #     pm.parent(limb.scaleGrp, self.rootGroup)
            #     pm.parent(limb.nonScaleGrp, self.rootGroup)
            #     if limb.cont_IK_OFF:
            #         pm.parent(limb.cont_IK_OFF, self.rootGroup)
            #         for s in limb.scaleConstraints:
            #             pm.scaleConstraint(self.cont_master, s)
            #     # pm.parent(limb.limbPlug)
            # elif limb:
            #     pm.parent(limb.limbPlug, self.rootGroup)
            #     pm.parent(limb.limbPlug, self.cont_placement)
            #     pm.scaleConstraint(self.cont_master, limb.startSocket)
            #     pm.scaleConstraint(self.cont_master, limb.scaleGrp)


        # Do the same for all children recursively
        children = rootNode.getChildren(type="joint")
        for c in children:
            print "AMNANANANA", c
            cID =  extra.identifyMaster(c)
            if cID[0] in self.validRootList:
                parentLimbomatik=limb
                ## ASSIGN THE NEW CREATED LIMB AS THE
                self.createLimbs(c, connectedLimb=parentLimbomatik, isRoot=True)
            else:
                self.createLimbs(c, isRoot=False)

    def getNearestSocket(self, initJoint, limbSockets):
        # gets the nearest socket of a limb
        distanceList=[]
        for socket in limbSockets:
            distanceList.append(extra.getDistance(socket, initJoint))
        index = distanceList.index(min(distanceList))
        return limbSockets[index]




    ## get all the joint hierarchy and identify them
    def catalogueRoots(self, rootJoint):

        ## get all hierarchy
        allJ = pm.listRelatives(rootJoint, ad=True, type="joint")
        self.allRoots = [rootJoint]
        for j in allJ:
            jID = extra.identifyMaster(j)
            # first collect the roots
            if jID[0] in self.validRootList:
                self.allRoots.append(j)


    def getWholeLimb(self, node):
        limbDict = {}
        multiList = []
        # nodeList = [node]
        limbName, limbType, limbSide = extra.identifyMaster(node)
        limbDict[limbName] = node
        nextNode = node
        z=True
        while z:
            children = nextNode.getChildren(type="joint")
            if len(children) < 1:
                z=False
            failedChildren = 0
            for c in children:
                cID = extra.identifyMaster(c)
                if cID[0] not in self.validRootList and cID[1] == limbType:
                    nextNode = c
                    if cID[0] == "Spine" or cID[0] == "Neck" or cID[0] == "Tail":  ## spine and neck joints are multiple, so put them in a list
                        multiList.append(c)
                        limbDict[cID[0]] = multiList
                    else:
                        limbDict[cID[0]] = c
                else:
                    failedChildren += 1
            if len(children) == failedChildren:
                z=False
        return limbDict, limbType, limbSide

    def getRestOfTheLimb(self, limbRoot):
        # wholeLimb=[limbRoot]
        limbName, limbType, limbSide = extra.identifyMaster(limbRoot)
        allRelatives = pm.listRelatives(limbRoot, ad=True, type="joint")
        limbDict={}
        limbDict[limbName]=limbRoot
        multiList = []
        for i in allRelatives:
            rName, rType, rSide = extra.identifyMaster(i)
            if rType == limbType and rSide == limbSide:
                # while rName in limbDict.keys():
                #     rName+="+"
                if rName == "Spine" or rName == "Neck" or rName == "Tail": ## spine and neck joints are multiple, so put them in a list
                    multiList.append(i)
                    limbDict[rName]=multiList
                else:
                    limbDict[rName]=i
                ## convert it to a dictionary

        return limbDict, limbType, limbSide
    def buildRig(self):
        # first gather all used sockets
        self.getSocketPoints()
        for r in self.allRoots:
            bones, type, side = self.getRestOfTheLimb(r)

            if type == "arm":
                if side == "L":
                    self.rightShoulder = bones["Shoulder"]
                if side == "R":
                    self.leftShoulder = bones["Shoulder"]
                limb_arm = arm.arm()
                limb_arm.createArm(bones, suffix=side + "_arm", side=side)
                self.limbList.append(limb_arm)
                # //TODO: add socket connections

            if type == "leg":
                if side == "L":
                    self.leftHip = bones["Hip"]
                if side == "R":
                    self.rightHip = bones["Hip"]

                limb_leg = leg.leg()
                limb_leg.createLeg(bones, suffix=side + "_leg", side=side)
                self.limbList.append(limb_leg)
                # //TODO: add socket connections

            if type == "neck":
                limb_neck = neckAndHead.neckAndHead()
                limb_neck.createNeckAndHead(bones, suffix="_n")
                self.limbList.append(limb_neck)
                # //TODO: add socket connections

            if type == "spine":
                limb_spine = spine.spine()
                limb_spine.createSpine(bones, suffix="_s")  # s for spine...
                self.limbList.append(limb_spine)
                # update the socketPointDict with the new created values
                for key in limb_spine.socketDict.keys():
                    if key in self.socketPointDict.keys():
                        self.socketPointDict[key]=limb_spine.socketDict.get(key)

            if type == "tail":
                limb_tail = simpleTail.simpleTail()
                limb_tail.createSimpleTail(bones, suffix="_tail")
                self.limbList.append(limb_tail)
                # //TODO: add socket connections

        ## get sizes for controllers
        if self.leftHip and self.rightHip:
            self.hipSize=extra.getDistance(self.leftHip, self.rightHip)

        if self.rightShoulder and self.leftShoulder:
            self.chestSize = extra.getDistance(self.rightShoulder, self.leftShoulder)

        cont_placement = icon.circle("cont_Placement", (self.hipSize, self.hipSize, self.hipSize))
        cont_master = icon.triCircle("cont_Master", (self.hipSize * 1.5, self.hipSize * 1.5, self.hipSize * 1.5))
        pm.addAttr(cont_master, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True)
        pm.addAttr(cont_master, at="bool", ln="Joints_Visibility", sn="jointVis")
        pm.addAttr(cont_master, at="bool", ln="Rig_Visibility", sn="rigVis")

        # make the created attributes visible in the channelbox
        pm.setAttr(cont_master.contVis, cb=True)
        pm.setAttr(cont_master.jointVis, cb=True)
        pm.setAttr(cont_master.rigVis, cb=True)
        pm.parent(cont_placement, cont_master)
        # add these to the anchor locations
        self.anchorLocations.append(cont_master)
        self.anchorLocations.append(cont_placement)
        # COLOR CODING
        index = 17
        extra.colorize(cont_master, index)
        extra.colorize(cont_placement, index)
        ############################

        for limb in self.limbList:
            self.anchorLocations += limb.anchorLocations
            if limb.connectsTo in self.socketPointDict.keys():
                plug=limb.limbPlug
                socket=self.socketPointDict.get(limb.connectsTo)
                print "%s will connect to %s" %(plug, socket)
                pm.parent(plug, socket)
                self.anchors += limb.anchors


        for anchor in list(reversed(self.anchors)):
            extra.spaceSwitcher(anchor[0], self.anchorLocations, mode=anchor[1], defaultVal=anchor[2], listException=anchor[3])
        # # GOOD PARENTING
        rootGroup = pm.group(name="tik_autoRig", em=True)
        extra.lockAndHide(rootGroup, ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"])
        pm.parent(cont_master, rootGroup)


        for i in self.limbList:

            pm.parent(i.scaleGrp, rootGroup)
            pm.parent(i.nonScaleGrp, rootGroup)
            if i.cont_IK_OFF:
                pm.parent(i.cont_IK_OFF, rootGroup)
            if isinstance(i, spine.spine):
                pm.parent(i.startSocket, rootGroup)
                pm.parent(i.cont_body, cont_placement)
                pm.scaleConstraint(cont_master, i.startSocket)
                pm.scaleConstraint(cont_master, i.scaleGrp)
            else:
                for s in i.scaleConstraints:
                    pm.scaleConstraint(cont_master, s)


    def getSocketPoints(self):
        self.socketPointDict={}
        NonValidPlugNames=["Spine", "NeckRoot", "Neck", "Collar", "LegRoot", "ToePv", "HeelPv", "BankIN", "BankOUT", "Knee", "Elbow"]
        for r in self.allRoots:

            bones, type, side = self.getRestOfTheLimb(r)
            bones = self.flatten(bones)

            for b in bones:
                if b not in NonValidPlugNames:
                    bChildren = b.getChildren()
                    for c in bChildren:
                        if c.type() == "joint":
                            cName, cType, cSide = extra.identifyMaster(c)
                            if cName in self.validRootList:
                                if not b in self.socketPointDict.keys():
                                    self.socketPointDict[b]= ""
        return self.socketPointDict

    def flatten(self, d):
        res = []  # Result list
        if isinstance(d, dict):
            for key, val in d.items():
                res.extend(self.flatten(val))
        elif isinstance(d, list):
            res = d
        else:
            res.append(d)
        return res










