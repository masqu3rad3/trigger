"""Module for converting blendshape deformations joint based deformations"""
import subprocess

from maya import cmds

from trigger.library import deformers, attribute
from trigger.library import connection

class Jointify(object):
    def __init__(self, blendshape_node=None, *args, **kwargs):
        super(Jointify, self).__init__()

        # class variables
        self.blendshapeNode = blendshape_node
        self.originalData = {}

    def start(self, blendshape_node=None):
        """Main function"""
        self.blendshapeNode = self.blendshapeNode or blendshape_node
        if not self.blendshapeNode:
            raise Exception("Blendshape node is not defined")

        self.collect_original_data()
        self.prepare_training_set()

    def collect_original_data(self):
        """Collects all target and hook plug data

        Sample:
        {
        'blink': {
                'connected': True,
                'in': 'morph_hook.blink',
                'out': 'trigger_morph_blendshape.blink',
                'type': 'base'},
        'browLowerer': {
                'connected': True,
                'in': 'morph_hook.browLowerer',
                'out': 'trigger_morph_blendshape.browLowerer',
                'type': 'base'}
        }

        """
        self.originalData.clear()
        targetshapes = deformers.get_influencers(self.blendshapeNode)
        for shape in targetshapes:
            self.originalData[shape] = {}
            incoming = cmds.listConnections("{0}.{1}".format(self.blendshapeNode, shape), s=True, d=False)
            if incoming:
                cnx = connection.connections("{0}.{1}".format(self.blendshapeNode, shape), return_mode="incoming")[0]
                self.originalData[shape]["connected"] = True
                if cmds.objectType(incoming) == "combinationShape":
                    self.originalData[shape]["type"] = "combination"
                else:
                    self.originalData[shape]["type"] = "base"
                self.originalData[shape]["in"] = cnx["plug_in"]
                self.originalData[shape]["out"] = cnx["plug_out"]

            else:
                self.originalData[shape]["connected"] = False
                self.originalData[shape]["type"] = "base"
                self.originalData[shape]["in"] = ""
                self.originalData[shape]["out"] = ""
        return self.originalData

    def prepare_training_set(self):
        """Creates a ROM from blendshape targets"""

        shape_duration = 10

        for nmb, (attr, data) in enumerate(self.originalData.items()):
            print("nmb", nmb)
            print("attr", attr)
            print("data", data)


            # disconnect inputs
            if data["connected"]:
                cmds.disconnectAttr(data["in"], data["out"])
            start_frame = shape_duration * (nmb+1)
            end_frame = start_frame + (shape_duration-1)
            cmds.setKeyframe(self.blendshapeNode, at=attr, t=start_frame - 1, value=0)
            cmds.setKeyframe(self.blendshapeNode, at=attr, t=start_frame, value=0)
            cmds.setKeyframe(self.blendshapeNode, at=attr, t=end_frame, value=1)
            cmds.setKeyframe(self.blendshapeNode, at=attr, t=end_frame + 1, value=0)

    def create_dem_bones(self):
        """Exports the training set to DEM bones. does the training and get back the FBX"""
        pass

    def jointify(self):
        """Creates a joint version of the blendshape deformations using the dem bones data as guidance"""
        pass



