import pymel.core as pm
import extraProcedures as extra
import pprint

class limbBuilder():

    spinesList = []
    armsList = []
    legsList = []
    fingersList = []
    tailsList = []

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
        wholeLimb=[limbRoot]
        limbName, limbType, limbSide = extra.identifyMaster(limbRoot)
        allRelatives = pm.listRelatives(limbRoot, ad=True, type="joint")
        for i in allRelatives:
            rName, rType, rSide = extra.identifyMaster(i)
            if rType == limbType and rSide == limbSide:
                wholeLimb.append(i)
        pprint.pprint(wholeLimb)

