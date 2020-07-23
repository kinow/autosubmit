import logging, os, sys
from datetime import datetime

class LogFormatter:
    """
    Class to format log output.

    :param to_file: If True, creates a LogFormatter for files; if False, for console
    :type to_file: bool
    """
    __module__ = __name__
    RESULT = '\x1b[32m'
    WARNING = '\x1b[33m'
    ERROR = '\x1b[31m'
    CRITICAL = '\x1b[1m \x1b[31m'
    DEFAULT = '\x1b[0m\x1b[39m'

    def __init__(self, to_file=False):
        """
        Initializer for LogFormatter

        """
        self._file = to_file
        if self._file:
            self._formatter = logging.Formatter('%(asctime)s %(message)s')
        else:
            self._formatter = logging.Formatter('%(message)s')

    def format(self, record):
        """
        Format log output, adding labels if needed for log level. If logging to console, also manages font color.
        If logging to file adds timestamp

        :param record: log record to format
        :type record: LogRecord
        :return: formatted record
        :rtype: str
        """
        header = ''
        if record.levelno == Log.RESULT:
            if not self._file:
                header = LogFormatter.RESULT
        elif record.levelno == Log.USER_WARNING:
            if not self._file:
                header = LogFormatter.WARNING
        elif record.levelno == Log.WARNING:
            if not self._file:
                header = LogFormatter.WARNING
            header += '[WARNING] '
        elif record.levelno == Log.ERROR:
            if not self._file:
                header = LogFormatter.ERROR
            header += '[ERROR] '
        elif record.levelno == Log.CRITICAL:
            if not self._file:
                header = LogFormatter.ERROR
            header += '[CRITICAL] '
        msg = self._formatter.format(record)
        if header != '' and not self._file:
            msg += LogFormatter.DEFAULT
        return header + msg


class StatusFilter(logging.Filter):

    def filter(self, rec):
        return rec.levelno == Log.STATUS


class Log:
    """
    Static class to manage the log for the application. Messages will be sent to console and to file if it is
    configured. Levels can be set for each output independently. These levels are (from lower to higher priority):
        - EVERYTHING
        - INFO
        - RESULT
        - ERROR
        - CRITICAL
        - USER_WARNING
        - WARNING
        - DEBUG
        - NO_LOG : this level is just defined to remove every output
    """
    __module__ = __name__
    EVERYTHING = 0
    STATUS = 100
    DEBUG = 101
    WARNING = 102
    USER_WARNING = 103
    INFO = 104
    RESULT = 105
    ERROR = 106
    CRITICAL = 107
    NO_LOG = CRITICAL + 1
    logging.basicConfig()
    if 'Autosubmit' in logging.Logger.manager.loggerDict.keys():
        log = logging.getLogger('Autosubmit')
    else:
        log = logging.Logger('Autosubmit', EVERYTHING)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(INFO)
    console_handler.setFormatter(LogFormatter(False))
    log.addHandler(console_handler)

    @staticmethod
    def set_file(file_path, type='out', level=WARNING):
        """
        Configure the file to store the log. If another file was specified earlier, new messages will only go to the
        new file.

        :param file_path: file to store the log
        :type file_path: str
        """
        directory, filename = os.path.split(file_path)
        if not os.path.exists(directory):
            os.mkdir(directory)
        files = [ f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)) and f.endswith(filename) ]
        if len(files) >= 5:
            files.sort()
            os.remove(os.path.join(directory, files[0]))
        file_path = os.path.join(directory, ('{0:%Y%m%d_%H%M%S}_').format(datetime.now()) + filename)
        if type == 'out':
            file_handler = logging.FileHandler(file_path, 'w')
            file_handler.setLevel(level)
            file_handler.setFormatter(LogFormatter(True))
            Log.log.addHandler(file_handler)
        elif type == 'err':
            err_file_handler = logging.FileHandler(file_path, 'w')
            err_file_handler.setLevel(Log.ERROR)
            err_file_handler.setFormatter(LogFormatter(True))
            Log.log.addHandler(err_file_handler)
        elif type == 'status':
            custom_filter = StatusFilter()
            file_path = os.path.join(directory, filename)
            status_file_handler = logging.FileHandler(file_path, 'w')
            status_file_handler.setLevel(Log.STATUS)
            status_file_handler.setFormatter(LogFormatter(False))
            status_file_handler.addFilter(custom_filter)
            Log.log.addHandler(status_file_handler)
        os.chmod(file_path, 509)

    @staticmethod
    def set_console_level(level):
        """
        Sets log level for logging to console. Every output of level equal or higher to parameter level will be
        printed on console

        :param level: new level for console
        :return: None
        """
        if type(level) is str:
            level = getattr(Log, level)
        Log.console_handler.level = level

    @staticmethod
    def set_error_level(level):
        """
        Sets log level for logging to console. Every output of level equal or higher to parameter level will be
        printed on console

        :param level: new level for console
        :return: None
        """
        if type(level) is str:
            level = getattr(Log, level)
        Log.error.level = level

    @staticmethod
    def debug(msg, *args):
        """
        Sends debug information to the log

        :param msg: message to show
        :param args: arguments for message formating (it will be done using format() method on str)
        """
        Log.log.log(Log.DEBUG, msg.format(*args))

    @staticmethod
    def info(msg, *args):
        """
        Sends information to the log

        :param msg: message to show
        :param args: arguments for message formatting (it will be done using format() method on str)
        """
        Log.log.log(Log.INFO, msg.format(*args))

    @staticmethod
    def result(msg, *args):
        """
        Sends results information to the log. It will be shown in green in the console.

        :param msg: message to show
        :param args: arguments for message formating (it will be done using format() method on str)
        """
        Log.log.log(Log.RESULT, msg.format(*args))

    @staticmethod
    def user_warning(msg, *args):
        """
        Sends warnings for the user to the log. It will be shown in yellow in the console.

        :param msg: message to show
        :param args: arguments for message formating (it will be done using format() method on str)
        """
        Log.log.log(Log.USER_WARNING, msg.format(*args))

    @staticmethod
    def warning(msg, *args):
        """
        Sends program warnings to the log. It will be shown in yellow in the console.

        :param msg: message to show
        :param args: arguments for message formatting (it will be done using format() method on str)
        """
        Log.log.log(Log.WARNING, msg.format(*args))

    @staticmethod
    def error(msg, *args):
        """
        Sends errors to the log. It will be shown in red in the console.

        :param msg: message to show
        :param args: arguments for message formatting (it will be done using format() method on str)
        """
        Log.log.log(Log.ERROR, msg.format(*args))

    @staticmethod
    def critical(msg, *args):
        """
        Sends critical errors to the log. It will be shown in red in the console.

        :param msg: message to show
        :param args: arguments for message formatting (it will be done using format() method on str)
        """
        Log.log.log(Log.CRITICAL, msg.format(*args))

    @staticmethod
    def status(msg, *args):
        """
        Sends status of jobs to the log. It will be shown in white in the console.

        :param msg: message to show
        :param args: arguments for message formatting (it will be done using format() method on str)
        """
        Log.log.log(Log.STATUS, msg.format(*args))