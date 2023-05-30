from maya import cmds
from trigger.objects.controller import Controller
from trigger.library import functions, naming, api, connection, attribute


# create a ground squash controller for each foot

for side in "LR":
    cont = Controller(shape="Square", name=naming.parse("FootTouch", side=side, suffix="cont"), scale=[5, 5, 14])
    foot_cont = "{}_Leg_IK_foot_cont".format(side)
    functions.align_to(cont.name, foot_cont)
    cont_offset = cont.add_offset("off")
    cont_auto = cont.add_offset("auto")
    _pos = api.get_world_translation("{}_Leg_toe_jDef".format(side))
    cmds.setAttr("{}.ty".format(cont_offset), _pos[1])  # move the controller to the bottom of the foot
    connection.matrixConstraint("{}_Leg_foot_jDef".format(side), cont_offset, maintainOffset=True)

    # drive the claw IK offsets with this controller
    ik_offsets = [
        "{}_Toe1_IK_end_cont_OFF",
        "{}_Toe2_IK_end_cont_OFF",
        "{}_Dewclaw_IK_end_cont_OFF"
    ]

    for ik_off in ik_offsets:
        connection.matrixConstraint(cont.name, ik_off.format(side), maintainOffset=True)

    # drive the cont_auto offset group with foot controller
    attribute.drive_attrs("{}.tz".format(foot_cont), "{}.ty".format(cont_auto), [3, 0], [0, 3])

    # lock the attributes
    attribute.lock_and_hide(cont.name, ["tx", "tz", "sx", "sy", "sz", "v"])

    cmds.parent(cont_offset, "{}_Leg_controller_grp".format(side))

    