## //TODO
## Ribbon flips when switching between  FK - IK

import pymel.core as pm
import sys
#sys.path.append("C:/Users/kutlu/Documents/maya/2017/scripts/tik_autorigger")


import extraProcedures as extra
reload(extra)
import createRibbon as cr
reload(cr)

whichLeg="l_leg"

# def createLeg(whichLeg):
#     legLocators=pm.ls("jInit*"+whichLeg)
#     if (len(legLocators)>=9):
        
        
##Groups
scaleGrp=pm.group(name="scaleGrp_"+whichLeg, em=True)
tempPoCon=pm.pointConstraint("jInit_Foot_"+whichLeg, scaleGrp, mo=False)
pm.delete(tempPoCon)
nonScaleGrp=pm.group(name="NonScaleGrp_"+whichLeg, em=True)

###Create common Joints
pm.select(d=True)
jDef_Rcon=pm.joint(name="jDef_Rcon_"+whichLeg, p=pm.PyNode("jInit_Rcon_"+whichLeg).getTranslation(space="world"), radius=1.5)
jDef_Upleg=pm.joint(name="jDef_UpLeg_"+whichLeg, p=pm.PyNode("jInit_UpLeg_"+whichLeg).getTranslation(space="world"), radius=1.5)
pm.joint(jDef_Rcon, e=True, zso=True, oj="xyz")
pm.joint(jDef_Upleg, e=True, zso=True, oj="xyz")
pm.parent(jDef_Rcon, scaleGrp)


###########################
######### IK LEG ##########
###########################



masterIK=pm.spaceLocator(name="masterIK_"+whichLeg)
tempPoCon=pm.pointConstraint("jInit_Foot_"+whichLeg, masterIK)
pm.delete(tempPoCon)

initUpperLegDist=extra.getDistance(pm.PyNode("jInit_UpLeg_"+whichLeg), pm.PyNode("jInit_Knee_"+whichLeg))
initLowerLegDist=extra.getDistance(pm.PyNode("jInit_Knee_"+whichLeg), pm.PyNode("jInit_Foot_"+whichLeg))


pm.select(d=True)
jIK_orig_Root=pm.joint(name="jIK_orig_Root_"+whichLeg, p=pm.PyNode("jInit_UpLeg_"+whichLeg).getTranslation(space="world"), radius=1.5)
jIK_orig_Knee=pm.joint(name="jIK_orig_Knee_"+whichLeg, p=pm.PyNode("jInit_Knee_"+whichLeg).getTranslation(space="world"), radius=1.5)
jIK_orig_End=pm.joint(name="jIK_orig_End_"+whichLeg, p=pm.PyNode("jInit_Foot_"+whichLeg).getTranslation(space="world"), radius=1.5)        
pm.select(d=True)
jIK_SC_Root=pm.joint(name="jIK_SC_Root_"+whichLeg, p=pm.PyNode("jInit_UpLeg_"+whichLeg).getTranslation(space="world"), radius=1)
jIK_SC_Knee=pm.joint(name="jIK_SC_Knee_"+whichLeg, p=pm.PyNode("jInit_Knee_"+whichLeg).getTranslation(space="world"), radius=1)
jIK_SC_End=pm.joint(name="jIK_SC_End_"+whichLeg, p=pm.PyNode("jInit_Foot_"+whichLeg).getTranslation(space="world"), radius=1)
pm.select(d=True)
jIK_RP_Root=pm.joint(name="jIK_RP_Root_"+whichLeg, p=pm.PyNode("jInit_UpLeg_"+whichLeg).getTranslation(space="world"), radius=0.7)
jIK_RP_Knee=pm.joint(name="jIK_RP_Knee_"+whichLeg, p=pm.PyNode("jInit_Knee_"+whichLeg).getTranslation(space="world"), radius=0.7)
jIK_RP_End=pm.joint(name="jIK_RP_End_"+whichLeg, p=pm.PyNode("jInit_Foot_"+whichLeg).getTranslation(space="world"), radius=0.7)
pm.select(d=True)
jIK_Foot=pm.joint(name="jIK_Foot_"+whichLeg, p=pm.PyNode("jInit_Foot_"+whichLeg).getTranslation(space="world"), radius=1.0)
jIK_Ball=pm.joint(name="jIK_Ball_"+whichLeg, p=pm.PyNode("jInit_Ball_"+whichLeg).getTranslation(space="world"), radius=1.0)
jIK_Toe=pm.joint(name="jIK_Toe_"+whichLeg, p=pm.PyNode("jInit_Toe_"+whichLeg).getTranslation(space="world"), radius=1.0)



pm.joint(jIK_orig_Root, e=True, zso=True, oj="xyz")
pm.joint(jIK_orig_Knee, e=True, zso=True, oj="xyz")
pm.joint(jIK_orig_End, e=True, zso=True, oj="xyz")
pm.joint(jIK_SC_Root, e=True, zso=True, oj="xyz")
pm.joint(jIK_SC_Knee, e=True, zso=True, oj="xyz")
pm.joint(jIK_SC_End, e=True, zso=True, oj="xyz")
pm.joint(jIK_RP_Root, e=True, zso=True, oj="xyz")
pm.joint(jIK_RP_Knee, e=True, zso=True, oj="xyz")
pm.joint(jIK_RP_End, e=True, zso=True, oj="xyz")
pm.joint(jIK_Foot, e=True, zso=True, oj="xyz")
pm.joint(jIK_Ball, e=True, zso=True, oj="xyz")
pm.joint(jIK_Toe, e=True, zso=True, oj="xyz")


###Create Foot Pivots
pm.select(cl=True)

Pv_BankIn=pm.group(name="Pv_BankIn_"+whichLeg, em=True)
extra.alignTo(Pv_BankIn, "jInit_BankIn_"+whichLeg, 0)
pm.makeIdentity(Pv_BankIn, a=True, t=False, r=True, s=True)

