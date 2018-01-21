import pymel.core as pm
import extraProcedures as extra

reload(extra)

import contIcons as icon

reload(icon)


class SimpleTail(object):

    def __init__(self):
        self.limbGrp = None
        self.scaleGrp = None
        self.cont_body = None
        self.cont_hips = None
        self.limbPlug = None
        self.nonScaleGrp = None
        self.cont_IK_OFF = None
        self.sockets = []
        self.scaleConstraints = []
        self.anchors = []
        self.anchorLocations = []
        self.deformerJoints = []

    def createSimpleTail(self, inits, suffix="", side="C", conts="cube"):
        if not isinstance(inits, list):
            tailRoot = inits.get("TailRoot")
            tails = (inits.get("Tail"))
            inits = [tailRoot] + (tails)

        suffix=(extra.uniqueName("limbGrp_%s" % suffix)).replace("limbGrp_", "")
        self.limbGrp = pm.group(name="limbGrp_%s" % suffix, em=True)

        print "Creating Simple Tail %s" %suffix

        if (len(inits) < 2):
            pm.error("Tail setup needs at least 2 initial joints")
            return



        self.scaleGrp = pm.group(name="scaleGrp_" + suffix, em=True)
        self.scaleConstraints.append(self.scaleGrp)

        # find the Socket
        # self.connectsTo = inits[0].getParent()
        # if tailParent != None and tailParent.type() == "joint":
        #     self.connectsTo = extra.identifyMaster(tailParent)[0]

        ## Create LimbPlug

        pm.select(d=True)
        self.limbPlug = pm.joint(name="limbPlug_" + suffix, p=inits[0].getTranslation(space="world"), radius=3)
        # self.scaleConstraints.append(self.limbPlug)
        pm.parentConstraint(self.limbPlug, self.scaleGrp)

        ## Get the orientation axises
        upAxis, mirroAxis, spineDir = extra.getRigAxes(inits[0])

        ## Create Joints
        self.deformerJoints=[]

        pm.select(d=True)

        for j in range (0,len(inits)):
            location = inits[j].getTranslation(space="world")
            bone = pm.joint(name="jDef_{0}_{1}".format(j, suffix), p=location)
            self.sockets.append(bone)
            # if j == 0 or j == len(inits):
            #     self.sockets.append(bone)
            self.deformerJoints.append(bone)

        for j in self.deformerJoints:
            pm.joint(j, e=True, zso=True, oj="yzx", sao="zup")

        pm.parent(self.deformerJoints[0], self.scaleGrp)

        pm.parent(self.scaleGrp, self.nonScaleGrp, self.cont_IK_OFF, self.limbGrp)

        contList=[]
        cont_off_list=[]
        for j in range (0,len(self.deformerJoints)):
            if not j == len(self.deformerJoints)-1:
                targetInit = inits[j+1]
                rotateOff = (90,90,0)
                scaleDis = extra.getDistance(self.deformerJoints[j], self.deformerJoints[j+1])/2
                cont = icon.cube(name="cont_%s_%s" %(suffix, str(j)), scale=(scaleDis,scaleDis,scaleDis))
                contList.append(cont)

                pm.xform(cont, piv=(0,-scaleDis,0))

                # extra.alignToAlter(cont, deformerJoints[j], 2)
                extra.alignAndAim(cont, targetList=[inits[j]], aimTargetList=[targetInit], upVector=upAxis,
                                  rotateOff=rotateOff)

                cont_OFF = extra.createUpGrp(cont, "OFF")
                cont_ORE = extra.createUpGrp(cont, "ORE")

                if side == "R":
                    pm.setAttr("{0}.s{1}".format(cont_OFF, "x"), -1)
                cont_off_list.append(cont_OFF)
                pm.parentConstraint(cont, self.deformerJoints[j], mo=False)

                # create additive scalability
                sGlobal = pm.createNode("multiplyDivide")
                self.limbPlug.scale >> sGlobal.input1
                cont.scale >> sGlobal.input2
                sGlobal.output >> self.deformerJoints[j].scale

                # cont.scale >> deformerJoints[j].scale

                if j != 0:
                    pm.parent(cont_off_list[j], contList[j-1])
                else:
                    pm.parent(cont_off_list[j], self.scaleGrp)
            else: ## last joint has no cont, use the previous one to scale that
                # pass
                extra.alignTo(self.deformerJoints[j], inits[-1])
                sGlobal = pm.createNode("multiplyDivide")
                self.limbPlug.scale >> sGlobal.input1
                contList[j-1].scale >> sGlobal.input2
                sGlobal.output >> self.deformerJoints[j].scale

            # pm.parentConstraint(cont, deformerJoints[j], mo=False)

            # pm.scaleConstraint(cont, deformerJoints[j], mo=False)
        # import mrCubic as mcube
        # mcube.mrCube(deformerJoints)


        pm.addAttr(self.scaleGrp, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True)
        pm.addAttr(self.scaleGrp, at="bool", ln="Joints_Visibility", sn="jointVis", defaultValue=True)
        pm.addAttr(self.scaleGrp, at="bool", ln="Rig_Visibility", sn="rigVis", defaultValue=False)
        # make the created attributes visible in the channelbox
        pm.setAttr(self.scaleGrp.contVis, cb=True)
        pm.setAttr(self.scaleGrp.jointVis, cb=True)
        pm.setAttr(self.scaleGrp.rigVis, cb=True)

        ## Cont visibilities
        for i in cont_off_list:
            self.scaleGrp.contVis >> i.v

        ## global joint visibilities
        for j in self.deformerJoints:
            self.scaleGrp.jointVis >> j.v

        ## Rig Visibilities
        self.scaleGrp.rigVis >> self.limbPlug.v

        ## COLORIZE
        # index = 17 ## default yellow color coding for non-sided tentacles
        # if side == "R":
        #     index = 13
        #     indexMin = 9
        #
        # elif side == "L":
        #     index = 6
        #     indexMin = 18
        for i in contList:
            extra.colorize(i, side)






