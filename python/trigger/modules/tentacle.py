from maya import cmds
import maya.api.OpenMaya as om

from trigger.library import functions, joint
from trigger.library import naming
from trigger.library import attribute
from trigger.library import api
from trigger.objects.controller import Controller

from trigger.core import filelog

log = filelog.Filelog(logname=__name__, filename="trigger_log")

LIMB_DATA = {
    "members": ["TentacleRoot", "Tentacle", "TentacleEnd"],
    "properties": [{"attr_name": "contRes",
                    "nice_name": "Ctrl_Res",
                    "attr_type": "long",
                    "min_value": 1,
                    "max_value": 9999,
                    "default_value": 5,
                    },
                   {"attr_name": "jointRes",
                    "nice_name": "Joint_Res",
                    "attr_type": "long",
                    "min_value": 1,
                    "max_value": 9999,
                    "default_value": 25,
                    },
                   {"attr_name": "deformerRes",
                    "nice_name": "Deformer_Resolution",
                    "attr_type": "long",
                    "min_value": 1,
                    "max_value": 9999,
                    "default_value": 25,
                    },
                   {"attr_name": "dropoff",
                    "nice_name": "Drop_Off",
                    "attr_type": "float",
                    "min_value": 0.1,
                    "max_value": 5.0,
                    "default_value": 1.0,
                    },
                   ],
    "multi_guide": "Tentacle",
    "sided": True,
}


