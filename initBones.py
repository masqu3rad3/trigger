import pymel.core as pm

### Create Locators

#  TODO // Make a fool check for if there is a naming conflict 

whichLeg="l_leg"

def initLegBones(whichLeg):
    pm.select(d=True)
    rcon=pm.joint(p=(0,14,0), name=("jInit_Rcon_"+whichLeg))
    upleg=pm.joint(p=(5,10,0), name=("jInit_UpLeg_"+whichLeg))
    knee=pm.joint(p=(5,5,1), name=("jInit_Knee_"+whichLeg))
    foot=pm.joint(p=(5,1,0), name=("jInit_Foot_"+whichLeg))
    ball=pm.joint(p=(5,0,2), name=("jInit_Ball_"+whichLeg))
    toe=pm.joint(p=(5,0,4), name=("jInit_Toe_"+whichLeg))
    pm.select(d=True)
    bankout=pm.joint(p=(4,0,2), name=("jInit_BankOut_"+whichLeg))
    pm.select(d=True)
    bankin=pm.joint(p=(6,0,2), name=("jInit_BankIn_"+whichLeg))
    pm.select(d=True)
    toepv=pm.joint(p=(5,0,4.3), name=("jInit_ToePv_"+whichLeg))
    pm.select(d=True)
    heelpv=pm.joint(p=(5,0,-0.2), name=("jInit_HeelPv_"+whichLeg))
    pm.joint(rcon, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(upleg, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(knee, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(foot, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(ball, e=True, zso=True, oj="xyz", sao="yup")
    pm.joint(toe, e=True, zso=True, oj="xyz", sao="yup")

#  TODO // Make a fool check for if there is a naming conflict 


def initArmBones(whichArm):
    pm.select(d=True)
    shoulder=pm.joint(p=(0,10,0), name=("jInit_Shoulder_"+whichArm))
    uparm=pm.joint(p=(2,10,0), name=("jInit_Up_"+whichArm))
    lowarm=pm.joint(p=(7,10,-1), name=("jInit_Low_"+whichArm))
    lowendarm=pm.joint(p=(12,10,0), name=("jInit_LowEnd_"+whichArm))

    pm.select(d=True)
    pinky00=pm.joint(p=(14,10,-1), name=("jInit_pinky00_"+whichArm))
    pinky01=pm.joint(p=(15,10,-1), name=("jInit_pinky01_"+whichArm))
    pinky02=pm.joint(p=(16,10,-1), name=("jInit_pinky02_"+whichArm))
    pinky03=pm.joint(p=(17,10,-1), name=("jInit_pinky03_"+whichArm))

    pm.select(d=True)
    ring00=pm.joint(p=(14,10,-0.5), name=("jInit_ring00_"+whichArm))
    ring01=pm.joint(p=(15,10,-0.5), name=("jInit_ring01_"+whichArm))
    ring02=pm.joint(p=(16,10,-0.5), name=("jInit_ring02_"+whichArm))
    ring03=pm.joint(p=(17,10,-0.5), name=("jInit_ring03_"+whichArm))

    pm.select(d=True)
    middle00=pm.joint(p=(14,10,0), name=("jInit_middle00_"+whichArm))
    middle01=pm.joint(p=(15,10,0), name=("jInit_middle01_"+whichArm))
    middle02=pm.joint(p=(16,10,0), name=("jInit_middle02_"+whichArm))
    middle03=pm.joint(p=(17,10,0), name=("jInit_middle03_"+whichArm))

    pm.select(d=True)
    index00=pm.joint(p=(14,10,0.5), name=("jInit_index00_"+whichArm))
    index01=pm.joint(p=(15,10,0.5), name=("jInit_index01_"+whichArm))
    index02=pm.joint(p=(16,10,0.5), name=("jInit_index02_"+whichArm))
    index03=pm.joint(p=(17,10,0.5), name=("jInit_index03_"+whichArm))

    pm.select(d=True)
    thumb00=pm.joint(p=(13,10,1), name=("jInit_thumb00_"+whichArm))
    thumb01=pm.joint(p=(13,10,1.5), name=("jInit_thumb01_"+whichArm))
    thumb02=pm.joint(p=(13,10,2), name=("jInit_thumb02_"+whichArm))
    thumb03=pm.joint(p=(13,10,2.5), name=("jInit_thumb03_"+whichArm))

    pm.parent(pinky00, lowendarm)
    pm.parent(ring00, lowendarm)
    pm.parent(middle00, lowendarm)
    pm.parent(index00, lowendarm)
    pm.parent(thumb00, lowendarm)

initArmBones("l_arm")
initLegBones("l_leg")
