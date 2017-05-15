import pymel.core as pm
import extraProcedures as extra
reload(extra)
import contIcons as icon
reload(icon)

def fingerRig(handController, fingerBones, whichArm, thumb=False):
    whichFinger = fingerBones[0].name()
    whichFinger = whichFinger.replace("jInit_", "")
    whichFinger = whichFinger.replace(whichArm, "")
    whichFinger = whichFinger.replace("00_", "")
    if thumb == False:

        pm.addAttr(handController, longName=whichFinger, at="enum", en="--------", k=True)
        pm.addAttr(handController, shortName=("{0}{1}".format(whichFinger, "BendA")), longName=("{0}{1}".format(whichFinger, "_Bend_A")), defaultValue=0.0, at="float", k=True)
        pm.addAttr(handController, shortName=("{0}{1}".format(whichFinger, "BendB")), longName=("{0}{1}".format(whichFinger, "_Bend_B")), defaultValue=0.0, at="float", k=True)
        pm.addAttr(handController, shortName="{0}{1}".format(whichFinger, "BendC"), longName="{0}{1}".format(whichFinger, "_Bend_C"), defaultValue=0.0, at="float", k=True)
        pm.addAttr(handController, shortName="{0}{1}".format(whichFinger, "Spread"), longName="{0}{1}".format(whichFinger, "_Spread"), defaultValue=0.0, at="float", k=True)

        jDefList = []
        pm.select(d=True)
        for i in range(0, len(fingerBones)):
            jPos = fingerBones[i].getTranslation(space="world")
            j = pm.joint(name="jDef_{0}{1}_{2}".format(whichFinger, i, whichArm), p=jPos, radius=1.0)

            if i == (len(fingerBones) - 1):
                replacedName = (j.name()).replace("jDef", "j")
                pm.rename(j, replacedName)
            jDefList.append(j)

        conts = []
        conts_OFF = []
        conts_ORE = []
        conts_con = []
        for i in range(0, len(jDefList)):  # this second loop is necessary because joints needs to be aligned
            pm.joint(jDefList[i], e=True, zso=True, oj="xyz", sao="yup")
            contScl = (pm.getAttr(jDefList[1].tx)/2)
            contName = ("cont_{0}{1}_{2}".format(whichFinger, i, whichArm))
            cont = icon.circle(contName,(contScl,contScl,contScl), normal=(1,0,0))
            #cont = pm.circle(name="cont_{0}{1}_{2}".format(whichFinger, i, whichArm), radius=handContScale, nr=(1, 0, 0))
            extra.alignTo(cont, jDefList[i], 0)
            cont_OFF=extra.createUpGrp(cont,"OFF")
            cont_ORE = extra.createUpGrp(cont, "ORE")
            cont_con = extra.createUpGrp(cont, "con")
            if whichArm=="r_arm":
                pm.setAttr(cont_ORE.rotateZ, -180)
            extra.alignTo(cont, jDefList[i], 2)

    # //TODO WORKING ON THE PROCEDURALISM -- THIS IS THE TARGET





    else:
        pm.addAttr(handController, longName=whichFinger, at="enum", en="--------", k=True)
        pm.addAttr(handController, shortName=("{0}{1}".format(whichFinger, "UpDown")),
                   longName=("{0}{1}".format(whichFinger, "_Bend_A")), defaultValue=0.0, at="float", k=True)
        pm.addAttr(handController, shortName=("{0}{1}".format(whichFinger, "BendA")),
                   longName=("{0}{1}".format(whichFinger, "_Bend_B")), defaultValue=0.0, at="float", k=True)
        pm.addAttr(handController, shortName="{0}{1}".format(whichFinger, "BendB"),
                   longName="{0}{1}".format(whichFinger, "_Bend_C"), defaultValue=0.0, at="float", k=True)
        pm.addAttr(handController, shortName="{0}{1}".format(whichFinger, "Spread"),
                   longName="{0}{1}".format(whichFinger, "_Spread"), defaultValue=0.0, at="float", k=True)



