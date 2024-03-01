"""Module for dynamic Imports
THIS MODULE IS IMPORTANT FOR actions.script.py
"""
import os
import sys


def dynamic_import(file_path):
    """
    Temporarily import modules from a given path.
    Imported modules live ONLY IN GIVEN SCOPE not globally
    Args:
        file_path: (String) Path for python module

    Returns: <module>
    """
    module_name = os.path.splitext(os.path.basename(file_path))[0]

    if sys.version_info >= (
        3,
        5,
    ):
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
