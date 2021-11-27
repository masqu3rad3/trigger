from maya import cmds
from trigger.library import functions, attribute, transform, connection
from trigger.library import arithmetic as op


def replaceController(mirror=True, mirrorAxis="X", keepOldShape=False, keepAcopy=False, alignToCenter=False, *args,
                      **kwargs):
    if kwargs:
        if kwargs["oldController"] and kwargs["newController"]:
            oldCont = kwargs["oldController"]
            newCont = kwargs["newController"]
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
        keptdata = cmds.getAttr("%s.%s" % (oldCont, i))
        transformDict[i] = keptdata
        try:
            cmds.setAttr("%s.%s" % (oldCont, i), 0)
        except RuntimeError:
            pass

    if keepAcopy:
        newContDup = cmds.duplicate(newCont)[0]
    else:
        newContDup = newCont

    cmds.setAttr("%s.tx" % newContDup, e=True, k=True, l=False)
    cmds.setAttr("%s.ty" % newContDup, e=True, k=True, l=False)
    cmds.setAttr("%s.tz" % newContDup, e=True, k=True, l=False)
    cmds.setAttr("%s.rx" % newContDup, e=True, k=True, l=False)
    cmds.setAttr("%s.ry" % newContDup, e=True, k=True, l=False)
    cmds.setAttr("%s.rz" % newContDup, e=True, k=True, l=False)
    cmds.setAttr("%s.sx" % newContDup, e=True, k=True, l=False)
    cmds.setAttr("%s.sy" % newContDup, e=True, k=True, l=False)
    cmds.setAttr("%s.sz" % newContDup, e=True, k=True, l=False)

    cmds.makeIdentity(newContDup, a=True)

    # Make sure the new controllers transform are zeroed at the (0,0,0)
    offset = cmds.xform(newContDup, q=True, ws=True, rp=True)
    rvOffset = [x * -1 for x in offset]
    cmds.xform(newContDup, ws=True, t=rvOffset)

    cmds.makeIdentity(newContDup, apply=True, t=True, r=False, s=True, n=False, pn=True)

    ## get the same color code
    cmds.setAttr("%s.overrideEnabled" % functions.getShapes(newContDup)[0],
                 cmds.getAttr("%s.overrideEnabled" % functions.getShapes(oldCont)[0]))

    cmds.setAttr("%s.overrideColor" % functions.getShapes(newContDup)[0],
                 cmds.getAttr("%s.overrideColor" % functions.getShapes(oldCont)[0]))

    # move the new controller to the old controllers place
    if alignToCenter:
        functions.alignTo(newContDup, oldCont, mode=2)
    else:
        functions.alignToAlter(newContDup, oldCont, mode=2)

    ## put the new controller shape under the same parent with the old first (if there is a parent)
    if functions.getParent(oldCont):
        cmds.parent(newContDup, functions.getParent(oldCont))
    cmds.makeIdentity(newContDup, apply=True)

    if not keepOldShape:
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
        cmds.setAttr("%s.overrideEnabled" % functions.getShapes(newContDupMirror)[0],
                     cmds.getAttr("%s.overrideEnabled") % functions.getShapes(oldContMirror)[0])
        cmds.setAttr("%s.overrideColor" % functions.getShapes(newContDupMirror)[0],
                     cmds.getAttr("%s.overrideColor" % functions.getShapes(oldContMirror)[0]))

        # move the new controller to the old controllers place
        functions.alignToAlter(newContDupMirror, oldContMirror, mode=0)

        if not keepOldShape:
            cmds.delete(cmds.listRelatives(oldContMirror, shapes=True, children=True))

        newContDupMirror_shape = cmds.listRelatives(newContDupMirror, shapes=True, children=True)

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
    # duplicate the old skin
    newSkin = cmds.duplicate(oldSkin)[0]

    # add new joints influences to the skin cluster

    # copy skin weights from the old skin to the dup skin (with closest joint option)

    # delete the old skin(optional)
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
        cmds.setAttr("%s.nodeState" % cache, 0)