Pv_BankOut=pm.group(name="Pv_BankOut_"+whichLeg, em=True)
extra.alignTo(Pv_BankOut, "jInit_BankOut_"+whichLeg, 0)
pm.makeIdentity(Pv_BankOut, a=True, t=False, r=True, s=True)

Pv_Toe=pm.group(name="Pv_Toe_"+whichLeg, em=True)
extra.alignTo(Pv_Toe, "jInit_ToePv_"+whichLeg, 0)
pm.makeIdentity(Pv_Toe, a=True, t=False, r=True, s=True)

Pv_Ball=pm.group(name="Pv_Ball_"+whichLeg, em=True)
extra.alignTo(Pv_Ball, "jInit_Ball_"+whichLeg, 0)
pm.makeIdentity(Pv_Ball, a=True, t=False, r=True, s=True)

Pv_Heel=pm.group(name="Pv_Heel_"+whichLeg, em=True)
extra.alignTo(Pv_Heel, "jInit_HeelPv_"+whichLeg, 0)
pm.makeIdentity(Pv_Heel, a=True, t=False, r=True, s=True)

Pv_BallSpin=pm.group(name="Pv_BallSpin_"+whichLeg, em=True)
extra.alignTo(Pv_BallSpin, "jInit_Ball_"+whichLeg, 0)
pm.makeIdentity(Pv_BallSpin, a=True, t=False, r=True, s=True)

Pv_BallRoll=pm.group(name="Pv_BallRoll_"+whichLeg, em=True)
extra.alignTo(Pv_BallRoll, "jInit_Ball_"+whichLeg, 0)
pm.makeIdentity(Pv_BallRoll, a=True, t=False, r=True, s=True)

Pv_BallLean=pm.group(name="Pv_BallLean_"+whichLeg, em=True)
extra.alignTo(Pv_BallLean, "jInit_Ball_"+whichLeg, 0)
pm.makeIdentity(Pv_BallLean, a=True, t=False, r=True, s=True)


## Create Start Lock

startLock=pm.spaceLocator(name="startLock_"+whichLeg)
extra.alignTo(startLock, "jInit_UpLeg_"+whichLeg, 2)
startLock_Ore=extra.createUpGrp(startLock, "_Ore")
startLock_Pos=extra.createUpGrp(startLock, "_Pos")
startLock_Twist=extra.createUpGrp(startLock, "_AutoTwist")

startLockRot=pm.parentConstraint(jDef_Upleg, startLock, mo=True)
pm.setAttr(startLockRot.interpType, 0)

pm.parentConstraint(startLock, jIK_SC_Root, mo=True)
pm.parentConstraint(startLock, jIK_RP_Root, mo=True)


###Create IK handles

ikHandle_SC=pm.ikHandle(sj=jIK_SC_Root, ee=jIK_SC_End, name="ikHandle_SC_"+whichLeg)
ikHandle_RP=pm.ikHandle(sj=jIK_RP_Root, ee=jIK_RP_End, name="ikHandle_RP_"+whichLeg, sol="ikRPsolver")

ikHandle_Ball=pm.ikHandle(sj=jIK_Foot, ee=jIK_Ball, name="ikHandle_Ball_"+whichLeg)
ikHandle_Toe=pm.ikHandle(sj=jIK_Ball, ee=jIK_Toe, name="ikHandle_Toe_"+whichLeg)

###Create Hierarchy for Foot

pm.parent(ikHandle_Ball[0], Pv_Ball)
pm.parent(ikHandle_Toe[0], Pv_Ball)
pm.parent(masterIK, Pv_BallLean)
pm.parent(ikHandle_SC[0], masterIK)
pm.parent(ikHandle_RP[0], masterIK)
pm.parent(Pv_BallLean, Pv_BallRoll)
pm.parent(Pv_Ball, Pv_Toe)
pm.parent(Pv_BallRoll, Pv_Toe)
pm.parent(Pv_Toe, Pv_BallSpin)
pm.parent(Pv_BallSpin, Pv_Heel)
pm.parent(Pv_Heel, Pv_BankOut)
pm.parent(Pv_BankOut, Pv_BankIn)

###Create Control Curve - IK

zScale=extra.getDistance(Pv_Toe, Pv_Heel)
xScale=extra.getDistance(Pv_BankOut, Pv_BankIn)
offset=extra.getDistance(Pv_Ball, Pv_Heel)

cont_IK_foot=pm.circle(nrx=0, nry=1, nrz=0, name="cont_IK_foot_"+whichLeg)
pm.setAttr(cont_IK_foot[0]+".scaleX", xScale*0.75)
pm.setAttr(cont_IK_foot[0]+".scaleZ", zScale*0.75)

tempCons=pm.pointConstraint( Pv_Toe, Pv_Heel, Pv_BankIn, Pv_BankOut, cont_IK_foot, w=.1, mo=False)
pm.delete(tempCons)
pm.makeIdentity(a=True)
target=pm.PyNode("jInit_Foot_"+whichLeg).getTranslation(space="world")
pm.setAttr(cont_IK_foot[0]+".rotatePivot", (target.x,target.y,target.z))


