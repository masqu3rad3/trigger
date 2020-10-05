## This Script originally belongs to Duncan Brinsmead (parentToSurface.mel)
## I just converted it to Pymel for easier modification and
## added som more functionality in order to use inside other python maya_modules

# import pymel.core as pm
from maya import cmds

def convertToCmFactor():
    unit = cmds.currentUnit(q=True, linear=True)
    unitDictionary = {"mm": 0.1, "cm": 1.0, "m": 100.0, "in": 2.54, "ft": 30.48, "yd": 91.44}
    try:
        return unitDictionary[unit]
    except KeyError:
        return 1.0

def parentToSurface(objects=None, surface=None, mode="parent"):
    """
    Attaches the given objects to the surface by follicles
    Args:
        objects: (PyNode List) Objects list.
        surface: (PyNode) The surface that the objects will be attached on. Comptaible types are mesh and nurbs
        mode: attach mode. Valid values are 'parent', 'parentConstraint', 'pointConstraint' and 'None'

    Returns: Follicle Transform Node

    """
    if objects == None and surface == None:
        numSel = cmds.ls(sl=True)
        if len(numSel) < 2:
            cmds.warning("ParentToSurface: select object(s) to parent followed by a mesh or nurbsSurface to attach to.")
            return
        else:
            objects = numSel[0:-1]
            surface = numSel[-1]
    if cmds.nodeType(surface) == "transform":
        shapes = cmds.ls(surface, dag=True, s=True, ni=True, v=True)
        if len(shapes) > 0:
            surface = shapes[0]
    nType = cmds.nodeType(surface)

    # For some weird reason, if the mesh is hidden it does not return nodeType!!!
    # if nType != "mesh" and nType != "nurbsSurface":
    #     pm.warning("ParentToSurface: Last selected item must be a mesh or nurbsSurface.")
    #     return

    minU, minV, sizeU, sizeV = 0.0, 0.0, 0.0, 0.0
    if nType == "nurbsSurface":
        clPos = cmds.createNode("closestPointOnSurface")
        # surface.worldSpace[0] >> clPos.inputSurface
        cmds.connectAttr("%s.worldSpace[0]" % surface, "%s.inputSurface" % clPos)

        minU = cmds.getAttr("%s.mnu" % surface)
        maxU = cmds.getAttr("%s.mxu" % surface)
        sizeU = maxU - minU
        minV = cmds.getAttr("%s.mnv" % surface)
        maxV = cmds.getAttr("%s.mxv" % surface)
        sizeV = maxV - minV
    else:
        pomLoaded = cmds.pluginInfo("nearestPointOnMesh", query=True, l=True)
        if not pomLoaded:
            try:
                cmds.loadPlugin("nearestPointOnMesh")
            except RuntimeError:
                cmds.warning("ParentToSurface: Can't load nearestPointOnMesh plugin.")
                return

        convertFactor = convertToCmFactor()
        clPos = cmds.createNode("nearestPointOnMesh")

    follicleTransformList = []
    for obj in objects:
        # cmds.disconnectAttr(surface.worldMesh)
        # surface.worldMesh >> clPos.inMesh
        cmds.connectAttr("%s.worldMesh" % surface, "%s.inMesh" % clPos, f=True)

        bbox = cmds.xform(obj, q=True, ws=True, bb=True)
        pos = (((bbox[0] + bbox[3]) * 0.5) * convertFactor,
               ((bbox[1] + bbox[4]) * 0.5) * convertFactor,
               ((bbox[2] + bbox[5]) * 0.5) * convertFactor)
        # cmds.setAttr("%s.inPosition" % clPos, pos, type="double3")
        cmds.setAttr("%s.inPosition" % clPos, *pos)

        closestU = cmds.getAttr("%s.parameterU" % clPos)
        closestV = cmds.getAttr("%s.parameterV" % clPos)

        # attachObjectToSurface(obj, surface, closestU, closestV)
        follicle = cmds.createNode("follicle", name=("%s_follicleShape" %obj))
        # tforms = cmds.listTransforms(follicle)
        # tforms = functions.listTransforms(follicle)
        # follicleDag = tforms[0]
        follicleDag = cmds.listRelatives(follicle, parent=True)[0]
        cmds.rename(follicleDag, ("%s_follicle" %obj))

        # surface.worldMatrix[0] >> follicle.inputWorldMatrix
        cmds.connectAttr("%s.worldMatrix[0]" % surface, "%s.inputWorldMatrix" % follicle)
        nType = cmds.nodeType(surface)
        if nType == "nurbsSurface":
            # surface.local >> follicle.inputSurface
            cmds.connectAttr("%s.local" % surface, "%s.inputSurface" % follicle)
        else:
            # surface.outMesh >> follicle.inputMesh
            cmds.connectAttr("%s.outMesh" % surface, "%s.inputMesh" % follicle)

        # follicle.outTranslate >> follicleDag.translate
        cmds.connectAttr("%s.outTranslate" % follicle, "%s.translate" % follicleDag)
        # follicle.outRotate >> follicleDag.rotate
        cmds.connectAttr("%s.outRotate" % follicle, "%s.rotate" % follicleDag)
        cmds.setAttr("%s.translate" % follicleDag, lock=True)
        cmds.setAttr("%s.rotate" % follicleDag, lock=True)
        cmds.setAttr("%s.parameterU" % follicle, closestU)
        cmds.setAttr("%s.parameterV" % follicle, closestV)
        follicleTransformList.append(follicleDag)

        mode = mode.lower()
        if mode == "parent":
            cmds.parent(obj, follicleDag)
        if mode == "parentconstraint":
            cmds.parentConstraint(follicleDag, obj, mo=True)
        if mode == "pointconstraint":
            cmds.pointConstraint(follicleDag, obj, mo=True)
        if mode == "none":
            pass

    cmds.delete(clPos)


    return follicleTransformList

# parentToSurface([pm.ls(sl=True)[0]], pm.ls(sl=True)[1])

