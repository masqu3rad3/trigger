import pymel.core as pm

import extraProcedures as extra
reload(extra)

import contIcons as icon
reload(icon)

import createSplineIK as spline
reload(spline)

def createNeck():
    # define groups
    scaleGrp = pm.group(name="scaleGrp_NeckAndHead", em=True)
    nonScaleGrp = pm.group(name="nonScaleGrp_NeckAndHead", em=True)

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
    cont_neck_ORE = extra.createUpGrp(cont_neck, "ORE")

    # # head Controller
    headCenterPos = (headStart.getTranslation(space="world")+headEnd.getTranslation(space="world"))/2
    headPivPos = headStart.getTranslation(space="world")
    headScale = (extra.getDistance(headStart, headEnd)/3)
    cont_head = icon.halfDome(name="cont_head", scale=(headScale, headScale, headScale), location=headCenterPos)
    cont_head_ORE = extra.createUpGrp(cont_head, "ORE")
    pm.rotate(cont_head_ORE, (-90, 0, 0))

    pm.xform(cont_head, piv=headPivPos, ws=True)
    pm.makeIdentity(cont_head, a=True)

    # # head Squash Controller
    squashCenterPos = headEnd.getTranslation(space="world")
    cont_headSquash = icon.circle(name="cont_headSquash", scale=((headScale/2),(headScale/2),(headScale/2)), normal=(0,0,1), location=squashCenterPos)
    pm.parent(cont_headSquash, cont_head)

    # create spline IK for neck
    neckRootLoc = pm.spaceLocator(name="neckRootLoc")
    extra.alignTo(neckRootLoc, neckStart)
    neckSpline=spline.createSplineIK([neckStart,headStart],"neckSplineIK", 4, dropoff=2)
    neckSP_startConnection = neckSpline[0][0]
    pm.parent(neckSP_startConnection, neckRootLoc)
    neckSP_endConnection = neckSpline[0][1]
    neckSP_endLock = neckSpline[2]
    neckSP_scaleGrp = neckSpline[3]
    neckSP_nonScaleGrp = neckSpline[4]
    neckSP_passCont = neckSpline[5]
    # # Connect neck start to the neck controller
    pm.orientConstraint(cont_neck, neckSP_startConnection, mo=True) # This will be position constrained to the spine(or similar)
    pm.pointConstraint(neckSP_startConnection, cont_neck_ORE)
    # # Connect neck end to the head controller
    pm.parentConstraint(cont_head, neckSP_endConnection, mo=True)
    # # pass Stretch controls from the splineIK to neck controller
    extra.attrPass(neckSP_passCont, cont_neck)

    # create spline IK for Head squash
    headSpline = spline.createSplineIK([headStart, headEnd], "headSquashSplineIK", 4, dropoff=2)
    headSP_startConnection = headSpline[0][0]
    headSP_endConnection = headSpline[0][1]
    headSP_endLock = headSpline[2]
    headSP_scaleGrp = headSpline[3]
    headSP_nonScaleGrp = headSpline[4]
    headSP_passCont = headSpline[5]
    # # Position the head spline IK to end of the neck
    pm.pointConstraint(neckSP_endLock, headSP_startConnection, mo=True)
    # # orient the head spline to the head controller
    pm.orientConstraint(cont_head, headSP_startConnection, mo=True)

    pm.parentConstraint(cont_headSquash, headSP_endConnection, mo=True)
    # # pass Stretch controls from the splineIK to neck controller
    extra.attrPass(headSP_passCont, cont_headSquash)

    # GROUPING
    pm.parent(neckRootLoc, scaleGrp)
    pm.parent(neckSP_endConnection, scaleGrp)
    pm.parent(neckSP_endLock, scaleGrp)
    pm.parent(neckSP_scaleGrp, scaleGrp)

    pm.parent(cont_neck_ORE, scaleGrp)
    pm.parent(cont_head_ORE, scaleGrp)

    pm.parent(headSP_startConnection, scaleGrp)
    pm.parent(headSP_endConnection, scaleGrp)
    pm.parent(headSP_endLock, scaleGrp)
    pm.parent(headSP_scaleGrp, scaleGrp)

    pm.parent(neckSP_nonScaleGrp, nonScaleGrp)
    pm.parent(headSP_nonScaleGrp, nonScaleGrp)


    # FOOL PROOF
    extra.lockAndHide(cont_headSquash, ["sx", "sy", "sz", "v"])
    extra.lockAndHide(cont_head, ["v"])
    extra.lockAndHide(cont_neck, ["tx", "ty", "tz", "v"])

    # COLORIZE
    index = 17
    extra.colorize(cont_head, index)
    extra.colorize(cont_neck, index)
    extra.colorize(cont_headSquash, index)

    # RIG VISIBILITY

    # //TODO

    # RETURN

    # # returns: (neck root, head controller, scale group, non-scale group)
    returnTuple = (neckRootLoc, cont_neck, cont_head, scaleGrp, nonScaleGrp)
    return returnTuple
    # //TODO