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


###########################
######### IK ARM ##########
###########################
class arm():

    sockets = []
    # startSocket = None
    # endSocket = None
    scaleGrp = None
    nonScaleGrp = None
    cont_IK_hand = None
    # cont_IK_hand_OFF = None
    cont_IK_OFF = None
    rootSocket = None
    cont_Pole = None
    nodesContVis = None
    limbPlug = None
    scaleConstraints = []
    anchors = []
    anchorLocations = []

    ## This is a joint node and should be parented to another joint.
    def createArm(self, armInits, suffix="", side="L", mirrorAxis="X"):

        idCounter=0
        ## create an unique suffix
        while pm.objExists("scaleGrp_" + suffix):
            suffix = "%s%s" % (suffix, str(idCounter + 1))

        if len(armInits)<4:
            pm.error("Missing Joints for Arm Setup")
            return


        # reinitialize the dictionary for easy use
        collarRef = armInits["Collar"]
        shoulderRef = armInits["Shoulder"]
        elbowRef = armInits["Elbow"]
        handRef = armInits["Hand"]

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

        # Create Limb Plug
        pm.select(d=True)
        self.limbPlug = pm.joint(name="jPlug_" + suffix, p=collarPos, radius=3)

        # Shoulder Joints
        pm.select(d=True)
        jDef_Collar = pm.joint(name="jDef_Collar_" + suffix, p=collarPos, radius=1.5)
        self.sockets.append(jDef_Collar)
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

        pm.joint(jDef_Collar, e=True, zso=True, oj="xyz", sao="yup")
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

        ###Create Control Curve - IK
        IKcontScale = (initLowerArmDist / 3, initLowerArmDist / 3, initLowerArmDist / 3)
        self.cont_IK_hand = icon.circle("cont_IK_hand_" + suffix, IKcontScale, normal=(1, 0, 0))
        extra.alignTo(self.cont_IK_hand, handRef, 2)

        cont_IK_hand_OFF = extra.createUpGrp(self.cont_IK_hand, "OFF")
        cont_IK_hand_ORE = extra.createUpGrp(self.cont_IK_hand, "ORE")
        ###Add ATTRIBUTES to the IK Hand Controller
        pm.addAttr(shortName="polevector", longName="Pole_Vector", defaultValue=0.0, minValue=0.0, maxValue=1.0,
                   at="double", k=True)
        pm.addAttr(shortName="sUpArm", longName="Scale_Upper_Arm", defaultValue=1.0, minValue=0.0, at="double", k=True)
        pm.addAttr(shortName="sLowArm", longName="Scale_Lower_Arm", defaultValue=1.0, minValue=0.0, at="double", k=True)
        pm.addAttr(shortName="squash", longName="Squash", defaultValue=0.0, minValue=0.0, maxValue=1.0, at="double", k=True)
        pm.addAttr(shortName="stretch", longName="Stretch", defaultValue=100.0, minValue=0.0, maxValue=100.0, at="double",
                   k=True)

        ###Create Pole Vector Curve - IK

        polecontS = (((initUpperArmDist + initLowerArmDist) / 2) / 10)
        polecontScale = (polecontS, polecontS, polecontS)
        self.cont_Pole = icon.plus("cont_Pole_" + suffix, polecontScale)
        pm.rotate(self.cont_Pole, (90, 0, 0))
        pm.makeIdentity(a=True)
        extra.alignTo(self.cont_Pole, elbowRef, 0)

        pm.move(self.cont_Pole, (0, 0, (-polecontS*5)), r=True)
        pm.makeIdentity(a=True)
        cont_Pole_OFF = extra.createUpGrp(self.cont_Pole, "OFF")

        pm.poleVectorConstraint(self.cont_Pole, "ikHandle_RP_" + suffix)

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

        # Create Orig Switch (Pole Vector On/Off)

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

        ### Shoulder Controller
        shouldercontScale = (initShoulderDist / 2, initShoulderDist / 2, initShoulderDist / 2,)
        cont_Shoulder = icon.shoulder("cont_Shoulder_" + suffix, shouldercontScale)


        cont_Shoulder_OFF = extra.createUpGrp(cont_Shoulder, "OFF")
        cont_Shoulder_ORE = extra.createUpGrp(cont_Shoulder, "ORE")
        cont_Shoulder_POS = extra.createUpGrp(cont_Shoulder, "POS")

        extra.alignTo(cont_Shoulder_OFF, collarRef, 2)

        if side == "R":
            pm.setAttr("%s.rotate%s" % (cont_Shoulder_ORE, mirrorAxis), -180)
            pm.setAttr(cont_Shoulder.scaleY, -1)

        pm.select(cont_Shoulder)
        pm.addAttr(shortName="autoTwist", longName="Auto_Twist", defaultValue=1.0, minValue=0.0, maxValue=1.0, at="float",
                   k=True)
        pm.addAttr(shortName="manualTwist", longName="Manual_Twist", defaultValue=0.0, at="float", k=True)
        pm.select(d=True)

        pm.parent(jIK_orig_Up, masterRoot)
        pm.parent(jIK_SC_Up, masterRoot)
        pm.parent(jIK_RP_Up, masterRoot)

        pm.select(cont_Shoulder)

        pm.makeIdentity(a=True, t=True, r=True, s=False)

        jDef_paCon = pm.parentConstraint(cont_Shoulder, jDef_Collar, mo=True)

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

        ### Create Controller Curves
        scalecontFkUpArm = (initUpperArmDist / 8, initUpperArmDist / 2, initUpperArmDist / 8)
        cont_FK_UpArm = icon.cube("cont_FK_UpArm_" + suffix, scalecontFkUpArm)

        cont_FK_UpArm_OFF = extra.createUpGrp(cont_FK_UpArm, "OFF")
        cont_FK_UpArm_ORE = extra.createUpGrp(cont_FK_UpArm, "ORE")
        if side == "R":
            pm.setAttr("%s.rotate%s" % (cont_FK_UpArm_ORE, mirrorAxis), -180)

        temp_PoCon = pm.pointConstraint(jFK_Up, jFK_Low, cont_FK_UpArm_OFF)
        pm.delete(temp_PoCon)
        temp_AimCon = pm.aimConstraint(jFK_Low, cont_FK_UpArm_OFF, o=(90, 90, 0), u=(0, 1, 0))
        pm.delete(temp_AimCon)

        PvTarget = shoulderPos
        pm.xform(cont_FK_UpArm, piv=PvTarget, ws=True)
        pm.xform(cont_FK_UpArm_ORE, piv=PvTarget, ws=True)
        pm.xform(cont_FK_UpArm_OFF, piv=PvTarget, ws=True)

        pm.makeIdentity(a=True, t=True, r=False, s=True)
        pm.parent(cont_FK_UpArm, cont_FK_UpArm_ORE)

        cont_FK_UpArm.scaleY >> jFK_Up.scaleX

        scalecontFkLowArm = (initLowerArmDist / 8, initLowerArmDist / 2, initLowerArmDist / 8)

        cont_FK_LowArm = icon.cube("cont_FK_LowArm_" + suffix, scalecontFkLowArm)

        cont_FK_LowArm_OFF = extra.createUpGrp(cont_FK_LowArm, "OFF")
        cont_FK_LowArm_ORE = extra.createUpGrp(cont_FK_LowArm, "ORE")
        if side == "R":
            pm.setAttr("%s.rotate%s" %(cont_FK_LowArm_ORE,mirrorAxis), -180)

        temp_PoCon = pm.pointConstraint(jFK_Low, jFK_LowEnd, cont_FK_LowArm_OFF)
        pm.delete(temp_PoCon)
        temp_AimCon = pm.aimConstraint(jFK_LowEnd, cont_FK_LowArm_OFF, o=(90, 90, 0), u=(0, 1, 0))
        pm.delete(temp_AimCon)

        pm.makeIdentity(a=True, t=True, r=False, s=True)

        PvTarget = elbowPos
        pm.xform(cont_FK_LowArm, piv=PvTarget, ws=True)
        pm.xform(cont_FK_LowArm_ORE, piv=PvTarget, ws=True)
        pm.xform(cont_FK_LowArm_OFF, piv=PvTarget, ws=True)

        cont_FK_LowArm.scaleY >> jFK_Low.scaleX

        ################## // END of mod

        ### Create Midlock - FK

        pm.orientConstraint(cont_FK_UpArm, jFK_Up, mo=True)
        pm.pointConstraint(startLock, jFK_Up, mo=False)

        pm.orientConstraint(cont_FK_LowArm, jFK_Low, mo=True)

        pm.parentConstraint(cont_Shoulder, cont_FK_UpArm_OFF, sr=("x", "y", "z"), mo=True)
        pm.parentConstraint(cont_FK_UpArm, cont_FK_LowArm_OFF, mo=True)

        ### Create FK IK Icon

        iconScale = initUpperArmDist / 4

        cont_FK_IKList = icon.fkikSwitch(("cont_FK_IK_" + suffix), (iconScale, iconScale, iconScale))
        cont_FK_IK = cont_FK_IKList[0]
        fk_ik_rvs = cont_FK_IKList[1]

        ## FK-IK ICON Attributes

        pm.addAttr(cont_FK_IK, shortName="autoTwist", longName="Auto_Twist", defaultValue=1.0, minValue=0.0, maxValue=1.0,
                   at="float", k=True)
        pm.addAttr(cont_FK_IK, shortName="manualTwist", longName="Manual_Twist", defaultValue=0.0, at="float", k=True)
        pm.addAttr(cont_FK_IK, shortName="tweakControls", longName="Tweak_Controls", defaultValue=0, at="bool")
        pm.setAttr(cont_FK_IK.tweakControls, cb=True)
        pm.addAttr(cont_FK_IK, shortName="fingerControls", longName="Finger_Controls", defaultValue=1, at="bool")
        pm.setAttr(cont_FK_IK.fingerControls, cb=True)

        fk_ik_rvs.outputX >> cont_FK_UpArm_ORE.visibility
        fk_ik_rvs.outputX >> cont_FK_LowArm_ORE.visibility

        cont_FK_IK.fk_ik >> self.cont_IK_hand.visibility

        extra.alignTo(cont_FK_IK, handRef, 2)

        pm.move(cont_FK_IK, (0, iconScale * 2, 0), r=True)

        cont_FK_IK_POS = extra.createUpGrp(cont_FK_IK, "POS")

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

        endLockRot = pm.parentConstraint(IK_parentGRP, jFK_Low, endLock_Twist, st=("x", "y", "z"), mo=True)
        cont_FK_IK.fk_ik >> (endLockRot + "." + IK_parentGRP + "W0")
        fk_ik_rvs.outputX >> (endLockRot + "." + jFK_Low + "W1")

        ###################################
        #### CREATE DEFORMATION JOINTS ####
        ###################################

        # UPPERARM RIBBON

        # ribbonConnections_upperArm = rc..createRibbon(shoulderRef, elbowRef, "up_" + suffix, 0)
        ribbonUpperArm = rc.ribbon()
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

        ribbonLowerArm = rc.ribbon()
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

        ### Hand Controllers

        FKcontScale = (initLowerArmDist / 5, initLowerArmDist / 5, initLowerArmDist / 5)
        cont_FK_Hand = icon.cube("cont_FK_Hand_" + suffix, FKcontScale)
        extra.alignTo(cont_FK_Hand, endLock_Ore, 2)

        cont_FK_Hand_OFF = extra.createUpGrp(cont_FK_Hand, "OFF")
        cont_FK_Hand_POS = extra.createUpGrp(cont_FK_Hand, "POS")
        cont_FK_Hand_ORE = extra.createUpGrp(cont_FK_Hand, "ORE")

        handLock = pm.spaceLocator(
            name="handLock_" + suffix)  ## Bu iki satir r arm mirror posing icin dondurulse bile dogru bir weighted constraint yapilmasi icin araya bir node olusturuyor.
        extra.alignTo(handLock, cont_FK_Hand_OFF, 2)

        if side == "R":
            pm.setAttr("%s.rotate%s" % (cont_FK_Hand_ORE, mirrorAxis), -180)

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
        # deformerJoints = [[jDef_Hand]]
        pm.parent(jDef_Hand, rootMaster)

        handRoot = handRef
        # handFingers = mFingers.multiFingers()
        # handFingers.rigFingers(handRoot, cont_FK_IK, suffix, mirror)

        pm.pointConstraint(endLock, rootMaster, mo=True)
        pm.parentConstraint(cont_FK_LowArm, cont_FK_Hand_POS, mo=True)
        handOriCon = pm.orientConstraint(self.cont_IK_hand, handLock, rootMaster, mo=False)
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
        pm.parent(cont_FK_Hand_OFF, self.scaleGrp)
        pm.parent(midLock, self.scaleGrp)
        pm.parent(cont_midLock_POS, self.scaleGrp)
        pm.parent(cont_Pole_OFF, self.scaleGrp)
        pm.parent(jDef_elbow, self.scaleGrp)

        pm.parent(ribbonUpperArm.scaleGrp, self.nonScaleGrp)
        pm.parent(ribbonUpperArm.nonScaleGrp, self.nonScaleGrp)

        pm.parent(ribbonLowerArm.scaleGrp, self.nonScaleGrp)
        pm.parent(ribbonLowerArm.nonScaleGrp, self.nonScaleGrp)

        pm.parent(jDef_Collar, self.scaleGrp)

        pm.parent(handLock, self.scaleGrp)
        pm.parent(masterRoot, self.scaleGrp)
        pm.parent(jFK_Up, self.scaleGrp)
        pm.parent(cont_FK_IK_POS, self.scaleGrp)
        # pm.parent(handFingers.rootMaster, self.scaleGrp)

        ## CONNECT RIG VISIBILITES

        # Tweak controls
        tweakControls=(ribbonUpperArm.middleCont, ribbonLowerArm.middleCont, cont_midLock)

        for i in tweakControls:
            cont_FK_IK.tweakControls >> i.v

        # Hand controls
        # for finger in handFingers.allControllers:
        #     for i in finger:
        #         cont_FK_IK.fingerControls >> i.v

        pm.addAttr(self.scaleGrp, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True)
        pm.addAttr(self.scaleGrp, at="bool", ln="Joints_Visibility", sn="jointVis", defaultValue=True)
        pm.addAttr(self.scaleGrp, at="bool", ln="Rig_Visibility", sn="rigVis", defaultValue=False)
        # make the created attributes visible in the channelbox
        pm.setAttr(self.scaleGrp.contVis, cb=True)
        pm.setAttr(self.scaleGrp.jointVis, cb=True)
        pm.setAttr(self.scaleGrp.rigVis, cb=True)

        self.nodesContVis = [cont_Pole_OFF, cont_Shoulder_OFF, cont_IK_hand_OFF, cont_FK_Hand_OFF, cont_FK_IK_POS,
                        cont_FK_LowArm_OFF, cont_FK_UpArm_OFF, ribbonLowerArm.scaleGrp, ribbonUpperArm.scaleGrp, cont_midLock_POS]
        nodesJointVis = [jDef_elbow, jDef_paCon, jDef_Collar, jDef_Hand]
        nodesJointVisLists = [ribbonLowerArm.deformerJoints, ribbonUpperArm.deformerJoints, nodesJointVis]
        nodesRigVis = [endLock_Twist, startLock_Ore, armStart, armEnd, IK_parentGRP, midLock, masterRoot, jFK_Up, handLock, rootMaster]
        # global Cont visibilities


        for i in self.nodesContVis:
            self.scaleGrp.contVis >> i.v
        # for finger in handFingers.allControllers:
        #     for i in finger:
                # reserve the controllers visibility for finger controls visibility on FK_IK switch
                # ek = i.getParent()
                # self.scaleGrp.contVis >> ek.v

        # global Joint visibilities
        for lst in nodesJointVisLists:
            for j in lst:
                self.scaleGrp.jointVis >> j.v
        # for lst in handFingers.defJoints:
        #     for j in lst:
        #         self.scaleGrp.jointVis >> j.v

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
        extra.lockAndHide(cont_midLock, ["sx", "sy", "sz", "v"])
        extra.lockAndHide(cont_FK_IK, ["sx", "sy", "sz", "v"])
        extra.lockAndHide(cont_FK_Hand, ["tx", "ty", "tz", "v"])
        extra.lockAndHide(cont_FK_LowArm, ["tx", "ty", "tz", "sx", "sz", "v"])
        extra.lockAndHide(cont_FK_UpArm, ["tx", "ty", "tz", "sx", "sz", "v"])
        extra.lockAndHide(cont_Shoulder, ["sx", "sy", "sz", "v"])
        # for finger in handFingers.allControllers:
        #     for eklem in finger:
        #         extra.lockAndHide(eklem, ["sx", "sy", "sz"])

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
        # for i in handFingers.allControllers:
        #     extra.colorize(i, indexMin)

        extra.colorize(cont_midLock, indexMin)
        extra.colorize(ribbonUpperArm.middleCont, indexMin)
        extra.colorize(ribbonLowerArm.middleCont, indexMin)


        self.scaleConstraints = [self.scaleGrp, cont_IK_hand_OFF]
        self.anchors = [(self.cont_IK_hand, "parent", 1, None),(self.cont_Pole, "parent", 1, None)]
        self.cont_IK_OFF = cont_IK_hand_OFF
