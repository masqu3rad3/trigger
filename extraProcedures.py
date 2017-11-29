import pymel.core as pm
import pymel.core.datatypes as dt

def getDistance( node1, node2):
    """
    Calculates the distance between Node 1 and Node 2
    Args:
        node1: Node 1. Must be a transform node 
        node2: Node 2. Must be a transform node

    Returns: Distance value.

    """
    Ax, Ay, Az = node1.getTranslation(space="world")
    Bx, By, Bz = node2.getTranslation(space="world")
    return ((Ax-Bx)**2 + (Ay-By)**2 + (Az-Bz)**2)**0.5


def alignTo(sourceObj=None, targetObj=None, mode=0, sl=False, o=(0,0,0)):
    offset=dt.Vector(o)
    if sl == True:
        selection = pm.ls(sl=True)
        if not len(selection) == 2:
            pm.error("select exactly 2 objects")
            return
        sourceObj = selection[0]
        targetObj = selection[1]
    if not sourceObj or not targetObj:
        pm.error("No source and/or target object defined")
        return
    if mode == 0:

        targetTranslation = pm.xform(targetObj, query=True, worldSpace=True, translation=True)
        pm.xform(sourceObj, worldSpace=True, translation =targetTranslation)
    if mode == 1:
        targetRotation = pm.xform(targetObj, query=True, worldSpace=True, rotation=True)
        pm.xform(sourceObj, worldSpace=True, rotation =targetRotation+offset)
    if mode == 2:
        targetMatrix = pm.xform(targetObj, query=True, worldSpace=True, matrix=True)
        pm.xform(sourceObj, worldSpace=True, matrix=targetMatrix)


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
    if type(node1) == str:
        node1 = pm.PyNode(node1)

    if type(node2) == str:
        node2 = pm.PyNode(node2)

    if mode==0:
        ##Position Only
        tempPocon = pm.pointConstraint(node2, node1, mo=False)
        pm.delete(tempPocon)
        # targetLoc = node2.getRotatePivot(space="world")
        # pm.move(node1, targetLoc, a=True, ws=True)

    elif mode==1:
        ##Rotation Only
        if node2.type() == "joint":
            tempOri = pm.orientConstraint(node2, node1, o=o, mo=False)
            pm.delete(tempOri)
        else:
            targetRot = node2.getRotation()
            pm.rotate(node1, targetRot, a=True, ws=True)

    elif mode==2:
        ##Position and Rotation
        tempPacon = pm.parentConstraint(node2, node1, mo=False)
        pm.delete(tempPacon)

def alignAndAim(node, targetList, aimTargetList, upObject=None, upVector=None, rotateOff=None, translateOff=None, freezeTransform=False):
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
        pm.error("In alignAndAim function both upObject and upVector parameters cannot be used")
        return

    pointFlags = ""
    for i in range (len(targetList)):
        if not i == 0:
            pointFlags += ", "
        pointFlags += "targetList[{0}]".format(str(i))
    pointFlags += ", node"
    pointCommand = "pm.pointConstraint({0})".format(pointFlags)
    tempPo = eval(pointCommand)

    aimFlags = ""
    for i in range (len(aimTargetList)):
        if not i == 0:
            aimFlags += ", "
        aimFlags += "aimTargetList[{0}]".format(str(i))
    aimFlags += ", node"
    if upObject:
        aimFlags += ", wuo=upObject, wut='object'"
    if upVector:
        aimFlags += ", wu=upVector, wut='vector'"

    aimCommand = "pm.aimConstraint({0})".format(aimFlags)
    tempAim = eval(aimCommand)

    pm.delete(tempPo)
    pm.delete(tempAim)
    if translateOff:
        pm.move(node, translateOff, r=True)
    if rotateOff:
        pm.rotate(node, rotateOff, r=True, os=True)
    if freezeTransform:
        pm.makeIdentity(node, a=True, t=True)



