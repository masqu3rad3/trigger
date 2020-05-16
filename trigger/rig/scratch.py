"""THIS MODULE IS DEPRECATED USE builder MODULE INSTEAD"""

from maya import cmds
from trigger.modules import all_modules_data
import trigger.library.functions as extra
import trigger.library.controllers as ic
import trigger.modules.arm as arm
import trigger.modules.leg as leg
import trigger.modules.head as neckAndHead
import trigger.modules.spine as spine
import trigger.modules.tail as simpleTail
import trigger.modules.finger as finger
import trigger.modules.tentacle as tentacle
import trigger.modules.connector as root
import trigger.utils.space_switcher as anchorMaker
import trigger.library.tools as tools

# from Qt import QtWidgets, QtCore, QtGui
from trigger.ui.Qt import QtWidgets

class LimbBuilder():

    def __init__(self, settingsData, progressBar=None):
        # super(LimbBuilder, self).__init__()
        self.progressBar = progressBar
        self.validRootList = [values["members"][0] for values in all_modules_data.MODULE_DICTIONARY.values()]
        # self.validRootList = ["Collar", "LegRoot", "Root", "SpineRoot", "NeckRoot", "TailRoot", "FingerRoot",
        #                       "ThumbRoot", "IndexRoot", "MiddleRoot", "RingRoot", "PinkyRoot", "TentacleRoot"]
        self.fingerMatchList = []
        self.fingerMatchConts = []
        self.hipDistance = 1
        self.shoulderDistance = 1
        self.anchorLocations = []
        self.anchors = []
        self.hipSize = 1.0
        self.chestSize = 1.0
        self.allSocketsList = []
        self.limbCreationList = []
        self.riggedLimbList = []
        self.rigName = "tikAutoRig"
        self.rootGroup = None
        self.skinMeshList = None
        self.copySkinWeights = False
        self.replaceExisting = False
        self.totalDefJoints = []
        self.parseSettings(settingsData)
        if self.progressBar:
            self.progressBar.setProperty("value", 0)
        self.bindMethod = 0
        self.skinMethod = 0

    def parseSettings(self, settingsData):

        self.afterCreation = settingsData["afterCreation"]
        self.seperateSelectionSets = settingsData["seperateSelectionSets"]
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

        selection = cmds.ls(sl=True, type="joint")
        if len(selection) != 1 or extra.identifyMaster(selection[0])[0] not in self.validRootList:
            cmds.warning("select a single root joint")
            return

        # ## Create the holder group if it does not exist

        try:
            oldRootGroup = "{0}_rig".format(self.rigName)
            if self.replaceExisting:
                # get all objects under old rig
                oldGroupMembers = cmds.listRelatives(oldRootGroup, ad=True, c=True) + [oldRootGroup]
                # rename thame (add _OLD as suffix)
                for old_member in oldGroupMembers:
                    try:
                        cmds.rename(old_member, "{0}{1}".format(old_member, "_OLD"))
                    except RuntimeError:
                        pass
        except:
            oldRootGroup = None

        self.rootGroup = cmds.group(name=(extra.uniqueName("{0}_rig".format(self.rigName))), em=True)

        # first initialize the dimensions for icon creation
        self.hipDistance, self.shoulderDistance = self.getDimensions(selection[0])
        self.limbCreationList = self.getLimbProperties(selection[0])

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
                    cmds.parent(anchor[0], self.cont_placement)
                except RuntimeError:
                    pass
        for x in self.fingerMatchConts:
            contPos = extra.createUpGrp(x[0], "POS", freezeTransform=False)
            socket = self.getNearestSocket(x[1], self.allSocketsList)
            cmds.parentConstraint(socket, contPos, mo=True)
            cmds.scaleConstraint(self.cont_master, contPos)
            cmds.parent(contPos, self.rootGroup)

        if self.afterCreation == 1:
            # if the After Creation set to 'Hide Initial Joints'
            cmds.hide(selection)
        if self.afterCreation == 2:
            # if the After Creation set to 'Delete Initial Joints'
            cmds.delete(selection)
        if self.skinMeshList and not self.replaceExisting:
            # if there are skin mesh(s) defined, and replace existing is not checked, initiate the skinning process
            self.skinning(copyMode=self.copySkinWeights)


        if self.replaceExisting and oldRootGroup:
            # get every controller under the oldRootGroup
            allTransform = cmds.listRelatives(oldRootGroup, ad=True, c=True, typ="nurbsCurve")

            allOldCont = extra.uniqueList(
                [cmds.listRelatives(cont, parent=True)[0] for cont in allTransform if cont.startswith("cont_")])

            # find corresponding new controllers and replace them with the old ones

            for cont in allOldCont:
                if "cont_FK_IK" in cont:
                    continue
                try:
                    new = cont.replace("_OLD", "")
                    # duplicate
                    old = cmds.duplicate(cont)[0]
                    # unparent
                    cmds.parent(old, w=True)
                    cmds.delete(cmds.listRelatives(old, c=True, typ="transform"))
                    cmds.setAttr("%s.tx" %old, e=True, k=True, l=False)
                    cmds.setAttr("%s.ty" %old, e=True, k=True, l=False)
                    cmds.setAttr("%s.tz" %old, e=True, k=True, l=False)
                    cmds.setAttr("%s.rx" %old, e=True, k=True, l=False)
                    cmds.setAttr("%s.ry" %old, e=True, k=True, l=False)
                    cmds.setAttr("%s.rz" %old, e=True, k=True, l=False)
                    cmds.setAttr("%s.sx" %old, e=True, k=True, l=False)
                    cmds.setAttr("%s.sy" %old, e=True, k=True, l=False)
                    cmds.setAttr("%s.sz" %old, e=True, k=True, l=False)

                    cmds.setAttr("%s.tx" %old, 0)
                    cmds.setAttr("%s.ty" %old, 0)
                    cmds.setAttr("%s.tz" %old, 0)
                    cmds.setAttr("%s.rx" %old, 0)
                    cmds.setAttr("%s.ry" %old, 0)
                    cmds.setAttr("%s.rz" %old, 0)
                    cmds.setAttr("%s.sx" %old, 1)
                    cmds.setAttr("%s.sy" %old, 1)
                    cmds.setAttr("%s.sz" %old, 1)

                    tools.replaceController(mirror=False,
                                            oldController=new,
                                            newController=old,
                                            keepAcopy=False
                                            )
                except:
                    pass
            # find old skinned meshes
            allJoints = cmds.listRelatives(oldRootGroup, ad=True, c=True, typ="joint")
            allOldDefJoints = extra.uniqueList([j for j in allJoints if j.startswith("jDef")])
            skinList = []
            for i in allOldDefJoints:
                skinList += extra.uniqueList(cmds.listConnections(i, type="skinCluster"))
            skinList = extra.uniqueList(skinList)

            skinnedObjects = [cmds.listConnections(skinC.outputGeometry)[0] for skinC in skinList]

            for mesh in skinnedObjects:
                dupMesh = cmds.duplicate(mesh)[0]
                cmds.skinCluster(self.totalDefJoints, dupMesh, tsb=True)
                cmds.copySkinWeights(mesh, dupMesh, noMirror=True, surfaceAssociation="closestPoint",
                                   influenceAssociation="closestJoint", normalize=True)
                # delete the skin cluster on old mesh
                # oldSkin = cmds.listConnections(mesh.getShape(), type="skinCluster")[0]
                oldSkin = cmds.listConnections(cmds.listRelatives(mesh, s=True), type="skinCluster")[0]

                cmds.delete(oldSkin)
                # re-create the skin cluster with
                cmds.skinCluster(self.totalDefJoints, mesh, tsb=True)
                cmds.copySkinWeights(dupMesh, mesh, noMirror=True, surfaceAssociation="closestPoint",
                                   influenceAssociation="closestJoint", normalize=True)

                # delete duplicate
                cmds.delete(dupMesh)


    def skinning(self, copyMode):
        if copyMode:
            for i in self.skinMeshList:
                dupMesh = cmds.duplicate(i)[0]
                cmds.skinCluster(self.totalDefJoints, dupMesh, tsb=True)
                cmds.copySkinWeights(i, dupMesh, noMirror=True, surfaceAssociation="closestPoint",
                                   influenceAssociation="closestJoint", normalize=True)

        else:
            for i in self.skinMeshList:
                cmds.skinCluster(self.totalDefJoints, i, tsb=True, bindMethod=self.bindMethod, skinMethod=self.skinMethod)

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
            selection = cmds.ls(sl=True)
            if len(selection) > 3:
                cmds.error(
                    "Select exactly three nodes. First reference root node then target parent and finally master controller")
                return
            referenceRoot = selection[0]
            parentSocket = selection[1]
            masterController = selection[2]
            if extra.identifyMaster(referenceRoot)[0] not in self.validRootList:
                cmds.error("First selection must be a valid root joint node")
                return
            limbCreationList = [self.getWholeLimb(referenceRoot)]

        j_def_set = None

        if not self.seperateSelectionSets:
            print "limbCreationList", limbCreationList
            cmds.select(d=True)
            # if not pm.uniqueObjExists("def_jointsSet_%s" % self.rigName):
            if not cmds.objExists("def_jointsSet_%s" % self.rigName):
                j_def_set = cmds.sets(name="def_jointsSet_%s" % self.rigName)
            else:
                j_def_set = "def_jointsSet_%s" % self.rigName

        total_limb_count = len(limbCreationList)
        limb_counter = 0
        percent = (100 * limb_counter) / total_limb_count
        for x in limbCreationList:
            if self.progressBar:
                limb_counter = limb_counter + 1
                percent = (100 * limb_counter) / total_limb_count
                self.progressBar.setProperty("value", percent)
                QtWidgets.QApplication.processEvents()

            if x[2] == "R":
                sideVal = "R"
                colorCodes = [self.majorRightColor, self.majorLeftColor]
            elif x[2] == "L":
                sideVal = "L"
                colorCodes = [self.majorLeftColor, self.minorLeftColor]
            else:
                sideVal = "C"
                colorCodes = [self.majorCenterColor, self.minorCenterColor]

            # pm.select(d=True)
            if self.seperateSelectionSets:
                set_name = "def_%s_%s_Set" % (x[1], x[2])
                set_name = extra.uniqueName(set_name)
                j_def_set = cmds.sets(name=set_name)

            ### LIMB CREATION HERE #####
            if x[1] == "arm":
                if x[2] == "L":
                    self.rightShoulder = x[0]["Shoulder"]
                if x[2] == "R":
                    self.leftShoulder = x[0]["Shoulder"]
                # limb = arm.Arm()
                limb = arm.Arm(x[0], suffix="%s_Arm" % sideVal, side=x[2])
                limb.colorCodes = colorCodes
                # limb.createarm(x[0], suffix="%s_Arm" %sideVal, side=x[2])
                limb.createLimb()

            elif x[1] == "leg":
                if x[2] == "L":
                    self.leftHip = x[0]["Hip"]
                if x[2] == "R":
                    self.rightHip = x[0]["Hip"]

                limb = leg.Leg(x[0], suffix="%s_Leg" % sideVal, side=x[2])
                limb.colorCodes = colorCodes
                # limb.createleg(x[0], suffix="%s_Leg" %sideVal, side=x[2])
                limb.createLimb()

            elif x[1] == "neck":
                # limb = neckAndHead.NeckAndHead()
                limb = neckAndHead.Head(x[0], suffix="NeckAndHead", resolution=x[0]["resolution"],
                                        dropoff=x[0]["dropoff"])
                limb.colorCodes = colorCodes
                # limb.createNeckAndHead(x[0], suffix="NeckAndHead", resolution=x[0]["resolution"], dropoff=x[0]["dropoff"])
                limb.createLimb()

            elif x[1] == "spine":
                # limb = spine.Spine()
                limb = spine.Spine(x[0], suffix="Spine", resolution=x[0]["resolution"], dropoff=x[0]["dropoff"])
                limb.colorCodes = colorCodes
                # limb.createSpine(x[0], suffix="Spine", resolution=x[0]["resolution"], dropoff=x[0]["dropoff"])  # s for spine...
                limb.createLimb()

            elif x[1] == "tail":
                # limb = simpleTail.SimpleTail()
                limb = simpleTail.Tail(x[0], suffix="%s_Tail" % sideVal, side=x[2])
                limb.colorCodes = colorCodes
                # limb.createSimpleTail(x[0], suffix="%s_Tail" %sideVal, side=x[2])
                limb.createLimb()

            elif x[1] == "finger":

                parentController = None
                for matching in self.fingerMatchList:
                    for f in matching:
                        if f in x[0].values():
                            index = self.fingerMatchList.index(matching)
                            parentController = self.fingerMatchConts[index][0]

                # limb = finger.Fingers()
                # from pprint import pprint
                # pprint(x)
                # cmds.error("ANAN")

                limb = finger.Finger(x[0], suffix=sideVal, side=x[2], parentController=parentController)
                limb.colorCodes = colorCodes
                # limb.createFinger(x[0], suffix=sideVal, side=x[2], parentController=parentController)
                limb.createLimb()

            elif x[1] == "tentacle":
                # limb = tentacle.Tentacle()
                limb = tentacle.Tentacle(x[0], suffix="%s_Tentacle" % x[2], side=x[2], contRes=x[0]["contRes"],
                                         jointRes=x[0]["jointRes"], deformerRes=x[0]["deformerRes"],
                                         dropoff=x[0]["dropoff"])
                limb.colorCodes = colorCodes
                # limb.createTentacle(x[0], suffix="%s_Tentacle" % x[2], side=x[2], npResolution=x[0]["contRes"], jResolution = x[0]["jointRes"], blResolution = x[0]["deformerRes"], dropoff = x[0]["dropoff"])
                limb.createLimb()

            elif x[1] == "root":
                limb = root.Root(build_data=x[0], suffix="Toot")
                limb.colorCodes = colorCodes
                limb.createLimb()

            else:
                cmds.error("limb creation failed.")
                return

            ##############################################
            if addLimb:
                cmds.parent(limb.limbPlug, parentSocket)

                ## Good parenting / scale connections

                ## get the holder group
                # self.rootGroup = masterController.getParent()
                self.rootGroup = cmds.listRelatives(masterController, parent=True)

                ## Create the holder group if it does not exist

                # if not pm.objExists("{0}_rig".format(self.rigName)):
                #     self.rootGroup = pm.group(name=("{0}_rig".format(self.rigName)), em=True)
                # else:
                #     self.rootGroup = pm.PyNode("{0}_rig".format(self.rigName))

                # pm.parent(limb.scaleGrp, self.rootGroup)
                scaleGrpPiv = limb.limbPlug.getTranslation(space="world")
                cmds.xform(limb.scaleGrp, piv=scaleGrpPiv, ws=True)
                ## pass the attributes

                extra.attrPass(limb.scaleGrp, masterController, values=True, daisyChain=True, overrideEx=False)

                cmds.parent(limb.limbGrp, self.rootGroup)

                for sCon in limb.scaleConstraints:
                    cmds.scaleConstraint(masterController, sCon)

            ##############################################
            else:
                self.anchorLocations += limb.anchorLocations
                self.anchors += limb.anchors

                ## gather all sockets in a list
                self.allSocketsList += limb.sockets

                ## add the rigged limb to the riggedLimbList
                self.riggedLimbList.append(limb)

                parentInitJoint = x[3]
                #

                if parentInitJoint:
                    parentSocket = self.getNearestSocket(parentInitJoint, self.allSocketsList, excluding=limb.sockets)

                else:
                    parentSocket = self.cont_placement

                cmds.parent(limb.limbPlug, parentSocket)

                ## Good parenting / scale connections
                # pm.parent(limb.scaleGrp, self.rootGroup)
                # scaleGrpPiv = limb.limbPlug.getTranslation(space="world")
                scaleGrpPiv = extra.getWorldTranslation(limb.limbPlug)
                cmds.xform(limb.scaleGrp, piv=scaleGrpPiv, ws=True)
                ## pass the attributes

                extra.attrPass(limb.scaleGrp, self.cont_master, values=True, daisyChain=True, overrideEx=False)
                cmds.parent(limb.limbGrp, self.rootGroup)
                for sCon in limb.scaleConstraints:
                    cmds.scaleConstraint(self.cont_master, sCon)

            #
            # if not seperateSelectionSets:
            self.totalDefJoints += limb.deformerJoints
            if j_def_set:
                # for element in limb.deformerJoints:
                #     cmds.sets(j_def_set, add=element)
                # map(lambda x: cmds.sets(j_def_set, add=x), limb.deformerJoints)
                # cmds.sets(j_def_set, add=limb.deformerJoints)
                cmds.sets(limb.deformerJoints, add=j_def_set)

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
        allJoints = cmds.listRelatives(rootNode, type="joint", ad=True)
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
                x_parent = cmds.listRelatives(x, parent=True)
                y_parent = cmds.listRelatives(y, parent=True)
                if x_parent == y_parent:
                    tempGrp.append(y)
            if len(tempGrp) > 0 and tempGrp not in self.fingerMatchList:
                self.fingerMatchList.append(tempGrp)


        return hipDist, shoulderDist

    def getLimbProperties(self, node, isRoot=True, parentIndex=None, r_list=None):
        """
        Checks the given nodes entire hieararchy for roots, and catalogues the root nodes into dictionaries.

        isRoot: if True, the given joint is considered as true. Default is True. For recursion.
        parentIndex: indicates the parent of the current node. Default is none. For recursion.

        Returns: None (Updates limbCreationList attribute of the parent class)

        """
        if not r_list:
            r_list = []
        if isRoot:
            limbProps = self.getWholeLimb(node)
            limbProps.append(parentIndex)
            # self.limbCreationList.append(limbProps)
            r_list.append(limbProps)

        # Do the same for all children recursively
        children = cmds.listRelatives(node, children=True, type="joint")
        children = children if children else []
        for jnt in children:
            cID = extra.identifyMaster(jnt)
            if cID[0] in self.validRootList:
                self.getLimbProperties(jnt, isRoot=True, parentIndex=node, r_list=r_list)
            else:
                self.getLimbProperties(jnt, isRoot=False, r_list=r_list)
        return r_list
        # if isRoot:
        #     limbProps = self.getWholeLimb(node)
        #     limbProps.append(parentIndex)
        #     self.limbCreationList.append(limbProps)
        #
        # # Do the same for all children recursively
        # # children = node.getChildren(type="joint")
        # children = cmds.listRelatives(node, children=True, type="joint")
        # children = children if children else []
        # for c in children:
        #     cID = extra.identifyMaster(c)
        #     if cID[0] in self.validRootList:
        #         self.getLimbProperties(c, isRoot=True, parentIndex=node)
        #     else:
        #         self.getLimbProperties(c, isRoot=False)

    def createMasters(self):
        """
        This method creates master controllers (Placement and Master)
        Returns: None

        """

        icon = ic.Icon()

        # self.cont_placement = icon.circle(extra.uniqueName("cont_Placement"), (self.hipDistance, self.hipDistance, self.hipDistance))
        self.cont_placement, dmp = icon.createIcon("Circle", iconName=extra.uniqueName("cont_Placement"),
                                                   scale=(self.hipDistance, self.hipDistance, self.hipDistance))
        # self.cont_master = icon.triCircle(extra.uniqueName("cont_Master"), (self.hipDistance * 1.5, self.hipDistance * 1.5, self.hipDistance * 1.5))
        self.cont_master, dmp = icon.createIcon("TriCircle", iconName=extra.uniqueName("cont_Master"), scale=(
        self.hipDistance * 1.5, self.hipDistance * 1.5, self.hipDistance * 1.5))
        # cmds.addAttr(self.cont_master, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True)
        # cmds.addAttr(self.cont_master, at="bool", ln="Joints_Visibility", sn="jointVis")
        # cmds.addAttr(self.cont_master, at="bool", ln="Rig_Visibility", sn="rigVis")

        cmds.addAttr(self.cont_master, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True, keyable=True)
        cmds.addAttr(self.cont_master, at="bool", ln="Joints_Visibility", sn="jointVis", keyable=True)
        cmds.addAttr(self.cont_master, at="bool", ln="Rig_Visibility", sn="rigVis", keyable=True)

        for f in self.fingerMatchList:
            fName, fType, fSide = extra.identifyMaster(f[0])
            f_parent = cmds.listRelatives(f[0], parent=True)[0]
            offsetVector = extra.getBetweenVector(f_parent, f)
            iconSize = extra.getDistance(f[0], f[-1])
            translateOff = (iconSize / 2, 0, iconSize / 2)
            rotateOff = (0, 0, 0)
            if "_left" in f[0]:
                iconName = f[0].replace("_left", "_LEFT")
            elif "_right" in f[0]:
                iconName = f[0].replace("_right", "_RIGHT")
                rotateOff = (0, 180, 0)
                translateOff = (iconSize / 2, 0, -iconSize / 2)
            else:
                iconName = f[0]

            # cont_fGroup = icon.square(name="cont_Fgrp_{0}".format(iconName), scale=(iconSize/6, iconSize/4, iconSize/2))
            cont_fGroup, dmp = icon.createIcon("Square", iconName="cont_Fgrp_{0}".format(iconName),
                                               scale=(iconSize / 6, iconSize / 4, iconSize / 2))
            cmds.rotate(90, 0, 0, cont_fGroup)
            cmds.makeIdentity(cont_fGroup, a=True)

            extra.alignAndAim(cont_fGroup, targetList=[f_parent], aimTargetList=[f[0], f[-1]], upObject=f[0],
                              rotateOff=rotateOff, translateOff=(-offsetVector * (iconSize / 2)))
            cmds.move(0, 0, (-iconSize / 2), cont_fGroup, r=True, os=True)
            self.fingerMatchConts.append([cont_fGroup, f_parent])

        # make the created attributes visible in the channelbox
        cmds.setAttr("%s.contVis" %self.cont_master, cb=True)
        cmds.setAttr("%s.jointVis" %self.cont_master, cb=True)
        cmds.setAttr("%s.rigVis" %self.cont_master, cb=True)
        cmds.parent(self.cont_placement, self.cont_master)
        # # add these to the anchor locations
        self.anchorLocations.append(self.cont_master)
        self.anchorLocations.append(self.cont_placement)

        # COLOR CODING
        index = 17
        extra.colorize(self.cont_master, index)
        extra.colorize(self.cont_placement, index)

        # # GOOD PARENTING

        extra.lockAndHide(self.rootGroup, ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"])
        cmds.parent(self.cont_master, self.rootGroup)

    def getNearestSocket(self, initJoint, limbSockets, excluding=[]):
        """
        searches through limbSockets list and gets the nearest socket to the initJoint.
        Args:
            initJoint: (pymel object) initial joint to test the distance
            limbSockets: (list) limbSockets list

        Returns:

        """
        distanceList = []
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
        # for property in all_modules_data.MODULE_DICTIONARY[limbType]["properties"]:
        #     limbDict[property] = cmds.getAttr("%s.%s" %(node, property))
        for property in all_modules_data.MODULE_DICTIONARY[limbType]["properties"]:
            attr = property["attr_name"]
            limbDict[attr] = cmds.getAttr("%s.%s" % (node, attr))
        # if limbType == "spine" or limbType == "neck":
        #     limbDict["resolution"] = cmds.getAttr("%s.resolution" %node)
        #     limbDict["dropoff"] = cmds.getAttr("%s.dropoff" %node)
        # if limbType == "tentacle":
        #     limbDict["contRes"] = cmds.getAttr("%s.contRes" %node)
        #     limbDict["jointRes"] = cmds.getAttr("%s.jointRes" %node)
        #     limbDict["deformerRes"] = cmds.getAttr("%s.deformerRes" %node)
        #     limbDict["dropoff"] = cmds.getAttr("%s.dropoff" %node)

        limbDict[limbName] = node
        nextNode = node
        z = True
        while z:
            children = cmds.listRelatives(nextNode, children=True, type="joint")
            # children = nextNode.getChildren(type="joint")
            children = [] if not children else children
            if len(children) < 1:
                z = False
            failedChildren = 0
            for c in children:
                cID = extra.identifyMaster(c)
                if cID[0] not in self.validRootList and cID[1] == limbType:
                    nextNode = c
                    if cID[0] == "Spine" or cID[0] == "Neck" or cID[0] == "Tentacle" or cID[0] == "Tail" or cID[
                        1] == "finger":  ## spine and neck joints are multiple, so put them in a list
                        multiList.append(c)
                        limbDict[cID[0]] = multiList
                    else:
                        limbDict[cID[0]] = c
                else:
                    failedChildren += 1
            if len(children) == failedChildren:
                z = False
        return [limbDict, limbType, limbSide]





