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
    },
    "leg": {
        "members": ["LegRoot", "Hip", "Knee", "Foot", "Ball", "HeelPV", "ToePV", "BankIN", "BankOUT"],
        "properties": [],
    },
    "spine": {
        "members": ["SpineRoot", "Spine", "SpineEnd"],
        "properties": ["resolution", "dropoff"],
    },
    "neck": {
        "members": ["NeckRoot", "Neck", "Head", "Jaw", "HeadEnd"],
        "properties": ["resolution", "dropoff"],
    },
    "tail": {
        "members": ["TailRoot", "Tail"],
        "properties": [],
    },
    "finger": {
        "members": ["FingerRoot", "Finger"],
        "properties": [],
    },
    "tentacle": {
        "members":["TentacleRoot", "Tentacle", "TentacleEnd"],
        "properties": ["contRes", "jointRes", "deformerRes", "dropoff"],
    },
    "root": {
        "members": ["Root"],
        "properties": [],
    },
}