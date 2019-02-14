import pymel.core as pm
import extraProcedures as extra
reload(extra)
import contIcons as icon
reload(icon)
import armClass as arm
# import armClass_state1 as arm
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
import tentacleClass as tentacle
reload(tentacle)
import rootClass as root
reload(root)
import anchorMaker
reload(anchorMaker)

# from Qt import QtWidgets, QtCore, QtGui
from Qt import QtWidgets

# if Qt.__binding__ == "PySide":
#     from shiboken import wrapInstance
#     from Qt.QtCore import Signal
# elif Qt.__binding__.startswith('PyQt'):
#     from sip import wrapinstance as wrapInstance
#     from Qt.Core import pyqtSignal as Signal
# else:
#     from shiboken2 import wrapInstance
#     from Qt.QtCore import Signal

class LimbBuilder():

    def __init__(self, settingsData, progressBar=None):
        # super(LimbBuilder, self).__init__()
        self.progressBar=progressBar
        # self.catalogueRoots(pm.ls(sl=True)[0])
        self.validRootList = ["Collar", "LegRoot", "Root", "SpineRoot", "NeckRoot", "TailRoot", "FingerRoot", "ThumbRoot", "IndexRoot", "MiddleRoot", "RingRoot", "PinkyRoot", "TentacleRoot"]
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
        self.rigName = "tikAutoRig"
        self.rootGroup = None
        self.skinMeshList = None
        self.copySkinWeights = False
        self.replaceExisting = False
        self.totalDefJoints = []
        # self.spineRes = 4
        # self.neckRes = 3
        # self.spineDropoff = 2.0
        # self.neckDropoff = 2.0
        # self.createAnchors = True
        self.parseSettings(settingsData)
        if self.progressBar:
            self.progressBar.setProperty("value", 0)
        self.bindMethod=0
        self.skinMethod=0


    def parseSettings(self, settingsData):

        self.afterCreation = settingsData["afterCreation"]
        self.seperateSelectionSets = settingsData["seperateSelectionSets"]

        # self.rigName = settingsData["rigName"]
        self.majorLeftColor = settingsData["majorLeftColor"]
        self.minorLeftColor = settingsData["minorLeftColor"]
        self.majorRightColor = settingsData["majorRightColor"]
        self.minorRightColor = settingsData["minorRightColor"]
        self.majorCenterColor = settingsData["majorCenterColor"]
        self.minorCenterColor = settingsData["minorCenterColor"]

    def startBuilding(self, createAnchors=False):
        """
        Main method for rig creation. Using the other methods it builds the rig, make the connections.
        This is the first and final step at rig creation.
        Args:
            createAnchors: (Bool) If true, it attempts to build the anchors based on the limb settings.
                            Default: False

        Returns: None

        """
        # self.__init__()


        selection = pm.ls(sl=True, type="joint")
        if len(selection) != 1 or extra.identifyMaster(selection[0])[0] not in self.validRootList :
            pm.warning("select a single root joint")
            return

        # ## Create the holder group if it does not exist
        # if not pm.objExists("{0}_rig".format(self.rigName)):
        #     self.rootGroup = pm.group(name=("{0}_rig".format(self.rigName)), em=True)
        #     # self.allOldCont = []
        # else:
        #     self.rootGroup = pm.PyNode("{0}_rig".format(self.rigName))
        #     # get all controllers under the existing group into a list
        #     # allTransform = pm.listRelatives(self.rootGroup, ad=True, c=True, typ="nurbsCurve")
        #     # self.allOldCont = extra.uniqueList([cont.getParent() for cont in allTransform if cont.name().startswith("cont_")])
        try:
            oldRootGroup = pm.PyNode("{0}_rig".format(self.rigName))
        except:
            oldRootGroup = None

        self.rootGroup = pm.group(name=(extra.uniqueName("{0}_rig".format(self.rigName))), em=True)

        # first initialize the dimensions for icon creation
        self.hipDistance, self.shoulderDistance = self.getDimensions(selection[0])
        self.getLimbProperties(selection[0])
        self.createMasters()
        # Create limbs and make connection to the parents
        self.createlimbs(self.limbCreationList)

        # Create anchors (spaceswithcers)
        if createAnchors:
            for anchor in (self.anchors):
                # extra.spaceSwitcher(anchor[0], self.anchorLocations, mode=anchor[1], defaultVal=anchor[2], listException=anchor[3])
                anchorMaker.spaceSwitcher(anchor[0], self.anchorLocations, mode=anchor[1], defaultVal=anchor[2],
                                          listException=anchor[3])

        else:
            for anchor in (self.anchors):
                try:
                    pm.parent(anchor[0], self.cont_placement)
                except RuntimeError:
                    pass
        for x in self.fingerMatchConts:
            contPos = extra.createUpGrp(x[0], "POS", mi=False)
            socket = self.getNearestSocket(x[1], self.allSocketsList)
            pm.parentConstraint(socket, contPos, mo=True)
            pm.scaleConstraint(self.cont_master, contPos)
            pm.parent(contPos, self.rootGroup)

        if self.afterCreation == 1:
            # if the After Creation set to 'Hide Initial Joints'
            pm.hide(selection)
        if self.afterCreation == 2:
            # if the After Creation set to 'Delete Initial Joints'
            pm.delete(selection)
        if self.skinMeshList:
            # if there are skin mesh(s) defined, initiate the skinning process
            self.skinning(copyMode=self.copySkinWeights)
            pass

        replace = True
        if replace and oldRootGroup:
            # get every controller under the oldRootGroup
            # find corresponding new controllers and replace them with the old ones
            # find old skinned meshes
            # duplicate them
            # copy skin weights to new ones
            pass

    def skinning(self, copyMode):
        if copyMode:
            # print "copyskins"
            # print self.totalDefJoints
            for i in self.skinMeshList:
                dupMesh = pm.duplicate(i)
                pm.skinCluster(self.totalDefJoints, dupMesh, tsb=True)
                pm.copySkinWeights(i, dupMesh, noMirror=True, surfaceAssociation="closestPoint",
                                   influenceAssociation="closestJoint", normalize=True)

        else:
            # print "dont copy, only initial skinning"
            # print self.totalDefJoints
            for i in self.skinMeshList:
                pm.skinCluster(self.totalDefJoints, i, tsb=True, bindMethod=self.bindMethod, skinMethod=self.skinMethod)


    def createlimbs(self, limbCreationList=[], addLimb=False, *args, **kwargs):
        """
        Creates limb with the order defined in the limbCreationList (which created with getLimbProperties)
        Args:
            limbCreationList: (List) The list of initial limb roots for creation
            addLimb: (Boolean) If True, it adds the first node in the selection list to the rig. Default False. 
                        The selection order must be with this order:
                        initial Limb root => parent joint of the existing rig => master controller of the existing rig (for the extra attributes
                         and global scaling)
            seperateSelectionSets: (Boolean) if True, i

        Returns: None

        """

        if addLimb:
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
            limbCreationList = [self.getWholeLimb(referenceRoot)]

        j_def_set = None

        if not self.seperateSelectionSets:
            print "limbCreationList", limbCreationList
            pm.select(d=True)
            if not pm.uniqueObjExists("def_jointsSet_%s" % self.rigName):
                j_def_set = pm.sets(name="def_jointsSet_%s" % self.rigName)
            else:
                j_def_set = pm.PyNode("def_jointsSet_%s" % self.rigName)


        total_limb_count = len(limbCreationList)
        limb_counter = 0
        percent = (100 * limb_counter)/total_limb_count
        for x in limbCreationList:
            if self.progressBar:
                limb_counter = limb_counter+1
                percent = (100 * limb_counter) / total_limb_count
                self.progressBar.setProperty("value", percent)
                QtWidgets.QApplication.processEvents()

            if x[2] == "R":
                sideVal = "_RIGHT_"
                colorCodes = [self.majorRightColor, self.majorLeftColor]
            elif x[2] == "L":
                sideVal = "_LEFT_"
                colorCodes = [self.majorLeftColor, self.minorLeftColor]
            else:
                sideVal = "c"
                colorCodes = [self.majorCenterColor, self.minorCenterColor]

            # pm.select(d=True)
            if self.seperateSelectionSets:
                set_name = "def_%s_%s_Set" % (x[1], x[2])
                set_name = extra.uniqueName(set_name)
                j_def_set = pm.sets(name=set_name)

            ### LIMB CREATION HERE #####
            if x[1] == "arm":
                if x[2] == "L":
                    self.rightShoulder = x[0]["Shoulder"]
                if x[2] == "R":
                    self.leftShoulder = x[0]["Shoulder"]
                # limb = arm.Arm()
                limb = arm.Arm(x[0], suffix="%s_Arm" %sideVal, side=x[2])
                limb.colorCodes = colorCodes
                # limb.createarm(x[0], suffix="%s_Arm" %sideVal, side=x[2])
                limb.createLimb()

            elif x[1] == "leg":
                if x[2] == "L":
                    self.leftHip = x[0]["Hip"]
                if x[2] == "R":
                    self.rightHip = x[0]["Hip"]

                limb = leg.Leg()
                limb.colorCodes = colorCodes
                limb.createleg(x[0], suffix="%s_Leg" %sideVal, side=x[2])

            elif x[1] == "neck":
                limb = neckAndHead.NeckAndHead()
                limb.colorCodes = colorCodes
                limb.createNeckAndHead(x[0], suffix="NeckAndHead", resolution=x[0]["resolution"], dropoff=x[0]["dropoff"])

            elif x[1] == "spine":
                limb = spine.Spine()
                limb.colorCodes = colorCodes
                limb.createSpine(x[0], suffix="Spine", resolution=x[0]["resolution"], dropoff=x[0]["dropoff"])  # s for spine...

            elif x[1] == "tail":
                limb = simpleTail.SimpleTail()
                limb.colorCodes = colorCodes
                limb.createSimpleTail(x[0], suffix="%s_Tail" %sideVal, side=x[2])

            elif x[1] == "finger":

                parentController = None
                for matching in self.fingerMatchList:
                    for f in matching:
                        if f in x[0].values():
                            index = self.fingerMatchList.index(matching)
                            parentController = self.fingerMatchConts[index][0]

                limb = finger.Fingers()
                limb.colorCodes = colorCodes
                limb.createFinger(x[0], suffix=sideVal, side=x[2], parentController=parentController)

            elif x[1] == "tentacle":
                limb = tentacle.Tentacle()
                limb.colorCodes = colorCodes
                limb.createTentacle(x[0], suffix="%s_Tentacle" % x[2], side=x[2], npResolution=x[0]["contRes"], jResolution = x[0]["jointRes"], blResolution = x[0]["deformerRes"], dropoff = x[0]["dropoff"])

            elif x[1] == "root":
                limb = root.Root()
                limb.colorCodes = colorCodes
                limb.createRoot(x[0], suffix="Toot")

            else:
                pm.error("limb creation failed.")
                return

            ##############################################
            if addLimb:
                pm.parent(limb.limbPlug, parentSocket)

                ## Good parenting / scale connections

                ## get the holder group
                self.rootGroup = masterController.getParent()

                ## Create the holder group if it does not exist

                # if not pm.objExists("{0}_rig".format(self.rigName)):
                #     self.rootGroup = pm.group(name=("{0}_rig".format(self.rigName)), em=True)
                # else:
                #     self.rootGroup = pm.PyNode("{0}_rig".format(self.rigName))

                # pm.parent(limb.scaleGrp, self.rootGroup)
                scaleGrpPiv = limb.limbPlug.getTranslation(space="world")
                pm.xform(limb.scaleGrp, piv=scaleGrpPiv, ws=True)
                ## pass the attributes

                extra.attrPass(limb.scaleGrp, masterController, values=True, daisyChain=True, overrideEx=False)

                pm.parent(limb.limbGrp, self.rootGroup)

                for sCon in limb.scaleConstraints:
                    pm.scaleConstraint(masterController, sCon)

            ##############################################
            else:
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
                # pm.parent(limb.scaleGrp, self.rootGroup)
                scaleGrpPiv = limb.limbPlug.getTranslation(space="world")
                pm.xform(limb.scaleGrp, piv=scaleGrpPiv, ws=True)
                ## pass the attributes

                extra.attrPass(limb.scaleGrp, self.cont_master, values=True, daisyChain=True, overrideEx=False)
                pm.parent(limb.limbGrp, self.rootGroup)
                for sCon in limb.scaleConstraints:
                    pm.scaleConstraint(self.cont_master, sCon)

            #
            # if not seperateSelectionSets:
            self.totalDefJoints += limb.deformerJoints
            if j_def_set:
                pm.sets(j_def_set, add=limb.deformerJoints)


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

            if jID[0] == "FingerRoot":
                allFingers.append(j)

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


        self.cont_placement = icon.circle(extra.uniqueName("cont_Placement"), (self.hipDistance, self.hipDistance, self.hipDistance))
        self.cont_master = icon.triCircle(extra.uniqueName("cont_Master"), (self.hipDistance * 1.5, self.hipDistance * 1.5, self.hipDistance * 1.5))
        pm.addAttr(self.cont_master, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True)
        pm.addAttr(self.cont_master, at="bool", ln="Joints_Visibility", sn="jointVis")
        pm.addAttr(self.cont_master, at="bool", ln="Rig_Visibility", sn="rigVis")

        for f in self.fingerMatchList:
            fName, fType, fSide = extra.identifyMaster(f[0])
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
        if limbType == "tentacle":
            limbDict["contRes"] = pm.getAttr(node.contRes)
            limbDict["jointRes"] = pm.getAttr(node.jointRes)
            limbDict["deformerRes"] = pm.getAttr(node.deformerRes)
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
                    if cID[0] == "Spine" or cID[0] == "Neck" or cID[0]== "Tentacle" or cID[0] == "Tail" or cID[1] == "finger":  ## spine and neck joints are multiple, so put them in a list
                        multiList.append(c)
                        limbDict[cID[0]] = multiList
                    else:
                        limbDict[cID[0]] = c
                else:
                    failedChildren += 1
            if len(children) == failedChildren:
                z=False
        return [limbDict, limbType, limbSide]




