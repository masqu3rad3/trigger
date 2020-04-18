


import maya.cmds as cmds
# import maya.OpenMaya as om
# USING MAYA API 2.0
import maya.api.OpenMaya as om

def getMDagPath(node):
    selList = om.MSelectionList()
    selList.add(node)
    return selList.getDagPath(0)

def getWorldTranslation(node):
    """Returns given nodes world translation of rotate pivot"""
    targetMTransform = om.MFnTransform(getMDagPath(node))
    targetRotatePivot = om.MVector(targetMTransform.rotatePivot(om.MSpace.kWorld))
    return targetRotatePivot

def getDistance(node1, node2):
    """Returns the distance between two nodes"""
    Ax, Ay, Az = getWorldTranslation(node1)
    Bx, By, Bz = getWorldTranslation(node2)
    return ((Ax-Bx)**2 + (Ay-By)**2 + (Az-Bz)**2)**0.5

# def getDistance( node1, node2):
#     """
#     Calculates the distance between Node 1 and Node 2
#     Args:
#         node1: Node 1. Must be a transform node
#         node2: Node 2. Must be a transform node
#
#     Returns: Distance value.
#
#     """
#     Ax, Ay, Az = node1.getTranslation(space="world")
#     Bx, By, Bz = node2.getTranslation(space="world")
#     return ((Ax-Bx)**2 + (Ay-By)**2 + (Az-Bz)**2)**0.5

def alignTo(node, target, position=True, rotation=False):
    """
    This is the fastest align method. May not work in all cases
    http://www.rihamtoulan.com/blog/2017/12/21/matching-transformation-in-maya-and-mfntransform-pitfalls
    """
    nodeMTransform = om.MFnTransform(getMDagPath(node))
    targetMTransform = om.MFnTransform(getMDagPath(target))
    if position:
        targetRotatePivot = om.MVector(targetMTransform.rotatePivot(om.MSpace.kWorld))
        nodeMTransform.setTranslation(targetRotatePivot, om.MSpace.kWorld)
    if rotation:
        targetMTMatrix = om.MTransformationMatrix(om.MMatrix(cmds.xform(target, matrix=True, ws=1, q=True)))
        # using the target matrix decomposition
        # Worked on all cases tested
        nodeMTransform.setRotation(targetMTMatrix.rotation(True), om.MSpace.kWorld)

# def alignTo(node, target, position=True, rotation=False):
#
#     if rotation and position:
#         targetMatrix = cmds.xform(target, query=True, worldSpace=True, matrix=True)
#         cmds.xform(node, worldSpace=True, matrix=targetMatrix)
#         return
#     if position:
#         targetTranslation = cmds.xform(target, query=True, worldSpace=True, translation=True)
#         cmds.xform(node, worldSpace=True, translation =targetTranslation)
#     if rotation:
#         targetRotation = pm.xform(target, query=True, worldSpace=True, rotation=True)
#         cmds.xform(node, worldSpace=True, rotation = targetRotation)



# def alignTo(sourceObj=None, targetObj=None, mode=0, sl=False, o=(0,0,0)):
#     offset=dt.Vector(o)
#     if sl == True:
#         selection = pm.ls(sl=True)
#         if not len(selection) == 2:
#             pm.error("select exactly 2 objects")
#             return
#         sourceObj = selection[0]
#         targetObj = selection[1]
#     if not sourceObj or not targetObj:
#         pm.error("No source and/or target object defined")
#         return
#     if mode == 0:
#
#         targetTranslation = pm.xform(targetObj, query=True, worldSpace=True, translation=True)
#         pm.xform(sourceObj, worldSpace=True, translation =targetTranslation)
#     if mode == 1:
#         targetRotation = pm.xform(targetObj, query=True, worldSpace=True, rotation=True)
#         pm.xform(sourceObj, worldSpace=True, rotation =targetRotation+offset)
#     if mode == 2:
#         targetMatrix = pm.xform(targetObj, query=True, worldSpace=True, matrix=True)
#         pm.xform(sourceObj, worldSpace=True, matrix=targetMatrix)



def alignToAlter(node1, node2, mode=0, o=(0,0,0)):
    """
    Aligns the first node to the second.
    Args:
        node1: Node to be aligned.
        node2: Target Node.
        mode: Specifies the alignment Mode. Valid Values: 0=position only, 1=Rotation Only, 2=Position and Rotation
        o: Offset Value. Default: (0,0,0)

    Returns:None

    """
    if mode==0:
        ##Position Only
        cmds.delete(cmds.pointConstraint(node2, node1, mo=False))

    elif mode==1:
        ##Rotation Only
        cmds.delete(cmds.orientConstraint(node2, node1, o=o, mo=False))
    elif mode==2:
        ##Position and Rotation
        cmds.delete(cmds.parentConstraint(node2, node1, mo=False))

