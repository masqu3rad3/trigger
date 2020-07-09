
from maya import cmds

from trigger.library import functions
from trigger.actions import import_export
from trigger.library import deformers
from trigger.base import session
from trigger.library import controllers
from trigger.library import functions
from trigger.utils import jointsOnBlendshape
from trigger.utils import parentToSurface

# reset scene
cmds.file(new=True, force=True)
# open the previous rig
cmds.file("/mnt/ps-storage01/vfx_hgd_000/SG_ROOT/eg2/assets/Character/charEmma/RIG/work/maya/rootCharEmmaAvA.v001.ma",open=True, force=True)
cmds.hide(cmds.listRelatives("bn_head", children=True))
cmds.hide(cmds.listRelatives("grp_faceExtra", children=True))

# import the mesh grp
import_act = import_export.ImportExport()
import_act.import_scene("/mnt/ps-storage01/vfx_hgd_000/SG_ROOT/eg2/assets/Character/charEmmaChair/MDL/publish/maya/charEmmaChairAvA.v015.ma")
import_act.import_scene("/mnt/ps-storage01/vfx_hgd_000/SG_ROOT/eg2/assets/Character/charEmma/MDL/work/maya/charEmmaAvA.v019.ma")

# get all final meshes
chair_meshes = functions.getMeshes("charEmmaChairAvA")
body_meshes = functions.getMeshes("charEmmaAvA")
final_meshes = chair_meshes + body_meshes

# build the BASEs of Local Rigs
face_meshes = ["charEmmaAvA_teethUpper_GEO_IDteeth",
               "charEmmaAvA_teethLower_GEO_IDteeth",
               "charEmmaAvA_tongue_GEO_IDtongue",
               "charEmmaAvA_Eye_Outer_L_GEO_IDeyeOuter",
               "charEmmaAvA_Eye_Outer_R_GEO_IDeyeOuter",
               "charEmmaAvA_Eye_Inner_L_GEO_IDeyeInner",
               "charEmmaAvA_Eye_Inner_R_GEO_IDeyeInner",
               "charEmmaAvA_face_GEO_IDskin",
               "charEmmaAvA_hair_GEO_IDhair",
               ]

local_meshes = []
for mesh in face_meshes:
    # print mesh
    local_BS_blendshape = "%s_local_bs" % mesh
    local_meshes.append(deformers.localize(mesh, local_BS_blendshape, "%s_local" % mesh, group_name="local_BS_rig_grp"))

TWK_MESH = "charEmmaAvA_face_GEO_IDskin_local"
local_tweakers_blendshape = "local_TWK_rig_bs"
local_meshes.append(
    deformers.localize(TWK_MESH, local_tweakers_blendshape, "%s_TWK" % TWK_MESH, group_name="local_TWK_rig_grp"))

###############################
####### LOCAL BS RIG ##########
###############################


