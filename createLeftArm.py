import pymel.core as pm
import sys
sys.path.append("C:\Users\Arda\Documents\maya\2017\scripts\AutoRigger_ard")

import extraProcedures as extra
reload(extra)
import createRibbon as cr
reload(cr)


whichArm="l_arm"
###########################
######### IK ARM ##########
###########################

masterRoot=pm.group(em=True, name="masterRoot_"+whichArm)
tempPoCon=pm.pointConstraint("Loc_Shoulder_"+whichArm, masterRoot, mo=False)
pm.delete(tempPoCon)
pm.makeIdentity(a=True)

masterIK=pm.spaceLocator(name="masterIK_"+whichArm)
tempPoCon=pm.pointConstraint("Loc_LowEnd_"+whichArm, masterIK)
pm.delete(tempPoCon)

initUpperArmDist=extra.getDistance(pm.PyNode("Loc_Up_"+whichArm), pm.PyNode("Loc_Low_"+whichArm))
initLowerArmDist=extra.getDistance(pm.PyNode("Loc_Low_"+whichArm), pm.PyNode("Loc_LowEnd_"+whichArm))


#Shoulder Joints
pm.select(d=True)
jDef_Shoulder=pm.joint(name="jDef_Shoulder_"+whichArm, p=pm.PyNode("Loc_Shoulder_"+whichArm).getTranslation(space="world"), radius=1.5)
j_ShoulderEnd=pm.joint(name="j_ShoulderEnd_"+whichArm, p=pm.PyNode("Loc_Up_"+whichArm).getTranslation(space="world"), radius=1.5)

pm.select(d=True)
jIK_orig_Up=pm.joint(name="jIK_orig_Up_"+whichArm, p=pm.PyNode("Loc_Up_"+whichArm).getTranslation(space="world"), radius=1.5)
jIK_orig_Low=pm.joint(name="jIK_orig_Low_"+whichArm, p=pm.PyNode("Loc_Low_"+whichArm).getTranslation(space="world"), radius=1.5)
jIK_orig_LowEnd=pm.joint(name="jIK_orig_LowEnd_"+whichArm, p=pm.PyNode("Loc_LowEnd_"+whichArm).getTranslation(space="world"), radius=1.5)        
pm.select(d=True)

jIK_SC_Up=pm.joint(name="jIK_SC_Up_"+whichArm, p=pm.PyNode("Loc_Up_"+whichArm).getTranslation(space="world"), radius=1)
jIK_SC_Low=pm.joint(name="jIK_SC_Low_"+whichArm, p=pm.PyNode("Loc_Low_"+whichArm).getTranslation(space="world"), radius=1)
jIK_SC_LowEnd=pm.joint(name="jIK_SC_LowEnd_"+whichArm, p=pm.PyNode("Loc_LowEnd_"+whichArm).getTranslation(space="world"), radius=1)
pm.select(d=True)

jIK_RP_Up=pm.joint(name="jIK_RP_Up_"+whichArm, p=pm.PyNode("Loc_Up_"+whichArm).getTranslation(space="world"), radius=0.7)
jIK_RP_Low=pm.joint(name="jIK_RP_Low_"+whichArm, p=pm.PyNode("Loc_Low_"+whichArm).getTranslation(space="world"), radius=0.7)
jIK_RP_LowEnd=pm.joint(name="jIK_RP_LowEnd_"+whichArm, p=pm.PyNode("Loc_LowEnd_"+whichArm).getTranslation(space="world"), radius=0.7)
pm.select(d=True)

pm.joint(jDef_Shoulder, e=True, zso=True, oj="xyz")
pm.joint(j_ShoulderEnd, e=True, zso=True, oj="xyz")

pm.joint(jIK_orig_Up, e=True, zso=True, oj="xyz")
pm.joint(jIK_orig_Low, e=True, zso=True, oj="xyz")
pm.joint(jIK_orig_LowEnd, e=True, zso=True, oj="xyz")

pm.joint(jIK_SC_Up, e=True, zso=True, oj="xyz")
pm.joint(jIK_SC_Low, e=True, zso=True, oj="xyz")
pm.joint(jIK_SC_LowEnd, e=True, zso=True, oj="xyz")

pm.joint(jIK_RP_Up, e=True, zso=True, oj="xyz")
pm.joint(jIK_RP_Low, e=True, zso=True, oj="xyz")
pm.joint(jIK_RP_LowEnd, e=True, zso=True, oj="xyz")

