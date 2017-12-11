import pymel.core as pm
import extraProcedures as extra

reload(extra)

import contIcons as icon

reload(icon)

import ribbonClass as rc

reload(rc)

import twistSplineClass as twistSpline

reload(twistSpline)

import maya.cmds as cmds

import pymel.core.datatypes as dt

class Tentacle(object):

    def __init__(self):
        self.scaleGrp = None
        self.limbPlug = None
        self.nonScaleGrp = None
        self.cont_IK_OFF = None
        self.sockets = []
        self.scaleConstraints = []
        self.anchors = []
        self.anchorLocations = []

    def createTentacle(self, inits, suffix="", side="C", npResolution=5.0, jResolution=5.0, blResolution=25.0, dropoff=2.0):
        if not isinstance(inits, list):
            tentacleRoot = inits.get("TentacleRoot")
            tentacles = (inits.get("Tentacle"))
            inits = [tentacleRoot] + (tentacles)

        npResolution=1.0*npResolution
        jResolution = 1.0 * jResolution

        ## Make sure the suffix is unique
        idCounter=0
        while pm.objExists("scaleGrp_" + suffix):
            suffix = "%s%s" % (suffix, str(idCounter + 1))

        if len(inits)<2:
            pm.error("Tentacle setup needs at least 2 initial joints")
            return
        rootPoint = inits[0].getTranslation(space="world")

        ## Create Groups
        self.scaleGrp = pm.group(name="scaleGrp_" + suffix, em=True)
        extra.alignTo(self.scaleGrp, inits[0], 0)
        self.nonScaleGrp = pm.group(name="NonScaleGrp_" + suffix, em=True)

        ## Get the orientation axises
        upAxis, mirroAxis, spineDir = extra.getRigAxes(inits[0])

        ## Create Controller Curves

        ## specialController
        iconScale = extra.getDistance(inits[0], inits[1])/3
        cont_special = icon.looper(name="tentacleSP_" + suffix)
        extra.alignAndAim(cont_special, targetList = [inits[0]], aimTargetList = [inits[-1]], upVector=upAxis, rotateOff=(90,0,0))
        pm.move(cont_special, (dt.Vector(upAxis) *(iconScale*2)), r=True)

        # extra.alignAndAim(cont_special , targetList=[inits[0]], aimTargetList=[inits[1]], upVector=upAxis,
        #                   translateOff=(0,0,0), rotateOff=(90,90,0))
        # pm.move(cont_special, (3, 0, 0), r=True, os=True)

        cont_special_ORE = extra.createUpGrp(cont_special,"ORE")

        ## seperator - curl
        pm.addAttr(cont_special, shortName="curlSeperator", at="enum", en="----------", k=True)
        pm.setAttr(cont_special.curlSeperator, lock=True)

        pm.addAttr(cont_special, shortName="curl", longName="Curl", defaultValue=0.0, minValue=-10.0, maxValue=10.0, at="float",
                   k=True)
        pm.addAttr(cont_special, shortName="curlSize", longName="Curl_Size", defaultValue=1.0, at="float", k=True)

        pm.addAttr(cont_special, shortName="curlAngle", longName="Curl_Angle", defaultValue=1.0, at="float",
                   k=True)

        pm.addAttr(cont_special, shortName="curlShift", longName="Curl_Shift", defaultValue=0.0, at="float",
                   k=True)


        ## seperator - twist
        pm.addAttr(cont_special, shortName="twistSeperator", at="enum", en="----------", k=True)
        pm.setAttr(cont_special.twistSeperator, lock=True)

        pm.addAttr(cont_special, shortName="twistAngle", longName="Twist_Angle", defaultValue=0.0, at="float",
                   k=True)
        pm.addAttr(cont_special, shortName="twistSlide", longName="Twist_Slide", defaultValue=0.0, at="float",
                   k=True)
        pm.addAttr(cont_special, shortName="twistArea", longName="Twist_Area", defaultValue=1.0, at="float",
                   k=True)

        ## seperator - sine
        pm.addAttr(cont_special, shortName="sineSeperator", at="enum", en="----------", k=True)
        pm.setAttr(cont_special.sineSeperator, lock=True)
        pm.addAttr(cont_special, shortName="sineAmplitude", longName="Sine_Amplitude", defaultValue=0.0, at="float",
                   k=True)
        pm.addAttr(cont_special, shortName="sineWavelength", longName="Sine_Wavelength", defaultValue=1.0, at="float",
                   k=True)
        pm.addAttr(cont_special, shortName="sineDropoff", longName="Sine_Dropoff", defaultValue=0.0, at="float",
                   k=True)
        pm.addAttr(cont_special, shortName="sineSlide", longName="Sine_Slide", defaultValue=0.0, at="float",
                   k=True)
        pm.addAttr(cont_special, shortName="sineArea", longName="Sine_area", defaultValue=1.0, at="float",
                   k=True)

        pm.addAttr(cont_special, shortName="sineAnimate", longName="Sine_Animate", defaultValue=0.0, at="float",
                   k=True)

        contFK_List = []
        contTwk_List = []
        for j in range (len(inits)):

            if not j == (len(inits)-1):
                targetInit = inits[j+1]
                rotateOff = (90,90,0)
            else:
                targetInit = inits[j-1]
                rotateOff = (-90,-90, 180)
            s = extra.getDistance(inits[j], targetInit)/3
            contScaleTwk = (s, s, s)
            contTwk = icon.circle("cont_tentacleTweak{0}_{1}".format(str(j), suffix), contScaleTwk)
            extra.alignAndAim(contTwk, targetList=[inits[j]], aimTargetList=[targetInit], upVector=upAxis, rotateOff=rotateOff)
            contTwk_OFF = extra.createUpGrp(contTwk, "OFF")
            contTwk_ORE = extra.createUpGrp(contTwk, "ORE")
            contTwk_List.append(contTwk)

            contScaleFK = (s*1.2, s*1.2, s*1.2)
            contFK = icon.ngon("cont_tentacleFK{0}_{1}".format(str(j), suffix), contScaleFK)
            extra.alignAndAim(contFK, targetList=[inits[j]], aimTargetList=[targetInit], upVector=upAxis,
                          rotateOff=rotateOff)
            contFK_OFF = extra.createUpGrp(contFK, "OFF")
            contFK_ORE = extra.createUpGrp(contFK, "ORE")
            if side == "R":
                pm.setAttr("{0}.s{1}".format(contFK_ORE, "x"), -1)
            contFK_List.append(contFK)

            pm.parent(contTwk_OFF, contFK)
            if not j == 0:
                pm.parent(contFK_OFF, contFK_List[j-1])
            else:
                pm.parent(contFK_OFF, self.scaleGrp)

        ## Make a straight line from inits joints (like in the twistSpline)
        # calculate the necessary distance for the joints
        totalLength = 0
        contDistances = []
        ctrlDistance = 0
        for i in range(0, len(inits)):
            if i == 0:
                tmin = 0
            else:
                tmin = i - 1
            currentJointLength = extra.getDistance(inits[i], inits[tmin])
            ctrlDistance = currentJointLength + ctrlDistance
            totalLength += currentJointLength
            # this list contains distance between each control point
            contDistances.append(ctrlDistance)
        endVc = (rootPoint.x, (rootPoint.y + totalLength), rootPoint.z)
        splitVc = endVc - rootPoint

        ## Create Control Joints
        contJointsList = []
        pm.select(d=True)
        for i in range(0, len(contDistances)):
            ctrlVc = splitVc.normal() * contDistances[i]
            place = rootPoint + (ctrlVc)
            j = pm.joint(p=place, name="jCont_tentacle_" + suffix + str(i), radius=5, o=(0, 0, 0))
            contJointsList.append(j)
            pm.select(d=True)

        ## Create the Base Nurbs Plane (npBase)
        ribbonLength = extra.getDistance(contJointsList[0], contJointsList[-1])
        npBase=pm.nurbsPlane(ax=(0,1,0),u=npResolution,v=1, w=ribbonLength, lr=(1.0/ribbonLength), name="npBase_"+suffix)
        pm.rebuildSurface (npBase, ch=1, rpo=1, rt=0, end=1, kr=2, kcp=0, kc=0, su=5, du=3, sv=1, dv=1, tol=0, fr=0, dir=1)
        extra.alignAndAim(npBase, targetList=[contJointsList[0], contJointsList[-1]], aimTargetList=[contJointsList[-1]], upVector=spineDir)

        ## Duplicate the Base Nurbs Plane as joint Holder (npJDefHolder)
        npJdefHolder = pm.nurbsPlane(ax=(0, 1, 0), u=blResolution, v=1, w=ribbonLength, lr=(1.0 / ribbonLength),
                               name="npJDefHolder_" + suffix)
        pm.rebuildSurface(npJdefHolder, ch=1, rpo=1, rt=0, end=1, kr=2, kcp=0, kc=0, su=5, du=3, sv=1, dv=1, tol=0, fr=0,
                          dir=1)
        extra.alignAndAim(npJdefHolder, targetList=[contJointsList[0], contJointsList[-1]], aimTargetList=[contJointsList[-1]],
                          upVector=spineDir)

        # npJdefHolder = pm.duplicate(npBase[0], name="npJDefHolder_"+suffix)

        ## Create the follicles on the npJDefHolder
        npJdefHolderShape = npJdefHolder[0].getShape()
        self.deformerJoints = []
        # self.toHide.append(npJdefHolder[0])
        follicleList = []
        for i in range (0, int(jResolution)):
            follicle = pm.createNode('follicle', name="follicle_{0}{1}".format(suffix, str(i)))
            npJdefHolderShape.local.connect(follicle.inputSurface)
            npJdefHolderShape.worldMatrix[0].connect(follicle.inputWorldMatrix)
            follicle.outRotate.connect(follicle.getParent().rotate)
            follicle.outTranslate.connect(follicle.getParent().translate)
            follicle.parameterV.set(0.5)
            follicle.parameterU.set((1/jResolution)+(i/jResolution)-((1/jResolution)/2))
            follicle.getParent().t.lock()
            follicle.getParent().r.lock()
            follicleList.append(follicle)
            defJ=pm.joint(name="jDef_{0}{1}".format(suffix,str(i)))
            pm.joint(defJ, e=True, zso=True, oj='zxy')
            self.deformerJoints.append(defJ)
            self.sockets.append(defJ)
            pm.parent(follicle.getParent(), self.nonScaleGrp)
            pm.scaleConstraint(self.scaleGrp, follicle.getParent(), mo=True)
            # self.toHide.append(follicle)

        ## Duplicate it 3 more times for deformation targets (npDeformers, npTwist, npSine)

        npDeformers = pm.duplicate(npJdefHolder[0], name="npDeformers_"+suffix)
        pm.move(npDeformers[0], (0,totalLength/2,0))
        pm.rotate(npDeformers[0], (0,0,90))

        ## Create Blendshape node between np_jDefHolder and deformation targets
        npBlend = pm.blendShape(npDeformers, npJdefHolder[0], w=(0,1))

        ## Wrap npjDefHolder to the Base Plane
        # npWrap = pm.deformer(type="wrap", g=npJdefHolder)
        npWrap, npWrapGeo = self.createWrap(npBase[0], npJdefHolder[0],weightThreshold=0.0, maxDistance=50, autoWeightThreshold=False)

        ## make the Wrap node Scale-able with the rig
        pm.select(d=True)
        wrapScaleJoint = pm.joint(name="jWrapScale_{0}".format(suffix))
        pm.skinCluster(wrapScaleJoint, npWrapGeo, tsb=True)

        ## Create skin cluster
        pm.skinCluster(contJointsList, npBase[0], tsb=True, dropoffRate=dropoff)

        ## CURL DEFORMER
        # pm.select(npDeformers)
        curlDeformer = pm.nonLinear(npDeformers, type='bend', curvature=1500)

        # pm.select(curlDeformer)
        # pm.setAttr(curlDeformer[1].rz, 4)
        pm.setAttr(curlDeformer[0].lowBound, -1)
        pm.setAttr(curlDeformer[0].highBound, 0)
        ## Ratio is:
        order = [1, -1]
        # if side == "R":
        #     order=[-1, 1]
        # else:
        #     order=[1, -1]
        pm.setDrivenKeyframe(curlDeformer[0].curvature, cd=cont_special.curl, v=0.0, dv=0.0, itt='linear', ott='linear')
        pm.setDrivenKeyframe(curlDeformer[0].curvature, cd=cont_special.curl, v=1500.0, dv=0.01, itt='linear', ott='linear')
        pm.setDrivenKeyframe(curlDeformer[0].curvature, cd=cont_special.curl, v=-1500.0, dv=-0.01, itt='linear', ott='linear')

        pm.setDrivenKeyframe(curlDeformer[1].ty, cd=cont_special.curl, v=0.0, dv=10.0, itt='linear', ott='linear')
        pm.setDrivenKeyframe(curlDeformer[1].ty, cd=cont_special.curl, v=0.0, dv=-10.0, itt='linear', ott='linear')
        pm.setDrivenKeyframe([curlDeformer[1].sx, curlDeformer[1].sy, curlDeformer[1].sz], cd=cont_special.curl, v=(totalLength * 2), dv=10.0, itt='linear', ott='linear')
        pm.setDrivenKeyframe([curlDeformer[1].sx, curlDeformer[1].sy, curlDeformer[1].sz], cd=cont_special.curl, v=(totalLength * 2), dv=-10.0, itt='linear', ott='linear')
        pm.setDrivenKeyframe(curlDeformer[1].rz, cd=cont_special.curl, v=4.0*order[0], dv=10.0, itt='linear', ott='linear')
        pm.setDrivenKeyframe(curlDeformer[1].rz, cd=cont_special.curl, v=4.0*order[1], dv=-10.0, itt='linear', ott='linear')

        pm.setDrivenKeyframe(curlDeformer[1].ty, cd=cont_special.curl, v=totalLength, dv=0.0, itt='linear', ott='linear')
        pm.setDrivenKeyframe([curlDeformer[1].sx, curlDeformer[1].sy, curlDeformer[1].sz], cd=cont_special.curl, v=(totalLength / 2), dv=0.0, itt='linear', ott='linear')
        pm.setDrivenKeyframe(curlDeformer[1].rz, cd=cont_special.curl, v=6.0, dv=0.01, itt='linear', ott='linear')
        pm.setDrivenKeyframe(curlDeformer[1].rz, cd=cont_special.curl, v=-6.0, dv=-0.01, itt='linear', ott='linear')

        ## create curl size multipliers

        curlSizeMultX = pm.createNode("multDoubleLinear", name="curlSizeMultX_{0}".format(suffix))
        curlSizeMultY = pm.createNode("multDoubleLinear", name="curlSizeMultY_{0}".format(suffix))
        curlSizeMultZ = pm.createNode("multDoubleLinear", name="curlSizeMultZ_{0}".format(suffix))

        curlAngleMultZ = pm.createNode("multDoubleLinear", name="curlAngleMultZ_{0}".format(suffix))

        curlShiftAdd = pm.createNode("plusMinusAverage", name="curlAddShift_{0}".format(suffix))
        cont_special.curlShift >> curlShiftAdd.input1D[0]
        pm.setAttr(curlShiftAdd.input1D[1], 180)
        curlShiftAdd.output1D >> curlDeformer[1].rx

        cont_special.curlSize >> curlSizeMultX.input1
        cont_special.curlSize >> curlSizeMultY.input1
        cont_special.curlSize >> curlSizeMultZ.input1

        cont_special.curlAngle >> curlAngleMultZ.input1


        pm.listConnections(curlDeformer[1].sx)[0].output >> curlSizeMultX.input2
        pm.listConnections(curlDeformer[1].sy)[0].output >> curlSizeMultY.input2
        pm.listConnections(curlDeformer[1].sz)[0].output >> curlSizeMultZ.input2

        pm.listConnections(curlDeformer[1].rz)[0].output >> curlAngleMultZ.input2

        curlSizeMultX.output >> curlDeformer[1].sx
        curlSizeMultY.output >> curlDeformer[1].sy
        curlSizeMultZ.output >> curlDeformer[1].sz

        curlAngleMultZ.output >> curlDeformer[1].rz

        # cont_special.curlShift >> curlDeformer[1].rx

        ## TWIST DEFORMER
        twistDeformer = pm.nonLinear(npDeformers, type='twist')
        pm.rotate(twistDeformer[1], (0,0,0))
        twistLoc = pm.spaceLocator(name="twistLoc_{0}".format(suffix))
        # extra.alignTo(twistLoc, inits[0])
        pm.parent(twistDeformer[1], twistLoc)

        ## make connections:
        cont_special.twistAngle >> twistDeformer[0].endAngle
        cont_special.twistSlide >> twistLoc.translateY
        cont_special.twistArea >> twistLoc.scaleY


        ## SINE DEFORMER
        sineDeformer = pm.nonLinear(npDeformers, type='sine')
        pm.rotate(sineDeformer[1], (0,0,0))
        sineLoc = pm.spaceLocator(name="sineLoc_{0}".format(suffix))
        # extra.alignTo(sineLoc, inits[0])
        pm.parent(sineDeformer[1], sineLoc)

        ## make connections:
        cont_special.sineAmplitude >> sineDeformer[0].amplitude
        cont_special.sineWavelength >> sineDeformer[0].wavelength
        cont_special.sineDropoff >> sineDeformer[0].dropoff
        cont_special.sineAnimate >> sineDeformer[0].offset

        cont_special.sineSlide >> sineLoc.translateY
        cont_special.sineArea >> sineLoc.scaleY




        ## move the control points back into the place
        for j in range (len(inits)):
            if not j == (len(inits)-1):
                targetInit = inits[j+1]
                rotateOff = (90,90,0)
            else:
                targetInit = inits[j-1]
                rotateOff = (-90,-90, 180)
            extra.alignAndAim(contJointsList[j], targetList=[inits[j]], aimTargetList=[targetInit], upVector=upAxis, rotateOff=rotateOff)

        ## constrain joints to controllers

        for j in range (len(contJointsList)):
            pm.parentConstraint(contTwk_List[j], contJointsList[j], mo=False)

        ## Create limb plug
        pm.select(d=True)
        self.limbPlug = pm.joint(name="limbPlug_" + suffix, p=rootPoint, radius=3)
        pm.parentConstraint(self.limbPlug, self.scaleGrp, mo=False)

        ## Good Parenting
        pm.parent(cont_special_ORE, contFK_List[0])

        pm.parent(npBase[0], self.nonScaleGrp)
        # pm.parent(npJdefHolder[0], self.nonScaleGrp)
        pm.parent(npDeformers[0], self.nonScaleGrp)
        # pm.parent(follicleList, self.nonScaleGrp)
        pm.parent(curlDeformer[1], self.nonScaleGrp)
        pm.parent(twistLoc, self.nonScaleGrp)
        pm.parent(sineLoc,self.nonScaleGrp)
        pm.parent(npWrapGeo, self.nonScaleGrp)
        #
        #
        pm.parent(contJointsList, self.scaleGrp)
        pm.parent(wrapScaleJoint, self.scaleGrp)

        pm.parent(npJdefHolder[0], self.scaleGrp)

        ## CONNECT RIG VISIBILITIES

        pm.addAttr(self.scaleGrp, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True)
        pm.addAttr(self.scaleGrp, at="bool", ln="Joints_Visibility", sn="jointVis", defaultValue=True)
        pm.addAttr(self.scaleGrp, at="bool", ln="Rig_Visibility", sn="rigVis", defaultValue=False)
        # make the created attributes visible in the channelbox
        pm.setAttr(self.scaleGrp.contVis, cb=True)
        pm.setAttr(self.scaleGrp.jointVis, cb=True)
        pm.setAttr(self.scaleGrp.rigVis, cb=True)

        nodesContVis = [contTwk_List, contFK_List]
        nodesRigVis = [npBase[0], npJdefHolder[0], npDeformers[0], sineLoc, twistLoc, curlDeformer[1], follicleList, contJointsList, wrapScaleJoint]

        # Cont visibilities
        for i in nodesContVis:
            if isinstance(i, list):
                for x in i:
                    self.scaleGrp.contVis >> x.v
            else:
                self.scaleGrp.contVis >> i.v

        for i in self.deformerJoints:
            self.scaleGrp.jointVis >> i.v

        # Rig Visibilities
        for i in nodesRigVis:
            if isinstance(i, list):
                for x in i:
                    self.scaleGrp.rigVis >> x.v
            else:
                self.scaleGrp.rigVis >> i.v

        ## FOOL PROOFING

        for i in contFK_List:
            extra.lockAndHide(i, ["sx", "sy", "sz"])
        for i in contTwk_List:
            extra.lockAndHide(i, ["sx", "sy", "sz"])

        ## COLOR CODING

        # index = 17 ## default yellow color coding for non-sided tentacles
        # if side == "R":
        #     index = 13
        #     indexMin = 9
        #
        # elif side == "L":
        #     index = 6
        #     indexMin = 18

        # for i in contFK_List:
        #     extra.colorize(i, side)
        # for i in contTwk_List:
        #     extra.colorize(i, side)

        extra.colorize(contFK_List, side)
        extra.colorize(contTwk_List, side)
        extra.colorize(cont_special, side)

        self.scaleConstraints = [self.scaleGrp]


## https://www.youtube.com/watch?v=sQOCfp-VMRU
## https://www.youtube.com/watch?v=A0thwIfThB4


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

