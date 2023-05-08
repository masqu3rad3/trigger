# pylint: disable=consider-using-f-string

from maya import cmds
from trigger.library import functions, attribute, transform, connection
from trigger.library import arithmetic as op


def replace_controller(old_controller, new_controller, mirror=True, mirror_axis="X", keep_old_shape=False,
                       keep_copy=False, align_to_center=False):
    """Replace old_controller with new_controller.

    Args:
        old_controller (str): The controller with the old shape
        new_controller (str): The new shape for the old controller
        mirror (bool): If True mirrors the controller shape
        mirror_axis (str): Mirror axis direction. Only valid if mirror set to True.
                            Defaults to "X"
        keep_old_shape (bool): If True does not delete the old controller shape
        keep_copy (bool): If True, duplicates the new controller, keeping a copy of it intact
        align_to_center (bool): If True aligns to the center

    Returns:

    """

    # get the current transform
    try_channels = ["tx", "ty", "tz", "rx", "ry", "rz"]
    transform_dict = {}
    for attr in try_channels:
        kept_data = cmds.getAttr("%s.%s" % (old_controller, attr))
        transform_dict[attr] = kept_data
        try:
            cmds.setAttr("%s.%s" % (old_controller, attr), 0)
        except RuntimeError:
            pass

    new_cont_dup = cmds.duplicate(new_controller)[0] if keep_copy else new_controller
    # make a nested loop for all channels
    for attr in [(x, y) for x in "trs" for y in "xyz"]:
        cmds.setAttr("{0}.{1}{2}".format(new_cont_dup, attr[0], attr[1]), e=True, k=True, l=False)

    cmds.makeIdentity(new_cont_dup, a=True)

    # Make sure the new controllers transform are zeroed at the (0,0,0)
    offset = cmds.xform(new_cont_dup, q=True, ws=True, rp=True)
    rv_offset = [x * -1 for x in offset]
    cmds.xform(new_cont_dup, ws=True, t=rv_offset)

    cmds.makeIdentity(new_cont_dup, apply=True, t=True, r=False, s=True, n=False, pn=True)

    # get the same color code
    cmds.setAttr("%s.overrideEnabled" % functions.get_shapes(new_cont_dup)[0],
                 cmds.getAttr("%s.overrideEnabled" % functions.get_shapes(old_controller)[0]))

    cmds.setAttr("%s.overrideColor" % functions.get_shapes(new_cont_dup)[0],
                 cmds.getAttr("%s.overrideColor" % functions.get_shapes(old_controller)[0]))

    # move the new controller to the old controllers place
    if align_to_center:
        functions.align_to(new_cont_dup, old_controller, position=True, rotation=True)
    else:
        functions.align_to_alter(new_cont_dup, old_controller, mode=2)

    # put the new controller shape under the same parent with the old first (if there is a parent)
    if functions.get_parent(old_controller):
        cmds.parent(new_cont_dup, functions.get_parent(old_controller))
    cmds.makeIdentity(new_cont_dup, apply=True)

    if not keep_old_shape:
        cmds.delete(cmds.listRelatives(old_controller, shapes=True, children=True))

    cmds.parent(functions.get_shapes(new_cont_dup)[0], old_controller, r=True, s=True)

    if mirror:
        # find the mirror of the oldController
        if old_controller.startswith("L_"):
            mirror_name = old_controller.replace("L_", "R_")
        elif old_controller.startswith("R_"):
            mirror_name = old_controller.replace("R_", "L_")
        else:
            cmds.warning("Cannot find the mirror controller, skipping mirror part")
            if not keep_old_shape:
                cmds.delete(functions.get_shapes(old_controller))
            return
        old_cont_mirror = mirror_name
        # get the current transform
        transform_dict_mirror = {}
        for attr in try_channels:
            kept_data_mirror = cmds.getAttr("{0}.{1}".format(old_cont_mirror, attr))
            transform_dict_mirror[attr] = kept_data_mirror
            try:
                cmds.setAttr("%s.%s" % (old_cont_mirror, attr), 0)
            except RuntimeError:
                pass

        new_cont_dup_mirror = cmds.duplicate(new_controller)[0]
        cmds.makeIdentity(new_cont_dup_mirror, a=True)
        # Make sure the new controllers transform are zeroed at the (0,0,0)
        offset = cmds.xform(new_cont_dup_mirror, q=True, ws=True, rp=True)
        rv_offset = [x * -1 for x in offset]
        cmds.xform(new_cont_dup_mirror, ws=True, t=rv_offset)
        cmds.makeIdentity(new_cont_dup_mirror, apply=True, t=True, r=True, s=True, n=False, pn=True)
        cmds.setAttr("{0}.scale{1}".format(new_cont_dup_mirror, mirror_axis), -1)
        cmds.makeIdentity(new_cont_dup_mirror, apply=True, s=True)

        # get the same color code
        cmds.setAttr("%s.overrideEnabled" % functions.get_shapes(new_cont_dup_mirror)[0],
                     cmds.getAttr("%s.overrideEnabled") % functions.get_shapes(old_cont_mirror)[0])
        cmds.setAttr("%s.overrideColor" % functions.get_shapes(new_cont_dup_mirror)[0],
                     cmds.getAttr("%s.overrideColor" % functions.get_shapes(old_cont_mirror)[0]))

        # move the new controller to the old controllers place
        functions.align_to_alter(new_cont_dup_mirror, old_cont_mirror, mode=0)

        if not keep_old_shape:
            cmds.delete(cmds.listRelatives(old_cont_mirror, shapes=True, children=True))

        for attr in try_channels:
            try:
                cmds.setAttr("{0}.{1}".format(old_cont_mirror, attr), transform_dict_mirror[attr])
            except RuntimeError:
                pass

    for attr in try_channels:
        try:
            cmds.setAttr("{0}.{1}".format(old_controller, attr), transform_dict[attr])
        except RuntimeError:
            pass


