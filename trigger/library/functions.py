import maya.cmds as cmds
# import maya.OpenMaya as om
# USING MAYA API 2.0
import maya.api.OpenMaya as om

from trigger.core import feedback
from trigger.core.undo_dec import undo
FEEDBACK = feedback.Feedback(logger_name=__name__)

JOINT_TYPE_DICT = {
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

JOINT_SIDE_DICT = {
    0: 'C',
    1: 'L',
    2: 'R',
}

AXIS_CONVERSION_DICT = {

}

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
        node: (String) Source Object
        suffix: (String) Suffix for the group. String.
        freezeTransform: (Boolean) Stands for "makeIdentity" If True, freezes the transformations of the new group. Default is True

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
                FEEDBACK.throw_error("Colorize error... Unknown index command")
                return
        else:
            FEEDBACK.throw_error("Colorize error... Index flag must be integer or string('L', 'R', 'C')")
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

def lockAndHide (node, channelArray=None, hide=True):
    """
    Locks and hides the channels specified in the channelArray.
    Args:
        node: Node
        channelArray: Must be list value containing the channels as string values. eg: ["sx", "sy", "sz"] or ["translateX", "rotateX", "sz"]

    Returns: None

    """
    channelArray = ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz", "v"] if not channelArray else channelArray
    ## // TODO OPTIMIZE HERE (map function?)
    for i in channelArray:
        attribute=("%s.%s" %(node, i))
        cmds.setAttr(attribute, lock=True, keyable=not hide, channelBox=not hide)

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

def create_global_joint_attrs(joint, moduleName=None, upAxis=None, mirrorAxis=None, lookAxis=None):
    moduleName = joint if not moduleName else moduleName
    if not cmds.attributeQuery("moduleName", node=joint, exists=True):
        cmds.addAttr(joint, longName="moduleName", dataType="string", k=False)
        cmds.setAttr("%s.%s" % (joint, "moduleName"), moduleName, type="string")

    axis_attrs = ["upAxis", "mirrorAxis", "lookAxis"]
    for attr in axis_attrs:
        if not cmds.attributeQuery(attr, node=joint, exists=True):
            cmds.addAttr(joint, ln=attr, at="float3")
            cmds.addAttr(joint, ln="%sX" % attr, at="float", parent=attr)
            cmds.addAttr(joint, ln="%sY" % attr, at="float", parent=attr)
            cmds.addAttr(joint, ln="%sZ" % attr, at="float", parent=attr)
    if upAxis:
        _ = [cmds.setAttr("%s.upAxis%s" % (joint, axis), upAxis[nmb]) for nmb, axis in enumerate("XYZ")]
    if mirrorAxis:
        _ = [cmds.setAttr("%s.mirrorAxis%s" % (joint, axis), mirrorAxis[nmb]) for nmb, axis in enumerate("XYZ")]
    if lookAxis:
        _ = [cmds.setAttr("%s.lookAxis%s" % (joint, axis), lookAxis[nmb]) for nmb, axis in enumerate("XYZ")]

    if not cmds.attributeQuery("useRefOri", node=joint, exists=True):
        cmds.addAttr(joint, longName="useRefOri", niceName="Inherit_Orientation", at="bool", keyable=True)
    cmds.setAttr("{0}.useRefOri".format(joint), True)

@undo
def create_attribute(node, property_dict=None, keyable=True, display=True, *args, **kwargs):
    """
    Create attribute with the properties defined by the property_dict
    Args:
        node: (String) Node to create attribute on
        property_dict: (Dictionary) This holds the necessary information for the attribute:
                {<nice_name>: (Optional) nice name for the attribute,
                 <attr_name>: name of the attribute,
                 <attr_type>: Valid types are "long", "short", "bool", "enum", "float", "double", "string"
                 <enum_list>: Must be a single string (hence the name) Eg. "option1:option2:option3"
                            Required if the attr_type is "enum".
                 <default_value>: (Optional) Can be float, integer, string or bool depending on the attr_type.
                            If not provided it is 0, "", or False depending on the attr_type
                 <min_value>:  (Optional) Float or Integer. Default is -99999
                 <max_value>:  (Optional) Float or Integer. Default is 99999

                 For easier use, each these elements can be entered as kwargs.

        keyable: (bool) Makes the attribute keyable and visible in the channelbox
        display: (bool) Makes the attr displayable in the cb

    Returns:

    """

    if not property_dict:
        property_dict = {key: value for key, value in kwargs.items()}

    supported_attrs = ["long", "short", "bool", "enum", "float", "double", "string"]
    attr_name = property_dict.get("attr_name")

    if not attr_name:
        FEEDBACK.throw_error("The attribute dictionary does not have 'attr_name' value")
    nice_name = property_dict.get("nice_name") if property_dict.get("nice_name") else attr_name
    attr_type = property_dict.get("attr_type")
    if not attr_type:
        FEEDBACK.throw_error("The attribute dictionary does not have 'attr_type' value")
    if attr_type not in supported_attrs:
        FEEDBACK.throw_error("The attribute type (%s) is not supported by this method" % attr_type)
    # if some attribute with same name exists, quit
    default_value = property_dict.get("default_value")
    if cmds.attributeQuery(attr_name, node=node, exists=True):
        if default_value:
            if type(default_value) == str or type(default_value) == unicode:
                cmds.setAttr("%s.%s" % (node, attr_name), default_value, type="string")
            else:
                cmds.setAttr("%s.%s" % (node, attr_name), default_value)
        return
    if attr_type == "bool":
        default_value = default_value if default_value else 0
        cmds.addAttr(node, longName=attr_name, niceName=nice_name, at=attr_type, k=keyable, defaultValue=default_value)
    elif attr_type == "enum":
        default_value = default_value if default_value else 0
        enum_list = property_dict.get("enum_list")
        if enum_list == None:
            FEEDBACK.throw_error("Missing 'enum_list'")
        cmds.addAttr(node, longName=attr_name, niceName=nice_name, at=attr_type, en=enum_list, k=keyable, defaultValue=default_value)
    elif attr_type == "string":
        default_value = default_value if default_value else ""
        cmds.addAttr(node, longName=attr_name, niceName=nice_name, k=keyable, dataType="string")
        cmds.setAttr("%s.%s" % (node, attr_name), default_value, type="string")
    else:
        min_val = property_dict.get("min_value") if property_dict.get("min_value") != None else -99999
        max_val = property_dict.get("max_value") if property_dict.get("max_value") != None else 99999
        default_value = default_value if default_value else 0
        cmds.addAttr(node,
                     longName=attr_name,
                     niceName=nice_name,
                     at=attr_type,
                     minValue=min_val,
                     maxValue=max_val,
                     defaultValue=default_value,
                     k=keyable,
                     )

    cmds.setAttr("%s.%s" % (node, attr_name), e=True, cb=display)
    return "%s.%s" % (node, attr_name)


def set_joint_type(joint, type_name):
    if type_name in JOINT_TYPE_DICT.values():
        # get the key from the value
        type_int = JOINT_TYPE_DICT.keys()[JOINT_TYPE_DICT.values().index(type_name)]
        cmds.setAttr("%s.type" % joint, type_int)
    else:
        cmds.setAttr("%s.type" % joint , 18) # 18 is the other
        cmds.setAttr("%s.otherType" % joint, type_name, type="string")

def get_joint_type(joint, skipErrors=True):
    type_int = cmds.getAttr("%s.type" % joint)
    if type_int not in JOINT_TYPE_DICT.keys():
        if skipErrors:
            return
        else:
            FEEDBACK.throw_error("Cannot detect joint type => %s" % joint)
    if type_int == 18:
        type_name = cmds.getAttr("{0}.otherType".format(joint))
    else:
        type_name = JOINT_TYPE_DICT[type_int]
    return type_name

def set_joint_side(joint, side):
    if side.lower() == "left" or side.lower() == "l":
        cmds.setAttr("%s.side" % joint, 1)
    elif side.lower() == "right" or side.lower() == "r":
        cmds.setAttr("%s.side" % joint, 2)
    elif side.lower() == "center" or side.lower() == "c":
        cmds.setAttr("%s.side" % joint, 0)
    else:
        FEEDBACK.throw_error("%s is not a valid side value" % side)

def get_joint_side(joint, skipErrors=True):
    side_int = cmds.getAttr("{0}.side".format(joint))
    if side_int not in JOINT_SIDE_DICT.keys():
        if skipErrors:
            return
        else:
            FEEDBACK.throw_error("Joint Side cannot not be detected (%s)" % joint)
    return JOINT_SIDE_DICT[side_int]

def identifyMaster(joint, modules_dictionary):
    # define values as no
    limbType = "N/A"
    jointType = get_joint_type(joint)

    for key, value in modules_dictionary.items():
        limbType = key if jointType in value["members"] else limbType

    side = get_joint_side(joint)
    return jointType, limbType, side

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
    # get the up axis

    upAxis = [cmds.getAttr("%s.upAxis%s" % (joint, dir)) for dir in "XYZ"]
    mirrorAxis = [cmds.getAttr("%s.mirrorAxis%s" % (joint, dir)) for dir in "XYZ"]
    lookAxis = [cmds.getAttr("%s.lookAxis%s" % (joint, dir)) for dir in "XYZ"]

    return tuple(upAxis), tuple(mirrorAxis), tuple(lookAxis)

def uniqueName(name, return_counter=False):
    baseName = name
    idcounter = 0
    while cmds.objExists(name):
        name = "%s%s" % (baseName, str(idcounter + 1))
        idcounter = idcounter + 1
    if return_counter:
        return idcounter
    else:
        return name

def uniqueScene():
    """Makes sure that everything is named uniquely. Returns list of renamed nodes and list of new names"""
    collection = []
    for obj in cmds.ls():
        pathway = obj.split("|")
        if len(pathway) > 1:
            uniqueName(pathway[-1])
            collection.append(obj)
    collection.reverse()
    old_names = []
    new_names = []
    for xe in collection:
        pathway = xe.split("|")
        old_names.append(pathway[-1])
        new_names.append(cmds.rename(xe, uniqueName(pathway[-1])))
    return old_names, new_names

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

def getMeshes(node):
    """Gets only the mesh transform nodes under a group"""
    all_mesh_shapes = cmds.listRelatives(node, ad=True, children=True, type="mesh")
    return uniqueList([getParent(mesh) for mesh in all_mesh_shapes])


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


def drive_attrs(driver_attr, driven_attrs, driver_range=None, driven_range=None, force=True):
    if type(driven_attrs) != list:
        driven_attrs = [driven_attrs]
    if not driver_range or not driven_range:
        # direct connect
        for driven in driven_attrs:
            cmds.connectAttr(driver_attr, driven, force=force)
        return
    if driver_range == driven_range:
        # also direct connect
        for driven in driven_attrs:
            cmds.connectAttr(driver_attr, driven, force=force)
        return

    # RANGE INPUTS
    # check if there is a compound attr
    splits = driver_attr.split(".")
    driver_node = splits[0]
    attr_name = ".".join(splits[1:])
    # driver_node, attr_name = driver_attr.split(".")
    if len(splits) > 2:
        driver_attr_children = []
    else:
        driver_attr_children = cmds.attributeQuery(attr_name, n=driver_node, listChildren=True)
    is_driver_compound = True if driver_attr_children else False
    # if it is eligible use a single set range node
    if is_driver_compound:
        if len(driver_attr_children) > 3:
            cmds.error(
                "drive_attrs does not support more than 3 channel compounds. Connect channels separetely ==> %s" % driver_attr)
            return
        range_node = cmds.createNode("setRange", name="%s_%s_setRange" % (driver_node, attr_name))
        for ch in "XYZ":
            cmds.setAttr("%s.oldMin%s" % (range_node, ch), driver_range[0])
            cmds.setAttr("%s.oldMax%s" % (range_node, ch), driver_range[1])
            cmds.setAttr("%s.min%s" % (range_node, ch), driven_range[0])
            cmds.setAttr("%s.max%s" % (range_node, ch), driven_range[1])

        if len(driver_attr_children) == 3:
            cmds.connectAttr(driver_attr, "%s.value" % range_node, force=force)
        else:
            range_node_input_children = cmds.attributeQuery("value", n=range_node, listChildren=True)
            for nmb, attr in enumerate(driver_attr_children):
                cmds.connectAttr("%s.%s" % (driver_node, attr), "%s.%s" % (range_node, range_node_input_children[nmb]), force=force)
    # if single channel
    else:
        range_node = cmds.createNode("remapValue", name="%s_%s_setRange" % (driver_node, attr_name))
        cmds.setAttr("%s.inputMin" % range_node, driver_range[0])
        cmds.setAttr("%s.inputMax" % range_node, driver_range[1])
        cmds.setAttr("%s.outputMin" % range_node, driven_range[0])
        cmds.setAttr("%s.outputMax" % range_node, driven_range[1])
        cmds.connectAttr(driver_attr, "%s.inputValue" % range_node, force=force)

    # RANGE OUTPUTS
    for driven in driven_attrs:
        # check if the attr is compound
        splits = driven.split(".")
        driven_node = splits[0]
        driven_attr_name = ".".join(splits[1:])
        # driven_node, driven_attr_name = driven.split(".")
        if len(splits) > 2:
            driven_attr_children = []
        else:
            driven_attr_children = cmds.attributeQuery(driven_attr_name, n=driven_node, listChildren=True)
        is_driven_compound = True if driven_attr_children else False
        if is_driven_compound:
            if len(driven_attr_children) > 3:
                cmds.error(
                    "drive_attrs does not support more than 3 channel compounds. Connect channels separetely ==> %s" % driven)
                return
            if is_driver_compound:
                if len(driven_attr_children) == 3:
                    cmds.connectAttr("%s.outValue" % range_node, driven, force=force)
                else:
                    range_node_output_children = cmds.attributeQuery("outValue", n=range_node, listChildren=True)
                    for nmb in range(len(driven_attr_children)):
                        cmds.connectAttr("%s.%s" % (range_node, range_node_output_children[nmb]),
                                         "%s.%s" % (driven_node, driven_attr_children[nmb]), force=force)
            else:
                # if the driver is compound but the driven isnt, just connect the first one
                cmds.connectAttr("%s.outputValueX" % (range_node), driven, force=force)
        else:
            # driver is not compound but driven is
            if is_driven_compound:
                for attr_name in driven_attr_children:
                    cmds.connectAttr("%s.outValue" % range_node, "%s.%s" % (driven_node, attr_name), force=force)
            # nothing is compound
            else:
                cmds.connectAttr("%s.outValue" % range_node, driven, force=force)

def deleteObject(node, force=True):
    if cmds.objExists(node):
        if force:
            cmds.lockNode(node, lock=False)
        cmds.delete(node)
        return True
    else:
        return