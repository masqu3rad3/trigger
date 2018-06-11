import pymel.core as pm

import extraProcedures as extra

reload(extra)
import contIcons as icon

reload(icon)



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

    def createTspline(self, refJoints, name, cuts, dropoff=2, mode="equalDistance", twistType="regular", colorCode=17):
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

        # for j in refJoints:
        #     pm.joint(j, e=True, zso=True, oj="xyz", sao="yup")

        endVc = (rootVc.x, (rootVc.y + totalLength), rootVc.z)

        splitVc = endVc - rootVc
        segmentVc = (splitVc / (cuts))
        segmentLoc = rootVc + segmentVc
        curvePoints = []  # for curve creation
        IKjoints = []
        pm.select(d=True)

        # Create IK Joints ORIENTATION - ORIENTATION - ORIENTATION
        curveType = 3
        if mode == "equalDistance":

            curveType = 3
            for i in range(0, cuts + 2):  # iterates one extra to create an additional joint for orientation

                place = rootVc + (segmentVc * (i))
                j = pm.joint(p=place, name="jIK_" + name + str(i), )
                # pm.setAttr(j.displayLocalAxis, 1)
                if i < (cuts + 1):  # if it is not the extra bone, update the lists
                    IKjoints.append(j)
                    curvePoints.append(place)

        elif mode == "sameDistance":
            curveType = 1
            for i in range(0, len(contDistances)):
                ctrlVc = splitVc.normal() * contDistances[i]
                place = rootVc + (ctrlVc)
                j = pm.joint(p=place, name="jIK_" + name + str(i), radius=2, o=(0, 0, 0))
                # j = pm.joint(p=place, name="jIK_" + name + str(i), radius=2, o=(0, 90, 0))


                #extra.alignTo(j, refJoints[i], 2)

                IKjoints.append(j)
                curvePoints.append(place)
        else:
            pm.error ("Mode is not supported - twistSplineClass.py")


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
            pm.joint(j, e=True, zso=True, oj="xyz", sao="zup")
            # if twistType=="infinite":
            #     pm.joint(j, e=True, zso=True, oj="yzx", sao="zup")
            # if twistType=="regular":
            #     pm.joint(j, e=True, zso=True, oj="xyz", sao="zup")

        # get rid of the extra bone
        deadBone = pm.listRelatives(IKjoints[len(IKjoints) - 1], c=True)
        pm.delete(deadBone)

        # tempArray = IKjoints[0:-1] ## pop out the last joint
        # self.defJoints = pm.duplicate(tempArray, name="jDef_%s0" % name)
        self.defJoints = pm.duplicate(IKjoints, name="jDef_%s0" % name)

        # create the controller joints

        contJoints = []
        pm.select(d=True)
        for i in range(0, len(contDistances)):
            ctrlVc = splitVc.normal() * contDistances[i]
            place = rootVc + (ctrlVc)
            j = pm.joint(p=place, name="jCont_spline_" + name + str(i), radius=5, o=(0, 0, 0))
            #pm.setAttr(j.rotateZ, 90)
#############################################################
            # extra.alignTo(j, refJoints[i], 1)
