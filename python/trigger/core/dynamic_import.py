"""Module for dynamic Imports"""
import os, sys

def dynamic_import(file_path):
    module_name = os.path.splitext(os.path.basename(file_path))[0]

    if sys.version_info >= (3,5,):
        import importlib.util

        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if not spec:
            return

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        return module
    else:
        import imp
        mod = imp.load_source(module_name, file_path)
        return mod