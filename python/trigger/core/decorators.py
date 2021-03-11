# import sys
from functools import wraps
from maya import cmds
from maya import mel
# import logging
import traceback


from trigger.core import filelog

log = filelog.Filelog(logname=__name__, filename="trigger_log")

def logerror(func):
    """
    Decorator to save the exceptions into log file
    """
    @wraps(func)
    def _exception(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            # log the exception
            log.error("Exception in %s %s" %(func.__name__, func.__module__))
            log.error(traceback.format_exc())
            raise
    return _exception

def undo(func):
    """ Puts the wrapped `func` into a single Maya Undo action, then
        undoes it when the function enters the finally: block """
    @wraps(func)
    def _undofunc(*args, **kwargs):
        cmds.undoInfo(ock=True)
        result = None
        try:
            # start an undo chunk
            return func(*args, **kwargs)
        except Exception as e:
            # log.error(e)
            raise
        finally:
            # after calling the func, end the undo chunk and undo
            cmds.undoInfo(cck=True)
    return _undofunc

def viewportOff(func):
    """
    Decorator - turn off Maya display while func is running.
    if func will fail, the error will be raised after.
    """
    @wraps(func)
    def wrap(*args, **kwargs):

        # Turn $gMainPane Off:
        mel.eval("paneLayout -e -manage false $gMainPane")

        # Decorator will try/except running the function.
        # But it will always turn on the viewport at the end.
        # In case the function failed, it will prevent leaving maya viewport off.
        try:
            return func(*args, **kwargs)
        except Exception:
            mel.eval("paneLayout -e -manage true $gMainPane")
            raise  # will raise original error
        finally:
            mel.eval("paneLayout -e -manage true $gMainPane")
    return wrap

def keepselection(func):
    """Decorator method to keep the current selection. Useful where
    the wrapped method messes with the current selection"""
    @wraps(func)
    def _keepfunc(*args, **kwargs):
        original_selection = cmds.ls(sl=True)
        try:
            # start an undo chunk
            return func(*args, **kwargs)
        except Exception as e:
            # log.error(e)
            raise
        finally:
            # after calling the func, end the undo chunk and undo
            cmds.select(original_selection)

    return _keepfunc

def tracktime(func):
    """Tracks time for the given function"""
    @wraps(func)
    def _tracktime(*args, **kwargs):
        import time
        start = time.time()
        try:
            return func(*args, **kwargs)
        except Exception as e:
            raise
        finally:
            end = time.time()
            log.info("Elapsed: %s" %(end-start))
    return _tracktime

def windowsOff(func):
    """
    Decorator which turns off the Hypershade, Graph Editor, Node Editor and Blendshape Editor
    """
    @wraps(func)
    def _windows_off(*args, **kwargs):
        window_dict = {
            "nodeEditorPanel1Window": cmds.NodeEditorWindow,
            "hyperShadePanel1Window": cmds.HypershadeWindow,
            "blendShapePanel1Window": cmds.BlendShapeEditor,
            "graphEditor1Window": cmds.GraphEditor
        }
        open_windows = cmds.lsUI(type="window")
        # close the windows
        for key, value in window_dict.items():
            if key in open_windows:
                cmds.deleteUI(key)
        try:
            return func(*args, **kwargs)
        except Exception as e:
            for key, value in window_dict.items():
                if key in open_windows:
                    value()
            raise
        finally:
            for key, value in window_dict.items():
                if key in open_windows:
                    value()

    return _windows_off