def alignAndAim(node, targetList, aimTargetList, upObject=None, upVector=None, localUp=(0.0,1.0,0.0), rotateOff=None, translateOff=None, freezeTransform=False):
    """
    Aligns the position of the node to the target and rotation to the aimTarget object.
    Args:
        node: Node to be aligned
        targetList: (List) Target nodes for positioning
        aimTargetList: (List) Target nodes for aiming
        upObject: (Optional) if defined the up node will be up axis of this object
        rotateOff: (Optional) rotation offset with given value (tuple)
        translateOff: (Optional) translate offset with given value (tuple)
        freezeTransform: (Optional) if set True, freezes transforms of the node at the end

    Returns:
        None

    """
    if upObject and upVector:
        cmds.error("In alignAndAim function both upObject and upVector parameters cannot be used")
        return

    pointFlags = ""
    for i in range (len(targetList)):
        if not i == 0:
            pointFlags = "%s, " % pointFlags
        pointFlags = "{0}targetList[{1}]".format(pointFlags, str(i))
    pointFlags = "%s, node" % pointFlags
    pointCommand = "cmds.pointConstraint({0})".format(pointFlags)
    tempPo = eval(pointCommand)

    aimFlags = ""
    for i in range (len(aimTargetList)):
        if not i == 0:
            aimFlags = "%s, " % aimFlags
        aimFlags = "{0}aimTargetList[{1}]".format(aimFlags, str(i))
    aimFlags = "%s, node" % aimFlags
    aimFlags = "%s, u=%s" % (aimFlags, localUp)
    if upObject:
        aimFlags = "%s, wuo=upObject, wut='object'" % aimFlags
    if upVector:
        aimFlags = "%s, wu=upVector, wut='vector'" % aimFlags

    aimCommand = "cmds.aimConstraint({0})".format(aimFlags)
    tempAim = eval(aimCommand)

    cmds.delete(tempPo)
    cmds.delete(tempAim)
    if translateOff:
        cmds.move(translateOff[0], translateOff[1], translateOff[2], node, r=True)
    if rotateOff:
        cmds.rotate(rotateOff[0], rotateOff[1], rotateOff[2], node, r=True, os=True)
    if freezeTransform:
        cmds.makeIdentity(node, a=True, t=True)

def alignBetween (node, targetA, targetB, position=True, aim_b=True, orientation=False, o=(0,0,0)):
    """
    Alignes the node between target A and target B
    Args:
        node(String): Node to be aligned
        targetA(String): Target A
        targetB(String): Target B
        position(bool): If True, aligns the position between targets. Default True
        aim_b(bool): If True, node aims to the targetB
        orientation(bool): If true orients between targetA and targetB
        o(tuple): orientation offset vector


    Returns: None

    """
    if position:
        cmds.delete(cmds.pointConstraint(targetA, targetB, node, mo=False))
    if aim_b:
        cmds.delete(cmds.aimConstraint(targetB,node, mo=False, o=o))
    if orientation:
        cmds.delete(cmds.orientConstraint(targetA, targetB, node, mo=False, o=o))

# def getBetweenVector(node, targetPointNodeList):
#     # get center vector
#     nodePos = node.getTranslation(space="world")
#     sumVectors = dt.Vector(0,0,0)
#     for p in targetPointNodeList:
#         pVector = p.getTranslation(space="world")
#         addVector = dt.Vector(dt.Vector(nodePos) - dt.Vector(pVector)).normal()
#         sumVectors = sumVectors + addVector
#     return sumVectors.normal()


def getBetweenVector(node, targetPointNodeList):
    nodePos = getWorldTranslation(node)
    sumVectors = om.MVector(0,0,0)
    for point in targetPointNodeList:
        pVector = getWorldTranslation(point)
        addVector = om.MVector(om.MVector(nodePos)-om.MVector(pVector)).normal()
        sumVectors += addVector
    return sumVectors.normal()


def createUpGrp(node, suffix, freezeTransform=True):
    """
    Creates an Upper Group for the given object.
    Args:
        node: (Pymel Object) Source Object
        suffix: (String) Suffix for the group. String.
        mi: (Boolean) Stands for "makeIdentity" If True, freezes the transformations of the new group. Default is True

    Returns: The created group node

    """
    grpName = "%s_%s" % (node, suffix)
    newGrp = cmds.group(em=True, name=grpName)

    #align the new created empty group to the selected object

    alignTo(newGrp, node, position=True, rotation=True)

    #check if the target object has a parent
    originalParent = cmds.listRelatives(node, p=True)
    if originalParent:
        cmds.parent(newGrp, originalParent[0], r=False)
        if freezeTransform:
            cmds.makeIdentity(newGrp, a=True)

    cmds.parent(node,newGrp)
    return newGrp


