import pymel.core as pm

import extraProcedures as extra
reload(extra)

import contIcons as icon
reload(icon)

import createSplineIK as spline
reload(spline)

# define related joints
neckStart = pm.PyNode("jInit_neck")
headStart = pm.PyNode("jInit_head")
headEnd = pm.PyNode("jInit_headEnd")
jawStart = pm.PyNode("jInit_jawStart")
jawEnd = pm.PyNode("jInit_jawEnd")

# get necessary distances
neckDist=extra.getDistance(neckStart, headStart)
headDist=extra.getDistance(headStart, headEnd)

# create Controllers

# # neck Controller
neckScale=(neckDist/2, neckDist/2, neckDist/2)
cont_neck = icon.curvedCircle(name="cont_neck", scale=neckScale, location=(neckStart.getTranslation(space="world")))

# # head Controller
headCenterPos = (headStart.getTranslation(space="world")+headEnd.getTranslation(space="world"))/2
headPivPos = headStart.getTranslation(space="world")
headScale = (extra.getDistance(headStart, headEnd)/3)
cont_head = icon.halfDome(name="cont_head", scale=(headScale, headScale, headScale), location=headCenterPos)
pm.rotate(cont_head, (-90, 0, 0))
pm.makeIdentity(cont_head, a=True)
pm.xform(cont_head, piv=headPivPos, ws=True)

# # head Squash Controller
squashCenterPos = headEnd.getTranslation(space="world")
cont_headSquash = icon.circle(name="cont_headSquash", scale=((headScale/2),(headScale/2),(headScale/2)), normal=(0,0,1), location=squashCenterPos)
pm.parent(cont_headSquash, cont_head)

# create spline IK for neck
neckSpline=spline.createSplineIK([neckStart,headStart],"neckSplineIK", 4, dropoff=2)
neckSP_startConnection = neckSpline[0][0]
neckSP_endConnection = neckSpline[0][1]
neckSP_endLock = neckSpline[2]
# # Connect neck start to the neck controller
pm.parentConstraint(cont_neck, neckSP_startConnection, mo=True)
# # Connect neck end to the head controller
pm.parentConstraint(cont_head, neckSP_endConnection, mo=True)

# create spline IK for Head squash
headSpline = spline.createSplineIK([headStart, headEnd], "headSquashSplineIK", 4, dropoff=2)
headSP_startConnection = headSpline[0][0]
headSP_endConnection = headSpline[0][1]
# # Position the head spline IK to end of the neck
pm.pointConstraint(neckSP_endLock, headSP_startConnection, mo=True)
# # orient the head spline to the head controller
pm.orientConstraint(cont_head, headSP_startConnection, mo=True)

pm.parentConstraint(cont_headSquash, headSP_endConnection, mo=True)

## fool proofing

