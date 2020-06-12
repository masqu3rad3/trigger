## This Script originally belongs to Duncan Brinsmead (parentToSurface.mel)
## I just converted it to Pymel for easier modification and
## added som more functionality in order to use inside other python modules

import pymel.core as pm
def convertToCmFactor():
    unit = pm.currentUnit(q=True, linear=True)
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
        numSel = pm.ls(sl=True)
        if numSel < 2:
            pm.warning("ParentToSurface: select object(s) to parent followed by a mesh or nurbsSurface to attach to.")
            return
        else:
            objects = numSel[0:-1]
            surface = numSel[-1]
    if pm.nodeType(surface) == "transform":
        shapes = pm.ls(surface, dag=True, s=True, ni=True, v=True)
        if len(shapes) > 0:
            surface = shapes[0]
    nType = pm.nodeType(surface)

    # For some weird reason, if the mesh is hidden it does not return nodeType!!!
    # if nType != "mesh" and nType != "nurbsSurface":
    #     pm.warning("ParentToSurface: Last selected item must be a mesh or nurbsSurface.")
    #     return

    minU, minV, sizeU, sizeV = 0.0, 0.0, 0.0, 0.0
    if nType == "nurbsSurface":
        clPos = pm.createNode("closestPointOnSurface")
        surface.worldSpace[0] >> clPos.inputSurface
        minU = pm.getAttr(surface.mnu)
        maxU = pm.getAttr(surface.mxu)
        sizeU = maxU - minU
        minV = pm.getAttr(surface.mnv)
        maxV = pm.getAttr(surface.mxv)
        sizeV = maxV - minV
    else:
        pomLoaded = pm.pluginInfo("nearestPointOnMesh", query=True, l=True)
        if not pomLoaded:
            try:
                pm.loadPlugin("nearestPointOnMesh")
            except RunTimeError:
                pm.warning("ParentToSurface: Can't load nearestPointOnMesh plugin.")
                return

        convertFactor = convertToCmFactor()
        clPos = pm.createNode("nearestPointOnMesh")

    follicleTransformList = []
    for obj in objects:
        pm.disconnectAttr(surface.worldMesh)
        surface.worldMesh >> clPos.inMesh

        bbox = pm.xform(obj, q=True, ws=True, bb=True)
        pos = (((bbox[0] + bbox[3]) * 0.5) * convertFactor,
               ((bbox[1] + bbox[4]) * 0.5) * convertFactor,
               ((bbox[2] + bbox[5]) * 0.5) * convertFactor)
        pm.setAttr(clPos.inPosition, pos, type="double3")

        closestU = pm.getAttr(clPos.parameterU)
        closestV = pm.getAttr(clPos.parameterV)

        # attachObjectToSurface(obj, surface, closestU, closestV)
        follicle = pm.createNode("follicle", name=("%s_follicleShape" %obj.name()))
        tforms = pm.listTransforms(follicle)
        follicleDag = tforms[0]
        pm.rename(follicleDag, ("%s_follicle" %obj.name()))

        surface.worldMatrix[0] >> follicle.inputWorldMatrix
        nType = pm.nodeType(surface)
        if nType == "nurbsSurface":
            surface.local >> follicle.inputSurface
        else:
            surface.outMesh >> follicle.inputMesh

        follicle.outTranslate >> follicleDag.translate
        follicle.outRotate >> follicleDag.rotate
        pm.setAttr(follicleDag.translate, lock=True)
        pm.setAttr(follicleDag.rotate, lock=True)
        pm.setAttr(follicle.parameterU, closestU)
        pm.setAttr(follicle.parameterV, closestV)
        follicleTransformList.append(follicleDag)

        mode = mode.lower()
        if mode == "parent":
            pm.parent(obj, follicleDag)
        if mode == "parentconstraint":
            pm.parentConstraint(follicleDag, obj, mo=True)
        if mode == "pointconstraint":
            pm.pointConstraint(follicleDag, obj, mo=True)
        if mode == "none":
            pass

    pm.delete(clPos)


    return follicleTransformList

# parentToSurface([pm.ls(sl=True)[0]], pm.ls(sl=True)[1])

