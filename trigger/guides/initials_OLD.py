from maya import cmds
import maya.api.OpenMaya as om
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

        parsingDictionary = {u'+x':(1,0,0),
                             u'+y':(0,1,0),
                             u'+z':(0,0,1),
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
        self.tMatrix  = om.MMatrix(((side_vect.x, side_vect.y, side_vect.z, 0), (self.upVector.x, self.upVector.y, self.upVector.z, 0), (front_vect.x, front_vect.y, front_vect.z, 0), (0, 0, 0, 1)))

        # self.majorLeftColor = self.get("majorLeftColor")
        # self.minorLeftColor = self.get("minorLeftColor")
        # self.majorRightColor = self.get("majorRightColor")
        # self.minorRightColor = self.get("minorRightColor")
        # self.majorCenterColor = self.get("majorCenterColor")
        # self.minorCenterColor = self.get("minorCenterColor")

    def autoGet (self, parentBone):
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

    def initLimb (self, limb_name, whichSide="left",
                  segments=3, constrainedTo = None, parentNode=None, defineAs=False):
        if limb_name not in self.valid_limbs:
            FEEDBACK.throw_error("%s is not a valid limb" %limb_name)
            
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
                FEEDBACK.throw_error("side argument '%s' is not valid. Valid arguments are: %s" %(whichSide, valid_sides))
            if len(cmds.ls(sl=True, type="joint")) != 1 and whichSide == "auto" and defineAs == False:
                FEEDBACK.warning("You need to select a single joint to use Auto method")
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
            constLocs = self.initLimb(limb_name, "left", segments=segments)
            self.initLimb(limb_name, "right", constrainedTo=constLocs, segments=segments)
            return
        if whichSide == "auto" and masterParent:
            mirrorParent, givenAlignment, returnAlignment = self.autoGet(masterParent)
            constLocs = self.initLimb(limb_name, givenAlignment, segments=segments)
            if mirrorParent:
                self.initLimb(limb_name, returnAlignment, constrainedTo=constLocs, parentNode=mirrorParent, segments=segments)
            return

        limbGroup = cmds.group(em=True, name="%sGrp_%s" %(limb_name, suffix))
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
        construct_command = "{0}({1})".format(module, flags)
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

        # ### FROM HERE IT WILL BE LIMB SPECIFIC ###
        # 
        # if limb_name == "spine":
        #     limbJoints, offsetVector = self.initialSpine(segments=segments, suffix=suffix)
        # 
        # if limb_name == "arm":
        #     limbJoints, offsetVector = self.initialArm(side=side, suffix=suffix)
        # 
        # if limb_name == "leg":
        #     limbJoints, offsetVector = self.initialLeg(side=side, suffix=suffix)
        # 
        # if limb_name == "hand":
        #     limbJoints, jRoots = self.initialHand(fingerCount=fingerCount, side=side, suffix=suffix)
        # 
        # if limb_name == "head":
        #     limbJoints, offsetVector = self.initialNeck(segments=segments, suffix=suffix)
        # 
        # if limb_name == "tail":
        #     limbJoints, offsetVector = self.initialTail(segments=segments, side=side, suffix=suffix)
        # 
        # if limb_name == "finger":
        #     limbJoints, offsetVector = self.initialFinger(segments=segments, side=side, suffix=suffix, thumb=thumb)
        # 
        # if limb_name == "tentacle":
        #     limbJoints, offsetVector = self.initialTentacle(segments=segments, side=side, suffix=suffix)
        # 
        # if limb_name == "root":
        #     limbJoints, offsetVector = self.initialRoot(suffix=suffix)

        ### Constrain locating

        loc_grp = cmds.group(name=("locGrp_%s" %suffix), em=True)
        cmds.setAttr("{0}.v".format(loc_grp), 0)
        locatorsList=[]

        # for num, jnt in enumerate(guide.guideJoints):
        #     locator = cmds.spaceLocator(name="loc_%s" % jnt)[0]
        #     locatorsList.append(locator)
        #     if constrainedTo:
        #         extra.alignTo(locator, jnt, position=True, rotation=False)
        #         extra.connectMirror(jnt, locatorsList[num], mirrorAxis=self.mirrorVector_asString)
        #
        #         extra.alignTo(jnt, locator, position=True, rotation=False)
        #         cmds.parentConstraint(locator, jnt, mo=True)
        #     else:
        #         cmds.parentConstraint(jnt, locator, mo=False)

        
        for jnt in range (0,len(guide.guideJoints)):
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
                cmds.move(guide.offsetVector[0], guide.offsetVector[1], guide.offsetVector[2], guide.guideJoints[0], relative=True)
            else:
                for joint in guide.guideJoints:
                    extra.lockAndHide(joint, ["tx", "ty", "tz", "rx", "ry", "rz"], hide=False)
            cmds.parent(guide.guideJoints[0], masterParent)
        else:
            cmds.parent(guide.guideJoints[0], limbGroup)
        cmds.select(currentselection)

        return locatorsList

    def _getMirror(self, vector):
        """Returns reflection of the vector along the mirror axis"""
        return vector-2*(vector * self.mirrorVector)*self.mirrorVector

    def initialRoot(self, suffix):
        """
        Creates a single simple root joint to connect or bridge limbs
        Args:
            transformKey: (List) the keyword for transformation matrix. transformator function will use this key to orienct joint in space
            suffix: (String) name suffix - must be unique

        Returns: (List) rootJoint

        """
        cmds.select(d=True)
        rootInit = cmds.joint(name="root_{0}".format(suffix))
        cmds.setAttr("{0}.type".format(rootInit), 1)
        self.createAxisAttributes(rootInit)
        cmds.setAttr("{0}.radius".format(rootInit), 3)
        cmds.setAttr("{0}.drawLabel".format(rootInit), 1)
        # offsetVector = om.MVector(0,0,0)
        offsetVector = om.MVector(0,0,0)
        extra.colorize(rootInit, self.majorCenterColor, shape=False)

        return [rootInit], offsetVector

    def initialSpine(self, segments, suffix, side=0):
        """
        Creates a preset spine hieararchy with given segments
        Args:
            transformKey: the keyword for transformation matrix. transformator function will use this key to orienct joint in space
            segments: (int) segment count
            suffix: (String) name suffix - must be unique

        Returns: (List) jointList

        """
        sideMult = -1 if side == 2 else 1

        rPoint = om.MVector(0, 14.0, 0) * self.tMatrix

        nPoint = om.MVector(0, 21.0, 0) * self.tMatrix
        offsetVector = (nPoint - rPoint).normal()
        add = (nPoint - rPoint) / ((segments + 1) - 1)
        jointList = []
        for i in range(0, (segments + 1)):
            spine = cmds.joint(p=(rPoint + (add * i)), name="jInit_spine_%s_%s" %(suffix, str(i)))
            cmds.setAttr("%s.side" % spine, 0)
            type = 18
            if i == 0:
                cmds.setAttr("%s.type" % spine, type)
                cmds.setAttr("%s.otherType" % spine, "SpineRoot", type="string")
                cmds.addAttr(shortName="resolution", longName="Resolution", defaultValue=4, minValue=1,
                           at="long", k=True)
                cmds.addAttr(shortName="dropoff", longName="DropOff", defaultValue=1.0, minValue=0.1,
                           at="float", k=True)
                cmds.addAttr(at="enum", k=True, shortName="twistType", longName="Twist_Type", en="regular:infinite")
                cmds.addAttr(at="enum", k=True, shortName="mode", longName="Mode", en="equalDistance:sameDistance")

                self.createAxisAttributes(spine)
                cmds.setAttr("{0}.radius".format(spine), 3)
            elif i == (segments):
                # type = 18
                cmds.setAttr("%s.type" % spine, type)
                cmds.setAttr("%s.otherType" % spine, "SpineEnd", type="string")
            else:
                type = 6
                cmds.setAttr("%s.type" % spine, type)

            jointList.append(spine)
            for i in jointList:
                cmds.setAttr("%s.drawLabel" % i, 1)
                cmds.setAttr("{0}.displayLocalAxis".format(i), 1)

        extra.orientJoints(jointList, worldUpAxis=-self.lookVector, reverseAim=sideMult, reverseUp=sideMult)

        self.spineJointsList.append(jointList)
        extra.colorize(jointList, self.majorCenterColor, shape=False)
        return jointList, offsetVector
    
    def initialLeg(self, side, suffix):
        sideMult = -1 if side == 2 else 1
        if side == 0:
            rootVec = om.MVector(0, 14, 0) * self.tMatrix
            hipVec = om.MVector(0, 10, 0) * self.tMatrix
            kneeVec = om.MVector(0, 5, 1) * self.tMatrix
            footVec = om.MVector(0, 1, 0) * self.tMatrix
            ballVec = om.MVector(0, 0, 2) * self.tMatrix
            toeVec = om.MVector(0, 0, 4) * self.tMatrix
            bankoutVec = om.MVector(-1, 0, 2) * self.tMatrix
            bankinVec = om.MVector(1, 0, 2) * self.tMatrix
            toepvVec = om.MVector(0, 0, 4.3) * self.tMatrix
            heelpvVec = om.MVector(0, 0, -0.2) * self.tMatrix
        else:
            rootVec = om.MVector(2*sideMult,14,0) * self.tMatrix
            hipVec = om.MVector(5*sideMult,10,0) * self.tMatrix
            kneeVec = om.MVector(5*sideMult,5,1) * self.tMatrix
            footVec = om.MVector(5*sideMult,1,0) * self.tMatrix
            ballVec = om.MVector(5*sideMult,0,2) * self.tMatrix
            toeVec = om.MVector(5*sideMult,0,4) * self.tMatrix
            bankoutVec = om.MVector(4*sideMult,0,2) * self.tMatrix
            bankinVec = om.MVector(6*sideMult,0,2) * self.tMatrix
            toepvVec = om.MVector(5*sideMult,0,4.3) * self.tMatrix
            heelpvVec = om.MVector(5*sideMult,0,-0.2) * self.tMatrix

        offsetVector = -((rootVec - hipVec).normal())
        root = cmds.joint(p=rootVec, name=("jInit_LegRoot_%s" % suffix))
        cmds.setAttr("%s.radius" %root, 3)
        hip = cmds.joint(p=hipVec, name=("jInit_Hip_%s" % suffix))
        knee = cmds.joint(p=kneeVec, name=("jInit_Knee_%s" % suffix))
        foot = cmds.joint(p=footVec, name=("jInit_Foot_%s" % suffix))
        extra.orientJoints([root, hip, knee, foot], worldUpAxis=self.mirrorVector, upAxis=(0, 1, 0), reverseAim=sideMult)

        ball = cmds.joint(p=ballVec, name=("jInit_Ball_%s" % suffix))
        toe = cmds.joint(p=toeVec, name=("jInit_Toe_%s" % suffix))
        cmds.select(d=True)
        bankout = cmds.joint(p=bankoutVec, name=("jInit_BankOut_%s" % suffix))
        cmds.select(d=True)
        bankin = cmds.joint(p=bankinVec, name=("jInit_BankIn_%s" % suffix))
        cmds.select(d=True)
        toepv = cmds.joint(p=toepvVec, name=("jInit_ToePv_%s" % suffix))
        cmds.select(d=True)
        heelpv = cmds.joint(p=heelpvVec, name=("jInit_HeelPv_%s" % suffix))

        cmds.parent(heelpv, foot)
        cmds.parent(toepv, foot)
        cmds.parent(bankin, foot)
        cmds.parent(bankout, foot)

        extra.orientJoints([ball, toe], worldUpAxis=self.mirrorVector, upAxis=(0, 1, 0), reverseAim=sideMult)

        cmds.setAttr("%s.side" % root, side)
        cmds.setAttr("%s.type" % root, 18)
        cmds.setAttr("%s.otherType" % root, "LegRoot", type="string")
        cmds.setAttr("%s.displayLocalAxis" %root, 1)

        cmds.setAttr("%s.side" % hip, side)
        cmds.setAttr("%s.type" % hip, 2)
        cmds.setAttr("%s.displayLocalAxis" %hip, 1)

        cmds.setAttr("%s.side" % knee, side)
        cmds.setAttr("%s.type" % knee, 3)
        cmds.setAttr("%s.displayLocalAxis" %knee, 1)

        cmds.setAttr("%s.side" % foot, side)
        cmds.setAttr("%s.type" % foot, 4)
        cmds.setAttr("%s.displayLocalAxis" %foot, 1)

        cmds.setAttr("%s.side" % ball, side)
        cmds.setAttr("%s.type" % ball, 18)
        cmds.setAttr("%s.otherType" % ball, "Ball", type="string")
        cmds.setAttr("%s.displayLocalAxis" %ball, 1)

        cmds.setAttr("%s.side" % toe, side)
        cmds.setAttr("%s.type" % toe, 5)
        cmds.setAttr("%s.displayLocalAxis" %toe, 1)

        cmds.setAttr("%s.side" % heelpv, side)
        cmds.setAttr("%s.type" % heelpv, 18)
        cmds.setAttr("%s.otherType" % heelpv, "HeelPV", type="string")
        cmds.setAttr("%s.side" % toepv, side)
        cmds.setAttr("%s.type" % toepv, 18)
        cmds.setAttr("%s.otherType" % toepv, "ToePV", type="string")
        cmds.setAttr("%s.side" % bankin, side)
        cmds.setAttr("%s.type" % bankin, 18)
        cmds.setAttr("%s.otherType" % bankin, "BankIN", type="string")
        cmds.setAttr("%s.side" % bankout, side)
        cmds.setAttr("%s.type" % bankout, 18)
        cmds.setAttr("%s.otherType" % bankout, "BankOUT", type="string")

        ## custom attributes
        self.createAxisAttributes(root)

        jointList = [root, hip, knee, foot, ball, toe, bankout, bankin, toepv, heelpv]
        for i in jointList:
            cmds.setAttr("%s.drawLabel" % i, 1)

        if side == 0:
            extra.colorize(jointList, self.majorCenterColor, shape=False)
        if side == 1:
            extra.colorize(jointList, self.majorLeftColor, shape=False)
        if side == 2:
            extra.colorize(jointList, self.majorRightColor, shape=False)

        return jointList, offsetVector

    def initialHand(self, fingerCount, side, suffix):
        sideMult = -1 if side == 2 else 1

        jointList = []
        fingerRoots = []

        if fingerCount > 0:
            thumb00vec = om.MVector(0.681*sideMult, -0.143, 0.733) * self.tMatrix
            thumb01vec = om.MVector(1.192*sideMult, -0.21, 1.375) * self.tMatrix
            thumb02vec = om.MVector(1.64*sideMult, -0.477, 1.885) * self.tMatrix
            thumb03vec = om.MVector(2.053*sideMult, -0.724, 2.356) * self.tMatrix

            cmds.select(d=True)

            thumb00 = cmds.joint(p=thumb00vec, name=("jInit_thumb00_%s" % suffix))
            thumb01 = cmds.joint(p=thumb01vec, name=("jInit_thumb01_%s" % suffix))
            thumb02 = cmds.joint(p=thumb02vec, name=("jInit_thumb02_%s" % suffix))
            thumb03 = cmds.joint(p=thumb03vec, name=("jInit_thumb03_%s" % suffix))
            thumbJoints = [thumb00, thumb01, thumb02, thumb03]

            extra.orientJoints(thumbJoints, worldUpAxis=self.upVector, upAxis=(0,-1,0), reverseAim=sideMult,
                               reverseUp=sideMult)
            for i in thumbJoints:
                cmds.setAttr("%s.displayLocalAxis" %i, 1)
                if i == thumbJoints[0]:
                    cmds.setAttr("%s.type" % i, 18)
                    cmds.setAttr("%s.otherType" % i, "FingerRoot", type="string")
                else:
                    cmds.setAttr("%s.type" % i, 13)
                cmds.setAttr("%s.side" % i, side)
            # draw label on knuckles
            cmds.setAttr("%s.drawLabel" % thumbJoints[1], 1)
            self.createAxisAttributes(thumbJoints[0])
            cmds.addAttr(thumbJoints[0], shortName="fingerType", longName="Finger_Type", at="enum",
                       en="Extra:Thumb:Index:Middle:Ring:Pinky:Toe", k=True)
            cmds.setAttr("%s.fingerType" % thumbJoints[0], 1)

            self.fingerJointsList.append(thumbJoints)
            jointList.extend(thumbJoints)
            fingerRoots.append(thumbJoints[0])

        if fingerCount > 1:
            index00vec = om.MVector(1.517*sideMult, 0.05, 0.656) * self.tMatrix
            index01vec = om.MVector(2.494*sideMult, 0.05, 0.868) * self.tMatrix
            index02vec = om.MVector(3.126*sideMult, 0.05, 1.005) * self.tMatrix
            index03vec = om.MVector(3.746*sideMult, 0.05, 1.139) * self.tMatrix
            index04vec = om.MVector(4.278*sideMult, 0.05, 1.254) * self.tMatrix
            cmds.select(d=True)
            index00 = cmds.joint(p=index00vec, name=("jInit_indexF00_%s" % suffix))
            index01 = cmds.joint(p=index01vec, name=("jInit_indexF01_%s" % suffix))
            index02 = cmds.joint(p=index02vec, name=("jInit_indexF02_%s" % suffix))
            index03 = cmds.joint(p=index03vec, name=("jInit_indexF03_%s" % suffix))
            index04 = cmds.joint(p=index04vec, name=("jInit_indexF04_%s" % suffix))
            indexJoints = [index00, index01, index02, index03, index04]
            extra.orientJoints(indexJoints, worldUpAxis=self.upVector, upAxis=(0,-1,0), reverseAim=sideMult,
                               reverseUp=sideMult)
            for i in indexJoints:
                cmds.setAttr("%s.displayLocalAxis" %i, 1)

                if i == indexJoints[0]:
                    cmds.setAttr("%s.type" % i, 18)
                    cmds.setAttr("%s.otherType" % i, "FingerRoot", type="string")
                else:
                    cmds.setAttr("%s.type" % i, 13)
                cmds.setAttr("%s.side" % i, side)
            cmds.setAttr("%s.drawLabel" % index01, 1)
            self.createAxisAttributes(indexJoints[0])
            cmds.addAttr(indexJoints[0], shortName="fingerType", longName="Finger_Type", at="enum",
                       en="Extra:Thumb:Index:Middle:Ring:Pinky:Toe", k=True)
            cmds.setAttr("%s.fingerType" %indexJoints[0], 2)
            self.fingerJointsList.append(indexJoints)
            jointList.extend(indexJoints)
            fingerRoots.append(index00)

        if fingerCount > 2:
            middle00vec = om.MVector(1.597*sideMult, 0.123, 0.063) * self.tMatrix
            middle01vec = om.MVector(2.594*sideMult, 0.123, 0.137) * self.tMatrix
            middle02vec = om.MVector(3.312*sideMult, 0.123, 0.19) * self.tMatrix
            middle03vec = om.MVector(4.012*sideMult, 0.123, 0.242) * self.tMatrix
            middle04vec = om.MVector(4.588*sideMult, 0.123, 0.285) * self.tMatrix
            cmds.select(d=True)
            middle00 = cmds.joint(p=middle00vec, name=("jInit_middleF00_%s" % suffix))
            middle01 = cmds.joint(p=middle01vec, name=("jInit_middleF01_%s" % suffix))
            middle02 = cmds.joint(p=middle02vec, name=("jInit_middleF02_%s" % suffix))
            middle03 = cmds.joint(p=middle03vec, name=("jInit_middleF03_%s" % suffix))
            middle04 = cmds.joint(p=middle04vec, name=("jInit_middleF04_%s" % suffix))
            middleJoints = [middle00, middle01, middle02, middle03, middle04]
            extra.orientJoints(middleJoints, worldUpAxis=self.upVector, upAxis=(0,-1,0), reverseAim=sideMult,
                               reverseUp=sideMult)
            for i in middleJoints:
                cmds.setAttr("%s.displayLocalAxis" %i, 1)
                if i == middleJoints[0]:
                    cmds.setAttr("%s.type" % i, 18)
                    cmds.setAttr("%s.otherType" % i, "FingerRoot", type="string")
                else:
                    cmds.setAttr("%s.type" % i, 13)
                cmds.setAttr("%s.side" % i, side)
            cmds.setAttr("%s.drawLabel" % middle01, 1)
            self.createAxisAttributes(middleJoints[0])
            cmds.addAttr(middleJoints[0], shortName="fingerType", longName="Finger_Type", at="enum",
                       en="Extra:Thumb:Index:Middle:Ring:Pinky:Toe", k=True)
            cmds.setAttr("%s.fingerType" %middleJoints[0], 3)
            self.fingerJointsList.append(middleJoints)
            jointList.extend(middleJoints)
            fingerRoots.append(middle00)

        if fingerCount > 3:
            ring00vec = om.MVector(1.605*sideMult, 0.123, -0.437) * self.tMatrix
            ring01vec = om.MVector(2.603*sideMult, 0.123, -0.499) * self.tMatrix
            ring02vec = om.MVector(3.301*sideMult, 0.123, -0.541) * self.tMatrix
            ring03vec = om.MVector(3.926*sideMult, 0.123, -0.58) * self.tMatrix
            ring04vec = om.MVector(4.414*sideMult, 0.123, -0.58) * self.tMatrix
            cmds.select(d=True)
            ring00 = cmds.joint(p=ring00vec, name=("jInit_ringF00_%s" % suffix))
            ring01 = cmds.joint(p=ring01vec, name=("jInit_ringF01_%s" % suffix))
            ring02 = cmds.joint(p=ring02vec, name=("jInit_ringF02_%s" % suffix))
            ring03 = cmds.joint(p=ring03vec, name=("jInit_ringF03_%s" % suffix))
            ring04 = cmds.joint(p=ring04vec, name=("jInit_ringF04_%s" % suffix))
            ringJoints = [ring00, ring01, ring02, ring03, ring04]
            extra.orientJoints(ringJoints, worldUpAxis=self.upVector, upAxis=(0,-1,0), reverseAim=sideMult,
                               reverseUp=sideMult)
            for i in ringJoints:
                cmds.setAttr("%s.displayLocalAxis" %i, 1)
                if i == ringJoints[0]:
                    cmds.setAttr("%s.type" % i, 18)
                    cmds.setAttr("%s.otherType" % i, "FingerRoot", type="string")
                else:
                    cmds.setAttr("%s.type" % i, 13)
                cmds.setAttr("%s.side" % i, side)
            cmds.setAttr("%s.drawLabel" % ring01, 1)
            self.createAxisAttributes(ringJoints[0])
            cmds.addAttr(ringJoints[0], shortName="fingerType", longName="Finger_Type", at="enum",
                       en="Extra:Thumb:Index:Middle:Ring:Pinky:Toe", k=True)
            cmds.setAttr("%s.fingerType" %ringJoints[0], 4)
            self.fingerJointsList.append(ringJoints)
            jointList.extend(ringJoints)
            fingerRoots.append(ring00)

        if fingerCount > 4:
            pinky00vec = om.MVector(1.405*sideMult, 0, -0.909) * self.tMatrix
            pinky01vec = om.MVector(2.387*sideMult, 0, -1.097) * self.tMatrix
            pinky02vec = om.MVector(2.907*sideMult, 0, -1.196) * self.tMatrix
            pinky03vec = om.MVector(3.378*sideMult, 0, -1.286) * self.tMatrix
            pinky04vec = om.MVector(3.767*sideMult, 0, -1.361) * self.tMatrix
            cmds.select(d=True)
            pinky00 = cmds.joint(p=pinky00vec, name=("jInit_pinkyF00_%s" % suffix))
            pinky01 = cmds.joint(p=pinky01vec, name=("jInit_pinkyF01_%s" % suffix))
            pinky02 = cmds.joint(p=pinky02vec, name=("jInit_pinkyF02_%s" % suffix))
            pinky03 = cmds.joint(p=pinky03vec, name=("jInit_pinkyF03_%s" % suffix))
            pinky04 = cmds.joint(p=pinky04vec, name=("jInit_pinkyF04_%s" % suffix))
            pinkyJoints = [pinky00, pinky01, pinky02, pinky03, pinky04]
            extra.orientJoints(pinkyJoints, worldUpAxis=self.upVector, upAxis=(0,-1,0), reverseAim=sideMult,
                               reverseUp=sideMult)
            for i in pinkyJoints:
                cmds.setAttr("%s.displayLocalAxis" %i, 1)
                if i == pinkyJoints[0]:
                    cmds.setAttr("%s.type" % i, 18)
                    cmds.setAttr("%s.otherType" % i, "FingerRoot", type="string")
                else:
                    cmds.setAttr("%s.type" % i, 13)
                cmds.setAttr("%s.side" % i, side)
            cmds.setAttr("%s.drawLabel" % pinky01, 1)
            self.createAxisAttributes(pinkyJoints[0])
            cmds.addAttr(pinkyJoints[0], shortName="fingerType", longName="Finger_Type", at="enum",
                       en="Extra:Thumb:Index:Middle:Ring:Pinky:Toe", k=True)
            cmds.setAttr("%s.fingerType" %pinkyJoints[0], 5)
            self.fingerJointsList.append(pinkyJoints)
            jointList.extend(pinkyJoints)
            fingerRoots.append(pinky00)
        if fingerCount > 5:
            for x in range(0, (fingerCount - 5)):
                ##//TODO put extra fingers
                pass
        for r in fingerRoots:
            cmds.setAttr("%s.radius" %r, 2)
        if side == 0:
            extra.colorize(jointList, self.majorCenterColor, shape=False)
        if side == 1:
            extra.colorize(jointList, self.majorLeftColor, shape=False)
        if side == 2:
            extra.colorize(jointList, self.majorRightColor, shape=False)

        return jointList, fingerRoots

    def initialNeck(self, segments, suffix, side=0):
        sideMult = -1 if side == 2 else 1
        rPointNeck =  om.MVector(0, 25.757, 0) * self.tMatrix
        nPointNeck =  om.MVector(0, 29.418, 0.817) * self.tMatrix
        pointHead =  om.MVector(0, 32,0.817) * self.tMatrix
        offsetVector = (nPointNeck-rPointNeck).normal()
        addNeck = (nPointNeck - rPointNeck) / ((segments + 1) - 1)
        jointList = []
        for i in range(0, (segments + 1)):
            if not i == (segments):
                head = cmds.joint(p=(rPointNeck + (addNeck * i)), name="jInit_neck_%s_%s" %(suffix, str(i)))
                cmds.setAttr("%s.side" % head, 0)
                if i == 0:
                    cmds.setAttr("%s.type" % head, 18)
                    cmds.setAttr("%s.otherType" % head, "NeckRoot", type="string")
                    cmds.addAttr(shortName="resolution", longName="Resolution", defaultValue=4, minValue=1,
                               at="long", k=True)
                    cmds.addAttr(shortName="dropoff", longName="DropOff", defaultValue=1.0, minValue=0.1,
                               at="float", k=True)
                    cmds.addAttr(at="enum", k=True, shortName="twistType", longName="Twist_Type", en="regular:infinite")
                    cmds.addAttr(at="enum", k=True, shortName="mode", longName="Mode", en="equalDistance:sameDistance")
                    self.createAxisAttributes(head)
                    cmds.setAttr("%s.radius" %head, 3)
                else:
                    cmds.setAttr("%s.type" % head, 7)
            else:
                head= cmds.joint(p=(rPointNeck + (addNeck * i)), name="jInit_head_%s_%s" %(suffix, str(i)))
                cmds.setAttr("%s.type" % head, 8)
                self.createAxisAttributes(head)
            cmds.setAttr("%s.drawLabel" % head, 1)
            jointList.append(head)
        headEnd = cmds.joint(p=pointHead, name="jInit_headEnd_%s_%s" %(suffix, str(i)))
        cmds.setAttr("%s.side" % headEnd, 0)
        cmds.setAttr("%s.type" % headEnd, 18)
        cmds.setAttr("%s.otherType" % headEnd, "HeadEnd", type="string")
        cmds.setAttr("%s.drawLabel" % headEnd, 1)
        jointList.append(headEnd)

        extra.orientJoints(jointList, worldUpAxis=-self.lookVector, reverseAim=sideMult, reverseUp=sideMult)
        map(lambda x: cmds.setAttr("%s.displayLocalAxis" %x, 1), jointList)
        self.neckJointsList.append(jointList)
        extra.colorize(jointList, self.majorCenterColor, shape=False)
        return jointList, offsetVector

    def initialTail(self,  side, segments, suffix):
        sideMult = -1 if side == 2 else 1
        if segments < 1:
            FEEDBACK.warning("minimum segments required for the simple tail is two. current: %s" %segments)
            return

        rPointTail = om.MVector(0, 14, 0) * self.tMatrix
        if side == 0:
            nPointTail = om.MVector(0, 8.075, -7.673) * self.tMatrix
        else:
            nPointTail = om.MVector(7.673*sideMult, 8.075, 0) * self.tMatrix
        offsetVector = (nPointTail-rPointTail).normal()
        addTail = (nPointTail - rPointTail) / ((segments + 1) - 1)
        jointList = []
        for i in range(0, (segments + 1)):
            tail = cmds.joint(p=(rPointTail + (addTail * i)), name="jInit_tail_%s_%s" %(suffix, str(i)))
            cmds.setAttr("%s.side" % tail, side)

            if i == 0:
                cmds.setAttr("%s.type" % tail, 18)
                cmds.setAttr("%s.otherType" % tail, "TailRoot", type="string")
                self.createAxisAttributes(tail)
                cmds.setAttr("%s.radius" %tail, 3)
            else:
                cmds.setAttr("%s.type" % tail, 18)
                cmds.setAttr("%s.otherType" % tail, "Tail", type="string")

            cmds.setAttr("%s.drawLabel" % tail, 1)
            jointList.append(tail)

        self.tailJointsList.append(jointList)
        map(lambda x: cmds.setAttr("%s.displayLocalAxis" %x, 1), jointList)
        extra.orientJoints(jointList, worldUpAxis=self.lookVector, upAxis=(0, 1, 0), reverseAim=sideMult, reverseUp=sideMult)

        if side == 0:
            extra.colorize(jointList, self.majorCenterColor, shape=False)
        if side == 1:
            extra.colorize(jointList, self.majorLeftColor, shape=False)
        if side == 2:
            extra.colorize(jointList, self.majorRightColor, shape=False)

        return jointList, offsetVector

    def initialFinger(self,segments,  side, suffix, thumb=False):
        sideMult = -1 if side == 2 else 1

        if segments < 2:
            FEEDBACK.warning("minimum segments for the fingers are two. current: %s" %segments)
            return

        rPointFinger = om.MVector(0, 0, 0) * self.tMatrix
        nPointFinger = om.MVector(5*sideMult, 0, 0) * self.tMatrix

        offsetVector = (nPointFinger-rPointFinger).normal()
        addFinger = (nPointFinger - rPointFinger) / ((segments + 1) - 1)

        jointList = []
        for i in range(0, (segments + 1)):
            finger = cmds.joint(p=(rPointFinger + (addFinger * i)), name="jInit_finger_%s_%s" %(suffix, str(i)))
            cmds.setAttr("%s.side" % finger, side)

            if i == 0:
                cmds.setAttr("%s.type" % finger, 18)
                cmds.setAttr("%s.otherType" % finger, "FingerRoot", type="string")
                cmds.setAttr("%s.drawLabel" % finger, 1)
                self.createAxisAttributes(finger)
                cmds.addAttr(finger, shortName="fingerType", longName="Finger_Type", at="enum", en="Extra:Thumb:Index:Middle:Ring:Pinky:Toe", k=True)
                cmds.setAttr("%s.radius" %finger, 2)
            else:
                cmds.setAttr("%s.type" % finger, 13)

            jointList.append(finger)

        self.fingerJointsList.append(jointList)
        map(lambda x: cmds.setAttr("%s.displayLocalAxis" %x, 1), jointList)
        extra.orientJoints(jointList, worldUpAxis=self.upVector, upAxis=(0, -1, 0), reverseAim=sideMult,
                           reverseUp=sideMult)
        if side == 0:
            extra.colorize(jointList, self.majorCenterColor, shape=False)
        if side == 1:
            extra.colorize(jointList, self.majorLeftColor, shape=False)
        if side == 2:
            extra.colorize(jointList, self.majorRightColor, shape=False)

        return jointList, offsetVector

    def initialTentacle(self,  segments, side, suffix):
        sideMult = -1 if side == 2 else 1

        if segments < 1:
            FEEDBACK.warning("minimum segments required for the tentacle is two. current: %s" %segments)
            return
        rPointTentacle = om.MVector(0, 14, 0) * self.tMatrix
        if side == 0:
            nPointTentacle = om.MVector(0, 14, 10) * self.tMatrix
        else:
            nPointTentacle = om.MVector(10*sideMult, 14, 0) * self.tMatrix
        offsetVector = (nPointTentacle-rPointTentacle).normal()
        addTentacle = (nPointTentacle - rPointTentacle) / ((segments + 1) - 1)
        jointList = []
        for i in range(0, (segments + 1)):
            tentacle = cmds.joint(p=(rPointTentacle + (addTentacle * i)), name="jInit_tentacle_%s_%s" %(suffix, str(i)))
            cmds.setAttr("%s.side" % tentacle, side)

            if i == 0:
                cmds.setAttr("%s.type" % tentacle, 18)
                cmds.setAttr("%s.otherType" % tentacle, "TentacleRoot", type="string")
                cmds.addAttr(shortName="contRes", longName="Cont_Resolution", defaultValue=5, minValue=1,
                           at="long", k=True)
                cmds.addAttr(shortName="jointRes", longName="Joint_Resolution", defaultValue=25, minValue=1,
                           at="long", k=True)
                cmds.addAttr(shortName="deformerRes", longName="Deformer_Resolution", defaultValue=25, minValue=1,
                           at="long", k=True)
                cmds.addAttr(shortName="dropoff", longName="DropOff", defaultValue=2.0, minValue=0.1,
                           at="float", k=True)
                self.createAxisAttributes(tentacle)
                cmds.setAttr("%s.radius" %tentacle, 3)
            else:
                cmds.setAttr("%s.type" % tentacle, 18)
                cmds.setAttr("%s.otherType" % tentacle, "Tentacle", type="string")

            cmds.setAttr("%s.drawLabel" % tentacle, 1)
            jointList.append(tentacle)

        self.tentacleJointsList.append(jointList)
        map(lambda x: cmds.setAttr("%s.displayLocalAxis" %x, 1), jointList)
        extra.orientJoints(jointList, worldUpAxis=self.upVector, upAxis=(0,1,0), reverseAim=sideMult, reverseUp=sideMult)

        if side == 0:
            extra.colorize(jointList, self.majorCenterColor, shape=False)
        if side == 1:
            extra.colorize(jointList, self.majorLeftColor, shape=False)
        if side == 2:
            extra.colorize(jointList, self.majorRightColor, shape=False)

        return jointList, offsetVector

    def initHumanoid(self, spineSegments=3, neckSegments=3, fingers=5):
        self.initLimb("spine", "auto", segments=spineSegments)
        root = self.spineJointsList[-1][0]
        chest = self.spineJointsList[-1][-1]
        cmds.select(root)
        self.initLimb("leg", "auto")
        cmds.select(chest)
        self.initLimb("arm", "auto")
        self.initLimb("head", "auto", segments=neckSegments)
        rHand =  self.armJointsList[0][-1]
        cmds.select(rHand)
        self.initLimb("hand", "auto", fingerCount=fingers)

    def convertSelectionToInits(self, limbType, jointList=[], suffix="", whichside=""):

        ## // TODO PAY ATTENTION HERE: THIS METHOD IS BROKEN

        ## get the selection
        if whichside == "left":
            side = 1
            extra.colorize(jointList, self.majorLeftColor, shape=False)
        elif whichside == "right":
            side = 2
            extra.colorize(jointList, self.majorRightColor, shape=False)
        else:
            side = 0
            extra.colorize(jointList, self.majorCenterColor, shape=False)

        self.createAxisAttributes(jointList[0])

        if limbType == "spine":
            if len(jointList) < 2:
                FEEDBACK.warning("You need to select at least 2 joints for spine conversion\nNothing Changed")
                return
            for j in range (len(jointList)):
                cmds.select(jointList[j])
                cmds.setAttr("%s.side" % jointList[j],0)
                cmds.setAttr("%s.drawLabel" % jointList[j], 1)
                ## if it is the first jointList
                if j == 0:
                    type =18
                    cmds.setAttr("%s.type" % jointList[j], type)
                    cmds.setAttr("%s.otherType" % jointList[j], "SpineRoot", type="string")

                    if not cmds.attributeQuery("resolution", node=jointList[j], exists=True):
                        cmds.addAttr(shortName="resolution", longName="Resolution", defaultValue=4, minValue=1,
                               at="long", k=True)
                    if not cmds.attributeQuery("dropoff", node=jointList[j], exists=True):
                        cmds.addAttr(shortName="dropoff", longName="DropOff", defaultValue=1.0, minValue=0.1,
                               at="float", k=True)
                    if not cmds.attributeQuery("twistType", node=jointList[j], exists=True):
                        cmds.addAttr(at="enum", k=True, shortName="twistType", longName="Twist_Type", en="regular:infinite")
                    if not cmds.attributeQuery("mode", node=jointList[j], exists=True):
                        cmds.addAttr(at="enum", k=True, shortName="mode", longName="Mode", en="equalDistance:sameDistance")

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
                FEEDBACK.warning("You must select exactly 10 joints to define the chain as Leg\nNothing Changed\nCorrect jointList order is Root -> Hip -> Knee -> Foot -> Ball -> Heel Pivot -> Toe Pivot -> Bank In Pivot -> Bank Out Pivot")
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
                FEEDBACK.warning("You must select exactly 3 joints to define the chain as Neck and Head\nNothing Changed")
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
                        cmds.addAttr(at="enum", k=True, shortName="twistType", longName="Twist_Type", en="regular:infinite")
                    if not cmds.attributeQuery("mode", node=jointList[i], exists=True):
                        cmds.addAttr(at="enum", k=True, shortName="mode", longName="Mode", en="equalDistance:sameDistance")

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
            for i in range (len(jointList)):
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
                        cmds.addAttr(shortName="deformerRes", longName="Deformer_Resolution", defaultValue=25, minValue=1,
                                   at="long", k=True)
                    if not cmds.attributeQuery("dropoff", node=jointList[j], exists=True):
                        cmds.addAttr(shortName="dropoff", longName="DropOff", defaultValue=2.0, minValue=0.1,
                                   at="float", k=True)
                else:
                    cmds.setAttr("%s.type" % jointList[j], 18)
                    cmds.setAttr("%s.otherType" % jointList[j], "Tentacle", type="string")

    def createAxisAttributes(self, node):
        axisAttributes=["upAxis", "mirrorAxis", "lookAxis"]
        for att in axisAttributes:
            if not cmds.attributeQuery(att, node=node, exists=True):
                cmds.addAttr(node, longName=att, dt="string")

        cmds.setAttr("{0}.upAxis".format(node), self.upVector_asString, type="string")
        cmds.setAttr("{0}.mirrorAxis".format(node), self.mirrorVector_asString, type="string")
        cmds.setAttr("{0}.lookAxis".format(node), self.lookVector_asString, type="string")

        if not cmds.attributeQuery("useRefOri", node=node, exists=True):
            cmds.addAttr(node, longName="useRefOri", niceName="Inherit_Orientation", at="bool", keyable=True)

        cmds.setAttr("{0}.useRefOri".format(node), True)