## example use: connectMirror(obj1, obj2, "X")
def connectMirror (node1, node2, mirrorAxis="X"):
    """
    Make a mirrored connection between node1 and node2 along the mirrorAxis
    Args:
        node1: Driver Node
        node2: Driven Node
        mirrorAxis: Mirror axis for the driven node.

    Returns: None

    """
    ## make sure the axis is uppercase:
    mirrorAxis = mirrorAxis.upper()
    ## strip - and +
    mirrorAxis = mirrorAxis.replace("+", "")
    mirrorAxis = mirrorAxis.replace("-", "")

    #nodes Translate
    rvsNodeT=cmds.createNode("reverse")
    minusOpT=cmds.createNode("plusMinusAverage")
    cmds.setAttr("%s.operation" %minusOpT, 2)
    cmds.connectAttr("{0}.translate".format(node1), "{0}.input".format(rvsNodeT))
    cmds.connectAttr("{0}.output".format(rvsNodeT), "{0}.input3D[0]".format(minusOpT))
    cmds.setAttr("%s.input3D[1]" %minusOpT, 1, 1, 1)
    #nodes Rotate
    rvsNodeR = cmds.createNode("reverse")
    minusOpR = cmds.createNode("plusMinusAverage")
    cmds.setAttr("%s.operation" %minusOpR, 2)
    cmds.connectAttr("{0}.rotate".format(node1), "{0}.input".format(rvsNodeR))

    # rvsNodeR.output >> minusOpR.input3D[0]
    cmds.connectAttr("{0}.output".format(rvsNodeR), "{0}.input3D[0]".format(minusOpR))

    cmds.setAttr("%s.input3D[1]" %minusOpR, 1, 1, 1)

    #Translate

    if (mirrorAxis=="X"):
        cmds.connectAttr("{0}.output3Dx".format(minusOpT), "{0}.tx".format(node2))
        cmds.connectAttr("{0}.ty".format(node1), "{0}.ty".format(node2))
        cmds.connectAttr("{0}.tz".format(node1), "{0}.tz".format(node2))
        cmds.connectAttr("{0}.rx".format(node1), "{0}.rx".format(node2))
        cmds.connectAttr("{0}.output3Dy".format(minusOpR), "{0}.ry".format(node2))
        cmds.connectAttr("{0}.output3Dz".format(minusOpR), "{0}.rz".format(node2))

    if (mirrorAxis=="Y"):
        cmds.connectAttr("{0}.tx".format(node1), "{0}.tx".format(node2))
        cmds.connectAttr("{0}.output3Dy".format(minusOpT), "{0}.ty".format(node2))
        cmds.connectAttr("{0}.tz".format(node1), "{0}.tz".format(node2))
        cmds.connectAttr("{0}.output3Dx".format(minusOpR), "{0}.rx".format(node2))
        cmds.connectAttr("{0}.ry".format(node1), "{0}.ry".format(node2))
        cmds.connectAttr("{0}.output3Dz".format(minusOpR), "{0}.rz".format(node2))

    if (mirrorAxis=="Z"):
        cmds.connectAttr("{0}.tx".format(node1), "{0}.tx".format(node2))
        cmds.connectAttr("{0}.ty".format(node1), "{0}.ty".format(node2))
        cmds.connectAttr("{0}.output3Dz".format(minusOpT), "{0}.tz".format(node2))
        cmds.connectAttr("{0}.rx".format(node1), "{0}.rx".format(node2))
        cmds.connectAttr("{0}.output3Dy".format(minusOpR), "{0}.ry".format(node2))
        cmds.connectAttr("{0}.output3Dz".format(minusOpR), "{0}.rz".format(node2))

def colorize (node_list, index, shape=True):
    """
    Changes the wire color of the node to the index
    Args:
        node_list: Node
        index: Index Number

    Returns:None

    """
    if not isinstance(node_list, list):
        node_list=[node_list]
    for node in node_list:
        if isinstance(index, int):
            pass
        elif isinstance(index, str):
            sidesDict={"L":6, "R":13, "C":17, "RMIN":9, "LMIN":18, "CMIN":20}
            if index.upper() in sidesDict.keys():
                index = sidesDict[index.upper()]
            else:
                cmds.error("Colorize error... Unknown index command")
                return
        else:
            cmds.error("Colorize error... Index flag must be integer or string('L', 'R', 'C')")
            return
        #shape=node.getShape()
        if shape:
            shapes=cmds.listRelatives(node, s=True)
            shapes = [] if shapes == None else shapes
            for shape in shapes:
                cmds.setAttr("{0}.overrideEnabled".format(shape), True)
                cmds.setAttr("{0}.overrideColor".format(shape), index)
        else:
            for shape in node_list:
                cmds.setAttr("{0}.overrideEnabled".format(shape), True)
                cmds.setAttr("{0}.overrideColor".format(shape), index)

