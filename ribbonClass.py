##Creates a ribbon joint chain between given locations
## Usage:
## createRibbon (Start Point, End Point, Name of the Ribbon)
## Returns (Start Handle, End Handle, scale group, non-scale group, deformer joints list, middle controller)

################################
######### RIBBON Func ##########
################################

import pymel.core as pm

import extraProcedures as extra
reload(extra)

import contIcons as icon
reload(icon)

class Ribbon():

    startConnection = None
    endConnection = None
    scaleGrp = None
    nonScaleGrp = None
    deformerJoints = None
    middleCont = None
    toHide = None
    def createRibbon(self, startPoint, endPoint, name, orientation, rResolution=5, jResolution=5.0):

        name=(extra.uniqueName("RBN_ScaleGrp_" + name)).replace("RBN_ScaleGrp_", "")

        self.nonScaleGrp=pm.group(em=True, name="RBN_nonScaleGrp_"+name)

        if type(startPoint) == str:
            startPoint = pm.PyNode(startPoint)
        if type(endPoint) == str:
            endPoint = pm.PyNode(endPoint)
        ribbonLength=extra.getDistance(startPoint, endPoint)
        nSurfTrans=pm.nurbsPlane(ax=(0,0,1),u=rResolution,v=1, w=ribbonLength, lr=(1.0/ribbonLength), name="nSurf_"+name)
        pm.parent(nSurfTrans[0], self.nonScaleGrp)
        pm.rebuildSurface (nSurfTrans, ch=1, rpo=1, rt=0, end=1, kr=2, kcp=0, kc=0, su=5, du=3, sv=1, dv=1, tol=0, fr=0, dir=1)
        pm.makeIdentity(a=True)
        nSurf=nSurfTrans[0].getShape()
        self.toHide=[]
        follicleList=[]
        self.deformerJoints=[]
        self.toHide.append(nSurfTrans[0])

        for i in range (0, int(jResolution)):
            follicle = pm.createNode('follicle', name="follicle_"+name+str(i))
            nSurf.local.connect(follicle.inputSurface)
            nSurf.worldMatrix[0].connect(follicle.inputWorldMatrix)
            follicle.outRotate.connect(follicle.getParent().rotate)
            follicle.outTranslate.connect(follicle.getParent().translate)
            follicle.parameterV.set(0.5)
            follicle.parameterU.set(0.1+(i/jResolution))
            follicle.getParent().t.lock()
            follicle.getParent().r.lock()
            follicleList.append(follicle)
            defJ=pm.joint(name="jDef_"+name+str(i))
            pm.joint(defJ, e=True, zso=True, oj='zxy')
            self.deformerJoints.append(defJ)
            pm.parent(follicle.getParent(), self.nonScaleGrp)
            self.toHide.append(follicle)

        pm.select(d=True)
        startJoint=pm.joint(name="jRbn_Start_"+name, radius=2)
        self.toHide.append(startJoint)
        pm.move(startJoint, (-(ribbonLength/2.0),0,0))
        pm.select(d=True)
        middleJoint=pm.joint(name="jRbn_Mid_"+name, radius=2)
        self.toHide.append(middleJoint)
        pm.select(d=True)
        endJoint=pm.joint(name="jRbn_End_"+name, radius=2)
        self.toHide.append(endJoint)
        pm.move(endJoint, ((ribbonLength/2.0),0,0))

        pm.select(nSurf)
        pm.skinCluster(startJoint, middleJoint, endJoint, nSurf, tsb=True)

        ##
        #Start Upnodes
        pm.select(d=True)
        start_AIM=pm.group(em=True, name="jRbn_Start_"+name)
        pm.move(start_AIM, (-(ribbonLength/2.0),0,0))
        pm.makeIdentity(a=True)
        start_UP=pm.spaceLocator(name="jRbn_Start_"+name)
        self.toHide.append(start_UP.getShape())
        pm.move(start_UP, (-(ribbonLength/2.0),0.5,0))

        self.startConnection=pm.spaceLocator(name="jRbn_Start_" + name)
        self.toHide.append(self.startConnection.getShape())
        pm.move(self.startConnection, (-(ribbonLength / 2.0), 0, 0))
        pm.makeIdentity(a=True)

        pm.parent(start_AIM, start_UP, self.startConnection)

        pm.parent(startJoint,start_AIM)
        pm.aimConstraint(middleJoint,start_AIM, aimVector=(1,0,0), upVector=(0,1,0), wut=1, wuo=start_UP, mo=False)

        #End Upnodes
        pm.select(d=True)
        end_AIM=pm.group(em=True, name="jRbn_End_"+name)
        pm.move(end_AIM, (-(ribbonLength/-2.0),0,0))
        pm.makeIdentity(a=True)
        end_UP=pm.spaceLocator(name="jRbn_End_"+name)
        self.toHide.append(end_UP.getShape())
        pm.move(end_UP, (-(ribbonLength/-2.0),0.5,0))

        self.endConnection=pm.spaceLocator(name="jRbn_End_" + name)
        self.toHide.append(self.endConnection.getShape())
        pm.move(self.endConnection, (-(ribbonLength / -2.0), 0, 0))
        pm.makeIdentity(a=True)

        pm.parent(end_AIM, end_UP, self.endConnection)
        pm.parent(endJoint,end_AIM)
        pm.aimConstraint(middleJoint,end_AIM, aimVector=(1,0,0), upVector=(0,1,0), wut=1, wuo=end_UP, mo=True)

        #Mid Upnodes
        pm.select(d=True)
        self.middleCont = icon.circle("cont_midRbn_" + name, normal=(1, 0, 0))
        middle_OFF=pm.spaceLocator(name="jRbn_Mid_"+name)
        self.toHide.append(middle_OFF.getShape())
        middle_AIM=pm.group(em=True, name="jRbn_Mid_"+name)
        pm.move(middle_AIM, (0,0,0))
        pm.makeIdentity(a=True)
        middle_UP=pm.spaceLocator(name="jRbn_Mid_"+name)
        self.toHide.append(middle_UP.getShape())
        pm.move(middle_UP, (0,0.5,0))
        middle_POS=pm.spaceLocator(name="jRbn_Mid_"+name)
        self.toHide.append(middle_POS.getShape())
        pm.move(middle_POS, (0,0,0))
        pm.makeIdentity(a=True)

        pm.parent(middleJoint, self.middleCont)
        pm.parent(self.middleCont, middle_OFF)
        pm.parent(middle_OFF, middle_AIM)
        pm.parent(middle_UP, middle_AIM, middle_POS)
        pm.aimConstraint(self.startConnection, middle_AIM, aimVector=(0, 0, -1), upVector=(0, 1, 0), wut=1, wuo=middle_UP, mo=True)
        pm.pointConstraint(self.startConnection, self.endConnection, middle_POS)
        pm.pointConstraint(start_UP, end_UP, middle_UP)

        ##

        pm.select(self.startConnection, middle_POS, self.endConnection)
        self.scaleGrp=pm.group(name="RBN_ScaleGrp_"+name)
        tempPoCon=pm.pointConstraint(startPoint, endPoint, self.scaleGrp)
        pm.delete(tempPoCon)
        tempAimCon=pm.aimConstraint(endPoint, self.scaleGrp, aim=(1,0,0), o=(orientation,0,0))
        pm.delete(tempAimCon)

        ### Create Stretch Squash Nodes
        ##

        pm.select(self.middleCont)
        pm.addAttr(shortName='preserveVol', longName='Preserve_Volume', defaultValue=0.0, minValue=0.0, maxValue=1.0, at="double", k=True)
        pm.select(self.scaleGrp)

        globalDefMult=pm.createNode("multiplyDivide", name="global_def_mult_"+name)
        pm.setAttr(globalDefMult.input1, (1,ribbonLength,ribbonLength))

        scaleRatio=pm.createNode("multiplyDivide", name="scaleRatio_def_"+name)
        pm.setAttr(scaleRatio.input1X, 1)
        pm.setAttr(scaleRatio.input2X, 1)
        pm.setAttr(scaleRatio.operation, 2)

        pow_def_j0=pm.createNode("multiplyDivide", name="pow_def_j0_"+name)
        pm.setAttr(pow_def_j0.operation, 3)
        pm.setAttr(pow_def_j0.input2, (1,0,0))
        pow_def_j1=pm.createNode("multiplyDivide", name="pow_def_j1_"+name)
        pm.setAttr(pow_def_j1.operation, 3)
        pm.setAttr(pow_def_j1.input2, (1,1,1))
        pow_def_j2=pm.createNode("multiplyDivide", name="pow_def_j2_"+name)
        pm.setAttr(pow_def_j2.operation, 3)
        pm.setAttr(pow_def_j2.input2, (1,2,2))
        pow_def_j3=pm.createNode("multiplyDivide", name="pow_def_j3_"+name)
        pm.setAttr(pow_def_j3.operation, 3)
        pm.setAttr(pow_def_j3.input2, (1,1,1))
        pow_def_j4=pm.createNode("multiplyDivide", name="pow_def_j4_"+name)
        pm.setAttr(pow_def_j4.operation, 3)
        pm.setAttr(pow_def_j4.input2, (1,0,0))


        def_volumePreserve0=pm.createNode("blendColors", name="def_volumePreserve0_"+name)
        pm.setAttr(def_volumePreserve0.color2, (1,1,1))
        def_volumePreserve1=pm.createNode("blendColors", name="def_volumePreserve1_"+name)
        pm.setAttr(def_volumePreserve1.color2, (1,1,1))
        def_volumePreserve2=pm.createNode("blendColors", name="def_volumePreserve2_"+name)
        pm.setAttr(def_volumePreserve2.color2, (1,1,1))
        def_volumePreserve3=pm.createNode("blendColors", name="def_volumePreserve3_"+name)
        pm.setAttr(def_volumePreserve3.color2, (1,1,1))
        def_volumePreserve4=pm.createNode("blendColors", name="def_volumePreserve4_"+name)
        pm.setAttr(def_volumePreserve4.color2, (1,1,1))

        glob_pow_def_j0=pm.createNode("multiplyDivide", name="glob_pow_def_j0_"+name)
        glob_pow_def_j1=pm.createNode("multiplyDivide", name="glob_pow_def_j1_"+name)
        glob_pow_def_j2=pm.createNode("multiplyDivide", name="glob_pow_def_j2_"+name)
        glob_pow_def_j3=pm.createNode("multiplyDivide", name="glob_pow_def_j3_"+name)
        glob_pow_def_j4=pm.createNode("multiplyDivide", name="glob_pow_def_j4_"+name)

        initialRbnLen=pm.arclen(nSurf.v[0], ch=1, name="arclen_rbn_"+name)

        ## Make Stretch Squash Connections

        self.scaleGrp.scale >> globalDefMult.input2

        self.middleCont.preserveVol >> def_volumePreserve0.blender
        self.middleCont.preserveVol >> def_volumePreserve1.blender
        self.middleCont.preserveVol >> def_volumePreserve2.blender
        self.middleCont.preserveVol >> def_volumePreserve3.blender
        self.middleCont.preserveVol >> def_volumePreserve4.blender

        self.scaleGrp.scale >> glob_pow_def_j0.input2
        self.scaleGrp.scale >> glob_pow_def_j1.input2
        self.scaleGrp.scale >> glob_pow_def_j2.input2
        self.scaleGrp.scale >> glob_pow_def_j3.input2
        self.scaleGrp.scale >> glob_pow_def_j4.input2

        globalDefMult.outputY >> scaleRatio.input1Y
        globalDefMult.outputZ >> scaleRatio.input1Z

        initialRbnLen.arcLength >> scaleRatio.input2Y
        initialRbnLen.arcLength >> scaleRatio.input2Z

        scaleRatio.output >> pow_def_j0.input1
        scaleRatio.output >> pow_def_j1.input1
        scaleRatio.output >> pow_def_j2.input1
        scaleRatio.output >> pow_def_j3.input1
        scaleRatio.output >> pow_def_j4.input1

        scaleRatio.output >> def_volumePreserve0.color1
        scaleRatio.output >> def_volumePreserve1.color1
        scaleRatio.output >> def_volumePreserve2.color1
        scaleRatio.output >> def_volumePreserve3.color1
        scaleRatio.output >> def_volumePreserve4.color1

        def_volumePreserve0.output >> glob_pow_def_j0.input1
        def_volumePreserve1.output >> glob_pow_def_j1.input1
        def_volumePreserve2.output >> glob_pow_def_j2.input1
        def_volumePreserve3.output >> glob_pow_def_j3.input1
        def_volumePreserve4.output >> glob_pow_def_j4.input1

        glob_pow_def_j0.output >> self.deformerJoints[0].scale
        glob_pow_def_j1.output >> self.deformerJoints[1].scale
        glob_pow_def_j2.output >> self.deformerJoints[2].scale
        glob_pow_def_j3.output >> self.deformerJoints[3].scale
        glob_pow_def_j4.output >> self.deformerJoints[4].scale

