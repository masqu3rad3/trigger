from os.path import dirname, basename, isfile, join
import glob
modules = glob.glob(join(dirname(__file__), "*.py"))
# __all__ = [ basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]

exceptions = ['__init__.py', 'boiler_plate.py', 'all_modules_data.py']
__all__ = [ basename(f)[:-3] for f in modules if isfile(f) and not basename(f) in exceptions]

for mod in __all__:
    exec("import %s" %mod)