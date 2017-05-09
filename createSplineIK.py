## Create splineIK

import pymel.core as pm

refJoints=[pm.PyNode("joint1"), pm.PyNode("joint2"), pm.PyNode("joint3"), pm.PyNode("joint4")]

cuts=5

totalLength=0
rootPoint=refJoints[0].getTranslation(space="world")
splitCount=5
contDistances=[0]
for i in range (0, len(refJoints)):
    currentJointLength=pm.getAttr(refJoints[i].tx)
    totalLength+=currentJointLength
    contDistances.append(currentJointLength)
contDistances.remove(len(contDistances)-1)
del contDistances[len(contDistances)-1]
contDistances.delete(len(contDistances)-1)
## Draw a new joint for spline IK

# starting point will be the same with the ref
# pm.select(d=True)
# splineRoot=pm.joint(p=rootPoint, name=("jDef_splineRoot"))
# splineEnd=pm.joint(p=(rootPoint.x, (rootPoint.y+totalLength), rootPoint.z), name=("jDef_splineEnd"))

rootVc=rootPoint
endVc=(rootPoint.x, (rootPoint.y+totalLength), rootPoint.z)

splitVc=endVc-rootVc
segmentVc=(splitVc/(cuts))
segmentLoc=rootVc+segmentVc
curvePoints=[]
splineJoints=[]
for i in range (0, cuts+1):
    place=rootVc+(segmentVc*(i))
    # pm.spaceLocator(p=place)
    j=pm.joint(p=place, name="jDef_spline"+str(i))
    splineJoints.append(j)
    curvePoints.append(place)
    
splineCurve=pm.curve(name="splineCurve", p=curvePoints)

splineIK=pm.ikHandle(sol="ikSplineSolver", c=splineCurve, sj=splineJoints[0], ee=splineJoints[len(splineJoints)-1], w=1.0)

## Create controller Joints
contJoints=[]
pm.select(d=True)
for i in range (0, cuts+1):
    place=rootVc*(contDistances[i])
    j=pm.joint(p=place, name="jCont_spline"+str(i))
    contJoints.append(j)
    pm.select(d=True)
