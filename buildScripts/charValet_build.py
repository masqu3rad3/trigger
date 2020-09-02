
from maya import cmds
from trigger.actions import import_export
from trigger.actions import kinematics
from trigger.actions import shapes
from trigger.actions import weights

from trigger.library import functions
from trigger.actions import import_export
from trigger.library import deformers
from trigger.base import session
from trigger.library import controllers
from trigger.library import functions
from trigger.utils import jointsOnBlendshape
from trigger.utils import parentToSurface

import_act = import_export.ImportExport()
sessionHandler = session.Session()
weightHandler = weights.Weights()
icon_handler = controllers.Icon()

# reset scene
cmds.file(new=True, force=True)
# open the previous rig
cmds.file("/mnt/ps-storage01/vfx_hgd_000/SG_ROOT/eg2/assets/Character/charValet/RIG/work/maya/rootCharValetAvA.v002.ma",open=True, force=True)
cmds.hide(cmds.listRelatives("bn_head", children=True))
cmds.hide(cmds.listRelatives("grp_faceExtra", children=True))

# import the mesh grp

# import_act.import_alembic("/mnt/ps-storage01/vfx_hgd_000/SG_ROOT/eg2/assets/Character/charValet/MDL/publish/caches/charValetAvA.v008.abc")
import_act.import_scene(
    "/mnt/ps-storage01/vfx_hgd_000/SG_ROOT/eg2/assets/Character/charValet/MDL/publish/maya/charValetAvA.v031.ma")
final_meshes = functions.getMeshes("charValetAvA")

# build the BASEs of Local Rigs
face_meshes = ["charValetAvA_hair_GEO",
               "charValetAvA_hat_GEO",
               "charValetAvA_left_innerEye_GEO",
               "charValetAvA_right_innerEye_GEO",
               "charValetAvA_right_outerEye_GEO",
               "charValetAvA_left_outerEye_GEO",
               "charValetAvA_face_IDskin",
               "charValetAvA_tongue_GEO",
               "charValetAvA_teethUpper_GEO",
               "charValetAvA_teethLower_GEO"
               ]
               
               
local_meshes = []
for mesh in face_meshes:
    # print mesh
    local_BS_blendshape = "%s_local_bs" % mesh
    local_meshes.append(deformers.localize(mesh, local_BS_blendshape, "%s_local" % mesh, group_name="local_BS_rig_grp"))

TWK_MESH = "charValetAvA_face_IDskin_local"
local_tweakers_blendshape = "local_TWK_rig_bs"
local_meshes.append(
    deformers.localize(TWK_MESH, local_tweakers_blendshape, "%s_TWK" % TWK_MESH, group_name="local_TWK_rig_grp"))
    

###############################
####### LOCAL BS RIG ##########
###############################


sessionHandler = session.Session()
sessionHandler.load_session(
    "/mnt/ps-storage01/vfx_hgd_000/SG_ROOT/eg2/assets/Character/charValet/RIG/work/maya/triggerData/guides/valet_local_bs_guides.json",
    reset_scene=False)


# move the local bs joints and make the labels invisible
local_bs_joints = cmds.listRelatives("trigger_refGuides", children=True, type="joint", ad=True)
_ = [cmds.setAttr("%s.drawLabel" % jnt, 0) for jnt in local_bs_joints]
cmds.parent(cmds.listRelatives("trigger_refGuides", children=True), "local_BS_rig_grp")
cmds.delete("trigger_refGuides")

# TONGUE RIG
############
tongue_joints = cmds.ls("tongue_*_jDef")

icon_handler = controllers.Icon()

tongue_conts = []
for jnt in tongue_joints:
    cmds.makeIdentity(jnt, a=True)
    cont, _ = icon_handler.createIcon("Circle", iconName=jnt.replace("jDef", "cont"), normal=(1, 0, 0))
    functions.alignTo(cont, jnt, position=True, rotation=True)
    offset_cont = functions.createUpGrp(cont, "offset")
    if tongue_conts:
        cmds.parent(offset_cont, tongue_conts[-1])
    tongue_conts.append(cont)
    functions.colorize(cont, "C")
    cmds.connectAttr("%s.rotate" % cont, "%s.rotate" % jnt)

# create a hinge at the jaw location to move the tongue conts with jaw
jaw_follow_grp = cmds.group(name="jaw_follow_grp", em=True)
functions.alignTo(jaw_follow_grp, "jaw_jDef")
cmds.connectAttr("jaw_jDef.rotate", "%s.rotate" % jaw_follow_grp)
cmds.parent(functions.getParent(tongue_conts[0]), jaw_follow_grp)

head_follow_grp = cmds.group(name="tongue_headFollow", em=True)
cmds.parentConstraint("bn_head", head_follow_grp, mo=False)

cmds.parent(jaw_follow_grp, head_follow_grp)
tongue_ctrl_grp = cmds.group(head_follow_grp, name="tongue_ctrl_grp")
cmds.parent(tongue_ctrl_grp, "Rig_Controllers")

import_act.import_scene(
    "/mnt/ps-storage01/vfx_hgd_000/SG_ROOT/eg2/assets/Character/charMax/RIG/work/maya/triggerData/UI/faceUI.mb")
# import_act.import_alembic("/home/arda.kutlu/localProjects/EG2_playground_200617/_TRANSFER/ALEMBIC/faceUI.abc")
cmds.setAttr("face_ctrls_grp.translate", -36, 170, 0)
cmds.parentConstraint("ctrl_head", "face_ctrls_grp", mo=True)
cmds.parent("face_ctrls_grp", "Rig_Controllers")

hook_blendshapes = "hook_blendshapes"

# TEETH RIG
###########
# upper_teeth_cont, _ = icon_handler.createIcon("Circle", iconName="upperTeeth_cont", scale=(3, 3, 3), normal=(0, 1, 0))
# lower_teeth_cont, _ = icon_handler.createIcon("Circle", iconName="lowerTeeth_cont", scale=(3, 3, 3), normal=(0, 1, 0))
# upper_teeth_cont_offset = functions.createUpGrp(upper_teeth_cont, "offset")
# lower_teeth_cont_offset = functions.createUpGrp(lower_teeth_cont, "offset")
# functions.alignTo(upper_teeth_cont_offset, "upperTeeth_jDef", position=True, rotation=True)
# functions.alignTo(lower_teeth_cont_offset, "lowerTeeth_jDef", position=True, rotation=True)

