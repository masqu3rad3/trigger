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

class limbBuilder():
    limbList = []
    validRootList = ["Collar", "LegRoot", "Root", "NeckRoot", "FingerRoot", "TailRoot"]
    bindingDictionary = {}
    def __init__(self):
        self.catalogueRoots(pm.ls(sl=True)[0])

    ## get all the joint hierarchy and identify them
    def catalogueRoots(self, rootJoint):
        # validRootList = ["Collar", "LegRoot", "Root", "NeckRoot", "FingerRoot", "TailRoot"]
        ## get all hierarchy
        allJ = pm.listRelatives(rootJoint, ad=True, type="joint")
        self.allRoots = [rootJoint]
        for j in allJ:
            jID = extra.identifyMaster(j)
            # first collect the roots
            if jID[0] in self.validRootList:
                self.allRoots.append(j)

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
                # wholeLimb.append(i)
        return limbDict, limbType, limbSide
    def buildRig(self):
        # first gather all used sockets
        self.getSocketPoints()
        for r in self.allRoots:
            bones, type, side = self.getRestOfTheLimb(r)

            if type == "arm":
                limb_arm = arm.arm()
                limb_arm.createArm(bones, suffix=side + "_arm", side=side)
                self.limbList.append(limb_arm)
                # //TODO: add socket connections

            if type == "leg":
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

        for limb in self.limbList:
            if limb.connectsTo in self.socketPointDict.keys():
                plug=limb.limbPlug
                socket=self.socketPointDict.get(limb.connectsTo)
                print "%s will connect to %s" %(plug, socket)
                pm.parent(plug, socket)

    def getSocketPoints(self):
        self.socketPointDict={}
        NonValidPlugNames=["Spine", "NeckRoot", "Neck", "Collar", "LegRoot", "ToePv", "HeelPv", "BankIN", "BankOUT"]
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
        # pprint.pprint(self.plugPointDict)
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
            ## raise TypeError("Undefined type for flatten: %s" % type(d))

        return res










