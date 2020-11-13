from maya import cmds
import shelf_tools_rigging

cmds.evalDeferred(shelf_tools_rigging.add_python_path)
cmds.evalDeferred(shelf_tools_rigging.load_shelves)
cmds.evalDeferred(shelf_tools_rigging.load_menu)
