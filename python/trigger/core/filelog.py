"""Logging Module for Trigger"""
import sys
import logging
import os
import datetime


class Filelog(object):
    """Filelog class for logging to file"""
    def __init__(self,
                 logname=None,
                 filename=None,
                 filedir=None,
                 date=True,
                 time=True,
                 size_cap=500000,
                 *args,
                 **kwargs):
        super(Filelog, self).__init__()
        self.fileName = filename if filename else "defaultLog"
        self.fileDir = filedir if filedir else os.path.expanduser("~")
        self.filePath = os.path.join(self.fileDir, "%s.log" % self.fileName)
        self.logName = logname if logname else self.fileName
        # self.logger = logging.getLogger(self.fileName)
        self.logger = logging.getLogger(self.logName)
        self.logger.setLevel(logging.DEBUG)
        # self.console_handler = ColorHandler()
        self.logger.addHandler(ColorHandler())
        self.isDate = date
        self.isTime = time
        if not os.path.isfile(self.filePath):
            self._welcome()
        if self.get_size() > size_cap:
            self.clear()

    def _get_now(self):
        """Return the formatted current date and time."""
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
        """Print the welcome message."""
        self._start_logging()
        self.logger.info("=" * len(self.logName))
        self.logger.info(self.logName)
        self.logger.info("=" * len(self.logName))
        self.logger.info("")
        self._end_logging()

    def debug(self, msg):
        """Print debug message."""
        stamped_msg = "%sDEBUG : %s" % (self._get_now(), msg)
        self._start_logging()
        self.logger.debug(stamped_msg)
        self._end_logging()

    def info(self, msg):
        """Print info message."""
        stamped_msg = "%sINFO    : %s" % (self._get_now(), msg)
        self._start_logging()
        self.logger.info(stamped_msg)
        self._end_logging()

    def warning(self, msg):
        """Print warning message."""
        stamped_msg = "%sWARNING : %s" % (self._get_now(), msg)
        self._start_logging()
        self.logger.warning(stamped_msg)
        self._end_logging()

    def error(self, msg, proceed=True):
        """Print error message."""
        stamped_msg = "%sERROR   : %s" % (self._get_now(), msg)
        self._start_logging()
        self.logger.error(stamped_msg)
        self._end_logging()
        if not proceed:
            raise Exception(msg)

    def title(self, msg):
        """Add a title to the log."""
        self._start_logging()
        self.logger.debug("")
        self.logger.debug("=" * (len(msg)))
        self.logger.debug(msg)
        self.logger.debug("=" * (len(msg)))
        # self.logger.debug("\n")
        self._end_logging()

    def header(self, msg):
        """Add a header to the log."""
        self._start_logging()
        self.logger.debug("")
        self.logger.debug(msg)
        self.logger.debug("=" * (len(msg)))
        # self.logger.debug("\n")
        self._end_logging()

    def seperator(self):
        """Add a separator."""
        self._start_logging()
        self.logger.debug("")
        self.logger.debug("-" * 30)
        # self.logger.debug("\n")
        self._end_logging()

    def clear(self):
        """Clear/Reset the log."""
        if os.path.isfile(self.filePath):
            os.remove(self.filePath)
        self._welcome()

    def _start_logging(self):
        """Prepare logger to write into log file."""
        file_logger = logging.FileHandler(self.filePath, delay=True)
        # file_logger = FileHandler(self.filePath)
        self.logger.addHandler(file_logger)
        # self.logger.addHandler(self.console_handler)

    def _end_logging(self):
        """Delete handlers once the logging into file finishes."""
        for handler in self.logger.handlers:
            if isinstance(handler, logging.FileHandler):
                self.logger.removeHandler(handler)
                handler.flush()
                handler.close()
            # self.logger.removeHandler(handler)
            # handler.flush()
            # handler.close()

    def get_size(self):
        """Return the size of the log file."""
        size = os.path.getsize(self.filePath)
        return size

class _AnsiColorizer(object):
    """
    A colorizer is an object that loosely wraps around a stream, allowing
    callers to write text to the stream in a particular color.

    Colorizer classes must implement C{supported()} and C{write(text, color)}.
    """
    _colors = dict(black=30, red=31, green=32, yellow=33,
                   blue=34, magenta=35, cyan=36, white=37)

    def __init__(self, stream):
        self.stream = stream

    @classmethod
    def supported(cls, stream=sys.stdout):
        """
        A class method that returns True if the current platform supports
        coloring terminal output using this method. Returns False otherwise.
        """
        if not stream.isatty():
            return False  # auto color only on TTYs
        try:
            import curses
        except ImportError:
            return False
        else:
            try:
                try:
                    return curses.tigetnum("colors") > 2
                except curses.error:
                    curses.setupterm()
                    return curses.tigetnum("colors") > 2
            except:
                raise
                # guess false in case of error
                return False

    def write(self, text, color):
        """
        Write the given text to the stream in the given color.

        @param text: Text to be written to the stream.

        @param color: A string label for a color. e.g. 'red', 'white'.
        """
        color = self._colors[color]
        self.stream.write('\x1b[%s;1m%s\x1b[0m' % (color, text))


class ColorHandler(logging.StreamHandler):
    def __init__(self, stream=sys.stdout):
        super(ColorHandler, self).__init__(_AnsiColorizer(stream))

    def emit(self, record):
        msg_colors = {
            logging.DEBUG: "green",
            logging.INFO: "blue",
            logging.WARNING: "yellow",
            logging.ERROR: "red"
        }

        color = msg_colors.get(record.levelno, "blue")
        self.stream.write(record.msg + "\n", color)

class FileHandler(logging.FileHandler):
    def emit(self, record):
        pass


if __name__ == "__main__":
    a = Filelog()
    a.info("This is a info test")
    a.debug("This is a debug test")
    a.warning("This is a warninge test")
    a.error("This is a error test")