# upper_teeth_jaw_follow = cmds.group(name="upperTeeth_jawFollow", em=True)
# lower_teeth_jaw_follow = cmds.group(name="lowerTeeth_jawFollow", em=True)
# functions.alignTo(upper_teeth_jaw_follow, "jawN_jDef", position=True, rotation=True)
# functions.alignTo(lower_teeth_jaw_follow, "jaw_jDef", position=True, rotation=True)

# cmds.parent(upper_teeth_cont_offset, upper_teeth_jaw_follow)
# cmds.parent(lower_teeth_cont_offset, lower_teeth_jaw_follow)

# teeth_head_follow = cmds.group([upper_teeth_jaw_follow, lower_teeth_jaw_follow], name="teeth_headFollow")

# functions.drive_attrs("jawN_jDef.t", "%s.t" % upper_teeth_jaw_follow)
# functions.drive_attrs("jawN_jDef.r", "%s.r" % upper_teeth_jaw_follow)
# functions.drive_attrs("jaw_jDef.t", "%s.t" % lower_teeth_jaw_follow)
# functions.drive_attrs("jaw_jDef.r", "%s.r" % lower_teeth_jaw_follow)

# cmds.connectAttr("%s.xformMatrix" % upper_teeth_cont, "upperTeeth_jDef.offsetParentMatrix")
# cmds.connectAttr("%s.xformMatrix" % lower_teeth_cont, "lowerTeeth_jDef.offsetParentMatrix")
# cmds.parentConstraint("bn_head", teeth_head_follow, mo=True)
# teeth_ctrls_grp = cmds.group(teeth_head_follow, name="teeth_ctrls_grp")
# cmds.parent(teeth_ctrls_grp, "Rig_Controllers")

upper_teeth_cont, _ = icon_handler.createIcon("Circle", iconName="upperTeeth_cont", scale=(3, 3, 3), normal=(0, 1, 0))
lower_teeth_cont, _ = icon_handler.createIcon("Circle", iconName="lowerTeeth_cont", scale=(3, 3, 3), normal=(0, 1, 0))
upper_teeth_cont_offset = functions.createUpGrp(upper_teeth_cont, "offset")
lower_teeth_cont_offset = functions.createUpGrp(lower_teeth_cont, "offset")
functions.alignTo(upper_teeth_cont_offset, "upperTeeth_jDef", position=True, rotation=True)
functions.alignTo(lower_teeth_cont_offset, "lowerTeeth_jDef", position=True, rotation=True)

# freeze transformations of joints and move joint orientation to the upper grp
cmds.makeIdentity("upperTeeth_jDef", a=True)
cmds.makeIdentity("lowerTeeth_jDef", a=True)

# create a zero locator
upper_zero = cmds.spaceLocator(name="upperTeeth_zero")[0]
functions.alignTo(upper_zero, "upperTeeth_jDef", position=True, rotation=True)
upper_zero_off = functions.createUpGrp(upper_zero, "off")
cmds.parentConstraint(upper_zero, "upperTeeth_jDef", mo=True)
lower_zero = cmds.spaceLocator(name="lowerTeeth_zero")[0]
functions.alignTo(lower_zero, "lowerTeeth_jDef", position=True, rotation=True)
lower_zero_off = functions.createUpGrp(lower_zero, "off")
cmds.parentConstraint(lower_zero, "lowerTeeth_jDef", mo=True)

cmds.parent(upper_zero_off, "jawN_jDef")
cmds.parent(lower_zero_off, "jaw_jDef")

upper_teeth_jaw_follow = cmds.group(name="upperTeeth_jawFollow", em=True)
lower_teeth_jaw_follow = cmds.group(name="lowerTeeth_jawFollow", em=True)
functions.alignTo(upper_teeth_jaw_follow, "jawN_jDef", position=True, rotation=True)
functions.alignTo(lower_teeth_jaw_follow, "jaw_jDef", position=True, rotation=True)

cmds.parent(upper_teeth_cont_offset, upper_teeth_jaw_follow)
cmds.parent(lower_teeth_cont_offset, lower_teeth_jaw_follow)

teeth_head_follow = cmds.group([upper_teeth_jaw_follow, lower_teeth_jaw_follow], name="teeth_headFollow")

functions.drive_attrs("jawN_jDef.t", "%s.t" % upper_teeth_jaw_follow)
functions.drive_attrs("jawN_jDef.r", "%s.r" % upper_teeth_jaw_follow)
functions.drive_attrs("jaw_jDef.t", "%s.t" % lower_teeth_jaw_follow)
functions.drive_attrs("jaw_jDef.r", "%s.r" % lower_teeth_jaw_follow)

cmds.connectAttr("%s.t" % upper_teeth_cont, "%s.t" % upper_zero)
cmds.connectAttr("%s.r" % upper_teeth_cont, "%s.r" % upper_zero)
cmds.connectAttr("%s.t" % lower_teeth_cont, "%s.t" % lower_zero)
cmds.connectAttr("%s.r" % lower_teeth_cont, "%s.r" % lower_zero)

cmds.parentConstraint("bn_head", teeth_head_follow, mo=True)
teeth_ctrls_grp = cmds.group(teeth_head_follow, name="teeth_ctrls_grp")
cmds.parent(teeth_ctrls_grp, "Rig_Controllers")

# MOUTH RIG
###########
mouth_cont_X = "%s.mouth_tx" % hook_blendshapes
mouth_cont_Y = "%s.mouth_ty" % hook_blendshapes
mouth_cont_Z = "mouth_z_cont.tx"
jaw_tz = "jaw_jDef.tz"
jaw_tz_val = cmds.getAttr(jaw_tz)
jaw_rx = "jaw_jDef.rx"
jaw_rx_val = cmds.getAttr(jaw_rx)
jaw_ry = "jaw_jDef.ry"
jaw_ry_val = cmds.getAttr(jaw_ry)
jaw_rz = "jaw_jDef.rz"
jaw_rz_val = cmds.getAttr(jaw_rz)
jawN_rx = "jawN_jDef.rx"
jawN_rx_val = cmds.getAttr(jawN_rx)
jawN_ry = "jawN_jDef.ry"
jawN_ry_val = cmds.getAttr(jawN_ry)

