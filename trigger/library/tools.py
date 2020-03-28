# import pymel.core as pm

from maya import cmds
import trigger.library.functions as functions

def replaceController(mirror=True, mirrorAxis="X", keepOldShape=False, keepAcopy=False, alignToCenter=False, *args, **kwargs):
    if kwargs:
        if kwargs["oldController"] and kwargs["newController"]:
            oldCont = kwargs["oldController"]
            newCont = kwargs["newController"]
            # if type(oldCont) == str:
            #     oldCont=pm.PyNode(oldCont)
            # if type(newCont) == str:
            #     newCont=pm.PyNode(newCont)
        else:
            selection = cmds.ls(sl=True)
            if not len(selection) == 2:
                cmds.error("select at least two nodes (first new controller then old controller)")
            newCont = selection[0]
            oldCont = selection[1]
        # duplicate the new controller for possible further use

    else:
        selection = cmds.ls(sl=True)
        if not len(selection) == 2:
            cmds.error("select at least two nodes (first new controller then old controller)")
        newCont = selection[0]
        oldCont = selection[1]

    # get the current transform
    tryChannels = ["tx", "ty", "tz", "rx", "ry", "rz"]
    transformDict = {}
    for i in tryChannels:
        keptdata = cmds.getAttr("%s.%s" %(oldCont, i))
        transformDict[i]=keptdata
        try:
            cmds.setAttr("%s.%s" %(oldCont, i), 0)
        except RuntimeError:
            pass


    if keepAcopy:
        newContDup = cmds.duplicate(newCont)[0]
    else:
        newContDup = newCont

    cmds.setAttr("%s.tx" %newContDup, e=True, k=True, l=False)
    cmds.setAttr("%s.ty" %newContDup, e=True, k=True, l=False)
    cmds.setAttr("%s.tz" %newContDup, e=True, k=True, l=False)
    cmds.setAttr("%s.rx" %newContDup, e=True, k=True, l=False)
    cmds.setAttr("%s.ry" %newContDup, e=True, k=True, l=False)
    cmds.setAttr("%s.rz" %newContDup, e=True, k=True, l=False)
    cmds.setAttr("%s.sx" %newContDup, e=True, k=True, l=False)
    cmds.setAttr("%s.sy" %newContDup, e=True, k=True, l=False)
    cmds.setAttr("%s.sz" %newContDup, e=True, k=True, l=False)

    cmds.makeIdentity(newContDup, a=True)

    #Make sure the new controllers transform are zeroed at the (0,0,0)
    offset = cmds.xform(newContDup, q=True, ws=True, rp=True)
    rvOffset = [x * -1 for x in offset]
    cmds.xform(newContDup, ws=True, t=rvOffset)


    cmds.makeIdentity(newContDup, apply=True, t=True, r=False, s=True, n=False, pn=True)

    ## get the same color code
    # pm.setAttr(newContDup.getShape()+".overrideEnabled", pm.getAttr(oldCont.getShape()+".overrideEnabled"))
    cmds.setAttr("%s.overrideEnabled" % newContDup.getShape(), cmds.getAttr("%s.overrideEnabled" % oldCont.getShape()))

    # pm.setAttr(newContDup.getShape()+".overrideColor", pm.getAttr(oldCont.getShape()+".overrideColor"))
    cmds.setAttr("%s.overrideColor" % newContDup.getShape(), cmds.getAttr("%s.overrideColor" % oldCont.getShape()))




    #move the new controller to the old controllers place
    if alignToCenter:
        functions.alignTo(newContDup, oldCont, mode=2)
    else:
        functions.alignToAlter(newContDup, oldCont, mode=2)


    ## put the new controller shape under the same parent with the old first (if there is a parent)
    if oldCont.getParent():
        cmds.parent(newContDup, oldCont.getParent())
    cmds.makeIdentity(newContDup, apply=True)
    # move the pivot to the same position
    # pivotPoint = pm.xform(oldCont,q=True, t=True, ws=True)
    # pm.xform(newContDup, piv=pivotPoint, ws=True)


    if not keepOldShape:
        # pm.delete(oldCont.getShape())
        cmds.delete(cmds.listRelatives(oldCont, shapes=True, children=True))

    cmds.parent(newContDup.getShape(), oldCont, r=True, s=True)

    if mirror:
        # find the mirror of the oldController
        if "_LEFT_" in oldCont:
            mirrorName = oldCont.replace("_LEFT_", "_RIGHT_")
        elif "_RIGHT_" in oldCont:
            mirrorName = oldCont.replace("_RIGHT_", "_LEFT_")
        else:
            cmds.warning("Cannot find the mirror controller, skipping mirror part")
            if not keepOldShape:
                cmds.delete(oldCont.getShape())
            return
        oldContMirror = mirrorName

        # get the current transform
        transformDict_mir = {}
        for i in tryChannels:
            keptdata_mir = cmds.getAttr("%s.%s" % (oldContMirror, i))
            transformDict_mir[i] = keptdata_mir
            try:
                cmds.setAttr("%s.%s" % (oldContMirror, i), 0)
            except RuntimeError:
                pass

        newContDupMirror = cmds.duplicate(newCont)[0]
        cmds.makeIdentity(newContDupMirror, a=True)
        # Make sure the new controllers transform are zeroed at the (0,0,0)
        offset = cmds.xform(newContDupMirror, q=True, ws=True, rp=True)
        rvOffset = [x * -1 for x in offset]
        cmds.xform(newContDupMirror, ws=True, t=rvOffset)
        cmds.makeIdentity(newContDupMirror, apply=True, t=True, r=True, s=True, n=False, pn=True)
        cmds.setAttr("{0}.scale{1}".format(newContDupMirror, mirrorAxis), -1)
        cmds.makeIdentity(newContDupMirror, apply=True, s=True)

        ## get the same color code
        # pm.setAttr(newContDupMirror.getShape() + ".overrideEnabled", pm.getAttr(oldContMirror.getShape() + ".overrideEnabled"))
        cmds.setAttr("%s.overrideEnabled" % newContDupMirror.getShape(), cmds.getAttr("%s.overrideEnabled") % oldContMirror.getShape())


        # pm.setAttr(newContDupMirror.getShape() + ".overrideColor", pm.getAttr(oldContMirror.getShape() + ".overrideColor"))
        cmds.setAttr("%s.overrideColor" % newContDupMirror.getShape(), cmds.getAttr("%s.overrideColor" % oldContMirror.getShape()))


        # move the new controller to the old controllers place
        functions.alignToAlter(newContDupMirror, oldContMirror, mode=0)

        if not keepOldShape:
            # pm.delete(oldContMirror.getShape())
            cmds.delete(cmds.listRelatives(oldContMirror, shapes=True, children=True))

        newContDupMirror_shape = cmds.listRelatives(newContDupMirror, shapes=True, children=True)
        # pm.parent(newContDupMirror.getShape(), oldContMirror, r=True, s=True)


        for i in tryChannels:
            try:
                cmds.setAttr("%s.%s" % (oldContMirror, i), transformDict_mir[i])
            except RuntimeError:
                pass

    for i in tryChannels:
        try:
            cmds.setAttr("%s.%s" % (oldCont, i), transformDict[i])
        except RuntimeError:
            pass

def rigTransfer(oldSkin, newJointList, deleteOld=False):

    #duplicate the old skin
    newSkin = cmds.duplicate(oldSkin)[0]

    #add new joints influences to the skin cluster

    #copy skin weights from the old skin to the dup skin (with closest joint option)

    #delete the old skin(optional)
    if deleteOld:
        # name = oldSkin.name()
        cmds.delete(oldSkin)
        cmds.rename(newSkin, oldSkin)
