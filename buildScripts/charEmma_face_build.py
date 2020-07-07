/mnt/ps-storage01/vfx_hgd_000/SG_ROOT/eg2/assets/Character/charEmmaChair/MDL/publish/maya/charEmmaChairAvA.v015.ma

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

# get all final meshes
chair_meshes = functions.getMeshes("charEmmaChairAvA")
body_meshes = []
final_meshes = chair_meshes + body_meshes