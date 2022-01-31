try:
    from trigger.version_control import rbl_shotgrid as controller
    from trigger.version_control.vcs import Vcs
    _ = Vcs()
    _.controller = "rbl_shotgrid"
except ImportError:
    controller = None