def replace_curve(orig_curve, new_curve, snap=True, transfer_color=True):
    """Replace orig_curve with new_curve.

    Args:
        orig_curve (str): nurbsCurve to replace.
        new_curve (str): nurbsCurve to replace with.
        maintain_offset (bool, optional): Match position. Defaults to True.
    """
    if snap:
        new_curve = cmds.duplicate(new_curve, rc=1)[0]
        cmds.parentConstraint(orig_curve, new_curve)

    if cmds.objectType(orig_curve) == 'transform' or cmds.objectType(orig_curve) == "joint":
        orig_shapes = cmds.listRelatives(orig_curve, shapes=True, type="nurbsCurve")
    else:
        raise Exception("Cant find the shape of the orig_curve")

    if cmds.objectType(new_curve) == 'transform' or cmds.objectType(new_curve) == "joint":
        new_shapes = cmds.listRelatives(new_curve, shapes=True, type="nurbsCurve")
    else:
        raise Exception("Cant find the shape of the new_curve")

    color = None
    if transfer_color:
        if cmds.getAttr(new_curve + ".overrideEnabled"):
            color = cmds.getAttr(new_curve + ".overrideColor")

    # Make amount of shapes equal
    shape_dif = len(orig_shapes) - len(new_shapes)
    if shape_dif != 0:
        # If original curve has fewer shapes, create new nulls until equal
        if shape_dif < 0:
            for shape in range(0, shape_dif * -1):
                dupe_curve = cmds.duplicate(orig_shapes, rc=1)[0]
                dupe_shape = cmds.listRelatives(dupe_curve, s=1)[0]
                # if color:
                #     cmds.setAttr(dupe_shape + ".overrideEnabled", 1)
                #     cmds.setAttr(dupe_shape + ".overrideColor", color)
                orig_shapes.append(dupe_shape)
                cmds.select(dupe_shape, orig_curve)
                cmds.parent(r=1, s=1)
                cmds.delete(dupe_curve)
        # If original curve has more shapes, delete shapes until equal
        if shape_dif > 0:
            for shape in range(0, shape_dif):
                cmds.delete(orig_shapes[shape])

    orig_shapes = cmds.listRelatives(orig_curve, s=1)
    # For each shape, transfer from original to new.
    for new_shape, orig_shape in zip(new_shapes, orig_shapes):
        if color:
            cmds.setAttr("{}.overrideEnabled".format(new_shape), 1)
            cmds.setAttr("{}.overrideColor".format(new_shape), color)
        cmds.connectAttr("{}.worldSpace".format(new_shape), "{}.create".format(orig_shape))

        cmds.dgeval("{}.worldSpace".format(orig_shape))
        cmds.disconnectAttr("{}.worldSpace".format(new_shape), "{}.create".format(orig_shape))

        spans = cmds.getAttr('{}.degree'.format(orig_shape))
        degree = cmds.getAttr('{}.spans'.format(orig_shape))
        for i in range(0, spans + degree):
            cmds.xform(orig_shape + '.cv[' + str(i) + ']', t=cmds.pointPosition(new_shape + '.cv[' + str(i) + ']'),
                       ws=1)

    if snap:
        cmds.delete(new_curve)


