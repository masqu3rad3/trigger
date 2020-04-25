"""New rig builder module"""
from maya import cmds
from trigger.core import feedback
from trigger.modules import all_modules_data
import trigger.library.functions as extra
import trigger.library.controllers as ic
import trigger.modules.arm as arm
import trigger.modules.leg as leg
import trigger.modules.head as neckAndHead
import trigger.modules.spine as spine
import trigger.modules.tail as simpleTail
import trigger.modules.digits as finger
import trigger.modules.tentacle as tentacle
import trigger.modules.root as root
import trigger.utils.space_switcher_old as anchorMaker
import trigger.library.tools as tools
from trigger.core import io

from trigger.Qt import QtWidgets

# import logging
# LOG = logging.getLogger(__name__)
# LOG.setLevel(logging.INFO)
FEEDBACK = feedback.Feedback(logger_name=__name__)

class Builder(object):
    def __init__(self, name="trigger", progress_bar=None):
        self.progress_bar = progress_bar
        if self.progress_bar:
            self.progress_bar.setProperty("value", 0)
        self.rig_name = name
        self.validRootList = [values[0] for values in all_modules_data.MODULE_DICTIONARY.values()]
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

    def start_building(self, root=None):
        if not root:
            selection = cmds.ls(sl=True)
            if len(selection) == 1:
                root = selection[0]
            else:
                FEEDBACK.warning("Select a single root joint")
        if not cmds.objectType(root, isType="joint"):
            FEEDBACK.error("root is not a joint")
        root_name, root_type, root_side = extra.identifyMaster(root)
        if root_name not in self.validRootList:
            FEEDBACK.error("selected joint is not in the valid root list")

        self.rootGroup = cmds.group(name=(extra.uniqueName("{0}_rig".format(self.root_name))), em=True)

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
        children = cmds.listRelatives(node, children=True, type="joint")
        children = children if children else []
        for jnt in children:
            cID = extra.identifyMaster(jnt)
            if cID[0] in self.validRootList:
                self.getLimbProperties(jnt, isRoot=True, parentIndex=node)
            else:
                self.getLimbProperties(jnt, isRoot=False)

    def createMasters(self):
        """
        This method creates master controllers (Placement and Master)
        Returns: None

        """
        icon = ic.Icon()
        self.cont_placement, dmp = icon.createIcon("Circle", iconName=extra.uniqueName("cont_Placement"),
                                                   scale=(self.hipDistance, self.hipDistance, self.hipDistance))
        self.cont_master, dmp = icon.createIcon("TriCircle", iconName=extra.uniqueName("cont_Master"), scale=(
        self.hipDistance * 1.5, self.hipDistance * 1.5, self.hipDistance * 1.5))

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

    def getDimensions(self, rootNode):
        """
        Collects all the joints under the rootNode hierarchy calculates necessary cross-limb distances for scale size
        Args:
            rootNode: (string) All the hiearchy under this will be collected

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
