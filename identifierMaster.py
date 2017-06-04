# This script can be used to identify joints (//TODO others
# either by labels or name conventions

import pymel.core as pm

def identifyMaster(node, idBy="label"):
    validIdByValues = ("label, name")

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
        19: 'Index Finger',
        20: 'Middle Finger',
        21: 'Ring Finger',
        22: 'Pinky Finger',
        23: 'Extra Finger',
        24: 'Big Toe',
        25: 'Index Toe',
        26: 'Middle Toe',
        27: 'Ring Toe',
        28: 'Pinky Toe',
        29: 'Extra Toe'
    }

    limbDictionary = {
        "arm": ["Collar", "Shoulder", "Elbow"]
    }

    if not idBy in validIdByValues:
        pm.error("idBy flag is not valid. Valid Values are:%s" %s(validIdByValues))

    ## get the label ID
    if idBy == "label":
        if node.type() != "joint":
            pm.error("label identification can only be used for joints")
    typeNum = pm.getAttr("%s.type" %node)
    if typeNum not in typeDict.keys():
        pm.error("Joint Type is not detected with idByLabel method")

    if typeNum == 18:  # if type is in the 'other' category:
        typeName = pm.getAttr(node.otherType)
    else:
        typeName = typeDict[typeNum]
    return typeName