# driven keys

cmds.undoInfo(ock=True)
# Controller Y Connections
cmds.setDrivenKeyframe(jaw_rx, cd=mouth_cont_Y, v=jaw_rx_val, dv=0.0, itt="spline", ott="linear")
cmds.setDrivenKeyframe(jaw_rx, cd=mouth_cont_Y, v=-60, dv=-10, itt="linear", ott="linear")
cmds.setDrivenKeyframe(jaw_rx, cd=mouth_cont_Y, v=-15, dv=10, itt="linear", ott="linear")

cmds.setDrivenKeyframe(jawN_rx, cd=mouth_cont_Y, v=jawN_rx_val, dv=0, itt="linear", ott="linear")
cmds.setDrivenKeyframe(jawN_rx, cd=mouth_cont_Y, v=-15, dv=10, itt="linear", ott="linear")

# Controller X Connections
cmds.setDrivenKeyframe(jaw_ry, cd=mouth_cont_X, v=jaw_ry_val, dv=0.0, itt="spline", ott="spline")
cmds.setDrivenKeyframe(jaw_ry, cd=mouth_cont_X, v=20, dv=-10, itt="linear", ott="linear")
cmds.setDrivenKeyframe(jaw_ry, cd=mouth_cont_X, v=-20, dv=10, itt="linear", ott="linear")

cmds.setDrivenKeyframe(jaw_rz, cd=mouth_cont_X, v=jaw_rz_val, dv=0.0, itt="spline", ott="spline")
cmds.setDrivenKeyframe(jaw_rz, cd=mouth_cont_X, v=-40, dv=-10, itt="spline", ott="spline")
cmds.setDrivenKeyframe(jaw_rz, cd=mouth_cont_X, v=40, dv=10, itt="spline", ott="spline")

# Controller Z Connections
cmds.setDrivenKeyframe(jaw_tz, cd=mouth_cont_Z, v=jaw_tz_val, dv=0.0, itt="spline", ott="spline")
cmds.setDrivenKeyframe(jaw_tz, cd=mouth_cont_Z, v=-3.5, dv=-10, itt="linear", ott="linear")
cmds.setDrivenKeyframe(jaw_tz, cd=mouth_cont_Z, v=1, dv=10, itt="linear", ott="linear")
cmds.undoInfo(cck=True)

# EYES RIG
###########
# duplicate the eye joints to ingest into the body rig (aim controls)
eye_L_local = "eye_L_local_jDef"
eye_R_local = "eye_R_local_jDef"
eye_L_local_offset = functions.createUpGrp(eye_L_local, "offset")
eye_R_local_offset = functions.createUpGrp(eye_R_local, "offset")

eye_L = cmds.duplicate(eye_L_local, name="eye_L_jnt")[0]
eye_R = cmds.duplicate(eye_R_local, name="eye_R_jnt")[0]
eye_L_offset = functions.createUpGrp(eye_L, "offset")
eye_R_offset = functions.createUpGrp(eye_R, "offset")
cmds.parent(eye_L_offset, "bn_head")
cmds.parent(eye_R_offset, "bn_head")

# offset the eyeLook at to the correct position
# eyeLookat_offset = functions.createUpGrp("crtl_eyeLookat", "offset")
# cmds.setAttr("%s.ty" % eyeLookat_offset, 5.725296945384471)

# first layer eye movement
cmds.aimConstraint("ctrl_L_eyeLookat", eye_L, weight=1, upVector=(0, 1, 0), worldUpObject='ctrl_head',
                   worldUpType="objectrotation", offset=(0, 0, 0), aimVector=(0, 0, -1), worldUpVector=(0, 1, 0))
cmds.aimConstraint("ctrl_R_eyeLookat", eye_R, weight=1, upVector=(0, 1, 0), worldUpObject='ctrl_head',
                   worldUpType="objectrotation", offset=(0, 0, 0), aimVector=(0, 0, -1), worldUpVector=(0, 1, 0))
cmds.connectAttr("%s.rotate" % eye_L, "%s.rotate" % eye_L_local_offset)
cmds.connectAttr("%s.rotate" % eye_R, "%s.rotate" % eye_R_local_offset)

# secong layer eye movement
for side in "LR":
    setrange = cmds.createNode("setRange", name="eye_%s_cont_setRange" % side)
    cmds.setAttr("%s.min" % setrange, 55, -55, 0)
    cmds.setAttr("%s.max" % setrange, -55, 55, 0)
    cmds.setAttr("%s.oldMin" % setrange, -10, -10, 0)
    cmds.setAttr("%s.oldMax" % setrange, 10, 10, 0)
    cmds.connectAttr("eye_%s_cont.translate" % side, "%s.value" % setrange)
    cmds.connectAttr("%s.outValueX" % setrange, "eye_%s_local_jDef.ry" % side)
    cmds.connectAttr("%s.outValueY" % setrange, "eye_%s_local_jDef.rx" % side)

# eyeFollows
# extract rotations from the nested controllers
for side in "LR":
    extractor = cmds.spaceLocator(name="eye_rotate_extractor_%s_" % side)[0]
    cmds.parent(extractor, "local_BS_rig_grp")
    functions.alignTo(extractor, "eye_%s_local_jDef" % side, position=True, rotation=True)
    cmds.orientConstraint("eye_%s_local_jDef" % side, extractor)

    #     # make follow groups matching with the eye joints
    # # for side in "LR":
    eyeFollowGrp = cmds.group(name="eyeFollow_%s_jnt_offset" % side, em=True)
    cmds.parent(eyeFollowGrp, "local_BS_rig_grp")
    functions.alignTo(eyeFollowGrp, "eye_%s_local_jDef" % side, position=True, rotation=True)
    cmds.parent("upper_eyeLid_%s_jDef" % side, eyeFollowGrp)
    cmds.parent("lower_eyeLid_%s_jDef" % side, eyeFollowGrp)

    # driven keys
    cmds.setDrivenKeyframe("%s.rx" % eyeFollowGrp, cd="%s.rx" % extractor, v=0.0, dv=0.0, itt="spline", ott="spline")
    cmds.setDrivenKeyframe("%s.rx" % eyeFollowGrp, cd="%s.rx" % extractor, v=-10, dv=-28.61, itt="spline", ott="spline")
    cmds.setDrivenKeyframe("%s.rx" % eyeFollowGrp, cd="%s.rx" % extractor, v=18, dv=19.97, itt="spline", ott="spline")
    cmds.setDrivenKeyframe("%s.ry" % eyeFollowGrp, cd="%s.ry" % extractor, v=0.0, dv=0.0, itt="spline", ott="spline")
    cmds.setDrivenKeyframe("%s.ry" % eyeFollowGrp, cd="%s.ry" % extractor, v=-18, dv=-42.27, itt="spline", ott="spline")
    cmds.setDrivenKeyframe("%s.ry" % eyeFollowGrp, cd="%s.ry" % extractor, v=18, dv=42.27, itt="spline", ott="spline")

