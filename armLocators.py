import pymel.core as pm

### Create Locators

#  TODO // Make a fool check for if there is a naming conflict 

def createArmLocs():
    pm.spaceLocator(name="Loc_Shoulder_l_arm")
    pm.move(0,10,0)
    pm.spaceLocator(name="Loc_Up_l_arm")
    pm.move(2,10,0)
    pm.spaceLocator(name="Loc_Low_l_arm")
    pm.move(7,10,-1)
    pm.spaceLocator(name="Loc_LowEnd_l_arm")
    pm.move(12,10,0)

createArmLocs()