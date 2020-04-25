##Creates a power ribbon joint chain between given locations

################################
######### POWER RIBBON Func ##########
################################
from maya import cmds
from trigger.library import functions as extra
from trigger.library import controllers as ic

class PowerRibbon():

    def __init__(self):
        # super(PowerRibbon, self).__init__()
        self.startConnection = None
        self.endConnection = None
        self.scaleGrp = None
        self.nonScaleGrp = None
        self.deformerJoints = []
        self.middleCont = []
        self.toHide = []
        self.startAim = None

    def createPowerRibbon(self, startPoint,
                          endPoint,
                          name,
                          side="C",
                          ribbonRes=5,
                          jointRes=5,
                          controllerCount=1,
                          controllerList=None,
                          dropoff=2.0,
                          connectStartAim=True,
                          orientation=0,
                          upVector=(0, 1, 0)
                          ):

        # Create groups
        name = extra.uniqueName("RBN_ScaleGrp_%s" %name)
        self.scaleGrp = cmds.group(name="RBN_ScaleGrp_%s" %name, em=True)
        self.nonScaleGrp = cmds.group(name="RBN_nonScaleGrp_%s" %name, em=True)

        ribbonLength = extra.getDistance(startPoint, endPoint)
        nSurfTrans = cmds.nurbsPlane(ax=(0, 0, 1), u=float(ribbonRes), v=1, w=ribbonLength, lr=(1.0/ribbonLength), name="nSurf_%s" %name)[0]
        cmds.parent(nSurfTrans, self.nonScaleGrp)
        cmds.rebuildSurface (nSurfTrans, ch=1, rpo=1, rt=0, end=1, kr=2, kcp=0, kc=0, su=5, du=3, sv=1, dv=1, tol=0, fr=0, dir=1)
        cmds.makeIdentity(a=True)
        nSurf = extra.getShapes(nSurfTrans)[0]

        self.toHide.append(nSurfTrans)

        #Start Upnodes
        cmds.select(d=True)
        self.startAim = cmds.group(em=True, name="jRbn_Start_CON_%s" %name)
        cmds.move(-(ribbonLength/2.0), 0, 0, self.startAim)
        cmds.makeIdentity(self.startAim, a=True)
        startORE = cmds.duplicate(self.startAim, name="jRbn_Start_ORE_%s" %name)[0]
        cmds.parent(startORE, self.startAim)


        start_UP = cmds.spaceLocator(name="jRbn_StartUp_%s" %name)[0]
        self.toHide.append(extra.getShapes(start_UP)[0])
        cmds.move(-(ribbonLength/2.0), 0.5, 0, start_UP)

        self.startConnection = cmds.spaceLocator(name="jRbn_StartCn_%s" %name)[0]
        self.toHide.append(extra.getShapes(self.startConnection)[0])
        cmds.move(-(ribbonLength / 2.0), 0, 0, self.startConnection)
        cmds.makeIdentity(self.startConnection, a=True)

        cmds.parent(self.startAim, start_UP, self.startConnection)

        cmds.addAttr(self.startConnection, shortName="scaleSwitch", longName="Scale_Switch",
                     defaultValue=1.0, at="float", minValue=0.0, maxValue=1.0, k=True)

        #End Upnodes
        cmds.select(d=True)
        end_AIM = cmds.group(name="jRbn_End_%s_AIM" %name, em=True)
        cmds.move(-(ribbonLength/-2.0), 0, 0, end_AIM)
        cmds.makeIdentity(end_AIM, a=True)
        end_UP = cmds.spaceLocator(name="jRbn_End_%s_UP" %name)[0]
        self.toHide.append(extra.getShapes(end_UP)[0])
        cmds.move(-(ribbonLength/-2.0), 0.5, 0, end_UP)

        self.endConnection = cmds.spaceLocator(name="jRbn_End_%s_endCon" %name)[0]
        self.toHide.append(extra.getShapes(self.endConnection)[0])
        cmds.move(-(ribbonLength / -2.0), 0, 0, self.endConnection)
        cmds.makeIdentity(self.endConnection, a=True)

        follicleList=[]
        # create follicles and deformer joints
        for index in range (int(jointRes)):
            follicle = cmds.createNode('follicle', name="follicle_{0}{1}".format(name, index))
            follicle_transform = extra.getParent(follicle)
            cmds.connectAttr("%s.local" % nSurf, "%s.inputSurface" % follicle)
            cmds.connectAttr("%s.worldMatrix[0]" % nSurf, "%s.inputWorldMatrix" % follicle)
            cmds.connectAttr("%s.outRotate" % follicle, "%s.rotate" % follicle_transform)
            cmds.connectAttr("%s.outTranslate" % follicle, "%s.translate" % follicle_transform)
            cmds.setAttr("%s.parameterV" % follicle, 0.5)
            cmds.setAttr("%s.parameterU" % follicle, 0.1+(index/float(jointRes)))
            extra.lockAndHide(follicle_transform, ["tx","ty","tz","rx","ry","rz"], hide=False)
            follicleList.append(follicle)
            defJ = cmds.joint(name="jDef_%s%i" %(name,index))
            cmds.joint(defJ, e=True, zso=True, oj='zxy')
            self.deformerJoints.append(defJ)
            cmds.parent(follicle_transform, self.nonScaleGrp)
            self.toHide.append(follicle)

        # create follicles for scaling calculations
        follicle_sca_list = []
        counter=0 # TODO : Why did I use this?
        for index in range (int(jointRes)):
            s_follicle = cmds.createNode('follicle', name="follicleSCA_%s%i" % (name, index))
            s_follicle_transform = extra.getParent(s_follicle)
            cmds.connectAttr("%s.local" % nSurf,"%s.inputSurface" % s_follicle)
            cmds.connectAttr("%s.worldMatrix[0]" % nSurf,"%s.inputWorldMatrix" % s_follicle)
            cmds.connectAttr("%s.outRotate" % s_follicle,"%s.rotate" % s_follicle_transform)
            cmds.connectAttr("%s.outTranslate" % s_follicle,"%s.translate" % s_follicle_transform)
            cmds.setAttr("%s.parameterV" % s_follicle, 0.0)
            cmds.setAttr("%s.parameterU" % s_follicle, 0.1+(index/float(jointRes)))
            extra.lockAndHide(s_follicle_transform, ["tx","ty","tz","rx","ry","rz"], hide=False)
            follicle_sca_list.append(s_follicle)
            cmds.parent(s_follicle_transform, self.nonScaleGrp)
            self.toHide.append(s_follicle)
            # create distance node
            distNode = cmds.createNode("distanceBetween", name="fDistance_%s%i" %(name, index))
            cmds.connectAttr("%s.outTranslate" % follicleList[counter], "%s.point1" % distNode)
            cmds.connectAttr("%s.outTranslate" % s_follicle, "%s.point2" % distNode)

            multiplier = cmds.createNode("multDoubleLinear", name="fMult_%s%i" % (name, index))
            cmds.connectAttr("%s.distance" % distNode, "%s.input1" % multiplier)

            cmds.setAttr("%s.input2" % multiplier, 2)

            global_mult = cmds.createNode("multDoubleLinear", name= "fGlobal_%s%i" % (name, index))
            cmds.connectAttr("%s.output" % multiplier, "%s.input1" % global_mult)
            cmds.connectAttr("%s.scaleX" % self.scaleGrp, "%s.input2" % global_mult)

            global_divide = cmds.createNode("multiplyDivide", name= "fGlobDiv_%s%i" %(name, index))
            cmds.setAttr("%s.operation" % global_divide, 2)
            cmds.connectAttr("%s.output" % global_mult, "%s.input1X" % global_divide)
            cmds.connectAttr("%s.scaleX" % self.scaleGrp, "%s.input2X" % global_divide)

            global_mixer = cmds.createNode("blendColors", name= "fGlobMix_%s%i" %(name, index))

            cmds.connectAttr("%s.outputX" % global_divide, "%s.color1R" % global_mixer)
            cmds.connectAttr("%s.outputX" % global_divide, "%s.color1G" % global_mixer)
            cmds.connectAttr("%s.outputX" % global_divide, "%s.color1B" % global_mixer)

            cmds.setAttr("%s.color2R" % global_mixer, 1)
            cmds.setAttr("%s.color2G" % global_mixer, 1)
            cmds.setAttr("%s.color2B" % global_mixer, 1)

            cmds.connectAttr("%s.output" % global_mixer, "%s.scale" % self.deformerJoints[counter])

            cmds.connectAttr("%s.scaleSwitch" % self.startConnection, "%s.blender" % global_mixer)
            counter += 1

        # create control joints
        cmds.select(d=True)
        startJoint = cmds.joint(name="jRbn_Start_%s" % name, radius=2)
        self.toHide.append(startJoint)
        cmds.move(-(ribbonLength / 2.0), 0, 0, startJoint)

        cmds.select(d=True)
        endJoint = cmds.joint(name="jRbn_End_%s" % name, radius=2)
        self.toHide.append(endJoint)
        cmds.move((ribbonLength/2.0), 0, 0, endJoint)

        mid_joint_list=[]
        counter = 0
        if controllerList:
            counter += 1
            for ctrl in controllerList:
                cmds.select(d=True)
                midJ = cmds.joint(name="jRbn_Mid_%i_%s" %(counter, name), radius=2)
                extra.alignToAlter(midJ, ctrl)
                mid_joint_list.append(midJ)
        else:
            interval = ribbonLength / (controllerCount+1)

            for index in range(controllerCount):
                counter +=1
                cmds.select(d=True)
                midJ = cmds.joint(name="jRbn_Mid_%i_%s" %(index, name), p=(-(ribbonLength/2.0)+(interval*counter), 0, 0), radius=2)
                mid_joint_list.append(midJ)

        cmds.skinCluster(startJoint, endJoint, mid_joint_list, nSurf, tsb=True, dropoffRate=dropoff)

        cmds.parent(startJoint, startORE)
        if connectStartAim:
            # aim it to the next midjoint after the start
            cmds.aimConstraint(mid_joint_list[0],self.startAim, aimVector=(1,0,0), upVector=(0,1,0), wut=1, wuo=start_UP, mo=False)

        cmds.parent(end_AIM, end_UP, self.endConnection)
        cmds.parent(endJoint, end_AIM)
        cmds.aimConstraint(mid_joint_list[-1], end_AIM, aimVector=(1,0,0), upVector=(0,1,0), wut=1, wuo=end_UP, mo=True)

        middle_POS_list=[]
        counter = 0

        icon = ic.Icon()
        for mid in mid_joint_list:
            counter += 1
            midCon, _ = icon.createIcon("Circle", iconName="cont_midRbn_%s%i" %(name, counter), normal=(1, 0, 0))
            self.middleCont.append(midCon)
            middle_OFF = cmds.spaceLocator(name="mid_OFF_%s%i" % (name, counter))[0]
            self.toHide.append(extra.getShapes(middle_OFF)[0])
            middle_AIM = cmds.group(em=True, name="mid_AIM_%s%i" %(name, counter))
            extra.alignTo(middle_AIM, mid, position=True, rotation=False)
            middle_UP = cmds.spaceLocator(name="mid_UP_{0}{1}".format (name, counter))[0]
            self.toHide.append(extra.getShapes(middle_UP)[0])

            extra.alignTo(middle_UP, mid, position=True, rotation=False)
            cmds.setAttr("%s.ty" % middle_UP, 0.5)

            middle_POS = cmds.spaceLocator(name="mid_POS_{0}{1}".format (name, counter))[0]
            self.toHide.append(extra.getShapes(middle_POS)[0])
            extra.alignTo(middle_POS, mid, position=True, rotation=False)

            cmds.parent(mid, midCon)
            cmds.parent(midCon, middle_OFF)
            cmds.parent(middle_OFF, middle_AIM)
            cmds.parent(middle_UP, middle_AIM, middle_POS)
            cmds.aimConstraint(self.startConnection, middle_AIM, aimVector=(0, 0, -1), upVector=(0, 1, 0), wut=1,
                             wuo=middle_UP, mo=True)
            cmds.pointConstraint(self.startConnection, self.endConnection, middle_POS)
            cmds.pointConstraint(start_UP, end_UP, middle_UP)
            middle_POS_list.append(middle_POS)

        cmds.delete(cmds.pointConstraint([self.startConnection, self.endConnection], self.scaleGrp, mo=False)[0])

        cmds.makeIdentity(self.scaleGrp, a=True, t=True)

        cmds.parent([self.startConnection, self.endConnection] + middle_POS_list, self.scaleGrp)

        extra.alignAndAim(self.scaleGrp, [startPoint, endPoint], [endPoint], upVector=upVector)



