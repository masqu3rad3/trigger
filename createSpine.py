import pymel.core as pm
import collections
import extraProcedures as extra
reload(extra)
import contIcons as icon
reload(icon)

import createSplineIK as spline
reload(spline)

def createSpine():
    spineList = pm.ls("jInit_spine*")

    initShouDis = extra.getDistance(pm.PyNode("jInit_Shoulder_l_arm"), pm.PyNode("jInit_Shoulder_r_arm"))
    initLegsDis = extra.getDistance(pm.PyNode("jInit_HeelPv_l_leg"), pm.PyNode("jInit_HeelPv_r_leg"))
    initUpBodyDis = extra.getDistance(spineList[len(spineList) / 2], spineList[len(spineList) - 1])
    initLowBodyDis = extra.getDistance(spineList[0], spineList[len(spineList) / 2])

    rootPoint = pm.PyNode("jInit_spine0").getTranslation(space="world")
    midPoint = spineList[len(spineList) / 2].getTranslation(space="world")
    chestPoint = spineList[len(spineList) - 1].getTranslation(space="world")
    neckPoint = pm.PyNode("jInit_neck").getTranslation(space="world")
    armPoint_r_arm = pm.PyNode("jInit_Shoulder_r_arm").getTranslation(space="world")
    armPoint_l_arm = pm.PyNode("jInit_Shoulder_l_arm").getTranslation(space="world")

    # # Create Plug Joints
    pm.select(None)
    jChestPlug = pm.joint(name="jChestPlug", p=chestPoint)
    pm.select(None)
    jHeadPlug = pm.joint(name="jHeadPlug", p=neckPoint)
    pm.select(None)
    jArmPlug_r_arm = pm.joint(name="jArmPlug_r_arm", p=armPoint_r_arm)
    pm.select(None)
    jArmPlug_l_arm = pm.joint(name="jArmPlug_l_arm", p=armPoint_l_arm)

    # parent upper plug joints
    pm.parent(jArmPlug_l_arm, jArmPlug_r_arm, jHeadPlug, jChestPlug)

    pm.select(None)
    gmRoot = pm.joint(p=rootPoint, name="gmRoot", radius=10)
    contHipsScale = (initLegsDis / 1.5, initLegsDis / 1.5, initLegsDis / 1.5)
    cont_hips = icon.waist("cont_Hips", contHipsScale, location=rootPoint)
    contBodyScale = (initLegsDis*0.75, initLegsDis*0.75, initLegsDis*0.75)
    cont_body = icon.square("cont_Body", contBodyScale, location=rootPoint)

    cont_chest = icon.cube("cont_Chest", (initShouDis, initUpBodyDis / 2, initUpBodyDis / 2),
                           location=(chestPoint + neckPoint) / 2)
    pm.xform(cont_chest, piv=chestPoint)

    spine=spline.createSplineIK(pm.ls("jInit_spine*"), "spine", 4, dropoff=2)
    bottomConnection= spine[0][0]
    upConnection= spine[1]
    midConnection= spine[0][len(spine[0])/2]
    endPositionLock= spine[2]
    scaleGrp=spine[3]
    nonScaleGrp=spine[4]
    passCont=spine[5]

    # # connect the spine root to the master root
    pm.parentConstraint(gmRoot, bottomConnection, mo=True)
    # # connect the spine end
    pm.parentConstraint(cont_chest, upConnection, mo=True)
    # # connect the master root to the hips controller
    pm.parentConstraint(cont_hips, gmRoot, mo=True)

    # # connect upper plug points to the spine and orient it to the chest controller
    pm.pointConstraint(endPositionLock, jChestPlug)
    pm.orientConstraint(cont_chest, jChestPlug)

    # # pass Stretch controls from the splineIK to neck controller
    extra.attrPass(passCont, cont_chest)

    ## create locators on the mid controller to be used as alignment
    midSpineLocA = pm.spaceLocator(name="midSpineLocA", p=midPoint)
    midSpineLocB = pm.spaceLocator(name="midSpineLocB", p=midPoint)

    pm.parentConstraint(midSpineLocA, midSpineLocB, midConnection, mo=True)



    contSpineFKAScale = (initLegsDis / 2, initLegsDis / 2, initLegsDis / 2)
    cont_spineFK_A_01 = icon.circle("cont_SpineFK_A01", contSpineFKAScale, location=rootPoint)
    cont_spineFK_A_02 = icon.circle("cont_SpineFK_A02", contSpineFKAScale, location=midPoint)
    cont_spineFK_A_03 = icon.circle("cont_SpineFK_A03", contSpineFKAScale, location=chestPoint)

    contSpineFKBScale = (initLegsDis / 2.5, initLegsDis / 2.5, initLegsDis / 2.5)
    cont_spineFK_B_01 = icon.ngon("cont_SpineFK_B01", contSpineFKBScale, location=rootPoint)
    cont_spineFK_B_02 = icon.ngon("cont_SpineFK_B02", contSpineFKBScale, location=midPoint)
    cont_spineFK_B_03 = icon.ngon("cont_SpineFK_B03", contSpineFKBScale, location=chestPoint)

    # good parenting
    pm.parent(midSpineLocA, cont_chest)
    pm.parent(cont_chest, cont_spineFK_A_03)
    pm.parent(cont_spineFK_A_03, cont_spineFK_A_02)
    pm.parent(cont_spineFK_A_02, cont_spineFK_A_01)
    pm.parent(cont_spineFK_A_01, cont_body)
    pm.parent(spine[0], scaleGrp) # contcurve Ore s -> scaleGrp
    pm.parent(jChestPlug, scaleGrp)

    pm.parent(midSpineLocB, cont_hips)
    pm.parent(cont_hips, cont_spineFK_B_01)
    pm.parent(cont_spineFK_B_01, cont_spineFK_B_02)
    pm.parent(cont_spineFK_B_02, cont_spineFK_B_03)
    pm.parent(cont_spineFK_B_03, cont_body)
    pm.parent(endPositionLock, scaleGrp)

    ## fool proofing
    extra.lockAndHide(cont_spineFK_A_01, ["tx", "ty", "tz", "sx", "sy", "sz", "v"])
    extra.lockAndHide(cont_spineFK_A_02, ["tx", "ty", "tz", "sx", "sy", "sz", "v"])
    extra.lockAndHide(cont_spineFK_A_03, ["tx", "ty", "tz", "sx", "sy", "sz", "v"])
    extra.lockAndHide(cont_spineFK_B_01, ["tx", "ty", "tz", "sx", "sy", "sz", "v"])
    extra.lockAndHide(cont_spineFK_B_02, ["tx", "ty", "tz", "sx", "sy", "sz", "v"])
    extra.lockAndHide(cont_spineFK_B_03, ["tx", "ty", "tz", "sx", "sy", "sz", "v"])

    ## color coding
    index = 17
    indexIK = 20
    indexFKA = 30
    indexFKB = 31
    extra.colorize(cont_body, index)
    extra.colorize(cont_chest, index)
    extra.colorize(cont_hips, index)
    extra.colorize(cont_spineFK_A_01, indexFKA)
    extra.colorize(cont_spineFK_A_02, indexFKA)
    extra.colorize(cont_spineFK_A_03, indexFKA)
    extra.colorize(cont_spineFK_B_01, indexFKB)
    extra.colorize(cont_spineFK_B_02, indexFKB)
    extra.colorize(cont_spineFK_B_03, indexFKB)

    #return (scaleGrp, cont_chest, master Root, head plug, rightArmPlug, leftArmPlug, nonScaleGrp)
    returnTuple=(scaleGrp, cont_body, cont_hips, cont_chest, gmRoot, jHeadPlug, jArmPlug_r_arm, jArmPlug_l_arm, nonScaleGrp)
    return returnTuple
