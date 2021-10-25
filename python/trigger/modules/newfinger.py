from maya import cmds
import maya.api.OpenMaya as om
from trigger.library import functions
from trigger.library import naming
from trigger.library import attribute
from trigger.library import controllers as ic

from trigger.core import filelog
log = filelog.Filelog(logname=__name__, filename="trigger_log")


LIMB_DATA = {"members": ["FingerRoot", "Finger"],
             "properties": [{"attr_name": "fingerType",
                             "nice_name": "Finger_Type",
                             "attr_type": "enum",
                             "enum_list": "Extra:Thumb:Index:Middle:Ring:Pinky:Toe",
                             "default_value": 0,
                             },
                            {
                                "attr_name": "groupID",
                                "nice_name": "Group_ID",
                                "attr_type": "long",
                                "min_value": 0,
                                "max_value": 9999,
                                "default_value": 1
                            },
                            ],
             "multi_guide": "Finger",
             "sided": True,
             }

class Newfinger():
    def __init__(self, build_data=None, inits=None, *args, **kwargs):
        super(Newfinger, self).__init__()
        # fool proofing

        # reinitialize the initial Joints
        if build_data:
            self.fingerRoot = build_data.get("FingerRoot")
            self.fingers = (build_data.get("Finger"))
            self.inits = [self.fingerRoot] + (self.fingers)
        elif inits:
            # fool proofing
            if (len(inits) < 2):
                log.error("Insufficient Finger Initialization Joints")
                return
            self.inits = inits
        else:
            log.error("Class needs either build_data or inits to be constructed")

        # get distances

        # get positions

        # get the properties from the root
        self.useRefOrientation = cmds.getAttr("%s.useRefOri" % self.inits[0])
        self.fingerType = cmds.getAttr("%s.fingerType" % self.fingerRoot, asString=True)
        self.isThumb = self.fingerType == "Thumb"
        self.side = functions.get_joint_side(self.inits[0])
        self.sideMult = -1 if self.side == "R" else 1
        self.groupID = int(cmds.getAttr("%s.groupID" % self.inits[0]))

        # initialize coordinates
        self.up_axis, self.mirror_axis, self.look_axis = functions.getRigAxes(self.inits[0])

        # initialize suffix
        self.suffix = (naming.uniqueName(cmds.getAttr("%s.moduleName" % self.inits[0])))

        # BASE variables
        self.controllers = []
        self.sockets = []
        self.limbGrp = None
        self.scaleGrp = None
        self.nonScaleGrp = None
        self.limbPlug = None
        self.scaleConstraints = []
        self.anchors = []
        self.anchorLocations = []
        self.deformerJoints = []
        self.colorCodes = [6, 18]

    def createGrp(self):
        self.limbGrp = cmds.group(name=self.suffix, em=True)
        self.scaleGrp = cmds.group(name="%s_scaleGrp" % self.suffix, em=True)
        functions.alignTo(self.scaleGrp, self.inits[0], 0)
        self.nonScaleGrp = cmds.group(name="%s_nonScaleGrp" % self.suffix, em=True)

        cmds.addAttr(self.scaleGrp, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True)
        cmds.addAttr(self.scaleGrp, at="bool", ln="Joints_Visibility", sn="jointVis", defaultValue=True)
        cmds.addAttr(self.scaleGrp, at="bool", ln="Rig_Visibility", sn="rigVis", defaultValue=False)
        # make the created attributes visible in the channelbox
        cmds.setAttr("%s.contVis" % self.scaleGrp, cb=True)
        cmds.setAttr("%s.jointVis" % self.scaleGrp, cb=True)
        cmds.setAttr("%s.rigVis" % self.scaleGrp, cb=True)

        cmds.parent(self.scaleGrp, self.limbGrp)
        cmds.parent(self.nonScaleGrp, self.limbGrp)

    def createJoints(self):
        # draw Joints

        # orientations
        pass

    def createControllers(self):
        pass

    def createRoots(self):
        pass

    def createIKsetup(self):
        pass

    def createFKsetup(self):
        pass

    def ikfkSwitching(self):
        pass

    def createRibbons(self):
        pass

    def createTwistSplines(self):
        pass

    def createAngleExtractors(self):
        pass

    def roundUp(self):
        cmds.parentConstraint(self.limbPlug, self.scaleGrp, mo=False)
        cmds.setAttr("%s.rigVis" % self.scaleGrp, 0)

        self.scaleConstraints.append(self.scaleGrp)
        # lock and hide

    def createLimb(self):
        self.createGrp()
        self.createJoints()
        self.createControllers()
        self.createRoots()
        self.createIKsetup()
        self.createFKsetup()
        self.ikfkSwitching()
        self.createRibbons()
        self.createTwistSplines()
        self.createAngleExtractors()
        self.roundUp()

class Guides(object):
    def __init__(self, side="L", suffix="LIMBNAME", segments=None, tMatrix=None, upVector=(0, 1, 0), mirrorVector=(1, 0, 0), lookVector=(0,0,1), *args, **kwargs):
        super(Guides, self).__init__()
        # fool check

        #-------Mandatory------[Start]
        self.side = side
        self.sideMultiplier = -1 if side == "R" else 1
        self.suffix = suffix
        self.segments = segments
        self.tMatrix = om.MMatrix(tMatrix) if tMatrix else om.MMatrix()
        self.upVector = om.MVector(upVector)
        self.mirrorVector = om.MVector(mirrorVector)
        self.lookVector = om.MVector(lookVector)

        self.offsetVector = None
        self.guideJoints = []
        #-------Mandatory------[End]

    def draw_joints(self):
        if self.side == "C":
            # Guide joint positions for limbs with no side orientation
            pass
        else:
            # Guide joint positions for limbs with sides
            pass

        # Define the offset vector

        # Draw the joints

        # Update the guideJoints list

        # set orientation of joints

    def define_attributes(self):
        # set joint side and type attributes
        _ = [functions.set_joint_side(jnt, self.side) for jnt in self.guideJoints]

        # ----------Mandatory---------[Start]
        root_jnt = self.guideJoints[0]
        attribute.create_global_joint_attrs(root_jnt, moduleName="%s_MODULENAME" % self.side, upAxis=self.upVector, mirrorAxis=self.mirrorVector, lookAxis=self.lookVector)
        # ----------Mandatory---------[End]

        for attr_dict in LIMB_DATA["properties"]:
            attribute.create_attribute(root_jnt, attr_dict)

    def createGuides(self):
        self.draw_joints()
        self.define_attributes()

    def convertJoints(self, joints_list):
        self.guideJoints = joints_list
        self.define_attributes()