###Add ATTRIBUTES to the IK Foot Controller
pm.select(cont_IK_foot)
pm.addAttr( shortName="polevector", longName="Pole_Vector", defaultValue=0.0, minValue=0.0, maxValue=1.0, at="double", k=True)
pm.addAttr( shortName="sUpLeg", longName="Scale_Upper_Leg", defaultValue=1.0, minValue=0.0, at="double", k=True)
pm.addAttr( shortName="sLowLeg", longName="Scale_Lower_Leg", defaultValue=1.0, minValue=0.0, at="double", k=True)
pm.addAttr( shortName="squash", longName="Squash", defaultValue=0.0, minValue=0.0, maxValue=1.0, at="double", k=True)
pm.addAttr( shortName="stretch", longName="Stretch", defaultValue=100.0, minValue=0.0, maxValue=100.0, at="double", k=True)
pm.addAttr( shortName="bLean", longName="Ball_Lean", defaultValue=0.0, at="double", k=True)
pm.addAttr( shortName="bRoll", longName="Ball_Roll", defaultValue=0.0, at="double", k=True)
pm.addAttr( shortName="bSpin", longName="Ball_Spin", defaultValue=0.0, at="double", k=True)
pm.addAttr( shortName="hRoll", longName="Heel_Roll", defaultValue=0.0, at="double", k=True)
pm.addAttr( shortName="hSpin", longName="Heel_Spin", defaultValue=0.0, at="double", k=True)
pm.addAttr( shortName="tRoll", longName="Toes_Roll", defaultValue=0.0, at="double", k=True)
pm.addAttr( shortName="tSpin", longName="Toes_Spin", defaultValue=0.0, at="double", k=True)
pm.addAttr( shortName="tWiggle", longName="Toes_Wiggle", defaultValue=0.0, at="double", k=True)
pm.addAttr( shortName="bank", longName="Bank", defaultValue=0.0, at="double", k=True)

###Create Midlock - IK Target

target_midLock_IK=pm.spaceLocator(name="target_midLock_IK_"+whichLeg)
pm.makeIdentity(a=True)
extra.alignTo(target_midLock_IK, "jInit_Knee_"+whichLeg, 0)

pm.pointConstraint(jIK_orig_Knee, target_midLock_IK, mo=False)
MidLockIK_ori=pm.orientConstraint(jIK_orig_Root, jIK_orig_Knee, target_midLock_IK, mo=False)
pm.setAttr(MidLockIK_ori.interpType, 0)

#MidLockIK_ori=pm.aimConstraint(jIK_orig_Root, jIK_orig_End, target_midLock_IK, mo=False)

###Create Pole Vector Curve - IK

cont_Pole=pm.curve(name="cont_Pole_"+whichLeg, d=1,p=[(-1, 0, -3), (-1, 0, -1),(-3, 0, -1), (-3, 0, 1), (-1, 0, 1), (-1, 0, 3), (1, 0, 3), (1, 0, 1), (3, 0, 1), (3, 0, -1), (1, 0, -1), (1, 0, -3), (-1, 0, -3)], k=[0,1,2,3,4,5,6,7,8,9,10,11,12])
pm.setAttr(cont_Pole+".scale", (0.5,0.5,0.5))
pm.makeIdentity(a=True)
tempCons=pm.pointConstraint( "jInit_Knee_"+whichLeg, cont_Pole, w=.1, mo=False, sk="z")
pm.delete(tempCons)
tempCons=pm.pointConstraint( "jInit_ToePv_"+whichLeg, cont_Pole, w=.1, mo=False, sk=["x","y"])
pm.delete(tempCons)
tempCons=pm.aimConstraint( "jInit_Knee_"+whichLeg, cont_Pole, w=.1, mo=False, o=(0,0,90))
pm.delete(tempCons)
scaleValue=(((initUpperLegDist+initLowerLegDist)/2)/10)
pm.setAttr(cont_Pole+".scale", (scaleValue,scaleValue,scaleValue))
pm.makeIdentity(a=True)
pm.poleVectorConstraint(cont_Pole, "ikHandle_RP_"+whichLeg)

### Create and constrain Distance Locators

legStart= pm.spaceLocator(name="legStart_loc_"+whichLeg)
pm.pointConstraint(startLock, legStart, mo=False)

legEnd= pm.spaceLocator(name="legEnd_loc_"+whichLeg)
pm.pointConstraint(masterIK, legEnd, mo=False)


### Create Nodes and Connections for Strethchy IK SC

stretchOffset=pm.createNode("plusMinusAverage", name="stretchOffset_"+whichLeg)
distance_SC=pm.createNode("distanceBetween", name="distance_SC_"+whichLeg)
IK_stretch_distanceClamp=pm.createNode("clamp", name="IK_stretch_distanceClamp"+whichLeg)
IK_stretch_stretchynessClamp=pm.createNode("clamp", name="IK_stretch_stretchynessClamp"+whichLeg)
extraScaleMult_SC=pm.createNode("multiplyDivide", name="extraScaleMult_SC"+whichLeg)
initialDivide_SC=pm.createNode("multiplyDivide", name="initialDivide_SC_"+whichLeg)
initialLengthMultip_SC=pm.createNode("multiplyDivide", name="initialLengthMultip_SC_"+whichLeg)
stretchAmount_SC=pm.createNode("multiplyDivide", name="stretchAmount_SC_"+whichLeg)
sumOfJLengths_SC=pm.createNode("plusMinusAverage", name="sumOfJLengths_SC_"+whichLeg)
stretchCondition_SC=pm.createNode("condition", name="stretchCondition_SC_"+whichLeg)
squashyness_SC=pm.createNode("blendColors", name="squashyness_SC_"+whichLeg)
stretchyness_SC=pm.createNode("blendColors", name="stretchyness_SC_"+whichLeg)

pm.setAttr(IK_stretch_stretchynessClamp+".maxR", 1)
pm.setAttr(initialLengthMultip_SC+".input1X", initUpperLegDist)
pm.setAttr(initialLengthMultip_SC+".input1Y", initLowerLegDist)

pm.setAttr(initialDivide_SC+".operation", 2)
pm.setAttr(stretchCondition_SC+".operation", 2)


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

cont_IK_foot[0].rotate >> jIK_RP_End.rotate

# Stretch Attributes Controller connections

cont_IK_foot[0].sUpLeg >> extraScaleMult_SC.input2X
cont_IK_foot[0].sLowLeg >> extraScaleMult_SC.input2Y 
cont_IK_foot[0].squash >> squashyness_SC.blender

