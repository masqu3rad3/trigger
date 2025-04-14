#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Python3 - Python2 and Maya version compatibility methods"""
import sys
from maya import cmds

if cmds.about(api=True) >= 20260000:
    ADD_NODE_NAME = "addDL"
    MULT_NODE_NAME = "multDL"
else:
    ADD_NODE_NAME = "addDoubleLinear"
    MULT_NODE_NAME = "multDoubleLinear"

if sys.version_info.major == 3:
    from trigger.core.python3_only import flatten
else:
    from trigger.core.python2_only import flatten


def encode(data):
    """Encodes the data as unicode data if the interpreter is Python 2.x"""
    try:
        return unicode(data).encode("utf-8")
    except NameError:
        return data


def decode(data):
    """Decodes the unicode data if the interpreter is Python 2.x"""
    try:
        return unicode(data).decode("utf-8")
    except NameError:
        if type(data) == bytes:
            return data.decode("utf-8")
        else:
            return data


def is_string(data):
    if sys.version_info.major == 3:
        if isinstance(data, str):
            return True
        else:
            return False
    else:
        if isinstance(data, (unicode, str)):
            return True
        else:
            return False
