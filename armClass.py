import pymel.core as pm
import sys

import extraProcedures as extra

reload(extra)
import ribbonClass as rc

reload(rc)
import contIcons as icon

reload(icon)
import multiFingersClass as mFingers
reload(mFingers)

import pymel.core.datatypes as dt
###########################
######### IK ARM ##########
###########################
class Arm():
    def __init__(self):
        self.sockets = []
        # startSocket = None
        # endSocket = None
        self.scaleGrp = None
        self.nonScaleGrp = None
        self.cont_IK_hand = None
        # cont_IK_hand_OFF = None
        self.cont_IK_OFF = None
        self.rootSocket = None
        self.cont_Pole = None
        self.nodesContVis = None
        self.limbPlug = None
        self.scaleConstraints = []
        self.anchors = []
        self.anchorLocations = []
        self.jDef_Collar = None
        self.upAxis = None
        ## get the up axis
    ## This is a joint node and should be parented to another joint.
    def createArm(self, armInits, suffix="", side="L"):
        idCounter=0
        ## create an unique suffix
        while pm.objExists("scaleGrp_" + suffix):
            suffix = "%s%s" % (suffix, str(idCounter + 1))

        if len(armInits)<4:
            pm.error("Missing Joints for Arm Setup")
            return

        if not type(armInits) == dict and not type(armInits) == list:
            pm.error("Init joints must be list or dictionary")
            return

        if type(armInits) == dict:
        # reinitialize the dictionary for easy use
            collarRef = armInits["Collar"]
            shoulderRef = armInits["Shoulder"]
            elbowRef = armInits["Elbow"]
            handRef = armInits["Hand"]
        else:
            collarRef = armInits[0]
            shoulderRef = armInits[1]
            elbowRef = armInits[2]
            handRef = armInits[3]


        ## get the up axis
        axisDict={"x":(1.0,0.0,0.0),"y":(0.0,1.0,0.0),"z":(0.0,0.0,1.0),"-x":(-1.0,0.0,0.0),"-y":(0.0,-1.0,0.0),"-z":(0.0,0.0,-1.0)}

        if pm.attributeQuery("upAxis", node=collarRef, exists=True):
            try:
                self.upAxis=axisDict[pm.getAttr(collarRef.upAxis).lower()]
            except:
                pm.warning("upAxis attribute is not valid, proceeding with default value (y up)")
                self.upAxis = (0.0, 1.0, 0.0)
        else:
            pm.warning("upAxis attribute of the root node does not exist. Using default value (y up)")
            self.upAxis = (0.0, 1.0, 0.0)
        ## get the mirror axis
        if pm.attributeQuery("mirrorAxis", node=collarRef, exists=True):
            try:
                self.mirrorAxis=axisDict[pm.getAttr(collarRef.mirrorAxis).lower()]
            except:
                pm.warning("mirrorAxis attribute is not valid, proceeding with default value (scene x)")
                self.mirrorAxis= (1.0, 0.0, 0.0)
        else:
            pm.warning("mirrorAxis attribute of the root node does not exist. Using default value (scene x)")
            self.mirrorAxis = (1.0, 0.0, 0.0)

        # mirrorRotateAxis = "xyz".replace(upAxisStr, "")
        # mirrorRotateAxis =  mirrorRotateAxis.replace(mirrorAxisStr, "")

        # print "self.upAxis", self.upAxis


        ##Groups
        self.scaleGrp = pm.group(name="scaleGrp_" + suffix, em=True)
        extra.alignTo(self.scaleGrp, collarRef, 0)
        self.nonScaleGrp = pm.group(name="NonScaleGrp_" + suffix, em=True)

        masterRoot = pm.group(em=True, name="masterRoot_" + suffix)
        extra.alignTo(masterRoot, collarRef, 0)
        pm.makeIdentity(a=True)

        masterIK = pm.spaceLocator(name="masterIK_" + suffix)
        extra.alignTo(masterIK, handRef, 0)

        collarPos = collarRef.getTranslation(space="world")
        shoulderPos = shoulderRef.getTranslation(space="world")
        elbowPos = elbowRef.getTranslation(space="world")
        handPos = handRef.getTranslation(space="world")
        initShoulderDist = extra.getDistance(collarRef, shoulderRef)
        initUpperArmDist = extra.getDistance(shoulderRef, elbowRef)
        initLowerArmDist = extra.getDistance(elbowRef, handRef)

        #     _____            _             _ _
        #    / ____|          | |           | | |
        #   | |     ___  _ __ | |_ _ __ ___ | | | ___ _ __ ___
        #   | |    / _ \| '_ \| __| '__/ _ \| | |/ _ \ '__/ __|
        #   | |___| (_) | | | | |_| | | (_) | | |  __/ |  \__ \
        #    \_____\___/|_| |_|\__|_|  \___/|_|_|\___|_|  |___/
        #
        #

        ## shoulder controller
        shouldercontScale = (initShoulderDist / 2, initShoulderDist / 2, initShoulderDist / 2)
        cont_Shoulder = icon.shoulder("cont_Shoulder_" + suffix, shouldercontScale)
        extra.alignAndAim(cont_Shoulder, targetList = [collarRef], aimTargetList=[shoulderRef], upVector=self.upAxis)
        cont_Shoulder_OFF = extra.createUpGrp(cont_Shoulder, "OFF")
        cont_Shoulder_ORE = extra.createUpGrp(cont_Shoulder, "ORE")
        cont_Shoulder_POS = extra.createUpGrp(cont_Shoulder, "POS")

        if side == "R":
            pm.setAttr("{0}.s{1}".format(cont_Shoulder_POS, "z"), -1)

        pm.addAttr(cont_Shoulder, shortName="autoTwist", longName="Auto_Twist", defaultValue=1.0, minValue=0.0, maxValue=1.0, at="float",
                   k=True)
        pm.addAttr(cont_Shoulder, shortName="manualTwist", longName="Manual_Twist", defaultValue=0.0, at="float", k=True)

        ## IK hand controller
        IKcontScale = (initLowerArmDist / 3, initLowerArmDist / 3, initLowerArmDist / 3)
        self.cont_IK_hand = icon.circle("cont_IK_hand_" + suffix, IKcontScale, normal=(1, 0, 0))
        extra.alignAndAim(self.cont_IK_hand, targetList = [handRef], aimTargetList = [elbowRef], upVector=self.upAxis, rotateOff=(0, -180, 0))
        cont_IK_hand_OFF = extra.createUpGrp(self.cont_IK_hand, "OFF")
        cont_IK_hand_ORE = extra.createUpGrp(self.cont_IK_hand, "ORE")
        cont_IK_hand_POS = extra.createUpGrp(self.cont_IK_hand, "POS")

        pm.addAttr(shortName="polevector", longName="Pole_Vector", defaultValue=0.0, minValue=0.0, maxValue=1.0,
                   at="double", k=True)
        pm.addAttr(shortName="sUpArm", longName="Scale_Upper_Arm", defaultValue=1.0, minValue=0.0, at="double", k=True)
        pm.addAttr(shortName="sLowArm", longName="Scale_Lower_Arm", defaultValue=1.0, minValue=0.0, at="double", k=True)
        pm.addAttr(shortName="squash", longName="Squash", defaultValue=0.0, minValue=0.0, maxValue=1.0, at="double", k=True)
        pm.addAttr(shortName="stretch", longName="Stretch", defaultValue=100.0, minValue=0.0, maxValue=100.0, at="double",
                   k=True)

        ## Pole Vector Controller
        polecontScale = ((((initUpperArmDist + initLowerArmDist) / 2) / 10), (((initUpperArmDist + initLowerArmDist) / 2) / 10), (((initUpperArmDist + initLowerArmDist) / 2) / 10))
        self.cont_Pole = icon.plus("cont_Pole_" + suffix, polecontScale, normal=(0,0,1))
        offsetMagPole = (((initUpperArmDist + initLowerArmDist) / 4))
        offsetVectorPole = extra.getBetweenVector(elbowRef, [shoulderRef,handRef])
        extra.alignAndAim(self.cont_Pole, targetList = [elbowRef], aimTargetList = [shoulderRef, handRef], upVector=self.upAxis, translateOff=(offsetVectorPole*offsetMagPole))
        cont_Pole_OFF = extra.createUpGrp(self.cont_Pole, "OFF")

        ## FK UP Arm Controller

        FKupArmScale = (initUpperArmDist / 2, initUpperArmDist / 8, initUpperArmDist / 8)

        cont_FK_UpArm = icon.cube("cont_FK_UpArm_" + suffix, FKupArmScale)
        extra.alignAndAim(cont_FK_UpArm, targetList= [shoulderRef, elbowRef], aimTargetList=[elbowRef], upVector=self.upAxis)
        cont_FK_UpArm_OFF = extra.createUpGrp(cont_FK_UpArm, "OFF")
        cont_FK_UpArm_ORE = extra.createUpGrp(cont_FK_UpArm, "ORE")
        if side == "R":
            pm.setAttr("%s.r%s" % (cont_FK_UpArm_ORE, "z"), -180)

        pm.xform(cont_FK_UpArm, piv=shoulderPos, ws=True)
        pm.xform(cont_FK_UpArm_ORE, piv=shoulderPos, ws=True)
        pm.xform(cont_FK_UpArm_OFF, piv=shoulderPos, ws=True)

        ## FK LOW Arm Controller
        FKlowArmScale = (initLowerArmDist / 2, initLowerArmDist / 8, initLowerArmDist / 8)
        cont_FK_LowArm = icon.cube("cont_FK_LowArm_" + suffix, FKlowArmScale)
        # pm.xform(cont_FK_LowArm, piv=(-(initLowerArmDist / 2), 0, 0), ws=True)
        extra.alignAndAim(cont_FK_LowArm, targetList= [elbowRef, handRef], aimTargetList=[handRef], upVector=self.upAxis)
        cont_FK_LowArm_OFF = extra.createUpGrp(cont_FK_LowArm, "OFF")
        cont_FK_LowArm_ORE = extra.createUpGrp(cont_FK_LowArm, "ORE")
        if side == "R":
            pm.setAttr("%s.r%s" % (cont_FK_LowArm_ORE, "z"), -180)

        pm.xform(cont_FK_LowArm, piv=elbowPos, ws=True)
        pm.xform(cont_FK_LowArm_ORE, piv=elbowPos, ws=True)
        pm.xform(cont_FK_LowArm_OFF, piv=elbowPos, ws=True)

        ## FK HAND Controller
        FKcontScale = (initLowerArmDist / 5, initLowerArmDist / 5, initLowerArmDist / 5)
        cont_FK_Hand = icon.cube("cont_FK_Hand_" + suffix, FKcontScale)
        extra.alignAndAim(cont_FK_Hand, targetList=[handRef], aimTargetList=[elbowRef], upVector=self.upAxis, rotateOff=(0, -180, 0))
        cont_FK_Hand_OFF = extra.createUpGrp(cont_FK_Hand, "OFF")
        cont_FK_Hand_POS = extra.createUpGrp(cont_FK_Hand, "POS")
        cont_FK_Hand_ORE = extra.createUpGrp(cont_FK_Hand, "ORE")

        if side == "R":
            pm.setAttr("%s.r%s" % (cont_FK_Hand_ORE, "z"), -180)

        # FK-IK SWITCH Controller
        iconScale = initUpperArmDist / 4
        cont_FK_IK, fk_ik_rvs = icon.fkikSwitch(("cont_FK_IK_" + suffix), (iconScale, iconScale, iconScale))
        extra.alignAndAim(cont_FK_IK, targetList = [handRef], aimTargetList = [elbowRef], upVector=self.upAxis, rotateOff=(0,180,0))
        pm.move(cont_FK_IK, (dt.Vector(self.upAxis) *(iconScale*2)), r=True)
        cont_FK_IK_POS = extra.createUpGrp(cont_FK_IK, "POS")

        if side == "R":
            pm.setAttr("{0}.s{1}".format(cont_FK_IK, "x"), -1)

        pm.addAttr(cont_FK_IK, shortName="autoTwist", longName="Auto_Twist", defaultValue=1.0, minValue=0.0, maxValue=1.0,
                   at="float", k=True)
        pm.addAttr(cont_FK_IK, shortName="manualTwist", longName="Manual_Twist", defaultValue=0.0, at="float", k=True)
        pm.addAttr(cont_FK_IK, shortName="tweakControls", longName="Tweak_Controls", defaultValue=0, at="bool")
        pm.setAttr(cont_FK_IK.tweakControls, cb=True)
        pm.addAttr(cont_FK_IK, shortName="fingerControls", longName="Finger_Controls", defaultValue=1, at="bool")
        pm.setAttr(cont_FK_IK.fingerControls, cb=True)



        # Create Limb Plug
        pm.select(d=True)
        self.limbPlug = pm.joint(name="jPlug_" + suffix, p=collarPos, radius=3)

        # Shoulder Joints
        pm.select(d=True)
        self.jDef_Collar = pm.joint(name="jDef_Collar_" + suffix, p=collarPos, radius=1.5)
        self.sockets.append(self.jDef_Collar)
        j_CollarEnd = pm.joint(name="j_CollarEnd_" + suffix, p=shoulderPos, radius=1.5)

        pm.select(d=True)
        jDef_elbow = pm.joint(name="jDef_elbow_" + suffix, p=elbowPos, radius=1.5)

        pm.select(d=True)
        jIK_orig_Up = pm.joint(name="jIK_orig_Up_" + suffix, p=shoulderPos, radius=1.5)
        jIK_orig_Low = pm.joint(name="jIK_orig_Low_" + suffix, p=elbowPos, radius=1.5)
        jIK_orig_LowEnd = pm.joint(name="jIK_orig_LowEnd_" + suffix, p=handPos, radius=1.5)

        pm.select(d=True)
        jIK_SC_Up = pm.joint(name="jIK_SC_Up_" + suffix, p=shoulderPos, radius=1)
        jIK_SC_Low = pm.joint(name="jIK_SC_Low_" + suffix, p=elbowPos, radius=1)
        jIK_SC_LowEnd = pm.joint(name="jIK_SC_LowEnd_" + suffix, p=handPos, radius=1)

        pm.select(d=True)
        jIK_RP_Up = pm.joint(name="jIK_RP_Up_" + suffix, p=shoulderPos, radius=0.7)
        jIK_RP_Low = pm.joint(name="jIK_RP_Low_" + suffix, p=elbowPos, radius=0.7)
        jIK_RP_LowEnd = pm.joint(name="jIK_RP_LowEnd_" + suffix, p=handPos, radius=0.7)

        pm.select(d=True)

        pm.joint(self.jDef_Collar, e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(j_CollarEnd, e=True, zso=True, oj="xyz", sao="yup")

        pm.joint(jIK_orig_Up, e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(jIK_orig_Low, e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(jIK_orig_LowEnd, e=True, zso=True, oj="xyz", sao="yup")

        pm.joint(jIK_SC_Up, e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(jIK_SC_Low, e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(jIK_SC_LowEnd, e=True, zso=True, oj="xyz", sao="yup")

        pm.joint(jIK_RP_Up, e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(jIK_RP_Low, e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(jIK_RP_LowEnd, e=True, zso=True, oj="xyz", sao="yup")

        ###Create Start Lock

        startLock = pm.spaceLocator(name="startLock_" + suffix)
        extra.alignTo(startLock, shoulderRef, 2)
        startLock_Ore = extra.createUpGrp(startLock, "Ore")
        startLock_Pos = extra.createUpGrp(startLock, "Pos")
        startLock_Twist = extra.createUpGrp(startLock, "AutoTwist")

        startLockWeight = pm.parentConstraint(j_CollarEnd, startLock, sr=("y", "z"), mo=True)

        # pm.setAttr(startLockWeight.interpType, 0)

        pm.parentConstraint(startLock, jIK_SC_Up, mo=True)
        pm.parentConstraint(startLock, jIK_RP_Up, mo=True)

        ###Create IK handles

        ikHandle_SC = pm.ikHandle(sj=jIK_SC_Up, ee=jIK_SC_LowEnd, name="ikHandle_SC_" + suffix)
        ikHandle_RP = pm.ikHandle(sj=jIK_RP_Up, ee=jIK_RP_LowEnd, name="ikHandle_RP_" + suffix, sol="ikRPsolver")


        pm.poleVectorConstraint(self.cont_Pole, ikHandle_RP[0])
        pm.aimConstraint(jIK_RP_Low, self.cont_Pole, u=self.upAxis, wut="vector")

        ### Create and constrain Distance Locators

        armStart = pm.spaceLocator(name="armStart_" + suffix)
        pm.pointConstraint(startLock, armStart, mo=False)

        armEnd = pm.spaceLocator(name="armEnd_" + suffix)
        pm.pointConstraint(masterIK, armEnd, mo=False)

        ### Create Nodes and Connections for Strethchy IK SC

        stretchOffset = pm.createNode("plusMinusAverage", name="stretchOffset_" + suffix)
        distance_SC = pm.createNode("distanceBetween", name="distance_SC_" + suffix)
        IK_stretch_distanceClamp = pm.createNode("clamp", name="IK_stretch_distanceClamp_" + suffix)
        IK_stretch_stretchynessClamp = pm.createNode("clamp", name="IK_stretch_stretchynessClamp_" + suffix)
        extraScaleMult_SC = pm.createNode("multiplyDivide", name="extraScaleMult_SC_" + suffix)
        initialDivide_SC = pm.createNode("multiplyDivide", name="initialDivide_SC_" + suffix)
        initialLengthMultip_SC = pm.createNode("multiplyDivide", name="initialLengthMultip_SC_" + suffix)
        stretchAmount_SC = pm.createNode("multiplyDivide", name="stretchAmount_SC_" + suffix)
        sumOfJLengths_SC = pm.createNode("plusMinusAverage", name="sumOfJLengths_SC_" + suffix)
        stretchCondition_SC = pm.createNode("condition", name="stretchCondition_SC_" + suffix)
        squashyness_SC = pm.createNode("blendColors", name="squashyness_SC_" + suffix)
        stretchyness_SC = pm.createNode("blendColors", name="stretchyness_SC_" + suffix)

        pm.setAttr(IK_stretch_stretchynessClamp + ".maxR", 1)
        pm.setAttr(initialLengthMultip_SC + ".input1X", initUpperArmDist)
        pm.setAttr(initialLengthMultip_SC + ".input1Y", initLowerArmDist)

        pm.setAttr(initialDivide_SC + ".operation", 2)
        pm.setAttr(stretchCondition_SC + ".operation", 2)

        ### Bind Attributes and make constraints

        # Bind Stretch Attributes
        armStart.translate >> distance_SC.point1
        armEnd.translate >> distance_SC.point2
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
        stretchyness_SC.outputR >> jIK_SC_Low.translateX
        stretchyness_SC.outputG >> jIK_SC_LowEnd.translateX
        stretchyness_SC.outputR >> jIK_RP_Low.translateX
        stretchyness_SC.outputG >> jIK_RP_LowEnd.translateX

        self.cont_IK_hand.rotate >> jIK_RP_Low.rotate

        # Stretch Attributes Controller connections

        self.cont_IK_hand.sUpArm >> extraScaleMult_SC.input2X
        self.cont_IK_hand.sLowArm >> extraScaleMult_SC.input2Y
        self.cont_IK_hand.squash >> squashyness_SC.blender

        stretchOffset.output1D >> IK_stretch_distanceClamp.maxR
        self.cont_IK_hand.stretch >> IK_stretch_stretchynessClamp.inputR
        self.cont_IK_hand.stretch >> stretchOffset.input1D[2]

        IK_parentGRP = pm.group(name="IK_parentGRP_" + suffix, em=True)
        extra.alignTo(IK_parentGRP, handRef, 2)

        pm.parent(ikHandle_SC[0], IK_parentGRP)
        pm.parent(ikHandle_RP[0], IK_parentGRP)
        pm.parent(masterIK, IK_parentGRP)
        pm.parentConstraint(self.cont_IK_hand, IK_parentGRP, mo=True)

        blendORE_IK_Up = pm.createNode("blendColors", name="blendORE_IK_Up_" + suffix)
        jIK_SC_Up.rotate >> blendORE_IK_Up.color2
        jIK_RP_Up.rotate >> blendORE_IK_Up.color1
        blendORE_IK_Up.output >> jIK_orig_Up.rotate
        self.cont_IK_hand.polevector >> blendORE_IK_Up.blender

        blendPOS_IK_Up = pm.createNode("blendColors", name="blendPOS_IK_Up_" + suffix)
        jIK_SC_Up.translate >> blendPOS_IK_Up.color2
        jIK_RP_Up.translate >> blendPOS_IK_Up.color1
        blendPOS_IK_Up.output >> jIK_orig_Up.translate
        self.cont_IK_hand.polevector >> blendPOS_IK_Up.blender

        blendORE_IK_Low = pm.createNode("blendColors", name="blendORE_IK_Low_" + suffix)
        jIK_SC_Low.rotate >> blendORE_IK_Low.color2
        jIK_RP_Low.rotate >> blendORE_IK_Low.color1
        blendORE_IK_Low.output >> jIK_orig_Low.rotate
        self.cont_IK_hand.polevector >> blendORE_IK_Low.blender

        blendPOS_IK_Low = pm.createNode("blendColors", name="blendPOS_IK_Low_" + suffix)
        jIK_SC_Low.translate >> blendPOS_IK_Low.color2
        jIK_RP_Low.translate >> blendPOS_IK_Low.color1
        blendPOS_IK_Low.output >> jIK_orig_Low.translate
        self.cont_IK_hand.polevector >> blendPOS_IK_Low.blender

        blendORE_IK_LowEnd = pm.createNode("blendColors", name="blendORE_IK_LowEnd_" + suffix)
        jIK_SC_LowEnd.rotate >> blendORE_IK_LowEnd.color2
        jIK_RP_LowEnd.rotate >> blendORE_IK_LowEnd.color1
        blendORE_IK_LowEnd.output >> jIK_orig_LowEnd.rotate
        self.cont_IK_hand.polevector >> blendORE_IK_LowEnd.blender

        blendPOS_IK_LowEnd = pm.createNode("blendColors", name="blendPOS_IK_LowEnd_" + suffix)
        jIK_SC_LowEnd.translate >> blendPOS_IK_LowEnd.color2
        jIK_RP_LowEnd.translate >> blendPOS_IK_LowEnd.color1
        blendPOS_IK_LowEnd.output >> jIK_orig_LowEnd.translate
        self.cont_IK_hand.polevector >> blendPOS_IK_LowEnd.blender

        poleVector_Rvs = pm.createNode("reverse", name="poleVector_Rvs_" + suffix)
        self.cont_IK_hand.polevector >> poleVector_Rvs.inputX
        self.cont_IK_hand.polevector >> self.cont_Pole.v

        pm.parent(jIK_orig_Up, masterRoot)
        pm.parent(jIK_SC_Up, masterRoot)
        pm.parent(jIK_RP_Up, masterRoot)

        pm.select(cont_Shoulder)

        paconLocatorShou = pm.spaceLocator(name="paConLoc_" + suffix)
        extra.alignTo(paconLocatorShou, self.jDef_Collar)

        jDef_paCon = pm.parentConstraint(cont_Shoulder, paconLocatorShou, mo=True)

        ###########################
        ######### FK ARM ##########
        ###########################

        pm.select(d=True)
        jFK_Up = pm.joint(name="jFK_Up_" + suffix, p=shoulderPos, radius=1.0)
        jFK_Low = pm.joint(name="jFK_Low_" + suffix, p=elbowPos, radius=1.0)
        jFK_LowEnd = pm.joint(name="jFK_LowEnd_" + suffix, p=handPos, radius=1.0)

        pm.joint(jFK_Up, e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(jFK_Low, e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(jFK_LowEnd, e=True, zso=True, oj="xyz", sao="yup")

        cont_FK_UpArm.scaleY >> jFK_Up.scaleX

        cont_FK_LowArm.scaleY >> jFK_Low.scaleX

        ### Create Midlock - FK

        pm.orientConstraint(cont_FK_UpArm, jFK_Up, mo=True)
        pm.pointConstraint(startLock, jFK_Up, mo=False)

        pm.orientConstraint(cont_FK_LowArm, jFK_Low, mo=True)

        pm.parentConstraint(cont_Shoulder, cont_FK_UpArm_OFF, sr=("x", "y", "z"), mo=True)
        pm.parentConstraint(cont_FK_UpArm, cont_FK_LowArm_OFF, mo=True)

        fk_ik_rvs.outputX >> cont_FK_UpArm_ORE.visibility
        fk_ik_rvs.outputX >> cont_FK_LowArm_ORE.visibility

        cont_FK_IK.fk_ik >> self.cont_IK_hand.visibility

        ### Create MidLock controller

        midcontScale = (initLowerArmDist / 4, initLowerArmDist / 4, initLowerArmDist / 4)
        cont_midLock = icon.star("cont_mid_" + suffix, midcontScale, normal=(1, 0, 0))

        cont_midLock_POS = extra.createUpGrp(cont_midLock, "POS")
        cont_midLock_AVE = extra.createUpGrp(cont_midLock, "AVE")
        extra.alignTo(cont_midLock_POS, elbowRef, 0)

        midLock_paConWeight = pm.parentConstraint(jIK_orig_Up, jFK_Up, cont_midLock_POS, mo=True)
        cont_FK_IK.fk_ik >> (midLock_paConWeight + "." + jIK_orig_Up + "W0")
        fk_ik_rvs.outputX >> (midLock_paConWeight + "." + jFK_Up + "W1")

        midLock_poConWeight = pm.pointConstraint(jIK_orig_Low, jFK_Low, cont_midLock_AVE, mo=False)
        cont_FK_IK.fk_ik >> (midLock_poConWeight + "." + jIK_orig_Low + "W0")
        fk_ik_rvs.outputX >> (midLock_poConWeight + "." + jFK_Low + "W1")

        midLock_xBln = pm.createNode("multiplyDivide", name="midLock_xBln_" + suffix)

        midLock_rotXsw = pm.createNode("blendTwoAttr", name="midLock_rotXsw_" + suffix)
        jIK_orig_Low.rotateY >> midLock_rotXsw.input[0]
        jFK_Low.rotateY >> midLock_rotXsw.input[1]
        fk_ik_rvs.outputX >> midLock_rotXsw.attributesBlender

        midLock_rotXsw.output >> midLock_xBln.input1Z

        pm.setAttr(midLock_xBln.input2Z, 0.5)
        midLock_xBln.outputZ >> cont_midLock_AVE.rotateY

        ### Create Midlock

        midLock = pm.spaceLocator(name="midLock_" + suffix)
        pm.parentConstraint(midLock, jDef_elbow)
        extra.alignTo(midLock, cont_midLock, 0)

        pm.parentConstraint(cont_midLock, midLock, mo=False)

        ### Create End Lock
        endLock = pm.spaceLocator(name="endLock_" + suffix)
        extra.alignTo(endLock, handRef, 2)
        endLock_Ore = extra.createUpGrp(endLock, "Ore")
        endLock_Pos = extra.createUpGrp(endLock, "Pos")
        endLock_Twist = extra.createUpGrp(endLock, "Twist")

        endLockWeight = pm.pointConstraint(jIK_orig_LowEnd, jFK_LowEnd, endLock_Pos, mo=False)
        cont_FK_IK.fk_ik >> (endLockWeight + "." + jIK_orig_LowEnd + "W0")
        fk_ik_rvs.outputX >> (endLockWeight + "." + jFK_LowEnd + "W1")

        pm.parentConstraint(endLock, cont_FK_IK_POS, mo=True)
        pm.parent(endLock_Ore, self.scaleGrp)

        endLockRot = pm.parentConstraint(IK_parentGRP, cont_FK_Hand, endLock_Twist, st=("x", "y", "z"), mo=True)
        cont_FK_IK.fk_ik >> (endLockRot + "." + IK_parentGRP + "W0")
        fk_ik_rvs.outputX >> (endLockRot + "." + cont_FK_Hand + "W1")

        ###################################
        #### CREATE DEFORMATION JOINTS ####
        ###################################

        # UPPERARM RIBBON

        # ribbonConnections_upperArm = rc..createRibbon(shoulderRef, elbowRef, "up_" + suffix, 0)
        ribbonUpperArm = rc.Ribbon()
        ribbonUpperArm.createRibbon(shoulderRef, elbowRef, "up_" + suffix, 0)
        ribbonStart_paCon_upperArm_Start = pm.parentConstraint(startLock, ribbonUpperArm.startConnection, mo=True)
        ribbonStart_paCon_upperArm_End = pm.parentConstraint(midLock, ribbonUpperArm.endConnection, mo=True)

        pm.scaleConstraint(self.scaleGrp, ribbonUpperArm.scaleGrp)

        # AUTO AND MANUAL TWIST

        # auto
        autoTwist = pm.createNode("multiplyDivide", name="autoTwist_" + suffix)
        cont_Shoulder.autoTwist >> autoTwist.input2X
        ribbonStart_paCon_upperArm_Start.constraintRotate >> autoTwist.input1

        ###!!! The parent constrain override should be disconnected like this
        pm.disconnectAttr(ribbonStart_paCon_upperArm_Start.constraintRotateX, ribbonUpperArm.startConnection.rotateX)

        # manual
        AddManualTwist = pm.createNode("plusMinusAverage", name=("AddManualTwist_UpperArm_" + suffix))
        autoTwist.output >> AddManualTwist.input3D[0]
        cont_Shoulder.manualTwist >> AddManualTwist.input3D[1].input3Dx

        # connect to the joint
        AddManualTwist.output3D >> ribbonUpperArm.startConnection.rotate

        # LOWERARM RIBBON

        ribbonLowerArm = rc.Ribbon()
        ribbonLowerArm.createRibbon(elbowRef, handRef, "low_" + suffix,0)

        ribbonStart_paCon_lowerArm_Start = pm.parentConstraint(midLock, ribbonLowerArm.startConnection, mo=True)
        ribbonStart_paCon_lowerArm_End = pm.parentConstraint(endLock, ribbonLowerArm.endConnection, mo=True)

        pm.scaleConstraint(self.scaleGrp, ribbonLowerArm.scaleGrp)

        # AUTO AND MANUAL TWIST

        # auto
        autoTwist = pm.createNode("multiplyDivide", name="autoTwist_" + suffix)
        cont_FK_IK.autoTwist >> autoTwist.input2X
        ribbonStart_paCon_lowerArm_End.constraintRotate >> autoTwist.input1

        ###!!! The parent constrain override should be disconnected like this
        pm.disconnectAttr(ribbonStart_paCon_lowerArm_End.constraintRotateX, ribbonLowerArm.endConnection.rotateX)

        # manual
        AddManualTwist = pm.createNode("plusMinusAverage", name=("AddManualTwist_LowerArm_" + suffix))
        autoTwist.output >> AddManualTwist.input3D[0]
        cont_FK_IK.manualTwist >> AddManualTwist.input3D[1].input3Dx

        # connect to the joint
        AddManualTwist.output3D >> ribbonLowerArm.endConnection.rotate

        ###############################################
        ################### HAND ######################
        ###############################################

        handLock = pm.spaceLocator(
            name="handLock_" + suffix)  ## Bu iki satir r arm mirror posing icin dondurulse bile dogru bir weighted constraint yapilmasi icin araya bir node olusturuyor.
        extra.alignTo(handLock, cont_FK_Hand_OFF, 2)
        pm.parentConstraint(cont_FK_Hand, handLock, mo=True)  ## Olusturulan ara node baglanir

        ####################
        ## CREATE FINGERS ##
        ####################

        if side == "R":
            mirror = True
        else:
            mirror = False

        rootPosition = handRef.getTranslation(space="world")
        rootMaster = pm.spaceLocator(name="handMaster_" + suffix)
        extra.alignTo(rootMaster, handRef, 2)
        pm.select(d=True)
        jDef_Hand = pm.joint(name="jDef_Hand_" + suffix, p=rootPosition, radius=1.0)
        self.sockets.append(jDef_Hand)
        # self.defJoints.append([jDef_Hand])
        extra.alignTo(jDef_Hand, handRef, 2)
        deformerJoints = [[jDef_Hand]]
        pm.parent(jDef_Hand, rootMaster)

        handRoot = handRef

        pm.pointConstraint(endLock, rootMaster, mo=True)
        pm.parentConstraint(cont_FK_LowArm, cont_FK_Hand_POS, mo=True)
        # handOriCon = pm.orientConstraint(self.cont_IK_hand, handLock, rootMaster, mo=False)
        handOriCon = pm.parentConstraint(self.cont_IK_hand, handLock, rootMaster, st=("x", "y", "z"), mo=True)
        cont_FK_IK.fk_ik >> (handOriCon + "." + self.cont_IK_hand + "W0")
        fk_ik_rvs.outputX >> (handOriCon + "." + handLock + "W1")
        fk_ik_rvs.outputX >> cont_FK_Hand.v

        handScaCon = pm.createNode("blendColors", name="handScaCon_" + suffix)
        self.cont_IK_hand.scale >> handScaCon.color1
        cont_FK_Hand.scale >> handScaCon.color2
        cont_FK_IK.fk_ik >> handScaCon.blender
        handScaCon.output >> rootMaster.scale

        ### FINAL ROUND UP

        pm.select(armStart)

        pm.parentConstraint(self.limbPlug, self.scaleGrp, mo=True)
        pm.parent(startLock_Ore, self.scaleGrp)
        pm.parent(armStart, self.scaleGrp)
        pm.parent(armEnd, self.scaleGrp)
        pm.parent(IK_parentGRP, self.scaleGrp)
        pm.parent(cont_Shoulder_OFF, self.scaleGrp)
        pm.parent(cont_FK_UpArm_OFF, self.scaleGrp)
        pm.parent(cont_FK_LowArm_OFF, self.scaleGrp)

        pm.parent(IK_parentGRP, self.scaleGrp)
        pm.parent(cont_FK_Hand_OFF, self.scaleGrp)
        pm.parent(midLock, self.scaleGrp)
        pm.parent(cont_midLock_POS, self.scaleGrp)
        pm.parent(cont_Pole_OFF, self.scaleGrp)
        pm.parent(jDef_elbow, self.scaleGrp)

        pm.parent(ribbonUpperArm.scaleGrp, self.nonScaleGrp)
        pm.parent(ribbonUpperArm.nonScaleGrp, self.nonScaleGrp)

        pm.parent(ribbonLowerArm.scaleGrp, self.nonScaleGrp)
        pm.parent(ribbonLowerArm.nonScaleGrp, self.nonScaleGrp)

        pm.parent(paconLocatorShou, self.scaleGrp)
        pm.parent(self.jDef_Collar, paconLocatorShou)

        pm.parent(handLock, self.scaleGrp)
        pm.parent(masterRoot, self.scaleGrp)
        pm.parent(jFK_Up, self.scaleGrp)
        pm.parent(cont_FK_IK_POS, self.scaleGrp)
        pm.parent(rootMaster, self.scaleGrp)

        ## CONNECT RIG VISIBILITES

        # Tweak controls
        tweakControls=(ribbonUpperArm.middleCont, ribbonLowerArm.middleCont, cont_midLock)

        for i in tweakControls:
            cont_FK_IK.tweakControls >> i.v

        pm.addAttr(self.scaleGrp, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True)
        pm.addAttr(self.scaleGrp, at="bool", ln="Joints_Visibility", sn="jointVis", defaultValue=True)
        pm.addAttr(self.scaleGrp, at="bool", ln="Rig_Visibility", sn="rigVis", defaultValue=False)
        # make the created attributes visible in the channelbox
        pm.setAttr(self.scaleGrp.contVis, cb=True)
        pm.setAttr(self.scaleGrp.jointVis, cb=True)
        pm.setAttr(self.scaleGrp.rigVis, cb=True)

        self.nodesContVis = [cont_Pole_OFF, cont_Shoulder_OFF, cont_IK_hand_OFF, cont_FK_Hand_OFF, cont_FK_IK_POS,
                        cont_FK_LowArm_OFF, cont_FK_UpArm_OFF, ribbonLowerArm.scaleGrp, ribbonUpperArm.scaleGrp, cont_midLock_POS]
        nodesJointVis = [jDef_elbow, jDef_paCon, self.jDef_Collar, jDef_Hand]
        nodesJointVisLists = [ribbonLowerArm.deformerJoints, ribbonUpperArm.deformerJoints, nodesJointVis]
        nodesRigVis = [endLock_Twist, startLock_Ore, armStart, armEnd, IK_parentGRP, midLock, masterRoot, jFK_Up, handLock, rootMaster.getShape(), paconLocatorShou.getShape()]
        # global Cont visibilities


        for i in self.nodesContVis:
            self.scaleGrp.contVis >> i.v

        # global Joint visibilities
        for lst in nodesJointVisLists:
            for j in lst:
                self.scaleGrp.jointVis >> j.v

        # global Rig visibilities

        for i in nodesRigVis:
            self.scaleGrp.rigVis >> i.v
        for i in ribbonLowerArm.toHide:
            self.scaleGrp.rigVis >> i.v
        for i in ribbonUpperArm.toHide:
            self.scaleGrp.rigVis >> i.v

        pm.setAttr(self.scaleGrp.rigVis, 0)

        # FOOL PROOFING

        extra.lockAndHide(self.cont_IK_hand, ["v"])
        extra.lockAndHide(self.cont_Pole, ["rx", "ry", "rz", "sx", "sy", "sz", "v"])
        extra.lockAndHide(cont_midLock, ["sx", "sy", "sz", "v"])
        extra.lockAndHide(cont_FK_IK, ["sx", "sy", "sz", "v"])
        extra.lockAndHide(cont_FK_Hand, ["tx", "ty", "tz", "v"])
        extra.lockAndHide(cont_FK_LowArm, ["tx", "ty", "tz", "sx", "sz", "v"])
        extra.lockAndHide(cont_FK_UpArm, ["tx", "ty", "tz", "sx", "sz", "v"])
        extra.lockAndHide(cont_Shoulder, ["sx", "sy", "sz", "v"])

        # COLOR CODING

        if side == "R":
            index = 13  ##Red color index
            indexMin = 9  ##Magenta color index
        else:
            index = 6  ##Blue Color index
            indexMin = 18

        extra.colorize(cont_Shoulder, index)
        extra.colorize(self.cont_IK_hand, index)
        extra.colorize(self.cont_Pole, index)
        extra.colorize(cont_FK_IK, index)
        extra.colorize(cont_FK_UpArm, index)
        extra.colorize(cont_FK_LowArm, index)
        extra.colorize(cont_FK_Hand, index)
        extra.colorize(cont_midLock, indexMin)
        extra.colorize(ribbonUpperArm.middleCont, indexMin)
        extra.colorize(ribbonLowerArm.middleCont, indexMin)

        self.scaleConstraints = [self.scaleGrp, cont_IK_hand_OFF]
        self.anchors = [(self.cont_IK_hand, "parent", 1, None),(self.cont_Pole, "parent", 1, None)]
        self.cont_IK_OFF = cont_IK_hand_OFF
