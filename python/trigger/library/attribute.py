import re

from maya import cmds
from maya import mel

from trigger.core.decorators import undo
from trigger.core import filelog
from trigger.core import compatibility as compat

log = filelog.Filelog(logname=__name__, filename="trigger_log")

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
        log.error("The attribute dictionary does not have 'attr_name' value")
    nice_name = property_dict.get("nice_name") if property_dict.get("nice_name") else attr_name
    attr_type = property_dict.get("attr_type")
    if not attr_type:
        log.error("The attribute dictionary does not have 'attr_type' value")
    if attr_type not in supported_attrs:
        log.error("The attribute type (%s) is not supported by this method" % attr_type)
    # if some attribute with same name exists, quit
    default_value = property_dict.get("default_value")
    if cmds.attributeQuery(attr_name, node=node, exists=True):
        if default_value:
            if compat.is_string(default_value):
                cmds.setAttr("%s.%s" % (node, attr_name), default_value, type="string")
            else:
                cmds.setAttr("%s.%s" % (node, attr_name), default_value)
        return
    if attr_type == "bool":
        default_value = default_value if default_value else 0
        cmds.addAttr(node, longName=attr_name, niceName=nice_name, at=attr_type, k=keyable, defaultValue=default_value)
        cmds.setAttr("%s.%s" % (node, attr_name), e=True, cb=display)
    elif attr_type == "enum":
        default_value = default_value if default_value else 0
        enum_list = property_dict.get("enum_list")
        if enum_list == None:
            log.error("Missing 'enum_list'")
        cmds.addAttr(node, longName=attr_name, niceName=nice_name, at=attr_type, en=enum_list, k=keyable, defaultValue=default_value)
        cmds.setAttr("%s.%s" % (node, attr_name), e=True, cb=display)
    elif attr_type == "string":
        default_value = default_value if default_value else ""
        cmds.addAttr(node, longName=attr_name, niceName=nice_name, k=keyable, dataType="string")
        cmds.setAttr("%s.%s" % (node, attr_name), default_value, type="string")
        cmds.setAttr("%s.%s" % (node, attr_name), e=True, cb=display)
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

    attr_plug = "%s.%s" % (node, attr_name)
    if display:
        cmds.setAttr(attr_plug, e=True, channelBox=True)

    return attr_plug

def validate_attr(attr, attr_range=None, nice_name=None, attr_type="float", default_value=None, keyable=True, display=True,):
    """Validate attribute.

    Check if attr exists, and create if it doesn't

    """
    splits = attr.split(".")
    node_name = splits[0]
    attr_name = ".".join(splits[1:])
    if cmds.attributeQuery(attr_name, node=node_name, exists=True):
        if not cmds.addAttr(attr, query=True, exists=True):
            # if this isn't a dynamic attr, we don't need to worry about min or max
            return attr

        if attr_range:
            min_value = cmds.addAttr(attr, query=True, min=True)
            max_value = cmds.addAttr(attr, query=True, max=True)
            if min_value is None or attr_range[0] < min_value:
                cmds.addAttr(
                    attr, edit=True, hasMinValue=True, min=attr_range[0]
                )

            if max_value is None or attr_range[1] > max_value:
                cmds.addAttr(
                    attr, edit=True, hasMaxValue=True, max=attr_range[1]
                )
    else:
        # create the creation dict
        min_value = None if not attr_range else attr_range[0]
        max_value = None if not attr_range else attr_range[1]
        property_dict = {
            "attr_name": attr_name,
            "nice_name": nice_name,
            "attr_type": attr_type,
            "default_value": default_value,
            "min_value": min_value,
            "max_value": max_value
        }
        create_attribute(node_name, property_dict=property_dict, keyable=keyable, display=display)

    return attr

