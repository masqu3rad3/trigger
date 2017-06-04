# This script can be used to identify joints (//TODO others
# either by labels or name conventions

import pymel.core as pm

def identifyMaster(node, idBy="label"):
    validIdByValues = ("label, name")

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
        "leg": ["LegRoot", "Hip", "Knee", "Foot"],
        "hand": ["Finger", "Thumb", "Index_F", "Middle_F", "Ring_F", "Pinky_F", "Extra_F"],
        "foot": ["Ball", "HeelPV", "ToePV", "BankIN", "BankOUT"],
        "spine": ["Spine"],
        "neck": ["Neck"],
        "head": ["Head", "Jaw"]
    }

    if not idBy in validIdByValues:
        pm.error("idBy flag is not valid. Valid Values are:%s" %(validIdByValues))

    ## get the label ID
    if idBy == "label":
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

    return limbName, limbType



