from maya import cmds
import maya.api.OpenMaya as om

from trigger.library import functions
from trigger.library import controllers as ic
# from trigger.library import ribbon as rc
# from trigger.library import twist_spline as twistSpline

import maya.cmds as cmds

from trigger.core import logger

FEEDBACK = logger.Logger(__name__)

LIMB_DATA = {
        "members":["TentacleRoot", "Tentacle", "TentacleEnd"],
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
            FEEDBACK.throw_error("Class needs either build_data or inits to be constructed")

        # get distances

        # get positions

        self.rootPos = functions.getWorldTranslation(self.inits[0])

        # initialize coordinates
        self.up_axis, self.mirror_axis, self.look_axis = functions.getRigAxes(self.inits[0])

        # get the properties from the root
        self.useRefOrientation = cmds.getAttr("%s.useRefOri" % self.inits[0])
        self.contRes = float(cmds.getAttr("%s.contRes" % self.inits[0]))
        self.jointRes = float(cmds.getAttr("%s.jointRes" % self.inits[0]))
        self.deformerRes = float(cmds.getAttr("%s.deformerRes" % self.inits[0]))
        self.dropoff = float(cmds.getAttr("%s.dropoff" % self.inits[0]))
        self.side = functions.get_joint_side(self.inits[0])
        self.sideMult = -1 if self.side == "R" else 1

        # initialize suffix
        # self.suffix = (extra.uniqueName("limbGrp_%s" % suffix)).replace("limbGrp_", "")
        # self.suffix = (extra.uniqueName(suffix))
        self.suffix = (functions.uniqueName(cmds.getAttr("%s.moduleName" % self.inits[0])))


        # scratch variables
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
        cmds.setAttr("%s.contVis" % self.scaleGrp, cb=True)
        cmds.setAttr("%s.jointVis" % self.scaleGrp, cb=True)
        cmds.setAttr("%s.rigVis" % self.scaleGrp, cb=True)

        cmds.parent(self.scaleGrp, self.limbGrp)
        cmds.parent(self.nonScaleGrp, self.limbGrp)

    def createJoints(self):

        cmds.select(d=True)
        self.limbPlug = cmds.joint(name="limbPlug_%s" % self.suffix, p=self.rootPos, radius=3)
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
            currentJointLength = functions.getDistance(self.inits[i], self.inits[tmin])
            ctrlDistance = currentJointLength + ctrlDistance
            self.totalLength += currentJointLength
            # this list contains distance between each control point
            contDistances.append(ctrlDistance)
        endVc = om.MVector(self.rootPos.x, (self.rootPos.y + self.totalLength), self.rootPos.z)
        splitVc = endVc - self.rootPos

        ## Create Control Joints
        self.contJointsList = []
        cmds.select(d=True)
        for index in range(0, len(contDistances)):
            ctrlVc = splitVc.normal() * contDistances[index]
            place = self.rootPos + (ctrlVc)
            jnt = cmds.joint(p=place, name="jCont_tentacle_%s_%i" % (self.suffix, index), radius=5, o=(90, 0, 90))
            self.contJointsList.append(jnt)
            cmds.select(d=True)

        ## Create temporaray Guide Joints
        cmds.select(d=True)
        self.guideJoints = [cmds.joint(p=functions.getWorldTranslation(i)) for i in self.inits]
        # orientations
        if not self.useRefOrientation:
            functions.orientJoints(self.guideJoints, worldUpAxis=(self.up_axis), upAxis=(0, 1, 0), reverseAim=self.sideMult,
                                   reverseUp=self.sideMult)
        else:
            for x in range(len(self.guideJoints)):
                functions.alignTo(self.guideJoints[x], self.inits[x], position=True, rotation=True)
                cmds.makeIdentity(self.guideJoints[x], a=True)

        cmds.select(d=True)
        self.wrapScaleJoint = cmds.joint(name="jWrapScale_{0}".format(self.suffix))

        cmds.parent(self.contJointsList, self.scaleGrp)
        cmds.parent(self.wrapScaleJoint, self.scaleGrp)

        # map(lambda x: cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % x), self.contJointsList)
        functions.drive_attrs("%s.rigVis" % self.scaleGrp, ["%s.v" % x for x in self.contJointsList])

        cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % self.wrapScaleJoint)

    def createControllers(self):

        icon = ic.Icon()
        ## specialController
        iconScale = functions.getDistance(self.inits[0], self.inits[1]) / 3
        self.cont_special, dmp = icon.createIcon("Looper", iconName="tentacleSP_%s_cont" % self.suffix,
                                                 scale=(iconScale, iconScale, iconScale))
        functions.alignAndAim(self.cont_special, targetList=[self.inits[0]], aimTargetList=[self.inits[-1]],
                              upVector=self.up_axis, rotateOff=(90, 0, 0))
        move_pos = om.MVector(self.up_axis) * (iconScale * 2.0)
        # cmds.move(self.cont_special, om.MVector(self.up_axis) *(iconScale*2), r=True)
        cmds.move(move_pos[0], move_pos[1], move_pos[2], self.cont_special, r=True)

        cont_special_ORE = functions.createUpGrp(self.cont_special, "ORE")

        ## seperator - curl
        cmds.addAttr(self.cont_special, shortName="curlSeperator", at="enum", en="----------", k=True)
        cmds.setAttr("%s.curlSeperator" % self.cont_special, lock=True)

        cmds.addAttr(self.cont_special, shortName="curl", longName="Curl", defaultValue=0.0, minValue=-10.0,
                     maxValue=10.0, at="float",
                     k=True)
        cmds.addAttr(self.cont_special, shortName="curlSize", longName="Curl_Size", defaultValue=1.0, at="float",
                     k=True)

        cmds.addAttr(self.cont_special, shortName="curlAngle", longName="Curl_Angle", defaultValue=1.0, at="float",
                     k=True)
        cmds.addAttr(self.cont_special, shortName="curlDirection", longName="Curl_Direction", defaultValue=0.0,
                     at="float",
                     k=True)

        cmds.addAttr(self.cont_special, shortName="curlShift", longName="Curl_Shift", defaultValue=0.0, at="float",
                     k=True)

        ## seperator - twist
        cmds.addAttr(self.cont_special, shortName="twistSeperator", at="enum", en="----------", k=True)
        cmds.setAttr("%s.twistSeperator" % self.cont_special, lock=True)

        cmds.addAttr(self.cont_special, shortName="twistAngle", longName="Twist_Angle", defaultValue=0.0, at="float",
                     k=True)
        cmds.addAttr(self.cont_special, shortName="twistSlide", longName="Twist_Slide", defaultValue=0.0, at="float",
                     k=True)
        cmds.addAttr(self.cont_special, shortName="twistArea", longName="Twist_Area", defaultValue=1.0, at="float",
                     k=True)

        ## seperator - sine
        cmds.addAttr(self.cont_special, shortName="sineSeperator", at="enum", en="----------", k=True)
        cmds.setAttr("%s.sineSeperator" % self.cont_special, lock=True)
        cmds.addAttr(self.cont_special, shortName="sineAmplitude", longName="Sine_Amplitude", defaultValue=0.0,
                     at="float",
                     k=True)
        cmds.addAttr(self.cont_special, shortName="sineWavelength", longName="Sine_Wavelength", defaultValue=1.0,
                     at="float",
                     k=True)
        cmds.addAttr(self.cont_special, shortName="sineDropoff", longName="Sine_Dropoff", defaultValue=0.0, at="float",
                     k=True)
        cmds.addAttr(self.cont_special, shortName="sineSlide", longName="Sine_Slide", defaultValue=0.0, at="float",
                     k=True)
        cmds.addAttr(self.cont_special, shortName="sineArea", longName="Sine_area", defaultValue=1.0, at="float",
                     k=True)
        cmds.addAttr(self.cont_special, shortName="sineDirection", longName="Sine_Direction", defaultValue=0.0,
                     at="float",
                     k=True)

        cmds.addAttr(self.cont_special, shortName="sineAnimate", longName="Sine_Animate", defaultValue=0.0, at="float",
                     k=True)

        self.contFK_List = []
        self.contTwk_List = []

        for j in range(len(self.guideJoints)):
            s = cmds.getAttr("%s.tx" % self.guideJoints[j]) / 3
            s = iconScale if s == 0 else s
            scaleTwk = (s, s, s)
            contTwk, dmp = icon.createIcon("Circle", iconName="%s_tentacleTweak%i_cont" % (self.suffix, j),
                                           scale=scaleTwk, normal=self.mirror_axis)
            functions.alignToAlter(contTwk, self.guideJoints[j], mode=2)
            contTwk_OFF = functions.createUpGrp(contTwk, "OFF")
            contTwk_ORE = functions.createUpGrp(contTwk, "ORE")
            self.contTwk_List.append(contTwk)

            scaleFK = (s * 1.2, s * 1.2, s * 1.2)
            contFK, _ = icon.createIcon("Ngon", iconName="%s_tentacleFK%i_cont" % (self.suffix, j), scale=scaleFK,
                                        normal=self.mirror_axis)
            functions.alignToAlter(contFK, self.guideJoints[j], mode=2)
            contFK_OFF = functions.createUpGrp(contFK, "OFF")
            contFK_ORE = functions.createUpGrp(contFK, "ORE")
            self.contFK_List.append(contFK)

            cmds.parent(contTwk_OFF, contFK)
            if not j == 0:
                cmds.parent(contFK_OFF, self.contFK_List[j - 1])
            else:
                cmds.parent(contFK_OFF, self.scaleGrp)

        cmds.parent(cont_special_ORE, self.contFK_List[0])

        functions.colorize(self.contFK_List, self.colorCodes[0])
        functions.colorize(self.contTwk_List, self.colorCodes[0])
        functions.colorize(self.cont_special, self.colorCodes[0])

        # map(lambda x: cmds.connectAttr("%s.contVis" % self.scaleGrp, "%s.v" % x), self.contTwk_List)
        functions.drive_attrs("%s.contVis" % self.scaleGrp, ["%s.v" % x for x in self.contTwk_List])
        # map(lambda x: cmds.connectAttr("%s.contVis" % self.scaleGrp, "%s.v" % x), self.contFK_List)
        functions.drive_attrs("%s.contVis" % self.scaleGrp, ["%s.v" % x for x in self.contFK_List])

    def createRoots(self):
        pass

    def createIKsetup(self):
        ## Create the Base Nurbs Plane (npBase)
        ribbonLength = functions.getDistance(self.contJointsList[0], self.contJointsList[-1])

        npBase = cmds.nurbsPlane(ax=(0, 1, 0), u=self.contRes, v=1, w=ribbonLength, lr=(1.0 / ribbonLength),
                                 name="npBase_%s" % self.suffix)[0]
        cmds.rebuildSurface(npBase, ch=1, rpo=1, rt=0, end=1, kr=2, kcp=0, kc=0, su=5, du=3, sv=1, dv=1, tol=0, fr=0,
                            dir=1)
        functions.alignAndAim(npBase, targetList=[self.contJointsList[0], self.contJointsList[-1]],
                              aimTargetList=[self.contJointsList[-1]], upVector=self.up_axis)

        ## Duplicate the Base Nurbs Plane as joint Holder (npJDefHolder)
        npJdefHolder = cmds.nurbsPlane(ax=(0, 1, 0), u=self.deformerRes, v=1, w=ribbonLength, lr=(1.0 / ribbonLength),
                                       name="npJDefHolder_%s" % self.suffix)[0]
        cmds.rebuildSurface(npJdefHolder, ch=1, rpo=1, rt=0, end=1, kr=2, kcp=0, kc=0, su=5, du=3, sv=1, dv=1, tol=0,
                            fr=0,
                            dir=1)
        functions.alignAndAim(npJdefHolder, targetList=[self.contJointsList[0], self.contJointsList[-1]],
                              aimTargetList=[self.contJointsList[-1]],
                              upVector=self.up_axis)

        ## Create the follicles on the npJDefHolder
        npJdefHolderShape = functions.getShapes(npJdefHolder)[0]
        follicleList = []
        for i in range(0, int(self.jointRes)):
            follicle = cmds.createNode('follicle', name="follicle_{0}{1}".format(self.suffix, str(i)))
            follicle_transform = functions.getParent(follicle)
            cmds.connectAttr("%s.local" % npJdefHolderShape, "%s.inputSurface" % follicle)
            cmds.connectAttr("%s.worldMatrix[0]" % npJdefHolderShape, "%s.inputWorldMatrix" % follicle)
            cmds.connectAttr("%s.outRotate" % follicle, "%s.rotate" % follicle_transform)
            cmds.connectAttr("%s.outTranslate" % follicle, "%s.translate" % follicle_transform)
            cmds.setAttr("%s.parameterV" % follicle, 0.5)
            cmds.setAttr("%s.parameterU" % follicle,
                         ((1 / self.jointRes) + (i / self.jointRes) - ((1 / self.jointRes) / 2)))
            functions.lockAndHide(follicle_transform, ["tx", "ty", "tz", "rx", "ry", "rz"], hide=False)
            follicleList.append(follicle)

            defJ = cmds.joint(name="%s_%i_jDef" % (self.suffix, i))
            cmds.joint(defJ, e=True, zso=True, oj='zxy')
            self.deformerJoints.append(defJ)
            self.sockets.append(defJ)
            cmds.parent(follicle_transform, self.nonScaleGrp)
            cmds.scaleConstraint(self.scaleGrp, follicle_transform, mo=True)

        # create follicles for scaling calculations
        follicle_sca_list = []
        counter = 0
        for index in range(int(self.jointRes)):
            s_follicle = cmds.createNode('follicle', name="follicleSCA_{0}{1}".format(self.suffix, index))
            s_follicle_transform = functions.getParent(s_follicle)
            cmds.connectAttr("%s.local" % npJdefHolderShape, "%s.inputSurface" % s_follicle)
            cmds.connectAttr("%s.worldMatrix[0]" % npJdefHolderShape, "%s.inputWorldMatrix" % s_follicle)
            cmds.connectAttr("%s.outRotate" % s_follicle, "%s.rotate" % s_follicle_transform)
            cmds.connectAttr("%s.outTranslate" % s_follicle, "%s.translate" % s_follicle_transform)

            cmds.setAttr("%s.parameterV" % s_follicle, 0.0)
            cmds.setAttr("%s.parameterU" % s_follicle,
                         ((1 / self.jointRes) + (index / self.jointRes) - ((1 / self.jointRes) / 2)))
            functions.lockAndHide(s_follicle_transform, ["tx", "ty", "tz", "rx", "ry", "rz"], hide=False)
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

        cmds.setDrivenKeyframe("%s.curvature" % curlDeformer[0], cd="%s.curl" % self.cont_special, v=0.0, dv=0.0,
                               itt='linear', ott='linear')
        cmds.setDrivenKeyframe("%s.curvature" % curlDeformer[0], cd="%s.curl" % self.cont_special, v=1500.0, dv=0.01,
                               itt='linear', ott='linear')
        cmds.setDrivenKeyframe("%s.curvature" % curlDeformer[0], cd="%s.curl" % self.cont_special, v=-1500.0, dv=-0.01,
                               itt='linear', ott='linear')

        cmds.setDrivenKeyframe("%s.ty" % curlDeformer[1], cd="%s.curl" % self.cont_special, v=0.0, dv=10.0,
                               itt='linear', ott='linear')
        cmds.setDrivenKeyframe("%s.ty" % curlDeformer[1], cd="%s.curl" % self.cont_special, v=0.0, dv=-10.0,
                               itt='linear', ott='linear')
        cmds.setDrivenKeyframe(["%s.sx" % curlDeformer[1], "%s.sy" % curlDeformer[1], "%s.sz" % curlDeformer[1]],
                               cd="%s.curl" % self.cont_special, v=(self.totalLength * 2), dv=10.0, itt='linear',
                               ott='linear')
        cmds.setDrivenKeyframe(["%s.sx" % curlDeformer[1], "%s.sy" % curlDeformer[1], "%s.sz" % curlDeformer[1]],
                               cd="%s.curl" % self.cont_special, v=(self.totalLength * 2), dv=-10.0, itt='linear',
                               ott='linear')
        cmds.setDrivenKeyframe("%s.rz" % curlDeformer[1], cd="%s.curl" % self.cont_special, v=4.0, dv=10.0,
                               itt='linear', ott='linear')
        cmds.setDrivenKeyframe("%s.rz" % curlDeformer[1], cd="%s.curl" % self.cont_special, v=-4.0, dv=-10.0,
                               itt='linear', ott='linear')
        cmds.setDrivenKeyframe("%s.ty" % curlDeformer[1], cd="%s.curl" % self.cont_special, v=self.totalLength, dv=0.0,
                               itt='linear', ott='linear')
        cmds.setDrivenKeyframe(["%s.sx" % curlDeformer[1], "%s.sy" % curlDeformer[1], "%s.sz" % curlDeformer[1]],
                               cd="%s.curl" % self.cont_special, v=(self.totalLength / 2), dv=0.0, itt='linear',
                               ott='linear')
        cmds.setDrivenKeyframe("%s.rz" % curlDeformer[1], cd="%s.curl" % self.cont_special, v=6.0, dv=0.01,
                               itt='linear', ott='linear')
        cmds.setDrivenKeyframe("%s.rz" % curlDeformer[1], cd="%s.curl" % self.cont_special, v=-6.0, dv=-0.01,
                               itt='linear', ott='linear')

        ## create curl size multipliers

        curlSizeMultX = cmds.createNode("multDoubleLinear", name="curlSizeMultX_{0}".format(self.suffix))
        curlSizeMultY = cmds.createNode("multDoubleLinear", name="curlSizeMultY_{0}".format(self.suffix))
        curlSizeMultZ = cmds.createNode("multDoubleLinear", name="curlSizeMultZ_{0}".format(self.suffix))

        curlAngleMultZ = cmds.createNode("multDoubleLinear", name="curlAngleMultZ_{0}".format(self.suffix))

        curlShiftAdd = cmds.createNode("plusMinusAverage", name="curlAddShift_{0}".format(self.suffix))
        cmds.connectAttr("%s.curlShift" % self.cont_special, "%s.input1D[0]" % curlShiftAdd)
        cmds.setAttr("%s.input1D[1]" % curlShiftAdd, 180)

        cmds.connectAttr("%s.output1D" % curlShiftAdd, "%s.rx" % curlDeformer[1])
        cmds.connectAttr("%s.curlSize" % self.cont_special, "%s.input1" % curlSizeMultX)
        cmds.connectAttr("%s.curlSize" % self.cont_special, "%s.input1" % curlSizeMultY)
        cmds.connectAttr("%s.curlSize" % self.cont_special, "%s.input1" % curlSizeMultZ)
        cmds.connectAttr("%s.curlAngle" % self.cont_special, "%s.input1" % curlAngleMultZ)

        cmds.connectAttr("%s.output" % cmds.listConnections("%s.sx" % curlDeformer[1])[0], "%s.input2" % curlSizeMultX)
        cmds.connectAttr("%s.output" % cmds.listConnections("%s.sy" % curlDeformer[1])[0], "%s.input2" % curlSizeMultY)
        cmds.connectAttr("%s.output" % cmds.listConnections("%s.sz" % curlDeformer[1])[0], "%s.input2" % curlSizeMultZ)
        cmds.connectAttr("%s.output" % cmds.listConnections("%s.rz" % curlDeformer[1])[0], "%s.input2" % curlAngleMultZ)

        cmds.connectAttr("%s.output" % curlSizeMultX, "%s.sx" % curlDeformer[1], force=True)
        cmds.connectAttr("%s.output" % curlSizeMultY, "%s.sy" % curlDeformer[1], force=True)
        cmds.connectAttr("%s.output" % curlSizeMultZ, "%s.sz" % curlDeformer[1], force=True)
        cmds.connectAttr("%s.output" % curlAngleMultZ, "%s.rz" % curlDeformer[1], force=True)
        cmds.connectAttr("%s.curlDirection" % self.cont_special, "%s.ry" % curlLoc)

        ## TWIST DEFORMER
        twistDeformer = cmds.nonLinear(npDeformers, type='twist')
        cmds.rotate(0, 0, 0, twistDeformer[1])
        twistLoc = cmds.spaceLocator(name="twistLoc_{0}".format(self.suffix))[0]
        cmds.parent(twistDeformer[1], twistLoc)

        ## make connections:
        cmds.connectAttr("%s.twistAngle" % self.cont_special, "%s.endAngle" % twistDeformer[0], force=True)
        cmds.connectAttr("%s.twistSlide" % self.cont_special, "%s.translateY" % twistLoc)
        cmds.connectAttr("%s.twistArea" % self.cont_special, "%s.scaleY" % twistLoc)

        ## SINE DEFORMER
        sineDeformer = cmds.nonLinear(npDeformers, type='sine')
        cmds.rotate(0, 0, 0, sineDeformer[1])
        sineLoc = cmds.spaceLocator(name="sineLoc_{0}".format(self.suffix))[0]
        cmds.parent(sineDeformer[1], sineLoc)

        ## make connections:
        cmds.connectAttr("%s.sineAmplitude" % self.cont_special, "%s.amplitude" % sineDeformer[0], force=True)
        cmds.connectAttr("%s.sineWavelength" % self.cont_special, "%s.wavelength" % sineDeformer[0], force=True)
        cmds.connectAttr("%s.sineDropoff" % self.cont_special, "%s.dropoff" % sineDeformer[0], force=True)
        cmds.connectAttr("%s.sineAnimate" % self.cont_special, "%s.offset" % sineDeformer[0], force=True)

        cmds.connectAttr("%s.sineSlide" % self.cont_special, "%s.translateY" % sineLoc)
        cmds.connectAttr("%s.sineArea" % self.cont_special, "%s.scaleY" % sineLoc)
        cmds.connectAttr("%s.sineDirection" % self.cont_special, "%s.rotateY" % sineLoc)

        # WHY THIS OFFSET IS NECESSARY? TRY TO GED RID OF
        offsetVal = (0, 180, 0) if self.sideMult == -1 else (0, 0, 0)
        for j in range(len(self.guideJoints)):
            functions.alignToAlter(self.contJointsList[j], self.guideJoints[j], mode=2)
            cmds.pointConstraint(self.contTwk_List[j], self.contJointsList[j], mo=False)
            cmds.orientConstraint(self.contTwk_List[j], self.contJointsList[j], mo=False, offset=offsetVal)

            cmds.scaleConstraint(self.contTwk_List[j], self.contJointsList[j], mo=False)

        cmds.parent(npBase, self.nonScaleGrp)
        cmds.parent(npDeformers, self.nonScaleGrp)
        cmds.parent(curlLoc, self.nonScaleGrp)
        cmds.parent(twistLoc, self.nonScaleGrp)
        cmds.parent(sineLoc, self.nonScaleGrp)
        cmds.parent(npWrapGeo, self.nonScaleGrp)
        cmds.parent(npJdefHolder, self.scaleGrp)

        nodesRigVis = [npBase, npJdefHolder, npDeformers, sineLoc, twistLoc, curlLoc]
        # map(lambda x: cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % x), nodesRigVis)
        functions.drive_attrs("%s.rigVis" % self.scaleGrp, ["%s.v" % x for x in nodesRigVis])
        # map(lambda x: cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % x), follicle_sca_list)
        functions.drive_attrs("%s.rigVis" % self.scaleGrp, ["%s.v" % x for x in follicle_sca_list])
        # map(lambda x: cmds.connectAttr("%s.rigVis" % self.scaleGrp, "%s.v" % x), follicleList)
        functions.drive_attrs("%s.rigVis" % self.scaleGrp, ["%s.v" % x for x in follicleList])

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
        cmds.setAttr("%s.rigVis" % self.scaleGrp, 0)

        # map(lambda x: extra.lockAndHide(x, ["sx", "sy", "sz"]), self.contFK_List)
        _ = [functions.lockAndHide(x, ["sx", "sy", "sz"]) for x in self.contFK_List]
        self.scaleConstraints = [self.scaleGrp]

        cmds.delete(self.guideJoints)

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
        if not cmds.attributeQuery('dropoff', n=influence, exists=True):
            cmds.addAttr(influence, sn='dr', ln='dropoff', dv=4.0, min=0.0, max=20.0)
            cmds.setAttr(influence + '.dr', k=True)

        # if type mesh
        if cmds.nodeType(influenceShape) == 'mesh':
            # create smoothness attr if it doesn't exist
            if not cmds.attributeQuery('smoothness', n=influence, exists=True):
                cmds.addAttr(influence, sn='smt', ln='smoothness', dv=0.0, min=0.0)
                cmds.setAttr(influence + '.smt', k=True)

            # create the inflType attr if it doesn't exist
            if not cmds.attributeQuery('inflType', n=influence, exists=True):
                cmds.addAttr(influence, at='short', sn='ift', ln='inflType', dv=2, min=1, max=2)

            cmds.connectAttr(influenceShape + '.worldMesh', wrapNode + '.driverPoints[0]')
            cmds.connectAttr(baseShape + '.worldMesh', wrapNode + '.basePoints[0]')
            cmds.connectAttr(influence + '.inflType', wrapNode + '.inflType[0]')
            cmds.connectAttr(influence + '.smoothness', wrapNode + '.smoothness[0]')

        # if type nurbsCurve or nurbsSurface
        if cmds.nodeType(influenceShape) == 'nurbsCurve' or cmds.nodeType(influenceShape) == 'nurbsSurface':
            # create the wrapSamples attr if it doesn't exist
            if not cmds.attributeQuery('wrapSamples', n=influence, exists=True):
                cmds.addAttr(influence, at='short', sn='wsm', ln='wrapSamples', dv=10, min=1)
                cmds.setAttr(influence + '.wsm', k=True)

            cmds.connectAttr(influenceShape + '.ws', wrapNode + '.driverPoints[0]')
            cmds.connectAttr(baseShape + '.ws', wrapNode + '.basePoints[0]')
            cmds.connectAttr(influence + '.wsm', wrapNode + '.nurbsSamples[0]')

        cmds.connectAttr(influence + '.dropoff', wrapNode + '.dropoff[0]')
        # I want to return a pyNode object for the wrap deformer.
        # I do not see the reason to rewrite the code here into pymel.
        return wrapNode, base
        # return pm.nt.Wrap(wrapNode), base


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
            tentacle_jnt = cmds.joint(p=(rPointTentacle + (addTentacle * seg)),
                                      name="jInit_tentacle_%s_%i" % (self.suffix, seg))
            # Update the guideJoints list
            self.guideJoints.append(tentacle_jnt)

        # set orientation of joints
        functions.orientJoints(self.guideJoints, worldUpAxis=self.upVector, upAxis=(0, 1, 0),
                               reverseAim=self.sideMultiplier, reverseUp=self.sideMultiplier)

    def define_attributes(self):
        # set joint side and type attributes
        functions.set_joint_type(self.guideJoints[0], "TentacleRoot")
        _ = [functions.set_joint_type(jnt, "Tentacle") for jnt in self.guideJoints[1:]]
        _ = [functions.set_joint_side(jnt, self.side) for jnt in self.guideJoints]

        # ----------Mandatory---------[Start]
        root_jnt = self.guideJoints[0]
        functions.create_global_joint_attrs(root_jnt, moduleName="%s_Tentacle" % self.side, upAxis=self.upVector, mirrorAxis=self.mirrorVector,
                                            lookAxis=self.lookVector)
        # ----------Mandatory---------[End]

        for attr_dict in LIMB_DATA["properties"]:
            functions.create_attribute(root_jnt, attr_dict)

    def createGuides(self):
        self.draw_joints()
        self.define_attributes()

    def convertJoints(self, joints_list):
        if len(joints_list) < 2:
            FEEDBACK.warning("Define or select at least 2 joints for Tentacle Guide conversion. Skipping")
            return
        self.guideJoints = joints_list
        self.define_attributes()


