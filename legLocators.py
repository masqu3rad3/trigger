import pymel.core as pm

### Create Locators

#  TODO // Make a fool check for if there is a naming conflict 

def createLegLocs():
    pm.spaceLocator(name="Loc_Rcon_l_leg")
    pm.move(0,14,0)                
    pm.spaceLocator(name="Loc_UpLeg_l_leg")
    pm.move(5,10,0)
    pm.spaceLocator(name="Loc_Knee_l_leg")
    pm.move(5,5,1)
    pm.spaceLocator(name="Loc_Foot_l_leg")
    pm.move(5,1,0)
    pm.spaceLocator(name="Loc_Ball_l_leg")
    pm.move(5,0,2)
    pm.spaceLocator(name="Loc_Toe_l_leg")
    pm.move(5,0,4)
    pm.spaceLocator(name="Loc_BankOut_l_leg")
    pm.move(4,0,2)
    pm.spaceLocator(name="Loc_BankIn_l_leg")
    pm.move(6,0,2)
    pm.spaceLocator(name="Loc_ToePv_l_leg")
    pm.move(5,0,4.3)
    pm.spaceLocator(name="Loc_HeelPv_l_leg")
    pm.move(5,0,-0.2)
createLegLocs()