#############################################################
            contJoints.append(j)
            pm.select(d=True)




        # create the splineIK for the IK joints
        # # create the spline curve
        splineCurve = pm.curve(name="splineCurve_" + name, d=curveType, p=curvePoints)
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

        # print "defjoints", self.defJoints
        # print "ikJoints", IKjoints

        if twistType == "infinite":
            for i in range(0, len(self.defJoints)):
                if i < len(self.defJoints) - 1:
                    RP = pm.ikHandle(sj=self.defJoints[i], ee=self.defJoints[i + 1], name="tSpine_RP_%s_%s" % (i, name),
                                     sol="ikRPsolver")
                    RPhandles.append(RP[0])
                    # rpSolvers.append(RP[0])
                    # # create locator and group for each rp
                    loc = pm.spaceLocator(name="tSpinePoleLoc_%s_%s" % (i, name))
                    pm.setAttr(loc.rotateOrder,3)
                    loc_POS = extra.createUpGrp(loc, "POS")
                    pm.setAttr(loc_POS.rotateOrder, 3)
                    loc_OFF = extra.createUpGrp(loc, "OFF")
                    pm.setAttr(loc_OFF.rotateOrder, 3)

                    extra.alignTo(loc_OFF, self.defJoints[i])
                    pm.move(loc, (10, 0, 0), r=True)
                    # parent locator groups, pole vector locators >> RP Solvers, point constraint RP Solver >> IK Joints
                    pm.parent(loc_POS, IKjoints[i])
                    poleGroups.append(loc_OFF)
                    pm.poleVectorConstraint(loc, RP[0])
                    pm.pointConstraint(IKjoints[i + 1], RP[0])
                    pm.parent(RP[0], self.nonScaleGrp)

            # # connect the roots of two chains
            pm.pointConstraint(IKjoints[0], self.defJoints[0], mo=False)

        else:
            for i in range(0, len(self.defJoints)):
                pm.parentConstraint(IKjoints[i], self.defJoints[i])

            ## adjust the twist controls for regular IK
            pm.setAttr(splineIK[0].dTwistControlEnable, 1)
            pm.setAttr(splineIK[0].dWorldUpType, 4)
            pm.setAttr(splineIK[0].dWorldUpAxis, 1)
            pm.setAttr(splineIK[0].dWorldUpVectorX, 0)
            pm.setAttr(splineIK[0].dWorldUpVectorY, 0)
            pm.setAttr(splineIK[0].dWorldUpVectorZ, -1)
            pm.setAttr(splineIK[0].dWorldUpVectorEndX, 0)
            pm.setAttr(splineIK[0].dWorldUpVectorEndY, 0)
            pm.setAttr(splineIK[0].dWorldUpVectorEndZ, -1)

            contJoints[0].worldMatrix[0] >> splineIK[0].dWorldUpMatrix
            contJoints[-1].worldMatrix[0] >> splineIK[0].dWorldUpMatrixEnd



        # connect rotations of locator groups



        # CONTROL CURVES

        for i in range(0, len(contJoints)):
            #extra.alignTo(contJoints[i], refJoints[i], 0)
            scaleRatio = (totalLength / len(contJoints))
            if i != 0 and i != (len(contJoints) - 1):
                ## Create control Curve if it is not the first or last control joint
                cont_Curve = icon.star("cont_spline_" + name + str(i), (scaleRatio, scaleRatio, scaleRatio))
            else:
                cont_Curve = pm.spaceLocator(name="lockPoint_" + name + str(i))
            pm.setAttr(cont_Curve.rotateOrder,3)
            # cont_Curve_OFF = extra.createUpGrp(cont_Curve, "OFF")
            cont_Curve_ORE = extra.createUpGrp(cont_Curve, "ORE")
            pm.setAttr(cont_Curve_ORE.rotateOrder, 3)
            extra.alignTo(cont_Curve_ORE, contJoints[i], 2, o=(0, 0, 0))
            pm.parentConstraint(cont_Curve, contJoints[i], mo=True)
            #extra.alignTo(cont_Curve_ORE, refJoints[i], 2)
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
                    bottomCon = pm.orientConstraint(self.contCurve_Start, poleGroups[i], mo=True)
                elif i == len(poleGroups)-1:
                    topCon = pm.orientConstraint(self.contCurve_End, poleGroups[i], mo=True)
                else:
                    blender = pm.createNode("blendColors", name="tSplineX_blend" + str(i))
                    poleGroups[-1].rotate >> blender.color1
                    poleGroups[0].rotate >> blender.color2
                    blender.outputG >> poleGroups[i].rotateY
                    blendRatio = (i + 0.0) / (cuts - 1.0)
                    pm.setAttr(blender.blender, blendRatio)
        else:
            pass




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
            self.attPassCont.volumeFactor >> volumeFactor.input1Y
            self.attPassCont.volumeFactor >> volumeFactor.input1Z
            volumeFactor.output >> volumePow.input2

            pm.setAttr(volumePow.operation, 3)

            ## make sure first and last joints preserves the full volume
            if i == 0 or i == len(IKjoints) - 1:
                pm.setAttr(volumeFactor.input2Y, 0)
                pm.setAttr(volumeFactor.input2Z, 0)

            elif (i <= middlePoint):
                powValue = powValue - 1
                pm.setAttr(volumeFactor.input2Y, powValue)
                pm.setAttr(volumeFactor.input2Z, powValue)

            else:
                powValue = powValue + 1
                pm.setAttr(volumeFactor.input2Y, powValue)
                pm.setAttr(volumeFactor.input2Z, powValue)

            curveInfo.arcLength >> curveGlobMult.input1X
            pm.setAttr(stretchSw.input[0], initialLength)
            curveGlobMult.outputX >> stretchSw.input[1]
            self.attPassCont.stretchy >> stretchSw.attributesBlender

            self.scaleGrp.sx >> curveGlobMult.input2X
            stretchSw.output >> lengthMult.input1X
            pm.setAttr(lengthMult.input2X, initialLength)
            lengthMult.outputX >> boneGlobMult.input1X

            lengthMult.outputX >> volumePow.input1Y
            lengthMult.outputX >> volumePow.input1Z
            pm.setAttr(volumeSw.color2G, 1)
            pm.setAttr(volumeSw.color2B, 1)
            volumePow.outputY >> volumeSw.color1G
            volumePow.outputZ >> volumeSw.color1B
            volumeSw.outputG >> boneGlobMult.input1Y
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

        ## Move them to original Positions

        for o in range (0,len(self.contCurves_ORE)):

            extra.alignTo(self.contCurves_ORE[o], refJoints[o])
            if not o == (len(self.contCurves_ORE)-1):
                tempAim = pm.aimConstraint(refJoints[o+1], self.contCurves_ORE[o], aimVector=(0,1,0), upVector=(0,1,0), mo=False)
            else:
                tempAim = pm.aimConstraint(refJoints[o-1], self.contCurves_ORE[o], aimVector=(0, -1, 0), upVector=(0, -1, 0), mo=False)
            pm.delete(tempAim)


        # GOOD PARENTING

        pm.parent(contJoints, self.scaleGrp)
        pm.parent(splineIK[0], self.nonScaleGrp)
        pm.parent(splineCurve, self.nonScaleGrp)
        pm.parent(self.defJoints[0], self.nonScaleGrp)

        # FOOL PROOFING
        for i in contCurves:
            extra.lockAndHide(i, ["sx", "sy", "sz", "v"])

        # COLOR CODING
        # for i in range(0, len(contCurves)):
        #     if i != 0 or i != len(contCurves):
        #         extra.colorize(contCurves[i], colorCode)
        extra.colorize(contCurves, colorCode)

        # RETURN
        # re-initialize the deformation joints (remove the last of it
        self.defJoints.pop(-1)
        self.noTouchData = ([splineCurve, splineIK[0], self.endLock], IKjoints, contJoints, poleGroups, RPhandles)