sessionHandler = session.Session()
sessionHandler.load_session(
    "/mnt/ps-storage01/vfx_hgd_000/SG_ROOT/eg2/assets/Character/charEmma/RIG/work/maya/triggerData/guides/emma_local_bs_guides.json",
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

# import face UI
# cmds.file("/home/arda.kutlu/localProjects/EG2_playground_200617/scenes/UI/faceUI/faceUI_UI_gn_v001.mb", i=True, mnr=True)
import_act.import_scene(
    "/mnt/ps-storage01/vfx_hgd_000/SG_ROOT/eg2/assets/Character/charMax/RIG/work/maya/triggerData/UI/faceUI.mb")
# import_act.import_alembic("/home/arda.kutlu/localProjects/EG2_playground_200617/_TRANSFER/ALEMBIC/faceUI.abc")
cmds.setAttr("face_ctrls_grp.translate", -36, 170, 0)
cmds.parentConstraint("ctrl_head", "face_ctrls_grp", mo=True)
cmds.parent("face_ctrls_grp", "Rig_Controllers")

hook_blendshapes = "hook_blendshapes"

# TEETH RIG
###########
upper_teeth_cont, _ = icon_handler.createIcon("Circle", iconName="upperTeeth_cont", scale=(3, 3, 3), normal=(0, 1, 0))
lower_teeth_cont, _ = icon_handler.createIcon("Circle", iconName="lowerTeeth_cont", scale=(3, 3, 3), normal=(0, 1, 0))
upper_teeth_cont_offset = functions.createUpGrp(upper_teeth_cont, "offset")
lower_teeth_cont_offset = functions.createUpGrp(lower_teeth_cont, "offset")
functions.alignTo(upper_teeth_cont_offset, "upperTeeth_jDef", position=True, rotation=True)
functions.alignTo(lower_teeth_cont_offset, "lowerTeeth_jDef", position=True, rotation=True)

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

cmds.connectAttr("%s.xformMatrix" % upper_teeth_cont, "upperTeeth_jDef.offsetParentMatrix")
cmds.connectAttr("%s.xformMatrix" % lower_teeth_cont, "lowerTeeth_jDef.offsetParentMatrix")
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
cmds.setDrivenKeyframe(jaw_rx, cd=mouth_cont_Y, v=-8, dv=10, itt="linear", ott="linear")

cmds.setDrivenKeyframe(jawN_rx, cd=mouth_cont_Y, v=jawN_rx_val, dv=1, itt="linear", ott="linear")
cmds.setDrivenKeyframe(jawN_rx, cd=mouth_cont_Y, v=-8, dv=10, itt="linear", ott="linear")

# Controller X Connections
cmds.setDrivenKeyframe(jaw_ry, cd=mouth_cont_X, v=jaw_ry_val, dv=0.0, itt="spline", ott="spline")
cmds.setDrivenKeyframe(jaw_ry, cd=mouth_cont_X, v=20, dv=-10, itt="linear", ott="linear")
cmds.setDrivenKeyframe(jaw_ry, cd=mouth_cont_X, v=-20, dv=10, itt="linear", ott="linear")

cmds.setDrivenKeyframe(jaw_rz, cd=mouth_cont_X, v=jaw_rz_val, dv=0.0, itt="spline", ott="spline")
cmds.setDrivenKeyframe(jaw_rz, cd=mouth_cont_X, v=-40, dv=-10, itt="spline", ott="spline")
cmds.setDrivenKeyframe(jaw_rz, cd=mouth_cont_X, v=40, dv=10, itt="spline", ott="spline")

# Controller Z Connections
cmds.setDrivenKeyframe(jaw_tz, cd=mouth_cont_Z, v=jaw_tz_val, dv=0.0, itt="spline", ott="spline")
cmds.setDrivenKeyframe(jaw_tz, cd=mouth_cont_Z, v=0, dv=-10, itt="linear", ott="linear")
cmds.setDrivenKeyframe(jaw_tz, cd=mouth_cont_Z, v=5, dv=10, itt="linear", ott="linear")
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
eyeLookat_offset = functions.createUpGrp("crtl_eyeLookat", "offset")
cmds.setAttr("%s.ty" % eyeLookat_offset, 5.725296945384471)

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
    cmds.setDrivenKeyframe("%s.rx" % eyeFollowGrp, cd="%s.rx" % extractor, v=-18, dv=-28.61, itt="spline", ott="spline")
    cmds.setDrivenKeyframe("%s.rx" % eyeFollowGrp, cd="%s.rx" % extractor, v=18, dv=19.97, itt="spline", ott="spline")
    cmds.setDrivenKeyframe("%s.ry" % eyeFollowGrp, cd="%s.ry" % extractor, v=0.0, dv=0.0, itt="spline", ott="spline")
    cmds.setDrivenKeyframe("%s.ry" % eyeFollowGrp, cd="%s.ry" % extractor, v=-18, dv=-42.27, itt="spline", ott="spline")
    cmds.setDrivenKeyframe("%s.ry" % eyeFollowGrp, cd="%s.ry" % extractor, v=18, dv=42.27, itt="spline", ott="spline")

# Eye Lids
for side in "LR":
    cmds.setDrivenKeyframe("upper_eyeLid_%s_jDef.rx" % side, cd="upper_eyeLid_%s_cont.ty" % side, v=0.0, dv=0.0,
                           itt="linear", ott="linear")
    cmds.setDrivenKeyframe("upper_eyeLid_%s_jDef.rx" % side, cd="upper_eyeLid_%s_cont.ty" % side, v=-56, dv=-19,
                           itt="linear", ott="linear")
    cmds.setDrivenKeyframe("upper_eyeLid_%s_jDef.rx" % side, cd="upper_eyeLid_%s_cont.ty" % side, v=22, dv=3.50,
                           itt="linear", ott="linear")

    cmds.setDrivenKeyframe("lower_eyeLid_%s_jDef.rx" % side, cd="lower_eyeLid_%s_cont.ty" % side, v=0.0, dv=0.0,
                           itt="linear", ott="linear")
    cmds.setDrivenKeyframe("lower_eyeLid_%s_jDef.rx" % side, cd="lower_eyeLid_%s_cont.ty" % side, v=-25, dv=-3,
                           itt="linear", ott="linear")
    cmds.setDrivenKeyframe("lower_eyeLid_%s_jDef.rx" % side, cd="lower_eyeLid_%s_cont.ty" % side, v=59, dv=19,
                           itt="linear", ott="linear")

#############################################################