def lockAndHide (node, channelArray, hide=True):
    """
    Locks and hides the channels specified in the channelArray.
    Args:
        node: Node
        channelArray: Must be list value containing the channels as string values. eg: ["sx", "sy", "sz"] or ["translateX", "rotateX", "sz"]

    Returns: None

    """
    ## // TODO OPTIMIZE HERE (map function?)
    for i in channelArray:
        attribute=("%s.%s" %(node, i))
        cmds.setAttr(attribute, lock=True, keyable=not hide, channelBox=not hide)

# def alignJoints (sourceJoint, targetJoints):
#     tempLocs
#     flags = ""
#     for i in targetJoints:
#         temp
#         flags = "{0}, {1}".format(flags, i)
#
#     flags = "{0}, {1}".format(flags, sourceJoint)
#
#     command = "pm.orientConstraint({0}, mo=False)".foramt(flags)
#     eval(command)

def attrPass (sourceNode, targetNode, attributes=[], inConnections=True, outConnections=True, keepSourceAttributes=False, values=True, daisyChain=False, overrideEx=False):
    """
    Copies the attributes from source node to the target node.
    Args:
        sourceNode: (Unicode) Source Object which the attributes will be copied from
        targetNode: (Unicode) Target Object which the attributes will be copied onto.
        attributes: (List of Strings) Optional. If left blank, all user defined custom attributes will be copied. Accepts String list.
        inConnections: (Bool) whether the incoming connections will be copied or not. Default is True. daisyChain overrides this argument.
        outConnections: (Bool) whether the incoming connections will be copied or not. Default is True. If True, the present out connections of source object will be lost.
        keepSourceAttributes: (Bool) If False the copied attributes will be deleted from the source node. Default is False
        values: (Bool) If True the values of the attributes will be copied as well
        daisyChain: (Bool) If true, instead of copyAttr command, it connects the source attributes to the target attributes. Non-destructive. Overrides inConnections and outConnections.
        overrideExisting: (Bool) When this flas set to True, if an Attribute on the target node with the same name exists, it gets deleted and created again to ensure it has the same properties.
    Returns: None

    """

    # get the user defined attributes:
    if len(attributes)==0:
        userAttr = cmds.listAttr(sourceNode, ud=True)
    else:
        userAttr = attributes

    if not userAttr:
        return

    for attr in userAttr:
        flagBuildList=[]
        atType = cmds.getAttr("%s.%s" % (sourceNode,attr), type=True)
        atTypeFlag = "at='%s'" % (str(atType))
        flagBuildList.append(atTypeFlag)

        if cmds.attributeQuery(attr, node=sourceNode, enum=True)==True:
            enumList=cmds.attributeQuery(attr, node=sourceNode, listEnum=True)
            enumListFlag="en='%s'" % str(enumList[0])
            flagBuildList.append(enumListFlag)

        hiddenState = cmds.attributeQuery(attr, node=sourceNode, hidden=True)
        hiddenStateFlag = "h=%s" % (str(hiddenState))
        flagBuildList.append(hiddenStateFlag)

        keyableState = cmds.attributeQuery(attr, node=sourceNode, keyable=True)
        keyableStateFlag = "k=%s" % (str(keyableState))
        flagBuildList.append(keyableStateFlag)

        longName = cmds.attributeQuery(attr, node=sourceNode, longName=True)
        longNameFlag = "ln='%s'" % str(longName)
        flagBuildList.append(longNameFlag)

        if cmds.attributeQuery(attr, node=sourceNode, maxExists=True) == True:
            hardMax=cmds.attributeQuery(attr, node=sourceNode, maximum =True)
            hardMaxFlag = "max=%s" % (str(hardMax[0]))
            flagBuildList.append(hardMaxFlag)

        if cmds.attributeQuery(attr, node=sourceNode, minExists=True) == True:
            hardMin = cmds.attributeQuery(attr, node=sourceNode, minimum=True)
            hardMinFlag = "min=%s" % (str(hardMin[0]))
            flagBuildList.append(hardMinFlag)

        readState = cmds.attributeQuery(attr, node=sourceNode, readable=True)
        readStateFlag = "r=%s" % (readState)
        flagBuildList.append(readStateFlag)

        shortName = cmds.attributeQuery(attr, node=sourceNode, shortName=True)
        shortNameFlag = "sn='%s'" % str(shortName)
        flagBuildList.append(shortNameFlag)

        if cmds.attributeQuery(attr, node=sourceNode, softMaxExists=True) == True:
            softMax = cmds.attributeQuery(attr, node=sourceNode, softMax =True)
            softMaxFlag = "smx=%s" % (str(softMax[0]))
            flagBuildList.append(softMaxFlag)

        if cmds.attributeQuery(attr, node=sourceNode, softMinExists=True) == True:
            softMin = cmds.attributeQuery(attr, node=sourceNode, softMin =True)
            softMinFlag = "smn=%s" % (str(softMin[0]))
            flagBuildList.append(softMinFlag)

        writeState = cmds.attributeQuery(attr, node=sourceNode, writable=True)
        writeStateFlag = "w=%s" % (writeState)
        flagBuildList.append(writeStateFlag)


        # parse the flagBuildList into single string
        addAttribute = "cmds.addAttr('%s', " % (targetNode)
        for i in range (0,len(flagBuildList)):

            # addAttribute+=flagBuildList[i]
            addAttribute = "%s%s" % (addAttribute, flagBuildList[i])
            if i < len(flagBuildList)-1:
                addAttribute = "%s, " % addAttribute
            else:
                addAttribute = "%s)" % addAttribute


        # if an attribute with the same name exists
        if cmds.attributeQuery(attr, node=targetNode, exists=True):
            if overrideEx:
                cmds.deleteAttr("%s.%s" % (targetNode, attr))
                exec (addAttribute)
            else:
                continue
        else:

            exec(addAttribute)

    if daisyChain==True:
        # create connections between old and new attributes
        for i in range (0, len(userAttr)):
            if values==True:
                # get value
                value = cmds.getAttr("%s.%s" % (sourceNode, userAttr[i]))
                # set Value
                cmds.setAttr("%s.%s" % (targetNode, userAttr[i]), value)
            cmds.connectAttr("{0}.{1}".format(targetNode, userAttr[i]), "{0}.{1}".format(sourceNode, userAttr[i]))
            # pm.PyNode("%s.%s" % (targetNode, userAttr[i])) >> pm.PyNode("%s.%s" % (sourceNode, userAttr[i]))
    else:
        cmds.copyAttr(sourceNode, targetNode, inConnections=inConnections, outConnections=outConnections, values=values, attribute=userAttr)
        if keepSourceAttributes==False:
            for i in userAttr:
                cmds.deleteAttr("%s.%s" % (sourceNode,i))

