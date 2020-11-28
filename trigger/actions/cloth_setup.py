"""Prepares Cloth Sim Setup"""

import os
from maya import cmds
from maya import mel
from trigger.core import logger
from trigger.library import selection
from trigger.library import connection
import trigger.library.functions as functions
import trigger.library.controllers as ic

from trigger.ui.Qt import QtWidgets, QtGui # for progressbar
from trigger.ui import feedback

LOG = logger.Logger(logger_name=__name__)

ACTION_DATA = {
    "cloth_objects": [],
    "collider_objects": [],
    "motion_multiplier_vertices": [],
}

class Cloth_setup(object):
    def __init__(self, *args, **kwargs):
        super(Cloth_setup, self).__init__()
        self.clothObjects = []
        self.colliderObjects = []
        self.motionMultiplierVertices = []

    def feed(self, action_data):
        """Feeds the instance with the action data stored in actions session"""
        self.clothObjects = action_data.get("cloth_objects")
        self.colliderObjects = action_data.get("collider_objects")
        self.motionMultiplierVertices = action_data.get("motion_multiplier_vertices")

    def action(self):
        """Execute Action"""

        self.setupHierarchy()
        self.createClothGroup()
        self.createCloth(self.clothObjects)
        self.createStartFrameLoc()
        self.createWindControl()

        ## makeMotionMult

        ## createCollider Loop

        pass

    def save_action(self):
        pass

    def ui(self, ctrl, layout, *args, **kwargs):
        feedback_handler = feedback.Feedback()
        cloth_objects_lbl = QtWidgets.QLabel(text="Cloth Objects:")
        cloth_objects_hlay = QtWidgets.QHBoxLayout()
        cloth_objects_le = QtWidgets.QLineEdit()
        cloth_objects_hlay.addWidget(cloth_objects_le)
        get_cloth_objects_pb = QtWidgets.QPushButton(text="Set")
        cloth_objects_hlay.addWidget(get_cloth_objects_pb)
        layout.addRow(cloth_objects_lbl, cloth_objects_hlay)

        collider_objects_lbl = QtWidgets.QLabel(text="Collider Objects:")
        collider_objects_hlay = QtWidgets.QHBoxLayout()
        collider_objects_le = QtWidgets.QLineEdit()
        collider_objects_hlay.addWidget(collider_objects_le)
        get_collider_objects_pb = QtWidgets.QPushButton(text="Set")
        collider_objects_hlay.addWidget(get_collider_objects_pb)
        layout.addRow(collider_objects_lbl, collider_objects_hlay)

        mm_vertices_lbl = QtWidgets.QLabel(text="Motion Multiplier Vertices:")
        mm_vertices_hlay = QtWidgets.QHBoxLayout()
        mm_vertices_le = QtWidgets.QLineEdit()
        mm_vertices_hlay.addWidget(mm_vertices_le)
        get_vertices_pb = QtWidgets.QPushButton(text="Set")
        mm_vertices_hlay.addWidget(get_vertices_pb)
        layout.addRow(mm_vertices_lbl, mm_vertices_hlay)

        # make connections with the controller object
        ctrl.connect(cloth_objects_le, "cloth_objects", list)
        ctrl.connect(collider_objects_le, "collider_objects", list)
        ctrl.connect(mm_vertices_le, "motion_multiplier_vertices", list)

        ctrl.update_ui()

        def get_cloth_objects():
            selection = cmds.ls(sl=True, o=True)
            if not selection:
                return
            for obj in selection:
                if obj in cloth_objects_le.text():
                    selection.remove(obj)
                if obj in collider_objects_le.text():
                    feedback_handler.pop_info(title="Conflict", text="%s defined as collider. Objects cannot be defined both cloth and passive collider, Skipping" %obj)
                    continue
            cloth_objects_le.setText(ctrl.list_to_text(selection))
            ctrl.update_model()

        def get_collider_objects():
            selection = cmds.ls(sl=True, o=True)
            if not selection:
                return
            for obj in selection:
                if obj in collider_objects_le.text():
                    selection.remove(obj)
                if obj in cloth_objects_le.text():
                    feedback_handler.pop_info(title="Conflict", text="%s defined as cloth. Objects cannot be defined both cloth and passive collider, Skipping" %obj)
                    continue
            collider_objects_le.setText(ctrl.list_to_text(selection))
            ctrl.update_model()

        def get_mm_vertices():
            if selection.get_selection_type() != "vertex":
                feedback_handler.pop_info(title="Wrong selection", text="N number of vertices from a single mesh must me selected")
                return
            ids = [(val.split('.vtx[', 1)[1].split(']')[0]) for val in cmds.ls(sl=True)]
            mm_vertices_le.setText(ctrl.list_to_text(ids))
            ctrl.update_model()

        ### Signals
        get_cloth_objects_pb.clicked.connect(get_cloth_objects)
        get_collider_objects_pb.clicked.connect(get_collider_objects)
        get_vertices_pb.clicked.connect(get_mm_vertices)

    @staticmethod
    def setupHierarchy():
        # Creates the basic Hierarchy and tags to the groups
        name = "simRig"
        simRigName = "%s_grp" %name
        cmds.group(n=simRigName, em=True)

        for i in ["driver", "skeleton", "controls", "cloth", "motionMultiplier", "output"]:
            grpCreate = cmds.group(n='%s_grp' % i, em=True, p=simRigName)
            cmds.addAttr(ln='simRig_%s' % i, at='bool', dv=True)

        for i in ["colliders", "constraints", "forces"]:
            grpCreate = cmds.group(n='%s_grp' % i, em=True, p='cloth_grp')
            cmds.addAttr(ln='simRig_%s' % i, at='bool', dv=True)

        for i in ["world", "local"]:
            grpCreate = cmds.group(n='%s_grp' % i, em=True, p='output_grp')
            cmds.addAttr(ln='simRig_%s' % i, at='bool', dv=True)

            outLYR = cmds.createDisplayLayer(n="Output_LYR", e=True)
            clthLYR = cmds.createDisplayLayer(n="Cloth_LYR", e=True)
            drvLYR = cmds.createDisplayLayer(n="Driver_LYR", e=True)

            cmds.setAttr('Driver_LYR.color', 29)
            cmds.setAttr('Cloth_LYR.color', 31)
            cmds.setAttr('Driver_LYR.color', 17)
            cmds.editDisplayLayerMembers('Driver_LYR', 'driver_grp')
            cmds.editDisplayLayerMembers('Cloth_LYR', 'cloth_grp')
            cmds.editDisplayLayerMembers('Output_LYR', 'output_grp')

            nucName = '%sNucleus' % name
            cmds.createNode('nucleus', n=nucName)
            cmds.setAttr('*Nucleus.subSteps', 12)
            cmds.setAttr('*Nucleus.maxCollisionIterations', 16)
            cmds.setAttr('*Nucleus.spaceScale', 0.01)
            cmds.parent(nucName, 'controls_grp')
            cmds.connectAttr('*time1.outTime', '*Nucleus.currentTime')
            return nucName

    @staticmethod
    def createClothGroup():
        # Creates Cloth Group Hierarchy based on an input name
        groupName = "cloth_grp"
        if not cmds.objExists(groupName):
            cmds.group(n=groupName, em=True)
        # if cmds.objExists('cloth_grp') == True:
        #     cmds.group(n=groupName, em=True, p='cloth_grp')
        # else:
        #     cmds.group(n=groupName, em=True)

        for i in ["wrapBase", "constraints", "colliders", "forces"]:
            grpCreate = cmds.group(n='%s_grp' % i, em=True, p=groupName)
            cmds.addAttr(ln='simRig_%s' % i, at='bool', dv=True)

    @staticmethod
    def createCloth(objs, groupName="cloth_grp"):
        # Creates the connections for nCloth setup including INNIT CLOTH and REST Meshes. Parents to the cloth group.
        print("DEBUGaaaaa", objs)
        for cloth in objs:
            print("DEBUG----", cloth)
            createInIt = cmds.duplicate(cloth, n=cloth + '_INIT')
            createCloth = cmds.duplicate(cloth, n=cloth + '_CLOTH')
            createRest = cmds.duplicate(cloth, n=cloth + '_REST')

            cmds.parent(createInIt, groupName)
            cmds.parent(createCloth, groupName)
            cmds.parent(createRest, groupName)
            cmds.hide(createInIt)
            cmds.hide(createRest)

            cmds.blendShape(createInIt, createCloth, n="%s_InitBlend" % cloth, w=(0, 1))

            cmds.select(createCloth, r=True)
            mel.eval('createNCloth 0')
            cmds.parent('nCloth*', groupName)

    @staticmethod
    def createStartFrameLoc(nucleusName=None):
        """Creates a start frame locator that gives the start frame to the nucleus automatically."""
        if not nucleusName:
            # get the first nucleus in the scene
            nucleuses = cmds.ls(type="nucleus")
            assert nucleuses, "There are no Nucleuses in the scene"
            nucleusName = nucleuses[0]

        startLoc = cmds.spaceLocator(n='StartFrameLoc')[0]
        cmds.addAttr(ln="StartFrame", at='float', dv=0)
        cmds.setAttr('%s.StartFrame' % startLoc, cb=True)

        cmds.setAttr("%s.tx" % startLoc, k=False, cb=False)
        cmds.setAttr("%s.ty" % startLoc, k=False, cb=False)
        cmds.setAttr("%s.tz" % startLoc, k=False, cb=False)

        cmds.setAttr("%s.rx" % startLoc, k=False, cb=False)
        cmds.setAttr("%s.ry" % startLoc, k=False, cb=False)
        cmds.setAttr("%s.rz" % startLoc, k=False, cb=False)

        cmds.setAttr("%s.sx" % startLoc, k=False, cb=False)
        cmds.setAttr("%s.sy" % startLoc, k=False, cb=False)
        cmds.setAttr("%s.sz" % startLoc, k=False, cb=False)
        cmds.setAttr("%s.v" % startLoc, 0, k=False, cb=False)

        cmds.expression(s="StartFrameLoc.StartFrame = `playbackOptions -q -min`", o='StartFrameLoc', ae=1, uc=all)
        cmds.select(cl=True)

        if cmds.objExists('cloth_grp') == True:
            cmds.parent(startLoc, 'cloth_grp')

        cmds.connectAttr('StartFrameLoc.StartFrame', '%s.startFrame' % nucleusName)

    @staticmethod
    def createWindControl(nucleusName=None):
        """Create wind controller"""
        if not nucleusName:
            # get the first nucleus in the scene
            nucleuses = cmds.ls(type="nucleus")
            assert nucleuses, "There are no Nucleuses in the scene"
            nucleusName = nucleuses[0]
        _list = []
        _list.append(cmds.curve(
            p=[(-1.0, 0.0, 0.0), (-1.0, 0.0, 2.0), (1.0, 0.0, 2.0), (1.0, 0.0, 0.0), (2.0, 0.0, 0.0), (0.0, 0.0, -2.0),
               (-2.0, 0.0, 0.0), (-1.0, 0.0, 0.0)], per=False, d=1, k=[0, 1, 2, 3, 4, 5, 6, 7]))
        for x in range(len(_list) - 1):
            cmds.makeIdentity(_list[x + 1], apply=True, t=1, r=1, s=1, n=0)
            shapeNode = cmds.listRelatives(_list[x + 1], shapes=True)
            cmds.parent(shapeNode, _list[0], add=True, s=True)
            cmds.delete(_list[x + 1])
        cmds.select(_list[0])
        cmds.rename(_list[0], 'pvWindArrow')
        cmds.rotate(0, -90, 0)
        cmds.makeIdentity(apply=True, t=True, r=True, n=True)
        getShape = cmds.listRelatives(s=True, pa=True)[0]
        cmds.rename(getShape, 'pvWindArrowShape')
        cmds.spaceLocator(n='pvWindOrigin')
        cmds.setAttr('pvWindOrigin.visibility', 0)
        cmds.spaceLocator(n='pvWindAim')
        cmds.setAttr('pvWindAim.visibility', 0)
        cmds.group('pvWindAim', n='pvWindAim_Null')
        cmds.setAttr('pvWindAim.translateX', 1)
        cmds.aimConstraint('pvWindAim', 'pvWindOrigin')
        windCntrl = cmds.group('pvWindArrow', n='windCTRL')
        cmds.parentConstraint('windCTRL', 'pvWindAim_Null')
        cmds.select('pvWindArrowShape', 'windCTRL')
        cmds.parent(r=True, s=True)
        cmds.delete('pvWindArrow')
        cmds.pointConstraint('windCTRL', 'pvWindOrigin')
        cmds.pickWalk(direction="up")

        cmds.addAttr(ln='windSpeed', nn='Wind Speed', at='float', dv=0)
        cmds.addAttr(ln='windNoise', nn='Wind Noise', at='float', dv=0)

        cmds.connectAttr('windCTRL.windSpeed', '%s.windSpeed' % nucleusName)
        cmds.connectAttr('windCTRL.windNoise', '%s.windNoise' % nucleusName)

        cmds.setAttr('windCTRL.windSpeed', k=True)
        cmds.setAttr('windCTRL.windNoise', k=True)

        cmds.setAttr('pvWindArrowShape.overrideEnabled', 1)
        cmds.setAttr('pvWindArrowShape.overrideColor', 18)

        cmds.group('pvWindOrigin', 'pvWindAim_Null', windCntrl, n='globalWind_grp', p='controls_grp')

        cmds.setAttr('globalWind_grp.translateX', k=False, l=True)
        cmds.setAttr('globalWind_grp.translateY', k=False, l=True)
        cmds.setAttr('globalWind_grp.translateZ', k=False, l=True)

        cmds.setAttr('globalWind_grp.rotateX', k=False, l=True)
        cmds.setAttr('globalWind_grp.rotateY', k=False, l=True)
        cmds.setAttr('globalWind_grp.rotateZ', k=False, l=True)

        cmds.setAttr('globalWind_grp.scaleX', k=False, l=True)
        cmds.setAttr('globalWind_grp.scaleY', k=False, l=True)
        cmds.setAttr('globalWind_grp.scaleZ', k=False, l=True)

        cmds.setAttr('globalWind_grp.visibility', k=False, l=True)

        cmds.connectAttr('pvWindOrigin_aimConstraint1.constraintVectorX', '%s.windDirectionX' % nucleusName)
        cmds.connectAttr('pvWindOrigin_aimConstraint1.constraintVectorY', '%s.windDirectionY' % nucleusName)
        cmds.connectAttr('pvWindOrigin_aimConstraint1.constraintVectorZ', '%s.windDirectionZ' % nucleusName)

        cmds.select(cl=True)
        return windCntrl

    @staticmethod
    def makeMotionMult(average_vertex_list):
        """Creates a motion multiplier to reduce or increase input motion for cloth simulation"""
        grpNames = ['driver_grp', 'output_grp']
        # pelvises = cmds.ls("*:bn_pelvis")
        # assert len(pelvises) == 1, "There are no or multiple pelvis joints"
        # moBase = pelvises[0]
        moBase = cmds.ls(sl=True)

        for grp in grpNames:
            cmds.select(grp, hi=True)
            cmds.select(grp, d=True)
            grpSel = cmds.ls(sl=True, fl=True)
            if grp == 'Driver_grp':
                localCl = cmds.cluster(n='localCluster')
            else:
                worldCl = cmds.cluster(n='worldCluster')
            localMult = cmds.shadingNode('multiplyDivide', asUtility=True, n='LocalMultiplyDivide')
            invertNode = cmds.shadingNode('reverse', asUtility=True, n='InvertInput')
            worldMult = cmds.shadingNode('localCluster', asUtility=True)
            decompMat = cmds.shadingNode('decomposeMatrix', asUtility=True)

            cmds.connectAttr(str(moBase) + 'Shape.worldMatrix[0]', str(decompMat) + '.inputMatrix', f=True)
            cmds.connectAttr(str(localMult) + '.input2', str(invertNode) + '.input', f=True)
            cmds.connectAttr(str(invertNode) + '.output', str(worldMult) + 'input2', f=True)
            cmds.connectAttr(str(decompMat) + '.outputTranslate', str(localMult) + '.input1', f=True)
            cmds.connectAttr(str(decompMat) + '.outputTranslate', str(worldMult) + '.input1', f=True)
            cmds.connectAttr(str(localMult) + 'output', str(localCl[1]) + '.translate', f=True)
            cmds.connectAttr(str(localMult) + 'output', str(worldCl[1]) + '.translate', f=True)

            nucleus = cmds.ls(type='nucleus')
            cmds.addAttr(nucleus, ln='MontionMultiplier', at="enum", en="----------:")
            cmds.setAttr(str(nucleus[0]) + 'MotionMultiplier', k=False, cb=True, l=True)

            cmds.addAttr(nucleus, ln="X", at='double', dv=0)
            cmds.setAttr(str(nucleus[0]) + 'X', k=True)

            cmds.addAttr(nucleus, ln="Y", at='double', dv=0)
            cmds.setAttr(str(nucleus[0]) + 'Y', k=True)

            cmds.addAttr(nucleus, ln="Z", at='double', dv=0)
            cmds.setAttr(str(nucleus[0]) + 'Z', k=True)

            cmds.connectAttr(str(nucleus[0]) + '.X', str(localMult) + '.input2.input2X', f=True)
            cmds.connectAttr(str(nucleus[0]) + '.Y', str(localMult) + '.input2.input2Y', f=True)
            cmds.connectAttr(str(nucleus[0]) + '.Z', str(localMult) + '.input2.input2Z', f=True)

            cmds.parent(localCl, worldCl, 'MotionMultiplier')
