import sys

import maya.cmds as cmds
import base_test
from trigger.core import filelog

from standalone_start import standalone_prep


LOG = filelog.Filelog(logname=__name__, filename="trigger_log")

# LOG.title("Module Tests")

class ModuleTests(base_test.TestCase):
    # LOG.title("Module Tests")
    @classmethod
    def setUpClass(cls):
        standalone_prep()
        from trigger.modules import base
        from trigger.base import session
        from trigger.base import initials
        cls.initializer = initials.Initials()
        cls.guides_handler = session.Session()
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

    def test_arm(self):
        # LOG.info("test_arm")

        kinematics = self.basic_creation_test("arm")
        # self.assertTrue(kinematics)

        # Socket / Plug connections
        kinematics2 = self.basic_creation_test(["surface", "arm", "tentacle"])
        # kinematics2 = self.basic_creation_test(["arm", "tentacle"])
        # kinematics2 = self.basic_creation_test(["base", "arm", "fkik"])
        # kinematics2 = self.basic_creation_test(["base", "arm", "fkik"])
        self.assertTrue(kinematics2)

    def test_base(self):
        # LOG.info("test_base")

        kinematics = self.basic_creation_test("base")
        self.assertTrue(kinematics)

        # Socket / Plug connections
        kinematics2 = self.basic_creation_test([ "arm", "base", "fkik"])
        self.assertTrue(kinematics2)

    def test_connector(self):
        # LOG.info("connector")

        kinematics = self.basic_creation_test("connector")
        self.assertTrue(kinematics)

        # Socket / Plug connections
        kinematics2 = self.basic_creation_test(["base", "connector", "arm"])
        self.assertTrue(kinematics2)

    def test_eye(self):
        # LOG.info("eye")

        kinematics = self.basic_creation_test("eye")
        self.assertTrue(kinematics)

        # Socket / Plug connections
        kinematics2 = self.basic_creation_test(["connector", "eye", "base"])
        # kinematics2 = self.basic_creation_test(["eye", "base", "eye"])
        self.assertTrue(kinematics2)

    def test_finger(self):
        # LOG.info("finger")

        kinematics = self.basic_creation_test("finger")
        self.assertTrue(kinematics)

        # Socket / Plug connections
        kinematics2 = self.basic_creation_test(["arm", "finger", "fkik"])
        self.assertTrue(kinematics2)

    def test_fkik(self):
        # LOG.info("fkik")

        kinematics = self.basic_creation_test("fkik")
        self.assertTrue(kinematics)

        # Socket / Plug connections
        # kinematics2 = self.basic_creation_test(["finger", "fkik", "singleton"])
        kinematics2 = self.basic_creation_test(["arm", "fkik", "finger"])
        self.assertTrue(kinematics2)

    def test_head(self):
        # LOG.info("head")

        kinematics = self.basic_creation_test("head")
        self.assertTrue(kinematics)

        # Socket / Plug connections
        kinematics2 = self.basic_creation_test(["base", "head", "finger"])
        self.assertTrue(kinematics2)

    def test_hindleg(self):
        # LOG.info("test_hindleg")

        kinematics = self.basic_creation_test("hindleg")
        self.assertTrue(kinematics)

        # Socket / Plug connections
        kinematics2 = self.basic_creation_test(["tentacle", "hindleg", "arm"])
        self.assertTrue(kinematics2)

    def test_leg(self):
        # LOG.info("test_leg")

        kinematics = self.basic_creation_test("leg")
        self.assertTrue(kinematics)

        # Socket / Plug connections
        kinematics2 = self.basic_creation_test(["base", "leg", "fkik"])
        self.assertTrue(kinematics2)


    def test_singleton(self):
        # LOG.info("test_singleton")

        kinematics = self.basic_creation_test("singleton")
        self.assertTrue(kinematics)

        # Socket / Plug connections
        kinematics2 = self.basic_creation_test(["base", "singleton", "fkik"])
        self.assertTrue(kinematics2)

    def test_spine(self):
        # LOG.info("test_spine")

        kinematics = self.basic_creation_test("spine")
        self.assertTrue(kinematics)

        # Socket / Plug connections
        kinematics2 = self.basic_creation_test(["base", "spine", "leg"])
        self.assertTrue(kinematics2)

    def test_surface(self):
        # LOG.info("test_surface")

        kinematics = self.basic_creation_test("surface")
        self.assertTrue(kinematics)

        # Socket / Plug connections
        kinematics2 = self.basic_creation_test(["base", "surface", "connector"])
        self.assertTrue(kinematics2)

    def test_tail(self):
        # LOG.info("test_tail")

        kinematics = self.basic_creation_test("tail")
        self.assertTrue(kinematics)

        # Socket / Plug connections
        kinematics2 = self.basic_creation_test(["base", "tail", "leg"])
        self.assertTrue(kinematics2)

    def test_tentacle(self):
        # LOG.info("test_tentacle")

        # single tentacle
        kinematics = self.basic_creation_test("tentacle")
        self.assertTrue(kinematics)

        # Socket / Plug connections
        kinematics2 = self.basic_creation_test(["base", "tentacle", "finger"])
        self.assertTrue(kinematics2)

    def test_humanoid(self):
        # LOG.info("test_humanoid")
        # self.reset_scene()
        self.guides_handler.reset_scene()
        self.guides_handler.init.initHumanoid()
        self.guides_handler.init.test_build("C_base_root_jInit")
        # self.assertTrue(kinematics)

    def basic_creation_test(self, module_names):
        """Create the module with default guide joints."""
        # _guider = module.Guides()
        # _guider.createGuides()
        self.guides_handler.reset_scene()
        if isinstance(module_names, str):
            module_names = [module_names]
        root_guides = []
        previous_end_guide = None
        for module_name in module_names:
            cmds.select(clear=True)
            locators, side_dict = self.guides_handler.init.initLimb(module_name, whichSide="left", defineAs=False)
            first_guide = list(side_dict.values())[0][0]
            root_guides.append(first_guide)

            if previous_end_guide:
                cmds.parent(first_guide, previous_end_guide)
                cmds.setAttr("{}.translate".format(first_guide), 0, 0, 0)
            previous_end_guide = list(side_dict.values())[0][-1]
        return self.guides_handler.init.test_build(root_guides[0])