# Eye Lids
for side in "LR":
    cmds.setDrivenKeyframe("upper_eyeLid_%s_jDef.rx" % side, cd="upper_eyeLid_%s_cont.ty" % side, v=0.0, dv=0.0,
                           itt="linear", ott="linear")
    cmds.setDrivenKeyframe("upper_eyeLid_%s_jDef.rx" % side, cd="upper_eyeLid_%s_cont.ty" % side, v=-68, dv=-19,
                           itt="linear", ott="linear")
    cmds.setDrivenKeyframe("upper_eyeLid_%s_jDef.rx" % side, cd="upper_eyeLid_%s_cont.ty" % side, v=22, dv=3.50,
                           itt="linear", ott="linear")

    cmds.setDrivenKeyframe("lower_eyeLid_%s_jDef.rx" % side, cd="lower_eyeLid_%s_cont.ty" % side, v=0.0, dv=0.0,
                           itt="linear", ott="linear")
    cmds.setDrivenKeyframe("lower_eyeLid_%s_jDef.rx" % side, cd="lower_eyeLid_%s_cont.ty" % side, v=-25, dv=-3,
                           itt="linear", ott="linear")
    cmds.setDrivenKeyframe("lower_eyeLid_%s_jDef.rx" % side, cd="lower_eyeLid_%s_cont.ty" % side, v=68, dv=19,
                           itt="linear", ott="linear")

#############################################################


# # BLENDSHAPES
# #############
# import_act.import_alembic("/mnt/ps-storage01/vfx_hgd_000/SG_ROOT/eg2/assets/Character/charMax/RIG/publish/caches/charMaxBlendshapes.v002.abc")
# blendshapes = functions.getMeshes("blendshapes_grp")
# # filter out X meshes and neutral
# blendshapes = [shape for shape in blendshapes if not shape.endswith("X") and shape != "neutral"]

# for shape in blendshapes:
#     hook_attr = shape.replace("Corrective", "")
#     deformers.connect_bs_targets("%s.%s" %(hook_blendshapes, hook_attr), {"charMaxAvA_local": shape})

# # eyelid correctives= Override hook node input to correct it in bone level
# LU_eyelid_multMatrix = cmds.createNode("multMatrix", name="LU_eyelid_multMatrix")
# LU_eyelid_decMatrix = cmds.createNode("decomposeMatrix", name = "LU_eyelid_decMatrix")
# cmds.connectAttr("upper_eyeLid_L_jDef.worldMatrix[0]", "%s.matrixIn[0]" % LU_eyelid_multMatrix)
# cmds.connectAttr("%s.matrixSum" % LU_eyelid_multMatrix, "%s.inputMatrix" % LU_eyelid_decMatrix)
# functions.drive_attrs("%s.outputRotateX" % LU_eyelid_decMatrix, "%s.ULeyesWide" % hook_blendshapes, driver_range=[0, 22], driven_range=[0,1])

# LD_eyelid_multMatrix = cmds.createNode("multMatrix", name="LD_eyelid_multMatrix")
# LD_eyelid_decMatrix = cmds.createNode("decomposeMatrix", name = "LD_eyelid_decMatrix")
# cmds.connectAttr("lower_eyeLid_L_jDef.worldMatrix[0]", "%s.matrixIn[0]" % LD_eyelid_multMatrix)
# cmds.connectAttr("%s.matrixSum" % LD_eyelid_multMatrix, "%s.inputMatrix" % LD_eyelid_decMatrix)
# functions.drive_attrs("%s.outputRotateX" % LD_eyelid_decMatrix, "%s.DLeyesWide" % hook_blendshapes, driver_range=[0, -25], driven_range=[0,1])

# RU_eyelid_multMatrix = cmds.createNode("multMatrix", name="RU_eyelid_multMatrix")
# RU_eyelid_decMatrix = cmds.createNode("decomposeMatrix", name = "RU_eyelid_decMatrix")
# cmds.connectAttr("upper_eyeLid_R_jDef.worldMatrix[0]", "%s.matrixIn[0]" % RU_eyelid_multMatrix)
# cmds.connectAttr("%s.matrixSum" % RU_eyelid_multMatrix, "%s.inputMatrix" % RU_eyelid_decMatrix)
# functions.drive_attrs("%s.outputRotateX" % RU_eyelid_decMatrix, "%s.UReyesWide" % hook_blendshapes, driver_range=[0, 22], driven_range=[0,1])

# RD_eyelid_multMatrix = cmds.createNode("multMatrix", name="RD_eyelid_multMatrix")
# RD_eyelid_decMatrix = cmds.createNode("decomposeMatrix", name = "RD_eyelid_decMatrix")
# cmds.connectAttr("lower_eyeLid_L_jDef.worldMatrix[0]", "%s.matrixIn[0]" % RD_eyelid_multMatrix)
# cmds.connectAttr("%s.matrixSum" % RD_eyelid_multMatrix, "%s.inputMatrix" % RD_eyelid_decMatrix)
# functions.drive_attrs("%s.outputRotateX" % RD_eyelid_decMatrix, "%s.DReyesWide" % hook_blendshapes, driver_range=[0, -25], driven_range=[0,1])

# # LIPS_SEAL
# ###########

# # create an inbetween joint
# between_jnt = cmds.joint(name="betweenJaw_jDef")
# cmds.parentConstraint(["jaw_jDef", "jawN_jDef"], between_jnt, mo=False)
# cmds.parent(between_jnt, "local_BS_rig_grp")

