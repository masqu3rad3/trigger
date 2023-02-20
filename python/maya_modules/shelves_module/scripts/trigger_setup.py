import os, sys
from maya import cmds
from maya import mel

dir_path = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.abspath(os.path.join(dir_path, os.pardir))
SHELF_DIR = os.path.join(parent_dir, "shelves")

if not os.path.exists(SHELF_DIR):
    print('\n\n WARNING \n\n')


def add_python_path():
    """adds the python path to during launch"""
    maya_modules_path = os.path.abspath(os.path.join(parent_dir, os.pardir))
    rigging_path = os.path.abspath(os.path.join(maya_modules_path, os.pardir))
    if rigging_path not in sys.path:
        sys.path.append(rigging_path)
    print("%s added to the python path" % rigging_path)


def load_shelves(reset=False):
    """
    Loads all shelves under SHELF_DIR.
    Args:
        reset: (Bool) if True, deletes the existing shelves and re-creates them

    Returns: None

    """
    if os.path.isdir(SHELF_DIR) and not cmds.about(batch=True):
        for s in os.listdir(SHELF_DIR):
            path = os.path.join(SHELF_DIR, s).replace('\\', '/')
            if not os.path.isfile(path): continue
            name = os.path.splitext(s)[0].replace('shelf_', '')
            # Delete existing shelf before loading
            if cmds.shelfLayout(name, exists=True):
                if reset:
                    cmds.deleteUI(name)
                    mel.eval('loadNewShelf("{}")'.format(path))
            else:
                mel.eval('loadNewShelf("{}")'.format(path))


def load_menu():
    trigger_command = "from trigger.ui import main\nmain.launch()"
    add_to_menu("Trigger", "Launch Trigger", trigger_command)

    selector_command = "from trigger.utils import trigger_tools\ntrigger_tools.dock_window(trigger_tools.MainUI)"
    add_to_menu("Trigger", "Trigger Selector", selector_command)

    make_up_command = "from trigger.utils import makeup\nmakeup.launch()"
    add_to_menu("Trigger", "Make Up", make_up_command)

    blendshape_transfer_command = "from trigger.utils import blendshape_transfer\nblendshape_transfer.MainUI().show()"
    add_to_menu("Trigger", "Blendshape Transfer", blendshape_transfer_command)

    # add a separator
    cmds.menuItem(divider=True)
    recreate_command = "trigger_setup.load_shelves(reset=True)"
    add_to_menu("Trigger", "Re-create Shelves", recreate_command)


def add_to_menu(menu, menu_item, command):
    main_window = mel.eval('$tmpVar=$gMainWindow')
    menu_widget = '%s_widget' % menu

    # dont create another menu if already exists
    if cmds.menu(menu_widget, label=menu, exists=True, parent=main_window):
        trigger_menu = '%s|%s' % (main_window, menu_widget)
    else:
        trigger_menu = cmds.menu(menu_widget, label=menu, parent=main_window, tearOff=True)

    # skip the process if the menu_item exists
    item_array = cmds.menu(menu_widget, query=True, itemArray=True)
    if item_array:
        for item in item_array:
            label = cmds.menuItem(item, query=True, label=True)
            if label == menu_item:
                return

    cmds.menuItem(label=menu_item, command=command)