def mirror_controller(axis="x", node_list=None, side_flags=("L_", "R_"), side_bias="start", continue_on_fail=True):
    if not node_list:
        node_list = cmds.ls(sl=True)

    warnings = []

    bias_dict = {"start": "'{0}'.startswith('{1}')", "end": "'{0}'.endswith('{1}')", "include": "'{1}' in '{0}'"}
    if side_bias not in bias_dict.keys():
        cmds.error("Invalid argument: {0}".format(side_bias))
    for node in node_list:
        if eval(bias_dict[side_bias].format(node, side_flags[0])):
            other_side = node.replace(side_flags[0], side_flags[1])
        elif eval(bias_dict[side_bias].format(node, side_flags[1])):
            other_side = node.replace(side_flags[1], side_flags[0])
        else:
            if continue_on_fail:
                msg = "Cannot find side flags for %s. Skipping" % node
                cmds.warning(msg)
                warnings.append(msg)
                continue
            else:
                return -1
        if not cmds.objExists(other_side):
            if continue_on_fail:
                msg = "Cannot find the other side controller %s. Skipping" % other_side
                cmds.warning(msg)
                warnings.append(msg)
                continue
            else:
                return -1

        tmp_cont = cmds.duplicate(node, name="tmp_{0}".format(node), rr=True, renameChildren=True)
        # delete nodes below it
        cmds.transformLimits(tmp_cont, etx=(0, 0), ety=(0, 0), etz=(0, 0), erx=(0, 0), ery=(0, 0), erz=(0, 0),
                             esx=(0, 0), esy=(0, 0), esz=(0, 0))
        attribute.unlock(tmp_cont[0])
        cmds.delete(cmds.listRelatives(tmp_cont, type="transform"))

        # create a group for the selected controller
        node_grp = cmds.group(name="tmpGrp", em=True)
        cmds.parent(tmp_cont, node_grp)
        # get rid of the limits
        # ## mirror it on the given axis
        cmds.setAttr("%s.s%s" % (node_grp, axis), -1)
        # ungroup it
        cmds.ungroup(node_grp)
        # cmds.makeIdentity(tmp_cont[0], a=True, r=False, t=False, s=True)
        replace_curve(other_side, tmp_cont, snap=False)
        cmds.delete(tmp_cont)


