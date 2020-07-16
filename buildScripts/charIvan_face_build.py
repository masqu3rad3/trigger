
from maya import cmds
from trigger.actions import import_export
from trigger.actions import kinematics
from trigger.actions import shapes

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

# reset scene
cmds.file(new=True, force=True)
# open the previous rig
cmds.file("/mnt/ps-storage01/vfx_hgd_000/SG_ROOT/eg2/assets/Character/charIvan/RIG/work/maya/rootCharIvanAvA.v001.ma",open=True, force=True)
cmds.hide(cmds.listRelatives("bn_head", children=True))
cmds.hide(cmds.listRelatives("grp_faceExtra", children=True))

# import the mesh grp

import_act.import_alembic(
    "/mnt/ps-storage01/vfx_hgd_000/SG_ROOT/eg2/assets/Character/charIvan/MDL/publish/caches/charIvanAvA.v038.abc")
# get all final meshes
final_meshes = functions.getMeshes("charIvanAvA")

#########################
###### BODY RIG #########
#########################


# sessionHandler.load_session("/home/arda.kutlu/EG2_playground/guideData/max_local_bs_guides.json", reset_scene=False)
sessionHandler.load_session(
    "/mnt/ps-storage01/vfx_hgd_000/SG_ROOT/eg2/assets/Character/charIvan/RIG/work/maya/triggerData/guides/ivan_body_guides.json",
    reset_scene=False)

# medals

medalA = kinematics.Kinematics("jInit_tail_center_0", create_switchers=False)
medalA.action()
medalB = kinematics.Kinematics("jInit_tail_center_4", create_switchers=False)
medalB.action()
medalC = kinematics.Kinematics("jInit_tail_center_5", create_switchers=False)
medalC.action()
medalD = kinematics.Kinematics("jInit_tail_center_6", create_switchers=False)
medalD.action()

medal_follicles = parentToSurface.parentToSurface(["limbPlug_medalA", "limbPlug_medalB", "limbPlug_medalC", "limbPlug_medalD"], "charIvanAvA_jacket_GEO")

star = kinematics.Kinematics("jInit_tail_center1_0", create_switchers=False)
star.action()

star_follicle = parentToSurface.parentToSurface(["limbPlug_star"], "charIvanAvA_sash_GEO")

sstrap_right = kinematics.Kinematics("jInit_tail_right_0", create_switchers=False)
sstrap_right.action()
sstrap_left = kinematics.Kinematics("jInit_tail_left_0", create_switchers=False)
sstrap_left.action()

cmds.parentConstraint("cBn_R_upArm_armor", "limbPlug_R_sstrapBase", mo=True)
cmds.parentConstraint("cBn_L_upArm_armor", "limbPlug_L_sstrapBase", mo=True)

cmds.select([x for x in cmds.ls(sl=True) if "jDef" in x])