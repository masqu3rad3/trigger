import pymel.core as pm

import extraProcedures as extra

reload(extra)

import ribbonClass as rc

reload(rc)

import contIcons as icon

reload(icon)

import pymel.core.datatypes as dt



# whichLeg="l_leg"
class Leg():
    def __init__(self):
        # none = None
        self.scaleGrp = None
        self.cont_IK_foot = None
        self.cont_Pole = None
        self.nonScaleGrp = None
        # cont_IK_foot_OFF = None
        self.cont_IK_OFF = None
        self.sockets = []
        # startSocket = None
        # endSocket = None
        self.limbPlug = None
        self.connectsTo = None
        self.scaleConstraints = []
        self.anchors = []
        self.anchorLocations = []
        self.jDef_legRoot = None
        self.upAxis = None

    def createLeg(self, legInits, suffix="", side="L"):
        idCounter = 0
        ## create an unique suffix
        while pm.objExists("scaleGrp_" + suffix):
            suffix = "%s%s" % (suffix, str(idCounter + 1))

        if (len(legInits) < 9):
            pm.error("Some or all Leg Init Bones are missing (or Renamed)")
            return

        if not type(legInits) == dict and not type(legInits) == list:
            pm.error("Init joints must be list or dictionary")
            return

        # reinitialize the dictionary for easy use
        if type(legInits) == dict:
            legRootRef = legInits["LegRoot"]
            hipRef = legInits["Hip"]
            kneeRef = legInits["Knee"]
            footRef = legInits["Foot"]
            ballRef = legInits["Ball"]
            heelPvRef = legInits["HeelPV"]
            toePvRef = legInits["ToePV"]
            bankInRef = legInits["BankIN"]
            bankOutRef = legInits["BankOUT"]
        else:
            legRootRef = legInits[0]
            hipRef = legInits[1]
            kneeRef = legInits[2]
            footRef = legInits[3]
            ballRef = legInits[4]
            heelPvRef = legInits[5]
            toePvRef = legInits[6]
            bankInRef = legInits[7]
            bankOutRef = legInits[8]

        ## get the up axis
        if pm.attributeQuery("upAxis", node=legRootRef, exists=True):
            if pm.getAttr(legRootRef.upAxis) == "x":
                self.upAxis = (1.0,0.0,0.0)
            elif pm.getAttr(legRootRef.upAxis) == "y":
                self.upAxis = (0.0, 1.0, 0.0)
            elif pm.getAttr(legRootRef.upAxis) == "z":
                self.upAxis = (0.0, 0.0, 1.0)
            elif pm.getAttr(legRootRef.upAxis) == "-x":
                self.upAxis = (-1.0, 0.0, 0.0)
            elif pm.getAttr(legRootRef.upAxis) == "-y":
                self.upAxis = (0.0, -1.0, 0.0)
            elif pm.getAttr(legRootRef.upAxis) == "-z":
                self.upAxis = (0.0, 0.0, -1.0)
        else:
            pm.warning("upAxis attribute of the root node does not exist. Using default value (y up)")
            self.upAxis = (0.0, 1.0, 0.0)

        # find the Socket
        self.connectsTo = legRootRef.getParent()

        legRootPos = legRootRef.getTranslation(space="world")
        hipPos = hipRef.getTranslation(space="world")
        kneePos = kneeRef.getTranslation(space="world")
        footPos = footRef.getTranslation(space="world")
        ballPos = ballRef.getTranslation(space="world")
        heelPvPos = heelPvRef.getTranslation(space="world")
        toePvPos = toePvRef.getTranslation(space="world")
        bankInPos = bankInRef.getTranslation(space="world")
        bankOutPos = bankOutRef.getTranslation(space="world")

        initUpperLegDist = extra.getDistance(hipRef, kneeRef)
        initLowerLegDist = extra.getDistance(kneeRef, footRef)
        initBallDist = extra.getDistance(footRef, ballRef)
        initToeDist = extra.getDistance(ballRef, toePvRef)
        initFootLength = extra.getDistance(toePvRef, heelPvRef)
        initFootWidth = extra.getDistance(bankInRef, bankOutRef)

        ########
        ########
        footPlane = pm.spaceLocator(name="testLocator")
        pm.setAttr(footPlane.rotateOrder, 0)
        pm.pointConstraint(heelPvRef, toePvRef, footPlane)
        pm.aimConstraint(toePvRef, footPlane, wuo=footRef, wut="object")
        ########
        ########

        #     _____            _             _ _
        #    / ____|          | |           | | |
        #   | |     ___  _ __ | |_ _ __ ___ | | | ___ _ __ ___
        #   | |    / _ \| '_ \| __| '__/ _ \| | |/ _ \ '__/ __|
        #   | |___| (_) | | | | |_| | | (_) | | |  __/ |  \__ \
        #    \_____\___/|_| |_|\__|_|  \___/|_|_|\___|_|  |___/
        #
        #

        # Thigh Controller

        thighContScale = (initUpperLegDist / 4, initUpperLegDist / 16, initUpperLegDist / 4)
        cont_Thigh = icon.cube("cont_Thigh_" + suffix, thighContScale )
        extra.alignAndAim(cont_Thigh, targetList=[hipRef], aimTargetList=[kneeRef], upObject=legRootRef)
        pm.move(cont_Thigh, (0, -thighContScale[0] * 2, 0), r=True, os=True)
        pm.xform(cont_Thigh, piv=legRootPos, ws=True)
        cont_Thigh_OFF = extra.createUpGrp(cont_Thigh, "OFF")
        cont_Thigh_ORE = extra.createUpGrp(cont_Thigh, "ORE")
        if side == "R":
            pm.setAttr(cont_Thigh_ORE.rotateZ, -180)
        pm.addAttr(shortName="autoTwist", longName="Auto_Twist", defaultValue=1.0, minValue=0.0, maxValue=1.0, at="float",
                   k=True)
        pm.addAttr(shortName="manualTwist", longName="Manual_Twist", defaultValue=0.0, at="float", k=True)

        # IK Foot Controller

        footContScale = (initFootLength*0.75, 1, initFootWidth*0.8)
        self.cont_IK_foot = icon.circle("self.cont_IK_foot_" + suffix, scale=(footContScale), normal=(0, 1, 0))
        extra.alignAndAim(self.cont_IK_foot, targetList=[bankOutRef, bankInRef, toePvRef, heelPvRef], aimTargetList=[toePvRef], upObject=footRef)
        pm.xform(self.cont_IK_foot, piv=footPos, ws=True)

        cont_IK_foot_OFF = extra.createUpGrp(self.cont_IK_foot, "OFF")

        pm.addAttr(self.cont_IK_foot, shortName="polevector", longName="Pole_Vector", defaultValue=0.0, minValue=0.0, maxValue=1.0,
                   at="double", k=True)
        pm.addAttr(self.cont_IK_foot, shortName="sUpLeg", longName="Scale_Upper_Leg", defaultValue=1.0, minValue=0.0, at="double", k=True)
        pm.addAttr(self.cont_IK_foot, shortName="sLowLeg", longName="Scale_Lower_Leg", defaultValue=1.0, minValue=0.0, at="double", k=True)
        pm.addAttr(self.cont_IK_foot, shortName="squash", longName="Squash", defaultValue=0.0, minValue=0.0, maxValue=1.0, at="double", k=True)
        pm.addAttr(self.cont_IK_foot, shortName="stretch", longName="Stretch", defaultValue=100.0, minValue=0.0, maxValue=100.0, at="double",
                   k=True)
        pm.addAttr(self.cont_IK_foot, shortName="bLean", longName="Ball_Lean", defaultValue=0.0, at="double", k=True)
        pm.addAttr(self.cont_IK_foot, shortName="bRoll", longName="Ball_Roll", defaultValue=0.0, at="double", k=True)
        pm.addAttr(self.cont_IK_foot, shortName="bSpin", longName="Ball_Spin", defaultValue=0.0, at="double", k=True)
        pm.addAttr(self.cont_IK_foot, shortName="hRoll", longName="Heel_Roll", defaultValue=0.0, at="double", k=True)
        pm.addAttr(self.cont_IK_foot, shortName="hSpin", longName="Heel_Spin", defaultValue=0.0, at="double", k=True)
        pm.addAttr(self.cont_IK_foot, shortName="tRoll", longName="Toes_Roll", defaultValue=0.0, at="double", k=True)
        pm.addAttr(self.cont_IK_foot, shortName="tSpin", longName="Toes_Spin", defaultValue=0.0, at="double", k=True)
        pm.addAttr(self.cont_IK_foot, shortName="tWiggle", longName="Toes_Wiggle", defaultValue=0.0, at="double", k=True)
        pm.addAttr(self.cont_IK_foot, shortName="bank", longName="Bank", defaultValue=0.0, at="double", k=True)

        ## Pole Vector Controller
        polecontScale = ((((initUpperLegDist + initLowerLegDist) / 2) / 10), (((initUpperLegDist + initLowerLegDist) / 2) / 10), (((initUpperLegDist + initLowerLegDist) / 2) / 10))
        self.cont_Pole = icon.plus("cont_Pole_" + suffix, polecontScale, normal=(0,0,1))
        offsetMagPole = (((initUpperLegDist + initLowerLegDist) / 4))
        offsetVectorPole = extra.getBetweenVector(kneeRef, [hipRef,footRef])
        extra.alignAndAim(self.cont_Pole, targetList = [kneeRef], aimTargetList = [hipRef, footRef], upVector=self.upAxis, translateOff=(offsetVectorPole*offsetMagPole))
        cont_Pole_OFF = extra.createUpGrp(self.cont_Pole, "OFF")

        ## FK Upleg Controller
        scalecontFkUpLeg = (initUpperLegDist / 2, initUpperLegDist /6, initUpperLegDist / 6)
        cont_FK_UpLeg = icon.cube("cont_FK_Upleg_" + suffix, scalecontFkUpLeg)
        extra.alignAndAim(cont_FK_UpLeg, targetList=[hipRef,kneeRef], aimTargetList=[kneeRef], upVector=self.upAxis)

        cont_FK_UpLeg_OFF = extra.createUpGrp(cont_FK_UpLeg, "OFF")
        cont_FK_UpLeg_ORE = extra.createUpGrp(cont_FK_UpLeg, "ORE")

        if side == "R":
            pm.setAttr("%s.r%s" % (cont_FK_UpLeg_ORE, "z"), -180)

        pm.xform(cont_FK_UpLeg, piv=hipPos, ws=True)
        pm.xform(cont_FK_UpLeg_ORE, piv=hipPos, ws=True)
        pm.xform(cont_FK_UpLeg_OFF, piv=hipPos, ws=True)

        ## FK Lowleg Controller
        scalecontFkLowLeg = (initLowerLegDist / 2, initLowerLegDist /6, initLowerLegDist / 6)
        cont_FK_LowLeg = icon.cube("cont_FK_Lowleg_" + suffix, scalecontFkLowLeg)
        extra.alignAndAim(cont_FK_LowLeg, targetList=[kneeRef,footRef], aimTargetList=[footRef], upVector=self.upAxis)

        cont_FK_LowLeg_OFF = extra.createUpGrp(cont_FK_LowLeg, "OFF")
        cont_FK_LowLeg_ORE = extra.createUpGrp(cont_FK_LowLeg, "ORE")

        if side == "R":
            pm.setAttr("%s.r%s" % (cont_FK_LowLeg_ORE, "z"), -180)

        pm.xform(cont_FK_LowLeg, piv=kneePos, ws=True)
        pm.xform(cont_FK_LowLeg_ORE, piv=kneePos, ws=True)
        pm.xform(cont_FK_LowLeg_OFF, piv=kneePos, ws=True)

        ## FK Foot Controller
        scalecontFkFoot = (initBallDist/2, initBallDist/3, initFootWidth/2)
        cont_FK_Foot = icon.cube(name="cont_FK_Foot_" + suffix, scale=scalecontFkFoot)
        extra.alignAndAim(cont_FK_Foot, targetList=[footRef,ballRef], aimTargetList=[ballRef], upVector=self.upAxis)

        cont_FK_Foot_OFF = extra.createUpGrp(cont_FK_Foot, "OFF")
        cont_FK_Foot_ORE = extra.createUpGrp(cont_FK_Foot, "ORE")

        if side == "R":
            pm.setAttr("%s.r%s" % (cont_FK_Foot_ORE, "z"), -180)

        pm.xform(cont_FK_Foot, piv=footPos, ws=True)
        pm.xform(cont_FK_Foot_ORE, piv=footPos, ws=True)
        pm.xform(cont_FK_Foot_OFF, piv=footPos, ws=True)

        ## FK Ball Controller
        scalecontFkBall = (initToeDist/2, initToeDist/3, initFootWidth/2)
        cont_FK_Ball = icon.cube(name="cont_FK_Ball_" + suffix, scale=scalecontFkBall)
        extra.alignAndAim(cont_FK_Ball, targetList=[ballRef,toePvRef], aimTargetList=[toePvRef], upVector=self.upAxis)

        cont_FK_Ball_OFF = extra.createUpGrp(cont_FK_Ball, "OFF")
        cont_FK_Ball_ORE = extra.createUpGrp(cont_FK_Ball, "ORE")

        if side == "R":
            pm.setAttr("%s.r%s" % (cont_FK_Ball_ORE, "z"), -180)

        pm.xform(cont_FK_Ball, piv=ballPos, ws=True)
        pm.xform(cont_FK_Ball_ORE, piv=ballPos, ws=True)
        pm.xform(cont_FK_Ball_OFF, piv=ballPos, ws=True)

        ## FK-IK SWITCH Controller
        iconScale = initLowerLegDist / 4
        cont_FK_IK, fk_ik_rvs = icon.fkikSwitch(("cont_FK_IK_" + suffix), (iconScale, iconScale, iconScale))
        extra.alignAndAim(cont_FK_IK, targetList = [footRef], aimTargetList = [kneeRef], upVector=self.upAxis, rotateOff=(90,90,0))
        # pm.move(cont_FK_IK, (dt.Vector(self.upAxis) *(iconScale*2)), r=True)
        pm.move(cont_FK_IK, (iconScale*2,0,0), r=True, os=True)
        cont_FK_IK_POS = extra.createUpGrp(cont_FK_IK, "POS")

        if side == "R":
            pm.move(cont_FK_IK, (-iconScale * 4, 0, 0), r=True, os=True)

        pm.addAttr(cont_FK_IK, shortName="autoTwist", longName="Auto_Twist", defaultValue=1.0, minValue=0.0, maxValue=1.0,
                   at="float", k=True)
        pm.addAttr(cont_FK_IK, shortName="manualTwist", longName="Manual_Twist", defaultValue=0.0, at="float", k=True)
        pm.addAttr(cont_FK_IK, shortName="tweakControls", longName="Tweak_Controls", defaultValue=0, at="bool")
        pm.setAttr(cont_FK_IK.tweakControls, cb=True)
        pm.addAttr(cont_FK_IK, shortName="fingerControls", longName="Finger_Controls", defaultValue=1, at="bool")
        pm.setAttr(cont_FK_IK.fingerControls, cb=True)

