import pymel.core as pm
import extraProcedures as extra

reload(extra)

# import contIcons as icon
# reload(icon)

import icons as ic
reload(ic)

import ribbonClass as rc

reload(rc)

import twistSplineClass as twistSpline

reload(twistSpline)

import maya.cmds as cmds

import pymel.core.datatypes as dt

class Tentacle(object):

    def __init__(self, inits,
                       suffix="",
                       side="C",
                       npResolution=5.0,
                       jResolution=5.0,
                       blResolution=25.0,
                       dropoff=2.0):


        # reinitialize the initial Joints
        if not isinstance(inits, list):
            self.tentacleRoot = inits.get("TentacleRoot")
            self.tentacles = (inits.get("Tentacle"))
            self.inits = [self.tentacleRoot] + (self.tentacles)

        self.npResolution = 1.0 * npResolution
        self.jResolution = 1.0 * jResolution
        self.blResolution = 1.0 * blResolution
        self.dropoff = 1.0 * dropoff

        # fool proofing
        if len(inits)<2:
            pm.error("Tentacle setup needs at least 2 initial joints")
            return


        # get distances

        # get positions

        self.rootPos = self.inits[0].getTranslation(space="world")

        # initialize sides
        self.sideMult = -1 if side == "R" else 1
        self.side = side

        # initialize coordinates
        self.up_axis, self.mirror_axis, self.look_axis = extra.getRigAxes(self.inits[0])

        # initialize suffix
        self.suffix = (extra.uniqueName("limbGrp_%s" % suffix)).replace("limbGrp_", "")

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
        self.limbGrp = pm.group(name="limbGrp_%s" % self.suffix, em=True)
        self.scaleGrp = pm.group(name="scaleGrp_%s" % self.suffix, em=True)
        extra.alignTo(self.scaleGrp, self.inits[0], 0)
        self.nonScaleGrp = pm.group(name="NonScaleGrp_%s" % self.suffix, em=True)

        pm.addAttr(self.scaleGrp, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True)
        pm.addAttr(self.scaleGrp, at="bool", ln="Joints_Visibility", sn="jointVis", defaultValue=True)
        pm.addAttr(self.scaleGrp, at="bool", ln="Rig_Visibility", sn="rigVis", defaultValue=False)
        # make the created attributes visible in the channelbox
        pm.setAttr(self.scaleGrp.contVis, cb=True)
        pm.setAttr(self.scaleGrp.jointVis, cb=True)
        pm.setAttr(self.scaleGrp.rigVis, cb=True)

        pm.parent(self.scaleGrp, self.limbGrp)
        pm.parent(self.nonScaleGrp, self.limbGrp)


    def createJoints(self):

        pm.select(d=True)
        self.limbPlug = pm.joint(name="limbPlug_%s" % self.suffix, p=self.rootPos, radius=3)
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
            currentJointLength = extra.getDistance(self.inits[i], self.inits[tmin])
            ctrlDistance = currentJointLength + ctrlDistance
            self.totalLength += currentJointLength
            # this list contains distance between each control point
            contDistances.append(ctrlDistance)
        endVc = (self.rootPos.x, (self.rootPos.y + self.totalLength), self.rootPos.z)
        splitVc = endVc - self.rootPos

        ## Create Control Joints
        self.contJointsList = []
        pm.select(d=True)
        for i in range(0, len(contDistances)):
            ctrlVc = splitVc.normal() * contDistances[i]
            place = self.rootPos + (ctrlVc)
            j = pm.joint(p=place, name="jCont_tentacle_%s%s" %(self.suffix , str(i)), radius=5, o=(90, 0, 90))
            self.contJointsList.append(j)
            pm.select(d=True)

        ## Create temporaray Guide Joints
        pm.select(d=True)
        self.guideJoints = [pm.joint(p=i.getTranslation(space="world")) for i in self.inits]
        # orientations
        # extra.orientJoints(self.guideJoints,
        #                    localMoveAxis=self.sideMult * (dt.Vector(self.up_axis)),
        #                    mirrorAxis=(self.sideMult, 0.0, 0.0), upAxis=self.sideMult * (dt.Vector(self.look_axis)))
        extra.orientJoints(self.guideJoints, worldUpAxis=(self.up_axis), reverse=self.sideMult)


        pm.select(d=True)
        self.wrapScaleJoint = pm.joint(name="jWrapScale_{0}".format(self.suffix))

        pm.parent(self.contJointsList, self.scaleGrp)
        pm.parent(self.wrapScaleJoint, self.scaleGrp)

        map(lambda x: pm.connectAttr(self.scaleGrp.rigVis, x.v), self.contJointsList)
        self.scaleGrp.rigVis >> self.wrapScaleJoint.v

        pass

    def createControllers(self):

        icon = ic.Icon()
        ## specialController
        iconScale = extra.getDistance(self.inits[0], self.inits[1])/3
        # self.cont_special = icon.looper(name="tentacleSP_%s" % self.suffix)
        self.cont_special, dmp = icon.createIcon("Looper", iconName="tentacleSP_%s" % self.suffix, scale=(iconScale, iconScale, iconScale))
        extra.alignAndAim(self.cont_special, targetList = [self.inits[0]], aimTargetList=[self.inits[-1]], upVector=self.up_axis, rotateOff=(90,0,0))
        pm.move(self.cont_special, (dt.Vector(self.up_axis) *(iconScale*2)), r=True)

        cont_special_ORE = extra.createUpGrp(self.cont_special,"ORE")

        ## seperator - curl
        pm.addAttr(self.cont_special, shortName="curlSeperator", at="enum", en="----------", k=True)
        pm.setAttr(self.cont_special.curlSeperator, lock=True)

        pm.addAttr(self.cont_special, shortName="curl", longName="Curl", defaultValue=0.0, minValue=-10.0, maxValue=10.0, at="float",
                   k=True)
        pm.addAttr(self.cont_special, shortName="curlSize", longName="Curl_Size", defaultValue=1.0, at="float", k=True)

        pm.addAttr(self.cont_special, shortName="curlAngle", longName="Curl_Angle", defaultValue=1.0, at="float",
                   k=True)
        pm.addAttr(self.cont_special, shortName="curlDirection", longName="Curl_Direction", defaultValue=0.0, at="float",
                   k=True)

        pm.addAttr(self.cont_special, shortName="curlShift", longName="Curl_Shift", defaultValue=0.0, at="float",
                   k=True)


        ## seperator - twist
        pm.addAttr(self.cont_special, shortName="twistSeperator", at="enum", en="----------", k=True)
        pm.setAttr(self.cont_special.twistSeperator, lock=True)

        pm.addAttr(self.cont_special, shortName="twistAngle", longName="Twist_Angle", defaultValue=0.0, at="float",
                   k=True)
        pm.addAttr(self.cont_special, shortName="twistSlide", longName="Twist_Slide", defaultValue=0.0, at="float",
                   k=True)
        pm.addAttr(self.cont_special, shortName="twistArea", longName="Twist_Area", defaultValue=1.0, at="float",
                   k=True)

        ## seperator - sine
        pm.addAttr(self.cont_special, shortName="sineSeperator", at="enum", en="----------", k=True)
        pm.setAttr(self.cont_special.sineSeperator, lock=True)
        pm.addAttr(self.cont_special, shortName="sineAmplitude", longName="Sine_Amplitude", defaultValue=0.0, at="float",
                   k=True)
        pm.addAttr(self.cont_special, shortName="sineWavelength", longName="Sine_Wavelength", defaultValue=1.0, at="float",
                   k=True)
        pm.addAttr(self.cont_special, shortName="sineDropoff", longName="Sine_Dropoff", defaultValue=0.0, at="float",
                   k=True)
        pm.addAttr(self.cont_special, shortName="sineSlide", longName="Sine_Slide", defaultValue=0.0, at="float",
                   k=True)
        pm.addAttr(self.cont_special, shortName="sineArea", longName="Sine_area", defaultValue=1.0, at="float",
                   k=True)
        pm.addAttr(self.cont_special, shortName="sineDirection", longName="Sine_Direction", defaultValue=0.0, at="float",
                   k=True)

        pm.addAttr(self.cont_special, shortName="sineAnimate", longName="Sine_Animate", defaultValue=0.0, at="float",
                   k=True)

        self.contFK_List = []
        self.contTwk_List = []

        for j in range (len(self.guideJoints)):
            s = pm.getAttr(self.guideJoints[j].tx)/3
            s = iconScale if s == 0 else s
            scaleTwk = (s, s, s)
            # contTwk = icon.circle("cont_tentacleTweak{0}_{1}".format(str(j), self.suffix), scaleTwk, normal=(0,0,1))
            contTwk, dmp = icon.createIcon("Circle", iconName="cont_tentacleTweak{0}_{1}".format(str(j), self.suffix), scale=scaleTwk, normal=self.mirror_axis)
            extra.alignToAlter(contTwk, self.guideJoints[j], mode=2)
            contTwk_OFF = extra.createUpGrp(contTwk, "OFF")
            contTwk_ORE = extra.createUpGrp(contTwk, "ORE")
            self.contTwk_List.append(contTwk)

            scaleFK = (s*1.2, s*1.2, s*1.2)
            # contFK = icon.ngon("cont_tentacleFK{0}_{1}".format(str(j), self.suffix), scaleFK, normal=(0,0,1))
            contFK, dmp = icon.createIcon("Ngon", iconName="cont_tentacleFK{0}_{1}".format(str(j), self.suffix), scale=scaleFK, normal=self.mirror_axis)
            extra.alignToAlter(contFK, self.guideJoints[j], mode=2)
            contFK_OFF = extra.createUpGrp(contFK, "OFF")
            contFK_ORE = extra.createUpGrp(contFK, "ORE")
            self.contFK_List.append(contFK)

            pm.parent(contTwk_OFF, contFK)
            if not j == 0:
                pm.parent(contFK_OFF, self.contFK_List[j - 1])
            else:
                pm.parent(contFK_OFF, self.scaleGrp)

        pm.parent(cont_special_ORE, self.contFK_List[0])

        extra.colorize(self.contFK_List, self.colorCodes[0])
        extra.colorize(self.contTwk_List, self.colorCodes[0])
        extra.colorize(self.cont_special, self.colorCodes[0])

        map(lambda x: pm.connectAttr(self.scaleGrp.contVis, x.v), self.contTwk_List)
        map(lambda x: pm.connectAttr(self.scaleGrp.contVis, x.v), self.contFK_List)

    def createRoots(self):
        pass

    def createIKsetup(self):
        ## Create the Base Nurbs Plane (npBase)
        ribbonLength = extra.getDistance(self.contJointsList[0], self.contJointsList[-1])
        npBase=pm.nurbsPlane(ax=(0,1,0),u=self.npResolution,v=1, w=ribbonLength, lr=(1.0/ribbonLength), name="npBase_%s" % self.suffix)
        pm.rebuildSurface (npBase, ch=1, rpo=1, rt=0, end=1, kr=2, kcp=0, kc=0, su=5, du=3, sv=1, dv=1, tol=0, fr=0, dir=1)
        extra.alignAndAim(npBase, targetList=[self.contJointsList[0], self.contJointsList[-1]], aimTargetList=[self.contJointsList[-1]], upVector=self.up_axis)

        ## Duplicate the Base Nurbs Plane as joint Holder (npJDefHolder)
        npJdefHolder = pm.nurbsPlane(ax=(0, 1, 0), u=self.blResolution, v=1, w=ribbonLength, lr=(1.0 / ribbonLength),
                               name="npJDefHolder_%s" % self.suffix)
        pm.rebuildSurface(npJdefHolder, ch=1, rpo=1, rt=0, end=1, kr=2, kcp=0, kc=0, su=5, du=3, sv=1, dv=1, tol=0, fr=0,
                          dir=1)
        extra.alignAndAim(npJdefHolder, targetList=[self.contJointsList[0], self.contJointsList[-1]], aimTargetList=[self.contJointsList[-1]],
                          upVector=self.up_axis)

        ## Create the follicles on the npJDefHolder
        npJdefHolderShape = npJdefHolder[0].getShape()
        # self.toHide.append(npJdefHolder[0])
        follicleList = []
        for i in range (0, int(self.jResolution)):
            follicle = pm.createNode('follicle', name="follicle_{0}{1}".format(self.suffix, str(i)))
            npJdefHolderShape.local.connect(follicle.inputSurface)
            npJdefHolderShape.worldMatrix[0].connect(follicle.inputWorldMatrix)
            follicle.outRotate.connect(follicle.getParent().rotate)
            follicle.outTranslate.connect(follicle.getParent().translate)
            follicle.parameterV.set(0.5)
            follicle.parameterU.set((1/self.jResolution)+(i/self.jResolution)-((1/self.jResolution)/2))
            follicle.getParent().t.lock()
            follicle.getParent().r.lock()
            follicleList.append(follicle)
            defJ=pm.joint(name="jDef_{0}{1}".format(self.suffix,str(i)))
            pm.joint(defJ, e=True, zso=True, oj='zxy')
            self.deformerJoints.append(defJ)
            self.sockets.append(defJ)
            pm.parent(follicle.getParent(), self.nonScaleGrp)
            pm.scaleConstraint(self.scaleGrp, follicle.getParent(), mo=True)

        # create follicles for scaling calculations
        follicle_sca_list = []
        counter=0
        for i in range (0, int(self.jResolution)):
            s_follicle = pm.createNode('follicle', name="follicleSCA_{0}{1}".format(self.suffix, i))
            npJdefHolderShape.local.connect(s_follicle.inputSurface)
            npJdefHolderShape.worldMatrix[0].connect(s_follicle.inputWorldMatrix)
            s_follicle.outRotate.connect(s_follicle.getParent().rotate)
            s_follicle.outTranslate.connect(s_follicle.getParent().translate)
            s_follicle.parameterV.set(0.0)
            s_follicle.parameterU.set((1/self.jResolution)+(i/self.jResolution)-((1/self.jResolution)/2))
            s_follicle.getParent().t.lock()
            s_follicle.getParent().r.lock()
            follicle_sca_list.append(s_follicle)
            pm.parent(s_follicle.getParent(), self.nonScaleGrp)
            # self.toHide.append(s_follicle)
            # create distance node
            distNode = pm.createNode("distanceBetween", name="fDistance_{0}{1}".format(self.suffix, i))
            follicleList[counter].outTranslate >> distNode.point1
            s_follicle.outTranslate >> distNode.point2

            multiplier = pm.createNode("multDoubleLinear", name="fMult_{0}{1}".format(self.suffix, i))
            distNode.distance >> multiplier.input1
            pm.setAttr(multiplier.input2, 2)

            global_divide = pm.createNode("multiplyDivide", name= "fGlobDiv_{0}{1}".format(self.suffix, i))
            pm.setAttr(global_divide.operation, 2)
            multiplier.output >> global_divide.input1X
            self.scaleGrp.scaleX >> global_divide.input2X

            global_divide.outputX >> self.deformerJoints[counter].scaleX
            global_divide.outputX >> self.deformerJoints[counter].scaleY
            global_divide.outputX >> self.deformerJoints[counter].scaleZ

            counter += 1

        ## Duplicate it 3 more times for deformation targets (npDeformers, npTwist, npSine)

        npDeformers = pm.duplicate(npJdefHolder[0], name="npDeformers_%s" % self.suffix)
        pm.move(npDeformers[0], (0, self.totalLength/2, 0))
        pm.rotate(npDeformers[0], (0, 0, 90))

        ## Create Blendshape node between np_jDefHolder and deformation targets
        npBlend = pm.blendShape(npDeformers, npJdefHolder[0], w=(0,1))

        ## Wrap npjDefHolder to the Base Plane
        npWrap, npWrapGeo = self.createWrap(npBase[0], npJdefHolder[0],weightThreshold=0.0, maxDistance=50, autoWeightThreshold=False)
        maxDistanceMult = pm.createNode("multDoubleLinear", name="npWrap_{0}".format(self.suffix))
        self.scaleGrp.scaleX >> maxDistanceMult.input1
        pm.setAttr(maxDistanceMult.input2, 50)
        maxDistanceMult.output >> npWrap.maxDistance

        ## make the Wrap node Scale-able with the rig
        pm.skinCluster(self.wrapScaleJoint, npWrapGeo, tsb=True)

        ## Create skin cluster
        pm.skinCluster(self.contJointsList, npBase[0], tsb=True, dropoffRate=self.dropoff)

        ## CURL DEFORMER
        curlDeformer = pm.nonLinear(npDeformers, type='bend', curvature=1500)
        curlLoc = pm.spaceLocator(name="curlLoc{0}".format(self.suffix))
        pm.parent(curlDeformer[1], curlLoc)
        pm.setAttr(curlDeformer[0].lowBound, -1)
        pm.setAttr(curlDeformer[0].highBound, 0)

        pm.setDrivenKeyframe(curlDeformer[0].curvature, cd=self.cont_special.curl, v=0.0, dv=0.0, itt='linear', ott='linear')
        pm.setDrivenKeyframe(curlDeformer[0].curvature, cd=self.cont_special.curl, v=1500.0, dv=0.01, itt='linear', ott='linear')
        pm.setDrivenKeyframe(curlDeformer[0].curvature, cd=self.cont_special.curl, v=-1500.0, dv=-0.01, itt='linear', ott='linear')

        pm.setDrivenKeyframe(curlDeformer[1].ty, cd=self.cont_special.curl, v=0.0, dv=10.0, itt='linear', ott='linear')
        pm.setDrivenKeyframe(curlDeformer[1].ty, cd=self.cont_special.curl, v=0.0, dv=-10.0, itt='linear', ott='linear')
        pm.setDrivenKeyframe([curlDeformer[1].sx, curlDeformer[1].sy, curlDeformer[1].sz], cd=self.cont_special.curl, v=(self.totalLength * 2), dv=10.0, itt='linear', ott='linear')
        pm.setDrivenKeyframe([curlDeformer[1].sx, curlDeformer[1].sy, curlDeformer[1].sz], cd=self.cont_special.curl, v=(self.totalLength * 2), dv=-10.0, itt='linear', ott='linear')
        pm.setDrivenKeyframe(curlDeformer[1].rz, cd=self.cont_special.curl, v=4.0, dv=10.0, itt='linear', ott='linear')
        pm.setDrivenKeyframe(curlDeformer[1].rz, cd=self.cont_special.curl, v=-4.0, dv=-10.0, itt='linear', ott='linear')

        pm.setDrivenKeyframe(curlDeformer[1].ty, cd=self.cont_special.curl, v=self.totalLength, dv=0.0, itt='linear', ott='linear')
        pm.setDrivenKeyframe([curlDeformer[1].sx, curlDeformer[1].sy, curlDeformer[1].sz], cd=self.cont_special.curl, v=(self.totalLength / 2), dv=0.0, itt='linear', ott='linear')
        pm.setDrivenKeyframe(curlDeformer[1].rz, cd=self.cont_special.curl, v=6.0, dv=0.01, itt='linear', ott='linear')
        pm.setDrivenKeyframe(curlDeformer[1].rz, cd=self.cont_special.curl, v=-6.0, dv=-0.01, itt='linear', ott='linear')

        ## create curl size multipliers

        curlSizeMultX = pm.createNode("multDoubleLinear", name="curlSizeMultX_{0}".format(self.suffix))
        curlSizeMultY = pm.createNode("multDoubleLinear", name="curlSizeMultY_{0}".format(self.suffix))
        curlSizeMultZ = pm.createNode("multDoubleLinear", name="curlSizeMultZ_{0}".format(self.suffix))

        curlAngleMultZ = pm.createNode("multDoubleLinear", name="curlAngleMultZ_{0}".format(self.suffix))

        curlShiftAdd = pm.createNode("plusMinusAverage", name="curlAddShift_{0}".format(self.suffix))
        self.cont_special.curlShift >> curlShiftAdd.input1D[0]
        pm.setAttr(curlShiftAdd.input1D[1], 180)
        curlShiftAdd.output1D >> curlDeformer[1].rx

        self.cont_special.curlSize >> curlSizeMultX.input1
        self.cont_special.curlSize >> curlSizeMultY.input1
        self.cont_special.curlSize >> curlSizeMultZ.input1

        self.cont_special.curlAngle >> curlAngleMultZ.input1


        pm.listConnections(curlDeformer[1].sx)[0].output >> curlSizeMultX.input2
        pm.listConnections(curlDeformer[1].sy)[0].output >> curlSizeMultY.input2
        pm.listConnections(curlDeformer[1].sz)[0].output >> curlSizeMultZ.input2

        pm.listConnections(curlDeformer[1].rz)[0].output >> curlAngleMultZ.input2

        curlSizeMultX.output >> curlDeformer[1].sx
        curlSizeMultY.output >> curlDeformer[1].sy
        curlSizeMultZ.output >> curlDeformer[1].sz

        curlAngleMultZ.output >> curlDeformer[1].rz

        self.cont_special.curlDirection >> curlLoc.ry

        ## TWIST DEFORMER
        twistDeformer = pm.nonLinear(npDeformers, type='twist')
        pm.rotate(twistDeformer[1], (0,0,0))
        twistLoc = pm.spaceLocator(name="twistLoc_{0}".format(self.suffix))
        pm.parent(twistDeformer[1], twistLoc)

        ## make connections:
        self.cont_special.twistAngle >> twistDeformer[0].endAngle
        self.cont_special.twistSlide >> twistLoc.translateY
        self.cont_special.twistArea >> twistLoc.scaleY

        ## SINE DEFORMER
        sineDeformer = pm.nonLinear(npDeformers, type='sine')
        pm.rotate(sineDeformer[1], (0,0,0))
        sineLoc = pm.spaceLocator(name="sineLoc_{0}".format(self.suffix))
        pm.parent(sineDeformer[1], sineLoc)

        ## make connections:
        self.cont_special.sineAmplitude >> sineDeformer[0].amplitude
        self.cont_special.sineWavelength >> sineDeformer[0].wavelength
        self.cont_special.sineDropoff >> sineDeformer[0].dropoff
        self.cont_special.sineAnimate >> sineDeformer[0].offset

        self.cont_special.sineSlide >> sineLoc.translateY
        self.cont_special.sineArea >> sineLoc.scaleY

        self.cont_special.sineDirection >> sineLoc.rotateY

        for j in range(len(self.guideJoints)):
            extra.alignToAlter(self.contJointsList[j], self.guideJoints[j], mode=2)
            pm.parentConstraint(self.contTwk_List[j], self.contJointsList[j], mo=False)
            pm.scaleConstraint(self.contTwk_List[j], self.contJointsList[j], mo=False)

        pm.parent(npBase[0], self.nonScaleGrp)
        pm.parent(npDeformers[0], self.nonScaleGrp)
        pm.parent(curlLoc, self.nonScaleGrp)
        pm.parent(twistLoc, self.nonScaleGrp)
        pm.parent(sineLoc,self.nonScaleGrp)
        pm.parent(npWrapGeo, self.nonScaleGrp)
        pm.parent(npJdefHolder[0], self.scaleGrp)

        nodesRigVis = [npBase[0], npJdefHolder[0], npDeformers[0], sineLoc, twistLoc, curlLoc]
        map(lambda x: pm.connectAttr(self.scaleGrp.rigVis, x.v), nodesRigVis)
        map(lambda x: pm.connectAttr(self.scaleGrp.rigVis, x.v), follicle_sca_list)
        map(lambda x: pm.connectAttr(self.scaleGrp.rigVis, x.v), follicleList)

        extra.colorize(self.deformerJoints, self.colorCodes[0], shape=False)

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
        pm.parentConstraint(self.limbPlug, self.scaleGrp, mo=False)
        pm.setAttr(self.scaleGrp.rigVis, 0)

        map(lambda x: extra.lockAndHide(x, ["sx", "sy", "sz"]), self.contFK_List)
        self.scaleConstraints = [self.scaleGrp]

        pm.delete(self.guideJoints)

    def createLimb(self):
        self.createGrp()
        self.createJoints()
        self.createControllers()
        self.createRoots()
        self.createIKsetup()
        self.roundUp()

    def createWrap(self, *args, **kwargs):

        influence = args[0].name()
        surface = args[1].name()

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
        # return wrapNode
        return pm.nt.Wrap(wrapNode), base


