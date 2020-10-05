"""Builds the kinematics starting from the given root and for all descendants"""

from maya import cmds
from trigger.core import feedback
import trigger.library.functions as functions
import trigger.library.controllers as ic

from trigger.base import session

from trigger import modules
import trigger.utils.space_switcher as anchorMaker
from trigger.core import settings

from trigger.actions import master

from trigger.ui.Qt import QtWidgets

FEEDBACK = feedback.Feedback(logger_name=__name__)
#
ACTION_DATA = {"use_guides": "from_file",
               "guides_file_path": "",
               "guide_roots": [],
               "auto_switchers": True,
               # "anchors": [],
               # "anchor_locations": [],
               "extra_switchers": [],
               "after_creation": "delete"
               }

class Kinematics(settings.Settings):
# class Kinematics(object):
    def __init__(self, root_joints=None, progress_bar=None, create_switchers=True, *args, **kwargs):
        super(Kinematics, self).__init__()
        self.progress_bar = progress_bar
        if self.progress_bar:
            self.progress_bar.setProperty("value", 0)

        self.autoSwitchers = create_switchers
        self.root_joints = root_joints if type(root_joints) == list else [root_joints]
        self.module_dict = {mod: eval("modules.{0}.LIMB_DATA".format(mod)) for mod in modules.__all__}
        self.validRootList = [values["members"][0] for values in self.module_dict.values()]

        self.fingerMatchList = []
        self.fingerMatchConts = []
        # self.spaceSwitchers = []
        self.shoulderDist = 1.0
        self.hipDist = 1.0

        self.anchorLocations = []
        self.anchors = []
        self.extraSwitchers = []
        self.allSocketsList = []
        self.riggedLimbList = []
        self.totalDefJoints = []
        self.afterlife = "hide" # valid values are keep, hide, delete

        self.guides_file_path = None

    def feed(self, action_data):
        """Mandatory Function for builder- feeds with the Action Data from builder"""
        self.guides_file_path = action_data.get("guides_file_path")
        self.root_joints = action_data.get("guide_roots")
        self.autoSwitchers = action_data.get("auto_switchers")
        # self.anchors = action_data.get("anchors")
        # self.anchorLocations = action_data.get("anchor_locations")
        self.extraSwitchers = action_data.get("extra_switchers")
        self.afterlife = action_data.get("after_creation")


    def action(self):
        root_grp = "trigger_grp"
        if self.guides_file_path:
            guides_handler = session.Session()
            guides_handler.load_session(self.guides_file_path)
        if not cmds.objExists(root_grp):
            master.Master().action()
        for root_joint in self.root_joints:
            self.collect_guides_info(root_joint)
            self.limbCreationList = self.get_limb_hierarchy(root_joint)
            self.match_fingers(self.fingerMatchList)
            self.createlimbs(self.limbCreationList)

            if self.autoSwitchers and self.anchorLocations:
            # if self.anchors and self.anchorLocations:
                for anchor in (self.anchors):
                    anchorMaker.create_space_switch(anchor[0], self.anchorLocations, mode=anchor[1], defaultVal=anchor[2],
                                                    listException=anchor[3])


            # grouping for fingers / toes
            for x in self.fingerMatchConts:
                # TODO: tidy up / matrix constraint
                cont_offset = functions.createUpGrp(x[0], "offset", freezeTransform=False)
                socket = self.getNearestSocket(x[1], self.allSocketsList)
                cmds.parentConstraint(socket, cont_offset, mo=True)
                cmds.scaleConstraint("pref_cont", cont_offset)
                cmds.parent(cont_offset, root_grp)
                cmds.connectAttr("pref_cont.Control_Visibility", "%s.v" % cont_offset)

            if self.afterlife == "hide":
                cmds.hide(root_joint)
            elif self.afterlife == "delete":
                functions.deleteObject(root_joint)

            # # TODO : tidy up / make settings human readable
            # if self.get("afterCreation") == 1:
            #     # if the After Creation set to 'Hide Initial Joints'
            #     cmds.hide(root_joint)
            # if self.get("afterCreation") == 2:
            #     # if the After Creation set to 'Delete Initial Joints'
            #     cmds.delete(root_joint)


    def match_fingers(self, finger_match_list):
        icon = ic.Icon()
        for brother_roots in finger_match_list:
            # finger_name, finger_type, finger_side = extra.identifyMaster(brother_roots[0], self.module_dict)
            finger_parent = functions.getParent(brother_roots[0])
            offsetVector = functions.getBetweenVector(finger_parent, brother_roots)
            iconSize = functions.getDistance(brother_roots[0], brother_roots[-1])
            translateOff = (iconSize / 2, 0, iconSize / 2)
            rotateOff = (0, 0, 0)
            icon_name = brother_roots[0].replace("jInit", "")
            if "_left" in icon_name:
                icon_name = "L%s" % icon_name.replace("_left", "")
            elif "_right" in icon_name:
                icon_name = "R%s" % icon_name.replace("_right", "")
                rotateOff = (0, 180, 0)
                translateOff = (iconSize / 2, 0, -iconSize / 2)
            else:
                pass

            cont_fGroup, dmp = icon.createIcon("Square", iconName="%s_Fgrp_cont" % icon_name,
                                               scale=(iconSize / 6, iconSize / 4, iconSize / 2))
            cmds.rotate(90, 0, 0, cont_fGroup)
            cmds.makeIdentity(cont_fGroup, a=True)

            functions.alignAndAim(cont_fGroup, targetList=[finger_parent], aimTargetList=[brother_roots[0], brother_roots[-1]], upObject=brother_roots[0],
                                  rotateOff=rotateOff, translateOff=(-offsetVector * (iconSize / 2)))
            cmds.move(0, 0, (-iconSize / 2), cont_fGroup, r=True, os=True)
            self.fingerMatchConts.append([cont_fGroup, finger_parent])
            for finger_root in brother_roots:
                cmds.setAttr("%s.handController" % finger_root, cont_fGroup, type="string")

    def collect_guides_info(self, rootNode):
        """
        Collects all the joints under the rootNode hierarchy
        Args:
            rootNode: (string) All the hiearchy under this will be collected

        Returns: None

        """
        l_hip, r_hip, l_shoulder, r_shoulder = [None, None, None, None]
        allJoints = cmds.listRelatives(rootNode, type="joint", ad=True)
        allJoints = [] if not allJoints else allJoints
        all_fingers = []
        for jnt in allJoints:
            limb_name, limb_type, limb_side = functions.identifyMaster(jnt, self.module_dict)
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

        self.hipDist = functions.getDistance(l_hip, r_hip) if l_hip and r_hip else self.hipDist
        self.shoulderDist = functions.getDistance(l_shoulder,
                                                  r_shoulder) if l_shoulder and r_shoulder else self.shoulderDist

        for finger in all_fingers:
            # group the same type brothers and append them into the list if it is not already there
            parent = functions.getParent(finger)
            brothers = cmds.listRelatives(parent, c=True, type="joint")
            if brothers:
                digit_brothers = [brother for brother in brothers if brother in all_fingers]
                if digit_brothers and digit_brothers not in self.fingerMatchList:
                    self.fingerMatchList.append(digit_brothers)


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
            cID = functions.identifyMaster(jnt, self.module_dict)
            if cID[0] in self.validRootList:
                self.get_limb_hierarchy(jnt, isRoot=True, parentIndex=node, r_list=r_list)
            else:
                self.get_limb_hierarchy(jnt, isRoot=False, r_list=r_list)
        return r_list

    def getWholeLimb(self, node):
        multi_guide_jnts = [value["multi_guide"] for value in self.module_dict.values() if
                            value["multi_guide"]]
        limb_dict = {}
        multiList = []
        limb_name, limb_type, limb_side = functions.identifyMaster(node, self.module_dict)

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
                child_limb_name, child_limb_type, child_limb_side = functions.identifyMaster(child, self.module_dict)
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
                distanceList.append(functions.getDistance(socket, initJoint))
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
                    if functions.identifyMaster(root_plug, self.module_dict)[0] not in self.validRootList:
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
                if functions.identifyMaster(root_plug, self.module_dict)[0] not in self.validRootList:
                    FEEDBACK.throw_error("First selection must be a valid root joint node")

            limbCreationList = self.get_limb_hierarchy(root_plug)

        j_def_set = None

        if not self.get("seperateSelectionSets"):
            cmds.select(d=True)
            if not cmds.objExists("def_jointsSet_%s" % self.rig_name):
                j_def_set = cmds.sets(name="def_jointsSet_%s" % self.rig_name)
            else:
                j_def_set = "def_jointsSet_%s" % self.rig_name

        total_limb_count = len(limbCreationList)
        limb_counter = 0
        for x in limbCreationList:
            if self.progress_bar:
                limb_counter = limb_counter + 1
                percent = (100 * limb_counter) / total_limb_count
                self.progress_bar.setProperty("value", percent)
                QtWidgets.QApplication.processEvents()

            if x[2] == "R":
                sideVal = "R"
                colorCodes = [self.get("majorRightColor"), self.get("majorLeftColor")]
            elif x[2] == "L":
                sideVal = "L"
                colorCodes = [self.get("majorLeftColor"), self.get("minorLeftColor")]
            else:
                sideVal = "C"
                colorCodes = [self.get("majorCenterColor"), self.get("minorCenterColor")]

            if self.get("seperateSelectionSets"):
                set_name = "def_%s_%s_Set" % (x[1], x[2])
                set_name = functions.uniqueName(set_name)
                j_def_set = cmds.sets(name=set_name)

            # suffix = "%s_%s" % (sideVal, x[1].capitalize()) if sideVal != "C" else x[1].capitalize()
            module = "modules.{0}.{1}".format(x[1], x[1].capitalize())
            flags = "build_data={0}".format(x[0])
            construct_command = "{0}({1})".format(module, flags)

            limb = eval(construct_command)
            limb.colorCodes = colorCodes
            limb.createLimb()

            ##############################################
            if add_limb:
                cmds.parent(limb.limbPlug, parent_socket)
                ## Good parenting / scale connections
                ## get the holder group
                self.rootGroup = functions.getParent(master_cont)
                ## Create the holder group if it does not exist
                scaleGrpPiv = functions.getWorldTranslation(limb.limbPlug)
                cmds.xform(limb.scaleGrp, piv=scaleGrpPiv, ws=True)
                ## pass the attributes

                functions.attrPass(limb.scaleGrp, master_cont, values=True, daisyChain=True, overrideEx=False)
                cmds.parent(limb.limbGrp, self.rootGroup)
                for sCon in limb.scaleConstraints:
                    cmds.scaleConstraint(master_cont, sCon)
            ##############################################
            else:
                if self.autoSwitchers:
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

                # else:
                #     parentSocket = self.cont_placement

                    cmds.parent(limb.limbPlug, parentSocket)

                ## Good parenting / scale connections
                scaleGrpPiv = functions.getWorldTranslation(limb.limbPlug)
                cmds.xform(limb.scaleGrp, piv=scaleGrpPiv, ws=True)
                ## pass the attributes

                functions.attrPass(limb.scaleGrp, "pref_cont", values=True, daisyChain=True, overrideEx=False)
                cmds.parent(limb.limbGrp, "trigger_grp")
                # for sCon in limb.scaleConstraints:
                #     cmds.scaleConstraint(self.cont_master, sCon)
                for sCon in limb.scaleConstraints:
                    cmds.scaleConstraint("pref_cont", sCon)
            self.totalDefJoints += limb.deformerJoints
            if j_def_set:
                cmds.sets(limb.deformerJoints, add=j_def_set)