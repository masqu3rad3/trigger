import pymel.core as pm
import extraProcedures as extra
reload(extra)
import contIcons as icon

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

class LimbBuilder():

    def __init__(self):
        # self.catalogueRoots(pm.ls(sl=True)[0])
        self.validRootList = ["Collar", "LegRoot", "Root", "NeckRoot", "TailRoot", "FingerRoot", "ThumbRoot", "IndexRoot", "MiddleRoot", "RingRoot", "PinkyRoot"]
        # self.limbList = []
        self.fingerMatchList = []
        self.fingerMatchConts = []
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
        self.projectName = "tikAutoRig"
        self.rootGroup = None
        self.spineRes = 4
        self.neckRes = 3
        # self.spineDropoff = 2.0
        # self.neckDropoff = 2.0
        # self.createAnchors = True

    def startBuilding(self, createAnchors=False):
        # self.__init__()


        selection = pm.ls(sl=True, type="joint")
        if len(selection) != 1 or extra.identifyMaster(selection[0])[0] not in self.validRootList :
            pm.warning("select a single root joint")
            return

        ## Create the holder group if it does not exist
        if not pm.objExists("{0}_rig".format(self.projectName)):
            self.rootGroup = pm.group(name=("{0}_rig".format(self.projectName)), em=True)
        else:
            self.rootGroup = pm.PyNode("{0}_rig".format(self.projectName))

        # first initialize the dimensions for icon creation
        self.hipDistance, self.shoulderDistance = self.getDimensions(selection[0])
        self.getLimbProperties(selection[0])
        self.createMasters()
        # Create limbs and make connection to the parents
        self.createLimbs(self.limbCreationList)

        # Create anchors (spaceswithcers)
        if createAnchors:
            for anchor in (self.anchors):
                extra.spaceSwitcher(anchor[0], self.anchorLocations, mode=anchor[1], defaultVal=anchor[2], listException=anchor[3])

        for x in self.fingerMatchConts:
            contPos = extra.createUpGrp(x[0], "POS", mi=False)
            socket = self.getNearestSocket(x[1],self.allSocketsList)
            pm.parentConstraint(socket, contPos, mo=True)
            pm.scaleConstraint(self.cont_master, contPos)
            pm.parent(contPos, self.rootGroup)


    def addLimb(self):
        selection = pm.ls(sl=True)
        if len(selection) > 3:
            pm.error("Select exactly three nodes. First reference root node then target parent and finally master controller")
            return
        referenceRoot = selection[0]
        parentSocket = selection[1]
        masterController = selection[2]
        if extra.identifyMaster(referenceRoot)[0] not in self.validRootList:
            pm.error("First selection must be a valid root joint node")
            return
        limbProperties = self.getWholeLimb(referenceRoot)

        if limbProperties[1] == "arm":
            limb = arm.arm()
            limb.createArm(limbProperties[0], suffix="%s_arm" % limbProperties[2], side=limbProperties[2])

        elif limbProperties[1] == "leg":
            limb = leg.leg()
            limb.createLeg(limbProperties[0], suffix="%s_leg" % limbProperties[2], side=limbProperties[2])

        elif limbProperties[1] == "neck":
            limb = neckAndHead.neckAndHead()
            limb.createNeckAndHead(limbProperties[0], suffix="n", resolution=limbProperties[0]["resolution"], dropoff=limbProperties[0]["dropoff"])

        elif limbProperties[1] == "spine":
            limb = spine.spine()
            limb.createSpine(limbProperties[0], suffix="s", resolution=limbProperties[0]["resolution"], dropoff=limbProperties[0]["dropoff"])  # s for spine...

        elif limbProperties[1] == "tail":
            limb = simpleTail.simpleTail()
            limb.createSimpleTail(limbProperties[0], suffix="tail")

        elif limbProperties[1] == "finger":
            limb = finger.Fingers()
            limb.createFinger(limbProperties[0], suffix="%s_finger" % limbProperties[2])

        else:
            pm.error("limb creation failed.")
            return

        pm.parent(limb.limbPlug, parentSocket)

        ## Good parenting / scale connections
        ## Create the holder group if it does not exist
        if not pm.objExists("{0}_rig".format(self.projectName)):
            self.rootGroup = pm.group(name=("{0}_rig".format(self.projectName)),em=True)
        else:
            self.rootGroup = pm.PyNode("{0}_rig".format(self.projectName))

        pm.parent(limb.scaleGrp, self.rootGroup)
        scaleGrpPiv = limb.limbPlug.getTranslation(space="world")
        pm.xform(limb.scaleGrp, piv=scaleGrpPiv, ws=True)
        ## pass the attributes

        extra.attrPass(limb.scaleGrp, masterController, values=True, daisyChain=True, overrideEx=False)

        if limb.nonScaleGrp:
            pm.parent(limb.nonScaleGrp, self.rootGroup)
        if limb.cont_IK_OFF:
            pm.parent(limb.cont_IK_OFF, self.rootGroup)
        for sCon in limb.scaleConstraints:
            pm.scaleConstraint(masterController, sCon)


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
        allFingers = []
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
            ## collect fingers

            # allFingerParents = []
            validFingerRoots = ["FingerRoot", "ThumbRoot", "IndexRoot", "MiddleRoot", "RingRoot", "PinkyRoot"]
            if jID[0] in validFingerRoots:
                allFingers.append(j)
                # if j.getParent():
                #     allFingerParents.append(j.getParent())
        if leftHip and rightHip:
            hipDist = extra.getDistance(leftHip, rightHip)
        if leftShoulder and rightShoulder:
            shoulderDist = extra.getDistance(leftShoulder, rightShoulder)

        self.fingerMatchList = []
        for x in allFingers:
            tempGrp = []
            for y in allFingers:
                if x.getParent() == y.getParent():
                    tempGrp.append(y)
            if len(tempGrp) > 0 and tempGrp not in self.fingerMatchList:
                self.fingerMatchList.append(tempGrp)

        return hipDist, shoulderDist

    def getLimbProperties(self, node, isRoot=True, parentIndex=None):
        """
        Checks the given nodes entire hieararchy for roots, and catalogues the root nodes into dictionaries.
        
        isRoot: if True, the given joint is considered as true. Default is True. For recursion.
        parentIndex: indicates the parent of the current node. Default is none. For recursion.
        
        Returns: None (Updates limbCreationList attribute of the parent class)

        """

        if isRoot:
            limbProps = self.getWholeLimb(node)
            limbProps.append(parentIndex)
            self.limbCreationList.append(limbProps)

        # Do the same for all children recursively
        children = node.getChildren(type="joint")
        for c in children:
            cID =  extra.identifyMaster(c)
            if cID[0] in self.validRootList:
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

