##Creates a power ribbon joint chain between given locations

################################
######### POWER RIBBON Func ##########
################################

import pymel.core as pm

import extraProcedures as extra
reload(extra)

import contIcons as icon
reload(icon)

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
        name=(extra.uniqueName("RBN_ScaleGrp_" + name)).replace("RBN_ScaleGrp_", "")
        self.scaleGrp=pm.group(name="RBN_ScaleGrp_"+name, empty=True)
        self.nonScaleGrp=pm.group(em=True, name="RBN_nonScaleGrp_%s" %name)

        ribbonLength=extra.getDistance(startPoint, endPoint)
        nSurfTrans=pm.nurbsPlane(ax=(0,0,1),u=float(ribbonRes),v=1, w=ribbonLength, lr=(1.0/ribbonLength), name="nSurf_"+name)
        pm.parent(nSurfTrans[0], self.nonScaleGrp)
        pm.rebuildSurface (nSurfTrans, ch=1, rpo=1, rt=0, end=1, kr=2, kcp=0, kc=0, su=5, du=3, sv=1, dv=1, tol=0, fr=0, dir=1)
        pm.makeIdentity(a=True)
        nSurf=nSurfTrans[0].getShape()
        follicleList=[]
        self.toHide.append(nSurfTrans[0])

        # create follicles and deformer joints
        for i in range (0, int(jointRes)):
            follicle = pm.createNode('follicle', name="follicle_{0}{1}".format(name, i))
            nSurf.local.connect(follicle.inputSurface)
            nSurf.worldMatrix[0].connect(follicle.inputWorldMatrix)
            follicle.outRotate.connect(follicle.getParent().rotate)
            follicle.outTranslate.connect(follicle.getParent().translate)
            follicle.parameterV.set(0.5)
            follicle.parameterU.set(0.1+(i/float(jointRes)))
            follicle.getParent().t.lock()
            follicle.getParent().r.lock()
            follicleList.append(follicle)
            defJ=pm.joint(name="jDef_"+name+str(i))
            pm.joint(defJ, e=True, zso=True, oj='zxy')
            self.deformerJoints.append(defJ)
            pm.parent(follicle.getParent(), self.nonScaleGrp)
            self.toHide.append(follicle)

        # create follicles for scaling calculations
        follicle_sca_list = []
        counter=0
        for i in range (0, int(jointRes)):
            s_follicle = pm.createNode('follicle', name="follicleSCA_{0}{1}".format(name, i))
            nSurf.local.connect(s_follicle.inputSurface)
            nSurf.worldMatrix[0].connect(s_follicle.inputWorldMatrix)
            s_follicle.outRotate.connect(s_follicle.getParent().rotate)
            s_follicle.outTranslate.connect(s_follicle.getParent().translate)
            s_follicle.parameterV.set(0.0)
            s_follicle.parameterU.set(0.1+(i/float(jointRes)))
            s_follicle.getParent().t.lock()
            s_follicle.getParent().r.lock()
            follicle_sca_list.append(s_follicle)
            pm.parent(s_follicle.getParent(), self.nonScaleGrp)
            self.toHide.append(s_follicle)
            # create distance node
            distNode = pm.createNode("distanceBetween", name="fDistance_{0}{1}".format(name, i))
            follicleList[counter].outTranslate >> distNode.point1
            s_follicle.outTranslate >> distNode.point2

            multiplier = pm.createNode("multDoubleLinear", name="fMult_{0}{1}".format(name, i))
            distNode.distance >> multiplier.input1
            pm.setAttr(multiplier.input2, 2)

            global_mult = pm.createNode("multDoubleLinear", name= "fGlobal_{0}{1}".format(name, i))
            multiplier.output >> global_mult.input1
            self.scaleGrp.scaleX >> global_mult.input2

            global_divide = pm.createNode("multiplyDivide", name= "fGlobDiv_{0}{1}".format(name, i))
            pm.setAttr(global_divide.operation, 2)
            global_mult.output >> global_divide.input1X
            self.scaleGrp.scaleX >> global_divide.input2X



            # compensationNode = pm.createNode("addDoubleLinear", name="fCompensate_{0}{1}".format(name, i))
            # multiplier.output >> compensationNode.input1
            # pm.setAttr(compensationNode.input2, 1)

            # global_mult.output >> self.deformerJoints[counter].scaleY
            # global_mult.output >> self.deformerJoints[counter].scaleZ
            global_divide.outputX >> self.deformerJoints[counter].scaleX
            global_divide.outputX >> self.deformerJoints[counter].scaleY
            global_divide.outputX >> self.deformerJoints[counter].scaleZ

            counter += 1

        # create control joints
        pm.select(d=True)
        startJoint=pm.joint(name="jRbn_Start_"+name, radius=2)
        self.toHide.append(startJoint)
        pm.move(startJoint, (-(ribbonLength / 2.0), 0, 0))

        pm.select(d=True)
        endJoint=pm.joint(name="jRbn_End_"+name, radius=2)
        self.toHide.append(endJoint)
        pm.move(endJoint, ((ribbonLength/2.0),0,0))

        mid_joint_list=[]
        counter = 0
        if controllerList:
            counter += 1
            for p in controllerList:
                pm.select(d=True)
                midJ = pm.joint(name="jRbn_Mid_{0}_{1}".format(counter, name), radius=2)
                extra.alignToAlter(midJ, p)
                mid_joint_list.append(midJ)
        else:
            interval = ribbonLength / (controllerCount+1)

            for i in range (0, controllerCount):
                counter +=1
                pm.select(d=True)
                # pos = (-(ribbonLength/2.0)+(interval*counter),0,0)
                # print "pos", pos
                midJ = pm.joint(name="jRbn_Mid_{0}_{1}".format(i, name), p=(-(ribbonLength/2.0)+(interval*counter),0,0), radius=2)

                mid_joint_list.append(midJ)

        pm.skinCluster(startJoint,endJoint, mid_joint_list, nSurf, tsb=True, dropoffRate=dropoff)
        #Start Upnodes
        pm.select(d=True)
        self.startAim=pm.group(em=True, name="jRbn_Start_%s" %name)
        pm.move(self.startAim, (-(ribbonLength/2.0),0,0))
        pm.makeIdentity(a=True)
        start_UP=pm.spaceLocator(name="jRbn_Start_%s" %name)
        self.toHide.append(start_UP.getShape())
        pm.move(start_UP, (-(ribbonLength/2.0),0.5,0))

        self.startConnection=pm.spaceLocator(name="jRbn_Start_%s" %name)
        self.toHide.append(self.startConnection.getShape())
        pm.move(self.startConnection, (-(ribbonLength / 2.0), 0, 0))
        pm.makeIdentity(a=True)

        pm.parent(self.startAim, start_UP, self.startConnection)

        pm.parent(startJoint,self.startAim)
        if connectStartAim:
            # aim it to the next midjoint after the start
            pm.aimConstraint(mid_joint_list[0],self.startAim, aimVector=(1,0,0), upVector=(0,1,0), wut=1, wuo=start_UP, mo=False)

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
        pm.aimConstraint(mid_joint_list[-1],end_AIM, aimVector=(1,0,0), upVector=(0,1,0), wut=1, wuo=end_UP, mo=True)

        middle_POS_list=[]
        counter = 0

        for mid in mid_joint_list:
            counter += 1
            # self.middleCont = icon.circle("cont_midRbn_%s" %name, normal=(1, 0, 0))
            midCon = icon.circle("cont_midRbn_{0}{1}".format (name, counter), normal=(1, 0, 0))
            self.middleCont.append(midCon)
            middle_OFF = pm.spaceLocator(name="mid_OFF_{0}{1}".format (name, counter))
            self.toHide.append(middle_OFF.getShape())
            middle_AIM = pm.group(em=True, name="mid_AIM_{0}{1}".format (name, counter))
            extra.alignTo(middle_AIM, mid)
            # pm.move(middle_AIM, (0, 0, 0))
            # pm.makeIdentity(a=True)
            middle_UP = pm.spaceLocator(name="mid_UP_{0}{1}".format (name, counter))
            self.toHide.append(middle_UP.getShape())

            extra.alignTo(middle_UP, mid)
            pm.setAttr(middle_UP.ty, 0.5)

            middle_POS = pm.spaceLocator(name="mid_POS_{0}{1}".format (name, counter))
            self.toHide.append(middle_POS.getShape())
            extra.alignTo(middle_POS, mid)
            # pm.move(middle_POS, (0, 0, 0))
            # pm.makeIdentity(a=True)
            #
            pm.parent(mid, midCon)
            pm.parent(midCon, middle_OFF)
            pm.parent(middle_OFF, middle_AIM)
            pm.parent(middle_UP, middle_AIM, middle_POS)
            pm.aimConstraint(self.startConnection, middle_AIM, aimVector=(0, 0, -1), upVector=(0, 1, 0), wut=1,
                             wuo=middle_UP, mo=True)
            pm.pointConstraint(self.startConnection, self.endConnection, middle_POS)
            pm.pointConstraint(start_UP, end_UP, middle_UP)
            middle_POS_list.append(middle_POS)



        tePo = pm.pointConstraint([self.startConnection, self.endConnection], self.scaleGrp, mo=False)
        pm.delete(tePo)


        pm.makeIdentity(self.scaleGrp, a=True, t=True)

        pm.parent([self.startConnection, self.endConnection] + middle_POS_list, self.scaleGrp)


        # return
        ## take a look here
        # tempPoCon=pm.pointConstraint(startPoint, endPoint, self.scaleGrp)
        # pm.delete(tempPoCon)
        #
        # if side == "R":
        #     yVal = 180
        # else:
        #     yVal = 0
        #
        # tempAimCon=pm.orientConstraint(startPoint, self.scaleGrp, o=(orientation, yVal,0), mo=False)
        #
        # pm.delete(tempAimCon)

        extra.alignAndAim(self.scaleGrp, [startPoint, endPoint], [endPoint], upVector=upVector)



