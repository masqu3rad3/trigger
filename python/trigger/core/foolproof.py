#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Collection of methods for foolproofing sanitazing frequent user errors"""

import sys
import re
import unicodedata
from maya import cmds
# from rebellion.library import common
from trigger.library import functions


def selection(minimum=None, maximum=None, groupsOnly=False, meshesOnly=False, nurbsCurvesOnly=False, transforms=True,
              fullPath=False):
    selected = cmds.ls(sl=True, long=fullPath)
    if not selected:
        return False, "Nothing selected"

    if groupsOnly:
        non_groups = [node for node in selected if not functions.isGroup(node)]
        if non_groups:
            return False, "Selection contains non-group nodes" % non_groups

    check_list = []
    if meshesOnly:
        check_list.append("mesh")
    if nurbsCurvesOnly:
        check_list.append("nurbsCurve")

    for check in check_list:
        if not transforms:
            filtered = cmds.ls(selected, type=check)
            if len(filtered) != len(selected):
                return False, "Selection type Error. Only %s type objects can be selected. (No Transform nodes)" % check
        else:
            for node in selected:
                shapes = functions.getShapes(node)
                if not shapes:
                    return False, "Selection contains objects other than %s (No shape node)" % check
                for shape in shapes:
                    if cmds.objectType(shape) != check:
                        return False, "Selection contains objects other than %s" % check

    if minimum and len(selected) < minimum:
        return False, "The minimum required selection is %s" % minimum
    if maximum and len(selected) > maximum:
        return False, "The maximum selection is %s" % maximum
    return selected, ""


def string_value(input_text, allow_spaces=False, directory=False):
    """Checks the text for illegal characters"""
    allow_spaces = " " if allow_spaces else ""
    directory = "/\\\\:" if directory else ""

    pattern = r'^[:A-Za-z0-9%s%s.A_-]*$' % (directory, allow_spaces)

    if re.match(pattern, input_text):
        return True
    else:
        return False


def sanitize(text):
    """
    Checks the given unicode string and remove all special/localized
    characters from it.

    Category "Mn" stands for Nonspacing_Mark
    """

    if type(text) == str:
        if sys.version_info.major > 2:
            pass
        else:
            text = unicode(text, "utf-8")

    newNameList = []
    for c in unicodedata.normalize('NFKD', text):
        if unicodedata.category(c) != 'Mn':
            if c == u'ı':
                newNameList.append(u'i')
            else:
                newNameList.append(c)
    return ''.join(newNameList)
