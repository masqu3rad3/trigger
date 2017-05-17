## Create splineIK

import pymel.core as pm

import extraProcedures as extra
reload(extra)

import mrCubic as mrC
reload(mrC)

def createSplineIK(refJoints, name, cuts, dropoff=2):
    #refJoints=pm.ls("jInit_spine*")

    scaleGrp=pm.group(name="scaleGrp_"+name, em=True)
    nonScaleGrp=pm.group(name="nonScaleGrp_"+name, em=True)

    #dropoff=2
    #cuts=6
    extra.getDistance(refJoints[0], refJoints[0])
    totalLength=0
    rootPoint=refJoints[0].getTranslation(space="world")
    #splitCount=5
    contDistances=[]
    contCurves=[]
    ctrlDistance=0

    for i in range (0, len(refJoints)):
        if i==0:
            tmin=0
        else:
            tmin=i-1
        currentJointLength=extra.getDistance(refJoints[i], refJoints[tmin])
        ctrlDistance=currentJointLength+ctrlDistance
        totalLength+=currentJointLength
        contDistances.append(ctrlDistance)

    rootVc=rootPoint
    endVc=(rootPoint.x, (rootPoint.y+totalLength), rootPoint.z)

    splitVc=endVc-rootVc
    segmentVc=(splitVc/(cuts))
    segmentLoc=rootVc+segmentVc
    curvePoints=[]
    defJoints=[]
    pm.select(d=True)

    ## Create deformation Joints
    for i in range (0, cuts+1):
        place=rootVc+(segmentVc*(i))
        j=pm.joint(p=place, name="jDef_"+name+str(i))
        pm.setAttr(j.displayLocalAxis, 1)
        defJoints.append(j)
        curvePoints.append(place)

    mrC.mrCube(defJoints)

    # ## Fix orientation of deformation joints
    # for i in defJoints:
    #     pm.joint(i, e=True, zso=True, oj="xyz")
        
        
    splineCurve=pm.curve(name="splineCurve_"+name, p=curvePoints)

    splineIK=pm.ikHandle(sol="ikSplineSolver", createCurve=False, c=splineCurve, sj=defJoints[0], ee=defJoints[len(defJoints)-1], w=1.0)

    ## Create controller Joints
    contJoints=[]
    pm.select(d=True)
    for i in range (0, len(contDistances)):
        ctrlVc=splitVc.normal()*contDistances[i]
        place=rootVc+(ctrlVc)
        j=pm.joint(p=place, name="jCont_spline_"+name+str(i), radius=5)
        contJoints.append(j)
        pm.select(d=True)
        
    pm.select(contJoints)
    pm.select(splineCurve, add=True)
    pm.skinCluster(dr=dropoff, tsb=True)

    for i in range (0, len(contJoints)):
        extra.alignTo(contJoints[i], refJoints[i],0)
        ## Create control Curves
        cont_Curve=pm.circle(name="cont_spline_"+name+str(i), nr=(0,1,0))
        scaleRatio=(totalLength/len(contJoints))
        pm.setAttr(cont_Curve[0].scale, (scaleRatio, scaleRatio, scaleRatio))
        pm.makeIdentity(cont_Curve[0], a=True, t=False, r=False, s=True)
        cont_Curve_ORE=extra.createUpGrp(cont_Curve[0],"ORE")
        extra.alignTo(cont_Curve_ORE, contJoints[i],2)
        pm.parentConstraint(cont_Curve[0], contJoints[i])
        contCurves.append(cont_Curve)

    pm.setAttr(splineIK[0].dTwistControlEnable, 1)
    pm.setAttr(splineIK[0].dWorldUpType, 4)
    pm.setAttr(splineIK[0].dForwardAxis, 2)
    pm.setAttr(splineIK[0].dWorldUpAxis, 3)
    pm.setAttr(splineIK[0].dWorldUpVector, (0,0,1))
    pm.setAttr(splineIK[0].dWorldUpVectorEnd, (0,0,1))

    contCurves[0][0].worldMatrix >> splineIK[0].dWorldUpMatrix
    contCurves[len(contCurves)-1][0].worldMatrix >> splineIK[0].dWorldUpMatrixEnd

    ## Create Stretch and Squash Nodes


    pm.addAttr(contCurves[0], shortName='preserveVol', longName='Preserve_Volume', defaultValue=0.0, minValue=0.0, maxValue=1.0, at="double", k=True)
    pm.addAttr(contCurves[0], shortName='volumeFactor', longName='Volume_Factor', defaultValue=1, at="double", k=True)

    pm.addAttr(contCurves[0], shortName='stretchy', longName='Stretchyness', defaultValue=1, minValue=0.0, maxValue=1.0, at="double", k=True)

    curveInfo=pm.arclen(splineCurve, ch=True)
    initialLength=pm.getAttr(curveInfo.arcLength)

    step=1
    powValue=0
    increase=0
    decrease=0
    for i in range (0, len(defJoints)):
        
        curveGlobMult=pm.createNode("multiplyDivide", name="curveGlobMult_"+name)
        pm.setAttr(curveGlobMult.operation,2)
        boneGlobMult=pm.createNode("multiplyDivide", name="boneGlobMult_"+name)
        
        lengthMult=pm.createNode("multiplyDivide", name="length_Multiplier_"+name)
        pm.setAttr(lengthMult.operation, 2)
        
        volumeSw=pm.createNode("blendColors", name="volumeSw_"+name)
        stretchSw=pm.createNode("blendTwoAttr", name="stretchSw_"+name)
        
        middlePoint=(len(defJoints)/2)
        volumePow=pm.createNode("multiplyDivide", name="volume_Power_"+name)
        volumeFactor=pm.createNode("multiplyDivide", name="volume_Factor_"+name)
        contCurves[0][0].volumeFactor >> volumeFactor.input1X
        contCurves[0][0].volumeFactor >> volumeFactor.input1Z
        volumeFactor.output >> volumePow.input2
        
        pm.setAttr(volumePow.operation, 3)
        if (i<middlePoint):
            pm.setAttr(volumeFactor.input2X, powValue )
            pm.setAttr(volumeFactor.input2Z, powValue)
            powValue=powValue-1
        else:
            pm.setAttr(volumeFactor.input2X, powValue)
            pm.setAttr(volumeFactor.input2Z, powValue)
            powValue=powValue+1
            
            
        curveInfo.arcLength >> curveGlobMult.input1X
        pm.setAttr(stretchSw.input[0],initialLength)
        curveGlobMult.outputX >> stretchSw.input[1]
        contCurves[0][0].stretchy >> stretchSw.attributesBlender
        
        scaleGrp.sx >> curveGlobMult.input2X
        stretchSw.output >> lengthMult.input1X
        pm.setAttr(lengthMult.input2X, initialLength)
        lengthMult.outputX >> boneGlobMult.input1Y
        
        
        
        lengthMult.outputX >> volumePow.input1X
        lengthMult.outputX >> volumePow.input1Z
        pm.setAttr(volumeSw.color2R, 1)
        pm.setAttr(volumeSw.color2B, 1)
        volumePow.outputX >>  volumeSw.color1R
        volumePow.outputX >>  volumeSw.color1B
        volumeSw.outputR >>  boneGlobMult.input1X
        volumeSw.outputB >>  boneGlobMult.input1Z
        scaleGrp.sx >> boneGlobMult.input2X
        scaleGrp.sx >> boneGlobMult.input2Y
        scaleGrp.sx >> boneGlobMult.input2Z
        contCurves[0][0].preserveVol >> volumeSw.blender
        
        boneGlobMult.output >> defJoints[i].scale
        
    ## grouping
    pm.parent(contJoints,scaleGrp)
    pm.parent(splineIK[0], nonScaleGrp)
    pm.parent(splineCurve, nonScaleGrp)
    pm.parent(defJoints[0], nonScaleGrp)
    
    ## return (ConnectionPointBottom, ConnectionPointUp, [Controllers], scaleGrp, nonScaleGrp)
    