def getBetweenVector(node, targetPointNodeList):
    # get center vector
    nodePos = node.getTranslation(space="world")
    sumVectors = dt.Vector(0,0,0)
    for p in targetPointNodeList:
        pVector = p.getTranslation(space="world")
        addVector = dt.Vector(dt.Vector(nodePos) - dt.Vector(pVector)).normal()
        sumVectors = sumVectors + addVector
    return sumVectors.normal()

    # pVecA = dt.Vector(dt.Vector(elbowPos) - dt.Vector(shoulderPos)).normal()
    # pVecB = dt.Vector(dt.Vector(elbowPos) - dt.Vector(handPos)).normal()
    # offsetVector = dt.Vector((pVecA + pVecB)).normal()
    # offsetMag = (((initUpperArmDist + initLowerArmDist) / 4))

def createUpGrp(obj, suffix, mi=True):
    """
    Creates an Upper Group for the given object.
    Args:
        obj: (Pymel Object) Source Object
        suffix: (String) Suffix for the group. String.
        mi: (Boolean) Stands for "makeIdentity" If True, freezes the transformations of the new group. Default is True

    Returns: The created group node

    """
    grpName = (obj.nodeName() + "_" + suffix)
    newGrp = pm.group (em=True,name=grpName)

    #align the new created empty group to the selected object

    alignTo(newGrp, obj, mode=2)
    # pointCon = pm.parentConstraint (obj, newGrp, mo=False)
    # pm.delete (pointCon)
    # pm.makeIdentity(newGrp, a=True)

    #check if the target object has a parent
    originalParent = pm.listRelatives(obj, p=True)
    if (len(originalParent) > 0):
        pm.parent(newGrp, originalParent[0], r=False)
        if mi:
            pm.makeIdentity(newGrp, a=True)

    pm.parent(obj,newGrp)
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
    #nodes Translate
    rvsNodeT=pm.createNode("reverse")
    minusOpT=pm.createNode("plusMinusAverage")
    pm.setAttr(minusOpT.operation, 2)
    node1.translate >> rvsNodeT.input
    rvsNodeT.output >> minusOpT.input3D[0]
    pm.setAttr(minusOpT.input3D[1], (1, 1, 1))
    #nodes Rotate
    rvsNodeR=pm.createNode("reverse")
    minusOpR=pm.createNode("plusMinusAverage")
    pm.setAttr(minusOpR.operation, 2)
    node1.rotate >> rvsNodeR.input
    rvsNodeR.output >> minusOpR.input3D[0]
    pm.setAttr(minusOpR.input3D[1], (1, 1, 1))

    #Translate

    if (mirrorAxis=="X"):
        minusOpT.output3Dx >> node2.tx
        node1.ty >> node2.ty
        node1.tz >> node2.tz

        node1.rx >> node2.rx
        minusOpR.output3Dy >> node2.ry
        minusOpR.output3Dz >> node2.rz
    if (mirrorAxis=="Y"):
        node1.tx >> node2.tx
        minusOpT.output3Dy >> node2.ty
        node1.tz >> node2.tz

        minusOpR.output3Dx >> node2.rx
        node1.ry >> node2.ry
        minusOpR.output3Dz >> node2.rz

    if (mirrorAxis=="Z"):
        node1.tx >> node2.tx
        node1.ty >> node2.ty
        minusOpT.output3Dz >> node2.tz

        node1.rx >> node2.rx
        minusOpR.output3Dy >> node2.ry
        minusOpR.output3Dz >> node2.rz


def colorize (node, index):
    """
    Changes the wire color of the node to the index
    Args:
        node: Node
        index: Index Number

    Returns:None

    """
    if not isinstance(node, list):
        node=[node]
    for z in node:
        if isinstance(index, int):
            pass
        elif isinstance(index, str):
            sidesDict={"L":6, "R":13, "C":17, "RMIN":9, "LMIN":18, "CMIN":20}
            if index.upper() in sidesDict.keys():
                index = sidesDict[index.upper()]
            else:
                pm.error("Colorize error... Unknown index command")
                return
        else:
            pm.error("Colorize error... Index flag must be integer or string('L', 'R', 'C')")
            return
        #shape=node.getShape()
        shapes=pm.listRelatives(z, s=True)
        for i in shapes:
            pm.setAttr(i.overrideEnabled, True)
            pm.setAttr(i.overrideColor, index)