# def spaceSwitcher (node, targetList, overrideExisting=False, mode="parent", defaultVal=1, listException = None):
#     """
#     Creates the space switch attributes between selected node (controller) and targets.
#     Args:
#         node: (single object) Object which anchor space will be switched. Mostly a controller curve.
#         targetList: (list of objects) The node will be anchored between these targets.
#         overrideExisting: (bool) If True, the existing attributes on the node with the same name will be deleted and recreated. Default False
#         mode: (String) The type of the constrain that will be applied to the node. Valid options are "parent", "point and "orient". Default "parent"
#         defaultVal: (integer) Default value for the new Switch attribute. If it is out of range, 1 will be used. default: 1.
#         listException: (List) If this argument is not none, the given elements in the list will be removed from the targetList, in case it is in the list of course.
#     Returns: None
#
#     """
#
#     anchorPoses=list(targetList)
#     if anchorPoses.__contains__(node):
#         # if targetList contains the node itself, remove it
#         anchorPoses.remove(node)
#     if anchorPoses==[]:
#         pm.error("target list is empty or no valid targets")
#     if listException != None:
#         for x in listException:
#             if anchorPoses.__contains__(x):
#                 anchorPoses.remove(x)
#     if len(anchorPoses) > defaultVal:
#         defaultVal=1
#     modeList=("parent", "point", "orient")
#     if not modeList.__contains__(mode):
#         pm.error("unknown mode flag. Valid mode flags are 'parent', 'point' and 'orient' ")
#     # create the enumerator list
#     enumFlag = "worldSpace:"
#     for enum in range (0, len(anchorPoses)):
#         cur = str(anchorPoses[enum])
#         cur = cur.replace("cont_", "")
#         enumFlag = "%s%s:" % (enumFlag, cur)
#
#     # # check if the attribute exists
#     if pm.attributeQuery("%sSwitch" % mode, node=node, exists=True):
#         if overrideExisting:
#             pm.deleteAttr("{0}.{1}Switch".format(node, mode))
#         else:
#             pm.error("Switch Attribute already exists. Use overrideExisting=True to delete the old")
#     pm.addAttr(node, at="enum", k=True, shortName="%sSwitch" % mode, longName="%s_Switch" % mode, en=enumFlag, defaultValue=defaultVal)
#     driver = "%s.%sSwitch" %(node, mode)
#
#     switchGrp=createUpGrp(node, ("%sSW" % mode))
#     if mode == "parent":
#         con = pm.parentConstraint(anchorPoses, switchGrp, mo=True)
#     elif mode == "point":
#         con = pm.parentConstraint(anchorPoses, switchGrp, sr=("x","y","z"), mo=True)
#     elif mode == "orient":
#         con = pm.parentConstraint(anchorPoses, switchGrp, st=("x","y","z"), mo=True)
#
#
#     ## make worldSpace driven key (all zero)
#     for i in range (0, len(anchorPoses)):
#         attr="{0}W{1}".format(anchorPoses[i],i)
#         pm.setDrivenKeyframe(con, cd=driver, at=attr, dv=0, v=0)
#
#     # # loop for each DRIVER POSITION
#     for dPos in range (0, len(anchorPoses)):
#         # # loop for each target at parent constraint
#         for t in range (0, len(anchorPoses)):
#             attr = "{0}W{1}".format(anchorPoses[t], t)
#             # # if driver value matches the attribute, make the value 1, else 0
#             if t == (dPos):
#                 value = 1
#             else:
#                 value = 0
#             pm.setDrivenKeyframe(con, cd=driver, at=attr , dv=dPos+1, v=value )
#
#
# def removeAnchor(node):
#     """
#     Removes the anchors created with the spaceswitcher method
#     Args:
#         node: (PyNode Object) A Single object (mostly a controller curve) which the anchors will be removed
#
#     Returns:
#
#     """
#     userAtts = pm.listAttr(node, ud=True)
#     switchAtts = [att for att in userAtts if "_Switch" in att]
#     switchDir = {"point": "pointSW", "orient": "orientSW", "parent": "parentSW"}
#
#     for switch in switchAtts:
#
#         for type in (switchDir.keys()):
#             if type in switch:
#                 switchNode = pm.PyNode("{0}_{1}".format(node, switchDir[type]))
#                 # r = switchNode.getChildren()
#                 constraint = pm.listRelatives(switchNode, c=True,
#                                               type=["parentConstraint", "orientConstraint", "pointConstraint"])
#                 pm.delete(constraint)
#                 child = pm.listRelatives(switchNode, c=True, type="transform")[0]
#                 parent = pm.listRelatives(switchNode, p=True, type="transform")[0]
#                 pm.parent(child, parent)
#                 pm.delete(switchNode)
#                 pm.deleteAttr("{0}.{1}".format(node, switch))


