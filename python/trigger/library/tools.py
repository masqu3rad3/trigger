
from maya import cmds
from trigger.library import functions

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
    cmds.setAttr("%s.overrideEnabled" % functions.getShapes(newContDup)[0], cmds.getAttr("%s.overrideEnabled" % functions.getShapes(oldCont)[0]))

    # pm.setAttr(newContDup.getShape()+".overrideColor", pm.getAttr(oldCont.getShape()+".overrideColor"))
    cmds.setAttr("%s.overrideColor" % functions.getShapes(newContDup)[0], cmds.getAttr("%s.overrideColor" % functions.getShapes(oldCont)[0]))




    #move the new controller to the old controllers place
    if alignToCenter:
        functions.alignTo(newContDup, oldCont, mode=2)
    else:
        functions.alignToAlter(newContDup, oldCont, mode=2)


    ## put the new controller shape under the same parent with the old first (if there is a parent)
    if functions.getParent(oldCont):
        cmds.parent(newContDup, functions.getParent(oldCont))
    cmds.makeIdentity(newContDup, apply=True)
    # move the pivot to the same position
    # pivotPoint = pm.xform(oldCont,q=True, t=True, ws=True)
    # pm.xform(newContDup, piv=pivotPoint, ws=True)


    if not keepOldShape:
        # pm.delete(oldCont.getShape())
        cmds.delete(cmds.listRelatives(oldCont, shapes=True, children=True))

    cmds.parent(functions.getShapes(newContDup)[0], oldCont, r=True, s=True)

    if mirror:
        # find the mirror of the oldController
        if oldCont.startswith("L_"):
            mirrorName = oldCont.replace("L_", "R_")
        elif oldCont.startswith("R_"):
            mirrorName = oldCont.replace("R_", "L_")
        else:
            cmds.warning("Cannot find the mirror controller, skipping mirror part")
            if not keepOldShape:
                # cmds.delete(oldCont.getShape())
                cmds.delete(functions.getShapes(oldCont))
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
        # cmds.setAttr("%s.overrideEnabled" % newContDupMirror.getShape(), cmds.getAttr("%s.overrideEnabled") % oldContMirror.getShape())
        cmds.setAttr("%s.overrideEnabled" % functions.getShapes(newContDupMirror)[0], cmds.getAttr("%s.overrideEnabled") % functions.getShapes(oldContMirror)[0])


        # pm.setAttr(newContDupMirror.getShape() + ".overrideColor", pm.getAttr(oldContMirror.getShape() + ".overrideColor"))
        # cmds.setAttr("%s.overrideColor" % newContDupMirror.getShape(), cmds.getAttr("%s.overrideColor" % oldContMirror.getShape()))
        cmds.setAttr("%s.overrideColor" % functions.getShapes(newContDupMirror)[0], cmds.getAttr("%s.overrideColor" % functions.getShapes(oldContMirror)[0]))


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


def replace_curve(orig_curve, new_curve, maintain_offset=True):
    """Replace orig_curve with new_curve.

    Args:
        orig_curve (str): nurbsCurve to replace.
        new_curve (str): nurbsCurve to replace with.
        maintain_offset (bool, optional): Match position. Defaults to True.
    """
    if maintain_offset == True:
        new_curve = cmds.duplicate(new_curve, rc=1)[0]
        cmds.parentConstraint(orig_curve, new_curve)

    if cmds.objectType(orig_curve) == 'transform':
        orig_shapes = cmds.listRelatives(orig_curve, s=1)

    if cmds.objectType(new_curve) == 'transform':
        new_shapes = cmds.listRelatives(new_curve, s=1)

    color = None
    if cmds.getAttr(orig_shapes[0] + ".overrideEnabled"):
        color = cmds.getAttr(orig_shapes[0] + ".overrideColor")

    # Make amount of shapes equal
    shape_dif = len(orig_shapes) - len(new_shapes)
    if shape_dif != 0:
        # If original curve has less shapes, create new nulls until equal
        if shape_dif < 0:
            for shape in range(0, shape_dif * -1):
                dupe_curve = cmds.duplicate(orig_shapes, rc=1)[0]
                dupe_shape = cmds.listRelatives(dupe_curve, s=1)[0]
                if color:
                    cmds.setAttr(dupe_shape + ".overrideEnabled", 1)
                    cmds.setAttr(dupe_shape + ".overrideColor", color)
                orig_shapes.append(dupe_shape)
                cmds.select(dupe_shape, orig_curve)
                cmds.parent(r=1, s=1)
                cmds.delete(dupe_curve)
        # If original curve has more shapes, delete shapes until equal
        if shape_dif > 0:
            for shape in range(0, shape_dif):
                cmds.delete(orig_shapes[shape])

    orig_shapes = cmds.listRelatives(orig_curve, s=1)
    # For each shape, transfer from orignal to new.
    for new_shape, orig_shape in zip(new_shapes, orig_shapes):
        cmds.connectAttr(new_shape + ".worldSpace", orig_shape + ".create")

        cmds.dgeval(orig_shape + ".worldSpace")
        cmds.disconnectAttr(new_shape + ".worldSpace", orig_shape + ".create")

        spans = cmds.getAttr(orig_shape + '.degree')
        degree = cmds.getAttr(orig_shape + '.spans')
        for i in range(0, spans + degree):
            cmds.xform(orig_shape + '.cv[' + str(i) + ']', t=cmds.pointPosition(new_shape + '.cv[' + str(i) + ']'),
                       ws=1)

    if maintain_offset == True:
        cmds.delete(new_curve)


