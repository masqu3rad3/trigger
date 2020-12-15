"""Module for dynamic Imports"""
import os, sys

python_version = sys.version_info.major
if python_version < 2:
    import importlib as imp
else:
    import imp

def dynamic_import(file_path):
    module_name = os.path.splitext(os.path.basename(file_path))[0]
    module = imp.load_source(module_name, file_path)
    return module

