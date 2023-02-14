"""Guide related utility functions"""

from maya import cmds
from trigger.utils import parentToSurface
from trigger.library import deformers
from trigger.library import functions
# transfer face guides between same topo meshes

def transfer_guides(source_mesh, target_mesh, guides_grp):
    """
        Transfers the guides between assets sharing the same topology
    Useful to transfer the on face controllers

    Args:
        source_mesh: (String) old mesh which aligns with the current guide joints
        target_mesh: (String) new mesh
        guides_grp: (String) Group node which hold all the guide joints

    Returns: None

    """
    all_joints = cmds.listRelatives(guides_grp, children=True)
    temp_blendshape = cmds.blendShape(source_mesh, target_mesh, w=[0, 1], name="trTMP_guideTransfer_blendshape")
    follicles = parentToSurface.parentToSurface(objects=all_joints, surface=target_mesh, mode="parent")
    attribute = deformers.get_influencers(temp_blendshape)[0]
    cmds.setAttr("%s.%s" %(temp_blendshape[0],attribute), 0)
    # bring back joints where they belong
    cmds.parent(all_joints, guides_grp)

    # clean the mess
    functions.delete_object(temp_blendshape)
    functions.delete_object(follicles)