stretchOffset.output1D >> IK_stretch_distanceClamp.maxR
cont_IK_foot[0].stretch >> IK_stretch_stretchynessClamp.inputR
cont_IK_foot[0].stretch >> stretchOffset.input1D[2]


# Bind Foot Attributes to the controller
cont_IK_foot[0].bLean >> Pv_BallLean.rotateY
cont_IK_foot[0].bRoll >> Pv_BallRoll.rotateX
cont_IK_foot[0].bSpin >> Pv_BallSpin.rotateY
cont_IK_foot[0].hRoll >> Pv_Heel.rotateX
cont_IK_foot[0].hSpin >> Pv_Heel.rotateY
cont_IK_foot[0].tRoll >> Pv_Toe.rotateX
cont_IK_foot[0].tSpin >> Pv_Toe.rotateY
cont_IK_foot[0].tWiggle >> Pv_Ball.rotateX

pm.select(Pv_BankOut)
pm.setDrivenKeyframe(cd=cont_IK_foot[0].bank, at="rotateZ", dv=0, v=0)
pm.setDrivenKeyframe(cd=cont_IK_foot[0].bank, at="rotateZ", dv=-90, v=90)
pm.select(Pv_BankIn)
pm.setDrivenKeyframe(cd=cont_IK_foot[0].bank, at="rotateZ", dv=0, v=0)
pm.setDrivenKeyframe(cd=cont_IK_foot[0].bank, at="rotateZ", dv=90, v=-90)

IK_parentGRP=pm.group(name="IK_parentGRP_"+whichLeg, em=True)
extra.alignTo(IK_parentGRP, "jInit_Foot_"+whichLeg, 0)
pm.parent(Pv_BankIn, IK_parentGRP)
pm.parent(jIK_Foot, IK_parentGRP)

pm.parentConstraint(jIK_SC_End, jIK_Foot)

pm.parentConstraint(cont_IK_foot, IK_parentGRP, mo=True)

# Create Orig Switch (Pole Vector On/Off)

blendORE_IK_root=pm.createNode("blendColors", name="blendORE_IK_root_"+whichLeg)
jIK_SC_Root.rotate >> blendORE_IK_root.color2
jIK_RP_Root.rotate >> blendORE_IK_root.color1
blendORE_IK_root.output >> jIK_orig_Root.rotate
cont_IK_foot[0].polevector >> blendORE_IK_root.blender

blendPOS_IK_root=pm.createNode("blendColors", name="blendPOS_IK_root_"+whichLeg)
jIK_SC_Root.translate >> blendPOS_IK_root.color2
jIK_RP_Root.translate >> blendPOS_IK_root.color1
blendPOS_IK_root.output >> jIK_orig_Root.translate
cont_IK_foot[0].polevector >> blendPOS_IK_root.blender

blendORE_IK_knee=pm.createNode("blendColors", name="blendORE_IK_knee_"+whichLeg)
jIK_SC_Knee.rotate >> blendORE_IK_knee.color2
jIK_RP_Knee.rotate >> blendORE_IK_knee.color1
blendORE_IK_knee.output >> jIK_orig_Knee.rotate
cont_IK_foot[0].polevector >> blendORE_IK_knee.blender

blendPOS_IK_knee=pm.createNode("blendColors", name="blendPOS_IK_knee_"+whichLeg)
jIK_SC_Knee.translate >> blendPOS_IK_knee.color2
jIK_RP_Knee.translate >> blendPOS_IK_knee.color1
blendPOS_IK_knee.output >> jIK_orig_Knee.translate
cont_IK_foot[0].polevector >> blendPOS_IK_knee.blender

blendORE_IK_end=pm.createNode("blendColors", name="blendORE_IK_end_"+whichLeg)
jIK_SC_End.rotate >> blendORE_IK_end.color2
jIK_RP_End.rotate >> blendORE_IK_end.color1
blendORE_IK_end.output >> jIK_orig_End.rotate
cont_IK_foot[0].polevector >> blendORE_IK_end.blender

blendPOS_IK_end=pm.createNode("blendColors", name="blendPOS_IK_end_"+whichLeg)
jIK_SC_End.translate >> blendPOS_IK_end.color2
jIK_RP_End.translate >> blendPOS_IK_end.color1
blendPOS_IK_end.output >> jIK_orig_End.translate
cont_IK_foot[0].polevector >> blendPOS_IK_end.blender

poleVector_Rvs=pm.createNode("reverse", name="poleVector_Rvs_"+whichLeg)
cont_IK_foot[0].polevector >> poleVector_Rvs.inputX

cont_IK_foot[0].polevector >> cont_Pole.v

### Create Tigh Controller
thighContScale=extra.getDistance(pm.PyNode("jInit_UpLeg_"+whichLeg), pm.PyNode("jInit_Knee_"+whichLeg))/4
cont_thigh=pm.curve(name="cont_thigh"+whichLeg, d=1,p=[(-1,1,1), (-1,1,-1), (1,1,-1), (1,1,1), (-1,1,1), (-1,-1,1), (-1,-1,-1), (-1,1,-1), (-1,1,1), (-1,-1,1), (1,-1,1), (1,1,1), (1,1,-1), (1,-1,-1), (1,-1,1), (1,-1,-1), (-1,-1,-1)],k= [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16])
pm.setAttr(cont_thigh.scale, (thighContScale,thighContScale,thighContScale/4))
pm.makeIdentity(cont_thigh, a=True)

cont_thigh_OFF=extra.createUpGrp(cont_thigh, "OFF")
cont_thigh_ORE=extra.createUpGrp(cont_thigh, "ORE")
if whichLeg=="r_leg":
    pm.setAttr(cont_thigh_ORE.rotateX, -180)