endLock=pm.spaceLocator(name="endLock")
extra.alignTo(endLock, j_ShoulderEnd)
pm.parent(endLock, j_ShoulderEnd)

pm.parentConstraint(endLock, jIK_SC_Up, mo=True)
pm.parentConstraint(endLock, jIK_RP_Up, mo=True)

###Create IK handles

ikHandle_SC=pm.ikHandle(sj=jIK_SC_Up, ee=jIK_SC_LowEnd, name="ikHandle_SC_"+whichArm)
ikHandle_RP=pm.ikHandle(sj=jIK_RP_Up, ee=jIK_RP_LowEnd, name="ikHandle_RP_"+whichArm, sol="ikRPsolver")

###Create Control Curve - IK
cont_IK_hand=pm.circle(nrx=1, nry=0, nrz=0, name="cont_IK_hand_"+whichArm)
extra.alignTo(cont_IK_hand, jIK_RP_LowEnd)
tempAimCon=pm.aimConstraint(jIK_RP_Low, cont_IK_hand)
pm.delete(tempAimCon)

cont_IK_hand_ORE=extra.createUpGrp(cont_IK_hand[0], "_ORE")

###Add ATTRIBUTES to the IK Foot Controller
pm.addAttr( shortName="polevector", longName="Pole_Vector", defaultValue=0.0, minValue=0.0, maxValue=1.0, at="double", k=True)
pm.addAttr( shortName="sUpArm", longName="Scale_Upper_Leg", defaultValue=1.0, minValue=0.0, at="double", k=True)
pm.addAttr( shortName="sLowArm", longName="Scale_Lower_Leg", defaultValue=1.0, minValue=0.0, at="double", k=True)
pm.addAttr( shortName="squash", longName="Squash", defaultValue=0.0, minValue=0.0, maxValue=1.0, at="double", k=True)
pm.addAttr( shortName="stretch", longName="Stretch", defaultValue=100.0, minValue=0.0, maxValue=100.0, at="double", k=True)

###Create Midlock - IK

midLock_IK=pm.spaceLocator(name="midLock_IK_"+whichArm)

extra.alignTo(midLock_IK, pm.PyNode("Loc_Low_"+whichArm))
pm.makeIdentity(a=True)
pm.pointConstraint(jIK_orig_Low, midLock_IK, mo=False)
MidLockIK_ori=pm.orientConstraint(jIK_orig_Up, jIK_orig_Low, midLock_IK, mo=True)
pm.setAttr(MidLockIK_ori.interpType, 0)

###Create Pole Vector Curve - IK

cont_Pole=pm.curve(name="cont_Pole_"+whichArm, d=1,p=[(-1, 0, -3), (-1, 0, -1),(-3, 0, -1), (-3, 0, 1), (-1, 0, 1), (-1, 0, 3), (1, 0, 3), (1, 0, 1), (3, 0, 1), (3, 0, -1), (1, 0, -1), (1, 0, -3), (-1, 0, -3)], k=[0,1,2,3,4,5,6,7,8,9,10,11,12])
pm.setAttr(cont_Pole+".scale", (0.5,0.5,0.5))
pm.rotate(cont_Pole, (90,0,0))
pm.makeIdentity(a=True)
tempCons=pm.pointConstraint( "Loc_Low_"+whichArm, cont_Pole, w=.1, mo=False)
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
extra.alignTo(armStart, jIK_orig_Up)
pm.parentConstraint(j_ShoulderEnd, armStart)

armEnd= pm.spaceLocator(name="armEnd_"+whichArm)
pm.pointConstraint(masterIK, armEnd, mo=False)

### Create Nodes and Connections for Strethchy IK SC

stretchOffset=pm.createNode("plusMinusAverage", name="stretchOffset_"+whichArm)
distance_SC=pm.createNode("distanceBetween", name="distance_SC_"+whichArm)
IK_stretch_distanceClamp=pm.createNode("clamp", name="IK_stretch_distanceClamp"+whichArm)
IK_stretch_stretchynessClamp=pm.createNode("clamp", name="IK_stretch_stretchynessClamp"+whichArm)
extraScaleMult_SC=pm.createNode("multiplyDivide", name="extraScaleMult_SC"+whichArm)
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
extra.alignTo(IK_parentGRP, "Loc_LowEnd_"+whichArm)

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
pm.closeCurve (cont_Shoulder,ch=0,ps=0,rpo=1,bb=0.5,bki=0,p=0.1)
pm.delete(cont_Shoulder, ch=True)
pm.makeIdentity(cont_Shoulder, a=True)