def lockAndHide (node, channelArray):
    """
    Locks and hides the channels specified in the channelArray.
    Args:
        node: Node 
        channelArray: Must be list value containing the channels as string values. eg: ["sx", "sy", "sz"] or ["translateX", "rotateX", "sz"] 

    Returns: None

    """
    for i in channelArray:
        attribute=("{0}.{1}".format(node, i))
        pm.setAttr(attribute, lock=True, keyable=False, channelBox=False)

def alignBetween (node, targetA, targetB, pos=True, rot=True, ore=False, o=(0,0,0)):
    """
    Alignes the node between target A and target B
    Args:
        node: Node to be aligned
        targetA: Target A
        targetB: Target B
        pos: bool. If True, aligns the position between targets. Default True
        rot: bool. If True, aligns the rotation between targets. Default True

    Returns: None

    """
    if pos:
        tempPo=pm.pointConstraint(targetA, targetB, node, mo=False)
        pm.delete(tempPo)
    if rot:
        tempAim=pm.aimConstraint(targetB,node, mo=False, o=o)
        pm.delete(tempAim)
    if ore:
        tempOre=pm.orientConstraint(targetA, targetB, node, mo=False, o=o)
        pm.delete(tempOre)

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
        userAttr = pm.listAttr(sourceNode, ud=True)
    else:
        userAttr = attributes

    for attr in userAttr:



        flagBuildList=[]
        atType = pm.getAttr("%s.%s" % (sourceNode,attr), type=True)
        atTypeFlag = "at='%s'" % (str(atType))
        flagBuildList.append(atTypeFlag)

        if pm.attributeQuery(attr, node=sourceNode, enum=True)==True:
            enumList=pm.attributeQuery(attr, node=sourceNode, listEnum=True)
            enumListFlag="en='%s'" % str(enumList[0])
            flagBuildList.append(enumListFlag)

        hiddenState = pm.attributeQuery(attr, node=sourceNode, hidden=True)
        hiddenStateFlag = "h=%s" % (str(hiddenState))
        flagBuildList.append(hiddenStateFlag)

        keyableState = pm.attributeQuery(attr, node=sourceNode, keyable=True)
        keyableStateFlag = "k=%s" % (str(keyableState))
        flagBuildList.append(keyableStateFlag)

        longName = pm.attributeQuery(attr, node=sourceNode, longName=True)
        longNameFlag = "ln='%s'" % str(longName)
        flagBuildList.append(longNameFlag)

        if pm.attributeQuery(attr, node=sourceNode, maxExists=True) == True:
            hardMax=pm.attributeQuery(attr, node=sourceNode, maximum =True)
            hardMaxFlag = "max=%s" % (str(hardMax[0]))
            flagBuildList.append(hardMaxFlag)

        if pm.attributeQuery(attr, node=sourceNode, minExists=True) == True:
            hardMin = pm.attributeQuery(attr, node=sourceNode, minimum=True)
            hardMinFlag = "min=%s" % (str(hardMin[0]))
            flagBuildList.append(hardMinFlag)

        readState = pm.attributeQuery(attr, node=sourceNode, readable=True)
        readStateFlag = "r=%s" % (readState)
        flagBuildList.append(readStateFlag)

        shortName = pm.attributeQuery(attr, node=sourceNode, shortName=True)
        shortNameFlag = "sn='%s'" % str(shortName)
        flagBuildList.append(shortNameFlag)

        if pm.attributeQuery(attr, node=sourceNode, softMaxExists=True) == True:
            softMax=pm.attributeQuery(attr, node=sourceNode, softMax =True)
            softMaxFlag = "smx=%s" % (str(softMax[0]))
            flagBuildList.append(softMaxFlag)

        if pm.attributeQuery(attr, node=sourceNode, softMinExists=True) == True:
            softMin=pm.attributeQuery(attr, node=sourceNode, softMin =True)
            softMinFlag = "smn=%s" % (str(softMin[0]))
            flagBuildList.append(softMinFlag)

        writeState = pm.attributeQuery(attr, node=sourceNode, writable=True)
        writeStateFlag = "w=%s" % (writeState)
        flagBuildList.append(writeStateFlag)


        # parse the flagBuildList into single string
        addAttribute="pm.addAttr(pm.PyNode('%s'), " % (targetNode)
        for i in range (0,len(flagBuildList)):

            addAttribute+=flagBuildList[i]
            if i < len(flagBuildList)-1:
                addAttribute += ", "
            else:
                addAttribute += ")"


        # if an attribute with the same name exists
        if pm.attributeQuery(attr, node=targetNode, exists=True):
            if overrideEx:
                pm.deleteAttr("%s.%s" % (targetNode, attr))
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
                value=pm.getAttr(pm.PyNode("%s.%s" % (sourceNode, userAttr[i])))
                # set Value
                pm.setAttr(pm.PyNode("%s.%s" % (targetNode, userAttr[i])), value)
            pm.PyNode("%s.%s" % (targetNode, userAttr[i])) >> pm.PyNode("%s.%s" % (sourceNode, userAttr[i]))
    else:

        pm.copyAttr(sourceNode, targetNode, inConnections=inConnections, outConnections=outConnections, values=values, attribute=userAttr)
        if keepSourceAttributes==False:
            for i in userAttr:
                pm.deleteAttr("%s.%s" % (sourceNode,i))

