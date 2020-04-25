"""Logging functions for various debugging and information"""
import logging
import datetime
import os

class Logger(object):
    def __init__(self,  log_directory=None):
        super(Logger, self).__init__()
        self.log_directory = log_directory

    def error(self, title="", errorMessage=""):
        """
        Logs the error message
        :param title: (String) Title of the message
        :param errorMessage: (String) Body of the error message
        :return:
        """
        #
        logger = logging.getLogger('SceneManager')
        filePath = os.path.join(self._pathsDict["masterDir"], "sm_logs.log")
        file_logger = logging.FileHandler(filePath)
        logger.addHandler(file_logger)
        logger.setLevel(logging.DEBUG)

        now = datetime.datetime.now()
        timeInfo = now.strftime("%d.%m.%Y - %H:%M")
        userInfo = self.currentUser
        machineInfo = socket.gethostname()
        ## stuff
        logMessage = "-----------------------------------------\n" \
                     "{0} - {1}\n" \
                     "-----------------------------------------\n" \
                     "Log Message:\n" \
                     "{2}\n\n" \
                     "User: {3}\n" \
                     "Workstation: {4}\n".format(title, timeInfo, errorMessage, userInfo, machineInfo)

        logger.debug(logMessage)

        logger.removeHandler(file_logger)
        file_logger.flush()
        file_logger.close()


    def progress(self, action, actionPath):
        logger = logging.getLogger('progressLogs')
        userInfo = self.currentUser
        machineInfo = socket.gethostname()

        currentDT = datetime.datetime.now()
        today = currentDT.strftime("%y%m%d")
        timeStamp = currentDT.hour * 60 + currentDT.minute

        logFolder = os.path.join(self._pathsDict["masterDir"], "progressLogs", machineInfo)
        self._folderCheck(logFolder)
        logFile = os.path.join(logFolder, "%s.log" % today)
        file_logger = logging.FileHandler(logFile)
        logger.addHandler(file_logger)
        logger.setLevel(logging.DEBUG)

        logMessage = "{0}***{1}***{2}***{3}".format(action, userInfo, actionPath, timeStamp)

        logger.debug(logMessage)
        logger.removeHandler(file_logger)
        file_logger.flush()
        file_logger.close()

    def info(self, title, message):