# Maximilian Shape Splitting

import os
from maya import cmds
from trigger.library import functions
from trigger.core import io
reload(io)
from trigger.library import deformers
reload(deformers)
from trigger.actions import weights
reload(weights)
from trigger.utils import shape_splitter
reload(shape_splitter)

# instanciate class objects
weightHandler = weights.Weights()
splitter = shape_splitter.Splitter()

##################################
#### SPLIT MAP PREPARETION [Start]
##################################
# prepare for painting
paint_map_bs = splitter.prepare_for_painting("neutral")

# export painted split maps into SEPERATE files

# get influencers
# deformer_dictionary = deformers.get_deformers("neutral") #This is unnecessary
# paint_map_bs = deformer_dictionary["blendShape"][0] #This is unnecessary
influencers = deformers.get_influencers(paint_map_bs)

# export the split maps
export_root = "/mnt/ps-storage01/vfx_hgd_000/SG_ROOT/eg2/assets/Character/charEmma/RIG/work/maya/triggerData/splitmaps/"
for influencer in influencers:
    file_path = os.path.join(export_root, "%s.json" % influencer)
    weightHandler.io.file_path = file_path
    weightHandler.save_matching_weights(deformer=paint_map_bs, influencer=influencer)

# All split maps including their negatives are exported

###########################################
########## CREATE SPLIT SSHAPES ###########
###########################################

# define neutral
splitter.neutral = "neutral"

# add the blendshapes
cmds.select(functions.getMeshes("blendshapes_grp"))
splitter.clear_blendshapes()
splitter.add_blendshapes()
cmds.select(d=True)

# add available split maps
splitter.clear_splitmaps()
import_root = "/mnt/ps-storage01/vfx_hgd_000/SG_ROOT/eg2/assets/Character/charEmma/RIG/work/maya/triggerData/splitmaps/"
splitter.add_splitmap(os.path.join(import_root, "vertical_sharp.json"))
splitter.add_splitmap(os.path.join(import_root, "vertical_smooth.json"))
splitter.add_splitmap(os.path.join(import_root, "horizontal_sharp.json"))
# splitter.add_splitmap(os.path.join(import_root, "horizontal_noseLevel.json"))
splitter["splitMaps"]

# assign some split maps to some shapes
splitter.set_splitmap("openAngryCorrectiveX", "vertical_smooth")
# splitter.set_splitmap("closedGrin", "vertical_smooth")
# splitter.set_splitmap("meanBrows", "vertical_smooth")
# splitter.set_splitmap("slyEye", "vertical_sharp")
# splitter.set_splitmap("openGrin_corrective", "vertical_smooth")
# splitter.set_splitmap("smallGrin_corrective", "vertical_smooth")
# splitter.set_splitmap("eyesWide_corrective", ["vertical_smooth", "horizontal_sharp"])

splitter["matches"].items()

splitter.split_shapes()



# weightHandler.load_weights("blendShape1", file_path=os.path.join(export_root, "vertical_smooth.json"))
# cmds.refresh()
# test_loop = ["a", "a", "a"]
# for x in test_loop:
#     print test_loop
#     if len(test_loop) != 10:
#         test_loop.append("z")
        
