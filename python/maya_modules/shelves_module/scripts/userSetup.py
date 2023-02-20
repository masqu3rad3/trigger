from maya import cmds
import trigger_setup

cmds.evalDeferred(trigger_setup.add_python_path)
cmds.evalDeferred(trigger_setup.load_menu)
