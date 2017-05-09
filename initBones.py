import pymel.core as pm
import sys
#sys.path.append("C:/Users/kutlu/Documents/maya/2017/scripts/tik_autorigger")
path='C:/Users/Arda/Documents/maya/2017/scripts/tik_autorigger'
if not path in sys.path:
    sys.path.append(path)
    
import extraProcedures as extra
reload(extra)
    
### Create Locators

#  TODO // Make a fool check for if there is a naming conflict 

#whichLeg="l_leg"



def initLegBones(whichLeg, dir):
    jointList=[]
    pm.select(d=True)
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

L_loc_grp_arm=pm.group(name="locGrp_l_leg", em=True)
pm.setAttr(L_loc_grp_arm.v,0)
R_loc_grp_arm=pm.group(name="locGrp_r_leg", em=True)
pm.setAttr(R_loc_grp_arm.v,0)
L_joints=initLegBones("l_leg", 1)
L_locators=[]
for i in range (0,len(L_joints)):
    locator=pm.spaceLocator(name="loc_"+L_joints[i].name())
    L_locators.append(locator)
    pm.parentConstraint(L_joints[i], locator, mo=False)
    pm.parent(locator,L_loc_grp_arm)
R_joints=initLegBones("r_leg", -1)
R_locators=[]
for x in range (0,len(R_joints)):
    locator=pm.spaceLocator(name="loc_"+R_joints[x].name())
    R_locators.append(locator)
    extra.alignTo(locator,R_joints[x],2)
    pm.parentConstraint(locator, R_joints[x], mo=True)
    extra.connectMirror(L_locators[x], R_locators[x],"X")
    pm.parent(locator,R_loc_grp_arm)



#  TODO // Make a fool check for if there is a naming conflict 


def initArmBones(whichArm, dir):
    pm.select(d=True)
    shoulder=pm.joint(p=(2*dir,25,0), name=("jInit_Shoulder_"+whichArm))
    uparm=pm.joint(p=(5*dir,25,0), name=("jInit_Up_"+whichArm))
    lowarm=pm.joint(p=(9*dir,25,-1), name=("jInit_Low_"+whichArm))
    lowendarm=pm.joint(p=(14*dir,25,0), name=("jInit_LowEnd_"+whichArm))

    pm.select(d=True)
    pinky00=pm.joint(p=(15.405*dir,25,-0.909), name=("jInit_pinky00_"+whichArm))
    pinky01=pm.joint(p=(16.387*dir,25,-1.097), name=("jInit_pinky01_"+whichArm))
    pinky02=pm.joint(p=(16.907*dir,25,-1.196), name=("jInit_pinky02_"+whichArm))
    pinky03=pm.joint(p=(17.378*dir,25,-1.286), name=("jInit_pinky03_"+whichArm))
    pinky04=pm.joint(p=(17.767*dir,25,-1.361), name=("jInit_pinky04_"+whichArm))

    pm.select(d=True)
    ring00=pm.joint(p=(15.605*dir,25.123,-0.437), name=("jInit_ring00_"+whichArm))
    ring01=pm.joint(p=(16.603*dir,25.123,-0.499), name=("jInit_ring01_"+whichArm))
    ring02=pm.joint(p=(17.301*dir,25.123,-0.541), name=("jInit_ring02_"+whichArm))
    ring03=pm.joint(p=(17.926*dir,25.123,-0.58), name=("jInit_ring03_"+whichArm))
    ring04=pm.joint(p=(18.414*dir,25.123,-0.61), name=("jInit_ring04_"+whichArm))

    pm.select(d=True)
    middle00=pm.joint(p=(15.597*dir,25.123,0.063), name=("jInit_middle00_"+whichArm))
    middle01=pm.joint(p=(16.594*dir,25.123,0.137), name=("jInit_middle01_"+whichArm))
    middle02=pm.joint(p=(17.312*dir,25.123,0.19), name=("jInit_middle02_"+whichArm))
    middle03=pm.joint(p=(18.012*dir,25.123,0.242), name=("jInit_middle03_"+whichArm))
    middle04=pm.joint(p=(18.588*dir,25.123,0.285), name=("jInit_middle04_"+whichArm))

    pm.select(d=True)
    index00=pm.joint(p=(15.517*dir,25.05,0.656), name=("jInit_index00_"+whichArm))
    index01=pm.joint(p=(16.494*dir,25.05,0.868), name=("jInit_index01_"+whichArm))
    index02=pm.joint(p=(17.126*dir,25.05,1.005), name=("jInit_index02_"+whichArm))
    index03=pm.joint(p=(17.746*dir,25.05,1.139), name=("jInit_index03_"+whichArm))
    index04=pm.joint(p=(18.278*dir,25.05,1.254), name=("jInit_index04_"+whichArm))

    pm.select(d=True)
    thumb00=pm.joint(p=(14.681*dir,24.857,0.733), name=("jInit_thumb00_"+whichArm))
    thumb01=pm.joint(p=(15.192*dir,24.79,1.375), name=("jInit_thumb01_"+whichArm))
    thumb02=pm.joint(p=(15.64*dir,24.523,1.885), name=("jInit_thumb02_"+whichArm))
    thumb03=pm.joint(p=(16.053*dir,24.276,2.356), name=("jInit_thumb03_"+whichArm))

    pm.parent(pinky00, lowendarm)
    pm.parent(ring00, lowendarm)
    pm.parent(middle00, lowendarm)
    pm.parent(index00, lowendarm)
    pm.parent(thumb00, lowendarm)
    jointList=[shoulder, uparm, lowarm, lowendarm, pinky00, pinky01, pinky02, pinky03, ring00, ring01, ring02, ring03, middle00, middle01, middle02, middle03, index00, index01, index02, index03, thumb00, thumb01, thumb02, thumb03]
    return jointList


L_loc_grp_arm=pm.group(name="locGrp_l_arm", em=True)
pm.setAttr(L_loc_grp_arm.v,0)
R_loc_grp_arm=pm.group(name="locGrp_r_arm", em=True)
pm.setAttr(R_loc_grp_arm.v,0)
L_joints_arm=initArmBones("l_arm", 1)
L_locators_arm=[]
for i in range (0,len(L_joints_arm)):
    locator=pm.spaceLocator(name="loc_"+L_joints_arm[i].name())
    L_locators_arm.append(locator)
    pm.parentConstraint(L_joints_arm[i], locator, mo=False)
    pm.parent(locator,L_loc_grp_arm)
R_joints_arm=initArmBones("r_arm", -1)
R_locators_arm=[]
for x in range (0,len(R_joints_arm)):
    locator=pm.spaceLocator(name="loc_"+R_joints_arm[x].name())
    R_locators_arm.append(locator)
    extra.alignTo(locator,R_joints_arm[x],2)
    pm.parentConstraint(locator, R_joints_arm[x], mo=True)
    extra.connectMirror(L_locators_arm[x], R_locators_arm[x],"X")
    pm.parent(locator,R_loc_grp_arm)


