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

    def createTentacle(self, inits, suffix="", npResolution=5.0, jResolution=5.0, blResolution=25.0, dropoff=2.0):

        ## Make sure the suffix is unique
        idCounter=0
        while pm.objExists("scaleGrp_" + suffix):
            suffix = "%s%s" % (suffix, str(idCounter + 1))

        if len(inits)<2:
            pm.error("Tentacle setup needs at least 2 initial joints")
            return

        ## Create Groups
        self.scaleGrp = pm.group(name="scaleGrp_" + suffix, em=True)
        extra.alignTo(self.scaleGrp, inits[0], 0)
        self.nonScaleGrp = pm.group(name="NonScaleGrp_" + suffix, em=True)

        ## Get the orientation axises
        upAxis, mirroAxis, spineDir = extra.getRigAxes(inits[0])

        ## Create Controller Curves

        ## specialController
        cont_special = icon.looper(name="tentacleSP_" + suffix)

        extra.alignAndAim(cont_special , targetList=[inits[0]], aimTargetList=[inits[1]], upVector=upAxis,
                          translateOff=(0,0,0), rotateOff=(90,90,0))
        pm.move(cont_special, (3, 0, 0), r=True, os=True)

        cont_special_ORE = extra.createUpGrp(cont_special,"ORE")

        ## seperator - curl
        pm.addAttr(cont_special, shortName="curlSeperator", at="enum", en="----------", k=True)
        pm.setAttr(cont_special.curlSeperator, lock=True)

        pm.addAttr(cont_special, shortName="curl", longName="Curl", defaultValue=0.0, minValue=0.0, maxValue=10.0, at="float",
                   k=True)
        pm.addAttr(cont_special, shortName="startDiameter", longName="Start_Diameter", defaultValue=0.0, at="float", k=True)
        pm.addAttr(cont_special, shortName="endDiameter", longName="End_Diameter", defaultValue=0.0, at="float",
                   k=True)
        pm.addAttr(cont_special, shortName="startAngle", longName="Start_Angle", defaultValue=0.0, at="float",
                   k=True)
        pm.addAttr(cont_special, shortName="endAngle", longName="End_Angle", defaultValue=0.0, at="float",
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
        pm.addAttr(cont_special, shortName="sineWavelength", longName="Sine_Wavelength", defaultValue=0.0, at="float",
                   k=True)
        pm.addAttr(cont_special, shortName="sineDropOff", longName="Sine_Dropoff", defaultValue=0.0, at="float",
                   k=True)
        pm.addAttr(cont_special, shortName="sineSlide", longName="Sine_Slide", defaultValue=0.0, at="float",
                   k=True)
        pm.addAttr(cont_special, shortName="sineArea", longName="Sine_area", defaultValue=0.0, at="float",
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
            contFK_List.append(contFK)

            pm.parent(contTwk_OFF, contFK)
            if not j == 0:
                pm.parent(contFK_OFF, contFK_List[j-1])


        ## Make a straight line from inits joints (like in the twistSpline)
        # get the root position
        rootVc = inits[0].getTranslation(space="world")
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
        endVc = (rootVc.x, (rootVc.y + totalLength), rootVc.z)
        splitVc = endVc - rootVc

        ## Create Control Joints
        contJoints = []
        pm.select(d=True)
        for i in range(0, len(contDistances)):
            ctrlVc = splitVc.normal() * contDistances[i]
            place = rootVc + (ctrlVc)
            j = pm.joint(p=place, name="jCont_tentacle_" + suffix + str(i), radius=5, o=(0, 0, 0))
            contJoints.append(j)
            pm.select(d=True)

        ## Create the Base Nurbs Plane (npBase)
        ribbonLength = extra.getDistance(contJoints[0], contJoints[-1])
        npBase=pm.nurbsPlane(ax=(0,1,0),u=npResolution,v=1, w=ribbonLength, lr=(1.0/ribbonLength), name="npBase_"+suffix)
        pm.rebuildSurface (npBase, ch=1, rpo=1, rt=0, end=1, kr=2, kcp=0, kc=0, su=5, du=3, sv=1, dv=1, tol=0, fr=0, dir=1)
        extra.alignAndAim(npBase, targetList=[contJoints[0], contJoints[-1]], aimTargetList=[contJoints[-1]], upVector=spineDir)

        ## Duplicate the Base Nurbs Plane as joint Holder (npJDefHolder)
        npJdefHolder = pm.nurbsPlane(ax=(0, 1, 0), u=blResolution, v=1, w=ribbonLength, lr=(1.0 / ribbonLength),
                               name="npJDefHolder_" + suffix)
        pm.rebuildSurface(npJdefHolder, ch=1, rpo=1, rt=0, end=1, kr=2, kcp=0, kc=0, su=5, du=3, sv=1, dv=1, tol=0, fr=0,
                          dir=1)
        extra.alignAndAim(npJdefHolder, targetList=[contJoints[0], contJoints[-1]], aimTargetList=[contJoints[-1]],
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
            pm.parent(follicle.getParent(), self.nonScaleGrp)
            # self.toHide.append(follicle)

        ## Duplicate it 3 more times for deformation targets (npDeformers, npTwist, npSine)

        npDeformers = pm.duplicate(npJdefHolder[0], name="npCurl_"+suffix)
        # print "anan", npDeformers
        # pm.setAttr(npDeformers[0].getShape().patchesU, 25)
        # npTwist = pm.duplicate(npJdefHolder[0], name="npTwist_" + suffix)
        # npSine = pm.duplicate(npJdefHolder[0], name="npSine_" + suffix)
        ## Create Blendshape node between np_jDefHolder and deformation targets
        # npBlend = pm.blendShape(npTwist, npDeformers, npTwist, npSine, npJdefHolder[0], w=[(0,1),(1,1),(2,1)])
        npBlend = pm.blendShape(npDeformers, npJdefHolder[0], w=(0,1))

        ## Wrap npjDefHolder to the Base Plane
        # npWrap = pm.deformer(type="wrap", g=npJdefHolder)
        npWrap = self.createWrap(npBase[0], npJdefHolder[0],weightThreshold=0.0, maxDistance=50, autoWeightThreshold=False)

        ## Create skin cluster
        pm.skinCluster(contJoints, npBase[0], tsb=True, dropoffRate=dropoff)

        ## create the roll(bend) deformer
        # pm.select(npDeformers)
        curlDeformer = pm.nonLinear(npDeformers, type='bend', curvature=1500)
        # pm.select(curlDeformer)
        # pm.setAttr(curlDeformer[1].rz, 4)
        pm.setAttr(curlDeformer[0].lowBound, -1)
        pm.setAttr(curlDeformer[0].highBound, 0)
        ## Ratio is:

        pm.setDrivenKeyframe(curlDeformer[1].ty, cd=cont_special.curl, v=0.0, dv=10.0, itt='linear', ott='linear')
        pm.setDrivenKeyframe([curlDeformer[1].sx, curlDeformer[1].sy, curlDeformer[1].sz], cd=cont_special.curl, v=(totalLength * 2), dv=10.0, itt='linear', ott='linear')
        pm.setDrivenKeyframe(curlDeformer[1].rz, cd=cont_special.curl, v=4.0, dv=10.0, itt='linear', ott='linear')

        pm.setDrivenKeyframe(curlDeformer[1].ty, cd=cont_special.curl, v=totalLength, dv=0.0, itt='linear', ott='linear')
        pm.setDrivenKeyframe([curlDeformer[1].sx, curlDeformer[1].sy, curlDeformer[1].sz], cd=cont_special.curl, v=(totalLength / 2), dv=0.0, itt='linear', ott='linear')
        pm.setDrivenKeyframe(curlDeformer[1].rz, cd=cont_special.curl, v=6.0, dv=0.0, itt='linear', ott='linear')

        ## create twist deformer
        twistDeformer = pm.nonLinear(npDeformers, type='twist')
        pm.rotate(twistDeformer[1], (0,0,0))

        ## create sine deformer
        sineDeformer = pm.nonLinear(npDeformers, type='sine')
        pm.rotate(sineDeformer[1], (0,0,0))

        ## move the control points back into the place
        for j in range (len(inits)):
            if not j == (len(inits)-1):
                targetInit = inits[j+1]
                rotateOff = (90,90,0)
            else:
                targetInit = inits[j-1]
                rotateOff = (-90,-90, 180)
            extra.alignAndAim(contJoints[j], targetList=[inits[j]], aimTargetList=[targetInit], upVector=upAxis, rotateOff=rotateOff)

        ## constrain joints to controllers

        for j in range (len(contJoints)):
            pm.parentConstraint(contTwk_List[j], contJoints[j], mo=False)


        ## Good Parenting
        # pm.parent(npBase[0], self.nonScaleGrp)


## https://www.youtube.com/watch?v=sQOCfp-VMRU
## https://www.youtube.com/watch?v=A0thwIfThB4

        # if not isinstance(inits, list):
        #     ## parse the dictionary inits into a list
        #     sRoot=inits.get("Root")
        #     try:
        #         tentacles=reversed(inits.get("Tentacle"))
        #         tentacleEnd = inits.get("TentacleEnd")
        #         inits = [sRoot] + sorted(tentacles) + [tentacleEnd]
        #     except:
        #         tentacleEnd = inits.get("TentacleEnd")
        #         inits = [sRoot] + [tentacleEnd]
        #
        # idCounter = 0
        # ## create an unique suffix
        # while pm.objExists("scaleGrp_" + "tentacle" + suffix):
        #     suffix = "%s%s" %(suffix, str(idCounter + 1))
        #
        # if (len(inits) < 2):
        #     pm.error("Insufficient Tentacle Initialization Joints")
        #     return
        #
        # iconSize = extra.getDistance(inits[0], inits[len(inits)-1])
        # rootPoint = inits[0].getTranslation(space="world")
        # endPoint = inits[-1].getTranslation(space="world")
        #
        # ## get the up axis
        # axisDict={"x":(1.0,0.0,0.0),"y":(0.0,1.0,0.0),"z":(0.0,0.0,1.0),"-x":(-1.0,0.0,0.0),"-y":(0.0,-1.0,0.0),"-z":(0.0,0.0,-1.0)}
        # spineDir = {"x": (-1.0, 0.0, 0.0), "y": (0.0, -1.0, 0.0), "z": (0.0, 0.0, 1.0), "-x": (1.0, 0.0, 0.0), "-y": (0.0, 1.0, 0.0), "-z": (0.0, 0.0, 1.0)}
        # if pm.attributeQuery("upAxis", node=inits[0], exists=True):
        #     try:
        #         self.upAxis=axisDict[pm.getAttr(inits[0].upAxis).lower()]
        #     except:
        #         pm.warning("upAxis attribute is not valid, proceeding with default value (y up)")
        #         self.upAxis = (0.0, 1.0, 0.0)
        # else:
        #     pm.warning("upAxis attribute of the root node does not exist. Using default value (y up)")
        #     self.upAxis = (0.0, 1.0, 0.0)
        # ## get the mirror axis
        # if pm.attributeQuery("mirrorAxis", node=inits[0], exists=True):
        #     try:
        #         self.mirrorAxis=axisDict[pm.getAttr(inits[0].mirrorAxis).lower()]
        #     except:
        #         pm.warning("mirrorAxis attribute is not valid, proceeding with default value (scene x)")
        #         self.mirrorAxis= (1.0, 0.0, 0.0)
        # else:
        #     pm.warning("mirrorAxis attribute of the root node does not exist. Using default value (scene x)")
        #     self.mirrorAxis = (1.0, 0.0, 0.0)
        #
        # ## get spine Direction
        # if pm.attributeQuery("lookAxis", node=inits[0], exists=True):
        #     try:
        #         self.spineDir = spineDir[pm.getAttr(inits[0].lookAxis).lower()]
        #     except:
        #         pm.warning("Cannot get spine direction from lookAxis attribute, proceeding with default value (-x)")
        #         self.spineDir = (-1.0, 0.0, 0.0)
        # else:
        #     pm.warning("lookAxis attribute of the root node does not exist. Using default value (-x) for spine direction")
        #     self.spineDir = (1.0, 0.0, 0.0)
        #
        # #     _____            _             _ _
        # #    / ____|          | |           | | |
        # #   | |     ___  _ __ | |_ _ __ ___ | | | ___ _ __ ___
        # #   | |    / _ \| '_ \| __| '__/ _ \| | |/ _ \ '__/ __|
        # #   | |___| (_) | | | | |_| | | (_) | | |  __/ |  \__ \
        # #    \_____\___/|_| |_|\__|_|  \___/|_|_|\___|_|  |___/
        # #
        # #
        #
        # tentacle = twistSpline.twistSpline()
        # tentacle.createTspline(inits, "spine" + suffix, resolution, dropoff=dropoff)



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
        return pm.nt.Wrap(wrapNode)