def spaceSwitcher (node, targetList, overrideExisting=False, mode="parent", defaultVal=1, listException = None):
    """
    Creates the space switch attributes between selected node (controller) and targets.
    Args:
        node: (single object) Object which anchor space will be switched. Mostly a controller curve.
        targetList: (list of objects) The node will be anchored between these targets.
        overrideExisting: (bool) If True, the existing attributes on the node with the same name will be deleted and recreated. Default False
        mode: (String) The type of the constrain that will be applied to the node. Valid options are "parent", "point and "orient". Default "parent"
        defaultVal: (integer) Default value for the new Switch attribute. If it is out of range, 1 will be used. default: 1.
        listException: (List) If this argument is not none, the given elements in the list will be removed from the targetList, in case it is in the list of course.
    Returns: None

    """

    anchorPoses=list(targetList)
    if anchorPoses.__contains__(node):
        # if targetList contains the node itself, remove it
        anchorPoses.remove(node)
    if anchorPoses==[]:
        pm.error("target list is empty or no valid targets")
    if listException != None:
        for x in listException:
            if anchorPoses.__contains__(x):
                anchorPoses.remove(x)
    if len(anchorPoses) > defaultVal:
        defaultVal=1
    modeList=("parent", "point", "orient")
    if not modeList.__contains__(mode):
        pm.error("unknown mode flag. Valid mode flags are 'parent', 'point' and 'orient' ")
    # create the enumerator list
    enumFlag = "worldSpace:"
    for enum in range (0, len(anchorPoses)):
        cur = str(anchorPoses[enum])
        cur = cur.replace("cont_", "")
        enumFlag += "%s:" % cur

    # # check if the attribute exists
    if pm.attributeQuery(mode+"Switch", node=node, exists=True):
        if overrideExisting:
            pm.deleteAttr("{0}.{1}Switch".format(node, mode))
        else:
            pm.error("Switch Attribute already exists. Use overrideExisting=True to delete the old")
    pm.addAttr(node, at="enum", k=True, shortName=mode+"Switch", longName=mode+"_Switch", en=enumFlag, defaultValue=defaultVal)
    driver = "%s.%sSwitch" %(node, mode)

    switchGrp=createUpGrp(node, (mode+"SW"))
    if mode == "parent":
        con = pm.parentConstraint(anchorPoses, switchGrp, mo=True)
    elif mode == "point":
        con = pm.parentConstraint(anchorPoses, switchGrp, sr=("x","y","z"), mo=True)
    elif mode == "orient":
        con = pm.parentConstraint(anchorPoses, switchGrp, st=("x","y","z"), mo=True)


    ## make worldSpace driven key (all zero)
    for i in range (0, len(anchorPoses)):
        attr="{0}W{1}".format(anchorPoses[i],i)
        pm.setDrivenKeyframe(con, cd=driver, at=attr, dv=0, v=0)

    # # loop for each DRIVER POSITION
    for dPos in range (0, len(anchorPoses)):
        # # loop for each target at parent constraint
        for t in range (0, len(anchorPoses)):
            attr = "{0}W{1}".format(anchorPoses[t], t)
            # # if driver value matches the attribute, make the value 1, else 0
            if t == (dPos):
                value = 1
            else:
                value = 0
            pm.setDrivenKeyframe(con, cd=driver, at=attr , dv=dPos+1, v=value )


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
        "finger": ["Finger", "Thumb", "Index_F", "Middle_F", "Ring_F", "Pinky_F", "Extra_F", "FingerRoot", "ThumbRoot", "IndexRoot", "MiddleRoot", "RingRoot", "PinkyRoot", "ExtraRoot"],
        "tentacle": ["TentacleRoot", "Tentacle", "TentacleEnd"],
        "root": ["Root"]
    }

    if not idBy in validIdByValues:
        pm.error("idBy flag is not valid. Valid Values are:%s" %(validIdByValues))

    ## get the label ID
    if idBy == "idByLabel":
        if node.type() != "joint":
            pm.error("label identification can only be used for joints")
    typeNum = pm.getAttr("%s.type" %node)
    if typeNum not in typeDict.keys():
        pm.error("Joint Type is not detected with idByLabel method")

    if typeNum == 18:  # if type is in the 'other' category:
        limbName = pm.getAttr(node.otherType)
    else:
        limbName = typeDict[typeNum]
        # get which limb it is
    for i in limbDictionary.values():
        if limbName in i:
            limbType = limbDictionary.keys()[limbDictionary.values().index(i)]

    ## Get the Side

    sideDict = {
        0: 'C',
        1: 'L',
        2: 'R',
    }

    if idBy == "idByLabel":
            sideNum = pm.getAttr(node.side)

            if sideNum not in sideDict.keys():
                pm.error("Joint Side is not detected with idByLabel method")
            side = sideDict[sideNum]

    if idBy == "idByName":
        # identify the side
        if "_R_" in node.name():
            side = sideDict[2]
        elif "_L_" in node.name():
            side = sideDict[1]
        elif "_C_" in node.name():
            side = sideDict[0]
        else:
            pm.error("Joint Side is not detected with idByName method")

    return limbName, limbType, side


