import pymel.core as pm
import extraProcedures as extra
reload(extra)
import contIcons as icon
reload(icon)



def rigSingleFinger(handController, fingerBones, suffix, mirror=False, mirrorAxis="Z", thumb=False):
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

    jDefList = []
    pm.select(d=True)
    for i in range(0, len(fingerBones)):
        jPos = fingerBones[i].getTranslation(space="world")
        j = pm.joint(name="jDef_{0}{1}_{2}".format(whichFinger, i, suffix), p=jPos, radius=1.0)

        if i == (len(fingerBones) - 1):
            replacedName = (j.name()).replace("jDef", "j")
            pm.rename(j, replacedName)
        jDefList.append(j)

    conts = []
    conts_OFF = []
    conts_ORE = []
    conts_con = []

    for h in jDefList:
        pm.joint(h, e=True, zso=True, oj="xyz", sao="yup") # this second loop is necessary because joints needs to be aligned

    for i in range(0, len(jDefList)-1):
        #pm.joint(jDefList[i], e=True, zso=True, oj="xyz", sao="yup")
        contScl = (pm.getAttr(jDefList[1].tx)/2)
        contName = ("cont_{0}{1}_{2}".format(whichFinger, i, suffix))
        cont = icon.circle(contName,(contScl,contScl,contScl), normal=(1,0,0))
        cont_OFF=extra.createUpGrp(cont,"OFF", mi=False)
        conts_OFF.append([cont_OFF])
        cont_ORE = extra.createUpGrp(cont, "ORE", mi=False)
        cont_con = extra.createUpGrp(cont, "con", mi=False)




        extra.alignTo(cont_OFF, jDefList[i], 2)

        if mirror:
            pm.setAttr("%s.scale%s" % (cont_OFF, mirrorAxis), -1)
        #     # pm.setAttr("{0}.rotate{1}".format(cont_ORE, mirrorAxis), -180)

        if i>0:
            pm.parent(cont_OFF, conts[len(conts)-1])
            pm.makeIdentity(cont, a=True)
        conts.append(cont)
        conts_con.append(cont_con)

        pm.parentConstraint(cont, jDefList[i], mo=True)

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

    # Return [fingerRoot_OFF, jDefList]
    returnList=[conts_OFF[0], jDefList, conts]
    return returnList


def rigFingers(rootBone, controller, suffix, mirror=False):
    rootPosition=rootBone.getTranslation(space="world")
    rootMaster = pm.spaceLocator(name="handMaster_" + suffix)
    extra.alignTo(rootMaster, rootBone, 2)
    pm.select(d=True)
    #deformerJoints=[]
    jDef_Root=pm.joint(name="jDef_fingerRoot_"+suffix, p=rootPosition, radius=1.0)
    deformerJoints=[[jDef_Root]]
    pm.parent(jDef_Root, rootMaster)
    fingerRoots=pm.listRelatives(rootBone, children=True, type="joint")
    # fingerCount=len(fingerRoots)

    allControllers_con=[]

    for i in fingerRoots:
        fingerBones=pm.listRelatives(i, children=True, ad=True, type="joint")
        fingerBones.append(i)
        fingerBones=list(reversed(fingerBones))
        finger=rigSingleFinger(controller, fingerBones, suffix, mirror=mirror)
        fingerCons = finger[2]
        allControllers_con.append(fingerCons)
        pm.parent(finger[0],rootMaster)
        pm.parent(finger[1][0],jDef_Root)
        deformerJoints.append(finger[1])

    #return [rootmaster, allControllers_con]
    return [rootMaster, allControllers_con, deformerJoints]
