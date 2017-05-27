import time

start = time.time()

## masterRig
import pymel.core as pm
import sys

# sys.path.append("C:/Users/kutlu/Documents/maya/2017/scripts/tik_autorigger")
path = 'C:/Users/Arda/Documents/maya/2017/scripts/tik_autorigger'
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

import createNeck as neck

reload(neck)

rigName = "hoyt"

## get dimensions
spineList = pm.ls("jInit_spine*")
initShouDis = extra.getDistance(pm.PyNode("jInit_Shoulder_l_arm"), pm.PyNode("jInit_Shoulder_r_arm"))
initLegsDis = extra.getDistance(pm.PyNode("jInit_HeelPv_l_leg"), pm.PyNode("jInit_HeelPv_r_leg"))
initUpBodyDis = extra.getDistance(spineList[len(spineList) / 2], spineList[len(spineList) - 1])
initLowBodyDis = extra.getDistance(spineList[0], spineList[len(spineList) / 2])

rootPoint = pm.PyNode("jInit_spine0").getTranslation(space="world")
midPoint = spineList[len(spineList) / 2].getTranslation(space="world")
chestPoint = spineList[len(spineList) - 1].getTranslation(space="world")
neckPoint = pm.PyNode("jInit_neck").getTranslation(space="world")


cont_placement = icon.circle("cont_Placement", (initLegsDis, initLegsDis, initLegsDis))
cont_master = icon.triCircle("cont_Master", (initLegsDis * 1.5, initLegsDis * 1.5, initLegsDis * 1.5))
pm.addAttr(cont_master, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True)
pm.addAttr(cont_master, at="bool", ln="Joints_Visibility", sn="jointVis")
pm.addAttr(cont_master, at="bool", ln="Rig_Visibility", sn="rigVis")
# make the created attributes visible in the channelbox
pm.setAttr(cont_master.contVis, cb=True)
pm.setAttr(cont_master.jointVis, cb=True)
pm.setAttr(cont_master.rigVis, cb=True)

pm.parent(cont_placement, cont_master)

spine = spine.createSpine()
scaleGrp_spine = spine[0]
cont_body = spine[1]
cont_hips = spine[2]
cont_chest = spine[3]
gmRoot = spine[4]
neckPlug = spine[5]
rArmPlug = spine[6]
lArmPlug = spine[7]
nonScaleGrp_spine = spine[8]

pm.parent(cont_body, cont_placement)
pm.scaleConstraint(cont_master, gmRoot)
pm.scaleConstraint(cont_master, scaleGrp_spine)
extra.attrPass(scaleGrp_spine, cont_master, values=True, daisyChain=True, overrideEx=False)

## ARMS

rightArm = arm.createArm("r_arm")
scaleGrp_r_arm = rightArm[0]
cont_IK_hand_r_arm = rightArm[1]
cont_IK_hand_OFF_r_arm = rightArm[2]
cont_Pole_r_arm = rightArm[3]
nonScaleGrp_r_arm = rightArm[4]
pm.parentConstraint(rArmPlug, scaleGrp_r_arm, mo=True) ## attach right arm to the spine
pm.scaleConstraint(cont_master, scaleGrp_r_arm)
pm.scaleConstraint(cont_master, cont_IK_hand_OFF_r_arm)
extra.attrPass(scaleGrp_r_arm, cont_master, values=True, daisyChain=True, overrideEx=False)


leftArm = arm.createArm("l_arm")
scaleGrp_l_arm = leftArm[0]
cont_IK_hand_l_arm = leftArm[1]
cont_IK_hand_OFF_l_arm = leftArm[2]
cont_Pole_l_arm = leftArm[3]
nonScaleGrp_l_arm = leftArm[4]
pm.parentConstraint(lArmPlug, scaleGrp_l_arm, mo=True) ## attach right arm to the spine
pm.scaleConstraint(cont_master, scaleGrp_l_arm)
pm.scaleConstraint(cont_master, cont_IK_hand_OFF_l_arm)
extra.attrPass(scaleGrp_l_arm, cont_master, values=True, daisyChain=True, overrideEx=False)