def identifyMaster(node, idBy="idByLabel"):
    validIdByValues = ("idByLabel, idByName")

    # define values as no
    limbType = "N/A"
    limbName = "N/A"

    typeDict = {
        1: 'Root',
        2: 'Hip',
        3: 'Knee',
        4: 'Foot',
        5: 'Toe',
        6: 'Spine',
        7: 'Neck',
        8: 'Head',
        9: 'Collar',
        10: 'Shoulder',
        11: 'Elbow',
        12: 'Hand',
        13: 'Finger',
        14: 'Thumb',
        18: 'Other',
        19: 'Index_F',
        20: 'Middle_F',
        21: 'Ring_F',
        22: 'Pinky_F',
        23: 'Extra_F',
        24: 'Big_T',
        25: 'Index_T',
        26: 'Middle_T',
        27: 'Ring_T',
        28: 'Pinky_T',
        29: 'Extra_T'
    }

    limbDictionary = {
        "arm": ["Collar", "Shoulder", "Elbow", "Hand"],
        "leg": ["LegRoot", "Hip", "Knee", "Foot", "Ball", "HeelPV", "ToePV", "BankIN", "BankOUT"],
        # "hand": ["Finger", "Thumb", "Index_F", "Middle_F", "Ring_F", "Pinky_F", "Extra_F"],
        "spine": ["Spine", "SpineRoot", "SpineEnd"],
        "neck": ["NeckRoot", "Neck", "Head", "Jaw", "HeadEnd"],
        "tail": ["TailRoot", "Tail"],
        "finger": ["FingerRoot", "Finger"],
        "tentacle": ["TentacleRoot", "Tentacle", "TentacleEnd"],
        "root": ["Root"]
    }

    if not idBy in validIdByValues:
        cmds.error("idBy flag is not valid. Valid Values are:%s" %(validIdByValues))

    ## get the label ID
    if idBy == "idByLabel":
        if cmds.objectType(node) != "joint":
            cmds.warning("label identification can only be used for joints")
    typeNum = cmds.getAttr("%s.type" %node)
    if typeNum not in typeDict.keys():
        cmds.warning("Joint Type is not detected with idByLabel method")

    if typeNum == 18:  # if type is in the 'other' category:
        limbName = cmds.getAttr("{0}.otherType".format(node))
    else:
        limbName = typeDict[typeNum]
        # get which limb it is
    for value in limbDictionary.values():
        if limbName in value:
            limbType = limbDictionary.keys()[limbDictionary.values().index(value)]

    ## Get the Side

    sideDict = {
        0: 'C',
        1: 'L',
        2: 'R',
    }

    if idBy == "idByLabel":
            sideNum = cmds.getAttr("{0}.side".format(node))

            if sideNum not in sideDict.keys():
                cmds.warning("Joint Side is not detected with idByLabel method")
            side = sideDict[sideNum]

    if idBy == "idByName":
        # identify the side
        if "_R_" in node:
            side = sideDict[2]
        elif "_L_" in node:
            side = sideDict[1]
        elif "_C_" in node:
            side = sideDict[0]
        else:
            cmds.warning("Joint Side is not detected with idByName method")

    return limbName, limbType, side


