# -*- coding: utf-8 -*-

name = 'rigging'

version = '0.0.6'

authors = ['Arda Kutlu']

requires = [
    'python_extras',
    'python-2.7.17',
]


def commands():
    import os
    import subprocess

    env.PYTHONPATH.set("{root}/python/:$PYTHONPATH")
    env.MAYA_MODULE_PATH.prepend('{root}/python/maya_modules')
    