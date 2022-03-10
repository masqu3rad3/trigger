from importlib import reload
from maya import cmds
from trigger.library import functions, connection
from trigger.utils import parentToSurface

reload(parentToSurface)
from trigger.core.decorators import keepselection
from trigger.objects.controller import Controller

inits = cmds.ls("jInit_strap*", type="joint")
suffix = "C_strap"
surface = "pSphere1"


@keepselection
def _create_joint(name, align_to=None):
    jnt = cmds.joint(name=name)
    if align_to:
        functions.alignTo(jnt, align_to, rotation=True, position=True)
    return jnt


@keepselection
def _create_lock(name, align_to=None):
    lock = cmds.spaceLocator(name=name)[0]
    if align_to:
        functions.alignTo(lock, align_to, rotation=True, position=True)
    return lock


# groups
conts_grp = cmds.group(name="%s_conts_grp" % suffix, em=True)
joints_grp = cmds.group(name="%s_joints_grp" % suffix, em=True)
follicle_grp = cmds.group(name="%s_follicle_grp" % suffix, em=True)
master_grp = cmds.group([conts_grp, joints_grp, follicle_grp], name="%s_grp" % suffix)

# create deformation joints
def_joints = []
locks = []
conts = []
for nmb, j in enumerate(inits):
    cmds.select(d=True)
    j_def = _create_joint("jDef_%s%s" % (suffix, nmb + 1), align_to=j)
    def_joints.append(j_def)

    cont = Controller(name="cont_%s%s" % (suffix, nmb + 1), shape="Circle")
    cont_bind = cont.add_offset("bind")
    cont_off = cont.add_offset("pos")
    functions.alignTo(cont_off, j, position=True, rotation=True)
    connection.matrixConstraint(cont.name, j_def, mo=False)
    fol = parentToSurface.parentToSurface([cont_bind], surface, mode="matrixConstraint")

    cmds.parent(cont_bind, conts_grp)
    cmds.parent(fol, follicle_grp)
    cmds.parent(j_def, joints_grp)
