import pymel.core as pm
import extraProcedures as extra
reload(extra)
import contIcons as icon
reload(icon)

class finger(object):

    fingerRoot = None
    defJoints = None
    conts = None

    def rigSingleFinger(self, handController, fingerBones, suffix="", mirror=False, mirrorAxis="Z", thumb=False):
        """
        Rigs a single finger. (or a similar limb)
        Args:
            handController: (Transform Node) The Object which will be the custom attributes created on. 
            fingerBones: (List of Joints) List of reference joints. Deformation joints will be created according to them.
            suffix: (String, optional) This string will be added at the end of the names of the new nodes.
            mirror: (Bool) If True, the controllers will be mirrored for the right limb. Default is False
            mirrorAxis: (String) Self explanatory. Valid options are "X", "Y", "Z" Letters must be capital.
            thumb: (Boolean) If true, the custom attributes will be suitable for thumb movement. 
    
        Returns: List [Finger Roots OFF Group List, Deformer Joints List, Control Curves List]
    
        """

        if "thumb" in fingerBones[0]:
            thumb=True
        if len(fingerBones)<2:
            pm.error("there should be minimum 2 joints")
            return
        # try to find which finger is this
        fingerTuple=("thumb", "index", "middle", "ring", "pinky")
        whichFinger=""
        for i in range(len(fingerTuple)):

            if fingerTuple[i] in fingerBones[0].name():
                whichFinger=fingerTuple[i]
                break
            else:
                whichFinger=fingerBones[0].name()

        # first add split line and spread attribute.
        pm.addAttr(handController, longName=whichFinger, at="enum", en="--------", k=True)
        pm.addAttr(handController, shortName="{0}{1}".format(whichFinger, "Spread"), defaultValue=0.0, at="float", k=True)

        self.defJoints = []
        pm.select(d=True)

        for i in range(0, len(fingerBones)):
            jPos = fingerBones[i].getTranslation(space="world")
            jOri = pm.joint(fingerBones[i], q=True, o=True)
            j = pm.joint(name="jDef_{0}{1}_{2}".format(whichFinger, i, suffix), radius=1.0)
            extra.alignTo(j, fingerBones[i], 2)
            if i == (len(fingerBones) - 1):
                replacedName = (j.name()).replace("jDef", "j")
                pm.rename(j, replacedName)
            self.defJoints.append(j)

        self.conts = []
        conts_OFF = []
        conts_ORE = []
        conts_con = []


        for i in range(0, len(self.defJoints)-1):
            #pm.joint(jDefList[i], e=True, zso=True, oj="xyz", sao="yup")
            contScl = (pm.getAttr(self.defJoints[1].tx) / 2)
            contName = ("cont_{0}{1}_{2}".format(whichFinger, i, suffix))
            cont = icon.circle(contName,(contScl,contScl,contScl), normal=(1,0,0))
            cont_OFF=extra.createUpGrp(cont,"OFF", mi=False)
            conts_OFF.append([cont_OFF])
            cont_ORE = extra.createUpGrp(cont, "ORE", mi=False)
            cont_con = extra.createUpGrp(cont, "con", mi=False)

            if mirror:
                #pm.setAttr("%s.scale%s" % (cont_OFF, mirrorAxis), -1)
                pm.setAttr("%s.rotate%s" %(cont_ORE, mirrorAxis), -180)

            extra.alignTo(cont_OFF, self.defJoints[i], 2)

            if i>0:
                pm.parent(cont_OFF, self.conts[len(self.conts)-1])
                pm.makeIdentity(cont, a=True)
            self.conts.append(cont)
            conts_con.append(cont_con)

            pm.parentConstraint(cont, self.defJoints[i], mo=True)

        # Spread

        sprMult=pm.createNode("multiplyDivide", name="sprMult_{0}_{1}".format(whichFinger, suffix))
        pm.setAttr(sprMult.input1Y, 0.4)
        pm.PyNode("{0}.{1}{2}".format(handController, whichFinger, "Spread")) >> sprMult.input2Y
        sprMult.outputY >> conts_con[0].rotateY
        pm.PyNode("{0}.{1}{2}".format(handController, whichFinger, "Spread")) >> conts_con[1].rotateY

        # Bend
        # add bend attributes for each joint (except the end joint)
        for f in range (0, (len(fingerBones)-1)):
            if f == 0 and thumb == True:
                bendAttr="{0}{1}".format(whichFinger, "UpDown")
            else:
                bendAttr = "{0}{1}{2}".format(whichFinger, "Bend", f)

            bend = pm.addAttr(handController, shortName=bendAttr, defaultValue=0.0, at="float", k=True)
            pm.PyNode("{0}.{1}".format(handController, bendAttr)) >> conts_con[f].rotateZ


        self.fingerRoot = conts_OFF[0]