pm.select(cont_Shoulder)
pm.setAttr(cont_Shoulder.scale, (initUpperArmDist/5,initUpperArmDist/5,initUpperArmDist/5))
pm.makeIdentity(cont_Shoulder, a=True)
cont_Shoulder_POS=extra.createUpGrp(cont_Shoulder, "_POS")
extra.alignTo(cont_Shoulder_POS, masterRoot)

tempAimCon=pm.aimConstraint(endLock, cont_Shoulder_POS, o=(0,90,0))
pm.delete(tempAimCon)

### FInal Round UP

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
jFK_Root=pm.joint(name="jFK_Root_"+whichLeg, p=pm.PyNode("Loc_Root_"+whichLeg).getTranslation(space="world"), radius=1.0)
jFK_Knee=pm.joint(name="jFK_Knee_"+whichLeg, p=pm.PyNode("Loc_Knee_"+whichLeg).getTranslation(space="world"), radius=1.0)
jFK_Foot=pm.joint(name="jFK_Foot_"+whichLeg, p=pm.PyNode("Loc_Foot_"+whichLeg).getTranslation(space="world"), radius=1.0)
jFK_Ball=pm.joint(name="jFK_Ball_"+whichLeg, p=pm.PyNode("Loc_Ball_"+whichLeg).getTranslation(space="world"), radius=1.0)
jFK_Toe=pm.joint(name="jFK_Toe_"+whichLeg, p=pm.PyNode("Loc_Toe_"+whichLeg).getTranslation(space="world"), radius=1.0)

pm.joint(jFK_Root, e=True, zso=True, oj="xyz")
pm.joint(jFK_Knee, e=True, zso=True, oj="xyz")
pm.joint(jFK_Foot, e=True, zso=True, oj="xyz")
pm.joint(jFK_Ball, e=True, zso=True, oj="xyz")
pm.joint(jFK_Toe, e=True, zso=True, oj="xyz")

### Create Controller Curves

#UpLeg Cont
cont_FK_UpLeg=pm.curve(name="cont_FK_UpLeg"+whichLeg, d=1,p=[(-1,1,1), (-1,1,-1), (1,1,-1), (1,1,1), (-1,1,1), (-1,-1,1), (-1,-1,-1), (-1,1,-1), (-1,1,1), (-1,-1,1), (1,-1,1), (1,1,1), (1,1,-1), (1,-1,-1), (1,-1,1), (1,-1,-1), (-1,-1,-1)],k= [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16])
temp_PoCon=pm.pointConstraint(jFK_Root, jFK_Knee, cont_FK_UpLeg)
temp_AimCon=pm.aimConstraint(jFK_Knee, cont_FK_UpLeg, o=(180,0,0))
pm.delete(temp_PoCon);
pm.delete(temp_AimCon);

pm.setAttr(cont_FK_UpLeg+".scale", (pm.getAttr(jFK_Knee+".translateX")/2,0.5,0.5))
pm.makeIdentity(a=True, t=True, r=False, s=True)

PvTarget=pm.PyNode("Loc_Root_"+whichLeg).getTranslation(space="world")
pm.xform(cont_FK_UpLeg, piv=PvTarget, ws=True)

cont_FK_UpLeg_ORE=pm.group(name="cont_FK_UpLeg_ORE_"+whichLeg, em=True)
temp_PaCon=pm.parentConstraint(cont_FK_UpLeg, cont_FK_UpLeg_ORE, mo=False)
pm.delete(temp_PaCon)
pm.makeIdentity(a=True, t=True, r=False, s=True)
pm.parent(cont_FK_UpLeg, cont_FK_UpLeg_ORE)
pm.parentConstraint(masterRoot, cont_FK_UpLeg_ORE, mo=True)

