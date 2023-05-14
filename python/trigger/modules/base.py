from maya import cmds
import maya.api.OpenMaya as om

from trigger.library import functions, naming, joint
from trigger.library import connection
from trigger.objects.controller import Controller
from trigger.modules import _module

from trigger.core import filelog

LOG = filelog.Filelog(logname=__name__, filename="trigger_log")

LIMB_DATA = {
    "members": ["Base"],
    "properties": [],
    "multi_guide": None,
    "sided": False,
}


class Base(_module.ModuleCore):
    def __init__(self, build_data=None, inits=None, *args, **kwargs):
        super(Base, self).__init__()
        if build_data:
            if len(build_data.keys()) > 1:
                LOG.error("Base can only have one initial joint")
                return
            self.inits = [build_data["Base"]]
        elif inits:
            if len(inits) > 1:
                cmds.error("Root can only have one initial joint")
                return

            self.inits = inits
        else:
            LOG.error("Class needs either build_data or inits to be constructed")

        self.module_name = (naming.unique_name(cmds.getAttr("%s.moduleName" % self.inits[0])))
        self.base_jnt = None

        # self.cont_IK_OFF = None
        # self.controllers = []
        # self.limbGrp = None
        # self.scaleGrp = None
        # self.limbPlug = None
        # self.nonScaleGrp = None
        # self.sockets = []
        # self.scaleConstraints = []
        # self.anchors = []
        # self.anchorLocations = []
        # self.deformerJoints = []
        # self.colorCodes = [6, 18]

    def create_groups(self):
        self.limbGrp = cmds.group(name=naming.parse([self.module_name]), empty=True)

        self.scaleGrp = cmds.group(name=naming.parse([self.module_name, "scale"], suffix="grp"), empty=True)

        functions.align_to(self.scaleGrp, self.inits[0], position=True, rotation=False)
        self.nonScaleGrp = cmds.group(name=naming.parse([self.module_name, "nonScale"], suffix="grp"), empty=True)


        cmds.addAttr(self.scaleGrp, attributeType="bool", longName="Control_Visibility", shortName="contVis", defaultValue=True)
        cmds.addAttr(self.scaleGrp, attributeType="bool", longName="Joints_Visibility", shortName="jointVis", defaultValue=True)
        cmds.addAttr(self.scaleGrp, attributeType="bool", longName="Rig_Visibility", shortName="rigVis", defaultValue=False)
        # make the created attributes visible in the channel box
        cmds.setAttr("%s.contVis" % self.scaleGrp, channelBox=True)
        cmds.setAttr("%s.jointVis" % self.scaleGrp, channelBox=True)
        cmds.setAttr("%s.rigVis" % self.scaleGrp, channelBox=True)

        # cmds.parent(self.scaleGrp, self.limbGrp)
        cmds.parent(self.nonScaleGrp, self.limbGrp)

        # cmds.parent(self.scaleGrp, self.limbGrp)
        # cmds.parent(self.nonScaleGrp, self.limbGrp)
        # cmds.parent(self.cont_IK_OFF, self.limbGrp)

        # cmds.parent(self.scaleGrp, self.nonScaleGrp, self.cont_IK_OFF, self.limbGrp)

        # cmds.parent(self.scaleGrp, self.cont_IK_OFF, self.limbGrp)
        # cmds.parent(self.scaleGrp, None, self.limbGrp)
        cmds.parent(self.scaleGrp, self.limbGrp)
        # self.scaleConstraints.append(self.scaleGrp)

    def createJoints(self):
        self.base_jnt = cmds.joint(name=naming.parse([self.module_name], suffix="j"))
        cmds.connectAttr("{0}.rigVis".format(self.scaleGrp), "{0}.v".format(self.base_jnt))

        functions.align_to(self.base_jnt, self.inits[0], position=True, rotation=False)
        self.limbPlug = self.base_jnt
        self.sockets.append(self.base_jnt)

    def createControllers(self):
        # placement_cont, _ = icon.create_icon("Circle", icon_name=naming.unique_name("placement_cont"),
        #                                      scale=(10, 10, 10))
        placement_cont = Controller(shape="Circle",
                                    name=naming.parse([self.module_name, "placement"], suffix="cont"),
                                    scale=(10, 10, 10),
                                    side="C",
                                    tier="primary"
                                    )
        # master_cont, _ = icon.create_icon("TriCircle", icon_name=naming.unique_name("master_cont"), scale=(15, 15, 15))
        master_cont = Controller(shape="TriCircle",
                                 name=naming.parse([self.module_name, "master"], suffix="cont"),
                                 scale=(15, 15, 15),
                                 side = "C",
                                 tier = "primary"
                                 )


        self.controllers = [master_cont, placement_cont]

        placement_off = placement_cont.add_offset("off")
        master_off = master_cont.add_offset("off")
        functions.align_to(placement_off, self.base_jnt)
        functions.align_to(master_off, self.base_jnt)

        cmds.parent(placement_off, master_cont.name)
        # cmds.parent(master_off, self.scaleGrp)
        cmds.parent(master_off, self.limbGrp)

        # cmds.connectAttr("%s.s" %self.scaleGrp, "%s.s" %master_off)

        cmds.parentConstraint(placement_cont.name, self.base_jnt, maintainOffset=False)

        # functions.colorize(placement_cont, self.colorCodes[0])
        # functions.colorize(master_cont, self.colorCodes[0])
        self.anchorLocations.append(placement_cont.name)
        self.anchorLocations.append(master_cont.name)

        cmds.connectAttr("%s.contVis" % self.scaleGrp, "%s.v" % placement_off)
        cmds.connectAttr("%s.contVis" % self.scaleGrp, "%s.v" % master_off)

        connection.matrixConstraint(master_cont.name, self.scaleGrp, skipScale="xyz")


        placement_cont.lock(["sx", "sy", "sz", "v"])
        master_cont.lock(["sx", "sy", "sz", "v"])

    def execute(self):
        # self.scaleConstraints.append(self.scaleGrp)
        self.createJoints()
        self.createControllers()


    # def createLimb(self):
    #     """Creates base joint for master and placement conts"""
    #     LOG.info("Creating Base %s" % self.module_name)
    #     self.create_groups()
    #     self.createJoints()
    #     self.createControllers()