# lip_seal_mesh = cmds.duplicate("neutral", name="charMaxAvA_closeMouth")[0]
# # make sure its correct pos
# cmds.parent(lip_seal_mesh, "local_BS_rig_grp")
# cmds.setAttr("%s.translate" % lip_seal_mesh, 0, 0, 0)
# cmds.setAttr("%s.rotate" % lip_seal_mesh, 0, 0, 0)

# local_meshes.append(lip_seal_mesh)

# # apply the same bs to this shit
# for shape in blendshapes:
#     hook_attr = shape.replace("Corrective", "")
#     deformers.connect_bs_targets("%s.%s" %(hook_blendshapes, hook_attr), {lip_seal_mesh: shape})

# # THE SEAL MESH WILL BE ADDED AFTER SKINCLUSTERS


#############################################################################

###############################
####### TWEAKERS RIG ##########
###############################

sessionHandler.load_session(
    "/mnt/ps-storage01/vfx_hgd_000/SG_ROOT/eg2/assets/Character/charValet/RIG/work/maya/triggerData/guides/valet_twk_guides.json",
    reset_scene=False)

# sessionHandler.load_session("/mnt/ps-storage01/vfx_hgd_000/SG_ROOT/eg2/assets/Character/charMax/RIG/work/maya/triggerData/guides/max_local_bs_guides.json", reset_scene=False)
# move the local bs joints and make the labels invisible
local_twk_joints = cmds.listRelatives("trigger_refGuides", children=True, type="joint", ad=True)
_ = [cmds.setAttr("%s.drawLabel" % jnt, 0) for jnt in local_twk_joints]
cmds.parent(cmds.listRelatives("trigger_refGuides", children=True), "local_TWK_rig_grp")
cmds.delete("trigger_refGuides")

# create controllers on tweaker joints (except root)
local_twk_joints.remove("twk_root_C_jDef")
twk_conts = []
twk_cont_offsets = []
for jnt in local_twk_joints:
    cont, _ = icon_handler.createIcon("Diamond", iconName=jnt.replace("_jDef", "_cont"))
    functions.alignTo(cont, jnt, position=True, rotation=True)
    twk_conts.append(cont)
    twk_cont_offsets.append(functions.createUpGrp(cont, "offset"))

tweaker_conts_grp = cmds.group(twk_cont_offsets, name="twk_ctrls_grp")
cmds.parent(tweaker_conts_grp, "Rig_Controllers")

# define the main face mesh
main_face_mesh = "charValetAvA_face_IDskin"

## ALL CONTROLLERS must have the same basename with corresponding joints
## Example: twk_chin_C_jDef >> twk_chin_C_cont

## ALL JOINTs must be FROZEN. (No value on rotation channels)
_ = [cmds.makeIdentity(node, a=True) for node in local_twk_joints]

# create offset groups
joint_offsets = [functions.createUpGrp(jnt, suffix="offset") for jnt in local_twk_joints]

for jnt_off, jnt in zip(joint_offsets, local_twk_joints):
    # transfer jointOrientations to the offset group
    jointOrient = cmds.getAttr("%s.jointOrient" % jnt)[0]
    cmds.setAttr("%s.rotate" % jnt_off, *jointOrient)
    cmds.setAttr("%s.jointOrient" % jnt, 0, 0, 0)

    controller = jnt.replace("_jDef", "_cont")
    if not cmds.objExists(controller):
        cmds.error("CONTROLLER MISSING => %s" % controller)
    jointsOnBlendshape.jointOnBlendshapes(joint=str(jnt_off), controller=str(controller), surface=str(main_face_mesh),
                                          attach_mode="pointConstraint")

follicle_shapes = cmds.ls(type="follicle")
follicle_transforms = map(lambda x: functions.getParent(x), follicle_shapes)
follicle_grp = cmds.group(follicle_transforms, name="follicle_grp")
cmds.parent(follicle_grp, "local_TWK_rig_grp")

functions.drive_attrs("tweakers_onOff_cont.tx", "%s.v" % tweaker_conts_grp, driver_range=[0, -10], driven_range=[0, 1])


               
################################################
############### SKINCLUSTERS ###################
################################################

weights_root = "/mnt/ps-storage01/vfx_hgd_000/SG_ROOT/eg2/assets/Character/charValet/RIG/work/maya/triggerData/weights/"

############### LOAD WEIGHTS #################
all_meshes = final_meshes + local_meshes
for mesh in all_meshes:
    weight_file_path = os.path.join(weights_root, "%s.json" % mesh)
    if os.path.isfile(weight_file_path):
        weightHandler.create_deformer(os.path.join(weights_root, weight_file_path))
        
#############################################################


################################################
############### STRETCHY RIG ###################
################################################

# Emma Stretchy Face Build Script
stretch_grp = "local_STRETCH_rig_grp"
if not cmds.objExists(stretch_grp):
    cmds.group(name=stretch_grp, em=True)

from trigger.actions import kinematics
from trigger.actions import shapes

# create a temporary mesh for ffd boundaries
a = cmds.duplicate("charValetAvA_face_IDskin")
b = cmds.duplicate("charValetAvA_hat_GEO")
stretchy_mesh = cmds.polyUnite(a, b, ch=False)[0]

# Define other objects that will stretch ALL MESHES NEEEDS TO BE BLENDSHAPED to final Mesh
other_meshes = ["charValetAvA_face_IDskin_local",
                "charValetAvA_hat_GEO_local",
                "charValetAvA_hair_GEO_local",
                "charValetAvA_left_innerEye_GEO_local",
                "charValetAvA_right_innerEye_GEO_local",
                "charValetAvA_right_outerEye_GEO_local",
                "charValetAvA_left_outerEye_GEO_local",
                "charValetAvA_tongue_GEO_local",
                "charValetAvA_teethUpper_GEO_local",
                "charValetAvA_teethLower_GEO_local",
                ]

t_session = session.Session()

# # save the guides
# t_session.save_session("/home/arda.kutlu/EG2_playground/guideData/max_stretchyFace.json")

# load the guides
session_path = "/mnt/ps-storage01/vfx_hgd_000/SG_ROOT/eg2/assets/Character/charValet/RIG/work/maya/triggerData/guides/valet_stretchyFace.json"
t_session.load_session(session_path, reset_scene=False)

# build kinematics
root_joint = "root_c1"
t_kinematics = kinematics.Kinematics(root_joint, create_switchers=True)
t_kinematics.action()

