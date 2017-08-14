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

import fingersClass as finger
reload(finger)

import pprint

class LimbBuilder():

    def __init__(self):
        # self.catalogueRoots(pm.ls(sl=True)[0])
        self.validRootList = ["Collar", "LegRoot", "Root", "NeckRoot", "FingerRoot", "TailRoot", "FingerRoot", "ThumbRoot", "IndexRoot", "MiddleRoot", "RingRoot", "PinkyRoot"]
        # self.limbList = []
        self.hipDistance = 1
        self.shoulderDistance = 1
        self.anchorLocations = []
        self.anchors = []
        self.hipSize = 1.0
        self.chestSize = 1.0
        # self.socketDictionary={}
        self.allSocketsList=[]
        self.limbCreationList = []
        self.riggedLimbList = []


    def startBuilding(self):
        selection = pm.ls(sl=True, type="joint")
        if len(selection) != 1:
            pm.warning("select a single root joint")
            return
        # first initialize the dimensions for icon creation
        self.hipDistance, self.shoulderDistance = self.getDimensions(selection[0])

        self.getLimbProperties(selection[0])

        self.createMasters()
        # Create limbs and make connection to the parents
        self.createLimbs(self.limbCreationList)

        # print "anchorLocs", self.anchorLocations
        # print "anchors", self.anchors
        # Create anchors (spaceswithcers)
        #
        # for anchor in (self.anchors):
        #     extra.spaceSwitcher(anchor[0], self.anchorLocations, mode=anchor[1], defaultVal=anchor[2], listException=anchor[3])




    def getDimensions(self, rootNode):
        """
        Collects all the joints under the rootNode hierarchy calculates necessary cross-limb distances for scale size
        Args:
            rootNode: (pymel node) All the hiearchy under this will be collected

        Returns:(tuple) (hipsDistance, shoulderDistance)

        """
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

    def getLimbProperties(self, node, isRoot=True, parentIndex=None):
        """
        Checks the given nodes entire hieararchy for roots, and catalogues the root nodes into dictionaries.
        Returns: (List) [{limbDictionary}, LimbType, LimbSide]

        """

        if isRoot:
            limbDict = self.getWholeLimb(node)
            limbDict.append(parentIndex)
            self.limbCreationList.append(limbDict)
            # self.limbCreationList.append([inits])

        # Do the same for all children recursively
        children = node.getChildren(type="joint")
        for c in children:
            cID =  extra.identifyMaster(c)
            if cID[0] in self.validRootList:
                ## ASSIGN THE NEW CREATED LIMB AS THE
                self.getLimbProperties(c, isRoot=True, parentIndex=node)
            else:
                self.getLimbProperties(c, isRoot=False)


    def createMasters(self):
        """
        This method creates master controllers (Placement and Master)
        Returns: None

        """
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

    def createLimbs(self, limbCreationList):
        """
        Creates limb with the order defined in the limbCreationList (which created with getLimbProperties)
        Args:
            limbCreationList:

        Returns:

        """
        for x in limbCreationList:
            # limb = None
            ### LIMB CREATION HERE #####
            if x[1] == "arm":
                if x[2] == "L":
                    self.rightShoulder = x[0]["Shoulder"]
                if x[2] == "R":
                    self.leftShoulder = x[0]["Shoulder"]
                limb = arm.arm()
                limb.createArm(x[0], suffix=x[2] + "_arm", side=x[2])

            elif x[1] == "leg":
                if x[2] == "L":
                    self.leftHip = x[0]["Hip"]
                if x[2] == "R":
                    self.rightHip = x[0]["Hip"]

                limb = leg.leg()
                limb.createLeg(x[0], suffix=x[2] + "_leg", side=x[2])

            elif x[1] == "neck":
                limb = neckAndHead.neckAndHead()
                limb.createNeckAndHead(x[0], suffix="_n")

            elif x[1] == "spine":
                limb = spine.spine()
                limb.createSpine(x[0], suffix="_s")  # s for spine...

            elif x[1] == "tail":
                limb = simpleTail.simpleTail()
                limb.createSimpleTail(x[0], suffix="_tail")

            elif x[1] == "finger":
                print x[0]
                limb = finger.Fingers()
                limb.createFinger(x[0], suffix=x[2] + "_finger")

            else:
                pm.error("limb creation failed.")
                return

            self.riggedLimbList.append(limb)
            self.anchorLocations += limb.anchorLocations
            self.anchors += limb.anchors

            ## gather all sockets in a list
            self.allSocketsList += limb.sockets

            ## add the rigged limb to the riggedLimbList
            self.riggedLimbList.append(limb)

            parentInitJoint=x[3]
            #
            print "parentInitJoint:", parentInitJoint
            if parentInitJoint:
                parentSocket = self.getNearestSocket(parentInitJoint, self.allSocketsList)
                print "parentSocket", parentSocket
                pm.parent(limb.limbPlug, parentSocket)


    def getNearestSocket(self, initJoint, limbSockets):
        """
        searches through limbSockets list and gets the nearest socket to the initJoint.
        Args:
            initJoint: (pymel object) initial joint to test the distance
            limbSockets: (list) limbSockets list

        Returns:

        """
        distanceList=[]
        for socket in limbSockets:
            distanceList.append(extra.getDistance(socket, initJoint))
        index = distanceList.index(min(distanceList))
        return limbSockets[index]

    # def catalogueRoots(self, rootJoint):
    #
    #     ## get all hierarchy
    #     allJ = pm.listRelatives(rootJoint, ad=True, type="joint")
    #     self.allRoots = [rootJoint]
    #     for j in allJ:
    #         jID = extra.identifyMaster(j)
    #         # first collect the roots
    #         if jID[0] in self.validRootList:
    #             self.allRoots.append(j)
    #

    def getWholeLimb(self, node):
        limbDict = {}
        multiList = []
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
                    if cID[0] == "Spine" or cID[0] == "Neck" or cID[0] == "Tail" or cID[1] == "finger":  ## spine and neck joints are multiple, so put them in a list
                        multiList.append(c)
                        limbDict[cID[0]] = multiList
                    else:
                        limbDict[cID[0]] = c
                else:
                    failedChildren += 1
            if len(children) == failedChildren:
                z=False
        return [limbDict, limbType, limbSide]

    # def getRestOfTheLimb(self, limbRoot):
    #     # wholeLimb=[limbRoot]
    #     limbName, limbType, limbSide = extra.identifyMaster(limbRoot)
    #     allRelatives = pm.listRelatives(limbRoot, ad=True, type="joint")
    #     limbDict={}
    #     limbDict[limbName]=limbRoot
    #     multiList = []
    #     for i in allRelatives:
    #         rName, rType, rSide = extra.identifyMaster(i)
    #         if rType == limbType and rSide == limbSide:
    #             # while rName in limbDict.keys():
    #             #     rName+="+"
    #             if rName == "Spine" or rName == "Neck" or rName == "Tail": ## spine and neck joints are multiple, so put them in a list
    #                 multiList.append(i)
    #                 limbDict[rName]=multiList
    #             else:
    #                 limbDict[rName]=i
    #             ## convert it to a dictionary
    #
    #     return limbDict, limbType, limbSide
    # def buildRig(self):
    #     # first gather all used sockets
    #     self.getSocketPoints()
    #     for r in self.allRoots:
    #         bones, type, side = self.getRestOfTheLimb(r)
    #
    #         if type == "arm":
    #             if side == "L":
    #                 self.rightShoulder = bones["Shoulder"]
    #             if side == "R":
    #                 self.leftShoulder = bones["Shoulder"]
    #             limb_arm = arm.arm()
    #             limb_arm.createArm(bones, suffix=side + "_arm", side=side)
    #             self.limbList.append(limb_arm)
    #             # //TODO: add socket connections
    #
    #         if type == "leg":
    #             if side == "L":
    #                 self.leftHip = bones["Hip"]
    #             if side == "R":
    #                 self.rightHip = bones["Hip"]
    #
    #             limb_leg = leg.leg()
    #             limb_leg.createLeg(bones, suffix=side + "_leg", side=side)
    #             self.limbList.append(limb_leg)
    #             # //TODO: add socket connections
    #
    #         if type == "neck":
    #             limb_neck = neckAndHead.neckAndHead()
    #             limb_neck.createNeckAndHead(bones, suffix="_n")
    #             self.limbList.append(limb_neck)
    #             # //TODO: add socket connections
    #
    #         if type == "spine":
    #             limb_spine = spine.spine()
    #             limb_spine.createSpine(bones, suffix="_s")  # s for spine...
    #             self.limbList.append(limb_spine)
    #             # update the socketPointDict with the new created values
    #             for key in limb_spine.socketDict.keys():
    #                 if key in self.socketPointDict.keys():
    #                     self.socketPointDict[key]=limb_spine.socketDict.get(key)
    #
    #         if type == "tail":
    #             limb_tail = simpleTail.simpleTail()
    #             limb_tail.createSimpleTail(bones, suffix="_tail")
    #             self.limbList.append(limb_tail)
    #             # //TODO: add socket connections
    #
    #     ## get sizes for controllers
    #     if self.leftHip and self.rightHip:
    #         self.hipSize=extra.getDistance(self.leftHip, self.rightHip)
    #
    #     if self.rightShoulder and self.leftShoulder:
    #         self.chestSize = extra.getDistance(self.rightShoulder, self.leftShoulder)
    #
    #     cont_placement = icon.circle("cont_Placement", (self.hipSize, self.hipSize, self.hipSize))
    #     cont_master = icon.triCircle("cont_Master", (self.hipSize * 1.5, self.hipSize * 1.5, self.hipSize * 1.5))
    #     pm.addAttr(cont_master, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True)
    #     pm.addAttr(cont_master, at="bool", ln="Joints_Visibility", sn="jointVis")
    #     pm.addAttr(cont_master, at="bool", ln="Rig_Visibility", sn="rigVis")
    #
    #     # make the created attributes visible in the channelbox
    #     pm.setAttr(cont_master.contVis, cb=True)
    #     pm.setAttr(cont_master.jointVis, cb=True)
    #     pm.setAttr(cont_master.rigVis, cb=True)
    #     pm.parent(cont_placement, cont_master)
    #     # add these to the anchor locations
    #     self.anchorLocations.append(cont_master)
    #     self.anchorLocations.append(cont_placement)
    #     # COLOR CODING
    #     index = 17
    #     extra.colorize(cont_master, index)
    #     extra.colorize(cont_placement, index)
    #     ############################
    #
    #     for limb in self.limbList:
    #         self.anchorLocations += limb.anchorLocations
    #         if limb.connectsTo in self.socketPointDict.keys():
    #             plug=limb.limbPlug
    #             socket=self.socketPointDict.get(limb.connectsTo)
    #             print "%s will connect to %s" %(plug, socket)
    #             pm.parent(plug, socket)
    #             self.anchors += limb.anchors
    #
    #
    #     for anchor in list(reversed(self.anchors)):
    #         extra.spaceSwitcher(anchor[0], self.anchorLocations, mode=anchor[1], defaultVal=anchor[2], listException=anchor[3])
    #     # # GOOD PARENTING
    #     rootGroup = pm.group(name="tik_autoRig", em=True)
    #     extra.lockAndHide(rootGroup, ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"])
    #     pm.parent(cont_master, rootGroup)
    #
    #
    #     for i in self.limbList:
    #
    #         pm.parent(i.scaleGrp, rootGroup)
    #         pm.parent(i.nonScaleGrp, rootGroup)
    #         if i.cont_IK_OFF:
    #             pm.parent(i.cont_IK_OFF, rootGroup)
    #         if isinstance(i, spine.spine):
    #             pm.parent(i.startSocket, rootGroup)
    #             pm.parent(i.cont_body, cont_placement)
    #             pm.scaleConstraint(cont_master, i.startSocket)
    #             pm.scaleConstraint(cont_master, i.scaleGrp)
    #         else:
    #             for s in i.scaleConstraints:
    #                 pm.scaleConstraint(cont_master, s)
    #

    # def getSocketPoints(self):
    #     self.socketPointDict={}
    #     NonValidPlugNames=["Spine", "NeckRoot", "Neck", "Collar", "LegRoot", "ToePv", "HeelPv", "BankIN", "BankOUT", "Knee", "Elbow"]
    #     for r in self.allRoots:
    #
    #         bones, type, side = self.getRestOfTheLimb(r)
    #         bones = self.flatten(bones)
    #
    #         for b in bones:
    #             if b not in NonValidPlugNames:
    #                 bChildren = b.getChildren()
    #                 for c in bChildren:
    #                     if c.type() == "joint":
    #                         cName, cType, cSide = extra.identifyMaster(c)
    #                         if cName in self.validRootList:
    #                             if not b in self.socketPointDict.keys():
    #                                 self.socketPointDict[b]= ""
    #     return self.socketPointDict

    # def flatten(self, d):
    #     res = []  # Result list
    #     if isinstance(d, dict):
    #         for key, val in d.items():
    #             res.extend(self.flatten(val))
    #     elif isinstance(d, list):
    #         res = d
    #     else:
    #         res.append(d)
    #     return res
    #









