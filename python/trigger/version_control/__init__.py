"""Choose the version control system to use."""

try:
    from trigger.version_control.tik_manager import core
    controller = core.VCS

except ImportError:
    controller = None


