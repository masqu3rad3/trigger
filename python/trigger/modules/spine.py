from maya import cmds
import maya.api.OpenMaya as om

from trigger.library import functions, joint
from trigger.library import naming
from trigger.library import attribute
from trigger.library import api
from trigger.objects.controller import Controller
from trigger.objects import twist_spline as twistSpline

from trigger.core import filelog
log = filelog.Filelog(logname=__name__, filename="trigger_log")

LIMB_DATA = {
        "members": ["SpineRoot", "Spine", "SpineEnd"],
        "properties": [{"attr_name": "resolution",
                        "nice_name": "Resolution",
                        "attr_type": "long",
                        "min_value": 1,
                        "max_value": 9999,
                        "default_value": 4,
                        },
                       {"attr_name": "dropoff",
                        "nice_name": "Drop_Off",
                        "attr_type": "float",
                        "min_value": 0.1,
                        "max_value": 5.0,
                        "default_value": 1.0,
                        },
                       {"attr_name": "twistType",
                        "nice_name": "Twist_Type",
                        "attr_type": "enum",
                        "enum_list": "regular:infinite",
                        "default_value": 0,
                        },
                       {"attr_name": "mode",
                        "nice_name": "Mode",
                        "attr_type": "enum",
                        "enum_list": "equalDistance:sameDistance",
                        "default_value": 0,
                        },
                       ],
        "multi_guide": "Spine",
        "sided": False,
    }

