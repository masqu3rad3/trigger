"""Contains data for all modules"""

# This is the bare minimum guide joint names for all modules
#
# MODULE_DICTIONARY = {
#     "arm": ["Collar", "Shoulder", "Elbow", "Hand"],
#     "leg": ["LegRoot", "Hip", "Knee", "Foot", "Ball", "HeelPV", "ToePV", "BankIN", "BankOUT"],
#     "spine": ["SpineRoot", "Spine", "SpineEnd"],
#     "neck": ["NeckRoot", "Neck", "Head", "Jaw", "HeadEnd"],
#     "tail": ["TailRoot", "Tail"],
#     "finger": ["FingerRoot", "Finger"],
#     "tentacle": ["TentacleRoot", "Tentacle", "TentacleEnd"],
#     "root": ["Root"]
# }

MODULE_DICTIONARY = {
    "arm": {
        "members": ["Collar", "Shoulder", "Elbow", "Hand"],
        "properties": [],
        "multi_guide": None,
    },
    "leg": {
        "members": ["LegRoot", "Hip", "Knee", "Foot", "Ball", "HeelPV", "ToePV", "BankIN", "BankOUT"],
        "properties": [],
        "multi_guide": None,
    },
    "spine": {
        "members": ["SpineRoot", "Spine", "SpineEnd"],
        "properties": ["resolution", "dropoff"],
        "multi_guide": "Spine",
    },
    "head": {
        "members": ["NeckRoot", "Neck", "Head", "Jaw", "HeadEnd"],
        "properties": ["resolution", "dropoff"],
        "multi_guide": "Neck",
    },
    "tail": {
        "members": ["TailRoot", "Tail"],
        "properties": [],
        "multi_guide": "Tail",
    },
    "finger": {
        "members": ["FingerRoot", "Finger"],
        "properties": [],
        "multi_guide": "Finger",
    },
    "tentacle": {
        "members":["TentacleRoot", "Tentacle", "TentacleEnd"],
        "properties": ["contRes", "jointRes", "deformerRes", "dropoff"],
        "multi_guide": "Tentacle",
    },
    "root": {
        "members": ["Root"],
        "properties": [],
        "multi_guide": None,
    },
}