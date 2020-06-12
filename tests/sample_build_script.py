## sample build script

from trigger.base import session
reload(session)
from trigger.actions import kinematics
reload(kinematics)
from trigger.actions import shapes
reload(shapes)


# load the guides
t_session = session.Session()
t_session.load_session("/home/arda.kutlu/EG2_playground/guideData/max.json")

# build kinematics
root_joint = "base_c1"
t_kinematics = kinematics.Kinematics(root_joint, create_switchers=True)
t_kinematics.action()

# control shapes
# t_shapes = shapes.Shapes()
# export 
# t_shapes.export_shapes("/home/arda.kutlu/z_test_shapes.abc")
# import
# t_shapes.import_shapes("/home/arda.kutlu/z_test_shapes.abc")

cmds.delete("trigger_refGuides")


# /mnt/ps-storage01/vfx_hgd_000/SG_ROOT/eg2/assets/Character/charMax/MDL/work/maya/charMaxCvA.v029.ma

########################