# TODO: This should be implemented into trigger.library.deformers module
# Create the Lattice Deformer
# ---------------------------
res = (4, 16, 4)
local_inf = (4, 4, 4)

lattice_deformer, lattice_points, lattice_base = cmds.lattice(
    stretchy_mesh,
    divisions=res,
    cp=1,
    ldv=local_inf,
    ol=True,
    objectCentered=True,
    name="%s_ffd" % "valet_head_stretch",
)

# get the deformer set for lattice
lattice_set = cmds.listConnections(lattice_deformer, s=False, d=True, type="objectSet")[0]

# Add other objects to the set
for mesh in other_meshes:
    cmds.sets(mesh, fe=lattice_set)

# lattice attributes
cmds.setAttr("{0}.outsideLattice".format(lattice_deformer), 2)
cmds.setAttr("{0}.outsideFalloffDist".format(lattice_deformer), 7)

# Skincluster the joints to the lattice deformer
def_joints = [jnt for jnt in t_kinematics.totalDefJoints if "socket" not in jnt.lower() and "jDef" in jnt]
skincluster = cmds.skinCluster(
    lattice_points,
    def_joints,
    normalizeWeights=1,
    name="stretchyFaceFFD_skincluster",
    toSelectedBones=True,
)[0]

# Load Weightsw
# weights_path = "/mnt/ps-storage01/vfx_hgd_000/SG_ROOT/eg2/assets/Character/charZalika/RIG/work/maya/triggerData/weights/charZalikaAvA_top_idWhitePVC_GEO_local_bs.json"
# bs_deformer = "charZalikaAvA_top_idWhitePVC_GEO_local_bs"
# weightHandler.load_weights(deformer=bs_deformer, file_path=weights_path)

# delete the temporary boundary mesh
cmds.delete(stretchy_mesh)

##############################
# EXTRA Volume factor addition
#######################[Start]
volume_factors = cmds.ls("volume_Factor_*")

remap_nodes = []
for count, volume_factor in enumerate(volume_factors):
    # create a remap value for each
    remap = cmds.createNode("remapValue", name="remap_%s" % volume_factor)
    remap_nodes.append(remap)
    cmds.setAttr("%s.inputValue" % remap, count)
    cmds.connectAttr("%s.outValue" % remap, "%s.input2Y" % volume_factor)
    cmds.connectAttr("%s.outValue" % remap, "%s.input2Z" % volume_factor)

# set the attributes for the first remap
first_remap = remap_nodes[0]
# make an arc
cmds.setAttr("%s.value[0].value_Position" % first_remap, 0.0)
cmds.setAttr("%s.value[0].value_Interp" % first_remap, 2)
cmds.setAttr("%s.value[0].value_FloatValue" % first_remap, 0.0)

cmds.setAttr("%s.value[1].value_Position" % first_remap, 0.5)
cmds.setAttr("%s.value[1].value_Interp" % first_remap, 2)
cmds.setAttr("%s.value[1].value_FloatValue" % first_remap, 1.0)

cmds.setAttr("%s.value[2].value_Position" % first_remap, 1.0)
cmds.setAttr("%s.value[2].value_Interp" % first_remap, 2)
cmds.setAttr("%s.value[2].value_FloatValue" % first_remap, 0.0)

cmds.setAttr("%s.inputMax" % first_remap, len(volume_factors))

cmds.setAttr("%s.outputMin" % first_remap, 0)
cmds.setAttr("%s.outputMax" % first_remap, -2)

# chain link attributes of the remap nodes
link_attrs = ["value[0].value_Position",
              "value[0].value_Interp",
              "value[0].value_FloatValue",
              "value[1].value_Position",
              "value[1].value_Interp",
              "value[1].value_FloatValue",
              "value[2].value_Position",
              "value[2].value_Interp",
              "value[2].value_FloatValue",
              "inputMin",
              "inputMax",
              "outputMin",
              "outputMax"]

for target_remap in remap_nodes[1:]:
    for attr in link_attrs:
        cmds.connectAttr("%s.%s" % (first_remap, attr), "%s.%s" % (target_remap, attr))

functions.create_attribute("Spine_Chest_cont", attr_name="falloffTweak", nice_name="Falloff Tweak", attr_type="enum",
                           enum_list="---------")
functions.create_attribute("Spine_Chest_cont", attr_name="startPosition", nice_name="Start Position", attr_type="float",
                           min_value=0, max_value=100, default_value=0)
functions.create_attribute("Spine_Chest_cont", attr_name="startValue", nice_name="Start Value", attr_type="float",
                           min_value=0, max_value=100, default_value=0)
functions.create_attribute("Spine_Chest_cont", attr_name="midPosition", nice_name="Mid Position", attr_type="float",
                           min_value=0, max_value=100, default_value=50)
functions.create_attribute("Spine_Chest_cont", attr_name="midValue", nice_name="Mid Value", attr_type="float",
                           min_value=0, max_value=100, default_value=100)
functions.create_attribute("Spine_Chest_cont", attr_name="endPosition", nice_name="End Position", attr_type="float",
                           min_value=0, max_value=100, default_value=0)
functions.create_attribute("Spine_Chest_cont", attr_name="endValue", nice_name="End Value", attr_type="float",
                           min_value=0, max_value=100, default_value=0)

functions.drive_attrs("Spine_Chest_cont.startPosition", "%s.value[0].value_Position" % remap_nodes[0],
                      driver_range=[0, 100], driven_range=[0, 1])
functions.drive_attrs("Spine_Chest_cont.startValue", "%s.value[0].value_FloatValue" % remap_nodes[0],
                      driver_range=[0, 100], driven_range=[0, 1])
functions.drive_attrs("Spine_Chest_cont.midPosition", "%s.value[1].value_Position" % remap_nodes[0],
                      driver_range=[0, 100], driven_range=[0, 1])
functions.drive_attrs("Spine_Chest_cont.midValue", "%s.value[1].value_FloatValue" % remap_nodes[0],
                      driver_range=[0, 100], driven_range=[0, 1])
functions.drive_attrs("Spine_Chest_cont.endPosition", "%s.value[2].value_Position" % remap_nodes[0],
                      driver_range=[0, 100], driven_range=[0, 1])
