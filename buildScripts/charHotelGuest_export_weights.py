# export selected crowd weights to the triggerData/weights folder
from maya import cmds

from trigger.library import deformers
from trigger.library import functions
from trigger.actions import weights
weightHandler = weights.Weights()

weights_root = "/mnt/ps-storage01/vfx_hgd_000/SG_ROOT/eg2/assets/Character/charHotelGuest/RIG/work/maya/triggerData/weights/"

meshes = cmds.ls(sl=True)

for mesh in meshes:
    # prune
    cmds.select(mesh)
    cmds.PruneSmallWeights()
    cmds.RemoveUnusedInfluences()
    all_deformers = deformers.get_deformers(mesh)
    skincluster = all_deformers.get("skinCluster")
    if skincluster:
        file_path = os.path.join(weights_root, "%s.json" % mesh)
        weightHandler.io.file_path = file_path
        weightHandler.save_weights(deformer=skincluster)
    else:
        cmds.warning("There is no skin cluster on selected mesh => %s" % mesh)


# meshes = cmds.ls(sl=True)
# for mesh in meshes:
#     weightHandler.create_deformer(os.path.join(weights_root, "%s.json" % mesh))