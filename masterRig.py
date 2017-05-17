## masterRig

import pymel.core as pm

import extraProcedures as extra
reload(extra)

import contIcons as icon
reload(icon)

import createArms as arm
reload(arm)

import createLegs as leg
reload(leg)

import createSplineIK as spline
reload(spline)

##create GrandMaster Root
initShouDis=extra.getDistance(pm.PyNode("jInit_Shoulder_l_arm"), pm.PyNode("jInit_Shoulder_r_arm"))
initLegsDis=extra.getDistance(pm.PyNode("jInit_HeelPv_l_leg"), pm.PyNode("jInit_HeelPv_r_leg"))

rigName="hoyt"

rootPoint=pm.PyNode("jInit_spine0").getTranslation(space="world")
pm.select(None)
gmRoot=pm.joint(p=rootPoint, name="gmRoot_"+rigName, radius=10)
contHipsScale=(initLegsDis/2,initLegsDis/2,initLegsDis/2)
cont_hips=icon.waist("cont_Hips_"+rigName, contHipsScale, location=rootPoint)
contBodyScale=(initLegsDis/1.5,initLegsDis/1.5,initLegsDis/1.5)
cont_body=icon.square("cont_Body_"+rigName, contBodyScale, location=rootPoint)

# rightArm=arm.createArm("r_arm")
# leftArm=arm.createArm("l_arm")

rightLeg=leg.createLeg("r_leg")
leftLeg=leg.createLeg("l_leg")

spine=spline.createSplineIK(pm.ls("jInit_spine*"), "tst", 8, dropoff=2)

pm.parentConstraint(gmRoot, rightLeg[0], mo=True)
pm.parentConstraint(gmRoot, leftLeg[0], mo=True)