class Spine(object):

    def __init__(self, build_data=None, inits=None, *args, **kwargs):
        super(Spine, self).__init__()
        if build_data:
            sRoot=build_data.get("SpineRoot")
            try:
                self.spines=reversed(build_data.get("Spine"))
                self.spineEnd = build_data.get("SpineEnd")
                self.inits = [sRoot] + sorted(self.spines) + [self.spineEnd]
            except:
                self.spineEnd = build_data.get("SpineEnd")
                self.inits = [sRoot] + [self.spineEnd]
        elif inits:
            # fool proofing
            if (len(inits) < 2):
                cmds.error("Insufficient Spine Initialization Joints")
                return
            self.inits = inits

        else:
            log.error("Class needs either build_data or arminits to be constructed")

        # get distances
        self.iconSize = functions.get_distance(self.inits[0], self.inits[-1])

        # get positions
        self.rootPoint = api.get_world_translation(self.inits[0])
        self.chestPoint = api.get_world_translation(self.inits[-1])

        # initialize coordinates
        self.up_axis, self.mirror_axis, self.look_axis = joint.get_rig_axes(self.inits[0])

        # get the properties from the root
        self.useRefOrientation = cmds.getAttr("%s.useRefOri" %self.inits[0])
        self.resolution = int(cmds.getAttr("%s.resolution" %self.inits[0]))
        self.dropoff = float(cmds.getAttr("%s.dropoff" %self.inits[0]))
        self.splineMode = cmds.getAttr("%s.mode" %self.inits[0], asString=True)
        self.twistType = cmds.getAttr("%s.twistType" %self.inits[0], asString=True)
        self.side = joint.get_joint_side(self.inits[0])
        self.sideMult = -1 if self.side == "R" else 1

        # initialize suffix
        self.module_name = (naming.unique_name(cmds.getAttr("%s.moduleName" % self.inits[0])))


        # scratch variables
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

    def create_groups(self):
        self.limbGrp = cmds.group(name=naming.parse([self.module_name], suffix="grp"), empty=True)
        self.scaleGrp = cmds.group(name="%s_scaleGrp" % self.module_name, em=True)
        self.scaleGrp = cmds.group(name=naming.parse([self.module_name, "scale"], suffix="grp"), em=True)
        functions.align_to(self.scaleGrp, self.inits[0], position=True, rotation=False)
        self.nonScaleGrp = cmds.group(name="%s_nonScaleGrp" % self.module_name, em=True)
        self.nonScaleGrp = cmds.group(name=naming.parse([self.module_name, "nonScale"], suffix="grp"), em=True)

        for nicename, attrname in zip(["Control_Visibility", "Joints_Visibility", "Rig_Visibility"], ["contVis", "jointVis", "rigVis"]):
            attribute.create_attribute(self.scaleGrp, nice_name=nicename, attr_name=attrname, attr_type="bool",
                                       keyable=False, display=True)

        cmds.parent(self.scaleGrp, self.limbGrp)
        cmds.parent(self.nonScaleGrp, self.limbGrp)

    def create_joints(self):
        # draw Joints
        # # Create Plug Joints
        cmds.select(clear=True)
        self.limbPlug = cmds.joint(name=naming.parse([self.module_name, "plug"], suffix="j"), p=self.rootPoint, radius=3)
        cmds.select(clear=True)
        self.endSocket = cmds.joint(name=naming.parse([self.module_name, "socket", "chest"], suffix="jDef"), p=self.chestPoint)
        self.sockets.append(self.endSocket)
        cmds.select(clear=True)
        self.startSocket = cmds.joint(p=self.rootPoint, name=naming.parse([self.module_name, "socket", "root"], suffix="grp"), radius=3)
        self.sockets.append(self.startSocket)

        ## Create temporaray Guide Joints
        cmds.select(clear=True)
        self.guideJoints = [cmds.joint(p=api.get_world_translation(i)) for i in self.inits]

        if not self.useRefOrientation:
            joint.orient_joints(self.guideJoints, world_up_axis=(self.up_axis), up_axis=(0, 0, -1), reverse_aim=self.sideMult, reverse_up=self.sideMult)
        else:
            for x in range (len(self.guideJoints)):
                functions.align_to(self.guideJoints[x], self.inits[x], position=True, rotation=True)
                cmds.makeIdentity(self.guideJoints[x], apply=True)


        self.deformerJoints.append(self.startSocket)
        self.deformerJoints.append(self.endSocket)

        functions.align_to_alter(self.limbPlug, self.guideJoints[0], mode=2)

        cmds.parent(self.startSocket, self.scaleGrp)
        cmds.connectAttr("%s.rigVis" %self.scaleGrp, "%s.v" %self.limbPlug)

    def create_controllers(self):

        # icon = ic.Icon()
        ## Hips Controller
        cont_hips_scale = (self.iconSize / 1.5, self.iconSize / 1.5, self.iconSize / 1.5)
        self.cont_hips = Controller(
            name=naming.parse([self.module_name, "hips"], suffix="cont"),
            shape="Waist",
            scale=cont_hips_scale,
            normal=(1, 0, 0),
            side=self.side,
            tier="primary"
        )
        self.controllers.append(self.cont_hips)
        functions.align_to_alter(self.cont_hips.name, self.guideJoints[0], mode=2)
        self.cont_hips_ORE = self.cont_hips.add_offset("ORE")

        ## Body Controller
        cont_body_scale = (self.iconSize * 0.75, self.iconSize * 0.75, self.iconSize * 0.75)
        self.cont_body = Controller(
            name=naming.parse([self.module_name, "body"], suffix="cont"),
            shape="Square",
            scale=cont_body_scale,
            normal=(1, 0, 0),
            side=self.side,
            tier="primary"
        )
        self.controllers.insert(0, self.cont_body)
        functions.align_to_alter(self.cont_body.name, self.guideJoints[0], mode=2)
        self.cont_body_ORE = self.cont_body.add_offset("POS")

        # create visibility attributes for cont_Body
        cmds.addAttr(self.cont_body.name, attributeType="bool", longName="FK_A_Visibility", shortName="fkAvis", defaultValue=True)
        cmds.addAttr(self.cont_body.name, attributeType="bool", longName="FK_B_Visibility", shortName="fkBvis", defaultValue=True)
        cmds.addAttr(self.cont_body.name, attributeType="bool", longName="Tweaks_Visibility", shortName="tweakVis", defaultValue=True)
        # make the created attributes visible in the channelbox
        cmds.setAttr("{}.fkAvis".format(self.cont_body.name), channelBox=True)
        cmds.setAttr("{}.fkBvis".format(self.cont_body.name), channelBox=True)
        cmds.setAttr("{}.tweakVis".format(self.cont_body.name), channelBox=True)

        ## Chest Controller
        cont_chest_scale = (self.iconSize*0.5, self.iconSize*0.35, self.iconSize*0.2)
        self.cont_chest = Controller(
            name=naming.parse([self.module_name, "chest"], suffix="cont"),
            shape="Cube",
            scale=cont_chest_scale,
            normal=(0, 0, 1),
            side=self.side,
            tier="primary"
        )
        self.controllers.append(self.cont_chest)
        functions.align_to_alter(self.cont_chest.name, self.guideJoints[-1], mode=2)
        cont_Chest_ORE = self.cont_chest.add_offset("ORE")

        self.cont_spineFK_A_List = []
        self.cont_spineFK_B_List = []
        cont_spine_fk_a_scale = (self.iconSize / 2, self.iconSize / 2, self.iconSize / 2)
        cont_spine_fk_b_scale = (self.iconSize / 2.5, self.iconSize / 2.5, self.iconSize / 2.5)

        for m in range (0, len(self.guideJoints)):
            cont_a = Controller(
                name=naming.parse([self.module_name, "FK", "A", m], suffix="cont"),
                shape="Circle",
                scale=cont_spine_fk_a_scale,
                normal=(1, 0, 0),
                side=self.side,
                tier="primary"
            )
            functions.align_to_alter(cont_a.name, self.guideJoints[m], 2)
            cont_a_ore = cont_a.add_offset("ORE")
            self.cont_spineFK_A_List.append(cont_a)
            contB = Controller(
                name=naming.parse([self.module_name, "FK", "B", m], suffix="cont"),
                shape="Ngon",
                scale=cont_spine_fk_b_scale,
                normal=(1, 0, 0),
                side=self.side,
                tier="primary"
            )
            functions.align_to(contB.name, self.guideJoints[m], position=True, rotation=True)
            cont_b_ore = contB.add_offset("ORE")
            self.cont_spineFK_B_List.append(contB)

            if m != 0:
                a_start_parent = self.cont_spineFK_A_List[m].parent
                b_end_parent =self.cont_spineFK_B_List[m - 1].parent
                cmds.parent(a_start_parent, self.cont_spineFK_A_List[m - 1].name)
                cmds.parent(b_end_parent, self.cont_spineFK_B_List[m].name)

        cmds.parent(self.cont_hips_ORE, self.cont_spineFK_B_List[0].name)

        cmds.parent(self.cont_spineFK_B_List[-1].parent, self.cont_body.name)

        cmds.parent(cont_Chest_ORE, self.cont_spineFK_A_List[-1].name)
        cmds.parent(self.cont_spineFK_A_List[0].parent, self.cont_body.name)
        cmds.parent(self.cont_body_ORE, self.limbGrp)

        self.controllers.extend(self.cont_spineFK_A_List)
        self.controllers.extend(self.cont_spineFK_B_List)

        cmds.parentConstraint(self.limbPlug, self.cont_body_ORE, maintainOffset=False)

        attribute.drive_attrs("%s.fkAvis" % self.cont_body.name, ["%s.v" % x.shapes[0] for x in self.cont_spineFK_A_List])
        attribute.drive_attrs("%s.fkBvis" % self.cont_body.name, ["%s.v" % x.shapes[0] for x in self.cont_spineFK_B_List])

    def create_ik_setup(self):
        spine = twistSpline.TwistSpline()
        spine.upAxis =  -(om.MVector(self.look_axis))
        spine.createTspline(self.guideJoints, "Spine_%s" % self.module_name, self.resolution, dropoff=self.dropoff, mode=self.splineMode, twistType=self.twistType)

        self.sockets.extend(spine.defJoints)

        attribute.attribute_pass(spine.scaleGrp, self.scaleGrp, attributes=["sx", "sy", "sz"], keepSourceAttributes=True)

        midConnection = spine.contCurves_ORE[int((len(spine.contCurves_ORE) / 2))]

        # # connect the spine root to the master root
        cmds.parentConstraint(self.startSocket, spine.contCurve_Start, maintainOffset=True)

        # # connect the spine end
        cmds.parentConstraint(self.cont_chest.name, spine.contCurve_End, maintainOffset=True)

        # # connect the master root to the hips controller
        cmds.parentConstraint(self.cont_hips.name, self.startSocket, maintainOffset=True)
        # # connect upper plug points to the spine and orient it to the chest controller
        cmds.pointConstraint(spine.endLock, self.endSocket)
        cmds.orientConstraint(self.cont_chest.name, self.endSocket)

        # # pass Stretch controls from the splineIK to neck controller
        attribute.attribute_pass(spine.attPassCont, self.cont_chest.name)

        for m in range (len(spine.contCurves_ORE)):
            if m > 0 and m < len(spine.contCurves_ORE):
                oCon = cmds.parentConstraint(self.cont_chest.name, self.cont_hips.name, spine.contCurves_ORE[m], maintainOffset=True)[0]
                blendRatio = (m + 0.0) / len(spine.contCurves_ORE)
                cmds.setAttr("{0}.{1}W0".format(oCon, self.cont_chest.name), blendRatio)
                cmds.setAttr("{0}.{1}W1".format(oCon, self.cont_hips.name), 1 - blendRatio)

        cmds.parent(spine.contCurves_ORE, spine.scaleGrp)
        cmds.parent(self.endSocket, spine.scaleGrp)
        cmds.parent(spine.endLock, spine.scaleGrp)
        cmds.parent(spine.scaleGrp, self.scaleGrp)

        cmds.parent(spine.nonScaleGrp, self.nonScaleGrp)


        self.deformerJoints += spine.defJoints
        attribute.drive_attrs("%s.jointVis" % self.scaleGrp, ["%s.v" % x for x in self.deformerJoints])

        for i in range(len(spine.contCurves_ORE)):
            if i != 0 or i != len(spine.contCurves_ORE):
                node = functions.create_offset_group(spine.contCurves_ORE[i], "OFF")
                cmds.connectAttr("%s.tweakVis" %self.cont_body.name, "%s.v" %node)
                cmds.connectAttr("%s.contVis" %self.scaleGrp, "%s.v" %spine.contCurves_ORE[i])
        cmds.connectAttr("%s.contVis" %self.scaleGrp, "%s.v" %self.cont_body.name)

        for lst in spine.noTouchData:
            attribute.drive_attrs("%s.rigVis" % self.scaleGrp, ["%s.v" % x for x in lst])

        functions.colorize(self.deformerJoints, self.colorCodes[0], shape=False)

    def roundUp(self):
        cmds.parentConstraint(self.limbPlug, self.scaleGrp, maintainOffset=False)
        cmds.setAttr("%s.rigVis" %self.scaleGrp, 0)

        self.scaleConstraints.extend([self.scaleGrp, self.cont_body_ORE])
        self.anchorLocations = [self.cont_hips.name, self.cont_body.name, self.cont_chest.name]

        cmds.delete(self.guideJoints)
        # lock and hide
        self.cont_body.lock_visibility()
        self.cont_hips.lock(["sx", "sy", "sz", "v"])
        self.cont_chest.lock(["sx", "sy", "sz", "v"])

        _ = [x.lock(["tx", "ty", "tz", "sx", "sy", "sz", "v"]) for x in self.cont_spineFK_A_List]
        _ = [x.lock(["tx", "ty", "tz", "sx", "sy", "sz", "v"]) for x in self.cont_spineFK_B_List]

        for cont in self.controllers:
            cont.set_defaults()

    def createLimb(self):
        self.create_groups()
        self.create_joints()
        self.create_controllers()
        self.create_ik_setup()
        self.roundUp()

