"""I/O Class Module to handle all read/write operations
:created: 19/04/2020
:author: Arda Kutlu <ardakutlu@gmail.com>
"""
import os
import json
import shutil

from trigger.core import filelog
from trigger.core import compatibility as compat

log = filelog.Filelog(logname=__name__, filename="trigger_log")


class IO(dict):
    def __init__(self,
                 file_name=None,
                 folder_name=None,
                 root_path=None,
                 file_path=None):
        super(IO, self).__init__()
        self.extensions = [".json",
                           ".tr",
                           ".trg",
                           ".trw",
                           ".trs",
                           ".trl",
                           ".trsplit",
                           ".trp"]
        self.default_extension = ".json"
        if file_path:
            self.file_path = file_path
        elif file_name:
            self.folder_name = folder_name or ""
            if not root_path:
                self.root_path = os.path.normpath(os.path.expanduser("~"))
            self.file_path = os.path.join(self.root_path,
                                          self.folder_name,
                                          file_name)
        else:
            log.error('IO initialization error. Define name or file_path')

    @property
    def file_path(self):
        return self["file_path"]

    @file_path.setter
    def file_path(self, new_path):
        name, ext = os.path.splitext(new_path)
        directory, _ = os.path.split(new_path)
        if not ext:
            log.error("IO module needs to know the extension")
            raise Exception
        if ext not in self.extensions:
            log.error("IO maya_modules does not support this extension ({})"
                      .format(ext))
            raise Exception
        if directory:
            self["file_path"] = self._folderCheck(new_path)
        else:
            self["file_path"] = os.path.join(
                self.root_path, self.folder_name, new_path)

    def read(self, file_path=None):
        """Read and returns the data stored in file path"""
        file_path = file_path if file_path else self.file_path
        if os.path.isfile(file_path):
            return self._load_json(file_path)
        else:
            return False

    def write(self, data, file_path=None):
        """
        Write data to file.
        Args:
            data: <data> Data to be written to the json file
            file_path: (String) if not specified uses the one defined
            in the class instantiation.

        Returns:
            (String) Path of the file
        """
        file_path = file_path if file_path else self.file_path
        self._dump_json(data, file_path)
        return file_path

    @staticmethod
    def _load_json(file_path):
        """Loads the given json file"""
        if os.path.isfile(file_path):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    return data
            except ValueError:
                log.error("Corrupted file => %s" % file_path)
                raise Exception
        else:
            log.error("File cannot be found => %s" % file_path)

    @staticmethod
    def _dump_json(data, file_path):
        """Saves the data to the json file"""
        name, ext = os.path.splitext(compat.encode(file_path))
        temp_file = ("{0}.tmp".format(name))
        with open(temp_file, "w") as f:
            json.dump(data, f, indent=4)
        shutil.copyfile(temp_file, file_path)
        os.remove(temp_file)

    @staticmethod
    def _folderCheck(checkpath):
        """Checks if the folder exists, creates it if doesnt"""
        if os.path.splitext(checkpath)[1]:
            basefolder = os.path.split(checkpath)[0]  # in case it is a file path
        else:
            basefolder = checkpath

        if not os.path.isdir(os.path.normpath(basefolder)):
            os.makedirs(os.path.normpath(basefolder))
        return checkpath

    def _load_ini(self, file_path):
        pass

    def _dump_ini(self, file_path):
        pass
