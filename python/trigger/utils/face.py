"""Collection of face utils that are not complex enough to be an action or not yet implemented as action"""

from maya import cmds
from trigger.library import functions, attribute, deformers, connection, tools, arithmetic, api
from trigger.core.decorators import undo

@undo
def shrink_wrap_eyebulge(
        face_mesh,
        proxy_eye_ball,
        iris_guide,
        resolution=30,
        look_axis="+z",
        local_inf=2,
        eyescale=1.0,
        group=None,
):
    """Basic eye bulge with shrink wrap and lattice deformer without the need for extra helper geo.

    Args:
        face_mesh (String): The mesh which will be deformed
        proxy_eye_ball (String): eye ball proxy. The scale attributes needs to be unlocked if eyescale is different than 1.0
        iris_guide (String): Guide geometry (preferably joint) sits on the iris.
        resolution (int): overall resolution of the proxies and lattices.
        look_axis (str): Characters facing direction. Default is 'z'.
        local_inf (int): Local influence value of lattice deformers.
        eyescale (float): Multiplier for eye scale. The movement will be as if the eye is this big.
        group (String): If defined, everything will be tucked inside this group. Else 'eye_bulging' group will be used

    Returns: Eye Bulge Group

    """
    axis_d = {"+x": (1, 0, 0), "+y": (0, 1, 0), "+z": (0, 0, 1), "-x": (-1, 0, 0), "-y": (0, -1, 0), "-z": (0, 0, -1),}
    res_d = {
        "+x": (2, resolution, resolution),
        "+y": (resolution, 2, resolution),
        "+z": (resolution, resolution, 2),
        "-x": (2, resolution, resolution),
        "-y": (resolution, 2, resolution),
        "-z": (resolution, resolution, 2),
    }
    raw_axis = look_axis.replace("+", "").replace("-", "")

    group = group or "eye_bulging"
    bulge_grp = functions.validateGroup(group)

    mesh_res = resolution - 1

    cmds.xform(proxy_eye_ball, cp=True)
    for axis in "xyz":
        value = cmds.getAttr("{0}.s{1}".format(proxy_eye_ball, axis))
        cmds.setAttr(
            "{0}.s{1}".format(proxy_eye_ball, axis), (value * eyescale)
        )
    cmds.hide(proxy_eye_ball)
    cmds.parent(proxy_eye_ball, bulge_grp)
    # create proxy plane and proxy box

    proxy_plane = cmds.polyPlane(
        width=5,
        height=5,
        sh=mesh_res,
        sw=mesh_res,
        name="proxy_plane_{0}".format(iris_guide.replace("_env", "")),
        ax=axis_d[look_axis],
    )[0]
    proxy_box = cmds.polyCube(
        name="proxy_cube",
        width=5,
        height=15,
        depth=5,
        ax=axis_d[look_axis],
    )[0]

    functions.alignTo(proxy_plane, iris_guide, position=True, rotation=True)
    functions.alignTo(proxy_box, iris_guide, position=True, rotation=True)
    cmds.setAttr("{0}.s{1}".format(proxy_box, raw_axis.lower()), 0.05)

    # Create the shrink wrap
    # ----------------------
    shrink_wrap = deformers.create_shrink_wrap(proxy_eye_ball, proxy_plane, name=None, projection=3,
                                               targetInflation=0.02, falloff=0.2, falloffIterations=1, reverse=True)

    # Create the Lattice Deformer
    # ---------------------------
    lattice_name = "%s_ffd" % iris_guide.replace("_jnt", "")
    lattice_deformer, lattice_points, lattice_base = cmds.lattice(
        proxy_box,
        divisions=res_d[look_axis],
        cp=1,
        ldv=(local_inf, local_inf, local_inf),
        ol=True,
        objectCentered=True,
        name=lattice_name,
    )

    # get the deformer set for lattice
    lattice_set = cmds.listConnections(
        lattice_deformer, s=False, d=True, type="objectSet"
    )[0]
    # detach the lattice from proxy and bind to face
    cmds.sets(face_mesh, fe=lattice_set)

    # lattice attributes
    cmds.setAttr("{0}.outsideLattice".format(lattice_deformer), 2)
    cmds.setAttr("{0}.outsideFalloffDist".format(lattice_deformer), 7)

    cmds.delete(proxy_box)

    # parent them under the rig. Do that before wrap two prevent
    # calculating wrap bind twice
    lattice_grp = cmds.listRelatives(lattice_points, p=True, s=False)[0]
    cmds.parent([proxy_plane, lattice_grp], bulge_grp)

    deformers.create_wrap(proxy_plane, lattice_points, exclusiveBind=False)

    return bulge_grp