class Guides(object):
    def __init__(self, side="C", suffix="spine", segments=None, tMatrix=None, upVector=(0, 1, 0), mirrorVector=(1, 0, 0), lookVector=(0,0,1), *args, **kwargs):
        super(Guides, self).__init__()
        # fool check
        # if not segments or segments < 1:
        #     log.warning("minimum segments required for the simple tail is two. current: %s" % segments)
        #     return

        #-------Mandatory------[Start]
        self.side = side
        self.sideMultiplier = -1 if side == "R" else 1
        self.name = suffix
        self.segments = segments or 2
        self.tMatrix = om.MMatrix(tMatrix) if tMatrix else om.MMatrix()
        self.upVector = om.MVector(upVector)
        self.mirrorVector = om.MVector(mirrorVector)
        self.lookVector = om.MVector(lookVector)

        self.offsetVector = None
        self.guideJoints = []
        #-------Mandatory------[End]

    def draw_joints(self):
        rPoint = om.MVector(0, 14.0, 0) * self.tMatrix
        nPoint = om.MVector(0, 21.0, 0) * self.tMatrix
        add = (nPoint - rPoint) / ((self.segments + 1) - 1)

        # Define the offset vector
        self.offsetVector = (nPoint - rPoint).normal()

        # Draw the joints & set joint side and type attributes
        for nmb in range(self.segments + 1):
            spine_jnt = cmds.joint(p=(rPoint + (add * nmb)), name=naming.parse([self.name, nmb], suffix="jInit"))
            # Update the guideJoints list
            self.guideJoints.append(spine_jnt)

        # set orientation of joints
        joint.orient_joints(self.guideJoints, world_up_axis=-self.lookVector, reverse_aim=self.sideMultiplier, reverse_up=self.sideMultiplier)


    def define_attributes(self):
        joint.set_joint_type(self.guideJoints[0], "SpineRoot")
        _ = [joint.set_joint_type(jnt, "Spine") for jnt in self.guideJoints[1:-1]]
        joint.set_joint_type(self.guideJoints[-1], "SpineEnd")
        cmds.setAttr("{0}.radius".format(self.guideJoints[0]), 2)
        _ = [joint.set_joint_side(jnt, self.side) for jnt in self.guideJoints]

        # ----------Mandatory---------[Start]
        root_jnt = self.guideJoints[0]
        attribute.create_global_joint_attrs(root_jnt, moduleName="%s_spine" %self.name, upAxis=self.upVector, mirrorAxis=self.mirrorVector, lookAxis=self.lookVector)
        # ----------Mandatory---------[End]
        for attr_dict in LIMB_DATA["properties"]:
            attribute.create_attribute(root_jnt, attr_dict)

    def createGuides(self):
        self.draw_joints()
        self.define_attributes()

    def convertJoints(self, joints_list):
        if len(joints_list) < 2:
            log.warning("Define or select at least 2 joints for Spine Guide conversion. Skipping")
            return
        self.guideJoints = joints_list
        self.define_attributes()