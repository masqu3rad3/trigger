## masterRig
import pymel.core as pm
import sys
#sys.path.append("C:/Users/kutlu/Documents/maya/2017/scripts/tik_autorigger")
path='C:/Users/Arda/Documents/maya/2017/scripts/tik_autorigger'
if not path in sys.path:
    sys.path.append(path)

import extraProcedures as extra
reload(extra)

import contIcons as icon
reload(icon)

import createArms as arm
reload(arm)

import createLegs as leg
reload(leg)

import createSpine as spine
reload(spine)

rigName="hoyt"

## get dimensions
spineList=pm.ls("jInit_spine*")

initShouDis=extra.getDistance(pm.PyNode("jInit_Shoulder_l_arm"), pm.PyNode("jInit_Shoulder_r_arm"))
initLegsDis=extra.getDistance(pm.PyNode("jInit_HeelPv_l_leg"), pm.PyNode("jInit_HeelPv_r_leg"))
initUpBodyDis=extra.getDistance(spineList[len(spineList)/2], spineList[len(spineList)-1])
initLowBodyDis=extra.getDistance(spineList[0], spineList[len(spineList)/2])

rootPoint=pm.PyNode("jInit_spine0").getTranslation(space="world")
midPoint=spineList[len(spineList)/2].getTranslation(space="world")
chestPoint=spineList[len(spineList)-1].getTranslation(space="world")
neckPoint=pm.PyNode("jInit_neck").getTranslation(space="world")


cont_placement=icon.circle("cont_Place_"+rigName, (initLegsDis,initLegsDis,initLegsDis))
cont_master=icon.circle("cont_Master_"+rigName, (initLegsDis*1.5,initLegsDis*1.5,initLegsDis*1.5))

pm.parent(cont_placement, cont_master)

spine=spine.createSpine()
spineScaleGrp=spine[0]
cont_body=spine[1]
cont_chest=spine[2]
gmRoot=spine[3]
endLock_spine=spine[4]
spineNonScaleGrp=spine[5]

pm.parent(cont_body, cont_placement)
pm.scaleConstraint(cont_master, gmRoot)
pm.scaleConstraint(cont_master, spineScaleGrp)

## ARMS

rightArm=arm.createArm("r_arm")
scaleGrp_r_arm=rightArm[0]
cont_IK_hand_r_arm=rightArm[1]
cont_IK_hand_OFF_r_arm=rightArm[2]
cont_Pole_r_arm=rightArm[3]
nonScaleGrp_r_arm=rightArm[4]
pm.parentConstraint(endLock_spine, scaleGrp_r_arm, mo=True) ## attach right arm to the spine
pm.scaleConstraint(cont_master, scaleGrp_r_arm)
## //TODO space switch will be added

leftArm=arm.createArm("l_arm")
scaleGrp_l_arm=leftArm[0]
cont_IK_hand_l_arm=leftArm[1]
cont_IK_hand_OFF_l_arm=leftArm[2]
cont_Pole_l_arm=leftArm[3]
nonScaleGrp_l_arm=leftArm[4]
pm.parentConstraint(endLock_spine, scaleGrp_l_arm, mo=True) ## attach right arm to the spine
pm.scaleConstraint(cont_master, scaleGrp_l_arm)
## //TODO space switch will be added

## LEGS

rightLeg=leg.createLeg("r_leg")
scaleGrp_r_leg=rightLeg[0]
cont_IK_foot_r_leg=rightLeg[1]
cont_Pole_r_leg=rightLeg[2]
nonScaleGrp_r_leg=rightLeg[3]
pm.parentConstraint(gmRoot, scaleGrp_r_leg, mo=True)
pm.scaleConstraint(cont_master, scaleGrp_r_leg)

leftLeg=leg.createLeg("l_leg")
scaleGrp_l_leg=leftLeg[0]
cont_IK_foot_r_leg=leftLeg[1]
cont_Pole_l_leg=leftLeg[2]
nonScaleGrp_l_leg=leftLeg[3]
pm.parentConstraint(gmRoot, scaleGrp_l_leg, mo=True)
pm.scaleConstraint(cont_master, scaleGrp_l_leg)


## color coding
index = 17
extra.colorize(cont_master, index)
extra.colorize(cont_placement, index)

# pm.parentConstraint(gmRoot, leftLeg[0], mo=True)