class Guides(_module.GuidesCore):
    limb_data = LIMB_DATA
    # def __init__(self, side="L", suffix="base", segments=None, tMatrix=None, upVector=(0, 1, 0), mirrorVector=(1, 0, 0), lookVector=(0, 0, 1), *args, **kwargs):
    # def __init__(self, suffix="base", **kwargs):
    #     super(Guides, self).__init__(suffix=suffix, **kwargs)
    # def __init__(self, *args, **kwargs):
    #     super(Guides, self).__init__(*args, **kwargs)
        # fool check

        # # -------Mandatory------[Start]
        # self.side = side
        # self.sideMultiplier = -1 if side == "R" else 1
        # self.name = suffix
        # self.segments = segments
        # self.tMatrix = om.MMatrix(tMatrix) if tMatrix else om.MMatrix()
        # self.upVector = om.MVector(upVector)
        # self.mirrorVector = om.MVector(mirrorVector)
        # self.lookVector = om.MVector(lookVector)
        #
        # self.offsetVector = None
        # self.guideJoints = []
        # # -------Mandatory------[End]

    def draw_joints(self):
        # Define the offset vector
        self.offsetVector = om.MVector(0, 1, 0)

        # Draw the joints
        cmds.select(clear=True)
        root_jnt = cmds.joint(name=naming.parse([self.name, "root"], side=self.side, suffix="jInit"))

        # Update the guideJoints list
        self.guideJoints.append(root_jnt)

        # set orientation of joints

    def define_guides(self):
        """Override the guide definition method"""
        joint.set_joint_type(self.guideJoints[0], "Base")

    # def define_attributes(self):
    #     # set joint side and type attributes
    #     joint.set_joint_type(self.guideJoints[0], "Base")
    #     cmds.setAttr("{0}.radius".format(self.guideJoints[0]), 2)
    #     _ = [joint.set_joint_side(jnt, self.side) for jnt in self.guideJoints]
    #
    #     # ----------Mandatory---------[Start]
    #     root_jnt = self.guideJoints[0]
    #     attribute.create_global_joint_attrs(root_jnt, moduleName=naming.parse([self.name], side=self.side), upAxis=self.upVector,
    #                                         mirrorAxis=self.mirrorVector, lookAxis=self.lookVector)
    #     # ----------Mandatory---------[End]
    #
    #     for attr_dict in LIMB_DATA["properties"]:
    #         attribute.create_attribute(root_jnt, attr_dict)

    # def createGuides(self):
    #     self.draw_joints()
    #     self.define_attributes()
    #
    # def convertJoints(self, joints_list):
    #     if len(joints_list) != 1:
    #         LOG.warning("Define or select a single joint for Root Guide conversion. Skipping")
    #         return
    #     self.guideJoints = joints_list
    #     self.define_attributes()
