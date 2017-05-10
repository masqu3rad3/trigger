## Create splineIK

import pymel.core as pm

import extraProcedures as extra
reload(extra)


#refJoints=[pm.PyNode("joint1"), pm.PyNode("joint2"), pm.PyNode("joint3"), pm.PyNode("joint4"), pm.PyNode("joint5"), pm.PyNode("joint6"), pm.PyNode("joint7")]
refJoints=pm.selected()

dropoff=2
cuts=32
extra.getDistance(refJoints[0], refJoints[0])
totalLength=0
rootPoint=refJoints[0].getTranslation(space="world")
splitCount=5
contDistances=[]
contCurves=[]
ctrlDistance=0

for i in range (0, len(refJoints)):
    if i==0:
        tmin=0
    else:
        tmin=i-1
    currentJointLength=extra.getDistance(refJoints[i], refJoints[tmin])
    ctrlDistance=currentJointLength+ctrlDistance
    totalLength+=currentJointLength
    contDistances.append(ctrlDistance)

rootVc=rootPoint
endVc=(rootPoint.x, (rootPoint.y+totalLength), rootPoint.z)

splitVc=endVc-rootVc
segmentVc=(splitVc/(cuts))
segmentLoc=rootVc+segmentVc
curvePoints=[]
splineJoints=[]
pm.select(d=True)

## Create deformation Joints
for i in range (0, cuts+1):
    place=rootVc+(segmentVc*(i))
    j=pm.joint(p=place, name="jDef_spline"+str(i))
    splineJoints.append(j)
    curvePoints.append(place)
    
splineCurve=pm.curve(name="splineCurve", p=curvePoints)

splineIK=pm.ikHandle(sol="ikSplineSolver", createCurve=False, c=splineCurve, sj=splineJoints[0], ee=splineJoints[len(splineJoints)-1], w=1.0)

## Create controller Joints
contJoints=[]
pm.select(d=True)
for i in range (0, len(contDistances)):
    ctrlVc=splitVc.normal()*contDistances[i]
    place=rootVc+(ctrlVc)
    j=pm.joint(p=place, name="jCont_spline"+str(i), radius=5)
    contJoints.append(j)
    pm.select(d=True)
    
pm.select(contJoints)
pm.select(splineCurve, add=True)
pm.skinCluster(dr=dropoff, tsb=True)

for i in range (0, len(contJoints)):
    extra.alignTo(contJoints[i], refJoints[i],0)
    ## Create control Curves
    cont_Curve=pm.circle(name="cont_spline_"+str(i), nr=(0,1,0))
    scaleRatio=(totalLength/len(contJoints))
    pm.setAttr(cont_Curve[0].scale, (scaleRatio, scaleRatio, scaleRatio))
    cont_Curve_ORE=extra.createUpGrp(cont_Curve[0],"ORE")
    extra.alignTo(cont_Curve_ORE, contJoints[i],2)
    pm.parentConstraint(cont_Curve[0], contJoints[i])
    contCurves.append(cont_Curve)

    
## Create Stretch and Squash Nodes
curveInfo=pm.arclen(splineCurve, ch=True)
initialLength=pm.getAttr(curveInfo.arcLength)
for i in range (0, len(splineJoints)):
    

    lengthMult=pm.createNode("multiplyDivide")
    pm.setAttr(lengthMult.operation, 2)
    curveInfo.arcLength >> lengthMult.input1X
    pm.setAttr(lengthMult.input2X, initialLength)
    lengthMult.outputX >> splineJoints[i].sy
    
