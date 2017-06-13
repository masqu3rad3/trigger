import pymel.core as pm
import collections
import extraProcedures as extra

reload(extra)
import contIcons as icon

reload(icon)

import createTwistSpline as tSpline

reload(tSpline)

class spine(object):
    # returnTuple = (
    #     scaleGrp, cont_body, cont_hips, cont_chest, gmRoot, jHeadPlug, jArmPlug_r_arm, jArmPlug_l_arm, nonScaleGrp)
    # scaleGrp = None
    # cont_body = None
    # cont_hips = None
    # cont_chest = None
    # gmRoot = None

    def createSpine(self, inits, suffix=""):
        idCounter = 0
        ## create an unique suffix
        while pm.objExists("scaleGrp_" + suffix):
            suffix = "%s%s" % (suffix, str(idCounter + 1))

        if (len(inits) < 2):
            pm.error("Insufficient Spine Initialization Joints")
            return

        # spineList = pm.ls("jInit_spine*")

        # initShouDis = extra.getDistance(pm.PyNode("jInit_Shoulder_l_arm"), pm.PyNode("jInit_Shoulder_r_arm"))
        # initLegsDis = extra.getDistance(pm.PyNode("jInit_HeelPv_l_leg"), pm.PyNode("jInit_HeelPv_r_leg"))
        # initUpBodyDis = extra.getDistance(spineList[len(spineList) / 2], spineList[len(spineList) - 1])
        # initLowBodyDis = extra.getDistance(spineList[0], spineList[len(spineList) / 2])

        rootPoint = inits[0]
        midPoint = inits[(len(inits)/2)-1]
        chestPoint = inits[len(inits)-1]
        # neckPoint = pm.PyNode("jInit_neck").getTranslation(space="world")
        # armPoint_r_arm = pm.PyNode("jInit_Shoulder_r_arm").getTranslation(space="world")
        # armPoint_l_arm = pm.PyNode("jInit_Shoulder_l_arm").getTranslation(space="world")

        # # Create Plug Joints
        # pm.select(None)
        # jChestPlug = pm.joint(name="jDef_ChestPlug", p=chestPoint)
        # pm.select(None)
        # jHeadPlug = pm.joint(name="jDef_HeadPlug", p=neckPoint)
        # pm.select(None)
        # jArmPlug_r_arm = pm.joint(name="jArmPlug_r_arm", p=armPoint_r_arm)
        # pm.select(None)
        # jArmPlug_l_arm = pm.joint(name="jArmPlug_l_arm", p=armPoint_l_arm)

        # parent upper plug joints
        # pm.parent(jArmPlug_l_arm, jArmPlug_r_arm, jHeadPlug, jChestPlug)

        pm.select(None)
        gmRoot = pm.joint(p=rootPoint, name="gmRoot", radius=10)
        contHipsScale = (initLegsDis / 1.5, initLegsDis / 1.5, initLegsDis / 1.5)
        cont_hips = icon.waist("cont_Hips", contHipsScale, location=rootPoint)
        contBodyScale = (initLegsDis * 0.75, initLegsDis * 0.75, initLegsDis * 0.75)
        cont_body = icon.square("cont_Body", contBodyScale, location=rootPoint)

        cont_chest = icon.cube("cont_Chest", (initShouDis, initUpBodyDis / 2, initUpBodyDis / 2),
                               location=(chestPoint + neckPoint) / 2)
        pm.xform(cont_chest, piv=chestPoint)

        spine = tSpline.createTspline(pm.ls("jInit_spine*"), "spine", 4, dropoff=2)
        splineIKCurves_ORE_List = spine[0]
        bottomConnection = spine[1]
        upConnection = spine[2]
        midConnection = spine[0][len(spine[0]) / 2]
        endPositionLock = spine[3]
        scaleGrp = spine[4]
        nonScaleGrp = spine[5]
        passCont = spine[6]
        defJoints = spine[7]
        noTouchListofLists = spine[8]

        # # connect the spine root to the master root
        pm.parentConstraint(gmRoot, bottomConnection, mo=True)
        # # connect the spine end
        pm.parentConstraint(cont_chest, upConnection, mo=True)
        # # connect the master root to the hips controller
        pm.parentConstraint(cont_hips, gmRoot, mo=True)

        # # connect upper plug points to the spine and orient it to the chest controller
        pm.pointConstraint(endPositionLock, jChestPlug)
        pm.orientConstraint(cont_chest, jChestPlug)

        # # pass Stretch controls from the splineIK to neck controller
        extra.attrPass(passCont, cont_chest)

        ## create locators on the mid controller to be used as alignment
        midSpineLocA = pm.spaceLocator(name="midSpineLocA", p=midPoint)
        midSpineLocB = pm.spaceLocator(name="midSpineLocB", p=midPoint)

        pm.parentConstraint(midSpineLocA, midSpineLocB, midConnection, mo=True)

        contSpineFKAScale = (initLegsDis / 2, initLegsDis / 2, initLegsDis / 2)
        cont_spineFK_A_01 = icon.circle("cont_SpineFK_A01", contSpineFKAScale, location=rootPoint)
        cont_spineFK_A_02 = icon.circle("cont_SpineFK_A02", contSpineFKAScale, location=midPoint)
        cont_spineFK_A_03 = icon.circle("cont_SpineFK_A03", contSpineFKAScale, location=chestPoint)

        contSpineFKBScale = (initLegsDis / 2.5, initLegsDis / 2.5, initLegsDis / 2.5)
        cont_spineFK_B_01 = icon.ngon("cont_SpineFK_B01", contSpineFKBScale, location=rootPoint)
        cont_spineFK_B_02 = icon.ngon("cont_SpineFK_B02", contSpineFKBScale, location=midPoint)
        cont_spineFK_B_03 = icon.ngon("cont_SpineFK_B03", contSpineFKBScale, location=chestPoint)

        # good parenting
        pm.parent(midSpineLocA, cont_chest)
        pm.parent(cont_chest, cont_spineFK_A_03)
        pm.parent(cont_spineFK_A_03, cont_spineFK_A_02)
        pm.parent(cont_spineFK_A_02, cont_spineFK_A_01)
        pm.parent(cont_spineFK_A_01, cont_body)
        pm.parent(spine[0], scaleGrp)  # contcurve Ore s -> scaleGrp
        pm.parent(jChestPlug, scaleGrp)

        pm.parent(midSpineLocB, cont_hips)
        pm.parent(cont_hips, cont_spineFK_B_01)
        pm.parent(cont_spineFK_B_01, cont_spineFK_B_02)
        pm.parent(cont_spineFK_B_02, cont_spineFK_B_03)
        pm.parent(cont_spineFK_B_03, cont_body)
        pm.parent(endPositionLock, scaleGrp)

        ## CONNECT RIG VISIBILITES

        # create visibility attributes for cont_Body

        pm.addAttr(cont_body, at="bool", ln="FK_A_Visibility", sn="fkAvis", defaultValue=True)
        pm.addAttr(cont_body, at="bool", ln="FK_B_Visibility", sn="fkBvis", defaultValue=True)
        pm.addAttr(cont_body, at="bool", ln="Tweaks_Visibility", sn="tweakVis", defaultValue=True)
        # make the created attributes visible in the channelbox
        pm.setAttr(cont_body.fkAvis, cb=True)
        pm.setAttr(cont_body.fkBvis, cb=True)
        pm.setAttr(cont_body.tweakVis, cb=True)

        fkContsA = (cont_spineFK_A_01.getShape(), cont_spineFK_A_02.getShape(), cont_spineFK_A_03.getShape())
        fkContsB = (cont_spineFK_B_01.getShape(), cont_spineFK_B_02.getShape(), cont_spineFK_B_03.getShape())

        for i in fkContsA:
            cont_body.fkAvis >> i.visibility
        for i in fkContsB:
            cont_body.fkBvis >> i.visibility

        for i in range(0, len(splineIKCurves_ORE_List)):
            if i != 0 or i != len(splineIKCurves_ORE_List):
                node = extra.createUpGrp(splineIKCurves_ORE_List[i], "OFF")
                cont_body.tweakVis >> node.v

        # global visibilities attributes

        pm.addAttr(scaleGrp, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True)
        pm.addAttr(scaleGrp, at="bool", ln="Joints_Visibility", sn="jointVis", defaultValue=True)
        pm.addAttr(scaleGrp, at="bool", ln="Rig_Visibility", sn="rigVis", defaultValue=False)
        # make the created attributes visible in the channelbox
        pm.setAttr(scaleGrp.contVis, cb=True)
        pm.setAttr(scaleGrp.jointVis, cb=True)
        pm.setAttr(scaleGrp.rigVis, cb=True)

        # global cont visibilities

        for i in range(0, len(splineIKCurves_ORE_List)):
            if i != 0 or i != len(splineIKCurves_ORE_List):
                scaleGrp.contVis >> splineIKCurves_ORE_List[i].v
        scaleGrp.contVis >> cont_body.v

        # global joint visibilities

        for i in defJoints:
            scaleGrp.jointVis >> i.v
        scaleGrp.jointVis >> jChestPlug.v
        scaleGrp.jointVis >> jHeadPlug.v

        # global rig visibilities

        scaleGrp.rigVis >> splineIKCurves_ORE_List[0].v
        scaleGrp.rigVis >> splineIKCurves_ORE_List[len(splineIKCurves_ORE_List) - 1].v

        scaleGrp.rigVis >> midSpineLocA.v
        scaleGrp.rigVis >> midSpineLocB.v

        scaleGrp.rigVis >> gmRoot.v

        # scaleGrp.rigVis >> jChestPlug.v
        scaleGrp.rigVis >> jArmPlug_l_arm.v
        scaleGrp.rigVis >> jArmPlug_r_arm.v
        # scaleGrp.rigVis >> jHeadPlug.v

        for lst in noTouchListofLists:
            for i in lst:
                scaleGrp.rigVis >> i.v

        ## FOOL PROOFING

        extra.lockAndHide(cont_body, "v")
        extra.lockAndHide(cont_hips, ["sx", "sy", "sz", "v"])
        extra.lockAndHide(cont_chest, ["sx", "sy", "sz", "v"])
        extra.lockAndHide(cont_spineFK_A_01, ["tx", "ty", "tz", "sx", "sy", "sz", "v"])
        extra.lockAndHide(cont_spineFK_A_02, ["tx", "ty", "tz", "sx", "sy", "sz", "v"])
        extra.lockAndHide(cont_spineFK_A_03, ["tx", "ty", "tz", "sx", "sy", "sz", "v"])
        extra.lockAndHide(cont_spineFK_B_01, ["tx", "ty", "tz", "sx", "sy", "sz", "v"])
        extra.lockAndHide(cont_spineFK_B_02, ["tx", "ty", "tz", "sx", "sy", "sz", "v"])
        extra.lockAndHide(cont_spineFK_B_03, ["tx", "ty", "tz", "sx", "sy", "sz", "v"])

        ## COLOR CODING

        index = 17
        indexIK = 20
        indexFKA = 30
        indexFKB = 31
        extra.colorize(cont_body, index)
        extra.colorize(cont_chest, index)
        extra.colorize(cont_hips, index)
        extra.colorize(cont_spineFK_A_01, indexFKA)
        extra.colorize(cont_spineFK_A_02, indexFKA)
        extra.colorize(cont_spineFK_A_03, indexFKA)
        extra.colorize(cont_spineFK_B_01, indexFKB)
        extra.colorize(cont_spineFK_B_02, indexFKB)
        extra.colorize(cont_spineFK_B_03, indexFKB)

        # return (scaleGrp, cont_chest, master Root, head plug, rightArmPlug, leftArmPlug, nonScaleGrp)
        returnTuple = (
        scaleGrp, cont_body, cont_hips, cont_chest, gmRoot, jHeadPlug, jArmPlug_r_arm, jArmPlug_l_arm, nonScaleGrp)
        return returnTuple
