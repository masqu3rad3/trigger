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
    limbList = []
    validRootList = ["Collar", "LegRoot", "Root", "NeckRoot", "FingerRoot", "TailRoot", "FingerRoot", "ThumbRoot", "IndexRoot", "MiddleRoot", "RingRoot", "PinkyRoot"]
    bindingDictionary = {}
    def __init__(self):
        self.catalogueRoots(pm.ls(sl=True)[0])
        self.leftHip = None
        self.rightHip = None
        self.rightShoulder = None
        self.leftShoulder = None
        self.anchorLocations = []
        self.anchors = []
        self.hipSize = 1.0
        self.chestSize = 1.0
        self.socketDictionary={}

    def create(self, rootNode, connectedLimb=None, isRoot=True):

        # inits = None
        if isRoot:
            # print hedeHot
            inits, type, side = self.getWholeLimb(rootNode)
            # print inits
            print "inits", inits
            print "type", type

            ### LIMB CREATION HERE #####
            if type == "arm":
                if side == "L":
                    self.rightShoulder = inits["Shoulder"]
                if side == "R":
                    self.leftShoulder = inits["Shoulder"]
                limb_arm = arm.arm()
                limb_arm.createArm(inits, suffix=side + "_arm", side=side)
                # self.limbList.append(limb_arm)
                # //TODO: add socket connections

            if type == "leg":
                if side == "L":
                    self.leftHip = inits["Hip"]
                if side == "R":
                    self.rightHip = inits["Hip"]

                limb_leg = leg.leg()
                limb_leg.createLeg(inits, suffix=side + "_leg", side=side)
                # self.limbList.append(limb_leg)
                # //TODO: add socket connections

            if type == "neck":
                limb_neck = neckAndHead.neckAndHead()
                limb_neck.createNeckAndHead(inits, suffix="_n")
                # self.limbList.append(limb_neck)
                # //TODO: add socket connections

            if type == "spine":
                limb_spine = spine.spine()
                limb_spine.createSpine(inits, suffix="_s")  # s for spine...
                self.limbList.append(limb_spine)
                # update the socketPointDict with the new created values
                # for key in limb_spine.socketDict.keys():
                #     if key in self.socketPointDict.keys():
                #         self.socketPointDict[key] = limb_spine.socketDict.get(key)

            if type == "tail":
                limb_tail = simpleTail.simpleTail()
                limb_tail.createSimpleTail(inits, suffix="_tail")
                self.limbList.append(limb_tail)
                # //TODO: add socket connections

            # make the connections while the limb is still hot

            if connectedLimb:
                print "connects to %s:" %connectedLimb



        # Do the same for all children recursively
        children = rootNode.getChildren(type="joint")
        for c in children:
            cID =  extra.identifyMaster(c)
            if cID[0] in self.validRootList:
                limb="hedehot"+rootNode
                ## ASSIGN THE NEW CREATED LIMB AS THE
                self.create(c, connectedLimb=limb, isRoot=True)
            else:
                self.create(c, isRoot=False)


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
                    # print c
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
                pm.parent(i.rootSocket, rootGroup)
                pm.parent(i.cont_body, cont_placement)
                pm.scaleConstraint(cont_master, i.rootSocket)
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
                            # print "here", c
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










