import os
import glob
import importlib
import inspect
from trigger.core.action import ActionCore

def get_module_class(module):
    _data = {}
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and issubclass(obj, ActionCore) and obj != ActionCore:
            return obj

class_data = {}
modules = glob.glob(os.path.join(os.path.dirname(__file__), "*.py"))
exceptions = ["__init__.py"]

for mod in modules:
    file_name = os.path.basename(mod)
    if file_name not in exceptions and not file_name.startswith("_"):
        module_name = file_name[:-3]
        module_path = os.path.join(os.path.dirname(__file__), module_name)
        module = importlib.import_module("{0}.{1}".format(__name__, module_name))
        module_class = get_module_class(module)
        if module_class:
            class_data[module_name] = module_class

# from os.path import dirname, basename, isfile, join
# import glob
#
# modules = glob.glob(join(dirname(__file__), "*.py"))
# exceptions = ['__init__.py', 'boiler_plate.py', 'weights_wip.py']
# __all__ = [basename(f)[:-3] for f in modules if isfile(f) and not basename(f) in exceptions]
#
# for action in __all__:
#     # The following importlib.import_module approach may look more elegant but creating problems with inherited classes
#     ########
#     # z = importlib.import_module("trigger.actions.%s" % action)
#     # if sys.version_info.major >= 3:
#     #     importlib.reload(z)
#     # else:
#     #     reload(z)
#     #######
#     # So for now, stick to this ugly thing..
#     exec("import trigger.actions.%s" %action)