#
# # TODO // Create a mirrorController method which will mirror the shape to the other side. similar to the replace controller.
# def mirrorController():
#     pass

def getRigAxes(joint):
    """
    Gets the axis information from the joint which should be written with initBonesClass when created or defined.
    Args:
        joint: The node to look at the attributes

    Returns: upAxis, mirrorAxis, spineDir

    """
    axisDict = {"x": (1.0, 0.0, 0.0), "y": (0.0, 1.0, 0.0), "z": (0.0, 0.0, 1.0), "-x": (-1.0, 0.0, 0.0), "-y": (0.0, -1.0, 0.0), "-z": (0.0, 0.0, -1.0)}
    spineDict = {"x": (-1.0, 0.0, 0.0), "y": (0.0, -1.0, 0.0), "z": (0.0, 0.0, 1.0), "-x": (1.0, 0.0, 0.0), "-y": (0.0, 1.0, 0.0), "-z": (0.0, 0.0, 1.0)}
    upAxis = None
    mirrorAxis = None
    spineDir = None
    if cmds.attributeQuery("upAxis", node=joint, exists=True):
        try:
            upAxis = axisDict[cmds.getAttr("%s.upAxis" %joint).lower().replace("+", "")]
        except:
            cmds.warning("upAxis attribute is not valid, proceeding with default value (y up)")
            upAxis = (0.0, 1.0, 0.0)
    else:
        cmds.warning("upAxis attribute of the root node does not exist. Using default value (y up)")
        upAxis = (0.0, 1.0, 0.0)
    ## get the mirror axis
    if cmds.attributeQuery("mirrorAxis", node=joint, exists=True):
        try:
            mirrorAxis = axisDict[cmds.getAttr("%s.mirrorAxis" %joint).lower().replace("+", "")]
        except:
            cmds.warning("mirrorAxis attribute is not valid, proceeding with default value (scene x)")
            mirrorAxis = (1.0, 0.0, 0.0)
    else:
        cmds.warning("mirrorAxis attribute of the root node does not exist. Using default value (scene x)")
        mirrorAxis = (1.0, 0.0, 0.0)

    ## get spine Direction
    if cmds.attributeQuery("lookAxis", node=joint, exists=True):
        try:
            spineDir = spineDict[cmds.getAttr("%s.lookAxis" %joint).lower().replace("+", "")]
        except:
            cmds.warning("Cannot get spine direction from lookAxis attribute, proceeding with default value (-x)")
            spineDir = (-1.0, 0.0, 0.0)
    else:
        cmds.warning("lookAxis attribute of the root node does not exist. Using default value (-x) for spine direction")
        spineDir = (1.0, 0.0, 0.0)

    return upAxis, mirrorAxis, spineDir

def uniqueName(name):
    baseName = name
    idcounter = 0
    while cmds.objExists(name):
        name = "%s%s" % (baseName, str(idcounter + 1))
        idcounter = idcounter + 1
    return name

def getMirror(node):
    # find the mirror of the oldController
    if "_LEFT_" in node:
        mirrorNode = node.replace("_LEFT_", "_RIGHT_")

    elif "_RIGHT_" in node:
        mirrorNode = node.replace("_RIGHT_", "_LEFT_")
    else:
        mirrorNode = None
        cmds.warning("Cannot find the mirror controller")
    if mirrorNode:
        return mirrorNode

