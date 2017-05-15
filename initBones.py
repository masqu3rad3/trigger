import pymel.core as pm
import sys
#sys.path.append("C:/Users/kutlu/Documents/maya/2017/scripts/tik_autorigger")
path='C:/Users/Arda/Documents/maya/2017/scripts/tik_autorigger'
if not path in sys.path:
    sys.path.append(path)
    
import extraProcedures as extra
reload(extra)

def createInitBones(fingers=5, spineSegments=3):
    """
    This Function creates Initialization Bones to be used as reference points in the final rig.
    Args:
        fingers: Finger count for hand. Maximum:5, default:5
        spineSegments: Defines how many segments will be the spine splitted. Minimum:2, default:3

    Returns:

    """
    # fingers=5
    # spineSegments=3
    ### Create Locators

    #whichLeg="l_leg"

    ########### LEG BONES DEF ############

    def initLegBones(whichLeg, dir):
        pm.select(d=True)
        if pm.objExists("jInit_*"+whichLeg):
            pm.error("Naming mismatch!!! There are Leg Initializers in the Scene")
            return
        rcon=pm.joint(p=(2*dir,14,0), name=("jInit_Rcon_"+whichLeg))
        upleg=pm.joint(p=(5*dir,10,0), name=("jInit_UpLeg_"+whichLeg))
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
        pm.joint(rcon, e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(upleg, e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(knee, e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(foot, e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(ball, e=True, zso=True, oj="xyz", sao="yup")
        pm.joint(toe, e=True, zso=True, oj="xyz", sao="yup")
        pm.parent(heelpv, foot)
        pm.parent(toepv, foot)
        pm.parent(bankin,foot)
        pm.parent(bankout,foot)
        jointList=[rcon, upleg, knee, foot, ball, toe, bankout, bankin,toepv, heelpv]
        return jointList





    #  TODO // Make a fool check for if there is a naming conflict

    ########### ARM BONES DEF ############

    def initArmBones(whichArm, dir, fingerCount=5):
        if pm.objExists("jInit_*"+whichArm):
            pm.error("Naming mismatch!!! There are Arm Initializers in the Scene")
            return
        pm.select(d=True)
        shoulder=pm.joint(p=(2*dir,25,0), name=("jInit_Shoulder_"+whichArm))
        uparm=pm.joint(p=(5*dir,25,0), name=("jInit_Up_"+whichArm))
        lowarm=pm.joint(p=(9*dir,25,-1), name=("jInit_Low_"+whichArm))
        lowendarm=pm.joint(p=(14*dir,25,0), name=("jInit_LowEnd_"+whichArm))
        pm.addAttr(lowendarm, shortName="fingerCount", longName="fingerCount", defaultValue=fingerCount, minValue=0,
                   maxValue=5, at="long", k=False)
        jointList=[shoulder, uparm, lowarm, lowendarm]

        if fingerCount==0:
            return jointList
        if fingerCount>0:
            pm.select(d=True)
            index00=pm.joint(p=(15.517*dir,25.05,0.656), name=("jInit_index00_"+whichArm))
            index01=pm.joint(p=(16.494*dir,25.05,0.868), name=("jInit_index01_"+whichArm))
            index02=pm.joint(p=(17.126*dir,25.05,1.005), name=("jInit_index02_"+whichArm))
            index03=pm.joint(p=(17.746*dir,25.05,1.139), name=("jInit_index03_"+whichArm))
            index04=pm.joint(p=(18.278*dir,25.05,1.254), name=("jInit_index04_"+whichArm))
            pm.parent(index00, lowendarm)
            jointList.extend([index00,index01,index02,index03,index04])

            if fingerCount>1:
                pm.select(d=True)
                thumb00=pm.joint(p=(14.681*dir,24.857,0.733), name=("jInit_thumb00_"+whichArm))
                thumb01=pm.joint(p=(15.192*dir,24.79,1.375), name=("jInit_thumb01_"+whichArm))
                thumb02=pm.joint(p=(15.64*dir,24.523,1.885), name=("jInit_thumb02_"+whichArm))
                thumb03=pm.joint(p=(16.053*dir,24.276,2.356), name=("jInit_thumb03_"+whichArm))
                pm.parent(thumb00, lowendarm)
                jointList.extend([thumb00,thumb01,thumb02,thumb03])

                if fingerCount>2:
                    pm.select(d=True)
                    middle00=pm.joint(p=(15.597*dir,25.123,0.063), name=("jInit_middle00_"+whichArm))
                    middle01=pm.joint(p=(16.594*dir,25.123,0.137), name=("jInit_middle01_"+whichArm))
                    middle02=pm.joint(p=(17.312*dir,25.123,0.19), name=("jInit_middle02_"+whichArm))
                    middle03=pm.joint(p=(18.012*dir,25.123,0.242), name=("jInit_middle03_"+whichArm))
                    middle04=pm.joint(p=(18.588*dir,25.123,0.285), name=("jInit_middle04_"+whichArm))
                    pm.parent(middle00, lowendarm)
                    jointList.extend([middle00,middle01,middle02,middle03,middle04])

                    if fingerCount>3:
                        pm.select(d=True)
                        ring00=pm.joint(p=(15.605*dir,25.123,-0.437), name=("jInit_ring00_"+whichArm))
                        ring01=pm.joint(p=(16.603*dir,25.123,-0.499), name=("jInit_ring01_"+whichArm))
                        ring02=pm.joint(p=(17.301*dir,25.123,-0.541), name=("jInit_ring02_"+whichArm))
                        ring03=pm.joint(p=(17.926*dir,25.123,-0.58), name=("jInit_ring03_"+whichArm))
                        ring04=pm.joint(p=(18.414*dir,25.123,-0.61), name=("jInit_ring04_"+whichArm))
                        pm.parent(ring00, lowendarm)
                        jointList.extend([ring00,ring01,ring02,ring03,ring04])

                        if fingerCount>4:
                            pm.select(d=True)
                            pinky00=pm.joint(p=(15.405*dir,25,-0.909), name=("jInit_pinky00_"+whichArm))
                            pinky01=pm.joint(p=(16.387*dir,25,-1.097), name=("jInit_pinky01_"+whichArm))
                            pinky02=pm.joint(p=(16.907*dir,25,-1.196), name=("jInit_pinky02_"+whichArm))
                            pinky03=pm.joint(p=(17.378*dir,25,-1.286), name=("jInit_pinky03_"+whichArm))
                            pinky04=pm.joint(p=(17.767*dir,25,-1.361), name=("jInit_pinky04_"+whichArm))
                            pm.parent(pinky00, lowendarm)
                            jointList.extend([pinky00,pinky01,pinky02,pinky03,pinky04])
                            if fingerCount>5:
                                pm.error("finger limit is 5. Exceeded")
            return jointList


    ########### SPINE BONES DEF ############

    def initSpineBones(spineCount=3):
        if pm.objExists("jInit_spine*"):
            pm.error("Naming mismatch!!! There are Spine Initializers in the Scene")
            return
        pm.select(d=True)
        if spineCount<2:
            pm.message("Define at least 3 segment")
            return
        rPoint=14.0
        nPoint=25.0
        add=(nPoint-rPoint)/(spineCount-1)
        jointList=[]
        for i in range(0, spineCount):
            spine = pm.joint(p=(0,(rPoint+(add*i)),0), name="jInit_spine"+str(i))
            jointList.append(spine)
        neck = pm.joint(p=(0, 26.757, 0.249), name=("jInit_neck"))
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
        pm.parent(jawStart, head)
        return jointList


    ## Create Leg Init Bones
    L_loc_grp_leg=pm.group(name="locGrp_l_leg", em=True)
    pm.setAttr(L_loc_grp_leg.v,0)
    R_loc_grp_leg=pm.group(name="locGrp_r_leg", em=True)
    pm.setAttr(R_loc_grp_leg.v,0)
    joints_l_leg=initLegBones("l_leg", 1)
    locators_l_leg=[]
    for i in range (0,len(joints_l_leg)):
        locator=pm.spaceLocator(name="loc_"+joints_l_leg[i].name())
        locators_l_leg.append(locator)
        pm.parentConstraint(joints_l_leg[i], locator, mo=False)
        pm.parent(locator,L_loc_grp_leg)
    joints_r_leg=initLegBones("r_leg", -1)
    locators_r_leg=[]
    for x in range (0,len(joints_r_leg)):
        locator=pm.spaceLocator(name="loc_"+joints_r_leg[x].name())
        locators_r_leg.append(locator)
        extra.alignTo(locator,joints_r_leg[x],2)
        pm.parentConstraint(locator, joints_r_leg[x], mo=True)
        extra.connectMirror(locators_l_leg[x], locators_r_leg[x],"X")
        pm.parent(locator,R_loc_grp_leg)

    ## Create Arm Init Bones

    L_loc_grp_arm=pm.group(name="locGrp_l_arm", em=True)
    pm.setAttr(L_loc_grp_arm.v,0)
    R_loc_grp_arm=pm.group(name="locGrp_r_arm", em=True)
    pm.setAttr(R_loc_grp_arm.v,0)
    joints_l_arm=initArmBones("l_arm", 1, fingers)
    locators_l_arm=[]
    for i in range (0,len(joints_l_arm)):
        locator=pm.spaceLocator(name="loc_"+joints_l_arm[i].name())
        locators_l_arm.append(locator)
        pm.parentConstraint(joints_l_arm[i], locator, mo=False)
        pm.parent(locator,L_loc_grp_arm)
    joints_r_arm=initArmBones("r_arm", -1, fingers)
    locators_r_arm=[]
    for x in range (0,len(joints_r_arm)):
        locator=pm.spaceLocator(name="loc_"+joints_r_arm[x].name())
        locators_r_arm.append(locator)
        extra.alignTo(locator,joints_r_arm[x],2)
        pm.parentConstraint(locator, joints_r_arm[x], mo=True)
        extra.connectMirror(locators_l_arm[x], locators_r_arm[x],"X")
        pm.parent(locator,R_loc_grp_arm)

    ## Create Spine Bones

    joints_spine=initSpineBones(spineSegments)

    initBonesGrp=pm.group(em=True, name="initBones")
    pm.parent(joints_l_leg[0],initBonesGrp)
    pm.parent(L_loc_grp_leg,initBonesGrp)
    pm.parent(joints_r_leg[0],initBonesGrp)
    pm.parent(R_loc_grp_leg,initBonesGrp)
    pm.parent(joints_l_arm[0],initBonesGrp)
    pm.parent(L_loc_grp_arm,initBonesGrp)
    pm.parent(joints_r_arm[0],initBonesGrp)
    pm.parent(R_loc_grp_arm,initBonesGrp)
    pm.parent(joints_spine[0],initBonesGrp)