# import maya.standalone

import maya.cmds as cmds
import base_test
import logging

# from trigger.modules import base
# from trigger.base import initials
from standalone_start import standalone_prep

LOG = logging.getLogger(__name__)

class ModuleTests(base_test.TestCase):

    @classmethod
    def setUpClass(cls):
        standalone_prep()
    # @classmethod
    # def setUpClass(cls):
    #     import maya.standalone
    #     maya.standalone.initialize()
    #     pass
    #     cls.load_plugin('myBlendShapeExportingPlugin')

    # @classmethod
    # def tearDownClass(cls):
    #     super(ModuleTests, cls).tearDownClass()
    #     maya.standalone.uninitialize()

    def test_hindleg(self):
        LOG.info("------------------")
        LOG.info("test_hindleg")
        LOG.info("------------------")
        self.reset_scene()

        from trigger.modules import base
        from trigger.base import initials
        from trigger.modules import hindleg
        initializer = initials.Initials()
        base_guides = base.Guides()
        base_guides.createGuides()
        guider = hindleg.Guides(side="L")
        guider.createGuides()
        cmds.setAttr("%s.localJoints" % guider.guideJoints[0], True)
        cmds.setAttr("%s.stretchyIK" % guider.guideJoints[0], True)
        cmds.setAttr("%s.ribbon" % guider.guideJoints[0], True)
        cmds.parent(guider.guideJoints[0], base_guides.guideJoints[0])
        initializer.test_build(base_guides.guideJoints[0])
        cmds.setAttr("pref_cont.Rig_Visibility", 1)
        print(cmds.about(version=True))

    @staticmethod
    def reset_scene():
        """Reset the scene to a blank Maya scene."""
        cmds.file(newFile=True, force=True)
