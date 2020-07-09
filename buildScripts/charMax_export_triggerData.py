# save all weights
from trigger.library import functions
from trigger.actions import weights
reload(weights)
from trigger.base import session
reload(session)
weightHandler = weights.Weights()
weights_root = "/mnt/ps-storage01/vfx_hgd_000/SG_ROOT/eg2/assets/Character/charMax/RIG/work/maya/triggerData/weights/"

meshes = []
meshes.extend(functions.getMeshes("renderGeo_grp"))
meshes.extend(functions.getMeshes("local_BS_rig_grp"))
meshes.extend(functions.getMeshes("local_TWK_rig_grp"))
############### SAVE WEIGHTS #################
# export skincluster weight maps
for mesh in meshes:
    all_deformers = deformers.get_deformers(mesh)
    skincluster = all_deformers.get("skinCluster")
    blendshape = all_deformers.get("blendShape")
    if skincluster:
        file_path = os.path.join(weights_root, "%s.json" % mesh)
        weightHandler.io.file_path = file_path
        weightHandler.save_weights(deformer=skincluster)
    if blendshape:
        for bs in blendshape:
            file_path = os.path.join(weights_root, "%s.json" % bs)
            weightHandler.io.file_path = file_path
            weightHandler.save_weights(deformer=bs)
    else:
        print("="*30)
        print mesh

# test_deformers = deformers.get_deformers("charMaxAvA_local")    
# charMaxAvA_local
############## SAVE GUIDES ###################

#### CAREFUL ######

sessionHandler = session.Session()

# # SAVE LOCAL BS GUIDES
sessionHandler.save_session("/mnt/ps-storage01/vfx_hgd_000/SG_ROOT/eg2/assets/Character/charMax/RIG/work/maya/triggerData/guides/max_local_bs_guides.json")
# sessionHandler.load_session("/mnt/ps-storage01/vfx_hgd_000/SG_ROOT/eg2/assets/Character/charMax/RIG/work/maya/triggerData/guides/max_local_bs_guides.json", reset_scene=False)


# # SAVE TWK GUIDES
sessionHandler.save_session("/mnt/ps-storage01/vfx_hgd_000/SG_ROOT/eg2/assets/Character/charMax/RIG/work/maya/triggerData/guides/max_twk_guides.json")
        

############# SAVE CONTROL SHAPES ##############
from trigger.actions import shapes
reload(shapes)
shapesHandler = shapes.Shapes()
shapesHandler.export_shapes("/mnt/ps-storage01/vfx_hgd_000/SG_ROOT/eg2/assets/Character/charMax/RIG/work/maya/triggerData/shapes/max_control_shapes.json")


