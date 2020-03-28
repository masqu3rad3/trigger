from maya import cmds
import maya.api.OpenMaya as om

# import pymel.core as pm

from trigger.library import functions as extra
from trigger.library import controllers as ic
reload(ic)


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
        # self.worldUpAxis = (0.0, 1.0, 0.0)
        # self.localMoveAxis = (0.0, 0.0, 1.0)
        self.upAxis = (0.0, 1.0, 0.0)
        # self.mirrorAxis = (1.0, 0.0, 0.0)


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

        self.scaleGrp = cmds.group(name="scaleGrp_" + name, em=True)
        self.nonScaleGrp = cmds.group(name="nonScaleGrp_" + name, em=True)

        # rootVc = refJoints[0].getTranslation(space="world")  # Root Vector
        rootVc = extra.getWorldTranslation(refJoints[0])
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

        # endVc = (rootVc.x, (rootVc.y + totalLength), rootVc.z)
        endVc = om.MVector(rootVc.x, (rootVc.y + totalLength), rootVc.z)
        # endVc = ((rootVc.x + totalLength), rootVc.y, rootVc.z)

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
            for i in range(0, cuts + 2):  # iterates one extra to create an additional joint for orientation

                place = rootVc + (segmentVc * (i))
                j = cmds.joint(p=place, name="jIK_" + name + str(i), )
                # extra.alignToAlter(j, refJoints[0], mode=1)
                # pm.makeIdentity(j, a=True)
                if i < (cuts + 1):  # if it is not the extra bone, update the lists
                    IKjoints.append(j)
                    curvePoints.append(place)

        elif mode == "sameDistance":
            curveType = 1
            for i in range(0, len(contDistances)):
                ctrlVc = splitVc.normal() * contDistances[i]
                place = rootVc + (ctrlVc)
                j = cmds.joint(p=place, name="jIK_" + name + str(i), radius=2, o=(0, 0, 0))
                # extra.alignToAlter(j, refJoints[0], mode=1)
                # pm.makeIdentity(j, a=True)


                IKjoints.append(j)
                curvePoints.append(place)
        else:
            cmds.error ("Mode is not supported - twistSplineClass.py")


        cmds.parent(IKjoints[0], self.nonScaleGrp)

        # ORIENT JOINTS PROPERLY

        ######  ######  ####### ######  ####### ######  #       #     #
        #     # #     # #     # #     # #       #     # #        #   #
        #     # #     # #     # #     # #       #     # #         # #
        ######  ######  #     # ######  #####   ######  #          #
        #       #   #   #     # #       #       #   #   #          #
        #       #    #  #     # #       #       #    #  #          #
        #       #     # ####### #       ####### #     # #######    #


        # extra.orientJoints(IKjoints, localMoveAxis=self.localMoveAxis, upAxis=self.upAxis, mirrorAxis=self.mirrorAxis)
        extra.orientJoints(IKjoints, worldUpAxis=(self.upAxis))

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

        # tempArray = IKjoints[0:-1] ## pop out the last joint
        # self.defJoints = pm.duplicate(tempArray, name="jDef_%s0" % name)
        self.defJoints = cmds.duplicate(IKjoints, name="jDef_%s0" % name)

        # create the controller joints

