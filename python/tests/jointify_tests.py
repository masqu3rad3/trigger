from importlib import reload
from trigger.utils import jointify
reload(jointify)
fbx_source = "V:\\project_bck\\jointify_210630\\_TRANSFER\\FBX\\Female_Elf_fbxSource\\Female_Elf_fbxSource_v001.fbx"
j_hand = jointify.Jointify(blendshape_node="trigger_morph_blendshape",
                           joint_count=50,
                           shape_duration=0,
                           joint_iterations=30,
                           fbx_source=None,
                           root_nodes=["jDef_neckSplineIK_Head0", "jDef_neckSplineIK_Head1", "jDef_head_Head"],
                           correctives=False,
                           corrective_threshold=0.01)

j_hand.run()