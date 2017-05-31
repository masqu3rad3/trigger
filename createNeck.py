import pymel.core as pm

import extraProcedures as extra

reload(extra)

import contIcons as icon

reload(icon)

import createTwistSpline as spline

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
    neckDist = extra.getDistance(neckStart, headStart)
    headDist = extra.getDistance(headStart, headEnd)

    # create Controllers

    # # neck Controller
    neckScale = (neckDist / 2, neckDist / 2, neckDist / 2)
    cont_neck = icon.curvedCircle(name="cont_neck", scale=neckScale, location=(neckStart.getTranslation(space="world")))
    cont_neck_ORE = extra.createUpGrp(cont_neck, "ORE")

    # # head Controller
    headCenterPos = (headStart.getTranslation(space="world") + headEnd.getTranslation(space="world")) / 2
    headPivPos = headStart.getTranslation(space="world")
    headScale = (extra.getDistance(headStart, headEnd) / 3)
    cont_head = icon.halfDome(name="cont_head", scale=(headScale, headScale, headScale), location=headCenterPos)
    cont_head_OFF = extra.createUpGrp(cont_head, "OFF")
    cont_head_ORE = extra.createUpGrp(cont_head, "ORE")
    pm.rotate(cont_head, (-90, 0, 0))
    pm.makeIdentity(cont_head, a=True)

    pm.xform(cont_head, piv=headPivPos, ws=True)
    pm.makeIdentity(cont_head, a=True)

    # # head Squash Controller
    squashCenterPos = headEnd.getTranslation(space="world")
    cont_headSquash = icon.circle(name="cont_headSquash", scale=((headScale / 2), (headScale / 2), (headScale / 2)),
                                  normal=(0, 0, 1), location=squashCenterPos)
    pm.parent(cont_headSquash, cont_head)

    # create spline IK for neck
    neckRootLoc = pm.spaceLocator(name="neckRootLoc")
    extra.alignTo(neckRootLoc, neckStart)

    neckSpline = spline.createTspline([neckStart, headStart], "neckSplineIK", 4, dropoff=2)
    neckSP_IKCrv_ORE_List = neckSpline[0]
    neckSP_startConnection = neckSpline[1]
    # pm.parent(neckSP_startConnection, neckRootLoc)
    neckSP_endConnection = neckSpline[2]
    neckSP_endLock = neckSpline[3]
    neckSP_scaleGrp = neckSpline[4]
    neckSP_nonScaleGrp = neckSpline[5]
    neckSP_passCont = neckSpline[6]
    neckSP_defJoints = neckSpline[7]
    neckSP_noTouchListList = neckSpline[8]
    # # Connect neck start to the neck controller
    pm.orientConstraint(cont_neck, neckSP_startConnection,
                        mo=True)  # This will be position constrained to the spine(or similar)
    pm.pointConstraint(neckSP_startConnection, cont_neck_ORE)
    # # Connect neck end to the head controller
    pm.parentConstraint(cont_head, neckSP_endConnection, mo=True)
    # # pass Stretch controls from the splineIK to neck controller
    extra.attrPass(neckSP_passCont, cont_neck)

    # # Connect the scale to the scaleGrp
    scaleGrp.scale >> neckSP_scaleGrp.scale

    # create spline IK for Head squash
    headSpline = spline.createTspline([headStart, headEnd], "headSquashSplineIK", 4, dropoff=2)
    headSP_IKCrv_ORE_List = headSpline[0]
    headSP_startConnection = headSpline[1]
    headSP_endConnection = headSpline[2]
    headSP_endLock = headSpline[3]
    headSP_scaleGrp = headSpline[4]
    headSP_nonScaleGrp = headSpline[5]
    headSP_passCont = headSpline[6]
    headSP_defJoints = headSpline[7]
    headSP_noTouchListList = headSpline[8]

    # # Position the head spline IK to end of the neck
    pm.pointConstraint(neckSP_endLock, headSP_startConnection, mo=True)
    # # orient the head spline to the head controller
    pm.orientConstraint(cont_head, headSP_startConnection, mo=True)

    pm.parentConstraint(cont_headSquash, headSP_endConnection, mo=True)
    # # pass Stretch controls from the splineIK to neck controller
    extra.attrPass(headSP_passCont, cont_headSquash)

    # # Connect the scale to the scaleGrp
    scaleGrp.scale >> headSP_scaleGrp.scale



    # GOOD PARENTING
    pm.parent(neckSP_IKCrv_ORE_List[0], neckRootLoc)
    pm.parent(neckRootLoc, scaleGrp)
    pm.parent(neckSP_IKCrv_ORE_List[len(headSP_IKCrv_ORE_List) - 1], scaleGrp)
    pm.parent(neckSP_endLock, scaleGrp)
    pm.parent(neckSP_scaleGrp, scaleGrp)

    pm.parent(cont_neck_ORE, scaleGrp)
    # pm.parent(cont_head_ORE, scaleGrp)

    pm.parent(headSP_IKCrv_ORE_List[0], scaleGrp)
    pm.parent(headSP_IKCrv_ORE_List[len(headSP_IKCrv_ORE_List) - 1], scaleGrp)
    pm.parent(headSP_endLock, scaleGrp)
    pm.parent(headSP_scaleGrp, scaleGrp)

    pm.parent(neckSP_nonScaleGrp, nonScaleGrp)
    pm.parent(headSP_nonScaleGrp, nonScaleGrp)

    # GOOD RIDDANCE
    # pm.delete(neckSP_IKCrv_ORE_List)
    # pm.delete(headSP_IKCrv_ORE_List)

    # RIG VISIBILITY

    # global visibilities attributes

    pm.addAttr(scaleGrp, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True)
    pm.addAttr(scaleGrp, at="bool", ln="Joints_Visibility", sn="jointVis", defaultValue=True)
    pm.addAttr(scaleGrp, at="bool", ln="Rig_Visibility", sn="rigVis", defaultValue=False)
    # make the created attributes visible in the channelbox
    pm.setAttr(scaleGrp.contVis, cb=True)
    pm.setAttr(scaleGrp.jointVis, cb=True)
    pm.setAttr(scaleGrp.rigVis, cb=True)

    # global control visibilities

    scaleGrp.contVis >> cont_head_ORE.v
    scaleGrp.contVis >> cont_neck_ORE.v
    scaleGrp.contVis >> cont_headSquash.v

    # global joint visibilities

    for i in headSP_defJoints:
        scaleGrp.jointVis >> i.v

    for i in neckSP_defJoints:
        scaleGrp.jointVis >> i.v

    # global rig visibilities

    scaleGrp.rigVis >> headSP_IKCrv_ORE_List[0].v
    scaleGrp.rigVis >> headSP_IKCrv_ORE_List[len(headSP_IKCrv_ORE_List) - 1].v

    scaleGrp.rigVis >> neckSP_IKCrv_ORE_List[0].v
    scaleGrp.rigVis >> neckSP_IKCrv_ORE_List[len(headSP_IKCrv_ORE_List) - 1].v

    for lst in headSP_noTouchListList:
        for i in lst:
            scaleGrp.rigVis >> i.v

    for lst in neckSP_noTouchListList:
        for i in lst:
            scaleGrp.rigVis >> i.v

    # //TODO

    # FOOL PROOF
    extra.lockAndHide(cont_headSquash, ["sx", "sy", "sz", "v"])
    extra.lockAndHide(cont_head, ["v"])
    extra.lockAndHide(cont_neck, ["tx", "ty", "tz", "v"])

    # COLORIZE
    index = 17
    extra.colorize(cont_head, index)
    extra.colorize(cont_neck, index)
    extra.colorize(cont_headSquash, index)

    # RETURN

    # # returns: (neck root, neck controller, head controller, scale group, non-scale group, cont_head_OFF)
    returnTuple = (neckRootLoc, cont_neck, cont_head, scaleGrp, nonScaleGrp, cont_head_OFF)
    return returnTuple
    # //TODO
