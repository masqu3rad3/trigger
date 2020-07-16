cmds.error("PREVENT ACCIDENTAL RUN")

# save all weights
from trigger.library import functions
from trigger.actions import weights
reload(weights)
from trigger.base import session
reload(session)
weightHandler = weights.Weights()
triggerData_root = "/mnt/ps-storage01/vfx_hgd_000/SG_ROOT/eg2/assets/Character/charIvan/RIG/work/maya/triggerData/"
charName = "ivan"

meshes = []
meshes.extend(functions.getMeshes("charIvanAvA"))
meshes.extend(functions.getMeshes("local_BS_rig_grp"))
meshes.extend(functions.getMeshes("local_TWK_rig_grp"))
############### SAVE WEIGHTS #################
# export skincluster weight maps
for mesh in meshes:
    all_deformers = deformers.get_deformers(mesh)
    skincluster = all_deformers.get("skinCluster")
    blendshape = all_deformers.get("blendShape")
    ffd= all_deformers.get("ffd")
    if skincluster:
        file_path = os.path.join(triggerData_root, "weights", "%s.json" % mesh)
        weightHandler.io.file_path = file_path
        weightHandler.save_weights(deformer=skincluster)
    if blendshape:
        for bs in blendshape:
            file_path = os.path.join(triggerData_root, "weights", "%s.json" % bs)
            weightHandler.io.file_path = file_path
            weightHandler.save_weights(deformer=bs)
    # if ffd:
    #     for f in ffd:
    #         file_path = os.path.join(triggerData_root, "weights", "%s.json" % f)
    #         weightHandler.io.file_path = file_path
    #         weightHandler.save_weights(deformer=f)
    #         print("-"*30)
    #         print("="*30)
    #         print("*"*30)
    #         print f
    #         print file_path
            
    else:
        print("="*30)
        print mesh

# test_deformers = deformers.get_deformers("charMaxAvA_local")    
# charMaxAvA_local
############## SAVE GUIDES ###################

#### CAREFUL ######

sessionHandler = session.Session()

# # SAVE BODY GUIDES
sessionHandler.save_session(os.path.join(triggerData_root, "guides", "%s_body_guides.json" % charName))


# # SAVE LOCAL BS GUIDES
sessionHandler.save_session(os.path.join(triggerData_root, "guides", "%s_local_bs_guides.json" % charName))


# # SAVE TWK GUIDES
sessionHandler.save_session(os.path.join(triggerData_root, "guides", "%s_twk_guides.json" % charName))


# # SAVE STRETCHY GUIDES
sessionHandler.save_session(os.path.join(triggerData_root, "guides", "%s_stretchyFace.json" % charName))

# # SAV FFD
ffd_name = "charIvanAvA_helmetglass_idHelmetGlass_GEO_local_ffd"
weightHandler.save_weights(deformer=ffd_name, file_path=os.path.join(triggerData_root, "weights", "%s.json" % ffd_name) , vertexConnections=False, force=True, influencer=None)


############# SAVE CONTROL SHAPES ##############
from trigger.actions import shapes
reload(shapes)
shapesHandler = shapes.Shapes()
shapesHandler.export_shapes(os.path.join(triggerData_root, "shapes", "%s_control_shapes" % charName))


