from maya import cmds
import shelf_tools

cmds.evalDeferred(shelf_tools.add_python_path)
cmds.evalDeferred(shelf_tools.load_shelves)
cmds.evalDeferred(shelf_tools.load_menu)