def parse_sides(input_list):
    middle = int(float(len(input_list))/2)
    if middle % 2 != 0:
        return input_list[:int(len(input_list)/2)], [input_list[int(middle - .5)]], list(reversed(input_list[int((len(input_list)/2)+1):]))
    else:
        return input_list[:int(len(input_list)/2)], [], list(reversed(input_list[int((len(input_list)/2)):]))


def lip_zipper(upper_lip_edges, lower_lip_edges, morph_mesh, final_mesh, pair_count, controller=None):
    cmds.select(upper_lip_edges)
    upper_lip_curve = cmds.polyToCurve(ch=0, name="follicles_up_grp")[0]

    cmds.select(lower_lip_edges)
    lower_lip_curve = cmds.polyToCurve(ch=0, name="follicles_low_grp")[0]
    cmds.reverseCurve(lower_lip_curve, ch=0)

    rig_grp = functions.validateGroup("rig_grp")

    face_mesh = upper_lip_edges[0].split(".")[0]
    lipzip_grp = "lipZip_grp"
    lipzip_mesh = deformers.localize(final_mesh, "local_face", local_target_name="trigger_lipZipMesh",
                                     group_name=lipzip_grp)
    cmds.parent(lipzip_grp, rig_grp)
    jnt_grp = cmds.group(name="lipzipJnt_grp", em=True)
    cmds.parent(jnt_grp, lipzip_grp)
    cmds.select(d=True)
    lipzip_root_jnt = cmds.joint(name="lipZip_root_jDef")
    cmds.parent(lipzip_root_jnt, jnt_grp)
    switch_hook = cmds.group(em=True, name="lipZip_switch_hook")

    cmds.parent(switch_hook, lipzip_grp)
    switch_loc_grp = cmds.group(name="switchLocs_grp", em=True)
    cmds.parent(switch_loc_grp, lipzip_grp)

    upper_locators = tools.motion_path_spline(upper_lip_curve, pair_count, object_type="locator")
    lower_locators = tools.motion_path_spline(lower_lip_curve, pair_count, object_type="locator")
    upper_locators_grp = functions.getParent(upper_locators[0])
    lower_locators_grp = functions.getParent(lower_locators[0])
    cmds.parent(upper_locators_grp, lipzip_grp)
    cmds.parent(lower_locators_grp, lipzip_grp)

    cmds.delete([upper_lip_curve, lower_lip_curve])

    for loc in upper_locators + lower_locators:
        connection.pin_to_surface(loc, morph_mesh, sr="xyz")

    counter = 0

    hook_U_attrs = []
    hook_D_attrs = []
    hook_dist_attrs = []
    for up, low in zip(upper_locators, lower_locators):

        mid_loc_common = cmds.spaceLocator(name="midLoc_common%i" % counter)[0]
        cmds.pointConstraint(up, low, mid_loc_common, mo=False)
        cmds.parent(mid_loc_common, switch_loc_grp)

        mid_loc_up = cmds.spaceLocator(name="midLoc_up%i" % counter)[0]
        functions.alignTo(mid_loc_up, up, position=True, rotation=False)
        cmds.parent(mid_loc_up, mid_loc_common)

        mid_loc_low = cmds.spaceLocator(name="midLoc_low%i" % counter)[0]
        functions.alignTo(mid_loc_low, low, position=True, rotation=False)
        cmds.parent(mid_loc_low, mid_loc_common)

        switch_up = cmds.spaceLocator(name="switchLoc_up%i" % counter)[0]
        u_attr = "U{0}".format(str(counter).zfill(2))
        connection.matrixSwitch(mid_loc_up, up, switch_up, "{0}.{1}".format(switch_hook, u_attr))
        hook_U_attrs.append(u_attr)
        cmds.parent(switch_up, switch_loc_grp)

        switch_low = cmds.spaceLocator(name="switchLoc_low%i" % counter)[0]
        d_attr = "D{0}".format(str(counter).zfill(2))
        connection.matrixSwitch(mid_loc_low, low, switch_low, "{0}.{1}".format(switch_hook, d_attr))
        hook_D_attrs.append(d_attr)
        cmds.parent(switch_low, switch_loc_grp)

        local_loc_up = cmds.spaceLocator(name="localLoc_up%i" % counter)[0]
        connection.matrixConstraint(switch_up, local_loc_up, mo=False, source_parent_cutoff=up)
        local_loc_up_off = functions.createUpGrp(local_loc_up, "off")
        functions.alignTo(local_loc_up_off, up, position=True, rotation=False)
        cmds.parent(local_loc_up_off, switch_loc_grp)

        local_loc_low = cmds.spaceLocator(name="localLoc_low%i" % counter)[0]
        connection.matrixConstraint(switch_low, local_loc_low, mo=False, source_parent_cutoff=low)
        local_loc_low_off = functions.createUpGrp(local_loc_low, "off")
        functions.alignTo(local_loc_low_off, up, position=True, rotation=False)
        cmds.parent(local_loc_low_off, switch_loc_grp)

        cmds.select(d=True)
        joint_up = cmds.joint(name="lipZip_up%i_jDef" % counter)
        functions.alignTo(joint_up, up, position=True, rotation=False)
        connection.matrixConstraint(local_loc_up, joint_up, mo=False, sr="xyz", ss="xyz")
        cmds.parent(joint_up, jnt_grp)

        cmds.select(d=True)
        joint_low = cmds.joint(name="lipZip_low%i_jDef" % counter)
        functions.alignTo(joint_low, low, position=True, rotation=False)
        connection.matrixConstraint(local_loc_low, joint_low, mo=False, sr="xyz", ss="xyz")
        cmds.parent(joint_low, jnt_grp)

        # create distance attributes
        distance_node = cmds.createNode("distanceBetween", name="distance_%i" % counter)
        loc_up_shape = functions.getShapes(up)[0]
        loc_low_shape = functions.getShapes(low)[0]
        cmds.connectAttr("%s.worldPosition[0]" % loc_up_shape, "%s.point1" % distance_node)
        cmds.connectAttr("%s.worldPosition[0]" % loc_low_shape, "%s.point2" % distance_node)
        distance_attr_name = "dist{0}".format(str(counter).zfill(2))
        dist_attr = attribute.create_attribute(switch_hook, attr_name=distance_attr_name, attr_type="float")
        if cmds.getAttr("%s.distance" % distance_node):
            normalized_distance_p = arithmetic.subtract("%s.distance" % distance_node,
                                                        float(cmds.getAttr("%s.distance" % distance_node)))
        else:
            normalized_distance_p = "%s.distance" % distance_node
        cmds.connectAttr(normalized_distance_p, dist_attr)
        hook_dist_attrs.append(distance_attr_name)

        counter += 1

    U_Left, U_C, U_Right = parse_sides(hook_U_attrs)
    D_Left, D_C, D_Right = parse_sides(hook_D_attrs)

    U_Left_loc, U_C_loc, U_Right_loc = parse_sides(upper_locators)
    D_Left_loc, D_C_loc, D_Right_loc = parse_sides(lower_locators)

    controller = controller or switch_hook
    attribute.separator(controller, name="Lip Zip")
    attribute.create_attribute(node=controller, nice_name="L_Zip", attr_name="lZip", attr_type="float", min_value=0,
                               max_value=100, display=False)
    attribute.create_attribute(node=controller, nice_name="R_Zip", attr_name="rZip", attr_type="float", min_value=0,
                               max_value=100, display=False)
    attribute.create_attribute(node=controller, nice_name="Ramp Edges", attr_name="rampEdges", attr_type="float",
                               min_value=0, max_value=100)
    attribute.create_attribute(node=controller, nice_name="Ramp Center", attr_name="rampCenter", attr_type="float",
                               min_value=0, max_value=100)
    attribute.create_attribute(node=controller, nice_name="Auto_Sticky", attr_name="stickyness", attr_type="float",
                               min_value=0, max_value=1)
    attribute.create_attribute(node=controller, nice_name="Auto_Distance", attr_name="stickyDistance",
                               attr_type="float", default_value=1)
    attribute.create_attribute(node=controller, nice_name="Auto_Strength", attr_name="stickyStrength",
                               attr_type="float", default_value=5)

    inc_value = 100.0 / float(len(U_Left) + 1)
    plus_node = None
    minus_node = None
    plus_clamp = None
    minus_clamp = None
    set_range = None
    average_node = None
    auto_range = None
    auto_clamp = None

    for n, side_group in enumerate([[U_Left + U_C, D_Left + D_C], [U_Right + U_C, D_Right + D_C]]):
        zip_attr = "%s.lZip" % controller if n == 0 else "%s.rZip" % controller
        rampA_attr = "%s.rampEdges" % controller
        rampB_attr = "%s.rampCenter" % controller
        for nmb, (up, down) in enumerate(zip(side_group[0], side_group[1])):
            mod = nmb % 3
            if mod == 0:
                plus_node = cmds.createNode("plusMinusAverage", name="plus")
                cmds.setAttr("%s.operation" % plus_node, 1)
                minus_node = cmds.createNode("plusMinusAverage", name="minus")
                cmds.setAttr("%s.operation" % minus_node, 2)
                plus_clamp = cmds.createNode("clamp")
                cmds.setAttr("%s.min" % plus_clamp, 0, 0, 0)
                cmds.setAttr("%s.max" % plus_clamp, 100, 100, 100)
                minus_clamp = cmds.createNode("clamp")
                cmds.setAttr("%s.min" % minus_clamp, 0, 0, 0)
                cmds.setAttr("%s.max" % minus_clamp, 100, 100, 100)
                set_range = cmds.createNode("setRange")
                cmds.setAttr("%s.min" % set_range, 0, 0, 0)
                cmds.setAttr("%s.max" % set_range, 1, 1, 1)

                # auto nodes
                auto_range = cmds.createNode("setRange", name="autoRange")
                cmds.setAttr("%s.min" % auto_range, 1, 1, 1)
                cmds.setAttr("%s.oldMax" % auto_range, 1, 1, 1)
                auto_clamp = cmds.createNode("clamp")
                cmds.setAttr("%s.min" % auto_clamp, 0, 0, 0)
                cmds.setAttr("%s.max" % auto_clamp, 1, 1, 1)

                # make the connections
                for a in "xyz":
                    cmds.connectAttr(zip_attr, "{0}.value{1}".format(set_range, a.upper()))
                    cmds.connectAttr(rampA_attr, "{0}.input3D[1].input3D{1}".format(plus_node, a))
                    cmds.connectAttr(rampB_attr, "{0}.input3D[1].input3D{1}".format(minus_node, a))
                    cmds.connectAttr("%s.stickyStrength" % controller, "{0}.min{1}".format(auto_range, a.upper()))
                    cmds.connectAttr("%s.stickyDistance" % controller, "{0}.oldMax{1}".format(auto_range, a.upper()))
                cmds.connectAttr("%s.output3D" % plus_node, "%s.input" % plus_clamp)
                cmds.connectAttr("%s.output3D" % minus_node, "%s.input" % minus_clamp)
                cmds.connectAttr("%s.output" % plus_clamp, "%s.oldMax" % set_range)
                cmds.connectAttr("%s.output" % minus_clamp, "%s.oldMin" % set_range)

                # auto
                cmds.connectAttr("%s.outValue" % auto_range, "%s.input" % auto_clamp)

                spare_attr = "X"
                clamp_spare = "R"
            elif mod == 1:
                spare_attr = "Y"
                clamp_spare = "G"
            elif mod == 2:
                spare_attr = "Z"
                clamp_spare = "B"

            # set the values for each pair
            cmds.setAttr("{0}.input3D[0].input3D{1}".format(plus_node, spare_attr.lower()), (nmb + 1) * inc_value)
            cmds.setAttr("{0}.input3D[0].input3D{1}".format(minus_node, spare_attr.lower()), (nmb) * inc_value)

            # center joints averaged between two sides
            if up in U_C or down in D_C:
                center_average = "{0}_{1}_average".format(up, down)
                if not cmds.objExists(center_average):
                    center_average = cmds.createNode("plusMinusAverage", name=center_average)
                    cmds.setAttr("%s.operation" % center_average, 3)
                next_index = attribute.getNextIndex("%s.input1D" % center_average)
                cmds.connectAttr("{0}.outValue{1}".format(set_range, spare_attr),
                                 "{0}.input1D[{1}]".format(center_average, next_index))
                output_p = "%s.output1D" % center_average
            else:
                output_p = "{0}.outValue{1}".format(set_range, spare_attr)

            # auto
            # this is very ugly way of getting the correct index number in all distance attributes
            source_dist_attr = down.replace("D", "dist")
            dist_index = (n * (len(side_group[0]) - 1)) + nmb
            # print(hook_dist_attrs, dist_index)
            cmds.connectAttr("{0}.{1}".format(switch_hook, source_dist_attr),
                             "{0}.value{1}".format(auto_range, spare_attr))
            blend_node = cmds.createNode("blendTwoAttr", name="blendAuto")
            cmds.connectAttr(output_p, "{0}.input[0]".format(blend_node))
            cmds.connectAttr("{0}.output{1}".format(auto_clamp, clamp_spare), "{0}.input[1]".format(blend_node))
            cmds.connectAttr("{0}.stickyness".format(controller), "{0}.attributesBlender".format(blend_node))

            cmds.connectAttr("%s.output" % blend_node, "{0}.{1}".format(switch_hook, up), force=True)
            cmds.connectAttr("%s.output" % blend_node, "{0}.{1}".format(switch_hook, down), force=True)

    if cmds.objExists("pref_cont"):
        cmds.connectAttr("pref_cont.Rig_Visibility", "trigger_lipZipMesh.v")
        cmds.connectAttr("pref_cont.Rig_Visibility", "switchLocs_grp.v")
        cmds.connectAttr("pref_cont.Rig_Visibility", "follicles_up_grp_locators.v")
        cmds.connectAttr("pref_cont.Rig_Visibility", "follicles_low_grp_locators.v")
        cmds.connectAttr("pref_cont.Joints_Visibility", "lipzipJnt_grp.v")

        attribute.lockAndHide(lipzip_grp)
        attribute.lockAndHide(jnt_grp)
        attribute.lockAndHide(switch_hook)
        attribute.lockAndHide(switch_loc_grp)