def alignNormal(node, normalVector):
    """
    Aligns the object according to the given normal vector
    Args:
        node: The node to be aligned
        normalVector: Alignment vector

    Returns: None

    """
    # create a temporary alignment locator
    tempTarget = cmds.spaceLocator(name="tempAlignTarget")[0]
    alignTo(tempTarget, node)
    cmds.makeIdentity(tempTarget, a=True)
    cmds.move(normalVector[0], normalVector[1], normalVector[2], tempTarget)
    cmds.delete(cmds.aimConstraint(tempTarget, node, aim=(0,1,0), mo=False))
    cmds.delete(tempTarget)


def orientJoints(jointList, aimAxis=(1.0,0.0,0.0), upAxis=(0.0,1.0,0.0), worldUpAxis=(0.0,1.0,0.0), reverseAim=1, reverseUp=1):


    # aimAxis = reverseAim*dt.Vector(aimAxis)
    aimAxis = reverseAim*om.MVector(aimAxis)
    # upAxis = reverseUp*dt.Vector(upAxis)
    upAxis = reverseUp*om.MVector(upAxis)

    if len(jointList) == 1:
        pass
        return


    for j in range(1, len(jointList)):
        cmds.parent(jointList[j], w=True)

    for j in range (0, len(jointList)):

        if not (j == (len(jointList)-1)):
            aimCon = cmds.aimConstraint(jointList[j+1], jointList[j], aim=aimAxis, upVector=upAxis, worldUpVector=worldUpAxis, worldUpType='vector', weight=1.0)
            cmds.delete(aimCon)
            cmds.makeIdentity(jointList[j], a=True)
    #
    # re-parent the hierarchy
    for j in range (1, len(jointList)):
        cmds.parent(jointList[j], jointList[j-1])

    cmds.makeIdentity(jointList[-1], a=True)
    cmds.setAttr("{0}.jointOrient".format(jointList[-1]), 0,0,0)

def uniqueList(seq): # Dave Kirby
    # Order preserving
    seen = set()
    return [x for x in seq if x not in seen and not seen.add(x)]

def getParent(node):
    parentList = cmds.listRelatives(node, parent=True)
    return parentList[0] if parentList else None

def getShapes(node):
    return cmds.listRelatives(node, c=True, shapes=True)

def matrixConstraint(parent, child, mo=True, prefix="", sr=None, st=None, ss=None):
    child_parent = getParent(child)
    # if child_parent:
    #     cmds.parent(child, w=True)


    mult_matrix = cmds.createNode("multMatrix", name="%s_multMatrix" % prefix)
    decompose_matrix = cmds.createNode("decomposeMatrix", name="%s_decomposeMatrix" % prefix)

    cmds.connectAttr("%s.worldMatrix[0]" % parent, "%s.matrixIn[1]" % mult_matrix)
    cmds.connectAttr("%s.matrixSum" % mult_matrix, "%s.inputMatrix" % decompose_matrix)

    if mo:
        parentWorldMatrix = getMDagPath(parent).inclusiveMatrix()
        childWorldMatrix = getMDagPath(child).inclusiveMatrix()
        localOffset = childWorldMatrix * parentWorldMatrix.inverse()
        cmds.setAttr("%s.matrixIn[0]" % mult_matrix, localOffset, type="matrix")
    if child_parent:
        child_parentWorldMatrix = getMDagPath(child_parent).inclusiveMatrix().inverse()
        # childWorldMatrix = getMDagPath(child).inclusiveMatrix()
        # localOffset = childWorldMatrix * child_parentWorldMatrix.inverse()
        cmds.setAttr("%s.matrixIn[2]" % mult_matrix, child_parentWorldMatrix, type="matrix")


    if not st:
        cmds.connectAttr("%s.outputTranslate" % decompose_matrix, "%s.translate" % child)
    else:
        for attr in "XYZ":
            if attr.lower() not in st and attr.upper() not in st:
                cmds.connectAttr("%s.outputTranslate%s" % (decompose_matrix, attr), "%s.translate%s" % (child, attr))
    if not sr:
        cmds.connectAttr("%s.outputRotate" % decompose_matrix, "%s.rotate" % child)
    else:
        for attr in "XYZ":
            if attr.lower() not in sr and attr.upper() not in sr:
                cmds.connectAttr("%s.outputRotate%s" % (decompose_matrix, attr), "%s.rotate%s" % (child, attr))
    if not ss:
        cmds.connectAttr("%s.outputScale" % decompose_matrix, "%s.scale" % child)
    else:
        for attr in "XYZ":
            if attr.lower() not in ss and attr.upper() not in ss:
                cmds.connectAttr("%s.outputScale%s" % (decompose_matrix, attr), "%s.scale%s" % (child, attr))

    return mult_matrix, decompose_matrix