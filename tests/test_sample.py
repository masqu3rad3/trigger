
import maya.cmds as cmds
import base_test
from standalone_start import standalone_prep

class SampleTests(base_test.TestCase):

    @classmethod
    def setUpClass(cls):
        standalone_prep()


    def test_export_blendshape(self):
        self.reset_scene()

        base = cmds.polySphere(radius=5)[0]
        target = cmds.polySphere(radius=10)[0]
        blendshape = cmds.blendShape(target, base)[0]
        # file_path = self.get_temp_filename('blendshape.shapes')
        # cmds.myCustomBlendShapeExporter(blendshape, path=file_path)
        print(blendshape)
        print(blendshape)
        print(blendshape)
        print(blendshape)
        self.assertTrue(cmds.objExists(blendshape))

    @staticmethod
    def reset_scene():
        """Reset the scene to a blank Maya scene."""
        cmds.file(newFile=True, force=True)