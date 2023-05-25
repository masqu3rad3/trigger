"""Validate functions"""

from maya import cmds
from trigger.core import filelog
from trigger.ui.feedback import Feedback

LOG = filelog.Filelog(logname=__name__, filename="trigger_log")
FEED = Feedback()


def plugin(plugin_name):
    """Make sure the given plugin is loaded."""
    if not cmds.pluginInfo(plugin_name, loaded=True, query=True):
        try:
            cmds.loadPlugin(plugin_name)
            return True
        except Exception as e:
            msg = "{} cannot be initialized".format(plugin_name)
            FEED.pop_info(title="Plugin Error", text=msg, critical=True)
            LOG.error(msg, proceed=False)
            raise e
