from os.path import dirname, basename, isfile, join
import glob
import importlib

modules = glob.glob(join(dirname(__file__), "*.py"))

exceptions = ["__init__.py", "boiler_plate.py"]
__all__ = [
    basename(f)[:-3]
    for f in modules
    if isfile(f) and not basename(f) in exceptions and not basename(f).startswith("_")
]

for mod in __all__:
    importlib.import_module("trigger.modules.%s" % mod)
