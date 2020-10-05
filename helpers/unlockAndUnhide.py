"""Unlocks and Unhide methods for debugging purposes"""

import maya.cmds as cmds
import sys

def unlockSingleAttribute(a):
    sel = cmds.ls(sl=True)
    for x in sel:
        cmds.setAttr("{0}.{1}".format(x, a), e=True, k=True, l=False)

def unlockVectorAttribute(a):
    sel = cmds.ls(sl=True)
    for x in sel:
        cmds.setAttr("{0}.{1}x".format(x, a), e=True, k=True, l=False)
        cmds.setAttr("{0}.{1}y".format(x, a), e=True, k=True, l=False)
        cmds.setAttr("{0}.{1}z".format(x, a), e=True, k=True, l=False)

def unlockEverything(sel=None):
    sel = cmds.ls(sl=True) if not sel else sel
    if type(sel) != list:
        sel=[sel]
    for x in sel:
        cmds.setAttr("%s.tx" %(x), e=True, k=True, l=False)
        cmds.setAttr("%s.ty" %(x), e=True, k=True, l=False)
        cmds.setAttr("%s.tz" %(x), e=True, k=True, l=False)
        cmds.setAttr("%s.rx" %(x), e=True, k=True, l=False)
        cmds.setAttr("%s.ry" %(x), e=True, k=True, l=False)
        cmds.setAttr("%s.rz" %(x), e=True, k=True, l=False)
        cmds.setAttr("%s.sx" %(x), e=True, k=True, l=False)
        cmds.setAttr("%s.sy" %(x), e=True, k=True, l=False)
        cmds.setAttr("%s.sz" %(x), e=True, k=True, l=False)
        cmds.setAttr("%s.v" %(x), e=True, k=True, l=False)

def command():
    validSingleInputs = ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz", "v"]
    validVectorInputs = ["t", "r", "s"]
    if sys.version_info.major == 3:
        attr = input()
    else:
        attr = raw_input()
    if attr and attr in validSingleInputs:
        unlockSingleAttribute(attr)
    elif attr and attr in validVectorInputs:
        unlockVectorAttribute(attr)
    else:
        cmds.warning("Input is not valid")