## LEGS

rightLeg = leg.createLeg("r_leg")
scaleGrp_r_leg = rightLeg[0]
cont_IK_foot_r_leg = rightLeg[1]
cont_Pole_r_leg = rightLeg[2]
nonScaleGrp_r_leg = rightLeg[3]
pm.parentConstraint(gmRoot, scaleGrp_r_leg, mo=True)
pm.scaleConstraint(cont_master, scaleGrp_r_leg)
extra.attrPass(scaleGrp_r_leg, cont_master, values=True, daisyChain=True, overrideEx=False)


leftLeg = leg.createLeg("l_leg")
scaleGrp_l_leg = leftLeg[0]
cont_IK_foot_l_leg = leftLeg[1]
cont_Pole_l_leg = leftLeg[2]
nonScaleGrp_l_leg = leftLeg[3]
pm.parentConstraint(gmRoot, scaleGrp_l_leg, mo=True)
pm.scaleConstraint(cont_master, scaleGrp_l_leg)
extra.attrPass(scaleGrp_l_leg, cont_master, values=True, daisyChain=True, overrideEx=False)


## NECK and HEAD
neckAndHead = neck.createNeck()
neckRoot = neckAndHead[0]
cont_neck = neckAndHead[1]
cont_head = neckAndHead[2]
scaleGrp_neck = neckAndHead[3]
nonScaleGrp_neck = neckAndHead[4]
pm.parentConstraint(neckPlug, neckRoot, mo=True)
pm.scaleConstraint(cont_master, scaleGrp_neck)
extra.attrPass(scaleGrp_neck, cont_master, values=True, daisyChain=True, overrideEx=False)

# ANCHOR SWITCHES
anchorList=[cont_placement, cont_master, cont_hips, cont_chest, cont_neck, cont_head]
extra.spaceSwitcher(cont_IK_hand_r_arm, anchorList)
extra.spaceSwitcher(cont_IK_hand_l_arm, anchorList)
extra.spaceSwitcher(cont_IK_foot_r_leg, anchorList)
extra.spaceSwitcher(cont_IK_foot_l_leg, anchorList)

extra.spaceSwitcher(cont_Pole_l_arm, anchorList)
extra.spaceSwitcher(cont_Pole_r_arm, anchorList)
extra.spaceSwitcher(cont_Pole_l_leg, anchorList)
extra.spaceSwitcher(cont_Pole_r_leg, anchorList)

extra.spaceSwitcher(cont_head, anchorList, mode="point", defaultVal=5)
extra.spaceSwitcher(cont_head, anchorList, mode="orient")
extra.spaceSwitcher(cont_neck, [cont_placement, cont_master, cont_hips, cont_chest], mode="orient", defaultVal=4)

# # GOOD PARENTING

rootGroup=pm.group(name=rigName, em=True)
extra.lockAndHide(rootGroup, ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"])
pm.parent(scaleGrp_r_arm, rootGroup)
pm.parent(scaleGrp_l_arm, rootGroup)
pm.parent(scaleGrp_r_leg, rootGroup)
pm.parent(scaleGrp_l_leg, rootGroup)
pm.parent(scaleGrp_neck, rootGroup)
pm.parent(scaleGrp_spine, rootGroup)

pm.parent(nonScaleGrp_r_arm, rootGroup)
pm.parent(nonScaleGrp_l_arm, rootGroup)
pm.parent(nonScaleGrp_r_leg, rootGroup)
pm.parent(nonScaleGrp_l_leg, rootGroup)
pm.parent(nonScaleGrp_neck, rootGroup)
pm.parent(nonScaleGrp_spine, rootGroup)

pm.parent(gmRoot, rootGroup)
pm.parent(cont_master, rootGroup)

# COLOR CODING
index = 17
extra.colorize(cont_master, index)
extra.colorize(cont_placement, index)

end = time.time()
print(end - start)
