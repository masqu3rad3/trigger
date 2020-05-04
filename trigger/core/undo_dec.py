from functools import wraps
from maya import cmds
from trigger.core import feedback

def undo(func):
    """ Puts the wrapped `func` into a single Maya Undo action, then
        undoes it when the function enters the finally: block """
    FEEDBACK = feedback.Feedback(func.__name__)
    @wraps(func)
    def _undofunc(*args, **kwargs):
        cmds.undoInfo(ock=True)
        result = None
        try:
            # start an undo chunk
            result = func(*args, **kwargs)
        except Exception as e:
            FEEDBACK.throw_error(e)
        finally:
            # after calling the func, end the undo chunk and undo
            cmds.undoInfo(cck=True)
            return result

    return _undofunc