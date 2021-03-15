from maya import cmds

side_dict = {"C": 0, "L": 1, "R": 2}

for jnt in cmds.ls(sl=True):
    parts = jnt.split("_")
    name = parts[1:]

    cmds.setAttr("%s.moduleName" % jnt, "_".join(name), type="string")
    cmds.setAttr("%s.controllerSurface" % jnt, "charArchetypeMaleAvA_face_IDmulti_1", type="string")
    cmds.setAttr("%s.rotateObject" % jnt, "head_follow", type="string")
    side = side_dict.get(parts[1][0], 0)
    cmds.setAttr("%s.side" % jnt, side)
