# import sys
from os.path import dirname, basename, isfile, join
import glob
# import importlib

modules = glob.glob(join(dirname(__file__), "*.py"))
exceptions = ['__init__.py', 'boiler_plate.py']
__all__ = [basename(f)[:-3] for f in modules if isfile(f) and not basename(f) in exceptions]

for action in __all__:
    # The following importlib.import_module approach may look more elegant but creating problems with inherited classes
    ########
    # z = importlib.import_module("trigger.actions.%s" % action)
    # if sys.version_info.major >= 3:
    #     importlib.reload(z)
    # else:
    #     reload(z)
    #######
    # So for now, stick to this ugly thing..
    exec("import trigger.actions.%s" %action)
