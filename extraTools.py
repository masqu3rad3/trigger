import pymel.core as pm
import extraProcedures as extra

def replaceController(mirror=True, mirrorAxis="X", keepOldShape=False, keepAcopy=False, alignToCenter=False, *args, **kwargs):

    if kwargs:
        if kwargs["oldController"] and kwargs["newController"]:
            oldCont = kwargs["oldController"]
            newCont = kwargs["newController"]
            if type(oldCont) == str:
                oldCont=pm.PyNode(oldCont)
            if type(newCont) == str:
                newCont=pm.PyNode(newCont)
        else:
            selection = pm.ls(sl=True)
            if not len(selection) == 2:
                pm.error("select at least two nodes (first new controller then old controller)")
            newCont = selection[0]
            oldCont = selection[1]
        # duplicate the new controller for possible further use

    else:
        selection = pm.ls(sl=True)
        if not len(selection) == 2:
            pm.error("select at least two nodes (first new controller then old controller)")
        newCont = selection[0]
        oldCont = selection[1]

    # get the current transform
    tryChannels = ["tx", "ty", "tz", "rx", "ry", "rz"]
    transformDict = {}
    for i in tryChannels:
        keptdata = pm.getAttr("%s.%s" %(oldCont, i))
        transformDict[i]=keptdata
        try:
            pm.setAttr("%s.%s" %(oldCont, i), 0)
        except RuntimeError:
            pass


    if keepAcopy:
        newContDup = pm.duplicate(newCont)[0]
    else:
        newContDup = newCont

    pm.setAttr(newContDup.tx, e=True, k=True, l=False)
    pm.setAttr(newContDup.ty, e=True, k=True, l=False)
    pm.setAttr(newContDup.tz, e=True, k=True, l=False)
    pm.setAttr(newContDup.rx, e=True, k=True, l=False)
    pm.setAttr(newContDup.ry, e=True, k=True, l=False)
    pm.setAttr(newContDup.rz, e=True, k=True, l=False)
    pm.setAttr(newContDup.sx, e=True, k=True, l=False)
    pm.setAttr(newContDup.sy, e=True, k=True, l=False)
    pm.setAttr(newContDup.sz, e=True, k=True, l=False)

    pm.makeIdentity(newContDup, a=True)

    #Make sure the new controllers transform are zeroed at the (0,0,0)
    offset = pm.xform(newContDup, q=True, ws=True, rp=True)
    rvOffset = [x * -1 for x in offset]
    pm.xform(newContDup, ws=True, t=rvOffset)


    pm.makeIdentity(newContDup, apply=True, t=True, r=False, s=True, n=False, pn=True)

    ## get the same color code
    # pm.setAttr(newContDup.getShape()+".overrideEnabled", pm.getAttr(oldCont.getShape()+".overrideEnabled"))
    pm.setAttr("%s.overrideEnabled" % newContDup.getShape(), pm.getAttr("%s.overrideEnabled" % oldCont.getShape()))

    # pm.setAttr(newContDup.getShape()+".overrideColor", pm.getAttr(oldCont.getShape()+".overrideColor"))
    pm.setAttr("%s.overrideColor" % newContDup.getShape(), pm.getAttr("%s.overrideColor" % oldCont.getShape()))




    #move the new controller to the old controllers place
    if alignToCenter:
        extra.alignTo(newContDup, oldCont, mode=2)
    else:
        extra.alignToAlter(newContDup, oldCont, mode=2)


    ## put the new controller shape under the same parent with the old first (if there is a parent)
    if oldCont.getParent():
        pm.parent(newContDup, oldCont.getParent())
    pm.makeIdentity(newContDup, apply=True)
    # move the pivot to the same position
    # pivotPoint = pm.xform(oldCont,q=True, t=True, ws=True)
    # pm.xform(newContDup, piv=pivotPoint, ws=True)


    if not keepOldShape:
        # pm.delete(oldCont.getShape())
        pm.delete(pm.listRelatives(oldCont, shapes=True, children=True))

    pm.parent(newContDup.getShape(), oldCont, r=True, s=True)

    if mirror:
        # find the mirror of the oldController
        if "_LEFT_" in oldCont.name():
            mirrorName = oldCont.name().replace("_LEFT_", "_RIGHT_")
        elif "_RIGHT_" in oldCont.name():
            mirrorName = oldCont.name().replace("_RIGHT_", "_LEFT_")
        else:
            pm.warning("Cannot find the mirror controller, skipping mirror part")
            if not keepOldShape:
                pm.delete(oldCont.getShape())
            return
        oldContMirror = pm.PyNode(mirrorName)

        # get the current transform
        transformDict_mir = {}
        for i in tryChannels:
            keptdata_mir = pm.getAttr("%s.%s" % (oldContMirror, i))
            transformDict_mir[i] = keptdata_mir
            try:
                pm.setAttr("%s.%s" % (oldContMirror, i), 0)
            except RuntimeError:
                pass

        newContDupMirror = pm.duplicate(newCont)[0]
        pm.makeIdentity(newContDupMirror, a=True)
        # Make sure the new controllers transform are zeroed at the (0,0,0)
        offset = pm.xform(newContDupMirror, q=True, ws=True, rp=True)
        rvOffset = [x * -1 for x in offset]
        pm.xform(newContDupMirror, ws=True, t=rvOffset)
        pm.makeIdentity(newContDupMirror, apply=True, t=True, r=True, s=True, n=False, pn=True)
        pm.setAttr("{0}.scale{1}".format(newContDupMirror, mirrorAxis), -1)
        pm.makeIdentity(newContDupMirror, apply=True, s=True)

        ## get the same color code
        # pm.setAttr(newContDupMirror.getShape() + ".overrideEnabled", pm.getAttr(oldContMirror.getShape() + ".overrideEnabled"))
        pm.setAttr("%s.overrideEnabled" % newContDupMirror.getShape(),
                   pm.getAttr("%s.overrideEnabled") % oldContMirror.getShape())


        # pm.setAttr(newContDupMirror.getShape() + ".overrideColor", pm.getAttr(oldContMirror.getShape() + ".overrideColor"))
        pm.setAttr("%s.overrideColor" % newContDupMirror.getShape(),
                   pm.getAttr("%s.overrideColor" % oldContMirror.getShape()))


        # move the new controller to the old controllers place
        extra.alignToAlter(newContDupMirror, oldContMirror, mode=0)

        if not keepOldShape:
            # pm.delete(oldContMirror.getShape())
            pm.delete(pm.listRelatives(oldContMirror, shapes=True, children=True))

        pm.parent(newContDupMirror.getShape(), oldContMirror, r=True, s=True)


        for i in tryChannels:
            try:
                pm.setAttr("%s.%s" % (oldContMirror, i), transformDict_mir[i])
            except RuntimeError:
                pass

    for i in tryChannels:
        try:
            pm.setAttr("%s.%s" % (oldCont, i), transformDict[i])
        except RuntimeError:
            pass
        