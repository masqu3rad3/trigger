from copy import deepcopy

from trigger.core import io
from trigger.core import logger

FEEDBACK = logger.Logger(logger_name=__name__)

DEFAULT_SETTINGS = {
    "upAxis": "+y",
    "mirrorAxis": "+x",
    "lookAxis": "+z",
    "majorCenterColor": 17,
    "minorCenterColor": 20,
    "majorLeftColor": 6,
    "minorLeftColor": 18,
    "majorRightColor": 13,
    "minorRightColor": 9,
    "seperateSelectionSets": True,
    "afterCreation": 0,
    "bindMethod": 0,
    "skinningMethod": 0
}

DEFAULT_FILENAME = "triggerSettings.json"

class Settings(dict):
    def __init__(self, filename=None, folder=None, custom_root_path=None):
        # super(Settings, self).__init__()
        FEEDBACK.debug("COUNTING")
        FEEDBACK.debug("dd")
        filename = DEFAULT_FILENAME if not filename else filename
        self.io = io.IO(file_name=filename, folder_name=folder, root_path=custom_root_path)
        self.original_settings = self.read_settings()
        self.current_settings = deepcopy(self.original_settings)

    def read_settings(self):
        settings = self.io.read()
        if settings:
            return settings
        else:
            settings = self.write_defaults()
            return settings

    def write_settings(self, settings):
        self.io.write(settings)

    def write_defaults(self):
        self.io.write(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS

    def isChanged(self):
        """Checks for differences between old and new settings"""
        return True if self.original_settings != self.current_settings else False

    def apply(self):
        """Equals original settings to the new settings and writes the changes to the file"""
        if self.isChanged():
            self.original_settings = deepcopy(self.current_settings)
            self.write_settings(self.original_settings)
            FEEDBACK.info("Changes saved")
        FEEDBACK.warning("Nothing changed")

    def get(self, name_of_setting):
        try:
            return self.current_settings[name_of_setting]
        except KeyError:
            FEEDBACK.throw_error("Invalid Setting Name %s" %name_of_setting)


    def set(self, name, value):
        """sets the value of a setting"""
        if name in self.current_settings.keys():
            self.current_settings[name] = value
            return True
        else:
            FEEDBACK.warning("'%s' is not in the settings. Use add instead" % name)
            return False

    def add(self, name, value):
        """adds a new item to the settings"""
        if name in self.current_settings.keys():
            FEEDBACK.warning("'%s' is already in the settings. Use set instead" % name)
            return False
        else:
            self.current_settings[name] = value
            return True