def face_switcher(bs_node, tongue_cont, l_eye_plug, r_eye_plug, upper_teeth_joint, switch_data, pref_cont="pref_cont"):
    """
    Creates a morphable face target

    Args:
        bs_node: Final face blendshape node
        tongue_cont: Tongue Root controller
        l_eye_plug: plug joint for left eye
        r_eye_plug: plug joint for right eye
        upper_teeth_joint: joint that only moves the upper teeth (not the gum)
        switch_data: dictionaries list for each face target.
                        e.g.:
                        switch_data = [
                        {
                            "name": "Officer",
                            "face": "charHumanAvA_officerFace_IDmulti_1",
                            "left_eye_pos": (-3.1209197044372558594, 170.943603515625, -9.8993054047092847725),
                            "right_eye_pos": (3.0962610244750976562, 170.946258544921875, -9.8466892853245191475),
                        },
                            {
                            "name": "Karl",
                            "face": "charHumanAvA_KarlFace_IDmulti_1",
                            "left_eye_pos": (-3.2438907623291015625, 171.622161865234375, -9.4153041839599609375),
                            "right_eye_pos": (3.2974126338958740234, 171.62481689453125, -9.3626880645751953125),
                        },
                        {
                            "name": "Elf",
                            "face": "face_IDskin_1",
                            "left_eye_pos": (-3.305, 171.376, -9.84),
                            "right_eye_pos": (3.305, 171.376, -9.84),
                        },
        pref_cont: Optional, Controller which will hold the morph attributes. Default is 'pref_cont'


    Returns:

    """
    l_eye_parent = functions.getParent(l_eye_plug)
    r_eye_parent = functions.getParent(r_eye_plug)
    upper_teeth_parent = functions.getParent(upper_teeth_joint)

    L_eye_b_node = cmds.createNode("blendMatrix", name="charBlender_Leye")
    L_eye_b_m_p = arithmetic.multiply_matrix(["%s.outputMatrix" %L_eye_b_node, cmds.getAttr("%s.worldInverseMatrix[0]" %l_eye_parent)])
    L_eye_b_out_p, _, _ = arithmetic.decompose_matrix(L_eye_b_m_p)

    R_eye_b_node = cmds.createNode("blendMatrix", name="charBlender_Reye")
    R_eye_b_m_p = arithmetic.multiply_matrix(["%s.outputMatrix" % R_eye_b_node, cmds.getAttr("%s.worldInverseMatrix[0]" %r_eye_parent)])
    R_eye_b_out_p, _, _ = arithmetic.decompose_matrix(R_eye_b_m_p)

    upper_teeth_node = cmds.createNode("blendMatrix", name="charBlender_upperTeeth")
    upper_teeth_m_p = arithmetic.multiply_matrix(["%s.outputMatrix" % upper_teeth_node, cmds.getAttr("%s.worldInverseMatrix[0]" % upper_teeth_parent)])
    upper_teeth_out_p, _, _ = arithmetic.decompose_matrix(upper_teeth_m_p)

    # initial input connections
    L_eye_inmatrix = cmds.xform(l_eye_plug, q=True, m=True, ws=True)
    R_eye_inmatrix = cmds.xform(r_eye_plug, q=True, m=True, ws=True)
    upper_teeth_inmatrix = cmds.xform(upper_teeth_joint, q=True, m=True, ws=True)

    cmds.setAttr("%s.inputMatrix" % L_eye_b_node, L_eye_inmatrix, type="matrix")
    cmds.setAttr("%s.inputMatrix" % R_eye_b_node, R_eye_inmatrix, type="matrix")
    cmds.setAttr("%s.inputMatrix" % upper_teeth_node, upper_teeth_inmatrix, type="matrix")

    # connect blender outputs
    cmds.connectAttr(L_eye_b_out_p, "%s.t" % l_eye_plug)
    cmds.connectAttr(R_eye_b_out_p, "%s.t" % r_eye_plug)
    cmds.connectAttr(upper_teeth_out_p, "%s.t" % upper_teeth_joint)

    attribute.separator(pref_cont, "Morphs")

    for nmb, data in enumerate(switch_data):
        attribute.create_attribute("pref_cont", attr_name=data["name"], attr_type="float", min_value=0, max_value=1)
        # morph the target face into the the morph_blendhshape
        deformers.add_target_blendshape(bs_node, data["face"])
        attribute.drive_attrs("%s.%s" % (pref_cont, data["name"]), "%s.%s" % (bs_node, data["face"]), driver_range=[0, 1], driven_range=[0, 1])

        leye_ref = cmds.spaceLocator(name="temp_leye_ref")[0]
        cmds.setAttr("%s.t" % leye_ref, *data["left_eye_pos"])
        reye_ref = cmds.spaceLocator(name="temp_reye_ref")[0]
        cmds.setAttr("%s.t" % reye_ref, *data["right_eye_pos"])
        upperTeeth_ref = cmds.spaceLocator(name="temp_upperTeeth_ref")[0]
        functions.alignTo(upperTeeth_ref, upper_teeth_joint, position=True, rotation=False)
        cmds.parent(upperTeeth_ref, tongue_cont)
        # get the new teeth position by temporarily turning on the switch
        cmds.setAttr("%s.%s" % (pref_cont, data["name"]), 1)
        cmds.parent(upperTeeth_ref, world=True)
        cmds.setAttr("%s.%s" % (pref_cont, data["name"]), 0)

        cmds.setAttr("{0}.target[{1}].targetMatrix".format(L_eye_b_node, nmb), cmds.xform(leye_ref, q=True, m=True, ws=True), type="matrix")
        attribute.drive_attrs("%s.%s" % (pref_cont, data["name"]), "{0}.target[{1}].weight".format(L_eye_b_node, nmb), driver_range=[0, 1], driven_range=[0, 1], force=False)

        cmds.setAttr("{0}.target[{1}].targetMatrix".format(R_eye_b_node, nmb), cmds.xform(reye_ref, q=True, m=True, ws=True), type="matrix")
        attribute.drive_attrs("%s.%s" % (pref_cont, data["name"]), "{0}.target[{1}].weight".format(R_eye_b_node, nmb), driver_range=[0, 1], driven_range=[0, 1], force=False)

        cmds.setAttr("{0}.target[{1}].targetMatrix".format(upper_teeth_node, nmb), cmds.xform(upperTeeth_ref, q=True, m=True, ws=True), type="matrix")
        attribute.drive_attrs("%s.%s" % (pref_cont, data["name"]), "{0}.target[{1}].weight".format(upper_teeth_node, nmb), driver_range=[0, 1], driven_range=[0, 1], force=False)

        functions.deleteObject([leye_ref, reye_ref, upperTeeth_ref])