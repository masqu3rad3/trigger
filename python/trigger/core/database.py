"""Class to handle the database/settings"""
from copy import deepcopy
from trigger.core import io

class Database(dict):
    def __init__(self):
        super(Database, self).__init__()
        self.userSettings = UserSettings()
        self.recentSessions = RecentSessions()

class RecentSessions(list):
    handler = io.IO(file_name="recentSessions.json", folder_name="trigger")

    def __init__(self):
        super(RecentSessions, self).__init__()
        self._get_data()

    def _get_data(self):
        del self[:]
        data = self.handler.read()
        if data:
            self.extend(data)

    def add(self, new_path):
        if new_path in self:
            self.remove(new_path)
        self.insert(0, new_path)
        if len(self) > 9:
            self.pop(-1)
        self.handler.write(self)


# class RecentSessions(object):
#     handler = io.IO(file_name="recentSessions.json", folder_name="trigger")
#     compareData = {}
#
#     def __init__(self):
#         self.recentSessions = []
#
#         self.compareData = deepcopy(self._parse_to_dict())
#         self._parse_from()
#
#     def _parse_from(self):
#         data = self.handler.read()
#
#         if data:
#             for key, value in data.items():
#                 exec("self." + key + '=value')
#             self.compareData = deepcopy(data)
#         else:
#             self.apply()
#
#     def _parse_to_dict(self):
#         data = deepcopy(self.__dict__)
#         data.pop('handler', None)
#         data.pop('compareData', None)
#         return data
#         # self.handler.write(data)
#
#     def apply(self):
#         self.handler.write(self._parse_to_dict())
#
#     def isChanged(self):
#         if self.compareData != self._parse_to_dict():
#             return True
#         else:
#             return False
#
#     def add(self, new_path):
#         if new_path in self.recentSessions:
#             self.recentSessions.remove(new_path)
#         self.recentSessions.insert(0, new_path)
#         if len(self.recentSessions) > 9:
#             self.recentSessions.pop(-1)
#         self.apply()

class UserSettings(object):
    handler = io.IO(file_name="userSettings.json", folder_name="trigger")
    compareData = {}

    def __init__(self):
        self.verboseLevel = 0
        self.upAxis = "+y"
        self.mirrorAxis = "+x"
        self.lookAxis = "+z"
        self.majorCenterColor = 17
        self.minorCenterColor = 20
        self.majorLeftColor = 6
        self.minorLeftColor = 18
        self.majorRightColor = 13
        self.minorRightColor = 12

        self.compareData = deepcopy(self._parse_to_dict())
        self._parse_from()

    def _parse_from(self):
        data = self.handler.read()
        if data:
            for key, value in data.items():
                if UserSettings.__dict__.get(key):
                    exec("self." + key + '=value')
            self.compareData = deepcopy(data)
        else:
            self.apply()

    def _parse_to_dict(self):
        data = deepcopy(self.__dict__)
        data.pop('handler', None)
        data.pop('compareData', None)
        return data
        # self.handler.write(data)

    def apply(self):
        self.handler.write(self._parse_to_dict())

    def isChanged(self):
        if self.compareData != self._parse_to_dict():
            return True
        else:
            return False

# class UserSettings(dict):
#     def __init__(self):
#         super(UserSettings, self).__init__()
#         self.handler = io.IO(file_name="userSettings.json", folder_name="trigger")
#         self["file_data"] = self.handler.read()
#         self["model_data"] = deepcopy(self["file_data"])
#
#     def apply(self):
#         self.handler.write(self["model_data"])
#         self["file_data"] = deepcopy(self["model_data"])
#
#     @property
#     def verboseLevel(self):
#         return self["model_data"].get("verboseLevel")
#
#     @verboseLevel.setter
#     def verboseLevel(self, value):
#         self["model_data"]["verboseLevel"] = value
#
#     @property
#     def upAxis(self):
#         return self["model_data"].get("upAxis")
#
#     @upAxis.setter
#     def upAxis(self, value):
#         self["model_data"]["upAxis"] = value
#
#     @property
#     def mirrorAxis(self):
#         return self["model_data"].get("mirrorAxis")
#
#     @mirrorAxis.setter
#     def mirrorAxis(self, value):
#         self["model_data"]["mirrorAxis"] = value
#
#     @property
#     def lookAxis(self):
#         return self["model_data"].get("lookAxis")
#
#     @lookAxis.setter
#     def lookAxis(self, value):
#         self["model_data"]["lookAxis"] = value
#
#     @property
#     def majorCenterColor(self):
#         return self["model_data"].get("majorCenterColor")
#
#     @majorCenterColor.setter
#     def majorCenterColor(self, value):
#         self["model_data"]["majorCenterColor"] = value
#
#     @property
#     def minorCenterColor(self):
#         return self["model_data"].get("minorCenterColor")
#
#     @minorCenterColor.setter
#     def minorCenterColor(self, value):
#         self["model_data"]["minorCenterColor"] = value
#
#     @property
#     def majorLeftColor(self):
#         return self["model_data"].get("majorLeftColor")
#
#     @majorLeftColor.setter
#     def majorLeftColor(self, value):
#         self["model_data"]["majorLeftColor"] = value
#
#     @property
#     def minorLeftColor(self):
#         return self["model_data"].get("minorLeftColor")
#
#     @minorLeftColor.setter
#     def minorLeftColor(self, value):
#         self["model_data"]["minorLeftColor"] = value
#
#     @property
#     def majorRightColor(self):
#         return self["model_data"].get("majorRightColor")
#
#     @majorRightColor.setter
#     def majorRightColor(self, value):
#         self["model_data"]["majorRightColor"] = value
#
#     @property
#     def minorRightColor(self):
#         return self["model_data"].get("minorRightColor")
#
#     @minorRightColor.setter
#     def minorRightColor(self, value):
#         self["model_data"]["minorRightColor"] = value