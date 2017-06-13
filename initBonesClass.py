
import pymel.core as pm
import extraProcedures as extra
reload(extra)

class initBones(object):
    fingers = 5
    spineSegments = 3
    def createInitBones(self):
        """
        This Function creates Initialization Bones to be used as reference points in the final rig.
        Args:
            fingers: Finger count for hand. Maximum:5, default:5
            spineSegments: Defines how many segments will be the spine splitted. Minimum:2, default:3
    
        Returns:
    
        """
        if self.fingers > 5 or self.fingers < 0:
            pm.error("Finger limits exceeded. Must be between 1-5")
            return
        if self.spineSegments+1 < 2 :
            pm.error("Minimum spine segment must be 1")
            return

        ### Create Locators

        #whichLeg="l_leg"

        ########### LEG BONES DEF ############
        # // TODO: FIX THE NAMES
        def initLegBones(whichLeg, dir):
            if dir == -1:
                side = 2
            if dir == 1:
                side = 1
            pm.select(d=True)
            if pm.objExists("jInit_*"+whichLeg):
                pm.error("Naming mismatch!!! There are Leg Initializers in the Scene")
                return
            root=pm.joint(p=(2*dir,14,0), name=("jInit_LegRoot_"+whichLeg))
            hip=pm.joint(p=(5*dir,10,0), name=("jInit_Hip_"+whichLeg))
            knee=pm.joint(p=(5*dir,5,1), name=("jInit_Knee_"+whichLeg))
            foot=pm.joint(p=(5*dir,1,0), name=("jInit_Foot_"+whichLeg))
            ball=pm.joint(p=(5*dir,0,2), name=("jInit_Ball_"+whichLeg))
            toe=pm.joint(p=(5*dir,0,4), name=("jInit_Toe_"+whichLeg))
            pm.select(d=True)
            bankout=pm.joint(p=(4*dir,0,2), name=("jInit_BankOut_"+whichLeg))
            pm.select(d=True)
            bankin=pm.joint(p=(6*dir,0,2), name=("jInit_BankIn_"+whichLeg))
            pm.select(d=True)
            toepv=pm.joint(p=(5*dir,0,4.3), name=("jInit_ToePv_"+whichLeg))
            pm.select(d=True)
            heelpv=pm.joint(p=(5*dir,0,-0.2), name=("jInit_HeelPv_"+whichLeg))
            pm.joint(root, e=True, zso=True, oj="xyz", sao="yup")
            pm.joint(hip, e=True, zso=True, oj="xyz", sao="yup")
            pm.joint(knee, e=True, zso=True, oj="xyz", sao="yup")
            pm.joint(foot, e=True, zso=True, oj="xyz", sao="yup")
            pm.joint(ball, e=True, zso=True, oj="xyz", sao="yup")
            pm.joint(toe, e=True, zso=True, oj="xyz", sao="yup")
            pm.parent(heelpv, foot)
            pm.parent(toepv, foot)
            pm.parent(bankin,foot)
            pm.parent(bankout,foot)

            pm.setAttr(root+".side", side)
            pm.setAttr(root+".type", 18)
            pm.setAttr(root+".otherType", "LegRoot")
            pm.setAttr(hip+".side", side)
            pm.setAttr(hip+".type", 2)
            pm.setAttr(knee+".side", side)
            pm.setAttr(knee+".type", 3)
            pm.setAttr(foot + ".side", side)
            pm.setAttr(foot + ".type", 4)

            pm.setAttr(ball + ".side", side)
            pm.setAttr(ball + ".type", 18)
            pm.setAttr(ball + ".otherType", "Ball")

            pm.setAttr(toe + ".side", side)
            pm.setAttr(toe + ".type", 5)

            pm.setAttr(heelpv + ".side", side)
            pm.setAttr(heelpv+ ".type", 18)
            pm.setAttr(heelpv+ ".otherType", "HeelPV")
            pm.setAttr(toepv + ".side", side)
            pm.setAttr(toepv+ ".type", 18)
            pm.setAttr(toepv + ".otherType", "ToePV")
            pm.setAttr(bankin+ ".side", side)
            pm.setAttr(bankin + ".type", 18)
            pm.setAttr(bankin + ".otherType", "BankIN")
            pm.setAttr(bankout + ".side", side)
            pm.setAttr(bankout + ".type", 18)
            pm.setAttr(bankout + ".otherType", "BankOUT")
            jointList=[root, hip, knee, foot, ball, toe, bankout, bankin,toepv, heelpv]
            for i in jointList:
                pm.setAttr(i + ".drawLabel", 1)
            return jointList


        ########### ARM BONES DEF ############

        def initArmBones(whichArm, dir):
            if dir == -1:
                side = 2
            if dir == 1:
                side = 1
            if pm.objExists("jInit_*"+whichArm):
                pm.error("Naming mismatch!!! There are Arm Initializers in the Scene")
                return
            pm.select(d=True)
            collar=pm.joint(p=(2*dir,25,0), name=("jInit_collar_"+whichArm))
            shoulder=pm.joint(p=(5*dir,25,0), name=("jInit_shoulder_"+whichArm))
            elbow=pm.joint(p=(9*dir,25,-1), name=("jInit_elbow_"+whichArm))
            hand=pm.joint(p=(14*dir,25,0), name=("jInit_hand_"+whichArm))
            # Orientation
            pm.joint(collar, e=True, zso=True, oj="xyz", sao="yup")
            pm.joint(shoulder, e=True, zso=True, oj="xyz", sao="yup")
            pm.joint(elbow, e=True, zso=True, oj="xyz", sao="yup")
            pm.joint(hand, e=True, zso=True, oj="xyz", sao="yup")
            # Joint Labeling
            pm.setAttr(collar+".side", side)
            pm.setAttr(collar+".type", 9)
            pm.setAttr(shoulder + ".side", side)
            pm.setAttr(shoulder + ".type", 10)
            pm.setAttr(elbow + ".side", side)
            pm.setAttr(elbow + ".type", 11)
            pm.setAttr(hand + ".side", side)
            pm.setAttr(hand + ".type", 12)

            jointList=[collar, shoulder, elbow, hand]
            for i in jointList:
                pm.setAttr(i + ".drawLabel", 1)

            if self.fingers==0:
                return jointList
            if self.fingers>0:
                pm.select(d=True)
                index00=pm.joint(p=(15.517*dir,25.05,0.656), name=("jInit_indexF00_"+whichArm))
                index01=pm.joint(p=(16.494*dir,25.05,0.868), name=("jInit_indexF01_"+whichArm))
                index02=pm.joint(p=(17.126*dir,25.05,1.005), name=("jInit_indexF02_"+whichArm))
                index03=pm.joint(p=(17.746*dir,25.05,1.139), name=("jInit_indexF03_"+whichArm))
                index04=pm.joint(p=(18.278*dir,25.05,1.254), name=("jInit_indexF04_"+whichArm))

                pm.parent(index00, hand)
                indexJoints = [index00,index01,index02,index03,index04]
                for i in indexJoints:
                    pm.joint(i, e=True, zso=True, oj="xyz", sao="yup")
                    pm.setAttr(i + ".side", side)
                    pm.setAttr(i + ".type", 19)
                pm.setAttr(index01 + ".drawLabel", 1)
                jointList.extend(indexJoints)

                if self.fingers>1:
                    pm.select(d=True)
                    thumb00=pm.joint(p=(14.681*dir,24.857,0.733), name=("jInit_thumb00_"+whichArm))
                    thumb01=pm.joint(p=(15.192*dir,24.79,1.375), name=("jInit_thumb01_"+whichArm))
                    thumb02=pm.joint(p=(15.64*dir,24.523,1.885), name=("jInit_thumb02_"+whichArm))
                    thumb03=pm.joint(p=(16.053*dir,24.276,2.356), name=("jInit_thumb03_"+whichArm))
                    pm.parent(thumb00, hand)
                    thumbJoints = [thumb00,thumb01,thumb02,thumb03]
                    for i in thumbJoints:
                        pm.joint(i, e=True, zso=True, oj="xyz", sao="yup")
                        pm.setAttr(i + ".side", side)
                        pm.setAttr(i + ".type", 14)
                    pm.setAttr(thumb01 + ".drawLabel", 1)
                    jointList.extend(thumbJoints)

                    if self.fingers>2:
                        pm.select(d=True)
                        middle00=pm.joint(p=(15.597*dir,25.123,0.063), name=("jInit_middleF00_"+whichArm))
                        middle01=pm.joint(p=(16.594*dir,25.123,0.137), name=("jInit_middleF01_"+whichArm))
                        middle02=pm.joint(p=(17.312*dir,25.123,0.19), name=("jInit_middleF02_"+whichArm))
                        middle03=pm.joint(p=(18.012*dir,25.123,0.242), name=("jInit_middleF03_"+whichArm))
                        middle04=pm.joint(p=(18.588*dir,25.123,0.285), name=("jInit_middleF04_"+whichArm))
                        pm.parent(middle00, hand)
                        middleJoints = [middle00,middle01,middle02,middle03,middle04]
                        for i in middleJoints:
                            pm.joint(i, e=True, zso=True, oj="xyz", sao="yup")
                            pm.setAttr(i + ".side", side)
                            pm.setAttr(i + ".type", 20)
                        pm.setAttr(middle01 + ".drawLabel", 1)
                        jointList.extend(middleJoints)

                        if self.fingers>3:
                            pm.select(d=True)
                            ring00=pm.joint(p=(15.605*dir,25.123,-0.437), name=("jInit_ringF00_"+whichArm))
                            ring01=pm.joint(p=(16.603*dir,25.123,-0.499), name=("jInit_ringF01_"+whichArm))
                            ring02=pm.joint(p=(17.301*dir,25.123,-0.541), name=("jInit_ringF02_"+whichArm))
                            ring03=pm.joint(p=(17.926*dir,25.123,-0.58), name=("jInit_ringF03_"+whichArm))
                            ring04=pm.joint(p=(18.414*dir,25.123,-0.61), name=("jInit_ringF04_"+whichArm))
                            pm.parent(ring00, hand)
                            ringJoints = [ring00,ring01,ring02,ring03,ring04]
                            for i in ringJoints:
                                pm.joint(i, e=True, zso=True, oj="xyz", sao="yup")
                                pm.setAttr(i + ".side", side)
                                pm.setAttr(i + ".type", 21)
                            pm.setAttr(ring01 + ".drawLabel", 1)
                            jointList.extend(ringJoints)

                            if self.fingers>4:
                                pm.select(d=True)
                                pinky00=pm.joint(p=(15.405*dir,25,-0.909), name=("jInit_pinkyF00_"+whichArm))
                                pinky01=pm.joint(p=(16.387*dir,25,-1.097), name=("jInit_pinkyF01_"+whichArm))
                                pinky02=pm.joint(p=(16.907*dir,25,-1.196), name=("jInit_pinkyF02_"+whichArm))
                                pinky03=pm.joint(p=(17.378*dir,25,-1.286), name=("jInit_pinkyF03_"+whichArm))
                                pinky04=pm.joint(p=(17.767*dir,25,-1.361), name=("jInit_pinkyF04_"+whichArm))
                                pm.parent(pinky00, hand)
                                pinkyJoints = [pinky00,pinky01,pinky02,pinky03,pinky04]
                                for i in pinkyJoints:
                                    pm.joint(i, e=True, zso=True, oj="xyz", sao="yup")
                                    pm.setAttr(i + ".side", side)
                                    pm.setAttr(i + ".type", 22)
                                pm.setAttr(pinky01 + ".drawLabel", 1)
                                jointList.extend(pinkyJoints)
                                if self.fingers>5:
                                    pm.error("finger limit is 5. Exceeded")
                return jointList


        ########### SPINE BONES DEF ############

        def initSpineBones():
            if pm.objExists("jInit_spine*"):
                pm.error("Naming mismatch!!! There are Spine Initializers in the Scene")
                return
            pm.select(d=True)
            if self.spineSegments<2:
                pm.message("Define at least 3 segment")
                return
            rPoint=14.0
            nPoint=21.0
            add=(nPoint-rPoint)/(self.spineSegments-1)
            jointList=[]
            for i in range(0, self.spineSegments):
                spine = pm.joint(p=(0,(rPoint+(add*i)),0), name="jInit_spine"+str(i))
                pm.setAttr(spine+ ".side", 0)
                type = 1 if i == 0 else 6
                pm.setAttr(spine + ".type", type)

                jointList.append(spine)
            neck = pm.joint(p=(0, 25.757, 0.249), name=("jInit_neck"))
            jointList.append(neck)
            head = pm.joint(p=(0, 29.418, 0.817), name=("jInit_head"))
            jointList.append(head)
            headEnd = pm.joint(p=(0, 32.848, 0.817), name=("jInit,headEnd"))
            jointList.append(headEnd)
            pm.select(d=True)
            jawStart = pm.joint(p=(0, 28.735, 1.367), name=("jInit_jawStart"))
            jointList.append(jawStart)
            jawEnd = pm.joint(p=(0, 27.857, 3.161), name=("jInit_jawEnd"))
            jointList.append(jawEnd)

            pm.setAttr(neck + ".side", 0)
            pm.setAttr(neck + ".type", 7)

            pm.setAttr(head + ".side", 0)
            pm.setAttr(head + ".type", 8)

            pm.setAttr(headEnd + ".side", 0)
            pm.setAttr(headEnd + ".type", 8)

            pm.setAttr(jawStart + ".side", 0)
            pm.setAttr(jawStart+ ".type", 18)
            pm.setAttr(jawStart+ ".otherType", "Jaw")

            pm.setAttr(jawEnd + ".side", 0)
            pm.setAttr(jawEnd+ ".type", 18)
            pm.setAttr(jawEnd+ ".otherType", "Jaw")

            pm.parent(jawStart, head)
            for i in jointList:
                pm.setAttr(i + ".drawLabel", 1)
            return jointList


        ## Create Leg Init Bones
        L_loc_grp_leg=pm.group(name="locGrp_l_leg", em=True)
        pm.setAttr(L_loc_grp_leg.v,0)
        R_loc_grp_leg=pm.group(name="locGrp_r_leg", em=True)
        pm.setAttr(R_loc_grp_leg.v,0)
        joints_l_leg=initLegBones("L_leg", 1)
        locators_l_leg=[]
        for i in range (0,len(joints_l_leg)):
            locator=pm.spaceLocator(name="loc_"+joints_l_leg[i].name())
            locators_l_leg.append(locator)
            pm.parentConstraint(joints_l_leg[i], locator, mo=False)
            pm.parent(locator,L_loc_grp_leg)
        joints_r_leg=initLegBones("R_leg", -1)
        locators_r_leg=[]
        for x in range (0,len(joints_r_leg)):
            locator=pm.spaceLocator(name="loc_"+joints_r_leg[x].name())
            locators_r_leg.append(locator)
            extra.alignTo(locator,joints_r_leg[x],2)
            pm.parentConstraint(locator, joints_r_leg[x], mo=True)
            extra.connectMirror(locators_l_leg[x], locators_r_leg[x],"X")
            pm.parent(locator,R_loc_grp_leg)

        ## Create Arm Init Bones

        L_loc_grp_arm=pm.group(name="locGrp_L_arm", em=True)
        pm.setAttr(L_loc_grp_arm.v,0)
        R_loc_grp_arm=pm.group(name="locGrp_R_arm", em=True)
        pm.setAttr(R_loc_grp_arm.v,0)
        joints_l_arm=initArmBones("L_arm", 1)
        locators_l_arm=[]
        for i in range (0,len(joints_l_arm)):
            locator=pm.spaceLocator(name="loc_"+joints_l_arm[i].name())
            locators_l_arm.append(locator)
            pm.parentConstraint(joints_l_arm[i], locator, mo=False)
            pm.parent(locator,L_loc_grp_arm)
        joints_r_arm=initArmBones("R_arm", -1)
        locators_r_arm=[]
        for x in range (0,len(joints_r_arm)):
            locator=pm.spaceLocator(name="loc_"+joints_r_arm[x].name())
            locators_r_arm.append(locator)
            extra.alignTo(locator,joints_r_arm[x],2)
            pm.parentConstraint(locator, joints_r_arm[x], mo=True)
            extra.connectMirror(locators_l_arm[x], locators_r_arm[x],"X")
            pm.parent(locator,R_loc_grp_arm)

        ## Create Spine Bones

        joints_spine=initSpineBones()

        pm.parent(joints_l_arm[0], joints_spine[self.spineSegments-1])
        pm.parent(joints_r_arm[0], joints_spine[self.spineSegments-1])
        pm.parent(joints_l_leg[0], joints_spine[0])
        pm.parent(joints_r_leg[0], joints_spine[0])

        initBonesGrp=pm.group(em=True, name="initBones")
        # pm.parent(joints_l_leg[0],initBonesGrp)
        pm.parent(L_loc_grp_leg,initBonesGrp)
        # pm.parent(joints_r_leg[0],initBonesGrp)
        pm.parent(R_loc_grp_leg,initBonesGrp)
        # pm.parent(joints_l_arm[0],initBonesGrp)
        pm.parent(L_loc_grp_arm,initBonesGrp)
        # pm.parent(joints_r_arm[0],initBonesGrp)
        pm.parent(R_loc_grp_arm,initBonesGrp)
        pm.parent(joints_spine[0],initBonesGrp)