######### //TODO WIP
        for f in self.fingerMatchList:
            fName, fType, fSide = extra.identifyMaster(f[0])
            # print "parentCheck", f[0].getParent()
            offsetVector = extra.getBetweenVector(f[0].getParent(),f)
            iconSize = extra.getDistance(f[0], f[-1])
            translateOff = (iconSize / 2, 0, iconSize / 2)
            rotateOff=(0,0,0)
            if "_left" in f[0].name():
                iconName = f[0].name().replace("_left", "_LEFT")
            elif "_right" in f[0].name():
                iconName = f[0].name().replace("_right", "_RIGHT")
                rotateOff = (0, 180, 0)
                translateOff = (iconSize / 2, 0, -iconSize / 2)
            else:
                iconName = f[0].name()


            cont_fGroup = icon.square(name="cont_Fgrp_{0}".format(iconName), scale=(iconSize/6, iconSize/4, iconSize/2))
            pm.rotate(cont_fGroup, (90,0,0))
            pm.makeIdentity(cont_fGroup, a=True)
            extra.alignAndAim(cont_fGroup, targetList=[f[0].getParent()], aimTargetList= [f[0], f[-1]], upObject=f[0], rotateOff=rotateOff, translateOff=(-offsetVector * (iconSize/2)))
            pm.move(cont_fGroup, (0,0,(-iconSize / 2)),r=True,os=True)


            # tempPA = pm.parentConstraint(f, cont_fGroup)
            # pm.delete(tempPA)
            # pm.move(cont_fGroup, (0,iconSize/2,0), r=True)
            # pm.makeIdentity(cont_fGroup, a=True)
            self.fingerMatchConts.append([cont_fGroup, f[0].getParent()])


        # make the created attributes visible in the channelbox
        pm.setAttr(self.cont_master.contVis, cb=True)
        pm.setAttr(self.cont_master.jointVis, cb=True)
        pm.setAttr(self.cont_master.rigVis, cb=True)
        pm.parent(self.cont_placement, self.cont_master)

        # self.masterSocket = pm.joint(name="jSocket_master", pt=self.cont_placement)
        # pm.parentConstraint(self.cont_placement, masterSocket)
        # # add these to the anchor locations
        self.anchorLocations.append(self.cont_master)
        self.anchorLocations.append(self.cont_placement)

        # COLOR CODING
        index = 17
        extra.colorize(self.cont_master, index)
        extra.colorize(self.cont_placement, index)



        # # GOOD PARENTING

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
            if x[2] == "R":
                sideVal = "_RIGHT_"
            elif x[2] == "L":
                sideVal = "_LEFT_"
            else:
                sideVal = "c"

            # limb = None
            ### LIMB CREATION HERE #####
            if x[1] == "arm":
                if x[2] == "L":
                    self.rightShoulder = x[0]["Shoulder"]
                if x[2] == "R":
                    self.leftShoulder = x[0]["Shoulder"]
                limb = arm.arm()
                limb.createArm(x[0], suffix="%s_arm" %sideVal, side=x[2])

            elif x[1] == "leg":
                if x[2] == "L":
                    self.leftHip = x[0]["Hip"]
                if x[2] == "R":
                    self.rightHip = x[0]["Hip"]

                limb = leg.leg()
                limb.createLeg(x[0], suffix="%s_leg" %sideVal, side=x[2])

            elif x[1] == "neck":
                limb = neckAndHead.neckAndHead()
                # limb.createNeckAndHead(x[0], suffix="n", resolution=x[3], dropoff=x[4])
                limb.createNeckAndHead(x[0], suffix="n", resolution=x[0]["resolution"], dropoff=x[0]["dropoff"])

            elif x[1] == "spine":
                limb = spine.spine()
                # limb.createSpine(x[0], suffix="s", resolution=x[3], dropoff=x[4])  # s for spine...
                limb.createSpine(x[0], suffix="s", resolution=x[0]["resolution"], dropoff=x[0]["dropoff"])  # s for spine...


            elif x[1] == "tail":
                limb = simpleTail.simpleTail()
                limb.createSimpleTail(x[0], suffix="tail")

            elif x[1] == "finger":

                parentController = None
                for matching in self.fingerMatchList:
                    for f in matching:
                        if f in x[0].values():
                            index = self.fingerMatchList.index(matching)
                            parentController = self.fingerMatchConts[index][0]

                limb = finger.Fingers()
                limb.createFinger(x[0], suffix=sideVal, side=x[2], parentController=parentController)

            else:
                pm.error("limb creation failed.")
                return

            # self.riggedLimbList.append(limb)
            self.anchorLocations += limb.anchorLocations
            self.anchors += limb.anchors

            ## gather all sockets in a list
            self.allSocketsList += limb.sockets

            ## add the rigged limb to the riggedLimbList
            self.riggedLimbList.append(limb)

            parentInitJoint=x[3]
            #


            if parentInitJoint:
                parentSocket = self.getNearestSocket(parentInitJoint, self.allSocketsList, excluding=limb.sockets)

            else:
                parentSocket = self.cont_placement

            pm.parent(limb.limbPlug, parentSocket)

            ## Good parenting / scale connections
            pm.parent(limb.scaleGrp, self.rootGroup)
            scaleGrpPiv = limb.limbPlug.getTranslation(space="world")
            pm.xform(limb.scaleGrp, piv=scaleGrpPiv, ws=True)
            ## pass the attributes

            extra.attrPass(limb.scaleGrp, self.cont_master, values=True, daisyChain=True, overrideEx=False)

            if limb.nonScaleGrp:
                pm.parent(limb.nonScaleGrp, self.rootGroup)
            if limb.cont_IK_OFF:
                pm.parent(limb.cont_IK_OFF, self.rootGroup)
            for sCon in limb.scaleConstraints:
                pm.scaleConstraint(self.cont_master, sCon)


    def getNearestSocket(self, initJoint, limbSockets, excluding=[]):
        """
        searches through limbSockets list and gets the nearest socket to the initJoint.
        Args:
            initJoint: (pymel object) initial joint to test the distance
            limbSockets: (list) limbSockets list

        Returns:

        """
        distanceList=[]
        for socket in limbSockets:
            if not socket in excluding:
                distanceList.append(extra.getDistance(socket, initJoint))
        index = distanceList.index(min(distanceList))
        return limbSockets[index]

    def getWholeLimb(self, node):
        limbDict = {}
        multiList = []
        segments = None
        dropoff = None
        limbName, limbType, limbSide = extra.identifyMaster(node)
        if limbType == "spine" or limbType == "neck":
            limbDict["resolution"] = pm.getAttr(node.resolution)
            limbDict["dropoff"] = pm.getAttr(node.dropoff)
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
        # return [limbDict, limbType, limbSide, segments, dropoff]
        return [limbDict, limbType, limbSide]




