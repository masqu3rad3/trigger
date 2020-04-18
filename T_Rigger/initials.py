import pymel.core as pm
import pymel.core.datatypes as dt
import extraProcedures as extra

class initialJoints():

    def __init__(self, settingsData):

        # self.mirrorAxis = "+x"
        # self.upAxis = "+y"
        # self.lookAxis = "+z"

        # default vectors

        self.parseSettings(settingsData)
        # self.upVector = dt.Vector(0,1,0)
        # self.lookVector = dt.Vector(0,0,1)
        # self.mirrorVector = dt.Vector(1,0,0)

        # if "-" in self.mirrorAxis:
        #     self.mirrorAxisMult = 1
        #     self.mirrorAxis = self.mirrorAxis.replace("-", "")
        # else:
        #     self.mirrorAxisMult = 1
        # if "-" in self.upAxis:
        #     self.upAxisMult = -1
        # else:
        #     self.upAxisMult = 1
        # if "-" in self.lookAxis:
        #     self.lookAxisMult = -1
        # else:
        #     self.lookAxisMult = 1

        self.spineJointsList=[]
        self.neckJointsList=[]
        self.armJointsList=[]
        self.legJointsList=[]
        self.fingerJointsList=[]
        self.tailJointsList=[]
        self.tentacleJointsList=[]
        self.projectName = "tikAutoRig"

    def parseSettings(self, settingsData):

        parsingDictionary = {u'+x':(1,0,0),
                             u'+y':(0,1,0),
                             u'+z':(0,0,1),
                             u'-x': (-1, 0, 0),
                             u'-y': (0, -1, 0),
                             u'-z': (0, 0, -1)
                             }
        # self.upAxis = settingsData["upAxis"]
        # self.lookAxis = settingsData["lookAxis"]
        # self.mirrorAxis = settingsData["mirrorAxis"]

        self.upVector_asString = settingsData["upAxis"]
        self.lookVector_asString = settingsData["lookAxis"]
        self.mirrorVector_asString = settingsData["mirrorAxis"]


        self.upVector = dt.Vector(parsingDictionary[settingsData["upAxis"]])
        self.lookVector = dt.Vector(parsingDictionary[settingsData["lookAxis"]])
        self.mirrorVector = dt.Vector(parsingDictionary[settingsData["mirrorAxis"]])


        # get transformation matrix:
        self.upVector.normalize()
        self.lookVector.normalize()
        # get the third axis with the cross vector
        side_vect = dt.Vector.cross(self.upVector, self.lookVector)
        # recross in case up and front were not originally orthoganl:
        front_vect = dt.Vector.cross(side_vect, self.upVector)
        # the new matrix is
        self.tMatrix = dt.Matrix(
            side_vect.x, side_vect.y, side_vect.z, 0,
            self.upVector.x,  self.upVector.y,  self.upVector.z, 0,
            front_vect.x, front_vect.y, front_vect.z, 0,
            0, 0, 0, 1)


        self.majorLeftColor = settingsData["majorLeftColor"]
        self.minorLeftColor = settingsData["minorLeftColor"]
        self.majorRightColor = settingsData["majorRightColor"]
        self.minorRightColor = settingsData["minorRightColor"]
        self.majorCenterColor = settingsData["majorCenterColor"]
        self.minorCenterColor = settingsData["minorCenterColor"]



    # def transformator (self, inputVector, transKey):
    #     ## convert the input tuple to an actual vector:
    #     inputVector = dt.Vector(inputVector)
    #     order = transKey[0]
    #     dirX = (transKey[1])
    #     dirY = (transKey[2])
    #     dirZ = (transKey[3])
    #     newVector = dt.Vector(inputVector.x*dirX, inputVector.y*dirY, inputVector.z*dirZ)
    #     newOrder = eval("newVector.{0},newVector.{1},newVector.{2}".format(order[0],order[1],order[2]))
    #     return newOrder

    def autoGet (self, parentBone):
        """
        Gets the mirror of the given object by its name. Returns the left if it finds right and vice versa
        Args:
            parentBone: (pymel object) the object which name will be checked

        Returns: (Tuple) None/pymel object, alignment of the given Obj(string), 
                alignment of the returned Obj(string)  Ex.: (bone_left, "left", "right") 

        """
        try:
            boneName = parentBone.name()
        except AttributeError:
            pm.warning("Bones cannot be identified automatically")
            return None, None, None
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

    # def changeOrientation(self, faceDir, upDir):
    #     dirValids = ["+x", "+y", "+z", "-x", "-y", "-z", "+X", "+Y", "+Z", "-X", "-Y", "-Z"]
    #     if faceDir not in dirValids:
    #         pm.error("faceDir argument is not valid. Valid arguments are: %s" % dirValids)
    #     if upDir not in dirValids:
    #         pm.error("upDir argument is not valid. Valid arguments are: %s" % dirValids)
    #     # make sure the imputs are lowercase:
    #     faceDir = faceDir.lower()
    #     upDir = upDir.lower()
    #
    #     lookAxis = faceDir.strip("+-")
    #     lookAxisMult = -1 if faceDir.strip(lookAxis) == "-" else 1
    #
    #     upAxis = upDir.strip("+-")
    #     upAxisMult = -1 if upDir.strip(upAxis) == "-" else 1
    #
    #     if lookAxis == upAxis:
    #         pm.warning("faceDir and upDir cannot be the same axis, cancelling")
    #         return
    #     self.lookAxis = lookAxis
    #     self.lookAxisMult = lookAxisMult
    #     self.upAxis = upAxis
    #     self.upAxisMult = upAxisMult
    #     self.mirrorAxis = "xyz".strip(lookAxis + upAxis)

    def initLimb (self, limb, whichSide="left",
                  segments=3, fingerCount=5, thumb=False,
                  constrainedTo = None, parentNode=None, defineAs=False):
        currentselection = pm.ls(sl=True)

        ## Create the holder group if it does not exist
        if not pm.objExists("{0}_refBones".format(self.projectName)):
            holderGroup = pm.group(name=("{0}_refBones".format(self.projectName)), em=True)
        else:
            holderGroup = pm.PyNode("{0}_refBones".format(self.projectName), em=True)

        ## skip side related stuff for no-side related limbs
        nonSidedLimbs = ["spine", "neck", "root"]
        if limb in nonSidedLimbs:
            whichSide = "c"
            side = 0

        else:
        ## check validity of arguments
            sideValids = ["left", "right", "center", "both", "auto"]
            if whichSide not in sideValids:
                pm.error("side argument '%s' is not valid. Valid arguments are: %s" %(whichSide, sideValids))
            if len(pm.ls(sl=True, type="joint")) != 1 and whichSide == "auto" and defineAs == False:
                pm.warning("You need to select a single joint to use Auto method")
                return

            ## get the necessary info from arguments
            if whichSide == "left":
                side =1
            elif whichSide == "right":
                side =2
            else:
                side = 0

        # sideMult = -1 if whichSide == "right" else 1

        if (segments + 1) < 2:
            pm.error("Define at least 2 segments")
            return

        suffix = extra.uniqueName("%sGrp_%s" %(limb, whichSide)).replace("%sGrp_" %(limb), "")

        ## if defineAs is True, define the selected joints as the given limb instead creating new ones.
        if defineAs:
            self.convertSelectionToInits(limb, jointList=currentselection, whichside=whichSide, suffix=suffix)
            return


        if not parentNode:
            if pm.ls(sl=True, type="joint"):
                valid_inits = ["arm", "leg", "spine", "neck", "tail", "finger", "tentacle", "root"]
                j = pm.ls(sl=True)[-1]
                try:
                    if extra.identifyMaster(j)[1] in valid_inits:
                        masterParent = pm.ls(sl=True)[-1]
                    else:
                        masterParent = None
                except KeyError:
                    masterParent = None

            else:
                masterParent = None
        else:
            masterParent = parentNode

        if whichSide == "both":
            constLocs = self.initLimb(limb, "left", segments=segments, fingerCount=fingerCount, thumb=thumb)
            self.initLimb(limb, "right", constrainedTo=constLocs, segments=segments, fingerCount=fingerCount, thumb=thumb)
            return
        if whichSide == "auto" and masterParent:
            mirrorParent, givenAlignment, returnAlignment = self.autoGet(masterParent)
            constLocs = self.initLimb(limb, givenAlignment, segments=segments, fingerCount=fingerCount, thumb=thumb)
            if mirrorParent:
                self.initLimb(limb, returnAlignment, constrainedTo=constLocs, parentNode=mirrorParent, segments=segments, fingerCount=fingerCount, thumb=thumb)
            return

        limbGroup = pm.group(em=True, name="%sGrp_%s" %(limb,suffix))
        pm.parent(limbGroup, holderGroup)
        pm.select(d=True)

        # if self.lookAxis.replace("-","") == "z" and self.upAxis.replace("-","") == "y":
        #     ## Facing Z Up Y
        #     a = [("x","y","z"), 1*sideMult*self.lookAxisMult, 1*self.upAxisMult, 1*self.lookAxisMult]
        # elif self.lookAxis.replace("-","") == "z" and self.upAxis.replace("-","") == "x":
        #     ## Facing Z Up X
        #     a = [("y", "x", "z"), -1*sideMult*self.lookAxisMult, 1*self.upAxisMult, 1*self.lookAxisMult]
        # elif self.lookAxis.replace("-","") == "y" and self.upAxis.replace("-","") == "z":
        #     ## Facing Y Up Z
        #     a = [("x", "z", "y"), -1*sideMult*self.lookAxisMult, 1*self.upAxisMult, 1*self.lookAxisMult]
        # elif self.lookAxis.replace("-","") == "y" and self.upAxis.replace("-","") == "x":
        #     ## Facing Y Up X
        #     a = [("y", "z", "x"), 1*sideMult*self.lookAxisMult, 1*self.upAxisMult, 1*self.lookAxisMult]
        # elif self.lookAxis.replace("-","") == "x" and self.upAxis.replace("-","") == "z":
        #     ## Facing X Up Z
        #     a = [("z", "x", "y"), 1*sideMult*self.lookAxisMult, 1*self.upAxisMult, 1*self.lookAxisMult]
        # elif self.lookAxis.replace("-","") == "x" and self.upAxis.replace("-","") == "y":
        #     ## Facing X Up Y
        #     a = [("z", "y", "x"), -1*sideMult*self.lookAxisMult, 1*self.upAxisMult, 1*self.lookAxisMult]

        ### FROM HERE IT WILL BE LIMB SPECIFIC ###

        if limb == "spine":
            limbJoints, offsetVector = self.initialSpine(segments=segments, suffix=suffix)

        if limb == "arm":
            limbJoints, offsetVector = self.initialArm(side=side, suffix=suffix)
            # offsetVector = offsetVector * sideMult

        if limb == "leg":
            limbJoints, offsetVector = self.initialLeg(side=side, suffix=suffix)
            # offsetVector = offsetVector * sideMult

        if limb == "hand":
            limbJoints, jRoots = self.initialHand(fingerCount=fingerCount, side=side, suffix=suffix)

        if limb == "neck":
            limbJoints, offsetVector = self.initialNeck(segments=segments, suffix=suffix)

        if limb == "tail":
            limbJoints, offsetVector = self.initialTail(segments=segments, side=side, suffix=suffix)

        if limb == "finger":
            limbJoints, offsetVector = self.initialFinger(segments=segments, side=side, suffix=suffix, thumb=thumb)

        if limb == "tentacle":
            limbJoints, offsetVector = self.initialTentacle(segments=segments, side=side, suffix=suffix)

        if limb == "root":
            limbJoints, offsetVector = self.initialRoot(suffix=suffix)

        ### Constrain locating

        loc_grp = pm.group(name=("locGrp_%s" %suffix), em=True)
        pm.setAttr(loc_grp.v, 0)
        locatorsList=[]
        
        for i in range (0,len(limbJoints)):
            locator = pm.spaceLocator(name="loc_%s" % limbJoints[i].name())
            locatorsList.append(locator)
            if constrainedTo:
                extra.alignTo(locator, limbJoints[i], mode=0)
                print self.mirrorVector
                extra.connectMirror(constrainedTo[i], locatorsList[i], mirrorAxis=self.mirrorVector_asString)

                extra.alignTo(limbJoints[i], locator, mode=0)
                pm.parentConstraint(locator, limbJoints[i], mo=True)


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
                    # move it along offsetvector
                    pm.move(limbJoints[0], offsetVector, relative=True)
                else:
                    for x in limbJoints:
                        x.translate.lock()
                        x.rotate.lock()
                pm.parent(limbJoints[0], masterParent)
            else:
                pm.parent(limbJoints[0], limbGroup)
        pm.select(currentselection)

        return locatorsList

    # def _getMirror(self, vector):
    #     """Returns reflection of the vector along the mirror axis"""
    #     return vector-2*(vector * self.mirrorVector)*self.mirrorVector

    def initialRoot(self, suffix):
        """
        Creates a single simple root joint to connect or bridge limbs
        Args:
            transformKey: (List) the keyword for transformation matrix. transformator function will use this key to orienct joint in space
            suffix: (String) name suffix - must be unique

        Returns: (List) rootJoint

        """
        pm.select(d=True)
        rootInit = pm.joint(name="root_{0}".format(suffix))
        pm.setAttr("{0}.type".format(rootInit), 1)
        self.createAxisAttributes(rootInit)
        pm.setAttr(rootInit.radius, 3)
        pm.setAttr("{0}.drawLabel".format(rootInit), 1)
        offsetVector = dt.Vector(0,0,0)
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
        # rPoint = dt.Vector(self.transformator((0, 14.0, 0), transformKey))
        rPoint = dt.Vector(0, 14.0, 0) * self.tMatrix
        # nPoint = dt.Vector(self.transformator((0, 21.0, 0), transformKey))
        nPoint = dt.Vector(0, 21.0, 0) * self.tMatrix
        # rPoint = 14.0
        # nPoint = 21.0
        offsetVector = dt.normal(nPoint - rPoint)
        add = (nPoint - rPoint) / ((segments + 1) - 1)
        jointList = []
        for i in range(0, (segments + 1)):
            spine = pm.joint(p=(rPoint + (add * i)), name="jInit_spine_%s_%s" %(suffix, str(i)))
            pm.setAttr("%s.side" % spine, 0)
            type = 18
            if i == 0:
                # type = 1
                # pm.setAttr(spine + ".type", type)
                pm.setAttr("%s.type" % spine, type)
                pm.setAttr("%s.otherType" % spine, "SpineRoot")
                pm.addAttr(shortName="resolution", longName="Resolution", defaultValue=4, minValue=1,
                           at="long", k=True)
                pm.addAttr(shortName="dropoff", longName="DropOff", defaultValue=1.0, minValue=0.1,
                           at="float", k=True)
                pm.addAttr(at="enum", k=True, shortName="twistType", longName="Twist_Type", en="regular:infinite")
                pm.addAttr(at="enum", k=True, shortName="mode", longName="Mode", en="equalDistance:sameDistance")

                self.createAxisAttributes(spine)
                pm.setAttr(spine.radius, 3)

            elif i == (segments):
                # type = 18
                pm.setAttr("%s.type" % spine, type)
                pm.setAttr("%s.otherType" % spine, "SpineEnd")

            else:
                type = 6
                pm.setAttr("%s.type" % spine, type)

            jointList.append(spine)
            for i in jointList:
                pm.setAttr("%s.drawLabel" % i, 1)
                pm.setAttr(i.displayLocalAxis, 1)


        extra.orientJoints(jointList, worldUpAxis=-self.lookVector, reverseAim=sideMult, reverseUp=sideMult)

        self.spineJointsList.append(jointList)
        extra.colorize(jointList, self.majorCenterColor, shape=False)
        return jointList, offsetVector

    def initialArm(self, side, suffix):
        sideMult = -1 if side == 2 else 1
        # Initial Joint positions for centered arm
        if side == 0:
            collarVec = dt.Vector(0, 0, 2) * self.tMatrix
            shoulderVec = dt.Vector(0, 0, 5) * self.tMatrix
            elbowVec =  dt.Vector(0, -1, 9) * self.tMatrix
            handVec =  dt.Vector(0, 0, 14 ) * self.tMatrix
        # Initial Joint positions for left arm
        else:
            collarVec =  dt.Vector(2*sideMult, 0, 0) * self.tMatrix
            shoulderVec =  dt.Vector(5*sideMult, 0, 0) * self.tMatrix
            elbowVec =  dt.Vector(9*sideMult, 0, -1) * self.tMatrix
            handVec =  dt.Vector(14*sideMult, 0, 0 ) * self.tMatrix


        offsetVector = -(dt.normal(dt.Vector(collarVec) - dt.Vector(shoulderVec)))

        pm.select(d=True)
        collar = pm.joint(p=collarVec, name=("jInit_collar_%s" % suffix))
        pm.setAttr(collar.radius, 3)
        shoulder = pm.joint(p=shoulderVec, name=("jInit_shoulder_%s" % suffix))
        elbow = pm.joint(p=elbowVec, name=("jInit_elbow_%s" % suffix))
        hand = pm.joint(p=handVec, name=("jInit_hand_%s" % suffix))

        pm.setAttr(collar.displayLocalAxis, 1)
        pm.setAttr(shoulder.displayLocalAxis, 1)
        pm.setAttr(elbow.displayLocalAxis, 1)
        pm.setAttr(hand.displayLocalAxis, 1)

        # Orientation
        # pm.joint(collar, e=True, zso=True, oj="xyz", sao="yup")
        # pm.joint(shoulder, e=True, zso=True, oj="xyz", sao="yup")
        # pm.joint(elbow, e=True, zso=True, oj="xyz", sao="yup")
        # pm.joint(hand, e=True, zso=True, oj="xyz", sao="yup")

        # extra.orientJoints([collar, shoulder, elbow, hand], worldUpAxis=self.upVector, upAxis=(0,1,0), reverseAim=sideMult, reverseUp=sideMult)
        extra.orientJoints([collar, shoulder, elbow, hand], worldUpAxis=self.lookVector, upAxis=(0, 1, 0), reverseAim=sideMult, reverseUp=sideMult)

        # Joint Labeling
        pm.setAttr("%s.side" % collar, side)
        pm.setAttr("%s.type" % collar, 9)
        pm.setAttr("%s.side" % shoulder, side)
        pm.setAttr("%s.type" % shoulder, 10)
        pm.setAttr("%s.side" % elbow, side)
        pm.setAttr("%s.type" % elbow, 11)
        pm.setAttr("%s.side" % hand, side)
        pm.setAttr("%s.type" % hand, 12)

        # custom Attributes
        self.createAxisAttributes(collar)

        jointList=[collar, shoulder, elbow, hand]
        for i in jointList:
            pm.setAttr("%s.drawLabel" % i, 1)
        self.armJointsList.append(jointList)

        if side == 0:
            extra.colorize(jointList, self.majorCenterColor, shape=False)
        if side == 1:
            extra.colorize(jointList, self.majorLeftColor, shape=False)
        if side == 2:
            extra.colorize(jointList, self.majorRightColor, shape=False)

        return jointList, offsetVector
    
    def initialLeg(self, side, suffix):
        sideMult = -1 if side == 2 else 1
        if side == 0:
            rootVec = dt.Vector(0, 14, 0) * self.tMatrix
            hipVec = dt.Vector(0, 10, 0) * self.tMatrix
            kneeVec = dt.Vector(0, 5, 1) * self.tMatrix
            footVec = dt.Vector(0, 1, 0) * self.tMatrix
            ballVec = dt.Vector(0, 0, 2) * self.tMatrix
            toeVec = dt.Vector(0, 0, 4) * self.tMatrix
            bankoutVec = dt.Vector(-1, 0, 2) * self.tMatrix
            bankinVec = dt.Vector(1, 0, 2) * self.tMatrix
            toepvVec = dt.Vector(0, 0, 4.3) * self.tMatrix
            heelpvVec = dt.Vector(0, 0, -0.2) * self.tMatrix

        else:
            rootVec = dt.Vector(2*sideMult,14,0) * self.tMatrix
            hipVec = dt.Vector(5*sideMult,10,0) * self.tMatrix
            kneeVec = dt.Vector(5*sideMult,5,1) * self.tMatrix
            footVec = dt.Vector(5*sideMult,1,0) * self.tMatrix
            ballVec = dt.Vector(5*sideMult,0,2) * self.tMatrix
            toeVec = dt.Vector(5*sideMult,0,4) * self.tMatrix
            bankoutVec = dt.Vector(4*sideMult,0,2) * self.tMatrix
            bankinVec = dt.Vector(6*sideMult,0,2) * self.tMatrix
            toepvVec = dt.Vector(5*sideMult,0,4.3) * self.tMatrix
            heelpvVec = dt.Vector(5*sideMult,0,-0.2) * self.tMatrix


        offsetVector = -(dt.normal(dt.Vector(rootVec) - dt.Vector(hipVec)))
        print "ananinAmi_rootVector", rootVec, hipVec
        print "ananinAmi", offsetVector

        
        root = pm.joint(p=rootVec, name=("jInit_LegRoot_%s" % suffix))
        pm.setAttr(root.radius, 3)
        hip = pm.joint(p=hipVec, name=("jInit_Hip_%s" % suffix))
        knee = pm.joint(p=kneeVec, name=("jInit_Knee_%s" % suffix))
        foot = pm.joint(p=footVec, name=("jInit_Foot_%s" % suffix))

        # extra.orientJoints([root, hip, knee, foot], worldUpAxis=self.upVector, upAxis=(0, 1, 0), reverseAim=sideMult)
        extra.orientJoints([root, hip, knee, foot], worldUpAxis=self.mirrorVector, upAxis=(0, 1, 0), reverseAim=sideMult)

        # return

        ball = pm.joint(p=ballVec, name=("jInit_Ball_%s" % suffix))
        toe = pm.joint(p=toeVec, name=("jInit_Toe_%s" % suffix))
        pm.select(d=True)
        bankout = pm.joint(p=bankoutVec, name=("jInit_BankOut_%s" % suffix))
        pm.select(d=True)
        bankin = pm.joint(p=bankinVec, name=("jInit_BankIn_%s" % suffix))
        pm.select(d=True)
        toepv = pm.joint(p=toepvVec, name=("jInit_ToePv_%s" % suffix))
        pm.select(d=True)
        heelpv = pm.joint(p=heelpvVec, name=("jInit_HeelPv_%s" % suffix))
        # pm.joint(root, e=True, zso=True, oj="xyz", sao="yup")
        # pm.joint(hip, e=True, zso=True, oj="xyz", sao="yup")
        # pm.joint(knee, e=True, zso=True, oj="xyz", sao="yup")
        # pm.joint(foot, e=True, zso=True, oj="xyz", sao="yup")
        # pm.joint(ball, e=True, zso=True, oj="xyz", sao="yup")
        # pm.joint(toe, e=True, zso=True, oj="xyz", sao="yup")
        pm.parent(heelpv, foot)
        pm.parent(toepv, foot)
        pm.parent(bankin, foot)
        pm.parent(bankout, foot)

        # extra.orientJoints([ball, toe], worldUpAxis=self.mirrorVector, reverseAim=sideMult)
        extra.orientJoints([ball, toe], worldUpAxis=self.mirrorVector, upAxis=(0, 1, 0), reverseAim=sideMult)


        # extra.orientJoints([root, hip, knee, foot, ball, toe], worldUpAxis=(0.0,1.0,0.0), upAxis=(1.0,0.0,0.0), reverseAim=direction)


        # extra.orientJoints([collar, shoulder, elbow, hand], worldUpAxis=(0.0,1.0,0.0), upAxis=(0.0,0.0,-1.0), reverseAim=direction, reverseUp=direction)


        pm.setAttr("%s.side" % root, side)
        pm.setAttr("%s.type" % root, 18)
        pm.setAttr("%s.otherType" % root, "LegRoot")
        pm.setAttr(root.displayLocalAxis, 1)

        pm.setAttr("%s.side" % hip, side)
        pm.setAttr("%s.type" % hip, 2)
        pm.setAttr(hip.displayLocalAxis, 1)

        pm.setAttr("%s.side" % knee, side)
        pm.setAttr("%s.type" % knee, 3)
        pm.setAttr(knee.displayLocalAxis, 1)

        pm.setAttr("%s.side" % foot, side)
        pm.setAttr("%s.type" % foot, 4)
        pm.setAttr(foot.displayLocalAxis, 1)

        pm.setAttr("%s.side" % ball, side)
        pm.setAttr("%s.type" % ball, 18)
        pm.setAttr("%s.otherType" % ball, "Ball")
        pm.setAttr(ball.displayLocalAxis, 1)

        pm.setAttr("%s.side" % toe, side)
        pm.setAttr("%s.type" % toe, 5)
        pm.setAttr(toe.displayLocalAxis, 1)

        pm.setAttr("%s.side" % heelpv, side)
        pm.setAttr("%s.type" % heelpv, 18)
        pm.setAttr("%s.otherType" % heelpv, "HeelPV")
        pm.setAttr("%s.side" % toepv, side)
        pm.setAttr("%s.type" % toepv, 18)
        pm.setAttr("%s.otherType" % toepv, "ToePV")
        pm.setAttr("%s.side" % bankin, side)
        pm.setAttr("%s.type" % bankin, 18)
        pm.setAttr("%s.otherType" % bankin, "BankIN")
        pm.setAttr("%s.side" % bankout, side)
        pm.setAttr("%s.type" % bankout, 18)
        pm.setAttr("%s.otherType" % bankout, "BankOUT")

        ## custom attributes
        self.createAxisAttributes(root)

        jointList = [root, hip, knee, foot, ball, toe, bankout, bankin, toepv, heelpv]
        for i in jointList:
            pm.setAttr("%s.drawLabel" % i, 1)

        if side == 0:
            extra.colorize(jointList, self.majorCenterColor, shape=False)
        if side == 1:
            extra.colorize(jointList, self.majorLeftColor, shape=False)
        if side == 2:
            extra.colorize(jointList, self.majorRightColor, shape=False)

        # extra.orientJoints([ball, toe], worldUpAxis=(0.0,1.0,0.0), upAxis=(1.0,0.0,0.0), reverseAim=direction)

        # print "OFFSET VECTOR", sideMult, offsetVector
        return jointList, offsetVector


    def initialHand(self, fingerCount, side, suffix):
        sideMult = -1 if side == 2 else 1

        jointList = []
        fingerRoots = []

        if fingerCount > 0:
            thumb00vec = dt.Vector(0.681*sideMult, -0.143, 0.733) * self.tMatrix
            thumb01vec = dt.Vector(1.192*sideMult, -0.21, 1.375) * self.tMatrix
            thumb02vec = dt.Vector(1.64*sideMult, -0.477, 1.885) * self.tMatrix
            thumb03vec = dt.Vector(2.053*sideMult, -0.724, 2.356) * self.tMatrix

            pm.select(d=True)

            # thumbJoints = [pm.joint(p=thumb00vec, name=("jInit_thumb%s_%s" % (x, suffix))) for x in range(4)]
            thumb00 = pm.joint(p=thumb00vec, name=("jInit_thumb00_%s" % suffix))
            thumb01 = pm.joint(p=thumb01vec, name=("jInit_thumb01_%s" % suffix))
            thumb02 = pm.joint(p=thumb02vec, name=("jInit_thumb02_%s" % suffix))
            thumb03 = pm.joint(p=thumb03vec, name=("jInit_thumb03_%s" % suffix))
            thumbJoints = [thumb00, thumb01, thumb02, thumb03]

            extra.orientJoints(thumbJoints, worldUpAxis=self.upVector, upAxis=(0,-1,0), reverseAim=sideMult,
                               reverseUp=sideMult)


            for i in thumbJoints:
                pm.setAttr(i.displayLocalAxis, 1)
                if i == thumbJoints[0]:
                    pm.setAttr("%s.type" % i, 18)
                    pm.setAttr("%s.otherType" % i, "FingerRoot")
                else:
                    # pm.joint(i, e=True, zso=True, oj="xyz", sao="yup")
                    pm.setAttr("%s.type" % i, 13)
                pm.setAttr("%s.side" % i, side)
            # draw label on knuckles
            pm.setAttr("%s.drawLabel" % thumbJoints[1], 1)
            self.createAxisAttributes(thumbJoints[0])
            pm.addAttr(thumbJoints[0], shortName="fingerType", longName="Finger_Type", at="enum",
                       en="Extra:Thumb:Index:Middle:Ring:Pinky:Toe", k=True)
            pm.setAttr(thumbJoints[0].fingerType, 1)

            self.fingerJointsList.append(thumbJoints)
            jointList.extend(thumbJoints)
            fingerRoots.append(thumbJoints[0])

        if fingerCount > 1:
            index00vec = dt.Vector(1.517*sideMult, 0.05, 0.656) * self.tMatrix
            index01vec = dt.Vector(2.494*sideMult, 0.05, 0.868) * self.tMatrix
            index02vec = dt.Vector(3.126*sideMult, 0.05, 1.005) * self.tMatrix
            index03vec = dt.Vector(3.746*sideMult, 0.05, 1.139) * self.tMatrix
            index04vec = dt.Vector(4.278*sideMult, 0.05, 1.254) * self.tMatrix

            pm.select(d=True)
            index00 = pm.joint(p=index00vec, name=("jInit_indexF00_%s" % suffix))
            index01 = pm.joint(p=index01vec, name=("jInit_indexF01_%s" % suffix))
            index02 = pm.joint(p=index02vec, name=("jInit_indexF02_%s" % suffix))
            index03 = pm.joint(p=index03vec, name=("jInit_indexF03_%s" % suffix))
            index04 = pm.joint(p=index04vec, name=("jInit_indexF04_%s" % suffix))
            indexJoints = [index00, index01, index02, index03, index04]
            extra.orientJoints(indexJoints, worldUpAxis=self.upVector, upAxis=(0,-1,0), reverseAim=sideMult,
                               reverseUp=sideMult)
            for i in indexJoints:
                pm.setAttr(i.displayLocalAxis, 1)

                if i == indexJoints[0]:
                    pm.setAttr("%s.type" % i, 18)
                    pm.setAttr("%s.otherType" % i, "FingerRoot")
                else:
                    # pm.joint(i, e=True, zso=True, oj="xyz", sao="yup")
                    pm.setAttr("%s.type" % i, 13)
                pm.setAttr("%s.side" % i, side)
            pm.setAttr("%s.drawLabel" % index01, 1)
            self.createAxisAttributes(indexJoints[0])
            pm.addAttr(indexJoints[0], shortName="fingerType", longName="Finger_Type", at="enum",
                       en="Extra:Thumb:Index:Middle:Ring:Pinky:Toe", k=True)
            pm.setAttr(indexJoints[0].fingerType, 2)
            self.fingerJointsList.append(indexJoints)
            jointList.extend(indexJoints)
            fingerRoots.append(index00)

        if fingerCount > 2:
            middle00vec = dt.Vector(1.597*sideMult, 0.123, 0.063) * self.tMatrix
            middle01vec = dt.Vector(2.594*sideMult, 0.123, 0.137) * self.tMatrix
            middle02vec = dt.Vector(3.312*sideMult, 0.123, 0.19) * self.tMatrix
            middle03vec = dt.Vector(4.012*sideMult, 0.123, 0.242) * self.tMatrix
            middle04vec = dt.Vector(4.588*sideMult, 0.123, 0.285) * self.tMatrix

            pm.select(d=True)
            middle00 = pm.joint(p=middle00vec, name=("jInit_middleF00_%s" % suffix))
            middle01 = pm.joint(p=middle01vec, name=("jInit_middleF01_%s" % suffix))
            middle02 = pm.joint(p=middle02vec, name=("jInit_middleF02_%s" % suffix))
            middle03 = pm.joint(p=middle03vec, name=("jInit_middleF03_%s" % suffix))
            middle04 = pm.joint(p=middle04vec, name=("jInit_middleF04_%s" % suffix))
            middleJoints = [middle00, middle01, middle02, middle03, middle04]
            extra.orientJoints(middleJoints, worldUpAxis=self.upVector, upAxis=(0,-1,0), reverseAim=sideMult,
                               reverseUp=sideMult)
            for i in middleJoints:
                pm.setAttr(i.displayLocalAxis, 1)

                if i == middleJoints[0]:
                    pm.setAttr("%s.type" % i, 18)
                    pm.setAttr("%s.otherType" % i, "FingerRoot")

                else:
                    # pm.joint(i, e=True, zso=True, oj="xyz", sao="yup")
                    pm.setAttr("%s.type" % i, 13)
                pm.setAttr("%s.side" % i, side)
            pm.setAttr("%s.drawLabel" % middle01, 1)
            self.createAxisAttributes(middleJoints[0])
            pm.addAttr(middleJoints[0], shortName="fingerType", longName="Finger_Type", at="enum",
                       en="Extra:Thumb:Index:Middle:Ring:Pinky:Toe", k=True)
            pm.setAttr(middleJoints[0].fingerType, 3)
            self.fingerJointsList.append(middleJoints)
            jointList.extend(middleJoints)
            fingerRoots.append(middle00)

        if fingerCount > 3:
            ring00vec = dt.Vector(1.605*sideMult, 0.123, -0.437) * self.tMatrix
            ring01vec = dt.Vector(2.603*sideMult, 0.123, -0.499) * self.tMatrix
            ring02vec = dt.Vector(3.301*sideMult, 0.123, -0.541) * self.tMatrix
            ring03vec = dt.Vector(3.926*sideMult, 0.123, -0.58) * self.tMatrix
            ring04vec = dt.Vector(4.414*sideMult, 0.123, -0.58) * self.tMatrix

            pm.select(d=True)
            ring00 = pm.joint(p=ring00vec, name=("jInit_ringF00_%s" % suffix))
            ring01 = pm.joint(p=ring01vec, name=("jInit_ringF01_%s" % suffix))
            ring02 = pm.joint(p=ring02vec, name=("jInit_ringF02_%s" % suffix))
            ring03 = pm.joint(p=ring03vec, name=("jInit_ringF03_%s" % suffix))
            ring04 = pm.joint(p=ring04vec, name=("jInit_ringF04_%s" % suffix))
            ringJoints = [ring00, ring01, ring02, ring03, ring04]
            extra.orientJoints(ringJoints, worldUpAxis=self.upVector, upAxis=(0,-1,0), reverseAim=sideMult,
                               reverseUp=sideMult)
            for i in ringJoints:
                pm.setAttr(i.displayLocalAxis, 1)

                if i == ringJoints[0]:
                    pm.setAttr("%s.type" % i, 18)
                    pm.setAttr("%s.otherType" % i, "FingerRoot")

                else:
                    # pm.joint(i, e=True, zso=True, oj="xyz", sao="yup")
                    pm.setAttr("%s.type" % i, 13)
                pm.setAttr("%s.side" % i, side)
            pm.setAttr("%s.drawLabel" % ring01, 1)
            self.createAxisAttributes(ringJoints[0])
            pm.addAttr(ringJoints[0], shortName="fingerType", longName="Finger_Type", at="enum",
                       en="Extra:Thumb:Index:Middle:Ring:Pinky:Toe", k=True)
            pm.setAttr(ringJoints[0].fingerType, 4)
            self.fingerJointsList.append(ringJoints)
            jointList.extend(ringJoints)
            fingerRoots.append(ring00)

        if fingerCount > 4:
            pinky00vec = dt.Vector(1.405*sideMult, 0, -0.909) * self.tMatrix
            pinky01vec = dt.Vector(2.387*sideMult, 0, -1.097) * self.tMatrix
            pinky02vec = dt.Vector(2.907*sideMult, 0, -1.196) * self.tMatrix
            pinky03vec = dt.Vector(3.378*sideMult, 0, -1.286) * self.tMatrix
            pinky04vec = dt.Vector(3.767*sideMult, 0, -1.361) * self.tMatrix

            pm.select(d=True)
            pinky00 = pm.joint(p=pinky00vec, name=("jInit_pinkyF00_%s" % suffix))
            pinky01 = pm.joint(p=pinky01vec, name=("jInit_pinkyF01_%s" % suffix))
            pinky02 = pm.joint(p=pinky02vec, name=("jInit_pinkyF02_%s" % suffix))
            pinky03 = pm.joint(p=pinky03vec, name=("jInit_pinkyF03_%s" % suffix))
            pinky04 = pm.joint(p=pinky04vec, name=("jInit_pinkyF04_%s" % suffix))
            pinkyJoints = [pinky00, pinky01, pinky02, pinky03, pinky04]
            extra.orientJoints(pinkyJoints, worldUpAxis=self.upVector, upAxis=(0,-1,0), reverseAim=sideMult,
                               reverseUp=sideMult)
            for i in pinkyJoints:
                pm.setAttr(i.displayLocalAxis, 1)
                if i == pinkyJoints[0]:
                    pm.setAttr("%s.type" % i, 18)
                    pm.setAttr("%s.otherType" % i, "FingerRoot")
                else:
                    # pm.joint(i, e=True, zso=True, oj="xyz", sao="yup")
                    pm.setAttr("%s.type" % i, 13)
                pm.setAttr("%s.side" % i, side)
            pm.setAttr("%s.drawLabel" % pinky01, 1)
            self.createAxisAttributes(pinkyJoints[0])
            pm.addAttr(pinkyJoints[0], shortName="fingerType", longName="Finger_Type", at="enum",
                       en="Extra:Thumb:Index:Middle:Ring:Pinky:Toe", k=True)
            pm.setAttr(pinkyJoints[0].fingerType, 5)
            self.fingerJointsList.append(pinkyJoints)
            jointList.extend(pinkyJoints)
            fingerRoots.append(pinky00)

        if fingerCount > 5:
            for x in range(0, (fingerCount - 5)):
                ##//TODO put extra fingers
                pass
        for r in fingerRoots:
            pm.setAttr(r.radius, 2)

        if side == 0:
            extra.colorize(jointList, self.majorCenterColor, shape=False)
        if side == 1:
            extra.colorize(jointList, self.majorLeftColor, shape=False)
        if side == 2:
            extra.colorize(jointList, self.majorRightColor, shape=False)

        return jointList, fingerRoots

    def initialNeck(self, segments, suffix, side=0):
        sideMult = -1 if side == 2 else 1

        rPointNeck =  dt.Vector(0, 25.757, 0) * self.tMatrix
        nPointNeck =  dt.Vector(0, 29.418, 0.817) * self.tMatrix
        pointHead =  dt.Vector(0, 32,0.817) * self.tMatrix
        offsetVector = dt.normal(nPointNeck-rPointNeck)
        addNeck = (nPointNeck - rPointNeck) / ((segments + 1) - 1)
        jointList = []
        for i in range(0, (segments + 1)):
            if not i == (segments):
                neck = pm.joint(p=(rPointNeck + (addNeck * i)), name="jInit_neck_%s_%s" %(suffix, str(i)))
                pm.setAttr("%s.side" % neck, 0)

                if i == 0:
                    pm.setAttr("%s.type" % neck, 18)
                    pm.setAttr("%s.otherType" % neck, "NeckRoot")
                    pm.addAttr(shortName="resolution", longName="Resolution", defaultValue=4, minValue=1,
                               at="long", k=True)
                    pm.addAttr(shortName="dropoff", longName="DropOff", defaultValue=1.0, minValue=0.1,
                               at="float", k=True)
                    pm.addAttr(at="enum", k=True, shortName="twistType", longName="Twist_Type", en="regular:infinite")
                    pm.addAttr(at="enum", k=True, shortName="mode", longName="Mode", en="equalDistance:sameDistance")
                    self.createAxisAttributes(neck)
                    pm.setAttr(neck.radius, 3)

                else:
                    pm.setAttr("%s.type" % neck, 7)

            else:
                neck= pm.joint(p=(rPointNeck + (addNeck * i)), name="jInit_head_%s_%s" %(suffix, str(i)))
                pm.setAttr("%s.type" % neck, 8)
                self.createAxisAttributes(neck)
            pm.setAttr("%s.drawLabel" % neck, 1)
            jointList.append(neck)
        headEnd = pm.joint(p=pointHead, name="jInit_headEnd_%s_%s" %(suffix, str(i)))
        pm.setAttr("%s.side" % headEnd, 0)
        pm.setAttr("%s.type" % headEnd, 18)
        pm.setAttr("%s.otherType" % headEnd, "HeadEnd")
        pm.setAttr("%s.drawLabel" % headEnd, 1)
        jointList.append(headEnd)

        extra.orientJoints(jointList, worldUpAxis=-self.lookVector, reverseAim=sideMult, reverseUp=sideMult)
        # lambda x: pm.setAttr(i.displayLocalAxis, 1)
        map(lambda x: pm.setAttr(x.displayLocalAxis, 1), jointList)
        self.neckJointsList.append(jointList)

        extra.colorize(jointList, self.majorCenterColor, shape=False)
        return jointList, offsetVector

    def initialTail(self,  side, segments, suffix):
        sideMult = -1 if side == 2 else 1
        if segments < 1:
            pm.warning("minimum segments required for the simple tail is two. current: %s" %segments)
            return

        rPointTail = dt.Vector(0, 14, 0) * self.tMatrix
        if side == 0:
            nPointTail = dt.Vector(0, 8.075, -7.673) * self.tMatrix
        else:
            nPointTail = dt.Vector(7.673*sideMult, 8.075, 0) * self.tMatrix
        # nPointTail = dt.Vector(self.transformator((0, 8.075, -7.673), transformKey))
        offsetVector = dt.normal(nPointTail-rPointTail)
        addTail = (nPointTail - rPointTail) / ((segments + 1) - 1)
        jointList = []
        for i in range(0, (segments + 1)):
            tail = pm.joint(p=(rPointTail + (addTail * i)), name="jInit_tail_%s_%s" %(suffix, str(i)))
            pm.setAttr("%s.side" % tail, side)

            if i == 0:
                pm.setAttr("%s.type" % tail, 18)
                pm.setAttr("%s.otherType" % tail, "TailRoot")
                self.createAxisAttributes(tail)
                pm.setAttr(tail.radius, 3)
            else:
                pm.setAttr("%s.type" % tail, 18)
                pm.setAttr("%s.otherType" % tail, "Tail")

            pm.setAttr("%s.drawLabel" % tail, 1)
            jointList.append(tail)

        self.tailJointsList.append(jointList)
        map(lambda x: pm.setAttr(x.displayLocalAxis, 1), jointList)
        extra.orientJoints(jointList, worldUpAxis=self.lookVector, upAxis=(0,1,0), reverseAim=sideMult, reverseUp=sideMult)

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
            pm.warning("minimum segments for the fingers are two. current: %s" %segments)
            return


        rPointFinger = dt.Vector(0, 0, 0) * self.tMatrix
        nPointFinger = dt.Vector(5*sideMult, 0, 0) * self.tMatrix


        offsetVector = dt.normal(nPointFinger-rPointFinger)
        addFinger = (nPointFinger - rPointFinger) / ((segments + 1) - 1)

        jointList = []
        for i in range(0, (segments + 1)):
            finger = pm.joint(p=(rPointFinger + (addFinger * i)), name="jInit_finger_%s_%s" %(suffix, str(i)))
            pm.setAttr("%s.side" % finger, side)

            if i == 0:
                pm.setAttr("%s.type" % finger, 18)
                pm.setAttr("%s.otherType" % finger, "FingerRoot")
                pm.setAttr("%s.drawLabel" % finger, 1)
                self.createAxisAttributes(finger)
                # pm.addAttr(finger, shortName="thumb", longName="Thumb",
                #                at="bool", k=True)
                # pm.setAttr(finger.thumb, thumb)
                pm.addAttr(finger, shortName="fingerType", longName="Finger_Type", at="enum", en="Extra:Thumb:Index:Middle:Ring:Pinky:Toe", k=True)

                pm.setAttr(finger.radius, 2)
            else:
                pm.setAttr("%s.type" % finger, 13)


            jointList.append(finger)

        self.fingerJointsList.append(jointList)
        map(lambda x: pm.setAttr(x.displayLocalAxis, 1), jointList)
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
            pm.warning("minimum segments required for the tentacle is two. current: %s" %segments)
            return
        rPointTentacle = dt.Vector(0, 14, 0) * self.tMatrix
        if side == 0:
            nPointTentacle = dt.Vector(0, 14, 10) * self.tMatrix
        else:
            nPointTentacle = dt.Vector(10*sideMult, 14, 0) * self.tMatrix
        offsetVector = dt.normal(nPointTentacle-rPointTentacle)
        addTentacle = (nPointTentacle - rPointTentacle) / ((segments + 1) - 1)
        jointList = []
        for i in range(0, (segments + 1)):
            tentacle = pm.joint(p=(rPointTentacle + (addTentacle * i)), name="jInit_tentacle_%s_%s" %(suffix, str(i)))
            pm.setAttr("%s.side" % tentacle, side)

            if i == 0:
                pm.setAttr("%s.type" % tentacle, 18)
                pm.setAttr("%s.otherType" % tentacle, "TentacleRoot")
                pm.addAttr(shortName="contRes", longName="Cont_Resolution", defaultValue=5, minValue=1,
                           at="long", k=True)
                pm.addAttr(shortName="jointRes", longName="Joint_Resolution", defaultValue=25, minValue=1,
                           at="long", k=True)
                pm.addAttr(shortName="deformerRes", longName="Deformer_Resolution", defaultValue=25, minValue=1,
                           at="long", k=True)
                pm.addAttr(shortName="dropoff", longName="DropOff", defaultValue=2.0, minValue=0.1,
                           at="float", k=True)
                self.createAxisAttributes(tentacle)
                pm.setAttr(tentacle.radius, 3)
            else:
                pm.setAttr("%s.type" % tentacle, 18)
                pm.setAttr("%s.otherType" % tentacle, "Tentacle")

            pm.setAttr("%s.drawLabel" % tentacle, 1)
            jointList.append(tentacle)

        self.tentacleJointsList.append(jointList)
        map(lambda x: pm.setAttr(x.displayLocalAxis, 1), jointList)
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
        pm.select(root)
        self.initLimb("leg", "auto")

        pm.select(chest)
        self.initLimb("arm", "auto")
        self.initLimb("neck", "auto", segments=neckSegments)
        rHand =  self.armJointsList[0][-1]

        pm.select(rHand)
        self.initLimb("hand", "auto", fingerCount=fingers)

    def convertSelectionToInits(self, limbType, jointList=[], suffix="", whichside=""):

        ## // TODO PAY ATTENTION HERE: THIS METHOD IS BROKEN

        ##
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
                pm.warning("You need to select at least 2 joints for spine conversion\nNothing Changed")
                return
            for j in range (len(jointList)):
                # newName = "jInit_spine_%s_%s" % (suffix, str(j))
                pm.select(jointList[j])
                # pm.rename(jointList[j], newName)
                pm.setAttr("%s.side" % jointList[j],0)
                pm.setAttr("%s.drawLabel" % jointList[j], 1)
                ## if it is the first jointList
                if j == 0:
                    type =18
                    pm.setAttr("%s.type" % jointList[j], type)
                    pm.setAttr("%s.otherType" % jointList[j], "SpineRoot")

                    if not pm.attributeQuery("resolution", node=jointList[j], exists=True):
                        pm.addAttr(shortName="resolution", longName="Resolution", defaultValue=4, minValue=1,
                               at="long", k=True)
                    if not pm.attributeQuery("dropoff", node=jointList[j], exists=True):
                        pm.addAttr(shortName="dropoff", longName="DropOff", defaultValue=1.0, minValue=0.1,
                               at="float", k=True)
                    if not pm.attributeQuery("twistType", node=jointList[j], exists=True):
                        pm.addAttr(at="enum", k=True, shortName="twistType", longName="Twist_Type", en="regular:infinite")
                    if not pm.attributeQuery("mode", node=jointList[j], exists=True):
                        pm.addAttr(at="enum", k=True, shortName="mode", longName="Mode", en="equalDistance:sameDistance")

                    pm.setAttr(jointList[j].radius, 3)
                    # pm.setAttr(jointList[j].radius, 3)

                elif jointList[j] == jointList[-1]:
                    type = 18
                    pm.setAttr("%s.type" % jointList[j], type)
                    pm.setAttr("%s.otherType" % jointList[j], "SpineEnd")

                else:
                    type = 6
                    pm.setAttr("%s.type" % jointList[j], type)

        if limbType == "tail":
            if len(jointList) < 2:
                pm.warning("You need to select at least 2 joints for tail conversion\nNothing Changed")
                return
            for j in range(len(jointList)):
                # newName = "jInit_tail_%s_%s" % (suffix, str(j))
                pm.select(jointList[j])
                # pm.rename(jointList[j], newName)
                pm.setAttr("%s.side" % jointList[j], side)
                pm.setAttr("%s.drawLabel" % jointList[j], 1)

                ## if it is the first selection
                if j == 0:
                    pm.setAttr("%s.type" % jointList[j], 18)
                    pm.setAttr("%s.otherType" % jointList[j], "TailRoot")
                    # pm.setAttr(jointList[j].radius, 3)
                else:
                    pm.setAttr("%s.type" % jointList[j], 18)
                    pm.setAttr("%s.otherType" % jointList[j], "Tail")

        if limbType == "arm":
            if not len(jointList) == 4:
                pm.warning("You must select exactly 4 joints to define the chain as Arm\nNothing Changed")
                return
            pm.setAttr("%s.side" % jointList[0], side)
            pm.setAttr("%s.type" % jointList[0], 9)
            pm.setAttr("%s.side" % jointList[1], side)
            pm.setAttr("%s.type" % jointList[1], 10)
            pm.setAttr("%s.side" % jointList[2], side)
            pm.setAttr("%s.type" % jointList[2], 11)
            pm.setAttr("%s.side" % jointList[3], side)
            pm.setAttr("%s.type" % jointList[3], 12)

        if limbType == "leg":
            if not len(jointList) == 10:
                pm.warning("You must select exactly 10 joints to define the chain as Leg\nNothing Changed\nCorrect jointList order is Root -> Hip -> Knee -> Foot -> Ball -> Heel Pivot -> Toe Pivot -> Bank In Pivot -> Bank Out Pivot")
                return
            pm.setAttr("%s.side" % jointList[0], side)
            pm.setAttr("%s.type" % jointList[0], 18)
            pm.setAttr("%s.otherType" % jointList[0], "LegRoot")
            pm.setAttr("%s.side" % jointList[1], side)
            pm.setAttr("%s.type" % jointList[1], 2)
            pm.setAttr("%s.side" % jointList[2], side)
            pm.setAttr("%s.type" % jointList[2], 3)
            pm.setAttr("%s.side" % jointList[3], side)
            pm.setAttr("%s.type" % jointList[3], 4)

            pm.setAttr("%s.side" % jointList[4], side)
            pm.setAttr("%s.type" % jointList[4], 18)
            pm.setAttr("%s.otherType" % jointList[4], "Ball")

            pm.setAttr("%s.side" % jointList[5], side)
            pm.setAttr("%s.type" % jointList[5], 5)

            pm.setAttr("%s.side" % jointList[6], side)
            pm.setAttr("%s.type" % jointList[6], 18)
            pm.setAttr("%s.otherType" % jointList[6], "HeelPV")
            pm.setAttr("%s.side" % jointList[7], side)
            pm.setAttr("%s.type" % jointList[7], 18)
            pm.setAttr("%s.otherType" % jointList[7], "ToePV")
            pm.setAttr("%s.side" % jointList[8], side)
            pm.setAttr("%s.type" % jointList[8], 18)
            pm.setAttr("%s.otherType" % jointList[8], "BankIN")
            pm.setAttr("%s.side" % jointList[9], side)
            pm.setAttr("%s.type" % jointList[9], 18)
            pm.setAttr("%s.otherType" % jointList[9], "BankOUT")

        if limbType == "neck":
            if not len(jointList) >= 3:
                pm.warning("You must select exactly 3 joints to define the chain as Neck and Head\nNothing Changed")
                return
            for i in range(len(jointList)):
                if i == 0:
                    pm.setAttr("%s.type" % jointList[i], 18)
                    pm.setAttr("%s.otherType" % jointList[i], "NeckRoot")
                    pm.select(jointList[i])

                    if not pm.attributeQuery("resolution", node=jointList[i], exists=True):
                        pm.addAttr(shortName="resolution", longName="Resolution", defaultValue=4, minValue=1,
                               at="long", k=True)
                    if not pm.attributeQuery("dropoff", node=jointList[i], exists=True):
                        pm.addAttr(shortName="dropoff", longName="DropOff", defaultValue=1.0, minValue=0.1,
                               at="float", k=True)
                    if not pm.attributeQuery("twistType", node=jointList[i], exists=True):
                        pm.addAttr(at="enum", k=True, shortName="twistType", longName="Twist_Type", en="regular:infinite")
                    if not pm.attributeQuery("mode", node=jointList[i], exists=True):
                        pm.addAttr(at="enum", k=True, shortName="mode", longName="Mode", en="equalDistance:sameDistance")

                elif jointList[i] == jointList[-2]:
                    pm.setAttr("%s.type" % jointList[i], 8)
                elif jointList[i] == jointList[-1]:
                    pm.setAttr("%s.side" % jointList[i], 0)
                    pm.setAttr("%s.type" % jointList[i], 18)
                    pm.setAttr("%s.otherType" % jointList[i], "HeadEnd")
                    pm.setAttr("%s.drawLabel" % jointList[i], 1)
                else:
                    pm.setAttr("%s.type" % jointList[i], 7)
                pm.setAttr("%s.drawLabel" % jointList[i], 1)

        if limbType == "finger":
            if not len(jointList) > 1:
                pm.warning("You must at least 2 joints to define the chain as Finger\nNothing Changed")
                return
            for i in range (len(jointList)):
                pm.setAttr("%s.side" % jointList[i], 0)

                if i == 0:
                    pm.setAttr("%s.type" % jointList[i], 18)
                    pm.setAttr("%s.otherType" % jointList[i], "FingerRoot")
                    pm.setAttr("%s.drawLabel" % jointList[i], 1)
                    if not pm.attributeQuery("fingerType", node=jointList[i], exists=True):
                        pm.addAttr(jointList[i], shortName="fingerType", longName="Finger_Type", at="enum",
                               en="Extra:Thumb:Index:Middle:Ring:Pinky:Toe", k=True)
                else:
                    # pm.setAttr("%s.type" % jointList[i], 23)
                    pm.setAttr("%s.type" % jointList[i], 13)

        if limbType == "tentacle":
            if not len(jointList) > 1:
                pm.warning("minimum segments required for the tentacle is two. current: %s" % len(jointList))
                return

            for j in range(len(jointList)):
                # newName = "jInit_tail_%s_%s" % (suffix, str(j))
                pm.select(jointList[j])
                # pm.rename(jointList[j], newName)
                pm.setAttr("%s.side" % jointList[j], side)
                pm.setAttr("%s.drawLabel" % jointList[j], 1)
                ## if it is the first selection
                if j == 0:
                    pm.setAttr("%s.type" % jointList[j], 18)
                    pm.setAttr("%s.otherType" % jointList[j], "TentacleRoot")
                    if not pm.attributeQuery("contRes", node=jointList[j], exists=True):
                        pm.addAttr(shortName="contRes", longName="Cont_Resolution", defaultValue=5, minValue=1,
                                   at="long", k=True)
                    if not pm.attributeQuery("jointRes", node=jointList[j], exists=True):
                        pm.addAttr(shortName="jointRes", longName="Joint_Resolution", defaultValue=25, minValue=1,
                                   at="long", k=True)
                    if not pm.attributeQuery("deformerRes", node=jointList[j], exists=True):
                        pm.addAttr(shortName="deformerRes", longName="Deformer_Resolution", defaultValue=25, minValue=1,
                                   at="long", k=True)
                    if not pm.attributeQuery("dropoff", node=jointList[j], exists=True):
                        pm.addAttr(shortName="dropoff", longName="DropOff", defaultValue=2.0, minValue=0.1,
                                   at="float", k=True)
                    # pm.setAttr(jointList[j].radius, 3)
                else:
                    pm.setAttr("%s.type" % jointList[j], 18)
                    pm.setAttr("%s.otherType" % jointList[j], "Tentacle")



    def createAxisAttributes(self, node):
        axisAttributes=["upAxis", "mirrorAxis", "lookAxis"]
        for att in axisAttributes:
            if not pm.attributeQuery(att, node=node, exists=True):
                pm.addAttr(node, longName=att, dt="string")

        # R_parsingDict = { dt.Vector(1, 0, 0):u'+x',
        #                   dt.Vector(0, 1, 0):u'+y',
        #                   dt.Vector(0, 0, 1):u'+z',
        #                   dt.Vector(-1, 0, 0):u'-x',
        #                   dt.Vector(0, -1, 0):u'-y',
        #                   dt.Vector(0, 0, -1):u'-z'
        #                  }

        # upAxis_asString = R_parsingDict[self.upVector]
        # looAxis_asString = R_parsingDict[self.lookAxis]
        # mirrorAxis_asString = R_parsingDict[self.mirrorAxis]


        # pm.setAttr(node.upAxis, "-%s" %self.upAxis if self.upAxisMult == -1 else "%s" %self.upAxis)
        # pm.setAttr(node.mirrorAxis, "-%s" %self.mirrorAxis if self.mirrorAxisMult == -1 else "%s" %self.mirrorAxis)
        # pm.setAttr(node.lookAxis, "-%s" %self.lookAxis if self.lookAxisMult == -1 else "%s" %self.lookAxis)

        pm.setAttr(node.upAxis, self.upVector_asString)
        pm.setAttr(node.mirrorAxis, self.mirrorVector_asString)
        pm.setAttr(node.lookAxis, self.lookVector_asString)

        if not pm.attributeQuery("useRefOri", node=node, exists=True):
            pm.addAttr(node, longName="useRefOri", niceName="Inherit_Orientation", at="bool", keyable=True)

        # pm.addAttr(node, longName="useRefOri", niceName="Inherit_Orientation", at="bool", keyable=True)
        pm.setAttr(node.useRefOri, True)
        # pm.setAttr(node.lookAxis, "-%s" %self.lookAxis if self.lookAxisMult == -1 else "%s" %self.lookAxis)
        # self.lookAxis