functions.drive_attrs("Spine_Chest_cont.endValue", "%s.value[2].value_FloatValue" % remap_nodes[0],
                      driver_range=[0, 100], driven_range=[0, 1])

#######################[End]

# Create Live rig controllers and direct connect stretch rig controllers to these
# TODO:
stretch_top_ctrl, _ = icon_handler.createIcon("Cube", iconName="Stretch_top_cont")
stretch_top_ctrl_offset = functions.createUpGrp(stretch_top_ctrl, "offset")
functions.alignTo(stretch_top_ctrl_offset, "Spine_Chest_cont", position=True, rotation=True)

stretch_down_ctrl, _ = icon_handler.createIcon("Cube", iconName="Stretch_down_cont")
stretch_down_ctrl_offset = functions.createUpGrp(stretch_down_ctrl, "offset")
functions.alignTo(stretch_down_ctrl_offset, "Spine_Hips_cont", position=True, rotation=True)
# stretch_top_head_attach = functions.createUpGrp(stretch_top_ctrl_offset, "headAttach")

stretch_head_attach = cmds.group(name="stretch_headAttach", em=True)
cmds.parentConstraint("bn_head", stretch_head_attach, mo=False)
cmds.parent([stretch_top_ctrl_offset, stretch_down_ctrl_offset], stretch_head_attach)

cmds.parent(stretch_head_attach, "Rig_Controllers")
cmds.connectAttr("%s.translate" % stretch_top_ctrl, "Spine_Chest_cont.translate")
cmds.connectAttr("%s.rotate" % stretch_top_ctrl, "Spine_Chest_cont.rotate")
cmds.connectAttr("%s.translate" % stretch_down_ctrl, "Spine_Hips_cont.translate")
cmds.connectAttr("%s.rotate" % stretch_down_ctrl, "Spine_Hips_cont.rotate")

functions.lockAndHide(stretch_top_ctrl, ["sx", "sy", "sz", "v"])
functions.lockAndHide(stretch_down_ctrl, ["sx", "sy", "sz", "v"])

functions.attrPass("Spine_Chest_cont", stretch_top_ctrl, inConnections=True, outConnections=True,
                   keepSourceAttributes=False, values=True, daisyChain=False, overrideEx=False)

## CLEANUP
cmds.rename("trigger_grp", "trigger_stretch_grp")
cmds.parent(functions.getParent(lattice_base), "trigger_stretch_grp")

cmds.parent("trigger_stretch_grp", stretch_grp)

# delete excess data
cmds.delete("trigger_refGuides")

#########################################
## FINAL CLEANUP & DISPLAY ADJUSTMENTS ##12
#########################################

# # replace adjusted Shapes
from trigger.actions import shapes

reload(shapes)
shapesHandler = shapes.Shapes()

# # visibility connections
cmds.connectAttr("ctrl_character.ctrlVis_face", "face_ctrlBound.visibility")

# all shapes need to be visible prior to replace!
cmds.setAttr("tweakers_onOff_cont.tx", -10)
shapesHandler.import_shapes("/mnt/ps-storage01/vfx_hgd_000/SG_ROOT/eg2/assets/Character/charValet/RIG/work/maya/triggerData/shapes/valet_control_shapes.abc")
cmds.setAttr("tweakers_onOff_cont.tx", 0)

# # hide the local groups
cmds.hide("local_BS_rig_grp")
cmds.hide("local_TWK_rig_grp")
cmds.hide("local_STRETCH_rig_grp")
# delete old meshes
# cmds.delete(["Emma_BodyNone", "Emma_Chair", "Emma_Hair", "Emma_Hands", "Emma_Head"])

# # delete blendshape grp
# # cmds.delete("blendshapes_grp")

# hide old rig elemets
cmds.hide("ctrl_faceRigPanel")
# colorize
for cont in twk_conts:
    if "_L_" in cont:
        functions.colorize(cont, "L")
    elif "_R_" in cont:
        functions.colorize(cont, "R")
    else:
        functions.colorize(cont, "C")
functions.colorize("Stretch_top_cont", "C")
functions.colorize("Stretch_down_cont", "C")

cmds.setAttr("%s.Preserve_Volume" % stretch_top_ctrl, 1)

# Good Parenting
rig_grp = cmds.group(name="rig_grp", em=True)
renderGeo_grp = cmds.group(name="renderGeo_grp", em=True)
cmds.parent(renderGeo_grp, rig_grp)

cmds.parent("charGroup", rig_grp)
cmds.parent("local_BS_rig_grp", "charGroup")
cmds.parent("local_TWK_rig_grp", "charGroup")
cmds.parent("local_STRETCH_rig_grp", "charGroup")
functions.lockAndHide(rig_grp)
functions.lockAndHide("charGroup")
functions.lockAndHide("charValetAvA")
cmds.parent("charValetAvA", renderGeo_grp)


# # Fix the texture paths
# possibleFileHolders = cmds.listRelatives("charMax", ad=True, type=["mesh", "nurbsSurface"], fullPath=True)
# allFileNodes = _getFileNodes(possibleFileHolders)
# for file_node in allFileNodes:
#     oldAbsPath = os.path.normpath(cmds.getAttr("%s.fileTextureName" %file_node))
#     relative_path = (oldAbsPath.split("maya/"))[1]
#     cmds.setAttr("%s.fileTextureName" % file_node, relative_path, type="string")


# kill the turtle
turtleNodes = ["TurtleDefaultBakeLayer", "TurtleBakeLayerManager", "TurtleRenderOptions", "TurtleUIOptions"]
for node in turtleNodes:
    try:
        cmds.lockNode(node, lock=False)
        cmds.delete(node)
    except:
        pass
    cmds.unloadPlugin("Turtle", f=True)

functions.deleteObject("MA_Hair_ShortBasic")
functions.deleteObject("MA_Hands_Generic")
functions.deleteObject("Male_head")
functions.deleteObject("MA_BodyNone_Valet")
functions.deleteObject("def_*_Set")

cmds.setAttr("bn_pelvis.v", 0)

### EYE SPEC ###

eye_pos_dict = {"R": [2.777, 155.514, -6.443], "L": [-2.777, 155.514, -6.443]}

