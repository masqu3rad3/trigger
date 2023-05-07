# import maya.standalone

import maya.cmds as cmds
import base_test
import logging

# from trigger.modules import base
# from trigger.base import initials
from standalone_start import standalone_prep

LOG = logging.getLogger(__name__)

class ModuleTests(base_test.TestCase):

    # def __init__(self, *args):
        # super(ModuleTests, self).__init__()

    @classmethod
    def setUpClass(cls):
        standalone_prep()
        from trigger.modules import base
        from trigger.base import initials
        cls.initializer = initials.Initials()
        cls.base_guides = base.Guides()


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

        from trigger.modules import hindleg
        # initializer = initials.Initials()
        # base_guides = base.Guides()
        self.base_guides.createGuides()
        guider = hindleg.Guides(side="L")
        guider.createGuides()
        cmds.setAttr("%s.localJoints" % guider.guideJoints[0], True)
        cmds.setAttr("%s.stretchyIK" % guider.guideJoints[0], True)
        cmds.setAttr("%s.ribbon" % guider.guideJoints[0], True)
        cmds.parent(guider.guideJoints[0], self.base_guides.guideJoints[0])
        self.initializer.test_build(self.base_guides.guideJoints[0])
        cmds.setAttr("pref_cont.Rig_Visibility", 1)
        print(cmds.about(version=True))

    def test_arm(self):
        LOG.debug("------------------")
        LOG.debug("test_arm")
        LOG.debug("------------------")
        self.reset_scene()

        from trigger.modules import arm
        kinematics = self.basic_creation_test(arm)
        print(kinematics)


    def basic_creation_test(self, module):
        """Create the module with default guide joints."""
        _guider = module.Guides()
        _guider.createGuides()
        return self.initializer.test_build(_guider.guideJoints[0])


    @staticmethod
    def reset_scene():
        """Reset the scene to a blank Maya scene."""
        cmds.file(newFile=True, force=True)
