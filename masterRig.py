## masterRig

import pymel.core as pm

import extraProcedures as extra
reload(extra)

import createArms as arm
reload(arm)

import createLegs as leg
reload(leg)

##create GrandMaster Root

rigName="hoyt"

rootPoint=pm.PyNode("jInit_spine0").getTranslation(space="world")
pm.select(None)
gmRoot=pm.joint(p=rootPoint, name="gmRoot_"+rigName, radius=10)

rightArm=arm.createArm("r_arm")
leftArm=arm.createArm("l_arm")

rightLeg=leg.createLeg("r_leg")
leftLeg=leg.createLeg("l_leg")

test=pm.ls(sl=True)
strTest=test[0].name()
anan=strTest.replace("jInit_","")