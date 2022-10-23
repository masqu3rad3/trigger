from maya import cmds
import maya.api.OpenMaya as om

from trigger.library import functions, naming, joint
from trigger.library import attribute
from trigger.library import connection

from trigger.library import controllers as ic
from trigger.core import filelog


log = filelog.Filelog(logname=__name__, filename="trigger_log")


LIMB_DATA = {
        "members": ["Base"],
        "properties": [],
        "multi_guide": None,
        "sided": False,
    }

class Base(object):
    def __init__(self, build_data=None, inits=None, *args, **kwargs):
        super(Base, self).__init__()
        if build_data:
            if len(build_data.keys()) > 1:
                log.error("Base can only have one initial joint")
                return
            self.baseInit = build_data["Base"]
        elif inits:
            if len(inits) > 1:
                cmds.error("Root can only have one initial joint")
                return
            self.baseInit = inits[0]
        else:
            log.error("Class needs either build_data or inits to be constructed")

        self.suffix = (naming.unique_name(cmds.getAttr("%s.moduleName" % self.baseInit)))

        self.controllers = []
        self.limbGrp = None
        self.scaleGrp = None
        self.limbPlug = None
        self.nonScaleGrp = None
        self.cont_IK_OFF = None
        self.sockets = []
        self.scaleConstraints = []
        self.anchors = []
        self.anchorLocations = []
        self.deformerJoints = []
        self.colorCodes = [6, 18]

    def createGrp(self):
        self.scaleGrp = cmds.group(name="%s_scaleGrp" % self.suffix, em=True)
        cmds.addAttr(self.scaleGrp, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True)
        cmds.addAttr(self.scaleGrp, at="bool", ln="Joints_Visibility", sn="jointVis", defaultValue=True)
        cmds.addAttr(self.scaleGrp, at="bool", ln="Rig_Visibility", sn="rigVis", defaultValue=True)
        # make the created attributes visible in the channelbox
        cmds.setAttr("{0}.contVis".format(self.scaleGrp), cb=True)
        cmds.setAttr("{0}.jointVis".format(self.scaleGrp), cb=True)
        cmds.setAttr("{0}.rigVis".format(self.scaleGrp), cb=True)

        self.limbGrp = cmds.group(name=self.suffix, em=True)
        cmds.parent(self.scaleGrp, self.nonScaleGrp, self.cont_IK_OFF, self.limbGrp)
        self.scaleConstraints.append(self.scaleGrp)

    def createJoints(self):
        self.base_jnt = cmds.joint(name="%s_jnt" % self.suffix)
        cmds.connectAttr("{0}.rigVis".format(self.scaleGrp), "{0}.v".format(self.base_jnt))

        functions.align_to(self.base_jnt, self.baseInit, position=True, rotation=False)
        self.limbPlug = self.base_jnt
        self.sockets.append(self.base_jnt)

    def createControllers(self):
        icon = ic.Icon()
        placement_cont, _ = icon.create_icon("Circle", icon_name=naming.unique_name("placement_cont"), scale=(10, 10, 10))
        master_cont, _ = icon.create_icon("TriCircle", icon_name=naming.unique_name("master_cont"), scale=(15, 15, 15))
        self.controllers = [master_cont, placement_cont]

        placement_off = functions.create_offset_group(placement_cont, "off")
        master_off = functions.create_offset_group(master_cont, "off")
        functions.align_to(placement_off, self.base_jnt)
        functions.align_to(master_off, self.base_jnt)

        cmds.parent(placement_off, master_cont)
        # cmds.parent(master_off, self.scaleGrp)
        cmds.parent(master_off, self.limbGrp)

        # cmds.connectAttr("%s.s" %self.scaleGrp, "%s.s" %master_off)

        cmds.parentConstraint(placement_cont, self.base_jnt, mo=False)

        functions.colorize(placement_cont, self.colorCodes[0])
        functions.colorize(master_cont, self.colorCodes[0])
        self.anchorLocations.append(placement_cont)
        self.anchorLocations.append(master_cont)

        cmds.connectAttr("%s.contVis" % self.scaleGrp, "%s.v" % placement_off)
        cmds.connectAttr("%s.contVis" % self.scaleGrp, "%s.v" % master_off)

        connection.matrixConstraint(master_cont, self.scaleGrp, ss="xyz")

        attribute.lock_and_hide(placement_cont, ["sx", "sy", "sz", "v"])
        attribute.lock_and_hide(master_cont, ["sx", "sy", "sz", "v"])

    def createLimb(self):
        """Creates base joint for master and placement conts"""
        log.info("Creating Base %s" % self.suffix)
        self.createGrp()
        self.createJoints()
        self.createControllers()




class Guides(object):
    def __init__(self, side="L", suffix="base", segments=None, tMatrix=None, upVector=(0, 1, 0), mirrorVector=(1, 0, 0), lookVector=(0,0,1), *args, **kwargs):
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
        self.offsetVector = om.MVector(0, 1, 0)

        # Draw the joints
        cmds.select(d=True)
        root_jnt = cmds.joint(name="base_{0}".format(self.suffix))

        # Update the guideJoints list
        self.guideJoints.append(root_jnt)

        # set orientation of joints

    def define_attributes(self):
        # set joint side and type attributes
        joint.set_joint_type(self.guideJoints[0], "Base")
        cmds.setAttr("{0}.radius".format(self.guideJoints[0]), 2)
        _ = [joint.set_joint_side(jnt, self.side) for jnt in self.guideJoints]

        # ----------Mandatory---------[Start]
        root_jnt = self.guideJoints[0]
        attribute.create_global_joint_attrs(root_jnt, moduleName="Base", upAxis=self.upVector, mirrorAxis=self.mirrorVector, lookAxis=self.lookVector)
        # ----------Mandatory---------[End]

        for attr_dict in LIMB_DATA["properties"]:
            attribute.create_attribute(root_jnt, attr_dict)

    def createGuides(self):
        self.draw_joints()
        self.define_attributes()

    def convertJoints(self, joints_list):
        if len(joints_list) != 1:
            log.warning("Define or select a single joint for Root Guide conversion. Skipping")
            return
        self.guideJoints = joints_list
        self.define_attributes()