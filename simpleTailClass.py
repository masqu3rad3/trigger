import pymel.core as pm
import collections
import extraProcedures as extra

reload(extra)

import contIcons as icon

reload(icon)


class simpleTail(object):
    scaleGrp = None
    cont_body = None
    cont_hips = None
    limbPlug = None
    rootSocket = None
    nonScaleGrp = None
    connectsTo = None
    cont_IK_OFF = None
    scaleConstraints = []
    anchors = []
    anchorLocations = []

    def createSimpleTail(self, inits, suffix=""):
        print inits
        tailRoot = inits.get("TailRoot")
        tails = (inits.get("Tail"))

        inits = [tailRoot] + sorted(tails)


        idCounter = 0
        ## create an unique suffix
        while pm.objExists("scaleGrp_" + suffix):
            suffix = "%s%s" % (suffix, str(idCounter + 1))

        print "Creating Simple Tail %s" %suffix

        if (len(inits) < 2):
            pm.error("Insufficient Spine Initialization Joints")
            return

        self.scaleGrp = pm.group(name="scaleGrp_" + suffix, em=True)
        self.scaleConstraints.append(self.scaleGrp)

        # find the Socket
        self.connectsTo = inits[0].getParent()
        # if tailParent != None and tailParent.type() == "joint":
        #     self.connectsTo = extra.identifyMaster(tailParent)[0]

        ## Create LimbPlug

        pm.select(d=True)
        self.limbPlug = pm.joint(name="limbPlug_" + suffix, p=inits[0].getTranslation(space="world"), radius=3)
        # self.scaleConstraints.append(self.limbPlug)
        pm.parentConstraint(self.limbPlug, self.scaleGrp)

        ## Create Joints
        deformerJoints=[]

        pm.select(d=True)

        for j in range (0,len(inits)):
            location = inits[j].getTranslation(space="world")
            bone = pm.joint(name="jDef_" + suffix, p=location)
            deformerJoints.append(bone)

        for j in deformerJoints:
            pm.joint(j, e=True, zso=True, oj="yzx", sao="zup")

        pm.parent(deformerJoints[0], self.scaleGrp)

        contList=[]
        cont_OREList=[]
        for j in range (0,len(deformerJoints)):
            print "defj", deformerJoints[j]
            if j != len(deformerJoints)-1:
                scaleDis = extra.getDistance(deformerJoints[j], deformerJoints[j+1])/2
                cont = icon.cube(name="cont_%s_%s" %(suffix, str(j)), scale=(scaleDis,scaleDis,scaleDis))
                contList.append(cont)
                # extra.alignToAlter(cont, bone, 2)

                pm.xform(cont, piv=(0,-scaleDis,0))

                extra.alignToAlter(cont, deformerJoints[j], 2)

                # pm.makeIdentity(cont)

                cont_ORE = extra.createUpGrp(cont, "ORE")
                cont_OREList.append(cont_ORE)
                # extra.alignToAlter(cont_ORE, deformerJoints[j], 2)
                pm.parentConstraint(cont, deformerJoints[j], mo=True)

                # create additive scalability
                sGlobal = pm.createNode("multiplyDivide")
                self.limbPlug.scale >> sGlobal.input1
                cont.scale >> sGlobal.input2
                sGlobal.output >> deformerJoints[j].scale

                # cont.scale >> deformerJoints[j].scale

                if j != 0:
                    pm.parent(cont_OREList[j], contList[j-1])
                else:
                    pm.parent(cont_OREList[j], self.scaleGrp)
            else: ## last joint has no cont, use the previous one to scale that
                sGlobal = pm.createNode("multiplyDivide")
                self.limbPlug.scale >> sGlobal.input1
                contList[j-1].scale >> sGlobal.input2
                sGlobal.output >> deformerJoints[j].scale
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
        for i in cont_OREList:
            self.scaleGrp.contVis >> i.v

        ## global joint visibilities
        for j in deformerJoints:
            self.scaleGrp.jointVis >> j.v

        ## Rig Visibilities
        self.scaleGrp.rigVis >> self.limbPlug.v

        ## COLORIZE
        index = 17
        for i in contList:
            extra.colorize(i, index)






