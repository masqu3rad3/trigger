import pymel.core as pm
import pymel.core.datatypes as dt
import extraProcedures as extra

class initialJoints():

    def __init__(self):
        self.lookAxis = "z"
        self.lookAxisMult = 1
        self.upAxis = "y"
        self.upAxisMult = 1
        self.mirrorAxis = "x"

        self.spineJointsList=[]
        self.neckJointsList=[]
        self.armJointsList=[]
        self.legJointsList=[]
        self.fingerJointsList=[]
        self.tailJointsList=[]

    def transformator (self, inputVector, transKey):
        ## convert the input tuple to an actual vector:
        inputVector = dt.Vector(inputVector)
        order = transKey[0]
        dirX = (transKey[1])
        dirY = (transKey[2])
        dirZ = (transKey[3])
        newVector = dt.Vector(inputVector.x*dirX, inputVector.y*dirY, inputVector.z*dirZ)
        newOrder = eval("newVector.{0},newVector.{1},newVector.{2}".format(order[0],order[1],order[2]))
        return newOrder

    def autoGet (self, parentBone):
        """
        Gets the mirror of the given object by its name. Returns the left if it finds right and vice versa
        Args:
            parentBone: (pymel object) the object which name will be checked

        Returns: (Tuple) None/pymel object, alignment of the given Obj(string), 
                alignment of the returned Obj(string)  Ex.: (bone_left, "left", "right") 

        """
        boneName = parentBone.name()
        if "_right" in boneName:
            mirrorBoneName = boneName.replace("_right", "_left")
            alignmentGiven = "right"
            alignmentReturn = "left"
        elif "_left" in boneName:
            mirrorBoneName = boneName.replace("_left", "_right")
            alignmentGiven = "left"
            alignmentReturn = "right"
        elif "_c" in boneName:
            return None, "both", None
        else:
            pm.warning("Bones cannot be identified automatically")
            return None, None, None
        try:
            returnBone = pm.PyNode(mirrorBoneName)
        except:
            pm.warning("cannot find mirror bone automatically")
            return None, alignmentGiven, None
        return returnBone, alignmentGiven, alignmentReturn

    def changeOrientation(self, faceDir, upDir):
        dirValids = ["+x", "+y", "+z", "-x", "-y", "-z", "+X", "+Y", "+Z", "-X", "-Y", "-Z"]
        if faceDir not in dirValids:
            pm.error("faceDir argument is not valid. Valid arguments are: %s" %dirValids)
        if upDir not in dirValids:
            pm.error("upDir argument is not valid. Valid arguments are: %s" % dirValids)
        # make sure the imputs are lowercase:
        faceDir = faceDir.lower()
        upDir = upDir.lower()

        lookAxis = faceDir.strip("+-")
        lookAxisMult = -1 if faceDir.strip(lookAxis) == "-" else 1

        upAxis = upDir.strip("+-")
        upAxisMult = -1 if upDir.strip(upAxis) == "-" else 1

        if lookAxis == upAxis:
            pm.warning("faceDir and upDir cannot be the same axis, cancelling")
            return
        self.lookAxis = lookAxis
        self.lookAxisMult = lookAxisMult
        self.upAxis = upAxis
        self.upAxisMult = upAxisMult
        self.mirrorAxis = "xyz".strip(lookAxis + upAxis)

    def initLimb (self, limb, whichSide="left", segments=3, fingerCount=5, thumb=False, constrainedTo = None, parentNode=None):


        ## skip side related stuff for no-side related limbs
        nonSidedLimbs = ["spine", "neck", "tail"]
        if limb in nonSidedLimbs:
            whichSide = "c"

        else:
        ## check validity of arguments
            sideValids = ["left", "right", "both", "auto"]
            if whichSide not in sideValids:
                pm.error("side argument '%s' is not valid. Valid arguments are: %s" %(whichSide, sideValids))
            if len(pm.ls(sl=True, type="joint")) != 1 and whichSide == "auto":
                pm.warning("You need to select a single joint to use Auto method")
                return

            ## get the necessary info from arguments
            side = 1 if whichSide == "left" else 2

        sideMult = 1 if whichSide == "left" else -1

        if (segments + 1) < 2:
            pm.error("Define at least 2 segments")
            return

        currentselection = pm.ls(sl=True)

        ID = 0
        suffix = whichSide
        ## make the suffix unique (check the corresponding group name)
        while pm.objExists("%sGrp_%s" %(limb,suffix)):
            ID += 1
            suffix = "%s_%s" % (str(ID), whichSide)

        if not parentNode:
            if pm.ls(sl=True, type="joint"):
                masterParent = pm.ls(sl=True)[-1]
            else:
                masterParent = None
        else:
            masterParent = parentNode

        if whichSide == "both":
            constLocs = self.initLimb(limb, "left")
            self.initLimb(limb, "right", constrainedTo=constLocs)
            return
        if whichSide == "auto":
            mirrorParent, givenAlignment, returnAlignment = self.autoGet(masterParent)
            constLocs = self.initLimb(limb, givenAlignment)
            if mirrorParent:
                self.initLimb(limb, returnAlignment, constrainedTo=constLocs, parentNode=mirrorParent)
            return

        limbGroup = pm.group(em=True, name="%sGrp_%s" %(limb,suffix))
        pm.select(d=True)

        if self.lookAxis == "z" and self.upAxis == "y":
            ## Facing Z Up Y
            a = [("x","y","z"), 1*sideMult*self.lookAxisMult, 1*self.upAxisMult, 1*self.lookAxisMult]
        elif self.lookAxis == "z" and self.upAxis == "x":
            ## Facing Z Up X
            a = [("y", "x", "z"), -1*sideMult*self.lookAxisMult, 1*self.upAxisMult, 1*self.lookAxisMult]
        elif self.lookAxis == "y" and self.upAxis == "z":
            ## Facing Y Up Z
            a = [("x", "z", "y"), -1*sideMult*self.lookAxisMult, 1*self.upAxisMult, 1*self.lookAxisMult]
        elif self.lookAxis == "y" and self.upAxis == "x":
            ## Facing Y Up X
            a = [("y", "z", "x"), 1*sideMult*self.lookAxisMult, 1*self.upAxisMult, 1*self.lookAxisMult]
        elif self.lookAxis == "x" and self.upAxis == "z":
            ## Facing X Up Z
            a = [("z", "x", "y"), 1*sideMult*self.lookAxisMult, 1*self.upAxisMult, 1*self.lookAxisMult]
        elif self.lookAxis == "x" and self.upAxis == "y":
            ## Facing X Up Y
            a = [("z", "y", "x"), -1*sideMult*self.lookAxisMult, 1*self.upAxisMult, 1*self.lookAxisMult]

        ### FROM HERE IT WILL BE LIMB SPECIFIC ###

        if limb == "spine":
            limbJoints, offsetVector = self.initialSpine(transformKey=a, segments=segments, suffix=suffix)

        if limb == "arm":
            limbJoints, offsetVector = self.initialArm(transformKey=a, side=side, suffix=suffix)
            offsetVector = offsetVector * sideMult

        if limb == "leg":
            limbJoints, offsetVector = self.initialLeg(transformKey=a, side=side, suffix=suffix)
            # offsetVector = offsetVector * sideMult

        if limb == "hand":
            limbJoints, jRoots = self.initialHand(fingerCount=fingerCount, transformKey=a, side=side, suffix=suffix)

        if limb == "neck":
            limbJoints, offsetVector = self.initialNeck(transformKey=a, segments=segments, suffix=suffix)

        if limb == "tail":
            limbJoints, offsetVector = self.initialTail(transformKey=a, segments=segments, suffix=suffix)

        if limb == "finger":
            limbJoints, offsetVector = self.initialFinger(segments=segments, transformKey=a, side=side, suffix=suffix)


        ### Constrain locating

        loc_grp = pm.group(name=("locGrp_%s" %suffix), em=True)
        pm.setAttr(loc_grp.v, 0)
        locatorsList=[]
        
        for i in range (0,len(limbJoints)):
            locator = pm.spaceLocator(name="loc_" + limbJoints[i].name())
            locatorsList.append(locator)
            if constrainedTo:
                extra.alignTo(locator, limbJoints[i], 2)
                pm.parentConstraint(locator, limbJoints[i], mo=True)
                extra.connectMirror(constrainedTo[i], locatorsList[i], mirrorAxis=self.mirrorAxis.upper())
            else:
                pm.parentConstraint(limbJoints[i], locator, mo=False)
            pm.parent(locator, loc_grp)
            pm.parent(loc_grp, limbGroup)

        # hand and foot limbs are actually just a collection of fingers.
        # # That is why they need a temporary group to be moved together
        if limb == "hand" or limb == "foot":
            if masterParent:
                if not constrainedTo:
                    tempGroup = pm.group(em=True)
                    pm.parent(jRoots, tempGroup)
                    extra.alignTo(tempGroup, masterParent)
                    pm.ungroup(tempGroup)
                pm.parent(jRoots, masterParent)
            else:
                pm.parent(limbJoints[0], limbGroup)

        else:
            ### MOVE THE LIMB TO THE DESIRED LOCATION
            if masterParent:
                if not constrainedTo:
                    # align the none constrained near to the selected joint
                    extra.alignTo(limbJoints[0], masterParent)
                    # move it a little along the mirrorAxis

                    # value = pm.getAttr("%s.t%s" %(limbJoints[0],self.mirrorAxis))
                    # pm.setAttr("%s.t%s" %(limbJoints[0],self.mirrorAxis), value+3)
                    # move it along offsetvector
                    pm.move(limbJoints[0], offsetVector, relative=True)

                pm.parent(limbJoints[0], masterParent)
            else:
                pm.parent(limbJoints[0], limbGroup)
        pm.select(currentselection)

        return locatorsList

    def initialSpine(self, transformKey, segments, suffix):
        """
        Creates a preset spine hieararchy with given segments
        Args:
            segments: (int) segment count
            suffix: (String) name suffix - must be unique

        Returns: (List) jointList

        """

        rPoint = dt.Vector(self.transformator((0, 14.0, 0), transformKey))
        nPoint = dt.Vector(self.transformator((0, 21.0, 0), transformKey))
        # rPoint = 14.0
        # nPoint = 21.0
        offsetVector = dt.normal(nPoint - rPoint)
        add = (nPoint - rPoint) / ((segments + 1) - 1)
        jointList = []
        for i in range(0, (segments + 1)):
            spine = pm.joint(p=(rPoint + (add * i)), name="jInit_spine_%s_%s" %(suffix, str(i)))
            pm.setAttr(spine + ".side", 0)
            if i == 0:
                type = 1
                pm.setAttr(spine + ".type", type)
            elif i == (segments):
                type = 18
                pm.setAttr(spine + ".type", type)
                pm.setAttr(spine + ".otherType", "SpineEnd")

            else:
                type = 6
                pm.setAttr(spine + ".type", type)

            jointList.append(spine)
            for i in jointList:
                pm.setAttr(i + ".drawLabel", 1)
        self.spineJointsList.append(jointList)
        return jointList, offsetVector

    def initialArm(self, transformKey, side, suffix):
        collarVec = self.transformator((2, 0, 0), transformKey)
        shoulderVec = self.transformator((5, 0, 0), transformKey)
        elbowVec = self.transformator((9, 0, -1), transformKey)
        handVec = self.transformator((14, 0, 0 ), transformKey)

        pm.select(d=True)
        collar = pm.joint(p=collarVec, name=("jInit_collar_" + suffix))
        shoulder = pm.joint(p=shoulderVec, name=("jInit_shoulder_" + suffix))
        elbow = pm.joint(p=elbowVec, name=("jInit_elbow_" + suffix))
        hand = pm.joint(p=handVec, name=("jInit_hand_" + suffix))
        # Orientation
        pm.joint(collar, e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(shoulder, e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(elbow, e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(hand, e=True, zso=True, oj="xyz", sao="yup")
        # Joint Labeling
        pm.setAttr(collar+".side", side)
        pm.setAttr(collar+".type", 9)
        pm.setAttr(shoulder + ".side", side)
        pm.setAttr(shoulder + ".type", 10)
        pm.setAttr(elbow + ".side", side)
        pm.setAttr(elbow + ".type", 11)
        pm.setAttr(hand + ".side", side)
        pm.setAttr(hand + ".type", 12)

        jointList=[collar, shoulder, elbow, hand]
        for i in jointList:
            pm.setAttr(i + ".drawLabel", 1)
        self.armJointsList.append(jointList)
        if self.mirrorAxis == "x":
            offsetAxis = dt.Vector(1,0,0)
        if self.mirrorAxis == "y":
            offsetAxis = dt.Vector(0,1,0)
        if self.mirrorAxis == "z":
            offsetAxis = dt.Vector(0, 0, 1)

        return jointList, offsetAxis
    
    def initialLeg(self, transformKey, side, suffix):
        rootVec = self.transformator((2,14,0), transformKey)
        hipVec = self.transformator((5,10,0), transformKey)
        kneeVec = self.transformator((5,5,1), transformKey)
        footVec = self.transformator((5,1,0), transformKey)
        ballVec = self.transformator((5,0,2), transformKey)
        toeVec = self.transformator((5,0,4), transformKey)
        bankoutVec = self.transformator((4,0,2), transformKey)
        bankinVec = self.transformator((6,0,2), transformKey)
        toepvVec = self.transformator((5,0,4.3), transformKey)
        heelpvVec = self.transformator((5,0,-0.2), transformKey)
        
        root = pm.joint(p=rootVec, name=("jInit_LegRoot_" + suffix))
        hip = pm.joint(p=hipVec, name=("jInit_Hip_" + suffix))
        knee = pm.joint(p=kneeVec, name=("jInit_Knee_" + suffix))
        foot = pm.joint(p=footVec, name=("jInit_Foot_" + suffix))
        ball = pm.joint(p=ballVec, name=("jInit_Ball_" + suffix))
        toe = pm.joint(p=toeVec, name=("jInit_Toe_" + suffix))
        pm.select(d=True)
        bankout = pm.joint(p=bankoutVec, name=("jInit_BankOut_" + suffix))
        pm.select(d=True)
        bankin = pm.joint(p=bankinVec, name=("jInit_BankIn_" + suffix))
        pm.select(d=True)
        toepv = pm.joint(p=toepvVec, name=("jInit_ToePv_" + suffix))
        pm.select(d=True)
        heelpv = pm.joint(p=heelpvVec, name=("jInit_HeelPv_" + suffix))
        pm.joint(root, e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(hip, e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(knee, e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(foot, e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(ball, e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(toe, e=True, zso=True, oj="xyz", sao="yup")
        pm.parent(heelpv, foot)
        pm.parent(toepv, foot)
        pm.parent(bankin, foot)
        pm.parent(bankout, foot)

        pm.setAttr(root + ".side", side)
        pm.setAttr(root + ".type", 18)
        pm.setAttr(root + ".otherType", "LegRoot")
        pm.setAttr(hip + ".side", side)
        pm.setAttr(hip + ".type", 2)
        pm.setAttr(knee + ".side", side)
        pm.setAttr(knee + ".type", 3)
        pm.setAttr(foot + ".side", side)
        pm.setAttr(foot + ".type", 4)

        pm.setAttr(ball + ".side", side)
        pm.setAttr(ball + ".type", 18)
        pm.setAttr(ball + ".otherType", "Ball")

        pm.setAttr(toe + ".side", side)
        pm.setAttr(toe + ".type", 5)

        pm.setAttr(heelpv + ".side", side)
        pm.setAttr(heelpv + ".type", 18)
        pm.setAttr(heelpv + ".otherType", "HeelPV")
        pm.setAttr(toepv + ".side", side)
        pm.setAttr(toepv + ".type", 18)
        pm.setAttr(toepv + ".otherType", "ToePV")
        pm.setAttr(bankin + ".side", side)
        pm.setAttr(bankin + ".type", 18)
        pm.setAttr(bankin + ".otherType", "BankIN")
        pm.setAttr(bankout + ".side", side)
        pm.setAttr(bankout + ".type", 18)
        pm.setAttr(bankout + ".otherType", "BankOUT")
        jointList = [root, hip, knee, foot, ball, toe, bankout, bankin, toepv, heelpv]
        for i in jointList:
            pm.setAttr(i + ".drawLabel", 1)
        self.legJointsList.append(jointList)
        if self.mirrorAxis == "x":
            offsetAxis = dt.Vector(1,0,0)
        if self.mirrorAxis == "y":
            offsetAxis = dt.Vector(0,1,0)
        if self.mirrorAxis == "z":
            offsetAxis = dt.Vector(0, 0, 1)

        return jointList, offsetAxis

    def initialHand(self, fingerCount, transformKey, side, suffix):
        jointList = []
        fingerRoots = []
        if fingerCount > 0:
            thumb00vec = self.transformator((0.681, -0.143, 0.733), transformKey)
            thumb01vec = self.transformator((1.192, -0.21, 1.375), transformKey)

            thumb02vec = self.transformator((1.64, -0.477, 1.885), transformKey)
            thumb03vec = self.transformator((2.053, -0.724, 2.356), transformKey)

            pm.select(d=True)
            thumb00 = pm.joint(p=thumb00vec, name=("jInit_thumb00_" + suffix))
            thumb01 = pm.joint(p=thumb01vec, name=("jInit_thumb01_" + suffix))
            thumb02 = pm.joint(p=thumb02vec, name=("jInit_thumb02_" + suffix))
            thumb03 = pm.joint(p=thumb03vec, name=("jInit_thumb03_" + suffix))
            thumbJoints = [thumb00, thumb01, thumb02, thumb03]
            for i in thumbJoints:
                if i==thumbJoints[0]:
                    pm.setAttr(i + ".type", 18)
                    pm.setAttr(i + ".otherType", "ThumbRoot")
                else:
                    pm.joint(i, e=True, zso=True, oj="xyz", sao="yup")
                    pm.setAttr(i + ".side", side)
                    pm.setAttr(i + ".type", 14)
            pm.setAttr(thumb01 + ".drawLabel", 1)
            self.fingerJointsList.append(thumbJoints)
            jointList.extend(thumbJoints)
            fingerRoots.append(thumb00)

        if fingerCount > 1:
            index00vec = self.transformator((1.517, 0.05, 0.656), transformKey)
            index01vec = self.transformator((2.494, 0.05, 0.868), transformKey)
            index02vec = self.transformator((3.126, 0.05, 1.005), transformKey)
            index03vec = self.transformator((3.746, 0.05, 1.139), transformKey)
            index04vec = self.transformator((4.278, 0.05, 1.254), transformKey)

            pm.select(d=True)
            index00 = pm.joint(p=index00vec, name=("jInit_indexF00_" + suffix))
            index01 = pm.joint(p=index01vec, name=("jInit_indexF01_" + suffix))
            index02 = pm.joint(p=index02vec, name=("jInit_indexF02_" + suffix))
            index03 = pm.joint(p=index03vec, name=("jInit_indexF03_" + suffix))
            index04 = pm.joint(p=index04vec, name=("jInit_indexF04_" + suffix))
            indexJoints = [index00, index01, index02, index03, index04]
            for i in indexJoints:
                if i==indexJoints[0]:
                    pm.setAttr(i + ".type", 18)
                    pm.setAttr(i + ".otherType", "IndexRoot")
                else:
                    pm.joint(i, e=True, zso=True, oj="xyz", sao="yup")
                    pm.setAttr(i + ".side", side)
                    pm.setAttr(i + ".type", 19)
            pm.setAttr(index01 + ".drawLabel", 1)
            self.fingerJointsList.append(indexJoints)
            jointList.extend(indexJoints)
            fingerRoots.append(index00)

        if fingerCount > 2:
            middle00vec = self.transformator((1.597, 0.123, 0.063), transformKey)
            middle01vec = self.transformator((2.594, 0.123, 0.137), transformKey)
            middle02vec = self.transformator((3.312, 0.123, 0.19), transformKey)
            middle03vec = self.transformator((4.012, 0.123, 0.242), transformKey)
            middle04vec = self.transformator((4.588, 0.123, 0.285), transformKey)

            pm.select(d=True)
            middle00 = pm.joint(p=middle00vec, name=("jInit_middleF00_" + suffix))
            middle01 = pm.joint(p=middle01vec, name=("jInit_middleF01_" + suffix))
            middle02 = pm.joint(p=middle02vec, name=("jInit_middleF02_" + suffix))
            middle03 = pm.joint(p=middle03vec, name=("jInit_middleF03_" + suffix))
            middle04 = pm.joint(p=middle04vec, name=("jInit_middleF04_" + suffix))
            middleJoints = [middle00, middle01, middle02, middle03, middle04]
            for i in middleJoints:
                if i==middleJoints[0]:
                    pm.setAttr(i + ".type", 18)
                    pm.setAttr(i + ".otherType", "MiddleRoot")
                else:
                    pm.joint(i, e=True, zso=True, oj="xyz", sao="yup")
                    pm.setAttr(i + ".side", side)
                    pm.setAttr(i + ".type", 20)
            pm.setAttr(middle01 + ".drawLabel", 1)
            self.fingerJointsList.append(middleJoints)
            jointList.extend(middleJoints)
            fingerRoots.append(middle00)

        if fingerCount > 3:
            ring00vec = self.transformator((1.605, 0.123, -0.437), transformKey)
            ring01vec = self.transformator((2.603, 0.123, -0.499), transformKey)
            ring02vec = self.transformator((3.301, 0.123, -0.541), transformKey)
            ring03vec = self.transformator((3.926, 0.123, -0.58), transformKey)
            ring04vec = self.transformator((4.414, 0.123, -0.58), transformKey)

            pm.select(d=True)
            ring00 = pm.joint(p=ring00vec, name=("jInit_ringF00_" + suffix))
            ring01 = pm.joint(p=ring01vec, name=("jInit_ringF01_" + suffix))
            ring02 = pm.joint(p=ring02vec, name=("jInit_ringF02_" + suffix))
            ring03 = pm.joint(p=ring03vec, name=("jInit_ringF03_" + suffix))
            ring04 = pm.joint(p=ring04vec, name=("jInit_ringF04_" + suffix))
            ringJoints = [ring00, ring01, ring02, ring03, ring04]
            for i in ringJoints:
                if i==ringJoints[0]:
                    pm.setAttr(i + ".type", 18)
                    pm.setAttr(i + ".otherType", "RingRoot")
                else:
                    pm.joint(i, e=True, zso=True, oj="xyz", sao="yup")
                    pm.setAttr(i + ".side", side)
                    pm.setAttr(i + ".type", 21)
            pm.setAttr(ring01 + ".drawLabel", 1)
            self.fingerJointsList.append(ringJoints)
            jointList.extend(ringJoints)
            fingerRoots.append(ring00)

        if fingerCount > 4:
            pinky00vec = self.transformator((1.405, 0, -0.909), transformKey)
            pinky01vec = self.transformator((2.387, 0, -1.097), transformKey)
            pinky02vec = self.transformator((2.907, 0, -1.196), transformKey)
            pinky03vec = self.transformator((3.378, 0, -1.286), transformKey)
            pinky04vec = self.transformator((3.767, 0, -1.361), transformKey)

            pm.select(d=True)
            pinky00 = pm.joint(p=pinky00vec, name=("jInit_pinkyF00_" + suffix))
            pinky01 = pm.joint(p=pinky01vec, name=("jInit_pinkyF01_" + suffix))
            pinky02 = pm.joint(p=pinky02vec, name=("jInit_pinkyF02_" + suffix))
            pinky03 = pm.joint(p=pinky03vec, name=("jInit_pinkyF03_" + suffix))
            pinky04 = pm.joint(p=pinky04vec, name=("jInit_pinkyF04_" + suffix))
            pinkyJoints = [pinky00, pinky01, pinky02, pinky03, pinky04]

            for i in pinkyJoints:
                if i==pinkyJoints[0]:
                    pm.setAttr(i + ".type", 18)
                    pm.setAttr(i + ".otherType", "PinkyRoot")
                else:
                    pm.joint(i, e=True, zso=True, oj="xyz", sao="yup")
                    pm.setAttr(i + ".side", side)
                    pm.setAttr(i + ".type", 22)
            pm.setAttr(pinky01 + ".drawLabel", 1)
            self.fingerJointsList.append(pinkyJoints)
            jointList.extend(pinkyJoints)
            fingerRoots.append(pinky00)

        if fingerCount > 5:
            for x in range(0, (fingerCount - 5)):
                ##//TODO put extra fingers
                pass
        return jointList, fingerRoots

    def initialNeck(self, transformKey, segments, suffix):
        rPointNeck = dt.Vector(self.transformator((0, 25.757, 0), transformKey))
        nPointNeck = dt.Vector(self.transformator((0, 29.418, 0.817), transformKey))
        pointHead = dt.Vector(self.transformator((0, 32,0.817), transformKey))
        offsetVector = dt.normal(nPointNeck-rPointNeck)
        addNeck = (nPointNeck - rPointNeck) / ((segments + 1) - 1)
        jointList = []
        for i in range(0, (segments + 1)):
            if not i == (segments):
                neck = pm.joint(p=(rPointNeck + (addNeck * i)), name="jInit_neck_%s_%s" %(suffix, str(i)))
                pm.setAttr(neck + ".side", 0)

                if i == 0:
                    pm.setAttr(neck + ".type", 18)
                    pm.setAttr(neck + ".otherType", "NeckRoot")
                else:
                    pm.setAttr(neck + ".type", 7)

            else:
                neck= pm.joint(p=(rPointNeck + (addNeck * i)), name="jInit_head_%s_%s" %(suffix, str(i)))
                pm.setAttr(neck + ".type", 8)
            pm.setAttr(neck + ".drawLabel", 1)
            jointList.append(neck)
        headEnd = pm.joint(p=pointHead, name="jInit_headEnd_%s_%s" %(suffix, str(i)))
        pm.setAttr(headEnd + ".side", 0)
        pm.setAttr(headEnd + ".type", 18)
        pm.setAttr(headEnd + ".otherType", "HeadEnd")
        pm.setAttr(headEnd + ".drawLabel", 1)
        jointList.append(headEnd)

        self.neckJointsList.append(jointList)
        return jointList, offsetVector

    def initialTail(self, transformKey, segments, suffix):

        rPointTail = dt.Vector(self.transformator((0, 14, 0), transformKey))
        nPointTail = dt.Vector(self.transformator((0, 8.075, -7.673), transformKey))
        offsetVector = dt.normal(nPointTail-rPointTail)
        addTail = (nPointTail - rPointTail) / ((segments + 1) - 1)
        jointList = []
        for i in range(0, (segments + 1)):
            tail = pm.joint(p=(rPointTail + (addTail * i)), name="jInit_tail_%s_%s" %(suffix, str(i)))
            pm.setAttr(tail + ".side", 0)

            if i == 0:
                pm.setAttr(tail + ".type", 18)
                pm.setAttr(tail + ".otherType", "TailRoot")
            else:
                pm.setAttr(tail + ".type", 18)
                pm.setAttr(tail + ".otherType", "Tail")

            pm.setAttr(tail + ".drawLabel", 1)
            jointList.append(tail)

        self.tailJointsList.append(jointList)
        return jointList, offsetVector

    def initialFinger(self,segments, transformKey, side, suffix, thumb=False):
        if segments < 2:
            pm.warning("minimum segments for the fingers are two. current: %s" %segments)
            return


        rPointFinger = dt.Vector(self.transformator((0, 0, 0), transformKey))
        nPointFinger = dt.Vector(self.transformator((5, 0, 0), transformKey))


        offsetVector = dt.normal(nPointFinger-rPointFinger)
        addFinger = (nPointFinger - rPointFinger) / ((segments + 1) - 1)

        jointList = []
        for i in range(0, (segments + 1)):
            tail = pm.joint(p=(rPointFinger + (addFinger * i)), name="jInit_tail_%s_%s" %(suffix, str(i)))
            pm.setAttr(tail + ".side", 0)

            if i == 0:
                pm.setAttr(tail + ".type", 18)
                pm.setAttr(tail + ".otherType", "FingerRoot")
                pm.setAttr(tail + ".drawLabel", 1)
            else:
                pm.setAttr(tail + ".type", 23)


            jointList.append(tail)

        self.tailJointsList.append(jointList)
        return jointList, offsetVector

    def initHumanoid(self):
        self.initLimb("spine", "auto", segments=3)
        root = self.spineJointsList[-1][0]
        chest = self.spineJointsList[-1][-1]
        pm.select(root)
        self.initLimb("leg", "auto")

        pm.select(chest)
        self.initLimb("arm", "auto")
        self.initLimb("neck", "auto", segments=2)
        rHand =  self.armJointsList[-1][-1]

        pm.select(rHand)
        self.initLimb("hand", "auto")





