import pymel.core as pm
import collections
import extraProcedures as extra

reload(extra)
import contIcons as icon

reload(icon)

import twistSplineClass as twistSpline

reload(twistSpline)

class spine(object):
    # returnTuple = (
    #     scaleGrp, cont_body, cont_hips, cont_chest, gmRoot, jHeadPlug, jArmPlug_r_arm, jArmPlug_l_arm, nonScaleGrp)
    scaleGrp = None
    cont_body = None
    cont_hips = None
    cont_chest = None
    gmRoot = None
    nonScaleGrp = None

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
        print inits
        iconSize = extra.getDistance(inits[0], inits[len(inits)-1])

        rootPoint = inits[0].getTranslation(space="world")
        midPoint = inits[(len(inits)/2)].getTranslation(space="world")
        chestPoint = inits[len(inits)-1].getTranslation(space="world")
        # neckPoint = pm.PyNode("jInit_neck").getTranslation(space="world")
        # armPoint_r_arm = pm.PyNode("jInit_Shoulder_r_arm").getTranslation(space="world")
        # armPoint_l_arm = pm.PyNode("jInit_Shoulder_l_arm").getTranslation(space="world")

        # # Create Plug Joints
        pm.select(None)
        jChestPlug = pm.joint(name="jDef_ChestPlug", p=chestPoint)
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
        contHipsScale = (iconSize / 1.5, iconSize / 1.5, iconSize / 1.5)
        cont_hips = icon.waist("cont_Hips", contHipsScale, location=rootPoint)
        contBodyScale = (iconSize * 0.75, iconSize * 0.75, iconSize * 0.75)
        cont_body = icon.square("cont_Body", contBodyScale, location=rootPoint)

        cont_chest = icon.cube("cont_Chest", (iconSize*0.5, iconSize*0.5, iconSize*0.5))
        # move the pivot to its base
        pm.xform(cont_chest, piv=(0,-iconSize/2,0))
        pm.move(cont_chest, chestPoint, rpr=True)
        # pm.setAttr(cont_chest.translate, chestPoint)
        #extra.alignTo(cont_chest, inits[len(inits)-1])

        # spine = tSpline.createTspline(pm.ls("jInit_spine*"), "spine", 4, dropoff=2)
        spine = twistSpline.twistSpline()
        spine.createTspline(inits, "spine" + suffix, 4, dropoff=2)

        midConnection = spine.contCurves_ORE[(len(spine.contCurves_ORE)/2)]


        self.nonScaleGrp = spine.nonScaleGrp

        # # connect the spine root to the master root
        pm.parentConstraint(gmRoot, spine.contCurve_Start, mo=True)
        # # connect the spine end
        pm.parentConstraint(cont_chest, spine.contCurve_End, mo=True)
        # # connect the master root to the hips controller
        pm.parentConstraint(cont_hips, gmRoot, mo=True)

        # # connect upper plug points to the spine and orient it to the chest controller
        pm.pointConstraint(spine.endLock, jChestPlug)
        pm.orientConstraint(cont_chest, jChestPlug)

        # # pass Stretch controls from the splineIK to neck controller
        extra.attrPass(spine.attPassCont, cont_chest)

        ## create locators on the mid controller to be used as alignment
        midSpineLocA = pm.spaceLocator(name="midSpineLocA", p=midPoint)
        midSpineLocB = pm.spaceLocator(name="midSpineLocB", p=midPoint)

        pm.parentConstraint(midSpineLocA, midSpineLocB, midConnection, mo=True)

        contSpineFKAScale = (iconSize / 2, iconSize / 2, iconSize / 2)
        cont_spineFK_A_01 = icon.circle("cont_SpineFK_A01", contSpineFKAScale, location=rootPoint)
        cont_spineFK_A_02 = icon.circle("cont_SpineFK_A02", contSpineFKAScale, location=midPoint)
        cont_spineFK_A_03 = icon.circle("cont_SpineFK_A03", contSpineFKAScale, location=chestPoint)

        contSpineFKBScale = (iconSize / 2.5, iconSize / 2.5, iconSize / 2.5)
        cont_spineFK_B_01 = icon.ngon("cont_SpineFK_B01", contSpineFKBScale, location=rootPoint)
        cont_spineFK_B_02 = icon.ngon("cont_SpineFK_B02", contSpineFKBScale, location=midPoint)
        cont_spineFK_B_03 = icon.ngon("cont_SpineFK_B03", contSpineFKBScale, location=chestPoint)

        # good parenting
        pm.parent(midSpineLocA, cont_chest)
        pm.parent(cont_chest, cont_spineFK_A_03)
        pm.parent(cont_spineFK_A_03, cont_spineFK_A_02)
        pm.parent(cont_spineFK_A_02, cont_spineFK_A_01)
        pm.parent(cont_spineFK_A_01, cont_body)
        pm.parent(spine.contCurves_ORE, spine.scaleGrp)  # contcurve Ore s -> scaleGrp
        pm.parent(jChestPlug, spine.scaleGrp)

        pm.parent(midSpineLocB, cont_hips)
        pm.parent(cont_hips, cont_spineFK_B_01)
        pm.parent(cont_spineFK_B_01, cont_spineFK_B_02)
        pm.parent(cont_spineFK_B_02, cont_spineFK_B_03)
        pm.parent(cont_spineFK_B_03, cont_body)
        pm.parent(spine.endLock, spine.scaleGrp)

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

        for i in range(0, len(spine.contCurves_ORE)):
            if i != 0 or i != len(spine.contCurves_ORE):
                node = extra.createUpGrp(spine.contCurves_ORE[i], "OFF")
                cont_body.tweakVis >> node.v

        # global visibilities attributes

        pm.addAttr(spine.scaleGrp, at="bool", ln="Control_Visibility", sn="contVis", defaultValue=True)
        pm.addAttr(spine.scaleGrp, at="bool", ln="Joints_Visibility", sn="jointVis", defaultValue=True)
        pm.addAttr(spine.scaleGrp, at="bool", ln="Rig_Visibility", sn="rigVis", defaultValue=False)
        # make the created attributes visible in the channelbox
        pm.setAttr(spine.scaleGrp.contVis, cb=True)
        pm.setAttr(spine.scaleGrp.jointVis, cb=True)
        pm.setAttr(spine.scaleGrp.rigVis, cb=True)

        # global cont visibilities

        for i in range(0, len(spine.contCurves_ORE)):
            if i != 0 or i != len(spine.contCurves_ORE):
                spine.scaleGrp.contVis >> spine.contCurves_ORE[i].v
        spine.scaleGrp.contVis >> cont_body.v

        # global joint visibilities

        for i in spine.defJoints:
            spine.scaleGrp.jointVis >> i.v
        spine.scaleGrp.jointVis >> jChestPlug.v
        # spine.scaleGrp.jointVis >> jHeadPlug.v

        # global rig visibilities

        spine.scaleGrp.rigVis >> spine.contCurves_ORE[0].v
        spine.scaleGrp.rigVis >> spine.contCurves_ORE[len(spine.contCurves_ORE) - 1].v

        spine.scaleGrp.rigVis >> midSpineLocA.v
        spine.scaleGrp.rigVis >> midSpineLocB.v

        spine.scaleGrp.rigVis >> gmRoot.v

        # scaleGrp.rigVis >> jChestPlug.v
        # spine.scaleGrp.rigVis >> jArmPlug_l_arm.v
        # spine.scaleGrp.rigVis >> jArmPlug_r_arm.v
        # scaleGrp.rigVis >> jHeadPlug.v

        for lst in spine.noTouchData:
            for i in lst:
                spine.scaleGrp.rigVis >> i.v

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

        self.scaleGrp = spine.scaleGrp
        # return (scaleGrp, cont_chest, master Root, head plug, rightArmPlug, leftArmPlug, nonScaleGrp)
        # returnTuple = (
        # scaleGrp, cont_body, cont_hips, cont_chest, gmRoot, jHeadPlug, jArmPlug_r_arm, jArmPlug_l_arm, nonScaleGrp)
        # return returnTuple