#LowLeg Cont
cont_FK_LowLeg=pm.curve(name="cont_FK_LowLeg_"+whichLeg, d=1,p=[(-1,1,1), (-1,1,-1), (1,1,-1), (1,1,1), (-1,1,1), (-1,-1,1), (-1,-1,-1), (-1,1,-1), (-1,1,1), (-1,-1,1), (1,-1,1), (1,1,1), (1,1,-1), (1,-1,-1), (1,-1,1), (1,-1,-1), (-1,-1,-1)],k= [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16])
temp_PoCon=pm.pointConstraint(jFK_Knee, jFK_Foot, cont_FK_LowLeg)
temp_AimCon=pm.aimConstraint(jFK_Foot, cont_FK_LowLeg)
pm.delete(temp_PoCon);
pm.delete(temp_AimCon);
pm.setAttr(cont_FK_LowLeg+".scale", (pm.getAttr(jFK_Foot+".translateX")/2,0.5,0.5))
pm.makeIdentity(a=True, t=True, r=False, s=True)

PvTarget=pm.PyNode("Loc_Knee_"+whichLeg).getTranslation(space="world")
pm.xform(cont_FK_LowLeg, piv=PvTarget, ws=True)

cont_FK_LowLeg_ORE=pm.group(name="cont_FK_LowLeg_ORE_"+whichLeg, em=True)
temp_PaCon=pm.parentConstraint(cont_FK_LowLeg, cont_FK_LowLeg_ORE, mo=False)
pm.delete(temp_PaCon)
pm.makeIdentity(a=True, t=True, r=False, s=True)
pm.parent(cont_FK_LowLeg, cont_FK_LowLeg_ORE)

#Foot Cont
cont_FK_Foot=pm.curve(name="cont_FK_Foot_"+whichLeg, d=1,p=[(-1,1,1), (-1,1,-1), (1,1,-1), (1,1,1), (-1,1,1), (-1,-1,1), (-1,-1,-1), (-1,1,-1), (-1,1,1), (-1,-1,1), (1,-1,1), (1,1,1), (1,1,-1), (1,-1,-1), (1,-1,1), (1,-1,-1), (-1,-1,-1)],k= [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16])
temp_PoCon=pm.pointConstraint(jFK_Foot, jFK_Ball, cont_FK_Foot)
temp_AimCon=pm.aimConstraint(jFK_Ball, cont_FK_Foot)
pm.delete(temp_PoCon);
pm.delete(temp_AimCon);
pm.setAttr(cont_FK_Foot+".scale", (pm.getAttr(jFK_Ball+".translateX")/2,0.5,0.5))
pm.makeIdentity(a=True, t=True, r=False, s=True)

PvTarget=pm.PyNode("Loc_Foot_"+whichLeg).getTranslation(space="world")
pm.xform(cont_FK_Foot, piv=PvTarget, ws=True)

cont_FK_Foot_ORE=pm.group(name="cont_FK_Foot_ORE_"+whichLeg, em=True)
temp_PaCon=pm.parentConstraint(cont_FK_Foot, cont_FK_Foot_ORE, mo=False)
pm.delete(temp_PaCon)
pm.makeIdentity(a=True, t=True, r=False, s=True)
pm.parent(cont_FK_Foot, cont_FK_Foot_ORE)

#Ball Cont
cont_FK_Ball=pm.curve(name="cont_FK_Ball_"+whichLeg, d=1,p=[(-1,1,1), (-1,1,-1), (1,1,-1), (1,1,1), (-1,1,1), (-1,-1,1), (-1,-1,-1), (-1,1,-1), (-1,1,1), (-1,-1,1), (1,-1,1), (1,1,1), (1,1,-1), (1,-1,-1), (1,-1,1), (1,-1,-1), (-1,-1,-1)],k= [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16])
temp_PoCon=pm.pointConstraint(jFK_Ball, jFK_Toe, cont_FK_Ball)
temp_AimCon=pm.aimConstraint(jFK_Toe, cont_FK_Ball)
pm.delete(temp_PoCon);
pm.delete(temp_AimCon);
pm.setAttr(cont_FK_Ball+".scale", (pm.getAttr(jFK_Toe+".translateX")/2,0.5,0.5))
pm.makeIdentity(a=True, t=True, r=False, s=True)

PvTarget=pm.PyNode("Loc_Ball_"+whichLeg).getTranslation(space="world")
pm.xform(cont_FK_Ball, piv=PvTarget, ws=True)

cont_FK_Ball_ORE=pm.group(name="cont_FK_Ball_ORE_"+whichLeg, em=True)
temp_PaCon=pm.parentConstraint(cont_FK_Ball, cont_FK_Ball_ORE, mo=False)
pm.delete(temp_PaCon)
pm.makeIdentity(a=True, t=True, r=False, s=True)
pm.parent(cont_FK_Ball, cont_FK_Ball_ORE)