# pylint: disable = too-many-arguments
def whip(node_list,
         attr_holder=None,
         create_up_grp=True,
         maximum_offset=5,
         diminish=0.8,
         attr_list=None
         ):
    """Create a whip like effect on the given nodes."""

    if not isinstance(node_list, list):
        cmds.error("node_list must be a list variable. duh...")
    if len(node_list) < 2:
        cmds.error("node_list must contain at least 2 elements. duh...")

    attr_holder = attr_holder or node_list[0]
    attr_list = attr_list or ["rx", "ry", "rz"]

    if create_up_grp:
        temp_list = []
        for node in node_list[1:]:
            up_node = functions.create_offset_group(node, "whip")
            cmds.makeIdentity(up_node, a=True)
            temp_list.append(up_node)
        node_list = [node_list[0]] + temp_list

    cmds.addAttr(attr_holder, ln="delay", at="long", defaultValue=maximum_offset, k=False)
    cmds.setAttr("{}.delay".format(attr_holder), edit=True, channelBox=True)
    cmds.addAttr(attr_holder, at="float", ln="powerDim", min=0, max=1, defaultValue=diminish, k=True)

    for attr in attr_list:
        cmds.addAttr(attr_holder, at="float", ln="offsetMult_%s" % attr, defaultValue=1, k=True)

    for nmb, node in enumerate(node_list[1:]):
        for attr in attr_list:
            frame_cache = cmds.createNode("frameCache", name="%s_frameCache" % node)
            choice = cmds.createNode("choice", name="%s_choice" % node)
            cmds.connectAttr("%s.delay" % attr_holder, "%s.selector" % choice)
            for x in range(0, maximum_offset + 1):
                cmds.connectAttr("{0}.past[{1}]".format(frame_cache, x), "{0}.input[{1}]".format(choice, x))
            power_mult = cmds.createNode("multDoubleLinear", name="%s_powerLose" % node)
            master_mult = cmds.createNode("multDoubleLinear", name="%s_%s_masterMult" % (attr_holder, attr))

            cmds.connectAttr("%s.%s" % (node_list[nmb], attr), "%s.input1" % power_mult)
            cmds.connectAttr("%s.powerDim" % attr_holder, "%s.input2" % power_mult)

            cmds.connectAttr("%s.output" % power_mult, "%s.input1" % master_mult)
            cmds.connectAttr("%s.%s" % (attr_holder, "offsetMult_%s" % attr), "%s.input2" % master_mult)

            cmds.connectAttr("%s.output" % master_mult, "%s.stream" % frame_cache)
            cmds.connectAttr("%s.output" % choice, "{0}.{1}".format(node, attr))


def whip_refresh():
    frame_caches = cmds.ls(type="frameCache")
    for cache in frame_caches:
        cmds.setAttr("%s.nodeState" % cache, 1)
        cmds.setAttr("%s.nodeState" % cache, 0)


