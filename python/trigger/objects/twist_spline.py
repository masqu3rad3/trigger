from maya import cmds
import maya.api.OpenMaya as om

from trigger.library import functions, joint
from trigger.library import attribute
from trigger.library import api
from trigger.library import controllers as ic

class TwistSpline(object):

    def __init__(self):
        self.contCurves_ORE = None
        self.contCurve_Start = None
        self.contCurve_End = None
        self.endLock = None
        self.scaleGrp = None
        self.nonScaleGrp = None
        self.attPassCont = None
        self.defJoints = None
        self.noTouchData = None
        self.moveAxis = None
        self.upAxis = (0.0, 1.0, 0.0)


    def createTspline(self, refJoints, name, cuts=10, dropoff=2, mode="equalDistance", twistType="regular", colorCode=17):
        """
        
        Args:
            refJoints: (PyNode) Reference Joints to be taken as templates for start/end and controller locations 
            name: (String) Naming convention for newly created nodes.
            cuts: (Integer) Determines the resolution of joint chain.
            dropoff: (Float) Drop off value for skin bind between control curve and control joints
            mode: (String) The mode for joint creation. Valid valuer are 'equalDistance' and 'sameDistance'. 
                            If 'equalDistance' The chain joints will be seperated evenly. If 'sameDistance'
                            cuts value will be ignored and reference joint lengths will be used. Default: 'equalDistance'
            twistType: (String) Valid values are 'infinite', 'regular' and 'simple'. 'infinite' will use the awesomeSpline method
                        which will allow 360 degree rotations, but will be problematic if many midcontrollers are present.
                        'regular' mode is better if there are several middle controllers, but the spine cannot turn a full 360
                        without flipping. 'simple' mode is best for tentacles and terminal limbs which twisting will occur only
                        one end of the limb.

        Returns: None

        """

        self.scaleGrp = cmds.group(name="scaleGrp_%s" % name, em=True)
        self.nonScaleGrp = cmds.group(name="nonScaleGrp_%s" % name, em=True)

        rootVc = api.get_world_translation(refJoints[0])
        totalLength = 0
        contDistances = []
        contCurves = []
        self.contCurves_ORE = []
        ctrlDistance = 0

        # calculate the necessary distance for the joints
        for i in range(0, len(refJoints)):
            if i == 0:
                tmin = 0
            else:
                tmin = i - 1
            currentJointLength = functions.get_distance(refJoints[i], refJoints[tmin])
            ctrlDistance = currentJointLength + ctrlDistance
            totalLength += currentJointLength
            contDistances.append(ctrlDistance)  # this list contains distance between each control point

        endVc = om.MVector(rootVc.x, (rootVc.y + totalLength), rootVc.z)

        splitVc = endVc - rootVc
        segmentVc = (splitVc / (cuts))
        segmentLoc = rootVc + segmentVc
        curvePoints = []  # for curve creation
        IKjoints = []
        cmds.select(d=True)

        # Create IK Joints ORIENTATION - ORIENTATION - ORIENTATION
        curveType = 3
        if mode == "equalDistance":

            curveType = 3
            for index in range(cuts + 2):  # iterates one extra to create an additional joint for orientation
                place = rootVc + (segmentVc * (index))
                j = cmds.joint(p=place, name="jIK_%s%i" %(name, index))
                if index < (cuts + 1):  # if it is not the extra bone, update the lists
                    IKjoints.append(j)
                    curvePoints.append(place)

        elif mode == "sameDistance":
            curveType = 1
            for index in range(0, len(contDistances)):
                ctrlVc = splitVc.normal() * contDistances[index]
                place = rootVc + (ctrlVc)
                j = cmds.joint(p=place, name="jIK_%s%i" %(name, index), radius=2, o=(0, 0, 0))
                IKjoints.append(j)
                curvePoints.append(place)
        else:
            cmds.error ("Mode is not supported - twistSplineClass.py")


        cmds.parent(IKjoints[0], self.nonScaleGrp)

        # ORIENT JOINTS PROPERLY
        joint.orient_joints(IKjoints, worldUpAxis=(self.upAxis))

        map(lambda x: cmds.setAttr("%s.displayLocalAxis" %x, True), IKjoints)
        # for j in IKjoints:
        #     pm.joint(j, e=True, zso=True, oj="xyz", sao="zup")
            #TODO // Soktumunun infinite versiyonu calismiyor
            # if twistType=="infinite":
            #     pm.joint(j, e=True, zso=True, oj="yzx", sao="zup")
            # if twistType=="regular":
            #     pm.joint(j, e=True, zso=True, oj="xyz", sao="zup")

        # get rid of the extra bone
        deadBone = cmds.listRelatives(IKjoints[len(IKjoints) - 1], c=True)
        cmds.delete(deadBone)

        self.defJoints = cmds.duplicate(IKjoints, name="jDef_%s0" % name)

        # create the controller joints
        contJoints = []
        cmds.select(d=True)
        for index in range(len(contDistances)):
            ctrlVc = splitVc.normal() * contDistances[index]
            place = rootVc + (ctrlVc)
            jnt = cmds.joint(p=place, name="jCont_spline_%s%i" %(name, index), radius=5, o=(0, 0, 0))
            contJoints.append(jnt)

        joint.orient_joints(contJoints, worldUpAxis=(self.upAxis))

        cmds.select(d=True)
        cmds.parent(contJoints[1:], w=True)

        #############################################

        # create the splineIK for the IK joints
        # # create the spline curve
        splineCurve = cmds.curve(name="splineCurve_%s" % name, d=curveType, p=curvePoints)
        # # create spline IK
        splineIK = cmds.ikHandle(sol="ikSplineSolver", createCurve=False, c=splineCurve, sj=IKjoints[0],
                               ee=IKjoints[len(self.defJoints) - 1], w=1.0)
        # # skin bind control joints
        cmds.select(contJoints)
        cmds.select(splineCurve, add=True)
        cmds.skinCluster(dr=dropoff, tsb=True)

        # create the RP Solver IKs for the jDef joints
        poleGroups = []
        RPhandles = []

        if twistType == "infinite":
            for i in range(0, len(self.defJoints)):
                if i < len(self.defJoints) - 1:
                    RP = cmds.ikHandle(sj=self.defJoints[i], ee=self.defJoints[i + 1], name="tSpine_RP_%s%i" % (name, i),
                                     sol="ikRPsolver")
                    RPhandles.append(RP[0])
                    # # create locator and group for each rp
                    loc = cmds.spaceLocator(name="tSpinePoleLoc_%s%i" % (name, i))[0]
                    loc_POS = functions.create_offset_group(loc, "POS")
                    loc_OFF = functions.create_offset_group(loc, "OFF")

                    functions.align_to_alter(loc_POS, self.defJoints[i], mode=2)
                    cmds.setAttr("%s.tz" %loc, 5)

                    # parent locator groups, pole vector locators >> RP Solvers, point constraint RP Solver >> IK Joints
                    cmds.parent(loc_POS, IKjoints[i])
                    poleGroups.append(loc_OFF)
                    cmds.poleVectorConstraint(loc, RP[0])
                    cmds.pointConstraint(IKjoints[i + 1], RP[0])
                    cmds.parent(RP[0], self.nonScaleGrp)

            # # connect the roots of two chains
            cmds.pointConstraint(IKjoints[0], self.defJoints[0], mo=False)

        else:
            for i in range(0, len(self.defJoints)):
                cmds.parentConstraint(IKjoints[i], self.defJoints[i])

            ## adjust the twist controls for regular IK
            cmds.setAttr("%s.dTwistControlEnable" %splineIK[0], 1)
            cmds.setAttr("%s.dWorldUpType" %splineIK[0], 4)
            cmds.setAttr("%s.dWorldUpAxis" %splineIK[0], 1)
            cmds.setAttr("%s.dWorldUpVectorX" %splineIK[0], 0)
            cmds.setAttr("%s.dWorldUpVectorY" %splineIK[0], 0)
            cmds.setAttr("%s.dWorldUpVectorZ" %splineIK[0], -1)
            cmds.setAttr("%s.dWorldUpVectorEndX" %splineIK[0], 0)
            cmds.setAttr("%s.dWorldUpVectorEndY" %splineIK[0], 0)
            cmds.setAttr("%s.dWorldUpVectorEndZ" %splineIK[0], -1)

            cmds.connectAttr("%s.worldMatrix[0]" %contJoints[0], "%s.dWorldUpMatrix" %splineIK[0])
            cmds.connectAttr("%s.worldMatrix[0]" %contJoints[-1], "%s.dWorldUpMatrixEnd" %splineIK[0])

        # connect rotations of locator groups

        icon = ic.Icon()

        for i in range(0, len(contJoints)):
            scaleRatio = (totalLength / len(contJoints))
            if i != 0 and i != (len(contJoints) - 1):
                ## Create control Curve if it is not the first or last control joint
                cont_Curve, dmp = icon.create_icon("Star", icon_name="%s%i_tweak_cont" % (name, i), scale=(scaleRatio, scaleRatio, scaleRatio), normal=(1, 0, 0))
            else:
                cont_Curve = cmds.spaceLocator(name="lockPoint_%s%i" %(name, i))[0]
            # pm.setAttr(cont_Curve.rotateOrder,3)
            # cont_Curve_OFF = extra.createUpGrp(cont_Curve, "OFF")
            functions.align_to_alter(cont_Curve, contJoints[i], mode=2)
            cont_Curve_ORE = functions.create_offset_group(cont_Curve, "ORE")
            # pm.setAttr(cont_Curve_ORE.rotateOrder, 3)
            cmds.parentConstraint(cont_Curve, contJoints[i], mo=False)
            contCurves.append(cont_Curve)
            self.contCurves_ORE.append(cont_Curve_ORE)

        self.contCurve_Start = contCurves[0]
        self.contCurve_End = contCurves[len(contCurves) - 1]


        if twistType == "infinite":
            ## CREATE A TWIST NODE TO BE PASSED. this is the twist driver, connect it to rotation or attributes

            ## first make a solid connection for the top and bottom:
            for i in range(0, len(poleGroups)):
                ## if it is the first or the last group
                if i == 0:
                    bottomCon = cmds.orientConstraint(self.contCurve_Start, poleGroups[i], mo=False)
                elif i == len(poleGroups)-1:
                    topCon = cmds.orientConstraint(self.contCurve_End, poleGroups[i], mo=False)
                else:
                    blender = cmds.createNode("blendColors", name="tSplineX_blend" + str(i))
                    cmds.connectAttr("%s.rotate" % poleGroups[-1], "%s.color1" % blender)
                    cmds.connectAttr("%s.rotate" % poleGroups[0], "%s.color2" % blender)
                    cmds.connectAttr("%s.outputR" % blender, "%s.rotateX" % poleGroups[i])
                    blendRatio = (i + 0.0) / (cuts - 1.0)
                    cmds.setAttr("%s.blender" %blender, blendRatio)
        else:
            pass

        # STRETCH and SQUASH
        #
        # Create Stretch and Squash Nodes
        #
        # first controller is the one which holds the attributes to be passed
        self.attPassCont = (contCurves[0])

        cmds.addAttr(self.attPassCont, shortName='preserveVol', longName='Preserve_Volume', defaultValue=0.0,
                   minValue=0.0,
                   maxValue=1.0, at="double", k=True)
        cmds.addAttr(self.attPassCont, shortName='volumeFactor', longName='Volume_Factor', defaultValue=1, at="double",
                   k=True)

        cmds.addAttr(self.attPassCont, shortName='stretchy', longName='Stretchyness', defaultValue=1, minValue=0.0,
                   maxValue=1.0,
                   at="double", k=True)

        curveInfo = cmds.arclen(splineCurve, ch=True)
        initialLength = cmds.getAttr("%s.arcLength" %curveInfo)

        powValue = 0

        for i in range(0, len(IKjoints)):
            curveGlobMult = cmds.createNode("multiplyDivide", name="curveGlobMult_" + name)
            cmds.setAttr("%s.operation" %curveGlobMult, 2)
            boneGlobMult = cmds.createNode("multiplyDivide", name="boneGlobMult_" + name)

            lengthMult = cmds.createNode("multiplyDivide", name="length_Multiplier_" + name)
            cmds.setAttr("%s.operation" %lengthMult, 2)

            volumeSw = cmds.createNode("blendColors", name="volumeSw_" + name)
            stretchSw = cmds.createNode("blendTwoAttr", name="stretchSw_" + name)

            middlePoint = (len(IKjoints) / 2)
            volumePow = cmds.createNode("multiplyDivide", name="volume_Power_" + name)
            volumeFactor = cmds.createNode("multiplyDivide", name="volume_Factor_" + name)

            cmds.connectAttr("%s.volumeFactor" %self.attPassCont, "%s.input1Y" %volumeFactor)
            cmds.connectAttr("%s.volumeFactor" %self.attPassCont, "%s.input1Z" %volumeFactor)
            cmds.connectAttr("%s.output" %volumeFactor, "%s.input2" %volumePow)
            cmds.setAttr("%s.operation" %volumePow, 3)

            ## make sure first and last joints preserves the full volume
            if i == 0 or i == len(IKjoints) - 1:
                cmds.setAttr("%s.input2Y" %volumeFactor, 0)
                cmds.setAttr("%s.input2Z" %volumeFactor, 0)
            elif (i <= middlePoint):
                powValue = powValue - 1
                cmds.setAttr("%s.input2Y" %volumeFactor, powValue)
                cmds.setAttr("%s.input2Z" %volumeFactor, powValue)
            else:
                powValue = powValue + 1
                cmds.setAttr("%s.input2Y" %volumeFactor, powValue)
                cmds.setAttr("%s.input2Z" %volumeFactor, powValue)

            cmds.connectAttr("%s.arcLength" %curveInfo, "%s.input1X" %curveGlobMult)
            cmds.setAttr("%s.input[0]" %stretchSw, initialLength)
            cmds.connectAttr("%s.outputX" %curveGlobMult, "%s.input[1]" %stretchSw)
            cmds.connectAttr("%s.stretchy" %self.attPassCont, "%s.attributesBlender" %stretchSw)
            cmds.connectAttr("%s.sx" %self.scaleGrp, "%s.input2X" %curveGlobMult)
            cmds.connectAttr("%s.output" %stretchSw, "%s.input1X" %lengthMult)
            cmds.setAttr("%s.input2X" %lengthMult, initialLength)
            cmds.connectAttr("%s.outputX" %lengthMult, "%s.input1X" %boneGlobMult)
            cmds.connectAttr("%s.outputX" %lengthMult, "%s.input1Y" %volumePow)
            cmds.connectAttr("%s.outputX" %lengthMult, "%s.input1Z" %volumePow)
            cmds.setAttr("%s.color2G" %volumeSw, 1)
            cmds.setAttr("%s.color2B" %volumeSw, 1)
            cmds.connectAttr("%s.outputY" %volumePow, "%s.color1G" %volumeSw)
            cmds.connectAttr("%s.outputZ" %volumePow, "%s.color1B" %volumeSw)
            cmds.connectAttr("%s.outputG" %volumeSw, "%s.input1Y" %boneGlobMult)
            cmds.connectAttr("%s.outputB" %volumeSw, "%s.input1Z" %boneGlobMult)
            cmds.connectAttr("%s.sx" %self.scaleGrp, "%s.input2X" %boneGlobMult)
            cmds.connectAttr("%s.sx" %self.scaleGrp, "%s.input2Y" %boneGlobMult)
            cmds.connectAttr("%s.sx" %self.scaleGrp, "%s.input2Z" %boneGlobMult)
            cmds.connectAttr("%s.preserveVol" %self.attPassCont, "%s.blender" %volumeSw)
            cmds.connectAttr("%s.output" %boneGlobMult, "%s.scale" %IKjoints[i])
            cmds.connectAttr("%s.output" %boneGlobMult, "%s.scale" %self.defJoints[i])

        # Create endLock
        self.endLock = cmds.spaceLocator(name="endLock_%s" %name)[0]
        cmds.pointConstraint(self.defJoints[len(self.defJoints) - 1], self.endLock, mo=False)

        ## Move them to original Positions
        for o in range (0,len(self.contCurves_ORE)):
            if o == 0:
                functions.align_to_alter(self.contCurves_ORE[o], refJoints[o], mode=2)
            else:
                functions.align_to_alter(self.contCurves_ORE[o], refJoints[o], mode=0)
                functions.align_to_alter(self.contCurves_ORE[o], refJoints[o - 1], mode=1)

        # GOOD PARENTING
        cmds.parent(contJoints, self.scaleGrp)
        cmds.parent(splineIK[0], self.nonScaleGrp)

        # FOOL PROOFING
        for i in contCurves:
            attribute.lock_and_hide(i, ["sx", "sy", "sz", "v"])

        # COLOR CODING
        functions.colorize(contCurves, colorCode)

        # RETURN
        self.noTouchData = ([splineCurve, splineIK[0], self.endLock], IKjoints, contJoints, poleGroups, RPhandles)