#         contJoints = []
#         pm.select(d=True)
#         for i in range(0, len(contDistances)):
#             ctrlVc = splitVc.normal() * contDistances[i]
#             place = rootVc + (ctrlVc)
#             j = pm.joint(p=place, name="jCont_spline_" + name + str(i), radius=5, o=(0, 0, 0))
#             #pm.setAttr(j.rotateZ, 90)
# #############################################################
#             # extra.alignTo(j, refJoints[i], 1)
# #############################################################
#             contJoints.append(j)
#             pm.select(d=True)

        contJoints = []
        cmds.select(d=True)
        for i in range(0, len(contDistances)):
            ctrlVc = splitVc.normal() * contDistances[i]
            place = rootVc + (ctrlVc)
            j = cmds.joint(p=place, name="jCont_spline_" + name + str(i), radius=5, o=(0, 0, 0))
            # pm.setAttr(j.rotateZ, 90)
            #############################################################
            # extra.alignTo(j, refJoints[i], mode=1)
            #############################################################
            contJoints.append(j)

        # extra.orientJoints(contJoints, localMoveAxis=self.localMoveAxis, upAxis=self.upAxis, mirrorAxis=self.mirrorAxis)
        extra.orientJoints(contJoints, worldUpAxis=(self.upAxis))

        cmds.select(d=True)
        cmds.parent(contJoints[1:], w=True)

        #############################################

        # create the splineIK for the IK joints
        # # create the spline curve
        splineCurve = cmds.curve(name="splineCurve_" + name, d=curveType, p=curvePoints)
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

        # print "defjoints", self.defJoints
        # print "ikJoints", IKjoints

        if twistType == "infinite":
            for i in range(0, len(self.defJoints)):
                if i < len(self.defJoints) - 1:
                    RP = cmds.ikHandle(sj=self.defJoints[i], ee=self.defJoints[i + 1], name="tSpine_RP_%s_%s" % (i, name),
                                     sol="ikRPsolver")
                    RPhandles.append(RP[0])
                    # rpSolvers.append(RP[0])
                    # # create locator and group for each rp
                    loc = cmds.spaceLocator(name="tSpinePoleLoc_%s_%s" % (i, name))[0]
                    # pm.setAttr(loc.rotateOrder,3)
                    loc_POS = extra.createUpGrp(loc, "POS")
                    # pm.setAttr(loc_POS.rotateOrder, 3)
                    loc_OFF = extra.createUpGrp(loc, "OFF")
                    # pm.setAttr(loc_OFF.rotateOrder, 3)

                    # extra.alignToAlter(loc_OFF, self.defJoints[i], mode=2)
                    extra.alignToAlter(loc_POS, self.defJoints[i], mode=2)
                    # pm.move(loc, (0, 5, 0), r=True)
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
            # contJoints[0].worldMatrix[0] >> splineIK[0].dWorldUpMatrix
            # contJoints[-1].worldMatrix[0] >> splineIK[0].dWorldUpMatrixEnd



        # connect rotations of locator groups



        # CONTROL CURVES

        # for i in range(0, len(contJoints)):
        #     #extra.alignTo(contJoints[i], refJoints[i], 0)
        #     scaleRatio = (totalLength / len(contJoints))
        #     if i != 0 and i != (len(contJoints) - 1):
        #         ## Create control Curve if it is not the first or last control joint
        #         cont_Curve = icon.star("cont_spline_" + name + str(i), (scaleRatio, scaleRatio, scaleRatio))
        #     else:
        #         cont_Curve = pm.spaceLocator(name="lockPoint_" + name + str(i))
        #     pm.setAttr(cont_Curve.rotateOrder,3)
        #     # cont_Curve_OFF = extra.createUpGrp(cont_Curve, "OFF")
        #     cont_Curve_ORE = extra.createUpGrp(cont_Curve, "ORE")
        #     pm.setAttr(cont_Curve_ORE.rotateOrder, 3)
        #     extra.alignTo(cont_Curve_ORE, contJoints[i], 2, o=(0, 0, 0))
        #     pm.parentConstraint(cont_Curve, contJoints[i], mo=False)
        #     #extra.alignTo(cont_Curve_ORE, refJoints[i], 2)
        #     contCurves.append(cont_Curve)
        #     self.contCurves_ORE.append(cont_Curve_ORE)
        #
        # self.contCurve_Start = contCurves[0]
        # self.contCurve_End = contCurves[len(contCurves) - 1]

        icon = ic.Icon()

        for i in range(0, len(contJoints)):
            scaleRatio = (totalLength / len(contJoints))
            if i != 0 and i != (len(contJoints) - 1):
                ## Create control Curve if it is not the first or last control joint
                # cont_Curve = icon.star("cont_spline_" + name + str(i), (scaleRatio, scaleRatio, scaleRatio), normal=self.mirrorAxis)
                cont_Curve, dmp = icon.createIcon("Star", iconName="cont_spline_" + name + str(i), scale=(scaleRatio, scaleRatio, scaleRatio), normal=(1,0,0))
            else:
                cont_Curve = cmds.spaceLocator(name="lockPoint_" + name + str(i))[0]
            # pm.setAttr(cont_Curve.rotateOrder,3)
            # cont_Curve_OFF = extra.createUpGrp(cont_Curve, "OFF")
            extra.alignToAlter(cont_Curve, contJoints[i], mode=2)
            cont_Curve_ORE = extra.createUpGrp(cont_Curve, "ORE")
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
                    poleGroups[-1].rotate >> blender.color1
                    poleGroups[0].rotate >> blender.color2
                    blender.outputR >> poleGroups[i].rotateX
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
            # self.attPassCont.volumeFactor >> volumeFactor.input1Y
            # self.attPassCont.volumeFactor >> volumeFactor.input1Z
            # volumeFactor.output >> volumePow.input2

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

            # curveInfo.arcLength >> curveGlobMult.input1X
            cmds.connectAttr("%s.arcLength" %curveInfo, "%s.input1X" %curveGlobMult)
            cmds.setAttr("%s.input[0]" %stretchSw, initialLength)
            # curveGlobMult.outputX >> stretchSw.input[1]
            cmds.connectAttr("%s.outputX" %curveGlobMult, "%s.input[1]" %stretchSw)


            # self.attPassCont.stretchy >> stretchSw.attributesBlender
            cmds.connectAttr("%s.stretchy" %self.attPassCont, "%s.attributesBlender" %stretchSw)


            # self.scaleGrp.sx >> curveGlobMult.input2X
            cmds.connectAttr("%s.sx" %self.scaleGrp, "%s.input2X" %curveGlobMult)


            # stretchSw.output >> lengthMult.input1X
            cmds.connectAttr("%s.output" %stretchSw, "%s.input1X" %lengthMult)


            cmds.setAttr("%s.input2X" %lengthMult, initialLength)

            # lengthMult.outputX >> boneGlobMult.input1X
            cmds.connectAttr("%s.outputX" %lengthMult, "%s.input1X" %boneGlobMult)

            # lengthMult.outputX >> volumePow.input1Y
            cmds.connectAttr("%s.outputX" %lengthMult, "%s.input1Y" %volumePow)

            # lengthMult.outputX >> volumePow.input1Z
            cmds.connectAttr("%s.outputX" %lengthMult, "%s.input1Z" %volumePow)

            cmds.setAttr("%s.color2G" %volumeSw, 1)
            cmds.setAttr("%s.color2B" %volumeSw, 1)
            # volumePow.outputY >> volumeSw.color1G
            cmds.connectAttr("%s.outputY" %volumePow, "%s.color1G" %volumeSw)

            # volumePow.outputZ >> volumeSw.color1B
            cmds.connectAttr("%s.outputZ" %volumePow, "%s.color1B" %volumeSw)

            # volumeSw.outputG >> boneGlobMult.input1Y
            cmds.connectAttr("%s.outputG" %volumeSw, "%s.input1Y" %boneGlobMult)

            # volumeSw.outputB >> boneGlobMult.input1Z
            cmds.connectAttr("%s.outputB" %volumeSw, "%s.input1Z" %boneGlobMult)

            # self.scaleGrp.sx >> boneGlobMult.input2X
            cmds.connectAttr("%s.sx" %self.scaleGrp, "%s.input2X" %boneGlobMult)

            # self.scaleGrp.sx >> boneGlobMult.input2Y
            cmds.connectAttr("%s.sx" %self.scaleGrp, "%s.input2Y" %boneGlobMult)

            # self.scaleGrp.sx >> boneGlobMult.input2Z
            cmds.connectAttr("%s.sx" %self.scaleGrp, "%s.input2Z" %boneGlobMult)

            # self.attPassCont.preserveVol >> volumeSw.blender
            cmds.connectAttr("%s.preserveVol" %self.attPassCont, "%s.blender" %volumeSw)

            # boneGlobMult.output >> IKjoints[i].scale
            cmds.connectAttr("%s.output" %boneGlobMult, "%s.scale" %IKjoints[i])

            # boneGlobMult.output >> self.defJoints[i].scale
            cmds.connectAttr("%s.output" %boneGlobMult, "%s.scale" %self.defJoints[i])

        # Create endLock
        self.endLock = cmds.spaceLocator(name="endLock_%s" %name)[0]
        cmds.pointConstraint(self.defJoints[len(self.defJoints) - 1], self.endLock, mo=False)

        ## Move them to original Positions

        # for o in range (0,len(self.contCurves_ORE)):
        #
        #     extra.alignToAlter(self.contCurves_ORE[o], refJoints[o])
        #     if not o == (len(self.contCurves_ORE)-1):
        #         tempAim = pm.aimConstraint(refJoints[o+1], self.contCurves_ORE[o], aimVector=(0,1,0), upVector=(0,1,0), mo=False)
        #     else:
        #         tempAim = pm.aimConstraint(refJoints[o-1], self.contCurves_ORE[o], aimVector=(0, -1, 0), upVector=(0, -1, 0), mo=False)
        #     pm.delete(tempAim)

        for o in range (0,len(self.contCurves_ORE)):
            if o == 0:
                extra.alignToAlter(self.contCurves_ORE[o], refJoints[o], mode=2)
            else:
                extra.alignToAlter(self.contCurves_ORE[o], refJoints[o], mode=0)
                extra.alignToAlter(self.contCurves_ORE[o], refJoints[o-1], mode=1)


        # GOOD PARENTING

        cmds.parent(contJoints, self.scaleGrp)
        cmds.parent(splineIK[0], self.nonScaleGrp)
        # import pdb
        # pdb.set_trace()
        # cmds.parent(splineCurve, self.nonScaleGrp)
        # cmds.parent(self.defJoints[0], self.nonScaleGrp)

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

