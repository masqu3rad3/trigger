import pymel.core as pm
import pymel.core.datatypes as dt
import extraProcedures as extra

class initialJoints():
    lookAxis = "z"
    lookAxisMult = 1
    upAxis = "y"
    upAxisMult = 1
    mirrorAxis = "x"

    def initSpineBones(self, segments):
        ID = 0
        suffix = str(ID)
        while pm.objExists("jInit_spine"+suffix):
            ID += 1
            suffix = str(ID)


        if pm.ls(sl=True, type="joint"):
            root = pm.ls(sl=True)[-1]
        else:
            root = None

        pm.select(d=True)
        if (segments + 1) < 2:
            pm.error("Define at least 3 segments for spine section")
            return
        rPoint = 14.0
        nPoint = 21.0
        add = (nPoint - rPoint) / ((segments + 1) - 1)
        jointList = []
        for i in range(0, (segments + 1)):
            spine = pm.joint(p=(0, (rPoint + (add * i)), 0), name="jInit_spine%s_%s" %(suffix, str(i)))
            pm.setAttr(spine + ".side", 0)
            type = 1 if i == 0 else 6
            pm.setAttr(spine + ".type", type)
            jointList.append(spine)
            for i in jointList:
                pm.setAttr(i + ".drawLabel", 1)
        if root:
            extra.alignTo(jointList[0], root)
            pm.move(jointList[0], (0,2,0), relative=True)
            pm.parent(jointList[0],root)

    def initArmBones(self, whichArm, constrainedTo=None, parentNode=None):
        # check validity of arguments
        whichArmValids = ["left", "right", "both", "auto"]
        if whichArm not in whichArmValids:
            pm.error("whichArm argument is not valid. Valid arguments are: %s" %whichArmValids)

        if len(pm.ls(sl=True, type="joint")) != 1 and whichArm == "auto":
            pm.warning("You need to select a single joint to use Auto method")
            return

        ## get the necessary info from arguments
        side = 1 if whichArm == "left" else 2
        sideMult = 1 if whichArm == "left" else -1

        currentselection=pm.ls(sl=True)

        ID = 0
        suffix = whichArm
        while pm.objExists("armInitsGrp_%s" %suffix):
            ID += 1
            suffix = "%s_%s" % (str(ID),whichArm)

        if not parentNode:
            if pm.ls(sl=True, type="joint"):
                masterParent = pm.ls(sl=True)[-1]
            else:
                masterParent = None
        else:
            masterParent = parentNode

        if whichArm=="both":
            leftLocs = self.initArmBones("left")
            self.initArmBones("right", constrainedTo=leftLocs)
            return

        if whichArm == "auto":
            mirrorParent, givenAlignment, returnAlignment = self.autoGet(masterParent)
            leftLocs = self.initArmBones(givenAlignment)
            if mirrorParent:
                self.initArmBones(returnAlignment, constrainedTo=leftLocs, parentNode=mirrorParent)
            return
        armGroup = pm.group(em=True, name="armInitsGrp_%s" %whichArm)
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

        collarVec = self.transformator((2, 0, 0), a)
        shoulderVec = self.transformator((5, 0, 0), a)
        elbowVec = self.transformator((9, 0, -1), a)
        handVec = self.transformator((14, 0, 0 ), a)

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

        loc_grp_arm = pm.group(name=("locGrp_%s" %suffix), em=True)
        pm.setAttr(loc_grp_arm.v, 0)
        locatorsList=[]
        for i in range (0,len(jointList)):
            locator = pm.spaceLocator(name="loc_" + jointList[i].name())
            locatorsList.append(locator)
            if constrainedTo:
                extra.alignTo(locator, jointList[i], 2)
                pm.parentConstraint(locator, jointList[i], mo=True)
                extra.connectMirror(constrainedTo[i], locatorsList[i], mirrorAxis=self.mirrorAxis.upper())
            else:
                pm.parentConstraint(jointList[i], locator, mo=False)
            pm.parent(locator, loc_grp_arm)
            pm.parent(loc_grp_arm, armGroup)

        if masterParent:
            if not constrainedTo:
                # align the none constrained near to the selected joint
                extra.alignTo(jointList[0], masterParent)
                # move it a little along the mirrorAxis
                value = pm.getAttr("%s.t%s" %(jointList[0],self.mirrorAxis))
                pm.setAttr("%s.t%s" %(jointList[0],self.mirrorAxis), value+3)

            pm.parent(jointList[0], masterParent)
        else:
            pm.parent(jointList[0], armGroup)
        pm.select(currentselection)
        return locatorsList

    def initLegBones(self, whichLeg, constrainedTo=None, parentNode=None):

        # check validity of arguments
        whichLegValids = ["left", "right", "both", "auto"]
        if whichLeg not in whichLegValids:
            pm.error("whichArm argument is not valid. Valid arguments are: %s" %whichLegValids)
            
        if len(pm.ls(sl=True, type="joint")) != 1 and whichLeg == "auto":
            pm.warning("You need to select a single joint to use Auto method")
            return

        ## get the necessary info from arguments
        side = 1 if whichLeg == "left" else 2
        sideMult = 1 if whichLeg == "left" else -1

        currentselection=pm.ls(sl=True)

        ID = 0
        suffix = whichLeg
        while pm.objExists("legInitsGrp_%s" %suffix):
            ID += 1
            suffix = "%s_%s" % (str(ID), whichLeg)

        if not parentNode:
            if pm.ls(sl=True, type="joint"):
                masterParent = pm.ls(sl=True)[-1]
            else:
                masterParent = None
        else:
            masterParent = parentNode

        if whichLeg=="both":
            leftLocs = self.initLegBones("left")
            self.initLegBones("right", constrainedTo=leftLocs)
            return
        
        if whichLeg == "auto":
            mirrorParent, givenAlignment, returnAlignment = self.autoGet(masterParent)
            leftLocs = self.initLegBones(givenAlignment)
            if mirrorParent:
                self.initLegBones(returnAlignment, constrainedTo=leftLocs, parentNode=mirrorParent)
            return

        legGroup = pm.group(em=True, name="legInitsGrp_%s" %whichLeg)
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

        rootVec = self.transformator((2,14,0), a)
        hipVec = self.transformator((5,10,0), a)
        kneeVec = self.transformator((5,5,1), a)
        footVec = self.transformator((5,1,0), a)
        ballVec = self.transformator((5,0,2), a)
        toeVec = self.transformator((5,0,4), a)
        bankoutVec = self.transformator((4,0,2), a)
        bankinVec = self.transformator((6,0,2), a)
        toepvVec = self.transformator((5,0,4.3), a)
        heelpvVec = self.transformator((5,0,-0.2), a)
        

        root = pm.joint(p=rootVec, name=("jInit_LegRoot_" + whichLeg))
        hip = pm.joint(p=hipVec, name=("jInit_Hip_" + whichLeg))
        knee = pm.joint(p=kneeVec, name=("jInit_Knee_" + whichLeg))
        foot = pm.joint(p=footVec, name=("jInit_Foot_" + whichLeg))
        ball = pm.joint(p=ballVec, name=("jInit_Ball_" + whichLeg))
        toe = pm.joint(p=toeVec, name=("jInit_Toe_" + whichLeg))
        pm.select(d=True)
        bankout = pm.joint(p=bankoutVec, name=("jInit_BankOut_" + whichLeg))
        pm.select(d=True)
        bankin = pm.joint(p=bankinVec, name=("jInit_BankIn_" + whichLeg))
        pm.select(d=True)
        toepv = pm.joint(p=toepvVec, name=("jInit_ToePv_" + whichLeg))
        pm.select(d=True)
        heelpv = pm.joint(p=heelpvVec, name=("jInit_HeelPv_" + whichLeg))
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

        loc_grp_leg = pm.group(name=("locGrp_%s" %suffix), em=True)
        pm.setAttr(loc_grp_leg.v, 0)
        locatorsList=[]
        for i in range (0,len(jointList)):
            locator = pm.spaceLocator(name="loc_" + jointList[i].name())
            locatorsList.append(locator)
            if constrainedTo:
                extra.alignTo(locator, jointList[i], 2)
                pm.parentConstraint(locator, jointList[i], mo=True)
                extra.connectMirror(constrainedTo[i], locatorsList[i], mirrorAxis=self.mirrorAxis.upper())
            else:
                pm.parentConstraint(jointList[i], locator, mo=False)
            pm.parent(locator, loc_grp_leg)
            pm.parent(loc_grp_leg, legGroup)

        if masterParent:
            if not constrainedTo:
                # align the none constrained near to the selected joint
                extra.alignTo(jointList[0], masterParent)
                # move it a little along the mirrorAxis
                value = pm.getAttr("%s.t%s" %(jointList[0],self.mirrorAxis))
                pm.setAttr("%s.t%s" %(jointList[0],self.mirrorAxis), value+3)

            pm.parent(jointList[0], masterParent)
        else:
            pm.parent(jointList[0], legGroup)
        pm.select(currentselection)
        return locatorsList

    def initHandBones (self, whichArm, fingerCount=5, constrainedTo=None, parentNode=None):
        # check validity of arguments
        if fingerCount < 1:
            pm.error ("fingerCount cannot be smaller than 1")
        whichArmValids = ["left", "right", "both", "auto"]
        if whichArm not in whichArmValids:
            pm.error("whichArm argument is not valid. Valid arguments are: %s" %whichArmValids)

        if len(pm.ls(sl=True, type="joint")) != 1 and whichArm == "auto":
            pm.warning("You need to select a single joint to use Auto method")
            return

        ## get the necessary info from arguments
        side = 1 if whichArm == "left" else 2
        sideMult = 1 if whichArm == "left" else -1

        currentselection=pm.ls(sl=True)

        # make the suffix unique
        ID = 0
        suffix = whichArm
        while pm.objExists("handInitsGrp_%s" %suffix):
            ID += 1
            suffix = "%s_%s" % (str(ID), whichArm)

        if not parentNode:
            if pm.ls(sl=True, type="joint"):
                masterParent = pm.ls(sl=True)[-1]
            else:
                pm.select(d=True)
                masterParent = pm.joint(p=(0,0,0), name=("jInit_Hand_" + whichArm))
                pm.select(currentselection)
        else:
            masterParent = parentNode

        if whichArm == "both":
            leftLocs = self.initHandBones("left", fingerCount=fingerCount)
            self.initHandBones("right", fingerCount=fingerCount, constrainedTo=leftLocs)
            return

        if whichArm == "auto":
            mirrorParent, givenAlignment, returnAlignment = self.autoGet(masterParent)
            if givenAlignment:
                leftLocs = self.initHandBones(givenAlignment, fingerCount=fingerCount)
            if mirrorParent:
                self.initHandBones(returnAlignment, fingerCount=fingerCount, constrainedTo=leftLocs, parentNode=mirrorParent)
            return

        handGroup = pm.group(em=True, name="handInitsGrp_%s" %whichArm)
        pm.select(d=True)

        if self.lookAxis == "z" and self.upAxis == "y":
            ## Facing Z Up Y
            a = [("x", "y", "z"), 1 * sideMult * self.lookAxisMult, 1 * self.upAxisMult, 1 * self.lookAxisMult]
        elif self.lookAxis == "z" and self.upAxis == "x":
            ## Facing Z Up X
            a = [("y", "x", "z"), -1 * sideMult * self.lookAxisMult, 1 * self.upAxisMult, 1 * self.lookAxisMult]
        elif self.lookAxis == "y" and self.upAxis == "z":
            ## Facing Y Up Z
            a = [("x", "z", "y"), -1 * sideMult * self.lookAxisMult, 1 * self.upAxisMult, 1 * self.lookAxisMult]
        elif self.lookAxis == "y" and self.upAxis == "x":
            ## Facing Y Up X
            a = [("y", "z", "x"), 1 * sideMult * self.lookAxisMult, 1 * self.upAxisMult, 1 * self.lookAxisMult]
        elif self.lookAxis == "x" and self.upAxis == "z":
            ## Facing X Up Z
            a = [("z", "x", "y"), 1 * sideMult * self.lookAxisMult, 1 * self.upAxisMult, 1 * self.lookAxisMult]
        elif self.lookAxis == "x" and self.upAxis == "y":
            ## Facing X Up Y
            a = [("z", "y", "x"), -1 * sideMult * self.lookAxisMult, 1 * self.upAxisMult, 1 * self.lookAxisMult]

        jointList = []
        fingerRoots = []
        if fingerCount > 0:
            thumb00vec = self.transformator((0.681,-0.143,0.733), a)
            thumb01vec = self.transformator((1.192,-0.21,1.375), a)

            thumb02vec = self.transformator((1.64,-0.477,1.885), a)
            thumb03vec = self.transformator((2.053,-0.724,2.356), a)

            pm.select(d=True)
            thumb00 = pm.joint(p=thumb00vec, name=("jInit_thumb00_" + whichArm))
            thumb01 = pm.joint(p=thumb01vec, name=("jInit_thumb01_" + whichArm))
            thumb02 = pm.joint(p=thumb02vec, name=("jInit_thumb02_" + whichArm))
            thumb03 = pm.joint(p=thumb03vec, name=("jInit_thumb03_" + whichArm))
            thumbJoints = [thumb00, thumb01, thumb02, thumb03]
            for i in thumbJoints:
                pm.joint(i, e=True, zso=True, oj="xyz", sao="yup")
                pm.setAttr(i + ".side", side)
                pm.setAttr(i + ".type", 14)
            pm.setAttr(thumb01 + ".drawLabel", 1)
            jointList.extend(thumbJoints)
            fingerRoots.append(thumb00)

        if fingerCount > 1:
            index00vec = self.transformator((1.517,0.05,0.656), a)
            index01vec = self.transformator((2.494,0.05,0.868), a)
            index02vec = self.transformator((3.126,0.05,1.005), a)
            index03vec = self.transformator((3.746,0.05,1.139), a)
            index04vec = self.transformator((4.278,0.05,1.254), a)

            pm.select(d=True)
            index00 = pm.joint(p=index00vec, name=("jInit_indexF00_" + whichArm))
            index01 = pm.joint(p=index01vec, name=("jInit_indexF01_" + whichArm))
            index02 = pm.joint(p=index02vec, name=("jInit_indexF02_" + whichArm))
            index03 = pm.joint(p=index03vec, name=("jInit_indexF03_" + whichArm))
            index04 = pm.joint(p=index04vec, name=("jInit_indexF04_" + whichArm))
            indexJoints = [index00, index01, index02, index03, index04]
            for i in indexJoints:
                pm.joint(i, e=True, zso=True, oj="xyz", sao="yup")
                pm.setAttr(i + ".side", side)
                pm.setAttr(i + ".type", 19)
            pm.setAttr(index01 + ".drawLabel", 1)
            jointList.extend(indexJoints)
            fingerRoots.append(index00)

        if fingerCount > 2:
            middle00vec = self.transformator((1.597,0.123,0.063), a)
            middle01vec = self.transformator((2.594,0.123,0.137), a)
            middle02vec = self.transformator((3.312,0.123,0.19), a)
            middle03vec = self.transformator((4.012,0.123,0.242), a)
            middle04vec = self.transformator((4.588,0.123,0.285), a)

            pm.select(d=True)
            middle00 = pm.joint(p=middle00vec, name=("jInit_middleF00_" + whichArm))
            middle01 = pm.joint(p=middle01vec, name=("jInit_middleF01_" + whichArm))
            middle02 = pm.joint(p=middle02vec, name=("jInit_middleF02_" + whichArm))
            middle03 = pm.joint(p=middle03vec, name=("jInit_middleF03_" + whichArm))
            middle04 = pm.joint(p=middle04vec, name=("jInit_middleF04_" + whichArm))
            middleJoints = [middle00, middle01, middle02, middle03, middle04]
            for i in middleJoints:
                pm.joint(i, e=True, zso=True, oj="xyz", sao="yup")
                pm.setAttr(i + ".side", side)
                pm.setAttr(i + ".type", 20)
            pm.setAttr(middle01 + ".drawLabel", 1)
            jointList.extend(middleJoints)
            fingerRoots.append(middle00)

        if fingerCount > 3:
            ring00vec = self.transformator((1.605,0.123,-0.437), a)
            ring01vec = self.transformator((2.603,0.123,-0.499), a)
            ring02vec = self.transformator((3.301,0.123,-0.541), a)
            ring03vec = self.transformator((3.926,0.123,-0.58), a)
            ring04vec = self.transformator((4.414,0.123,-0.58), a)

            pm.select(d=True)
            ring00 = pm.joint(p=ring00vec, name=("jInit_ringF00_" + whichArm))
            ring01 = pm.joint(p=ring01vec, name=("jInit_ringF01_" + whichArm))
            ring02 = pm.joint(p=ring02vec, name=("jInit_ringF02_" + whichArm))
            ring03 = pm.joint(p=ring03vec, name=("jInit_ringF03_" + whichArm))
            ring04 = pm.joint(p=ring04vec, name=("jInit_ringF04_" + whichArm))
            ringJoints = [ring00, ring01, ring02, ring03, ring04]
            for i in ringJoints:
                pm.joint(i, e=True, zso=True, oj="xyz", sao="yup")
                pm.setAttr(i + ".side", side)
                pm.setAttr(i + ".type", 21)
            pm.setAttr(ring01 + ".drawLabel", 1)
            jointList.extend(ringJoints)
            fingerRoots.append(ring00)

        if fingerCount > 4:
            pinky00vec = self.transformator((1.405,0,-0.909), a)
            pinky01vec = self.transformator((2.387,0,-1.097), a)
            pinky02vec = self.transformator((2.907,0,-1.196), a)
            pinky03vec = self.transformator((3.378,0,-1.286), a)
            pinky04vec = self.transformator((3.767,0,-1.361), a)

            pm.select(d=True)
            pinky00 = pm.joint(p=pinky00vec, name=("jInit_pinkyF00_" + whichArm))
            pinky01 = pm.joint(p=pinky01vec, name=("jInit_pinkyF01_" + whichArm))
            pinky02 = pm.joint(p=pinky02vec, name=("jInit_pinkyF02_" + whichArm))
            pinky03 = pm.joint(p=pinky03vec, name=("jInit_pinkyF03_" + whichArm))
            pinky04 = pm.joint(p=pinky04vec, name=("jInit_pinkyF04_" + whichArm))
            pinkyJoints = [pinky00, pinky01, pinky02, pinky03, pinky04]

            for i in pinkyJoints:
                pm.joint(i, e=True, zso=True, oj="xyz", sao="yup")
                pm.setAttr(i + ".side", side)
                pm.setAttr(i + ".type", 22)
            pm.setAttr(pinky01 + ".drawLabel", 1)
            jointList.extend(pinkyJoints)
            fingerRoots.append(pinky00)

        if fingerCount > 5:
            for x in range(0, (fingerCount - 5)):
                ##//TODO put extra fingers
                pass

        loc_grp_arm = pm.group(name=("locGrp_%s" %suffix), em=True)
        pm.setAttr(loc_grp_arm.v, 0)
        locatorsList=[]

        for i in range (0,len(jointList)):
            locator = pm.spaceLocator(name="loc_" + jointList[i].name())
            locatorsList.append(locator)
            if constrainedTo:
                extra.alignTo(locator, jointList[i], 2)
                pm.parentConstraint(locator, jointList[i], mo=True)
                extra.connectMirror(constrainedTo[i], locatorsList[i], mirrorAxis=self.mirrorAxis.upper())
            else:
                pm.parentConstraint(jointList[i], locator, mo=False)
            pm.parent(locator, loc_grp_arm)
            pm.parent(loc_grp_arm, handGroup)
        if masterParent:
            if not constrainedTo:
                # align the none constrained near to the selected joint
                tempGroup = pm.group(em=True)
                pm.parent(fingerRoots, tempGroup)
                extra.alignTo(tempGroup, masterParent)
                pm.ungroup(tempGroup)
            pm.parent(fingerRoots, masterParent)
        pm.select(currentselection)

        return locatorsList

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

    def initLimb (self, limb, whichSide, segments=3, fingerCount=5, constrainedTo = None, parentNode=None):

        sideValids = ["left", "right", "both", "auto"]
        if whichSide not in sideValids:
            pm.error("side argument is not valid. Valid arguments are: %s" %sideValids)
        if len(pm.ls(sl=True, type="joint")) != 1 and whichSide == "auto":
            pm.warning("You need to select a single joint to use Auto method")
            return
        ## get the necessary info from arguments
        side = 1 if whichSide == "left" else 2
        sideMult = 1 if whichSide == "left" else -1

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
