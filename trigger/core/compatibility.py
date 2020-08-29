#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Python3 - Python2 compatibility methods"""

def encode(data):
    """Encodes the data as unicode data if the interpreter is Python 2.x"""
    try: return unicode(data).encode("utf-8")
    except NameError: return data


def decode(data):
    """Decodes the unicode data if the interpreter is Python 2.x"""
    try: return unicode(data).decode("utf-8")
    except NameError:
        if type(data) == bytes:
            return data.decode("utf-8")
        else:
            return data






