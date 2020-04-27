"""New rig builder module"""
from maya import cmds
from trigger.core import feedback
from trigger.modules import all_modules_data
import trigger.library.functions as extra
import trigger.library.controllers as ic

from trigger import modules

# import trigger.modules.arm as arm
# import trigger.modules.leg as leg
# import trigger.modules.head as neckAndHead
# import trigger.modules.spine as spine
# import trigger.modules.tail as simpleTail
# import trigger.modules.finger as finger
# import trigger.modules.tentacle as tentacle
# import trigger.modules.root as root
import trigger.utils.space_switcher as anchorMaker
import trigger.library.tools as tools
from trigger.core import io

from trigger.Qt import QtWidgets

import pdb

FEEDBACK = feedback.Feedback(logger_name=__name__)


class Builder(object):
    def __init__(self, name="trigger", progress_bar=None):
        self.progress_bar = progress_bar
        if self.progress_bar:
            self.progress_bar.setProperty("value", 0)
        self.rig_name = name
        self.validRootList = [values["members"][0] for values in all_modules_data.MODULE_DICTIONARY.values()]
        default_settings = {
            "upAxis": "+y",
            "mirrorAxis": "+x",
            "lookAxis": "+z",
            "majorCenterColor": 17,
            "minorCenterColor": 20,
            "majorLeftColor": 6,
            "minorLeftColor": 18,
            "majorRightColor": 13,
            "minorRightColor": 9,
            "seperateSelectionSets": True,
            "afterCreation": 0,
            "bindMethod": 0,
            "skinningMethod": 0
        }
        self.settings = io.Settings("triggerSettings.json", defaults=default_settings)
        # Parse the dictionary settings to variables
        self.majorCenterColor = self.settings.currents["majorCenterColor"]
        self.minorCenterColor = self.settings.currents["minorCenterColor"]
        self.majorLeftColor = self.settings.currents["majorLeftColor"]
        self.minorLeftColor = self.settings.currents["minorLeftColor"]
        self.majorRightColor = self.settings.currents["majorRightColor"]
        self.minorRightColor = self.settings.currents["minorRightColor"]
        self.seperateSelectionSets = self.settings.currents["seperateSelectionSets"]
        self.afterCreation = self.settings.currents["afterCreation"]
        self.bindMethod = self.settings.currents["bindMethod"]
        self.skinMethod = self.settings.currents["skinningMethod"]

        self.limbCreationList = []

        self.fingerMatchList = []
        self.fingerMatchConts = []
        self.spaceSwitchers = []
        self.shoulderDist = 1.0
        self.hipDist = 1.0

        self.anchorLocations = []
        self.anchors = []
        self.allSocketsList = []
        self.riggedLimbList = []
        self.totalDefJoints = []

        # TODO: These should go
        self.skinMeshList = None
        self.copySkinWeights = False
        self.replaceExisting = False

    def start_building(self, root_jnt=None, create_switchers=False):
        """ Creates the modules for the selected root and for all the roots in the hiearchy and connects them

        Args:
            root_jnt(string): root guide joint. If not defined, scene selection will be used.
            create_switchers (bool): If True, the default space switchers will be created.

        Returns: None

        """
        if not root_jnt:
            selection = cmds.ls(sl=True)
            if len(selection) == 1:
                root_jnt = selection[0]
            else:
                FEEDBACK.warning("Select a single root_jnt joint")
        if not cmds.objectType(root_jnt, isType="joint"):
            FEEDBACK.throw_error("root_jnt is not a joint")
        root_name, root_type, root_side = extra.identifyMaster(root_jnt)
        if root_name not in self.validRootList:
            FEEDBACK.throw_error("selected joint is not in the valid root_jnt list")

        self.rootGroup = cmds.group(name=(extra.uniqueName("{0}_rig".format(self.rig_name))), em=True)
        self.collect_guides_info(root_jnt)
        # self.get_limb_hierarchy(root_jnt)
        self.limbCreationList = self.get_limb_hierarchy(root_jnt)

        self.createMasters()
        self.createlimbs(self.limbCreationList)

        # create space switchers
        if create_switchers:
            for anchor in (self.anchors):
                FEEDBACK.warning(anchor)
                anchorMaker.create_space_switch(anchor[0], self.anchorLocations, mode=anchor[1], defaultVal=anchor[2],
                                                listException=anchor[3])

        else:
            # TODO: tidy up here
            for anchor in (self.anchors):
                try:
                    cmds.parent(anchor[0], self.cont_placement)
                except RuntimeError:
                    pass

        # grouping for fingers / toes
        for x in self.fingerMatchConts:
            # TODO: tidy up / matrix constraint
            cont_offset = extra.createUpGrp(x[0], "offset", freezeTransform=False)
            socket = self.getNearestSocket(x[1], self.allSocketsList)
            cmds.parentConstraint(socket, cont_offset, mo=True)
            cmds.scaleConstraint(self.cont_master, cont_offset)
            cmds.parent(cont_offset, self.rootGroup)

        # TODO : tidy up / make settings human readable
        if self.afterCreation == 1:
            # if the After Creation set to 'Hide Initial Joints'
            cmds.hide(root_jnt)
        if self.afterCreation == 2:
            # if the After Creation set to 'Delete Initial Joints'
            cmds.delete(root_jnt)

        # TODO : re-make the whole skinCluster handling with a more sensible way
        if self.skinMeshList and not self.replaceExisting:
            # if there are skin mesh(s) defined, and replace existing is not checked, initiate the skinning process
            self.skinning(copyMode=self.copySkinWeights)

    def get_limb_hierarchy(self, node, isRoot=True, parentIndex=None, r_list=None):
        """Checks the given nodes entire hieararchy for roots, and catalogues the root nodes into dictionaries.

        Args:
            node (string): starts checking from this node
            isRoot(bool): if True, the given joint is considered as true. Default is True. For recursion.
            parentIndex(string): indicates the parent of the current node. Default is none. For recursion.
            r_list(list): If a list is provided, it appends the results into this one. For recursion

        Returns (list): list of root guide nodes in the hierarchy

        """
        if not r_list:
            r_list = []
        if isRoot:
            limbProps = self.getWholeLimb(node)
            limbProps.append(parentIndex)
            # self.limbCreationList.append(limbProps)
            r_list.append(limbProps)
            # pdb.set_trace()

        # Do the same for all children recursively
        children = cmds.listRelatives(node, children=True, type="joint")
        children = children if children else []
        for jnt in children:
            cID = extra.identifyMaster(jnt)
            if cID[0] in self.validRootList:
                self.get_limb_hierarchy(jnt, isRoot=True, parentIndex=node, r_list=r_list)
            else:
                self.get_limb_hierarchy(jnt, isRoot=False, r_list=r_list)
        return r_list

    def createMasters(self):
        """
        This method creates master controllers (Placement and Master)
        Returns: None

        """
        icon = ic.Icon()
        self.cont_placement, _ = icon.createIcon("Circle", iconName=extra.uniqueName("placement_cont"),
                                                 scale=(self.hipDist, self.hipDist, self.hipDist))
        self.cont_master, _ = icon.createIcon("TriCircle", iconName=extra.uniqueName("master_cont"), scale=(
            self.hipDist * 1.5, self.hipDist * 1.5, self.hipDist * 1.5))

        cmds.addAttr(self.cont_master, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True,
                     keyable=True)
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

            cont_fGroup, dmp = icon.createIcon("Square", iconName="cont_Fgrp_{0}".format(iconName),
                                               scale=(iconSize / 6, iconSize / 4, iconSize / 2))
            cmds.rotate(90, 0, 0, cont_fGroup)
            cmds.makeIdentity(cont_fGroup, a=True)

            extra.alignAndAim(cont_fGroup, targetList=[f_parent], aimTargetList=[f[0], f[-1]], upObject=f[0],
                              rotateOff=rotateOff, translateOff=(-offsetVector * (iconSize / 2)))
            cmds.move(0, 0, (-iconSize / 2), cont_fGroup, r=True, os=True)
            self.fingerMatchConts.append([cont_fGroup, f_parent])

        # make the created attributes visible in the channelbox
        cmds.setAttr("%s.contVis" % self.cont_master, cb=True)
        cmds.setAttr("%s.jointVis" % self.cont_master, cb=True)
        cmds.setAttr("%s.rigVis" % self.cont_master, cb=True)
        cmds.parent(self.cont_placement, self.cont_master)
        # # add these to the anchor locations
        self.spaceSwitchers.append(self.cont_master)
        self.spaceSwitchers.append(self.cont_placement)

        # COLOR CODING
        index = 17
        extra.colorize(self.cont_master, index)
        extra.colorize(self.cont_placement, index)

        # # GOOD PARENTING

        extra.lockAndHide(self.rootGroup, ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"])
        cmds.parent(self.cont_master, self.rootGroup)

    def collect_guides_info(self, rootNode):
        """
        Collects all the joints under the rootNode hierarchy
        Args:
            rootNode: (string) All the hiearchy under this will be collected

        Returns: None

        """
        l_hip, r_hip, l_shoulder, r_shoulder = [None, None, None, None]
        allJoints = cmds.listRelatives(rootNode, type="joint", ad=True)
        all_fingers = []
        for jnt in allJoints:
            limb_name, limb_type, limb_side = extra.identifyMaster(jnt)
            if limb_name == "Hip" and limb_side == "L":
                l_hip = jnt
            if limb_name == "Hip" and limb_side == "R":
                r_hip = jnt
            if limb_name == "Shoulder" and limb_side == "L":
                l_shoulder = jnt
            if limb_name == "Shoulder" and limb_side == "R":
                r_shoulder = jnt
            ## collect fingers
            if limb_name == "FingerRoot":
                all_fingers.append(jnt)

        self.hipDist = extra.getDistance(l_hip, r_hip) if l_hip and r_hip else self.hipDist
        self.shoulderDist = extra.getDistance(l_shoulder,
                                              r_shoulder) if l_shoulder and r_shoulder else self.shoulderDist

        for finger in all_fingers:
            # group the same type brothers and append them into the list if it is not already there
            parent = extra.getParent(finger)
            brothers = cmds.listRelatives(parent, c=True, type="joint")
            if brothers:
                digit_brothers = [brother for brother in brothers if brother in all_fingers]
                if digit_brothers and digit_brothers not in self.fingerMatchList:
                    self.fingerMatchList.append(digit_brothers)

        # self.fingerMatchList = []
        # for x in all_fingers:
        #     tempGrp = []
        #     for y in all_fingers:
        #         x_parent = cmds.listRelatives(x, parent=True)
        #         y_parent = cmds.listRelatives(y, parent=True)
        #         if x_parent == y_parent:
        #             tempGrp.append(y)
        #     if len(tempGrp) > 0 and tempGrp not in self.fingerMatchList:
        #         self.fingerMatchList.append(tempGrp)

    def getWholeLimb(self, node):
        multi_guide_jnts = [value["multi_guide"] for value in all_modules_data.MODULE_DICTIONARY.values() if
                            value["multi_guide"]]
        limb_dict = {}
        multiList = []
        segments = None
        dropoff = None
        limb_name, limb_type, limb_side = extra.identifyMaster(node)
        for property in all_modules_data.MODULE_DICTIONARY[limb_type]["properties"]:
            limb_dict[property] = cmds.getAttr("%s.%s" % (node, property))

        limb_dict[limb_name] = node
        nextNode = node
        z = True
        while z:
            children = cmds.listRelatives(nextNode, children=True, type="joint")
            children = [] if not children else children
            if len(children) < 1:
                z = False
            failedChildren = 0
            for child in children:
                child_limb_name, child_limb_type, child_limb_side = extra.identifyMaster(child)
                if child_limb_name not in self.validRootList and child_limb_type == limb_type:
                    nextNode = child
                    if child_limb_name in multi_guide_jnts:
                        multiList.append(child)
                        limb_dict[child_limb_name] = multiList
                    else:
                        limb_dict[child_limb_name] = child
                else:
                    failedChildren += 1
            if len(children) == failedChildren:
                z = False
        return [limb_dict, limb_type, limb_side]

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

    def createlimbs(self, limbCreationList=None, add_limb=False, root_plug=None, parent_socket=None, master_cont=None,
                    selection_mode=False, *args, **kwargs):
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
        if add_limb:  # this means we are adding limbs to the existing rig
            if not selection_mode:
                if root_plug and parent_socket and master_cont:
                    # check the root
                    if extra.identifyMaster(root_plug)[0] not in self.validRootList:
                        FEEDBACK.throw_error("root must be a valid root guide node")
                    limbCreationList = self.get_limb_hierarchy(root_plug)
                else:
                    FEEDBACK.throw_error("add_limb mode requires all root, parent and master_cont flags")
            else:
                if len(cmds.ls(sl=True)) == 3:
                    root_plug, parent_socket, master_cont = cmds.ls(sl=True)
                else:
                    FEEDBACK.throw_error(
                        "Select exactly three nodes. First reference root node then target parent and finally master controller")
                if extra.identifyMaster(root_plug)[0] not in self.validRootList:
                    FEEDBACK.throw_error("First selection must be a valid root joint node")

            limbCreationList = self.get_limb_hierarchy(root_plug)

        j_def_set = None

        if not self.seperateSelectionSets:
            cmds.select(d=True)
            if not cmds.objExists("def_jointsSet_%s" % self.rig_name):
                j_def_set = cmds.sets(name="def_jointsSet_%s" % self.rig_name)
            else:
                j_def_set = "def_jointsSet_%s" % self.rig_name

        total_limb_count = len(limbCreationList)
        limb_counter = 0
        # percent = (100 * limb_counter) / total_limb_count
        FEEDBACK.warning(limbCreationList)
        for x in limbCreationList:
            if self.progress_bar:
                limb_counter = limb_counter + 1
                percent = (100 * limb_counter) / total_limb_count
                self.progress_bar.setProperty("value", percent)
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

            if self.seperateSelectionSets:
                set_name = "def_%s_%s_Set" % (x[1], x[2])
                set_name = extra.uniqueName(set_name)
                j_def_set = cmds.sets(name=set_name)

            # # get the shoulders and hips
            # if x[1] == "arm":
            #     if x[2] == "L":
            #         self.rightShoulder = x[0]["Shoulder"]
            #     if x[2] == "R":
            #         self.leftShoulder = x[0]["Shoulder"]
            #
            # elif x[1] == "leg":
            #     if x[2] == "L":
            #         self.leftHip = x[0]["Hip"]
            #     if x[2] == "R":
            #         self.rightHip = x[0]["Hip"]

            suffix = "%s_%s" % (sideVal, x[1].capitalize()) if sideVal != "C" else x[1].capitalize()
            module = "modules.{0}.{1}".format(x[1], x[1].capitalize())
            flags = "build_data={0}, suffix='{1}', side='{2}'".format(x[0], suffix, x[2])
            command = "{0}({1})".format(module, flags)

            # FEEDBACK.debug("="*30, command, "-"*30)

            limb = eval(command)
            limb.colorCodes = colorCodes
            limb.createLimb()

            ##############################################
            if add_limb:
                cmds.parent(limb.limbPlug, parent_socket)

                ## Good parenting / scale connections
                ## get the holder group
                self.rootGroup = extra.getParent(master_cont)
                ## Create the holder group if it does not exist
                # scaleGrpPiv = limb.limbPlug.getTranslation(space="world")
                scaleGrpPiv = extra.getWorldTranslation(limb.limbPlug)
                cmds.xform(limb.scaleGrp, piv=scaleGrpPiv, ws=True)
                ## pass the attributes

                extra.attrPass(limb.scaleGrp, master_cont, values=True, daisyChain=True, overrideEx=False)
                cmds.parent(limb.limbGrp, self.rootGroup)
                for sCon in limb.scaleConstraints:
                    cmds.scaleConstraint(master_cont, sCon)
            ##############################################
            else:
                self.anchorLocations += limb.anchorLocations
                self.anchors += limb.anchors

                ## gather all sockets in a list
                self.allSocketsList += limb.sockets

                ## add the rigged limb to the riggedLimbList
                self.riggedLimbList.append(limb)

                parent_guide_joint = x[3]
                if parent_guide_joint:
                    parentSocket = self.getNearestSocket(parent_guide_joint, self.allSocketsList,
                                                         excluding=limb.sockets)

                else:
                    parentSocket = self.cont_placement

                cmds.parent(limb.limbPlug, parentSocket)

                ## Good parenting / scale connections
                scaleGrpPiv = extra.getWorldTranslation(limb.limbPlug)
                cmds.xform(limb.scaleGrp, piv=scaleGrpPiv, ws=True)
                ## pass the attributes

                extra.attrPass(limb.scaleGrp, self.cont_master, values=True, daisyChain=True, overrideEx=False)
                cmds.parent(limb.limbGrp, self.rootGroup)
                for sCon in limb.scaleConstraints:
                    cmds.scaleConstraint(self.cont_master, sCon)
            # if not seperateSelectionSets:
            self.totalDefJoints += limb.deformerJoints
            if j_def_set:
                cmds.sets(limb.deformerJoints, add=j_def_set)

    def skinning(self, copyMode):
        if copyMode:
            for i in self.skinMeshList:
                dupMesh = cmds.duplicate(i)[0]
                cmds.skinCluster(self.totalDefJoints, dupMesh, tsb=True)
                cmds.copySkinWeights(i, dupMesh, noMirror=True, surfaceAssociation="closestPoint",
                                     influenceAssociation="closestJoint", normalize=True)

        else:
            for i in self.skinMeshList:
                cmds.skinCluster(self.totalDefJoints, i, tsb=True, bindMethod=self.bindMethod,
                                 skinMethod=self.skinMethod)