### Create Midlock - FK

midLock_FK=pm.spaceLocator(name="midLock_FK_"+whichLeg)
pm.makeIdentity(midLock_FK)
extra.alignTo(midLock_FK, pm.PyNode("Loc_Knee_"+whichLeg))
pm.pointConstraint(jFK_Knee, midLock_FK, mo=False)
MidLockFK_ori=pm.orientConstraint(jFK_Root, jFK_Knee, midLock_FK, mo=False)
pm.setAttr(MidLockFK_ori.interpType, 0)

### CReate Constraints and Hierarchy
pm.orientConstraint(cont_FK_UpLeg, jFK_Root, mo=False)
pm.orientConstraint(cont_FK_LowLeg, jFK_Knee, mo=False)
pm.orientConstraint(cont_FK_Foot, jFK_Foot, mo=False)
pm.orientConstraint(cont_FK_Ball, jFK_Ball, mo=False)

pm.pointConstraint(jFK_Knee, cont_FK_LowLeg_ORE, mo=False)
pm.pointConstraint(jFK_Foot, cont_FK_Foot_ORE, mo=False)
pm.pointConstraint(jFK_Ball, cont_FK_Ball_ORE, mo=False)

pm.orientConstraint(cont_FK_UpLeg, cont_FK_LowLeg_ORE, mo=True)
pm.orientConstraint(cont_FK_LowLeg, cont_FK_Foot_ORE, mo=True)
pm.orientConstraint(cont_FK_Foot, cont_FK_Ball_ORE, mo=True)

pm.scaleConstraint(cont_FK_UpLeg, jFK_Root, mo=False)
pm.scaleConstraint(cont_FK_LowLeg, jFK_Knee, mo=False)
pm.scaleConstraint(cont_FK_Foot, jFK_Foot, mo=False)
pm.scaleConstraint(cont_FK_Ball, jFK_Ball, mo=False)

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

cont_FK_IK=pm.rename(letterFK, "cont_FK_IK_"+whichLeg)
pm.select(cont_FK_IK)
pm.addAttr( shortName="fk_ik", longName="FK_IK", defaultValue=1.0, minValue=0.0, maxValue=1.0, at="float", k=True)

fk_ik_rvs=pm.createNode("reverse", name="fk_ik_rvs"+whichLeg)
cont_FK_IK.fk_ik >> blShape_FKtoIK[0].weight[0]
cont_FK_IK.fk_ik >> fk_ik_rvs.inputX

fk_ik_rvs.outputX >> cont_FK_UpLeg_ORE.visibility
fk_ik_rvs.outputX >> cont_FK_LowLeg_ORE.visibility
fk_ik_rvs.outputX >> cont_FK_Foot_ORE.visibility
fk_ik_rvs.outputX >> cont_FK_Ball_ORE.visibility
cont_FK_IK.fk_ik >> cont_IK_foot[0].visibility

pm.setAttr(cont_FK_IK+".sx", 0.1)
pm.setAttr(cont_FK_IK+".sy", 0.1)
pm.setAttr(cont_FK_IK+".sz", 0.1)

####################################################cont_FK_IK.fk_ik 

pm.delete(letterIK)

pm.select(cont_FK_IK)
pm.makeIdentity(a=True)

logoScale=(extra.getDistance(pm.PyNode("Loc_Foot_"+whichLeg), pm.PyNode("Loc_Knee_"+whichLeg)))/4
pm.setAttr(cont_FK_IK+".scale", (logoScale, logoScale, logoScale))
pm.makeIdentity(a=True)
tempPoCon=pm.pointConstraint("Loc_Foot_"+whichLeg, cont_FK_IK, mo=False)
pm.delete(tempPoCon)
pm.move(cont_FK_IK, (logoScale*2,0,0), r=True)
    
###################################
#### CREATE DEFORMATION JOINTS ####
###################################



# Upperleg Ribbon

ribbonConnections_upperLeg=cr.createRibbon("Loc_Root_"+whichLeg, "Loc_Knee_"+whichLeg, "up_"+whichLeg)

ribbonStart_paCon_upperLeg_Start=pm.parentConstraint(jIK_orig_Root, jFK_Root, ribbonConnections_upperLeg[0], mo=True)
ribbonStart_paCon_upperLeg_End=pm.parentConstraint(midLock_IK, midLock_FK, ribbonConnections_upperLeg[1], mo=True)