def mirrorController(axis="x", node_list=None, side_flags=("L_", "R_"), side_bias="start"):
    if not node_list:
        node_list = cmds.ls(sl=True)

    warnings = []

    bias_dict = {"start": "'{0}'.startswith('{1}')", "end": "'{0}'.endswith('{1}')", "include": "'{1}' in '{0}'"}
    if not side_bias in bias_dict.keys():
        cmds.error("Invalid argument: {0}".format(side_bias))
    for node in node_list:
        if eval(bias_dict[side_bias].format(node, side_flags[0])):
            other_side = node.replace(side_flags[0], side_flags[1])
        elif eval(bias_dict[side_bias].format(node, side_flags[1])):
            other_side = node.replace(side_flags[1], side_flags[0])
        else:
            msg = "Cannot find side flags for %s. Skipping" % node
            cmds.warning(msg)
            warnings.append(msg)
            continue
        if not cmds.objExists(other_side):
            msg = "Cannot find the other side controller %s. Skipping" % other_side
            cmds.warning(msg)
            warnings.append(msg)
            continue

        tmp_cont = cmds.duplicate(node, name="tmp_{0}".format(node), rr=True, renameChildren=True)
        ## delete nodes below it
        cmds.delete(cmds.listRelatives(tmp_cont, type="transform"))

        ## create a group for the selected controller
        node_grp = cmds.group(name="tmpGrp", em=True)
        cmds.parent(tmp_cont, node_grp)
        # get rid of the limits
        cmds.transformLimits(tmp_cont, etx=(0, 0), ety=(0, 0), etz=(0, 0), erx=(0, 0), ery=(0, 0), erz=(0, 0),
                             esx=(0, 0), esy=(0, 0), esz=(0, 0))
        # ## mirror it on the given axis
        cmds.setAttr("%s.s%s" % (node_grp, axis), -1)
        ## ungroup it
        cmds.ungroup(node_grp)
        replace_curve(other_side, tmp_cont, maintain_offset=False)
        cmds.delete(tmp_cont)

# replace_curve(orig_curve=cmds.ls(sl=1)[0], new_curve=cmds.ls(sl=1)[1], maintain_offset=True)
# mirrorController()

from maya import cmds
from trigger.library import functions


def whip(node_list, attr_holder=None, create_up_grp=True, offset=5, diminish=0.8, attr_list=None):
    if type(node_list) is not list:
        cmds.error("node_list must be a list variable. duh...")
    if len(node_list) < 2:
        cmds.error("node_list must contain at least 2 elements. duh...")

    attr_holder = node_list[0] if not attr_holder else attr_holder
    attr_list = ["rx", "ry", "rz"] if not attr_list else attr_list

    if create_up_grp:
        temp_list = []
        for node in node_list[1:]:
            up_node = functions.createUpGrp(node, "whip")
            cmds.makeIdentity(up_node, a=True)
            temp_list.append(up_node)
        node_list = [node_list[0]] + temp_list
        # node_list = [functions.createUpGrp(node, "whip") for node in node_list]

    cmds.addAttr(attr_holder, at="float", ln="powerDim", min=0, max=1, defaultValue=0.8, k=True)

    for attr in attr_list:
        cmds.addAttr(attr_holder, at="float", ln="offsetMult_%s" % attr, defaultValue=1, k=True)

    for nmb, node in enumerate(node_list[1:]):
        print("*" * 30)
        print(nmb, node, node_list[nmb])
        print("*" * 30)
        for attr in attr_list:
            frame_cache = cmds.createNode("frameCache", name="%s_frameCache" % node)
            power_mult = cmds.createNode("multDoubleLinear", name="%s_powerlose" % node)
            master_mult = cmds.createNode("multDoubleLinear", name="%s_%s_masterMult" % (attr_holder, attr))

            cmds.connectAttr("%s.%s" % (node_list[nmb], attr), "%s.input1" % power_mult)
            cmds.connectAttr("%s.powerDim" % attr_holder, "%s.input2" % power_mult)

            cmds.connectAttr("%s.output" % power_mult, "%s.input1" % master_mult)
            cmds.connectAttr("%s.%s" % (attr_holder, "offsetMult_%s" % attr), "%s.input2" % (master_mult))

            cmds.connectAttr("%s.output" % master_mult, "%s.stream" % frame_cache)
            cmds.connectAttr("%s.past[%s]" % (frame_cache, int(offset)), "%s.%s" % (node, attr))


def whip_refresh():
    frame_caches = cmds.ls(type="frameCache")
    for cache in frame_caches:
        cmds.setAttr("%s.nodeState" % cache, 1)
        # cmds.refresh()
        cmds.setAttr("%s.nodeState" % cache, 0)
        # cmds.refresh()
