from maya import cmds
from importlib import reload
from trigger.base import initials
from trigger.modules import base
from trigger.modules import singleton
reload(singleton)

cmds.file(new=True, force=True)

# test surface object
test_sil = cmds.polyCylinder()
cmds.setAttr("%s.height" % test_sil[1], 10)
cmds.setAttr("%s.radius" % test_sil[1], 0.5)
cmds.setAttr("%s.subdivisionsHeight" % test_sil[1], 50)
cmds.setAttr("%s.t" % test_sil[0], 8, 2, 5)
cmds.setAttr("%s.rz" % test_sil[0], 90)
cmds.delete(test_sil[0], ch=True)
cmds.makeIdentity(test_sil[0], a=True)

initializer = initials.Initials()
baseG = base.Guides()
baseG.createGuides()
guider = singleton.Guides(side="L", segments=4)
guider.createGuides()

cmds.setAttr("%s.surface" % guider.guideJoints[0], test_sil[0], type="string")
cmds.move(4,2,5, guider.guideJoints[0])
cmds.setAttr("%s.localJoints" % guider.guideJoints[0], True)

cmds.parent(guider.guideJoints[0], baseG.guideJoints[0])
initializer.test_build(baseG.guideJoints[0])

# vis
cmds.setAttr("pref_cont.Rig_Visibility", 1)

