import time
import pymel.core as pm
import extraProcedures as extra
import contIcons as icon

import pprint

import armClass as arm
reload(arm)
import legClass as leg
import neckAndHeadClass as neckAndHead
reload(neckAndHead)
import spineClass as spine
reload(spine)
import simpleTailClass as simpleTail

class limbBuilder():
    limbList = []

    def __init__(self):
        self.catalogueRoots(pm.ls(sl=True)[0])

    ## get all the joint hierarchy and identify them
    def catalogueRoots(self, rootJoint):
        validRootList = ["Collar", "LegRoot", "Root", "NeckRoot", "FingerRoot", "TailRoot"]
        ## get all hierarchy
        allJ = pm.listRelatives(rootJoint, ad=True, type="joint")
        self.allRoots = [rootJoint]
        for j in allJ:
            jID = extra.identifyMaster(j)
            # first collect the roots
            if jID[0] in validRootList:
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
                if rName == "Spine" or rName == "Neck": ## spine and neck joints are multiple, so put them in a list
                    multiList.append(i)
                    limbDict[rName]=multiList
                else:
                    limbDict[rName]=i
                ## convert it to a dictionary
                # wholeLimb.append(i)
        return limbDict, limbType, limbSide
    def buildRig(self):
        for r in self.allRoots:
            bones, type, side = self.getRestOfTheLimb(r)

            # pprint.pprint(bones)
            ## parse the dictionary to a regular list

            if type == "arm":
                limb_arm = arm.arm()
                limb_arm.createArm(bones, suffix=side + "_arm", side=side)
                self.limbList.append(limb_arm)

            if type == "leg":
                limb_leg = leg.leg()
                limb_leg.createLeg(bones, suffix=side + "_leg", side=side)
                self.limbList.append(limb_leg)

            if type == "neck":
                limb_neck = neckAndHead.neckAndHead()
                limb_neck.createNeckAndHead(bones, suffix="_n")
                self.limbList.append(limb_neck)

            if type == "spine":
                limb_spine = spine.spine()
                limb_spine.createSpine(bones, suffix="_s")  # s for spine...
                self.limbList.append(limb_spine)

            if type == "tail":
                limb_tail = simpleTail.simpleTail()
                limb_tail.createSimpleTail(bones, suffix="_tail")
                self.limbList.append(limb_tail)






