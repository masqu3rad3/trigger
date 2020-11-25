from maya import cmds

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