"""Qt related Maya Utility Methods"""
import sys
from maya import cmds
from maya import OpenMayaUI as omui
from trigger.ui.Qt import QtWidgets, QtCore, QtCompat

def getMayaMainWindow():
    """
    Gets the memory adress of the main window to connect Qt dialog to it.
    Returns:
        (long or int) Memory Adress
    """
    win = omui.MQtUtil_mainWindow()
    if sys.version_info.major == 3:
        ptr = QtCompat.wrapInstance(int(win), QtWidgets.QMainWindow)
    else:
        ptr = QtCompat.wrapInstance(long(win), QtWidgets.QMainWindow)
    return ptr