class Tentacle(object):

    def __init__(self, build_data=None, inits=None, *args, **kwargs):
        super(Tentacle, self).__init__()
        if build_data:
            self.tentacleRoot = build_data.get("TentacleRoot")
            self.tentacles = (build_data.get("Tentacle"))
            self.inits = [self.tentacleRoot] + (self.tentacles)
        elif inits:
            if len(inits) < 2:
                cmds.error("Tentacle setup needs at least 2 initial joints")
                return
            self.inits = inits
        else:
            log.error("Class needs either build_data or inits to be constructed")

        # get distances

        # get positions

        self.rootPos = api.get_world_translation(self.inits[0])

        # initialize coordinates
        self.up_axis, self.mirror_axis, self.look_axis = joint.get_rig_axes(self.inits[0])

        # get the properties from the root
        self.useRefOrientation = cmds.getAttr("%s.useRefOri" % self.inits[0])
        self.controller_resolution = float(cmds.getAttr("%s.contRes" % self.inits[0]))
        self.jointRes = float(cmds.getAttr("%s.jointRes" % self.inits[0]))
        self.deformerRes = float(cmds.getAttr("%s.deformerRes" % self.inits[0]))
        self.dropoff = float(cmds.getAttr("%s.dropoff" % self.inits[0]))
        self.side = joint.get_joint_side(self.inits[0])
        self.sideMult = -1 if self.side == "R" else 1

        # initialize suffix
        self.suffix = (naming.unique_name(cmds.getAttr("%s.moduleName" % self.inits[0])))

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
        functions.align_to(self.scaleGrp, self.inits[0], position=True, rotation=False)
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

        cmds.select(deselect=True)
        self.limbPlug = cmds.joint(name="limbPlug_%s" % self.suffix, position=self.rootPos, radius=3)
        ## Make a straight line from inits joints (like in the twistSpline)
        # calculate the necessary distance for the joints

        self.totalLength = 0
        contDistances = []
        ctrlDistance = 0
        for i in range(0, len(self.inits)):
            if i == 0:
                tmin = 0
            else:
                tmin = i - 1
            currentJointLength = functions.get_distance(self.inits[i], self.inits[tmin])
            ctrlDistance = currentJointLength + ctrlDistance
            self.totalLength += currentJointLength
            # this list contains distance between each control point
            contDistances.append(ctrlDistance)
        endVc = om.MVector(self.rootPos.x, (self.rootPos.y + self.totalLength), self.rootPos.z)
        splitVc = endVc - self.rootPos

        ## Create Control Joints
        self.contJointsList = []
        cmds.select(deselect=True)
        for index in range(0, len(contDistances)):
            ctrlVc = splitVc.normal() * contDistances[index]
            place = self.rootPos + (ctrlVc)
            jnt = cmds.joint(position=place, name="jCont_tentacle_%s_%i" % (self.suffix, index), radius=5, o=(90, 0, 90))
            self.contJointsList.append(jnt)
            cmds.select(deselect=True)

        ## Create temporaray Guide Joints
        cmds.select(deselect=True)
        self.guideJoints = [cmds.joint(position=api.get_world_translation(i)) for i in self.inits]
        # orientations
        if not self.useRefOrientation:
            joint.orient_joints(self.guideJoints, world_up_axis=(self.up_axis), up_axis=(0, 1, 0),
                                reverse_aim=self.sideMult,
                                reverse_up=self.sideMult)
        else:
            for x in range(len(self.guideJoints)):
                functions.align_to(self.guideJoints[x], self.inits[x], position=True, rotation=True)
                cmds.makeIdentity(self.guideJoints[x], apply=True)

        cmds.select(deselect=True)
        self.wrapScaleJoint = cmds.joint(name="jWrapScale_{0}".format(self.suffix))

        cmds.parent(self.contJointsList, self.scaleGrp)
        cmds.parent(self.wrapScaleJoint, self.scaleGrp)

        attribute.drive_attrs("%s.rigVis" % self.scaleGrp, ["%s.v" % x for x in self.contJointsList])

        cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % self.wrapScaleJoint)

    def createControllers(self):

        ## specialController
        iconScale = functions.get_distance(self.inits[0], self.inits[1]) / 3
        self.cont_special = Controller(name="{}_tentacleSP_cont".format(self.suffix),
                                       shape="Looper",
                                       scale=(iconScale, iconScale, iconScale),
                                       side=self.side,
                                       tier="primary"
                                       )
        self.controllers.append(self.cont_special)
        functions.align_and_aim(self.cont_special.name, target_list=[self.inits[0]], aim_target_list=[self.inits[-1]],
                                up_vector=self.up_axis, rotate_offset=(90, 0, 0))
        move_pos = om.MVector(self.up_axis) * (iconScale * 2.0)
        # cmds.move(self.cont_special, om.MVector(self.up_axis) *(iconScale*2), r=True)
        cmds.move(move_pos[0], move_pos[1], move_pos[2], self.cont_special.name, relative=True)

        cont_special_ORE = self.cont_special.add_offset("ORE")

        ## seperator - curl
        cmds.addAttr(self.cont_special.name, shortName="curlSeperator", attributeType="enum", enumName="----------",
                     keyable=True)
        cmds.setAttr("%s.curlSeperator" % self.cont_special.name, lock=True)

        cmds.addAttr(self.cont_special.name, shortName="curl", longName="Curl", defaultValue=0.0, minValue=-10.0,
                     maxValue=10.0, attributeType="float",
                     keyable=True)
        cmds.addAttr(self.cont_special.name, shortName="curlSize", longName="Curl_Size", defaultValue=1.0,
                     attributeType="float",
                     keyable=True)

        cmds.addAttr(self.cont_special.name, shortName="curlAngle", longName="Curl_Angle", defaultValue=1.0,
                     attributeType="float",
                     keyable=True)
        cmds.addAttr(self.cont_special.name, shortName="curlDirection", longName="Curl_Direction", defaultValue=0.0,
                     attributeType="float",
                     keyable=True)

        cmds.addAttr(self.cont_special.name, shortName="curlShift", longName="Curl_Shift", defaultValue=0.0,
                     attributeType="float",
                     keyable=True)

        ## seperator - twist
        cmds.addAttr(self.cont_special.name, shortName="twistSeperator", attributeType="enum", enumName="----------",
                     keyable=True)
        cmds.setAttr("%s.twistSeperator" % self.cont_special.name, lock=True)

        cmds.addAttr(self.cont_special.name, shortName="twistAngle", longName="Twist_Angle", defaultValue=0.0,
                     attributeType="float",
                     keyable=True)
        cmds.addAttr(self.cont_special.name, shortName="twistSlide", longName="Twist_Slide", defaultValue=0.0,
                     attributeType="float",
                     keyable=True)
        cmds.addAttr(self.cont_special.name, shortName="twistArea", longName="Twist_Area", defaultValue=1.0,
                     attributeType="float",
                     keyable=True)

        ## seperator - sine
        cmds.addAttr(self.cont_special.name, shortName="sineSeperator", attributeType="enum", enumName="----------",
                     keyable=True)
        cmds.setAttr("%s.sineSeperator" % self.cont_special.name, lock=True)
        cmds.addAttr(self.cont_special.name, shortName="sineAmplitude", longName="Sine_Amplitude", defaultValue=0.0,
                     attributeType="float",
                     keyable=True)
        cmds.addAttr(self.cont_special.name, shortName="sineWavelength", longName="Sine_Wavelength", defaultValue=1.0,
                     attributeType="float",
                     keyable=True)
        cmds.addAttr(self.cont_special.name, shortName="sineDropoff", longName="Sine_Dropoff", defaultValue=0.0,
                     attributeType="float",
                     keyable=True)
        cmds.addAttr(self.cont_special.name, shortName="sineSlide", longName="Sine_Slide", defaultValue=0.0,
                     attributeType="float",
                     keyable=True)
        cmds.addAttr(self.cont_special.name, shortName="sineArea", longName="Sine_area", defaultValue=1.0,
                     attributeType="float",
                     keyable=True)
        cmds.addAttr(self.cont_special.name, shortName="sineDirection", longName="Sine_Direction", defaultValue=0.0,
                     attributeType="float",
                     keyable=True)

        cmds.addAttr(self.cont_special.name, shortName="sineAnimate", longName="Sine_Animate", defaultValue=0.0,
                     attributeType="float",
                     keyable=True)

        self.cont_fk_list = []
        self.cont_twk_list = []

        for j in range(len(self.guideJoints)):
            s = cmds.getAttr("%s.tx" % self.guideJoints[j]) / 3
            s = iconScale if s == 0 else s
            scale_twk = (s, s, s)
            # cont_twk, dmp = icon.create_icon("Circle", icon_name="%s_tentacleTweak%i_cont" % (self.suffix, j),
            #                                 scale=scale_twk, normal=self.mirror_axis)
            cont_twk = Controller(name="{}_tentacleTweak{}_cont".format(self.suffix, j),
                                  shape="Circle",
                                  scale=scale_twk,
                                  normal=self.mirror_axis,
                                  side=self.side,
                                  tier="primary"
                                  )

            functions.align_to_alter(cont_twk.name, self.guideJoints[j], mode=2)
            cont_twk_off = cont_twk.add_offset("OFF")
            cont_twk_ore = cont_twk.add_offset("ORE")
            self.cont_twk_list.append(cont_twk)

            scale_fk = (s * 1.2, s * 1.2, s * 1.2)
            # cont_fk, _ = icon.create_icon("Ngon", icon_name="%s_tentacleFK%i_cont" % (self.suffix, j), scale=scale_fk,
            #                              normal=self.mirror_axis)
            cont_fk = Controller(name="{}_tentacleFK{}_cont".format(self.suffix, j),
                                shape="Ngon",
                                scale=scale_fk,
                                normal=self.mirror_axis,
                                side=self.side,
                                tier="primary"
                                )
            functions.align_to_alter(cont_fk.name, self.guideJoints[j], mode=2)
            cont_fk_off = cont_fk.add_offset("OFF")
            cont_fk_ore = cont_fk.add_offset("ORE")
            self.cont_fk_list.append(cont_fk)

            cmds.parent(cont_twk_off, cont_fk.name)
            if not j == 0:
                cmds.parent(cont_fk_off, self.cont_fk_list[j - 1].name)
            else:
                cmds.parent(cont_fk_off, self.scaleGrp)

        self.controllers.extend(self.cont_fk_list)
        self.controllers.extend(self.cont_twk_list)

        cmds.parent(cont_special_ORE, self.cont_fk_list[0].name)

        attribute.drive_attrs("%s.contVis" % self.scaleGrp, ["%s.v" % x.name for x in self.cont_twk_list])
        attribute.drive_attrs("%s.contVis" % self.scaleGrp, ["%s.v" % x.name for x in self.cont_fk_list])

    def createRoots(self):
        pass

    def createIKsetup(self):
        ## Create the Base Nurbs Plane (npBase)
        ribbonLength = functions.get_distance(self.contJointsList[0], self.contJointsList[-1])

        npBase = cmds.nurbsPlane(axis=(0, 1, 0), patchesU=int(self.controller_resolution), patchesV=1, width=ribbonLength, lengthRatio=(1.0 / ribbonLength),
                                 name="npBase_%s" % self.suffix)[0]
        cmds.rebuildSurface(npBase, constructionHistory=True, replaceOriginal=True, rebuildType=0, endKnots=1, keepRange=2, keepControlPoints=False, keepCorners=False, spansU=5, degreeU=3, spansV=1, degreeV=1, tolerance=0, fitRebuild=0,
                            direction=1)
        functions.align_and_aim(npBase, target_list=[self.contJointsList[0], self.contJointsList[-1]],
                                aim_target_list=[self.contJointsList[-1]], up_vector=self.up_axis)

        ## Duplicate the Base Nurbs Plane as joint Holder (npJDefHolder)
        npJdefHolder = cmds.nurbsPlane(axis=(0, 1, 0), patchesU=int(self.deformerRes), patchesV=1, width=ribbonLength, lengthRatio=(1.0 / ribbonLength),
                                       name="npJDefHolder_%s" % self.suffix)[0]
        cmds.rebuildSurface(npJdefHolder, constructionHistory=True, replaceOriginal=True, rebuildType=0, endKnots=1, keepRange=2, keepControlPoints=False, keepCorners=False, spansU=5, degreeU=3, spansV=1, degreeV=1, tolerance=0,
                            fitRebuild=0,
                            direction=1)
        functions.align_and_aim(npJdefHolder, target_list=[self.contJointsList[0], self.contJointsList[-1]],
                                aim_target_list=[self.contJointsList[-1]],
                                up_vector=self.up_axis)

        ## Create the follicles on the npJDefHolder
        npJdefHolderShape = functions.get_shapes(npJdefHolder)[0]
        follicleList = []
        for i in range(0, int(self.jointRes)):
            follicle = cmds.createNode('follicle', name="follicle_{0}{1}".format(self.suffix, str(i)))
            follicle_transform = functions.get_parent(follicle)
            cmds.connectAttr("%s.local" % npJdefHolderShape, "%s.inputSurface" % follicle)
            cmds.connectAttr("%s.worldMatrix[0]" % npJdefHolderShape, "%s.inputWorldMatrix" % follicle)
            cmds.connectAttr("%s.outRotate" % follicle, "%s.rotate" % follicle_transform)
            cmds.connectAttr("%s.outTranslate" % follicle, "%s.translate" % follicle_transform)
            cmds.setAttr("%s.parameterV" % follicle, 0.5)
            cmds.setAttr("%s.parameterU" % follicle,
                         ((1 / self.jointRes) + (i / self.jointRes) - ((1 / self.jointRes) / 2)))
            attribute.lock_and_hide(follicle_transform, ["tx", "ty", "tz", "rx", "ry", "rz"], hide=False)
            follicleList.append(follicle)

            defJ = cmds.joint(name="%s_%i_jDef" % (self.suffix, i))
            cmds.joint(defJ, exists=True, zeroScaleOrient=True, orientJoint='zxy')
            self.deformerJoints.append(defJ)
            self.sockets.append(defJ)
            cmds.parent(follicle_transform, self.nonScaleGrp)
            cmds.scaleConstraint(self.scaleGrp, follicle_transform, maintainOffset=True)

        # create follicles for scaling calculations
        follicle_sca_list = []
        counter = 0
        for index in range(int(self.jointRes)):
            s_follicle = cmds.createNode('follicle', name="follicleSCA_{0}{1}".format(self.suffix, index))
            s_follicle_transform = functions.get_parent(s_follicle)
            cmds.connectAttr("%s.local" % npJdefHolderShape, "%s.inputSurface" % s_follicle)
            cmds.connectAttr("%s.worldMatrix[0]" % npJdefHolderShape, "%s.inputWorldMatrix" % s_follicle)
            cmds.connectAttr("%s.outRotate" % s_follicle, "%s.rotate" % s_follicle_transform)
            cmds.connectAttr("%s.outTranslate" % s_follicle, "%s.translate" % s_follicle_transform)

            cmds.setAttr("%s.parameterV" % s_follicle, 0.0)
            cmds.setAttr("%s.parameterU" % s_follicle,
                         ((1 / self.jointRes) + (index / self.jointRes) - ((1 / self.jointRes) / 2)))
            attribute.lock_and_hide(s_follicle_transform, ["tx", "ty", "tz", "rx", "ry", "rz"], hide=False)
            follicle_sca_list.append(s_follicle)
            cmds.parent(s_follicle_transform, self.nonScaleGrp)
            # create distance node
            distNode = cmds.createNode("distanceBetween", name="fDistance_{0}{1}".format(self.suffix, index))
            cmds.connectAttr("%s.outTranslate" % follicleList[counter], "%s.point1" % distNode)
            cmds.connectAttr("%s.outTranslate" % s_follicle, "%s.point2" % distNode)

            multiplier = cmds.createNode("multDoubleLinear", name="fMult_{0}{1}".format(self.suffix, index))
            cmds.connectAttr("%s.distance" % distNode, "%s.input1" % multiplier)
            cmds.setAttr("%s.input2" % multiplier, 2)

            global_divide = cmds.createNode("multiplyDivide", name="fGlobDiv_{0}{1}".format(self.suffix, index))
            cmds.setAttr("%s.operation" % global_divide, 2)
            cmds.connectAttr("%s.output" % multiplier, "%s.input1X" % global_divide)
            cmds.connectAttr("%s.scaleX" % self.scaleGrp, "%s.input2X" % global_divide)

            cmds.connectAttr("%s.outputX" % global_divide, "%s.scaleX" % self.deformerJoints[counter])
            cmds.connectAttr("%s.outputX" % global_divide, "%s.scaleY" % self.deformerJoints[counter])
            cmds.connectAttr("%s.outputX" % global_divide, "%s.scaleZ" % self.deformerJoints[counter])
            counter += 1

        ## Duplicate it 3 more times for deformation targets (npDeformers, npTwist, npSine)
        npDeformers = cmds.duplicate(npJdefHolder, name="npDeformers_%s" % self.suffix)[0]
        cmds.move(0, self.totalLength / 2, 0, npDeformers)
        cmds.rotate(0, 0, 90, npDeformers, )

        ## Create Blendshape node between np_jDefHolder and deformation targets
        npBlend = cmds.blendShape(npDeformers, npJdefHolder, w=(0, 1))

        ## Wrap npjDefHolder to the Base Plane
        npWrap, npWrapGeo = self.createWrap(npBase, npJdefHolder, weightThreshold=0.0, maxDistance=50,
                                            autoWeightThreshold=False)
        maxDistanceMult = cmds.createNode("multDoubleLinear", name="npWrap_{0}".format(self.suffix))
        cmds.connectAttr("%s.scaleX" % self.scaleGrp, "%s.input1" % maxDistanceMult)
        cmds.setAttr("%s.input2" % maxDistanceMult, 50)
        cmds.connectAttr("%s.output" % maxDistanceMult, "%s.maxDistance" % npWrap)

        ## make the Wrap node Scale-able with the rig
        cmds.skinCluster(self.wrapScaleJoint, npWrapGeo, tsb=True)

        ## Create skin cluster
        cmds.skinCluster(self.contJointsList, npBase, tsb=True, dropoffRate=self.dropoff)

        ## CURL DEFORMER
        curlDeformer = cmds.nonLinear(npDeformers, type='bend', curvature=1500)
        curlLoc = cmds.spaceLocator(name="curlLoc{0}".format(self.suffix))[0]
        cmds.parent(curlDeformer[1], curlLoc)
        cmds.setAttr("%s.lowBound" % curlDeformer[0], -1)
        cmds.setAttr("%s.highBound" % curlDeformer[0], 0)

        cmds.setDrivenKeyframe("%s.curvature" % curlDeformer[0], currentDriver="%s.curl" % self.cont_special.name,
                               value=0.0, driverValue=0.0,
                               inTangentType='linear', outTangentType='linear')
        cmds.setDrivenKeyframe("%s.curvature" % curlDeformer[0], currentDriver="%s.curl" % self.cont_special.name,
                               value=1500.0, driverValue=0.01,
                               inTangentType='linear', outTangentType='linear')
        cmds.setDrivenKeyframe("%s.curvature" % curlDeformer[0], currentDriver="%s.curl" % self.cont_special.name,
                               value=-1500.0, driverValue=-0.01,
                               inTangentType='linear', outTangentType='linear')

        cmds.setDrivenKeyframe("%s.ty" % curlDeformer[1], currentDriver="%s.curl" % self.cont_special.name, value=0.0,
                               driverValue=10.0,
                               inTangentType='linear', outTangentType='linear')
        cmds.setDrivenKeyframe("%s.ty" % curlDeformer[1], currentDriver="%s.curl" % self.cont_special.name, value=0.0,
                               driverValue=-10.0,
                               inTangentType='linear', outTangentType='linear')
        cmds.setDrivenKeyframe(["%s.sx" % curlDeformer[1], "%s.sy" % curlDeformer[1], "%s.sz" % curlDeformer[1]],
                               currentDriver="%s.curl" % self.cont_special.name, value=(self.totalLength * 2),
                               driverValue=10.0, inTangentType='linear',
                               outTangentType='linear')
        cmds.setDrivenKeyframe(["%s.sx" % curlDeformer[1], "%s.sy" % curlDeformer[1], "%s.sz" % curlDeformer[1]],
                               currentDriver="%s.curl" % self.cont_special.name, value=(self.totalLength * 2),
                               driverValue=-10.0, inTangentType='linear',
                               outTangentType='linear')
        cmds.setDrivenKeyframe("%s.rz" % curlDeformer[1], currentDriver="%s.curl" % self.cont_special.name, value=4.0,
                               driverValue=10.0,
                               inTangentType='linear', outTangentType='linear')
        cmds.setDrivenKeyframe("%s.rz" % curlDeformer[1], currentDriver="%s.curl" % self.cont_special.name, value=-4.0,
                               driverValue=-10.0,
                               inTangentType='linear', outTangentType='linear')
        cmds.setDrivenKeyframe("%s.ty" % curlDeformer[1], currentDriver="%s.curl" % self.cont_special.name,
                               value=self.totalLength, driverValue=0.0,
                               inTangentType='linear', outTangentType='linear')
        cmds.setDrivenKeyframe(["%s.sx" % curlDeformer[1], "%s.sy" % curlDeformer[1], "%s.sz" % curlDeformer[1]],
                               currentDriver="%s.curl" % self.cont_special.name, value=(self.totalLength / 2),
                               driverValue=0.0, inTangentType='linear',
                               outTangentType='linear')
        cmds.setDrivenKeyframe("%s.rz" % curlDeformer[1], currentDriver="%s.curl" % self.cont_special.name, value=6.0,
                               driverValue=0.01,
                               inTangentType='linear', outTangentType='linear')
        cmds.setDrivenKeyframe("%s.rz" % curlDeformer[1], currentDriver="%s.curl" % self.cont_special.name, value=-6.0,
                               driverValue=-0.01,
                               inTangentType='linear', outTangentType='linear')

        ## create curl size multipliers

        curlSizeMultX = cmds.createNode("multDoubleLinear", name="curlSizeMultX_{0}".format(self.suffix))
        curlSizeMultY = cmds.createNode("multDoubleLinear", name="curlSizeMultY_{0}".format(self.suffix))
        curlSizeMultZ = cmds.createNode("multDoubleLinear", name="curlSizeMultZ_{0}".format(self.suffix))

        curlAngleMultZ = cmds.createNode("multDoubleLinear", name="curlAngleMultZ_{0}".format(self.suffix))

        curlShiftAdd = cmds.createNode("plusMinusAverage", name="curlAddShift_{0}".format(self.suffix))
        cmds.connectAttr("%s.curlShift" % self.cont_special.name, "%s.input1D[0]" % curlShiftAdd)
        cmds.setAttr("%s.input1D[1]" % curlShiftAdd, 180)

        cmds.connectAttr("%s.output1D" % curlShiftAdd, "%s.rx" % curlDeformer[1])
        cmds.connectAttr("%s.curlSize" % self.cont_special.name, "%s.input1" % curlSizeMultX)
        cmds.connectAttr("%s.curlSize" % self.cont_special.name, "%s.input1" % curlSizeMultY)
        cmds.connectAttr("%s.curlSize" % self.cont_special.name, "%s.input1" % curlSizeMultZ)
        cmds.connectAttr("%s.curlAngle" % self.cont_special.name, "%s.input1" % curlAngleMultZ)

        cmds.connectAttr("%s.output" % cmds.listConnections("%s.sx" % curlDeformer[1])[0], "%s.input2" % curlSizeMultX)
        cmds.connectAttr("%s.output" % cmds.listConnections("%s.sy" % curlDeformer[1])[0], "%s.input2" % curlSizeMultY)
        cmds.connectAttr("%s.output" % cmds.listConnections("%s.sz" % curlDeformer[1])[0], "%s.input2" % curlSizeMultZ)
        cmds.connectAttr("%s.output" % cmds.listConnections("%s.rz" % curlDeformer[1])[0], "%s.input2" % curlAngleMultZ)

        cmds.connectAttr("%s.output" % curlSizeMultX, "%s.sx" % curlDeformer[1], force=True)
        cmds.connectAttr("%s.output" % curlSizeMultY, "%s.sy" % curlDeformer[1], force=True)
        cmds.connectAttr("%s.output" % curlSizeMultZ, "%s.sz" % curlDeformer[1], force=True)
        cmds.connectAttr("%s.output" % curlAngleMultZ, "%s.rz" % curlDeformer[1], force=True)
        cmds.connectAttr("%s.curlDirection" % self.cont_special.name, "%s.ry" % curlLoc)

        ## TWIST DEFORMER
        twistDeformer = cmds.nonLinear(npDeformers, type='twist')
        cmds.rotate(0, 0, 0, twistDeformer[1])
        twistLoc = cmds.spaceLocator(name="twistLoc_{0}".format(self.suffix))[0]
        cmds.parent(twistDeformer[1], twistLoc)

        ## make connections:
        cmds.connectAttr("%s.twistAngle" % self.cont_special.name, "%s.endAngle" % twistDeformer[0], force=True)
        cmds.connectAttr("%s.twistSlide" % self.cont_special.name, "%s.translateY" % twistLoc)
        cmds.connectAttr("%s.twistArea" % self.cont_special.name, "%s.scaleY" % twistLoc)

        ## SINE DEFORMER
        sineDeformer = cmds.nonLinear(npDeformers, type='sine')
        cmds.rotate(0, 0, 0, sineDeformer[1])
        sineLoc = cmds.spaceLocator(name="sineLoc_{0}".format(self.suffix))[0]
        cmds.parent(sineDeformer[1], sineLoc)

        ## make connections:
        cmds.connectAttr("%s.sineAmplitude" % self.cont_special.name, "%s.amplitude" % sineDeformer[0], force=True)
        cmds.connectAttr("%s.sineWavelength" % self.cont_special.name, "%s.wavelength" % sineDeformer[0], force=True)
        cmds.connectAttr("%s.sineDropoff" % self.cont_special.name, "%s.dropoff" % sineDeformer[0], force=True)
        cmds.connectAttr("%s.sineAnimate" % self.cont_special.name, "%s.offset" % sineDeformer[0], force=True)

        cmds.connectAttr("%s.sineSlide" % self.cont_special.name, "%s.translateY" % sineLoc)
        cmds.connectAttr("%s.sineArea" % self.cont_special.name, "%s.scaleY" % sineLoc)
        cmds.connectAttr("%s.sineDirection" % self.cont_special.name, "%s.rotateY" % sineLoc)

        # WHY THIS OFFSET IS NECESSARY? TRY TO GED RID OF
        offsetVal = (0, 180, 0) if self.sideMult == -1 else (0, 0, 0)
        for j in range(len(self.guideJoints)):
            functions.align_to_alter(self.contJointsList[j], self.guideJoints[j], mode=2)
            cmds.pointConstraint(self.cont_twk_list[j].name, self.contJointsList[j], maintainOffset=False)
            cmds.orientConstraint(self.cont_twk_list[j].name, self.contJointsList[j], maintainOffset=False, offset=offsetVal)

            cmds.scaleConstraint(self.cont_twk_list[j].name, self.contJointsList[j], maintainOffset=False)

        cmds.parent(npBase, self.nonScaleGrp)
        cmds.parent(npDeformers, self.nonScaleGrp)
        cmds.parent(curlLoc, self.nonScaleGrp)
        cmds.parent(twistLoc, self.nonScaleGrp)
        cmds.parent(sineLoc, self.nonScaleGrp)
        cmds.parent(npWrapGeo, self.nonScaleGrp)
        cmds.parent(npJdefHolder, self.scaleGrp)

        nodesRigVis = [npBase, npJdefHolder, npDeformers, sineLoc, twistLoc, curlLoc]
        attribute.drive_attrs("%s.rigVis" % self.scaleGrp, ["%s.v" % x for x in nodesRigVis])
        attribute.drive_attrs("%s.rigVis" % self.scaleGrp, ["%s.v" % x for x in follicle_sca_list])
        attribute.drive_attrs("%s.rigVis" % self.scaleGrp, ["%s.v" % x for x in follicleList])

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
        cmds.parentConstraint(self.limbPlug, self.scaleGrp, maintainOffset=False)
        cmds.setAttr("%s.rigVis" % self.scaleGrp, 0)

        _ = [x.lock(["sx", "sy", "sz"]) for x in self.cont_fk_list]
        self.scaleConstraints = [self.scaleGrp]

        cmds.delete(self.guideJoints)

        for cont in self.controllers:
            cont.set_defaults()

    def createLimb(self):
        self.createGrp()
        self.createJoints()
        self.createControllers()
        self.createRoots()
        self.createIKsetup()
        self.roundUp()

    def createWrap(self, *args, **kwargs):
        ## TODO: refine the function and move to the library
        influence = args[0]
        surface = args[1]

        shapes = cmds.listRelatives(influence, shapes=True)
        influenceShape = shapes[0]

        shapes = cmds.listRelatives(surface, shapes=True)
        surfaceShape = shapes[0]

        # create wrap deformer
        weightThreshold = kwargs.get('weightThreshold', 0.0)
        maxDistance = kwargs.get('maxDistance', 1.0)
        exclusiveBind = kwargs.get('exclusiveBind', False)
        autoWeightThreshold = kwargs.get('autoWeightThreshold', True)
        falloffMode = kwargs.get('falloffMode', 0)

        wrapData = cmds.deformer(surface, type='wrap')
        wrapNode = wrapData[0]

        cmds.setAttr(wrapNode + '.weightThreshold', weightThreshold)
        cmds.setAttr(wrapNode + '.maxDistance', maxDistance)
        cmds.setAttr(wrapNode + '.exclusiveBind', exclusiveBind)
        cmds.setAttr(wrapNode + '.autoWeightThreshold', autoWeightThreshold)
        cmds.setAttr(wrapNode + '.falloffMode', falloffMode)

        cmds.connectAttr(surface + '.worldMatrix[0]', wrapNode + '.geomMatrix')

        # add influence
        duplicateData = cmds.duplicate(influence, name=influence + 'Base')
        base = duplicateData[0]
        shapes = cmds.listRelatives(base, shapes=True)
        baseShape = shapes[0]
        cmds.hide(base)

        # create dropoff attr if it doesn't exist
        if not cmds.attributeQuery('dropoff', node=influence, exists=True):
            cmds.addAttr(influence, shortName='dr', longName='dropoff', defaultValue=4.0, minValue=0.0, maxValue=20.0)
            cmds.setAttr(influence + '.dr', keyable=True)

        # if type mesh
        if cmds.nodeType(influenceShape) == 'mesh':
            # create smoothness attr if it doesn't exist
            if not cmds.attributeQuery('smoothness', node=influence, exists=True):
                cmds.addAttr(influence, shortName='smt', longName='smoothness', defaultValue=0.0, minValue=0.0)
                cmds.setAttr(influence + '.smt', keyable=True)

            # create the inflType attr if it doesn't exist
            if not cmds.attributeQuery('inflType', node=influence, exists=True):
                cmds.addAttr(influence, attributeType='short', shortName='ift', longName='inflType', defaultValue=2, minValue=1, maxValue=2)

            cmds.connectAttr(influenceShape + '.worldMesh', wrapNode + '.driverPoints[0]')
            cmds.connectAttr(baseShape + '.worldMesh', wrapNode + '.basePoints[0]')
            cmds.connectAttr(influence + '.inflType', wrapNode + '.inflType[0]')
            cmds.connectAttr(influence + '.smoothness', wrapNode + '.smoothness[0]')

        # if type nurbsCurve or nurbsSurface
        if cmds.nodeType(influenceShape) == 'nurbsCurve' or cmds.nodeType(influenceShape) == 'nurbsSurface':
            # create the wrapSamples attr if it doesn't exist
            if not cmds.attributeQuery('wrapSamples', node=influence, exists=True):
                cmds.addAttr(influence, attributeType='short', shortName='wsm', longName='wrapSamples', defaultValue=10, minValue=1)
                cmds.setAttr(influence + '.wsm', keyable=True)

            cmds.connectAttr(influenceShape + '.ws', wrapNode + '.driverPoints[0]')
            cmds.connectAttr(baseShape + '.ws', wrapNode + '.basePoints[0]')
            cmds.connectAttr(influence + '.wsm', wrapNode + '.nurbsSamples[0]')

        cmds.connectAttr(influence + '.dropoff', wrapNode + '.dropoff[0]')
        # I want to return a pyNode object for the wrap deformer.
        # I do not see the reason to rewrite the code here into pymel.
        return wrapNode, base


