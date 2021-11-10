from maya import cmds
import maya.api.OpenMaya as om

from trigger.library import functions
from trigger.library import naming
from trigger.library import attribute
from trigger.library import api
from trigger.library import controllers as ic
from trigger.library import twist_spline as twistSpline

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
        self.iconSize = functions.getDistance(self.inits[0], self.inits[-1])

        # get positions
        self.rootPoint = api.getWorldTranslation(self.inits[0])
        self.chestPoint = api.getWorldTranslation(self.inits[-1])

        # initialize coordinates
        self.up_axis, self.mirror_axis, self.look_axis = functions.getRigAxes(self.inits[0])

        # get the properties from the root
        self.useRefOrientation = cmds.getAttr("%s.useRefOri" %self.inits[0])
        self.resolution = int(cmds.getAttr("%s.resolution" %self.inits[0]))
        self.dropoff = float(cmds.getAttr("%s.dropoff" %self.inits[0]))
        self.splineMode = cmds.getAttr("%s.mode" %self.inits[0], asString=True)
        self.twistType = cmds.getAttr("%s.twistType" %self.inits[0], asString=True)
        self.side = functions.get_joint_side(self.inits[0])
        self.sideMult = -1 if self.side == "R" else 1

        # initialize suffix
        self.suffix = (naming.uniqueName(cmds.getAttr("%s.moduleName" % self.inits[0])))


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

    def createGrp(self):
        self.limbGrp = cmds.group(name=self.suffix, em=True)
        self.scaleGrp = cmds.group(name="%s_scaleGrp" % self.suffix, em=True)
        functions.alignTo(self.scaleGrp, self.inits[0], position=True, rotation=False)
        self.nonScaleGrp = cmds.group(name="%s_nonScaleGrp" % self.suffix, em=True)

        cmds.addAttr(self.scaleGrp, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True)
        cmds.addAttr(self.scaleGrp, at="bool", ln="Joints_Visibility", sn="jointVis", defaultValue=True)
        cmds.addAttr(self.scaleGrp, at="bool", ln="Rig_Visibility", sn="rigVis", defaultValue=False)
        # make the created attributes visible in the channelbox
        cmds.setAttr("%s.contVis" %self.scaleGrp, cb=True)
        cmds.setAttr("%s.jointVis" %self.scaleGrp, cb=True)
        cmds.setAttr("%s.rigVis" %self.scaleGrp, cb=True)

        cmds.parent(self.scaleGrp, self.limbGrp)
        cmds.parent(self.nonScaleGrp, self.limbGrp)

    def createJoints(self):
        # draw Joints
        # # Create Plug Joints
        cmds.select(None)
        self.limbPlug = cmds.joint(name="limbPlug_%s" % self.suffix, p=self.rootPoint, radius=3)
        cmds.select(None)
        self.endSocket = cmds.joint(name="jDef_ChestSocket_%s" % self.suffix, p=self.chestPoint)
        self.sockets.append(self.endSocket)
        cmds.select(None)
        self.startSocket = cmds.joint(p=self.rootPoint, name="jDef_RootSocket_%s" % self.suffix, radius=3)
        self.sockets.append(self.startSocket)

        ## Create temporaray Guide Joints
        cmds.select(d=True)
        self.guideJoints = [cmds.joint(p=api.getWorldTranslation(i)) for i in self.inits]

        if not self.useRefOrientation:
            functions.orientJoints(self.guideJoints, worldUpAxis=(self.up_axis), upAxis=(0, 0, -1), reverseAim=self.sideMult, reverseUp=self.sideMult)
        else:
            for x in range (len(self.guideJoints)):
                functions.alignTo(self.guideJoints[x], self.inits[x], position=True, rotation=True)
                cmds.makeIdentity(self.guideJoints[x], a=True)


        self.deformerJoints.append(self.startSocket)
        self.deformerJoints.append(self.endSocket)

        functions.alignToAlter(self.limbPlug, self.guideJoints[0], mode=2)

        cmds.parent(self.startSocket, self.scaleGrp)
        cmds.connectAttr("%s.rigVis" %self.scaleGrp, "%s.v" %self.limbPlug)

    def createControllers(self):

        icon = ic.Icon()
        ## Hips Controller
        contHipsScale = (self.iconSize / 1.5, self.iconSize / 1.5, self.iconSize / 1.5)
        self.cont_hips, dmp = icon.createIcon("Waist", iconName="%s_Hips_cont" % self.suffix, scale=contHipsScale, normal=(1,0,0))
        self.controllers.append(self.cont_hips)
        functions.alignToAlter(self.cont_hips, self.guideJoints[0], mode=2)
        self.cont_hips_ORE = functions.createUpGrp(self.cont_hips, "ORE")

        ## Body Controller
        contBodyScale = (self.iconSize * 0.75, self.iconSize * 0.75, self.iconSize * 0.75)
        self.cont_body, dmp = icon.createIcon("Square", iconName="%s_Body_cont" % self.suffix, scale=contBodyScale, normal=(1,0,0))
        self.controllers.insert(0, self.cont_body)
        functions.alignToAlter(self.cont_body, self.guideJoints[0], mode=2)
        self.cont_body_ORE = functions.createUpGrp(self.cont_body, "POS")

        # create visibility attributes for cont_Body
        cmds.addAttr(self.cont_body, at="bool", ln="FK_A_Visibility", sn="fkAvis", defaultValue=True)
        cmds.addAttr(self.cont_body, at="bool", ln="FK_B_Visibility", sn="fkBvis", defaultValue=True)
        cmds.addAttr(self.cont_body, at="bool", ln="Tweaks_Visibility", sn="tweakVis", defaultValue=True)
        # make the created attributes visible in the channelbox
        cmds.setAttr("%s.fkAvis" %self.cont_body, cb=True)
        cmds.setAttr("%s.fkBvis" %self.cont_body, cb=True)
        cmds.setAttr("%s.tweakVis" %self.cont_body, cb=True)

        ## Chest Controller
        contChestScale = (self.iconSize*0.5, self.iconSize*0.35, self.iconSize*0.2)
        self.cont_chest, dmp = icon.createIcon("Cube", iconName="%s_Chest_cont" % self.suffix, scale=contChestScale, normal=(0,0,1))
        self.controllers.append(self.cont_chest)
        functions.alignToAlter(self.cont_chest, self.guideJoints[-1], mode=2)
        cont_Chest_ORE = functions.createUpGrp(self.cont_chest, "ORE")

        self.cont_spineFK_A_List = []
        self.cont_spineFK_B_List = []
        contSpineFKAScale = (self.iconSize / 2, self.iconSize / 2, self.iconSize / 2)
        contSpineFKBScale = (self.iconSize / 2.5, self.iconSize / 2.5, self.iconSize / 2.5)

        for m in range (0, len(self.guideJoints)):
            contA, _ = icon.createIcon("Circle", iconName="%s%i_SpineFK_A_cont" %(self.suffix, m), scale=contSpineFKAScale, normal=(1, 0, 0))
            functions.alignToAlter(contA, self.guideJoints[m], 2)
            contA_ORE = functions.createUpGrp(contA, "ORE")
            self.cont_spineFK_A_List.append(contA)
            contB, dmp = icon.createIcon("Ngon", iconName="%s%i_SpineFK_B_cont" %(self.suffix, m), scale=contSpineFKBScale, normal=(1,0,0))
            functions.alignTo(contB, self.guideJoints[m], position=True, rotation=True)
            contB_ORE = functions.createUpGrp(contB, "ORE")
            self.cont_spineFK_B_List.append(contB)

            if m != 0:
                a_start_parent = cmds.listRelatives(self.cont_spineFK_A_List[m], parent=True)[0]
                b_end_parent = cmds.listRelatives(self.cont_spineFK_B_List[m - 1], parent=True)[0]
                cmds.parent(a_start_parent, self.cont_spineFK_A_List[m - 1])
                cmds.parent(b_end_parent, self.cont_spineFK_B_List[m])

        cmds.parent(self.cont_hips_ORE, self.cont_spineFK_B_List[0])

        cmds.parent(cmds.listRelatives(self.cont_spineFK_B_List[-1], parent=True), self.cont_body)

        cmds.parent(cont_Chest_ORE, self.cont_spineFK_A_List[-1])
        cmds.parent(cmds.listRelatives(self.cont_spineFK_A_List[0], parent=True), self.cont_body)
        cmds.parent(self.cont_body_ORE, self.limbGrp)

        self.controllers.extend(self.cont_spineFK_A_List)
        self.controllers.extend(self.cont_spineFK_B_List)


        cmds.parentConstraint(self.limbPlug, self.cont_body_ORE, mo=False)

        attribute.drive_attrs("%s.fkAvis" % self.cont_body, ["%s.v" % functions.getShapes(x)[0] for x in self.cont_spineFK_A_List])
        attribute.drive_attrs("%s.fkBvis" % self.cont_body, ["%s.v" % functions.getShapes(x)[0] for x in self.cont_spineFK_B_List])

        functions.colorize(self.cont_body, self.colorCodes[0])
        functions.colorize(self.cont_chest, self.colorCodes[0])
        functions.colorize(self.cont_hips, self.colorCodes[0])

        functions.colorize(self.cont_spineFK_A_List, self.colorCodes[0])
        functions.colorize(self.cont_spineFK_B_List, self.colorCodes[1])

    def createRoots(self):
        pass

    def createIKsetup(self):
        spine = twistSpline.TwistSpline()
        spine.upAxis =  -(om.MVector(self.look_axis))
        spine.createTspline(self.guideJoints, "Spine_%s" % self.suffix, self.resolution, dropoff=self.dropoff, mode=self.splineMode, twistType=self.twistType)

        self.sockets.extend(spine.defJoints)

        attribute.attrPass(spine.scaleGrp, self.scaleGrp, attributes=["sx", "sy", "sz"], keepSourceAttributes=True)

        midConnection = spine.contCurves_ORE[int((len(spine.contCurves_ORE) / 2))]

        # # connect the spine root to the master root
        cmds.parentConstraint(self.startSocket, spine.contCurve_Start, mo=True)

        # # connect the spine end
        cmds.parentConstraint(self.cont_chest, spine.contCurve_End, mo=True)

        # # connect the master root to the hips controller
        cmds.parentConstraint(self.cont_hips, self.startSocket, mo=True)
        # # connect upper plug points to the spine and orient it to the chest controller
        cmds.pointConstraint(spine.endLock, self.endSocket)
        cmds.orientConstraint(self.cont_chest, self.endSocket)

        # # pass Stretch controls from the splineIK to neck controller
        attribute.attrPass(spine.attPassCont, self.cont_chest)

        for m in range (len(spine.contCurves_ORE)):
            if m > 0 and m < len(spine.contCurves_ORE):
                oCon = cmds.parentConstraint(self.cont_chest, self.cont_hips, spine.contCurves_ORE[m], mo=True)[0]
                blendRatio = (m + 0.0) / len(spine.contCurves_ORE)
                cmds.setAttr("{0}.{1}W0".format(oCon, self.cont_chest), blendRatio)
                cmds.setAttr("{0}.{1}W1".format(oCon, self.cont_hips), 1 - blendRatio)

        cmds.parent(spine.contCurves_ORE, spine.scaleGrp)
        cmds.parent(self.endSocket, spine.scaleGrp)
        cmds.parent(spine.endLock, spine.scaleGrp)
        cmds.parent(spine.scaleGrp, self.scaleGrp)

        cmds.parent(spine.nonScaleGrp, self.nonScaleGrp)


        self.deformerJoints += spine.defJoints
        attribute.drive_attrs("%s.jointVis" % self.scaleGrp, ["%s.v" % x for x in self.deformerJoints])

        for i in range(len(spine.contCurves_ORE)):
            if i != 0 or i != len(spine.contCurves_ORE):
                node = functions.createUpGrp(spine.contCurves_ORE[i], "OFF")
                cmds.connectAttr("%s.tweakVis" %self.cont_body, "%s.v" %node)
                cmds.connectAttr("%s.contVis" %self.scaleGrp, "%s.v" %spine.contCurves_ORE[i])
        cmds.connectAttr("%s.contVis" %self.scaleGrp, "%s.v" %self.cont_body)

        for lst in spine.noTouchData:
            attribute.drive_attrs("%s.rigVis" % self.scaleGrp, ["%s.v" % x for x in lst])

        functions.colorize(self.deformerJoints, self.colorCodes[0], shape=False)

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
        cmds.setAttr("%s.rigVis" %self.scaleGrp, 0)

        self.scaleConstraints.extend([self.scaleGrp, self.cont_body_ORE])
        self.anchorLocations = [self.cont_hips, self.cont_body, self.cont_chest]

        cmds.delete(self.guideJoints)
        # lock and hide
        attribute.lockAndHide(self.cont_body, "v")
        attribute.lockAndHide(self.cont_hips, ["sx", "sy", "sz", "v"])
        attribute.lockAndHide(self.cont_chest, ["sx", "sy", "sz", "v"])

        _ = [attribute.lockAndHide(x, ["tx", "ty", "tz", "sx", "sy", "sz", "v"]) for x in self.cont_spineFK_A_List]
        _ = [attribute.lockAndHide(x, ["tx", "ty", "tz", "sx", "sy", "sz", "v"]) for x in self.cont_spineFK_B_List]


    def createLimb(self):
        self.createGrp()
        self.createJoints()
        self.createControllers()
        self.createRoots()
        self.createIKsetup()
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
        rPoint = om.MVector(0, 14.0, 0) * self.tMatrix
        nPoint = om.MVector(0, 21.0, 0) * self.tMatrix
        add = (nPoint - rPoint) / ((self.segments + 1) - 1)

        # Define the offset vector
        self.offsetVector = (nPoint - rPoint).normal()

        # Draw the joints & set joint side and type attributes
        for nmb in range(self.segments + 1):
            spine_jnt = cmds.joint(p=(rPoint + (add * nmb)), name="jInit_spine_%s_%i" %(self.suffix, nmb))
            # Update the guideJoints list
            self.guideJoints.append(spine_jnt)

        # set orientation of joints
        functions.orientJoints(self.guideJoints, worldUpAxis=-self.lookVector, reverseAim=self.sideMultiplier, reverseUp=self.sideMultiplier)


    def define_attributes(self):
        functions.set_joint_type(self.guideJoints[0], "SpineRoot")
        _ = [functions.set_joint_type(jnt, "Spine") for jnt in self.guideJoints[1:-1]]
        functions.set_joint_type(self.guideJoints[-1], "SpineEnd")
        cmds.setAttr("{0}.radius".format(self.guideJoints[0]), 2)
        _ = [functions.set_joint_side(jnt, self.side) for jnt in self.guideJoints]

        # ----------Mandatory---------[Start]
        root_jnt = self.guideJoints[0]
        attribute.create_global_joint_attrs(root_jnt, moduleName="%s_spine" %self.suffix, upAxis=self.upVector, mirrorAxis=self.mirrorVector, lookAxis=self.lookVector)
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