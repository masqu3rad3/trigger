import importlib
from os.path import dirname, basename, isfile, join
import glob

modules = glob.glob(join(dirname(__file__), "*.py"))
# __all__ = [ basename(f)[:-3] for f in maya_modules if isfile(f) and not f.endswith('__init__.py')]

exceptions = ['__init__.py', 'boiler_plate.py']
__all__ = [basename(f)[:-3] for f in modules if isfile(f) and not basename(f) in exceptions]

for action in __all__:
    importlib.import_module("trigger.actions.%s" % action)
    # exec("import %s" %mod)