def copy_controller(a, b=None, axis=None, side_flags=("L_", "R_"), side_bias="start"):
    # get the other side
    bias_dict = {"start": "'{0}'.startswith('{1}')", "end": "'{0}'.endswith('{1}')", "include": "'{1}' in '{0}'"}
    if side_bias not in bias_dict.keys():
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
    # delete nodes below it
    cmds.delete(cmds.listRelatives(temp_cont, type="transform"))
    attribute.unlock(temp_cont)
    transform.free_limits(temp_cont)

    cmds.parent(temp_cont, world=True)
    cmds.setAttr("%s.r" % temp_cont, 0, 0, 0)
    temp_loc = cmds.spaceLocator()[0]
    functions.align_to_alter(temp_cont, temp_loc, mode=0)
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
        else:
            raise ValueError("object type must be a joint or locator")
        obj_list.append(obj)

        motion_path = cmds.shadingNode('motionPath', n="%s_motionPath" % obj, asUtility=True)
        cmds.connectAttr("%s.worldSpace[0]" % curve_obj, "%s.geometryPath" % motion_path)
        cmds.connectAttr('%s.allCoordinates.xCoordinate' % motion_path, '%s.translateX' % obj)
        cmds.connectAttr('%s.allCoordinates.yCoordinate' % motion_path, '%s.translateY' % obj)
        cmds.connectAttr('%s.allCoordinates.zCoordinate' % motion_path, '%s.translateZ' % obj)
        u_value = cmds.getAttr('%s.maxValue' % curve_obj)
        cmds.setAttr('%s.uValue' % motion_path, incr)
        incr += u_value / (num_of_objects - 1)

    cmds.group(obj_list, n="{0}_{1}s".format(curve_obj, object_type))
    if aim:
        clusters = []
        up_vec_curve = cmds.duplicate(curve_obj, n='%s_upVec_curve' % curve_obj)[0]
        cmds.xform(up_vec_curve, t=[1, 0, 0], r=1)
        # Create clusters along curve & upVec curve. Transform rotate pivots to original curve
        spans = cmds.getAttr('%s.degree' % curve_obj)
        degree = cmds.getAttr('%s.spans' % curve_obj)
        # For number of cv points, create cluster handles for both curve & duplicate.
        for i in range(0, spans + degree):
            cv_pos = cmds.pointPosition("{0}.cv[{1}]".format(curve_obj, str(i)))
            cluster, _clusterHandle = cmds.cluster("{0}.cv[{1}]".format(curve_obj, str(i)),
                                                   "{0}.cv[{1}]".format(up_vec_curve, str(i)),
                                                   n="{0}{1}_cluster".format(curve_obj, i))
            cmds.xform(_clusterHandle, rp=cv_pos)
            clusters.append(_clusterHandle)

        # Create objects/joints along new curve
        up_vec_joints = motion_path_spline(up_vec_curve, num_of_objects, aim=False)

        for i in range(0, len(obj_list)):
            if obj_list[i] == obj_list[-1]:
                break
            cmds.aimConstraint(up_vec_joints[i],
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
        cmds.group(cluster_grp, up_vec_joints, up_vec_curve, n=curve_obj + '_aim_grp')

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
    functions.align_to(root_loc, joint_chain[0], position=True, rotation=True)
    connection.matrixConstraint(root_controller, root_loc, skipRotate="xyz", maintainOffset=True)
    cmds.aimConstraint(end_controller, root_loc, wuo=root_controller)

    end_loc = cmds.spaceLocator(name="endLoc_%s" % name)[0]
    end_loc_shape = functions.get_shapes(end_loc)[0]
    functions.align_to(end_loc, end_controller, position=True, rotation=True)
    cmds.parent(end_loc, root_loc)
    soft_blend_loc = cmds.spaceLocator(name="softBlendLoc_%s" % name)[0]
    soft_blend_loc_shape = functions.get_shapes(soft_blend_loc)[0]
    functions.align_to(soft_blend_loc, end_controller, position=True, rotation=True)
    connection.matrix_switch(end_controller, end_loc, soft_blend_loc, "%s.stretch" % end_controller, position=True,
                             rotation=True)

    if not distance_start:
        distance_start_loc = cmds.spaceLocator(name="distance_start_%s" % name)[0]
        connection.matrixConstraint(root_controller, distance_start_loc, skipRotate="xyz", skipScale="xyz",
                                    maintainOffset=False)
    else:
        distance_start_loc = distance_start

    if not distance_end:
        distance_end_loc = cmds.spaceLocator(name="distance_end_%s" % name)[0]
        connection.matrixConstraint(end_controller, distance_end_loc, skipRotate="xyz", skipScale="xyz",
                                    maintainOffset=False)
    else:
        distance_end_loc = distance_end

    ctrl_distance = cmds.createNode("distanceBetween", name="distance_%s" % name)
    cmds.connectAttr("%s.translate" % distance_start_loc, "%s.point1" % ctrl_distance)
    cmds.connectAttr("%s.translate" % distance_end_loc, "%s.point2" % ctrl_distance)
    ctrl_distance_p = "%s.distance" % ctrl_distance

    plugs_to_sum = []
    for nmb, jnt in enumerate(joint_chain[1:]):
        dist = functions.get_distance(jnt, joint_chain[nmb])
        cmds.addAttr(jnt, ln="initialDistance", at="double", dv=dist)
        plugs_to_sum.append("%s.initialDistance" % jnt)
        # cmds.connectAttr("%s.initialDistance" %jnt, "%s.input1D[%i]" %(sum_of_initial_lengths, nmb))

    sum_of_lengths_p = op.add(value_list=plugs_to_sum)

    # SOFT IK PART
    soft_ik_out = op.add("%s.softIK" % end_controller, 0.001)
    # soft_ik_sub1_p = op.subtract(sum_of_lengths_p, "%s.softIK" % end_controller)
    soft_ik_sub1_p = op.subtract(sum_of_lengths_p, soft_ik_out)
    # get the scale value from controller
    scale_mult_matrix = cmds.createNode("multMatrix", name="_multMatrix")
    scale_decompose_matrix = cmds.createNode("decomposeMatrix", name="_decomposeMatrix")
    cmds.connectAttr("%s.worldMatrix[0]" % root_controller, "%s.matrixIn[0]" % scale_mult_matrix)
    cmds.connectAttr("%s.matrixSum" % scale_mult_matrix, "%s.inputMatrix" % scale_decompose_matrix)

    global_scale_div_p = op.divide(1, "%s.outputScaleX" % scale_decompose_matrix, name="global_scale_div")
    if is_local:
        global_mult_p = ctrl_distance_p
    else:
        global_mult_p = op.multiply(ctrl_distance_p, global_scale_div_p, name="global_mult")
    soft_ik_sub2_p = op.subtract(global_mult_p, soft_ik_sub1_p, name="softIK_sub2")
    # soft_ik_div_p = op.divide(soft_ik_sub2_p, "%s.softIK" % end_controller, name="softIK_div")
    soft_ik_div_p = op.divide(soft_ik_sub2_p, soft_ik_out, name="softIK_div")
    soft_ik_invert_p = op.invert(soft_ik_div_p, name="softIK_invert")
    soft_ik_exponent_p = op.power(2.71828, soft_ik_invert_p, name="softIK_exponent")
    # soft_ik_mult_p = op.multiply(soft_ik_exponent_p, "%s.softIK" % end_controller, name="softIK_mult")
    soft_ik_mult_p = op.multiply(soft_ik_exponent_p, soft_ik_out, name="softIK_mult")
    soft_ik_sub3_p = op.subtract(sum_of_lengths_p, soft_ik_mult_p, name="softIK_sub3")

    condition_zero_p = op.if_else("%s.softIK" % end_controller, ">", 0, soft_ik_sub3_p, sum_of_lengths_p,
                                  name="condition_zero")
    condition_length_p = op.if_else(global_mult_p, ">", soft_ik_sub1_p, condition_zero_p, global_mult_p,
                                    name="condition_length")

    cmds.connectAttr(condition_length_p, "%s.tx" % end_loc)

    # STRETCHING PART
    soft_distance = cmds.createNode("distanceBetween", name="distanceSoft_%s" % name)
    cmds.connectAttr("%s.worldPosition[0]" % end_loc_shape, "%s.point1" % soft_distance)
    cmds.connectAttr("%s.worldPosition[0]" % soft_blend_loc_shape, "%s.point2" % soft_distance)
    soft_distance_p = "%s.distance" % soft_distance

    stretch_global_div_p = op.divide(soft_distance_p, "%s.outputScaleX" % scale_decompose_matrix,
                                     name="stretch_global_div")
    initial_divide_p = op.divide(ctrl_distance_p, sum_of_lengths_p)

    for jnt in joint_chain[1:]:
        div_initial_by_sum_p = op.divide("%s.initialDistance" % jnt, sum_of_lengths_p)
        mult1_p = op.multiply(stretch_global_div_p, div_initial_by_sum_p)
        sum1_p = op.add(mult1_p, "%s.initialDistance" % jnt)
        squash_mult_p = op.multiply(initial_divide_p, "%s.initialDistance" % jnt)

        clamp_p = op.clamp(squash_mult_p, maximum="%s.initialDistance" % jnt)
        switch_p = op.switch(clamp_p, squash_mult_p, "%s.stretch" % end_controller)

        squash_blend_node = cmds.createNode("blendColors", name="squash_blend_%s" % name)
        # cmds.connectAttr(squash_mult_p, "%s.color1R" %squash_blend_node)
        cmds.connectAttr(switch_p, "%s.color1R" % squash_blend_node)
        # Stretch limit
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
        connection.matrixConstraint(soft_blend_loc, x, maintainOffset=True, source_parent_cutoff=source_parent_cutoff)

    # connection.matrixConstraint(soft_blend_loc, ik_handle, mo=False, source_parent_cutoff=source_parent_cutoff)
    return soft_blend_loc, root_loc, distance_start_loc, distance_end_loc
