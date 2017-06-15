import pymel.core as pm

import extraProcedures as extra

reload(extra)
import contIcons as icon

reload(icon)


# Def arguments:
# refJoints = [pm.PyNode("joint1"), pm.PyNode("joint2")]
# name = "test"
# cuts = 5
# dropoff = 2
class twistSpline(object):
    contCurves_ORE = None
    contCurve_Start = None
    contCurve_End = None
    endLock = None
    scaleGrp = None
    nonScaleGrp = None
    attPassCont = None
    defJoints = None
    noTouchData = None

    def createTspline(self, refJoints, name, cuts, dropoff=2):
        self.scaleGrp = pm.group(name="scaleGrp_" + name, em=True)
        self.nonScaleGrp = pm.group(name="nonScaleGrp_" + name, em=True)
        rootVc = refJoints[0].getTranslation(space="world")  # Root Vector
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
            currentJointLength = extra.getDistance(refJoints[i], refJoints[tmin])
            ctrlDistance = currentJointLength + ctrlDistance
            totalLength += currentJointLength
            contDistances.append(ctrlDistance)  # this list contains distance between each control point

        endVc = (rootVc.x, (rootVc.y + totalLength), rootVc.z)

        splitVc = endVc - rootVc
        segmentVc = (splitVc / (cuts))
        segmentLoc = rootVc + segmentVc
        curvePoints = []  # for curve creation
        IKjoints = []
        pm.select(d=True)

        # Create IK Joints ORIENTATION - ORIENTATION - ORIENTATION

        for i in range(0, cuts + 2):  # iterates one extra to create an additional joint for orientation
            place = rootVc + (segmentVc * (i))
            j = pm.joint(p=place, name="jIK_" + name + str(i), )
            # pm.setAttr(j.displayLocalAxis, 1)
            if i < (cuts + 1):  # if it is not the extra bone, update the lists
                IKjoints.append(j)
                curvePoints.append(place)

        pm.parent(IKjoints[0], self.nonScaleGrp)

        # ORIENT JOINTS PROPERLY

        ######  ######  ####### ######  ####### ######  #       #     #
        #     # #     # #     # #     # #       #     # #        #   #
        #     # #     # #     # #     # #       #     # #         # #
        ######  ######  #     # ######  #####   ######  #          #
        #       #   #   #     # #       #       #   #   #          #
        #       #    #  #     # #       #       #    #  #          #
        #       #     # ####### #       ####### #     # #######    #

        for j in IKjoints:
            pm.joint(j, e=True, zso=True, oj="yzx", sao="zup")

        # get rid of the extra bone
        deadBone = pm.listRelatives(IKjoints[len(IKjoints) - 1], c=True)
        pm.delete(deadBone)

        self.defJoints = pm.duplicate(IKjoints, name="jDef_%s0" % name)

        # create the controller joints

        contJoints = []
        pm.select(d=True)
        for i in range(0, len(contDistances)):
            ctrlVc = splitVc.normal() * contDistances[i]
            place = rootVc + (ctrlVc)
            j = pm.joint(p=place, name="jCont_spline_" + name + str(i), radius=5, o=(0, 0, 0))
            # pm.setAttr(j.displayLocalAxis, 1)
            contJoints.append(j)
            pm.select(d=True)

        # create the splineIK for the IK joints
        # # create the spline curve
        splineCurve = pm.curve(name="splineCurve_" + name, p=curvePoints)
        # # create spline IK
        splineIK = pm.ikHandle(sol="ikSplineSolver", createCurve=False, c=splineCurve, sj=IKjoints[0],
                               ee=IKjoints[len(self.defJoints) - 1], w=1.0)
        # # skin bind control joints
        pm.select(contJoints)
        pm.select(splineCurve, add=True)
        pm.skinCluster(dr=dropoff, tsb=True)

        # create the RP Solver IKs for the jDef joints
        poleGroups = []
        RPhandles = []
        for i in range(0, len(self.defJoints)):
            if i < len(self.defJoints) - 1:
                RP = pm.ikHandle(sj=self.defJoints[i], ee=self.defJoints[i + 1], name="tSpine_RP_%s_%s" % (i, name),
                                 sol="ikRPsolver")
                RPhandles.append(RP[0])
                # rpSolvers.append(RP[0])
                # # create locator and group for each rp
                loc = pm.spaceLocator(name="tSpinePoleLoc_%s_%s" % (i, name))
                loc_OFF = extra.createUpGrp(loc, "OFF")
                extra.alignTo(loc_OFF, self.defJoints[i])
                pm.move(loc, (1, 0, 0), r=True)
                # parent locator groups, pole vector locators >> RP Solvers, point constraint RP Solver >> IK Joints
                pm.parent(loc_OFF, IKjoints[i])
                poleGroups.append(loc_OFF)
                pm.poleVectorConstraint(loc, RP[0])
                pm.pointConstraint(IKjoints[i + 1], RP[0])
                pm.parent(RP[0], self.nonScaleGrp)

        # # connect the roots of two chains
        pm.pointConstraint(IKjoints[0], self.defJoints[0], mo=False)

        # connect rotations of locator groups
        for i in range(0, len(poleGroups)):
            blender = pm.createNode("blendTwoAttr", name="tSplineX_blend" + str(i))
            contJoints[0].rotateY >> blender.input[0]
            contJoints[len(contJoints) - 1].rotateY >> blender.input[1]
            blender.output >> poleGroups[i].rotateY
            blendRatio = (i + 0.0) / (cuts - 1.0)
            pm.setAttr(blender.attributesBlender, blendRatio)

        # CONTROL CURVES

        for i in range(0, len(contJoints)):
            extra.alignTo(contJoints[i], refJoints[i], 0)
            scaleRatio = (totalLength / len(contJoints))
            if i != 0 and i != (len(contJoints) - 1):
                ## Create control Curve if it is not the first or last control joint
                cont_Curve = icon.star("cont_spline_" + name + str(i), (scaleRatio, scaleRatio, scaleRatio))
            else:
                cont_Curve = pm.spaceLocator(name="lockPoint_" + name + str(i))
            # cont_Curve_OFF = extra.createUpGrp(cont_Curve, "OFF")
            cont_Curve_ORE = extra.createUpGrp(cont_Curve, "ORE")
            extra.alignTo(cont_Curve_ORE, contJoints[i], 2)
            pm.parentConstraint(cont_Curve, contJoints[i])
            contCurves.append(cont_Curve)
            self.contCurves_ORE.append(cont_Curve_ORE)

        self.contCurve_Start = contCurves[0]
        self.contCurve_End = contCurves[len(contCurves) - 1]
        # STRETCH and SQUASH
        #
        # Create Stretch and Squash Nodes
        #
        # first controller is the one which holds the attributes to be passed
        self.attPassCont = (contCurves[0])

        pm.addAttr(self.attPassCont, shortName='preserveVol', longName='Preserve_Volume', defaultValue=0.0,
                   minValue=0.0,
                   maxValue=1.0, at="double", k=True)
        pm.addAttr(self.attPassCont, shortName='volumeFactor', longName='Volume_Factor', defaultValue=1, at="double",
                   k=True)

        pm.addAttr(self.attPassCont, shortName='stretchy', longName='Stretchyness', defaultValue=1, minValue=0.0,
                   maxValue=1.0,
                   at="double", k=True)

        curveInfo = pm.arclen(splineCurve, ch=True)
        initialLength = pm.getAttr(curveInfo.arcLength)

        powValue = 0

        for i in range(0, len(IKjoints)):

            curveGlobMult = pm.createNode("multiplyDivide", name="curveGlobMult_" + name)
            pm.setAttr(curveGlobMult.operation, 2)
            boneGlobMult = pm.createNode("multiplyDivide", name="boneGlobMult_" + name)

            lengthMult = pm.createNode("multiplyDivide", name="length_Multiplier_" + name)
            pm.setAttr(lengthMult.operation, 2)

            volumeSw = pm.createNode("blendColors", name="volumeSw_" + name)
            stretchSw = pm.createNode("blendTwoAttr", name="stretchSw_" + name)

            middlePoint = (len(IKjoints) / 2)
            volumePow = pm.createNode("multiplyDivide", name="volume_Power_" + name)
            volumeFactor = pm.createNode("multiplyDivide", name="volume_Factor_" + name)
            self.attPassCont.volumeFactor >> volumeFactor.input1X
            self.attPassCont.volumeFactor >> volumeFactor.input1Z
            volumeFactor.output >> volumePow.input2

            pm.setAttr(volumePow.operation, 3)

            ## make sure first and last joints preserves the full volume
            if i == 0 or i == len(IKjoints) - 1:
                pm.setAttr(volumeFactor.input2X, 0)
                pm.setAttr(volumeFactor.input2Z, 0)

            elif (i <= middlePoint):
                powValue = powValue - 1
                pm.setAttr(volumeFactor.input2X, powValue)
                pm.setAttr(volumeFactor.input2Z, powValue)

            else:
                powValue = powValue + 1
                pm.setAttr(volumeFactor.input2X, powValue)
                pm.setAttr(volumeFactor.input2Z, powValue)

            curveInfo.arcLength >> curveGlobMult.input1X
            pm.setAttr(stretchSw.input[0], initialLength)
            curveGlobMult.outputX >> stretchSw.input[1]
            self.attPassCont.stretchy >> stretchSw.attributesBlender

            self.scaleGrp.sx >> curveGlobMult.input2X
            stretchSw.output >> lengthMult.input1X
            pm.setAttr(lengthMult.input2X, initialLength)
            lengthMult.outputX >> boneGlobMult.input1Y

            lengthMult.outputX >> volumePow.input1X
            lengthMult.outputX >> volumePow.input1Z
            pm.setAttr(volumeSw.color2R, 1)
            pm.setAttr(volumeSw.color2B, 1)
            volumePow.outputX >> volumeSw.color1R
            volumePow.outputX >> volumeSw.color1B
            volumeSw.outputR >> boneGlobMult.input1X
            volumeSw.outputB >> boneGlobMult.input1Z
            self.scaleGrp.sx >> boneGlobMult.input2X
            self.scaleGrp.sx >> boneGlobMult.input2Y
            self.scaleGrp.sx >> boneGlobMult.input2Z
            self.attPassCont.preserveVol >> volumeSw.blender

            boneGlobMult.output >> IKjoints[i].scale
            boneGlobMult.output >> self.defJoints[i].scale

        # Create endLock
        self.endLock = pm.spaceLocator(name="endLock_" + name)
        pm.pointConstraint(self.defJoints[len(self.defJoints) - 1], self.endLock, mo=False)

        # GOOD PARENTING

        pm.parent(contJoints, self.scaleGrp)
        pm.parent(splineIK[0], self.nonScaleGrp)
        pm.parent(splineCurve, self.nonScaleGrp)
        pm.parent(self.defJoints[0], self.nonScaleGrp)

        # FOOL PROOFING
        for i in contCurves:
            extra.lockAndHide(i, ["sx", "sy", "sz", "v"])

        # COLOR CODING
        index = 17
        for i in range(0, len(contCurves)):
            if i != 0 or i != len(contCurves):
                extra.colorize(contCurves[i], index)

        # RETURN

        self.noTouchData = ([splineCurve, splineIK[0], self.endLock], IKjoints, contJoints, poleGroups, RPhandles)
