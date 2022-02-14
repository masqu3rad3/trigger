"""Logging Module for Trigger"""

import logging
import os
import datetime


class Filelog(object):
    def __init__(self, logname=None, filename=None, filedir=None, date=True, time=True, size_cap=500000, *args,
                 **kwargs):
        super(Filelog, self).__init__()
        self.fileName = filename if filename else "defaultLog"
        self.fileDir = filedir if filedir else os.path.expanduser("~")
        self.filePath = os.path.join(self.fileDir, "%s.log" % self.fileName)
        self.logger = logging.getLogger(self.fileName)
        self.logger.setLevel(logging.DEBUG)
        self.logName = logname if logname else self.fileName
        self.isDate = date
        self.isTime = time
        if not os.path.isfile(self.filePath):
            self._welcome()
        if self.get_size() > size_cap:
            self.clear()

    def _get_now(self):
        """Returns the formatted current date and time"""
        if self.isDate or self.isTime:
            now = datetime.datetime.now()
            now_data = []
            if self.isDate:
                now_data.append(now.strftime("%d/%m/%y"))
            if self.isTime:
                now_data.append(now.strftime("%H:%M"))
            now_string = " - ".join(now_data)
            return "%s - " % now_string
        else:
            return ""

    def _welcome(self):
        """Prints the welcome message"""
        self._start_logging()
        self.logger.debug("=" * len(self.logName))
        self.logger.debug(self.logName)
        self.logger.debug("=" * len(self.logName))
        self.logger.debug("")
        self._end_logging()

    def debug(self, msg):
        """Prints debug message"""
        stamped_msg = "%sDEBUG : %s" % (self._get_now(), msg)
        self._start_logging()
        self.logger.debug(stamped_msg)
        self._end_logging()

    def info(self, msg):
        """Prints info message"""
        stamped_msg = "%sINFO    : %s" % (self._get_now(), msg)
        self._start_logging()
        self.logger.info(stamped_msg)
        self._end_logging()

    def warning(self, msg):
        """Prints warning message"""
        stamped_msg = "%sWARNING : %s" % (self._get_now(), msg)
        self._start_logging()
        self.logger.warning(stamped_msg)
        self._end_logging()

    def error(self, msg, proceed=True):
        """Prints error message"""
        stamped_msg = "%sERROR   : %s" % (self._get_now(), msg)
        self._start_logging()
        self.logger.error(stamped_msg)
        self._end_logging()
        if not proceed:
            raise Exception(msg)

    def title(self, msg):
        """Adds a title to the log"""
        self._start_logging()
        self.logger.debug("")
        self.logger.debug("=" * (len(msg)))
        self.logger.debug(msg)
        self.logger.debug("=" * (len(msg)))
        # self.logger.debug("\n")
        self._end_logging()

    def header(self, msg):
        """Adds a header to the log"""
        self._start_logging()
        self.logger.debug("")
        self.logger.debug(msg)
        self.logger.debug("=" * (len(msg)))
        # self.logger.debug("\n")
        self._end_logging()

    def seperator(self):
        """Adds a separator"""
        self._start_logging()
        self.logger.debug("")
        self.logger.debug("-" * 30)
        # self.logger.debug("\n")
        self._end_logging()

    def clear(self):
        """Clears/Reset the log"""
        if os.path.isfile(self.filePath):
            os.remove(self.filePath)
        self._welcome()

    def _start_logging(self):
        """Prepares logger to write into log file"""
        file_logger = logging.FileHandler(self.filePath)
        self.logger.addHandler(file_logger)

    def _end_logging(self):
        """Deletes handlers once the logging into file finishes"""
        for handler in self.logger.handlers:
            self.logger.removeHandler(handler)
            handler.flush()
            handler.close()

    def get_size(self):
        """Returns the size of the log file"""
        size = os.path.getsize(self.filePath)
        return size