###########################################################################################################################

        ##Groups
        self.scaleGrp = pm.group(name="scaleGrp_" + suffix, em=True)
        extra.alignTo(self.scaleGrp, legRootRef, 0)
        self.nonScaleGrp = pm.group(name="NonScaleGrp_" + suffix, em=True)

        ## Create Limb Plug
        pm.select(d=True)
        self.limbPlug = pm.joint(name="limbPlug_" + suffix, p=legRootPos, radius=3)


        ###Create common Joints
        pm.select(d=True)
        jDef_midLeg = pm.joint(name="jDef_knee_" + suffix, p=kneePos, radius=1.5)
        pm.select(d=True)
        self.jDef_legRoot = pm.joint(name="jDef_legRoot_" + suffix, p=legRootPos, radius=1.5)
        self.sockets.append(self.jDef_legRoot)
        jDef_hip = pm.joint(name="jDef_hip_" + suffix, p=hipPos, radius=1.5)
        pm.joint(self.jDef_legRoot, e=True, zso=True, oj="xyz")
        pm.joint(jDef_hip, e=True, zso=True, oj="xyz")
        pm.parent(self.jDef_legRoot, self.scaleGrp)

        ###########################
        ######### IK LEG ##########
        ###########################

        masterIK = pm.spaceLocator(name="masterIK_" + suffix)
        extra.alignTo(masterIK, footRef)

        pm.select(d=True)
        jIK_orig_Root = pm.joint(name="jIK_orig_Root_" + suffix, p=hipPos, radius=1.5)
        jIK_orig_Knee = pm.joint(name="jIK_orig_Knee_" + suffix, p=kneePos, radius=1.5)
        jIK_orig_End = pm.joint(name="jIK_orig_End_" + suffix, p=footPos, radius=1.5)
        pm.select(d=True)
        jIK_SC_Root = pm.joint(name="jIK_SC_Root_" + suffix, p=hipPos, radius=1)
        jIK_SC_Knee = pm.joint(name="jIK_SC_Knee_" + suffix, p=kneePos, radius=1)
        jIK_SC_End = pm.joint(name="jIK_SC_End_" + suffix, p=footPos, radius=1)
        pm.select(d=True)
        jIK_RP_Root = pm.joint(name="jIK_RP_Root_" + suffix, p=hipPos, radius=0.7)
        jIK_RP_Knee = pm.joint(name="jIK_RP_Knee_" + suffix, p=kneePos, radius=0.7)
        jIK_RP_End = pm.joint(name="jIK_RP_End_" + suffix, p=footPos, radius=0.7)
        pm.select(d=True)
        jIK_Foot = pm.joint(name="jIK_Foot_" + suffix, p=footPos, radius=1.0)
        jIK_Ball = pm.joint(name="jIK_Ball_" + suffix, p=ballPos, radius=1.0)
        jIK_Toe = pm.joint(name="jIK_Toe_" + suffix, p=toePvPos,  ## POSSIBLE PROBLEM
                           radius=1.0)

        pm.joint(jIK_orig_Root, e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(jIK_orig_Knee, e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(jIK_orig_End,  e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(jIK_SC_Root,   e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(jIK_SC_Knee,   e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(jIK_SC_End,    e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(jIK_RP_Root,   e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(jIK_RP_Knee,   e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(jIK_RP_End,    e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(jIK_Foot,      e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(jIK_Ball,      e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(jIK_Toe,       e=True, zso=True, oj="xyz", sao="yup")

        ###Create Foot Pivots and Ball Socket
        pm.select(cl=True)

        Pv_BankIn = pm.group(name="Pv_BankIn_" + suffix, em=True)
        extra.alignTo(Pv_BankIn, bankInRef, 2)
        pm.makeIdentity(Pv_BankIn, a=True, t=False, r=True, s=True)
        pm.setAttr(Pv_BankIn.rotate, pm.getAttr(footPlane.rotate))

        Pv_BankOut = pm.group(name="Pv_BankOut_" + suffix, em=True)
        extra.alignTo(Pv_BankOut, bankOutRef, 2)
        pm.makeIdentity(Pv_BankOut, a=True, t=False, r=True, s=True)
        pm.setAttr(Pv_BankOut.rotate, pm.getAttr(footPlane.rotate))


        Pv_Toe = pm.group(name="Pv_Toe_" + suffix, em=True)
        extra.alignTo(Pv_Toe, toePvRef, 2)
        Pv_Toe_ORE = extra.createUpGrp(Pv_Toe, "ORE")

        Pv_Ball = pm.group(name="Pv_Ball_" + suffix, em=True)
        extra.alignTo(Pv_Ball, ballRef, 2)
        Pv_Ball_ORE = extra.createUpGrp(Pv_Ball, "ORE")

        jSocketBall = pm.joint(name="jBallSocket_" + suffix, radius=3)
        pm.parentConstraint(Pv_Ball, jSocketBall)
        # TODO // SOCKETBALL NEEDS A IK/FK Switch
        self.sockets.append(jSocketBall)


        Pv_Heel = pm.group(name="Pv_Heel_" + suffix, em=True)
        extra.alignTo(Pv_Heel, heelPvRef, 2)
        Pv_Heel_ORE = extra.createUpGrp(Pv_Heel, "ORE")

        Pv_BallSpin = pm.group(name="Pv_BallSpin_" + suffix, em=True)
        extra.alignTo(Pv_BallSpin, ballRef, 2)
        Pv_BallSpin_ORE = extra.createUpGrp(Pv_BallSpin, "ORE")


        Pv_BallRoll = pm.group(name="Pv_BallRoll_" + suffix, em=True)
        extra.alignTo(Pv_BallRoll, ballRef, 2)
        Pv_BallRoll_ORE = extra.createUpGrp(Pv_BallRoll, "ORE")

        Pv_BallLean = pm.group(name="Pv_BallLean_" + suffix, em=True)
        extra.alignTo(Pv_BallLean, ballRef, 2)
        Pv_BallLean_ORE = extra.createUpGrp(Pv_BallLean, "ORE")


        ## Create Start Lock

        startLock = pm.spaceLocator(name="startLock_" + suffix)
        extra.alignTo(startLock, hipRef, 2)
        startLock_Ore = extra.createUpGrp(startLock, "_Ore")
        startLock_Pos = extra.createUpGrp(startLock, "_Pos")
        startLock_Twist = extra.createUpGrp(startLock, "_AutoTwist")

        startLockRot = pm.parentConstraint(jDef_hip, startLock, mo=True)

        pm.parentConstraint(startLock, jIK_SC_Root, mo=True)
        pm.parentConstraint(startLock, jIK_RP_Root, mo=True)

        ###Create IK handles

        ikHandle_SC = pm.ikHandle(sj=jIK_SC_Root, ee=jIK_SC_End, name="ikHandle_SC_" + suffix)
        ikHandle_RP = pm.ikHandle(sj=jIK_RP_Root, ee=jIK_RP_End, name="ikHandle_RP_" + suffix, sol="ikRPsolver")

        pm.poleVectorConstraint(self.cont_Pole, ikHandle_RP[0])
        pm.aimConstraint(jIK_RP_Knee, self.cont_Pole)

        ikHandle_Ball = pm.ikHandle(sj=jIK_Foot, ee=jIK_Ball, name="ikHandle_Ball_" + suffix)
        ikHandle_Toe = pm.ikHandle(sj=jIK_Ball, ee=jIK_Toe, name="ikHandle_Toe_" + suffix)

        ###Create Hierarchy for Foot

        pm.parent(ikHandle_Ball[0], Pv_Ball)
        pm.parent(ikHandle_Toe[0], Pv_Ball)
        pm.parent(masterIK, Pv_BallLean)
        pm.parent(ikHandle_SC[0], masterIK)
        pm.parent(ikHandle_RP[0], masterIK)
        pm.parent(Pv_BallLean_ORE, Pv_BallRoll)
        pm.parent(Pv_Ball_ORE, Pv_Toe)
        pm.parent(Pv_BallRoll_ORE, Pv_Toe)
        pm.parent(Pv_Toe_ORE, Pv_BallSpin)
        pm.parent(Pv_BallSpin_ORE, Pv_Heel)
        pm.parent(Pv_Heel_ORE, Pv_BankOut)
        pm.parent(Pv_BankOut, Pv_BankIn)

        #########################################################

        ### Create and constrain Distance Locators

        legStart = pm.spaceLocator(name="legStart_loc_" + suffix)
        pm.pointConstraint(startLock, legStart, mo=False)

        legEnd = pm.spaceLocator(name="legEnd_loc_" + suffix)
        pm.pointConstraint(masterIK, legEnd, mo=False)

        ### Create Nodes and Connections for Strethchy IK SC

        stretchOffset = pm.createNode("plusMinusAverage", name="stretchOffset_" + suffix)
        distance_SC = pm.createNode("distanceBetween", name="distance_SC_" + suffix)
        IK_stretch_distanceClamp = pm.createNode("clamp", name="IK_stretch_distanceClamp" + suffix)
        IK_stretch_stretchynessClamp = pm.createNode("clamp", name="IK_stretch_stretchynessClamp" + suffix)
        extraScaleMult_SC = pm.createNode("multiplyDivide", name="extraScaleMult_SC" + suffix)
        initialDivide_SC = pm.createNode("multiplyDivide", name="initialDivide_SC_" + suffix)
        initialLengthMultip_SC = pm.createNode("multiplyDivide", name="initialLengthMultip_SC_" + suffix)
        stretchAmount_SC = pm.createNode("multiplyDivide", name="stretchAmount_SC_" + suffix)
        sumOfJLengths_SC = pm.createNode("plusMinusAverage", name="sumOfJLengths_SC_" + suffix)
        stretchCondition_SC = pm.createNode("condition", name="stretchCondition_SC_" + suffix)
        squashyness_SC = pm.createNode("blendColors", name="squashyness_SC_" + suffix)
        stretchyness_SC = pm.createNode("blendColors", name="stretchyness_SC_" + suffix)

        pm.setAttr(IK_stretch_stretchynessClamp + ".maxR", 1)
        pm.setAttr(initialLengthMultip_SC + ".input1X", initUpperLegDist)
        pm.setAttr(initialLengthMultip_SC + ".input1Y", initLowerLegDist)

        pm.setAttr(initialDivide_SC + ".operation", 2)
        pm.setAttr(stretchCondition_SC + ".operation", 2)

        ### Bind Attributes and make constraints

        # Bind Stretch Attributes
        legStart.translate >> distance_SC.point1
        legEnd.translate >> distance_SC.point2
        distance_SC.distance >> IK_stretch_distanceClamp.inputR

        IK_stretch_distanceClamp.outputR >> stretchCondition_SC.firstTerm
        IK_stretch_distanceClamp.outputR >> initialDivide_SC.input1X
        IK_stretch_stretchynessClamp.outputR >> stretchyness_SC.blender

        initialDivide_SC.outputX >> stretchAmount_SC.input2X
        initialDivide_SC.outputX >> stretchAmount_SC.input2Y

        initialLengthMultip_SC.outputX >> extraScaleMult_SC.input1X
        initialLengthMultip_SC.outputY >> extraScaleMult_SC.input1Y
        initialLengthMultip_SC.outputX >> stretchOffset.input1D[0]
        initialLengthMultip_SC.outputY >> stretchOffset.input1D[1]

        extraScaleMult_SC.outputX >> stretchAmount_SC.input1X
        extraScaleMult_SC.outputY >> stretchAmount_SC.input1Y
        extraScaleMult_SC.outputX >> stretchyness_SC.color2R
        extraScaleMult_SC.outputY >> stretchyness_SC.color2G
        extraScaleMult_SC.outputX >> stretchCondition_SC.colorIfFalseR
        extraScaleMult_SC.outputY >> stretchCondition_SC.colorIfFalseG
        extraScaleMult_SC.outputX >> sumOfJLengths_SC.input1D[0]
        extraScaleMult_SC.outputY >> sumOfJLengths_SC.input1D[1]

        stretchAmount_SC.outputX >> squashyness_SC.color1R
        stretchAmount_SC.outputY >> squashyness_SC.color1G
        stretchAmount_SC.outputX >> stretchCondition_SC.colorIfTrueR
        stretchAmount_SC.outputY >> stretchCondition_SC.colorIfTrueG
        sumOfJLengths_SC.output1D >> initialDivide_SC.input2X
        sumOfJLengths_SC.output1D >> stretchCondition_SC.secondTerm
        stretchCondition_SC.outColorR >> squashyness_SC.color2R
        stretchCondition_SC.outColorG >> squashyness_SC.color2G
        squashyness_SC.outputR >> stretchyness_SC.color1R
        squashyness_SC.outputG >> stretchyness_SC.color1G
        stretchyness_SC.outputR >> jIK_SC_Knee.translateX
        stretchyness_SC.outputG >> jIK_SC_End.translateX
        stretchyness_SC.outputR >> jIK_RP_Knee.translateX
        stretchyness_SC.outputG >> jIK_RP_End.translateX

        ###########################################################

        self.cont_IK_foot.rotate >> jIK_RP_End.rotate

        # Stretch Attributes Controller connections

        self.cont_IK_foot.sUpLeg >> extraScaleMult_SC.input2X
        self.cont_IK_foot.sLowLeg >> extraScaleMult_SC.input2Y
        self.cont_IK_foot.squash >> squashyness_SC.blender

        stretchOffset.output1D >> IK_stretch_distanceClamp.maxR
        self.cont_IK_foot.stretch >> IK_stretch_stretchynessClamp.inputR
        self.cont_IK_foot.stretch >> stretchOffset.input1D[2]

        # Bind Foot Attributes to the controller
        self.cont_IK_foot.bLean >> Pv_BallLean.rotateY
        self.cont_IK_foot.bRoll >> Pv_BallRoll.rotateZ
        self.cont_IK_foot.bSpin >> Pv_BallSpin.rotateY
        self.cont_IK_foot.hRoll >> Pv_Heel.rotateX
        self.cont_IK_foot.hSpin >> Pv_Heel.rotateY
        self.cont_IK_foot.tRoll >> Pv_Toe.rotateX
        self.cont_IK_foot.tSpin >> Pv_Toe.rotateY
        self.cont_IK_foot.tWiggle >> Pv_Ball.rotateZ
        # // TODO: Reduction possible
        ## create an upper group for bank in to zero out rotations
        Pv_BankIn_ORE = extra.createUpGrp(Pv_BankIn, "ORE")

        pm.select(Pv_BankOut)
        pm.setDrivenKeyframe(cd=self.cont_IK_foot.bank, at="rotateX", dv=0, v=0)
        pm.setDrivenKeyframe(cd=self.cont_IK_foot.bank, at="rotateX", dv=-90, v=90)
        pm.select(Pv_BankIn)
        pm.setDrivenKeyframe(cd=self.cont_IK_foot.bank, at="rotateX", dv=0, v=0)
        pm.setDrivenKeyframe(cd=self.cont_IK_foot.bank, at="rotateX", dv=90, v=-90)

        IK_parentGRP = pm.group(name="IK_parentGRP_" + suffix, em=True)
        extra.alignTo(IK_parentGRP, footRef, 0)
        pm.parent(Pv_BankIn_ORE, IK_parentGRP)
        pm.parent(jIK_Foot, IK_parentGRP)

        pm.parentConstraint(jIK_SC_End, jIK_Foot)

        pm.parentConstraint(self.cont_IK_foot, IK_parentGRP, mo=True)

        # Create Orig Switch (Pole Vector On/Off)

        blendORE_IK_root = pm.createNode("blendColors", name="blendORE_IK_root_" + suffix)
        jIK_SC_Root.rotate >> blendORE_IK_root.color2
        jIK_RP_Root.rotate >> blendORE_IK_root.color1
        blendORE_IK_root.output >> jIK_orig_Root.rotate
        self.cont_IK_foot.polevector >> blendORE_IK_root.blender

        blendPOS_IK_root = pm.createNode("blendColors", name="blendPOS_IK_root_" + suffix)
        jIK_SC_Root.translate >> blendPOS_IK_root.color2
        jIK_RP_Root.translate >> blendPOS_IK_root.color1
        blendPOS_IK_root.output >> jIK_orig_Root.translate
        self.cont_IK_foot.polevector >> blendPOS_IK_root.blender

        blendORE_IK_knee = pm.createNode("blendColors", name="blendORE_IK_knee_" + suffix)
        jIK_SC_Knee.rotate >> blendORE_IK_knee.color2
        jIK_RP_Knee.rotate >> blendORE_IK_knee.color1
        blendORE_IK_knee.output >> jIK_orig_Knee.rotate
        self.cont_IK_foot.polevector >> blendORE_IK_knee.blender

        blendPOS_IK_knee = pm.createNode("blendColors", name="blendPOS_IK_knee_" + suffix)
        jIK_SC_Knee.translate >> blendPOS_IK_knee.color2
        jIK_RP_Knee.translate >> blendPOS_IK_knee.color1
        blendPOS_IK_knee.output >> jIK_orig_Knee.translate
        self.cont_IK_foot.polevector >> blendPOS_IK_knee.blender

        blendORE_IK_end = pm.createNode("blendColors", name="blendORE_IK_end_" + suffix)
        jIK_SC_End.rotate >> blendORE_IK_end.color2
        jIK_RP_End.rotate >> blendORE_IK_end.color1
        blendORE_IK_end.output >> jIK_orig_End.rotate
        self.cont_IK_foot.polevector >> blendORE_IK_end.blender

        blendPOS_IK_end = pm.createNode("blendColors", name="blendPOS_IK_end_" + suffix)
        jIK_SC_End.translate >> blendPOS_IK_end.color2
        jIK_RP_End.translate >> blendPOS_IK_end.color1
        blendPOS_IK_end.output >> jIK_orig_End.translate
        self.cont_IK_foot.polevector >> blendPOS_IK_end.blender

        poleVector_Rvs = pm.createNode("reverse", name="poleVector_Rvs_" + suffix)
        self.cont_IK_foot.polevector >> poleVector_Rvs.inputX

        self.cont_IK_foot.polevector >> self.cont_Pole.v

        pm.parentConstraint(cont_Thigh, self.jDef_legRoot, mo=True, st=("x", "y", "z"))
        pm.pointConstraint(cont_Thigh, jDef_hip, mo=True)

        ###########################
        ######### FK LEG ##########
        ###########################

        pm.select(d=True)
        jFK_Root = pm.joint(name="jFK_UpLeg_" + suffix, p=hipPos, radius=1.0)
        jFK_Knee = pm.joint(name="jFK_Knee_" + suffix, p=kneePos, radius=1.0)
        jFK_Foot = pm.joint(name="jFK_Foot_" + suffix, p=footPos, radius=1.0)
        jFK_Ball = pm.joint(name="jFK_Ball_" + suffix, p=ballPos, radius=1.0)
        jFK_Toe = pm.joint(name="jFK_Toe_" + suffix, p=toePvPos, radius=1.0)

        pm.joint(jFK_Root,e=True, zso=True, oj="yzx", sao="yup")
        pm.joint(jFK_Knee,e=True, zso=True, oj="yzx", sao="yup")
        pm.joint(jFK_Foot,e=True, zso=True, oj="yzx", sao="yup")
        pm.joint(jFK_Ball,e=True, zso=True, oj="yzx", sao="yup")
        pm.joint(jFK_Toe, e=True, zso=True, oj="yzx", sao="yup")

        cont_FK_UpLeg.scaleX >> jFK_Root.scaleX
        cont_FK_LowLeg.scaleX >> jFK_Knee.scaleX
        cont_FK_Foot.scaleX >> jFK_Foot.scaleX
        cont_FK_Ball.scaleX >> jFK_Ball.scaleX

        ### CReate Constraints and Hierarchy
        pm.orientConstraint(cont_FK_UpLeg, jFK_Root, mo=True)
        pm.pointConstraint(startLock, jFK_Root, mo=False)

        pm.orientConstraint(cont_FK_LowLeg, jFK_Knee, mo=True)
        pm.orientConstraint(cont_FK_Foot, jFK_Foot, mo=False)
        pm.orientConstraint(cont_FK_Ball, jFK_Ball, mo=True)

        pm.parentConstraint(cont_Thigh, cont_FK_UpLeg_OFF, sr=("x", "y", "z"), mo=True)
        pm.parentConstraint(cont_FK_UpLeg, cont_FK_LowLeg_OFF, mo=True)
        pm.parentConstraint(cont_FK_LowLeg, cont_FK_Foot_OFF, mo=True)
        pm.parentConstraint(cont_FK_Foot, cont_FK_Ball_OFF, mo=True)

        ### Create FK IK Icon
        # iconScale = (extra.getDistance(footRef, kneeRef)) / 4
        #
        # cont_FK_IK, fk_ik_rvs = icon.fkikSwitch(("cont_FK_IK_" + suffix), (iconScale, iconScale, iconScale))
        #
        # pm.addAttr(cont_FK_IK, shortName="autoTwist", longName="Auto_Twist", defaultValue=1.0, minValue=0.0, maxValue=1.0,
        #            at="float", k=True)
        # pm.addAttr(cont_FK_IK, shortName="manualTwist", longName="Manual_Twist", defaultValue=0.0, at="float", k=True)
        # pm.addAttr(cont_FK_IK, shortName="tweakControls", longName="Tweak_Controls", defaultValue=0, at="bool")
        # pm.setAttr(cont_FK_IK.tweakControls, cb=True)
        # pm.addAttr(cont_FK_IK, shortName="fingerControls", longName="Finger_Controls", defaultValue=0, at="bool")
        # pm.setAttr(cont_FK_IK.fingerControls, cb=True)

        fk_ik_rvs.outputX >> cont_FK_UpLeg_ORE.visibility
        fk_ik_rvs.outputX >> cont_FK_LowLeg_ORE.visibility
        fk_ik_rvs.outputX >> cont_FK_Foot_ORE.visibility
        fk_ik_rvs.outputX >> cont_FK_Ball_ORE.visibility
        cont_FK_IK.fk_ik >> self.cont_IK_foot.visibility

        # extra.alignAndAim(cont_FK_IK, targetList=[footRef], aimTargetList=[kneeRef], upVector=self.upAxis, rotateOff=(90,90,0))
        #
        # if side == "R":
        #     pm.move(cont_FK_IK, (-(iconScale * 2), 0, 0), r=True, os=True)
        # else:
        #     pm.move(cont_FK_IK, (iconScale * 2, 0, 0), r=True, os=True)
        #
        # cont_FK_IK_POS = extra.createUpGrp(cont_FK_IK, "_POS")
        pm.parent(cont_FK_IK_POS, self.scaleGrp)

        ### Create MidLock controller

        midcontScale = extra.getDistance(footRef, kneeRef) / 3
        cont_midLock = icon.star("cont_mid_" + suffix, (midcontScale, midcontScale, midcontScale), normal=(0, 1, 0))

        cont_midLock_POS = extra.createUpGrp(cont_midLock, "POS")
        cont_midLock_AVE = extra.createUpGrp(cont_midLock, "AVE")
        extra.alignTo(cont_midLock_POS, kneeRef, 0)

        midLock_paConWeight = pm.parentConstraint(jIK_orig_Root, jFK_Root, cont_midLock_POS, mo=True)
        cont_FK_IK.fk_ik >> (midLock_paConWeight + "." + jIK_orig_Root + "W0")
        fk_ik_rvs.outputX >> (midLock_paConWeight + "." + jFK_Root + "W1")

        midLock_poConWeight = pm.pointConstraint(jIK_orig_Knee, jFK_Knee, cont_midLock_AVE, mo=False)
        cont_FK_IK.fk_ik >> (midLock_poConWeight + "." + jIK_orig_Knee + "W0")
        fk_ik_rvs.outputX >> (midLock_poConWeight + "." + jFK_Knee + "W1")

        midLock_xBln = pm.createNode("multiplyDivide", name="midLock_xBln" + suffix)

        midLock_rotXsw = pm.createNode("blendTwoAttr", name="midLock_rotXsw" + suffix)
        jIK_orig_Knee.rotateZ >> midLock_rotXsw.input[0]
        jFK_Knee.rotateZ >> midLock_rotXsw.input[1]
        fk_ik_rvs.outputX >> midLock_rotXsw.attributesBlender

        midLock_rotXsw.output >> midLock_xBln.input1Z

        pm.setAttr(midLock_xBln.input2Z, 0.5)
        midLock_xBln.outputZ >> cont_midLock_AVE.rotateX

        ### Create Midlock

        midLock = pm.spaceLocator(name="midLock_" + suffix)
        pm.parentConstraint(midLock, jDef_midLeg)
        # pm.scaleConstraint(midLock, jDef_midLeg)
        extra.alignTo(midLock, cont_midLock, 0)

        pm.parentConstraint(cont_midLock, midLock, mo=False)

        ### Create End Lock
        endLock = pm.spaceLocator(name="endLock_" + suffix)
        extra.alignTo(endLock, footRef, 2)
        endLock_Ore = extra.createUpGrp(endLock, "_Ore")
        endLock_Pos = extra.createUpGrp(endLock, "_Pos")
        endLock_Twist = extra.createUpGrp(endLock, "_Twist")
        endLockWeight = pm.pointConstraint(jIK_orig_End, jFK_Foot, endLock_Pos, mo=False)
        cont_FK_IK.fk_ik >> (endLockWeight + "." + jIK_orig_End + "W0")
        fk_ik_rvs.outputX >> (endLockWeight + "." + jFK_Foot + "W1")

        pm.parentConstraint(endLock, cont_FK_IK_POS, mo=True)
        pm.parent(endLock_Ore, self.scaleGrp)

        endLockRot = pm.parentConstraint(IK_parentGRP, jFK_Foot, endLock, st=("x", "y", "z"), mo=True)
        # pm.setAttr(endLockRot.interpType, 0)
        cont_FK_IK.fk_ik >> (endLockRot + "." + IK_parentGRP + "W0")
        fk_ik_rvs.outputX >> (endLockRot + "." + jFK_Foot + "W1")

        ###################################
        #### CREATE DEFORMATION JOINTS ####
        ###################################

        # UPPERLEG RIBBON

        ribbonUpperLeg = rc.Ribbon()
        ribbonUpperLeg.createRibbon(hipRef, kneeRef, "up_" + suffix, -90)

        ribbonStart_paCon_upperLeg_Start = pm.parentConstraint(startLock, ribbonUpperLeg.startConnection, mo=True)
        ribbonStart_paCon_upperLeg_End = pm.parentConstraint(midLock, ribbonUpperLeg.endConnection, mo=True)

        pm.scaleConstraint(self.scaleGrp, ribbonUpperLeg.scaleGrp)

        # AUTO AND MANUAL TWIST

        # auto
        autoTwistThigh = pm.createNode("multiplyDivide", name="autoTwistThigh_" + suffix)
        cont_Thigh.autoTwist >> autoTwistThigh.input2X
        ribbonStart_paCon_upperLeg_Start.constraintRotate >> autoTwistThigh.input1

        ###!!! The parent constrain override should be disconnected like this
        pm.disconnectAttr(ribbonStart_paCon_upperLeg_Start.constraintRotateX, ribbonUpperLeg.startConnection.rotateX)

        # manual
        AddManualTwistThigh = pm.createNode("plusMinusAverage", name=("AddManualTwist_UpperLeg_" + suffix))
        autoTwistThigh.output >> AddManualTwistThigh.input3D[0]
        cont_Thigh.manualTwist >> AddManualTwistThigh.input3D[1].input3Dx

        # connect to the joint
        AddManualTwistThigh.output3D >> ribbonUpperLeg.startConnection.rotate

        # LOWERLEG RIBBON

        ribbonLowerLeg = rc.Ribbon()
        ribbonLowerLeg.createRibbon(kneeRef, footRef, "low_" + suffix, 90)

        ribbonStart_paCon_lowerLeg_Start = pm.parentConstraint(midLock, ribbonLowerLeg.startConnection, mo=True)
        ribbonStart_paCon_lowerLeg_End = pm.parentConstraint(endLock, ribbonLowerLeg.endConnection, mo=True)

        pm.scaleConstraint(self.scaleGrp, ribbonLowerLeg.scaleGrp)

        # AUTO AND MANUAL TWIST

        # auto
        autoTwistAnkle = pm.createNode("multiplyDivide", name="autoTwistAnkle_" + suffix)
        cont_FK_IK.autoTwist >> autoTwistAnkle.input2X
        ribbonStart_paCon_lowerLeg_End.constraintRotate >> autoTwistAnkle.input1

        ###!!! The parent constrain override should be disconnected like this
        pm.disconnectAttr(ribbonStart_paCon_lowerLeg_End.constraintRotateX, ribbonLowerLeg.endConnection.rotateX)

        # manual
        AddManualTwistAnkle = pm.createNode("plusMinusAverage", name=("AddManualTwist_LowerLeg_" + suffix))
        autoTwistAnkle.output >> AddManualTwistAnkle.input3D[0]
        cont_FK_IK.manualTwist >> AddManualTwistAnkle.input3D[1].input3Dx

        # connect to the joint
        AddManualTwistAnkle.output3D >> ribbonLowerLeg.endConnection.rotate

        # Foot Joint

        pm.select(d=True)
        jDef_Foot = pm.joint(name="jDef_Foot_" + suffix, p=footPos, radius=1.0)
        jDef_Ball = pm.joint(name="jDef_Ball_" + suffix, p=ballPos, radius=1.0)

        jDef_Toe = pm.joint(name="jDef_Toe_" + suffix, p=toePvPos, radius=1.0)  ## POSSIBLE PROBLEM

        foot_paCon = pm.parentConstraint(jIK_Foot, jFK_Foot, jDef_Foot, mo=True)
        ball_paCon = pm.parentConstraint(jIK_Ball, jFK_Ball, jDef_Ball, mo=True)
        toe_paCon = pm.parentConstraint(jIK_Toe, jFK_Toe, jDef_Toe, mo=True)

        cont_FK_IK.fk_ik >> (foot_paCon + "." + jIK_Foot + "W0")
        fk_ik_rvs.outputX >> (foot_paCon + "." + jFK_Foot + "W1")

        cont_FK_IK.fk_ik >> (ball_paCon + "." + jIK_Ball + "W0")
        fk_ik_rvs.outputX >> (ball_paCon + "." + jFK_Ball + "W1")

        cont_FK_IK.fk_ik >> (toe_paCon + "." + jIK_Toe + "W0")
        fk_ik_rvs.outputX >> (toe_paCon + "." + jFK_Toe + "W1")

        # # GOOD PARENTING

        pm.parentConstraint(self.limbPlug, self.scaleGrp, mo=True)

        # Create Master Root and Scale and nonScale Group

        pm.parent(jIK_SC_Root, startLock)
        pm.parent(jIK_RP_Root, startLock)
        pm.parent(jIK_orig_Root, startLock)
        pm.parent(jFK_Root, startLock)

        pm.parent(startLock_Ore, self.scaleGrp)
        pm.parent(legStart, self.scaleGrp)
        pm.parent(legEnd, self.scaleGrp)
        pm.parent(IK_parentGRP, self.scaleGrp)
        pm.parent(cont_Thigh_OFF, self.scaleGrp)
        pm.parent(cont_FK_UpLeg_OFF, self.scaleGrp)
        pm.parent(cont_FK_LowLeg_OFF, self.scaleGrp)
        pm.parent(cont_FK_Foot_OFF, self.scaleGrp)
        pm.parent(cont_FK_Ball_OFF, self.scaleGrp)
        pm.parent(midLock, self.scaleGrp)
        pm.parent(cont_midLock_POS, self.scaleGrp)
        pm.parent(cont_Pole_OFF, self.scaleGrp)
        pm.parent(jDef_midLeg, self.scaleGrp)

        pm.parent(ribbonUpperLeg.scaleGrp, self.nonScaleGrp)
        pm.parent(ribbonUpperLeg.nonScaleGrp, self.nonScaleGrp)

        pm.parent(ribbonLowerLeg.scaleGrp, self.nonScaleGrp)
        pm.parent(ribbonLowerLeg.nonScaleGrp, self.nonScaleGrp)

        pm.parent(jDef_Foot, self.scaleGrp)

        ## CONNECT RIG VISIBILITIES

        # Tweak Controls

        tweakControls = (ribbonUpperLeg.middleCont, ribbonLowerLeg.middleCont, cont_midLock)
        for i in tweakControls:
            cont_FK_IK.tweakControls >> i.v

        pm.addAttr(self.scaleGrp, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True)
        pm.addAttr(self.scaleGrp, at="bool", ln="Joints_Visibility", sn="jointVis", defaultValue=True)
        pm.addAttr(self.scaleGrp, at="bool", ln="Rig_Visibility", sn="rigVis", defaultValue=False)
        # make the created attributes visible in the channelbox
        pm.setAttr(self.scaleGrp.contVis, cb=True)
        pm.setAttr(self.scaleGrp.jointVis, cb=True)
        pm.setAttr(self.scaleGrp.rigVis, cb=True)

        nodesContVis = [cont_Pole_OFF, cont_Thigh_OFF, cont_IK_foot_OFF, cont_FK_Foot_OFF, cont_midLock_POS, cont_FK_IK_POS,
                        cont_FK_Ball_OFF, cont_FK_LowLeg_OFF, cont_FK_UpLeg_OFF, ribbonUpperLeg.scaleGrp, ribbonLowerLeg.scaleGrp]
        nodesJointVis = [jDef_midLeg, jDef_Ball, jDef_Foot, self.jDef_legRoot, jDef_Toe, jDef_hip]
        nodesJointVisLists = [ribbonUpperLeg.deformerJoints, ribbonLowerLeg.deformerJoints, nodesJointVis]
        nodesRigVis = [endLock_Ore, startLock_Ore, legStart, legEnd, IK_parentGRP, midLock]

        # Cont visibilities
        for i in nodesContVis:
            self.scaleGrp.contVis >> i.v

        # global joint visibilities
        for lst in nodesJointVisLists:
            for j in lst:
                self.scaleGrp.jointVis >> j.v

        # Rig Visibilities
        for i in nodesRigVis:
            self.scaleGrp.rigVis >> i.v
        for i in ribbonLowerLeg.toHide:
            self.scaleGrp.rigVis >> i.v
        for i in ribbonUpperLeg.toHide:
            self.scaleGrp.rigVis >> i.v

        # pm.setAttr(cont_FK_IK.rigVis, 0)

        # # FOOL PROOFING

        extra.lockAndHide(cont_Thigh, ["sx", "sy", "sz", "v"])
        extra.lockAndHide(self.cont_IK_foot, ["sx", "sy", "sz", "v"])
        extra.lockAndHide(self.cont_Pole, ["rx", "ry", "rz", "sx", "sy", "sz", "v"])
        extra.lockAndHide(cont_FK_IK, ["sx", "sy", "sz", "v"])
        extra.lockAndHide(cont_FK_UpLeg, ["tx", "ty", "tz", "sy", "sz", "v"])
        extra.lockAndHide(cont_FK_LowLeg, ["tx", "ty", "tz", "sy", "sz", "v"])
        extra.lockAndHide(cont_FK_Foot, ["tx", "ty", "tz", "sy", "sz", "v"])
        extra.lockAndHide(cont_FK_Ball, ["tx", "ty", "tz", "sy", "sz", "v"])

        # # COLOR CODING

        extra.colorize(cont_Thigh, side)
        extra.colorize(self.cont_IK_foot, side)
        extra.colorize(cont_FK_IK, side)
        extra.colorize(cont_FK_UpLeg, side)
        extra.colorize(cont_FK_LowLeg, side)
        extra.colorize(cont_FK_Foot, side)
        extra.colorize(cont_FK_Ball, side)

        extra.colorize(cont_midLock, side+"MIN")
        extra.colorize(ribbonUpperLeg.middleCont, side+"MIN")
        extra.colorize(ribbonLowerLeg.middleCont, side+"MIN")

        # # GOOD RIDDANCE
        pm.delete(footPlane)

        self.scaleConstraints = [self.scaleGrp, cont_IK_foot_OFF]
        self.anchors = [(self.cont_IK_foot, "parent", 1, None),(self.cont_Pole, "parent", 1, None)]
        self.cont_IK_OFF = cont_IK_foot_OFF
