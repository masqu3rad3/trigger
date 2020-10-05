import pymel.core as pm

reload(arm)

reload(tentacleClass)

t= tentacleClass.Tentacle()
t.createTentacle(pm.ls(sl=True), "test", npResolution=5.0, jResolution=25.0, blResolution=25.0,dropoff=2.0)

from T_Rigger_deprecated import mrCubic

mrCubic.mrCube(pm.ls("jDef*", type="joint"))



# a=arm.Arm()
# a.createArm(pm.ls(sl=True),suffix="testArm",side="L")


---------------------------------------

import pymel.core as pm
from tik_autorigger.T_Rigger import extraProcedures as extra

reload(extra)
import pymel.core.datatypes as dt

refJoints = pm.ls(sl=True)
up_axis, mirror_axis, look_axis = extra.getRigAxes(refJoints[0])

extra.orientJoints(refJoints,
                   aimAxis=-dt.Vector(mirror_axis),
                   upAxis=-dt.Vector(up_axis),
                   worldUpAxis=(0.0, 0.0, 1.0))