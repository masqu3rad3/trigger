from functools import wraps
from maya import cmds
from maya import mel
import logging


logger = logging.getLogger(__name__)

def undo(func):
    """ Puts the wrapped `func` into a single Maya Undo action, then
        undoes it when the function enters the finally: block """
    @wraps(func)
    def _undofunc(*args, **kwargs):
        cmds.undoInfo(ock=True)
        result = None
        try:
            # start an undo chunk
            result = func(*args, **kwargs)
        except Exception as e:
            logger.error(e)
        finally:
            # after calling the func, end the undo chunk and undo
            cmds.undoInfo(cck=True)
            return result

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
        result = None
        try:
            # start an undo chunk
            result = func(*args, **kwargs)
        except Exception as e:
            cmds.select(original_selection)
            logger.error(e)
        finally:
            # after calling the func, end the undo chunk and undo
            cmds.select(original_selection)
            return result
    return _keepfunc

def tracktime(func):
    """Tracks time for the given function"""
    @wraps(func)
    def _tracktime(*args, **kwargs):
        import time
        start = time.time()
        result = None
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            end = time.time()
            logger.warning("Elapsed: %s" %(end-start))
            logger.error(e)
        finally:
            end = time.time()
            logger.warning("Elapsed: %s" %(end-start))
            return result
    return _tracktime
