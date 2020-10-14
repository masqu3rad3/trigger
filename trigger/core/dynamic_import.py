"""Module for dynamic Imports"""
import os, sys
import imp
import importlib

python_version = sys.version_info.major

def dynamic_import(file_path):
    module_name = os.path.splitext(os.path.basename(file_path))[0]
    module = imp.load_source(module_name, file_path)
    return module

# class TestClass(object):
#     def __init__(self):
#         self.filePath = None
#         self.asName = None
#
#     def action(self):
#         exec("global %s" % self.asName, globals())
#         foo = "imp.load_source('%s', '/home/arda.kutlu/Downloads/trigger_test_script.py')" % self.asName
#         cmd = "{0}={1}".format(self.asName, foo)
#         exec(cmd, globals())