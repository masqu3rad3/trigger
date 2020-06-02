from compiler.ast import flatten
from maya import cmds
from pprint import pprint

from trigger.library import functions as extra
reload(extra)
from trigger.base import builder
reload(builder)
from trigger.base import initials
reload(initials)


#########################
def get_user_attrs(jnt):    
    """Returns a list of dictionaries which holds the information for rebuilding"""
    supported_attrs = ["long", "short", "bool", "enum", "float", "double", "string", "typed"] #wtf is typed
    list_of_dicts = []
    user_attr_list = cmds.listAttr(jnt, userDefined=True)
    if not user_attr_list:
        return []
    for attr in user_attr_list:
        attr_type = cmds.attributeQuery(attr, node=jnt, at=True)
        if attr_type not in supported_attrs:
            continue
        tmp_dict = {}
        tmp_dict["attr_name"] = cmds.attributeQuery(attr, node=jnt, ln=True)
        tmp_dict["attr_type"] = attr_type
        tmp_dict["nice_name"] = cmds.attributeQuery(attr, node=jnt, nn=True)
        tmp_dict["default_value"] = cmds.getAttr("%s.%s" % (jnt, attr))
        if attr_type == "enum":
            tmp_dict["enum_list"] = cmds.attributeQuery(attr, node=jnt, le=True)[0]
        elif attr_type == "bool":
            pass
        elif attr_type == "typed":
            ## Wtf is "typed" anyway??
            tmp_dict["attr_type"] = "string"
        else:
            try: tmp_dict["min_value"] = cmds.attributeQuery(attr, node=jnt, min=True)[0]
            except RuntimeError: pass
            try: tmp_dict["max_value"] = cmds.attributeQuery(attr, node=jnt, max=True)[0]
            except RuntimeError: pass
        
        list_of_dicts.append(tmp_dict)
    return list_of_dicts
##########################



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
    cmds.select(d=True)
    tmp_jnt = cmds.joint()
    extra.alignTo(tmp_jnt, jnt, position=True, rotation=True)
    world_pos = tuple(extra.getWorldTranslation(tmp_jnt))
    rotation = cmds.getAttr("%s.rotate" % tmp_jnt)[0]
    joint_orient = cmds.getAttr("%s.jointOrient" % tmp_jnt)[0]
    scale = cmds.getAttr("%s.scale" % jnt)[0]
    side = extra.get_joint_side(jnt)
    j_type = extra.get_joint_type(jnt)
    color = cmds.getAttr("%s.overrideColor" % jnt)
    radius = cmds.getAttr("%s.radius" % jnt)
    parent = extra.getParent(jnt)
    if parent in flat_jnt_list:
        pass
    else:
        parent = None
    # get all custom attributes
    # this returns list of dictionaries compatible with create_attribute method in library.functions
    user_attrs = get_user_attrs(jnt) 
    
    jnt_dict = {"name": jnt,
                "position": world_pos,
                "rotation": rotation,
                "joint_orient": joint_orient,
                "scale": scale,
                "parent": parent,
                "side": side,
                "type": j_type,
                "color": color,
                "radius": radius,
                "user_attributes": user_attrs}
    save_data.append(jnt_dict)
    
# pprint(save_data)

##### rebuild
for jnt_dict in save_data:
    cmds.select(d=True)
    jnt = cmds.joint(name=jnt_dict.get("name"), p=jnt_dict.get("position"))
    extra.create_global_joint_attrs(jnt)
    cmds.setAttr("%s.rotate" % jnt, *jnt_dict.get("rotation"))
    cmds.setAttr("%s.jointOrient" % jnt, *jnt_dict.get("joint_orient"))
    cmds.setAttr("%s.scale" % jnt, *jnt_dict.get("scale"))
    cmds.setAttr("%s.radius" % jnt, jnt_dict.get("radius"))
    cmds.setAttr("%s.drawLabel" % jnt, 1)
    cmds.setAttr("%s.displayLocalAxis" % jnt, 1)
    cmds.setAttr("%s.overrideEnabled" % jnt, True)
    cmds.setAttr("%s.overrideColor" % jnt, jnt_dict.get("color"))
    extra.set_joint_side(jnt, jnt_dict.get("side"))
    extra.set_joint_type(jnt, jnt_dict.get("type"))
    property_attrs = jnt_dict.get("user_attributes")
    for attr_dict in property_attrs:
        extra.create_attribute(jnt, attr_dict)
for jnt_dict in save_data:
    if jnt_dict.get("parent"):
        cmds.parent(jnt_dict.get("name"), jnt_dict.get("parent"))
    




# cmds.listAttr("jInit_finger_left_0", ud=True)

# cmds.attributeQuery("handController", node="jInit_finger_left_0", at=True)





    