def drive_attrs(driver_attr, driven_attrs, driver_range=None, driven_range=None, force=True):
    """
    Creates a ranged connection between driver and driven attr(s)
    Args:
        driver_attr: (String) Driver Attribute. Eg. pPlane.tx
        driven_attrs: (List or String) Driven attribute or list of driven attributes. "pSphere.sx" or  ["pSphere.sx", "pSphere.sy"]
        driver_range: (Tuple or List) Optional. Minumum and maximum range of driver. If not provided, there will be a direct connection between driver and driven
        driven_range: (Tuple or List) Optional. Minumum and maximum range of driven. If not provided, there will be a direct connection between driver and driven
        force: (Bool) If true, any existing connections on driven will be overriden.

    Returns:

    """


    if type(driven_attrs) != list:
        driven_attrs = [driven_attrs]

    # validation
    if force:
        validate_attr(driver_attr, attr_range=driver_range)
        for attr in driven_attrs:
            validate_attr(attr, attr_range=driven_range)


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


def lockAndHide (node, channelArray=None, hide=True):
    """
    Locks and hides the channels specified in the channelArray.
    Args:
        node: (String) target object
        channelArray: (List) the channels as string values. eg: ["sx", "sy", "sz"] or ["translateX", "rotateX", "sz"]
        hide: (Bool) if false, the attributes will be only locked but not hidden. Defaulf True
    Returns: None

    """
    channelArray = ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz", "v"] if not channelArray else channelArray
    for i in channelArray:
        attribute=("%s.%s" %(node, i))
        cmds.setAttr(attribute, lock=True, keyable=not hide, channelBox=not hide)

def unlock(node, attr_list=None):
    attr_list = ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz", "v"] if not attr_list else attr_list
    if type(attr_list) != list:
        attr_list = [attr_list]
    for attr in attr_list:
        cmds.setAttr("{0}.{1}".format(node, attr), e=True, k=True, l=False)

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
    else:
        cmds.copyAttr(sourceNode, targetNode, inConnections=inConnections, outConnections=outConnections, values=values, attribute=userAttr)
        if keepSourceAttributes==False:
            for i in userAttr:
                cmds.deleteAttr("%s.%s" % (sourceNode,i))

def create_global_joint_attrs(joint, moduleName=None, upAxis=None, mirrorAxis=None, lookAxis=None):
    """
    Creates Trigger specific global attrubutes.

    Args:
        joint: (String) Targer Joint
        moduleName: (String) Optional. Name of the module name. If none given, joint name will be used instead
        upAxis: (Tuple) Overrides default upAxis Values for Trigger
        mirrorAxis: (Tuple) Overrides default mirrorAxis Values for Trigger
        lookAxis: (Tuple) Overrides default lookAxis Values for Trigger

    Returns:

    """
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

def getNextIndex(attr, startFrom=0):
    """Returns the next free index from a multi index attribute"""
    return mel.eval("getNextFreeMultiIndex %s %s" % (attr, startFrom))

def disconnect_attr(node=None, attr=None, suppress_warnings=False):
    """Disconnects all connections to the attribute"""
    if len(node.split(".")) < 2:
        if not attr:
            cmds.error("You need to provide node=<node> and attr=<attr> or node=<node>.<attr>")
            return
        attr_path = "%s.%s" %(node, attr)
    else:
        attr_path = node
    plug = cmds.listConnections(attr_path, source=True, plugs=True)

    if plug:
        cmds.disconnectAttr(plug[0], attr_path)
    else:
        if not suppress_warnings:
            log.warning("Nothing connected to this attribute => %s" %attr_path)
        else:
            pass

def separator(node, name, border="-"):
    """Create an attribute providing a visual separator in the channel box.

    Args:
        node (str): The node to add the attribute to.
        name (str): The name of the attribute.
        border (str): The type of character to surround the name.
            Default is `=` but other good options are `_` or `-`.

    Returns:
        str: The name of the attribute created.
    """
    long_name = "__{0}__".format(name.title().replace(" ", ""))
    nice_name = re.sub(r"([a-z])([A-Z])", r"\g<1> \g<2>", name).upper()
    nice_name = "{0} {1}".format(border * 5, nice_name)

    if cmds.attributeQuery(long_name, node=node, exists=True):
        log.info("Attribute %s already exists." %long_name)
        return long_name

    cmds.addAttr(
        node,
        longName=long_name,
        attributeType="enum",
        niceName=nice_name,
        enumName=border * 5,
    )
    cmds.setAttr("{0}.{1}".format(node, long_name), channelBox=True, lock=True)

    return "{0}.{1}".format(node, long_name)

