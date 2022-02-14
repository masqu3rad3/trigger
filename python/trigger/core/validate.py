"""Validate functions"""

from maya import cmds
from trigger.core import filelog
from trigger.ui.feedback import Feedback

log = filelog.Filelog(logname=__name__, filename="trigger_log")
feed = Feedback()

def plugin(plugin):
    """Makes sure the given plugin is loaded"""
    if not cmds.pluginInfo(plugin, l=True, q=True):
        try:
            cmds.loadPlugin(plugin)
            return True
        except:
            msg = "%s cannot be initialized" %plugin
            feed.pop_info(title="Plugin Error", text=msg, critical=True)
            log.error(msg, proceed=False)

