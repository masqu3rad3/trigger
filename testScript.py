import pymel.core as pm

import armClass as arm
reload(arm)

import tentacleClass
reload(tentacleClass)

t=tentacleClass.Tentacle()
t.createTentacle(pm.ls(sl=True), "test", npResolution=5.0, jResolution=25.0, blResolution=25.0,dropoff=2.0)

import mrCubic
mrCubic.mrCube(pm.ls("jDef*", type="joint"))



# a=arm.Arm()
# a.createArm(pm.ls(sl=True),suffix="testArm",side="L")