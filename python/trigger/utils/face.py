"""Collection of face utils that are not complex enough to be an action or not yet implemented as action"""

from maya import cmds
from trigger.library import functions, attribute, deformers
from trigger.core.decorators import undo
# from trigger.utils.skinTransfer import skinTransfer

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