"""I/O Class Module to handle all read/write operations
:created: 19/04/2020
:author: Arda Kutlu <ardakutlu@gmail.com>
"""
import os
import json
import shutil

from trigger.core import feedback

FEEDBACK = feedback.Feedback(logger_name=__name__)

class IO(dict):
    def __init__(self, file_name=None, folder_name=None, root_path=None, file_path=None):
        super(IO, self).__init__()
        self.valid_extensions = [".json"]
        self.default_extension = ".json"
        if file_path:
            # self["file_path"] = file_path
            self.file_path = file_path
        elif file_name:
            if not folder_name:
                self.folder_name = ""
            if not root_path:
                self.root_path = os.path.normpath(os.path.expanduser("~"))
            # self["file_path"] = os.path.join(root_path, folder_name, file_name)
            self.file_path = os.path.join(self.root_path, self.folder_name, file_name)
        else:
            FEEDBACK.throw_error("IO class cannot initialized. At least a file name or file_path must be defined")

        # self._folderCheck(self.file_path)

    @property
    def file_path(self):
        return self["file_path"]

    @file_path.setter
    def file_path(self, new_path):
        name, ext = os.path.splitext(new_path)
        if not ext:
            FEEDBACK.throw_error("IO module needs to know the extension")
            raise Exception
        if ext not in self.valid_extensions:
            FEEDBACK.throw_error("IO modules does not support this extension (%s)" % ext)
            raise Exception
        if os.path.isdir(new_path):
            self["file_path"] = self._folderCheck(new_path)
        else:
            self["file_path"] = os.path.join(self.root_path, self.folder_name, new_path)

    def read(self):
        if os.path.isfile(self.file_path):
            return self._load_json(self.file_path)
        else:
            return False

    def write(self, data):
        self._dump_json(data, self.file_path)
        return self.file_path

    def _load_json(self, file_path):
        """Loads the given json file"""
        if os.path.isfile(file_path):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    return data
            except ValueError:
                FEEDBACK.throw_error("Corrupted JSON file => %s" % file_path)
                raise Exception
        else:
            FEEDBACK.throw_error("File cannot be found => %s" % file_path)

    def _dump_json(self, data, file_path):
        """Saves the data to the json file"""
        name, ext = os.path.splitext(unicode(file_path).encode("utf-8"))
        temp_file = ("{0}.tmp".format(name))
        with open(temp_file, "w") as f:
            json.dump(data, f, indent=4)
        shutil.copyfile(temp_file, file_path)
        os.remove(temp_file)

    def _folderCheck(self, checkpath):
        """Checks if the folder exists, creates it if doesnt"""
        basefolder = os.path.split(checkpath)[0] # in case it is a file path
        if not os.path.isdir(os.path.normpath(basefolder)):
            os.makedirs(os.path.normpath(basefolder))
        return checkpath

    def _load_ini(self, file_path):
        pass

    def _dump_ini(self, file_path):
        pass

# class Settings(dict):
#     def __init__(self, filename, folder=None, defaults=None, custom_root_path=None):
#         super(Settings, self).__init__()
#         self.io = IO(file_name=filename, folder_name=folder, root_path=custom_root_path)
#         self.defaults = defaults
#         self.originals = self.read_settings()
#         self.currents = deepcopy(self.originals)
#
#     def read_settings(self):
#         settings = self.io.read()
#         if settings:
#             return settings
#         else:
#             settings = self.write_defaults()
#             return settings
#
#     def write_settings(self, settings):
#         self.io.write(settings)
#
#     def write_defaults(self):
#         if self.defaults:
#             self.io.write(self.defaults)
#             return self.defaults
#         else:
#             FEEDBACK.throw_error("default settings not defined. Cannot write defaults")
#
#     def isChanged(self):
#         """Checks for differences between old and new settings"""
#         return True if self.originals != self.currents else False
#
#     def apply(self):
#         """Equals original settings to the new settings and writes the changes to the file"""
#         if self.isChanged():
#             self.originals = deepcopy(self.currents)
#             self.write_settings(self.originals)
#             FEEDBACK.info("Changes saved")
#         FEEDBACK.warning("Nothing changed")
#
#
#     def set(self, name, value):
#         """sets the value of a setting"""
#         if name in self.currents.keys():
#             self.currents[name] = value
#             return True
#         else:
#             FEEDBACK.warning("'%s' is not in the settings. Use add instead" % name)
#             return False
#
#     def add(self, name, value):
#         """adds a new item to the settings"""
#         if name in self.currents.keys():
#             FEEDBACK.warning("'%s' is already in the settings. Use set instead" % name)
#             return False
#         else:
#             self.currents[name] = value
#             return True