def copy_controller(a, b=None, axis=None, side_flags=("L_", "R_"), side_bias="start"):
    # get the other side
    bias_dict = {"start": "'{0}'.startswith('{1}')", "end": "'{0}'.endswith('{1}')", "include": "'{1}' in '{0}'"}
    if not side_bias in bias_dict.keys():
        cmds.error("Invalid argument: {0}".format(side_bias))

    if not b:
        if eval(bias_dict[side_bias].format(a, side_flags[0])):
            b = a.replace(side_flags[0], side_flags[1])
        elif eval(bias_dict[side_bias].format(a, side_flags[1])):
            b = a.replace(side_flags[1], side_flags[0])
        else:
            msg = "Cannot find side flags for %s. Skipping" % a
            cmds.warning(msg)
            return

        if not cmds.objExists(b):
            msg = "Cannot find the other side controller %s. Skipping" % b
            cmds.warning(msg)
            return

    # extract the stuff from the controller
    temp_cont = cmds.duplicate(a, name="tmp_{0}".format(a), rr=True, renameChildren=True)[0]
    ## delete nodes below it
    cmds.delete(cmds.listRelatives(temp_cont, type="transform"))
    attribute.unlock(temp_cont)
    transform.free_limits(temp_cont)

    cmds.parent(temp_cont, world=True)
    cmds.setAttr("%s.r" % temp_cont, 0, 0, 0)
    temp_loc = cmds.spaceLocator()[0]
    functions.alignToAlter(temp_cont, temp_loc, mode=0)
    cmds.delete(temp_loc)
    cmds.makeIdentity(temp_cont, a=True)
    if axis:
        cmds.setAttr("{0}.s{1}".format(temp_cont, axis), -1)
    cmds.makeIdentity(temp_cont, a=True)

    replace_curve(b, temp_cont)
    cmds.delete(temp_cont)


def motion_path_spline(curve_obj, num_of_objects, object_type="joint", aim=False):
    incr = 0
    obj_list = []
    for i in range(num_of_objects):
        if object_type == "joint":
            obj = cmds.joint(n="{0}_{1}_jnt".format(curve_obj, i))
        elif object_type == "locator":
            obj = cmds.spaceLocator(n="{0}_{1}_loc".format(curve_obj, i))[0]
        obj_list.append(obj)

        motion_path = cmds.shadingNode('motionPath', n="%s_motionPath" % obj, asUtility=True)
        cmds.connectAttr("%s.worldSpace[0]" % curve_obj, "%s.geometryPath" % motion_path)
        cmds.connectAttr('%s.allCoordinates.xCoordinate' % motion_path, '%s.translateX' % obj)
        cmds.connectAttr('%s.allCoordinates.yCoordinate' % motion_path, '%s.translateY' % obj)
        cmds.connectAttr('%s.allCoordinates.zCoordinate' % motion_path, '%s.translateZ' % obj)
        u_value = cmds.getAttr('%s.maxValue' % curve_obj)
        cmds.setAttr('%s.uValue' % motion_path, incr)
        incr += u_value / (num_of_objects - 1)

    grp = cmds.group(obj_list, n="{0}_{1}s".format(curve_obj, object_type))

    if aim == True:
        clusters = []
        upVec_curve = cmds.duplicate(curve_obj, n='%s_upVec_curve' % curve_obj)[0]
        cmds.xform(upVec_curve, t=[1, 0, 0], r=1)
        # Create clusters along curve & upVec curve. Transform rotate pivots to original curve
        spans = cmds.getAttr('%s.degree' % curve_obj)
        degree = cmds.getAttr('%s.spans' % curve_obj)
        # For number of cv points, create cluster handles for both curve & duplicate.
        for i in range(0, spans + degree):
            cv_pos = cmds.pointPosition("{0}.cv[{1}]".format(curve_obj, str(i)))
            cluster, _clusterHandle = cmds.cluster("{0}.cv[{1}]".format(curve_obj, str(i)),
                                                   "{0}.cv[{1}]".format(upVec_curve, str(i)),
                                                   n="{0}{1}_cluster".format(curve_obj, i))
            cmds.xform(_clusterHandle, rp=cv_pos)
            clusters.append(_clusterHandle)

        # Create objects/joints along new curve
        upVec_jnts = motion_path_spline(upVec_curve, num_of_objects, aim=False)

        for i in range(0, len(obj_list)):
            if obj_list[i] == obj_list[-1]:
                break
            cmds.aimConstraint(upVec_jnts[i],
                               obj_list[i],
                               weight=1,
                               upVector=(0, 1, 0),
                               worldUpObject=obj_list[i + 1],
                               worldUpType="object",
                               offset=(0, 0, 0),
                               aimVector=(1, 0, 0),
                               worldUpVector=(1, 0, 0))
        # Cleanup aim
        cluster_grp = cmds.group(clusters, n='%s_aim_clusters' % curve_obj)
        aim_grp = cmds.group(cluster_grp, upVec_jnts, upVec_curve, n=curve_obj + '_aim_grp')

        return obj_list, clusters
    return obj_list


