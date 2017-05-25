import pymel.core as pm

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
    
def alignTo(node1, node2, mode=0, o=(0,0,0)):
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
        pointCon=pm.pointConstraint (node2, node1, mo=False, o=o)
        pm.delete(pointCon)
    elif mode==1:
        ##Rotation Only
        orientCon=pm.orientConstraint (node2, node1, mo=False, o=o)
        pm.delete(orientCon)
    elif mode==2:
        ##Position and Rotation
        parentCon=pm.parentConstraint (node2, node1, mo=False)
        pm.delete(parentCon)

    
def createUpGrp(obj, suffix):
    """
    Creates an Upper Group for the given object.
    Args:
        obj: Source Object
        suffix: Suffix for the group. String.

    Returns: The created group node

    """
    grpName = (obj.nodeName() + "_" + suffix)
    slJoGrp = pm.group (em=True,name=grpName)

    #align the new created empty group to the selected object
    pointCon = pm.parentConstraint (obj, slJoGrp, mo=False)
    pm.delete (pointCon)
    
    #check if the target object has a parent
    originalParent = pm.listRelatives(obj, p=True)
    if (len(originalParent) > 0):
        pm.parent(slJoGrp, originalParent[0])

    pm.parent(obj,slJoGrp)
    return slJoGrp



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
    #shape=node.getShape()
    shapes=pm.listRelatives(node, s=True)
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
    
def alignBetween (node, targetA, targetB, pos=True, rot=True):
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
        tempAim=pm.aimConstraint(targetB,node, mo=False)
        pm.delete(tempAim)

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
        # if an attribute with the same name exists, pass it
        if pm.attributeQuery(attr, node=targetNode, exists=True):
            if overrideEx:
                pm.deleteAttr("%s.%s" % (targetNode, attr))
            else:
                continue


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

        #print flagBuildList

        # parse the flagBuildList into single string
        addAttribute="pm.addAttr(pm.PyNode('%s'), " % (targetNode)
        for i in range (0,len(flagBuildList)):

            addAttribute+=flagBuildList[i]
            if i < len(flagBuildList)-1:
                addAttribute += ", "
            else:
                addAttribute += ")"
        print addAttribute

        exec(addAttribute)

    print ("daisyChain" + str(daisyChain))
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

def spaceSwitcher (node, targetList, overrideExisting=False, mode="parent", defaultVal=1):
    """
    Creates the space switch attributes between selected node (controller) and targets.
    Args:
        node: (single object) Object which anchor space will be switched. Mostly a controller curve.
        targetList: (list of objects) The node will be anchored between these targets.
        overrideExisting: (bool) If True, the existing attributes on the node with the same name will be deleted and recreated. Default False
        mode: (String) The type of the constrain that will be applied to the node. Valid options are "parent", "point and "orient". Default "parent"
        defaultVal: (integer) Default value for the new Switch attribute. If it is out of range, 1 will be used. default: 1.
        
    Returns: None

    """

    anchors=list(targetList)
    if anchors.__contains__(node):
        # if targetList contains the node itself, remove it
        anchors.remove(node)
    if anchors==[]:
        pm.error("target list is empty or no valid targets")

    if len(anchors) > defaultVal:
        defaultVal=1
    modeList=("parent", "point", "orient")
    if not modeList.__contains__(mode):
        pm.error("unknown mode flag. Valid mode flags are 'parent', 'point' and 'orient' ")
    # create the enumerator list
    enumFlag = "worldSpace:"
    for enum in range (0, len(anchors)):
        cur = str(anchors[enum])
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
        con = pm.parentConstraint(anchors, switchGrp, mo=True)
    elif mode == "point":
        con = pm.parentConstraint(anchors, switchGrp, sr=("x","y","z"), mo=True)
    elif mode == "orient":
        con = pm.parentConstraint(anchors, switchGrp, st=("x","y","z"), mo=True)


    ## make worldSpace driven key (all zero)
    for i in range (0, len(anchors)):
        attr="{0}W{1}".format(anchors[i],i)
        pm.setDrivenKeyframe(con, cd=driver, at=attr, dv=0, v=0)

    # # loop for each DRIVER POSITION
    for dPos in range (0, len(anchors)):
        # # loop for each target at parent constraint
        for t in range (0, len(anchors)):
            attr = "{0}W{1}".format(anchors[t], t)
            # # if driver value matches the attribute, make the value 1, else 0
            if t == (dPos):
                value = 1
            else:
                value = 0
            pm.setDrivenKeyframe(con, cd=driver, at=attr , dv=dPos+1, v=value )
