#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Python3 - Python2 compatibility methods"""
import sys
if sys.version_info.major == 3:
    from trigger.core.python3_only import flatten
else:
    from trigger.core.python2_only import flatten

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

def is_string(data):
    if sys.version_info.major == 3:
        if type(data) == str:
            return True
        else:
            return False
    else:
        if type(data) == str or type(data) == unicode:
            return True
        else:
            return False

# try:
#     from compiler.ast import flatten
# except:
#     pass
    # def flatten(l):
    #     for el in l:
    #         if isinstance(el, collections.Iterable) and not isinstance(el, (str, bytes)):
    #             yield from flatten(el)
    #         else:
    #             yield el

# if sys.version_info.major == 3:
#     def flatten(l):
#         for el in l:
#             if isinstance(el, collections.Iterable) and not isinstance(el, (str, bytes)):
#                 yield from flatten(el)
#             else:
#                 yield el
# else:
#     def flatten(l):
#         for el in l:
#             if isinstance(el, collections.Iterable) and not isinstance(el, basestring):
#                 for sub in flatten(el):
#                     yield sub
#             else:
#                 yield el