def make_stretchy_ik(joint_chain, ik_handle, root_controller, end_controller, side="L", source_parent_cutoff=None,
                     name=None, distance_start=None, distance_end=None, is_local=False):
    if not name:
        name = joint_chain[0]

    if type(ik_handle) != list:
        ik_handle = [ik_handle]

    attribute.validate_attr("%s.squash" % end_controller, attr_type="double", attr_range=[0.0, 1.0], default_value=0.0)
    attribute.validate_attr("%s.stretch" % end_controller, attr_type="double", attr_range=[0.0, 1.0], default_value=1.0)
    attribute.validate_attr("%s.stretchLimit" % end_controller, attr_type="double", attr_range=[0.0, 99999.0],
                            default_value=100.0)
    attribute.validate_attr("%s.softIK" % end_controller, attr_type="double", attr_range=[0.0, 100.0],
                            default_value=0.0)

    root_loc = cmds.spaceLocator(name="rootLoc_%s" % name)[0]
    functions.alignTo(root_loc, joint_chain[0], position=True, rotation=True)
    connection.matrixConstraint(root_controller, root_loc, sr="xyz", mo=True)
    cmds.aimConstraint(end_controller, root_loc, wuo=root_controller)

    end_loc = cmds.spaceLocator(name="endLoc_%s" % name)[0]
    end_loc_shape = functions.getShapes(end_loc)[0]
    functions.alignTo(end_loc, end_controller, position=True, rotation=True)
    cmds.parent(end_loc, root_loc)
    soft_blend_loc = cmds.spaceLocator(name="softBlendLoc_%s" % name)[0]
    soft_blend_loc_shape = functions.getShapes(soft_blend_loc)[0]
    functions.alignTo(soft_blend_loc, end_controller, position=True, rotation=True)
    connection.matrixSwitch(end_controller, end_loc, soft_blend_loc, "%s.stretch" % end_controller, position=True,
                            rotation=True)

    if not distance_start:
        distance_start_loc = cmds.spaceLocator(name="distance_start_%s" % name)[0]
        connection.matrixConstraint(root_controller, distance_start_loc, sr="xyz", ss="xyz", mo=False)
    else:
        distance_start_loc = distance_start

    if not distance_end:
        distance_end_loc = cmds.spaceLocator(name="distance_end_%s" % name)[0]
        connection.matrixConstraint(end_controller, distance_end_loc, sr="xyz", ss="xyz", mo=False)
    else:
        distance_end_loc = distance_end

    ctrl_distance = cmds.createNode("distanceBetween", name="distance_%s" % name)
    cmds.connectAttr("%s.translate" % distance_start_loc, "%s.point1" % ctrl_distance)
    cmds.connectAttr("%s.translate" % distance_end_loc, "%s.point2" % ctrl_distance)
    ctrl_distance_p = "%s.distance" % ctrl_distance

    plugs_to_sum = []
    for nmb, jnt in enumerate(joint_chain[1:]):
        dist = functions.getDistance(jnt, joint_chain[nmb])
        cmds.addAttr(jnt, ln="initialDistance", at="double", dv=dist)
        plugs_to_sum.append("%s.initialDistance" % jnt)
        # cmds.connectAttr("%s.initialDistance" %jnt, "%s.input1D[%i]" %(sum_of_initial_lengths, nmb))

    sum_of_lengths_p = op.add(value_list=plugs_to_sum)

    # SOFT IK PART
    softIK_sub1_p = op.subtract(sum_of_lengths_p, "%s.softIK" % end_controller)
    # get the scale value from controller
    scale_multMatrix = cmds.createNode("multMatrix", name="_multMatrix")
    scale_decomposeMatrix = cmds.createNode("decomposeMatrix", name="_decomposeMatrix")
    cmds.connectAttr("%s.worldMatrix[0]" % root_controller, "%s.matrixIn[0]" % scale_multMatrix)
    cmds.connectAttr("%s.matrixSum" % scale_multMatrix, "%s.inputMatrix" % scale_decomposeMatrix)

    global_scale_div_p = op.divide(1, "%s.outputScaleX" % scale_decomposeMatrix, name="global_scale_div")
    if is_local:
        global_mult_p = ctrl_distance_p
    else:
        global_mult_p = op.multiply(ctrl_distance_p, global_scale_div_p, name="global_mult")
    softIK_sub2_p = op.subtract(global_mult_p, softIK_sub1_p, name="softIK_sub2")
    softIK_div_p = op.divide(softIK_sub2_p, "%s.softIK" % end_controller, name="softIK_div")
    softIK_invert_p = op.invert(softIK_div_p, name="softIK_invert")
    softIK_exponent_p = op.power(2.71828, softIK_invert_p, name="softIK_exponent")
    softIK_mult_p = op.multiply(softIK_exponent_p, "%s.softIK" % end_controller, name="softIK_mult")
    softIK_sub3_p = op.subtract(sum_of_lengths_p, softIK_mult_p, name="softIK_sub3")

    condition_zero_p = op.if_else("%s.softIK" % end_controller, ">", 0, softIK_sub3_p, sum_of_lengths_p,
                                  name="condition_zero")
    condition_length_p = op.if_else(global_mult_p, ">", softIK_sub1_p, condition_zero_p, global_mult_p,
                                    name="condition_length")

    cmds.connectAttr(condition_length_p, "%s.tx" % end_loc)

    # STRETCHING PART
    soft_distance = cmds.createNode("distanceBetween", name="distanceSoft_%s" % name)
    cmds.connectAttr("%s.worldPosition[0]" % end_loc_shape, "%s.point1" % soft_distance)
    cmds.connectAttr("%s.worldPosition[0]" % soft_blend_loc_shape, "%s.point2" % soft_distance)
    soft_distance_p = "%s.distance" % soft_distance

    stretch_global_div_p = op.divide(soft_distance_p, "%s.outputScaleX" % scale_decomposeMatrix,
                                     name="stretch_global_div")
    initial_divide_p = op.divide(ctrl_distance_p, sum_of_lengths_p)

    for jnt in joint_chain[1:]:
        div_initial_by_sum_p = op.divide("%s.initialDistance" % jnt, sum_of_lengths_p)
        mult1_p = op.multiply(stretch_global_div_p, div_initial_by_sum_p)
        sum1_p = op.add(mult1_p, "%s.initialDistance" % jnt)
        squash_mult_p = op.multiply(initial_divide_p, "%s.initialDistance" % jnt)

        clamp_p = op.clamp(squash_mult_p, max="%s.initialDistance" % jnt)
        switch_p = op.switch(clamp_p, squash_mult_p, "%s.stretch" % end_controller)

        squash_blend_node = cmds.createNode("blendColors", name="squash_blend_%s" % name)
        # cmds.connectAttr(squash_mult_p, "%s.color1R" %squash_blend_node)
        cmds.connectAttr(switch_p, "%s.color1R" % squash_blend_node)
        ## Stretch limit
        clamp_node = cmds.createNode("clamp", name="stretchLimit_%s" % name)
        max_distance_p = op.add("%s.stretchLimit" % end_controller, "%s.initialDistance" % jnt)
        cmds.connectAttr(sum1_p, "%s.inputR" % clamp_node)
        cmds.connectAttr(max_distance_p, "%s.maxR" % clamp_node)
        cmds.connectAttr(sum1_p, "%s.minR" % clamp_node)
        ##
        cmds.connectAttr("%s.outputR" % clamp_node, "%s.color2R" % squash_blend_node)
        cmds.connectAttr("%s.squash" % end_controller, "%s.blender" % squash_blend_node)

        # SIDE
        # if right side, invert X?
        if side == "R":
            output_x_p = op.invert("%s.outputR" % squash_blend_node, name="side_invert")
        else:
            output_x_p = "%s.outputR" % squash_blend_node
        cmds.connectAttr(output_x_p, "%s.tx" % jnt)

    for x in ik_handle:
        connection.matrixConstraint(soft_blend_loc, x, mo=True, source_parent_cutoff=source_parent_cutoff)

    # connection.matrixConstraint(soft_blend_loc, ik_handle, mo=False, source_parent_cutoff=source_parent_cutoff)
    return soft_blend_loc, root_loc, distance_start_loc, distance_end_loc


