# Example script for creating double blendshape face ui controls

from maya import cmds
from trigger.library import controllers
from trigger.library import functions

iconHandler = controllers.Icon()

hookNode = "hook_blendshapes"

double_controllers = ["grumpy", "smallGrin", "closedGrin", "meanBrows", "slyEye", "openGrin"]

if not cmds.objExists(hookNode):
    cmds.group(name=hookNode, em=True)

for contName in double_controllers:
    cont, _ = iconHandler.createIcon("Circle", iconName="%s_cont" % contName, normal=(0, 0, 1))
    bound, _ = iconHandler.createIcon("Square", iconName="%s_bound" % contName, normal=(0, 0, 1))
    cmds.setAttr("%s.s" % bound, 10, 5, 10)
    cmds.setAttr("%s.ty" % bound, 5)
    cmds.makeIdentity(bound, a=True)

    cont_offset = functions.createUpGrp(cont, "offset")
    cmds.parent(cont_offset, bound)
    cmds.group(bound, name="%s_move_offset" % contName)

    left_mult = cmds.createNode("multDoubleLinear", name="%s_L_mult" % contName)
    right_mult = cmds.createNode("multDoubleLinear", name="%s_R_mult" % contName)

    functions.drive_attrs("%s.ty" % cont, ["%s.input1" % right_mult, "%s.input1" % left_mult], driver_range=[0, 10],
                          driven_range=[0, 1])
    functions.drive_attrs("%s.tx" % cont, "%s.input2" % right_mult, driver_range=[0, -10], driven_range=[1, 0])
    functions.drive_attrs("%s.tx" % cont, "%s.input2" % left_mult, driver_range=[0, 10], driven_range=[1, 0])

    hook_attr_L = functions.create_attribute(hookNode,
                                             {"attr_name": "L%s" % contName, "attr_type": "float", "min_value": 0,
                                              "max_value": 1}, display=False)
    hook_attr_R = functions.create_attribute(hookNode,
                                             {"attr_name": "R%s" % contName, "attr_type": "float", "min_value": 0,
                                              "max_value": 1}, display=False)

    cmds.connectAttr("%s.output" % left_mult, hook_attr_L)
    cmds.connectAttr("%s.output" % right_mult, hook_attr_R)

    cmds.transformLimits(cont, tx=(-10, 10), etx=(1, 1))
    cmds.transformLimits(cont, ty=(0, 10), ety=(1, 1))