extra.alignTo(cont_thigh_OFF, "jInit_UpLeg_"+whichLeg, 2)


pm.addAttr( shortName="autoTwist", longName="Auto_Twist", defaultValue=1.0, minValue=0.0, maxValue=1.0, at="float", k=True)
pm.addAttr( shortName="manualTwist", longName="Manual_Twist", defaultValue=0.0, at="float", k=True)

extra.alignTo(cont_thigh_OFF, "jInit_UpLeg_"+whichLeg, 2)
PvTarget=pm.PyNode("jInit_Rcon_"+whichLeg).getTranslation(space="world")

pm.move(cont_thigh, (0,thighContScale*2,0), r=True)
temp_AimCon=pm.aimConstraint("jInit_UpLeg_"+whichLeg, cont_thigh, o=(0,0,0))
pm.delete(temp_AimCon)
pm.xform(cont_thigh, piv=PvTarget, ws=True)
pm.makeIdentity(cont_thigh, a=True, t=True, r=False, s=True)
pm.parentConstraint(cont_thigh, jDef_Rcon, mo=True)


###########################
######### FK LEG ##########
###########################


pm.select(d=True)
jFK_Root=pm.joint(name="jFK_Root_"+whichLeg, p=pm.PyNode("jInit_UpLeg_"+whichLeg).getTranslation(space="world"), radius=1.0)
jFK_Knee=pm.joint(name="jFK_Knee_"+whichLeg, p=pm.PyNode("jInit_Knee_"+whichLeg).getTranslation(space="world"), radius=1.0)
jFK_Foot=pm.joint(name="jFK_Foot_"+whichLeg, p=pm.PyNode("jInit_Foot_"+whichLeg).getTranslation(space="world"), radius=1.0)
jFK_Ball=pm.joint(name="jFK_Ball_"+whichLeg, p=pm.PyNode("jInit_Ball_"+whichLeg).getTranslation(space="world"), radius=1.0)
jFK_Toe=pm.joint(name="jFK_Toe_"+whichLeg, p=pm.PyNode("jInit_Toe_"+whichLeg).getTranslation(space="world"), radius=1.0)

pm.joint(jFK_Root, e=True, zso=True, oj="xyz")
pm.joint(jFK_Knee, e=True, zso=True, oj="xyz")
pm.joint(jFK_Foot, e=True, zso=True, oj="xyz")
pm.joint(jFK_Ball, e=True, zso=True, oj="xyz")
pm.joint(jFK_Toe, e=True, zso=True, oj="xyz")

### Create Controller Curves

#UpLeg Cont
cont_FK_UpLeg=pm.curve(name="cont_FK_UpLeg"+whichLeg, d=1,p=[(-1,1,1), (-1,1,-1), (1,1,-1), (1,1,1), (-1,1,1), (-1,-1,1), (-1,-1,-1), (-1,1,-1), (-1,1,1), (-1,-1,1), (1,-1,1), (1,1,1), (1,1,-1), (1,-1,-1), (1,-1,1), (1,-1,-1), (-1,-1,-1)],k= [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16])
pm.setAttr(cont_FK_UpLeg.scale, (pm.getAttr(jFK_Knee.translateX)/8,pm.getAttr(jFK_Knee.translateX)/2,pm.getAttr(jFK_Knee.translateX)/8))
pm.makeIdentity(cont_FK_UpLeg, a=True)

cont_FK_UpLeg_OFF=extra.createUpGrp(cont_FK_UpLeg, "OFF")
cont_FK_UpLeg_ORE=extra.createUpGrp(cont_FK_UpLeg, "ORE")
if whichLeg=="r_leg":
    pm.setAttr(cont_FK_UpLeg_ORE.rotateX, -180)

temp_PoCon=pm.pointConstraint(jFK_Root, jFK_Knee, cont_FK_UpLeg_OFF)
pm.delete(temp_PoCon)
temp_AimCon=pm.aimConstraint(jFK_Knee, cont_FK_UpLeg_OFF, o=(90,90,0), u=(0,1,0))
pm.delete(temp_AimCon)

PvTarget=pm.PyNode("jInit_UpLeg_"+whichLeg).getTranslation(space="world")
pm.xform(cont_FK_UpLeg, piv=PvTarget, ws=True)


pm.makeIdentity(a=True, t=True, r=False, s=True)
pm.parent(cont_FK_UpLeg, cont_FK_UpLeg_ORE)

pm.parentConstraint(startLock, cont_FK_UpLeg_OFF, mo=True)

#LowLeg Cont
cont_FK_LowLeg=pm.curve(name="cont_FK_LowLeg_"+whichLeg, d=1,p=[(-1,1,1), (-1,1,-1), (1,1,-1), (1,1,1), (-1,1,1), (-1,-1,1), (-1,-1,-1), (-1,1,-1), (-1,1,1), (-1,-1,1), (1,-1,1), (1,1,1), (1,1,-1), (1,-1,-1), (1,-1,1), (1,-1,-1), (-1,-1,-1)],k= [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16])
pm.setAttr(cont_FK_LowLeg.scale, (pm.getAttr(jFK_Foot.translateX)/8,pm.getAttr(jFK_Foot.translateX)/2,pm.getAttr(jFK_Foot.translateX)/8))
pm.makeIdentity(cont_FK_LowLeg, a=True)

cont_FK_LowLeg_OFF=extra.createUpGrp(cont_FK_LowLeg, "OFF")
cont_FK_LowLeg_ORE=extra.createUpGrp(cont_FK_LowLeg, "ORE")
if whichLeg=="r_leg":
    pm.setAttr(cont_FK_LowLeg_ORE.rotateX, -180)