def angle_extractors(root_node, fixed_node, float_offset, suffix=""):
    # TODO THIS METHOD IS WIP
    angle_ext_root = cmds.spaceLocator(name="angleExt_Root_IK_%s" % suffix)[0]
    angle_ext_fixed = cmds.spaceLocator(name="angleExt_Fixed_IK_%s" % suffix)[0]
    angle_ext_float = cmds.spaceLocator(name="angleExt_Float_IK_%s" % suffix)[0]
    cmds.parent(angle_ext_fixed, angle_ext_float, angle_ext_root)
    # connection.matrixConstraint(self.limbPlug, angle_ext_root, mo=False)
    # cmds.pointConstraint(self.handIkCont.name, angle_ext_fixed, mo=False)
    # functions.alignToAlter(angle_ext_float, self.j_def_collar, 2)
    # cmds.move(0, 0, -self.sideMult * 5, angle_ext_float, objectSpace=True)

    angle_node_ik = cmds.createNode("angleBetween", name="angleBetweenIK_%s" % suffix)
    angle_remap_ik = cmds.createNode("remapValue", name="angleRemapIK_%s" % suffix)
    angle_mult_ik = cmds.createNode("multDoubleLinear", name="angleMultIK_%s" % suffix)

    cmds.connectAttr("{0}.translate".format(angle_ext_fixed), "{0}.vector1".format(angle_node_ik))
    cmds.connectAttr("{0}.translate".format(angle_ext_float), "{0}.vector2".format(angle_node_ik))

    cmds.connectAttr("{0}.angle".format(angle_node_ik), "{0}.inputValue".format(angle_remap_ik))
    cmds.setAttr("{0}.inputMin".format(angle_remap_ik), cmds.getAttr("{0}.angle".format(angle_node_ik)))
    cmds.setAttr("{0}.inputMax".format(angle_remap_ik), 0)
    cmds.setAttr("{0}.outputMin".format(angle_remap_ik), 0)
    cmds.setAttr("{0}.outputMax".format(angle_remap_ik), cmds.getAttr("{0}.angle".format(angle_node_ik)))

    cmds.connectAttr("{0}.outValue".format(angle_remap_ik), "{0}.input1".format(angle_mult_ik))
    cmds.setAttr("{0}.input2".format(angle_mult_ik), 0.5)

    return angle_ext_root, angle_ext_fixed, angle_ext_float
