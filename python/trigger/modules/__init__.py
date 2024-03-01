import os
import glob
import importlib
import inspect
from trigger.core.module import ModuleCore, GuidesCore

def get_module_classes(module):
    _data = {}
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and issubclass(obj, ModuleCore) and obj != ModuleCore:
            _data["build"] = obj
        if inspect.isclass(obj) and issubclass(obj, GuidesCore) and obj != GuidesCore:
            _data["guide"] = obj
    return _data


class_data = {}
modules = glob.glob(os.path.join(os.path.dirname(__file__), "*.py"))
exceptions = ["__init__.py"]

for mod in modules:
    file_name = os.path.basename(mod)
    if file_name not in exceptions and not file_name.startswith("_"):
        module_name = file_name[:-3]
        module_path = os.path.join(os.path.dirname(__file__), module_name)
        module = importlib.import_module("{0}.{1}".format(__name__, module_name))
        module_classes = get_module_classes(module)
        if module_classes:
            class_data[module_name] = get_module_classes(module)



# modules = glob.glob(join(dirname(__file__), "*.py"))
#
# exceptions = ["__init__.py"]
# __all__ = [
#     basename(f)[:-3]
#     for f in modules
#     if isfile(f) and not basename(f) in exceptions and not basename(f).startswith("_")
# ]
#
# for mod in __all__:
#     importlib.import_module("trigger.modules.%s" % mod)