temp_PoCon=pm.pointConstraint(jFK_Knee, jFK_Foot, cont_FK_LowLeg_OFF)
pm.delete(temp_PoCon)
temp_AimCon=pm.aimConstraint(jFK_Foot, cont_FK_LowLeg_OFF, o=(90,90,0), u=(0,1,0))
pm.delete(temp_AimCon)

pm.makeIdentity(a=True, t=True, r=False, s=True)

PvTarget=pm.PyNode("jInit_Knee_"+whichLeg).getTranslation(space="world")
pm.xform(cont_FK_LowLeg, piv=PvTarget, ws=True)

#Foot Cont
cont_FK_Foot=pm.curve(name="cont_FK_Foot_"+whichLeg, d=1,p=[(-1,1,1), (-1,1,-1), (1,1,-1), (1,1,1), (-1,1,1), (-1,-1,1), (-1,-1,-1), (-1,1,-1), (-1,1,1), (-1,-1,1), (1,-1,1), (1,1,1), (1,1,-1), (1,-1,-1), (1,-1,1), (1,-1,-1), (-1,-1,-1)],k= [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16])
pm.setAttr(cont_FK_Foot.scale, (pm.getAttr(jFK_Ball.translateX)/4,pm.getAttr(jFK_Ball.translateX)/2,pm.getAttr(jFK_Ball.translateX)/4))
pm.makeIdentity(cont_FK_Foot, a=True)

cont_FK_Foot_OFF=extra.createUpGrp(cont_FK_Foot, "OFF")
cont_FK_Foot_ORE=extra.createUpGrp(cont_FK_Foot, "ORE")
if whichLeg=="r_leg":
    pm.setAttr(cont_FK_Foot_ORE.rotateX, -180)

temp_PoCon=pm.pointConstraint(jFK_Foot, jFK_Ball, cont_FK_Foot_OFF)
pm.delete(temp_PoCon);
temp_AimCon=pm.aimConstraint(jFK_Ball, cont_FK_Foot_OFF, o=(90,90,0), u=(0,1,0))
pm.delete(temp_AimCon);

pm.makeIdentity(a=True, t=True, r=False, s=True)

PvTarget=pm.PyNode("jInit_Foot_"+whichLeg).getTranslation(space="world")
pm.xform(cont_FK_Foot, piv=PvTarget, ws=True)

#Ball Cont
cont_FK_Ball=pm.curve(name="cont_FK_Ball_"+whichLeg, d=1,p=[(-1,1,1), (-1,1,-1), (1,1,-1), (1,1,1), (-1,1,1), (-1,-1,1), (-1,-1,-1), (-1,1,-1), (-1,1,1), (-1,-1,1), (1,-1,1), (1,1,1), (1,1,-1), (1,-1,-1), (1,-1,1), (1,-1,-1), (-1,-1,-1)],k= [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16])
pm.setAttr(cont_FK_Ball.scale, (pm.getAttr(jFK_Toe.translateX)/4,pm.getAttr(jFK_Toe.translateX)/2,pm.getAttr(jFK_Toe.translateX)/4))
pm.makeIdentity(cont_FK_Ball, a=True)

cont_FK_Ball_OFF=extra.createUpGrp(cont_FK_Ball, "OFF")
cont_FK_Ball_ORE=extra.createUpGrp(cont_FK_Ball, "ORE")

if whichLeg=="r_leg":
    pm.setAttr(cont_FK_Ball_ORE.rotateX, -180)
    
temp_PoCon=pm.pointConstraint(jFK_Ball, jFK_Toe, cont_FK_Ball)
pm.delete(temp_PoCon);
temp_AimCon=pm.aimConstraint(jFK_Toe, cont_FK_Ball, o=(90,90,0), u=(0,1,0))
pm.delete(temp_AimCon);

pm.makeIdentity(a=True, t=True, r=False, s=True)

PvTarget=pm.PyNode("jInit_Ball_"+whichLeg).getTranslation(space="world")
pm.xform(cont_FK_Ball, piv=PvTarget, ws=True)

### Create Midlock - FK

target_midLock_FK=pm.spaceLocator(name="target_midLock_FK_"+whichLeg)
pm.makeIdentity(target_midLock_FK)
extra.alignTo(target_midLock_FK, "jInit_Knee_"+whichLeg, 0)

pm.pointConstraint(jFK_Knee, target_midLock_FK, mo=False)
MidLockFK_ori=pm.orientConstraint(jFK_Root, jFK_Knee, target_midLock_FK, mo=True)
#pm.setAttr(MidLockFK_ori.interpType, 0)



### CReate Constraints and Hierarchy
pm.orientConstraint(cont_FK_UpLeg, jFK_Root, mo=True)
pm.pointConstraint(startLock, jFK_Root, mo=False)

pm.orientConstraint(cont_FK_LowLeg, jFK_Knee, mo=True)
pm.orientConstraint(cont_FK_Foot, jFK_Foot, mo=True)
pm.orientConstraint(cont_FK_Ball, jFK_Ball, mo=True)

pm.parent(cont_FK_UpLeg_OFF, cont_thigh)
pm.parent(cont_FK_LowLeg_OFF, cont_FK_UpLeg)
pm.parent(cont_FK_Foot_OFF, cont_FK_LowLeg)
pm.parent(cont_FK_Ball_OFF, cont_FK_Foot)

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
pm.addAttr( shortName="autoTwist", longName="Auto_Twist", defaultValue=1.0, minValue=0.0, maxValue=1.0, at="float", k=True)
pm.addAttr( shortName="manualTwist", longName="Manual_Twist", defaultValue=0.0, at="float", k=True)
pm.addAttr( shortName="twistInterpolation", longName="Twist_Interpolation", at="enum", enumName="No_Flip:Average:Shortest:Longest:Cache", defaultValue=2, k=True)

fk_ik_rvs=pm.createNode("reverse", name="fk_ik_rvs"+whichLeg)
cont_FK_IK.fk_ik >> blShape_FKtoIK[0].weight[0]
cont_FK_IK.fk_ik >> fk_ik_rvs.inputX

