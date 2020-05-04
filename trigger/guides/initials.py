from maya import cmds
import maya.api.OpenMaya as om

from trigger.core.undo_dec import undo
from trigger.library import functions as extra

from trigger import modules
from trigger.core import settings

from trigger.core import feedback

FEEDBACK = feedback.Feedback(logger_name=__name__)


class Initials(settings.Settings):

    def __init__(self):
        super(Initials, self).__init__()
        # settings = st.Settings("triggerSettings.json")
        self.parseSettings()
        self.projectName = "tikAutoRig"
        self.module_dict = modules.all_modules_data.MODULE_DICTIONARY
        self.valid_limbs = self.module_dict.keys()
        self.non_sided_limbs = [limb for limb in self.valid_limbs if not self.module_dict[limb]["sided"]]

    def parseSettings(self):

        parsingDictionary = {u'+x': (1, 0, 0),
                             u'+y': (0, 1, 0),
                             u'+z': (0, 0, 1),
                             u'-x': (-1, 0, 0),
                             u'-y': (0, -1, 0),
                             u'-z': (0, 0, -1)
                             }
        self.upVector_asString = self.get("upAxis")
        self.lookVector_asString = self.get("lookAxis")
        self.mirrorVector_asString = self.get("mirrorAxis")

        self.upVector = om.MVector(parsingDictionary[self.get("upAxis")])
        self.lookVector = om.MVector(parsingDictionary[self.get("lookAxis")])
        self.mirrorVector = om.MVector(parsingDictionary[self.get("mirrorAxis")])

        # get transformation matrix:
        self.upVector.normalize()
        self.lookVector.normalize()
        # get the third axis with the cross vector
        side_vect = self.upVector ^ self.lookVector
        # recross in case up and front were not originally orthoganl:
        front_vect = side_vect ^ self.upVector
        # the new matrix is
        self.tMatrix = om.MMatrix(((side_vect.x, side_vect.y, side_vect.z, 0),
                                   (self.upVector.x, self.upVector.y, self.upVector.z, 0),
                                   (front_vect.x, front_vect.y, front_vect.z, 0), (0, 0, 0, 1)))


    def autoGet(self, parentBone):
        """
        Gets the mirror of the given object by its name. Returns the left if it finds right and vice versa
        Args:
            parentBone: (pymel object) the object which name will be checked

        Returns: (Tuple) None/pymel object, alignment of the given Obj(string),
                alignment of the returned Obj(string)  Ex.: (bone_left, "left", "right")

        """
        if not cmds.objExists(parentBone):
            FEEDBACK.warning("Bones cannot be identified automatically")
            return None, None, None
        if "_right" in parentBone:
            mirrorBoneName = parentBone.replace("_right", "_left")
            alignmentGiven = "right"
            alignmentReturn = "left"
        elif "_left" in parentBone:
            mirrorBoneName = parentBone.replace("_left", "_right")
            alignmentGiven = "left"
            alignmentReturn = "right"
        elif "_c" in parentBone:
            return None, "both", None
        else:
            FEEDBACK.warning("Bones cannot be identified automatically")
            return None, None, None
        if cmds.objExists(mirrorBoneName):
            return mirrorBoneName, alignmentGiven, alignmentReturn
        else:
            FEEDBACK.warning("cannot find mirror bone automatically")
            return None, alignmentGiven, None

    @undo
    def initLimb(self, limb_name, whichSide="left",
                 segments=3, constrainedTo=None, parentNode=None, defineAs=False, *args, **kwargs):

        if limb_name not in self.valid_limbs:
            FEEDBACK.throw_error("%s is not a valid limb" % limb_name)

        currentselection = cmds.ls(sl=True)

        ## Create the holder group if it does not exist
        holderGroup = "{0}_refGuides".format(self.projectName)
        if not cmds.objExists(holderGroup):
            holderGroup = cmds.group(name=holderGroup, em=True)

        ## skip side related stuff for no-side related limbs
        if limb_name in self.non_sided_limbs:
            whichSide = "c"
            side = "C"
        else:
            ## check validity of side arguments
            valid_sides = ["left", "right", "center", "both", "auto"]
            if whichSide not in valid_sides:
                FEEDBACK.throw_error(
                    "side argument '%s' is not valid. Valid arguments are: %s" % (whichSide, valid_sides))
            if len(cmds.ls(sl=True, type="joint")) != 1 and whichSide == "auto" and defineAs == False:
                FEEDBACK.throw_error("You need to select a single joint to use Auto method")
                return
            ## get the necessary info from arguments
            if whichSide == "left":
                side = "L"
            elif whichSide == "right":
                side = "R"
            else:
                side = "C"

        if (segments + 1) < 2:
            FEEDBACK.throw_error("Define at least 2 segments")
            return

        suffix = extra.uniqueName("%sGrp_%s" % (limb_name, whichSide)).replace("%sGrp_" % (limb_name), "")

        ## if defineAs is True, define the selected joints as the given limb instead creating new ones.
        if defineAs:
            self.convertSelectionToInits(limb_name, jointList=currentselection, whichside=whichSide, suffix=suffix)
            return

        if not parentNode:
            if cmds.ls(sl=True, type="joint"):
                j = cmds.ls(sl=True)[-1]
                try:
                    if extra.identifyMaster(j)[1] in self.valid_limbs:
                        masterParent = cmds.ls(sl=True)[-1]
                    else:
                        masterParent = None
                except KeyError:
                    masterParent = None
            else:
                masterParent = None
        else:
            masterParent = parentNode
        if whichSide == "both":
            locators1, jnt_dict_side1 = self.initLimb(limb_name, "left", segments=segments)
            locators2, jnt_dict_side2 = self.initLimb(limb_name, "right", constrainedTo=locators1, segments=segments)
            jnt_dict_side1.update(jnt_dict_side2)
            return (locators1 + locators2), jnt_dict_side1
        if whichSide == "auto" and masterParent:
            mirrorParent, givenAlignment, returnAlignment = self.autoGet(masterParent)
            locators1, jnt_dict_side1 = self.initLimb(limb_name, givenAlignment, segments=segments)
            if mirrorParent:
                locators2, jnt_dict_side2 = self.initLimb(limb_name, returnAlignment, constrainedTo=locators1, parentNode=mirrorParent,
                              segments=segments)
                total_locators = locators1 + locators2
                jnt_dict_side1.update(jnt_dict_side2)
            else:
                total_locators = locators1
            return total_locators, jnt_dict_side1

        limbGroup = cmds.group(em=True, name="%sGrp_%s" % (limb_name, suffix))
        cmds.parent(limbGroup, holderGroup)
        cmds.select(d=True)

        module = "modules.{0}.{1}".format(limb_name, "Guides")
        flags = "side='{0}', " \
                "suffix='{1}', " \
                "segments={2}, " \
                "tMatrix={3}, " \
                "upVector={4}, " \
                "mirrorVector={5}, " \
                "lookVector={6}".format(side, suffix, segments, self.tMatrix,
                                        self.upVector, self.mirrorVector, self.lookVector)

        extra_arg_list = []
        for key, value in kwargs.items():
            if type(value) == str:
                extra_arg_list.append("%s='%s'" % (key, value))
            else:
                extra_arg_list.append("%s=%s" % (key, value))

        # extra_arg_list = ["%s='%s'" %(key, value) for key, value in kwargs.items() if (type(value) == str) else 12]
        extra_flags = ", ".join(extra_arg_list)
        construct_command = "{0}({1},{2})".format(module, flags, extra_flags)
        guide = eval(construct_command)
        guide.createGuides()

        for jnt in guide.guideJoints:
            cmds.setAttr("%s.displayLocalAxis" % jnt, 1)
            cmds.setAttr("%s.drawLabel" % jnt, 1)

        if guide.side == "C":
            extra.colorize(guide.guideJoints, self.get("majorCenterColor"), shape=False)
        if guide.side == "L":
            extra.colorize(guide.guideJoints, self.get("majorLeftColor"), shape=False)
        if guide.side == "R":
            extra.colorize(guide.guideJoints, self.get("majorRightColor"), shape=False)

        cmds.select(d=True)


        ### Constrain locating

        loc_grp = cmds.group(name=("locGrp_%s" % suffix), em=True)
        cmds.setAttr("{0}.v".format(loc_grp), 0)
        locatorsList = []

        for jnt in range(0, len(guide.guideJoints)):
            locator = cmds.spaceLocator(name="loc_%s" % guide.guideJoints[jnt])[0]
            locatorsList.append(locator)
            if constrainedTo:
                extra.alignTo(locator, guide.guideJoints[jnt], position=True, rotation=False)
                extra.connectMirror(constrainedTo[jnt], locatorsList[jnt], mirrorAxis=self.mirrorVector_asString)

                extra.alignTo(guide.guideJoints[jnt], locator, position=True, rotation=False)
                cmds.parentConstraint(locator, guide.guideJoints[jnt], mo=True)
                # extra.matrixConstraint(locator, limbJoints[jnt], mo=True)
            else:
                cmds.parentConstraint(guide.guideJoints[jnt], locator, mo=False)
                # extra.matrixConstraint(limbJoints[jnt], locator, mo=False)

            cmds.parent(locator, loc_grp)
        cmds.parent(loc_grp, limbGroup)

        ### MOVE THE LIMB TO THE DESIRED LOCATION
        if masterParent:
            if not constrainedTo:
                # align the none constrained near to the selected joint
                extra.alignTo(guide.guideJoints[0], masterParent)
                # move it a little along the mirrorAxis
                # move it along offsetvector
                cmds.move(guide.offsetVector[0], guide.offsetVector[1], guide.offsetVector[2], guide.guideJoints[0],
                          relative=True)
            else:
                for joint in guide.guideJoints:
                    extra.lockAndHide(joint, ["tx", "ty", "tz", "rx", "ry", "rz"], hide=False)
            cmds.parent(guide.guideJoints[0], masterParent)
        else:
            cmds.parent(guide.guideJoints[0], limbGroup)
        cmds.select(currentselection)

        # cmds.undoInfo(closeChunk=True)
        return locatorsList, {side: guide.guideJoints}

    def _getMirror(self, vector):
        """Returns reflection of the vector along the mirror axis"""
        return vector - 2 * (vector * self.mirrorVector) * self.mirrorVector

    @undo
    def initHumanoid(self, spineSegments=3, neckSegments=3, fingers=5):
        _, spine_dict = self.initLimb("spine", "auto", segments=spineSegments)
        root = spine_dict["C"][0]
        chest = spine_dict["C"][-1]
        cmds.select(root)
        _, leg_dict = self.initLimb("leg", "auto")
        cmds.select(chest)
        _, arm_dict = self.initLimb("arm", "auto")
        _, head_dict = self.initLimb("head", "auto", segments=neckSegments)
        left_hand = arm_dict["L"][-1]
        fingers = []
        for nmb in range(5):
            cmds.select(left_hand)
            _, finger_dict = self.initLimb("finger", whichSide="auto")
            fingers.append(finger_dict["L"])

        thumb_pos_data = [(1.1, 0.9, 0.25), (0.8, 0.0, 0.0), (0.55, 0.0, 0.00012367864829724757), (0.45, 0.0, 0.0)]
        thumb_rot_data = [(31.0, 45.0, 3.0000000000000004), (-1.0, -2.0, 17.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)]
        index_pos_data = [(2.0, 0.55, 0.0), (1.0, 0.0, 0.0), (0.65, 0.0, 0.0), (0.6, 0.0, 0.0)]
        index_rot_data = [(1.0, 17.0, -3.0000000000000004), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)]
        middle_pos_data = [(2.0, -0.05, -0.09983537560644819), (0.9997424668383346, 0.0, 0.0), (0.7, 0.0, 0.0), (0.7, 0.0, 0.0)]
        middle_rot_data = [(0.0, 7.805352401908098, -0.9999999999999998), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)]
        ring_pos_data = [(1.8, -0.55, -0.10011550541107042), (0.95, 0.0, 0.0), (0.7, 0.0, 0.0), (0.6, 0.0, 0.0)]
        ring_rot_data = [(0.0, -5.0, -1.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)]
        pinky_pos_data = [(1.5, -1.1, 0.0), (0.8, 0.0, 0.0), (0.5, 0.0, 0.0), (0.5, 0.0, 0.0)]
        pinky_rot_data = [(0.0, -12.000000000000002, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)]


        for nmb, member in enumerate(fingers[0]):
            cmds.xform(member, a=True, t=thumb_pos_data[nmb], ro=thumb_rot_data[nmb])
        cmds.setAttr("%s.Finger_Type" % fingers[0][0], 1)

        for nmb, member in enumerate(fingers[1]):
            cmds.xform(member, a=True, t=index_pos_data[nmb], ro=index_rot_data[nmb])
        cmds.setAttr("%s.Finger_Type" % fingers[1][0], 2)

        for nmb, member in enumerate(fingers[2]):
            cmds.xform(member, a=True, t=middle_pos_data[nmb], ro=middle_rot_data[nmb])
        cmds.setAttr("%s.Finger_Type" % fingers[2][0], 3)

        for nmb, member in enumerate(fingers[3]):
            cmds.xform(member, a=True, t=ring_pos_data[nmb], ro=ring_rot_data[nmb])
        cmds.setAttr("%s.Finger_Type" % fingers[3][0], 4)

        for nmb, member in enumerate(fingers[4]):
            cmds.xform(member, a=True, t=pinky_pos_data[nmb], ro=pinky_rot_data[nmb])
        cmds.setAttr("%s.Finger_Type" % fingers[4][0], 5)

    def convertSelectionToInits(self, limbType, jointList=[], suffix="", whichside=""):

        ## // TODO PAY ATTENTION HERE: THIS METHOD IS BROKEN

        ## get the selection
        if whichside == "left":
            side = 1
            extra.colorize(jointList, self.get("majorLeftColor"), shape=False)
        elif whichside == "right":
            side = 2
            extra.colorize(jointList, self.get("majorRightColor"), shape=False)
        else:
            side = 0
            extra.colorize(jointList, self.get("majorCenterColor"), shape=False)

        self.createAxisAttributes(jointList[0])

        if limbType == "spine":
            if len(jointList) < 2:
                FEEDBACK.warning("You need to select at least 2 joints for spine conversion\nNothing Changed")
                return
            for j in range(len(jointList)):
                cmds.select(jointList[j])
                cmds.setAttr("%s.side" % jointList[j], 0)
                cmds.setAttr("%s.drawLabel" % jointList[j], 1)
                ## if it is the first jointList
                if j == 0:
                    type = 18
                    cmds.setAttr("%s.type" % jointList[j], type)
                    cmds.setAttr("%s.otherType" % jointList[j], "SpineRoot", type="string")

                    if not cmds.attributeQuery("resolution", node=jointList[j], exists=True):
                        cmds.addAttr(shortName="resolution", longName="Resolution", defaultValue=4, minValue=1,
                                     at="long", k=True)
                    if not cmds.attributeQuery("dropoff", node=jointList[j], exists=True):
                        cmds.addAttr(shortName="dropoff", longName="DropOff", defaultValue=1.0, minValue=0.1,
                                     at="float", k=True)
                    if not cmds.attributeQuery("twistType", node=jointList[j], exists=True):
                        cmds.addAttr(at="enum", k=True, shortName="twistType", longName="Twist_Type",
                                     en="regular:infinite")
                    if not cmds.attributeQuery("mode", node=jointList[j], exists=True):
                        cmds.addAttr(at="enum", k=True, shortName="mode", longName="Mode",
                                     en="equalDistance:sameDistance")

                    cmds.setAttr(jointList[j].radius, 3)

                elif jointList[j] == jointList[-1]:
                    type = 18
                    cmds.setAttr("%s.type" % jointList[j], type)
                    cmds.setAttr("%s.otherType" % jointList[j], "SpineEnd", type="string")

                else:
                    type = 6
                    cmds.setAttr("%s.type" % jointList[j], type)

        if limbType == "tail":
            if len(jointList) < 2:
                FEEDBACK.warning("You need to select at least 2 joints for tail conversion\nNothing Changed")
                return
            for j in range(len(jointList)):
                cmds.select(jointList[j])
                cmds.setAttr("%s.side" % jointList[j], side)
                cmds.setAttr("%s.drawLabel" % jointList[j], 1)

                ## if it is the first selection
                if j == 0:
                    cmds.setAttr("%s.type" % jointList[j], 18)
                    cmds.setAttr("%s.otherType" % jointList[j], "TailRoot", type="string")
                else:
                    cmds.setAttr("%s.type" % jointList[j], 18)
                    cmds.setAttr("%s.otherType" % jointList[j], "Tail", type="string")

        if limbType == "arm":
            if not len(jointList) == 4:
                FEEDBACK.warning("You must select exactly 4 joints to define the chain as Arm\nNothing Changed")
                return
            cmds.setAttr("%s.side" % jointList[0], side)
            cmds.setAttr("%s.type" % jointList[0], 9)
            cmds.setAttr("%s.side" % jointList[1], side)
            cmds.setAttr("%s.type" % jointList[1], 10)
            cmds.setAttr("%s.side" % jointList[2], side)
            cmds.setAttr("%s.type" % jointList[2], 11)
            cmds.setAttr("%s.side" % jointList[3], side)
            cmds.setAttr("%s.type" % jointList[3], 12)

        if limbType == "leg":
            if not len(jointList) == 10:
                FEEDBACK.warning(
                    "You must select exactly 10 joints to define the chain as Leg\nNothing Changed\nCorrect jointList order is Root -> Hip -> Knee -> Foot -> Ball -> Heel Pivot -> Toe Pivot -> Bank In Pivot -> Bank Out Pivot")
                return
            cmds.setAttr("%s.side" % jointList[0], side)
            cmds.setAttr("%s.type" % jointList[0], 18)
            cmds.setAttr("%s.otherType" % jointList[0], "LegRoot", type="string")
            cmds.setAttr("%s.side" % jointList[1], side)
            cmds.setAttr("%s.type" % jointList[1], 2)
            cmds.setAttr("%s.side" % jointList[2], side)
            cmds.setAttr("%s.type" % jointList[2], 3)
            cmds.setAttr("%s.side" % jointList[3], side)
            cmds.setAttr("%s.type" % jointList[3], 4)

            cmds.setAttr("%s.side" % jointList[4], side)
            cmds.setAttr("%s.type" % jointList[4], 18)
            cmds.setAttr("%s.otherType" % jointList[4], "Ball", type="string")

            cmds.setAttr("%s.side" % jointList[5], side)
            cmds.setAttr("%s.type" % jointList[5], 5)

            cmds.setAttr("%s.side" % jointList[6], side)
            cmds.setAttr("%s.type" % jointList[6], 18)
            cmds.setAttr("%s.otherType" % jointList[6], "HeelPV", type="string")
            cmds.setAttr("%s.side" % jointList[7], side)
            cmds.setAttr("%s.type" % jointList[7], 18)
            cmds.setAttr("%s.otherType" % jointList[7], "ToePV", type="string")
            cmds.setAttr("%s.side" % jointList[8], side)
            cmds.setAttr("%s.type" % jointList[8], 18)
            cmds.setAttr("%s.otherType" % jointList[8], "BankIN", type="string")
            cmds.setAttr("%s.side" % jointList[9], side)
            cmds.setAttr("%s.type" % jointList[9], 18)
            cmds.setAttr("%s.otherType" % jointList[9], "BankOUT", type="string")

        if limbType == "head":
            if not len(jointList) >= 3:
                FEEDBACK.warning(
                    "You must select exactly 3 joints to define the chain as Neck and Head\nNothing Changed")
                return
            for i in range(len(jointList)):
                if i == 0:
                    cmds.setAttr("%s.type" % jointList[i], 18)
                    cmds.setAttr("%s.otherType" % jointList[i], "NeckRoot", type="string")
                    cmds.select(jointList[i])

                    if not cmds.attributeQuery("resolution", node=jointList[i], exists=True):
                        cmds.addAttr(shortName="resolution", longName="Resolution", defaultValue=4, minValue=1,
                                     at="long", k=True)
                    if not cmds.attributeQuery("dropoff", node=jointList[i], exists=True):
                        cmds.addAttr(shortName="dropoff", longName="DropOff", defaultValue=1.0, minValue=0.1,
                                     at="float", k=True)
                    if not cmds.attributeQuery("twistType", node=jointList[i], exists=True):
                        cmds.addAttr(at="enum", k=True, shortName="twistType", longName="Twist_Type",
                                     en="regular:infinite")
                    if not cmds.attributeQuery("mode", node=jointList[i], exists=True):
                        cmds.addAttr(at="enum", k=True, shortName="mode", longName="Mode",
                                     en="equalDistance:sameDistance")

                elif jointList[i] == jointList[-2]:
                    cmds.setAttr("%s.type" % jointList[i], 8)
                elif jointList[i] == jointList[-1]:
                    cmds.setAttr("%s.side" % jointList[i], 0)
                    cmds.setAttr("%s.type" % jointList[i], 18)
                    cmds.setAttr("%s.otherType" % jointList[i], "HeadEnd", type="string")
                    cmds.setAttr("%s.drawLabel" % jointList[i], 1)
                else:
                    cmds.setAttr("%s.type" % jointList[i], 7)
                cmds.setAttr("%s.drawLabel" % jointList[i], 1)

        if limbType == "finger":
            if not len(jointList) > 1:
                FEEDBACK.warning("You must at least 2 joints to define the chain as Finger\nNothing Changed")
                return
            for i in range(len(jointList)):
                cmds.setAttr("%s.side" % jointList[i], 0)

                if i == 0:
                    cmds.setAttr("%s.type" % jointList[i], 18)
                    cmds.setAttr("%s.otherType" % jointList[i], "FingerRoot", type="string")
                    cmds.setAttr("%s.drawLabel" % jointList[i], 1)
                    if not cmds.attributeQuery("fingerType", node=jointList[i], exists=True):
                        cmds.addAttr(jointList[i], shortName="fingerType", longName="Finger_Type", at="enum",
                                     en="Extra:Thumb:Index:Middle:Ring:Pinky:Toe", k=True)
                else:
                    cmds.setAttr("%s.type" % jointList[i], 13)

        if limbType == "tentacle":
            if not len(jointList) > 1:
                FEEDBACK.warning("minimum segments required for the tentacle is two. current: %s" % len(jointList))
                return

            for j in range(len(jointList)):
                cmds.select(jointList[j])
                cmds.setAttr("%s.side" % jointList[j], side)
                cmds.setAttr("%s.drawLabel" % jointList[j], 1)
                ## if it is the first selection
                if j == 0:
                    cmds.setAttr("%s.type" % jointList[j], 18)
                    cmds.setAttr("%s.otherType" % jointList[j], "TentacleRoot", type="string")
                    if not cmds.attributeQuery("contRes", node=jointList[j], exists=True):
                        cmds.addAttr(shortName="contRes", longName="Cont_Resolution", defaultValue=5, minValue=1,
                                     at="long", k=True)
                    if not cmds.attributeQuery("jointRes", node=jointList[j], exists=True):
                        cmds.addAttr(shortName="jointRes", longName="Joint_Resolution", defaultValue=25, minValue=1,
                                     at="long", k=True)
                    if not cmds.attributeQuery("deformerRes", node=jointList[j], exists=True):
                        cmds.addAttr(shortName="deformerRes", longName="Deformer_Resolution", defaultValue=25,
                                     minValue=1,
                                     at="long", k=True)
                    if not cmds.attributeQuery("dropoff", node=jointList[j], exists=True):
                        cmds.addAttr(shortName="dropoff", longName="DropOff", defaultValue=2.0, minValue=0.1,
                                     at="float", k=True)
                else:
                    cmds.setAttr("%s.type" % jointList[j], 18)
                    cmds.setAttr("%s.otherType" % jointList[j], "Tentacle", type="string")