class Guides(object):
    def __init__(self, side="L", suffix="tentacle", segments=None, tMatrix=None, upVector=(0, 1, 0),
                 mirrorVector=(1, 0, 0), lookVector=(0, 0, 1), *args, **kwargs):
        super(Guides, self).__init__()
        # fool check

        # -------Mandatory------[Start]
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
        # -------Mandatory------[End]

    def draw_joints(self):
        rPointTentacle = om.MVector(0, 14, 0) * self.tMatrix
        if self.side == "C":
            # Guide joint positions for limbs with no side orientation
            nPointTentacle = om.MVector(0, 14, 10) * self.tMatrix
        else:
            # Guide joint positions for limbs with sides
            nPointTentacle = om.MVector(10 * self.sideMultiplier, 14, 0) * self.tMatrix

        addTentacle = (nPointTentacle - rPointTentacle) / ((self.segments + 1) - 1)

        # Define the offset vector
        self.offsetVector = (nPointTentacle - rPointTentacle).normal()

        # Draw the joints
        for seg in range(self.segments + 1):
            tentacle_jnt = cmds.joint(position=(rPointTentacle + (addTentacle * seg)),
                                      name="jInit_tentacle_%s_%i" % (self.suffix, seg))
            # Update the guideJoints list
            self.guideJoints.append(tentacle_jnt)

        # set orientation of joints
        joint.orient_joints(self.guideJoints, world_up_axis=self.upVector, up_axis=(0, 1, 0),
                            reverse_aim=self.sideMultiplier, reverse_up=self.sideMultiplier)

    def define_attributes(self):
        # set joint side and type attributes
        joint.set_joint_type(self.guideJoints[0], "TentacleRoot")
        _ = [joint.set_joint_type(jnt, "Tentacle") for jnt in self.guideJoints[1:]]
        _ = [joint.set_joint_side(jnt, self.side) for jnt in self.guideJoints]

        # ----------Mandatory---------[Start]
        root_jnt = self.guideJoints[0]
        attribute.create_global_joint_attrs(root_jnt, moduleName="%s_Tentacle" % self.side, upAxis=self.upVector,
                                            mirrorAxis=self.mirrorVector,
                                            lookAxis=self.lookVector)
        # ----------Mandatory---------[End]

        for attr_dict in LIMB_DATA["properties"]:
            attribute.create_attribute(root_jnt, attr_dict)

    def createGuides(self):
        self.draw_joints()
        self.define_attributes()

    def convertJoints(self, joints_list):
        if len(joints_list) < 2:
            log.warning("Define or select at least 2 joints for Tentacle Guide conversion. Skipping")
            return
        self.guideJoints = joints_list
        self.define_attributes()
