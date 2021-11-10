from maya import cmds

cmds.file(new=True, f=True)

from trigger.modules import spine
reload(spine)

from trigger.library import ribbon
reload(ribbon)

from trigger.library import controllers
reload(controllers)

from trigger.library import objects
reload(objects)

from trigger.library import tools
reload(tools)

from trigger.library import functions
reload(functions)

from trigger import modules
reload(modules)

from trigger.modules import hindleg
reload(hindleg)

from trigger.modules import base

from trigger.base import initials
reload(initials)

initializer = initials.Initials()
baseG = base.Guides()
baseG.createGuides()
guider = hindleg.Guides(side="L")
guider.createGuides()
cmds.setAttr("%s.localJoints" %guider.guideJoints[0], True)
cmds.setAttr("%s.stretchyIK" %guider.guideJoints[0], True)
cmds.setAttr("%s.ribbon" %guider.guideJoints[0], True)
cmds.parent(guider.guideJoints[0], baseG.guideJoints[0])

initializer.test_build(baseG.guideJoints[0])


cmds.setAttr("pref_cont.Rig_Visibility", 1)

