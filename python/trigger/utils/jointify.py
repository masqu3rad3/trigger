"""Module for converting blendshape deformations joint based deformations"""
import subprocess
import os

from maya import cmds

from trigger.library import deformers, attribute
from trigger.library import connection

class Jointify(object):
    def __init__(self, blendshape_node=None, *args, **kwargs):
        super(Jointify, self).__init__()

        # class variables
        self.blendshapeNode = blendshape_node
        self.originalData = {}
        self.trainingData = {}

    def start(self, blendshape_node=None):
        """Main function"""
        self.blendshapeNode = self.blendshapeNode or blendshape_node
        if not self.blendshapeNode:
            raise Exception("Blendshape node is not defined")

        self.collect_original_data()
        self.prepare_training_set()
        self.create_dem_bones()
        self.jointify()

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
                    # get the base attributes forming the combination
                    plugs = cmds.listConnections(incoming, plugs=True, source=True, destination=False)
                    self.originalData[shape]["combinations"] = [x.split(".")[1] for x in plugs]
                else:
                    self.originalData[shape]["type"] = "base"
                    self.originalData[shape]["combinations"] = []
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
        self.trainingData["animationRange"] = [0, (len(self.originalData.items())*shape_duration)]

        for nmb, (attr, data) in enumerate(self.originalData.items()):
            # print("nmb", nmb)
            # print("attr", attr)
            # print("data", data)


            # disconnect inputs
            if data["connected"]:
                cmds.disconnectAttr(data["in"], data["out"])
            start_frame = (shape_duration * (nmb+1)) - shape_duration
            end_frame = start_frame + (shape_duration-1)
            cmds.setKeyframe(self.blendshapeNode, at=attr, t=start_frame - 1, value=0)
            cmds.setKeyframe(self.blendshapeNode, at=attr, t=start_frame, value=0)
            cmds.setKeyframe(self.blendshapeNode, at=attr, t=end_frame, value=1)
            cmds.setKeyframe(self.blendshapeNode, at=attr, t=end_frame + 1, value=0)
            data["timeGap"] = [start_frame, end_frame]

        # # update the training data
        # self.trainingData["startFrame"] = shape_duration
        # self.trainingData["endFrame"] = (shape_duration * (len(self.originalData.items())+1)) + (shape_duration-1)
        # self.trainingData["shapeDuration"] = shape_duration

    def create_dem_bones(self):
        """Exports the training set to DEM bones. does the training and get back the FBX"""

        # temporary file paths for alembic and FBX files
        abc_source = os.path.normpath(os.path.join(os.path.expanduser("~"), "jointify_source_abc.abc"))
        fbx_source = os.path.normpath(os.path.join(os.path.expanduser("~"), "jointify_source_fbx.fbx"))
        fbx_output = os.path.normpath(os.path.join(os.path.expanduser("~"), "jointify_output_fbx.fbx"))

        # export Alembic animation
            ## requires whole animation start and end frames

        # export static FBX
            ## requires original geo
        # duplicate a clean one

        # do the DEM magic
            ## requires joint count

        # import back the output fbx

        # return imported joints and mesh

        pass

    def jointify(self):
        """Creates a joint version of the blendshape deformations using the dem bones data as guidance"""
        # create a hook node to replace the blendshape deformer
        jointify_hook = cmds.group(em=True, name="jointify_hook")

        # TODO prepare the incoming database according to the requirements:
        # All imported animated joints
        # imported mesh which is skinclustered to the animated joints
        # Names of all shapes
        # Time Gaps for all shapes
        # combinationShape info for all shapes


        # requires imported animated joints and mesh

        # for each shape:
            ## requires TIME GAP for that shape
            # find the active joints in the time gap

            # for each active joint:
                # create an upper group, apply the same time gap animation to the group

                # create the corresponding attribute on the jointify hook
                # drive the group animation with that attribute


        # do a separate loop for connecting combination shapes and end-hook connections:
        # for each shape:
            # if the shape IS a combination shape:
                # create a combination node to drive that attribute with related base attributes
                ## requires all combination shapes
            # else (NOT a combination shape)
                # if original shape is driven with some other attr, drive this with the same one

        pass



