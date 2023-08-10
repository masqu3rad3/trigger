from maya import cmds
from trigger.library import functions
from trigger.core import filelog

LOG = filelog.Filelog(logname=__name__, filename="trigger_log")


def create_space_switch(
    node,
    targetList,
    overrideExisting=False,
    mode="parent",
    defaultVal=1,
    listException=None,
    skip_errors=False,
):
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

    anchorPoses = list(targetList)
    if anchorPoses.__contains__(node):
        # if targetList contains the node itself, remove it
        anchorPoses.remove(node)

    if listException != None:
        for x in listException:
            if anchorPoses.__contains__(x):
                anchorPoses.remove(x)
    if len(anchorPoses) > defaultVal:
        defaultVal = 1

    if anchorPoses == []:
        LOG.warning("target list is empty or no valid targets. Skipping...")
        return
    modeList = ("parent", "point", "orient")
    if not modeList.__contains__(mode):
        LOG.error(
            "unknown mode flag. Valid mode flags are 'parent', 'point' and 'orient' ",
            proceed=False,
        )
    # create the enumerator list
    enumFlag = "worldSpace:"
    for enum in range(0, len(anchorPoses)):
        cur = str(anchorPoses[enum])
        cur = cur.replace("cont_", "")
        enumFlag += "%s:" % cur

    # # check if the attribute exists
    if cmds.attributeQuery(mode + "Switch", node=node, exists=True):
        if overrideExisting:
            cmds.deleteAttr("{0}.{1}Switch".format(node, mode))
        else:
            if skip_errors:
                return
            else:
                cmds.error(
                    "Switch Attribute already exists. Use overrideExisting=True to delete the old"
                )
    cmds.addAttr(
        node,
        at="enum",
        k=True,
        shortName=mode + "Switch",
        longName=mode + "_Switch",
        en=enumFlag,
        defaultValue=defaultVal,
    )
    driver = "%s.%sSwitch" % (node, mode)

    # Offset grp [START]
    # Upgrp
    # grpName = ("{0}_{1}SW".format(node, mode))
    # switchGrp = cmds.group(em=True, name=grpName)
    # cmds.delete(cmds.parentConstraint(node, switchGrp, mo=False))
    # originalParent = cmds.listRelatives(node, p=True)
    # if originalParent:
    #     cmds.parent(switchGrp, originalParent[0])
    # cmds.parent(node, switchGrp)
    switchGrp = functions.create_offset_group(node, "SW")
    # Offset grp [END]

    if mode == "parent":
        con = cmds.parentConstraint(anchorPoses, switchGrp, mo=True)
    elif mode == "point":
        con = cmds.parentConstraint(anchorPoses, switchGrp, sr=("x", "y", "z"), mo=True)
    elif mode == "orient":
        con = cmds.parentConstraint(anchorPoses, switchGrp, st=("x", "y", "z"), mo=True)
    else:
        raise Exception(
            "Non-valid mode. The valid modes are 'parent', 'point' and 'orient'"
        )

    ## make worldSpace driven key (all zero)
    for i in range(0, len(anchorPoses)):
        attr = "{0}W{1}".format(anchorPoses[i], i)
        cmds.setDrivenKeyframe(con, cd=driver, at=attr, dv=0.0, v=0.0)

    # # loop for each DRIVER POSITION
    for dPos in range(0, len(anchorPoses)):
        # # loop for each target at parent constraint
        for t in range(0, len(anchorPoses)):
            attr = "{0}W{1}".format(anchorPoses[t], t)
            # # if driver value matches the attribute, make the value 1, else 0
            if t == (dPos):
                value = 1
            else:
                value = 0
            cmds.setDrivenKeyframe(
                con, cd=driver, at=attr, dv=float(dPos + 1), v=float(value)
            )


def remove_space_switch(node):
    """
    Removes the anchors created with the spaceswitcher method
    Args:
        node: (String) A Single object (mostly a controller curve) which the anchors will be removed

    Returns:

    """
    userAtts = cmds.listAttr(node, ud=True)
    switchAtts = [att for att in userAtts if "_Switch" in att]
    switchDir = {"point": "pointSW", "orient": "orientSW", "parent": "parentSW"}

    for switch in switchAtts:
        for type in switchDir.keys():
            if type in switch:
                switchNode = "{0}_{1}".format(node, switchDir[type])
                # r = switchNode.getChildren()
                constraint = cmds.listRelatives(
                    switchNode,
                    c=True,
                    type=["parentConstraint", "orientConstraint", "pointConstraint"],
                )
                cmds.delete(constraint)
                child = cmds.listRelatives(switchNode, c=True, type="transform")[0]
                parent = cmds.listRelatives(switchNode, p=True, type="transform")
                if parent:
                    cmds.parent(child, parent[0])
                else:
                    cmds.parent(child, w=True)
                cmds.delete(switchNode)
                cmds.deleteAttr("{0}.{1}".format(node, switch))
