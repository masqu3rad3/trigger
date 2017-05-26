import pymel.core as pm
import sys

path = 'C:/Users/Arda/Documents/maya/2017/scripts/tik_autorigger'
if not path in sys.path:
    sys.path.append(path)

import extraProcedures as extra

reload(extra)
import createRibbon as cr

reload(cr)
import contIcons as icon

reload(icon)
import createFinger as cf

reload(cf)


###########################
######### IK ARM ##########
###########################

def createArm(whichArm):
    # contScale= extra.getDistance(pm.PyNode("jInit_Low_"+whichArm), pm.PyNode("jInit_LowEnd_"+whichArm))

    initBones = pm.ls("jInit*" + whichArm)
    totalJcount = 4
    # if pm.objExists(pm.PyNode("jInit_LowEnd_{}".format(whichArm))):
    #     fingerCount=pm.getAttr(pm.PyNode("jInit_LowEnd_{0}.{1}".format(whichArm,"fingerCount")))
    #     totalJcount=4+(fingerCount*5)-1
    # else:
    #     pm.error("Some or all Arm Init Bones are missing (or Renamed)(fingercount)")
    #     return
    if (len(initBones) < totalJcount):
        pm.error("Some or all Arm Init Bones are missing (or Renamed)")
        return
    if pm.objExists("scaleGrp_" + whichArm):
        pm.error("Arm with the same name exists in the scene (or maybe not purged completely")
        return
    ##Groups
    scaleGrp = pm.group(name="scaleGrp_" + whichArm, em=True)
    extra.alignTo(scaleGrp, "jInit_Shoulder_" + whichArm, 0)
    nonScaleGrp = pm.group(name="NonScaleGrp_" + whichArm, em=True)

    masterRoot = pm.group(em=True, name="masterRoot_" + whichArm)
    extra.alignTo(masterRoot, "jInit_Shoulder_" + whichArm, 0)
    pm.makeIdentity(a=True)

    masterIK = pm.spaceLocator(name="masterIK_" + whichArm)
    extra.alignTo(masterIK, "jInit_LowEnd_" + whichArm, 0)

    initShoulderDist = extra.getDistance(pm.PyNode("jInit_Shoulder_" + whichArm), pm.PyNode("jInit_Up_" + whichArm))
    initUpperArmDist = extra.getDistance(pm.PyNode("jInit_Up_" + whichArm), pm.PyNode("jInit_Low_" + whichArm))
    initLowerArmDist = extra.getDistance(pm.PyNode("jInit_Low_" + whichArm), pm.PyNode("jInit_LowEnd_" + whichArm))

    # Shoulder Joints
    pm.select(d=True)
    jDef_Shoulder = pm.joint(name="jDef_Shoulder_" + whichArm,
                             p=pm.PyNode("jInit_Shoulder_" + whichArm).getTranslation(space="world"), radius=1.5)
    j_ShoulderEnd = pm.joint(name="j_ShoulderEnd_" + whichArm,
                             p=pm.PyNode("jInit_Up_" + whichArm).getTranslation(space="world"), radius=1.5)

    pm.select(d=True)
    jDef_midArm = pm.joint(name="jDef_midArm_" + whichArm,
                           p=pm.PyNode("jInit_Low_" + whichArm).getTranslation(space="world"), radius=1.5)

    pm.select(d=True)
    jIK_orig_Up = pm.joint(name="jIK_orig_Up_" + whichArm,
                           p=pm.PyNode("jInit_Up_" + whichArm).getTranslation(space="world"), radius=1.5)
    jIK_orig_Low = pm.joint(name="jIK_orig_Low_" + whichArm,
                            p=pm.PyNode("jInit_Low_" + whichArm).getTranslation(space="world"), radius=1.5)
    jIK_orig_LowEnd = pm.joint(name="jIK_orig_LowEnd_" + whichArm,
                               p=pm.PyNode("jInit_LowEnd_" + whichArm).getTranslation(space="world"), radius=1.5)
    pm.select(d=True)

    jIK_SC_Up = pm.joint(name="jIK_SC_Up_" + whichArm,
                         p=pm.PyNode("jInit_Up_" + whichArm).getTranslation(space="world"), radius=1)
    jIK_SC_Low = pm.joint(name="jIK_SC_Low_" + whichArm,
                          p=pm.PyNode("jInit_Low_" + whichArm).getTranslation(space="world"), radius=1)
    jIK_SC_LowEnd = pm.joint(name="jIK_SC_LowEnd_" + whichArm,
                             p=pm.PyNode("jInit_LowEnd_" + whichArm).getTranslation(space="world"), radius=1)
    pm.select(d=True)

    jIK_RP_Up = pm.joint(name="jIK_RP_Up_" + whichArm,
                         p=pm.PyNode("jInit_Up_" + whichArm).getTranslation(space="world"), radius=0.7)
    jIK_RP_Low = pm.joint(name="jIK_RP_Low_" + whichArm,
                          p=pm.PyNode("jInit_Low_" + whichArm).getTranslation(space="world"), radius=0.7)
    jIK_RP_LowEnd = pm.joint(name="jIK_RP_LowEnd_" + whichArm,
                             p=pm.PyNode("jInit_LowEnd_" + whichArm).getTranslation(space="world"), radius=0.7)
    pm.select(d=True)

    pm.joint(jDef_Shoulder, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(j_ShoulderEnd, e=True, zso=True, oj="xyz", sao="yup")

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

    startLock = pm.spaceLocator(name="startLock_" + whichArm)
    extra.alignTo(startLock, pm.PyNode("jInit_Up_" + whichArm), 2)
    startLock_Ore = extra.createUpGrp(startLock, "Ore")
    startLock_Pos = extra.createUpGrp(startLock, "Pos")
    startLock_Twist = extra.createUpGrp(startLock, "AutoTwist")

    startLockWeight = pm.parentConstraint(j_ShoulderEnd, startLock, sr=("y", "z"), mo=True)

    # pm.setAttr(startLockWeight.interpType, 0)

    pm.parentConstraint(startLock, jIK_SC_Up, mo=True)
    pm.parentConstraint(startLock, jIK_RP_Up, mo=True)

    ###Create IK handles

    ikHandle_SC = pm.ikHandle(sj=jIK_SC_Up, ee=jIK_SC_LowEnd, name="ikHandle_SC_" + whichArm)
    ikHandle_RP = pm.ikHandle(sj=jIK_RP_Up, ee=jIK_RP_LowEnd, name="ikHandle_RP_" + whichArm, sol="ikRPsolver")

    ###Create Control Curve - IK
    IKcontScale = (initLowerArmDist / 3, initLowerArmDist / 3, initLowerArmDist / 3)
    cont_IK_hand = icon.circle("cont_IK_hand_" + whichArm, IKcontScale, normal=(1, 0, 0))
    extra.alignTo(cont_IK_hand, pm.PyNode("jInit_LowEnd_" + whichArm), 2)

    cont_IK_hand_OFF = extra.createUpGrp(cont_IK_hand, "OFF")
    cont_IK_hand_ORE = extra.createUpGrp(cont_IK_hand, "ORE")

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
    cont_Pole = icon.plus("cont_Pole_" + whichArm, polecontScale)
    pm.rotate(cont_Pole, (90, 0, 0))
    pm.makeIdentity(a=True)
    extra.alignTo(cont_Pole, pm.PyNode("jInit_Low_" + whichArm), 0)

    pm.move(cont_Pole, (0, 0, (-polecontS*5)), r=True)
    pm.makeIdentity(a=True)
    cont_Pole_OFF = extra.createUpGrp(cont_Pole, "OFF")

    pm.poleVectorConstraint(cont_Pole, "ikHandle_RP_" + whichArm)

    ### Create and constrain Distance Locators

    armStart = pm.spaceLocator(name="armStart_" + whichArm)
    pm.pointConstraint(startLock, armStart, mo=False)

    armEnd = pm.spaceLocator(name="armEnd_" + whichArm)
    pm.pointConstraint(masterIK, armEnd, mo=False)

    ### Create Nodes and Connections for Strethchy IK SC

    stretchOffset = pm.createNode("plusMinusAverage", name="stretchOffset_" + whichArm)
    distance_SC = pm.createNode("distanceBetween", name="distance_SC_" + whichArm)
    IK_stretch_distanceClamp = pm.createNode("clamp", name="IK_stretch_distanceClamp_" + whichArm)
    IK_stretch_stretchynessClamp = pm.createNode("clamp", name="IK_stretch_stretchynessClamp_" + whichArm)
    extraScaleMult_SC = pm.createNode("multiplyDivide", name="extraScaleMult_SC_" + whichArm)
    initialDivide_SC = pm.createNode("multiplyDivide", name="initialDivide_SC_" + whichArm)
    initialLengthMultip_SC = pm.createNode("multiplyDivide", name="initialLengthMultip_SC_" + whichArm)
    stretchAmount_SC = pm.createNode("multiplyDivide", name="stretchAmount_SC_" + whichArm)
    sumOfJLengths_SC = pm.createNode("plusMinusAverage", name="sumOfJLengths_SC_" + whichArm)
    stretchCondition_SC = pm.createNode("condition", name="stretchCondition_SC_" + whichArm)
    squashyness_SC = pm.createNode("blendColors", name="squashyness_SC_" + whichArm)
    stretchyness_SC = pm.createNode("blendColors", name="stretchyness_SC_" + whichArm)

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

    cont_IK_hand.rotate >> jIK_RP_Low.rotate

    # Stretch Attributes Controller connections

    cont_IK_hand.sUpArm >> extraScaleMult_SC.input2X
    cont_IK_hand.sLowArm >> extraScaleMult_SC.input2Y
    cont_IK_hand.squash >> squashyness_SC.blender

    stretchOffset.output1D >> IK_stretch_distanceClamp.maxR
    cont_IK_hand.stretch >> IK_stretch_stretchynessClamp.inputR
    cont_IK_hand.stretch >> stretchOffset.input1D[2]

    IK_parentGRP = pm.group(name="IK_parentGRP_" + whichArm, em=True)
    extra.alignTo(IK_parentGRP, "jInit_LowEnd_" + whichArm, 2)

    pm.parent(ikHandle_SC[0], IK_parentGRP)
    pm.parent(ikHandle_RP[0], IK_parentGRP)
    pm.parent(masterIK, IK_parentGRP)
    pm.parentConstraint(cont_IK_hand, IK_parentGRP, mo=True)

    # Create Orig Switch (Pole Vector On/Off)

    blendORE_IK_Up = pm.createNode("blendColors", name="blendORE_IK_Up_" + whichArm)
    jIK_SC_Up.rotate >> blendORE_IK_Up.color2
    jIK_RP_Up.rotate >> blendORE_IK_Up.color1
    blendORE_IK_Up.output >> jIK_orig_Up.rotate
    cont_IK_hand.polevector >> blendORE_IK_Up.blender

    blendPOS_IK_Up = pm.createNode("blendColors", name="blendPOS_IK_Up_" + whichArm)
    jIK_SC_Up.translate >> blendPOS_IK_Up.color2
    jIK_RP_Up.translate >> blendPOS_IK_Up.color1
    blendPOS_IK_Up.output >> jIK_orig_Up.translate
    cont_IK_hand.polevector >> blendPOS_IK_Up.blender

    blendORE_IK_Low = pm.createNode("blendColors", name="blendORE_IK_Low_" + whichArm)
    jIK_SC_Low.rotate >> blendORE_IK_Low.color2
    jIK_RP_Low.rotate >> blendORE_IK_Low.color1
    blendORE_IK_Low.output >> jIK_orig_Low.rotate
    cont_IK_hand.polevector >> blendORE_IK_Low.blender

    blendPOS_IK_Low = pm.createNode("blendColors", name="blendPOS_IK_Low_" + whichArm)
    jIK_SC_Low.translate >> blendPOS_IK_Low.color2
    jIK_RP_Low.translate >> blendPOS_IK_Low.color1
    blendPOS_IK_Low.output >> jIK_orig_Low.translate
    cont_IK_hand.polevector >> blendPOS_IK_Low.blender

    blendORE_IK_LowEnd = pm.createNode("blendColors", name="blendORE_IK_LowEnd_" + whichArm)
    jIK_SC_LowEnd.rotate >> blendORE_IK_LowEnd.color2
    jIK_RP_LowEnd.rotate >> blendORE_IK_LowEnd.color1
    blendORE_IK_LowEnd.output >> jIK_orig_LowEnd.rotate
    cont_IK_hand.polevector >> blendORE_IK_LowEnd.blender

    blendPOS_IK_LowEnd = pm.createNode("blendColors", name="blendPOS_IK_LowEnd_" + whichArm)
    jIK_SC_LowEnd.translate >> blendPOS_IK_LowEnd.color2
    jIK_RP_LowEnd.translate >> blendPOS_IK_LowEnd.color1
    blendPOS_IK_LowEnd.output >> jIK_orig_LowEnd.translate
    cont_IK_hand.polevector >> blendPOS_IK_LowEnd.blender

    poleVector_Rvs = pm.createNode("reverse", name="poleVector_Rvs_" + whichArm)
    cont_IK_hand.polevector >> poleVector_Rvs.inputX
    cont_IK_hand.polevector >> cont_Pole.v

    ### Shoulder Controller
    shouldercontScale = (initShoulderDist / 2, initShoulderDist / 2, initShoulderDist / 2,)
    cont_Shoulder = icon.shoulder("cont_Shoulder_" + whichArm, shouldercontScale)

    if whichArm == "r_arm":
        pm.setAttr(cont_Shoulder.scaleY, -1)
        pm.makeIdentity(cont_Shoulder, a=True, t=False, r=False, s=True)
    pm.closeCurve(cont_Shoulder, ch=0, ps=0, rpo=1, bb=0.5, bki=0, p=0.1)
    pm.delete(cont_Shoulder, ch=True)

    cont_Shoulder_OFF = extra.createUpGrp(cont_Shoulder, "OFF")
    cont_Shoulder_ORE = extra.createUpGrp(cont_Shoulder, "ORE")
    cont_Shoulder_POS = extra.createUpGrp(cont_Shoulder, "POS")

    extra.alignTo(cont_Shoulder_OFF, "jInit_Shoulder_" + whichArm, 2)

    if whichArm == "r_arm":
        pm.makeIdentity(cont_Shoulder, a=True)
        pm.setAttr(cont_Shoulder_ORE.rotateX, -180)

    pm.select(cont_Shoulder)
    pm.addAttr(shortName="autoTwist", longName="Auto_Twist", defaultValue=1.0, minValue=0.0, maxValue=1.0, at="float",
               k=True)
    pm.addAttr(shortName="manualTwist", longName="Manual_Twist", defaultValue=0.0, at="float", k=True)
    pm.select(d=True)

    pm.parent(jIK_orig_Up, masterRoot)
    pm.parent(jIK_SC_Up, masterRoot)
    pm.parent(jIK_RP_Up, masterRoot)

    pm.select(cont_Shoulder)

    pm.makeIdentity(a=True)

    jDef_paCon = pm.parentConstraint(cont_Shoulder, jDef_Shoulder, mo=True)

    ###########################
    ######### FK ARM ##########
    ###########################

    pm.select(d=True)
    jFK_Up = pm.joint(name="jFK_Up_" + whichArm, p=pm.PyNode("jInit_Up_" + whichArm).getTranslation(space="world"),
                      radius=1.0)
    jFK_Low = pm.joint(name="jFK_Low_" + whichArm, p=pm.PyNode("jInit_Low_" + whichArm).getTranslation(space="world"),
                       radius=1.0)
    jFK_LowEnd = pm.joint(name="jFK_LowEnd_" + whichArm,
                          p=pm.PyNode("jInit_LowEnd_" + whichArm).getTranslation(space="world"), radius=1.0)

    pm.joint(jFK_Up, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(jFK_Low, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(jFK_LowEnd, e=True, zso=True, oj="xyz", sao="yup")

    ### Create Controller Curves
    scalecontFkUpArm = (initUpperArmDist / 8, initUpperArmDist / 2, initUpperArmDist / 8)
    cont_FK_UpArm = icon.cube("cont_FK_UpArm_" + whichArm, scalecontFkUpArm)
    # cont_FK_UpArm=pm.curve(name="cont_FK_UpArm_"+whichArm, d=1,p=[(-1,1,1), (-1,1,-1), (1,1,-1), (1,1,1), (-1,1,1), (-1,-1,1), (-1,-1,-1), (-1,1,-1), (-1,1,1), (-1,-1,1), (1,-1,1), (1,1,1), (1,1,-1), (1,-1,-1), (1,-1,1), (1,-1,-1), (-1,-1,-1)],k= [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16])
    # pm.setAttr(cont_FK_UpArm.scale, (pm.getAttr(jFK_Low.translateX)/8,pm.getAttr(jFK_Low.translateX)/2,pm.getAttr(jFK_Low.translateX)/8))
    # pm.makeIdentity(cont_FK_UpArm, a=True)

    cont_FK_UpArm_OFF = extra.createUpGrp(cont_FK_UpArm, "OFF")
    cont_FK_UpArm_ORE = extra.createUpGrp(cont_FK_UpArm, "ORE")
    if whichArm == "r_arm":
        pm.setAttr(cont_FK_UpArm_ORE.rotateX, -180)

    temp_PoCon = pm.pointConstraint(jFK_Up, jFK_Low, cont_FK_UpArm_OFF)
    pm.delete(temp_PoCon)
    temp_AimCon = pm.aimConstraint(jFK_Low, cont_FK_UpArm_OFF, o=(90, 90, 0), u=(0, 1, 0))
    pm.delete(temp_AimCon)

    PvTarget = pm.PyNode("jInit_Up_" + whichArm).getTranslation(space="world")
    pm.xform(cont_FK_UpArm, piv=PvTarget, ws=True)
    pm.xform(cont_FK_UpArm_ORE, piv=PvTarget, ws=True)
    pm.xform(cont_FK_UpArm_OFF, piv=PvTarget, ws=True)

    pm.makeIdentity(a=True, t=True, r=False, s=True)
    pm.parent(cont_FK_UpArm, cont_FK_UpArm_ORE)

    cont_FK_UpArm.scaleY >> jFK_Up.scaleX

    scalecontFkLowArm = (initLowerArmDist / 8, initLowerArmDist / 2, initLowerArmDist / 8)

    cont_FK_LowArm = icon.cube("cont_FK_LowArm_" + whichArm, scalecontFkLowArm)

    # cont_FK_LowArm=pm.curve(name="cont_FK_LowArm_"+whichArm, d=1,p=[(-1,1,1), (-1,1,-1), (1,1,-1), (1,1,1), (-1,1,1), (-1,-1,1), (-1,-1,-1), (-1,1,-1), (-1,1,1), (-1,-1,1), (1,-1,1), (1,1,1), (1,1,-1), (1,-1,-1), (1,-1,1), (1,-1,-1), (-1,-1,-1)],k= [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16])
    # pm.setAttr(cont_FK_LowArm.scale, (pm.getAttr(jFK_LowEnd.translateX)/8,pm.getAttr(jFK_LowEnd.translateX)/2,pm.getAttr(jFK_LowEnd.translateX)/8))
    # pm.makeIdentity(cont_FK_LowArm, a=True)

    cont_FK_LowArm_OFF = extra.createUpGrp(cont_FK_LowArm, "OFF")
    cont_FK_LowArm_ORE = extra.createUpGrp(cont_FK_LowArm, "ORE")
    if whichArm == "r_arm":
        pm.setAttr(cont_FK_LowArm_ORE.rotateX, -180)

    temp_PoCon = pm.pointConstraint(jFK_Low, jFK_LowEnd, cont_FK_LowArm_OFF)
    pm.delete(temp_PoCon)
    temp_AimCon = pm.aimConstraint(jFK_LowEnd, cont_FK_LowArm_OFF, o=(90, 90, 0), u=(0, 1, 0))
    pm.delete(temp_AimCon)

    pm.makeIdentity(a=True, t=True, r=False, s=True)

    PvTarget = pm.PyNode("jInit_Low_" + whichArm).getTranslation(space="world")
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

    cont_FK_IKList = icon.fkikSwitch(("cont_FK_IK_" + whichArm), (iconScale, iconScale, iconScale))
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

    cont_FK_IK.fk_ik >> cont_IK_hand.visibility

    extra.alignTo(cont_FK_IK, "jInit_LowEnd_" + whichArm, 2)

    pm.move(cont_FK_IK, (0, iconScale * 2, 0), r=True)

    cont_FK_IK_POS = extra.createUpGrp(cont_FK_IK, "POS")

    ### Create MidLock controller

    midcontScale = (initLowerArmDist / 4, initLowerArmDist / 4, initLowerArmDist / 4)
    cont_midLock = icon.star("cont_mid_" + whichArm, midcontScale, normal=(1, 0, 0))
    # cont_midLock=pm.circle(name="cont_mid_"+whichArm, nr=(1,0,0), ch=0)
    # pm.rebuildCurve(cont_midLock, s=12, ch=0)
    # pm.select(cont_midLock[0].cv[0],cont_midLock[0].cv[2],cont_midLock[0].cv[4],cont_midLock[0].cv[6],cont_midLock[0].cv[8],cont_midLock[0].cv[10])
    # pm.scale(0.5, 0.5, 0.5)
    # pm.select(d=True)
    # pm.setAttr(cont_midLock[0].scale, (midcontScale))
    # pm.makeIdentity(cont_midLock, a=True)

    cont_midLock_POS = extra.createUpGrp(cont_midLock, "POS")
    cont_midLock_AVE = extra.createUpGrp(cont_midLock, "AVE")
    extra.alignTo(cont_midLock_POS, "jInit_Low_" + whichArm, 0)

    midLock_paConWeight = pm.parentConstraint(jIK_orig_Up, jFK_Up, cont_midLock_POS, mo=True)
    cont_FK_IK.fk_ik >> (midLock_paConWeight + "." + jIK_orig_Up + "W0")
    fk_ik_rvs.outputX >> (midLock_paConWeight + "." + jFK_Up + "W1")

    midLock_poConWeight = pm.pointConstraint(jIK_orig_Low, jFK_Low, cont_midLock_AVE, mo=False)
    cont_FK_IK.fk_ik >> (midLock_poConWeight + "." + jIK_orig_Low + "W0")
    fk_ik_rvs.outputX >> (midLock_poConWeight + "." + jFK_Low + "W1")

    midLock_xBln = pm.createNode("multiplyDivide", name="midLock_xBln_" + whichArm)

    midLock_rotXsw = pm.createNode("blendTwoAttr", name="midLock_rotXsw_" + whichArm)
    jIK_orig_Low.rotateY >> midLock_rotXsw.input[0]
    jFK_Low.rotateY >> midLock_rotXsw.input[1]
    fk_ik_rvs.outputX >> midLock_rotXsw.attributesBlender

    midLock_rotXsw.output >> midLock_xBln.input1Z

    pm.setAttr(midLock_xBln.input2Z, 0.5)
    midLock_xBln.outputZ >> cont_midLock_AVE.rotateY

    ### Create Midlock

    midLock = pm.spaceLocator(name="midLock_" + whichArm)
    pm.parentConstraint(midLock, jDef_midArm)
    #pm.scaleConstraint(midLock, jDef_midArm)
    extra.alignTo(midLock, cont_midLock, 0)

    pm.parentConstraint(cont_midLock, midLock, mo=False)

    ### Create End Lock
    endLock = pm.spaceLocator(name="endLock_" + whichArm)
    extra.alignTo(endLock, "jInit_LowEnd_" + whichArm, 2)
    endLock_Ore = extra.createUpGrp(endLock, "Ore")
    endLock_Pos = extra.createUpGrp(endLock, "Pos")
    endLock_Twist = extra.createUpGrp(endLock, "Twist")

    endLockWeight = pm.pointConstraint(jIK_orig_LowEnd, jFK_LowEnd, endLock_Pos, mo=False)
    cont_FK_IK.fk_ik >> (endLockWeight + "." + jIK_orig_LowEnd + "W0")
    fk_ik_rvs.outputX >> (endLockWeight + "." + jFK_LowEnd + "W1")

    pm.parentConstraint(endLock, cont_FK_IK_POS, mo=True)
    pm.parent(endLock_Ore, scaleGrp)

    endLockRot = pm.parentConstraint(IK_parentGRP, jFK_Low, endLock_Twist, st=("x", "y", "z"), mo=True)
    cont_FK_IK.fk_ik >> (endLockRot + "." + IK_parentGRP + "W0")
    fk_ik_rvs.outputX >> (endLockRot + "." + jFK_Low + "W1")

    ###################################
    #### CREATE DEFORMATION JOINTS ####
    ###################################

    # UPPERARM RIBBON

    ribbonConnections_upperArm = cr.createRibbon("jInit_Up_" + whichArm, "jInit_Low_" + whichArm, "up_" + whichArm, 0)
    startPos_rbnUpper = ribbonConnections_upperArm[0]
    endPos_rbnUpper = ribbonConnections_upperArm[1]
    scaleGrp_rbnUpper = ribbonConnections_upperArm[2]
    nonScaleGrp_rbnUpper = ribbonConnections_upperArm[3]
    deformerJoints_rbnUpper = ribbonConnections_upperArm[4]
    middleCont_rbnUpper = ribbonConnections_upperArm[5]
    toHide_rbnUpper = ribbonConnections_upperArm[6]

    ribbonStart_paCon_upperArm_Start = pm.parentConstraint(startLock, startPos_rbnUpper, mo=True)
    ribbonStart_paCon_upperArm_End = pm.parentConstraint(midLock, endPos_rbnUpper, mo=True)

    pm.scaleConstraint(scaleGrp, scaleGrp_rbnUpper)

    # AUTO AND MANUAL TWIST

    # auto
    autoTwist = pm.createNode("multiplyDivide", name="autoTwist_" + whichArm)
    cont_Shoulder.autoTwist >> autoTwist.input2X
    ribbonStart_paCon_upperArm_Start.constraintRotate >> autoTwist.input1

    ###!!! The parent constrain override should be disconnected like this
    pm.disconnectAttr(ribbonStart_paCon_upperArm_Start.constraintRotateX, startPos_rbnUpper.rotateX)

    # manual
    AddManualTwist = pm.createNode("plusMinusAverage", name=("AddManualTwist_UpperArm_" + whichArm))
    autoTwist.output >> AddManualTwist.input3D[0]
    cont_Shoulder.manualTwist >> AddManualTwist.input3D[1].input3Dx

    # connect to the joint
    AddManualTwist.output3D >> startPos_rbnUpper.rotate

    # LOWERARM RIBBON

    ribbonConnections_lowerArm = cr.createRibbon("jInit_Low_" + whichArm, "jInit_LowEnd_" + whichArm, "low_" + whichArm,
                                                 0)
    startPos_rbnLower = ribbonConnections_lowerArm[0]
    endPos_rbnLower = ribbonConnections_lowerArm[1]
    scaleGrp_rbnLower = ribbonConnections_lowerArm[2]
    nonScaleGrp_rbnLower = ribbonConnections_lowerArm[3]
    deformerJoints_rbnLower = ribbonConnections_lowerArm[4]
    middleCont_rbnLower = ribbonConnections_lowerArm[5]
    toHide_rbnLower = ribbonConnections_lowerArm[6]

    ribbonStart_paCon_lowerArm_Start = pm.parentConstraint(midLock, startPos_rbnLower, mo=True)
    ribbonStart_paCon_lowerArm_End = pm.parentConstraint(endLock, endPos_rbnLower, mo=True)

    pm.scaleConstraint(scaleGrp, scaleGrp_rbnLower)

    # AUTO AND MANUAL TWIST

    # auto
    autoTwist = pm.createNode("multiplyDivide", name="autoTwist_" + whichArm)
    cont_FK_IK.autoTwist >> autoTwist.input2X
    ribbonStart_paCon_lowerArm_End.constraintRotate >> autoTwist.input1

    ###!!! The parent constrain override should be disconnected like this
    pm.disconnectAttr(ribbonStart_paCon_lowerArm_End.constraintRotateX, endPos_rbnLower.rotateX)

    # manual
    AddManualTwist = pm.createNode("plusMinusAverage", name=("AddManualTwist_LowerArm_" + whichArm))
    autoTwist.output >> AddManualTwist.input3D[0]
    cont_FK_IK.manualTwist >> AddManualTwist.input3D[1].input3Dx

    # connect to the joint
    AddManualTwist.output3D >> endPos_rbnLower.rotate

    ###############################################
    ################### HAND ######################
    ###############################################

    ### Hand Controllers

    FKcontScale = (initLowerArmDist / 5, initLowerArmDist / 5, initLowerArmDist / 5)
    cont_FK_Hand = icon.cube("cont_FK_Hand_" + whichArm, FKcontScale)
    extra.alignTo(cont_FK_Hand, endLock, 2)

    cont_FK_Hand_OFF = extra.createUpGrp(cont_FK_Hand, "OFF")
    cont_FK_Hand_POS = extra.createUpGrp(cont_FK_Hand, "POS")
    cont_FK_Hand_ORE = extra.createUpGrp(cont_FK_Hand, "ORE")

    handLock = pm.spaceLocator(
        name="handLock_" + whichArm)  ## Bu iki satir r arm mirror posing icin dondurulse bile dogru bir weighted constraint yapilmasi icin araya bir node olusturuyor.
    extra.alignTo(handLock, cont_FK_Hand_ORE, 0)

    if whichArm == "r_arm":
        pm.setAttr(cont_FK_Hand_ORE.rotateX, -180)

    pm.parentConstraint(cont_FK_Hand, handLock, mo=True)  ## Olusturulan ara node baglanir
    ####################
    ## CREATE FINGERS ##
    ####################

    if whichArm == "r_arm":
        mirror = True
    else:
        mirror = False
    handRoot = pm.PyNode("jInit_LowEnd_" + whichArm)
    fingersReturn = cf.rigFingers(handRoot, cont_FK_IK, whichArm, mirror)
    handMaster = fingersReturn[0]
    handConts = fingersReturn[1]
    handJoints = fingersReturn[2]

    pm.pointConstraint(endLock, handMaster, mo=True)
    pm.parentConstraint(cont_FK_LowArm_OFF, cont_FK_Hand_POS, mo=True)
    handOriCon = pm.orientConstraint(cont_IK_hand, handLock, handMaster, mo=False)
    cont_FK_IK.fk_ik >> (handOriCon + "." + cont_IK_hand + "W0")
    fk_ik_rvs.outputX >> (handOriCon + "." + handLock + "W1")
    fk_ik_rvs.outputX >> cont_FK_Hand.v

    handScaCon = pm.scaleConstraint(cont_IK_hand, cont_FK_Hand, handMaster, mo=False)
    cont_FK_IK.fk_ik >> (handScaCon + "." + cont_IK_hand + "W0")
    fk_ik_rvs.outputX >> (handScaCon + "." + cont_FK_Hand + "W1")

    ### FINAL ROUND UP

    pm.select(armStart)

    pm.parent(startLock_Ore, scaleGrp)
    pm.parent(armStart, scaleGrp)
    pm.parent(armEnd, scaleGrp)
    pm.parent(IK_parentGRP, scaleGrp)
    pm.parent(cont_Shoulder_OFF, scaleGrp)
    pm.parent(cont_FK_UpArm_OFF, scaleGrp)
    pm.parent(cont_FK_LowArm_OFF, scaleGrp)
    pm.parent(cont_FK_Hand_OFF, scaleGrp)
    pm.parent(midLock, scaleGrp)
    pm.parent(cont_midLock_POS, scaleGrp)
    pm.parent(cont_Pole_OFF, scaleGrp)
    pm.parent(jDef_midArm, scaleGrp)

    pm.parent(scaleGrp_rbnUpper, nonScaleGrp)
    pm.parent(nonScaleGrp_rbnUpper, nonScaleGrp)

    pm.parent(scaleGrp_rbnLower, nonScaleGrp)
    pm.parent(nonScaleGrp_rbnLower, nonScaleGrp)

    pm.parent(jDef_Shoulder, scaleGrp)

    pm.parent(handLock, scaleGrp)
    pm.parent(masterRoot, scaleGrp)
    pm.parent(jFK_Up, scaleGrp)
    pm.parent(cont_FK_IK_POS, scaleGrp)
    pm.parent(handMaster, scaleGrp)

    ## CONNECT RIG VISIBILITES

    # Tweak controls
    tweakControls=(middleCont_rbnUpper, middleCont_rbnLower, cont_midLock)

    for i in tweakControls:
        cont_FK_IK.tweakControls >> i.v

    # Hand controls
    for finger in handConts:
        for i in finger:
            cont_FK_IK.fingerControls >> i.v

    pm.addAttr(scaleGrp, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True)
    pm.addAttr(scaleGrp, at="bool", ln="Joints_Visibility", sn="jointVis", defaultValue=True)
    pm.addAttr(scaleGrp, at="bool", ln="Rig_Visibility", sn="rigVis", defaultValue=False)
    # make the created attributes visible in the channelbox
    pm.setAttr(scaleGrp.contVis, cb=True)
    pm.setAttr(scaleGrp.jointVis, cb=True)
    pm.setAttr(scaleGrp.rigVis, cb=True)

    nodesContVis = [cont_Pole_OFF, cont_Shoulder_OFF, cont_IK_hand_OFF, cont_FK_Hand_OFF, cont_FK_IK_POS,
                    cont_FK_LowArm_OFF, cont_FK_UpArm_OFF, scaleGrp_rbnLower, scaleGrp_rbnUpper, cont_midLock_POS]
    nodesJointVis = [jDef_midArm, jDef_paCon, jDef_Shoulder]
    nodesJointVisLists = [deformerJoints_rbnLower, deformerJoints_rbnUpper, nodesJointVis ]
    nodesRigVis = [endLock_Ore, startLock_Ore, armStart, armEnd, IK_parentGRP, midLock, masterRoot, jFK_Up, handLock,
                   (handMaster.getShape())]

    # global Cont visibilities


    for i in nodesContVis:
        scaleGrp.contVis >> i.v
    for finger in handConts:
        for i in finger:
            # reserve the controllers visibility for finger controls visibility on FK_IK switch
            ek = i.getParent()
            scaleGrp.contVis >> ek.v

    # global Joint visibilities
    for lst in nodesJointVisLists:
        for j in lst:
            scaleGrp.jointVis >> j.v

    for lst in handJoints:
        for j in lst:
            scaleGrp.jointVis >> j.v

    # global Rig visibilities
    for i in nodesRigVis:
        scaleGrp.rigVis >> i.v
    for i in toHide_rbnLower:
        scaleGrp.rigVis >> i.v
    for i in toHide_rbnUpper:
        scaleGrp.rigVis >> i.v

    pm.setAttr(scaleGrp.rigVis, 0)

    # FOOL PROOFING

    extra.lockAndHide(cont_IK_hand, ["v"])
    extra.lockAndHide(cont_midLock, ["sx", "sy", "sz", "v"])
    extra.lockAndHide(cont_FK_IK, ["sx", "sy", "sz", "v"])
    extra.lockAndHide(cont_FK_Hand, ["tx", "ty", "tz", "v"])
    extra.lockAndHide(cont_FK_LowArm, ["tx", "ty", "tz", "sx", "sz", "v"])
    extra.lockAndHide(cont_FK_UpArm, ["tx", "ty", "tz", "sx", "sz", "v"])
    extra.lockAndHide(cont_Shoulder, ["sx", "sy", "sz", "v"])
    for finger in handConts:
        for eklem in finger:
            extra.lockAndHide(eklem, ["sx", "sy", "sz"])

    # COLOR CODING

    if whichArm == "l_arm":
        index = 13  ##Red color index
        indexMin = 9  ##Magenta color index
    else:
        index = 6  ##Blue Color index
        indexMin = 18

    extra.colorize(cont_Shoulder, index)
    extra.colorize(cont_IK_hand, index)
    extra.colorize(cont_Pole, index)
    extra.colorize(cont_FK_IK, index)
    extra.colorize(cont_FK_UpArm, index)
    extra.colorize(cont_FK_LowArm, index)
    extra.colorize(cont_FK_Hand, index)
    for i in handConts:
        extra.colorize(i, indexMin)

    extra.colorize(cont_midLock, indexMin)
    extra.colorize(middleCont_rbnUpper, indexMin)
    extra.colorize(middleCont_rbnLower, indexMin)

    # RETURN
    # return [Spine_Connection, IK_Controller, IK Controller OFF, Pole_Vector, Do_Not_Touch_Data, nodesContVis]
    returnTuple = (scaleGrp, cont_IK_hand, cont_IK_hand_OFF, cont_Pole, nonScaleGrp, nodesContVis)
    return returnTuple