fk_ik_rvs.outputX >> cont_FK_UpLeg_OFF.visibility
fk_ik_rvs.outputX >> cont_FK_LowLeg_OFF.visibility
fk_ik_rvs.outputX >> cont_FK_Foot_OFF.visibility
fk_ik_rvs.outputX >> cont_FK_Ball_ORE.visibility
cont_FK_IK.fk_ik >> cont_IK_foot[0].visibility

pm.setAttr(cont_FK_IK+".sx", 0.1)
pm.setAttr(cont_FK_IK+".sy", 0.1)
pm.setAttr(cont_FK_IK+".sz", 0.1)

pm.delete(letterIK)

pm.select(cont_FK_IK)
pm.makeIdentity(a=True)

logoScale=(extra.getDistance(pm.PyNode("jInit_Foot_"+whichLeg), pm.PyNode("jInit_Knee_"+whichLeg)))/4
pm.setAttr(cont_FK_IK+".scale", (logoScale, logoScale, logoScale))
pm.makeIdentity(a=True)
tempPoCon=pm.pointConstraint("jInit_Foot_"+whichLeg, cont_FK_IK, mo=False)
pm.delete(tempPoCon)
pm.move(cont_FK_IK, (logoScale*2,0,0), r=True)

cont_FK_IK_POS=extra.createUpGrp(cont_FK_IK, "_POS")
pm.parent(cont_FK_IK_POS, scaleGrp)

### Create MidLock controller

contScale= extra.getDistance(pm.PyNode("jInit_Foot_"+whichLeg), pm.PyNode("jInit_Knee_"+whichLeg))/3
cont_midLock=pm.circle(name="cont_mid_"+whichLeg, nr=(0,1,0), ch=0)
pm.rebuildCurve(cont_midLock, s=12, ch=0)
pm.select(cont_midLock[0].cv[0],cont_midLock[0].cv[2],cont_midLock[0].cv[4],cont_midLock[0].cv[6],cont_midLock[0].cv[8],cont_midLock[0].cv[10])
pm.scale(0.5, 0.5, 0.5)
pm.select(d=True)
pm.setAttr(cont_midLock[0].scale, (contScale, contScale, contScale))
pm.makeIdentity(cont_midLock, a=True)

cont_midLock_POS=extra.createUpGrp(cont_midLock[0],"POS")
cont_midLock_AVE=extra.createUpGrp(cont_midLock[0],"AVE")
extra.alignTo(cont_midLock_POS, "jInit_Knee_"+whichLeg, 0)


midLock_paConWeight=pm.parentConstraint(jIK_orig_Root, jFK_Root, cont_midLock_POS, mo=True)
cont_FK_IK.fk_ik >> (midLock_paConWeight+"."+jIK_orig_Root+"W0")
fk_ik_rvs.outputX >> (midLock_paConWeight+"."+jFK_Root+"W1")

midLock_poConWeight=pm.pointConstraint(jIK_orig_Knee, jFK_Knee, cont_midLock_AVE, mo=False)
cont_FK_IK.fk_ik >> (midLock_poConWeight+"."+jIK_orig_Knee+"W0")
fk_ik_rvs.outputX >> (midLock_poConWeight+"."+jFK_Knee+"W1")

midLock_xBln=pm.createNode("multiplyDivide", name="midLock_xBln"+whichLeg)

midLock_rotXsw=pm.createNode("blendTwoAttr", name="midLock_rotXsw"+whichLeg)
jIK_orig_Knee.rotateZ >> midLock_rotXsw.input[0]
jFK_Knee.rotateZ >> midLock_rotXsw.input[1]
fk_ik_rvs.outputX >> midLock_rotXsw.attributesBlender

midLock_rotXsw.output >> midLock_xBln.input1Z


pm.setAttr(midLock_xBln.input2Z, 0.5)
midLock_xBln.outputZ >> cont_midLock_AVE.rotateX

### Create MASTER Midlock

midLock=pm.spaceLocator(name="midLock_"+whichLeg)
extra.alignTo(midLock, cont_midLock, 0)

pm.parentConstraint(cont_midLock, midLock, mo=False)

# midLock_POS=extra.createUpGrp(cont_midLock[0], "POS")
# midLock_CON=extra.createUpGrp(cont_midLock[0], "CON")

# midLockBlendPos=pm.createNode("blendColors", name="midLockBlendPos_"+whichLeg)
# midLockBlendRot=pm.createNode("blendColors", name="midLockBlendRot_"+whichLeg)

# target_midLock_IK.translate >> midLockBlendPos.color1
# target_midLock_IK.rotate >> midLockBlendRot.color1

# target_midLock_FK.translate >> midLockBlendPos.color2
# target_midLock_FK.rotate >> midLockBlendRot.color2

# midLockBlendPos.output >> midLock_POS.translate
# midLockBlendRot.output >> midLock_POS.rotate

# cont_FK_IK.fk_ik >> midLockBlendPos.blender
# cont_FK_IK.fk_ik >> midLockBlendRot.blender

# pm.parentConstraint(cont_midLock[0], midLock, mo=True)

### Create End Lock
endLock=pm.spaceLocator(name="endLock_"+whichLeg)
extra.alignTo(endLock, "jInit_Foot_"+whichLeg, 2)
endLock_Ore=extra.createUpGrp(endLock, "_Ore")
endLock_Pos=extra.createUpGrp(endLock, "_Pos")
endLock_Twist=extra.createUpGrp(endLock, "_Twist")
endLockWeight=pm.pointConstraint(jIK_orig_End, jFK_Foot, endLock_Pos, mo=False)
cont_FK_IK.fk_ik >> (endLockWeight+"."+jIK_orig_End+"W0")
fk_ik_rvs.outputX >> (endLockWeight+"."+jFK_Foot+"W1")

