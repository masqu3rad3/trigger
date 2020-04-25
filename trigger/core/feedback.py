"""Feedback and Logging functions for various debugging and information"""
import logging
# import datetime
# import os

# TODO : Improve the class with file logging abilities

class Feedback(object):
    def __init__(self,  logger_name=None, log_directory=None, logging_level="debug"):
        super(Feedback, self).__init__()
        self.log_directory = log_directory
        self.logger = logging.getLogger(__name__)
        if logging_level == "info":
            self.logger.setLevel(logging.INFO)
        elif logging_level == "warning":
            self.logger.setLevel(logging.WARNING)
        elif logging_level == "error":
            self.logger.setLevel(logging.ERROR)
        elif logging_level == "debug":
            self.logger.setLevel(logging.DEBUG)

    def error(self, keep_going=False, *args):
        msg = ("\n".join(args))
        self.logger.error(msg)
        if not keep_going:
            raise Exception

    def info(self, *args):
        msg = ("\n".join(args))
        self.logger.info(msg)

    def warning(self, *args):
        msg = ("\n".join(args))
        self.logger.warning(msg)
