from compiler.ast import flatten
from maya import cmds
from pprint import pprint

from trigger.library import functions as extra
reload(extra)
from trigger.base import builder
reload(builder)
from trigger.base import initials
reload(initials)

build = builder.Builder()
init = initials.Initials()

all_root_jnts_data = init.get_scene_roots()
root_joints_list = []

all_trigger_joints = []
for r_dict in all_root_jnts_data:
    root_jnt = (r_dict.get("root_joint"))
    root_joints_list.append(root_jnt)
    limb_dict, _, __ = build.getWholeLimb(root_jnt)
    all_trigger_joints.append(limb_dict.values())

flat_jnt_list = (flatten(all_trigger_joints))

save_data = []

for jnt in flat_jnt_list:
    world_pos = tuple(extra.getWorldTranslation(jnt))
    rotation = cmds.getAttr("%s.rotate" % jnt)[0]
    joint_orient = cmds.getAttr("%s.jointOrient" % jnt)[0]
    scale = cmds.getAttr("%s.scale" % jnt)[0]
    side = extra.get_joint_side(jnt)
    j_type = extra.get_joint_type(jnt)
    parent = extra.getParent(jnt)
    if parent in flat_jnt_list:
        pass
    else:
        parent = None
    # get all custom attributes
    if jnt in root_joints_list:
        user_attr_list = cmds.listAttr(jnt, scalarAndArray=True, userDefined=True)
        user_attr_dict = {attr: cmds.getAttr("%s.%s" % (jnt, attr)) for attr in user_attr_list}
    else: user_attr_dict = None
    
    jnt_dict = {"name": jnt,
                "position": world_pos,
                "rotation": rotation,
                "joint_orient": joint_orient,
                "scale": scale,
                "parent": parent,
                "side": side,
                "type": j_type,
                "user_attributes": user_attr_dict}
    save_data.append(jnt_dict)
    
# pprint(save_data)

##### rebuild
for jnt_dict in save_data:
    cmds.select(d=True)
    jnt = cmds.joint(name=jnt_dict.get("name"), p=jnt_dict.get("position"))
    cmds.setAttr("%s.rotate" % jnt, *jnt_dict.get("rotation"))
    cmds.setAttr("%s.jointOrient" % jnt, *jnt_dict.get("joint_orient"))
    cmds.setAttr("%s.scale" % jnt, *jnt_dict.get("scale"))
    extra.set_joint_side(jnt, jnt_dict.get("side"))
    extra.set_joint_type(jnt, jnt_dict.get("type"))
for jnt_dict in save_data:
    if jnt_dict.get("parent"):
        # print jnt_dict.get("parent")
        
        # print jnt_dict.get("parent")
        cmds.parent(jnt_dict.get("name"), jnt_dict.get("parent"))
    
    

    