for side in "LR":
    # side = "R"
    eye_pos = eye_pos_dict.get(side)

    # spec controls
    ic = controllers.Icon()
    cont, _ = ic.createIcon("Circle", iconName="Spec_%s_cont" % side, normal=(0,0,1), scale=(0.2, 0.2, 0.2))
    cont_offset = functions.createUpGrp(cont, "offset")
    functions.alignTo(cont_offset, "eye_%s_cont" % side, position=True, rotation=True)
    # cmds.makeIdentity(cont, a=True)

    cmds.addAttr(cont,
    longName="specScale",
    at="float",
    minValue=0,
    maxValue=10,
    defaultValue=5,
    k=True,
    )

    cmds.addAttr(cont,
    longName="snapToEye",
    at="float",
    minValue=0,
    maxValue=10,
    defaultValue=10,
    k=True,
    )
    
    
    cont_pacon = cmds.parentConstraint("eye_%s_cont" % side, "eye_ctrlBound_%s" % side, cont_offset)[0]
    cont_weight1, cont_weight2 = cmds.listAttr(cont_pacon, ud=True)

    functions.lockAndHide(cont, ["tz", "rx", "ry", "rz", "v"])

    cmds.polyDisc(sides=3, subdivisions=3)
    # polyDisc doesnt return anyvalue.. So name it from selection
    spec_geo = "charValetAvA_spec%s_IDglass_1" % side
    cmds.rename(cmds.ls(sl=True)[0], spec_geo)
    cmds.delete(spec_geo, ch=True)


    cmds.setAttr("%s.translate" % spec_geo, *eye_pos )
    # functions.alignTo(spec_geo, "eye_R_jnt", position=False, rotation=True)
    cmds.setAttr("%s.rx" %spec_geo, -90)

    spec_geo_local = deformers.localize(spec_geo, "local_spec%s_blendshape" % side, "%s_local" % spec_geo, group_name="local_BS_rig_grp")
    cluster, cluster_handle = deformers.cluster(spec_geo_local)

    bend1, bendhandle1 = cmds.nonLinear(spec_geo_local, type='bend', curvature=0)
    cmds.setAttr("%s.rotate" % bendhandle1, -180, -90, 0)

    bend2, bendhandle2 = cmds.nonLinear(spec_geo_local, type='bend', curvature=0)
    cmds.setAttr("%s.rotate" % bendhandle2, -180, -90, 90)

    cmds.setAttr("%s.curvature" % bend1, 25)
    cmds.setAttr("%s.curvature" % bend2, 25)

    cmds.select(d=True)
    spec_jdef = cmds.joint(name = "%s_jDef" %(spec_geo))
    functions.alignTo(spec_jdef, "eye_%s_local_jDef" % side, position = True, rotation = True)
    spec_jdef_offset = functions.createUpGrp(spec_jdef, "offset")
    ori_con = cmds.orientConstraint("eye_%s_local_jDef" % side, "localRig_root_jDef", spec_jdef_offset, mo=False)[0]

    weight1, weight2 = cmds.listAttr(ori_con, ud=True)

    cmds.getAttr("%s.scaleY" % cluster_handle)

    cmds.skinCluster(spec_jdef, spec_geo_local, tsb=True)
    cmds.skinCluster("bn_head", spec_geo, tsb=True)

    lattice_set = cmds.listConnections("valet_head_stretch_ffd", s=False, d=True, type="objectSet")[0]

    cmds.sets(spec_geo_local, fe=lattice_set)


    # drive attributes
    functions.drive_attrs("%s.snapToEye" % cont, ["%s.%s" % (ori_con, weight1), "%s.%s" % (cont_pacon, cont_weight1)], driver_range=[0,10], driven_range=[0,1])
    functions.drive_attrs("%s.snapToEye" % cont, ["%s.%s" % (ori_con, weight2), "%s.%s" % (cont_pacon, cont_weight2)], driver_range=[0,10], driven_range=[1,0])

    functions.drive_attrs("%s.specScale" % cont, ["%s.scaleX" % cluster_handle, "%s.scaleY" % cluster_handle, "%s.scaleZ" % cluster_handle], driver_range=[0,10], driven_range=[0,1])

    spec_setrange = cmds.createNode("setRange", name="spec_%s_cont_setRange" % side)
    cmds.setAttr("%s.min" % spec_setrange, 55, -55, 0)
    cmds.setAttr("%s.max" % spec_setrange, -55, 55, 0)
    cmds.setAttr("%s.oldMin" % spec_setrange, -10, -10, 0)
    cmds.setAttr("%s.oldMax" % spec_setrange, 10, 10, 0)
    cmds.connectAttr("%s.translate" % cont, "%s.value" % spec_setrange)
    cmds.connectAttr("%s.outValueX" % spec_setrange, "%s.ry" % spec_jdef)
    cmds.connectAttr("%s.outValueY" % spec_setrange, "%s.rx" % spec_jdef)

    # tiny offset from the sclera
    cmds.setAttr("%s.tz" % cluster_handle, 0.024)

    shader = cmds.shadingNode("surfaceShader", asShader=True, name="%s_M" % spec_geo.replace("_1", ""))
    new_sg = cmds.sets(spec_geo, empty=True, renderable=True, noSurfaceShader=True, name="%s_SG" % spec_geo.replace("_1", ""))
    cmds.connectAttr("%s.outColor" % shader, "%s.surfaceShader" % new_sg, f=True)
    cmds.sets(spec_geo, e=True, forceElement=new_sg)

    cmds.setAttr("%s.outColor" % shader, 1, 1, 1)
    
    # cleanup
    spec_data_grp = cmds.group(name="spec_%s_data_grp" % side, em=True)
    cmds.parent([bendhandle1, bendhandle2, cluster_handle, spec_jdef_offset], spec_data_grp)
    
    cmds.parent(cont_offset, "eye_ctrlBound_%s" % side)
    
    cmds.parent(spec_geo, "renderGeo_grp")
    
    cmds.parent(spec_data_grp, "charGroup")
    
    cmds.hide(spec_data_grp)
    functions.lockAndHide(spec_data_grp)
    
    # final touch
    functions.colorize(cont, side)
    cmds.setAttr("%s.tx" % cont, -1.5)
    cmds.setAttr("%s.ty" % cont, 1.5)
    cmds.setAttr("%s.specScale" % cont, 3)
    cmds.setAttr("%s.snapToEye" % cont, 5)
