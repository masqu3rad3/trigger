from importlib import reload
from trigger.library import functions
reload(functions)
from trigger.core import io
reload(io)
from trigger.core import settings
reload(settings)
from trigger.ui import main
reload(main)
from trigger.base import initials
reload(initials)
from trigger.modules import arm
reload(arm)
from trigger.modules import spine
reload(spine)
from trigger.modules import head
reload(head)

#a = main.MainUI().show()

from trigger.actions import kinematics
reload(kinematics)
from trigger.modules import surface
reload(surface)
from trigger.modules import tentacle
reload(tentacle)
tentacle_handler = kinematics.Kinematics(root_joint="jInit_tentacle_center_0")
tentacle_handler.action()
surface_handler = kinematics.Kinematics(root_joint="surface_center")
surface_handler.action()

functions.deleteObject("trigger_refGuides")

from trigger.actions import weights
reload(weights)
weight_handler = weights.Weights()

#weight_handler.save_weights(deformer="skinCluster3", file_path="C:\\Users\\kutlu\\Documents\\testObj_final.json")
#weight_handler.save_weights(deformer="skinCluster11", file_path="C:\\Users\\kutlu\\Documents\\testObj_local.json")

weight_handler.create_deformer("C:\\Users\\kutlu\\Documents\\testObj_final.json")
weight_handler.create_deformer("C:\\Users\\kutlu\\Documents\\testObj_local.json")