pm.parentConstraint(endLock, cont_FK_IK_POS, mo=True)
pm.parent(endLock_Ore, scaleGrp)



endLockRot=pm.parentConstraint(IK_parentGRP, jFK_Foot, endLock, st=("x","y","z"), mo=True)
pm.setAttr(endLockRot.interpType, 0)
cont_FK_IK.fk_ik >> (endLockRot+"."+IK_parentGRP+"W0")
fk_ik_rvs.outputX >> (endLockRot+"."+jFK_Foot+"W1")


###################################
#### CREATE DEFORMATION JOINTS ####
###################################

# UPPERLEG RIBBON

ribbonConnections_upperLeg=cr.createRibbon("jInit_UpLeg_"+whichLeg, "jInit_Knee_"+whichLeg, "up_"+whichLeg, -90)

ribbonStart_paCon_upperLeg_Start=pm.parentConstraint(startLock, ribbonConnections_upperLeg[0], mo=True)
ribbonStart_paCon_upperLeg_End=pm.parentConstraint(midLock, ribbonConnections_upperLeg[1], mo=True)

pm.scaleConstraint(scaleGrp,ribbonConnections_upperLeg[2])

# AUTO AND MANUAL TWIST

#auto
autoTwistThigh=pm.createNode("multiplyDivide", name="autoTwistThigh_"+whichLeg)
cont_thigh.autoTwist >> autoTwistThigh.input2X
ribbonStart_paCon_upperLeg_Start.constraintRotate >> autoTwistThigh.input1

###!!! The parent constrain override should be disconnected like this
pm.disconnectAttr(ribbonStart_paCon_upperLeg_Start.constraintRotateX, ribbonConnections_upperLeg[0].rotateX)

#manual
AddManualTwistThigh=pm.createNode("plusMinusAverage", name=("AddManualTwist_UpperLeg_"+whichLeg))
autoTwistThigh.output >> AddManualTwistThigh.input3D[0]
cont_thigh.manualTwist >> AddManualTwistThigh.input3D[1].input3Dx

#connect to the joint
AddManualTwistThigh.output3D >> ribbonConnections_upperLeg[0].rotate

# LOWERLEG RIBBON

ribbonConnections_lowerLeg=cr.createRibbon("jInit_Knee_"+whichLeg, "jInit_Foot_"+whichLeg, "low_"+whichLeg, 90)

ribbonStart_paCon_lowerLeg_Start=pm.parentConstraint(midLock, ribbonConnections_lowerLeg[0], mo=True)
ribbonStart_paCon_lowerLeg_End=pm.parentConstraint(endLock, ribbonConnections_lowerLeg[1], mo=True)

pm.scaleConstraint(scaleGrp,ribbonConnections_lowerLeg[2])

# AUTO AND MANUAL TWIST

#auto
autoTwistAnkle=pm.createNode("multiplyDivide", name="autoTwistAnkle_"+whichLeg)
cont_FK_IK.autoTwist >> autoTwistAnkle.input2X
ribbonStart_paCon_lowerLeg_End.constraintRotate >> autoTwistAnkle.input1

###!!! The parent constrain override should be disconnected like this
pm.disconnectAttr(ribbonStart_paCon_lowerLeg_End.constraintRotateX, ribbonConnections_lowerLeg[1].rotateX)

#manual
AddManualTwistAnkle=pm.createNode("plusMinusAverage", name=("AddManualTwist_LowerLeg_"+whichLeg))
autoTwistAnkle.output >> AddManualTwistAnkle.input3D[0]
cont_FK_IK.manualTwist >> AddManualTwistAnkle.input3D[1].input3Dx

#connect to the joint
AddManualTwistAnkle.output3D >> ribbonConnections_lowerLeg[1].rotate

# Foot Joint

pm.select(d=True)
jDef_Foot=pm.joint(name="jDef_Foot_"+whichLeg, p=pm.PyNode("jInit_Foot_"+whichLeg).getTranslation(space="world"), radius=1.0)
jDef_Ball=pm.joint(name="jDef_Ball_"+whichLeg, p=pm.PyNode("jInit_Ball_"+whichLeg).getTranslation(space="world"), radius=1.0)
jDef_Toe=pm.joint(name="jDef_Toe_"+whichLeg, p=pm.PyNode("jInit_Toe_"+whichLeg).getTranslation(space="world"), radius=1.0) 

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

###Interpolation Types
##cont_FK_IK.twistInterpolation >> startLockRot.interpType
##cont_FK_IK.twistInterpolation >> MidLockIK_ori.interpType
##cont_FK_IK.twistInterpolation >> MidLockFK_ori.interpType
##cont_FK_IK.twistInterpolation >> endLockRot.interpType

pm.parent(jIK_SC_Root, startLock)
pm.parent(jIK_RP_Root, startLock)
pm.parent(jIK_orig_Root, startLock)
pm.parent(jFK_Root, startLock)

pm.parent(startLock_Ore, scaleGrp)
pm.parent(legStart, scaleGrp)
pm.parent(legEnd, scaleGrp)
pm.parent(IK_parentGRP, scaleGrp)
pm.parent(cont_thigh_OFF, scaleGrp)
pm.parent(target_midLock_IK, scaleGrp)
pm.parent(target_midLock_FK, scaleGrp)
pm.parent(midLock, scaleGrp)
pm.parent(cont_midLock_POS, scaleGrp)

pm.parent(ribbonConnections_upperLeg[2], nonScaleGrp)
pm.parent(ribbonConnections_upperLeg[3], nonScaleGrp)

pm.parent(ribbonConnections_lowerLeg[2], nonScaleGrp)
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

#     else:
#         pm.error("Some or all Leg Locators are missing (or Renamed)")
    
# createLeg("l_leg")



