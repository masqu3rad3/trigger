import pymel.core as pm
import sys
path='C:/Users/Arda/Documents/maya/2017/scripts/tik_autorigger'
if not path in sys.path:
    sys.path.append(path)

import extraProcedures as extra
reload(extra)
import createRibbon as cr
reload(cr)

#whichArm="l_arm"
###########################
######### IK ARM ##########
###########################

def createArm(whichArm):
    initBones=pm.ls("jInit*"+whichArm)
    if (len(initBones)<28):
         pm.error("Some or all Arm Init Bones are missing (or Renamed)")
         return
    ##Groups
    scaleGrp=pm.group(name="scaleGrp_"+whichArm, em=True)
    extra.alignTo(scaleGrp, "jInit_Shoulder_"+whichArm, 0)
    nonScaleGrp=pm.group(name="NonScaleGrp_"+whichArm, em=True)
    
    masterRoot=pm.group(em=True, name="masterRoot_"+whichArm)
    extra.alignTo(masterRoot, "jInit_Shoulder_"+whichArm,0)
    pm.makeIdentity(a=True)
    
    masterIK=pm.spaceLocator(name="masterIK_"+whichArm)
    extra.alignTo(masterIK, "jInit_LowEnd_"+whichArm,0)
    
    initUpperArmDist=extra.getDistance(pm.PyNode("jInit_Up_"+whichArm), pm.PyNode("jInit_Low_"+whichArm))
    initLowerArmDist=extra.getDistance(pm.PyNode("jInit_Low_"+whichArm), pm.PyNode("jInit_LowEnd_"+whichArm))
    
    #Shoulder Joints
    pm.select(d=True)
    jDef_Shoulder=pm.joint(name="jDef_Shoulder_"+whichArm, p=pm.PyNode("jInit_Shoulder_"+whichArm).getTranslation(space="world"), radius=1.5)
    j_ShoulderEnd=pm.joint(name="j_ShoulderEnd_"+whichArm, p=pm.PyNode("jInit_Up_"+whichArm).getTranslation(space="world"), radius=1.5)
    
    pm.select(d=True)
    jIK_orig_Up=pm.joint(name="jIK_orig_Up_"+whichArm, p=pm.PyNode("jInit_Up_"+whichArm).getTranslation(space="world"), radius=1.5)
    jIK_orig_Low=pm.joint(name="jIK_orig_Low_"+whichArm, p=pm.PyNode("jInit_Low_"+whichArm).getTranslation(space="world"), radius=1.5)
    jIK_orig_LowEnd=pm.joint(name="jIK_orig_LowEnd_"+whichArm, p=pm.PyNode("jInit_LowEnd_"+whichArm).getTranslation(space="world"), radius=1.5)        
    pm.select(d=True)
    
    jIK_SC_Up=pm.joint(name="jIK_SC_Up_"+whichArm, p=pm.PyNode("jInit_Up_"+whichArm).getTranslation(space="world"), radius=1)
    jIK_SC_Low=pm.joint(name="jIK_SC_Low_"+whichArm, p=pm.PyNode("jInit_Low_"+whichArm).getTranslation(space="world"), radius=1)
    jIK_SC_LowEnd=pm.joint(name="jIK_SC_LowEnd_"+whichArm, p=pm.PyNode("jInit_LowEnd_"+whichArm).getTranslation(space="world"), radius=1)
    pm.select(d=True)
    
    jIK_RP_Up=pm.joint(name="jIK_RP_Up_"+whichArm, p=pm.PyNode("jInit_Up_"+whichArm).getTranslation(space="world"), radius=0.7)
    jIK_RP_Low=pm.joint(name="jIK_RP_Low_"+whichArm, p=pm.PyNode("jInit_Low_"+whichArm).getTranslation(space="world"), radius=0.7)
    jIK_RP_LowEnd=pm.joint(name="jIK_RP_LowEnd_"+whichArm, p=pm.PyNode("jInit_LowEnd_"+whichArm).getTranslation(space="world"), radius=0.7)
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
    
    startLock=pm.spaceLocator(name="startLock_"+whichArm)
    extra.alignTo(startLock, pm.PyNode("jInit_Up_"+whichArm),2)
    startLock_Ore=extra.createUpGrp(startLock, "Ore")
    startLock_Pos=extra.createUpGrp(startLock, "Pos")
    startLock_Twist=extra.createUpGrp(startLock, "AutoTwist")
    
    startLockWeight=pm.parentConstraint(j_ShoulderEnd,startLock, sr=("y","z"), mo=True)
    
    ## MAKE startLock Connection
    # startLockWeight=pm.parentConstraint(jIK_orig_Up, jFK_Up, startLock, mo=True)
    # cont_FK_IK.fk_ik >> (startLockWeight+"."+jIK_orig_Up+"W0")
    # fk_ik_rvs.outputX >> (startLockWeight+"."+jFK_Up+"W1")
    
    #pm.setAttr(startLockWeight.interpType, 0)
    
    pm.parentConstraint(startLock, jIK_SC_Up, mo=True)
    pm.parentConstraint(startLock, jIK_RP_Up, mo=True)
    
    ###Create IK handles
    
    ikHandle_SC=pm.ikHandle(sj=jIK_SC_Up, ee=jIK_SC_LowEnd, name="ikHandle_SC_"+whichArm)
    ikHandle_RP=pm.ikHandle(sj=jIK_RP_Up, ee=jIK_RP_LowEnd, name="ikHandle_RP_"+whichArm, sol="ikRPsolver")
    
    ###Create Control Curve - IK
    cont_IK_hand=pm.circle(nrx=1, nry=0, nrz=0, name="cont_IK_hand_"+whichArm)
    extra.alignTo(cont_IK_hand, pm.PyNode("jInit_LowEnd_"+whichArm),2)
    
    cont_IK_hand_OFF=extra.createUpGrp(cont_IK_hand[0], "OFF")
    cont_IK_hand_ORE=extra.createUpGrp(cont_IK_hand[0], "ORE")
    
    ###Add ATTRIBUTES to the IK Hand Controller
    pm.addAttr( shortName="polevector", longName="Pole_Vector", defaultValue=0.0, minValue=0.0, maxValue=1.0, at="double", k=True)
    pm.addAttr( shortName="sUpArm", longName="Scale_Upper_Arm", defaultValue=1.0, minValue=0.0, at="double", k=True)
    pm.addAttr( shortName="sLowArm", longName="Scale_Lower_Arm", defaultValue=1.0, minValue=0.0, at="double", k=True)
    pm.addAttr( shortName="squash", longName="Squash", defaultValue=0.0, minValue=0.0, maxValue=1.0, at="double", k=True)
    pm.addAttr( shortName="stretch", longName="Stretch", defaultValue=100.0, minValue=0.0, maxValue=100.0, at="double", k=True)
    
    
    ###Create Pole Vector Curve - IK

    cont_Pole=pm.curve(name="cont_Pole_"+whichArm, d=1,p=[(-1, 0, -3), (-1, 0, -1),(-3, 0, -1), (-3, 0, 1), (-1, 0, 1), (-1, 0, 3), (1, 0, 3), (1, 0, 1), (3, 0, 1), (3, 0, -1), (1, 0, -1), (1, 0, -3), (-1, 0, -3)], k=[0,1,2,3,4,5,6,7,8,9,10,11,12])
    pm.setAttr(cont_Pole+".scale", (0.5,0.5,0.5))
    pm.rotate(cont_Pole, (90,0,0))
    pm.makeIdentity(a=True)
    tempCons=pm.pointConstraint( "jInit_Low_"+whichArm, cont_Pole, w=.1, mo=False)
    pm.delete(tempCons)
    pm.makeIdentity(a=True)
    pm.move(cont_Pole, (0,0,-5))
    pm.makeIdentity(a=True)
    
    scaleValue=(((initUpperArmDist+initLowerArmDist)/2)/10)
    pm.setAttr(cont_Pole+".scale", (scaleValue,scaleValue,scaleValue))
    pm.makeIdentity(a=True)
    pm.poleVectorConstraint(cont_Pole, "ikHandle_RP_"+whichArm)
    
    ### Create and constrain Distance Locators
    
    armStart= pm.spaceLocator(name="armStart_"+whichArm)
    pm.pointConstraint(startLock, armStart, mo=False)
    
    armEnd= pm.spaceLocator(name="armEnd_"+whichArm)
    pm.pointConstraint(masterIK, armEnd, mo=False)
    
    ### Create Nodes and Connections for Strethchy IK SC
    
    stretchOffset=pm.createNode("plusMinusAverage", name="stretchOffset_"+whichArm)
    distance_SC=pm.createNode("distanceBetween", name="distance_SC_"+whichArm)
    IK_stretch_distanceClamp=pm.createNode("clamp", name="IK_stretch_distanceClamp_"+whichArm)
    IK_stretch_stretchynessClamp=pm.createNode("clamp", name="IK_stretch_stretchynessClamp_"+whichArm)
    extraScaleMult_SC=pm.createNode("multiplyDivide", name="extraScaleMult_SC_"+whichArm)
    initialDivide_SC=pm.createNode("multiplyDivide", name="initialDivide_SC_"+whichArm)
    initialLengthMultip_SC=pm.createNode("multiplyDivide", name="initialLengthMultip_SC_"+whichArm)
    stretchAmount_SC=pm.createNode("multiplyDivide", name="stretchAmount_SC_"+whichArm)
    sumOfJLengths_SC=pm.createNode("plusMinusAverage", name="sumOfJLengths_SC_"+whichArm)
    stretchCondition_SC=pm.createNode("condition", name="stretchCondition_SC_"+whichArm)
    squashyness_SC=pm.createNode("blendColors", name="squashyness_SC_"+whichArm)
    stretchyness_SC=pm.createNode("blendColors", name="stretchyness_SC_"+whichArm)
    
    pm.setAttr(IK_stretch_stretchynessClamp+".maxR", 1)
    pm.setAttr(initialLengthMultip_SC+".input1X", initUpperArmDist)
    pm.setAttr(initialLengthMultip_SC+".input1Y", initLowerArmDist)
    
    pm.setAttr(initialDivide_SC+".operation", 2)
    pm.setAttr(stretchCondition_SC+".operation", 2)
    
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
    
    cont_IK_hand[0].rotate >> jIK_RP_Low.rotate
    
    # Stretch Attributes Controller connections
    
    cont_IK_hand[0].sUpArm >> extraScaleMult_SC.input2X
    cont_IK_hand[0].sLowArm >> extraScaleMult_SC.input2Y 
    cont_IK_hand[0].squash >> squashyness_SC.blender
    
    stretchOffset.output1D >> IK_stretch_distanceClamp.maxR
    cont_IK_hand[0].stretch >> IK_stretch_stretchynessClamp.inputR
    cont_IK_hand[0].stretch >> stretchOffset.input1D[2]
    
    IK_parentGRP=pm.group(name="IK_parentGRP_"+whichArm, em=True)
    extra.alignTo(IK_parentGRP, "jInit_LowEnd_"+whichArm,2)
    
    pm.parent(ikHandle_SC[0], IK_parentGRP)
    pm.parent(ikHandle_RP[0], IK_parentGRP)
    pm.parent(masterIK, IK_parentGRP)
    pm.parentConstraint(cont_IK_hand, IK_parentGRP, mo=True)
    
    # Create Orig Switch (Pole Vector On/Off)
    
    blendORE_IK_Up=pm.createNode("blendColors", name="blendORE_IK_Up_"+whichArm)
    jIK_SC_Up.rotate >> blendORE_IK_Up.color2
    jIK_RP_Up.rotate >> blendORE_IK_Up.color1
    blendORE_IK_Up.output >> jIK_orig_Up.rotate
    cont_IK_hand[0].polevector >> blendORE_IK_Up.blender
    
    blendPOS_IK_Up=pm.createNode("blendColors", name="blendPOS_IK_Up_"+whichArm)
    jIK_SC_Up.translate >> blendPOS_IK_Up.color2
    jIK_RP_Up.translate >> blendPOS_IK_Up.color1
    blendPOS_IK_Up.output >> jIK_orig_Up.translate
    cont_IK_hand[0].polevector >> blendPOS_IK_Up.blender
    
    blendORE_IK_Low=pm.createNode("blendColors", name="blendORE_IK_Low_"+whichArm)
    jIK_SC_Low.rotate >> blendORE_IK_Low.color2
    jIK_RP_Low.rotate >> blendORE_IK_Low.color1
    blendORE_IK_Low.output >> jIK_orig_Low.rotate
    cont_IK_hand[0].polevector >> blendORE_IK_Low.blender
    
    blendPOS_IK_Low=pm.createNode("blendColors", name="blendPOS_IK_Low_"+whichArm)
    jIK_SC_Low.translate >> blendPOS_IK_Low.color2
    jIK_RP_Low.translate >> blendPOS_IK_Low.color1
    blendPOS_IK_Low.output >> jIK_orig_Low.translate
    cont_IK_hand[0].polevector >> blendPOS_IK_Low.blender
    
    blendORE_IK_LowEnd=pm.createNode("blendColors", name="blendORE_IK_LowEnd_"+whichArm)
    jIK_SC_LowEnd.rotate >> blendORE_IK_LowEnd.color2
    jIK_RP_LowEnd.rotate >> blendORE_IK_LowEnd.color1
    blendORE_IK_LowEnd.output >> jIK_orig_LowEnd.rotate
    cont_IK_hand[0].polevector >> blendORE_IK_LowEnd.blender
    
    blendPOS_IK_LowEnd=pm.createNode("blendColors", name="blendPOS_IK_LowEnd_"+whichArm)
    jIK_SC_LowEnd.translate >> blendPOS_IK_LowEnd.color2
    jIK_RP_LowEnd.translate >> blendPOS_IK_LowEnd.color1
    blendPOS_IK_LowEnd.output >> jIK_orig_LowEnd.translate
    cont_IK_hand[0].polevector >> blendPOS_IK_LowEnd.blender
    
    poleVector_Rvs=pm.createNode("reverse", name="poleVector_Rvs_"+whichArm)
    cont_IK_hand[0].polevector >> poleVector_Rvs.inputX
    cont_IK_hand[0].polevector >> cont_Pole.v
    
    ### Shoulder Controller
    cont_Shoulder=pm.curve (d=3, p=((-3, 0, 1),(-1, 2, 1), (1, 2, 1), (3, 0, 1), (3, 0, 0),(3, 0, -1),(1, 2, -1),(-1, 2, -1),(-3, 0, -1),(-3, 0, 0)),k=(0,0,0,1,2,3,4,5,6,7,7,7),name="cont_Shoulder_"+whichArm)
    pm.rotate(cont_Shoulder, (0,90,0))
    pm.makeIdentity(cont_Shoulder, a=True)
    if whichArm=="r_arm":
        pm.setAttr(cont_Shoulder.scaleY, -1)
        pm.makeIdentity(cont_Shoulder, a=True, t=False, r=False, s=True)
    pm.closeCurve (cont_Shoulder,ch=0,ps=0,rpo=1,bb=0.5,bki=0,p=0.1)
    pm.delete(cont_Shoulder, ch=True)
    
    pm.select(cont_Shoulder)
    pm.setAttr(cont_Shoulder.scale, (initUpperArmDist/5,initUpperArmDist/5,initUpperArmDist/5))
    pm.makeIdentity(cont_Shoulder, a=True)
    cont_Shoulder_OFF=extra.createUpGrp(cont_Shoulder, "OFF")
    cont_Shoulder_ORE=extra.createUpGrp(cont_Shoulder, "ORE")
    cont_Shoulder_POS=extra.createUpGrp(cont_Shoulder, "POS")
    
    extra.alignTo(cont_Shoulder_OFF, "jInit_Shoulder_"+whichArm, 2)
    
    if whichArm=="r_arm":
        
        pm.makeIdentity(cont_Shoulder, a=True)
        pm.setAttr(cont_Shoulder_ORE.rotateX, -180)
        #pm.setAttr(cont_Shoulder_POS.scaleY, -1)
        #pm.makeIdentity(cont_Shoulder, a=True, t=False, r=False, s=True)
    pm.select(cont_Shoulder)
    pm.addAttr( shortName="autoTwist", longName="Auto_Twist", defaultValue=1.0, minValue=0.0, maxValue=1.0, at="float", k=True)
    pm.addAttr( shortName="manualTwist", longName="Manual_Twist", defaultValue=0.0, at="float", k=True)
    pm.select(d=True)
    
    pm.parent(jIK_orig_Up, masterRoot)
    pm.parent(jIK_SC_Up, masterRoot)
    pm.parent(jIK_RP_Up, masterRoot)
    
    pm.select(cont_Shoulder)
    
    pm.makeIdentity(a=True)
    
    jDef_paCon=pm.parentConstraint(cont_Shoulder, jDef_Shoulder, mo=True)
    
    ###########################
    ######### FK ARM ##########
    ###########################
    
    ###########################
    
    
    pm.select(d=True)
    jFK_Up=pm.joint(name="jFK_Up_"+whichArm, p=pm.PyNode("jInit_Up_"+whichArm).getTranslation(space="world"), radius=1.0)
    jFK_Low=pm.joint(name="jFK_Low_"+whichArm, p=pm.PyNode("jInit_Low_"+whichArm).getTranslation(space="world"), radius=1.0)
    jFK_LowEnd=pm.joint(name="jFK_LowEnd_"+whichArm, p=pm.PyNode("jInit_LowEnd_"+whichArm).getTranslation(space="world"), radius=1.0)
    
    
    pm.joint(jFK_Up, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(jFK_Low, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(jFK_LowEnd, e=True, zso=True, oj="xyz", sao="yup")
    
    ### Create Controller Curves
    
    
    cont_FK_UpArm=pm.curve(name="cont_FK_UpArm_"+whichArm, d=1,p=[(-1,1,1), (-1,1,-1), (1,1,-1), (1,1,1), (-1,1,1), (-1,-1,1), (-1,-1,-1), (-1,1,-1), (-1,1,1), (-1,-1,1), (1,-1,1), (1,1,1), (1,1,-1), (1,-1,-1), (1,-1,1), (1,-1,-1), (-1,-1,-1)],k= [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16])
    pm.setAttr(cont_FK_UpArm.scale, (pm.getAttr(jFK_Low.translateX)/8,pm.getAttr(jFK_Low.translateX)/2,pm.getAttr(jFK_Low.translateX)/8))
    pm.makeIdentity(cont_FK_UpArm, a=True)
    
    cont_FK_UpArm_OFF=extra.createUpGrp(cont_FK_UpArm, "OFF")
    cont_FK_UpArm_ORE=extra.createUpGrp(cont_FK_UpArm, "ORE")
    if whichArm=="r_arm":
        pm.setAttr(cont_FK_UpArm_ORE.rotateX, -180)
        
    temp_PoCon=pm.pointConstraint(jFK_Up, jFK_Low, cont_FK_UpArm_OFF)
    pm.delete(temp_PoCon)
    temp_AimCon=pm.aimConstraint(jFK_Low, cont_FK_UpArm_OFF, o=(90,90,0), u=(0,1,0))
    pm.delete(temp_AimCon)
    
    PvTarget=pm.PyNode("jInit_Up_"+whichArm).getTranslation(space="world")
    pm.xform(cont_FK_UpArm, piv=PvTarget, ws=True)
    pm.xform(cont_FK_UpArm_ORE, piv=PvTarget, ws=True)
    pm.xform(cont_FK_UpArm_OFF, piv=PvTarget, ws=True)
    
    pm.makeIdentity(a=True, t=True, r=False, s=True)
    pm.parent(cont_FK_UpArm, cont_FK_UpArm_ORE)
    
    cont_FK_UpArm.scaleY >> jFK_Up.scaleX
    
    cont_FK_LowArm=pm.curve(name="cont_FK_LowArm_"+whichArm, d=1,p=[(-1,1,1), (-1,1,-1), (1,1,-1), (1,1,1), (-1,1,1), (-1,-1,1), (-1,-1,-1), (-1,1,-1), (-1,1,1), (-1,-1,1), (1,-1,1), (1,1,1), (1,1,-1), (1,-1,-1), (1,-1,1), (1,-1,-1), (-1,-1,-1)],k= [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16])
    pm.setAttr(cont_FK_LowArm.scale, (pm.getAttr(jFK_LowEnd.translateX)/8,pm.getAttr(jFK_LowEnd.translateX)/2,pm.getAttr(jFK_LowEnd.translateX)/8))
    pm.makeIdentity(cont_FK_LowArm, a=True)
    
    cont_FK_LowArm_OFF=extra.createUpGrp(cont_FK_LowArm, "OFF")
    cont_FK_LowArm_ORE=extra.createUpGrp(cont_FK_LowArm, "ORE")
    if whichArm=="r_arm":
        pm.setAttr(cont_FK_LowArm_ORE.rotateX, -180)
        
    temp_PoCon=pm.pointConstraint(jFK_Low, jFK_LowEnd, cont_FK_LowArm_OFF)
    pm.delete(temp_PoCon)
    temp_AimCon=pm.aimConstraint(jFK_LowEnd, cont_FK_LowArm_OFF, o=(90,90,0), u=(0,1,0))
    pm.delete(temp_AimCon)
    
    pm.makeIdentity(a=True, t=True, r=False, s=True)
    
    PvTarget=pm.PyNode("jInit_Low_"+whichArm).getTranslation(space="world")
    pm.xform(cont_FK_LowArm, piv=PvTarget, ws=True)
    pm.xform(cont_FK_LowArm_ORE, piv=PvTarget, ws=True)
    pm.xform(cont_FK_LowArm_OFF, piv=PvTarget, ws=True)
    
    cont_FK_LowArm.scaleY >> jFK_Low.scaleX
    
    ################## // END of mod
    
    ### Create Midlock - FK
    
    
    pm.orientConstraint(cont_FK_UpArm, jFK_Up, mo=True)
    pm.pointConstraint(startLock, jFK_Up, mo=False)
    
    pm.orientConstraint(cont_FK_LowArm, jFK_Low, mo=True)
    
    pm.parentConstraint(cont_Shoulder, cont_FK_UpArm_OFF, sr=("x","y","z") ,mo=True)
    pm.parentConstraint(cont_FK_UpArm, cont_FK_LowArm_OFF, mo=True)
    
    ### Create FK IK Icon
    
    letterFK_F=pm.curve (d= 1, p= [( -8.145734, -5.011799, 0 ), ( -8.145734, 4.99286, 0 ), ( -1.059101, 4.99286, 0 ), ( -1.059101, 2.908556, 0 ), ( -5.227709, 2.908556,0 ), ( -5.227709, 1.241113, 0 ), ( -1.892823, 1.241113, 0 ), ( -1.892823, -0.843191, 0 ), ( -5.227709, -0.843191, 0 ), ( -5.227709, -5.011799, 0 ), ( -8.145734, -5.011799, 0)], k=[ 0 ,  1 ,  2 ,  3 ,  4 ,  5 ,  6 ,  7 ,  8 ,  9 ,  10 ], name="letterFK_F")
    letterFK_K=pm.curve (d= 1, p= [(  1.025203, -5.011799, 0 ), (  1.025203, 4.99286, 0 ), (  3.943228, 4.99286, 0 ), (  3.943228, 1.215065, 0 ), (  7.193445, 4.99286, 0 ), (  11.029861, 4.99286, 0 ), (  7.382331, 1.084794, 0 ), (  11.029861, -5.011799, 0 ), (  7.857814, -5.011799, 0 ), (  5.669293, -0.752001, 0 ), (  3.943228, -2.608331, 0 ), (  3.943228, -5.011799, 0 ), (  1.025203, -5.011799, 0)], k= [0 , 1 , 2 , 3 , 4 , 5 , 6 , 7 , 8 , 9 , 10 , 11 , 12], name="letterFK_K")
    
    pm.parent(letterFK_K+"Shape", letterFK_F, r=True, s=True)
    pm.delete(letterFK_K)
    
    letterFK=pm.rename(letterFK_F, "letterFK")
    
    letterIK=pm.duplicate(letterFK, name="letterIK")
    
    pm.move(-4.168608, 0, 0, "letterIKShape.cv[2]", r=True, os=True, wd=True)
    pm.move(-4.168608, 0, 0, "letterIKShape.cv[3]", r=True, os=True, wd=True)
    pm.move(-3.334886, 0, 0, "letterIKShape.cv[6]", r=True, os=True, wd=True)
    pm.move(-3.334886, 0, 0, "letterIKShape.cv[7]", r=True, os=True, wd=True)
    pm.move(2.897946, 0, 0, "letterIKShape.cv[0:10]", r=True, os=True, wd=True)
    pm.move(-1.505933, 0, 0, "letterIK_KShape.cv[0:12]", r=True, os=True, wd=True)
    
    blShape_FKtoIK=pm.blendShape(letterIK, letterFK)
    
    cont_FK_IK=pm.rename(letterFK, "cont_FK_IK_"+whichArm)
    pm.select(cont_FK_IK)
    
    ## FK-IK ICON Attributes
    pm.addAttr( shortName="fk_ik", longName="FK_IK", defaultValue=1.0, minValue=0.0, maxValue=1.0, at="float", k=True)
    pm.addAttr( shortName="autoTwist", longName="Auto_Twist", defaultValue=1.0, minValue=0.0, maxValue=1.0, at="float", k=True)
    pm.addAttr( shortName="manualTwist", longName="Manual_Twist", defaultValue=0.0, at="float", k=True)
    pm.addAttr( longName="Thumb", at="enum", en="--------", k=True) 
    pm.addAttr( shortName="thumbUpDown", longName="Thumb_Up_Down", defaultValue=0.0, at="float", k=True)
    pm.addAttr( shortName="thumbBendA", longName="Thumb_Bend_A", defaultValue=0.0, at="float", k=True)
    pm.addAttr( shortName="thumbBendB", longName="Thumb_Bend_B", defaultValue=0.0, at="float", k=True)
    pm.addAttr( shortName="spreadThumb", longName="Spread_Thumb", defaultValue=0.0, at="float", k=True)
    
    pm.addAttr( longName="Index_Finger", at="enum", en="--------", k=True) 
    pm.addAttr( shortName="indexBendA", longName="Index_Bend_A", defaultValue=0.0, at="float", k=True)
    pm.addAttr( shortName="indexBendB", longName="Index_Bend_B", defaultValue=0.0, at="float", k=True)
    pm.addAttr( shortName="indexBendC", longName="Index_Bend_C", defaultValue=0.0, at="float", k=True)
    pm.addAttr( shortName="indexSpread", longName="Index_Spread", defaultValue=0.0, at="float", k=True)
    
    pm.addAttr( longName="Middle_Finger", at="enum", en="--------", k=True) 
    pm.addAttr( shortName="middleBendA", longName="Middle_Bend_A", defaultValue=0.0, at="float", k=True)
    pm.addAttr( shortName="middleBendB", longName="Middle_Bend_B", defaultValue=0.0, at="float", k=True)
    pm.addAttr( shortName="middleBendC", longName="Middle_Bend_C", defaultValue=0.0, at="float", k=True)
    pm.addAttr( shortName="middleSpread", longName="Middle_Spread", defaultValue=0.0, at="float", k=True)
    
    pm.addAttr( longName="Ring_Finger", at="enum", en="--------", k=True) 
    pm.addAttr( shortName="ringBendA", longName="Ring_Bend_A", defaultValue=0.0, at="float", k=True)
    pm.addAttr( shortName="ringBendB", longName="Ring_Bend_B", defaultValue=0.0, at="float", k=True)
    pm.addAttr( shortName="ringBendC", longName="Ring_Bend_C", defaultValue=0.0, at="float", k=True)
    pm.addAttr( shortName="ringSpread", longName="Ring_Spread", defaultValue=0.0, at="float", k=True)
    
    pm.addAttr( longName="Pinky_Finger", at="enum", en="--------", k=True) 
    pm.addAttr( shortName="pinkyBendA", longName="Pinky_Bend_A", defaultValue=0.0, at="float", k=True)
    pm.addAttr( shortName="pinkyBendB", longName="Pinky_Bend_B", defaultValue=0.0, at="float", k=True)
    pm.addAttr( shortName="pinkyBendC", longName="Pinky_Bend_C", defaultValue=0.0, at="float", k=True)
    pm.addAttr( shortName="pinkySpread", longName="Pinky_Spread", defaultValue=0.0, at="float", k=True)
    
    pm.addAttr( shortName="rigVis", longName="Rig_Visibility", defaultValue=1, minValue=0, maxValue=1, at="long", k=True)
    
    
    fk_ik_rvs=pm.createNode("reverse", name="fk_ik_rvs"+whichArm)
    cont_FK_IK.fk_ik >> blShape_FKtoIK[0].weight[0]
    cont_FK_IK.fk_ik >> fk_ik_rvs.inputX
    
    fk_ik_rvs.outputX >> cont_FK_UpArm_ORE.visibility
    fk_ik_rvs.outputX >> cont_FK_LowArm_ORE.visibility
    
    cont_FK_IK.fk_ik >> cont_IK_hand[0].visibility
    
    pm.setAttr(cont_FK_IK+".sx", 0.1)
    pm.setAttr(cont_FK_IK+".sy", 0.1)
    pm.setAttr(cont_FK_IK+".sz", 0.1)
    
    pm.delete(letterIK)
    
    pm.select(cont_FK_IK)
    pm.makeIdentity(cont_FK_IK, a=True)
    
    logoScale=initUpperArmDist/4
    pm.setAttr(cont_FK_IK+".scale", (logoScale, logoScale, logoScale))
    pm.makeIdentity(cont_FK_IK, a=True)
    extra.alignTo(cont_FK_IK, "jInit_LowEnd_"+whichArm, 2)
    
    pm.move(cont_FK_IK, (0,logoScale*2,0), r=True)
    
    cont_FK_IK_POS=extra.createUpGrp(cont_FK_IK, "POS")
    
    
    ### Create MidLock controller
    
    contScale= extra.getDistance(pm.PyNode("jInit_Low_"+whichArm), pm.PyNode("jInit_LowEnd_"+whichArm))/3
    cont_midLock=pm.circle(name="cont_mid_"+whichArm, nr=(1,0,0), ch=0)
    pm.rebuildCurve(cont_midLock, s=12, ch=0)
    pm.select(cont_midLock[0].cv[0],cont_midLock[0].cv[2],cont_midLock[0].cv[4],cont_midLock[0].cv[6],cont_midLock[0].cv[8],cont_midLock[0].cv[10])
    pm.scale(0.5, 0.5, 0.5)
    pm.select(d=True)
    pm.setAttr(cont_midLock[0].scale, (contScale, contScale, contScale))
    pm.makeIdentity(cont_midLock, a=True)
    
    cont_midLock_POS=extra.createUpGrp(cont_midLock[0],"POS")
    cont_midLock_AVE=extra.createUpGrp(cont_midLock[0],"AVE")
    extra.alignTo(cont_midLock_POS, "jInit_Low_"+whichArm, 0)
    
    
    midLock_paConWeight=pm.parentConstraint(jIK_orig_Up, jFK_Up, cont_midLock_POS, mo=True)
    cont_FK_IK.fk_ik >> (midLock_paConWeight+"."+jIK_orig_Up+"W0")
    fk_ik_rvs.outputX >> (midLock_paConWeight+"."+jFK_Up+"W1")
    
    midLock_poConWeight=pm.pointConstraint(jIK_orig_Low, jFK_Low, cont_midLock_AVE, mo=False)
    cont_FK_IK.fk_ik >> (midLock_poConWeight+"."+jIK_orig_Low+"W0")
    fk_ik_rvs.outputX >> (midLock_poConWeight+"."+jFK_Low+"W1")
    
    midLock_xBln=pm.createNode("multiplyDivide", name="midLock_xBln_"+whichArm)
    
    midLock_rotXsw=pm.createNode("blendTwoAttr", name="midLock_rotXsw_"+whichArm)
    jIK_orig_Low.rotateY >> midLock_rotXsw.input[0]
    jFK_Low.rotateY >> midLock_rotXsw.input[1]
    fk_ik_rvs.outputX >> midLock_rotXsw.attributesBlender
    
    midLock_rotXsw.output >> midLock_xBln.input1Z
    
    pm.setAttr(midLock_xBln.input2Z, 0.5)
    midLock_xBln.outputZ >> cont_midLock_AVE.rotateY
    
    ### Create Midlock
    
    midLock=pm.spaceLocator(name="midLock_"+whichArm)
    extra.alignTo(midLock, cont_midLock, 0)
    
    pm.parentConstraint(cont_midLock, midLock, mo=False)
    
    
    ### Create End Lock
    endLock=pm.spaceLocator(name="endLock_"+whichArm)
    extra.alignTo(endLock, "jInit_LowEnd_"+whichArm, 2)
    endLock_Ore=extra.createUpGrp(endLock, "Ore")
    endLock_Pos=extra.createUpGrp(endLock, "Pos")
    endLock_Twist=extra.createUpGrp(endLock, "Twist")
    
    endLockWeight=pm.pointConstraint(jIK_orig_LowEnd, jFK_LowEnd, endLock_Pos, mo=False)
    cont_FK_IK.fk_ik >> (endLockWeight+"."+jIK_orig_LowEnd+"W0")
    fk_ik_rvs.outputX >> (endLockWeight+"."+jFK_LowEnd+"W1")
    
    pm.parentConstraint(endLock, cont_FK_IK_POS, mo=True)
    pm.parent(endLock_Ore, scaleGrp)
    
    endLockRot=pm.parentConstraint(IK_parentGRP, jFK_Low, endLock_Twist, st=("x","y","z"), mo=True)
    cont_FK_IK.fk_ik >> (endLockRot+"."+IK_parentGRP+"W0")
    fk_ik_rvs.outputX >> (endLockRot+"."+jFK_Low+"W1")
    
    
    
    ###################################
    #### CREATE DEFORMATION JOINTS ####
    ###################################
    
    # UPPERARM RIBBON
    
    ribbonConnections_upperArm=cr.createRibbon("jInit_Up_"+whichArm, "jInit_Low_"+whichArm, "up_"+whichArm, 0)
    
    ribbonStart_paCon_upperArm_Start=pm.parentConstraint(startLock, ribbonConnections_upperArm[0], mo=True)
    ribbonStart_paCon_upperArm_End=pm.parentConstraint(midLock, ribbonConnections_upperArm[1], mo=True)
    
    pm.scaleConstraint(scaleGrp,ribbonConnections_upperArm[2])
    
    # AUTO AND MANUAL TWIST
    
    #auto
    autoTwist=pm.createNode("multiplyDivide", name="autoTwist_"+whichArm)
    cont_Shoulder.autoTwist >> autoTwist.input2X
    ribbonStart_paCon_upperArm_Start.constraintRotate >> autoTwist.input1
    
    ###!!! The parent constrain override should be disconnected like this
    pm.disconnectAttr(ribbonStart_paCon_upperArm_Start.constraintRotateX, ribbonConnections_upperArm[0].rotateX)
    
    #manual
    AddManualTwist=pm.createNode("plusMinusAverage", name=("AddManualTwist_UpperArm_"+whichArm))
    autoTwist.output >> AddManualTwist.input3D[0]
    cont_Shoulder.manualTwist >> AddManualTwist.input3D[1].input3Dx
    
    #connect to the joint
    AddManualTwist.output3D >> ribbonConnections_upperArm[0].rotate
    
    # LOWERARM RIBBON
    
    ribbonConnections_lowerArm=cr.createRibbon("jInit_Low_"+whichArm, "jInit_LowEnd_"+whichArm, "low_"+whichArm, 0)

    ribbonStart_paCon_lowerArm_Start=pm.parentConstraint(midLock, ribbonConnections_lowerArm[0], mo=True)
    ribbonStart_paCon_lowerArm_End=pm.parentConstraint(endLock, ribbonConnections_lowerArm[1], mo=True)
    
    pm.scaleConstraint(scaleGrp,ribbonConnections_lowerArm[2])
    
    # AUTO AND MANUAL TWIST
    
    #auto
    autoTwist=pm.createNode("multiplyDivide", name="autoTwist_"+whichArm)
    cont_FK_IK.autoTwist >> autoTwist.input2X
    ribbonStart_paCon_lowerArm_End.constraintRotate >> autoTwist.input1
    
    ###!!! The parent constrain override should be disconnected like this
    pm.disconnectAttr(ribbonStart_paCon_lowerArm_End.constraintRotateX, ribbonConnections_lowerArm[1].rotateX)
    
    #manual
    AddManualTwist=pm.createNode("plusMinusAverage", name=("AddManualTwist_LowerArm_"+whichArm))
    autoTwist.output >> AddManualTwist.input3D[0]
    cont_FK_IK.manualTwist >> AddManualTwist.input3D[1].input3Dx
    
    #connect to the joint
    AddManualTwist.output3D >> ribbonConnections_lowerArm[1].rotate
    
    ###############################################
    ################### HAND ######################
    ###############################################
    
    handMaster=pm.spaceLocator(name="handMaster_"+whichArm)
    extra.alignTo(handMaster, endLock, 2)
    
    pm.select(d=True)
    jDef_Hand=pm.joint(name="jDef_Hand_"+whichArm, p=pm.PyNode("jInit_LowEnd_"+whichArm).getTranslation(space="world"), radius=1.0)
    
    pm.select(d=True)
    jDef_pinky00=pm.joint(name="jDef_pinky00_"+whichArm, p=pm.PyNode("jInit_pinky00_"+whichArm).getTranslation(space="world"), radius=1.0)
    jDef_pinky01=pm.joint(name="jDef_pinky01_"+whichArm, p=pm.PyNode("jInit_pinky01_"+whichArm).getTranslation(space="world"), radius=1.0)
    jDef_pinky02=pm.joint(name="jDef_pinky02_"+whichArm, p=pm.PyNode("jInit_pinky02_"+whichArm).getTranslation(space="world"), radius=1.0)
    jDef_pinky03=pm.joint(name="jDef_pinky03_"+whichArm, p=pm.PyNode("jInit_pinky03_"+whichArm).getTranslation(space="world"), radius=1.0)
    j_pinky04=pm.joint(name="j_pinky04_"+whichArm, p=pm.PyNode("jInit_pinky04_"+whichArm).getTranslation(space="world"), radius=1.0)
    
    pm.select(d=True)
    jDef_ring00=pm.joint(name="jDef_ring00_"+whichArm, p=pm.PyNode("jInit_ring00_"+whichArm).getTranslation(space="world"), radius=1.0)
    jDef_ring01=pm.joint(name="jDef_ring01_"+whichArm, p=pm.PyNode("jInit_ring01_"+whichArm).getTranslation(space="world"), radius=1.0)
    jDef_ring02=pm.joint(name="jDef_ring02_"+whichArm, p=pm.PyNode("jInit_ring02_"+whichArm).getTranslation(space="world"), radius=1.0)
    jDef_ring03=pm.joint(name="jDef_ring03_"+whichArm, p=pm.PyNode("jInit_ring03_"+whichArm).getTranslation(space="world"), radius=1.0)
    j_ring04=pm.joint(name="j_ring04_"+whichArm, p=pm.PyNode("jInit_ring04_"+whichArm).getTranslation(space="world"), radius=1.0)
    
    pm.select(d=True)
    jDef_middle00=pm.joint(name="jDef_middle00_"+whichArm, p=pm.PyNode("jInit_middle00_"+whichArm).getTranslation(space="world"), radius=1.0)
    jDef_middle01=pm.joint(name="jDef_middle01_"+whichArm, p=pm.PyNode("jInit_middle01_"+whichArm).getTranslation(space="world"), radius=1.0)
    jDef_middle02=pm.joint(name="jDef_middle02_"+whichArm, p=pm.PyNode("jInit_middle02_"+whichArm).getTranslation(space="world"), radius=1.0)
    jDef_middle03=pm.joint(name="jDef_middle03_"+whichArm, p=pm.PyNode("jInit_middle03_"+whichArm).getTranslation(space="world"), radius=1.0)
    j_middle04=pm.joint(name="j_middle04_"+whichArm, p=pm.PyNode("jInit_middle04_"+whichArm).getTranslation(space="world"), radius=1.0)
    
    pm.select(d=True)
    jDef_index00=pm.joint(name="jDef_index00_"+whichArm, p=pm.PyNode("jInit_index00_"+whichArm).getTranslation(space="world"), radius=1.0)
    jDef_index01=pm.joint(name="jDef_index01_"+whichArm, p=pm.PyNode("jInit_index01_"+whichArm).getTranslation(space="world"), radius=1.0)
    jDef_index02=pm.joint(name="jDef_index02_"+whichArm, p=pm.PyNode("jInit_index02_"+whichArm).getTranslation(space="world"), radius=1.0)
    jDef_index03=pm.joint(name="jDef_index03_"+whichArm, p=pm.PyNode("jInit_index03_"+whichArm).getTranslation(space="world"), radius=1.0)
    j_index04=pm.joint(name="j_index04_"+whichArm, p=pm.PyNode("jInit_index04_"+whichArm).getTranslation(space="world"), radius=1.0)
    
    pm.select(d=True)
    jDef_thumb00=pm.joint(name="jDef_thumb00_"+whichArm, p=pm.PyNode("jInit_thumb00_"+whichArm).getTranslation(space="world"), radius=1.0)
    jDef_thumb01=pm.joint(name="jDef_thumb01_"+whichArm, p=pm.PyNode("jInit_thumb01_"+whichArm).getTranslation(space="world"), radius=1.0)
    jDef_thumb02=pm.joint(name="jDef_thumb02_"+whichArm, p=pm.PyNode("jInit_thumb02_"+whichArm).getTranslation(space="world"), radius=1.0)
    j_thumb03=pm.joint(name="j_thumb03_"+whichArm, p=pm.PyNode("jInit_thumb03_"+whichArm).getTranslation(space="world"), radius=1.0)
    
    pm.parent(jDef_pinky00, jDef_Hand)
    pm.parent(jDef_ring00, jDef_Hand)
    pm.parent(jDef_middle00, jDef_Hand)
    pm.parent(jDef_index00, jDef_Hand)
    pm.parent(jDef_thumb00, jDef_Hand)
    
    pm.joint(jDef_Hand, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(jDef_pinky00, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(jDef_pinky01, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(jDef_pinky02, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(jDef_pinky03, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(j_pinky04, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(jDef_ring00, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(jDef_ring01, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(jDef_ring02, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(jDef_ring03, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(j_ring04, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(jDef_middle00, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(jDef_middle01, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(jDef_middle02, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(jDef_middle03, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(j_middle04, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(jDef_index00, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(jDef_index01, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(jDef_index02, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(jDef_index03, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(j_index04, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(jDef_thumb00, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(jDef_thumb01, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(jDef_thumb02, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(j_thumb03, e=True, zso=True, oj="xyz", sao="yup")
    
    pm.parent(jDef_Hand, handMaster)
    
    ### Hand Controllers
    
    cont_FK_Hand=pm.curve(name="cont_FK_Hand_"+whichArm, d=1,p=[(-1,1,1), (-1,1,-1), (1,1,-1), (1,1,1), (-1,1,1), (-1,-1,1), (-1,-1,-1), (-1,1,-1), (-1,1,1), (-1,-1,1), (1,-1,1), (1,1,1), (1,1,-1), (1,-1,-1), (1,-1,1), (1,-1,-1), (-1,-1,-1)],k= [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16])
    
    handContScale=extra.getDistance(pm.PyNode("jInit_index00_"+whichArm), pm.PyNode("jInit_index01_"+whichArm))
    pm.setAttr(cont_FK_Hand.scale, (handContScale,handContScale,handContScale))
    pm.makeIdentity(cont_FK_Hand, a=True, r=False)
    extra.alignTo(cont_FK_Hand, endLock,2)
    
    cont_FK_Hand_OFF=extra.createUpGrp(cont_FK_Hand, "OFF")
    cont_FK_Hand_POS=extra.createUpGrp(cont_FK_Hand, "POS")
    cont_FK_Hand_ORE=extra.createUpGrp(cont_FK_Hand, "ORE")
    
    handLock=pm.spaceLocator(name="handLock_"+whichArm) ## Bu iki satir r arm mirror posing icin dondurulse bile dogru bir weighted constraint yapilmasi icin araya bir node olusturuyor.
    extra.alignTo(handLock, cont_FK_Hand_ORE, 0)
    
    if whichArm=="r_arm":
        pm.setAttr(cont_FK_Hand_ORE.rotateX, -180)
        
    pm.parentConstraint(cont_FK_Hand, handLock, mo=True) ## Olusturulan ara node baglanir
    
    pm.pointConstraint(endLock, handMaster, mo=True)
    pm.parentConstraint(cont_FK_LowArm_OFF,cont_FK_Hand_POS, mo=True)
    #pm.parent(cont_FK_Hand_POS, cont_FK_LowArm)
    handOriCon=pm.orientConstraint(cont_IK_hand, handLock, handMaster, mo=False)
    cont_FK_IK.fk_ik >> (handOriCon+"."+cont_IK_hand[0]+"W0")
    fk_ik_rvs.outputX >> (handOriCon+"."+handLock+"W1")
    fk_ik_rvs.outputX >> cont_FK_Hand.v
    
    handScaCon=pm.scaleConstraint(cont_IK_hand, cont_FK_Hand, handMaster, mo=False)
    cont_FK_IK.fk_ik >> (handScaCon+"."+cont_IK_hand[0]+"W0")
    fk_ik_rvs.outputX >> (handScaCon+"."+cont_FK_Hand+"W1")
    
    
    divider=3
    ##PINKY
    handContScale00=extra.getDistance(jDef_pinky00, jDef_pinky01)
    handContScale01=extra.getDistance(jDef_pinky01, jDef_pinky02)
    handContScale02=extra.getDistance(jDef_pinky02, jDef_pinky03)
    handContScale03=extra.getDistance(jDef_pinky03, j_pinky04)
    
    cont_pinky00=pm.circle(name="cont_pinky00_"+whichArm, radius=handContScale00/divider, nr=(1,0,0))
    extra.alignTo(cont_pinky00, jDef_pinky00,0)
    cont_pinky00_OFF=extra.createUpGrp(cont_pinky00[0], "OFF")
    cont_pinky00_ORE=extra.createUpGrp(cont_pinky00[0], "ORE")
    cont_pinky00_con=extra.createUpGrp(cont_pinky00[0], "con")
    if whichArm=="r_arm":
        pm.setAttr(cont_pinky00_ORE.rotateZ, -180)
    extra.alignTo(cont_pinky00_OFF, jDef_pinky00,2)
    
    cont_pinky01=pm.circle(name="cont_pinky01_"+whichArm, radius=handContScale00/divider, nr=(1,0,0))
    extra.alignTo(cont_pinky01, jDef_pinky01,0)
    cont_pinky01_OFF=extra.createUpGrp(cont_pinky01[0], "OFF")
    cont_pinky01_ORE=extra.createUpGrp(cont_pinky01[0], "ORE")
    cont_pinky01_con=extra.createUpGrp(cont_pinky01[0], "con")
    if whichArm=="r_arm":
        pm.setAttr(cont_pinky01_ORE.rotateZ, -180)
    extra.alignTo(cont_pinky01_OFF, jDef_pinky01,2)
    
    cont_pinky02=pm.circle(name="cont_pinky02_"+whichArm, radius=handContScale00/divider, nr=(1,0,0))
    extra.alignTo(cont_pinky02, jDef_pinky02,0)
    cont_pinky02_OFF=extra.createUpGrp(cont_pinky02[0], "OFF")
    cont_pinky02_ORE=extra.createUpGrp(cont_pinky02[0], "ORE")
    cont_pinky02_con=extra.createUpGrp(cont_pinky02[0], "con")
    if whichArm=="r_arm":
        pm.setAttr(cont_pinky02_ORE.rotateZ, -180)
    extra.alignTo(cont_pinky02_OFF, jDef_pinky02,2)
    
    cont_pinky03=pm.circle(name="cont_pinky03_"+whichArm, radius=handContScale00/divider, nr=(1,0,0))
    extra.alignTo(cont_pinky03, jDef_pinky03,0)
    cont_pinky03_OFF=extra.createUpGrp(cont_pinky03[0], "OFF")
    cont_pinky03_ORE=extra.createUpGrp(cont_pinky03[0], "ORE")
    cont_pinky03_con=extra.createUpGrp(cont_pinky03[0], "con")
    if whichArm=="r_arm":
        pm.setAttr(cont_pinky03_ORE.rotateZ, -180)
    extra.alignTo(cont_pinky03_OFF, jDef_pinky03,2)
    
    pm.parent(cont_pinky03_OFF, cont_pinky02[0])
    pm.parent(cont_pinky02_OFF, cont_pinky01[0])
    pm.parent(cont_pinky01_OFF, cont_pinky00[0])
    
    pm.parentConstraint(cont_pinky00, jDef_pinky00, mo=True)
    pm.parentConstraint(cont_pinky01, jDef_pinky01, mo=True)
    pm.parentConstraint(cont_pinky02, jDef_pinky02, mo=True)
    pm.parentConstraint(cont_pinky03, jDef_pinky03, mo=True)
    # pm.scaleConstraint(cont_pinky00, jDef_pinky00, mo=True)
    # pm.scaleConstraint(cont_pinky01, jDef_pinky01, mo=True)
    # pm.scaleConstraint(cont_pinky02, jDef_pinky02, mo=True)
    # pm.scaleConstraint(cont_pinky03, jDef_pinky03, mo=True)
    
    pm.parent(cont_pinky00_OFF, handMaster)
    #######spread
    pinkySprMult=pm.createNode("multiplyDivide", name="pinkySprMult_"+whichArm)
    pm.setAttr(pinkySprMult.input1Y, 0.4)
    cont_FK_IK.pinkySpread >> pinkySprMult.input2Y 
    pinkySprMult.outputY >> cont_pinky00_con.rotateY
    
    cont_FK_IK.pinkySpread >> cont_pinky01_con.rotateY
    
    ########bend
    cont_FK_IK.pinkyBendA >> cont_pinky01_con.rotateZ
    cont_FK_IK.pinkyBendB >> cont_pinky02_con.rotateZ
    cont_FK_IK.pinkyBendC >> cont_pinky03_con.rotateZ
    
    
    ##RING
    handContScale00=extra.getDistance(jDef_ring00, jDef_ring01)
    handContScale01=extra.getDistance(jDef_ring01, jDef_ring02)
    handContScale02=extra.getDistance(jDef_ring02, jDef_ring03)
    handContScale03=extra.getDistance(jDef_ring03, j_ring04)
    
    cont_ring00=pm.circle(name="cont_ring00_"+whichArm, radius=handContScale00/divider, nr=(1,0,0))
    extra.alignTo(cont_ring00, jDef_ring00,0)
    cont_ring00_OFF=extra.createUpGrp(cont_ring00[0], "OFF")
    cont_ring00_ORE=extra.createUpGrp(cont_ring00[0], "ORE")
    cont_ring00_con=extra.createUpGrp(cont_ring00[0], "con")
    if whichArm=="r_arm":
        pm.setAttr(cont_ring00_ORE.rotateZ, -180)
    extra.alignTo(cont_ring00_OFF, jDef_ring00,2)
    
    cont_ring01=pm.circle(name="cont_ring01_"+whichArm, radius=handContScale00/divider, nr=(1,0,0))
    extra.alignTo(cont_ring01, jDef_ring01,0)
    cont_ring01_OFF=extra.createUpGrp(cont_ring01[0], "OFF")
    cont_ring01_ORE=extra.createUpGrp(cont_ring01[0], "ORE")
    cont_ring01_con=extra.createUpGrp(cont_ring01[0], "con")
    if whichArm=="r_arm":
        pm.setAttr(cont_ring01_ORE.rotateZ, -180)
    extra.alignTo(cont_ring01_OFF, jDef_ring01,2)
    
    cont_ring02=pm.circle(name="cont_ring02_"+whichArm, radius=handContScale00/divider, nr=(1,0,0))
    extra.alignTo(cont_ring02, jDef_ring02,0)
    cont_ring02_OFF=extra.createUpGrp(cont_ring02[0], "OFF")
    cont_ring02_ORE=extra.createUpGrp(cont_ring02[0], "ORE")
    cont_ring02_con=extra.createUpGrp(cont_ring02[0], "con")
    if whichArm=="r_arm":
        pm.setAttr(cont_ring02_ORE.rotateZ, -180)
    extra.alignTo(cont_ring02_OFF, jDef_ring02,2)
    
    cont_ring03=pm.circle(name="cont_ring03_"+whichArm, radius=handContScale00/divider, nr=(1,0,0))
    extra.alignTo(cont_ring03, jDef_ring03,0)
    cont_ring03_OFF=extra.createUpGrp(cont_ring03[0], "OFF")
    cont_ring03_ORE=extra.createUpGrp(cont_ring03[0], "ORE")
    cont_ring03_con=extra.createUpGrp(cont_ring03[0], "con")
    if whichArm=="r_arm":
        pm.setAttr(cont_ring03_ORE.rotateZ, -180)
    extra.alignTo(cont_ring03_OFF, jDef_ring03,2)
    
    pm.parent(cont_ring03_OFF, cont_ring02[0])
    pm.parent(cont_ring02_OFF, cont_ring01[0])
    pm.parent(cont_ring01_OFF, cont_ring00[0])
    
    pm.parentConstraint(cont_ring00, jDef_ring00, mo=True)
    pm.parentConstraint(cont_ring01, jDef_ring01, mo=True)
    pm.parentConstraint(cont_ring02, jDef_ring02, mo=True)
    pm.parentConstraint(cont_ring03, jDef_ring03, mo=True)
    # pm.scaleConstraint(cont_ring00, jDef_ring00, mo=True)
    # pm.scaleConstraint(cont_ring01, jDef_ring01, mo=True)
    # pm.scaleConstraint(cont_ring02, jDef_ring02, mo=True)
    # pm.scaleConstraint(cont_ring03, jDef_ring03, mo=True)
    
    pm.parent(cont_ring00_OFF, handMaster)
    #######spread
    ringSprMult=pm.createNode("multiplyDivide", name="ringSprMult_"+whichArm)
    pm.setAttr(ringSprMult.input1Y, 0.4)
    cont_FK_IK.ringSpread >> ringSprMult.input2Y 
    ringSprMult.outputY >> cont_ring00_con.rotateY
    
    cont_FK_IK.ringSpread >> cont_ring01_con.rotateY
    
    ########bend
    cont_FK_IK.ringBendA >> cont_ring01_con.rotateZ
    cont_FK_IK.ringBendB >> cont_ring02_con.rotateZ
    cont_FK_IK.ringBendC >> cont_ring03_con.rotateZ
    
    ##middle
    handContScale00=extra.getDistance(jDef_middle00, jDef_middle01)
    handContScale01=extra.getDistance(jDef_middle01, jDef_middle02)
    handContScale02=extra.getDistance(jDef_middle02, jDef_middle03)
    handContScale03=extra.getDistance(jDef_middle03, j_middle04)
    
    cont_middle00=pm.circle(name="cont_middle00_"+whichArm, radius=handContScale00/divider, nr=(1,0,0))
    extra.alignTo(cont_middle00, jDef_middle00,0)
    cont_middle00_OFF=extra.createUpGrp(cont_middle00[0], "OFF")
    cont_middle00_ORE=extra.createUpGrp(cont_middle00[0], "ORE")
    cont_middle00_con=extra.createUpGrp(cont_middle00[0], "con")
    if whichArm=="r_arm":
        pm.setAttr(cont_middle00_ORE.rotateZ, -180)
    extra.alignTo(cont_middle00_OFF, jDef_middle00,2)
    
    cont_middle01=pm.circle(name="cont_middle01_"+whichArm, radius=handContScale00/divider, nr=(1,0,0))
    extra.alignTo(cont_middle01, jDef_middle01,0)
    cont_middle01_OFF=extra.createUpGrp(cont_middle01[0], "OFF")
    cont_middle01_ORE=extra.createUpGrp(cont_middle01[0], "ORE")
    cont_middle01_con=extra.createUpGrp(cont_middle01[0], "con")
    if whichArm=="r_arm":
        pm.setAttr(cont_middle01_ORE.rotateZ, -180)
    extra.alignTo(cont_middle01_OFF, jDef_middle01,2)
    
    cont_middle02=pm.circle(name="cont_middle02_"+whichArm, radius=handContScale00/divider, nr=(1,0,0))
    extra.alignTo(cont_middle02, jDef_middle02,0)
    cont_middle02_OFF=extra.createUpGrp(cont_middle02[0], "OFF")
    cont_middle02_ORE=extra.createUpGrp(cont_middle02[0], "ORE")
    cont_middle02_con=extra.createUpGrp(cont_middle02[0], "con")
    if whichArm=="r_arm":
        pm.setAttr(cont_middle02_ORE.rotateZ, -180)
    extra.alignTo(cont_middle02_OFF, jDef_middle02,2)
    
    cont_middle03=pm.circle(name="cont_middle03_"+whichArm, radius=handContScale00/divider, nr=(1,0,0))
    extra.alignTo(cont_middle03, jDef_middle03,0)
    cont_middle03_OFF=extra.createUpGrp(cont_middle03[0], "OFF")
    cont_middle03_ORE=extra.createUpGrp(cont_middle03[0], "ORE")
    cont_middle03_con=extra.createUpGrp(cont_middle03[0], "con")
    if whichArm=="r_arm":
        pm.setAttr(cont_middle03_ORE.rotateZ, -180)
    extra.alignTo(cont_middle03_OFF, jDef_middle03,2)
    
    pm.parent(cont_middle03_OFF, cont_middle02[0])
    pm.parent(cont_middle02_OFF, cont_middle01[0])
    pm.parent(cont_middle01_OFF, cont_middle00[0])
    
    pm.parentConstraint(cont_middle00, jDef_middle00, mo=True)
    pm.parentConstraint(cont_middle01, jDef_middle01, mo=True)
    pm.parentConstraint(cont_middle02, jDef_middle02, mo=True)
    pm.parentConstraint(cont_middle03, jDef_middle03, mo=True)
    # pm.scaleConstraint(cont_middle00, jDef_middle00, mo=True)
    # pm.scaleConstraint(cont_middle01, jDef_middle01, mo=True)
    # pm.scaleConstraint(cont_middle02, jDef_middle02, mo=True)
    # pm.scaleConstraint(cont_middle03, jDef_middle03, mo=True)
    
    pm.parent(cont_middle00_OFF, handMaster)
    #######spread
    middleSprMult=pm.createNode("multiplyDivide", name="middleSprMult_"+whichArm)
    pm.setAttr(middleSprMult.input1Y, 0.4)
    cont_FK_IK.middleSpread >> middleSprMult.input2Y 
    middleSprMult.outputY >> cont_middle00_con.rotateY
    
    cont_FK_IK.middleSpread >> cont_middle01_con.rotateY
    
    ########bend
    cont_FK_IK.middleBendA >> cont_middle01_con.rotateZ
    cont_FK_IK.middleBendB >> cont_middle02_con.rotateZ
    cont_FK_IK.middleBendC >> cont_middle03_con.rotateZ
    
    ##index
    handContScale00=extra.getDistance(jDef_index00, jDef_index01)
    handContScale01=extra.getDistance(jDef_index01, jDef_index02)
    handContScale02=extra.getDistance(jDef_index02, jDef_index03)
    handContScale03=extra.getDistance(jDef_index03, j_index04)
    
    cont_index00=pm.circle(name="cont_index00_"+whichArm, radius=handContScale00/divider, nr=(1,0,0))
    extra.alignTo(cont_index00, jDef_index00,0)
    cont_index00_OFF=extra.createUpGrp(cont_index00[0], "OFF")
    cont_index00_ORE=extra.createUpGrp(cont_index00[0], "ORE")
    cont_index00_con=extra.createUpGrp(cont_index00[0], "con")
    if whichArm=="r_arm":
        pm.setAttr(cont_index00_ORE.rotateZ, -180)
    extra.alignTo(cont_index00_OFF, jDef_index00,2)
    
    cont_index01=pm.circle(name="cont_index01_"+whichArm, radius=handContScale00/divider, nr=(1,0,0))
    extra.alignTo(cont_index01, jDef_index01,0)
    cont_index01_OFF=extra.createUpGrp(cont_index01[0], "OFF")
    cont_index01_ORE=extra.createUpGrp(cont_index01[0], "ORE")
    cont_index01_con=extra.createUpGrp(cont_index01[0], "con")
    if whichArm=="r_arm":
        pm.setAttr(cont_index01_ORE.rotateZ, -180)
    extra.alignTo(cont_index01_OFF, jDef_index01,2)
    
    cont_index02=pm.circle(name="cont_index02_"+whichArm, radius=handContScale00/divider, nr=(1,0,0))
    extra.alignTo(cont_index02, jDef_index02,0)
    cont_index02_OFF=extra.createUpGrp(cont_index02[0], "OFF")
    cont_index02_ORE=extra.createUpGrp(cont_index02[0], "ORE")
    cont_index02_con=extra.createUpGrp(cont_index02[0], "con")
    if whichArm=="r_arm":
        pm.setAttr(cont_index02_ORE.rotateZ, -180)
    extra.alignTo(cont_index02_OFF, jDef_index02,2)
    
    cont_index03=pm.circle(name="cont_index03_"+whichArm, radius=handContScale00/divider, nr=(1,0,0))
    extra.alignTo(cont_index03, jDef_index03,0)
    cont_index03_OFF=extra.createUpGrp(cont_index03[0], "OFF")
    cont_index03_ORE=extra.createUpGrp(cont_index03[0], "ORE")
    cont_index03_con=extra.createUpGrp(cont_index03[0], "con")
    if whichArm=="r_arm":
        pm.setAttr(cont_index03_ORE.rotateZ, -180)
    extra.alignTo(cont_index03_OFF, jDef_index03,2)
    
    pm.parent(cont_index03_OFF, cont_index02[0])
    pm.parent(cont_index02_OFF, cont_index01[0])
    pm.parent(cont_index01_OFF, cont_index00[0])
    
    pm.parentConstraint(cont_index00, jDef_index00, mo=True)
    pm.parentConstraint(cont_index01, jDef_index01, mo=True)
    pm.parentConstraint(cont_index02, jDef_index02, mo=True)
    pm.parentConstraint(cont_index03, jDef_index03, mo=True)
    # pm.scaleConstraint(cont_index00, jDef_index00, mo=True)
    # pm.scaleConstraint(cont_index01, jDef_index01, mo=True)
    # pm.scaleConstraint(cont_index02, jDef_index02, mo=True)
    # pm.scaleConstraint(cont_index03, jDef_index03, mo=True)
    
    pm.parent(cont_index00_OFF, handMaster)
    #######spread
    indexSprMult=pm.createNode("multiplyDivide", name="indexSprMult_"+whichArm)
    pm.setAttr(indexSprMult.input1Y, 0.4)
    cont_FK_IK.indexSpread >> indexSprMult.input2Y 
    indexSprMult.outputY >> cont_index00_con.rotateY
    
    cont_FK_IK.indexSpread >> cont_index01_con.rotateY
    
    ########bend
    cont_FK_IK.indexBendA >> cont_index01_con.rotateZ
    cont_FK_IK.indexBendB >> cont_index02_con.rotateZ
    cont_FK_IK.indexBendC >> cont_index03_con.rotateZ
    
    ##thumb
    handContScale00=extra.getDistance(jDef_thumb00, jDef_thumb01)
    handContScale01=extra.getDistance(jDef_thumb01, jDef_thumb02)
    handContScale02=extra.getDistance(jDef_thumb02, j_thumb03)
    
    cont_thumb00=pm.circle(name="cont_thumb00_"+whichArm, radius=handContScale00/divider, nr=(1,0,0))
    extra.alignTo(cont_thumb00, jDef_thumb00,0)
    cont_thumb00_OFF=extra.createUpGrp(cont_thumb00[0], "OFF")
    cont_thumb00_ORE=extra.createUpGrp(cont_thumb00[0], "ORE")
    cont_thumb00_con=extra.createUpGrp(cont_thumb00[0], "con")
    if whichArm=="r_arm":
        pm.setAttr(cont_thumb00_ORE.rotateZ, -180)
    extra.alignTo(cont_thumb00_OFF, jDef_thumb00,2)
    
    
    cont_thumb01=pm.circle(name="cont_thumb01_"+whichArm, radius=handContScale00/divider, nr=(1,0,0))
    extra.alignTo(cont_thumb01, jDef_thumb01,0)
    cont_thumb01_OFF=extra.createUpGrp(cont_thumb01[0], "OFF")
    cont_thumb01_ORE=extra.createUpGrp(cont_thumb01[0], "ORE")
    cont_thumb01_con=extra.createUpGrp(cont_thumb01[0], "con")
    if whichArm=="r_arm":
        pm.setAttr(cont_thumb01_ORE.rotateZ, -180)
    extra.alignTo(cont_thumb01_OFF, jDef_thumb01,2)
    
    
    cont_thumb02=pm.circle(name="cont_thumb02_"+whichArm, radius=handContScale00/divider, nr=(1,0,0))
    extra.alignTo(cont_thumb02, jDef_thumb02,0)
    cont_thumb02_OFF=extra.createUpGrp(cont_thumb02[0], "OFF")
    cont_thumb02_ORE=extra.createUpGrp(cont_thumb02[0], "ORE")
    cont_thumb02_con=extra.createUpGrp(cont_thumb02[0], "con")
    if whichArm=="r_arm":
        pm.setAttr(cont_thumb02_ORE.rotateZ, -180)
    extra.alignTo(cont_thumb02_OFF, jDef_thumb02,2)
    
    pm.parent(cont_thumb02_OFF, cont_thumb01[0])
    pm.parent(cont_thumb01_OFF, cont_thumb00[0])
    
    pm.parentConstraint(cont_thumb00, jDef_thumb00, mo=True)
    pm.parentConstraint(cont_thumb01, jDef_thumb01, mo=True)
    pm.parentConstraint(cont_thumb02, jDef_thumb02, mo=True)
    # pm.scaleConstraint(cont_thumb00, jDef_thumb00, mo=True)
    # pm.scaleConstraint(cont_thumb01, jDef_thumb01, mo=True)
    # pm.scaleConstraint(cont_thumb02, jDef_thumb02, mo=True)
    
    pm.parent(cont_thumb00_OFF, handMaster)
    
    #######spread
    thumbSprMult=pm.createNode("multiplyDivide", name="thumbSprMult_"+whichArm)
    pm.setAttr(thumbSprMult.input1Y, 0.4)
    cont_FK_IK.spreadThumb >> thumbSprMult.input2Y 
    thumbSprMult.outputY >> cont_thumb01_con.rotateY
    
    cont_FK_IK.spreadThumb >> cont_thumb00_con.rotateY
    
    ########bend
    cont_FK_IK.thumbBendA >> cont_thumb01_con.rotateZ
    cont_FK_IK.thumbBendB >> cont_thumb02_con.rotateZ
    
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
    #pm.parent(cont_IK_hand_OFF, scaleGrp)
    pm.parent(midLock, scaleGrp)
    pm.parent(cont_midLock_POS, scaleGrp)
    
    pm.parent(ribbonConnections_upperArm[2], nonScaleGrp)
    pm.parent(ribbonConnections_upperArm[3], nonScaleGrp)
    
    pm.parent(ribbonConnections_lowerArm[2], nonScaleGrp)
    pm.parent(ribbonConnections_lowerArm[3], nonScaleGrp)
    
    pm.parent(jDef_Shoulder, scaleGrp)
    
    pm.parent(handLock, scaleGrp)
    pm.parent(masterRoot, scaleGrp)
    pm.parent(jFK_Up, scaleGrp)
    pm.parent(cont_FK_IK_POS, scaleGrp)
    pm.parent(handMaster, scaleGrp)
    # ### Animator Fool Proofing
    
    extra.lockAndHide(cont_IK_hand[0], ["v"])
    extra.lockAndHide(cont_midLock[0], ["sx", "sy", "sz", "v"])
    extra.lockAndHide(cont_FK_IK, ["sx","sy","sz","v"])
    extra.lockAndHide(cont_FK_Hand, ["tx","ty","tz","v"])
    extra.lockAndHide(cont_FK_LowArm, ["tx","ty","tz","sx","sz","v"])
    extra.lockAndHide(cont_FK_UpArm, ["tx","ty","tz","sx","sz","v"])
    extra.lockAndHide(cont_Shoulder, ["sx","sy","sz","v"])
    extra.lockAndHide(cont_thumb00[0], ["sx","sy","sz","v"])
    extra.lockAndHide(cont_thumb01[0], ["sx","sy","sz","v"])
    extra.lockAndHide(cont_thumb02[0], ["sx","sy","sz","v"])
    extra.lockAndHide(cont_index00[0], ["sx","sy","sz","v"])
    extra.lockAndHide(cont_index01[0], ["sx","sy","sz","v"])
    extra.lockAndHide(cont_index02[0], ["sx","sy","sz","v"])
    extra.lockAndHide(cont_index03[0], ["sx","sy","sz","v"])
    extra.lockAndHide(cont_middle00[0], ["sx","sy","sz","v"])
    extra.lockAndHide(cont_middle01[0], ["sx","sy","sz","v"])
    extra.lockAndHide(cont_middle02[0], ["sx","sy","sz","v"])
    extra.lockAndHide(cont_middle03[0], ["sx","sy","sz","v"])
    extra.lockAndHide(cont_ring00[0], ["sx","sy","sz","v"])
    extra.lockAndHide(cont_ring01[0], ["sx","sy","sz","v"])
    extra.lockAndHide(cont_ring02[0], ["sx","sy","sz","v"])
    extra.lockAndHide(cont_ring03[0], ["sx","sy","sz","v"])
    extra.lockAndHide(cont_pinky00[0], ["sx","sy","sz","v"])
    extra.lockAndHide(cont_pinky01[0], ["sx","sy","sz","v"])
    extra.lockAndHide(cont_pinky02[0], ["sx","sy","sz","v"])
    extra.lockAndHide(cont_pinky03[0], ["sx","sy","sz","v"])
    
    ## COLOR CODING
    
    if whichArm == "l_arm":
        index = 13 ##Red color index
        indexMin = 9 ##Magenta color index
    else:
        index = 6 ##Blue Color index
        indexMin = 18
        
    extra.colorize(cont_Shoulder, index)
    extra.colorize(cont_IK_hand, index)
    extra.colorize(cont_Pole, index)
    extra.colorize(cont_FK_IK, index)
    extra.colorize(cont_FK_UpArm, index)
    extra.colorize(cont_FK_LowArm, index)
    extra.colorize(cont_FK_Hand, index)
    extra.colorize(cont_thumb00, indexMin)
    extra.colorize(cont_thumb01, indexMin)
    extra.colorize(cont_thumb02, indexMin)
    extra.colorize(cont_index00, indexMin)
    extra.colorize(cont_index01, indexMin)
    extra.colorize(cont_index02, indexMin)
    extra.colorize(cont_index03, indexMin)
    extra.colorize(cont_middle00, indexMin)
    extra.colorize(cont_middle01, indexMin)
    extra.colorize(cont_middle02, indexMin)
    extra.colorize(cont_middle03, indexMin)
    extra.colorize(cont_ring00, indexMin)
    extra.colorize(cont_ring01, indexMin)
    extra.colorize(cont_ring02, indexMin)
    extra.colorize(cont_ring03, indexMin)
    extra.colorize(cont_pinky00, indexMin)
    extra.colorize(cont_pinky01, indexMin)
    extra.colorize(cont_pinky02, indexMin)
    extra.colorize(cont_pinky03, indexMin)
    
    
    extra.colorize(cont_midLock, indexMin)
    extra.colorize(ribbonConnections_upperArm[5][0], indexMin)
    extra.colorize(ribbonConnections_lowerArm[5][0], indexMin)
    
    ## CONNECT RIG data visibility
    
    cont_FK_IK.rigVis >> endLock_Ore.v
    cont_FK_IK.rigVis >> startLock_Ore.v
    cont_FK_IK.rigVis >> armStart.v
    cont_FK_IK.rigVis >> armEnd.v
    cont_FK_IK.rigVis >> IK_parentGRP.v
    cont_FK_IK.rigVis >> midLock.v
    cont_FK_IK.rigVis >> masterRoot.v
    cont_FK_IK.rigVis >> jFK_Up.v
    cont_FK_IK.rigVis >> handLock.v
    handMasterShape=handMaster.getShape()
    cont_FK_IK.rigVis >> handMasterShape.v
    for i in ribbonConnections_lowerArm[6]:
        cont_FK_IK.rigVis >> i.v
    for i in ribbonConnections_upperArm[6]:
        cont_FK_IK.rigVis >> i.v
        
    pm.setAttr(cont_FK_IK.rigVis, 0)
    
    #return [Spine_Connection, IK_Controller, Pole_Vector, Do_Not_Touch_Data]
    return [scaleGrp, cont_IK_hand_OFF, cont_Pole, nonScaleGrp]

         
leftArm=createArm("l_arm")
rightArm=createArm("r_arm")