cont_FK_IK.fk_ik >> (ribbonStart_paCon_upperLeg_Start+"."+jIK_orig_Root+"W0")
fk_ik_rvs.outputX >> (ribbonStart_paCon_upperLeg_Start+"."+jFK_Root+"W1")

cont_FK_IK.fk_ik >> (ribbonStart_paCon_upperLeg_End+"."+midLock_IK+"W0")
fk_ik_rvs.outputX >> (ribbonStart_paCon_upperLeg_End+"."+midLock_FK+"W1")

# Lowerleg Ribbon

ribbonConnections_lowerLeg=cr.createRibbon("Loc_Knee_"+whichLeg, "Loc_Foot_"+whichLeg, "low_"+whichLeg)

ribbonStart_paCon_lowerLeg_Start=pm.parentConstraint(midLock_IK, midLock_FK, ribbonConnections_lowerLeg[0], mo=True)
ribbonStart_paCon_lowerLeg_End=pm.parentConstraint(jIK_orig_End, jFK_Foot, ribbonConnections_lowerLeg[1], mo=True)

cont_FK_IK.fk_ik >> (ribbonStart_paCon_lowerLeg_Start+"."+midLock_IK+"W0")
fk_ik_rvs.outputX >> (ribbonStart_paCon_lowerLeg_Start+"."+midLock_FK+"W1")

cont_FK_IK.fk_ik >> (ribbonStart_paCon_lowerLeg_End+"."+jIK_orig_End+"W0")
fk_ik_rvs.outputX >> (ribbonStart_paCon_lowerLeg_End+"."+jFK_Foot+"W1")

#LowerlegEnd_Sw_tr_RBN=pm.createNode("blendColors", name="LowerlegEnd_Sw_tr_RBN_"+whichLeg)
#LowerlegEnd_Sw_rot_RBN=pm.createNode("blendColors", name="LowerlegEnd_Sw_rot_RBN_"+whichLeg)
#jIK_orig_End.translate >> LowerlegEnd_Sw_tr_RBN.color2
#jFK_Foot.translate >> LowerlegEnd_Sw_tr_RBN.color1
#jIK_orig_End.rotate >> LowerlegEnd_Sw_rot_RBN.color2
#jFK_Foot.rotate >> LowerlegEnd_Sw_rot_RBN.color1
#cont_FK_IK.fk_ik >> LowerlegEnd_Sw_tr_RBN.blender
#cont_FK_IK.fk_ik >> LowerlegEnd_Sw_rot_RBN.blender
#LowerlegEnd_Sw_tr_RBN.output >> ribbonConnections_lowerLeg[1].translate
#LowerlegEnd_Sw_rot_RBN.output >> ribbonConnections_lowerLeg[1].rotate

# Foot Joint

pm.select(d=True)
jDef_Foot=pm.joint(name="jDef_Foot_"+whichLeg, p=pm.PyNode("Loc_Foot_"+whichLeg).getTranslation(space="world"), radius=1.0)
jDef_Ball=pm.joint(name="jDef_Ball_"+whichLeg, p=pm.PyNode("Loc_Ball_"+whichLeg).getTranslation(space="world"), radius=1.0)
jDef_Toe=pm.joint(name="jDef_Toe_"+whichLeg, p=pm.PyNode("Loc_Toe_"+whichLeg).getTranslation(space="world"), radius=1.0) 

foot_paCon=pm.parentConstraint(jIK_Foot, jFK_Foot, jDef_Foot, mo=True)
ball_paCon=pm.parentConstraint(jIK_Ball, jFK_Ball, jDef_Ball, mo=True)
toe_paCon=pm.parentConstraint(jIK_Toe, jFK_Toe, jDef_Toe, mo=True)

cont_FK_IK.fk_ik >> (foot_paCon+"."+jIK_Foot+"W0")
fk_ik_rvs.outputX >> (foot_paCon+"."+jFK_Foot+"W1")

cont_FK_IK.fk_ik >> (ball_paCon+"."+jIK_Ball+"W0")
fk_ik_rvs.outputX >> (ball_paCon+"."+jFK_Ball+"W1")

cont_FK_IK.fk_ik >> (toe_paCon+"."+jIK_Toe+"W0")
fk_ik_rvs.outputX >> (toe_paCon+"."+jFK_Toe+"W1")

