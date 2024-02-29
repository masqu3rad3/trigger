"""Choose the version control system to use."""
import sys

try:
    if sys.version_info[0] < 3:
        controller = None
    else:
        from trigger.version_control.tik_manager import core
        controller = core.VCS

# except ImportError or SyntaxError:
except (ImportError, RuntimeError) as e:
    controller = None
