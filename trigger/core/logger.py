"""Feedback and Logging functions for various debugging and information"""
import logging
# import datetime
# import os

# TODO : Improve the class with file logging abilities

class Logger(object):
    def __init__(self,  logger_name=None, log_directory=None, logging_level="debug"):
        super(Logger, self).__init__()
        self.log_directory = log_directory
        self.logger = logging.getLogger(logger_name)
        if logging_level == "info":
            self.logger.setLevel(logging.INFO)
        elif logging_level == "warning":
            self.logger.setLevel(logging.WARNING)
        elif logging_level == "error":
            self.logger.setLevel(logging.ERROR)
        elif logging_level == "debug":
            self.logger.setLevel(logging.DEBUG)

    def throw_error(self, *args):
        for arg in args:
            self.logger.error(arg)
        raise Exception

    def info(self, *args):
        for arg in args:
            self.logger.info(arg)

    def warning(self, *args):
        for arg in args:
            self.logger.warning(arg)

    def debug(self, *args):
        for arg in args:
            self.logger.debug(arg)