def replaceController(mirror=True, mirrorAxis="X", keepOld=False, *args, **kwargs):
    if kwargs:
        if kwargs["oldController"] and kwargs["newController"]:
            oldCont = kwargs["oldController"]
            newCont = kwargs["newController"]
            if type(oldCont) == str:
                oldCont=pm.PyNode(oldCont)
            if type(newCont) == str:
                newCont=pm.PyNode(newCont)
        else:
            selection = pm.ls(sl=True)
            if not len(selection) == 2:
                pm.error("select at least two nodes (first new controller then old controller)")
            newCont = selection[0]
            oldCont = selection[1]
        # duplicate the new controller for possible further use

    else:
        selection = pm.ls(sl=True)
        if not len(selection) == 2:
            pm.error("select at least two nodes (first new controller then old controller)")
        newCont = selection[0]
        oldCont = selection[1]


    newContDup = pm.duplicate(newCont)[0]

    pm.makeIdentity(newContDup, a=True)

    #Make sure the new controllers transform are zeroed at the (0,0,0)
    offset = pm.xform(newContDup, q=True, ws=True, rp=True)
    rvOffset = [x * -1 for x in offset]
    pm.xform(newContDup, ws=True, t=rvOffset)


    pm.makeIdentity(newContDup, apply=True, t=True, r=False, s=True, n=False, pn=True)

    ## get the same color code
    pm.setAttr(newContDup.getShape()+".overrideEnabled", pm.getAttr(oldCont.getShape()+".overrideEnabled"))
    pm.setAttr(newContDup.getShape()+".overrideColor", pm.getAttr(oldCont.getShape()+".overrideColor"))


    #move the new controller to the old controllers place
    alignToAlter(newContDup, oldCont)

    ## put the new controller shape under the same parent with the old first (if there is a parent)
    if oldCont.getParent():
        pm.parent(newContDup, oldCont.getParent())
    pm.makeIdentity(newContDup, apply=True)
    ## move the pivot to the same position
    # pivotPoint = pm.xform(oldCont,q=True, t=True, ws=True)
    # pm.xform(newContDup, piv=pivotPoint, ws=True)

    pm.parent(newContDup.getShape(), oldCont, r=True, s=True)



    if mirror:
        # find the mirror of the oldController
        if "_LEFT_" in oldCont.name():
            mirrorName = oldCont.name().replace("_LEFT_", "_RIGHT_")
        elif "_RIGHT_" in oldCont.name():
            mirrorName = oldCont.name().replace("_RIGHT_", "_LEFT_")
        else:
            pm.warning("Cannot find the mirror controller, skipping mirror part")
            if not keepOld:
                pm.delete(oldCont.getShape())
            return
        oldContMirror = pm.PyNode(mirrorName)
        newContDupMirror = pm.duplicate(newCont)[0]
        pm.makeIdentity(newContDupMirror, a=True)
        # Make sure the new controllers transform are zeroed at the (0,0,0)
        offset = pm.xform(newContDupMirror, q=True, ws=True, rp=True)
        rvOffset = [x * -1 for x in offset]
        pm.xform(newContDupMirror, ws=True, t=rvOffset)
        pm.makeIdentity(newContDupMirror, apply=True, t=True, r=True, s=True, n=False, pn=True)
        pm.setAttr("{0}.scale{1}".format(newContDupMirror, mirrorAxis), -1)
        pm.makeIdentity(newContDupMirror, apply=True, s=True)

        ## get the same color code
        pm.setAttr(newContDupMirror.getShape() + ".overrideEnabled", pm.getAttr(oldContMirror.getShape() + ".overrideEnabled"))
        pm.setAttr(newContDupMirror.getShape() + ".overrideColor", pm.getAttr(oldContMirror.getShape() + ".overrideColor"))

        # move the new controller to the old controllers place
        alignToAlter(newContDupMirror, oldContMirror, mode=0)
        pm.parent(newContDupMirror.getShape(), oldContMirror, r=True, s=True)

        if not keepOld:
            pm.delete(oldContMirror.getShape())

    if not keepOld:
        pm.delete(oldContMirror.getShape())

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
    if pm.attributeQuery("upAxis", node=joint, exists=True):
        try:
            upAxis = axisDict[pm.getAttr(joint.upAxis).lower()]
        except:
            pm.warning("upAxis attribute is not valid, proceeding with default value (y up)")
            upAxis = (0.0, 1.0, 0.0)
    else:
        pm.warning("upAxis attribute of the root node does not exist. Using default value (y up)")
        upAxis = (0.0, 1.0, 0.0)
    ## get the mirror axis
    if pm.attributeQuery("mirrorAxis", node=joint, exists=True):
        try:
            mirrorAxis = axisDict[pm.getAttr(joint.mirrorAxis).lower()]
        except:
            pm.warning("mirrorAxis attribute is not valid, proceeding with default value (scene x)")
            mirrorAxis = (1.0, 0.0, 0.0)
    else:
        pm.warning("mirrorAxis attribute of the root node does not exist. Using default value (scene x)")
        mirrorAxis = (1.0, 0.0, 0.0)

    ## get spine Direction
    if pm.attributeQuery("lookAxis", node=joint, exists=True):
        try:
            spineDir = spineDict[pm.getAttr(joint.lookAxis).lower()]
        except:
            pm.warning("Cannot get spine direction from lookAxis attribute, proceeding with default value (-x)")
            spineDir = (-1.0, 0.0, 0.0)
    else:
        pm.warning("lookAxis attribute of the root node does not exist. Using default value (-x) for spine direction")
        spineDir = (1.0, 0.0, 0.0)

    return upAxis, mirrorAxis, spineDir





