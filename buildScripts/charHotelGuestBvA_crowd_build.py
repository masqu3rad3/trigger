# create the crowd rig with
from maya import cmds
from trigger.actions import import_export
from trigger.library import functions
from trigger.actions import weights
reload(weights)
weightHandler = weights.Weights()
fileHandler = import_export.ImportExport()

baserig_file = "/mnt/ps-storage01/vfx_hgd_000/SG_ROOT/eg2/assets/Character/charHotelGuest/RIG/work/maya/rootCharHotelGuestBvA.v009.ma"
cmds.file(baserig_file, open=True, force=True)
meshes_file = "/mnt/ps-storage01/vfx_hgd_000/SG_ROOT/eg2/assets/Character/charHotelGuest/MDL/publish/maya/charHotelGuestBvA.v002.ma"
fileHandler.import_scene(meshes_file)

variation_meshes = functions.getMeshes("charHotelGuestBvA")
weights_root = "/mnt/ps-storage01/vfx_hgd_000/SG_ROOT/eg2/assets/Character/charHotelGuest/RIG/work/maya/triggerData/weights/"


# seperate the meshes into groups according to the second tags
variation_dict = {}
for mesh in variation_meshes:
    weightHandler.create_deformer(os.path.join(weights_root, "%s.json" % mesh))
    var_type = mesh.split("_")[1]
    if not variation_dict.get(var_type):
        variation_dict[var_type]=[mesh]
    else:
        variation_dict[var_type].append(mesh)

functions.create_attribute("ctrl_character", attr_name="varSeperator", nice_name = "----- Variations -----", attr_type="enum", enum_list=" :")

for attr, meshes in variation_dict.items():
    enum_names = [mesh.split("_")[2] for mesh in meshes]
    print (":".join(enum_names))
    functions.create_attribute("ctrl_character", attr_name=attr, attr_type="enum", enum_list=(":".join(enum_names)))
    for nmb, mesh in enumerate(meshes):
        condition = cmds.createNode("condition", name="%s_condition" %mesh)
        cmds.setAttr("%s.operation" % condition, 0)
        cmds.connectAttr("ctrl_character.%s" %attr, "%s.firstTerm" %condition)
        cmds.setAttr("%s.secondTerm" % condition, nmb)
        cmds.setAttr("%s.colorIfTrueR" % condition, 1)
        cmds.setAttr("%s.colorIfFalseR" % condition, 0)
        cmds.connectAttr("%s.outColorR" % condition, "%s.v" % mesh)
        functions.lockAndHide(mesh, "v")
        cmds.select(mesh)
        cmds.PruneSmallWeights()
        cmds.RemoveUnusedInfluences()

# put everything under rig grp

rig_grp = cmds.group(["rootCharHotelGuestBvA", "charHotelGuestBvA"], name="rig_grp")
functions.lockAndHide(rig_grp, ["tx","ty","tz","rx","ry","rz","sx","sy","sz","v"])

# fix FPS

cmds.currentUnit(time="film")
cmds.playbackOptions(ast=0, min=0, max=24, aet=24)

# grp renaming
cmds.rename("charHotelGuestBvA", "renderGeo_grp")

# extra bullet-proofing
functions.lockAndHide("renderGeo_grp")
functions.lockAndHide("rootCharHotelGuestBvA")

cmds.hide("bn_pelvis")