### FINAL ROUND UP

# Create Master Root and Scale and nonScale Group

pm.parent(jIK_SC_Root, masterRoot)
pm.parent(jIK_RP_Root, masterRoot)
pm.parent(jIK_orig_Root, masterRoot)
pm.parent(jFK_Root, masterRoot)

scaleGrp=pm.group(name="scaleGrp_"+whichLeg, em=True)
nonScaleGrp=pm.group(name="NonScaleGrp_"+whichLeg, em=True)
tempPoCon=pm.pointConstraint("Loc_Foot_"+whichLeg, scaleGrp, mo=False)
pm.delete(tempPoCon)

pm.parent(masterRoot, scaleGrp)
pm.parent(legStart, scaleGrp)
pm.parent(legEnd, scaleGrp)
pm.parent(IK_parentGRP, scaleGrp)
pm.parent(cont_FK_UpLeg_ORE, scaleGrp)
pm.parent(cont_FK_LowLeg_ORE, scaleGrp)
pm.parent(cont_FK_Foot_ORE, scaleGrp)
pm.parent(cont_FK_Ball_ORE, scaleGrp)
pm.parent(midLock_FK, scaleGrp)
pm.parent(midLock_IK, scaleGrp)

pm.parent(ribbonConnections_upperLeg[2], scaleGrp)
pm.parent(ribbonConnections_upperLeg[3], nonScaleGrp)

pm.parent(ribbonConnections_lowerLeg[2], scaleGrp)
pm.parent(ribbonConnections_lowerLeg[3], nonScaleGrp)

pm.parent(jDef_Foot, scaleGrp)

### Animator Fool Proofing

#cont_FK_IK
pm.setAttr(cont_FK_IK+".sx", lock=True, keyable=False, channelBox=False)
pm.setAttr(cont_FK_IK+".sy", lock=True, keyable=False, channelBox=False)
pm.setAttr(cont_FK_IK+".sz", lock=True, keyable=False, channelBox=False)
pm.setAttr(cont_FK_IK+".v", lock=True, keyable=False, channelBox=False)

#cont_FK_Ball
pm.setAttr(cont_FK_Ball+".tx", lock=True, keyable=False, channelBox=False)
pm.setAttr(cont_FK_Ball+".ty", lock=True, keyable=False, channelBox=False)
pm.setAttr(cont_FK_Ball+".tz", lock=True, keyable=False, channelBox=False)
pm.setAttr(cont_FK_Ball+".v", lock=True, keyable=False, channelBox=False)

#cont_IK_foot
pm.setAttr(cont_IK_foot[0]+".sx", lock=True, keyable=False, channelBox=False)
pm.setAttr(cont_IK_foot[0]+".sy", lock=True, keyable=False, channelBox=False)
pm.setAttr(cont_IK_foot[0]+".sz", lock=True, keyable=False, channelBox=False)
#pm.setAttr(cont_IK_foot[0]+".v", lock=True, keyable=False, channelBox=False)

#cont_FK_UpLeg
pm.setAttr(cont_FK_UpLeg+".tx", lock=True, keyable=False, channelBox=False)
pm.setAttr(cont_FK_UpLeg+".ty", lock=True, keyable=False, channelBox=False)
pm.setAttr(cont_FK_UpLeg+".tz", lock=True, keyable=False, channelBox=False)
pm.setAttr(cont_FK_UpLeg+".v", lock=True, keyable=False, channelBox=False)

#cont_FK_LowLeg
pm.setAttr(cont_FK_LowLeg+".tx", lock=True, keyable=False, channelBox=False)
pm.setAttr(cont_FK_LowLeg+".ty", lock=True, keyable=False, channelBox=False)
pm.setAttr(cont_FK_LowLeg+".tz", lock=True, keyable=False, channelBox=False)
pm.setAttr(cont_FK_LowLeg+".v", lock=True, keyable=False, channelBox=False)

#cont_FK_Foot
pm.setAttr(cont_FK_Foot+".tx", lock=True, keyable=False, channelBox=False)
pm.setAttr(cont_FK_Foot+".ty", lock=True, keyable=False, channelBox=False)
pm.setAttr(cont_FK_Foot+".tz", lock=True, keyable=False, channelBox=False)
pm.setAttr(cont_FK_Foot+".v", lock=True, keyable=False, channelBox=False)


