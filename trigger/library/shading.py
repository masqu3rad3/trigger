"""Collection of shading related functions"""

from maya import cmds

def get_file_nodes(objList):
    returnList = []
    if not objList:
        return returnList
    for obj in objList:
        # Get the shading group from the selected mesh
        sg = cmds.listConnections(obj, type='shadingEngine')
        if not sg:
            continue
        allInputs = []
        for i in sg:
            allInputs.extend(cmds.listHistory(i))

        uniqueInputs =set(allInputs)

        fileNodes = cmds.ls(uniqueInputs, type="file")
        if len(fileNodes) != 0:
            returnList.extend(fileNodes)
    returnList = set(returnList)
    return returnList