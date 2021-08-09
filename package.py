# -*- coding: utf-8 -*-

name = 'rigging'

version = '0.2.0'


authors = ['Arda Kutlu']

requires = [
    'python_extras',
]


def commands():
    import os
    import subprocess

    env.PYTHONPATH.set("{root}/python/:$PYTHONPATH")
    env.MAYA_MODULE_PATH.prepend('{root}/python/maya_modules')
